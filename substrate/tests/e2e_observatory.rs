//! E2E: Living Bets observatory signals: persistence/context-window budget, axis-register / perturbed-axis counts, signal #5 time-trends, doctrine-burst detector, bet_weakening_quorum, emergent composite weights, per-cycle compute/network/storage cost signals.
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

#[test]
fn phase_alpha_observatory_signal_1_basic_persistence_budget() {
    let (mut client, _dir) = spawn_substrate();
    // Do some work so the DAG has content.
    client
        .register_axis("obs_test", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client.perturb("obs_test", 1.5).expect("perturb");

    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory query");
    assert_eq!(resp.message_type, proto::QUERY_SUBSTRATE_OBSERVATORY_RESPONSE);

    let signal_1 = match resp.payload.get("signal_1_persistence_budget") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_1 missing"),
    };
    let node_count = match signal_1.get("dag_node_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("node_count missing"),
    };
    let edge_count = match signal_1.get("dag_edge_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("edge_count missing"),
    };
    let content_bytes = match signal_1.get("dag_total_content_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("content_bytes missing"),
    };
    // genesis_event + axis_registered + axis_perturbed → at least 3 nodes.
    assert!(
        node_count >= 3,
        "expected >=3 nodes after register+perturb; got {node_count}"
    );
    // Linear chain → edges = node_count - 1 (every non-genesis has 1 parent).
    assert!(edge_count >= node_count - 1, "edges {edge_count} < nodes-1 {}", node_count - 1);
    // Content non-trivial.
    assert!(content_bytes > 0, "total bytes should be > 0");

    // Signal #6 should be ABSENT when operator doesn't attest context window.
    assert!(
        resp.payload.get("signal_6_read_window_position").is_none(),
        "signal_6 should be absent without operator-supplied window"
    );

    // **M26.2**: observatory_format_version bumped 3 → 4 (added signals
    // 7/8/9 cost, renamed composite → signal_10, renamed doctrine_burst).
    let fmt = match resp.payload.get("observatory_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("fmt version missing"),
    };
    assert_eq!(fmt, 4, "M26.2 bumps observatory_format_version to 4");

    // M24.5 + M26.2: signals 2/3/4 + composite present.
    assert!(
        resp.payload.contains_key("signal_2_evolution_rate"),
        "M24.5: signal_2 present"
    );
    assert!(
        resp.payload.contains_key("signal_3_read_pattern_diversity"),
        "M24.5: signal_3 present"
    );
    assert!(
        resp.payload.contains_key("signal_4_federation_health"),
        "M24.5: signal_4 present"
    );
    assert!(
        resp.payload.contains_key("signal_10_composite_health"),
        "M26.2: composite renamed from signal_7_composite_health → signal_10_composite_health"
    );

    client.shutdown().expect("shutdown");
}

#[test]
fn m24_5_observatory_signal_2_counts_axis_registers() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("ev1", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register 1");
    client
        .register_axis("ev2", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register 2");

    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s2 = match resp.payload.get("signal_2_evolution_rate") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_2 missing"),
    };
    let count = match s2.get("axis_register_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("axis_register_count missing"),
    };
    assert!(count >= 2, "expected >= 2 axis_register events; got {count}");
    client.shutdown().expect("shutdown");
}

#[test]
fn m24_5_observatory_signal_3_distinct_perturbed_axes() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("a", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("ra");
    client
        .register_axis("b", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("rb");
    client.perturb("a", 0.5).expect("pa1");
    client.perturb("a", 0.7).expect("pa2"); // duplicate axis name; counted once
    client.perturb("b", 0.3).expect("pb1");

    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s3 = match resp.payload.get("signal_3_read_pattern_diversity") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_3 missing"),
    };
    let distinct = match s3.get("distinct_perturbed_axes_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("distinct_perturbed_axes_count missing"),
    };
    assert_eq!(distinct, 2, "expected 2 distinct axes (a + b); got {distinct}");
    client.shutdown().expect("shutdown");
}

#[test]
fn m24_5_observatory_signal_7_composite_is_valid_float() {
    // **M26.2**: composite is now under `signal_10_composite_health` (was
    // `signal_7_composite_health` in v3). Updated test name kept for git
    // history clarity but body asserts the new key.
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("composite_test", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s10 = match resp.payload.get("signal_10_composite_health") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_10_composite_health missing"),
    };
    let composite_repr = match s10.get("composite_health_score_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("composite_health_score_repr missing"),
    };
    let parsed: f64 = composite_repr.parse().expect("composite is parseable float");
    // **M26.2 NOTE**: composite can now be negative (cost signals contribute
    // with negative sign). For a fresh substrate with no cost history, all
    // cost terms are 0, so composite is >= 0 here — but in general the
    // bound is `Number::isFinite`, not `>= 0`.
    assert!(parsed.is_finite(), "composite must be a finite float; got {parsed}");
    let fmt = match s10.get("composite_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("composite_format_version missing"),
    };
    assert_eq!(
        fmt, 4,
        "M26.2: composite_format_version bumped 3 → 4 (negative cost-signal contributions)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn phase_alpha_observatory_signal_6_computes_ratio_when_window_attested() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("o6", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");

    // Operator attests a 1MiB context window.
    let one_mib: u64 = 1024 * 1024;
    let resp = client
        .call(
            proto::QUERY_SUBSTRATE_OBSERVATORY,
            build_payload(vec![(
                "operator_attested_context_window_bytes",
                CbValue::Uint(one_mib),
            )]),
        )
        .expect("query with window");

    let signal_6 = match resp.payload.get("signal_6_read_window_position") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_6 should be present when window is supplied"),
    };
    let window = match signal_6.get("operator_attested_context_window_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("window field missing"),
    };
    assert_eq!(window, one_mib);
    let substrate_bytes = match signal_6.get("substrate_total_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("substrate_total_bytes missing"),
    };
    assert!(substrate_bytes > 0);
    // Ratio repr is a parseable float string.
    let ratio_repr = match signal_6.get("ratio_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("ratio_repr missing"),
    };
    let parsed_ratio: f64 = ratio_repr.parse().expect("ratio parses as float");
    // Substrate is way smaller than 1MiB at this point, so ratio < 1.
    assert!(parsed_ratio < 1.0, "ratio should be < 1.0 for tiny substrate vs 1MiB window; got {parsed_ratio}");
    // And ratio should match substrate_bytes / window exactly (modulo float).
    let expected_ratio = (substrate_bytes as f64) / (one_mib as f64);
    let delta = (parsed_ratio - expected_ratio).abs();
    assert!(delta < 1e-9, "ratio drift: got {parsed_ratio}, expected {expected_ratio}");

    client.shutdown().expect("shutdown");
}

#[test]
fn phase_alpha_observatory_signal_6_handles_zero_window() {
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::QUERY_SUBSTRATE_OBSERVATORY,
            build_payload(vec![(
                "operator_attested_context_window_bytes",
                CbValue::Uint(0),
            )]),
        )
        .expect("zero window query");
    let signal_6 = match resp.payload.get("signal_6_read_window_position") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_6 missing"),
    };
    // Convention: ratio for zero window is "inf" (unbounded).
    let ratio_repr = match signal_6.get("ratio_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("ratio_repr missing"),
    };
    assert_eq!(
        ratio_repr, "inf",
        "zero window should yield 'inf' ratio (substrate has unbounded headroom)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_3_observatory_format_version_3() {
    // **M26.2**: name kept for git history; observatory_format_version
    // bumped 3 → 4 (added signals 7/8/9 cost + renamed composite to
    // signal_10 + renamed doctrine_burst to doctrine_revision_burst_status).
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory query");
    let fmt = match resp.payload.get("observatory_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("observatory_format_version missing"),
    };
    assert_eq!(fmt, 4, "M26.2: observatory_format_version bumped 3 → 4");
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_3_emergent_weights_cold_start_returns_equal() {
    // Fresh substrate with no cycle history yet → emergent_weights cannot
    // be computed; the handler MUST fall back to "equal_cold_start" weights.
    //
    // **M26.2**: weights basis expanded from {1, 2, 4b} to {1, 2, 4b, 7, 8, 9}.
    // Equal cold-start weights are now 1/6 each (was 1/3). Composite is now
    // under signal_10_composite_health (was signal_7_composite_health).
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s10 = match resp.payload.get("signal_10_composite_health") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_10_composite_health missing"),
    };
    let method = match s10.get("weights_method") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("weights_method missing"),
    };
    assert_eq!(
        method, "equal_cold_start",
        "cold-start substrate must use equal weights; got {method}"
    );
    let weights = match s10.get("weights") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_10.weights map missing"),
    };
    let one_sixth = 1.0_f64 / 6.0;
    let eps = 1e-9;
    for k in &["signal_1", "signal_2", "signal_4b", "signal_7", "signal_8", "signal_9"] {
        let w = match weights.get(*k) {
            Some(CbValue::String(s)) => s.parse::<f64>().expect("weight parses"),
            _ => panic!("weights.{k} missing"),
        };
        assert!(
            (w - one_sixth).abs() < eps,
            "{k} weight ≈ 1/6 in cold-start; got {w}"
        );
    }
    let composite_fmt = match s10.get("composite_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("composite_format_version missing"),
    };
    assert_eq!(composite_fmt, 4, "M26.2: composite_format_version bumped 3 → 4");
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_3_emergent_weights_after_history_become_emergent_or_degenerate() {
    // Once the substrate has accumulated ≥10 history snapshots, weights
    // must shift to either "emergent_variance" (signals moved) or
    // "equal_degenerate" (everything flat across the window). A bare
    // axis-register-only substrate has flat signal_4b (no peers) and
    // flat signal_2 (no evolution events) but signal_1 grows with each
    // cycle_advanced event — so we expect "emergent_variance".
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("m25_3_e", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    pump_cycles(&mut client, 12);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    // **M26.2**: composite is under signal_10_composite_health (was signal_7).
    let s10 = match resp.payload.get("signal_10_composite_health") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_10_composite_health missing"),
    };
    let method = match s10.get("weights_method") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("weights_method missing"),
    };
    assert!(
        method == "emergent_variance" || method == "equal_degenerate",
        "post-history weights must be emergent_variance or equal_degenerate; got {method}"
    );
    // **M26.2**: weights basis expanded from 3 dims to 6 dims
    // ({1, 2, 4b, 7, 8, 9}). Sum must still ≈ 1.
    let weights = match s10.get("weights") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_10.weights map missing"),
    };
    let parse_weight = |key: &str| -> f64 {
        match weights.get(key) {
            Some(CbValue::String(s)) => s.parse().expect("weight parses"),
            _ => panic!("weights.{key} missing"),
        }
    };
    let w1 = parse_weight("signal_1");
    let w2 = parse_weight("signal_2");
    let w4b = parse_weight("signal_4b");
    let w7 = parse_weight("signal_7");
    let w8 = parse_weight("signal_8");
    let w9 = parse_weight("signal_9");
    let total = w1 + w2 + w4b + w7 + w8 + w9;
    assert!(
        (total - 1.0).abs() < 1e-6,
        "weights must sum to 1.0; got w1={w1}, w2={w2}, w4b={w4b}, w7={w7}, w8={w8}, w9={w9}, sum={total}"
    );
    println!(
        "M25.3 + M26.2 demonstration: method={method}, w1={w1:.4}, w2={w2:.4}, \
         w4b={w4b:.4}, w7={w7:.4}, w8={w8:.4}, w9={w9:.4}, sum={total:.6}"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_2_signal_5_time_trends_unknown_when_history_short() {
    // Fresh substrate; observatory_history empty → trends MUST be "unknown"
    // and evaluable=false.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s5 = match resp.payload.get("signal_5_time_trends") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_5 missing"),
    };
    let evaluable = match s5.get("evaluable") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("evaluable missing"),
    };
    assert!(!evaluable, "fresh substrate: trends must NOT be evaluable");
    for k in &[
        "signal_1_direction",
        "signal_2_direction",
        "signal_3_direction",
        "signal_4b_direction",
        "signal_6_direction",
    ] {
        let v = match s5.get(*k) {
            Some(CbValue::String(s)) => s.clone(),
            _ => panic!("{k} missing"),
        };
        assert_eq!(v, "unknown", "{k} should be 'unknown' on fresh substrate");
    }
    let window_samples = match s5.get("window_samples") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("window_samples missing"),
    };
    assert_eq!(window_samples, 0, "fresh substrate has zero window samples");
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_2_signal_5_time_trends_evaluable_after_10_cycles() {
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 12);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s5 = match resp.payload.get("signal_5_time_trends") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_5 missing"),
    };
    let evaluable = match s5.get("evaluable") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("evaluable missing"),
    };
    assert!(evaluable, "after ≥10 cycles, trends MUST be evaluable");
    let s1_dir = match s5.get("signal_1_direction") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!(),
    };
    // signal_1 grows with each cycle (one cycle_advanced event each tick),
    // so it MUST trend "up".
    assert_eq!(s1_dir, "up", "signal_1 (dag size) should trend up; got {s1_dir}");
    let window_samples = match s5.get("window_samples") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!(),
    };
    assert!(window_samples >= 10, "window samples >= 10; got {window_samples}");
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_2_bet_weakening_quorum_not_triggered_in_birth() {
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let bwq = match resp.payload.get("bet_weakening_quorum") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("bet_weakening_quorum missing"),
    };
    let evaluable = match bwq.get("evaluable") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("evaluable missing"),
    };
    let triggered = match bwq.get("triggered") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("triggered missing"),
    };
    assert!(!evaluable, "fresh substrate: quorum predicate not evaluable");
    assert!(!triggered, "fresh substrate: quorum cannot fire");
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_1_doctrine_burst_detector_fires_on_excess_axis_registrations() {
    // Burst threshold = 10 CI events in 100-cycle window. Register 12
    // axes rapidly so the burst predicate fires.
    let (mut client, _dir) = spawn_substrate();
    for i in 0..12 {
        let name = format!("burst_axis_{i}");
        client
            .register_axis(&name, "appetite", 5.0, 0.0, 1.0, false, "noop")
            .expect("register");
    }
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    // **M26.2**: doctrine-burst is no longer one of the 10 numbered Living
    // Bet signals — it's a C37 detector output. Renamed from
    // `signal_8_doctrine_revision_burst` → `doctrine_revision_burst_status`.
    let burst = match resp.payload.get("doctrine_revision_burst_status") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("doctrine_revision_burst_status missing"),
    };
    let is_burst = match burst.get("is_burst") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("is_burst missing"),
    };
    // M26.1 C3 fix: window switched from substrate-cycles to wall-clock 90d
    // (L0/cards/LB_living_bets §3 (falsifiability quorum) + §13.1); the burst-count field renamed accordingly.
    let ci_count = match burst.get("ci_events_in_burst_window") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("ci_events_in_burst_window missing"),
    };
    let threshold = match burst.get("burst_threshold") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("burst_threshold missing"),
    };
    assert!(
        ci_count > threshold,
        "12 axis_registered events should exceed threshold {threshold}; got {ci_count}"
    );
    assert!(
        is_burst,
        "is_burst must be true when ci_events_in_burst_window ({ci_count}) > threshold ({threshold})"
    );

    // The handler MUST have emitted a C37 immune sporocarp.
    let immune_resp = client
        .call(
            proto::QUERY_IMMUNE_EVENTS,
            build_payload(vec![("count", CbValue::Uint(50))]),
        )
        .expect("query immune");
    let events = match immune_resp.payload.get("events") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("events missing"),
    };
    // Immune events surface as DAG nodes with `node_type = "immune:{detector_id}"`.
    let mut found_c37 = false;
    for ev in &events {
        if let CbValue::Map(m) = ev {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                if nt == "immune:C37_doctrine_instability_burst" {
                    found_c37 = true;
                    break;
                }
            }
        }
    }
    assert!(
        found_c37,
        "C37_doctrine_instability_burst sporocarp must appear in immune events after burst; \
         events seen: {:?}",
        events
            .iter()
            .filter_map(|e| match e {
                CbValue::Map(m) => m.get("node_type").and_then(|v| match v {
                    CbValue::String(s) => Some(s.clone()),
                    _ => None,
                }),
                _ => None,
            })
            .collect::<Vec<_>>()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_2_operator_context_window_cached_across_queries() {
    // Operator attests a context window in one query; the substrate caches it
    // so subsequent cycle-tick snapshots populate signal_6_ratio_repr without
    // a fresh attestation. We can observe this indirectly by pumping a few
    // cycles after the attested query and then asking for signal_5: the
    // signal_6_direction will eventually become non-"unknown" once history is
    // long enough.
    let (mut client, _dir) = spawn_substrate();
    // Attest a small window.
    let _ = client
        .call(
            proto::QUERY_SUBSTRATE_OBSERVATORY,
            build_payload(vec![(
                "operator_attested_context_window_bytes",
                CbValue::Uint(64 * 1024),
            )]),
        )
        .expect("attested observatory");
    pump_cycles(&mut client, 12);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s5 = match resp.payload.get("signal_5_time_trends") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_5 missing"),
    };
    let sig_6_dir = match s5.get("signal_6_direction") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("signal_6_direction missing"),
    };
    // The substrate's dag grew during pump_cycles → if the cached window
    // attestation is being used, signal_6 should NOT remain "unknown"
    // anymore (we have ≥3 samples) and should trend "up" (substrate
    // consuming more of the window).
    assert_ne!(
        sig_6_dir, "unknown",
        "cached operator window should populate signal_6 history; got '{sig_6_dir}'"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_2_observatory_format_version_is_4() {
    // Fresh substrate; v4 schema is unconditional at this point.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let ver = match resp.payload.get("observatory_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("observatory_format_version missing"),
    };
    assert_eq!(
        ver, 4,
        "M26.2 bumps observatory_format_version to 4; got {ver}"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_2_signal_7_compute_per_cycle_present_with_current_and_rolling_mean() {
    let (mut client, _dir) = spawn_substrate();
    // Pump some cycles so the rolling mean has real samples.
    pump_cycles(&mut client, 3);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s7 = match resp.payload.get("signal_7_compute_per_cycle") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_7_compute_per_cycle missing"),
    };
    let current_ns = match s7.get("current_cycle_ns") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("signal_7.current_cycle_ns missing"),
    };
    // Wall-clock should be > 0 (each cycle does real work: emit cycle_advanced,
    // append observatory snapshot, save dag.cb).
    assert!(
        current_ns > 0,
        "signal_7 current_cycle_ns must be > 0 after real cycles; got {current_ns}"
    );
    let mean_repr = match s7.get("rolling_mean_ns_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("signal_7.rolling_mean_ns_repr missing"),
    };
    let mean: f64 = mean_repr.parse().expect("rolling_mean parseable as f64");
    assert!(mean > 0.0, "rolling_mean_ns must be > 0; got {mean}");
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_2_signal_8_network_per_cycle_is_zero_without_federation_activity() {
    // No federation peer → signal_8 must be exactly 0 across cycles.
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 3);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s8 = match resp.payload.get("signal_8_network_per_cycle") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_8_network_per_cycle missing"),
    };
    let current = match s8.get("current_cycle_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("signal_8.current_cycle_bytes missing"),
    };
    assert_eq!(
        current, 0,
        "signal_8 must be 0 when no federation egress occurred; got {current}"
    );
    let mean_repr = match s8.get("rolling_mean_bytes_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("signal_8.rolling_mean_bytes_repr missing"),
    };
    let mean: f64 = mean_repr.parse().expect("rolling_mean parseable as f64");
    assert_eq!(mean, 0.0, "rolling_mean must be 0; got {mean}");
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_2_signal_9_storage_per_cycle_grows_as_dag_grows() {
    let (mut client, _dir) = spawn_substrate();
    // Pump a few cycles so storage delta has samples to report.
    pump_cycles(&mut client, 3);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s9 = match resp.payload.get("signal_9_storage_per_cycle") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_9_storage_per_cycle missing"),
    };
    let current = match s9.get("current_cycle_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("signal_9.current_cycle_bytes missing"),
    };
    // dag.cb is rewritten every cycle and grows by at least the cycle_advanced
    // event content. Storage delta MUST be positive for a healthy cycle.
    assert!(
        current > 0,
        "signal_9 current_cycle_bytes must be > 0 after dag growth; got {current}"
    );
    let mean_repr = match s9.get("rolling_mean_bytes_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("signal_9.rolling_mean_bytes_repr missing"),
    };
    let mean: f64 = mean_repr.parse().expect("rolling_mean parseable as f64");
    assert!(mean > 0.0, "rolling_mean must be > 0; got {mean}");
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_2_signal_10_composite_replaces_old_signal_7_key() {
    // Verifies the v3 → v4 rename: composite lives under signal_10_composite_health,
    // and the old signal_7_composite_health key is NO LONGER emitted.
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 3);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    assert!(
        resp.payload.get("signal_10_composite_health").is_some(),
        "signal_10_composite_health must be present in v4 schema"
    );
    assert!(
        resp.payload.get("signal_7_composite_health").is_none(),
        "old signal_7_composite_health key must NOT be emitted in v4 (the slot is now signal_7_compute_per_cycle)"
    );
    let s10 = match resp.payload.get("signal_10_composite_health") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_10_composite_health missing"),
    };
    // Composite must include weights for all 6 dimensions {1,2,4b,7,8,9}.
    let weights = match s10.get("weights") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("weights missing"),
    };
    for key in &["signal_1", "signal_2", "signal_4b", "signal_7", "signal_8", "signal_9"] {
        assert!(
            weights.get(*key).is_some(),
            "composite weights must include {key} in v4 schema"
        );
    }
    let composite_format_version = match s10.get("composite_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("composite_format_version missing"),
    };
    assert_eq!(
        composite_format_version, 4,
        "composite_format_version bumped to 4 alongside outer observatory_format_version"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_2_doctrine_revision_burst_status_renamed_from_signal_8_burst() {
    // Verifies the v3 → v4 rename: burst-detector status lives under
    // doctrine_revision_burst_status, not signal_8_doctrine_revision_burst
    // (the old name collided with the new M26.2 actual signal #8 network/cycle).
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    assert!(
        resp.payload.get("doctrine_revision_burst_status").is_some(),
        "doctrine_revision_burst_status must be present in v4 schema"
    );
    assert!(
        resp.payload.get("signal_8_doctrine_revision_burst").is_none(),
        "old signal_8_doctrine_revision_burst key must NOT be emitted in v4 (the slot is now signal_8_network_per_cycle)"
    );
    let burst = match resp.payload.get("doctrine_revision_burst_status") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("doctrine_revision_burst_status missing"),
    };
    // Structural sanity: the four fields C37 detector emits are all present.
    for k in &[
        "ci_events_in_burst_window",
        "burst_window_unix_ns",
        "burst_threshold",
        "is_burst",
    ] {
        assert!(
            burst.get(*k).is_some(),
            "doctrine_revision_burst_status missing field {k}"
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_2_observatory_snapshot_persists_cost_fields_across_restart() {
    // The observatory_history persisted in snapshot.cb must round-trip the
    // M26.2 cost fields (signal_7/8/9). This guards against accidental loss
    // of cost data across substrate reboots.
    let dir = fresh_state_dir();
    // Boot 1: pump enough cycles to write a snapshot (K=10 cycles).
    {
        let mut client = spawn_substrate_with_state_dir(&dir);
        pump_cycles(&mut client, 10);
        client.shutdown().expect("shutdown boot1");
    }
    // snapshot.cb should exist now.
    let snap_path = dir.join("snapshot.cb");
    assert!(
        snap_path.exists(),
        "snapshot.cb must be written after K=10 cycles"
    );
    // Boot 2: reload from snapshot, query observatory, verify cost fields
    // survived the roundtrip (rolling_mean > 0 implies history has cost data).
    {
        let mut client = spawn_substrate_with_state_dir(&dir);
        let resp = client
            .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
            .expect("observatory");
        let s7 = match resp.payload.get("signal_7_compute_per_cycle") {
            Some(CbValue::Map(m)) => m.clone(),
            _ => panic!("signal_7 missing after restart"),
        };
        let mean_repr = match s7.get("rolling_mean_ns_repr") {
            Some(CbValue::String(s)) => s.clone(),
            _ => panic!("signal_7.rolling_mean_ns_repr missing"),
        };
        let mean: f64 = mean_repr.parse().expect("parseable");
        assert!(
            mean > 0.0,
            "signal_7 rolling mean must survive restart; got {mean}"
        );
        client.shutdown().expect("shutdown boot2");
    }
}

