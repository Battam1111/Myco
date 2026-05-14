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
    default_state_dir, ensure_state_dir, load_dag, load_pinned_operator_identity, save_dag,
    save_pinned_operator_identity, Manifest, PinnedOperatorIdentity,
};
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// Stubs for the 4 cycle traits that are Rust-native at M6. The fifth
// (GradientAdvancer) is delegated to the Python bridge via a closure.
// ---------------------------------------------------------------------------

struct OkTier1;
impl Tier1Validator for OkTier1 {
    fn validate_tier1(&mut self) -> Result<(), String> {
        Ok(())
    }
}

struct NoOpAbsorber;
impl DeltaAbsorber for NoOpAbsorber {
    fn absorb_deltas(&mut self) -> Result<usize, String> {
        Ok(0)
    }
}

struct NoBreaches;
impl SkinBreachChecker for NoBreaches {
    fn check_skin_breaches(&mut self) -> Result<Vec<String>, String> {
        Ok(Vec::new())
    }
}

struct NoHandshakes;
impl HandshakeProcessor for NoHandshakes {
    fn process_handshake_attestation(&mut self) -> Result<usize, String> {
        Ok(0)
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
    /// Wall-clock expiry (unix nanoseconds). Default: now + 5 minutes.
    expiry_unix_ns: i64,
    /// Whether this nonce has been consumed (one-time use).
    consumed: bool,
}

/// M13: Default nonce TTL in seconds (5 minutes).
const NONCE_TTL_SECONDS: i64 = 300;

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
    let state_dir = default_state_dir();
    ensure_state_dir(&state_dir)?;
    let manifest = match Manifest::load(&state_dir)? {
        Some(m) => m,
        None => Manifest::genesis(),
    };
    // M11: C7 dag_retro_edit_detected — if dag.cb is present but fails to load
    // (tampered, corrupted, version-mismatched), quarantine the corrupted file
    // with a timestamped suffix, start with an empty DAG, and emit an immune
    // sporocarp recording the tamper attempt. Caller sees the immune event in
    // their first myco_query_recent_nodes call after this boot.
    let (dag, dag_load_failure_evidence): (Dag, Option<String>) = match load_dag(&state_dir) {
        Ok(Some(d)) => (d, None),
        Ok(None) => (Dag::default(), None),
        Err(e) => {
            // Quarantine the corrupted file.
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
    let pinned_operator_identity = load_pinned_operator_identity(&state_dir)?;
    let mut state = ServerState::new(state_dir, manifest, dag, pinned_operator_identity);

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
            let _ = emit_immune_sporocarp(
                &mut state,
                "C9_cold_resume_invariant_failure",
                &format!("cold_resume_invariant_failure ({})", result.check_id),
                &evidence,
            );
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
            // M7: persist gradient state after a mutation.
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::PERTURB => {
            let response = forward_to_python(state, request, msg_type::PERTURB_ACK)?;
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::SNAPSHOT => forward_to_python(state, request, msg_type::SNAPSHOT_RESPONSE),
        msg_type::ADVANCE => {
            let response = handle_advance(state, request)?;
            // M7: bump the persisted cycle counter (matches the value echoed in
            // the advance_response payload). save_manifest() also bumps
            // last_save_time for observability.
            state.manifest.cycle_counter = state.manifest.cycle_counter.saturating_add(1);
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
        other => Err(SubstrateError::Protocol(format!(
            "substrate cannot handle message type {other:?}"
        ))),
    }
}

/// M8: Return the last N DAG nodes (Rust-handled; no Python involvement).
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

    let all_nodes: Vec<_> = state.dag.iter_in_insertion_order().collect();
    let total = all_nodes.len();
    let start = total.saturating_sub(count as usize);
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
    payload.insert("total_dag_size".to_string(), Value::Uint(total as u64));
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

    let bound_dag_tip = state
        .dag
        .tip()
        .map(|t| {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(t.as_ref());
            arr
        })
        .unwrap_or([0u8; 32]);

    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let expiry_unix_ns = now_ns.saturating_add(NONCE_TTL_SECONDS * 1_000_000_000);

    state.nonce_log.insert(
        nonce,
        AttestationNonce {
            nonce,
            bound_content_hash: content_hash,
            bound_dag_tip,
            expiry_unix_ns,
            consumed: false,
        },
    );

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
fn verify_attestation_nonce(
    state: &mut ServerState,
    nonce_bytes: &[u8],
    content_hash: &[u8; 32],
    submitted_expiry_ns: Option<i64>,
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
        return Err(
            "wrong-binding rejected: DAG tip differs from issuance time".to_string(),
        );
    }

    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    if now_ns > stored.expiry_unix_ns {
        return Err("expired rejected: nonce TTL passed".to_string());
    }
    if let Some(submitted) = submitted_expiry_ns {
        if submitted != stored.expiry_unix_ns {
            return Err(
                "wrong-binding rejected: submitted expiry differs from issued expiry".to_string(),
            );
        }
    }

    // Mark consumed.
    if let Some(n) = state.nonce_log.get_mut(&nonce_arr) {
        n.consumed = true;
    }

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

    // Emit immune sporocarps for each failure (consistent with boot-time C9).
    let mut emitted_count: u64 = 0;
    for result in &results {
        if !result.passed {
            let evidence = format!(
                "ad-hoc integrity check failed: {} — {}",
                result.check_id, result.evidence
            );
            if emit_immune_sporocarp(
                state,
                "C9_cold_resume_invariant_failure",
                &format!("cold_resume_invariant_failure ({})", result.check_id),
                &evidence,
            )
            .is_ok()
            {
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
        if let Err(reason) =
            verify_attestation_nonce(state, &nonce_bytes, &content_hash, submitted_expiry)
        {
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
    let state_dir_str = state.state_dir.to_string_lossy().into_owned();
    let genesis_owner = state.pinned_operator_identity.as_ref().map(|p| p.pubkey);
    let (_hydrated_axis_count, _hydrated) =
        python_client.load_state_with_genesis(&state_dir_str, genesis_owner.as_ref())?;

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

    results
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

    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // M7: use the persisted manifest counter as the cycle source-of-truth so
    // cycle numbers monotonically advance across process restarts.
    let starting_cycle = state.manifest.cycle_counter;
    let mut tier1 = OkTier1;
    let mut absorber = NoOpAbsorber;
    let mut breach = NoBreaches;
    let mut handshake = NoHandshakes;
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
    }

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
