//! **v3.1.1 Sprint 8.G** — P03 §10.4 multi-cycle two-phase schema migration
//! DAG event vocabulary.
//!
//! A migration is a candidate schema validated alongside the active schema
//! across a window of metabolic cycles before commit-or-rollback (the FSM
//! lives in `kernel/schema/src/migration.rs`). Each transition is recorded as
//! a DAG event so the migration's full lifecycle is auditable from the causal
//! graph (P05 万物互联) and resumable across restart (P03 §10.4).
//!
//! ## Event types (4 new)
//!
//! | node_type                              | Records                          |
//! |----------------------------------------|----------------------------------|
//! | `schema_migration_started:{op}`        | candidate entered Validating     |
//! | `schema_migration_cycle_validated:{op}`| one dual-validation cycle outcome|
//! | `schema_migration_committed:{op}`      | candidate promoted → active      |
//! | `schema_migration_rolled_back:{op}`    | candidate dropped; active kept   |
//!
//! ## Back-compat sibling events (load-bearing)
//!
//! On commit AND on rollback the substrate ALSO emits the LEGACY single-cycle
//! sibling — `evolution_succeeded:{op}` / `evolution_failed:{op}` — so the
//! observatory's signal_2 evolution-event counter and every existing test
//! that watches for those node types keep working unchanged. The migration
//! events are ADDITIVE; they do not replace the legacy vocabulary.
//!
//! ## Determinism
//!
//! No floats are involved; every field is a String / Bytes / Uint / Timestamp,
//! so the canonical-bytes encoding is byte-deterministic across platforms by
//! construction (same discipline as `events/core.rs`).

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// node_type prefixes.
// ---------------------------------------------------------------------------

/// Prefix for `schema_migration_started:{op}` events.
pub const NODE_TYPE_SCHEMA_MIGRATION_STARTED_PREFIX: &str = "schema_migration_started:";

/// Prefix for `schema_migration_cycle_validated:{op}` events.
pub const NODE_TYPE_SCHEMA_MIGRATION_CYCLE_VALIDATED_PREFIX: &str =
    "schema_migration_cycle_validated:";

/// Prefix for `schema_migration_committed:{op}` events.
pub const NODE_TYPE_SCHEMA_MIGRATION_COMMITTED_PREFIX: &str = "schema_migration_committed:";

/// Prefix for `schema_migration_rolled_back:{op}` events.
pub const NODE_TYPE_SCHEMA_MIGRATION_ROLLED_BACK_PREFIX: &str = "schema_migration_rolled_back:";

// ---------------------------------------------------------------------------
// node_type builders.
// ---------------------------------------------------------------------------

/// node_type: `schema_migration_started:{op}`.
pub fn schema_migration_started_node_type(op: &str) -> String {
    format!("{NODE_TYPE_SCHEMA_MIGRATION_STARTED_PREFIX}{op}")
}

/// node_type: `schema_migration_cycle_validated:{op}`.
pub fn schema_migration_cycle_validated_node_type(op: &str) -> String {
    format!("{NODE_TYPE_SCHEMA_MIGRATION_CYCLE_VALIDATED_PREFIX}{op}")
}

/// node_type: `schema_migration_committed:{op}`.
pub fn schema_migration_committed_node_type(op: &str) -> String {
    format!("{NODE_TYPE_SCHEMA_MIGRATION_COMMITTED_PREFIX}{op}")
}

/// node_type: `schema_migration_rolled_back:{op}`.
pub fn schema_migration_rolled_back_node_type(op: &str) -> String {
    format!("{NODE_TYPE_SCHEMA_MIGRATION_ROLLED_BACK_PREFIX}{op}")
}

// ---------------------------------------------------------------------------
// Event encoders.
// ---------------------------------------------------------------------------

/// Content of a `schema_migration_started:{op}` event.
///
/// ```text
/// Map({
///   "op": String,
///   "schema_diff_canonical_bytes": Bytes,   // the diff the candidate applies
///   "started_at_cycle": Uint,               // cycle the window opened
///   "dual_validation_window_cycles": Uint,  // how many cycles until commit
///   "started_at_unix_ns": Timestamp,        // wall-clock at start (informational)
/// })
/// ```
pub fn encode_schema_migration_started(
    op: &str,
    schema_diff_canonical_bytes: &[u8],
    started_at_cycle: u64,
    dual_validation_window_cycles: u64,
    started_at_unix_ns: i64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("op".to_string(), Value::String(op.to_string()));
    m.insert(
        "schema_diff_canonical_bytes".to_string(),
        Value::Bytes(schema_diff_canonical_bytes.to_vec()),
    );
    m.insert(
        "started_at_cycle".to_string(),
        Value::Uint(started_at_cycle),
    );
    m.insert(
        "dual_validation_window_cycles".to_string(),
        Value::Uint(dual_validation_window_cycles),
    );
    m.insert(
        "started_at_unix_ns".to_string(),
        Value::Timestamp(started_at_unix_ns),
    );
    cb_encode(&Value::Map(m)).expect("schema_migration_started encode infallible")
}

/// Content of a `schema_migration_cycle_validated:{op}` event.
///
/// Emitted on a SAMPLED basis (every Nth cycle plus the decisive cycle) so a
/// long migration window doesn't flood the DAG with one event per cycle.
///
/// ```text
/// Map({
///   "op": String,
///   "at_cycle": Uint,
///   "equivalent": Bool,            // true = candidate matched active this cycle
///   "divergence_reason": String,   // empty when equivalent
/// })
/// ```
pub fn encode_schema_migration_cycle_validated(
    op: &str,
    at_cycle: u64,
    equivalent: bool,
    divergence_reason: &str,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("op".to_string(), Value::String(op.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert("equivalent".to_string(), Value::Bool(equivalent));
    m.insert(
        "divergence_reason".to_string(),
        Value::String(divergence_reason.to_string()),
    );
    cb_encode(&Value::Map(m)).expect("schema_migration_cycle_validated encode infallible")
}

/// Content of a `schema_migration_committed:{op}` event.
///
/// ```text
/// Map({
///   "op": String,
///   "committed_at_cycle": Uint,
///   "started_at_cycle": Uint,
///   "dual_validation_window_cycles": Uint,
/// })
/// ```
pub fn encode_schema_migration_committed(
    op: &str,
    committed_at_cycle: u64,
    started_at_cycle: u64,
    dual_validation_window_cycles: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("op".to_string(), Value::String(op.to_string()));
    m.insert(
        "committed_at_cycle".to_string(),
        Value::Uint(committed_at_cycle),
    );
    m.insert(
        "started_at_cycle".to_string(),
        Value::Uint(started_at_cycle),
    );
    m.insert(
        "dual_validation_window_cycles".to_string(),
        Value::Uint(dual_validation_window_cycles),
    );
    cb_encode(&Value::Map(m)).expect("schema_migration_committed encode infallible")
}

/// Content of a `schema_migration_rolled_back:{op}` event.
///
/// ```text
/// Map({
///   "op": String,
///   "reason": String,            // why the migration rolled back
///   "rolled_back_at_cycle": Uint,
/// })
/// ```
pub fn encode_schema_migration_rolled_back(
    op: &str,
    reason: &str,
    rolled_back_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("op".to_string(), Value::String(op.to_string()));
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    m.insert(
        "rolled_back_at_cycle".to_string(),
        Value::Uint(rolled_back_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("schema_migration_rolled_back encode infallible")
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::{decode, map_get_string, map_get_uint, Value};

    #[test]
    fn node_type_builders_carry_op_suffix() {
        assert_eq!(
            schema_migration_started_node_type("modify_axis_threshold"),
            "schema_migration_started:modify_axis_threshold"
        );
        assert_eq!(
            schema_migration_cycle_validated_node_type("add_axis_to_gradient"),
            "schema_migration_cycle_validated:add_axis_to_gradient"
        );
        assert_eq!(
            schema_migration_committed_node_type("modify_axis_threshold"),
            "schema_migration_committed:modify_axis_threshold"
        );
        assert_eq!(
            schema_migration_rolled_back_node_type("modify_axis_threshold"),
            "schema_migration_rolled_back:modify_axis_threshold"
        );
    }

    #[test]
    fn started_event_carries_all_fields() {
        let diff = vec![0xaa, 0xbb];
        let bytes = encode_schema_migration_started(
            "modify_axis_threshold",
            &diff,
            42,
            100,
            1_700_000_000_000_000_000,
        );
        let m = match decode(bytes.as_ref()).unwrap() {
            Value::Map(m) => m,
            _ => panic!("not a Map"),
        };
        assert_eq!(map_get_string(&m, "op").unwrap(), "modify_axis_threshold");
        assert_eq!(map_get_uint(&m, "started_at_cycle").unwrap(), 42);
        assert_eq!(map_get_uint(&m, "dual_validation_window_cycles").unwrap(), 100);
        match m.get("schema_diff_canonical_bytes") {
            Some(Value::Bytes(b)) => assert_eq!(b, &diff),
            _ => panic!("schema_diff_canonical_bytes missing"),
        }
        match m.get("started_at_unix_ns") {
            Some(Value::Timestamp(t)) => assert_eq!(*t, 1_700_000_000_000_000_000),
            _ => panic!("started_at_unix_ns missing"),
        }
    }

    #[test]
    fn cycle_validated_event_records_equivalence_and_reason() {
        let ok = encode_schema_migration_cycle_validated("op", 7, true, "");
        let m_ok = match decode(ok.as_ref()).unwrap() {
            Value::Map(m) => m,
            _ => panic!(),
        };
        assert!(matches!(m_ok.get("equivalent"), Some(Value::Bool(true))));
        assert_eq!(map_get_string(&m_ok, "divergence_reason").unwrap(), "");

        let bad = encode_schema_migration_cycle_validated("op", 9, false, "axis fruited");
        let m_bad = match decode(bad.as_ref()).unwrap() {
            Value::Map(m) => m,
            _ => panic!(),
        };
        assert!(matches!(m_bad.get("equivalent"), Some(Value::Bool(false))));
        assert_eq!(
            map_get_string(&m_bad, "divergence_reason").unwrap(),
            "axis fruited"
        );
    }

    #[test]
    fn committed_event_carries_window_metadata() {
        let bytes = encode_schema_migration_committed("op", 110, 10, 100);
        let m = match decode(bytes.as_ref()).unwrap() {
            Value::Map(m) => m,
            _ => panic!(),
        };
        assert_eq!(map_get_uint(&m, "committed_at_cycle").unwrap(), 110);
        assert_eq!(map_get_uint(&m, "started_at_cycle").unwrap(), 10);
        assert_eq!(map_get_uint(&m, "dual_validation_window_cycles").unwrap(), 100);
    }

    #[test]
    fn rolled_back_event_carries_reason() {
        let bytes = encode_schema_migration_rolled_back("op", "diverged at cycle 12", 12);
        let m = match decode(bytes.as_ref()).unwrap() {
            Value::Map(m) => m,
            _ => panic!(),
        };
        assert_eq!(map_get_string(&m, "reason").unwrap(), "diverged at cycle 12");
        assert_eq!(map_get_uint(&m, "rolled_back_at_cycle").unwrap(), 12);
    }

    #[test]
    fn determinism_same_inputs_identical_bytes() {
        let a = encode_schema_migration_started("op", &[1, 2, 3], 5, 100, 999);
        let b = encode_schema_migration_started("op", &[1, 2, 3], 5, 100, 999);
        assert_eq!(a.as_ref(), b.as_ref());
    }
}
