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
use myco_kernel_shared::canonical_bytes::{CanonicalBytes, Value};

use crate::persistence::{default_state_dir, ensure_state_dir, load_dag, save_dag, Manifest};
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
}

impl ServerState {
    fn new(state_dir: PathBuf, manifest: Manifest, dag: Dag) -> Self {
        // M7: the manifest's cycle_counter is the authoritative persisted
        // counter; the in-process CycleEngine maintains its own counter that
        // counts cycles within THIS process only. handle_advance() uses the
        // manifest counter as the cross-process source-of-truth.
        // M8: dag carries the substrate's causal history (sporocarps + future event types).
        ServerState {
            session_secret: [0u8; 32],
            handshake_complete: false,
            python_client: None,
            cycle_engine: CycleEngine::new(CycleConfig::default()),
            manifest,
            state_dir,
            dag,
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
    let dag = load_dag(&state_dir)?.unwrap_or_default();
    let mut state = ServerState::new(state_dir, manifest, dag);

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

    // M7 cold-resume: ask the Python worker to hydrate from disk, if a
    // gradient.cb exists in our state directory. Genesis condition →
    // hydrated=false; the worker starts with an empty gradient.
    let state_dir_str = state.state_dir.to_string_lossy().into_owned();
    let (_hydrated_axis_count, _hydrated) = python_client.load_state(&state_dir_str)?;

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
    {
        let mut ctx = CycleContext {
            tier1: &mut tier1,
            gradient: &mut gradient,
            absorber: &mut absorber,
            breach: &mut breach,
            handshake: &mut handshake,
        };
        let cycle_report = state
            .cycle_engine
            .run_cycle(&mut ctx)
            .map_err(|e| SubstrateError::Protocol(format!("cycle engine: {e}")))?;
        if !cycle_report.committed {
            return Err(SubstrateError::Protocol("cycle did not commit".to_string()));
        }
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
