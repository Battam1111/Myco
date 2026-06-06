//! E2E: P03 §10.4 two-phase schema migration (v3.1.1 Sprint 8.G).
//!
//! Spawns the real `myco-substrate` binary (which spawns the Python kernel
//! worker), drives it through the M5 protocol as the operator, and exercises
//! the full multi-cycle dual-validation FSM end-to-end across all three
//! languages:
//!
//!   - happy-path commit (migration_mode → started → advance window → committed)
//!   - divergence rollback
//!   - C66 window-exceeded (positive + negative)
//!   - operator abort_migration
//!   - cold-resume mid-window (shutdown + respawn → still pending via DAG replay)
//!   - back-compat (migration_mode absent → single-cycle path unchanged)
//!
//! Mirrors the `e2e_attestation.rs` harness; shared spawn/build helpers live in
//! `tests/common/mod.rs`.

mod common;
use common::*;

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
use myco_kernel_shared::crypto::Ed25519PrivateKey;
use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// schema_diff + signing helpers.
// ---------------------------------------------------------------------------

fn schema_diff_modify_threshold(axis: &str, new_threshold: &str) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("op".to_string(), Value::String("modify_axis_threshold".to_string()));
    m.insert("axis_name".to_string(), Value::String(axis.to_string()));
    m.insert(
        "new_threshold_repr".to_string(),
        Value::String(new_threshold.to_string()),
    );
    cb_encode(&Value::Map(m)).expect("encode").0
}

fn schema_diff_add_axis(axis: &str, threshold: &str, is_mortality: bool) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("op".to_string(), Value::String("add_axis_to_gradient".to_string()));
    m.insert("axis_name".to_string(), Value::String(axis.to_string()));
    m.insert("axis_class".to_string(), Value::String("appetite".to_string()));
    m.insert(
        "fruiting_threshold_repr".to_string(),
        Value::String(threshold.to_string()),
    );
    m.insert("initial_value_repr".to_string(), Value::String("0.0".to_string()));
    m.insert(
        "decay_rate_per_cycle_repr".to_string(),
        Value::String("1.0".to_string()),
    );
    m.insert("is_mortality_signal".to_string(), Value::Bool(is_mortality));
    m.insert("update_rule_kind".to_string(), Value::String("noop".to_string()));
    cb_encode(&Value::Map(m)).expect("encode").0
}

/// Sign content with the seed-derived owner key (M10 path: the substrate
/// verifies attestation_signature against the active owner key, which is the
/// pinned operator pubkey when spawned with a signing seed).
fn sign(seed: &[u8; 32], content: &[u8]) -> Vec<u8> {
    let key = Ed25519PrivateKey::from_seed(seed);
    key.sign(content).as_ref().to_vec()
}

/// Register an axis on the substrate (forwarded to Python).
fn register_axis(client: &mut BridgeClient, name: &str, threshold: f64, mortality: bool) {
    client
        .register_axis(
            name,
            if mortality { "decay" } else { "appetite" },
            threshold,
            0.0,
            1.0,
            mortality,
            if mortality { "decay" } else { "noop" },
        )
        .expect("register_axis");
}

/// Submit a schema_evolution mutation with migration_mode=true, signed.
fn submit_migration(
    client: &mut BridgeClient,
    seed: &[u8; 32],
    diff: &[u8],
) -> std::collections::BTreeMap<String, CbValue> {
    let sig = sign(seed, diff);
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("schema_evolution".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(diff.to_vec())),
                ("attestation_signature", CbValue::Bytes(sig)),
                ("migration_mode", CbValue::Bool(true)),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit_mutation");
    resp.payload
}

fn get_bool(payload: &std::collections::BTreeMap<String, CbValue>, key: &str) -> bool {
    matches!(payload.get(key), Some(CbValue::Bool(true)))
}

fn query_pending(
    client: &mut BridgeClient,
) -> std::collections::BTreeMap<String, CbValue> {
    client
        .call(proto::QUERY_MIGRATION_PENDING, build_payload(vec![]))
        .expect("query_migration_pending")
        .payload
}

/// Count DAG nodes whose node_type starts with `prefix`.
fn count_nodes(client: &mut BridgeClient, prefix: &str) -> usize {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(500)),
                ("node_type_prefix", CbValue::String(prefix.to_string())),
            ]),
        )
        .expect("query recent");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => 0,
    }
}

/// Snapshot axis values (forwarded to Python).
fn snapshot_axes(client: &mut BridgeClient) -> std::collections::BTreeMap<String, f64> {
    client.snapshot().expect("snapshot")
}

// ---------------------------------------------------------------------------
// 1. Happy-path commit.
// ---------------------------------------------------------------------------

#[test]
fn migration_happy_path_commits_after_window() {
    let seed: [u8; 32] = [0x11; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);
    register_axis(&mut client, "hunger", 10.0, false);

    // Start a migration that ADDS a new appetite axis with a high threshold so
    // it never fruits → the candidate is equivalent to active every cycle
    // (the new axis does nothing observable until commit makes it real).
    let diff = schema_diff_add_axis("grown", "1000.0", false);
    let resp = submit_migration(&mut client, &seed, &diff);
    assert!(
        get_bool(&resp, "accepted"),
        "migration submit should be accepted (signed CI); reason={:?}",
        resp.get("rejection_reason")
    );
    assert!(get_bool(&resp, "migration_mode"), "migration_mode echoed true");
    assert!(get_bool(&resp, "candidate_built"), "candidate built");

    // schema_migration_started event present; NOT yet committed.
    assert_eq!(count_nodes(&mut client, "schema_migration_started:"), 1);
    assert_eq!(count_nodes(&mut client, "schema_migration_committed:"), 0);
    assert_eq!(count_nodes(&mut client, "evolution_succeeded:"), 0);

    // query_migration_pending reports pending.
    let pending = query_pending(&mut client);
    assert!(get_bool(&pending, "pending"), "migration should be pending");
    assert_eq!(
        pending.get("op"),
        Some(&CbValue::String("add_axis_to_gradient".to_string()))
    );

    // The active gradient is UNCHANGED mid-window: "grown" not yet present.
    let mid = snapshot_axes(&mut client);
    assert!(!mid.contains_key("grown"), "active gradient must not yet have the candidate axis");
    assert!(mid.contains_key("hunger"));

    // Advance the full dual-validation window (default 100) + a couple extra so
    // the decisive (window-complete) cycle fires the commit.
    for cycle in 1..=103u64 {
        client.advance(cycle).expect("advance");
    }

    // Now committed: schema_migration_committed + legacy evolution_succeeded
    // siblings present, pending cleared.
    assert_eq!(
        count_nodes(&mut client, "schema_migration_committed:"),
        1,
        "exactly one committed event after the window"
    );
    assert_eq!(
        count_nodes(&mut client, "evolution_succeeded:"),
        1,
        "legacy evolution_succeeded sibling must be emitted on commit (back-compat)"
    );
    let pending_after = query_pending(&mut client);
    assert!(!get_bool(&pending_after, "pending"), "migration no longer pending after commit");

    // The active gradient now carries the committed axis (verifies Python
    // commit_migration promoted the candidate to active).
    let after = snapshot_axes(&mut client);
    assert!(
        after.contains_key("grown"),
        "committed axis must be present in the active gradient post-commit"
    );

    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// 2. Divergence rollback.
// ---------------------------------------------------------------------------

#[test]
fn migration_diverges_and_rolls_back() {
    let seed: [u8; 32] = [0x22; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);
    // A DECAY mortality axis that does NOT fruit (threshold far below value).
    register_axis(&mut client, "death", -100.0, true);

    // Candidate RAISES the mortality threshold to 100 so it fruits its
    // mortality_signal (value decays from 10 but stays >= 0, which is <= 100)
    // where the active (threshold -100) does not → Option-A divergence.
    let diff = schema_diff_modify_threshold("death", "100.0");
    let resp = submit_migration(&mut client, &seed, &diff);
    assert!(get_bool(&resp, "accepted"));
    assert!(get_bool(&resp, "candidate_built"));
    assert_eq!(count_nodes(&mut client, "schema_migration_started:"), 1);

    // A single advance should trigger divergence → rollback.
    client.advance(1).expect("advance");

    assert_eq!(
        count_nodes(&mut client, "schema_migration_rolled_back:"),
        1,
        "divergence must roll back within the first validating cycle"
    );
    assert_eq!(
        count_nodes(&mut client, "evolution_failed:"),
        1,
        "legacy evolution_failed sibling must be emitted on rollback (back-compat)"
    );
    assert_eq!(
        count_nodes(&mut client, "schema_migration_committed:"),
        0,
        "a diverged migration must NOT commit"
    );
    let pending = query_pending(&mut client);
    assert!(!get_bool(&pending, "pending"), "migration cleared after rollback");

    // The active mortality threshold is untouched: advancing further does not
    // fruit a mortality sporocarp (active threshold is still -100).
    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// 3. C66 window-exceeded: negative (does not fire while validating normally).
// ---------------------------------------------------------------------------

#[test]
fn migration_c66_does_not_fire_within_window_plus_grace() {
    let seed: [u8; 32] = [0x33; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);
    register_axis(&mut client, "hunger", 10.0, false);

    let diff = schema_diff_add_axis("grown", "1000.0", false);
    submit_migration(&mut client, &seed, &diff);

    // Advance a handful of cycles — well within window (100) + grace (10).
    for cycle in 1..=5u64 {
        client.advance(cycle).expect("advance");
    }
    assert_eq!(
        count_nodes(&mut client, "immune:C66_schema_migration_window_exceeded"),
        0,
        "C66 must NOT fire within window+grace"
    );
    // Still pending (window not complete).
    assert!(get_bool(&query_pending(&mut client), "pending"));
    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// 4. Operator abort.
// ---------------------------------------------------------------------------

#[test]
fn migration_operator_abort_rolls_back() {
    let seed: [u8; 32] = [0x44; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);
    register_axis(&mut client, "hunger", 10.0, false);

    let diff = schema_diff_add_axis("grown", "1000.0", false);
    submit_migration(&mut client, &seed, &diff);
    assert!(get_bool(&query_pending(&mut client), "pending"));

    // Advance a few cycles (mid-window), then operator submits abort_migration.
    for cycle in 1..=3u64 {
        client.advance(cycle).expect("advance");
    }

    // abort_migration is a CI mutation; sign its content with the owner key.
    let mut abort_content = BTreeMap::new();
    abort_content.insert("op".to_string(), Value::String("add_axis_to_gradient".to_string()));
    abort_content.insert(
        "reason".to_string(),
        Value::String("operator changed their mind".to_string()),
    );
    let abort_bytes = cb_encode(&Value::Map(abort_content)).expect("encode").0;
    let abort_sig = sign(&seed, &abort_bytes);
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("abort_migration".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(abort_bytes)),
                ("attestation_signature", CbValue::Bytes(abort_sig)),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("abort submit");
    assert!(
        matches!(resp.payload.get("accepted"), Some(CbValue::Bool(true))),
        "abort_migration should be accepted as a signed CI mutation; reason={:?}",
        resp.payload.get("rejection_reason")
    );

    // Migration rolled back + cleared.
    assert_eq!(count_nodes(&mut client, "schema_migration_rolled_back:"), 1);
    assert!(!get_bool(&query_pending(&mut client), "pending"));
    // Active gradient unchanged (axis never added).
    assert!(!snapshot_axes(&mut client).contains_key("grown"));
    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// 5. Cold-resume mid-window.
// ---------------------------------------------------------------------------

#[test]
fn migration_resumes_across_restart_via_dag_replay() {
    let seed: [u8; 32] = [0x55; 32];
    let dir = fresh_state_dir();
    {
        let mut client = spawn_substrate_with_signing_seed(&dir, seed);
        register_axis(&mut client, "hunger", 10.0, false);
        let diff = schema_diff_add_axis("grown", "1000.0", false);
        submit_migration(&mut client, &seed, &diff);
        // Advance a couple cycles (mid-window), then shut down.
        for cycle in 1..=3u64 {
            client.advance(cycle).expect("advance");
        }
        assert!(get_bool(&query_pending(&mut client), "pending"));
        client.shutdown().expect("shutdown first boot");
    }

    // Respawn against the SAME state_dir (with the same signing seed — the
    // first boot pinned this operator identity, so M9 C2 downgrade protection
    // requires the resume handshake to present it too). The substrate replays
    // the DAG (and/or loads snapshot.cb) and must resume the in-flight migration.
    let mut client2 = spawn_substrate_with_signing_seed(&dir, seed);
    let pending = query_pending(&mut client2);
    assert!(
        get_bool(&pending, "pending"),
        "migration must still be pending after restart (resumed from DAG)"
    );
    assert_eq!(
        pending.get("op"),
        Some(&CbValue::String("add_axis_to_gradient".to_string())),
        "resumed migration op must match"
    );
    client2.shutdown().expect("shutdown second boot");
}

// ---------------------------------------------------------------------------
// 6. Back-compat: migration_mode absent → single-cycle path unchanged.
// ---------------------------------------------------------------------------

#[test]
fn back_compat_no_migration_mode_uses_single_cycle_path() {
    let seed: [u8; 32] = [0x66; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);
    register_axis(&mut client, "hunger", 10.0, false);

    // Submit schema_evolution WITHOUT migration_mode → the existing single-cycle
    // apply path: evolution_succeeded fires immediately, NO migration events,
    // NOT pending.
    let diff = schema_diff_modify_threshold("hunger", "42.0");
    let sig = sign(&seed, &diff);
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("schema_evolution".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(diff)),
                ("attestation_signature", CbValue::Bytes(sig)),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                // NO migration_mode field.
            ]),
        )
        .expect("submit");
    assert!(
        matches!(resp.payload.get("accepted"), Some(CbValue::Bool(true))),
        "single-cycle schema_evolution should be accepted; reason={:?}",
        resp.payload.get("rejection_reason")
    );
    // migration_mode echoed false; single-cycle apply succeeded immediately.
    assert!(matches!(resp.payload.get("migration_mode"), Some(CbValue::Bool(false))));
    assert!(matches!(
        resp.payload.get("schema_apply_succeeded"),
        Some(CbValue::Bool(true))
    ));
    assert_eq!(count_nodes(&mut client, "evolution_succeeded:"), 1);
    assert_eq!(
        count_nodes(&mut client, "schema_migration_started:"),
        0,
        "single-cycle path must NOT emit any migration events"
    );
    assert!(
        !get_bool(&query_pending(&mut client), "pending"),
        "single-cycle apply leaves no migration in flight"
    );
    client.shutdown().expect("shutdown");
}
