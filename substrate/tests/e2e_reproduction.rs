//! E2E: P8 永恒繁衍 reproduction discipline — generation limits (forkbomb defense).
//!
//! Covers the two load-bearing immune detectors in the sprout path
//! (`reproduction::handle_sprout_child`), specified in
//! `docs/architecture/L1/GOVERNANCE.md` §16 (F22) + `L1/HARD_RULES` C47/C48:
//!
//! - **C47 `generation_depth_exceeded`** (§16.A): a substrate at
//!   `generation_depth == reproduction_lineage_depth_max` cannot sprout (the
//!   child would be `+1` over the cap). Breach → refuse + immune C47.
//! - **C48 `reproduction_lifetime_quota_exceeded`** (§16.C, QUOTA half): a
//!   substrate that has already spawned `reproduction_lifetime_quota` children
//!   cannot sprout again. Breach → refuse + immune C48. (The RATE half of
//!   §16.B is anchor-wall-clock-bound, M-anchor-3 deferred — not tested here.)
//!
//! Each detector gets a positive witness (breach refused + immune DAG node
//! present) and a negative witness (under the limit → child sprouts, no immune
//! node). The C47 suite also asserts the additive `generation_depth` field is
//! threaded into the child's `genesis_event` (root = 0; child = parent + 1) by
//! booting the child and reading its own DAG.
//!
//! The deterministic test seams (`MYCO_TEST_REPRODUCTION_DEPTH_MAX`,
//! `MYCO_TEST_REPRODUCTION_QUOTA`, `MYCO_GENERATION_DEPTH_OVERRIDE`) mirror the
//! established `MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53` precedent; production runs at
//! the §16 constitutional defaults (depth 10 / quota 100).

mod common;
use common::*;

use myco_kernel_shared::canonical_bytes::decode as cb_decode;

/// Sprout a child at `child_dir`, returning the raw `Result` so callers can
/// assert success or refusal. Mirrors the federation suite's SPROUT_CHILD call.
fn try_sprout(
    client: &mut BridgeClient,
    child_dir: &std::path::Path,
) -> Result<myco_kernel_bridge::protocol::Message, myco_kernel_bridge::BridgeError> {
    client.call(
        proto::SPROUT_CHILD,
        build_payload(vec![(
            "child_state_dir",
            CbValue::String(child_dir.to_string_lossy().into_owned()),
        )]),
    )
}

/// Count immune:* DAG nodes whose `node_type` contains `detector_id`.
fn count_immune(client: &mut BridgeClient, detector_id: &str) -> usize {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(100)),
                (
                    "node_type_prefix",
                    CbValue::String(format!("immune:{detector_id}")),
                ),
            ]),
        )
        .expect("query immune nodes");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => panic!("query_recent_nodes response missing 'nodes' array"),
    }
}

/// Read the `generation_depth` recorded in a (booted) substrate's own
/// `genesis_event:*` DAG node. Absent field → 0 (root, byte-compat).
fn child_recorded_generation_depth(client: &mut BridgeClient) -> u64 {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(100)),
                (
                    "node_type_prefix",
                    CbValue::String("genesis_event:".to_string()),
                ),
            ]),
        )
        .expect("query genesis_event node");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        1,
        "a substrate must have exactly one genesis_event node; got {}",
        nodes.len()
    );
    let content = match &nodes[0] {
        CbValue::Map(m) => match m.get("content_canonical_bytes") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("genesis_event node missing content_canonical_bytes"),
        },
        _ => panic!("genesis_event node not a Map"),
    };
    let decoded = cb_decode(&content).expect("decode genesis_event content");
    match decoded {
        CbValue::Map(m) => match m.get("generation_depth") {
            Some(CbValue::Uint(n)) => *n,
            // Absent → 0 (root / pre-8f byte-compat).
            None => 0,
            other => panic!("generation_depth wrong type: {other:?}"),
        },
        _ => panic!("genesis_event content not a Map"),
    }
}

// ===========================================================================
// C47 generation_depth_exceeded (§16.A)
// ===========================================================================

#[test]
fn c47_positive_at_depth_max_refuses_and_emits() {
    // Parent boots with depth-max forced to 0 → a depth-0 root is AT the max,
    // so any sprout (child would be depth 1) must be refused with C47.
    let dir = fresh_state_dir();
    let mut parent = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_REPRODUCTION_DEPTH_MAX".to_string(),
            "0".to_string(),
        )],
    );
    // Parent needs an axis registered so a (would-be) sprout has something to
    // clone — proves the refusal is the depth guard, not an empty-gradient path.
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let child_dir = fresh_state_dir();
    let result = try_sprout(&mut parent, &child_dir);
    assert!(
        result.is_err(),
        "C47: sprout at generation_depth == max must be REFUSED; got Ok"
    );

    // The breach must be recorded as an immune:C47 DAG node in the PARENT.
    assert_eq!(
        count_immune(&mut parent, "C47_generation_depth_exceeded"),
        1,
        "C47: exactly one C47_generation_depth_exceeded immune node expected"
    );
    // And NO child DAG must have been created (refuse-before-spawn).
    assert!(
        !child_dir.join("dag.cb").exists(),
        "C47: a refused sprout must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c47_positive_real_max_via_genesis_depth_override() {
    // End-to-end faithful variant: boot a substrate AT the real §16.A max
    // (depth 10) via the genesis-depth override. This exercises the full
    // depth-threading path (env → Manifest::genesis → genesis_event → boot
    // manifest.generation_depth → C47 guard) at the production cap value, with
    // NO test-only depth-max override in play.
    let dir = fresh_state_dir();
    let mut parent = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_GENERATION_DEPTH_OVERRIDE".to_string(),
            "10".to_string(),
        )],
    );
    // Sanity: the substrate booted at depth 10 (read from its own genesis_event).
    assert_eq!(
        child_recorded_generation_depth(&mut parent),
        10,
        "parent must boot at generation_depth 10 via override"
    );
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let child_dir = fresh_state_dir();
    let result = try_sprout(&mut parent, &child_dir);
    assert!(
        result.is_err(),
        "C47: substrate at the real depth-max (10) must refuse to sprout"
    );
    assert_eq!(
        count_immune(&mut parent, "C47_generation_depth_exceeded"),
        1,
        "C47: real-max breach must emit C47"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c47_negative_below_max_sprouts_child_at_parent_plus_one() {
    // A normal root parent (depth 0, default max 10) is well below the cap →
    // the sprout SUCCEEDS, no C47 fires, and the child's genesis_event records
    // generation_depth = parent + 1 = 1.
    let (mut parent, _dir) = spawn_substrate();
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let child_dir = fresh_state_dir();
    let resp = try_sprout(&mut parent, &child_dir).expect("C47 negative: sprout must succeed");

    // The response carries the child's depth = 1.
    assert!(
        matches!(resp.payload.get("child_generation_depth"), Some(CbValue::Uint(1))),
        "C47 negative: response child_generation_depth must be 1; got {:?}",
        resp.payload.get("child_generation_depth")
    );
    // No C47 immune node in the parent.
    assert_eq!(
        count_immune(&mut parent, "C47_generation_depth_exceeded"),
        0,
        "C47 negative: no C47 should fire for an under-max sprout"
    );
    parent.shutdown().expect("shutdown parent pre-child-boot");

    // Boot the child and confirm IT records generation_depth = 1 in its own
    // genesis_event (proves the additive field is threaded through the child's
    // DAG, the authoritative carrier the child reads at boot).
    let mut child = spawn_substrate_with_state_dir(&child_dir);
    assert_eq!(
        child_recorded_generation_depth(&mut child),
        1,
        "C47 negative: child's genesis_event must record generation_depth = parent + 1"
    );
    child.shutdown().expect("shutdown child");
}

#[test]
fn c47_grandchild_depth_increments_to_two() {
    // Lineage chaining: root(0) → child(1) → grandchild(2). Confirms depth is
    // a true running counter threaded through successive sprouts (not a flat 1).
    let (mut root, _dir) = spawn_substrate();
    root.register_axis("g", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    let child_dir = fresh_state_dir();
    let r1 = try_sprout(&mut root, &child_dir).expect("root sprouts child");
    assert!(matches!(
        r1.payload.get("child_generation_depth"),
        Some(CbValue::Uint(1))
    ));
    root.shutdown().expect("shutdown root");

    // Boot the child and have IT sprout a grandchild. The child already
    // inherited the root's "g" axis via the sprout (its gradient was cloned),
    // so it can sprout immediately without registering anything.
    let mut child = spawn_substrate_with_state_dir(&child_dir);
    assert_eq!(child_recorded_generation_depth(&mut child), 1);
    let grandchild_dir = fresh_state_dir();
    let r2 = try_sprout(&mut child, &grandchild_dir).expect("child sprouts grandchild");
    assert!(
        matches!(r2.payload.get("child_generation_depth"), Some(CbValue::Uint(2))),
        "grandchild depth must be 2; got {:?}",
        r2.payload.get("child_generation_depth")
    );
    child.shutdown().expect("shutdown child");

    // Boot the grandchild — its genesis_event records depth 2.
    let mut grandchild = spawn_substrate_with_state_dir(&grandchild_dir);
    assert_eq!(
        child_recorded_generation_depth(&mut grandchild),
        2,
        "grandchild's genesis_event must record generation_depth 2"
    );
    grandchild.shutdown().expect("shutdown grandchild");
}

// ===========================================================================
// C48 reproduction_lifetime_quota_exceeded (§16.C, QUOTA half)
// ===========================================================================

#[test]
fn c48_positive_over_quota_refuses_and_emits() {
    // Parent boots with the lifetime quota forced to 1. The FIRST sprout is
    // allowed (children_spawned_count 0 + 1 <= 1). The SECOND sprout would make
    // it 1 + 1 = 2 > 1 → refused with C48.
    let dir = fresh_state_dir();
    let mut parent = spawn_substrate_with_env(
        &dir,
        vec![("MYCO_TEST_REPRODUCTION_QUOTA".to_string(), "1".to_string())],
    );
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    // First sprout: under quota → succeeds.
    let first_dir = fresh_state_dir();
    try_sprout(&mut parent, &first_dir).expect("first sprout (under quota) must succeed");
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        0,
        "C48: first (in-quota) sprout must NOT fire C48"
    );

    // Second sprout: over quota → refused + C48.
    let second_dir = fresh_state_dir();
    let result = try_sprout(&mut parent, &second_dir);
    assert!(
        result.is_err(),
        "C48: sprout exceeding lifetime quota must be REFUSED; got Ok"
    );
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        1,
        "C48: over-quota sprout must emit exactly one C48 immune node"
    );
    // The over-quota child must NOT have been created.
    assert!(
        !second_dir.join("dag.cb").exists(),
        "C48: a refused over-quota sprout must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c48_negative_under_quota_sprouts_all_children() {
    // Parent boots with quota = 3. Two sprouts (counts 1 then 2, both <= 3)
    // both succeed and NO C48 fires.
    let dir = fresh_state_dir();
    let mut parent = spawn_substrate_with_env(
        &dir,
        vec![("MYCO_TEST_REPRODUCTION_QUOTA".to_string(), "3".to_string())],
    );
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    for i in 0..2 {
        let child_dir = fresh_state_dir();
        let resp = try_sprout(&mut parent, &child_dir)
            .unwrap_or_else(|e| panic!("C48 negative: sprout #{i} under quota must succeed: {e}"));
        // All these children are depth 1 (parent is a depth-0 root).
        assert!(matches!(
            resp.payload.get("child_generation_depth"),
            Some(CbValue::Uint(1))
        ));
        assert!(
            child_dir.join("dag.cb").exists(),
            "C48 negative: in-quota sprout #{i} must create the child's dag.cb"
        );
    }
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        0,
        "C48 negative: under-quota sprouts must NOT fire C48"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn reproduction_discipline_defaults_match_governance_s16() {
    // Pin the §16 constitutional defaults as a public-surface contract so a
    // refactor that silently changes depth=10 / quota=100 surfaces in CI.
    use substrate::reproduction::{REPRODUCTION_LIFETIME_QUOTA, REPRODUCTION_LINEAGE_DEPTH_MAX};
    assert_eq!(
        REPRODUCTION_LINEAGE_DEPTH_MAX, 10,
        "L1/GOVERNANCE §16.A reproduction_lineage_depth_max default is 10"
    );
    assert_eq!(
        REPRODUCTION_LIFETIME_QUOTA, 100,
        "L1/GOVERNANCE §16.C reproduction_lifetime_quota default is 100"
    );
}
