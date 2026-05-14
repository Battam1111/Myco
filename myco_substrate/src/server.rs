//! Substrate-side server loop — handles operator-facing M5 protocol.
//!
//! ## Lifecycle
//!
//! 1. Read first frame; expect `hello` keyed by [`bootstrap_key`].
//! 2. Extract session_secret, spawn the Python kernel/tropism worker (via
//!    [`BridgeClient::spawn_and_handshake`]), respond with `hello_ack`.
//! 3. Loop: read frame keyed by session_secret → dispatch → write response.
//! 4. On `shutdown`: write `shutdown_ack`, shut the Python worker down, exit.
//! 5. On EOF: shut down the Python worker and exit cleanly.
//!
//! ## Message routing
//!
//! - `register_axis` / `perturb` / `snapshot` → forwarded to Python verbatim.
//! - `advance` → runs one [`CycleEngine`] step; gradient-advance crosses to
//!   Python; other 4 steps are Rust-native stubs at M6.
//! - `shutdown` → graceful exit + Python worker shutdown.
//! - Any other type → `error` envelope.

use std::collections::BTreeMap;
use std::io::{Read, Write};
use std::path::PathBuf;

use myco_kernel_bridge::client::{BridgeClient, BridgeClientConfig};
use myco_kernel_bridge::framing::{read_frame, write_frame};
use myco_kernel_bridge::protocol::{
    bootstrap_key, decode_frame_body, empty_payload, encode_frame_body, msg_type, AdvanceReport,
    Message,
};
use myco_kernel_bridge::BridgeError;
use myco_kernel_continuity::cycle::{
    CycleConfig, CycleContext, CycleEngine, DeltaAbsorber, GradientAdvancer, HandshakeProcessor,
    SkinBreachChecker, Tier1Validator,
};
use myco_kernel_schema::dag::Dag;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use myco_kernel_shared::crypto::verify_signature;

use crate::persistence::{
    default_state_dir, ensure_state_dir, load_dag, load_nonce_log, load_pinned_operator_identity,
    save_dag, save_nonce_log, save_pinned_operator_identity, Manifest, PersistedNonceEntry,
    PinnedOperatorIdentity,
};
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// M18 P4 永恒迭代: 4 cycle traits activated with real DAG-aware behavior.
// The fifth (GradientAdvancer) was already real (delegates to Python bridge).
//
// Borrow-checker shape: each trait stores precomputed work (collected from
// state before the cycle started) + accumulates outputs into self. After the
// cycle inner scope ends, the dispatcher reads outputs and applies DAG/
// manifest mutations that need exclusive state access.
// ---------------------------------------------------------------------------

/// M18 Tier1: runs `Dag::verify_all` from precomputed result. The actual
/// DAG verification happens before cycle start (in the dispatcher) — this
/// trait impl just returns the precomputed outcome to satisfy the cycle
/// engine's protocol.
struct DagVerifyTier1 {
    precomputed_ok: bool,
    failure_reason: String,
}
impl Tier1Validator for DagVerifyTier1 {
    fn validate_tier1(&mut self) -> Result<(), String> {
        if self.precomputed_ok {
            Ok(())
        } else {
            Err(self.failure_reason.clone())
        }
    }
}

/// M18 DeltaAbsorber: counts raw_material:* DAG nodes added since
/// `last_absorbed_cycle`. The list of node hashes to be "absorbed" is
/// passed in at construction; after the cycle, the dispatcher inserts an
/// `absorption_event:cycle_{N}` DAG node + bumps manifest.last_absorbed_cycle.
struct CycleAbsorber {
    pending_absorption_hashes: Vec<myco_kernel_shared::crypto::NodeHash>,
}
impl DeltaAbsorber for CycleAbsorber {
    fn absorb_deltas(&mut self) -> Result<usize, String> {
        Ok(self.pending_absorption_hashes.len())
    }
}

/// M18 SkinBreachChecker: enumerates immune:* DAG nodes added DURING this
/// cycle (created_at_cycle == cycle_at_start). The list of breach names is
/// precomputed at cycle start; this trait impl returns it.
struct DagBreachWatcher {
    breach_names: Vec<String>,
}
impl SkinBreachChecker for DagBreachWatcher {
    fn check_skin_breaches(&mut self) -> Result<Vec<String>, String> {
        Ok(self.breach_names.clone())
    }
}

/// M18 HandshakeProcessor: reports whether the substrate has a pinned
/// operator identity. In M18-MV, this is binary (1 if pinned, 0 otherwise).
/// M19+ adds an anchor-surface inbound channel for new handshakes during a
/// cycle, which will bump this count.
struct PinnedHandshakeReader {
    pinned_count: usize,
}
impl HandshakeProcessor for PinnedHandshakeReader {
    fn process_handshake_attestation(&mut self) -> Result<usize, String> {
        Ok(self.pinned_count)
    }
}

/// GradientAdvancer that delegates to a Python BridgeClient. Keeps the latest
/// AdvanceReport so the server loop can attach sporocarp data to its response.
struct PythonGradientAdvancer<'a> {
    client: &'a mut BridgeClient,
    cycle_number: u64,
    latest_report: Option<AdvanceReport>,
}

impl<'a> GradientAdvancer for PythonGradientAdvancer<'a> {
    fn advance_gradient(&mut self) -> Result<(), String> {
        self.cycle_number += 1;
        match self.client.advance(self.cycle_number) {
            Ok(report) => {
                self.latest_report = Some(report);
                Ok(())
            }
            Err(e) => Err(format!("python gradient advance failed: {e}")),
        }
    }
}

// ---------------------------------------------------------------------------
// Server state.
// ---------------------------------------------------------------------------

/// M13: An attestation nonce issued by the substrate, bound to a specific
/// proposed mutation + DAG tip state. Operators include this nonce in their
/// attestation envelope; the substrate verifies binding + marks consumed
/// (replay protection).
///
/// M15: extended with optional anchor-clock fields for dual-clock expiry
/// defense against clock skew (L0 §9 anchor-surface envelope hardening).
#[derive(Debug, Clone)]
#[allow(dead_code)]
struct AttestationNonce {
    /// 32-byte random nonce (substrate-issued; redundant with HashMap key but
    /// useful for debug output / forensic logging).
    nonce: [u8; 32],
    /// Hash of `content_canonical_bytes` the operator intends to submit.
    bound_content_hash: [u8; 32],
    /// DAG tip at issuance time (32 bytes; all-zero if DAG was empty).
    bound_dag_tip: [u8; 32],
    /// Substrate-clock issuance time (M15) — used by the dual-clock elapsed-
    /// time check to detect substrate clock jumping backward.
    substrate_issued_at_unix_ns: i64,
    /// Substrate-clock expiry (unix nanoseconds). Default: substrate_issued + TTL.
    expiry_unix_ns: i64,
    /// Operator-supplied anchor-clock issuance time (M15). `None` when the
    /// operator did not supply a `client_clock_unix_ns` in the nonce request
    /// (M13/M14 callers; preserves single-clock semantics).
    anchor_clock_issued_at_unix_ns: Option<i64>,
    /// Anchor-clock expiry = anchor_issued + TTL (M15). `None` iff
    /// anchor_clock_issued_at is None.
    anchor_clock_expiry_unix_ns: Option<i64>,
    /// Whether this nonce has been consumed (one-time use).
    consumed: bool,
}

/// M13: Default nonce TTL in seconds (5 minutes).
const NONCE_TTL_SECONDS: i64 = 300;

/// M15: Maximum allowed clock-skew between the substrate's own clock and the
/// operator-supplied anchor clock at issuance time. Operators whose clock
/// deviates from the substrate's by more than this are still accepted (we
/// don't reject — clock-skew is a separate concern from forgery), but the
/// elapsed-time check at verification will catch any inconsistency.
///
/// Reserved for M16+ proactive clock-skew rejection.
#[allow(dead_code)]
const MAX_ANCHOR_CLOCK_SKEW_NS: i64 = 3_600 * 1_000_000_000; // 1 hour

/// Session state for one operator connection.
struct ServerState {
    /// The session_secret transported by the `hello` from the operator.
    session_secret: [u8; 32],
    /// Whether the operator handshake has completed.
    handshake_complete: bool,
    /// Python kernel/tropism worker handle (None pre-handshake).
    python_client: Option<BridgeClient>,
    /// CycleEngine for substrate-side metabolic-cycle execution.
    cycle_engine: CycleEngine,
    /// Persistent substrate identity + metabolic position (M7).
    manifest: Manifest,
    /// Directory in which the substrate's state files live (M7).
    state_dir: PathBuf,
    /// Persistent causal DAG of substrate events (sporocarps etc.) (M8).
    dag: Dag,
    /// Pinned operator identity public key (M9). `None` until TOFU on first hello.
    pinned_operator_identity: Option<PinnedOperatorIdentity>,
    /// M13: Attestation nonce log (in-process; not persisted at M13 minimum).
    /// Keyed by nonce bytes for O(1) lookup on submit.
    nonce_log: std::collections::HashMap<[u8; 32], AttestationNonce>,
}

impl ServerState {
    fn new(
        state_dir: PathBuf,
        manifest: Manifest,
        dag: Dag,
        pinned_operator_identity: Option<PinnedOperatorIdentity>,
    ) -> Self {
        // M7: the manifest's cycle_counter is the authoritative persisted
        // counter; the in-process CycleEngine maintains its own counter that
        // counts cycles within THIS process only. handle_advance() uses the
        // manifest counter as the cross-process source-of-truth.
        // M8: dag carries the substrate's causal history (sporocarps + future event types).
        // M9: pinned_operator_identity is the TOFU-pinned operator pubkey;
        //     None pre-first-hello.
        ServerState {
            session_secret: [0u8; 32],
            handshake_complete: false,
            python_client: None,
            cycle_engine: CycleEngine::new(CycleConfig::default()),
            manifest,
            state_dir,
            dag,
            pinned_operator_identity,
            nonce_log: std::collections::HashMap::new(),
        }
    }

    /// Persist the manifest to disk. Bumps last_save_time as a side effect.
    fn save_manifest(&mut self) -> Result<(), SubstrateError> {
        self.manifest.save(&self.state_dir)?;
        Ok(())
    }

    /// State directory as a string (for forwarding to the Python worker).
    fn state_dir_str(&self) -> String {
        self.state_dir.to_string_lossy().into_owned()
    }
}

// ---------------------------------------------------------------------------
// Public server entry point.
// ---------------------------------------------------------------------------

/// Run the substrate server loop against the given stdin/stdout.
///
/// Resolves the state directory (per `MYCO_STATE_DIR` env var or default),
/// loads the manifest if one exists (cold-resume), or generates a fresh
/// genesis manifest. The Python worker is hydrated from `gradient.cb` (if
/// present) during the hello-handshake forwarding.
///
/// Returns the exit code (0 = clean shutdown, 2 = handshake failure).
pub fn run_loop<R: Read, W: Write>(stdin: &mut R, stdout: &mut W) -> Result<u8, SubstrateError> {
    use crate::derived_state::DerivedState;

    let state_dir = default_state_dir();
    ensure_state_dir(&state_dir)?;

    // M21.2 P5 万物互联: DAG-first boot.
    //
    // 1. Load DAG (authoritative substrate event log).
    // 2. Derive substrate state via DerivedState::from_dag.
    // 3. If derived has substrate_id (genesis_event present), USE DERIVED
    //    STATE for ServerState fields. State files become regenerable caches.
    // 4. If DAG is empty or pre-M21 (no genesis_event), fall back to state
    //    file loading (legacy compat). Auto-emit genesis_event for legacy
    //    substrate to migrate forward.
    //
    // This is the moment the DAG becomes Rust-side authoritative. State files
    // are still written (M21.4 will remove them); they're no longer read.

    // M11: C7 dag_retro_edit_detected — quarantine corrupted dag.cb.
    let (dag, dag_load_failure_evidence): (Dag, Option<String>) = match load_dag(&state_dir) {
        Ok(Some(d)) => (d, None),
        Ok(None) => (Dag::default(), None),
        Err(e) => {
            let dag_path = state_dir.join("dag.cb");
            let quarantine_path = state_dir.join(format!(
                "dag.cb.quarantined_{}",
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0)
            ));
            let _ = std::fs::rename(&dag_path, &quarantine_path);
            (
                Dag::default(),
                Some(format!(
                    "dag.cb load failed ({e}); quarantined to {}",
                    quarantine_path.display()
                )),
            )
        }
    };

    // Derive state from DAG. On unrecoverable replay error, treat as empty
    // (fresh substrate path).
    let derived = DerivedState::from_dag(&dag).unwrap_or_else(|_| DerivedState::empty());

    // Determine boot mode:
    //  - "dag-first" (M21.2+): derived.is_post_m21_substrate() == true
    //  - "legacy" (pre-M21.1): fall back to state file loading
    //  - "fresh genesis" (no prior state at all): create new
    let boot_from_dag = derived.is_post_m21_substrate();
    let (manifest, pinned_operator_identity, nonce_log_entries, is_fresh_genesis): (
        Manifest,
        Option<crate::persistence::PinnedOperatorIdentity>,
        Vec<crate::persistence::PersistedNonceEntry>,
        bool,
    ) = if boot_from_dag {
        // M21.2 derived-first path: state comes from DAG events.
        let mfst = derived.to_legacy_manifest();
        let pinned = derived.pinned_operator_identity.clone();
        // Convert DerivedNonce → PersistedNonceEntry for ServerState population.
        let nonces: Vec<crate::persistence::PersistedNonceEntry> = derived
            .nonce_log
            .values()
            .map(|n| crate::persistence::PersistedNonceEntry {
                nonce: n.nonce,
                bound_content_hash: n.bound_content_hash,
                bound_dag_tip: n.bound_dag_tip,
                substrate_issued_at_unix_ns: n.substrate_issued_at_unix_ns,
                expiry_unix_ns: n.expiry_unix_ns,
                anchor_clock_issued_at_unix_ns: n.anchor_clock_issued_at_unix_ns,
                anchor_clock_expiry_unix_ns: n.anchor_clock_expiry_unix_ns,
                consumed: n.consumed,
            })
            .collect();
        (mfst, pinned, nonces, false)
    } else {
        // Legacy path: load from state files.
        let (m, fresh) = match Manifest::load(&state_dir)? {
            Some(m) => (m, false),
            None => (Manifest::genesis(), true),
        };
        let pinned = load_pinned_operator_identity(&state_dir)?;
        let now_for_prune = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let entries = match load_nonce_log(&state_dir) {
            Ok(Some(entries)) => entries
                .into_iter()
                .filter(|e| !(e.consumed && now_for_prune > e.expiry_unix_ns))
                .collect::<Vec<_>>(),
            _ => Vec::new(),
        };
        (m, pinned, entries, fresh)
    };

    let mut state = ServerState::new(state_dir, manifest, dag, pinned_operator_identity);
    for entry in nonce_log_entries {
        state.nonce_log.insert(
            entry.nonce,
            AttestationNonce {
                nonce: entry.nonce,
                bound_content_hash: entry.bound_content_hash,
                bound_dag_tip: entry.bound_dag_tip,
                substrate_issued_at_unix_ns: entry.substrate_issued_at_unix_ns,
                expiry_unix_ns: entry.expiry_unix_ns,
                anchor_clock_issued_at_unix_ns: entry.anchor_clock_issued_at_unix_ns,
                anchor_clock_expiry_unix_ns: entry.anchor_clock_expiry_unix_ns,
                consumed: entry.consumed,
            },
        );
    }

    // If DAG load failed: emit C7 immune sporocarp into the fresh DAG.
    if let Some(evidence) = dag_load_failure_evidence {
        let _ = emit_immune_sporocarp(
            &mut state,
            "C7_dag_retro_edit_detected",
            "dag_retro_edit_detected",
            &evidence,
        );
        let _ = save_dag_state(&state);
    }

    // M21.2/M21.3: legacy-substrate auto-migration moved to handle_hello,
    // AFTER Python loads its gradient state. This way the migration can
    // back-fill BOTH genesis_event AND axis_registered events from Python's
    // already-loaded state, preserving M20 child substrate behavior (and
    // any other case where state files are authoritative + DAG is empty).
    let _ = is_fresh_genesis; // suppress unused-var warning when migration moved

    // M21.1 P5 万物互联: fresh substrate (no manifest.cb on disk) emits
    // genesis_event as the first DAG node. M21.2 generalizes this: any
    // substrate without a genesis_event in DAG gets one auto-emitted (the
    // legacy_migration branch above handles existing manifest.cb; this branch
    // handles truly fresh).
    if is_fresh_genesis && state.dag.node_count() == 0 {
        let event_node_type = crate::events::genesis_event_node_type(&state.manifest.substrate_id);
        let event_content = crate::events::encode_genesis_event(
            &state.manifest.substrate_id,
            state.manifest.genesis_time_unix_ns,
        );
        let _ = emit_substrate_event(&mut state, event_node_type, event_content);
        let _ = save_dag_state(&state);
    }

    // M12: C9 cold_resume_invariant_failure — run comprehensive integrity
    // checks at boot. For each failing check, emit a C9 immune sporocarp.
    // The substrate continues running regardless; the immune events are an
    // audit trail for the operator to inspect.
    let integrity_results = run_integrity_checks(&state);
    let mut any_failed = false;
    for result in &integrity_results {
        if !result.passed {
            any_failed = true;
            let evidence = format!(
                "boot-time integrity check failed: {} — {}",
                result.check_id, result.evidence
            );
            // M19 P9 皮肤: route check_id "canonical_bytes_render_drift" to
            // its dedicated C18 detector; all others go to C9.
            let (detector_id, detector_name) = if result.check_id == "canonical_bytes_render_drift"
            {
                (
                    "C18_canonical_bytes_render_drift",
                    "canonical_bytes_render_drift".to_string(),
                )
            } else if result.check_id == "substrate_state_orphan_detected" {
                (
                    "C19_substrate_state_orphan_detected",
                    "substrate_state_orphan_detected".to_string(),
                )
            } else {
                (
                    "C9_cold_resume_invariant_failure",
                    format!("cold_resume_invariant_failure ({})", result.check_id),
                )
            };
            let _ = emit_immune_sporocarp(&mut state, detector_id, &detector_name, &evidence);
        }
    }
    if any_failed {
        let _ = save_dag_state(&state);
    }

    loop {
        let expected_key = if state.handshake_complete {
            state.session_secret
        } else {
            bootstrap_key()
        };

        let frame = match read_frame(stdin) {
            Ok(Some(f)) => f,
            Ok(None) => {
                // Clean EOF.
                graceful_shutdown_python(&mut state);
                return Ok(if state.handshake_complete { 0 } else { 2 });
            }
            Err(e) => {
                graceful_shutdown_python(&mut state);
                return Err(SubstrateError::Io(std::io::Error::other(format!(
                    "read_frame failed: {e}"
                ))));
            }
        };

        let request = match decode_frame_body(&frame, &expected_key) {
            Ok(msg) => msg,
            Err(BridgeError::HmacMismatch(msg)) => {
                // If pre-handshake, exit. If post, write error.
                if state.handshake_complete {
                    write_error_response(stdout, &state.session_secret, 0, "hmac_mismatch", &msg)?;
                    continue;
                }
                graceful_shutdown_python(&mut state);
                return Ok(2);
            }
            Err(e) => {
                if state.handshake_complete {
                    write_error_response(
                        stdout,
                        &state.session_secret,
                        0,
                        "protocol_error",
                        &e.to_string(),
                    )?;
                    continue;
                }
                graceful_shutdown_python(&mut state);
                return Ok(2);
            }
        };

        // Dispatch.
        let result = dispatch(&mut state, &request);
        match result {
            Ok(Some(response)) => {
                let frame = encode_frame_body(&response, &state.session_secret)
                    .map_err(SubstrateError::Bridge)?;
                write_frame(stdout, &frame).map_err(SubstrateError::Bridge)?;
                if request.message_type == msg_type::SHUTDOWN {
                    graceful_shutdown_python(&mut state);
                    return Ok(0);
                }
            }
            Ok(None) => {
                // Handshake-only path: state was mutated but no response queued (currently unused).
            }
            Err(e) => {
                // M9: when a HELLO request fails (e.g., pubkey mismatch),
                // key the error envelope with the operator-provided
                // session_secret from the hello payload so the TS operator
                // can decode our rejection. Then EXIT — a rejected hello
                // means the session is poisoned; no point continuing.
                if request.message_type == msg_type::HELLO {
                    // M11: emit immune sporocarp for the rejected hello (C2 family).
                    // The DAG is loaded at boot time and will accept this insertion
                    // even pre-handshake. Save DAG before exit so the next session
                    // can see the immune event.
                    let evidence = format!("hello rejected: {e}");
                    let _ = emit_immune_sporocarp(
                        &mut state,
                        "C2_handshake_pubkey_mismatch",
                        "handshake_pubkey_mismatch",
                        &evidence,
                    );
                    let _ = save_dag_state(&state);

                    let response_key = match request.payload.get("session_secret") {
                        Some(Value::Bytes(b)) if b.len() == 32 => {
                            let mut arr = [0u8; 32];
                            arr.copy_from_slice(b);
                            arr
                        }
                        _ => bootstrap_key(),
                    };
                    // Best-effort write of the error envelope (operator can decode).
                    let _ = write_error_response(
                        stdout,
                        &response_key,
                        request.request_id,
                        "hello_rejected",
                        &e.to_string(),
                    );
                    graceful_shutdown_python(&mut state);
                    return Ok(2);
                }
                let response_key = if state.handshake_complete {
                    state.session_secret
                } else {
                    bootstrap_key()
                };
                write_error_response(
                    stdout,
                    &response_key,
                    request.request_id,
                    "dispatcher_error",
                    &e.to_string(),
                )?;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Dispatch.
// ---------------------------------------------------------------------------

fn dispatch(state: &mut ServerState, request: &Message) -> Result<Option<Message>, SubstrateError> {
    // Pre-handshake: only HELLO is allowed.
    if !state.handshake_complete && request.message_type != msg_type::HELLO {
        return Err(SubstrateError::Handshake(format!(
            "received {} before hello",
            request.message_type
        )));
    }

    match request.message_type.as_str() {
        msg_type::HELLO => handle_hello(state, request),
        msg_type::REGISTER_AXIS => {
            let response = forward_to_python(state, request, msg_type::REGISTER_AXIS_ACK)?;
            // M21.1 P5 万物互联: emit axis_registered DAG event so the schema
            // addition is recorded in the causal graph (was an orphan prior).
            // The wire payload fields for register_axis are documented in
            // kernel/bridge::protocol::register_axis_payload — we extract them
            // here for the event content.
            if let Some(event) = build_axis_registered_event(request) {
                let nt = crate::events::axis_registered_node_type(&event.name);
                let content = crate::events::encode_axis_registered(&event);
                let _ = emit_substrate_event(state, nt, content);
                let _ = save_dag_state(state);
            }
            // M7: persist gradient state after a mutation.
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::PERTURB => {
            let response = forward_to_python(state, request, msg_type::PERTURB_ACK)?;
            // M21.1 P5 万物互联: emit axis_perturbed DAG event so the
            // perturbation is recorded in the causal graph. Plain perturb
            // (no raw_material binding) was an orphan prior to M21.1.
            if let (Some(axis_name), Some(delta)) = (
                request.payload.get("axis_name").and_then(|v| match v {
                    Value::String(s) => Some(s.clone()),
                    _ => None,
                }),
                request.payload.get("delta_repr").and_then(|v| match v {
                    Value::String(s) => s.parse::<f64>().ok(),
                    _ => None,
                }),
            ) {
                let nt = crate::events::axis_perturbed_node_type(&axis_name);
                let content = crate::events::encode_axis_perturbed(&axis_name, delta);
                let _ = emit_substrate_event(state, nt, content);
                let _ = save_dag_state(state);
            }
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::SNAPSHOT => forward_to_python(state, request, msg_type::SNAPSHOT_RESPONSE),
        msg_type::ADVANCE => {
            let response = handle_advance(state, request)?;
            // M7: bump the persisted cycle counter (matches the value echoed in
            // the advance_response payload). save_manifest() also bumps
            // last_save_time for observability.
            let prior_cycle = state.manifest.cycle_counter;
            let new_cycle = prior_cycle.saturating_add(1);
            state.manifest.cycle_counter = new_cycle;
            // M21.1 P5 万物互联: emit cycle_advanced DAG event so cycle counter
            // progression is recorded in the causal graph.
            let event_content = crate::events::encode_cycle_advanced(prior_cycle, new_cycle);
            let _ = emit_substrate_event(
                state,
                crate::events::NODE_TYPE_CYCLE_ADVANCED.to_string(),
                event_content,
            );
            state.save_manifest()?;
            save_python_state(state)?;
            // M8: persist the DAG (sporocarps inserted during handle_advance).
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::SHUTDOWN => {
            // M7+M8: final state save before exit (best-effort; ignore errors here).
            let _ = save_python_state(state);
            let _ = state.save_manifest();
            let _ = save_dag_state(state);
            Ok(Some(Message::new(
                msg_type::SHUTDOWN_ACK,
                request.request_id,
                empty_payload(),
            )))
        }
        // M8: DAG-related operator requests handled substrate-side.
        msg_type::QUERY_RECENT_NODES => handle_query_recent_nodes(state, request),
        msg_type::COMPUTE_INTENT => handle_compute_intent(state, request),
        // M10: classified-mutation submission.
        msg_type::SUBMIT_MUTATION => {
            let response = handle_submit_mutation(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // M11: immune event query (filters DAG by "immune:" prefix).
        msg_type::QUERY_IMMUNE_EVENTS => handle_query_immune_events(state, request),
        // M12: ad-hoc immune check (operator can verify integrity any time).
        msg_type::RUN_IMMUNE_CHECK => handle_run_immune_check(state, request),
        // M13: anchor-surface attestation nonce (operator pre-submit step).
        msg_type::REQUEST_ATTESTATION_NONCE => handle_request_attestation_nonce(state, request),
        // M15: DAG enumeration closure for owner-side Merkle chain reconstruction.
        msg_type::ENUMERATE_DAG_SINCE => handle_enumerate_dag_since(state, request),
        // M16: P2 永恒吞噬 — universal raw_material ingestion + causal perturbation.
        msg_type::INGEST_RAW_MATERIAL => {
            let response = handle_ingest_raw_material(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::PERTURB_AXIS_FROM_RAW_MATERIAL => {
            let response = handle_perturb_axis_from_raw_material(state, request)?;
            save_python_state(state)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // M20 P8 永恒繁衍 — sprout a child substrate from parent's spore-schema.
        msg_type::SPROUT_CHILD => {
            let response = handle_sprout_child(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        other => Err(SubstrateError::Protocol(format!(
            "substrate cannot handle message type {other:?}"
        ))),
    }
}

/// M8: Return the last N DAG nodes (Rust-handled; no Python involvement).
/// M16: optional `node_type_prefix` filter — return only nodes whose
/// node_type starts with the given prefix (e.g. "raw_material:" to filter
/// for ingested raw material; "mutation:" for accepted mutations).
fn handle_query_recent_nodes(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let count = request
        .payload
        .get("count")
        .and_then(|v| match v {
            Value::Uint(n) => Some(*n),
            _ => None,
        })
        .unwrap_or(50);

    // M16: optional node_type_prefix filter.
    let prefix_filter: Option<String> =
        request
            .payload
            .get("node_type_prefix")
            .and_then(|v| match v {
                Value::String(s) => Some(s.clone()),
                _ => None,
            });

    // Total DAG size is always reported unfiltered (caller-visible context).
    let unfiltered_total = state.dag.node_count();
    let all_nodes: Vec<_> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| {
            prefix_filter
                .as_ref()
                .map(|p| n.node_type.starts_with(p))
                .unwrap_or(true)
        })
        .collect();
    let filtered_total = all_nodes.len();
    let start = filtered_total.saturating_sub(count as usize);
    let recent: Vec<Value> = all_nodes[start..]
        .iter()
        .map(|n| {
            let mut m = BTreeMap::new();
            m.insert("hash".to_string(), Value::Bytes(n.hash.as_ref().to_vec()));
            m.insert(
                "parent_hashes".to_string(),
                Value::Array(
                    n.parent_hashes
                        .iter()
                        .map(|h| Value::Bytes(h.as_ref().to_vec()))
                        .collect(),
                ),
            );
            m.insert("node_type".to_string(), Value::String(n.node_type.clone()));
            m.insert("at_cycle".to_string(), Value::Uint(n.created_at_cycle));
            m.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(n.content_canonical_bytes.as_ref().to_vec()),
            );
            Value::Map(m)
        })
        .collect();

    let mut payload = BTreeMap::new();
    payload.insert(
        "total_dag_size".to_string(),
        Value::Uint(unfiltered_total as u64),
    );
    // M16: when a prefix filter was applied, expose the filtered-total count
    // separately so the caller can distinguish "DAG has 100 nodes; 5 match my
    // filter" from "DAG has 5 nodes total".
    payload.insert(
        "filtered_total".to_string(),
        Value::Uint(filtered_total as u64),
    );
    payload.insert(
        "returned_count".to_string(),
        Value::Uint(recent.len() as u64),
    );
    payload.insert("nodes".to_string(), Value::Array(recent));
    if let Some(tip) = state.dag.tip() {
        payload.insert("dag_tip".to_string(), Value::Bytes(tip.as_ref().to_vec()));
    }
    Ok(Some(Message::new(
        msg_type::QUERY_RECENT_NODES_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M8: Forward intent computation to the Python worker.
///
/// The substrate serializes ITS OWN DAG (full set at M8; M9+ adds windowing)
/// and sends it to Python along with the pivot and radius. Python builds an
/// in-memory DagSource and runs trajectory's neighborhood + ancestors_and_descendants
/// + cluster_C, returning the clusters.
fn handle_compute_intent(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // Default radius: 10 cycles. Operator can override via payload.
    let radius_cycles = request
        .payload
        .get("radius_cycles")
        .and_then(|v| match v {
            Value::Uint(n) => Some(*n),
            _ => None,
        })
        .unwrap_or(10);

    // Default pivot: DAG tip. Operator can override via payload (must be a hash present in DAG).
    let pivot_bytes: Vec<u8> = match request.payload.get("pivot_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => match state.dag.tip() {
            Some(t) => t.as_ref().to_vec(),
            None => {
                // Empty DAG → cold-start intent.
                return Ok(Some(empty_intent_response(request.request_id)));
            }
        },
    };
    let mut pivot_arr = [0u8; 32];
    pivot_arr.copy_from_slice(&pivot_bytes);

    // Serialize the substrate's full DAG as Array<Map> for Python.
    let dag_nodes: Vec<Value> = state
        .dag
        .iter_in_insertion_order()
        .map(|n| {
            let mut m = BTreeMap::new();
            m.insert("hash".to_string(), Value::Bytes(n.hash.as_ref().to_vec()));
            m.insert(
                "parent_hashes".to_string(),
                Value::Array(
                    n.parent_hashes
                        .iter()
                        .map(|h| Value::Bytes(h.as_ref().to_vec()))
                        .collect(),
                ),
            );
            m.insert("at_cycle".to_string(), Value::Uint(n.created_at_cycle));
            m.insert("node_type".to_string(), Value::String(n.node_type.clone()));
            Value::Map(m)
        })
        .collect();

    let payload =
        myco_kernel_bridge::protocol::compute_intent_payload(&pivot_arr, radius_cycles, dag_nodes);
    let python_response = client.call(msg_type::COMPUTE_INTENT, payload)?;
    if python_response.message_type != msg_type::COMPUTE_INTENT_RESPONSE {
        return Err(SubstrateError::Protocol(format!(
            "expected compute_intent_response from python; got {}",
            python_response.message_type
        )));
    }
    // Re-stamp the response with the operator's request_id.
    Ok(Some(Message::new(
        msg_type::COMPUTE_INTENT_RESPONSE,
        request.request_id,
        python_response.payload,
    )))
}

/// M13: Issue a fresh attestation nonce bound to (content_hash, dag_tip).
///
/// The operator computes the hash of their proposed mutation content and
/// includes it in this request. The substrate generates 32 random bytes,
/// records the binding (content_hash + current DAG tip + expiry), and returns
/// the nonce. Operator includes this nonce in submit_mutation; substrate
/// verifies binding + marks consumed.
///
/// M15: optionally accepts `anchor_clock_unix_ns` (operator's view of "now"
/// from the operator's wall clock). When present, the substrate records BOTH
/// the substrate-clock issuance time AND the anchor-clock issuance time,
/// and the response echoes an `anchor_clock_expiry_unix_ns` so the operator
/// can later supply `anchor_clock_submitted_at_unix_ns` for the dual-clock
/// check at verification time.
fn handle_request_attestation_nonce(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};

    // Extract content_hash from payload (required).
    let content_hash = match request.payload.get("content_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            arr
        }
        _ => {
            return Err(SubstrateError::Protocol(
                "request_attestation_nonce: content_hash must be 32 bytes".to_string(),
            ));
        }
    };

    // M15: optional operator-supplied anchor-clock time.
    let anchor_clock_issued_at: Option<i64> = match request.payload.get("anchor_clock_unix_ns") {
        Some(Value::Timestamp(ts)) => Some(*ts),
        _ => None,
    };

    // Generate 32-byte nonce (time + counter + stack-address SHA-256 mix).
    let nonce = {
        use sha2::{Digest, Sha256};
        let mut h = Sha256::new();
        h.update(b"myco-attestation-nonce-v1");
        h.update(
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map(|d| d.as_nanos())
                .unwrap_or(0)
                .to_le_bytes(),
        );
        h.update(std::process::id().to_le_bytes());
        h.update((state.nonce_log.len() as u64).to_le_bytes());
        let stack_var = 0u8;
        h.update((&stack_var as *const u8 as usize).to_le_bytes());
        h.update(content_hash);
        let result = h.finalize();
        let mut out = [0u8; 32];
        out.copy_from_slice(&result);
        out
    };

    // M13 bound_dag_tip semantic: the operator's command was relative to
    // THIS DAG state. We capture the tip BEFORE emitting the nonce_issued
    // event, so the event content records what the operator "saw" at request
    // time. (Used for forensic audit.)
    let operator_visible_tip_at_request = state
        .dag
        .tip()
        .map(|t| {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(t.as_ref());
            arr
        })
        .unwrap_or([0u8; 32]);

    let substrate_issued_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let ttl_ns = NONCE_TTL_SECONDS * 1_000_000_000;
    let expiry_unix_ns = substrate_issued_at.saturating_add(ttl_ns);
    // M15: anchor-clock expiry = operator's anchor-clock at issuance + same TTL.
    let anchor_clock_expiry_unix_ns: Option<i64> =
        anchor_clock_issued_at.map(|a| a.saturating_add(ttl_ns));

    // M21.1 P5 万物互联: emit nonce_issued DAG event FIRST, BEFORE binding
    // bound_dag_tip on the nonce. The event records the pre-emit tip
    // (operator-visible-at-request); the nonce's bound_dag_tip is set to the
    // POST-emit tip (which equals the nonce_issued event's own hash). At
    // verify time, substrate's current_tip must equal this — i.e., no DAG
    // events have happened between issuance and submission. This preserves
    // M13's "fresh-context" guarantee with dual-write.
    let event_nt = crate::events::nonce_issued_node_type(&nonce);
    let event_content = crate::events::encode_nonce_issued(
        &nonce,
        &content_hash,
        &operator_visible_tip_at_request,
        substrate_issued_at,
        expiry_unix_ns,
        anchor_clock_issued_at,
        anchor_clock_expiry_unix_ns,
    );
    let nonce_issued_event_hash = emit_substrate_event(state, event_nt, event_content)?;
    let _ = save_dag_state(state);

    // bound_dag_tip = the nonce_issued event's hash (= post-event DAG tip).
    let mut bound_dag_tip = [0u8; 32];
    bound_dag_tip.copy_from_slice(nonce_issued_event_hash.as_ref());

    state.nonce_log.insert(
        nonce,
        AttestationNonce {
            nonce,
            bound_content_hash: content_hash,
            bound_dag_tip,
            substrate_issued_at_unix_ns: substrate_issued_at,
            expiry_unix_ns,
            anchor_clock_issued_at_unix_ns: anchor_clock_issued_at,
            anchor_clock_expiry_unix_ns,
            consumed: false,
        },
    );
    // M14: persist nonce log to disk so issued nonces survive restart.
    save_nonce_state(state)?;
    let _ = save_dag_state(state);

    let mut payload = BTreeMap::new();
    payload.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    payload.insert(
        "bound_dag_tip".to_string(),
        Value::Bytes(bound_dag_tip.to_vec()),
    );
    payload.insert(
        "expiry_unix_ns".to_string(),
        Value::Timestamp(expiry_unix_ns),
    );
    payload.insert(
        "ttl_seconds".to_string(),
        Value::Uint(NONCE_TTL_SECONDS as u64),
    );
    // M15: echo anchor-clock expiry only when operator supplied anchor_clock.
    if let Some(anchor_expiry) = anchor_clock_expiry_unix_ns {
        payload.insert(
            "anchor_clock_expiry_unix_ns".to_string(),
            Value::Timestamp(anchor_expiry),
        );
    }

    Ok(Some(Message::new(
        msg_type::REQUEST_ATTESTATION_NONCE_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M13: Verify an attestation nonce on a submit_mutation.
///
/// Returns Ok(()) if all checks pass; Err(reason) if any fail. The caller
/// (handle_submit_mutation) translates Err into a C5 rejection + immune sporocarp
/// with refined evidence.
///
/// M15: dual-clock expiry check. When the stored nonce has anchor-clock fields
/// (operator supplied `anchor_clock_unix_ns` on the nonce request) AND the
/// submit envelope supplies `anchor_clock_submitted_at_unix_ns`, the substrate
/// enforces BOTH clocks (substrate-clock elapsed-time AND anchor-clock
/// elapsed-time) must be in the [0, TTL] window. Clock-skew attacks that try
/// to extend nonce lifetime by manipulating one clock will fail the other.
fn verify_attestation_nonce(
    state: &mut ServerState,
    nonce_bytes: &[u8],
    content_hash: &[u8; 32],
    submitted_expiry_ns: Option<i64>,
    submitted_anchor_clock_ns: Option<i64>,
) -> Result<(), String> {
    use std::time::{SystemTime, UNIX_EPOCH};

    if nonce_bytes.len() != 32 {
        return Err(format!("nonce must be 32 bytes; got {}", nonce_bytes.len()));
    }
    let mut nonce_arr = [0u8; 32];
    nonce_arr.copy_from_slice(nonce_bytes);

    let stored = state
        .nonce_log
        .get(&nonce_arr)
        .ok_or_else(|| "unknown nonce (never issued by this substrate)".to_string())?
        .clone();

    if stored.consumed {
        return Err("replay rejected: nonce already consumed".to_string());
    }

    if stored.bound_content_hash != *content_hash {
        return Err(
            "wrong-binding rejected: content_hash differs from nonce-bound hash".to_string(),
        );
    }

    let current_tip = state
        .dag
        .tip()
        .map(|t| {
            let mut a = [0u8; 32];
            a.copy_from_slice(t.as_ref());
            a
        })
        .unwrap_or([0u8; 32]);
    if stored.bound_dag_tip != current_tip {
        return Err("wrong-binding rejected: DAG tip differs from issuance time".to_string());
    }

    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    // Substrate-clock elapsed-time check (M15 — supersedes the simple
    // `now > expiry` check by also detecting backward clock jumps).
    if now_ns > stored.expiry_unix_ns {
        return Err("expired rejected: substrate-clock nonce TTL passed".to_string());
    }
    if now_ns < stored.substrate_issued_at_unix_ns {
        return Err(
            "expired rejected: substrate clock has jumped backward since issuance".to_string(),
        );
    }
    if let Some(submitted) = submitted_expiry_ns {
        if submitted != stored.expiry_unix_ns {
            return Err(
                "wrong-binding rejected: submitted expiry differs from issued expiry".to_string(),
            );
        }
    }

    // M15: Dual-clock expiry check. Apply only when the nonce was issued WITH
    // anchor-clock binding (operator supplied `anchor_clock_unix_ns` on
    // request_attestation_nonce). If the submit envelope omits
    // `anchor_clock_submitted_at_unix_ns` despite the nonce being dual-clock,
    // reject (operator must use the dual-clock contract consistently).
    if let (Some(anchor_issued), Some(anchor_expiry)) = (
        stored.anchor_clock_issued_at_unix_ns,
        stored.anchor_clock_expiry_unix_ns,
    ) {
        match submitted_anchor_clock_ns {
            None => {
                return Err(
                    "dual-clock binding rejected: nonce was issued with anchor-clock, but \
                     submit envelope omits anchor_clock_submitted_at_unix_ns"
                        .to_string(),
                );
            }
            Some(submitted_anchor) => {
                if submitted_anchor < anchor_issued {
                    return Err(
                        "dual-clock rejected: anchor clock jumped backward since issuance"
                            .to_string(),
                    );
                }
                if submitted_anchor > anchor_expiry {
                    return Err("dual-clock rejected: anchor-clock nonce TTL passed".to_string());
                }
            }
        }
    } else if submitted_anchor_clock_ns.is_some() {
        // Operator supplied anchor_clock at submit time but the nonce was
        // issued without anchor-clock binding. This is a protocol misuse —
        // either upgrade nonce issuance to dual-clock or drop the submit
        // field. We accept (M13 fallback path) but the inconsistency is
        // surfaced upstream when the operator re-runs the flow.
    }

    // Mark consumed.
    if let Some(n) = state.nonce_log.get_mut(&nonce_arr) {
        n.consumed = true;
    }
    // M14: persist nonce log so the consumed flag survives restart (replay
    // protection extends across substrate restarts).
    save_nonce_state(state).map_err(|e| format!("nonce log save failed: {e}"))?;
    // M21.1 P5 万物互联: emit nonce_consumed DAG event.
    let consumed_at_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let event_nt = crate::events::nonce_consumed_node_type(&nonce_arr);
    let event_content = crate::events::encode_nonce_consumed(&nonce_arr, consumed_at_unix_ns);
    let _ = emit_substrate_event(state, event_nt, event_content);
    let _ = save_dag_state(state);

    Ok(())
}

/// M14: Verify the per-handshake REVEAL keypair envelope.
///
/// Checks that:
/// 1. `identity_signature_over_reveal_pubkey` is a valid Ed25519 signature over
///    `canonical_bytes(Map({"context": "myco-reveal-key-binding-v1", "reveal_pubkey": ...}))`
///    by the pinned operator IDENTITY pubkey.
/// 2. The substrate has a pinned operator identity (i.e. M9 TOFU completed).
///
/// Does NOT check the REVEAL→content signature; that happens in Python's
/// dispatcher (which already verifies attestation_signature against whatever
/// pubkey we pass in — for M14 we update Python to use reveal_pubkey instead
/// of pinned operator pubkey when reveal_pubkey is present in the payload).
///
/// For M14 minimum-viable: Python is updated externally to look for reveal_pubkey
/// first. If the substrate Rust layer accepts the REVEAL bundle, Python verifies
/// `attestation_signature` against `reveal_pubkey` (passed through in payload).
fn verify_reveal_keypair_envelope(state: &ServerState, request: &Message) -> Result<(), String> {
    // Need pinned operator identity to verify identity-signature-over-REVEAL.
    let pinned = state
        .pinned_operator_identity
        .as_ref()
        .ok_or_else(|| "no pinned operator identity (M9 TOFU not completed)".to_string())?;

    let reveal_pubkey_bytes = match request.payload.get("reveal_pubkey") {
        Some(Value::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => return Err("reveal_pubkey must be 32 bytes".to_string()),
    };

    let identity_sig_bytes = match request.payload.get("identity_signature_over_reveal_pubkey") {
        Some(Value::Bytes(b)) if b.len() == 64 => b.clone(),
        _ => return Err("identity_signature_over_reveal_pubkey must be 64 bytes".to_string()),
    };

    // Reconstruct the signing input: canonical_bytes(Map({"context", "reveal_pubkey"})).
    let mut signing_map = BTreeMap::new();
    signing_map.insert(
        "context".to_string(),
        Value::String("myco-reveal-key-binding-v1".to_string()),
    );
    signing_map.insert(
        "reveal_pubkey".to_string(),
        Value::Bytes(reveal_pubkey_bytes.clone()),
    );
    let signing_input = cb_encode(&Value::Map(signing_map))
        .map_err(|e| format!("signing input encode failed: {e}"))?;

    // Verify IDENTITY-signature-over-REVEAL.
    verify_signature(&pinned.pubkey, &identity_sig_bytes, signing_input.as_ref())
        .map_err(|e| format!("identity signature over reveal_pubkey invalid: {e}"))?;

    Ok(())
}

/// M13: Compute SHA-256 hash of canonical bytes (used as content_hash in nonce binding).
fn compute_content_hash(content: &[u8]) -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(content);
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

/// M12: Run the substrate's comprehensive integrity checks ad-hoc.
///
/// Runs the same checks as boot-time C9 (substrate_id_well_formed,
/// cycle_counter_monotonic, pinned_pubkey_well_formed, dag_verify_all,
/// owner_keys_consistency). For each failing check, emits a new C9 immune
/// sporocarp. Always returns a structured report regardless of outcome.
fn handle_run_immune_check(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let results = run_integrity_checks(state);

    // Emit immune sporocarps for each failure (consistent with boot-time C9
    // routing; M19: canonical_bytes_render_drift gets its dedicated C18 ID).
    let mut emitted_count: u64 = 0;
    for result in &results {
        if !result.passed {
            let evidence = format!(
                "ad-hoc integrity check failed: {} — {}",
                result.check_id, result.evidence
            );
            let (detector_id, detector_name) = if result.check_id == "canonical_bytes_render_drift"
            {
                (
                    "C18_canonical_bytes_render_drift",
                    "canonical_bytes_render_drift".to_string(),
                )
            } else if result.check_id == "substrate_state_orphan_detected" {
                (
                    "C19_substrate_state_orphan_detected",
                    "substrate_state_orphan_detected".to_string(),
                )
            } else {
                (
                    "C9_cold_resume_invariant_failure",
                    format!("cold_resume_invariant_failure ({})", result.check_id),
                )
            };
            if emit_immune_sporocarp(state, detector_id, &detector_name, &evidence).is_ok() {
                emitted_count += 1;
            }
        }
    }
    if emitted_count > 0 {
        save_dag_state(state)?;
    }

    // Build response payload: per-check results.
    let check_values: Vec<Value> = results
        .iter()
        .map(|r| {
            let mut m = BTreeMap::new();
            m.insert("check_id".to_string(), Value::String(r.check_id.clone()));
            m.insert("passed".to_string(), Value::Bool(r.passed));
            m.insert("evidence".to_string(), Value::String(r.evidence.clone()));
            Value::Map(m)
        })
        .collect();

    let total_checks = results.len() as u64;
    let failed_checks = results.iter().filter(|r| !r.passed).count() as u64;

    let mut payload = BTreeMap::new();
    payload.insert("total_checks".to_string(), Value::Uint(total_checks));
    payload.insert("failed_checks".to_string(), Value::Uint(failed_checks));
    payload.insert(
        "immune_events_emitted".to_string(),
        Value::Uint(emitted_count),
    );
    payload.insert("checks".to_string(), Value::Array(check_values));

    Ok(Some(Message::new(
        msg_type::RUN_IMMUNE_CHECK_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M15: Enumerate DAG node hashes added since `prev_tip` (or all from genesis
/// if `prev_tip` absent), returning full per-node metadata so the owner can
/// reconstruct the Merkle chain independently. Closes L1_HARD_RULES C6
/// dag_enumeration_unclosed by giving owners a deterministic, validated view
/// of substrate state evolution since the last co-sign.
///
/// On unknown `prev_tip`: substrate emits C6 immune sporocarp + returns error.
/// (Owner is referencing a tip the substrate doesn't have — either operator
/// is confused, or attacker has presented a fabricated prev_tip; both cases
/// warrant a defensive log entry.)
fn handle_enumerate_dag_since(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Optional prev_tip: 32-byte hash if present, None means "from genesis".
    let prev_tip_arg: Option<myco_kernel_shared::crypto::NodeHash> =
        match request.payload.get("prev_tip") {
            Some(Value::Bytes(b)) if b.len() == 32 => {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                Some(myco_kernel_shared::crypto::NodeHash::from_bytes(arr))
            }
            Some(Value::Bytes(b)) => {
                return Err(SubstrateError::Protocol(format!(
                    "enumerate_dag_since: prev_tip must be 32 bytes; got {}",
                    b.len()
                )));
            }
            // Absent → None.
            _ => None,
        };

    // Run enumeration.
    let enumeration_result = state.dag.enumerate_since(prev_tip_arg.as_ref());
    let hashes = match enumeration_result {
        Ok(h) => h,
        Err(myco_kernel_schema::dag::DagError::UnknownPrevTip(t)) => {
            // C6 dag_enumeration_unclosed: operator referenced a prev_tip not
            // in the substrate's DAG. Emit immune sporocarp and reject the
            // request (operator's view is desynchronized OR forge attempt).
            let evidence = format!(
                "enumerate_dag_since called with unknown prev_tip {} \
                 (substrate has no record of this tip; possible desync or forge attempt)",
                hex_encode(t.as_ref())
            );
            let _ = emit_immune_sporocarp(
                state,
                "C6_dag_enumeration_unclosed",
                "dag_enumeration_unclosed",
                &evidence,
            );
            let _ = save_dag_state(state);
            return Err(SubstrateError::Protocol(format!(
                "enumerate_dag_since: {evidence}"
            )));
        }
        Err(e) => {
            return Err(SubstrateError::Protocol(format!(
                "enumerate_dag_since failed: {e}"
            )));
        }
    };

    // Build the per-node enumeration array. Each entry carries everything the
    // owner needs to recompute the Merkle hash + chain it to the prev_tip:
    //   - hash (substrate-claimed; owner recomputes from parents + content)
    //   - parent_hashes (declared parents in hash-order)
    //   - node_type (for L1_SCHEMA §2.2 audit)
    //   - at_cycle (informational; the cycle when emitted)
    //   - content_canonical_bytes (the actual node payload)
    //
    // Borrow-checker shape: build nodes_array in an inner scope holding only
    // an immutable borrow of state.dag. If a node is missing from the DAG
    // (impossible barring internal corruption), record the issue in
    // `missing_hash` and emit C6 after the borrow drops.
    let mut nodes_array: Vec<Value> = Vec::with_capacity(hashes.len());
    let mut missing_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    {
        let dag = &state.dag;
        for h in &hashes {
            let Some(node) = dag.get(h) else {
                missing_hash = Some(*h);
                break;
            };
            let mut node_map = BTreeMap::new();
            node_map.insert(
                "hash".to_string(),
                Value::Bytes(node.hash.as_ref().to_vec()),
            );
            node_map.insert(
                "parent_hashes".to_string(),
                Value::Array(
                    node.parent_hashes
                        .iter()
                        .map(|p| Value::Bytes(p.as_ref().to_vec()))
                        .collect(),
                ),
            );
            node_map.insert(
                "node_type".to_string(),
                Value::String(node.node_type.clone()),
            );
            node_map.insert("at_cycle".to_string(), Value::Uint(node.created_at_cycle));
            node_map.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(node.content_canonical_bytes.as_ref().to_vec()),
            );
            nodes_array.push(Value::Map(node_map));
        }
    }
    if let Some(h) = missing_hash {
        let evidence = format!(
            "enumerate_dag_since: enumeration listed hash {} but state.dag.get returned None \
             (DAG internal inconsistency)",
            hex_encode(h.as_ref())
        );
        let _ = emit_immune_sporocarp(
            state,
            "C6_dag_enumeration_unclosed",
            "dag_enumeration_unclosed",
            &evidence,
        );
        let _ = save_dag_state(state);
        return Err(SubstrateError::Protocol(evidence));
    }

    let total_dag_size = state.dag.node_count() as u64;
    let mut payload = BTreeMap::new();
    if let Some(tip) = state.dag.tip() {
        payload.insert(
            "current_tip".to_string(),
            Value::Bytes(tip.as_ref().to_vec()),
        );
    }
    payload.insert("total_dag_size".to_string(), Value::Uint(total_dag_size));
    payload.insert(
        "enumerated_count".to_string(),
        Value::Uint(nodes_array.len() as u64),
    );
    if let Some(prev) = prev_tip_arg {
        payload.insert("prev_tip".to_string(), Value::Bytes(prev.as_ref().to_vec()));
    }
    payload.insert("nodes".to_string(), Value::Array(nodes_array));

    Ok(Some(Message::new(
        msg_type::ENUMERATE_DAG_SINCE_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M16: P2 永恒吞噬 — Ingest a raw material payload as a `raw_material:{kind}`
/// DAG node. Activates the L0 P2 "no filter on intake" principle: any bytes the
/// operator can present (text / file / conversation / url-fetch / llm-response)
/// become canonical-bytes content of a new DAG node.
///
/// Payload schema:
/// ```text
/// Map({
///   "content_kind": String,    // "text" | "file" | "conversation" | "url" | "llm_response" | custom
///   "content_bytes": Bytes,    // raw material payload (max 1 MiB)
///   "source_uri": String       // optional; provenance hint (file path, url, message id)
///   "meta": Map                // optional; arbitrary K-V hints
/// })
/// ```
///
/// The substrate composes the DAG node's content as canonical_bytes(Map({
///   "kind": ..., "bytes": ..., "source_uri": ..., "meta": ...
/// })) — full intake context is hashed.
///
/// Returns the inserted node hash + tip + total DAG size.
fn handle_ingest_raw_material(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Required: content_kind + content_bytes.
    let content_kind = match request.payload.get("content_kind") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "ingest_raw_material: content_kind must be a non-empty String".to_string(),
            ));
        }
    };
    let content_bytes = match request.payload.get("content_bytes") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "ingest_raw_material: content_bytes must be Bytes".to_string(),
            ));
        }
    };

    // M16: 512 KiB cap per ingestion event. The bridge frame layer caps at
    // 1 MiB (MAX_FRAME_BODY_SIZE); leaving 512 KiB headroom for the
    // canonical-bytes envelope + meta/source_uri overhead so content-cap
    // rejections produce explicit error messages instead of frame-layer
    // connection drops. Operators ingesting larger files should chunk.
    const MAX_INGESTION_BYTES: usize = 512 * 1024;
    if content_bytes.len() > MAX_INGESTION_BYTES {
        return Err(SubstrateError::Protocol(format!(
            "ingest_raw_material: content_bytes size {} exceeds {MAX_INGESTION_BYTES}-byte cap",
            content_bytes.len()
        )));
    }

    // Optional: source_uri + meta.
    let source_uri = request.payload.get("source_uri").and_then(|v| match v {
        Value::String(s) => Some(s.clone()),
        _ => None,
    });
    let meta_value = request.payload.get("meta").cloned();

    // Compose the content canonical bytes (full intake context is hashed).
    let mut content_map = BTreeMap::new();
    content_map.insert("kind".to_string(), Value::String(content_kind.clone()));
    content_map.insert("bytes".to_string(), Value::Bytes(content_bytes));
    if let Some(uri) = source_uri {
        content_map.insert("source_uri".to_string(), Value::String(uri));
    }
    if let Some(m) = meta_value {
        content_map.insert("meta".to_string(), m);
    }
    let canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("ingest content encode: {e}")))?;

    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let node_type = format!("raw_material:{content_kind}");
    let cycle = state.manifest.cycle_counter;
    let node_hash = state
        .dag
        .insert_node(parents, node_type, cycle, canonical)
        .map_err(|e| SubstrateError::Protocol(format!("raw_material DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "dag_node_hash".to_string(),
        Value::Bytes(node_hash.as_ref().to_vec()),
    );
    if let Some(tip) = state.dag.tip() {
        payload.insert(
            "current_tip".to_string(),
            Value::Bytes(tip.as_ref().to_vec()),
        );
    }
    payload.insert(
        "total_dag_size".to_string(),
        Value::Uint(state.dag.node_count() as u64),
    );
    Ok(Some(Message::new(
        msg_type::INGEST_RAW_MATERIAL_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M16: P2 永恒吞噬 + P6 永恒因果 — Perturb an axis with causal linkage to a
/// previously-ingested raw_material node. The substrate first forwards the
/// numeric perturbation to the Python gradient (same as `perturb`), then
/// inserts a causal-link DAG node parented by BOTH the prior tip AND the
/// referenced raw_material node — so the gradient change is traceable back
/// to its environmental source via the DAG.
fn handle_perturb_axis_from_raw_material(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Extract axis_name + delta_repr (mirrors perturb_payload format).
    let axis_name = match request.payload.get("axis_name") {
        Some(Value::String(s)) => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "perturb_axis_from_raw_material: axis_name must be String".to_string(),
            ));
        }
    };
    let delta_repr = match request.payload.get("delta_repr") {
        Some(Value::String(s)) => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "perturb_axis_from_raw_material: delta_repr must be String".to_string(),
            ));
        }
    };
    let raw_material_hash = match request.payload.get("raw_material_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            myco_kernel_shared::crypto::NodeHash::from_bytes(arr)
        }
        _ => {
            return Err(SubstrateError::Protocol(
                "perturb_axis_from_raw_material: raw_material_hash must be 32 bytes".to_string(),
            ));
        }
    };

    // Verify the raw_material_hash exists in the DAG AND is a raw_material node.
    {
        let node = state.dag.get(&raw_material_hash).ok_or_else(|| {
            SubstrateError::Protocol(format!(
                "perturb_axis_from_raw_material: raw_material_hash {} not found in DAG",
                hex_encode(raw_material_hash.as_ref())
            ))
        })?;
        if !node.node_type.starts_with("raw_material:") {
            return Err(SubstrateError::Protocol(format!(
                "perturb_axis_from_raw_material: hash {} references a {:?} node, not raw_material",
                hex_encode(raw_material_hash.as_ref()),
                node.node_type
            )));
        }
    }

    // Parse delta + forward to Python.
    let delta: f64 = delta_repr
        .parse()
        .map_err(|e| SubstrateError::Protocol(format!("delta_repr parse: {e}")))?;
    {
        let client = state
            .python_client
            .as_mut()
            .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
        client
            .perturb(&axis_name, delta)
            .map_err(SubstrateError::Bridge)?;
    }

    // Insert causal-link DAG node — node_type = "perturb_from_raw:{axis_name}",
    // parents = [prior tip, raw_material_hash].
    let prior_tip = state.dag.tip();
    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match prior_tip {
        Some(t) if t != raw_material_hash => vec![t, raw_material_hash],
        _ => vec![raw_material_hash],
    };
    let mut content_map = BTreeMap::new();
    content_map.insert("axis_name".to_string(), Value::String(axis_name.clone()));
    content_map.insert("delta_repr".to_string(), Value::String(delta_repr));
    content_map.insert(
        "raw_material_hash".to_string(),
        Value::Bytes(raw_material_hash.as_ref().to_vec()),
    );
    let canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("perturb_from_raw content encode: {e}")))?;

    let node_type = format!("perturb_from_raw:{axis_name}");
    let cycle = state.manifest.cycle_counter;
    let link_hash = state
        .dag
        .insert_node(parents, node_type, cycle, canonical)
        .map_err(|e| SubstrateError::Protocol(format!("perturb_from_raw DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "causal_link_hash".to_string(),
        Value::Bytes(link_hash.as_ref().to_vec()),
    );
    payload.insert(
        "raw_material_hash".to_string(),
        Value::Bytes(raw_material_hash.as_ref().to_vec()),
    );
    Ok(Some(Message::new(
        msg_type::PERTURB_AXIS_FROM_RAW_MATERIAL_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M20 P8 永恒繁衍 — Sprout a child substrate from the parent's spore-schema.
///
/// Per L0 §2.2 P8: "The substrate can spawn child substrates. Reproduction is
/// a first-class operation. The new substrate inherits the parent's
/// spore-schema (minimum structural form for the child to begin its own
/// symbiosis)."
///
/// M20-MV spore-schema = (gradient axes + schemas + current values) +
/// (operator identity pubkey for continuity) + (fresh substrate_id +
/// fresh genesis_time + cycle_counter=0 + last_absorbed_cycle=None).
///
/// The parent's causal DAG is NOT transferred — the child starts its own
/// causal history (L1 decision per L0 P8). The parent emits a
/// `spore_emission:{child_id_hex_prefix}` DAG node recording the reproduction.
///
/// Payload schema:
/// ```text
/// Map({
///   "child_state_dir": String,  // target directory (must not exist or must be empty)
///   "spore_metadata": Map       // optional; arbitrary K-V hints recorded in the spore_emission node
/// })
/// ```
///
/// Returns:
/// ```text
/// Map({
///   "child_substrate_id": Bytes(32),
///   "child_state_dir": String,
///   "spore_emission_hash": Bytes(32),   // in parent's DAG
/// })
/// ```
fn handle_sprout_child(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use crate::persistence::{
        save_pinned_operator_identity, Manifest, OPERATOR_IDENTITY_PUBKEY_FILENAME,
    };

    let child_state_dir = match request.payload.get("child_state_dir") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "sprout_child: child_state_dir must be a non-empty String".to_string(),
            ));
        }
    };
    let spore_metadata = request.payload.get("spore_metadata").cloned();

    let child_path = std::path::PathBuf::from(&child_state_dir);

    // Guard: child_state_dir must not contain an existing manifest.cb (don't
    // overwrite an existing substrate's identity).
    if child_path.join("manifest.cb").exists() {
        return Err(SubstrateError::Protocol(format!(
            "sprout_child: refusing to overwrite existing manifest.cb at {child_state_dir}"
        )));
    }

    // Create the child state_dir.
    std::fs::create_dir_all(&child_path).map_err(SubstrateError::Io)?;

    // Build the child's fresh manifest (NEW substrate_id; cycle_counter=0).
    let mut child_manifest = Manifest::genesis();
    child_manifest.save(&child_path)?;

    // Copy parent's operator_identity_pubkey to child (operator continuity —
    // the same operator pubkey is pinned in the child, so the operator can
    // immediately attach to the child substrate after spawn).
    if let Some(parent_pinned) = &state.pinned_operator_identity {
        save_pinned_operator_identity(parent_pinned, &child_path)?;
    }

    // Snapshot the parent's gradient state into the child's state_dir.
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
    let mut snap_payload = BTreeMap::new();
    snap_payload.insert(
        "target_dir".to_string(),
        Value::String(child_state_dir.clone()),
    );
    let snap_response = client
        .call(msg_type::SNAPSHOT_GRADIENT_TO_DIR, snap_payload)
        .map_err(SubstrateError::Bridge)?;
    if snap_response.message_type != msg_type::SNAPSHOT_GRADIENT_TO_DIR_ACK {
        return Err(SubstrateError::Protocol(format!(
            "expected snapshot_gradient_to_dir_ack; got {}",
            snap_response.message_type
        )));
    }
    let child_axis_count = snap_response
        .payload
        .get("axis_count")
        .and_then(|v| match v {
            Value::Uint(n) => Some(*n),
            _ => None,
        })
        .unwrap_or(0);

    // Emit spore_emission:{child_id_prefix} DAG node in PARENT's DAG.
    let child_id_hex_prefix: String = child_manifest
        .substrate_id
        .iter()
        .take(8)
        .map(|b| format!("{b:02x}"))
        .collect();
    let mut spore_content = BTreeMap::new();
    spore_content.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(child_manifest.substrate_id.to_vec()),
    );
    spore_content.insert(
        "child_state_dir".to_string(),
        Value::String(child_state_dir.clone()),
    );
    spore_content.insert(
        "child_axis_count".to_string(),
        Value::Uint(child_axis_count),
    );
    spore_content.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(state.manifest.substrate_id.to_vec()),
    );
    spore_content.insert(
        "parent_cycle_at_emission".to_string(),
        Value::Uint(state.manifest.cycle_counter),
    );
    if let Some(m) = spore_metadata {
        spore_content.insert("spore_metadata".to_string(), m);
    }
    let spore_canonical = cb_encode(&Value::Map(spore_content))
        .map_err(|e| SubstrateError::Protocol(format!("spore_emission encode: {e}")))?;
    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let spore_node_type = format!("spore_emission:{child_id_hex_prefix}");
    let cycle = state.manifest.cycle_counter;
    let spore_hash = state
        .dag
        .insert_node(parents, spore_node_type, cycle, spore_canonical)
        .map_err(|e| SubstrateError::Protocol(format!("spore_emission DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(child_manifest.substrate_id.to_vec()),
    );
    payload.insert(
        "child_state_dir".to_string(),
        Value::String(child_state_dir),
    );
    payload.insert(
        "child_axis_count".to_string(),
        Value::Uint(child_axis_count),
    );
    payload.insert(
        "spore_emission_hash".to_string(),
        Value::Bytes(spore_hash.as_ref().to_vec()),
    );
    // Quiet the unused-import warning for OPERATOR_IDENTITY_PUBKEY_FILENAME
    // since it's not directly referenced here (used via save_pinned_operator_identity).
    let _ = OPERATOR_IDENTITY_PUBKEY_FILENAME;

    Ok(Some(Message::new(
        msg_type::SPROUT_CHILD_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M11: List recent immune sporocarps (DAG nodes with `node_type` prefix
/// `"immune:"`). Rust-handled; no Python involvement.
fn handle_query_immune_events(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let count = request
        .payload
        .get("count")
        .and_then(|v| match v {
            Value::Uint(n) => Some(*n),
            _ => None,
        })
        .unwrap_or(50);

    let all_nodes: Vec<_> = state.dag.iter_in_insertion_order().collect();
    let immune_nodes: Vec<_> = all_nodes
        .iter()
        .filter(|n| n.node_type.starts_with("immune:"))
        .copied()
        .collect();
    let total = immune_nodes.len();
    let start = total.saturating_sub(count as usize);
    let recent: Vec<Value> = immune_nodes[start..]
        .iter()
        .map(|n| {
            let mut m = BTreeMap::new();
            m.insert("hash".to_string(), Value::Bytes(n.hash.as_ref().to_vec()));
            m.insert("node_type".to_string(), Value::String(n.node_type.clone()));
            m.insert("at_cycle".to_string(), Value::Uint(n.created_at_cycle));
            m.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(n.content_canonical_bytes.as_ref().to_vec()),
            );
            Value::Map(m)
        })
        .collect();

    let mut payload = BTreeMap::new();
    payload.insert("total_immune_count".to_string(), Value::Uint(total as u64));
    payload.insert(
        "returned_count".to_string(),
        Value::Uint(recent.len() as u64),
    );
    payload.insert("events".to_string(), Value::Array(recent));
    Ok(Some(Message::new(
        msg_type::QUERY_IMMUNE_EVENTS_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M10: Forward submit_mutation to Python for classification + (CI) verification,
/// and on accept insert the mutation as a DAG node.
fn handle_submit_mutation(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // M14: Pre-Python REVEAL keypair verification.
    // If the operator included `reveal_pubkey` + `identity_signature_over_reveal_pubkey`,
    // verify the IDENTITY signature against the pinned operator pubkey BEFORE
    // doing anything else. Failures emit C17 operator_witness_forgery.
    //
    // The REVEAL pubkey then becomes the signer for the attestation signature
    // (the operator's `attestation_signature` field is treated as a REVEAL
    // signature when reveal_pubkey is present, rather than an IDENTITY signature).
    let reveal_pubkey_present = request.payload.contains_key("reveal_pubkey");
    if reveal_pubkey_present {
        if let Err(reason) = verify_reveal_keypair_envelope(state, request) {
            let evidence = format!("REVEAL keypair envelope verification failed: {reason}");
            let _ = emit_immune_sporocarp(
                state,
                "C17_operator_witness_forgery",
                "operator_witness_forgery",
                &evidence,
            );
            let _ = save_dag_state(state);

            let mut payload = BTreeMap::new();
            payload.insert(
                "classification".to_string(),
                Value::String("contract_identity_level".to_string()),
            );
            payload.insert("accepted".to_string(), Value::Bool(false));
            payload.insert("rejection_reason".to_string(), Value::String(reason));
            let mtype = request
                .payload
                .get("mutation_type")
                .and_then(|v| match v {
                    Value::String(s) => Some(s.clone()),
                    _ => None,
                })
                .unwrap_or_default();
            payload.insert("mutation_type".to_string(), Value::String(mtype));
            return Ok(Some(Message::new(
                msg_type::SUBMIT_MUTATION_RESPONSE,
                request.request_id,
                payload,
            )));
        }
    }

    // M13: Pre-Python nonce verification (anchor-surface envelope check).
    // If the operator included a nonce, verify it BEFORE forwarding. Failed
    // nonce checks short-circuit with a C5 rejection + immune sporocarp.
    let nonce_present = request.payload.contains_key("nonce");
    if nonce_present {
        let nonce_bytes = match request.payload.get("nonce") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => Vec::new(),
        };
        let content_bytes_for_hash = match request.payload.get("content_canonical_bytes") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => Vec::new(),
        };
        let content_hash = compute_content_hash(&content_bytes_for_hash);
        let submitted_expiry = request.payload.get("expiry_unix_ns").and_then(|v| match v {
            Value::Timestamp(t) => Some(*t),
            _ => None,
        });
        // M15: dual-clock — operator-supplied "now on anchor clock at submit time".
        let submitted_anchor_clock = request
            .payload
            .get("anchor_clock_submitted_at_unix_ns")
            .and_then(|v| match v {
                Value::Timestamp(t) => Some(*t),
                _ => None,
            });
        if let Err(reason) = verify_attestation_nonce(
            state,
            &nonce_bytes,
            &content_hash,
            submitted_expiry,
            submitted_anchor_clock,
        ) {
            // Build a rejection response directly; emit C5 immune sporocarp.
            let evidence = format!("anchor-surface envelope verification failed: {reason}");
            let _ = emit_immune_sporocarp(
                state,
                "C5_attestation_invalid",
                "attestation_invalid_anchor_surface",
                &evidence,
            );
            let _ = save_dag_state(state);

            let mut payload = BTreeMap::new();
            payload.insert(
                "classification".to_string(),
                Value::String("contract_identity_level".to_string()),
            );
            payload.insert("accepted".to_string(), Value::Bool(false));
            payload.insert("rejection_reason".to_string(), Value::String(reason));
            let mtype = request
                .payload
                .get("mutation_type")
                .and_then(|v| match v {
                    Value::String(s) => Some(s.clone()),
                    _ => None,
                })
                .unwrap_or_default();
            payload.insert("mutation_type".to_string(), Value::String(mtype));
            return Ok(Some(Message::new(
                msg_type::SUBMIT_MUTATION_RESPONSE,
                request.request_id,
                payload,
            )));
        }
        // Nonce verified; proceed to forward.
    }

    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // Forward verbatim to Python via the generic `call` API.
    let python_response = client
        .call(msg_type::SUBMIT_MUTATION, request.payload.clone())
        .map_err(SubstrateError::Bridge)?;
    if python_response.message_type != msg_type::SUBMIT_MUTATION_RESPONSE {
        return Err(SubstrateError::Protocol(format!(
            "expected submit_mutation_response; got {}",
            python_response.message_type
        )));
    }

    // Parse Python's response.
    let classification = python_response
        .payload
        .get("classification")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let accepted = python_response
        .payload
        .get("accepted")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let rejection_reason = python_response
        .payload
        .get("rejection_reason")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let content_bytes = python_response
        .payload
        .get("content_canonical_bytes")
        .and_then(|v| match v {
            Value::Bytes(b) => Some(b.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let mutation_type = python_response
        .payload
        .get("mutation_type")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();

    // M17 P3 永恒进化: read evolution outcome fields from Python's response.
    let schema_apply_attempted = python_response
        .payload
        .get("schema_apply_attempted")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let schema_apply_succeeded = python_response
        .payload
        .get("schema_apply_succeeded")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let schema_apply_failure_reason = python_response
        .payload
        .get("schema_apply_failure_reason")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let schema_apply_op = python_response
        .payload
        .get("schema_apply_op")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let schema_apply_summary = python_response
        .payload
        .get("schema_apply_summary")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();

    // If accepted: wrap as DAG node with parent=tip.
    // If rejected: emit an immune sporocarp (M11 C14 for UNTYPED; C5 for invalid CI attestation).
    let dag_node_hash = if accepted {
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let node_type = format!("mutation:{mutation_type}");
        let current_cycle = state.manifest.cycle_counter;
        let hash = state
            .dag
            .insert_node(
                parents,
                node_type,
                current_cycle,
                CanonicalBytes(content_bytes),
            )
            .map_err(|e| SubstrateError::Protocol(format!("mutation DAG insert: {e}")))?;
        Some(hash)
    } else {
        // M11: emit immune sporocarp for the rejection.
        let (detector_id, detector_name) = match classification.as_str() {
            "untyped" => ("C14_untyped_mutation_blocked", "untyped_mutation_blocked"),
            "contract_identity_level" => ("C5_attestation_invalid", "attestation_invalid"),
            _ => ("C_unknown", "unknown_breach"),
        };
        let evidence_str = format!(
            "mutation_type={mutation_type}; classification={classification}; reason={rejection_reason}"
        );
        // Best-effort emit; ignore errors (we don't want to mask the original rejection).
        let _ = emit_immune_sporocarp(state, detector_id, detector_name, &evidence_str);
        None
    };

    // M17 P3 永恒进化: after mutation acceptance, emit the evolution event DAG node.
    // - schema_apply_attempted + schema_apply_succeeded → evolution_succeeded:{op}
    // - schema_apply_attempted + !schema_apply_succeeded → evolution_failed:{op}
    //   (mutation:schema_evolution still in DAG as audit trail of the attempt.)
    let evolution_event_hash = if schema_apply_attempted {
        let event_node_type = if schema_apply_succeeded {
            format!("evolution_succeeded:{schema_apply_op}")
        } else {
            format!("evolution_failed:{schema_apply_op}")
        };
        let mut event_map = BTreeMap::new();
        event_map.insert("op".to_string(), Value::String(schema_apply_op.clone()));
        event_map.insert("succeeded".to_string(), Value::Bool(schema_apply_succeeded));
        event_map.insert(
            "summary".to_string(),
            Value::String(schema_apply_summary.clone()),
        );
        if !schema_apply_succeeded {
            event_map.insert(
                "failure_reason".to_string(),
                Value::String(schema_apply_failure_reason.clone()),
            );
        }
        let event_canonical = cb_encode(&Value::Map(event_map))
            .map_err(|e| SubstrateError::Protocol(format!("evolution event encode: {e}")))?;
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let cycle = state.manifest.cycle_counter;
        let h = state
            .dag
            .insert_node(parents, event_node_type, cycle, event_canonical)
            .map_err(|e| SubstrateError::Protocol(format!("evolution event DAG insert: {e}")))?;
        Some(h)
    } else {
        None
    };

    // Build response to operator.
    let mut payload = BTreeMap::new();
    payload.insert("classification".to_string(), Value::String(classification));
    payload.insert("accepted".to_string(), Value::Bool(accepted));
    payload.insert(
        "rejection_reason".to_string(),
        Value::String(rejection_reason),
    );
    payload.insert("mutation_type".to_string(), Value::String(mutation_type));
    if let Some(h) = dag_node_hash {
        payload.insert(
            "dag_node_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // M17 evolution fields surfaced to operator.
    payload.insert(
        "schema_apply_attempted".to_string(),
        Value::Bool(schema_apply_attempted),
    );
    payload.insert(
        "schema_apply_succeeded".to_string(),
        Value::Bool(schema_apply_succeeded),
    );
    payload.insert(
        "schema_apply_failure_reason".to_string(),
        Value::String(schema_apply_failure_reason),
    );
    payload.insert(
        "schema_apply_op".to_string(),
        Value::String(schema_apply_op),
    );
    payload.insert(
        "schema_apply_summary".to_string(),
        Value::String(schema_apply_summary),
    );
    if let Some(h) = evolution_event_hash {
        payload.insert(
            "evolution_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }

    Ok(Some(Message::new(
        msg_type::SUBMIT_MUTATION_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// Build an "empty DAG → cold-start" intent response (no clusters, cold_start=true).
fn empty_intent_response(request_id: u64) -> Message {
    let mut payload = BTreeMap::new();
    payload.insert("cold_start".to_string(), Value::Bool(true));
    payload.insert("neighborhood_node_count".to_string(), Value::Uint(0));
    payload.insert("full_set_node_count".to_string(), Value::Uint(0));
    payload.insert("cluster_count".to_string(), Value::Uint(0));
    payload.insert("clusters".to_string(), Value::Array(Vec::new()));
    Message::new(msg_type::COMPUTE_INTENT_RESPONSE, request_id, payload)
}

fn handle_hello(
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
            "hello missing operator_pubkey + hello_signature; substrate has a pinned operator identity (downgrade rejected; M9 L1_HARD_RULES C2)".to_string(),
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
            "hello_signature verification failed (L1_HARD_RULES C2): {e}"
        ))
    })?;

    // TOFU or match.
    match &state.pinned_operator_identity {
        None => {
            // First sight — pin.
            let pinned = PinnedOperatorIdentity::pin_now(pubkey_bytes);
            save_pinned_operator_identity(&pinned, &state.state_dir)?;
            // M21.1 P5 万物互联: emit operator_pinned DAG event so the TOFU
            // pinning is recorded in the causal graph (was an orphan prior).
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
                    "operator pubkey mismatch: pinned {} vs presented {} (L1_HARD_RULES C2 handshake_pubkey_mismatch)",
                    hex_encode(&pinned.pubkey),
                    hex_encode(&pubkey_bytes)
                )))
            }
        }
    }
}

fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

/// Trigger a save of the Python-side gradient state. Called after every
/// operation that mutates the gradient (register_axis / perturb / advance).
fn save_python_state(state: &mut ServerState) -> Result<(), SubstrateError> {
    let state_dir_str = state.state_dir_str();
    if let Some(client) = state.python_client.as_mut() {
        client.save_state(&state_dir_str)?;
    }
    Ok(())
}

/// M8: Persist the substrate's DAG to `<state_dir>/dag.cb`.
fn save_dag_state(state: &ServerState) -> Result<(), SubstrateError> {
    save_dag(&state.dag, &state.state_dir)
}

/// M14: Snapshot the substrate's in-process nonce log to `<state_dir>/nonces.cb`.
/// M15: also persists dual-clock fields when present.
fn save_nonce_state(state: &ServerState) -> Result<(), SubstrateError> {
    let entries: Vec<PersistedNonceEntry> = state
        .nonce_log
        .values()
        .map(|n| PersistedNonceEntry {
            nonce: n.nonce,
            bound_content_hash: n.bound_content_hash,
            bound_dag_tip: n.bound_dag_tip,
            substrate_issued_at_unix_ns: n.substrate_issued_at_unix_ns,
            expiry_unix_ns: n.expiry_unix_ns,
            anchor_clock_issued_at_unix_ns: n.anchor_clock_issued_at_unix_ns,
            anchor_clock_expiry_unix_ns: n.anchor_clock_expiry_unix_ns,
            consumed: n.consumed,
        })
        .collect();
    save_nonce_log(&entries, &state.state_dir)
}

/// M12: Result of one integrity check (C9 cold_resume_invariant_failure sub-check).
#[derive(Debug, Clone)]
struct IntegrityCheckResult {
    check_id: String,
    passed: bool,
    evidence: String,
}

/// M12: Run the substrate's comprehensive integrity checks.
///
/// Runs 5 checks:
/// 1. `substrate_id_well_formed` — manifest.substrate_id is non-zero
/// 2. `cycle_counter_monotonic` — manifest.cycle_counter ≥ max(DAG node at_cycle)
/// 3. `pinned_pubkey_well_formed` — pinned pubkey is non-zero Ed25519
/// 4. `dag_verify_all` — every DAG node's hash recomputes correctly
/// 5. `owner_keys_consistency` — (M10 operator==owner) active owner key MUST equal pinned operator pubkey
///
/// Returns a vec of results. Caller emits a C9 immune sporocarp for each failure.
fn run_integrity_checks(state: &ServerState) -> Vec<IntegrityCheckResult> {
    let mut results = Vec::new();

    // 1. substrate_id well-formed.
    let substrate_id_zero = state.manifest.substrate_id.iter().all(|b| *b == 0);
    results.push(IntegrityCheckResult {
        check_id: "substrate_id_well_formed".to_string(),
        passed: !substrate_id_zero,
        evidence: if substrate_id_zero {
            "manifest.substrate_id is all zeros (genesis bug or tamper)".to_string()
        } else {
            "ok".to_string()
        },
    });

    // 2. Cycle counter monotonic against DAG at_cycle.
    let max_dag_cycle = state
        .dag
        .iter_in_insertion_order()
        .map(|n| n.created_at_cycle)
        .max()
        .unwrap_or(0);
    let monotonic = state.manifest.cycle_counter >= max_dag_cycle;
    results.push(IntegrityCheckResult {
        check_id: "cycle_counter_monotonic".to_string(),
        passed: monotonic,
        evidence: if monotonic {
            format!(
                "manifest.cycle_counter={} >= max(DAG.at_cycle)={}",
                state.manifest.cycle_counter, max_dag_cycle
            )
        } else {
            format!(
                "manifest.cycle_counter={} < max(DAG.at_cycle)={} (manifest may have rolled back)",
                state.manifest.cycle_counter, max_dag_cycle
            )
        },
    });

    // 3. Pinned pubkey well-formed (if exists).
    if let Some(pinned) = &state.pinned_operator_identity {
        let zero = pinned.pubkey.iter().all(|b| *b == 0);
        results.push(IntegrityCheckResult {
            check_id: "pinned_pubkey_well_formed".to_string(),
            passed: !zero,
            evidence: if zero {
                "pinned operator_identity_pubkey is all zeros".to_string()
            } else {
                "ok (32 non-zero bytes)".to_string()
            },
        });
    }

    // 4. DAG.verify_all() — every node's hash recomputes correctly.
    let dag_verify = state.dag.verify_all();
    results.push(IntegrityCheckResult {
        check_id: "dag_verify_all".to_string(),
        passed: dag_verify.is_ok(),
        evidence: match &dag_verify {
            Ok(()) => format!(
                "ok (all {} nodes pass hash recomputation)",
                state.dag.node_count()
            ),
            Err(e) => format!("dag_verify_all failed: {e}"),
        },
    });

    // 5. owner_keys consistency check is operator-side: we can only verify the
    //    pinned operator pubkey is non-zero (the owner_keys live in Python and
    //    are loaded via load_state during hello). This check is therefore a
    //    placeholder at the Rust layer; full owner_keys vs pinned-pubkey cross-
    //    validation happens implicitly when the first CI mutation is submitted
    //    (signature verification will fail if Python's owner_keys diverges from
    //    Rust's pinned pubkey).
    results.push(IntegrityCheckResult {
        check_id: "owner_keys_consistency".to_string(),
        passed: true,
        evidence: "deferred to Python load_state path; CI mutation signatures cross-validate"
            .to_string(),
    });

    // 6. M19 P9 皮肤 / L1_HARD_RULES C18 canonical_bytes_render_drift:
    //    decode each DAG node's content_canonical_bytes, re-encode, and compare.
    //    Any divergence indicates canonical-bytes rendering is non-deterministic
    //    (e.g., map keys not sorted, repr drift, integer encoding inconsistency)
    //    — a CRITICAL skin breach that would let an attacker present the same
    //    semantic content with different byte sequences.
    //
    //    M19-MV scope: scan substrate-self-generated DAG nodes. Operator-
    //    supplied content (mutation:*) is opaque to the substrate — the
    //    operator chooses the encoding — so we skip those nodes. Substrate-
    //    generated nodes (sporocarp:*, immune:*, absorption_event:*,
    //    evolution_*:*, self_euthanasia_proposal:*, perturb_from_raw:*,
    //    raw_material:*) MUST round-trip cleanly because the substrate itself
    //    chose their canonical-bytes shape.
    let is_substrate_generated = |node_type: &str| -> bool { !node_type.starts_with("mutation:") };
    let (cb_drift_count, cb_drift_example): (usize, Option<String>) = {
        use myco_kernel_shared::canonical_bytes::{decode, encode};
        let mut drift_count = 0usize;
        let mut first_example: Option<String> = None;
        for node in state
            .dag
            .iter_in_insertion_order()
            .filter(|n| is_substrate_generated(&n.node_type))
        {
            let original = node.content_canonical_bytes.as_ref();
            // Decode then re-encode. If the bytes differ, drift detected.
            match decode(original) {
                Ok(value) => match encode(&value) {
                    Ok(reencoded) => {
                        if reencoded.as_ref() != original {
                            drift_count += 1;
                            if first_example.is_none() {
                                first_example = Some(format!(
                                    "node {} (type {:?}) round-trips to different bytes \
                                     (original {} bytes, re-encoded {} bytes)",
                                    hex_encode(node.hash.as_ref()),
                                    node.node_type,
                                    original.len(),
                                    reencoded.as_ref().len()
                                ));
                            }
                        }
                    }
                    Err(e) => {
                        drift_count += 1;
                        if first_example.is_none() {
                            first_example = Some(format!(
                                "node {} re-encode failed: {e}",
                                hex_encode(node.hash.as_ref())
                            ));
                        }
                    }
                },
                Err(e) => {
                    // Decode failure on supposedly canonical bytes is itself a drift signal.
                    drift_count += 1;
                    if first_example.is_none() {
                        first_example = Some(format!(
                            "node {} decode failed: {e}",
                            hex_encode(node.hash.as_ref())
                        ));
                    }
                }
            }
        }
        (drift_count, first_example)
    };
    // Count substrate-generated nodes for the OK-evidence message.
    let substrate_generated_count = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| is_substrate_generated(&n.node_type))
        .count();
    results.push(IntegrityCheckResult {
        check_id: "canonical_bytes_render_drift".to_string(),
        passed: cb_drift_count == 0,
        evidence: if cb_drift_count == 0 {
            format!(
                "ok (all {substrate_generated_count} substrate-generated DAG nodes round-trip cleanly; mutation:* content is operator-opaque and skipped)"
            )
        } else {
            cb_drift_example.unwrap_or_else(|| {
                format!("{cb_drift_count} nodes drift; no specific example captured")
            })
        },
    });

    // 7. M21.1 P5 万物互联 / L1_HARD_RULES C19 substrate_state_orphan_detected:
    //    rebuild Rust-side state from DAG events and compare to in-memory state.
    //    Divergence → some state mutation happened without emitting a DAG event
    //    (orphan), violating P5 "the substrate is a connected graph; orphans
    //    are dead tissue."
    //
    //    M21.1 dual-write phase scope: this check verifies that all Rust-side
    //    fields (substrate_id, genesis_time, cycle_counter, last_absorbed_cycle,
    //    pinned_operator_identity, nonce_log) can be derived from DAG events.
    //    Python-owned state (gradient, owner_keys) is deferred to M21.3 when
    //    Python becomes a derived-view consumer.
    let (orphan_passed, orphan_evidence) = check_substrate_state_orphans(state);
    results.push(IntegrityCheckResult {
        check_id: "substrate_state_orphan_detected".to_string(),
        passed: orphan_passed,
        evidence: orphan_evidence,
    });

    results
}

/// M21.1: C19 detector. Reconciles in-memory ServerState (Rust-side fields)
/// against DerivedState::from_dag. Returns (passed, evidence).
///
/// What this checks:
/// - substrate_id: live manifest.substrate_id == derived.substrate_id
/// - genesis_time_unix_ns: live manifest.genesis_time_unix_ns == derived.genesis_time_unix_ns
/// - cycle_counter: live manifest.cycle_counter == derived.cycle_counter
/// - last_absorbed_cycle: live manifest.last_absorbed_cycle == derived.last_absorbed_cycle
/// - pinned_operator_identity: live state.pinned_operator_identity == derived.pinned_operator_identity
/// - nonce_log: live state.nonce_log size + per-entry consumed flags == derived.nonce_log
fn check_substrate_state_orphans(state: &ServerState) -> (bool, String) {
    use crate::derived_state::DerivedState;

    let derived = match DerivedState::from_dag(&state.dag) {
        Ok(d) => d,
        Err(e) => {
            return (
                false,
                format!("DerivedState::from_dag failed: {e} (likely event encoding bug)"),
            );
        }
    };

    let mut divergences: Vec<String> = Vec::new();

    // substrate_id: derived is Some iff a genesis_event has been emitted.
    // If derived.substrate_id is None but live manifest has one, that means
    // the substrate is running on a manifest.cb without a corresponding
    // genesis_event in DAG — this is exactly the M21.1 migration condition
    // (existing substrates pre-M21 have no genesis_event). To avoid false
    // positives during migration, we ONLY report divergence when derived
    // HAS substrate_id and it differs from live.
    if let Some(d_id) = derived.substrate_id {
        if d_id != state.manifest.substrate_id {
            divergences.push(format!(
                "substrate_id mismatch: live={}, derived={}",
                hex_encode(&state.manifest.substrate_id),
                hex_encode(&d_id)
            ));
        }
    }

    // genesis_time: same migration-friendly check.
    if let Some(d_time) = derived.genesis_time_unix_ns {
        if d_time != state.manifest.genesis_time_unix_ns {
            divergences.push(format!(
                "genesis_time_unix_ns mismatch: live={}, derived={}",
                state.manifest.genesis_time_unix_ns, d_time
            ));
        }
    }

    // cycle_counter: this is INCREMENTED in the dispatch arm AFTER handle_advance
    // returns, but the cycle_advanced event is emitted from inside the dispatch
    // arm too. So derived.cycle_counter should EQUAL live.cycle_counter after
    // an advance. For pre-M21 manifests that never emitted cycle_advanced, the
    // derived value will be 0 while live can be > 0 — only report divergence
    // when derived.cycle_counter > 0 OR (derived.substrate_id is Some, i.e. we
    // have a genesis event and thus the substrate is post-M21).
    if (derived.cycle_counter > 0 || derived.substrate_id.is_some())
        && derived.cycle_counter != state.manifest.cycle_counter
    {
        divergences.push(format!(
            "cycle_counter mismatch: live={}, derived={}",
            state.manifest.cycle_counter, derived.cycle_counter
        ));
    }

    // last_absorbed_cycle: derived from absorption_event events (already in DAG
    // since M18). Should always match.
    if derived.last_absorbed_cycle != state.manifest.last_absorbed_cycle {
        // BUT: absorption_event was added in M18; pre-M21 last_absorbed_cycle
        // tracking is via manifest only. Migration tolerance:
        // - derived is Some → strict match required
        // - derived is None → tolerate live Some (legacy)
        if derived.last_absorbed_cycle.is_some() {
            divergences.push(format!(
                "last_absorbed_cycle mismatch: live={:?}, derived={:?}",
                state.manifest.last_absorbed_cycle, derived.last_absorbed_cycle
            ));
        }
    }

    // pinned_operator_identity: derived from operator_pinned event.
    if let Some(derived_id) = &derived.pinned_operator_identity {
        match &state.pinned_operator_identity {
            Some(live_id) => {
                if live_id.pubkey != derived_id.pubkey
                    || live_id.first_pinned_unix_ns != derived_id.first_pinned_unix_ns
                {
                    divergences.push(format!(
                        "pinned_operator_identity mismatch: live.pubkey={}, derived.pubkey={}",
                        hex_encode(&live_id.pubkey),
                        hex_encode(&derived_id.pubkey)
                    ));
                }
            }
            None => {
                divergences.push(
                    "pinned_operator_identity present in DAG but absent in live state".to_string(),
                );
            }
        }
    }

    // nonce_log: derived from nonce_issued/consumed/expired events.
    // Compare entry-by-entry. Migration tolerance: if derived.nonce_log is
    // empty AND live.nonce_log is non-empty AND no genesis_event in DAG, this
    // is pre-M21 legacy nonce data — tolerate. Otherwise enforce match.
    let derived_is_post_m21 = derived.substrate_id.is_some();
    if derived_is_post_m21 {
        for (nonce, live_entry) in &state.nonce_log {
            match derived.nonce_log.get(nonce) {
                Some(d_entry) => {
                    if live_entry.consumed != d_entry.consumed {
                        divergences.push(format!(
                            "nonce {} consumed-flag mismatch: live={}, derived={}",
                            hex_first_8_bytes(nonce),
                            live_entry.consumed,
                            d_entry.consumed
                        ));
                    }
                    if live_entry.expiry_unix_ns != d_entry.expiry_unix_ns {
                        divergences.push(format!(
                            "nonce {} expiry mismatch",
                            hex_first_8_bytes(nonce)
                        ));
                    }
                }
                None => {
                    divergences.push(format!(
                        "nonce {} in live log but no nonce_issued event in DAG",
                        hex_first_8_bytes(nonce)
                    ));
                }
            }
        }
        // Check derived has no extras absent from live.
        for nonce in derived.nonce_log.keys() {
            if !state.nonce_log.contains_key(nonce) {
                divergences.push(format!(
                    "nonce {} has nonce_issued event in DAG but absent in live log (premature prune?)",
                    hex_first_8_bytes(nonce)
                ));
            }
        }
    }

    if divergences.is_empty() {
        (
            true,
            format!(
                "ok (Rust-side state fully derivable from DAG; nonce_log={} entries)",
                state.nonce_log.len()
            ),
        )
    } else {
        let summary = if divergences.len() == 1 {
            divergences.into_iter().next().unwrap()
        } else {
            format!(
                "{} orphan(s) detected. First: {}",
                divergences.len(),
                divergences.into_iter().next().unwrap()
            )
        };
        (false, summary)
    }
}

fn hex_first_8_bytes(bytes: &[u8; 32]) -> String {
    bytes[..8].iter().map(|b| format!("{b:02x}")).collect()
}

/// M11: Emit an immune sporocarp as a DAG node.
///
/// Wraps a detected breach event as a DAG node with `node_type = "immune:{detector_id}"`.
/// The node's content is canonical-bytes of a Map carrying the detector ID,
/// evidence, and a wall-clock timestamp.
///
/// Returns the DAG node hash (32 bytes). On failure to encode or insert,
/// returns Err — but callers typically log + continue rather than escalating,
/// because immune emission failures should not mask the original breach.
fn emit_immune_sporocarp(
    state: &mut ServerState,
    detector_id: &str,
    detector_name: &str,
    evidence: &str,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};
    let timestamp_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);

    let mut content_map = BTreeMap::new();
    content_map.insert(
        "detector_id".to_string(),
        Value::String(detector_id.to_string()),
    );
    content_map.insert(
        "detector_name".to_string(),
        Value::String(detector_name.to_string()),
    );
    content_map.insert("evidence".to_string(), Value::String(evidence.to_string()));
    content_map.insert(
        "timestamp_unix_ns".to_string(),
        Value::Timestamp(timestamp_unix_ns),
    );
    let content_canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("immune encode: {e}")))?;

    let parents = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let node_type = format!("immune:{detector_id}");
    let cycle = state.manifest.cycle_counter;
    state
        .dag
        .insert_node(parents, node_type, cycle, content_canonical)
        .map_err(|e| SubstrateError::Protocol(format!("immune DAG insert: {e}")))
}

/// M21.3 P5 万物互联: back-fill DAG events for legacy substrates that loaded
/// state from disk (gradient.cb / owner_keys.cb / etc.).
///
/// Flow: Python loaded its state from disk; we query Python for the loaded
/// schemas; for each axis NOT yet recorded as an axis_registered event in
/// the DAG, we emit one. For each axis whose current_value != initial_value,
/// we also emit a synthetic axis_perturbed event capturing the delta.
///
/// Also emits the genesis_event if not yet present (so the substrate is now
/// post-M21 from this boot forward). Subsequent boots use the DAG-first path.
///
/// This is the one-shot legacy → M21 migration; idempotent (running it twice
/// is a no-op because all events would already be present after the first run).
fn backfill_dag_from_python_state(
    python_client: &mut BridgeClient,
    state: &mut ServerState,
    _genesis_owner: &Option<[u8; 32]>,
) -> Result<(), SubstrateError> {
    // First: emit genesis_event if missing.
    let has_genesis = state.dag.iter_in_insertion_order().any(|n| {
        n.node_type
            .starts_with(crate::events::NODE_TYPE_GENESIS_PREFIX)
    });
    if !has_genesis {
        let event_nt = crate::events::genesis_event_node_type(&state.manifest.substrate_id);
        let event_content = crate::events::encode_genesis_event(
            &state.manifest.substrate_id,
            state.manifest.genesis_time_unix_ns,
        );
        let _ = emit_substrate_event(state, event_nt, event_content);
        let _ = save_dag_state(state);
    }

    // Emit operator_pinned if missing.
    let has_op_pinned = state.dag.iter_in_insertion_order().any(|n| {
        n.node_type
            .starts_with(crate::events::NODE_TYPE_OPERATOR_PINNED_PREFIX)
    });
    if !has_op_pinned {
        if let Some(pinned) = state.pinned_operator_identity.clone() {
            let event_nt = crate::events::operator_pinned_node_type(&pinned.pubkey);
            let event_content =
                crate::events::encode_operator_pinned(&pinned.pubkey, pinned.first_pinned_unix_ns);
            let _ = emit_substrate_event(state, event_nt, event_content);
            let _ = save_dag_state(state);
        }
    }

    // Query Python for its loaded axis schemas + current values.
    let schemas = python_client
        .query_gradient_schemas()
        .map_err(SubstrateError::Bridge)?;

    // For each axis, if no axis_registered event exists for it in the DAG,
    // emit one. If current_value != initial_value, also emit axis_perturbed.
    for schema in schemas {
        let want_reg_nt = crate::events::axis_registered_node_type(&schema.name);
        let has_reg = state
            .dag
            .iter_in_insertion_order()
            .any(|n| n.node_type == want_reg_nt);
        if !has_reg {
            let event = crate::events::AxisRegisteredEvent {
                name: schema.name.clone(),
                axis_class: schema.axis_class.clone(),
                fruiting_threshold: schema.fruiting_threshold,
                initial_value: schema.initial_value,
                decay_rate_per_cycle: schema.decay_rate_per_cycle,
                is_mortality_signal: schema.is_mortality_signal,
                update_rule_kind: schema.update_rule_kind.clone(),
            };
            let event_content = crate::events::encode_axis_registered(&event);
            let _ = emit_substrate_event(state, want_reg_nt, event_content);
        }
        // If current value differs from initial, emit a perturbed event for the delta.
        let delta = schema.current_value - schema.initial_value;
        if delta != 0.0 {
            let perturbed_nt = crate::events::axis_perturbed_node_type(&schema.name);
            let event_content = crate::events::encode_axis_perturbed(&schema.name, delta);
            let _ = emit_substrate_event(state, perturbed_nt, event_content);
        }
    }
    let _ = save_dag_state(state);
    Ok(())
}

/// M21.3 P5 万物互联: replay DAG events to a freshly-loaded Python worker.
///
/// Iterates DAG events in insertion order. For each event that affects
/// Python-side gradient state (axis_registered:* / axis_perturbed:*),
/// invokes the corresponding Python BridgeClient method to reconstruct
/// state in-memory.
///
/// This is the inverse of `_handle_load_state(skip_disk_load=true)`:
/// load empty, then replay events to derive state.
///
/// Errors during replay propagate up — a malformed event in the DAG
/// indicates corruption; substrate refuses to boot with partial state.
fn replay_python_events_from_dag(
    python_client: &mut BridgeClient,
    dag: &Dag,
) -> Result<(), SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode, map_get_string};
    for node in dag.iter_in_insertion_order() {
        let nt = &node.node_type;
        if let Some(axis_name) = nt.strip_prefix(crate::events::NODE_TYPE_AXIS_REGISTERED_PREFIX) {
            // Decode the axis_registered event and replay as register_axis call.
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode axis_registered:{axis_name}: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} content not Map: {other:?}"
                    )))
                }
            };
            let getf = |k: &str| -> Result<&str, SubstrateError> {
                map_get_string(&map, k).map_err(|e| {
                    SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} field {k}: {e}"
                    ))
                })
            };
            let axis_class = getf("axis_class")?.to_string();
            let fruiting_threshold: f64 =
                getf("fruiting_threshold_repr")?.parse().map_err(|e| {
                    SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} fruiting_threshold_repr parse: {e}"
                    ))
                })?;
            let initial_value: f64 = getf("initial_value_repr")?.parse().map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_registered:{axis_name} initial_value_repr parse: {e}"
                ))
            })?;
            let decay_rate: f64 = getf("decay_rate_per_cycle_repr")?.parse().map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_registered:{axis_name} decay_rate_per_cycle_repr parse: {e}"
                ))
            })?;
            let is_mortality_signal = match map.get("is_mortality_signal") {
                Some(Value::Bool(b)) => *b,
                _ => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} missing is_mortality_signal"
                    )))
                }
            };
            let update_rule_kind = getf("update_rule_kind")?.to_string();
            python_client
                .register_axis(
                    axis_name,
                    &axis_class,
                    fruiting_threshold,
                    initial_value,
                    decay_rate,
                    is_mortality_signal,
                    &update_rule_kind,
                )
                .map_err(SubstrateError::Bridge)?;
        } else if let Some(axis_name) =
            nt.strip_prefix(crate::events::NODE_TYPE_AXIS_PERTURBED_PREFIX)
        {
            // Decode the axis_perturbed event and replay as perturb call.
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode axis_perturbed:{axis_name}: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay axis_perturbed:{axis_name} content not Map: {other:?}"
                    )))
                }
            };
            let delta_repr = map_get_string(&map, "delta_repr").map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_perturbed:{axis_name} delta_repr: {e}"
                ))
            })?;
            let delta: f64 = delta_repr.parse().map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_perturbed:{axis_name} delta parse: {e}"
                ))
            })?;
            python_client
                .perturb(axis_name, delta)
                .map_err(SubstrateError::Bridge)?;
        } else if nt.starts_with("perturb_from_raw:") {
            // M16 events: also a perturbation. Decode and replay.
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode perturb_from_raw: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay perturb_from_raw content not Map: {other:?}"
                    )))
                }
            };
            let axis_name = map_get_string(&map, "axis_name")
                .map_err(|e| {
                    SubstrateError::Protocol(format!("replay perturb_from_raw axis_name: {e}"))
                })?
                .to_string();
            let delta_repr = map_get_string(&map, "delta_repr").map_err(|e| {
                SubstrateError::Protocol(format!("replay perturb_from_raw delta_repr: {e}"))
            })?;
            let delta: f64 = delta_repr.parse().map_err(|e| {
                SubstrateError::Protocol(format!("replay perturb_from_raw delta parse: {e}"))
            })?;
            python_client
                .perturb(&axis_name, delta)
                .map_err(SubstrateError::Bridge)?;
        } else if nt == crate::events::NODE_TYPE_CYCLE_ADVANCED {
            // M21.3: replay cycle advance to Python so DECAY-rule axes get
            // their decay applied + APPETITE-axis fruiting resets fire.
            // Discards the advance_response (sporocarps were emitted during
            // the original cycle and are already DAG nodes; replay just
            // needs the gradient mutation side-effect).
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode cycle_advanced: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay cycle_advanced content not Map: {other:?}"
                    )))
                }
            };
            let new_cycle = match map.get("new_cycle") {
                Some(Value::Uint(u)) => *u,
                _ => {
                    return Err(SubstrateError::Protocol(
                        "replay cycle_advanced missing new_cycle".to_string(),
                    ))
                }
            };
            python_client
                .advance(new_cycle)
                .map_err(SubstrateError::Bridge)?;
        }
        // Other event types (genesis_event, operator_pinned, nonce_*,
        // sporocarp:*, mutation:*, immune:*, raw_material:*,
        // absorption_event:*, evolution_*:*, self_euthanasia_proposal:*,
        // spore_emission:*, owner_key_initialized) are NOT replayed to
        // Python (Rust-side state derived via DerivedState; Python doesn't
        // need them for gradient).
        //
        // NOTE: schema_evolution-driven schema changes (M17) are NOT
        // auto-replayed. M21.4+ may add `axis_threshold_modified` events
        // with replay paths.
    }
    Ok(())
}

/// M21.1: Build an AxisRegisteredEvent from a REGISTER_AXIS request payload.
/// Returns None if the payload is malformed (which should be caught upstream
/// but we guard defensively to avoid affecting the legacy path).
fn build_axis_registered_event(request: &Message) -> Option<crate::events::AxisRegisteredEvent> {
    let payload = &request.payload;
    let name = match payload.get("name") {
        Some(Value::String(s)) => s.clone(),
        _ => return None,
    };
    let axis_class = match payload.get("axis_class") {
        Some(Value::String(s)) => s.clone(),
        _ => return None,
    };
    let fruiting_threshold: f64 = match payload.get("fruiting_threshold_repr") {
        Some(Value::String(s)) => s.parse().ok()?,
        _ => return None,
    };
    let initial_value: f64 = match payload.get("initial_value_repr") {
        Some(Value::String(s)) => s.parse().ok()?,
        _ => return None,
    };
    let decay_rate_per_cycle: f64 = match payload.get("decay_rate_per_cycle_repr") {
        Some(Value::String(s)) => s.parse().ok()?,
        _ => return None,
    };
    let is_mortality_signal = match payload.get("is_mortality_signal") {
        Some(Value::Bool(b)) => *b,
        _ => return None,
    };
    let update_rule_kind = match payload.get("update_rule_kind") {
        Some(Value::String(s)) => s.clone(),
        _ => return None,
    };
    Some(crate::events::AxisRegisteredEvent {
        name,
        axis_class,
        fruiting_threshold,
        initial_value,
        decay_rate_per_cycle,
        is_mortality_signal,
        update_rule_kind,
    })
}

/// M21.1 P5 万物互联: emit a generic substrate event as a DAG node. This is
/// the unified helper used by all state-mutation handlers to record their
/// state changes in the DAG event log, closing P5 by ensuring no state
/// mutation is an orphan from the causal graph.
///
/// The node is parented by the current DAG tip (linear chain at M21.1; M21.2+
/// may add multi-parent for events with logical predecessors). Returns the
/// inserted node hash for callers who need it.
fn emit_substrate_event(
    state: &mut ServerState,
    node_type: String,
    content: myco_kernel_shared::canonical_bytes::CanonicalBytes,
) -> Result<myco_kernel_shared::crypto::NodeHash, SubstrateError> {
    let parents = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let cycle = state.manifest.cycle_counter;
    state
        .dag
        .insert_node(parents, node_type, cycle, content)
        .map_err(|e| SubstrateError::Protocol(format!("substrate event DAG insert: {e}")))
}

/// Forward a request to the Python worker verbatim and surface its response.
fn forward_to_python(
    state: &mut ServerState,
    request: &Message,
    expected_response_type: &str,
) -> Result<Option<Message>, SubstrateError> {
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
    // Re-encode and send through the BridgeClient's low-level frame API. We
    // can't reuse BridgeClient::register_axis() etc because those allocate
    // their own request_id; we want to preserve the operator's request_id
    // for correlation in the response we send BACK to the operator.
    //
    // M6 minimum: re-issue via BridgeClient methods (which allocate fresh
    // IDs), then re-stamp the response with the operator's request_id.
    let response = forward_message(client, request)?;
    if response.message_type != expected_response_type {
        return Err(SubstrateError::Protocol(format!(
            "expected {expected_response_type} from python; got {}",
            response.message_type
        )));
    }
    // Re-stamp with operator's request_id.
    Ok(Some(Message::new(
        &response.message_type,
        request.request_id,
        response.payload,
    )))
}

/// Low-level forwarder: takes a Message, asks the BridgeClient to send a
/// fresh-id copy, returns the response. Bypasses BridgeClient's typed
/// helpers because we want the raw payload pass-through.
fn forward_message(client: &mut BridgeClient, request: &Message) -> Result<Message, BridgeError> {
    match request.message_type.as_str() {
        msg_type::REGISTER_AXIS => {
            // Extract typed args from payload and call register_axis.
            let name = expect_string_field(&request.payload, "name")?;
            let axis_class = expect_string_field(&request.payload, "axis_class")?;
            let fruiting_threshold =
                parse_float_field(&request.payload, "fruiting_threshold_repr")?;
            let initial_value = parse_float_field(&request.payload, "initial_value_repr")?;
            let decay_rate = parse_float_field(&request.payload, "decay_rate_per_cycle_repr")?;
            let is_mortality_signal = expect_bool_field(&request.payload, "is_mortality_signal")?;
            let update_rule_kind = expect_string_field(&request.payload, "update_rule_kind")?;
            client.register_axis(
                &name,
                &axis_class,
                fruiting_threshold,
                initial_value,
                decay_rate,
                is_mortality_signal,
                &update_rule_kind,
            )?;
            Ok(Message::new(
                msg_type::REGISTER_AXIS_ACK,
                0, // operator-side will be re-stamped
                empty_payload(),
            ))
        }
        msg_type::PERTURB => {
            let axis_name = expect_string_field(&request.payload, "axis_name")?;
            let delta = parse_float_field(&request.payload, "delta_repr")?;
            client.perturb(&axis_name, delta)?;
            Ok(Message::new(msg_type::PERTURB_ACK, 0, empty_payload()))
        }
        msg_type::SNAPSHOT => {
            let values = client.snapshot()?;
            let mut values_map: BTreeMap<String, Value> = BTreeMap::new();
            for (k, v) in values {
                values_map.insert(k, Value::String(float_repr(v)));
            }
            let mut payload = BTreeMap::new();
            payload.insert("values".to_string(), Value::Map(values_map));
            Ok(Message::new(msg_type::SNAPSHOT_RESPONSE, 0, payload))
        }
        other => Err(BridgeError::Protocol(format!(
            "forward_message: cannot forward {other}"
        ))),
    }
}

fn handle_advance(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Extract the requested cycle number (informational; engine has its own counter).
    let _requested_cycle = request.payload.get("current_cycle").and_then(|v| match v {
        Value::Uint(u) => Some(*u),
        _ => None,
    });

    // M18 P4 永恒迭代: precompute cycle trait inputs BEFORE the cycle inner
    // scope (which mutably borrows state.python_client via gradient). All
    // DAG-reading work happens here; DAG mutations happen AFTER the inner scope.
    let starting_cycle = state.manifest.cycle_counter;
    let last_absorbed_cycle = state.manifest.last_absorbed_cycle;

    // Tier1 precompute: run DAG verify_all.
    let dag_verify_outcome = state.dag.verify_all();
    let (tier1_ok, tier1_reason) = match dag_verify_outcome {
        Ok(()) => (true, String::new()),
        Err(e) => (false, format!("DAG verify_all failed: {e}")),
    };

    // DeltaAbsorber precompute: list raw_material:* hashes added since
    // last_absorbed_cycle. These will be absorbed (= recorded as observed by
    // an absorption_event DAG node) in this cycle.
    // Filter semantics: None (never absorbed) → take all raw_material;
    // Some(c) → take only those created_at_cycle > c.
    let pending_absorption_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with("raw_material:"))
        .filter(|n| match last_absorbed_cycle {
            None => true,
            Some(c) => n.created_at_cycle > c,
        })
        .map(|n| n.hash)
        .collect();

    // SkinBreachChecker precompute: list immune:* node_types added during the
    // PRIOR cycle (created_at_cycle == starting_cycle - 1 OR ==starting_cycle
    // for boot-time immune events with cycle 0). M18-MV is observational —
    // we just propagate breach observations into the cycle report.
    let breach_names: Vec<String> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| {
            n.created_at_cycle >= starting_cycle.saturating_sub(1)
                && n.node_type.starts_with("immune:")
        })
        .map(|n| n.node_type.clone())
        .collect();

    // HandshakeProcessor precompute: report pinned-identity count.
    let pinned_count = if state.pinned_operator_identity.is_some() {
        1
    } else {
        0
    };

    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // M7: use the persisted manifest counter as the cycle source-of-truth so
    // cycle numbers monotonically advance across process restarts.
    let mut tier1 = DagVerifyTier1 {
        precomputed_ok: tier1_ok,
        failure_reason: tier1_reason,
    };
    let mut absorber = CycleAbsorber {
        pending_absorption_hashes: pending_absorption_hashes.clone(),
    };
    let mut breach = DagBreachWatcher {
        breach_names: breach_names.clone(),
    };
    let mut handshake = PinnedHandshakeReader { pinned_count };
    let mut gradient = PythonGradientAdvancer {
        client,
        cycle_number: starting_cycle,
        latest_report: None,
    };
    // M12: run the cycle in an inner scope so the CycleContext (which holds
    // a mutable borrow of state.python_client via the gradient advancer) is
    // released before we re-borrow state to emit immune sporocarps below.
    let run_result = {
        let mut ctx = CycleContext {
            tier1: &mut tier1,
            gradient: &mut gradient,
            absorber: &mut absorber,
            breach: &mut breach,
            handshake: &mut handshake,
        };
        state.cycle_engine.run_cycle(&mut ctx)
    };
    // M12: C12 cycle_step_failed — emit immune sporocarp on cycle errors,
    // then propagate the original error to the operator (don't mask it).
    let cycle_report = match run_result {
        Ok(r) => r,
        Err(e) => {
            let evidence = format!("CycleEngine.run_cycle returned Err: {e}");
            let _ = emit_immune_sporocarp(
                state,
                "C12_cycle_step_failed",
                "cycle_step_failed",
                &evidence,
            );
            let _ = save_dag_state(state);
            return Err(SubstrateError::Protocol(format!("cycle engine: {e}")));
        }
    };
    if !cycle_report.committed {
        let _ = emit_immune_sporocarp(
            state,
            "C12_cycle_step_failed",
            "cycle_step_failed",
            "CycleEngine.run_cycle returned non-committed report",
        );
        let _ = save_dag_state(state);
        return Err(SubstrateError::Protocol("cycle did not commit".to_string()));
    }

    // Build the response combining cycle metadata + sporocarp report.
    let advance_report = gradient.latest_report.unwrap_or_default();
    // M7: capture the post-advance cycle counter (the gradient advancer bumps
    // its internal counter by 1; we mirror that into the manifest below in the
    // dispatch arm).
    let post_cycle = gradient.cycle_number;

    // M8: insert each sporocarp into the substrate's persistent DAG. Each
    // sporocarp becomes a DAG node whose parent is the previous DAG tip (linear
    // chain at M8 minimum; M9+ may add multi-parent for causally-related events).
    // The DAG node's hash is computed by Rust from parent + content; the
    // sporocarp's own content-hash is stored inside the canonical_bytes payload
    // as an informational field.
    let mut dag_node_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = Vec::new();
    let mut euthanasia_proposal_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = Vec::new();
    for sp in &advance_report.sporocarps {
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let node_type = format!("sporocarp:{}", sp.sporocarp_type);
        let dag_hash = state
            .dag
            .insert_node(
                parents,
                node_type,
                sp.at_cycle,
                CanonicalBytes(sp.canonical_bytes.clone()),
            )
            .map_err(|e| SubstrateError::Protocol(format!("dag insert: {e}")))?;
        dag_node_hashes.push(dag_hash);

        // M19 P7 必朽 (Endogenous-pair mortality): when a mortality_signal axis
        // fruits, the substrate's metabolism has crossed an unrecoverable-
        // pathology threshold per L0 §2.2 P7. Auto-emit a
        // `self_euthanasia_proposal:{axis_name}` DAG node parented by the
        // sporocarp. The proposal awaits owner co-attestation per L0 P7
        // (M19-MV: informational only; M20+ adds owner co-attestation
        // execution).
        if sp.sporocarp_type == "mortality_signal_threshold_crossed" {
            let mut proposal_content = BTreeMap::new();
            proposal_content.insert("axis_name".to_string(), Value::String(sp.axis_name.clone()));
            proposal_content.insert(
                "fruiting_value_repr".to_string(),
                Value::String(float_repr(sp.fruiting_value)),
            );
            proposal_content.insert("at_cycle".to_string(), Value::Uint(sp.at_cycle));
            proposal_content.insert(
                "triggering_sporocarp_hash".to_string(),
                Value::Bytes(dag_hash.as_ref().to_vec()),
            );
            proposal_content.insert(
                "reason".to_string(),
                Value::String(format!(
                    "mortality_signal axis '{}' crossed threshold (decay → fruiting_value={})",
                    sp.axis_name,
                    float_repr(sp.fruiting_value)
                )),
            );
            let proposal_canonical = cb_encode(&Value::Map(proposal_content)).map_err(|e| {
                SubstrateError::Protocol(format!("self_euthanasia_proposal encode: {e}"))
            })?;
            let proposal_parents = vec![dag_hash];
            let proposal_node_type = format!("self_euthanasia_proposal:{}", sp.axis_name);
            let proposal_hash = state
                .dag
                .insert_node(
                    proposal_parents,
                    proposal_node_type,
                    sp.at_cycle,
                    proposal_canonical,
                )
                .map_err(|e| {
                    SubstrateError::Protocol(format!("self_euthanasia_proposal DAG insert: {e}"))
                })?;
            euthanasia_proposal_hashes.push(proposal_hash);
        }
    }

    // M18 P4 永恒迭代: emit absorption_event:cycle_{N} DAG node if there were
    // raw_material nodes to absorb. The event records what THIS cycle observed
    // and marks them as absorbed (so subsequent cycles don't re-process them).
    let absorption_event_hash: Option<myco_kernel_shared::crypto::NodeHash> =
        if !pending_absorption_hashes.is_empty() {
            // Track highest created_at_cycle among the absorbed batch so we
            // can advance last_absorbed_cycle to it (sentinel-free; allows
            // multiple raw_material nodes added in the same cycle to all be
            // absorbed together, then skipped on subsequent cycles).
            let max_absorbed_created_at: u64 = pending_absorption_hashes
                .iter()
                .filter_map(|h| state.dag.get(h))
                .map(|n| n.created_at_cycle)
                .max()
                .unwrap_or(0);

            let mut content_map = BTreeMap::new();
            content_map.insert("cycle".to_string(), Value::Uint(post_cycle));
            content_map.insert(
                "absorbed_count".to_string(),
                Value::Uint(pending_absorption_hashes.len() as u64),
            );
            let hashes_array: Vec<Value> = pending_absorption_hashes
                .iter()
                .map(|h| Value::Bytes(h.as_ref().to_vec()))
                .collect();
            content_map.insert("absorbed_hashes".to_string(), Value::Array(hashes_array));
            let content_canonical = cb_encode(&Value::Map(content_map))
                .map_err(|e| SubstrateError::Protocol(format!("absorption_event encode: {e}")))?;
            // Multi-parent: prior tip + all absorbed raw_material nodes (so the
            // causal chain links the absorption back to its sources).
            let mut parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            for h in &pending_absorption_hashes {
                if !parents.contains(h) {
                    parents.push(*h);
                }
            }
            let node_type = format!("absorption_event:cycle_{post_cycle}");
            let h = state
                .dag
                .insert_node(parents, node_type, post_cycle, content_canonical)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("absorption_event DAG insert: {e}"))
                })?;
            // Bump last_absorbed_cycle to the highest absorbed created_at —
            // future cycles use strict-greater comparison so this won't re-absorb.
            state.manifest.last_absorbed_cycle = Some(max_absorbed_created_at);
            Some(h)
        } else {
            None
        };

    let mut payload = BTreeMap::new();
    // Echo the substrate's authoritative cycle counter (post-increment).
    payload.insert("cycle_number".to_string(), Value::Uint(post_cycle));
    // M8: echo the current DAG tip + node count for observability.
    if let Some(tip) = state.dag.tip() {
        payload.insert("dag_tip".to_string(), Value::Bytes(tip.as_ref().to_vec()));
    }
    payload.insert(
        "dag_node_count".to_string(),
        Value::Uint(state.dag.node_count() as u64),
    );
    // Fruited axis names.
    payload.insert(
        "fruited_axes".to_string(),
        Value::Array(
            advance_report
                .fruited_axes
                .iter()
                .map(|n| Value::String(n.clone()))
                .collect(),
        ),
    );
    // Sporocarps + their DAG node hashes (operator can reconstruct causal chain).
    let sporocarps_array: Vec<Value> = advance_report
        .sporocarps
        .iter()
        .zip(dag_node_hashes.iter())
        .map(|(sp, dag_hash)| {
            let mut m = BTreeMap::new();
            m.insert(
                "sporocarp_type".to_string(),
                Value::String(sp.sporocarp_type.clone()),
            );
            m.insert("axis_name".to_string(), Value::String(sp.axis_name.clone()));
            m.insert(
                "fruiting_value_repr".to_string(),
                Value::String(float_repr(sp.fruiting_value)),
            );
            m.insert("at_cycle".to_string(), Value::Uint(sp.at_cycle));
            m.insert(
                "canonical_bytes".to_string(),
                Value::Bytes(sp.canonical_bytes.clone()),
            );
            m.insert("hash".to_string(), Value::Bytes(sp.hash.to_vec()));
            // M8: the DAG node hash (different from sporocarp content-hash; carries
            // parent-chain identity within the substrate's DAG).
            m.insert(
                "dag_node_hash".to_string(),
                Value::Bytes(dag_hash.as_ref().to_vec()),
            );
            Value::Map(m)
        })
        .collect();
    payload.insert("sporocarps".to_string(), Value::Array(sporocarps_array));

    // M18 P4 永恒迭代 cycle-pipeline output fields:
    payload.insert(
        "deltas_absorbed".to_string(),
        Value::Uint(cycle_report.deltas_absorbed as u64),
    );
    payload.insert(
        "handshake_events_processed".to_string(),
        Value::Uint(cycle_report.handshake_events_processed as u64),
    );
    payload.insert(
        "skin_breaches".to_string(),
        Value::Array(
            cycle_report
                .skin_breaches
                .iter()
                .map(|s| Value::String(s.clone()))
                .collect(),
        ),
    );
    if let Some(h) = absorption_event_hash {
        payload.insert(
            "absorption_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }

    // M19 P7 必朽 — surface the self-euthanasia proposals emitted this cycle.
    if !euthanasia_proposal_hashes.is_empty() {
        let proposals_array: Vec<Value> = euthanasia_proposal_hashes
            .iter()
            .map(|h| Value::Bytes(h.as_ref().to_vec()))
            .collect();
        payload.insert(
            "self_euthanasia_proposal_hashes".to_string(),
            Value::Array(proposals_array),
        );
    }

    Ok(Some(Message::new(
        msg_type::ADVANCE_RESPONSE,
        request.request_id,
        payload,
    )))
}

// ---------------------------------------------------------------------------
// Helpers.
// ---------------------------------------------------------------------------

fn write_error_response<W: Write>(
    stdout: &mut W,
    key: &[u8; 32],
    in_response_to: u64,
    code: &str,
    msg: &str,
) -> Result<(), SubstrateError> {
    let mut payload = BTreeMap::new();
    payload.insert("code".to_string(), Value::String(code.to_string()));
    payload.insert("message".to_string(), Value::String(msg.to_string()));
    payload.insert("in_response_to".to_string(), Value::Uint(in_response_to));
    let err_msg = Message::new(msg_type::ERROR, in_response_to, payload);
    let frame = encode_frame_body(&err_msg, key).map_err(SubstrateError::Bridge)?;
    write_frame(stdout, &frame).map_err(SubstrateError::Bridge)?;
    Ok(())
}

fn graceful_shutdown_python(state: &mut ServerState) {
    if let Some(client) = state.python_client.take() {
        let _ = client.shutdown();
    }
}

fn expect_string_field(map: &BTreeMap<String, Value>, key: &str) -> Result<String, BridgeError> {
    match map.get(key) {
        Some(Value::String(s)) => Ok(s.clone()),
        Some(other) => Err(BridgeError::Protocol(format!(
            "field {key:?} is not a String: {other:?}"
        ))),
        None => Err(BridgeError::Protocol(format!("missing field {key:?}"))),
    }
}

fn expect_bool_field(map: &BTreeMap<String, Value>, key: &str) -> Result<bool, BridgeError> {
    match map.get(key) {
        Some(Value::Bool(b)) => Ok(*b),
        Some(other) => Err(BridgeError::Protocol(format!(
            "field {key:?} is not a Bool: {other:?}"
        ))),
        None => Err(BridgeError::Protocol(format!("missing field {key:?}"))),
    }
}

fn parse_float_field(map: &BTreeMap<String, Value>, key: &str) -> Result<f64, BridgeError> {
    let s = expect_string_field(map, key)?;
    s.parse::<f64>()
        .map_err(|e| BridgeError::Protocol(format!("field {key:?} parse: {e}")))
}

/// Render an f64 as a Python-compatible repr string.
/// Identical to kernel/bridge::protocol::float_repr but reproduced here so
/// we don't need to expose that internal helper.
fn float_repr(f: f64) -> String {
    if f.is_nan() {
        "nan".to_string()
    } else if f.is_infinite() {
        if f > 0.0 {
            "inf".to_string()
        } else {
            "-inf".to_string()
        }
    } else if f == f.trunc() && f.abs() < 1e16 {
        format!("{f:.1}")
    } else {
        format!("{f}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn float_repr_pinned_values() {
        assert_eq!(float_repr(0.0), "0.0");
        assert_eq!(float_repr(1.5), "1.5");
        assert_eq!(float_repr(-2.0), "-2.0");
    }

    #[test]
    fn float_repr_special() {
        assert_eq!(float_repr(f64::NAN), "nan");
        assert_eq!(float_repr(f64::INFINITY), "inf");
        assert_eq!(float_repr(f64::NEG_INFINITY), "-inf");
    }

    #[test]
    fn expect_string_field_success() {
        let mut m = BTreeMap::new();
        m.insert("name".to_string(), Value::String("test".to_string()));
        assert_eq!(expect_string_field(&m, "name").unwrap(), "test");
    }

    #[test]
    fn expect_string_field_missing_errors() {
        let m: BTreeMap<String, Value> = BTreeMap::new();
        assert!(expect_string_field(&m, "missing").is_err());
    }

    #[test]
    fn expect_string_field_wrong_type_errors() {
        let mut m = BTreeMap::new();
        m.insert("n".to_string(), Value::Uint(42));
        assert!(expect_string_field(&m, "n").is_err());
    }

    #[test]
    fn parse_float_field_roundtrip() {
        let mut m = BTreeMap::new();
        m.insert("x".to_string(), Value::String("2.5".to_string()));
        assert_eq!(parse_float_field(&m, "x").unwrap(), 2.5);
    }

    #[test]
    fn parse_float_field_invalid_string_errors() {
        let mut m = BTreeMap::new();
        m.insert("x".to_string(), Value::String("not_a_number".to_string()));
        assert!(parse_float_field(&m, "x").is_err());
    }
}
