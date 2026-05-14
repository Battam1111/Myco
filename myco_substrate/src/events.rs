//! M21 P5 万物互联 — DAG event type definitions.
//!
//! This module defines the **substrate event vocabulary**: every state
//! mutation in the substrate emits a DAG node whose `node_type` is one of
//! the constants here, with a content-canonical-bytes Map matching the
//! documented schema.
//!
//! ## Doctrine alignment
//!
//! Per L0 §2.1 P5: "The substrate is a connected graph, not a collection.
//! Every node is reachable from every other by traversal. Orphans are dead
//! tissue."
//!
//! M21 closes a P5 violation that accumulated across M5-M20: numerous state
//! mutations (cycle_counter advance, axis registration, plain perturb_axis,
//! TOFU pinning, owner_key changes, nonce issue/consume) modified substrate
//! behavior but did NOT emit DAG nodes — making them ORPHANS from the
//! causal graph. M21 emits these as DAG events alongside the existing state
//! file writes (dual-write phase), enabling `DerivedState::from_dag` to
//! produce a complete derived view of substrate state from the DAG alone.
//!
//! ## Event types (12 new in M21.1; coexisting with existing M8-M20 types)
//!
//! | node_type                       | Records                                    |
//! |---------------------------------|--------------------------------------------|
//! | `genesis_event:{id_prefix}`     | First DAG node; substrate_id + genesis_time|
//! | `cycle_advanced`                | cycle_counter increment                    |
//! | `axis_registered:{name}`        | New axis schema + initial value            |
//! | `axis_perturbed:{name}`         | Plain perturb (not raw-material-linked)    |
//! | `axis_reset_after_fruiting:{n}` | APPETITE axis reset to initial_value       |
//! | `operator_pinned:{pk_prefix}`   | TOFU first-pinning of operator pubkey      |
//! | `owner_key_initialized`         | Genesis owner key write                    |
//! | `owner_key_added`               | New owner key added to history             |
//! | `owner_key_archived`            | Owner key marked archived (rotation)       |
//! | `nonce_issued:{nonce_prefix}`   | M13 nonce issuance                         |
//! | `nonce_consumed:{nonce_prefix}` | M13 nonce consume on submit                |
//! | `nonce_expired:{nonce_prefix}`  | M14 nonce TTL expiration during prune      |
//!
//! ## Determinism contract
//!
//! Each event encoder produces canonical-bytes that, when decoded, yield the
//! same logical content. `DerivedState::apply_event` is a pure function of
//! (current_state, event) — replaying any DAG segment in insertion order
//! produces identical state.
//!
//! Float values are stored as repr-strings (matching the wire protocol's
//! `repr(f64)` convention used since M5) so cross-platform replay is
//! byte-deterministic.

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// Event node_type constants
// ---------------------------------------------------------------------------

/// Prefix for the one-time genesis_event DAG node.
pub const NODE_TYPE_GENESIS_PREFIX: &str = "genesis_event:";

/// Cycle counter advance event.
pub const NODE_TYPE_CYCLE_ADVANCED: &str = "cycle_advanced";

/// Prefix for axis_registered events. Full type: `axis_registered:{axis_name}`.
pub const NODE_TYPE_AXIS_REGISTERED_PREFIX: &str = "axis_registered:";

/// Prefix for axis_perturbed events (plain perturb, no raw_material link).
/// Full type: `axis_perturbed:{axis_name}`.
pub const NODE_TYPE_AXIS_PERTURBED_PREFIX: &str = "axis_perturbed:";

/// Prefix for axis_reset_after_fruiting events.
pub const NODE_TYPE_AXIS_RESET_PREFIX: &str = "axis_reset_after_fruiting:";

/// Prefix for operator_pinned events (TOFU first-sighting).
pub const NODE_TYPE_OPERATOR_PINNED_PREFIX: &str = "operator_pinned:";

/// Genesis owner-key initialization event.
pub const NODE_TYPE_OWNER_KEY_INITIALIZED: &str = "owner_key_initialized";

/// Owner-key addition event (rotation start).
pub const NODE_TYPE_OWNER_KEY_ADDED: &str = "owner_key_added";

/// Owner-key archive event (rotation complete).
pub const NODE_TYPE_OWNER_KEY_ARCHIVED: &str = "owner_key_archived";

/// Prefix for nonce_issued events.
pub const NODE_TYPE_NONCE_ISSUED_PREFIX: &str = "nonce_issued:";

/// Prefix for nonce_consumed events.
pub const NODE_TYPE_NONCE_CONSUMED_PREFIX: &str = "nonce_consumed:";

/// Prefix for nonce_expired events (TTL-based pruning).
pub const NODE_TYPE_NONCE_EXPIRED_PREFIX: &str = "nonce_expired:";

// ---------------------------------------------------------------------------
// Float repr utility — matches kernel/bridge protocol's `float_repr` convention.
// ---------------------------------------------------------------------------

/// Format an f64 as a Python-compatible repr string for cross-platform
/// deterministic event encoding. Identical convention to the wire protocol's
/// `float_repr` (kernel/bridge::protocol::float_repr).
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
        format!("{f:.1}")
    } else {
        format!("{f}")
    }
}

// ---------------------------------------------------------------------------
// Event encoders — produce canonical-bytes for DAG-node `content_canonical_bytes`.
//
// Convention: each function takes a single struct (or destructured args) and
// returns a `CanonicalBytes` ready for `Dag::insert_node`.
//
// The substrate's `node_type` string for each event includes a per-type
// suffix (e.g. axis name, pubkey prefix, nonce prefix) so that `query_recent_nodes`
// with prefix filters can isolate specific event categories.
// ---------------------------------------------------------------------------

/// Hex-encode the first N bytes of a byte slice for use as a node_type suffix.
///
/// Used to make event types like `axis_perturbed:{axis_name}` unambiguous AND
/// to ensure events like `nonce_issued:{first_8_bytes_hex}` are sortable +
/// human-readable in DAG dumps.
pub fn hex_prefix(bytes: &[u8], n_bytes: usize) -> String {
    bytes
        .iter()
        .take(n_bytes)
        .map(|b| format!("{b:02x}"))
        .collect()
}

// ---- genesis_event ----

/// node_type for the one-time genesis_event: `genesis_event:{first_8_bytes_of_substrate_id_hex}`.
pub fn genesis_event_node_type(substrate_id: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_GENESIS_PREFIX,
        hex_prefix(substrate_id, 8)
    )
}

/// Content of a genesis_event:
/// ```text
/// Map({ "substrate_id": Bytes(32), "genesis_time_unix_ns": Timestamp })
/// ```
pub fn encode_genesis_event(substrate_id: &[u8; 32], genesis_time_unix_ns: i64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "substrate_id".to_string(),
        Value::Bytes(substrate_id.to_vec()),
    );
    m.insert(
        "genesis_time_unix_ns".to_string(),
        Value::Timestamp(genesis_time_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("genesis_event encode infallible")
}

// ---- cycle_advanced ----

/// Content of a cycle_advanced event:
/// ```text
/// Map({ "prior_cycle": Uint, "new_cycle": Uint })
/// ```
pub fn encode_cycle_advanced(prior_cycle: u64, new_cycle: u64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("prior_cycle".to_string(), Value::Uint(prior_cycle));
    m.insert("new_cycle".to_string(), Value::Uint(new_cycle));
    cb_encode(&Value::Map(m)).expect("cycle_advanced encode infallible")
}

// ---- axis_registered ----

/// Parameters captured at axis registration. Mirrors the wire protocol's
/// register_axis payload fields, recorded as a DAG event for P5/P6 fidelity.
#[derive(Debug, Clone)]
pub struct AxisRegisteredEvent {
    /// Axis name (also embedded in node_type suffix).
    pub name: String,
    /// "appetite" or "decay".
    pub axis_class: String,
    /// Fruiting threshold (repr-encoded for determinism).
    pub fruiting_threshold: f64,
    /// Initial gradient value.
    pub initial_value: f64,
    /// Per-cycle decay rate.
    pub decay_rate_per_cycle: f64,
    /// Whether this axis is the mortality signal.
    pub is_mortality_signal: bool,
    /// "noop" or "decay".
    pub update_rule_kind: String,
}

/// node_type: `axis_registered:{name}`.
pub fn axis_registered_node_type(name: &str) -> String {
    format!("{}{}", NODE_TYPE_AXIS_REGISTERED_PREFIX, name)
}

/// Content of an axis_registered event:
/// ```text
/// Map({
///   "name": String,
///   "axis_class": String,
///   "fruiting_threshold_repr": String,
///   "initial_value_repr": String,
///   "decay_rate_per_cycle_repr": String,
///   "is_mortality_signal": Bool,
///   "update_rule_kind": String,
/// })
/// ```
pub fn encode_axis_registered(event: &AxisRegisteredEvent) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("name".to_string(), Value::String(event.name.clone()));
    m.insert(
        "axis_class".to_string(),
        Value::String(event.axis_class.clone()),
    );
    m.insert(
        "fruiting_threshold_repr".to_string(),
        Value::String(float_repr(event.fruiting_threshold)),
    );
    m.insert(
        "initial_value_repr".to_string(),
        Value::String(float_repr(event.initial_value)),
    );
    m.insert(
        "decay_rate_per_cycle_repr".to_string(),
        Value::String(float_repr(event.decay_rate_per_cycle)),
    );
    m.insert(
        "is_mortality_signal".to_string(),
        Value::Bool(event.is_mortality_signal),
    );
    m.insert(
        "update_rule_kind".to_string(),
        Value::String(event.update_rule_kind.clone()),
    );
    cb_encode(&Value::Map(m)).expect("axis_registered encode infallible")
}

// ---- axis_perturbed ----

/// node_type: `axis_perturbed:{name}`.
pub fn axis_perturbed_node_type(name: &str) -> String {
    format!("{}{}", NODE_TYPE_AXIS_PERTURBED_PREFIX, name)
}

/// Content of an axis_perturbed event:
/// ```text
/// Map({
///   "axis_name": String,
///   "delta_repr": String,
/// })
/// ```
///
/// M21.1 schema records only delta. Replay (M21.3 Python view) computes axis
/// values by summing deltas since axis_registered, in DAG insertion order.
pub fn encode_axis_perturbed(axis_name: &str, delta: f64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "axis_name".to_string(),
        Value::String(axis_name.to_string()),
    );
    m.insert("delta_repr".to_string(), Value::String(float_repr(delta)));
    cb_encode(&Value::Map(m)).expect("axis_perturbed encode infallible")
}

// ---- axis_reset_after_fruiting ----

/// node_type: `axis_reset_after_fruiting:{name}`.
pub fn axis_reset_node_type(name: &str) -> String {
    format!("{}{}", NODE_TYPE_AXIS_RESET_PREFIX, name)
}

/// Content of an axis_reset_after_fruiting event:
/// ```text
/// Map({
///   "axis_name": String,
///   "at_cycle": Uint,
///   "fruiting_value_repr": String,
///   "reset_to_value_repr": String,
/// })
/// ```
pub fn encode_axis_reset_after_fruiting(
    axis_name: &str,
    at_cycle: u64,
    fruiting_value: f64,
    reset_to_value: f64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "axis_name".to_string(),
        Value::String(axis_name.to_string()),
    );
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "fruiting_value_repr".to_string(),
        Value::String(float_repr(fruiting_value)),
    );
    m.insert(
        "reset_to_value_repr".to_string(),
        Value::String(float_repr(reset_to_value)),
    );
    cb_encode(&Value::Map(m)).expect("axis_reset encode infallible")
}

// ---- operator_pinned ----

/// node_type: `operator_pinned:{pubkey_hex_prefix}`.
pub fn operator_pinned_node_type(pubkey: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_OPERATOR_PINNED_PREFIX,
        hex_prefix(pubkey, 8)
    )
}

/// Content of an operator_pinned event (M9 TOFU):
/// ```text
/// Map({ "pubkey": Bytes(32), "first_pinned_unix_ns": Timestamp })
/// ```
pub fn encode_operator_pinned(pubkey: &[u8; 32], first_pinned_unix_ns: i64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("pubkey".to_string(), Value::Bytes(pubkey.to_vec()));
    m.insert(
        "first_pinned_unix_ns".to_string(),
        Value::Timestamp(first_pinned_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("operator_pinned encode infallible")
}

// ---- owner_key_initialized ----

/// Content of an owner_key_initialized event (M10 genesis):
/// ```text
/// Map({ "pubkey": Bytes(32), "anchor_timestamp_unix_seconds": Uint })
/// ```
pub fn encode_owner_key_initialized(
    pubkey: &[u8; 32],
    anchor_timestamp_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("pubkey".to_string(), Value::Bytes(pubkey.to_vec()));
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_initialized encode infallible")
}

// ---- owner_key_added ----

/// Content of an owner_key_added event (M10 rotation: new key added):
/// ```text
/// Map({
///   "new_pubkey": Bytes(32),
///   "prior_active_pubkey": Bytes(32),
///   "anchor_timestamp_unix_seconds": Uint,
/// })
/// ```
pub fn encode_owner_key_added(
    new_pubkey: &[u8; 32],
    prior_active_pubkey: &[u8; 32],
    anchor_timestamp_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("new_pubkey".to_string(), Value::Bytes(new_pubkey.to_vec()));
    m.insert(
        "prior_active_pubkey".to_string(),
        Value::Bytes(prior_active_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_added encode infallible")
}

// ---- owner_key_archived ----

/// Content of an owner_key_archived event:
/// ```text
/// Map({
///   "archived_pubkey": Bytes(32),
///   "anchor_timestamp_unix_seconds": Uint,
/// })
/// ```
pub fn encode_owner_key_archived(
    archived_pubkey: &[u8; 32],
    anchor_timestamp_unix_seconds: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "archived_pubkey".to_string(),
        Value::Bytes(archived_pubkey.to_vec()),
    );
    m.insert(
        "anchor_timestamp_unix_seconds".to_string(),
        Value::Uint(anchor_timestamp_unix_seconds),
    );
    cb_encode(&Value::Map(m)).expect("owner_key_archived encode infallible")
}

// ---- nonce_issued ----

/// node_type: `nonce_issued:{nonce_hex_prefix}`.
pub fn nonce_issued_node_type(nonce: &[u8; 32]) -> String {
    format!("{}{}", NODE_TYPE_NONCE_ISSUED_PREFIX, hex_prefix(nonce, 8))
}

/// Content of a nonce_issued event (M13 + M15 dual-clock extension):
/// ```text
/// Map({
///   "nonce": Bytes(32),
///   "bound_content_hash": Bytes(32),
///   "bound_dag_tip": Bytes(32),
///   "substrate_issued_at_unix_ns": Timestamp,
///   "expiry_unix_ns": Timestamp,
///   "anchor_clock_issued_at_unix_ns": Timestamp [optional; dual-clock only],
///   "anchor_clock_expiry_unix_ns": Timestamp [optional; dual-clock only],
/// })
/// ```
#[allow(clippy::too_many_arguments)]
pub fn encode_nonce_issued(
    nonce: &[u8; 32],
    bound_content_hash: &[u8; 32],
    bound_dag_tip: &[u8; 32],
    substrate_issued_at_unix_ns: i64,
    expiry_unix_ns: i64,
    anchor_clock_issued_at_unix_ns: Option<i64>,
    anchor_clock_expiry_unix_ns: Option<i64>,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    m.insert(
        "bound_content_hash".to_string(),
        Value::Bytes(bound_content_hash.to_vec()),
    );
    m.insert(
        "bound_dag_tip".to_string(),
        Value::Bytes(bound_dag_tip.to_vec()),
    );
    m.insert(
        "substrate_issued_at_unix_ns".to_string(),
        Value::Timestamp(substrate_issued_at_unix_ns),
    );
    m.insert(
        "expiry_unix_ns".to_string(),
        Value::Timestamp(expiry_unix_ns),
    );
    if let Some(t) = anchor_clock_issued_at_unix_ns {
        m.insert(
            "anchor_clock_issued_at_unix_ns".to_string(),
            Value::Timestamp(t),
        );
    }
    if let Some(t) = anchor_clock_expiry_unix_ns {
        m.insert(
            "anchor_clock_expiry_unix_ns".to_string(),
            Value::Timestamp(t),
        );
    }
    cb_encode(&Value::Map(m)).expect("nonce_issued encode infallible")
}

// ---- nonce_consumed ----

/// node_type: `nonce_consumed:{nonce_hex_prefix}`.
pub fn nonce_consumed_node_type(nonce: &[u8; 32]) -> String {
    format!(
        "{}{}",
        NODE_TYPE_NONCE_CONSUMED_PREFIX,
        hex_prefix(nonce, 8)
    )
}

/// Content of a nonce_consumed event:
/// ```text
/// Map({ "nonce": Bytes(32), "consumed_at_unix_ns": Timestamp })
/// ```
pub fn encode_nonce_consumed(nonce: &[u8; 32], consumed_at_unix_ns: i64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    m.insert(
        "consumed_at_unix_ns".to_string(),
        Value::Timestamp(consumed_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("nonce_consumed encode infallible")
}

// ---- nonce_expired ----

/// node_type: `nonce_expired:{nonce_hex_prefix}`.
pub fn nonce_expired_node_type(nonce: &[u8; 32]) -> String {
    format!("{}{}", NODE_TYPE_NONCE_EXPIRED_PREFIX, hex_prefix(nonce, 8))
}

/// Content of a nonce_expired event:
/// ```text
/// Map({ "nonce": Bytes(32), "expiry_unix_ns": Timestamp, "pruned_at_unix_ns": Timestamp })
/// ```
pub fn encode_nonce_expired(
    nonce: &[u8; 32],
    expiry_unix_ns: i64,
    pruned_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    m.insert(
        "expiry_unix_ns".to_string(),
        Value::Timestamp(expiry_unix_ns),
    );
    m.insert(
        "pruned_at_unix_ns".to_string(),
        Value::Timestamp(pruned_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("nonce_expired encode infallible")
}

#[cfg(test)]
mod tests {
    use super::*;

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
    fn hex_prefix_8_bytes() {
        let id = [0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89, 0xff, 0xee];
        assert_eq!(hex_prefix(&id, 8), "abcdef0123456789");
    }

    #[test]
    fn genesis_event_node_type_format() {
        let id = [0xab; 32];
        assert_eq!(
            genesis_event_node_type(&id),
            "genesis_event:abababababababab"
        );
    }

    #[test]
    fn encode_genesis_event_roundtrip() {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_bytes};

        let id = [0x42; 32];
        let bytes = encode_genesis_event(&id, 1234567890);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_bytes(&map, "substrate_id").unwrap(), &[0x42; 32]);
    }

    #[test]
    fn encode_axis_registered_includes_all_fields() {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_bool, map_get_string};

        let event = AxisRegisteredEvent {
            name: "test_axis".to_string(),
            axis_class: "appetite".to_string(),
            fruiting_threshold: 10.0,
            initial_value: 0.0,
            decay_rate_per_cycle: 1.0,
            is_mortality_signal: false,
            update_rule_kind: "noop".to_string(),
        };
        let bytes = encode_axis_registered(&event);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_string(&map, "name").unwrap(), "test_axis");
        assert_eq!(
            map_get_string(&map, "fruiting_threshold_repr").unwrap(),
            "10.0"
        );
        assert!(!map_get_bool(&map, "is_mortality_signal").unwrap());
    }

    #[test]
    fn encode_axis_perturbed_preserves_float_determinism() {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_string};

        let bytes1 = encode_axis_perturbed("x", 2.5);
        let bytes2 = encode_axis_perturbed("x", 2.5);
        // Determinism: same inputs → identical canonical bytes.
        assert_eq!(bytes1.as_ref(), bytes2.as_ref());

        let decoded = decode(bytes1.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_string(&map, "delta_repr").unwrap(), "2.5");
        assert_eq!(map_get_string(&map, "axis_name").unwrap(), "x");
    }

    #[test]
    fn encode_nonce_issued_with_dual_clock_includes_anchor_fields() {
        use myco_kernel_shared::canonical_bytes::{decode, Value};

        let nonce = [0x01; 32];
        let content_hash = [0x02; 32];
        let dag_tip = [0x03; 32];
        let bytes = encode_nonce_issued(
            &nonce,
            &content_hash,
            &dag_tip,
            1000,
            301000,
            Some(2000),
            Some(302000),
        );
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(matches!(
            map.get("anchor_clock_issued_at_unix_ns"),
            Some(Value::Timestamp(2000))
        ));
        assert!(matches!(
            map.get("anchor_clock_expiry_unix_ns"),
            Some(Value::Timestamp(302000))
        ));
    }

    #[test]
    fn encode_nonce_issued_without_dual_clock_omits_anchor_fields() {
        use myco_kernel_shared::canonical_bytes::decode;

        let nonce = [0x01; 32];
        let bytes = encode_nonce_issued(&nonce, &[0; 32], &[0; 32], 1000, 301000, None, None);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(!map.contains_key("anchor_clock_issued_at_unix_ns"));
        assert!(!map.contains_key("anchor_clock_expiry_unix_ns"));
    }

    #[test]
    fn node_type_suffixes_are_consistent() {
        // Per-axis events use the same suffix conventions.
        assert_eq!(axis_registered_node_type("x"), "axis_registered:x");
        assert_eq!(axis_perturbed_node_type("x"), "axis_perturbed:x");
        assert_eq!(axis_reset_node_type("x"), "axis_reset_after_fruiting:x");
    }

    #[test]
    fn nonce_event_node_types_use_8_byte_hex_prefix() {
        let nonce = [0xde, 0xad, 0xbe, 0xef, 0xca, 0xfe, 0xba, 0xbe, 0xff, 0xee];
        assert_eq!(
            nonce_issued_node_type(&{
                let mut a = [0u8; 32];
                a[..10].copy_from_slice(&nonce);
                a
            }),
            "nonce_issued:deadbeefcafebabe"
        );
    }
}
