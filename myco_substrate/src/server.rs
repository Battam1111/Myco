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
use myco_kernel_shared::canonical_bytes::Value;

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
}

impl ServerState {
    fn new() -> Self {
        ServerState {
            session_secret: [0u8; 32],
            handshake_complete: false,
            python_client: None,
            cycle_engine: CycleEngine::new(CycleConfig::default()),
        }
    }
}

// ---------------------------------------------------------------------------
// Public server entry point.
// ---------------------------------------------------------------------------

/// Run the substrate server loop against the given stdin/stdout.
///
/// Returns the exit code (0 = clean shutdown, 2 = handshake failure).
pub fn run_loop<R: Read, W: Write>(stdin: &mut R, stdout: &mut W) -> Result<u8, SubstrateError> {
    let mut state = ServerState::new();

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
        msg_type::REGISTER_AXIS => forward_to_python(state, request, msg_type::REGISTER_AXIS_ACK),
        msg_type::PERTURB => forward_to_python(state, request, msg_type::PERTURB_ACK),
        msg_type::SNAPSHOT => forward_to_python(state, request, msg_type::SNAPSHOT_RESPONSE),
        msg_type::ADVANCE => handle_advance(state, request),
        msg_type::SHUTDOWN => Ok(Some(Message::new(
            msg_type::SHUTDOWN_ACK,
            request.request_id,
            empty_payload(),
        ))),
        other => Err(SubstrateError::Protocol(format!(
            "substrate cannot handle message type {other:?}"
        ))),
    }
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
    };
    let python_client = BridgeClient::spawn_and_handshake(python_config)?;
    let python_version = python_client.hello_ack.python_version.clone();
    let kernel_tropism_version = python_client.hello_ack.kernel_tropism_version.clone();
    state.python_client = Some(python_client);
    state.handshake_complete = true;

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
    Ok(Some(Message::new(
        msg_type::HELLO_ACK,
        request.request_id,
        payload,
    )))
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

    let starting_cycle = state.cycle_engine.current_cycle();
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
    let mut payload = BTreeMap::new();
    // Echo the substrate's authoritative cycle counter (post-increment).
    payload.insert(
        "cycle_number".to_string(),
        Value::Uint(state.cycle_engine.current_cycle()),
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
    // Sporocarps (full canonical-bytes + hash for DAG insertion downstream).
    let sporocarps_array: Vec<Value> = advance_report
        .sporocarps
        .iter()
        .map(|sp| {
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
