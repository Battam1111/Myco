//! Core M21 substrate event vocabulary: genesis / cycle / axis / operator /
//! owner_key / nonce — plus the shared float-repr + hex-prefix utilities used
//! by every domain.

use myco_kernel_shared::canonical_bytes::{
    encode as cb_encode, float_repr as shared_float_repr, CanonicalBytes, Value,
};
use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// Event node_type constants
// ---------------------------------------------------------------------------

/// Prefix for the one-time genesis_event DAG node.
pub const NODE_TYPE_GENESIS_PREFIX: &str = "genesis_event:";

/// Cycle counter advance event.
pub const NODE_TYPE_CYCLE_ADVANCED: &str = "cycle_advanced";

/// **Phase ① 永恒吞噬 (P02 §4.4 / CHAR01 §4.3)** — the cultivar reaching toward
/// food the cultivator has not provided. Emitted (debounced) when the substrate
/// has gone a moderate number of cycles with NO `raw_material:*` ingestion: the
/// cultivar is hungry and PROACTIVELY signals it, rather than waiting silently
/// for the next operator request. A request, NOT an immune alarm (severe hunger
/// escalates to the C74 `p02_ingestion_starvation` immune sporocarp). The
/// operator polls recent nodes, sees the request, and feeds.
pub const NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST: &str =
    "cultivar_initiated_ingestion_request";

/// Prefix for axis_registered events. Full type: `axis_registered:{axis_name}`.
pub const NODE_TYPE_AXIS_REGISTERED_PREFIX: &str = "axis_registered:";

/// Prefix for axis_perturbed events (plain perturb, no raw_material link).
/// Full type: `axis_perturbed:{axis_name}`.
pub const NODE_TYPE_AXIS_PERTURBED_PREFIX: &str = "axis_perturbed:";

/// Prefix for axis_reset_after_fruiting events.
pub const NODE_TYPE_AXIS_RESET_PREFIX: &str = "axis_reset_after_fruiting:";

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
/// deterministic event encoding.
///
/// **Single source of truth**: delegates to
/// [`myco_kernel_shared::canonical_bytes::float_repr`], which reproduces CPython
/// `repr(float)` exactly (the canonical oracle). Re-exported here so the many
/// substrate event/observatory/ingest call sites keep importing
/// `crate::events::float_repr` unchanged. See the shared implementation for the
/// algorithm and the L1/HARD_RULES C18 (`canonical_bytes_render_drift`)
/// rationale.
pub fn float_repr(f: f64) -> String {
    shared_float_repr(f)
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
/// Map({
///   "substrate_id": Bytes(32),
///   "genesis_time_unix_ns": Timestamp,
///   "generation_depth": Uint,   // 8f / §16.A; OMITTED when 0 (root)
/// })
/// ```
///
/// **8f / L1/GOVERNANCE §16.A (F22)**: `generation_depth` records this
/// substrate's lineage depth (root = 0; a sprouted child = parent + 1). It
/// is the authoritative carrier the child reads at boot via
/// `DerivedState::apply_genesis` → `Manifest.generation_depth`, which the C47
/// reproduction detector then enforces against `reproduction_lineage_depth_max`.
///
/// **Back-compat / determinism**: the field is emitted ONLY when non-zero so a
/// root substrate's genesis_event canonical-bytes (and therefore its DAG hash
/// chain + the v3.1.1.1 seal) are byte-identical to the pre-8f encoding. A
/// decoder that has never seen the field treats its absence as 0 (root).
pub fn encode_genesis_event(
    substrate_id: &[u8; 32],
    genesis_time_unix_ns: i64,
    generation_depth: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "substrate_id".to_string(),
        Value::Bytes(substrate_id.to_vec()),
    );
    m.insert(
        "genesis_time_unix_ns".to_string(),
        Value::Timestamp(genesis_time_unix_ns),
    );
    if generation_depth != 0 {
        m.insert(
            "generation_depth".to_string(),
            Value::Uint(generation_depth),
        );
    }
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

// ---- cultivar_initiated_ingestion_request ----

/// Content of a `cultivar_initiated_ingestion_request` event (Phase ①):
/// ```text
/// Map({
///   "at_cycle": Uint,                  // the cycle at which the request fruited
///   "cycles_since_last_ingestion": Uint, // hunger duration (0 ⇒ never fed)
///   "ever_fed": Bool,                  // false ⇒ never fed since genesis
/// })
/// ```
///
/// The substrate cannot name the food it lacks (only the cultivator/operator
/// knows what sources exist), so the request is global "I'm hungry" + the hunger
/// duration — NOT a per-axis appetite breakdown. The appetite gradient is
/// internal; what the cultivar can honestly assert is "no raw_material has
/// arrived for N cycles", which is exactly this event.
pub fn encode_cultivar_initiated_ingestion_request(
    at_cycle: u64,
    cycles_since_last_ingestion: u64,
    ever_fed: bool,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "cycles_since_last_ingestion".to_string(),
        Value::Uint(cycles_since_last_ingestion),
    );
    m.insert("ever_fed".to_string(), Value::Bool(ever_fed));
    cb_encode(&Value::Map(m)).expect("cultivar_initiated_ingestion_request encode infallible")
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

// ---- (v0.9 owner-key removal) ----
//
// The operator_pinned (M9 TOFU) codec, the owner_key_initialized genesis codec,
// the rotate_owner_key envelope machinery (legacy single-shot + the C70 3-phase
// FSM + `PendingOwnerKeyRotation` + `derive_pending_owner_key_rotation_from_dag`),
// and the owner_key_added / owner_key_archived codecs were all removed here.


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
        let bytes = encode_genesis_event(&id, 1234567890, 0);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert_eq!(map_get_bytes(&map, "substrate_id").unwrap(), &[0x42; 32]);
    }

    #[test]
    fn encode_genesis_event_root_omits_generation_depth() {
        // 8f back-compat: a root substrate (depth 0) must produce byte-identical
        // canonical-bytes to the pre-8f two-field encoding so the DAG hash
        // chain + v3.1.1.1 seal are unchanged. We assert the field is absent.
        use myco_kernel_shared::canonical_bytes::decode;
        let id = [0x42; 32];
        let bytes = encode_genesis_event(&id, 1234567890, 0);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(
            !map.contains_key("generation_depth"),
            "root genesis_event must omit generation_depth for byte-compat"
        );
    }

    #[test]
    fn encode_genesis_event_child_records_generation_depth() {
        // 8f / §16.A: a sprouted child (depth > 0) records the field so the
        // child can read its own lineage depth at boot.
        use myco_kernel_shared::canonical_bytes::{decode, Value};
        let id = [0x42; 32];
        let bytes = encode_genesis_event(&id, 1234567890, 7);
        let decoded = decode(bytes.as_ref()).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        assert!(matches!(
            map.get("generation_depth"),
            Some(Value::Uint(7))
        ));
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
