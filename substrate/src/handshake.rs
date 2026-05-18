//! Operator handshake primitives — extracted from `server.rs` (Phase B Step 3).
//!
//! Owns the `hello` request handler that completes the operator/substrate
//! M5-protocol handshake (session-secret intake, Python worker spawning,
//! optional M9 TOFU pin/verify of the operator's Ed25519 public key, and
//! event back-fill / replay across the M21 boundary) plus its M9 signature
//! verifier helper.
//!
//! Doctrine traceability:
//! - L1/SKIN §4.1 — operator handshake + envelope discipline.
//! - L1/HARD_RULES §1 — C2 handshake_pubkey_mismatch (TOFU/match).
//! - L1/HARD_RULES §1 — C2 downgrade protection (pinned-but-absent).

use std::collections::BTreeMap;

use myco_kernel_bridge::client::{BridgeClient, BridgeClientConfig};
use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
use myco_kernel_shared::crypto::verify_signature;

use crate::persistence::PinnedOperatorIdentity;
use crate::server::{
    backfill_dag_from_python_state, emit_substrate_event, hex_encode, replay_python_events_from_dag,
    save_dag_state, ServerState,
};
use crate::SubstrateError;

/// M5 handshake entry point: consume the operator's `hello`, optionally
/// TOFU-pin or match the operator's Ed25519 identity (M9+), spawn the
/// Python kernel/tropism worker, hydrate substrate-side state (M21+ DAG
/// replay vs. legacy gradient-disk path), and return `hello_ack`.
///
/// Errors:
/// - `SubstrateError::Handshake` if `hello` arrives after handshake is
///   complete, payload is missing `session_secret`, signature is invalid,
///   or pubkey downgrade is attempted against a pinned identity.
/// - `SubstrateError::Bridge` if the Python worker fails to spawn or
///   complete its own M5 handshake.
pub(crate) fn handle_hello(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    if state.handshake_complete {
        return Err(SubstrateError::Handshake(
            "hello received after handshake already complete".to_string(),
        ));
    }
    // Extract session_secret from payload.
    let secret = match request.payload.get("session_secret") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            arr
        }
        _ => {
            return Err(SubstrateError::Handshake(
                "hello payload missing 32-byte session_secret".to_string(),
            ))
        }
    };

    // M9: extract + verify operator identity. If the hello payload includes
    // operator_pubkey + hello_signature, verify the signature; then either
    // pin (first sight, TOFU) or match (subsequent sessions).
    //
    // For M5-M8 backward compatibility: if these fields are absent AND no
    // pubkey has been pinned, accept (legacy mode). If pinned but absent in
    // hello, REJECT (someone is trying to downgrade).
    let pubkey_present = request.payload.contains_key("operator_pubkey");
    let sig_present = request.payload.contains_key("hello_signature");
    let pinned_pre = state.pinned_operator_identity.clone();

    if pubkey_present && sig_present {
        verify_hello_signature_and_pin(state, &secret, request)?;
    } else if pinned_pre.is_some() {
        return Err(SubstrateError::Handshake(
            "hello missing operator_pubkey + hello_signature; substrate has a pinned operator identity (downgrade rejected; M9 L1/HARD_RULES C2)".to_string(),
        ));
    }
    // else: legacy mode (no pubkey pinned, no signature provided) — accept.

    state.session_secret = secret;

    // Spawn the Python worker. Use the same secret to keep the chain
    // simple (operator → substrate → python all keyed identically).
    let python_config = BridgeClientConfig {
        python_executable: std::env::var("MYCO_PYTHON_EXECUTABLE")
            .unwrap_or_else(|_| "python".to_string()),
        session_secret: Some(secret),
        extra_env: Vec::new(),
    };
    let mut python_client = BridgeClient::spawn_and_handshake(python_config)?;
    let python_version = python_client.hello_ack.python_version.clone();
    let kernel_tropism_version = python_client.hello_ack.kernel_tropism_version.clone();

    // M7 cold-resume: ask the Python worker to hydrate from disk.
    // M10: also pass the just-verified operator pubkey as the genesis owner
    // pubkey, so Python can initialize owner_keys.cb if no prior owner-key
    // history exists on disk. (For M10 minimum, operator == owner.)
    //
    // M21.3 P5 万物互联: post-M21 substrates use DAG-derived state. Rust
    // tells Python `skip_disk_load=true`; Python loads empty in-memory state;
    // Rust then replays DAG events to reconstruct Python's gradient view.
    let state_dir_str = state.state_dir.to_string_lossy().into_owned();
    let genesis_owner = state.pinned_operator_identity.as_ref().map(|p| p.pubkey);
    let derived = crate::derived_state::DerivedState::from_dag(&state.dag)
        .unwrap_or_else(|_| crate::derived_state::DerivedState::empty());
    let is_post_m21 = derived.is_post_m21_substrate();
    let (_hydrated_axis_count, _hydrated) = python_client.load_state_full(
        &state_dir_str,
        genesis_owner.as_ref(),
        /* skip_disk_load = */ is_post_m21,
    )?;

    // M21.3 P5 万物互联: two paths for state derivation.
    //
    // POST-M21 path (skip_disk_load=true): Python loaded empty; Rust replays
    // DAG events to reconstruct Python's gradient state in-memory.
    //
    // LEGACY path (skip_disk_load=false): Python loaded gradient.cb from disk;
    // Rust queries Python for the loaded schemas and BACK-FILLS missing DAG
    // events (axis_registered + axis_perturbed) so subsequent boots can use
    // the DAG-first path. This handles M9-M20 legacy substrates + M20-spawned
    // child substrates (which boot with state files but no DAG events).
    if is_post_m21 {
        replay_python_events_from_dag(&mut python_client, &state.dag)?;
    } else {
        // Legacy back-fill: query Python's loaded axes; emit DAG events for
        // each that's not yet recorded.
        backfill_dag_from_python_state(&mut python_client, state, &genesis_owner)?;
    }

    // M21.3: emit owner_key_initialized event if not already in DAG.
    // Back-fills for substrates that completed M9 TOFU before M21.3.
    let owner_key_initialized_present = state
        .dag
        .iter_in_insertion_order()
        .any(|n| n.node_type == crate::events::NODE_TYPE_OWNER_KEY_INITIALIZED);
    if !owner_key_initialized_present {
        if let Some(genesis_pk) = genesis_owner {
            let anchor_ts = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .ok()
                .map(|d| d.as_secs())
                .unwrap_or(0);
            let event_content = crate::events::encode_owner_key_initialized(&genesis_pk, anchor_ts);
            let parents = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            let cycle = state.manifest.cycle_counter;
            let _ = state.dag.insert_node(
                parents,
                crate::events::NODE_TYPE_OWNER_KEY_INITIALIZED.to_string(),
                cycle,
                event_content,
            );
            let _ = save_dag_state(state);
        }
    }

    state.python_client = Some(python_client);
    state.handshake_complete = true;

    // Persist the manifest now (creates manifest.cb on first boot; bumps
    // last_save_time on subsequent boots).
    state.save_manifest()?;

    // Build hello_ack with version info forwarded from the Python side
    // (so the operator runtime sees a unified view of the whole stack).
    let mut payload = BTreeMap::new();
    payload.insert(
        "kernel_tropism_version".to_string(),
        Value::String(kernel_tropism_version),
    );
    payload.insert("python_version".to_string(), Value::String(python_version));
    payload.insert(
        "substrate_version".to_string(),
        Value::String(env!("CARGO_PKG_VERSION").to_string()),
    );
    // M7: surface persistent substrate_id + cycle_counter to the operator runtime
    // so the LLM host can verify substrate identity continuity across sessions.
    payload.insert(
        "substrate_id".to_string(),
        Value::Bytes(state.manifest.substrate_id.to_vec()),
    );
    payload.insert(
        "persistent_cycle_counter".to_string(),
        Value::Uint(state.manifest.cycle_counter),
    );
    Ok(Some(Message::new(
        msg_type::HELLO_ACK,
        request.request_id,
        payload,
    )))
}

/// M9: Verify the hello message's Ed25519 signature and TOFU-pin or match
/// the operator's public key.
///
/// The signing input is the canonical-bytes encoding of a Map containing
/// {session_secret, operator_pubkey} (the hello_signature field is excluded
/// to avoid self-reference). Must match TS-side [`helloSigningBody`].
fn verify_hello_signature_and_pin(
    state: &mut ServerState,
    secret: &[u8; 32],
    request: &Message,
) -> Result<(), SubstrateError> {
    // Extract operator_pubkey.
    let pubkey_bytes = match request.payload.get("operator_pubkey") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            arr
        }
        _ => {
            return Err(SubstrateError::Handshake(
                "hello operator_pubkey must be 32 bytes".to_string(),
            ))
        }
    };

    // Extract hello_signature.
    let signature_bytes = match request.payload.get("hello_signature") {
        Some(Value::Bytes(b)) if b.len() == 64 => {
            let mut arr = [0u8; 64];
            arr.copy_from_slice(b);
            arr
        }
        _ => {
            return Err(SubstrateError::Handshake(
                "hello_signature must be 64 bytes".to_string(),
            ))
        }
    };

    // Reconstruct the signing body: canonical-bytes of {session_secret, operator_pubkey}.
    let mut signing_map = BTreeMap::new();
    signing_map.insert("session_secret".to_string(), Value::Bytes(secret.to_vec()));
    signing_map.insert(
        "operator_pubkey".to_string(),
        Value::Bytes(pubkey_bytes.to_vec()),
    );
    let signing_input = cb_encode(&Value::Map(signing_map))
        .map_err(|e| SubstrateError::Handshake(format!("hello signing-body encode: {e}")))?;

    // Verify the Ed25519 signature.
    verify_signature(&pubkey_bytes, &signature_bytes, signing_input.as_ref()).map_err(|e| {
        SubstrateError::Handshake(format!(
            "hello_signature verification failed (L1/HARD_RULES C2): {e}"
        ))
    })?;

    // TOFU or match.
    match &state.pinned_operator_identity {
        None => {
            // First sight — pin.
            // M21.4: do NOT write `operator_identity_pubkey.cb`. The pinned
            // identity is derived from the operator_pinned DAG event below.
            let pinned = PinnedOperatorIdentity::pin_now(pubkey_bytes);
            // M21.1 P5 万物互联: emit operator_pinned DAG event so the TOFU
            // pinning is recorded in the causal graph (now the authoritative
            // record, post-M21.4).
            let event_node_type = crate::events::operator_pinned_node_type(&pinned.pubkey);
            let event_content =
                crate::events::encode_operator_pinned(&pinned.pubkey, pinned.first_pinned_unix_ns);
            let _ = emit_substrate_event(state, event_node_type, event_content);
            let _ = save_dag_state(state);
            state.pinned_operator_identity = Some(pinned);
            Ok(())
        }
        Some(pinned) => {
            if pinned.pubkey == pubkey_bytes {
                Ok(())
            } else {
                Err(SubstrateError::Handshake(format!(
                    "operator pubkey mismatch: pinned {} vs presented {} (L1/HARD_RULES C2 handshake_pubkey_mismatch)",
                    hex_encode(&pinned.pubkey),
                    hex_encode(&pubkey_bytes)
                )))
            }
        }
    }
}
