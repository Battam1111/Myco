//! M22 P5 万物互联 — federation message handlers (extracted from `server.rs` in Phase B Step 5).
//!
//! This submodule owns the *operator-facing* federation dispatch handlers
//! (listener lifecycle, peer connect, poll, status, parent-link, pull-events)
//! plus the small DAG-event-emission helpers (`emit_federation_peer_pinned`
//! et al.) that are shared between the synchronous dispatch handlers and the
//! autonomous-tick path in `server.rs`.
//!
//! The lower-level federation primitives — wire framing, TOFU pinning,
//! `FederationState` / `ConnectPeerOutcome` / `PollPeerEvent` types — still
//! live in [`crate::federation`]. This module is a thin layer that translates
//! between those primitives and the operator's wire protocol.
//!
//! ## Doctrine traceability
//!
//! - L0/cards/P01-P14 (principles).1 P5 万物互联: federation is the inter-substrate half of "the
//!   substrate is a connected graph, not a collection."
//! - L1/HARD_RULES C33 (federation_peer_identity_mismatch), C35
//!   (federation_substrate_private_event_injection), C39
//!   (federation_hello_signature_invalid) — the three immune-sporocarp
//!   detectors this module emits.
//! - L2/FEDERATION wrapped-events architecture: incoming peer events are
//!   wrapped in `federation_received:{peer_id_prefix}` envelopes whose parent
//!   is the *receiver's* DAG tip (NOT the peer's parent_hashes) — preserves
//!   receiver Merkle-chain correctness while recording cross-substrate
//!   provenance.

use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};

use crate::server::{
    emit_immune_sporocarp, emit_substrate_event, hex_first_8_bytes, ServerState,
};
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// M22.1 P5 万物互联 — federation handlers (listener lifecycle + status).
//
// `handle_federation_open_listener` and `handle_federation_close_listener`
// mutate `state.federation.listener` and emit a corresponding
// `federation_listener_opened` / `federation_listener_closed` DAG event.
// `handle_federation_status` is a read-only reporter.
// ---------------------------------------------------------------------------

/// M22.1: open a TCP federation listener on the operator-supplied address.
///
/// Payload:
/// ```text
/// Map({ "bind_addr": String })
/// ```
///
/// Response payload:
/// ```text
/// Map({
///   "bind_addr": String,             // resolved (port-zero → real port)
///   "listener_opened_event_hash": Bytes(32),
/// })
/// ```
pub(crate) fn handle_federation_open_listener(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let bind_addr_requested = match request.payload.get("bind_addr") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "federation_open_listener: bind_addr must be non-empty String".to_string(),
            ));
        }
    };

    let resolved = state.federation.open_listener(&bind_addr_requested)?;
    let resolved_str = resolved.to_string();

    // Emit the federation_listener_opened DAG event so the listener state
    // is recorded in the substrate's causal graph (P5 + P6).
    let opened_at_unix_ns = state
        .federation
        .listener
        .as_ref()
        .map(|l| l.opened_at_unix_ns)
        .unwrap_or(0);
    let event_content = crate::events::encode_federation_listener_opened(
        &resolved_str,
        opened_at_unix_ns,
    );
    let event_hash = emit_substrate_event(
        state,
        crate::events::NODE_TYPE_FEDERATION_LISTENER_OPENED.to_string(),
        event_content,
    )?;

    let mut payload = BTreeMap::new();
    payload.insert("bind_addr".to_string(), Value::String(resolved_str));
    payload.insert(
        "listener_opened_event_hash".to_string(),
        Value::Bytes(event_hash.0.to_vec()),
    );
    Ok(Some(Message::new(
        msg_type::FEDERATION_OPEN_LISTENER_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M22.1: close the active federation listener (idempotent).
///
/// Payload: empty.
///
/// Response payload:
/// ```text
/// Map({
///   "was_listening": Bool,
///   "prior_bind_addr": String,             // empty if was_listening=false
///   "listener_closed_event_hash": Bytes(32) [optional; only if was_listening],
/// })
/// ```
pub(crate) fn handle_federation_close_listener(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let prior_addr_opt = state.federation.close_listener();
    let mut payload = BTreeMap::new();
    match prior_addr_opt {
        Some(prior_addr) => {
            let prior_addr_str = prior_addr.to_string();
            let closed_at_unix_ns = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .ok()
                .and_then(|d| i64::try_from(d.as_nanos()).ok())
                .unwrap_or(0);
            let event_content = crate::events::encode_federation_listener_closed(
                &prior_addr_str,
                closed_at_unix_ns,
            );
            let event_hash = emit_substrate_event(
                state,
                crate::events::NODE_TYPE_FEDERATION_LISTENER_CLOSED.to_string(),
                event_content,
            )?;
            payload.insert("was_listening".to_string(), Value::Bool(true));
            payload.insert(
                "prior_bind_addr".to_string(),
                Value::String(prior_addr_str),
            );
            payload.insert(
                "listener_closed_event_hash".to_string(),
                Value::Bytes(event_hash.0.to_vec()),
            );
        }
        None => {
            payload.insert("was_listening".to_string(), Value::Bool(false));
            payload.insert("prior_bind_addr".to_string(), Value::String(String::new()));
        }
    }
    Ok(Some(Message::new(
        msg_type::FEDERATION_CLOSE_LISTENER_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M22.2 + M25.4: emit a `federation_peer_pinned` DAG event for a newly-pinned
/// peer.
///
/// M25.4 added optional `signer_pubkey` payload — present iff the peer's
/// FED_HELLO carried a verified Ed25519 signature (so the receiver pinned the
/// signing key alongside the substrate_id). Absence = legacy peer.
///
/// Returns the inserted node hash so the caller can surface it in the
/// connect-peer / poll response.
pub(crate) fn emit_federation_peer_pinned(
    state: &mut ServerState,
    peer_substrate_id: &[u8; 32],
    remote_addr: &str,
    first_pinned_unix_ns: i64,
    signer_pubkey: Option<&[u8; 32]>,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    let nt = crate::events::federation_peer_pinned_node_type(peer_substrate_id);
    let content = crate::events::encode_federation_peer_pinned(
        peer_substrate_id,
        remote_addr,
        first_pinned_unix_ns,
        signer_pubkey,
    );
    emit_substrate_event(state, nt, content)
}

/// M25.4: emit a `federation_legacy_peer_pinned` observability event for a
/// peer pinned WITHOUT an Ed25519 signature (legacy compat). This is NOT an
/// immune sporocarp — legacy peers are allowed. The event exists so operators
/// can audit which connections were authenticated by signature vs TOFU only.
pub(crate) fn emit_federation_legacy_peer_pinned(
    state: &mut ServerState,
    peer_substrate_id: &[u8; 32],
    remote_addr: &str,
    first_pinned_unix_ns: i64,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    let nt = crate::events::federation_legacy_peer_pinned_node_type(peer_substrate_id);
    let content = crate::events::encode_federation_legacy_peer_pinned(
        peer_substrate_id,
        remote_addr,
        first_pinned_unix_ns,
    );
    emit_substrate_event(state, nt, content)
}

/// M25.4: emit `C39_federation_hello_signature_invalid` immune sporocarp when
/// a peer presents a tampered/invalid Ed25519 signature in their FED_HELLO.
pub(crate) fn emit_federation_hello_signature_invalid(
    state: &mut ServerState,
    peer_substrate_id: &[u8; 32],
    remote_addr: &str,
    reason: &str,
) -> Result<(), SubstrateError> {
    let evidence = format!(
        "fed_hello signature verification failed: peer_id_prefix={} remote={} reason={}",
        hex_first_8_bytes(peer_substrate_id),
        remote_addr,
        reason
    );
    let _ = emit_immune_sporocarp(
        state,
        "C39_federation_hello_signature_invalid",
        "federation_hello_signature_invalid",
        &evidence,
    );
    Ok(())
}

/// M22.2: emit a `federation_peer_rejected` DAG event + a C20 immune sporocarp
/// when an inbound or outbound peer fails TOFU pinning.
pub(crate) fn emit_federation_peer_rejected(
    state: &mut ServerState,
    offered_substrate_id: &[u8; 32],
    previously_pinned_substrate_id: &[u8; 32],
    remote_addr: &str,
    reason: &str,
) -> Result<(), SubstrateError> {
    let rejected_at_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let nt = crate::events::federation_peer_rejected_node_type(offered_substrate_id);
    let content = crate::events::encode_federation_peer_rejected(
        offered_substrate_id,
        previously_pinned_substrate_id,
        remote_addr,
        rejected_at_unix_ns,
        reason,
    );
    let _ = emit_substrate_event(state, nt, content);
    // C20: peer identity mismatch as an immune sporocarp for operator-level
    // visibility (filter via query_immune_events).
    let evidence = format!(
        "federation_peer_rejected: offered_id_prefix={} reason={}",
        hex_first_8_bytes(offered_substrate_id),
        reason
    );
    let _ = emit_immune_sporocarp(
        state,
        "C33_federation_peer_identity_mismatch",
        "federation_identity_mismatch_detected",
        &evidence,
    );
    Ok(())
}

/// M22.2: handle a `federation_connect_peer` request.
///
/// Payload:
/// ```text
/// Map({ "remote_addr": String })
/// ```
///
/// Response payload:
/// ```text
/// Map({
///   "outcome": String,                                    // "pinned" / "self_connection" / "identity_drift" / "already_pinned"
///   "peer_substrate_id": Bytes(32) [optional],
///   "peer_dag_tip": Bytes(32) [optional],
///   "remote_addr": String,
///   "peer_pinned_event_hash": Bytes(32) [optional; only for "pinned"],
/// })
/// ```
pub(crate) fn handle_federation_connect_peer(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let remote_addr = match request.payload.get("remote_addr") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "federation_connect_peer: remote_addr must be non-empty String".to_string(),
            ));
        }
    };
    let our_substrate_id = state.manifest.substrate_id;
    let our_dag_tip = state.dag.tip().map(|t| t.0);
    let our_signing_seed = state.substrate_signing_seed;

    let outcome = state.federation.connect_peer(
        &remote_addr,
        &our_substrate_id,
        our_dag_tip.as_ref(),
        Some(&our_signing_seed),
    )?;

    let mut payload = BTreeMap::new();
    payload.insert("remote_addr".to_string(), Value::String(remote_addr.clone()));
    match outcome {
        crate::federation::ConnectPeerOutcome::Pinned {
            peer_substrate_id,
            remote_addr_str,
            peer_dag_tip,
            signer_pubkey,
            signature_verified,
        } => {
            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .ok()
                .and_then(|d| i64::try_from(d.as_nanos()).ok())
                .unwrap_or(0);
            let event_hash = emit_federation_peer_pinned(
                state,
                &peer_substrate_id,
                &remote_addr_str,
                now,
                signer_pubkey.as_ref(),
            )?;
            if !signature_verified {
                let _ = emit_federation_legacy_peer_pinned(
                    state,
                    &peer_substrate_id,
                    &remote_addr_str,
                    now,
                );
            }
            payload.insert("outcome".to_string(), Value::String("pinned".to_string()));
            payload.insert(
                "peer_substrate_id".to_string(),
                Value::Bytes(peer_substrate_id.to_vec()),
            );
            if let Some(tip) = peer_dag_tip {
                payload.insert("peer_dag_tip".to_string(), Value::Bytes(tip.to_vec()));
            }
            payload.insert(
                "peer_pinned_event_hash".to_string(),
                Value::Bytes(event_hash.0.to_vec()),
            );
            if let Some(pk) = signer_pubkey {
                payload.insert(
                    "peer_signer_pubkey".to_string(),
                    Value::Bytes(pk.to_vec()),
                );
            }
            payload.insert(
                "signature_verified".to_string(),
                Value::Bool(signature_verified),
            );
        }
        crate::federation::ConnectPeerOutcome::RejectedSelfConnection {
            remote_addr_str,
        } => {
            payload.insert(
                "outcome".to_string(),
                Value::String("self_connection".to_string()),
            );
            payload.insert(
                "remote_addr".to_string(),
                Value::String(remote_addr_str),
            );
        }
        crate::federation::ConnectPeerOutcome::RejectedIdentityDrift {
            peer_substrate_id,
            new_remote_addr_str,
            previously_pinned_remote_addr_str,
        } => {
            let reason = format!(
                "identity drift: id previously pinned at {previously_pinned_remote_addr_str}; \
                 new connection at {new_remote_addr_str}"
            );
            let _ = emit_federation_peer_rejected(
                state,
                &peer_substrate_id,
                &peer_substrate_id,
                &new_remote_addr_str,
                &reason,
            );
            payload.insert(
                "outcome".to_string(),
                Value::String("identity_drift".to_string()),
            );
            payload.insert(
                "peer_substrate_id".to_string(),
                Value::Bytes(peer_substrate_id.to_vec()),
            );
            payload.insert(
                "remote_addr".to_string(),
                Value::String(new_remote_addr_str),
            );
        }
        crate::federation::ConnectPeerOutcome::RejectedSignatureInvalid {
            peer_substrate_id,
            remote_addr_str,
            reason,
        } => {
            let _ = emit_federation_hello_signature_invalid(
                state,
                &peer_substrate_id,
                &remote_addr_str,
                &reason,
            );
            payload.insert(
                "outcome".to_string(),
                Value::String("hello_signature_invalid".to_string()),
            );
            payload.insert(
                "peer_substrate_id".to_string(),
                Value::Bytes(peer_substrate_id.to_vec()),
            );
            payload.insert(
                "remote_addr".to_string(),
                Value::String(remote_addr_str),
            );
            payload.insert("reason".to_string(), Value::String(reason));
        }
        crate::federation::ConnectPeerOutcome::AlreadyPinned {
            peer_substrate_id,
            remote_addr_str,
        } => {
            payload.insert(
                "outcome".to_string(),
                Value::String("already_pinned".to_string()),
            );
            payload.insert(
                "peer_substrate_id".to_string(),
                Value::Bytes(peer_substrate_id.to_vec()),
            );
            payload.insert(
                "remote_addr".to_string(),
                Value::String(remote_addr_str),
            );
        }
    }
    Ok(Some(Message::new(
        msg_type::FEDERATION_CONNECT_PEER_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M22.2: handle a `federation_poll` request — drive one round of nonblocking
/// federation I/O.
///
/// Steps performed (in order):
/// 1. Accept queued inbound connections; add as `AwaitingHello` peers.
/// 2. For each `AwaitingHello` peer, try to read the inbound FED_HELLO;
///    on success, send FED_HELLO_ACK + pin (or reject + emit C20).
/// 3. M22.3+: drain established peers' inbound frames (event batches, etc.).
///
/// Response payload:
/// ```text
/// Map({
///   "accepted_connections": Uint,
///   "pinned_peers": Uint,
///   "rejected_peers": Uint,
/// })
/// ```
pub(crate) fn handle_federation_poll(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let accepted = state.federation.accept_pending()?;
    let our_substrate_id = state.manifest.substrate_id;
    let our_dag_tip = state.dag.tip().map(|t| t.0);
    let our_signing_seed = state.substrate_signing_seed;
    // M22.3 + M25.4: pass &dag so progress_peers can enumerate events for
    // inbound FED_REQUEST_EVENTS_SINCE responses, and pass the signing seed
    // so outbound FED_HELLO_ACK frames carry our Ed25519 signature.
    let events = state.federation.progress_peers(
        &our_substrate_id,
        our_dag_tip.as_ref(),
        Some(&our_signing_seed),
        &state.dag,
    );

    let mut pinned_count = 0u64;
    let mut rejected_count = 0u64;
    let mut event_batches_sent = 0u64;
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);

    for ev in events {
        match ev {
            crate::federation::PollPeerEvent::Pinned {
                peer_substrate_id,
                remote_addr_str,
                peer_dag_tip: _,
                signer_pubkey,
                signature_verified,
            } => {
                let _ = emit_federation_peer_pinned(
                    state,
                    &peer_substrate_id,
                    &remote_addr_str,
                    now,
                    signer_pubkey.as_ref(),
                );
                if !signature_verified {
                    let _ = emit_federation_legacy_peer_pinned(
                        state,
                        &peer_substrate_id,
                        &remote_addr_str,
                        now,
                    );
                }
                pinned_count += 1;
            }
            crate::federation::PollPeerEvent::RejectedSelfConnection { remote_addr_str } => {
                let _ = emit_federation_peer_rejected(
                    state,
                    &our_substrate_id,
                    &our_substrate_id,
                    &remote_addr_str,
                    "inbound peer claimed our own substrate_id (self-connection)",
                );
                rejected_count += 1;
            }
            crate::federation::PollPeerEvent::RejectedSignatureInvalid {
                peer_substrate_id,
                remote_addr_str,
                reason,
            } => {
                let _ = emit_federation_hello_signature_invalid(
                    state,
                    &peer_substrate_id,
                    &remote_addr_str,
                    &reason,
                );
                rejected_count += 1;
            }
            crate::federation::PollPeerEvent::RejectedProtocolVersion {
                peer_substrate_id,
                remote_addr_str,
                peer_version,
                our_version,
            } => {
                // **v3.1.1 Sprint 5.H (T2.5)** — emit C61 immune sporocarp.
                let evidence = format!(
                    "federation protocol version mismatch at fed_hello: \
                     peer.substrate_id={} from {remote_addr_str} declared \
                     protocol_version={peer_version}, our version={our_version}",
                    crate::server::hex_encode(&peer_substrate_id)
                );
                let _ = crate::server::emit_immune_sporocarp(
                    state,
                    "C61_federation_protocol_version_mismatch",
                    "federation_protocol_version_mismatch",
                    &evidence,
                );
                rejected_count += 1;
            }
            crate::federation::PollPeerEvent::FailedFrameRead {
                remote_addr_str,
                reason,
            } => {
                let _ = emit_federation_peer_rejected(
                    state,
                    &[0u8; 32],
                    &our_substrate_id,
                    &remote_addr_str,
                    &format!("frame read failure: {reason}"),
                );
                rejected_count += 1;
            }
            crate::federation::PollPeerEvent::EventsSent {
                peer_substrate_id,
                sent_event_hashes,
            } => {
                let content = crate::events::encode_federation_events_sent(
                    &peer_substrate_id,
                    &sent_event_hashes,
                    now,
                );
                let _ = emit_substrate_event(
                    state,
                    crate::events::NODE_TYPE_FEDERATION_EVENTS_SENT.to_string(),
                    content,
                );
                event_batches_sent += 1;
            }
        }
    }

    let mut payload = BTreeMap::new();
    payload.insert(
        "accepted_connections".to_string(),
        Value::Uint(accepted as u64),
    );
    payload.insert("pinned_peers".to_string(), Value::Uint(pinned_count));
    payload.insert("rejected_peers".to_string(), Value::Uint(rejected_count));
    payload.insert(
        "event_batches_sent".to_string(),
        Value::Uint(event_batches_sent),
    );
    Ok(Some(Message::new(
        msg_type::FEDERATION_POLL_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M22.4: handle `federation_link_to_parent_from_hint`.
///
/// Scans the local DAG for a `parent_federation_hint` event. If found:
/// 1. Extract `parent_federation_addr` + `parent_substrate_id` from event content.
/// 2. Skip if a `federation_parent_linked` event already exists (idempotent).
/// 3. Call `state.federation.connect_peer(...)` with parent's address.
/// 4. On successful pin: emit `federation_peer_pinned` + `federation_parent_linked`.
/// 5. Return outcome to operator.
///
/// Payload: empty.
///
/// Response payload:
/// ```text
/// Map({
///   "hint_found": Bool,
///   "already_linked": Bool,
///   "parent_substrate_id": Bytes(32) [optional; only if hint_found],
///   "parent_federation_addr": String [optional],
///   "parent_linked_event_hash": Bytes(32) [optional; only on success],
/// })
/// ```
pub(crate) fn handle_federation_link_to_parent_from_hint(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, map_get_bytes, map_get_string};

    // Scan for the most recent parent_federation_hint event. The DAG's
    // iter_in_insertion_order is not DoubleEndedIterator, so we scan forward
    // and remember the latest match.
    let hint_node = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type == crate::events::NODE_TYPE_PARENT_FEDERATION_HINT)
        .last();

    let mut payload = BTreeMap::new();
    let Some(hint) = hint_node else {
        payload.insert("hint_found".to_string(), Value::Bool(false));
        payload.insert("already_linked".to_string(), Value::Bool(false));
        return Ok(Some(Message::new(
            msg_type::FEDERATION_LINK_TO_PARENT_FROM_HINT_RESPONSE,
            request.request_id,
            payload,
        )));
    };

    let hint_decoded = cb_decode(hint.content_canonical_bytes.as_ref())
        .map_err(|e| SubstrateError::Protocol(format!("decode parent_federation_hint: {e}")))?;
    let hint_map = match hint_decoded {
        Value::Map(m) => m,
        _ => {
            return Err(SubstrateError::Protocol(
                "parent_federation_hint is not a Map".to_string(),
            ));
        }
    };
    let parent_id_bytes = map_get_bytes(&hint_map, "parent_substrate_id")
        .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
    if parent_id_bytes.len() != 32 {
        return Err(SubstrateError::Protocol(
            "parent_substrate_id in hint is not 32 bytes".to_string(),
        ));
    }
    let mut parent_substrate_id = [0u8; 32];
    parent_substrate_id.copy_from_slice(parent_id_bytes);
    let parent_federation_addr = map_get_string(&hint_map, "parent_federation_addr")
        .map_err(|e| SubstrateError::Protocol(e.to_string()))?
        .to_string();

    // Idempotency: if a federation_parent_linked event already exists for this
    // parent, return early — the link is already established.
    let already_linked = state
        .dag
        .iter_in_insertion_order()
        .any(|n| n.node_type == crate::events::NODE_TYPE_FEDERATION_PARENT_LINKED);

    payload.insert("hint_found".to_string(), Value::Bool(true));
    payload.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(parent_substrate_id.to_vec()),
    );
    payload.insert(
        "parent_federation_addr".to_string(),
        Value::String(parent_federation_addr.clone()),
    );

    if already_linked {
        payload.insert("already_linked".to_string(), Value::Bool(true));
        return Ok(Some(Message::new(
            msg_type::FEDERATION_LINK_TO_PARENT_FROM_HINT_RESPONSE,
            request.request_id,
            payload,
        )));
    }

    payload.insert("already_linked".to_string(), Value::Bool(false));

    // Connect to parent.
    let our_substrate_id = state.manifest.substrate_id;
    let our_dag_tip = state.dag.tip().map(|t| t.0);
    let our_signing_seed = state.substrate_signing_seed;
    let outcome = state.federation.connect_peer(
        &parent_federation_addr,
        &our_substrate_id,
        our_dag_tip.as_ref(),
        Some(&our_signing_seed),
    )?;

    if let crate::federation::ConnectPeerOutcome::Pinned {
        peer_substrate_id,
        remote_addr_str,
        peer_dag_tip: _,
        signer_pubkey,
        signature_verified,
    } = outcome
    {
        // Verify the pinned peer matches the hint's parent_substrate_id.
        if peer_substrate_id != parent_substrate_id {
            return Err(SubstrateError::Protocol(format!(
                "federation parent link: parent at {remote_addr_str} has substrate_id {} but \
                 hint says parent is {}",
                hex_first_8_bytes(&peer_substrate_id),
                hex_first_8_bytes(&parent_substrate_id),
            )));
        }
        let now_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        // Emit federation_peer_pinned (general) + federation_parent_linked (M22.4 specific).
        let _ = emit_federation_peer_pinned(
            state,
            &peer_substrate_id,
            &remote_addr_str,
            now_ns,
            signer_pubkey.as_ref(),
        );
        if !signature_verified {
            let _ = emit_federation_legacy_peer_pinned(
                state,
                &peer_substrate_id,
                &remote_addr_str,
                now_ns,
            );
        }
        let nt = crate::events::NODE_TYPE_FEDERATION_PARENT_LINKED.to_string();
        let content = crate::events::encode_federation_parent_linked(
            &peer_substrate_id,
            &remote_addr_str,
            now_ns,
        );
        let event_hash = emit_substrate_event(state, nt, content)?;
        payload.insert(
            "parent_linked_event_hash".to_string(),
            Value::Bytes(event_hash.0.to_vec()),
        );
    } else {
        // Connect failed in some other way (self-connect, drift, already pinned);
        // surface the outcome label.
        let outcome_label = match outcome {
            crate::federation::ConnectPeerOutcome::RejectedSelfConnection { .. } => {
                "self_connection"
            }
            crate::federation::ConnectPeerOutcome::RejectedIdentityDrift { .. } => "identity_drift",
            crate::federation::ConnectPeerOutcome::AlreadyPinned { .. } => "already_pinned",
            _ => "unknown",
        };
        payload.insert(
            "connect_outcome".to_string(),
            Value::String(outcome_label.to_string()),
        );
    }

    Ok(Some(Message::new(
        msg_type::FEDERATION_LINK_TO_PARENT_FROM_HINT_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M22.3: handle a `federation_pull_events_from_peer` request.
///
/// Payload:
/// ```text
/// Map({
///   "peer_substrate_id": Bytes(32),
///   "since_node_hash": Bytes(32) [optional; absent = pull from genesis],
///   "max_events": Uint [optional; defaults to FED_EVENT_BATCH_MAX_EVENTS],
/// })
/// ```
///
/// Response payload:
/// ```text
/// Map({
///   "events_received_count": Uint,
///   "events_ingested_count": Uint,
///   "is_last_batch": Bool,
///   "events_received_event_hash": Bytes(32) [optional; absent if no events ingested],
/// })
/// ```
pub(crate) fn handle_federation_pull_events_from_peer(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let peer_id_bytes = match request.payload.get("peer_substrate_id") {
        Some(Value::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "federation_pull_events_from_peer: peer_substrate_id must be 32 Bytes".to_string(),
            ));
        }
    };
    let mut peer_substrate_id = [0u8; 32];
    peer_substrate_id.copy_from_slice(&peer_id_bytes);

    let since_node_hash: Option<[u8; 32]> = match request.payload.get("since_node_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut h = [0u8; 32];
            h.copy_from_slice(b);
            Some(h)
        }
        _ => None,
    };
    let max_events = match request.payload.get("max_events") {
        Some(Value::Uint(n)) => *n,
        _ => crate::federation::protocol::FED_EVENT_BATCH_MAX_EVENTS,
    };

    let our_substrate_id = state.manifest.substrate_id;
    let parsed_batch = match state.federation.pull_events_from_peer(
        &peer_substrate_id,
        since_node_hash.as_ref(),
        &our_substrate_id,
        max_events,
    ) {
        Ok(b) => b,
        Err(SubstrateError::Protocol(msg))
            if msg.contains("FED_EVENT_MAX_CONTENT_BYTES") =>
        {
            // **v3.1.1 Sprint 6.B (T1.8)** — per-event size cap breach.
            // Emit C62 immune sporocarp + structured rejection response.
            // Per-event oversize is a peer-behavior signal worth recording
            // separately from generic frame-read failures.
            let evidence = format!(
                "federation peer {} pushed FED_EVENT_BATCH containing an event \
                 exceeding FED_EVENT_MAX_CONTENT_BYTES; parser error: {msg}",
                hex_first_8_bytes(&peer_substrate_id)
            );
            let _ = emit_immune_sporocarp(
                state,
                "C62_federation_event_oversized",
                "federation_event_oversized",
                &evidence,
            );
            // Return structured rejection (not propagate Err) so the operator
            // gets a clear "batch rejected for size" signal instead of a
            // generic protocol error.
            let mut response_payload = BTreeMap::new();
            response_payload.insert(
                "events_ingested_count".to_string(),
                Value::Uint(0),
            );
            response_payload.insert(
                "events_rejected_count".to_string(),
                Value::Uint(1),
            );
            response_payload.insert(
                "rejection_reason".to_string(),
                Value::String(format!("C62_federation_event_oversized: {msg}")),
            );
            return Ok(Some(Message::new(
                msg_type::FEDERATION_PULL_EVENTS_FROM_PEER_RESPONSE,
                request.request_id,
                response_payload,
            )));
        }
        Err(e) => return Err(e),
    };
    let events_received = parsed_batch.events.len();

    // Phase β SECURITY FIX (2026-05-15): event-type ALLOWLIST.
    //
    // Pre-fix, this loop accepted ANY node_type from the peer — letting a
    // malicious peer inject `operator_pinned:`, `cycle_advanced`,
    // `genesis_event:*`, `nonce_issued:*`, etc. The injected events would
    // then mutate Rust-authoritative state via `DerivedState::apply_event`
    // at boot — taking over the substrate's identity, cycle counter,
    // nonce log, or causing MultipleGenesis → empty derived state.
    //
    // Post-fix: only substrate-environmental events (raw_material, sporocarp,
    // mutation, immune) are accepted. Any other node_type triggers a
    // C22 immune sporocarp emission + the event is dropped.
    let mut rejected_events: Vec<(String, [u8; 32])> = Vec::new();
    let mut safe_events: Vec<&crate::federation::protocol::EventForFederation> = Vec::new();
    for ev in &parsed_batch.events {
        if crate::federation::protocol::is_federation_safe_node_type(&ev.node_type) {
            safe_events.push(ev);
        } else {
            // Compute the would-be hash for the rejection record.
            let parents: Vec<myco_kernel_shared::crypto::NodeHash> = ev
                .parent_hashes
                .iter()
                .map(|h| myco_kernel_shared::crypto::NodeHash::from_bytes(*h))
                .collect();
            let would_be_hash = myco_kernel_shared::crypto::merkle_hash(&parents, &ev.content_canonical_bytes);
            rejected_events.push((ev.node_type.clone(), would_be_hash.0));
        }
    }
    if !rejected_events.is_empty() {
        let evidence = format!(
            "federation peer {} attempted to push {} substrate-private event(s); types: {}",
            hex_first_8_bytes(&peer_substrate_id),
            rejected_events.len(),
            rejected_events
                .iter()
                .map(|(t, _)| t.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        );
        let _ = emit_immune_sporocarp(
            state,
            "C35_federation_substrate_private_event_injection",
            "federation_substrate_private_event_injection",
            &evidence,
        );
    }

    // Phase β SECURITY: wrap each ALLOWED peer event in a
    // `federation_received:{peer_id_prefix}` envelope whose parent is the
    // RECEIVER's local DAG tip — NOT the peer's parent_hashes. This:
    //   1. Preserves receiver's Merkle-chain correctness (peer's chain
    //      never merges into receiver's chain).
    //   2. Records full cross-substrate provenance (original peer event +
    //      its parent hashes + its hash are all inside the wrapper content).
    //   3. Makes federation a "I HEARD peer say X" attestation graph rather
    //      than a multi-substrate event-graph merge (which would require
    //      shared causal ancestors, impossible without owner co-attestation
    //      at genesis).
    // Idempotency: re-pulling the same peer event produces the same wrapper
    // content (since wrapper content includes peer_event_original_hash),
    // and Dag::insert_node is content-hash idempotent.
    let peer_id_prefix = hex_first_8_bytes(&peer_substrate_id);
    let wrapper_node_type = format!("federation_received:{peer_id_prefix}");
    let mut ingested_hashes: Vec<[u8; 32]> = Vec::new();
    for ev in &safe_events {
        // Compute the peer's original event hash (what they have in their DAG).
        let peer_parents_nh: Vec<myco_kernel_shared::crypto::NodeHash> = ev
            .parent_hashes
            .iter()
            .map(|h| myco_kernel_shared::crypto::NodeHash::from_bytes(*h))
            .collect();
        let peer_original_hash = myco_kernel_shared::crypto::merkle_hash(
            &peer_parents_nh,
            &ev.content_canonical_bytes,
        );
        // Build wrapper content.
        let mut wrapper_map = BTreeMap::new();
        wrapper_map.insert(
            "from_peer_substrate_id".to_string(),
            Value::Bytes(peer_substrate_id.to_vec()),
        );
        wrapper_map.insert(
            "peer_event_node_type".to_string(),
            Value::String(ev.node_type.clone()),
        );
        let peer_parent_values: Vec<Value> = ev
            .parent_hashes
            .iter()
            .map(|h| Value::Bytes(h.to_vec()))
            .collect();
        wrapper_map.insert(
            "peer_event_parent_hashes".to_string(),
            Value::Array(peer_parent_values),
        );
        wrapper_map.insert(
            "peer_event_content_canonical_bytes".to_string(),
            Value::Bytes(ev.content_canonical_bytes.clone()),
        );
        wrapper_map.insert(
            "peer_event_original_hash".to_string(),
            Value::Bytes(peer_original_hash.0.to_vec()),
        );
        wrapper_map.insert(
            "peer_event_created_at_cycle".to_string(),
            Value::Uint(ev.created_at_cycle),
        );
        let wrapper_content = cb_encode(&Value::Map(wrapper_map))
            .map_err(|e| SubstrateError::Protocol(format!("federation wrapper encode: {e}")))?;
        // Parent = receiver's local tip (NOT peer's parent_hashes).
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let cycle = state.manifest.cycle_counter;
        match state.dag.insert_node(
            parents,
            wrapper_node_type.clone(),
            cycle,
            wrapper_content,
        ) {
            Ok(h) => ingested_hashes.push(h.0),
            Err(e) => {
                return Err(SubstrateError::Protocol(format!(
                    "ingest federation wrapper ({}): {e}",
                    wrapper_node_type
                )));
            }
        }
    }
    state.federation.events_received_total = state
        .federation
        .events_received_total
        .saturating_add(events_received as u64);

    // Emit federation_events_received marker event (with the list of ingested
    // event hashes as content). This is the substrate's record of the
    // federation pull in its own causal chain.
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let events_received_event_hash = if !ingested_hashes.is_empty() {
        let content = crate::events::encode_federation_events_received(
            &peer_substrate_id,
            &ingested_hashes,
            now,
        );
        let h = emit_substrate_event(
            state,
            crate::events::NODE_TYPE_FEDERATION_EVENTS_RECEIVED.to_string(),
            content,
        )?;
        Some(h.0)
    } else {
        None
    };

    let mut payload = BTreeMap::new();
    payload.insert(
        "events_received_count".to_string(),
        Value::Uint(events_received as u64),
    );
    payload.insert(
        "events_ingested_count".to_string(),
        Value::Uint(ingested_hashes.len() as u64),
    );
    payload.insert(
        "is_last_batch".to_string(),
        Value::Bool(parsed_batch.is_last_batch),
    );
    if let Some(h) = events_received_event_hash {
        payload.insert(
            "events_received_event_hash".to_string(),
            Value::Bytes(h.to_vec()),
        );
    }
    Ok(Some(Message::new(
        msg_type::FEDERATION_PULL_EVENTS_FROM_PEER_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M22.1: report federation state.
///
/// Payload: empty.
///
/// Response payload:
/// ```text
/// Map({
///   "is_listening": Bool,
///   "bind_addr": String,                          // empty if not listening
///   "peer_count": Uint,
///   "events_received_total": Uint,
///   "events_sent_total": Uint,
/// })
/// ```
pub(crate) fn handle_federation_status(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let listener_addr = state.federation.listener_addr();
    let mut payload = BTreeMap::new();
    payload.insert(
        "is_listening".to_string(),
        Value::Bool(listener_addr.is_some()),
    );
    payload.insert(
        "bind_addr".to_string(),
        Value::String(listener_addr.map(|a| a.to_string()).unwrap_or_default()),
    );
    payload.insert(
        "peer_count".to_string(),
        Value::Uint(state.federation.peer_count() as u64),
    );
    payload.insert(
        "events_received_total".to_string(),
        Value::Uint(state.federation.events_received_total),
    );
    payload.insert(
        "events_sent_total".to_string(),
        Value::Uint(state.federation.events_sent_total),
    );
    Ok(Some(Message::new(
        msg_type::FEDERATION_STATUS_RESPONSE,
        request.request_id,
        payload,
    )))
}
