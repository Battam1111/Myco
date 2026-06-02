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
use myco_kernel_shared::canonical_bytes::{
    decode as cb_decode, encode as cb_encode, map_get_bytes, map_get_string, Value,
};

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

/// **C13** — emit a `federation_peer_revoked:{prefix}` DAG event (the
/// owner-attested CRL entry) AND insert the target into the in-memory
/// revoked-set.
///
/// **Idempotent at the EFFECT level**: if the peer is ALREADY in the
/// revoked-set, this is a no-op — it returns `Ok(None)` WITHOUT emitting a
/// second CRL event. (Content-hash dedup alone is insufficient: a re-revoke
/// arrives at a different DAG tip, so its `merkle_hash(parents, content)`
/// differs and `Dag::insert_node` would NOT collapse it. Guarding on the set
/// membership makes re-revoke a genuine no-op, matching the doctrine "re-revoke
/// = no-op".) The `mutation:revoke_federation_peer` audit node is still
/// recorded by the caller — only the duplicate CRL effect is suppressed.
///
/// The body fields (`revoked_pubkey`, `reason`, `anchor_timestamp_unix_seconds`)
/// and the owner attestation (`owner_signature`, `owner_pubkey`) come from the
/// decoded + accepted `revoke_federation_peer` mutation in
/// `attestation::handle_submit_mutation`. Returns `Ok(Some(hash))` on a
/// first-time revocation, `Ok(None)` when the peer was already revoked.
pub(crate) fn emit_federation_peer_revoked(
    state: &mut ServerState,
    revoked_peer_substrate_id: &[u8; 32],
    revoked_pubkey: &[u8; 32],
    reason: &str,
    anchor_timestamp_unix_seconds: u64,
    owner_signature: &[u8; 64],
    owner_pubkey: &[u8; 32],
) -> Result<Option<myco_kernel_shared::crypto::NodeHash>, SubstrateError> {
    if state
        .revoked_federation_peers
        .contains(revoked_peer_substrate_id)
    {
        // Already revoked — no-op (do not append a duplicate CRL entry).
        return Ok(None);
    }
    let nt = crate::events::federation_peer_revoked_node_type(revoked_peer_substrate_id);
    let content = crate::events::encode_federation_peer_revoked(
        revoked_peer_substrate_id,
        revoked_pubkey,
        reason,
        anchor_timestamp_unix_seconds,
        owner_signature,
        owner_pubkey,
    );
    let hash = emit_substrate_event(state, nt, content)?;
    state.revoked_federation_peers.insert(*revoked_peer_substrate_id);
    Ok(Some(hash))
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
    let our_substrate_id = state.substrate_id();
    let our_dag_tip = state.dag.tip().map(|t| t.0);
    let our_signing_seed = state.substrate_signing_seed;
    // **§6.5.a** — peer-count before the dial, to detect a 2→3 crossing.
    let prior_peer_count = state.federation.peer_count();

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
    // **§6.5.a** — emit the activation/deactivation crossing if this outbound
    // connect moved peer_count across the 2↔3 boundary.
    crate::consensus::emit_consensus_floor_crossing_if_needed(state, prior_peer_count)?;
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
    // **§6.5.a** — capture peer-count BEFORE this poll so we can emit a
    // consensus_floor_activated/_deactivated event if the poll crosses the 2↔3
    // boundary (inbound peers pinned during the poll change the count).
    let prior_peer_count = state.federation.peer_count();
    let accepted = state.federation.accept_pending()?;
    let our_substrate_id = state.substrate_id();
    let our_dag_tip = state.dag.tip().map(|t| t.0);
    let our_signing_seed = state.substrate_signing_seed;
    // M22.3 + M25.4: pass &dag so progress_peers can enumerate events for
    // inbound FED_REQUEST_EVENTS_SINCE responses, and pass the signing seed
    // so outbound FED_HELLO_ACK frames carry our Ed25519 signature.
    // **C13**: pass the revoked-set so the egress site can block (pre-emission)
    // any FED_EVENT_BATCH to a revoked peer. Disjoint-field borrows: `&mut
    // state.federation` + `&state.dag` + `&state.revoked_federation_peers`.
    let events = state.federation.progress_peers(
        &our_substrate_id,
        our_dag_tip.as_ref(),
        Some(&our_signing_seed),
        &state.dag,
        &state.revoked_federation_peers,
    );

    let mut pinned_count = 0u64;
    let mut rejected_count = 0u64;
    let mut event_batches_sent = 0u64;
    let mut egress_blocked_revoked_count = 0u64;
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
            crate::federation::PollPeerEvent::EgressBlockedRevoked {
                peer_substrate_id,
                remote_addr_str,
            } => {
                // **C13** (L1/HARD_RULES C13 peer_attestation_revoked_egress).
                // The egress site already suppressed the FED_EVENT_BATCH
                // (pre-emission). Fruit the immune sporocarp recording the
                // blocked outbound envelope. The skin-layer
                // `OutputError::FederationEgressBlocked` is the type a wired
                // output gate would return; substrate-side the realization is
                // this DAG-recorded breach + the suppressed send.
                let evidence = format!(
                    "federation_egress_blocked: outbound FED_EVENT_BATCH to peer {} \
                     (remote={remote_addr_str}) suppressed pre-emission — peer is on the \
                     owner-revocation list (L1/GOVERNANCE §5.2)",
                    hex_first_8_bytes(&peer_substrate_id)
                );
                let _ = emit_immune_sporocarp(
                    state,
                    "C13_peer_attestation_revoked_egress",
                    "peer_attestation_revoked_egress",
                    &evidence,
                );
                egress_blocked_revoked_count += 1;
            }
        }
    }

    // **§6.5.a** — emit the consensus-floor activation/deactivation crossing if
    // this poll moved peer_count across the 2↔3 boundary.
    crate::consensus::emit_consensus_floor_crossing_if_needed(state, prior_peer_count)?;

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
    payload.insert(
        "consensus_floor_active".to_string(),
        Value::Bool(crate::consensus::consensus_floor_active(state)),
    );
    // **C13**: number of FED_EVENT_BATCH egress attempts blocked this poll
    // because the requesting peer is on the owner-revocation list.
    payload.insert(
        "egress_blocked_revoked".to_string(),
        Value::Uint(egress_blocked_revoked_count),
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
    // `cb_decode` / `map_get_bytes` / `map_get_string` come from the module-level
    // import (extended for the C43 validator below).

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
    let our_substrate_id = state.substrate_id();
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

// ---------------------------------------------------------------------------
// C43 federation recursive-injection defense (L2/FEDERATION §11 +
// docs/architecture/algorithms/federation_recursive_validation.md).
//
// SECURITY-CRITICAL. The Phase β allowlist (`is_federation_safe_node_type`,
// see protocol.rs) intentionally permits the `federation_received:` prefix so
// that *chained* federation propagates ("I heard A heard B say X"). But that
// single-level allowlist check inspects only the OUTERMOST inner `node_type`.
// A malicious peer can therefore:
//   1. **Depth-exhaustion** — nest `federation_received:` wrappers arbitrarily
//      deep, forcing the receiver to carry an unbounded attestation chain
//      (and, at boot/replay, to walk it). C43 caps the nesting depth.
//   2. **Banned-type laundering** — bury a substrate-private node_type (e.g.
//      `operator_pinned:*`, `cycle_advanced`) several wrappers down, where the
//      single-level check never looks. C35 (here extended with a
//      `cascade_flag`) rejects it at any depth.
//
// `validate_federation_inner` is a PURE function over the peer event's
// (node_type, content) — no `ServerState`, so it is deterministically
// unit-testable over hand-built canonical bytes (see `#[cfg(test)]` below).
// The pull-path call site maps the returned `FederationRecursionReject` to the
// correct immune-sporocarp emission (C43 vs C35) and DROPS the whole offending
// envelope (no partial acceptance — layers 0..N-1's testimony was *about*
// layer N, so a banned/over-deep layer N poisons the entire chain).
// ---------------------------------------------------------------------------

/// Seed maximum `federation_received:` nesting depth (depth 0 = outermost
/// incoming peer event). A chain reaching depth `MAX_FEDERATION_RECURSION_DEPTH`
/// is still accepted; the first level *beyond* it (depth
/// `MAX_FEDERATION_RECURSION_DEPTH + 1`) is rejected with C43.
///
/// Per `federation_recursive_validation.md` "Max depth": seed = 5. L1 may
/// tighten (e.g. 3) or relax (e.g. 7); a future SSoT-tunable surfaces this.
pub(crate) const MAX_FEDERATION_RECURSION_DEPTH: usize = 5;

/// Why a peer event's (possibly nested) `federation_received:` chain was
/// rejected by [`validate_federation_inner`]. The pull-path call site turns
/// this into the matching immune sporocarp (C43 / C35) and drops the envelope.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum FederationRecursionReject {
    /// The chain nested deeper than [`MAX_FEDERATION_RECURSION_DEPTH`].
    /// `attempted_depth` is the depth at which the cap was exceeded
    /// (== `MAX_FEDERATION_RECURSION_DEPTH + 1` for the shallowest violation,
    /// deeper if the leaf itself is still a wrapper). Emits **C43**.
    DepthExceeded {
        /// Depth at which `depth > MAX_FEDERATION_RECURSION_DEPTH` first held.
        attempted_depth: usize,
    },
    /// A nested wrapper's inner `peer_event_node_type` is NOT
    /// `is_federation_safe_node_type` — a substrate-private type smuggled
    /// `depth` levels down. Emits **C35** with `cascade_flag=true`.
    BannedInnerType {
        /// Depth (>= 1) at which the banned inner type was found.
        depth: usize,
        /// The offending inner node_type (recorded in the C35 evidence).
        inner_node_type: String,
    },
    /// A `federation_received:` wrapper's content could not be decoded as a
    /// well-formed wrapper Map (missing/!`peer_event_node_type` or
    /// `peer_event_content_canonical_bytes`, or non-canonical bytes). Treated
    /// as a banned/cascade rejection (C35) — a peer offering a malformed
    /// wrapper under an allowlisted prefix is conservatively refused rather
    /// than silently wrapped. `depth` is where decoding failed.
    MalformedWrapper {
        /// Depth at which wrapper decoding failed.
        depth: usize,
        /// Human-readable decode failure (for the C35 evidence string).
        reason: String,
    },
}

/// **C43 / L2/FEDERATION §11** — recursively validate the (node_type, content)
/// of a peer event about to be wrapped on the federation pull path.
///
/// Pure + side-effect-free: returns `Ok(())` if the event (and every nested
/// `federation_received:` layer it carries) is within depth and contains only
/// allowlisted inner types; otherwise returns the [`FederationRecursionReject`]
/// describing the first violation. The caller emits the immune sporocarp and
/// rejects the ENTIRE outer envelope (no partial acceptance).
///
/// Recursion contract (matches `federation_recursive_validation.md`):
/// - `depth > MAX_FEDERATION_RECURSION_DEPTH` → `DepthExceeded` (checked FIRST,
///   before any decode, so an over-deep chain is refused regardless of leaf).
/// - `node_type` is NOT a `federation_received:` wrapper → `Ok` (the
///   single-level allowlist already vetted this leaf type at the call site for
///   depth 0; deeper leaf types are vetted by the recursion below before we
///   arrive here, so a non-wrapper node_type is a valid terminus).
/// - `node_type` IS a `federation_received:` wrapper → decode its
///   `peer_event_node_type` (inner type) + `peer_event_content_canonical_bytes`
///   (inner content); reject if the inner type is not
///   `is_federation_safe_node_type` (→ `BannedInnerType`), else recurse into
///   the inner (node_type, content) at `depth + 1`.
pub(crate) fn validate_federation_inner(
    node_type: &str,
    content: &[u8],
    depth: usize,
) -> Result<(), FederationRecursionReject> {
    // Depth gate FIRST — an over-deep chain is rejected before we even decode
    // the (potentially adversarial) content at this level. This is the
    // depth-exhaustion defense: the attacker cannot force unbounded recursion
    // / allocation here, and the over-deep envelope is dropped wholesale.
    if depth > MAX_FEDERATION_RECURSION_DEPTH {
        return Err(FederationRecursionReject::DepthExceeded {
            attempted_depth: depth,
        });
    }

    // Non-wrapper leaf: valid terminus. (At depth 0 the call site has already
    // confirmed this type is allowlisted; at depth >= 1 the parent wrapper's
    // inner-type allowlist check below confirmed it before recursing.)
    if !node_type.starts_with(crate::events::NODE_TYPE_FEDERATION_RECEIVED_PREFIX) {
        return Ok(());
    }

    // Wrapper: decode the embedded peer event (inner type + inner content) and
    // recurse one level deeper. A wrapper whose content is not a well-formed
    // wrapper Map is conservatively rejected (MalformedWrapper → C35) rather
    // than accepted — a peer offering garbage under the `federation_received:`
    // prefix is misbehaving.
    let decoded = match cb_decode(content) {
        Ok(Value::Map(m)) => m,
        Ok(_) => {
            return Err(FederationRecursionReject::MalformedWrapper {
                depth,
                reason: "federation_received wrapper content is not a Map".to_string(),
            });
        }
        Err(e) => {
            return Err(FederationRecursionReject::MalformedWrapper {
                depth,
                reason: format!("federation_received wrapper content decode failed: {e}"),
            });
        }
    };
    let inner_node_type = match map_get_string(&decoded, "peer_event_node_type") {
        Ok(s) => s.to_string(),
        Err(e) => {
            return Err(FederationRecursionReject::MalformedWrapper {
                depth,
                reason: format!("wrapper missing peer_event_node_type: {e}"),
            });
        }
    };
    let inner_content = match map_get_bytes(&decoded, "peer_event_content_canonical_bytes") {
        Ok(b) => b.to_vec(),
        Err(e) => {
            return Err(FederationRecursionReject::MalformedWrapper {
                depth,
                reason: format!("wrapper missing peer_event_content_canonical_bytes: {e}"),
            });
        }
    };

    // Banned-type-at-depth: the smuggled inner type must itself be on the
    // federation allowlist, at EVERY depth — not just the outermost level.
    if !crate::federation::protocol::is_federation_safe_node_type(&inner_node_type) {
        return Err(FederationRecursionReject::BannedInnerType {
            depth: depth + 1,
            inner_node_type,
        });
    }

    // Descend into the embedded peer event one level deeper.
    validate_federation_inner(&inner_node_type, &inner_content, depth + 1)
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

    // **C13 — ingest non-absorption check.** If the owner has revoked this
    // peer, its events must stop being absorbed (the symmetric inbound half of
    // the GOVERNANCE §5.2 revocation: a revoked peer is cut off BOTH ways). We
    // refuse before pulling a single frame over the wire — no revoked-peer
    // event can enter the DAG. Returns a structured rejection (ingested=0) so
    // the operator gets a clear signal, and fruits C13 with explicit
    // ingest-direction evidence (reusing the C13 row rather than minting a
    // new one — the revocation list is the same, only the direction differs).
    if state.revoked_federation_peers.contains(&peer_substrate_id) {
        let evidence = format!(
            "federation_ingest_blocked: pull from peer {} refused — peer is on the \
             owner-revocation list (L1/GOVERNANCE §5.2); a revoked peer's events are \
             not absorbed (inbound half of revocation)",
            hex_first_8_bytes(&peer_substrate_id)
        );
        let _ = emit_immune_sporocarp(
            state,
            "C13_peer_attestation_revoked_egress",
            "peer_attestation_revoked_egress",
            &evidence,
        );
        let mut response_payload = BTreeMap::new();
        response_payload.insert("events_received_count".to_string(), Value::Uint(0));
        response_payload.insert("events_ingested_count".to_string(), Value::Uint(0));
        response_payload.insert("events_rejected_count".to_string(), Value::Uint(0));
        response_payload.insert("is_last_batch".to_string(), Value::Bool(true));
        response_payload.insert(
            "rejection_reason".to_string(),
            Value::String(
                "C13_peer_attestation_revoked_egress: peer is revoked; ingest refused"
                    .to_string(),
            ),
        );
        return Ok(Some(Message::new(
            msg_type::FEDERATION_PULL_EVENTS_FROM_PEER_RESPONSE,
            request.request_id,
            response_payload,
        )));
    }

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

    let our_substrate_id = state.substrate_id();
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
    //
    // **C43 (2026-06-02) — recursive-injection / depth-exhaustion defense.**
    // The single-level allowlist above permits the `federation_received:`
    // prefix (so chained federation propagates). That alone is bypassable: a
    // malicious peer can nest `federation_received:` wrappers to (a) exhaust
    // recursion depth or (b) smuggle a banned substrate-private type buried
    // several wrappers down where the single-level check never looks. Each
    // candidate "safe" event is therefore ALSO run through
    // `validate_federation_inner` (recursive, every depth). A reject DROPS the
    // entire offending envelope (no partial acceptance — see C43 doctrine) and
    // emits C43 (depth-exhaustion) or C35-with-`cascade_flag` (banned/malformed
    // at depth). See `federation_recursive_validation.md` + L2/FEDERATION §11.
    // A recursive-validation reject that maps to the C35 cascade path. Carries a
    // typed `kind` instead of stuffing a sentinel string into the inner-type
    // slot, so the malformed-wrapper case is distinguishable from a genuine
    // banned inner type when an operator reads the evidence.
    enum CascadeKind {
        /// A substrate-private inner type smuggled `depth` levels down.
        BannedInner(String),
        /// A `federation_received:` wrapper that did not decode as a well-formed
        /// wrapper Map (carries the decode-failure reason).
        Malformed(String),
    }
    struct CascadeReject {
        depth: usize,
        kind: CascadeKind,
    }
    impl CascadeReject {
        /// `depth=N:<detail>` line for the C35 evidence string.
        fn detail(&self) -> String {
            match &self.kind {
                CascadeKind::BannedInner(ty) => format!("depth={}:{ty}", self.depth),
                CascadeKind::Malformed(reason) => {
                    format!("depth={}:<malformed wrapper: {reason}>", self.depth)
                }
            }
        }
    }

    let mut rejected_events: Vec<(String, [u8; 32])> = Vec::new();
    let mut recursive_depth_rejects: Vec<usize> = Vec::new();
    let mut recursive_cascade_rejects: Vec<CascadeReject> = Vec::new();
    let mut safe_events: Vec<&crate::federation::protocol::EventForFederation> = Vec::new();
    for ev in &parsed_batch.events {
        if !crate::federation::protocol::is_federation_safe_node_type(&ev.node_type) {
            // Single-level allowlist miss (existing Phase β C35 path).
            let parents: Vec<myco_kernel_shared::crypto::NodeHash> = ev
                .parent_hashes
                .iter()
                .map(|h| myco_kernel_shared::crypto::NodeHash::from_bytes(*h))
                .collect();
            let would_be_hash = myco_kernel_shared::crypto::merkle_hash(&parents, &ev.content_canonical_bytes);
            rejected_events.push((ev.node_type.clone(), would_be_hash.0));
            continue;
        }
        // C43: recursively validate the (node_type, content) before allowing
        // it to be wrapped. Conservative — any reject drops the whole event.
        match validate_federation_inner(&ev.node_type, &ev.content_canonical_bytes, 0) {
            Ok(()) => safe_events.push(ev),
            Err(FederationRecursionReject::DepthExceeded { attempted_depth }) => {
                recursive_depth_rejects.push(attempted_depth);
            }
            Err(FederationRecursionReject::BannedInnerType {
                depth,
                inner_node_type,
            }) => {
                recursive_cascade_rejects.push(CascadeReject {
                    depth,
                    kind: CascadeKind::BannedInner(inner_node_type),
                });
            }
            Err(FederationRecursionReject::MalformedWrapper { depth, reason }) => {
                // Malformed wrapper under an allowlisted prefix → conservative
                // C35-class reject (typed as Malformed so operators can tell it
                // from a genuine banned inner type).
                recursive_cascade_rejects.push(CascadeReject {
                    depth,
                    kind: CascadeKind::Malformed(reason),
                });
            }
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
    // C43 depth-exhaustion: emit one immune sporocarp summarizing the
    // over-deep envelope(s). The whole outer envelope was already dropped
    // (the event never entered `safe_events`).
    if !recursive_depth_rejects.is_empty() {
        let max_attempted = recursive_depth_rejects.iter().copied().max().unwrap_or(0);
        let evidence = format!(
            "federation_recursive_injection: peer {} pushed {} event(s) whose \
             federation_received: nesting exceeded MAX_FEDERATION_RECURSION_DEPTH; \
             attempted_depth={} max={}; entire outer envelope rejected (no partial \
             acceptance)",
            hex_first_8_bytes(&peer_substrate_id),
            recursive_depth_rejects.len(),
            max_attempted,
            MAX_FEDERATION_RECURSION_DEPTH,
        );
        let _ = emit_immune_sporocarp(
            state,
            "C43_federation_recursive_injection",
            "federation_recursive_injection",
            &evidence,
        );
    }
    // C35 (cascade) — banned / malformed inner type smuggled at depth. Distinct
    // from the single-level C35 above by `cascade_flag=true` + `depth` +
    // `inner_type` in the evidence string.
    if !recursive_cascade_rejects.is_empty() {
        let detail = recursive_cascade_rejects
            .iter()
            .map(CascadeReject::detail)
            .collect::<Vec<_>>()
            .join(", ");
        let evidence = format!(
            "federation_substrate_private_event_injection cascade_flag=true: peer {} \
             smuggled {} banned/malformed inner event-type(s) inside nested \
             federation_received: wrappers; {}; entire outer envelope rejected",
            hex_first_8_bytes(&peer_substrate_id),
            recursive_cascade_rejects.len(),
            detail,
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
        let cycle = state.cycle_counter();
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

#[cfg(test)]
mod c43_recursive_validation_tests {
    //! C43 federation recursive-injection defense — deterministic unit tests
    //! over hand-built canonical bytes (no wire / no `ServerState` needed).
    //!
    //! These exercise `validate_federation_inner` directly, which is the pure
    //! decision core wired into the federation pull path. The pull-path call
    //! site (in `handle_federation_pull_events_from_peer`) maps each
    //! `FederationRecursionReject` to the matching immune sporocarp (C43 /
    //! C35-cascade) and drops the whole offending envelope.
    use super::*;

    /// A safe, non-wrapper leaf event (allowlisted prefix `raw_material:`) with
    /// arbitrary canonical-bytes content. The recursion terminates here with
    /// `Ok`.
    fn safe_leaf() -> (String, Vec<u8>) {
        let mut m = BTreeMap::new();
        m.insert("content_kind".to_string(), Value::String("text".to_string()));
        m.insert("content".to_string(), Value::Bytes(b"peer environmental".to_vec()));
        let content = cb_encode(&Value::Map(m)).expect("leaf encode").as_ref().to_vec();
        ("raw_material:peer".to_string(), content)
    }

    /// A substrate-private (BANNED) leaf event — exactly the class the
    /// allowlist exists to keep out (`operator_pinned:*` overwrites the pinned
    /// operator identity at replay).
    fn banned_leaf() -> (String, Vec<u8>) {
        let mut m = BTreeMap::new();
        m.insert("victim".to_string(), Value::Bytes(vec![0xde, 0xad]));
        let content = cb_encode(&Value::Map(m)).expect("banned encode").as_ref().to_vec();
        ("operator_pinned:victim".to_string(), content)
    }

    /// Wrap an inner `(node_type, content)` pair into a `federation_received:`
    /// envelope's canonical bytes — exactly the wrapper-content shape the pull
    /// path produces (and therefore the shape the validator decodes). Returns
    /// the wrapper's own `(node_type, content)`.
    ///
    /// Only `peer_event_node_type` + `peer_event_content_canonical_bytes` are
    /// read by `validate_federation_inner`; the other provenance fields are
    /// included so the fixture matches the real on-wire wrapper byte-for-byte.
    fn wrap(inner_node_type: &str, inner_content: &[u8]) -> (String, Vec<u8>) {
        let mut m = BTreeMap::new();
        m.insert(
            "from_peer_substrate_id".to_string(),
            Value::Bytes(vec![0x11; 32]),
        );
        m.insert(
            "peer_event_node_type".to_string(),
            Value::String(inner_node_type.to_string()),
        );
        m.insert(
            "peer_event_parent_hashes".to_string(),
            Value::Array(Vec::new()),
        );
        m.insert(
            "peer_event_content_canonical_bytes".to_string(),
            Value::Bytes(inner_content.to_vec()),
        );
        m.insert(
            "peer_event_original_hash".to_string(),
            Value::Bytes(vec![0x22; 32]),
        );
        m.insert("peer_event_created_at_cycle".to_string(), Value::Uint(0));
        let content = cb_encode(&Value::Map(m)).expect("wrapper encode").as_ref().to_vec();
        ("federation_received:abcd1234".to_string(), content)
    }

    /// Build a chain of `n` `federation_received:` wrappers around `leaf`.
    /// The returned `(node_type, content)` is the OUTERMOST wrapper — i.e. what
    /// a peer would push as a single allowlisted event.
    fn nest(n: usize, leaf: (String, Vec<u8>)) -> (String, Vec<u8>) {
        let (mut ty, mut content) = leaf;
        for _ in 0..n {
            let (wt, wc) = wrap(&ty, &content);
            ty = wt;
            content = wc;
        }
        (ty, content)
    }

    #[test]
    fn max_depth_constant_matches_algorithm_doc_seed() {
        // federation_recursive_validation.md "Max depth": seed = 5.
        assert_eq!(MAX_FEDERATION_RECURSION_DEPTH, 5);
    }

    #[test]
    fn non_wrapper_safe_leaf_is_accepted() {
        let (ty, content) = safe_leaf();
        assert_eq!(validate_federation_inner(&ty, &content, 0), Ok(()));
    }

    #[test]
    fn single_level_wrapper_with_safe_inner_is_accepted() {
        // One `federation_received:` wrapper around a raw_material leaf — the
        // ordinary "I heard peer say X" attestation. Must pass (this is the
        // legitimate federation path the allowlist already permits).
        let (ty, content) = nest(1, safe_leaf());
        assert_eq!(validate_federation_inner(&ty, &content, 0), Ok(()));
    }

    #[test]
    fn legitimate_depth_5_chain_is_accepted() {
        // 5 nested wrappers + a safe leaf. The validator descends to depth 5
        // (== MAX_FEDERATION_RECURSION_DEPTH), finds a non-wrapper safe leaf,
        // and accepts. depth 5 is NOT > 5, so no C43.
        let (ty, content) = nest(5, safe_leaf());
        assert_eq!(
            validate_federation_inner(&ty, &content, 0),
            Ok(()),
            "a chain reaching exactly MAX depth must still be accepted"
        );
    }

    #[test]
    fn depth_exhaustion_at_six_levels_is_rejected_with_attempted_depth_6() {
        // 6 nested wrappers → the validator descends to depth 6, where the
        // `depth > MAX` gate fires FIRST (before decoding) → C43 with
        // attempted_depth == 6. The whole outer envelope is rejected.
        let (ty, content) = nest(6, safe_leaf());
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("6-deep nesting must be rejected");
        assert_eq!(
            reject,
            FederationRecursionReject::DepthExceeded { attempted_depth: 6 },
            "depth-exhaustion must report attempted_depth=6 (one beyond MAX=5)"
        );
    }

    #[test]
    fn deep_nesting_well_beyond_max_still_reports_first_violation_depth() {
        // Even a 50-deep chain is rejected at the FIRST over-MAX level
        // (attempted_depth = MAX + 1 = 6) — the validator never walks the
        // whole adversarial chain (depth-exhaustion protection works).
        let (ty, content) = nest(50, safe_leaf());
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("50-deep nesting must be rejected");
        assert_eq!(
            reject,
            FederationRecursionReject::DepthExceeded { attempted_depth: 6 },
        );
    }

    #[test]
    fn banned_type_buried_at_depth_3_is_rejected_with_cascade() {
        // 3 wrappers where the innermost wraps a substrate-private
        // `operator_pinned:` type. The single-level allowlist (outer type is
        // `federation_received:`) would MISS this; the recursive validator
        // catches it at depth 3 → C35 with cascade_flag.
        let (ty, content) = nest(3, banned_leaf());
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("banned inner type at depth 3 must be rejected");
        match reject {
            FederationRecursionReject::BannedInnerType {
                depth,
                inner_node_type,
            } => {
                assert_eq!(depth, 3, "banned inner type must be reported at depth 3");
                assert_eq!(inner_node_type, "operator_pinned:victim");
            }
            other => panic!("expected BannedInnerType at depth 3; got {other:?}"),
        }
    }

    #[test]
    fn banned_inner_at_depth_1_is_rejected() {
        // A single wrapper directly around a banned type (the minimal
        // laundering attempt). Caught at depth 1.
        let (ty, content) = nest(1, banned_leaf());
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("banned inner type at depth 1 must be rejected");
        assert_eq!(
            reject,
            FederationRecursionReject::BannedInnerType {
                depth: 1,
                inner_node_type: "operator_pinned:victim".to_string(),
            },
        );
    }

    #[test]
    fn banned_leaf_within_max_depth_is_caught_as_cascade_not_depth() {
        // 6 wrappers around a banned leaf. The innermost wrapper (which holds
        // the banned `operator_pinned:` inner type) is reached at recursion
        // depth 5 — WITHIN the depth bound — so its banned inner is caught and
        // reported as BannedInnerType at depth 6 (depth+1). The depth gate
        // (depth > 5) never fires because we never recurse past the banned
        // layer. Both outcomes drop the envelope; this pins the precise signal.
        let (ty, content) = nest(6, banned_leaf());
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("6-deep banned chain must be rejected");
        assert_eq!(
            reject,
            FederationRecursionReject::BannedInnerType {
                depth: 6,
                inner_node_type: "operator_pinned:victim".to_string(),
            },
            "a banned inner reachable within MAX depth is a cascade reject, not depth-exhaustion"
        );
    }

    #[test]
    fn depth_gate_cannot_be_bypassed_by_burying_banned_leaf_deeper() {
        // 7 wrappers around a banned leaf: the validator exhausts the depth
        // budget (DepthExceeded at attempted_depth=6) BEFORE it can ever reach
        // the wrapper holding the banned leaf (which sits at depth 7). This is
        // the security-critical property — an attacker cannot push the banned
        // payload past inspection by nesting it deeper; the depth gate refuses
        // the whole over-deep envelope first.
        let (ty, content) = nest(7, banned_leaf());
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("7-deep banned chain must be rejected");
        assert_eq!(
            reject,
            FederationRecursionReject::DepthExceeded { attempted_depth: 6 },
            "depth gate must fire before reaching a banned leaf buried beyond MAX depth"
        );
    }

    #[test]
    fn malformed_wrapper_content_is_conservatively_rejected() {
        // A `federation_received:` event whose content is NOT a decodable
        // wrapper Map. The validator refuses it (MalformedWrapper → C35-class)
        // rather than silently wrapping garbage under an allowlisted prefix.
        let ty = "federation_received:deadbeef".to_string();
        let content = vec![0xff, 0x00, 0x13, 0x37]; // not valid canonical bytes
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("undecodable wrapper content must be rejected");
        match reject {
            FederationRecursionReject::MalformedWrapper { depth, .. } => {
                assert_eq!(depth, 0);
            }
            other => panic!("expected MalformedWrapper; got {other:?}"),
        }
    }

    #[test]
    fn wrapper_missing_inner_type_field_is_rejected() {
        // A wrapper Map that decodes fine but lacks `peer_event_node_type`.
        let mut m = BTreeMap::new();
        m.insert(
            "peer_event_content_canonical_bytes".to_string(),
            Value::Bytes(vec![0x01, 0x02]),
        );
        let content = cb_encode(&Value::Map(m)).expect("encode").as_ref().to_vec();
        let ty = "federation_received:cafe".to_string();
        let reject = validate_federation_inner(&ty, &content, 0)
            .expect_err("wrapper missing peer_event_node_type must be rejected");
        assert!(matches!(
            reject,
            FederationRecursionReject::MalformedWrapper { depth: 0, .. }
        ));
    }

    #[test]
    fn mixed_chain_safe_wrappers_then_banned_leaf_at_depth_2() {
        // 2 safe wrappers around a banned leaf → caught at depth 2.
        let (ty, content) = nest(2, banned_leaf());
        let reject = validate_federation_inner(&ty, &content, 0).expect_err("must reject");
        assert_eq!(
            reject,
            FederationRecursionReject::BannedInnerType {
                depth: 2,
                inner_node_type: "operator_pinned:victim".to_string(),
            },
        );
    }
}
