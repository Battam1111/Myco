//! Operator handshake primitives — extracted from `server.rs` (Phase B Step 3).
//!
//! Owns the `hello` request handler that completes the operator/substrate
//! M5-protocol handshake (session-secret intake, Python worker spawning, and
//! event back-fill / replay across the M21 boundary) plus `hello_ack`.
//!
//! **v0.9 owner-key removal**: the M9 TOFU pin/verify of the operator's Ed25519
//! public key (and the strict-Ed25519 handshake gate, the operator_pinned
//! emission, and the owner_key_initialized genesis backfill) were removed along
//! with the rest of the anchor surface. The handshake is now keyless: any
//! operator presenting a valid session_secret completes it.
//!
//! Doctrine traceability:
//! - L1/SKIN §4.1 — operator handshake + envelope discipline.

use std::collections::BTreeMap;

use myco_kernel_bridge::client::{BridgeClient, BridgeClientConfig};
use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::Value;

use crate::server::{
    backfill_dag_from_python_state, replay_python_events_from_dag, ServerState,
};
use crate::SubstrateError;

/// M5 handshake entry point: consume the operator's `hello`, spawn the Python
/// kernel/tropism worker, hydrate substrate-side state (M21+ DAG replay vs.
/// legacy gradient-disk path), and return `hello_ack`.
///
/// **v0.9 keyless**: no operator-identity verification is performed; the only
/// requirement is a well-formed 32-byte `session_secret`.
///
/// Errors:
/// - `SubstrateError::Handshake` if `hello` arrives after handshake is
///   complete or the payload is missing `session_secret`.
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

    // (v0.9 owner-key removal: the M9 operator_pubkey / hello_signature TOFU
    // pin/verify + the strict-Ed25519 handshake gate were removed. Any
    // operator_pubkey / hello_signature fields in the payload are ignored.)

    state.session_secret = secret;

    // Spawn the Python worker. Use the same secret to keep the chain
    // simple (operator → substrate → python all keyed identically).
    let python_config = BridgeClientConfig {
        python_executable: std::env::var("MYCO_PYTHON_EXECUTABLE")
            .unwrap_or_else(|_| "python".to_string()),
        session_secret: Some(secret),
        extra_env: Vec::new(),
        // Sprint 6.E (T2.9): substrate-→-Python hellos don't carry an
        // operator identity (the substrate IS the operator from Python's
        // perspective; M5 protocol session_secret + HMAC handles auth).
        operator_signing_seed: None,
    };
    let mut python_client = BridgeClient::spawn_and_handshake(python_config)?;
    let python_version = python_client.hello_ack.python_version.clone();
    let kernel_tropism_version = python_client.hello_ack.kernel_tropism_version.clone();

    // M7 cold-resume: ask the Python worker to hydrate from disk.
    //
    // M21.3 P5 万物互联: post-M21 substrates use DAG-derived state. Rust
    // tells Python `skip_disk_load=true`; Python loads empty in-memory state;
    // Rust then replays DAG events to reconstruct Python's gradient view.
    //
    // **v0.9 keyless**: no genesis owner pubkey is passed to Python (the
    // owner-keys subsystem was removed); `load_state_full` receives `None`.
    let state_dir_str = state.state_dir.to_string_lossy().into_owned();
    let derived = crate::derived_state::DerivedState::from_dag(&state.dag)
        .unwrap_or_else(|_| crate::derived_state::DerivedState::empty());
    let is_post_m21 = derived.is_post_m21_substrate();
    let (_hydrated_axis_count, _hydrated) = python_client.load_state_full(
        &state_dir_str,
        None,
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
        // each that's not yet recorded. (No genesis owner in v0.9 keyless mode.)
        let no_genesis_owner: Option<[u8; 32]> = None;
        backfill_dag_from_python_state(&mut python_client, state, &no_genesis_owner)?;
    }

    state.python_client = Some(python_client);
    state.handshake_complete = true;

    // M21.4 / Task #8i: `save_manifest` is a no-op — substrate identity +
    // metabolic position are event-sourced via the DAG (and held in discrete
    // ServerState fields), not written to `manifest.cb`. Call retained for
    // call-site stability; it neither creates nor mutates any file.
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
        Value::Bytes(state.substrate_id().to_vec()),
    );
    payload.insert(
        "persistent_cycle_counter".to_string(),
        Value::Uint(state.cycle_counter()),
    );
    Ok(Some(Message::new(
        msg_type::HELLO_ACK,
        request.request_id,
        payload,
    )))
}
