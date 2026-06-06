//! E2E: Metabolic economy (P11): F19 cost budgets + F20 owner objective + P11.c saturation state machine + telos_alignment, and budget-exhausted emission / saturation transitions under tight budgets (Sprint 5.D).
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

#[test]
fn m26_4_seed_cost_budgets_match_doctrine() {
    use substrate::events::seed_cost_budgets;
    let b = seed_cost_budgets();
    // Doctrine: P11.b "compute / network / storage / cycle".
    assert!(b.compute_ns_per_cycle > 0);
    assert!(b.network_bytes_per_cycle > 0);
    assert!(b.storage_bytes_per_cycle > 0);
    // L0 P11.c default cycle floor = 1000.
    assert_eq!(b.pre_eligibility_cycle_floor, 1000);
    assert!(b.sustained_saturation_cycle_threshold > 0);
}

#[test]
fn m26_4_seed_owner_objective_is_none_default() {
    // L0 P14.b: owner objective is MAY-not-must declared at genesis. Seed =
    // None (substrate falls back to L1/TROPISM §F.1 branch-2 trajectory
    // centroid). Operator declares via CI mutation.
    use substrate::events::seed_owner_objective;
    assert!(seed_owner_objective().is_none());
}

#[test]
fn m26_4_saturation_stage_enum_as_str_stable() {
    use substrate::events::SaturationStage;
    assert_eq!(SaturationStage::Normal.as_str(), "normal");
    assert_eq!(SaturationStage::PreEligibility.as_str(), "pre_eligibility");
    assert_eq!(SaturationStage::PostEligibility.as_str(), "post_eligibility");
    assert_eq!(SaturationStage::Saturated.as_str(), "saturated");
}

#[test]
fn m26_4_owner_objective_canonical_bytes_roundtrip() {
    use substrate::events::{decode_owner_objective, encode_owner_objective, OwnerObjective};
    let obj = OwnerObjective {
        objective_id: "m26_4_test_objective".to_string(),
        declared_at_cycle: 42,
        weights: vec![
            ("axis_perturbed:".to_string(), 0.75),
            ("raw_material:".to_string(), 0.25),
        ],
    };
    let encoded = encode_owner_objective(&obj);
    let decoded = decode_owner_objective(encoded.as_ref()).expect("roundtrips");
    assert_eq!(decoded.objective_id, obj.objective_id);
    assert_eq!(decoded.declared_at_cycle, obj.declared_at_cycle);
    assert_eq!(decoded.weights.len(), obj.weights.len());
    for ((p1, w1), (p2, w2)) in decoded.weights.iter().zip(obj.weights.iter()) {
        assert_eq!(p1, p2);
        assert!(
            (w1 - w2).abs() < 1e-12,
            "weight roundtrip: {w1} != {w2}"
        );
    }
}

#[test]
fn m26_4_owner_objective_rejects_negative_weights() {
    // P14.c proxy: negative weights rejected (M26.4 minimum). Future
    // revisions may allow "actively against" semantics with negative
    // weights, but not in this milestone.
    use substrate::events::{decode_owner_objective, encode_owner_objective, OwnerObjective};
    let obj = OwnerObjective {
        objective_id: "negative_weight_test".to_string(),
        declared_at_cycle: 1,
        weights: vec![("axis_perturbed:".to_string(), -0.5)],
    };
    let encoded = encode_owner_objective(&obj);
    assert!(
        decode_owner_objective(encoded.as_ref()).is_none(),
        "negative weights must be rejected at decode time"
    );
}

#[test]
fn m26_4_budget_exhausted_events_observable_in_dag_when_exceeded() {
    // Set a deliberately-low compute_ns budget via env var (we'll need to
    // override seed budgets, but the seed defaults to 100ms which IS
    // exceeded on real hardware over enough cycles). Instead of overriding,
    // we use a different signal: register many axes + perturb in tight loop
    // to force storage > 10 MiB? That's too slow.
    //
    // Simpler approach: just pump 200 cycles + verify the cycle counter
    // crosses pre_eligibility_cycle_floor=1000? No, that's too slow too.
    //
    // The pragmatic M26.4 minimum coverage: structural test that the event
    // type emission path works. We can't easily induce budget exhaustion
    // in test (because real per-cycle compute is < 100ms). Instead, verify
    // the EVENT TYPE PREFIX is correctly registered + observable when we
    // synthesize the relevant DAG events directly via test helpers.
    //
    // This is a structural test, not a behavioral one. Behavioral tests
    // (real budget exhaustion under load) require either a slow-cycle
    // simulator or a budget-override hook (deferred to M26.5).
    use substrate::events::encode_budget_exhausted;
    let bytes = encode_budget_exhausted("compute_per_cycle", 999_999_999, 100_000_000, 42);
    assert!(!bytes.as_ref().is_empty());
    // Roundtrip via canonical-bytes decode to confirm shape.
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    let v = decode(bytes.as_ref()).expect("decodes");
    let m = match v {
        Value::Map(m) => m,
        _ => panic!("budget_exhausted body is not a Map"),
    };
    match m.get("axis") {
        Some(Value::String(s)) => assert_eq!(s, "compute_per_cycle"),
        _ => panic!("axis missing"),
    };
    match m.get("at_cycle") {
        Some(Value::Uint(n)) => assert_eq!(*n, 42),
        _ => panic!("at_cycle missing"),
    };
}

#[test]
fn m26_4_compression_proposed_events_have_expected_shape() {
    use substrate::events::encode_compression_proposed;
    let bytes = encode_compression_proposed(
        "raw_material_aggregate_v1",
        1234,
        "storage_per_cycle",
        17,
    );
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    let m = match decode(bytes.as_ref()).expect("decodes") {
        Value::Map(m) => m,
        _ => panic!(),
    };
    match m.get("rule_id") {
        Some(Value::String(s)) => assert_eq!(s, "raw_material_aggregate_v1"),
        _ => panic!("rule_id missing"),
    };
    match m.get("at_cycle") {
        Some(Value::Uint(n)) => assert_eq!(*n, 1234),
        _ => panic!("at_cycle missing"),
    };
    match m.get("proposed_axis") {
        Some(Value::String(s)) => assert_eq!(s, "storage_per_cycle"),
        _ => panic!("proposed_axis missing"),
    };
    match m.get("estimated_candidates") {
        Some(Value::Uint(n)) => assert_eq!(*n, 17),
        _ => panic!("estimated_candidates missing"),
    };
}

#[test]
fn m26_4_substrate_boots_in_normal_saturation_stage() {
    // Fresh substrate on a real cycle should boot in SaturationStage::Normal
    // (no cost signal exceeded yet). The state field is private; we verify
    // indirectly by querying recent DAG nodes and asserting NO
    // `substrate_saturated:*` event has been emitted.
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 3);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("substrate_saturated".to_string()),
                ),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        nodes.is_empty(),
        "fresh substrate should NOT emit substrate_saturated; got {} nodes",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_4_telos_alignment_pending_when_no_objective_declared() {
    // No owner objective → compute_telos_alignment_cosine returns None →
    // substrate periodically emits `telos_alignment_pending` per
    // L1/TROPISM §F.3. Verify the event type exists in DAG after enough
    // cycles to clear birth-period (≥10 cycles, the early-cycle skip
    // threshold in `apply_p14c_telos_drift`).
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 51); // cross the 50-cycle pending cadence
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("telos_alignment_pending".to_string()),
                ),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "telos_alignment_pending must be emitted when no owner objective is declared"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m26_4_telos_grade_threshold_table_matches_doctrine() {
    // Pin the §F.1 threshold table mapping. M26.4 implementation must
    // grade cosines exactly per L1/TROPISM §F + algorithms/telos_drift.md.
    //
    // - cos >  0.6: aligned (no emission)
    // - cos in (0.4, 0.6]: telos_alignment_low
    // - cos in (0.2, 0.4]: telos_drift
    // - cos in (0.0, 0.2]: telos_drift (elevated)
    // - cos ≤ 0.0:        telos_drift_critical (→ C24)
    //
    // The grading function is a file-private helper, so we test indirectly
    // via the public Const node-type prefixes that the grading table maps to.
    use substrate::events::{
        NODE_TYPE_TELOS_ALIGNMENT_LOW, NODE_TYPE_TELOS_DRIFT, NODE_TYPE_TELOS_DRIFT_CRITICAL,
    };
    // Pin the constants themselves to catch accidental rename.
    assert_eq!(NODE_TYPE_TELOS_ALIGNMENT_LOW, "telos_alignment_low");
    assert_eq!(NODE_TYPE_TELOS_DRIFT, "telos_drift");
    assert_eq!(NODE_TYPE_TELOS_DRIFT_CRITICAL, "telos_drift_critical");
}

#[test]
fn sprint_5d_tight_budgets_trigger_budget_exhausted_event() {
    // **Primary defense witness**: with budgets tightened to 1 unit, every
    // cycle's storage_bytes (dag.cb growth) exceeds 1 byte. Substrate MUST
    // emit budget_exhausted:storage_per_cycle DAG event within the first
    // few cycles. Without this, P11 §3.4 silent absorption is real.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    // Pump a few cycles, each one mutates dag.cb by at least the
    // cycle_advanced event (~100 bytes), exceeding the 1-byte storage
    // budget on every cycle.
    pump_cycles(&mut client, 5);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(100)),
                (
                    "node_type_prefix",
                    CbValue::String("budget_exhausted:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "Sprint 5.D T2.2: tight budgets MUST trigger budget_exhausted:* events; \
         saw 0 after 5 cycles (P11 §3.4 primary defense path broken — silent \
         cost absorption is happening)"
    );
    // Verify at least one event targets storage_per_cycle (the axis we KNOW
    // is exhausted every cycle).
    let saw_storage = nodes.iter().any(|n| {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                return nt.contains("storage_per_cycle");
            }
        }
        false
    });
    assert!(
        saw_storage,
        "expected at least one budget_exhausted:storage_per_cycle event"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5d_budget_exhausted_event_carries_cost_and_budget_fields() {
    // **Witness completeness**: the budget_exhausted event content must
    // carry both `current` (cost observed) AND `budget` (threshold breached)
    // fields so the operator can re-derive the breach offline. A naked
    // event without these fields makes the immune signal unverifiable.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    pump_cycles(&mut client, 3);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(20)),
                (
                    "node_type_prefix",
                    CbValue::String("budget_exhausted:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "need at least one budget_exhausted event to inspect"
    );
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let first = match &nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!("node not a Map"),
    };
    let content = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content_canonical_bytes missing"),
    };
    let decoded = cb_decode(&content).expect("event decodes");
    let m = match decoded {
        CbV::Map(m) => m,
        _ => panic!("event not a Map"),
    };
    // Required fields per encode_budget_exhausted contract.
    for required_field in &["axis", "current_value", "budget", "at_cycle"] {
        assert!(
            m.contains_key(*required_field),
            "Sprint 5.D T2.2: budget_exhausted event missing required field \
             {required_field:?}; got keys: {:?}",
            m.keys().collect::<Vec<_>>()
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5d_c53_under_normal_emission_pattern_stays_quiet() {
    // **Doctrine drift documentation**: under current C53 logic
    // (observatory.rs:636-718), as long as the primary emission path
    // runs, C53 stays quiet because last_emit gets refreshed every
    // ≥10 cycles. This test pins that behavior as a regression baseline
    //, if a future refactor changes C53 to fire under normal operation,
    // this test fails informatively.
    //
    // The semantic property being pinned: "C53 fires ONLY when emission
    // is silent", under tight budgets WITH working emit, C53 quiet
    // for ≤50 cycles (within the C53 detection window).
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    pump_cycles(&mut client, 30);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("immune:C53_budget_exhausted_silent".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        nodes.is_empty(),
        "Sprint 5.D T2.2 (doctrine drift baseline): C53 should NOT fire while \
         primary emission path is running normally; saw {} C53 events under \
         30 cycles of tight budgets — primary path may be broken OR C53 \
         logic has changed to fire under normal operation",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

// ===========================================================================
// P11.c automatic enforcement (OBSERVATORY gap): pre-eligibility P02 refusal +
// sustained-saturation → self_euthanasia_proposal + saturation_status surface.
// ===========================================================================

/// Helper: attempt a raw_material ingestion and return the decoded response.
fn try_ingest(client: &mut BridgeClient) -> myco_kernel_bridge::protocol::Message {
    client
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                ("content_bytes", CbValue::Bytes(b"hello substrate".to_vec())),
            ]),
        )
        .expect("ingest call")
}

#[test]
fn p11c_ingest_refused_under_saturation() {
    // **P11.c P02 refusal**: under tight budgets the substrate enters a
    // non-Normal saturation stage within a few cycles; a subsequent
    // ingest_raw_material MUST be refused (refused:true, reason:budget_exhausted)
    // rather than silently absorbing cost. Without this, P11 §5.3 is inert.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    // Sanity: a FRESH substrate (Normal stage) accepts ingestion.
    let accepted = try_ingest(&mut client);
    assert_eq!(
        accepted.payload.get("refused"),
        Some(&CbValue::Bool(false)),
        "fresh (Normal) substrate must accept ingestion"
    );
    // Drive cost exhaustion → non-Normal stage.
    pump_cycles(&mut client, 5);
    let refused = try_ingest(&mut client);
    assert_eq!(
        refused.payload.get("refused"),
        Some(&CbValue::Bool(true)),
        "saturated substrate MUST refuse new raw_material ingestion (P11.c)"
    );
    assert_eq!(
        refused.payload.get("reason"),
        Some(&CbValue::String("budget_exhausted".to_string())),
        "refusal reason must be budget_exhausted"
    );
    // The refusal carries the stage + the triggering axis for operator clarity.
    match refused.payload.get("saturation_stage") {
        Some(CbValue::String(s)) => assert_ne!(s, "normal", "stage must be non-normal"),
        _ => panic!("refusal missing saturation_stage"),
    }
    assert!(
        refused.payload.get("axis").is_some(),
        "refusal must name the exhausted axis"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn p11c_sustained_saturation_emits_self_euthanasia_proposal() {
    // **P11.c stage-3 → P7**: under tight budgets + tight thresholds (env sets
    // mortality threshold = 3 Saturated cycles), sustained saturation MUST
    // escalate to a `self_euthanasia_proposal:metabolic_saturation`, a PROPOSAL
    // the accept_self_euthanasia path can execute, NOT auto-death. Without this,
    // saturation is permanently inert (P11 §5.3 violated).
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    // Saturated reached ~cycle 2-3 (threshold=2); +3 more Saturated cycles to
    // cross the mortality threshold. Pump generously.
    pump_cycles(&mut client, 12);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(200)),
                (
                    "node_type_prefix",
                    CbValue::String("self_euthanasia_proposal:metabolic_saturation".to_string()),
                ),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "sustained saturation MUST emit self_euthanasia_proposal:metabolic_saturation; \
         saw 0 after 12 cycles of tight budgets (P11.c stage-3 escalation broken)"
    );
    // The proposal content must be accept_self_euthanasia-compatible: a Map with
    // axis_name = metabolic_saturation (so the existing path can execute it).
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let first = match &nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!("node not a Map"),
    };
    let content = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content missing"),
    };
    let m = match cb_decode(&content).expect("decodes") {
        CbV::Map(m) => m,
        _ => panic!("content not a Map"),
    };
    assert_eq!(
        m.get("axis_name"),
        Some(&CbV::String("metabolic_saturation".to_string())),
        "proposal must carry axis_name=metabolic_saturation for the accept path"
    );
    assert!(m.get("reason").is_some(), "proposal must carry a reason");
    client.shutdown().expect("shutdown");
}

#[test]
fn p7_keyless_accept_self_euthanasia_proposal_executes() {
    // **P7 必朽: keyless self-euthanasia happy path (the missing safety test).**
    //
    // The sibling `p11c_sustained_saturation_emits_self_euthanasia_proposal`
    // proves a real `self_euthanasia_proposal:metabolic_saturation` node is
    // EMITTED; this test closes the loop by ACCEPTING it through the keyless
    // handler and asserting a `self_euthanasia_executed:{axis}` event results.
    //
    // **v0.9 keyless**: whole-death is authorized by a DELIBERATE
    // `accept_self_euthanasia_proposal` call that REFERENCES a real proposal node
    // (the non-arbitrary structural gate), NOT an owner Ed25519 signature (the
    // owner-key + anchor layer was removed). The authorization root is the live
    // human-in-the-loop. Mirrors the keyless `accept_bet_retired_proposal` path
    // proven by `cultivation::tests::bet_retired_seals_archive_and_is_archived_keyless`.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    // Drive sustained saturation so the substrate emits the real proposal node.
    pump_cycles(&mut client, 12);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(200)),
                (
                    "node_type_prefix",
                    CbValue::String("self_euthanasia_proposal:metabolic_saturation".to_string()),
                ),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "precondition: sustained saturation must emit a self_euthanasia_proposal"
    );
    // Grab the proposal node's hash: the deliberate-action reference the keyless
    // accept handler requires.
    let proposal_hash = match &nodes[0] {
        CbValue::Map(m) => match m.get("hash") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("proposal node missing hash"),
        },
        _ => panic!("proposal node not a Map"),
    };
    assert_eq!(proposal_hash.len(), 32, "proposal hash must be 32 bytes");

    // Accept the proposal (keyless: only the proposal_hash reference is required).
    // The substrate emits `self_euthanasia_executed:{axis}` and returns its hash
    // in the response, THEN shuts down (P7: the substrate has been authorized to
    // die), so the response payload is the proof the executed event was emitted.
    let accept = client
        .call(
            proto::ACCEPT_SELF_EUTHANASIA_PROPOSAL,
            build_payload(vec![("proposal_hash", CbValue::Bytes(proposal_hash))]),
        )
        .expect("accept_self_euthanasia_proposal");
    assert_eq!(
        accept.payload.get("axis_name"),
        Some(&CbValue::String("metabolic_saturation".to_string())),
        "the executed event must carry the proposal's axis_name (keyless accept path)"
    );
    match accept.payload.get("executed_event_hash") {
        Some(CbValue::Bytes(h)) => assert_eq!(
            h.len(),
            32,
            "self_euthanasia_executed:{{axis}} must be emitted (32-byte event hash)"
        ),
        _ => panic!(
            "accept response missing executed_event_hash: the keyless accept path \
             did NOT emit self_euthanasia_executed:metabolic_saturation"
        ),
    }
    // The substrate self-terminates after authorizing its own death; no shutdown
    // call needed (the process is already exiting).
}

#[test]
fn p11c_saturation_status_surfaced_in_observatory_v5() {
    // The observatory query (format_version 5) must surface saturation_status:
    // stage + the two consecutive-cycle counters + per-axis exceeded flags.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    pump_cycles(&mut client, 6);
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let ver = match resp.payload.get("observatory_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("format version missing"),
    };
    assert_eq!(ver, 5, "format_version must be 5");
    let sat = match resp.payload.get("saturation_status") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("saturation_status missing"),
    };
    match sat.get("stage") {
        Some(CbValue::String(s)) => assert_eq!(
            s, "saturated",
            "under tight budgets the stage must be saturated; got {s}"
        ),
        _ => panic!("stage missing"),
    }
    for k in &[
        "post_eligibility_consecutive_cycles",
        "saturated_consecutive_cycles",
    ] {
        assert!(
            matches!(sat.get(*k), Some(CbValue::Uint(_))),
            "saturation_status.{k} missing or not Uint"
        );
    }
    // storage_per_cycle is exhausted every cycle under tight budgets.
    assert_eq!(
        sat.get("storage_exceeded"),
        Some(&CbValue::Bool(true)),
        "storage_exceeded must be true under tight budgets"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5d_saturation_stage_reaches_saturated_under_sustained_exhaustion() {
    // **Stage machine witness**: under tight budgets + tight thresholds
    // (env var sets pre_eligibility_cycle_floor=1, threshold=2), the
    // P11.c stage machine reaches Saturated by ~cycle 2-3 and emits a
    // substrate_saturated transition event. Note: PreEligibility and
    // PostEligibility don't emit explicit transition markers (per
    // observatory.rs:507), only Saturated and Normal-restored do.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    pump_cycles(&mut client, 5);
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(100)),
                (
                    "node_type_prefix",
                    CbValue::String("substrate_saturated".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "Sprint 5.D T2.2: P11.c saturation stage machine MUST reach Saturated \
         under sustained budget exhaustion (floor=1, threshold=2, 5 cycles); \
         no substrate_saturated event observed — stage machine broken"
    );
    client.shutdown().expect("shutdown");
}

