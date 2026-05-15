//! M22 P5 万物互联 — federation wire protocol constants + helpers.
//!
//! Federation messages reuse the bridge envelope shape from
//! [`myco_kernel_bridge::protocol`] verbatim:
//! ```text
//!  body = canonical_bytes(Map({
//!      "v": Uint(FEDERATION_PROTOCOL_VERSION),
//!      "type": String(message_type),
//!      "request_id": Uint(correlation_id),
//!      "payload": Map(...),
//!  }))
//!  frame_body = HMAC-SHA256(body, derive_federation_session_key(id_a, id_b)) || body
//! ```
//!
//! What changes:
//! - The `v` namespace is federation-specific
//!   ([`FEDERATION_PROTOCOL_VERSION`]) — a federation protocol bump is
//!   independent of the bridge protocol bump.
//! - The `type` value comes from [`fed_msg_type`] not
//!   [`myco_kernel_bridge::protocol::msg_type`].
//! - The HMAC key is derived from both peers' substrate_ids by
//!   [`derive_federation_session_key`], rather than the bridge's
//!   single-secret session_secret.

use sha2::{Digest, Sha256};

/// Federation protocol version (M22 = 1). Bumped on any breaking change to
/// federation message schemas or HMAC derivation.
pub const FEDERATION_PROTOCOL_VERSION: u64 = 1;

/// Deterministic HMAC key used for [`fed_msg_type::FED_HELLO`] and
/// [`fed_msg_type::FED_HELLO_ACK`] frames — before either side knows the
/// peer's substrate_id (and therefore before
/// [`derive_federation_session_key`] can be computed).
///
/// Computed as `SHA-256(b"myco-federation-protocol-v1-bootstrap")`. This is
/// **not** a real secret — TCP is not a trust boundary at M22. The bootstrap
/// key is a pinned constant so that protocol-version rollover is explicit
/// and clients/servers can't accidentally accept HELLOs from a future
/// federation version with a different key derivation.
pub fn federation_bootstrap_key() -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"myco-federation-protocol-v1-bootstrap");
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

/// Federation message type tag constants.
///
/// All federation message types use the `fed_` prefix to make them
/// distinguishable from operator/bridge messages in DAG dumps and logs.
pub mod fed_msg_type {
    /// Initial handshake. Sender asserts substrate_id + DAG tip + protocol
    /// version. Receiver pins (TOFU) and replies with [`FED_HELLO_ACK`].
    pub const FED_HELLO: &str = "fed_hello";
    /// Federation hello acknowledgment. Sender confirms peer pinning and
    /// reports its own DAG tip for sync planning.
    pub const FED_HELLO_ACK: &str = "fed_hello_ack";
    /// Request a batch of DAG events newer than a given node hash (M22.3).
    pub const FED_REQUEST_EVENTS_SINCE: &str = "fed_request_events_since";
    /// Batch of DAG events sent in response (M22.3).
    pub const FED_EVENT_BATCH: &str = "fed_event_batch";
    /// Federation-level error envelope (sent + connection closed).
    pub const FED_ERROR: &str = "fed_error";
}

/// Derive a deterministic per-peer HMAC session key from two substrate_ids.
///
/// Both peers compute the SAME key from their (now-mutually-known) id pair.
/// Construction: `SHA-256(b"myco-federation-v1:" || min(a, b) || max(a, b))`.
///
/// Ordering substrate_ids by `<=` makes the key symmetric — peer A computing
/// `derive(a, b)` and peer B computing `derive(b, a)` produce identical bytes.
///
/// This is **not** a real public-key authentication — it relies on the
/// fact that learning a peer's substrate_id over a TCP connection authentcates
/// that connection's later frames mostly via TOFU. M23 will add Ed25519 mutual
/// auth on top (per-substrate signing keypair).
pub fn derive_federation_session_key(id_a: &[u8; 32], id_b: &[u8; 32]) -> [u8; 32] {
    let (lo, hi) = if id_a <= id_b { (id_a, id_b) } else { (id_b, id_a) };
    let mut h = Sha256::new();
    h.update(b"myco-federation-v1:");
    h.update(lo);
    h.update(hi);
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

// ---------------------------------------------------------------------------
// M22.2 FED_HELLO / FED_HELLO_ACK payload encoders + parsers.
// ---------------------------------------------------------------------------

use myco_kernel_shared::canonical_bytes::Value;
use std::collections::BTreeMap;

/// Build the payload Map for a [`FED_HELLO`](fed_msg_type::FED_HELLO) message.
///
/// Payload Map shape:
/// ```text
/// {
///   "peer_substrate_id": Bytes(32),
///   "dag_tip": Bytes(32) | absent,           // absent for empty DAG
///   "protocol_version": Uint,
/// }
/// ```
pub fn build_fed_hello_payload(
    our_substrate_id: &[u8; 32],
    our_dag_tip: Option<&[u8; 32]>,
) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert(
        "peer_substrate_id".to_string(),
        Value::Bytes(our_substrate_id.to_vec()),
    );
    if let Some(tip) = our_dag_tip {
        m.insert("dag_tip".to_string(), Value::Bytes(tip.to_vec()));
    }
    m.insert(
        "protocol_version".to_string(),
        Value::Uint(FEDERATION_PROTOCOL_VERSION),
    );
    m
}

/// Build the payload Map for a [`FED_HELLO_ACK`](fed_msg_type::FED_HELLO_ACK)
/// message. Same shape as the FED_HELLO payload (responder asserts its own
/// substrate_id + DAG tip + version back at the initiator).
pub fn build_fed_hello_ack_payload(
    our_substrate_id: &[u8; 32],
    our_dag_tip: Option<&[u8; 32]>,
) -> BTreeMap<String, Value> {
    build_fed_hello_payload(our_substrate_id, our_dag_tip)
}

/// Parsed FED_HELLO / FED_HELLO_ACK payload fields.
#[derive(Debug, Clone)]
pub struct ParsedFedHello {
    /// The peer's claimed 32-byte substrate_id.
    pub peer_substrate_id: [u8; 32],
    /// The peer's claimed DAG tip (`None` if peer's DAG is empty).
    pub peer_dag_tip: Option<[u8; 32]>,
    /// The peer's federation protocol version.
    pub protocol_version: u64,
}

/// Parse a FED_HELLO / FED_HELLO_ACK payload Map.
///
/// Returns an error if any required field is missing or malformed.
pub fn parse_fed_hello_payload(
    payload: &BTreeMap<String, Value>,
) -> Result<ParsedFedHello, String> {
    let id_bytes = match payload.get("peer_substrate_id") {
        Some(Value::Bytes(b)) if b.len() == 32 => b,
        Some(_) => return Err("peer_substrate_id is not 32 Bytes".to_string()),
        None => return Err("peer_substrate_id missing".to_string()),
    };
    let mut peer_substrate_id = [0u8; 32];
    peer_substrate_id.copy_from_slice(id_bytes);

    let peer_dag_tip = match payload.get("dag_tip") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut t = [0u8; 32];
            t.copy_from_slice(b);
            Some(t)
        }
        Some(_) => return Err("dag_tip present but not 32 Bytes".to_string()),
        None => None,
    };

    let protocol_version = match payload.get("protocol_version") {
        Some(Value::Uint(v)) => *v,
        _ => return Err("protocol_version missing or not Uint".to_string()),
    };

    Ok(ParsedFedHello {
        peer_substrate_id,
        peer_dag_tip,
        protocol_version,
    })
}

/// Build a federation error payload:
/// ```text
/// { "code": String, "message": String }
/// ```
pub fn build_fed_error_payload(code: &str, message: &str) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    m.insert("code".to_string(), Value::String(code.to_string()));
    m.insert("message".to_string(), Value::String(message.to_string()));
    m
}

/// Phase β SECURITY FIX (2026-05-15): allowlist for federation-ingestible
/// event types. A peer's pushed/pulled events may ONLY have a node_type
/// matching one of these prefixes. Substrate-private events (those that
/// `DerivedState::apply_event` interprets as Rust-authoritative state
/// mutation) are explicitly **rejected** when arriving via federation —
/// blocking the attack class where a malicious peer injects e.g.
/// `operator_pinned:*` or `genesis_event:*` to take over the substrate.
///
/// The allowed types are environmental / observational / causal-history:
/// raw_material from peer's environment, peer's sporocarp emissions,
/// peer's mutation audit trail, peer's immune sporocarps.
///
/// FORBIDDEN (substrate-private; rejection emits C22 immune sporocarp):
/// - operator_pinned:* (overwrites pinned_operator_identity)
/// - cycle_advanced (sets cycle_counter)
/// - genesis_event:* (causes MultipleGenesis error → empty state)
/// - nonce_issued:*, nonce_consumed:*, nonce_expired:* (nonce log)
/// - owner_key_* (owner key history)
/// - federation_* (federation state)
/// - parent_federation_hint (M22.4 federation parent linking forgery)
/// - self_euthanasia_* (mortality state)
/// - birth_period_quarantine_* (quarantine state)
/// - axis_registered:* / axis_perturbed:* / axis_reset_after_fruiting:*
///   (gradient state — peer events would corrupt local gradient)
/// - spore_emission:* (reproduction state)
/// - absorption_event:cycle_* (cycle absorption record)
/// - evolution_succeeded:* / evolution_failed:* (schema evolution)
/// - perturb_from_raw:* (causal-linked perturbation)
pub fn is_federation_safe_node_type(node_type: &str) -> bool {
    // Allowed prefixes — peer environmental / observational events.
    const ALLOWED_PREFIXES: &[&str] = &[
        "raw_material:",         // peer's environmental ingestion (P2)
        "sporocarp:",            // peer's fruiting events (causal-only, no state mutation)
        "mutation:",             // peer's mutation audit trail (operator-supplied opaque content)
        "immune:",               // peer's immune sporocarps (observation across substrates)
        "federation_received:",  // Phase β: wrapped peer events from chained federation
                                 // ("I heard A heard B say X" — propagated attestation)
    ];
    ALLOWED_PREFIXES.iter().any(|p| node_type.starts_with(p))
}

// ---------------------------------------------------------------------------
// M22.3 FED_REQUEST_EVENTS_SINCE / FED_EVENT_BATCH payload encoders + parsers.
// ---------------------------------------------------------------------------

/// One DAG event in transit on the federation wire.
///
/// The receiver reconstructs the BLAKE3 content hash from `parent_hashes` +
/// `content_canonical_bytes`; that hash collision-checks against the sender's
/// hash on insert (idempotent via `Dag::insert_node`).
#[derive(Debug, Clone)]
pub struct EventForFederation {
    /// Causal parents of this event.
    pub parent_hashes: Vec<[u8; 32]>,
    /// node_type string (must be non-empty).
    pub node_type: String,
    /// Cycle counter at which this event was created.
    pub created_at_cycle: u64,
    /// Canonical-bytes-encoded content of the event.
    pub content_canonical_bytes: Vec<u8>,
}

/// Max events per FED_EVENT_BATCH response. Prevents one peer from forcing
/// the other into an unbounded write that could exceed the 1MiB frame cap
/// or hold the connection open for too long.
pub const FED_EVENT_BATCH_MAX_EVENTS: u64 = 100;

/// Build the payload for a [`FED_REQUEST_EVENTS_SINCE`](fed_msg_type::FED_REQUEST_EVENTS_SINCE)
/// message.
///
/// Payload Map:
/// ```text
/// {
///   "since_node_hash": Bytes(32) | absent,            // absent = from genesis
///   "max_events": Uint,                                // <= FED_EVENT_BATCH_MAX_EVENTS
/// }
/// ```
pub fn build_request_events_since_payload(
    since_node_hash: Option<&[u8; 32]>,
    max_events: u64,
) -> BTreeMap<String, Value> {
    let mut m = BTreeMap::new();
    if let Some(h) = since_node_hash {
        m.insert("since_node_hash".to_string(), Value::Bytes(h.to_vec()));
    }
    m.insert(
        "max_events".to_string(),
        Value::Uint(max_events.min(FED_EVENT_BATCH_MAX_EVENTS)),
    );
    m
}

/// Parsed FED_REQUEST_EVENTS_SINCE payload.
#[derive(Debug, Clone)]
pub struct ParsedRequestEventsSince {
    /// Hash to start enumerating after (None = from genesis).
    pub since_node_hash: Option<[u8; 32]>,
    /// Maximum number of events to return (capped at FED_EVENT_BATCH_MAX_EVENTS).
    pub max_events: u64,
}

/// Parse a FED_REQUEST_EVENTS_SINCE payload.
pub fn parse_request_events_since_payload(
    payload: &BTreeMap<String, Value>,
) -> Result<ParsedRequestEventsSince, String> {
    let since_node_hash = match payload.get("since_node_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut h = [0u8; 32];
            h.copy_from_slice(b);
            Some(h)
        }
        Some(_) => return Err("since_node_hash present but not 32 Bytes".to_string()),
        None => None,
    };
    let max_events = match payload.get("max_events") {
        Some(Value::Uint(n)) => (*n).min(FED_EVENT_BATCH_MAX_EVENTS),
        _ => FED_EVENT_BATCH_MAX_EVENTS,
    };
    Ok(ParsedRequestEventsSince {
        since_node_hash,
        max_events,
    })
}

/// Build the payload for a [`FED_EVENT_BATCH`](fed_msg_type::FED_EVENT_BATCH) message.
///
/// Payload Map:
/// ```text
/// {
///   "events": Array<Map({
///     "parent_hashes": Array<Bytes(32)>,
///     "node_type": String,
///     "created_at_cycle": Uint,
///     "content_canonical_bytes": Bytes,
///   })>,
///   "is_last_batch": Bool,                             // true if no more events available
/// }
/// ```
pub fn build_event_batch_payload(
    events: &[EventForFederation],
    is_last_batch: bool,
) -> BTreeMap<String, Value> {
    let event_values: Vec<Value> = events
        .iter()
        .map(|ev| {
            let mut em = BTreeMap::new();
            let parent_vals: Vec<Value> = ev
                .parent_hashes
                .iter()
                .map(|h| Value::Bytes(h.to_vec()))
                .collect();
            em.insert("parent_hashes".to_string(), Value::Array(parent_vals));
            em.insert("node_type".to_string(), Value::String(ev.node_type.clone()));
            em.insert(
                "created_at_cycle".to_string(),
                Value::Uint(ev.created_at_cycle),
            );
            em.insert(
                "content_canonical_bytes".to_string(),
                Value::Bytes(ev.content_canonical_bytes.clone()),
            );
            Value::Map(em)
        })
        .collect();
    let mut m = BTreeMap::new();
    m.insert("events".to_string(), Value::Array(event_values));
    m.insert("is_last_batch".to_string(), Value::Bool(is_last_batch));
    m
}

/// Parsed FED_EVENT_BATCH payload.
#[derive(Debug, Clone)]
pub struct ParsedEventBatch {
    /// The events in this batch (caller inserts into local DAG).
    pub events: Vec<EventForFederation>,
    /// Whether the sender has more events available past this batch.
    pub is_last_batch: bool,
}

/// Parse a FED_EVENT_BATCH payload.
pub fn parse_event_batch_payload(
    payload: &BTreeMap<String, Value>,
) -> Result<ParsedEventBatch, String> {
    let events_array = match payload.get("events") {
        Some(Value::Array(a)) => a,
        _ => return Err("events missing or not Array".to_string()),
    };
    let mut events = Vec::with_capacity(events_array.len());
    for v in events_array {
        let em = match v {
            Value::Map(m) => m,
            _ => return Err("event entry not Map".to_string()),
        };
        let parent_hashes = match em.get("parent_hashes") {
            Some(Value::Array(a)) => {
                let mut out = Vec::with_capacity(a.len());
                for pv in a {
                    match pv {
                        Value::Bytes(b) if b.len() == 32 => {
                            let mut h = [0u8; 32];
                            h.copy_from_slice(b);
                            out.push(h);
                        }
                        _ => return Err("parent_hash not 32 Bytes".to_string()),
                    }
                }
                out
            }
            _ => return Err("parent_hashes missing".to_string()),
        };
        let node_type = match em.get("node_type") {
            Some(Value::String(s)) if !s.is_empty() => s.clone(),
            _ => return Err("node_type missing or empty".to_string()),
        };
        let created_at_cycle = match em.get("created_at_cycle") {
            Some(Value::Uint(n)) => *n,
            _ => return Err("created_at_cycle missing".to_string()),
        };
        let content_canonical_bytes = match em.get("content_canonical_bytes") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => return Err("content_canonical_bytes missing".to_string()),
        };
        events.push(EventForFederation {
            parent_hashes,
            node_type,
            created_at_cycle,
            content_canonical_bytes,
        });
    }
    let is_last_batch = match payload.get("is_last_batch") {
        Some(Value::Bool(b)) => *b,
        _ => true,
    };
    Ok(ParsedEventBatch {
        events,
        is_last_batch,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn session_key_is_32_bytes() {
        let a = [0xaa; 32];
        let b = [0xbb; 32];
        let key = derive_federation_session_key(&a, &b);
        assert_eq!(key.len(), 32);
    }

    #[test]
    fn session_key_is_symmetric() {
        let a = [0x11; 32];
        let b = [0x22; 32];
        assert_eq!(
            derive_federation_session_key(&a, &b),
            derive_federation_session_key(&b, &a),
            "key must be identical regardless of argument order"
        );
    }

    #[test]
    fn session_key_changes_with_either_id() {
        let a1 = [0x11; 32];
        let a2 = [0x12; 32];
        let b = [0x22; 32];
        assert_ne!(
            derive_federation_session_key(&a1, &b),
            derive_federation_session_key(&a2, &b),
            "different first id must yield different key"
        );
    }

    #[test]
    fn session_key_pinned_value_for_protocol_v1() {
        // Pinned: changing any byte of this value is a federation protocol
        // version bump. Two zero substrate_ids → deterministic key.
        let key = derive_federation_session_key(&[0u8; 32], &[0u8; 32]);
        // Recompute the expected value to catch accidental drift.
        let mut h = Sha256::new();
        h.update(b"myco-federation-v1:");
        h.update([0u8; 32]);
        h.update([0u8; 32]);
        let expected = h.finalize();
        assert_eq!(&key, expected.as_slice());
    }

    #[test]
    fn fed_msg_type_constants_are_distinct() {
        // Cheap sanity: no two tag constants alias each other.
        let types = [
            fed_msg_type::FED_HELLO,
            fed_msg_type::FED_HELLO_ACK,
            fed_msg_type::FED_REQUEST_EVENTS_SINCE,
            fed_msg_type::FED_EVENT_BATCH,
            fed_msg_type::FED_ERROR,
        ];
        let mut sorted: Vec<&&str> = types.iter().collect();
        sorted.sort();
        sorted.dedup();
        assert_eq!(sorted.len(), types.len(), "fed msg type tags must be distinct");
    }

    #[test]
    fn federation_bootstrap_key_is_deterministic() {
        assert_eq!(federation_bootstrap_key(), federation_bootstrap_key());
    }

    #[test]
    fn federation_bootstrap_key_differs_from_bridge_bootstrap_key() {
        let fed = federation_bootstrap_key();
        let bridge = myco_kernel_bridge::protocol::bootstrap_key();
        assert_ne!(
            fed, bridge,
            "federation bootstrap key must differ from bridge bootstrap key"
        );
    }

    #[test]
    fn fed_hello_payload_roundtrips_with_tip() {
        let id = [0x42; 32];
        let tip = [0x99; 32];
        let payload = build_fed_hello_payload(&id, Some(&tip));
        let parsed = parse_fed_hello_payload(&payload).expect("parse");
        assert_eq!(parsed.peer_substrate_id, id);
        assert_eq!(parsed.peer_dag_tip, Some(tip));
        assert_eq!(parsed.protocol_version, FEDERATION_PROTOCOL_VERSION);
    }

    #[test]
    fn fed_hello_payload_roundtrips_without_tip() {
        let id = [0xab; 32];
        let payload = build_fed_hello_payload(&id, None);
        let parsed = parse_fed_hello_payload(&payload).expect("parse");
        assert_eq!(parsed.peer_substrate_id, id);
        assert_eq!(parsed.peer_dag_tip, None);
    }

    #[test]
    fn parse_fed_hello_rejects_missing_id() {
        let mut payload = BTreeMap::new();
        payload.insert(
            "protocol_version".to_string(),
            Value::Uint(FEDERATION_PROTOCOL_VERSION),
        );
        let err = parse_fed_hello_payload(&payload).unwrap_err();
        assert!(err.contains("peer_substrate_id"));
    }

    #[test]
    fn parse_fed_hello_rejects_wrong_id_size() {
        let mut payload = BTreeMap::new();
        payload.insert(
            "peer_substrate_id".to_string(),
            Value::Bytes(vec![0u8; 16]), // wrong size
        );
        payload.insert(
            "protocol_version".to_string(),
            Value::Uint(FEDERATION_PROTOCOL_VERSION),
        );
        let err = parse_fed_hello_payload(&payload).unwrap_err();
        assert!(err.contains("32"));
    }

    #[test]
    fn fed_error_payload_shape() {
        let p = build_fed_error_payload("identity_mismatch", "peer id drift");
        assert!(matches!(p.get("code"), Some(Value::String(s)) if s == "identity_mismatch"));
        assert!(matches!(p.get("message"), Some(Value::String(s)) if s == "peer id drift"));
    }
}
