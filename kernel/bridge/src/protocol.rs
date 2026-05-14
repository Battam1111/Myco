//! Bridge wire protocol — message types, body encode/decode, HMAC integrity.
//!
//! See crate-level documentation for the wire-format diagram.
//!
//! ## Encoding pattern
//!
//! All bridge messages share a common envelope shape:
//!
//! ```text
//!  body = canonical_bytes(Map({
//!      "v":          Uint(PROTOCOL_VERSION),
//!      "type":       String(message_type),
//!      "request_id": Uint(correlation_id),
//!      "payload":    Map(...),  // type-specific
//!  }))
//!  frame_body = HMAC-SHA256(body, key=session_secret) || body
//! ```
//!
//! Where the key is [`BOOTSTRAP_KEY`] for the `hello` message and the
//! exchanged session_secret for everything else.

use std::collections::BTreeMap;

use hmac::{Hmac, Mac};
use myco_kernel_shared::canonical_bytes::{
    decode as cb_decode, encode as cb_encode, map_get_array, map_get_bytes, map_get_map,
    map_get_string, map_get_uint, CanonicalBytes, CanonicalBytesError, Value,
};
use sha2::Sha256;

use crate::BridgeError;

/// Protocol version (M5 = 1). Bumped on any breaking change.
pub const PROTOCOL_VERSION: u64 = 1;

/// HMAC-SHA256 output size in bytes.
pub const HMAC_SIZE: usize = 32;

/// Maximum frame body+hmac size on the wire (1 MiB). DoS protection.
pub const MAX_FRAME_BODY_SIZE: usize = 1024 * 1024;

/// Deterministic bootstrap key for the `hello` message HMAC.
///
/// Computed as SHA-256(b"myco-bridge-protocol-v1-bootstrap"). This is **not**
/// a real secret — the IPC channel is the trust boundary. The bootstrap key
/// is a constant chosen to make protocol-version rollover explicit.
pub fn bootstrap_key() -> [u8; 32] {
    use sha2::Digest;
    let mut h = Sha256::new();
    h.update(b"myco-bridge-protocol-v1-bootstrap");
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

/// Message type string constants. Mirrors Python `MessageType` enum values.
pub mod msg_type {
    /// `hello` — Rust→Python: bootstrap handshake; transports session_secret.
    pub const HELLO: &str = "hello";
    /// `hello_ack` — Python→Rust: acknowledges hello; reports versions.
    pub const HELLO_ACK: &str = "hello_ack";
    /// `register_axis` — Rust→Python: register a gradient axis.
    pub const REGISTER_AXIS: &str = "register_axis";
    /// `register_axis_ack` — Python→Rust: axis registered.
    pub const REGISTER_AXIS_ACK: &str = "register_axis_ack";
    /// `perturb` — Rust→Python: apply a delta to an axis.
    pub const PERTURB: &str = "perturb";
    /// `perturb_ack` — Python→Rust: perturbation applied.
    pub const PERTURB_ACK: &str = "perturb_ack";
    /// `advance` — Rust→Python: run one cycle of gradient evolution.
    pub const ADVANCE: &str = "advance";
    /// `advance_response` — Python→Rust: fruited axes + sporocarps.
    pub const ADVANCE_RESPONSE: &str = "advance_response";
    /// `snapshot` — Rust→Python: read current gradient state.
    pub const SNAPSHOT: &str = "snapshot";
    /// `snapshot_response` — Python→Rust: current axis values.
    pub const SNAPSHOT_RESPONSE: &str = "snapshot_response";
    /// `shutdown` — Rust→Python: graceful exit signal.
    pub const SHUTDOWN: &str = "shutdown";
    /// `shutdown_ack` — Python→Rust: about to exit.
    pub const SHUTDOWN_ACK: &str = "shutdown_ack";
    /// `error` — either direction: error envelope.
    pub const ERROR: &str = "error";
    /// `save_state` — Rust→Python: persist gradient state to `state_dir` (M7).
    pub const SAVE_STATE: &str = "save_state";
    /// `save_state_ack` — Python→Rust: gradient state persisted.
    pub const SAVE_STATE_ACK: &str = "save_state_ack";
    /// `load_state` — Rust→Python: hydrate gradient state from `state_dir` (M7).
    pub const LOAD_STATE: &str = "load_state";
    /// `load_state_ack` — Python→Rust: gradient state hydrated; carries axis count.
    pub const LOAD_STATE_ACK: &str = "load_state_ack";
    /// `compute_intent` — Operator/Rust→Python: derive intent from a DAG subset (M8).
    pub const COMPUTE_INTENT: &str = "compute_intent";
    /// `compute_intent_response` — Python→Rust: cluster_C result over the subset.
    pub const COMPUTE_INTENT_RESPONSE: &str = "compute_intent_response";
    /// `query_recent_nodes` — Operator→Rust: list last N DAG nodes for diagnostics (M8).
    /// Handled by Rust substrate; not forwarded to Python.
    pub const QUERY_RECENT_NODES: &str = "query_recent_nodes";
    /// `query_recent_nodes_response` — Rust→Operator: enumerated recent DAG nodes.
    pub const QUERY_RECENT_NODES_RESPONSE: &str = "query_recent_nodes_response";
    /// `submit_mutation` — Operator→Rust→Python: submit a mutation for classification + (CI) attestation (M10).
    pub const SUBMIT_MUTATION: &str = "submit_mutation";
    /// `submit_mutation_response` — Python→Rust→Operator: classification + accepted + content.
    pub const SUBMIT_MUTATION_RESPONSE: &str = "submit_mutation_response";
    /// `query_immune_events` — Operator→Rust: list recent immune sporocarps (M11).
    /// Filters DAG by node_type prefix "immune:".
    pub const QUERY_IMMUNE_EVENTS: &str = "query_immune_events";
    /// `query_immune_events_response` — Rust→Operator: enumerated immune sporocarps.
    pub const QUERY_IMMUNE_EVENTS_RESPONSE: &str = "query_immune_events_response";
}

/// A decoded bridge message.
#[derive(Debug, Clone)]
pub struct Message {
    /// Protocol version. Always 1 on a valid M5 frame.
    pub version: u64,
    /// Message type tag (one of [`msg_type`] constants).
    pub message_type: String,
    /// Correlation ID; request ↔ response share this value.
    pub request_id: u64,
    /// Type-specific payload Map.
    pub payload: BTreeMap<String, Value>,
}

impl Message {
    /// Construct a new message.
    pub fn new(
        message_type: impl Into<String>,
        request_id: u64,
        payload: BTreeMap<String, Value>,
    ) -> Self {
        Message {
            version: PROTOCOL_VERSION,
            message_type: message_type.into(),
            request_id,
            payload,
        }
    }

    /// Encode the message body (NOT including HMAC or length prefix) to canonical bytes.
    pub fn to_body_canonical_bytes(&self) -> Result<CanonicalBytes, CanonicalBytesError> {
        let mut body = BTreeMap::new();
        body.insert("v".to_string(), Value::Uint(self.version));
        body.insert("type".to_string(), Value::String(self.message_type.clone()));
        body.insert("request_id".to_string(), Value::Uint(self.request_id));
        body.insert("payload".to_string(), Value::Map(self.payload.clone()));
        cb_encode(&Value::Map(body))
    }

    /// Decode a Message from a canonical-bytes body.
    pub fn from_body_canonical_bytes(body: &[u8]) -> Result<Self, BridgeError> {
        let decoded = cb_decode(body).map_err(BridgeError::from)?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(BridgeError::Protocol(format!(
                    "body is not a Map: {other:?}"
                )))
            }
        };
        let version = map_get_uint(&map, "v").map_err(|e| BridgeError::Protocol(e.to_string()))?;
        if version != PROTOCOL_VERSION {
            return Err(BridgeError::Protocol(format!(
                "protocol version mismatch: got {version}, expected {PROTOCOL_VERSION}"
            )));
        }
        let message_type = map_get_string(&map, "type")
            .map_err(|e| BridgeError::Protocol(e.to_string()))?
            .to_string();
        let request_id =
            map_get_uint(&map, "request_id").map_err(|e| BridgeError::Protocol(e.to_string()))?;
        let payload = map_get_map(&map, "payload")
            .map_err(|e| BridgeError::Protocol(e.to_string()))?
            .clone();
        Ok(Message {
            version,
            message_type,
            request_id,
            payload,
        })
    }
}

// ---------------------------------------------------------------------------
// HMAC compute / verify.
// ---------------------------------------------------------------------------

type HmacSha256 = Hmac<Sha256>;

/// Compute HMAC-SHA256 over `body` bytes with `key`. Returns 32 bytes.
pub fn compute_hmac(body: &[u8], key: &[u8]) -> Result<[u8; 32], BridgeError> {
    if key.is_empty() {
        return Err(BridgeError::Protocol(
            "HMAC key cannot be empty (per L1_SKIN §2)".to_string(),
        ));
    }
    let mut mac =
        HmacSha256::new_from_slice(key).map_err(|e| BridgeError::Protocol(e.to_string()))?;
    mac.update(body);
    let result = mac.finalize().into_bytes();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    Ok(out)
}

/// Verify HMAC in constant time. Returns Ok(()) on match, error otherwise.
pub fn verify_hmac(body: &[u8], key: &[u8], expected: &[u8]) -> Result<(), BridgeError> {
    if key.is_empty() {
        return Err(BridgeError::Protocol(
            "HMAC key cannot be empty".to_string(),
        ));
    }
    if expected.len() != HMAC_SIZE {
        return Err(BridgeError::HmacMismatch(format!(
            "HMAC size {} != expected {HMAC_SIZE}",
            expected.len()
        )));
    }
    let mut mac =
        HmacSha256::new_from_slice(key).map_err(|e| BridgeError::Protocol(e.to_string()))?;
    mac.update(body);
    mac.verify_slice(expected)
        .map_err(|_| BridgeError::HmacMismatch("HMAC verification failed".to_string()))
}

// ---------------------------------------------------------------------------
// Full frame body (HMAC + canonical-bytes body) encode / decode.
// ---------------------------------------------------------------------------

/// Encode a message into a frame body (HMAC + canonical-bytes body).
///
/// The caller (framing layer) prepends the u32 BE length prefix.
pub fn encode_frame_body(message: &Message, key: &[u8]) -> Result<Vec<u8>, BridgeError> {
    let body = message.to_body_canonical_bytes()?;
    let body_bytes = body.0;
    let hmac = compute_hmac(&body_bytes, key)?;
    let mut frame = Vec::with_capacity(HMAC_SIZE + body_bytes.len());
    frame.extend_from_slice(&hmac);
    frame.extend_from_slice(&body_bytes);
    Ok(frame)
}

/// Decode a frame body (HMAC + canonical-bytes body) into a [`Message`].
pub fn decode_frame_body(frame: &[u8], key: &[u8]) -> Result<Message, BridgeError> {
    if frame.len() < HMAC_SIZE {
        return Err(BridgeError::Protocol(format!(
            "frame body too small: {} < HMAC size {HMAC_SIZE}",
            frame.len()
        )));
    }
    let (hmac_received, body_bytes) = frame.split_at(HMAC_SIZE);
    verify_hmac(body_bytes, key, hmac_received)?;
    Message::from_body_canonical_bytes(body_bytes)
}

// ---------------------------------------------------------------------------
// Payload builders for common message types.
// ---------------------------------------------------------------------------

/// Build the payload for a `hello` request.
pub fn hello_payload(session_secret: &[u8; 32]) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert(
        "session_secret".to_string(),
        Value::Bytes(session_secret.to_vec()),
    );
    m
}

/// Build the payload for a `register_axis` request.
#[allow(clippy::too_many_arguments)]
pub fn register_axis_payload(
    name: &str,
    axis_class: &str,
    fruiting_threshold: f64,
    initial_value: f64,
    decay_rate_per_cycle: f64,
    is_mortality_signal: bool,
    update_rule_kind: &str,
) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert("name".to_string(), Value::String(name.to_string()));
    m.insert(
        "axis_class".to_string(),
        Value::String(axis_class.to_string()),
    );
    m.insert(
        "fruiting_threshold_repr".to_string(),
        Value::String(float_repr(fruiting_threshold)),
    );
    m.insert(
        "initial_value_repr".to_string(),
        Value::String(float_repr(initial_value)),
    );
    m.insert(
        "decay_rate_per_cycle_repr".to_string(),
        Value::String(float_repr(decay_rate_per_cycle)),
    );
    m.insert(
        "is_mortality_signal".to_string(),
        Value::Bool(is_mortality_signal),
    );
    m.insert(
        "update_rule_kind".to_string(),
        Value::String(update_rule_kind.to_string()),
    );
    m
}

/// Build the payload for a `perturb` request.
pub fn perturb_payload(axis_name: &str, delta: f64) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert(
        "axis_name".to_string(),
        Value::String(axis_name.to_string()),
    );
    m.insert("delta_repr".to_string(), Value::String(float_repr(delta)));
    m
}

/// Build the payload for an `advance` request.
pub fn advance_payload(current_cycle: u64) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert("current_cycle".to_string(), Value::Uint(current_cycle));
    m
}

/// Empty payload (snapshot, *_ack, shutdown).
pub fn empty_payload() -> BTreeMap<String, Value> {
    BTreeMap::new()
}

/// Build the payload for a `save_state` or `load_state` request.
///
/// Both messages share the same payload shape: a single `state_dir` string
/// pointing at the directory the Python worker should read/write its
/// gradient.cb file in.
pub fn state_dir_payload(state_dir: &str) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert(
        "state_dir".to_string(),
        Value::String(state_dir.to_string()),
    );
    m
}

/// Build the payload for a `load_state_ack` response carrying the count of
/// hydrated axes and whether a state file actually existed.
pub fn load_state_ack_payload(axis_count: u64, hydrated: bool) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert("axis_count".to_string(), Value::Uint(axis_count));
    m.insert("hydrated".to_string(), Value::Bool(hydrated));
    m
}

/// Build the payload for a `compute_intent` request (M8).
///
/// `dag_nodes` is an Array<Map> with these per-node fields:
/// - `hash`: Bytes(32)
/// - `parent_hashes`: Array<Bytes(32)>
/// - `at_cycle`: Uint
/// - `node_type`: String
pub fn compute_intent_payload(
    pivot_hash: &[u8; 32],
    radius_cycles: u64,
    dag_nodes: Vec<Value>,
) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert("pivot_hash".to_string(), Value::Bytes(pivot_hash.to_vec()));
    m.insert("radius_cycles".to_string(), Value::Uint(radius_cycles));
    m.insert("dag_nodes".to_string(), Value::Array(dag_nodes));
    m
}

/// Build the payload for a `query_recent_nodes` request (M8).
pub fn query_recent_nodes_payload(count: u64) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert("count".to_string(), Value::Uint(count));
    m
}

/// Build the payload for a `submit_mutation` request (M10).
///
/// `attestation_signature` is `None` for daily mutations and `Some(64 bytes)`
/// for CI mutations (Ed25519 signature over `content_canonical_bytes` by
/// the active owner key).
pub fn submit_mutation_payload(
    mutation_type: &str,
    touched_fields: Vec<String>,
    touched_files: Vec<String>,
    touched_meta_structures: Vec<String>,
    content_canonical_bytes: Vec<u8>,
    attestation_signature: Option<[u8; 64]>,
) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert(
        "mutation_type".to_string(),
        Value::String(mutation_type.to_string()),
    );
    m.insert(
        "touched_fields".to_string(),
        Value::Array(touched_fields.into_iter().map(Value::String).collect()),
    );
    m.insert(
        "touched_files".to_string(),
        Value::Array(touched_files.into_iter().map(Value::String).collect()),
    );
    m.insert(
        "touched_meta_structures".to_string(),
        Value::Array(
            touched_meta_structures
                .into_iter()
                .map(Value::String)
                .collect(),
        ),
    );
    m.insert(
        "content_canonical_bytes".to_string(),
        Value::Bytes(content_canonical_bytes),
    );
    if let Some(sig) = attestation_signature {
        m.insert(
            "attestation_signature".to_string(),
            Value::Bytes(sig.to_vec()),
        );
    }
    m
}

/// Render a float as a Python-compatible repr string.
///
/// This is the cross-language float-encoding convention: instead of binary
/// IEEE 754 (which has cross-language reproducibility hazards around NaN
/// payloads and signaling bits), we round-trip floats via their string
/// representations. Both sides parse the string back into a float.
pub fn float_repr(f: f64) -> String {
    if f.is_nan() {
        "nan".to_string()
    } else if f.is_infinite() {
        if f > 0.0 {
            "inf".to_string()
        } else {
            "-inf".to_string()
        }
    } else if f == f.trunc() && f.abs() < 1e16 {
        // Integer-valued float: match Python's repr (e.g., "0.0", "1.0", "-2.5").
        format!("{f:.1}")
    } else {
        format!("{f}")
    }
}

// ---------------------------------------------------------------------------
// Advance-response decoder helpers.
// ---------------------------------------------------------------------------

/// Description of a single sporocarp returned in an `advance_response`.
#[derive(Debug, Clone)]
pub struct SporocarpReport {
    /// Sporocarp subtype tag (e.g. "appetite_fruiting").
    pub sporocarp_type: String,
    /// Axis name that fruited this sporocarp.
    pub axis_name: String,
    /// Fruiting value (parsed from repr string).
    pub fruiting_value: f64,
    /// Substrate cycle counter at fruiting.
    pub at_cycle: u64,
    /// Sporocarp canonical-bytes encoding (for DAG insertion).
    pub canonical_bytes: Vec<u8>,
    /// Sporocarp content-hash (Merkle-style; 32 bytes).
    pub hash: [u8; 32],
}

/// Parsed `advance_response` payload.
#[derive(Debug, Clone, Default)]
pub struct AdvanceReport {
    /// Names of axes that fruited this cycle (in order).
    pub fruited_axes: Vec<String>,
    /// One sporocarp per fruited axis, in the same order.
    pub sporocarps: Vec<SporocarpReport>,
}

/// Parse a Message of type `advance_response` into an [`AdvanceReport`].
pub fn parse_advance_response(response: &Message) -> Result<AdvanceReport, BridgeError> {
    if response.message_type != msg_type::ADVANCE_RESPONSE {
        return Err(BridgeError::Protocol(format!(
            "expected advance_response; got {}",
            response.message_type
        )));
    }
    let fruited_array = map_get_array(&response.payload, "fruited_axes")
        .map_err(|e| BridgeError::Protocol(e.to_string()))?;
    let mut fruited_axes = Vec::with_capacity(fruited_array.len());
    for v in fruited_array {
        match v {
            Value::String(s) => fruited_axes.push(s.clone()),
            other => {
                return Err(BridgeError::Protocol(format!(
                    "fruited_axes contains non-String: {other:?}"
                )))
            }
        }
    }
    let sporocarps_array = map_get_array(&response.payload, "sporocarps")
        .map_err(|e| BridgeError::Protocol(e.to_string()))?;
    let mut sporocarps = Vec::with_capacity(sporocarps_array.len());
    for v in sporocarps_array {
        match v {
            Value::Map(sp_map) => {
                let sporocarp_type = map_get_string(sp_map, "sporocarp_type")
                    .map_err(|e| BridgeError::Protocol(e.to_string()))?
                    .to_string();
                let axis_name = map_get_string(sp_map, "axis_name")
                    .map_err(|e| BridgeError::Protocol(e.to_string()))?
                    .to_string();
                let fruiting_value_repr = map_get_string(sp_map, "fruiting_value_repr")
                    .map_err(|e| BridgeError::Protocol(e.to_string()))?;
                let fruiting_value: f64 = fruiting_value_repr.parse().map_err(|e| {
                    BridgeError::Protocol(format!("fruiting_value_repr parse: {e}"))
                })?;
                let at_cycle = map_get_uint(sp_map, "at_cycle")
                    .map_err(|e| BridgeError::Protocol(e.to_string()))?;
                let canonical_bytes_slice = map_get_bytes(sp_map, "canonical_bytes")
                    .map_err(|e| BridgeError::Protocol(e.to_string()))?;
                let hash_slice = map_get_bytes(sp_map, "hash")
                    .map_err(|e| BridgeError::Protocol(e.to_string()))?;
                if hash_slice.len() != 32 {
                    return Err(BridgeError::Protocol(format!(
                        "sporocarp.hash size {} != 32",
                        hash_slice.len()
                    )));
                }
                let mut hash = [0u8; 32];
                hash.copy_from_slice(hash_slice);
                sporocarps.push(SporocarpReport {
                    sporocarp_type,
                    axis_name,
                    fruiting_value,
                    at_cycle,
                    canonical_bytes: canonical_bytes_slice.to_vec(),
                    hash,
                });
            }
            other => {
                return Err(BridgeError::Protocol(format!(
                    "sporocarps contains non-Map: {other:?}"
                )))
            }
        }
    }
    Ok(AdvanceReport {
        fruited_axes,
        sporocarps,
    })
}

/// Parsed `snapshot_response` payload — a map of axis name to current value.
pub fn parse_snapshot_response(response: &Message) -> Result<BTreeMap<String, f64>, BridgeError> {
    if response.message_type != msg_type::SNAPSHOT_RESPONSE {
        return Err(BridgeError::Protocol(format!(
            "expected snapshot_response; got {}",
            response.message_type
        )));
    }
    let values_map = map_get_map(&response.payload, "values")
        .map_err(|e| BridgeError::Protocol(e.to_string()))?;
    let mut out = BTreeMap::new();
    for (k, v) in values_map {
        match v {
            Value::String(s) => {
                let f: f64 = s
                    .parse()
                    .map_err(|e| BridgeError::Protocol(format!("snapshot value parse: {e}")))?;
                out.insert(k.clone(), f);
            }
            other => {
                return Err(BridgeError::Protocol(format!(
                    "snapshot value for {k:?} is not String: {other:?}"
                )))
            }
        }
    }
    Ok(out)
}

/// Parsed `hello_ack` payload.
#[derive(Debug, Clone)]
pub struct HelloAck {
    /// Reported kernel/tropism version on the Python side.
    pub kernel_tropism_version: String,
    /// Reported Python interpreter version.
    pub python_version: String,
}

/// Parse a Message of type `hello_ack`.
pub fn parse_hello_ack(response: &Message) -> Result<HelloAck, BridgeError> {
    if response.message_type != msg_type::HELLO_ACK {
        return Err(BridgeError::Protocol(format!(
            "expected hello_ack; got {}",
            response.message_type
        )));
    }
    let kernel_tropism_version = map_get_string(&response.payload, "kernel_tropism_version")
        .map_err(|e| BridgeError::Protocol(e.to_string()))?
        .to_string();
    let python_version = map_get_string(&response.payload, "python_version")
        .map_err(|e| BridgeError::Protocol(e.to_string()))?
        .to_string();
    Ok(HelloAck {
        kernel_tropism_version,
        python_version,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bootstrap_key_is_32_bytes() {
        let key = bootstrap_key();
        assert_eq!(key.len(), 32);
    }

    #[test]
    fn bootstrap_key_is_deterministic() {
        assert_eq!(bootstrap_key(), bootstrap_key());
    }

    #[test]
    fn bootstrap_key_specific_value() {
        // Pinned: any change here is a protocol-version bump.
        use sha2::Digest;
        let mut h = Sha256::new();
        h.update(b"myco-bridge-protocol-v1-bootstrap");
        let expected = h.finalize();
        assert_eq!(bootstrap_key(), expected.as_slice());
    }

    #[test]
    fn body_encode_decode_roundtrip_hello() {
        let session_secret = [0xa5u8; 32];
        let msg = Message::new(msg_type::HELLO, 1, hello_payload(&session_secret));
        let body = msg.to_body_canonical_bytes().unwrap();
        let decoded = Message::from_body_canonical_bytes(&body.0).unwrap();
        assert_eq!(decoded.message_type, msg_type::HELLO);
        assert_eq!(decoded.request_id, 1);
        let payload_secret =
            map_get_bytes(&decoded.payload, "session_secret").expect("payload has session_secret");
        assert_eq!(payload_secret, &session_secret);
    }

    #[test]
    fn body_encode_decode_roundtrip_advance() {
        let msg = Message::new(msg_type::ADVANCE, 42, advance_payload(7));
        let body = msg.to_body_canonical_bytes().unwrap();
        let decoded = Message::from_body_canonical_bytes(&body.0).unwrap();
        assert_eq!(decoded.message_type, msg_type::ADVANCE);
        assert_eq!(decoded.request_id, 42);
        let cycle = map_get_uint(&decoded.payload, "current_cycle").unwrap();
        assert_eq!(cycle, 7);
    }

    #[test]
    fn frame_encode_decode_roundtrip_with_session_key() {
        let key = [0xeeu8; 32];
        let msg = Message::new(msg_type::ADVANCE, 5, advance_payload(11));
        let frame = encode_frame_body(&msg, &key).unwrap();
        let decoded = decode_frame_body(&frame, &key).unwrap();
        assert_eq!(decoded.message_type, msg_type::ADVANCE);
        assert_eq!(decoded.request_id, 5);
    }

    #[test]
    fn frame_hmac_mismatch_rejected() {
        let correct = [0xeeu8; 32];
        let wrong = [0x11u8; 32];
        let msg = Message::new(msg_type::ADVANCE, 5, advance_payload(11));
        let frame = encode_frame_body(&msg, &correct).unwrap();
        let err = decode_frame_body(&frame, &wrong).unwrap_err();
        assert!(matches!(err, BridgeError::HmacMismatch(_)));
    }

    #[test]
    fn frame_corrupted_body_rejected() {
        let key = [0xeeu8; 32];
        let msg = Message::new(msg_type::ADVANCE, 5, advance_payload(11));
        let mut frame = encode_frame_body(&msg, &key).unwrap();
        frame[40] ^= 0x01; // Flip a bit after HMAC.
        let err = decode_frame_body(&frame, &key).unwrap_err();
        assert!(matches!(err, BridgeError::HmacMismatch(_)));
    }

    #[test]
    fn frame_too_small_rejected() {
        let key = [0xeeu8; 32];
        let err = decode_frame_body(&[0u8; 10], &key).unwrap_err();
        assert!(matches!(err, BridgeError::Protocol(_)));
    }

    #[test]
    fn hmac_empty_key_rejected() {
        let err = compute_hmac(b"foo", &[]).unwrap_err();
        assert!(matches!(err, BridgeError::Protocol(_)));
    }

    #[test]
    fn version_mismatch_rejected() {
        let mut body_map = BTreeMap::new();
        body_map.insert("v".to_string(), Value::Uint(999));
        body_map.insert(
            "type".to_string(),
            Value::String(msg_type::HELLO.to_string()),
        );
        body_map.insert("request_id".to_string(), Value::Uint(0));
        body_map.insert("payload".to_string(), Value::Map(BTreeMap::new()));
        let body = cb_encode(&Value::Map(body_map)).unwrap();
        let err = Message::from_body_canonical_bytes(&body.0).unwrap_err();
        match err {
            BridgeError::Protocol(s) => assert!(s.contains("version")),
            other => panic!("expected Protocol(version); got {other:?}"),
        }
    }

    #[test]
    fn float_repr_integer_valued() {
        assert_eq!(float_repr(0.0), "0.0");
        assert_eq!(float_repr(1.0), "1.0");
        assert_eq!(float_repr(-2.0), "-2.0");
    }

    #[test]
    fn float_repr_fractional() {
        assert_eq!(float_repr(2.5), "2.5");
        assert_eq!(float_repr(-0.125), "-0.125");
    }

    #[test]
    fn float_repr_special() {
        assert_eq!(float_repr(f64::NAN), "nan");
        assert_eq!(float_repr(f64::INFINITY), "inf");
        assert_eq!(float_repr(f64::NEG_INFINITY), "-inf");
    }

    #[test]
    fn float_repr_roundtrips_through_parse() {
        for f in [0.0, 1.0, -1.0, 2.5, -0.125, 1e10, 1e-10] {
            let s = float_repr(f);
            let parsed: f64 = s.parse().unwrap();
            assert_eq!(parsed, f, "roundtrip drift for {f}");
        }
    }
}
