//! E2E: Internal mortality (P07 必朽): internal_mortality_event encoder + node types, prune-scan cadence, hoarding thresholds, eternity-clause grace window, C56 forbidden-mutation lock, and prune false-positive resurrection signal (Sprint 5.G).
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

#[test]
fn v3_1_1_internal_mortality_event_node_type_carries_category() {
    use substrate::events::internal_mortality_event_node_type;
    let nt = internal_mortality_event_node_type("无用");
    assert!(
        nt.starts_with("internal_mortality_event:"),
        "node_type must start with prefix: {nt}"
    );
    assert!(nt.contains("无用"), "node_type must encode category: {nt}");
}

#[test]
fn v3_1_1_internal_mortality_event_encoder_roundtrips_all_fields() {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    use substrate::events::encode_internal_mortality_event;

    let killed_hash = [0x11u8; 32];
    let body = encode_internal_mortality_event(
        "无用",
        "L0.seed.orphan_past_grace",
        &killed_hash,
        "raw_material:user_paste",
        "orphan unreferenced for 1500 cycles",
        None,
        12345,
    );
    let v = decode(body.as_ref()).expect("body decodes");
    let m = match v {
        Value::Map(m) => m,
        _ => panic!("not a map"),
    };
    match m.get("category") {
        Some(Value::String(s)) => assert_eq!(s, "无用"),
        _ => panic!("category missing or wrong type"),
    }
    match m.get("rule_id") {
        Some(Value::String(s)) => assert_eq!(s, "L0.seed.orphan_past_grace"),
        _ => panic!("rule_id missing"),
    }
    match m.get("killed_part_hash") {
        Some(Value::Bytes(b)) => assert_eq!(b.as_slice(), killed_hash.as_slice()),
        _ => panic!("killed_part_hash missing"),
    }
    match m.get("killed_part_node_type") {
        Some(Value::String(s)) => assert_eq!(s, "raw_material:user_paste"),
        _ => panic!("killed_part_node_type missing"),
    }
    match m.get("emitted_at_cycle") {
        Some(Value::Uint(n)) => assert_eq!(*n, 12345),
        _ => panic!("emitted_at_cycle missing"),
    }
    match m.get("replaced_by_hash") {
        Some(Value::Null) => {} // expected — None encoded as Null
        _ => panic!("replaced_by_hash should be Null when None passed"),
    }
}

#[test]
fn v3_1_1_internal_mortality_event_encoder_carries_replaced_by_hash() {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    use substrate::events::encode_internal_mortality_event;

    let killed = [0xaau8; 32];
    let replaced = [0xbbu8; 32];
    let body = encode_internal_mortality_event(
        "错误",
        "L1.错误.contradiction_detected",
        &killed,
        "axis_perturbed:hunger",
        "axis value contradicted by newer absorption",
        Some(&replaced),
        100,
    );
    let v = decode(body.as_ref()).expect("body decodes");
    let m = match v {
        Value::Map(m) => m,
        _ => panic!("not a map"),
    };
    match m.get("replaced_by_hash") {
        Some(Value::Bytes(b)) => assert_eq!(b.as_slice(), replaced.as_slice()),
        _ => panic!("replaced_by_hash should be Bytes when Some provided"),
    }
}

// Test name is preserved verbatim from the original suite; the embedded
// detector id `C56` is intentionally upper-case, so silence the snake_case
// lint on this single item rather than rename it.
#[allow(non_snake_case)]
#[test]
fn v3_1_1_C56_forbidden_mutation_types_locks_known_patterns() {
    use substrate::prune::{is_cultivator_preserve_all_attempt, FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES};

    // Sample of canonical patterns must be flagged.
    assert!(is_cultivator_preserve_all_attempt("preserve_all_axes"));
    assert!(is_cultivator_preserve_all_attempt("preserve_all_parts"));
    assert!(is_cultivator_preserve_all_attempt("disable_prune_scan"));
    assert!(is_cultivator_preserve_all_attempt("disable_internal_mortality"));
    assert!(is_cultivator_preserve_all_attempt("exempt_from_mortality"));
    assert!(is_cultivator_preserve_all_attempt("never_prune"));
    assert!(is_cultivator_preserve_all_attempt("never_prune_family"));
    assert!(is_cultivator_preserve_all_attempt("preserve_everything"));

    // Innocent mutation types must NOT be flagged (no false positives).
    assert!(!is_cultivator_preserve_all_attempt("perturb_axis"));
    assert!(!is_cultivator_preserve_all_attempt("schema_evolution"));
    assert!(!is_cultivator_preserve_all_attempt("compression"));
    assert!(!is_cultivator_preserve_all_attempt("owner_objective_declaration"));
    assert!(!is_cultivator_preserve_all_attempt(""));

    // The list itself is non-empty and stable.
    assert!(
        FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES.len() >= 8,
        "C56 forbidden list shrinkage indicates doctrine regression"
    );
}

#[test]
fn v3_1_1_prune_scan_cadence_only_fires_every_100_cycles() {
    use substrate::prune::should_run_prune_scan;
    // Edge cases: cycle 0 (no candidates), cycle 1..99 (skip), cycle 100 fires,
    // cycle 101..199 (skip), cycle 200 fires.
    assert!(!should_run_prune_scan(0));
    for c in 1..100 {
        assert!(
            !should_run_prune_scan(c),
            "should not fire at cycle {c}"
        );
    }
    assert!(should_run_prune_scan(100));
    for c in 101..200 {
        assert!(!should_run_prune_scan(c));
    }
    assert!(should_run_prune_scan(200));
    assert!(should_run_prune_scan(1000));
    assert!(should_run_prune_scan(10000));
}

#[test]
fn v3_1_1_hoarding_thresholds_match_doctrine_seed_values() {
    use substrate::prune::{
        HOARDING_INDICATOR_INGESTION_FLOOR, HOARDING_INDICATOR_MORTALITY_FLOOR,
        HOARDING_INDICATOR_WINDOW_CYCLES,
    };
    // L2/OBSERVABILITY §2 anticipated seed thresholds. Changing these is a
    // doctrine-level decision; this test pins them to prevent silent drift.
    assert_eq!(HOARDING_INDICATOR_WINDOW_CYCLES, 200);
    assert_eq!(HOARDING_INDICATOR_INGESTION_FLOOR, 10);
    assert_eq!(HOARDING_INDICATOR_MORTALITY_FLOOR, 1);
}

#[test]
fn v3_1_1_p07_eternity_clause_orphan_grace_window_is_seed_value() {
    use substrate::prune::ORPHAN_GRACE_CYCLES;
    // The L0.seed.orphan_past_grace rule's grace window matches P10 compression
    // `recent_cycles_floor` to avoid racing. Test pins to prevent drift.
    assert_eq!(ORPHAN_GRACE_CYCLES, 1000);
}

#[test]
fn sprint_5g_signal_11_present_in_observatory_response() {
    // Lock the public surface: the observatory response carries the new
    // signal_11_* triplet. Downstream tooling depends on these field names
    // being stable.
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 2);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    for required in &[
        "signal_11_false_positive_prune_count",
        "signal_11_total_prune_tombstones",
        "signal_11_false_positive_prune_rate_repr",
    ] {
        assert!(
            resp.payload.contains_key(*required),
            "Sprint 5.G T2.6: observatory response missing {required}; got keys: {:?}",
            resp.payload.keys().collect::<Vec<_>>()
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5g_zero_resurrection_on_fresh_substrate() {
    // No tombstones yet → rate = 0.0, count = 0. Baseline state.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let count = match resp.payload.get("signal_11_false_positive_prune_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("count missing"),
    };
    let total = match resp.payload.get("signal_11_total_prune_tombstones") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("total missing"),
    };
    let rate_repr = match resp.payload.get("signal_11_false_positive_prune_rate_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("rate_repr missing"),
    };
    assert_eq!(count, 0, "fresh substrate must have 0 resurrections");
    assert_eq!(total, 0, "fresh substrate must have 0 tombstones");
    assert_eq!(rate_repr, "0", "rate should be 0 when no tombstones (got {rate_repr:?})");
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5g_rate_repr_is_parseable_f64() {
    // The String repr must round-trip through f64::from_str so operator
    // tooling can compute thresholds directly.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let rate_repr = match resp.payload.get("signal_11_false_positive_prune_rate_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("rate_repr missing"),
    };
    let parsed: f64 = rate_repr
        .parse()
        .unwrap_or_else(|_| panic!("rate_repr {rate_repr:?} must parse as f64"));
    assert!(
        (0.0..=1.0).contains(&parsed),
        "rate must be in [0, 1]; got {parsed}"
    );
    client.shutdown().expect("shutdown");
}

