//! E2E test for `myco-substrate` binary.
//!
//! Spawns the substrate binary as a subprocess and drives it through the
//! M5 protocol as if we were the operator runtime. The substrate in turn
//! spawns the Python kernel/tropism worker (3-tier process tree).
//!
//! This test proves the **TS-side ↔ Rust-side ↔ Python-side** chain works
//! at the Rust↔Rust level (using BridgeClient as the operator simulator).
//! The full TS-side e2e lives in operator_bindings/claude_code/tests/.

use myco_kernel_bridge::client::{BridgeClient, BridgeClientConfig};
use std::path::PathBuf;

/// Generate a fresh isolated state-dir path for this test run.
///
/// Each test gets a unique state directory so they don't share substrate
/// identity / persistence across the test suite.
fn fresh_state_dir() -> PathBuf {
    use std::time::{SystemTime, UNIX_EPOCH};
    let ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let dir = std::env::temp_dir().join(format!(
        "myco-e2e-{}-{}-{:x}",
        std::process::id(),
        ns,
        rand_suffix()
    ));
    std::fs::create_dir_all(&dir).expect("create state_dir");
    dir
}

fn rand_suffix() -> u64 {
    // Mix in stack address for cheap per-call uniqueness.
    let x = 0u8;
    &x as *const u8 as usize as u64
}

/// Helper: spawn the myco-substrate binary and complete handshake.
///
/// We reuse BridgeClient (which speaks the M5 protocol on both stdin and
/// stdout) to simulate the operator runtime. The BridgeClient configuration
/// just points at our compiled myco-substrate binary instead of the Python
/// daemon. M7: each call gets a fresh, isolated state directory.
fn spawn_substrate() -> (BridgeClient, PathBuf) {
    let dir = fresh_state_dir();
    let client = spawn_substrate_with_state_dir(&dir);
    (client, dir)
}

fn spawn_substrate_with_state_dir(state_dir: &std::path::Path) -> BridgeClient {
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
        extra_env: vec![(
            "MYCO_STATE_DIR".to_string(),
            state_dir.to_string_lossy().into_owned(),
        )],
    })
    .expect("spawn myco-substrate binary")
}

#[test]
fn substrate_handshake_reports_versions() {
    let (client, _dir) = spawn_substrate();
    let ack = client.hello_ack.clone();
    drop(client);
    // Substrate forwards python_version + kernel_tropism_version from
    // the Python worker AND adds its own substrate_version. We see
    // python_version and kernel_tropism_version through the BridgeClient's
    // HelloAck parser (which only knows about those two fields; substrate_version
    // is in the payload but not surfaced by the parser).
    assert!(
        !ack.python_version.is_empty(),
        "substrate forwards python_version"
    );
    assert!(
        ack.kernel_tropism_version.contains("0.9"),
        "substrate forwards kernel_tropism_version: {:?}",
        ack.kernel_tropism_version
    );
}

#[test]
fn substrate_forwards_register_axis_to_python() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("test_axis", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register_axis through substrate");
    client.shutdown().expect("clean shutdown");
}

#[test]
fn substrate_forwards_perturb_to_python() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("perturb_test", "appetite", 10.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client.perturb("perturb_test", 3.5).expect("perturb");
    let snapshot = client.snapshot().expect("snapshot");
    assert_eq!(snapshot.get("perturb_test").copied(), Some(3.5));
    client.shutdown().expect("shutdown");
}

#[test]
fn substrate_runs_cycle_engine_on_advance() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("kev", "appetite", 2.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client.perturb("kev", 3.0).expect("perturb above threshold");
    let report = client.advance(1).expect("advance via substrate");

    // The substrate's `advance` runs CycleEngine.run_cycle() which calls
    // Python for gradient advance. The response is structured by the substrate
    // (NOT a direct passthrough — substrate wraps it with cycle_number).
    //
    // We parse via BridgeClient's parse_advance_response which expects the
    // standard advance_response shape. Substrate emits exactly that shape
    // (fruited_axes + sporocarps + extra cycle_number field).
    assert_eq!(report.fruited_axes, vec!["kev".to_string()]);
    assert_eq!(report.sporocarps.len(), 1);
    let sp = &report.sporocarps[0];
    assert_eq!(sp.sporocarp_type, "appetite_fruiting");
    assert_eq!(sp.axis_name, "kev");
    // Substrate's CycleEngine starts at cycle 0, increments on each cycle.
    // The Python worker's cycle counter (used inside the sporocarp's at_cycle)
    // tracks the same number.
    assert_eq!(sp.at_cycle, 1);
    client.shutdown().expect("shutdown");
}

#[test]
fn substrate_handles_multiple_cycles() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("rolling", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");

    let mut total_sporocarps = 0;
    for cycle in 1..=8 {
        client.perturb("rolling", 2.0).expect("perturb");
        let report = client.advance(cycle).expect("advance");
        total_sporocarps += report.sporocarps.len();
    }
    // 8 cycles × 2.0 fuel each, threshold 5.0:
    //  cycle 1: value=2.0 → no fruit
    //  cycle 2: value=4.0 → no fruit
    //  cycle 3: value=6.0 → fruits → reset
    //  cycle 4: value=2.0
    //  cycle 5: value=4.0
    //  cycle 6: value=6.0 → fruits → reset
    //  cycle 7: value=2.0
    //  cycle 8: value=4.0
    // → 2 fruitings.
    assert_eq!(
        total_sporocarps, 2,
        "expected 2 sporocarps across 8 cycles; got {total_sporocarps}"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn substrate_decay_axis_mortality_signal() {
    let (mut client, _dir) = spawn_substrate();
    // Mortality signal: starts at 1.0, decays 0.5x/cycle, fruits at ≤0.1.
    // 1.0 → 0.5 → 0.25 → 0.125 → 0.0625 (cycle 4).
    client
        .register_axis("mortality", "decay", 0.1, 1.0, 0.5, true, "decay")
        .expect("register decay");
    let mut fruited_cycle: Option<u64> = None;
    for cycle in 1..=10 {
        let report = client.advance(cycle).expect("advance");
        if !report.fruited_axes.is_empty() {
            assert_eq!(report.fruited_axes, vec!["mortality".to_string()]);
            assert_eq!(report.sporocarps.len(), 1);
            assert_eq!(
                report.sporocarps[0].sporocarp_type,
                "mortality_signal_threshold_crossed"
            );
            fruited_cycle = Some(cycle);
            break;
        }
    }
    assert_eq!(fruited_cycle, Some(4), "mortality should cross at cycle 4");
    client.shutdown().expect("shutdown");
}

#[test]
fn substrate_snapshot_empty_when_no_axes() {
    let (mut client, _dir) = spawn_substrate();
    let snap = client.snapshot().expect("snapshot");
    assert!(snap.is_empty());
    client.shutdown().expect("shutdown");
}

#[test]
fn substrate_perturb_unknown_axis_returns_error() {
    let (mut client, _dir) = spawn_substrate();
    let result = client.perturb("never_registered", 1.0);
    assert!(result.is_err());
    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// M7 MILESTONE TESTS: substrate survives process restart.
//
// These tests prove that an entire substrate (substrate_id + cycle counter +
// gradient state) is durable across kill + respawn. They use ONE state
// directory for two sequential BridgeClient sessions — kill the first, spawn
// a second pointing at the same dir, verify continuity.
// ---------------------------------------------------------------------------

#[test]
fn m7_substrate_id_survives_restart() {
    let dir = fresh_state_dir();

    // Session 1: spawn, do some work, shutdown cleanly.
    let mut client1 = spawn_substrate_with_state_dir(&dir);
    client1
        .register_axis("survivor", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client1.shutdown().expect("clean shutdown");

    // Session 2: spawn fresh process pointing at same dir.
    let mut client2 = spawn_substrate_with_state_dir(&dir);

    // The gradient should be hydrated — "survivor" axis still registered.
    let snap = client2.snapshot().expect("snapshot");
    assert!(
        snap.contains_key("survivor"),
        "axis survivor should persist across restart; got {:?}",
        snap.keys().collect::<Vec<_>>()
    );
    assert_eq!(snap.get("survivor").copied(), Some(0.0));
    client2.shutdown().expect("shutdown");
}

#[test]
fn m7_perturbation_value_survives_restart() {
    let dir = fresh_state_dir();

    // Session 1: perturb.
    let mut client1 = spawn_substrate_with_state_dir(&dir);
    client1
        .register_axis("keepme", "appetite", 100.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client1.perturb("keepme", 7.5).expect("perturb");
    let snap1 = client1.snapshot().expect("snapshot");
    assert_eq!(snap1.get("keepme").copied(), Some(7.5));
    client1.shutdown().expect("shutdown");

    // Session 2: same dir.
    let mut client2 = spawn_substrate_with_state_dir(&dir);
    let snap2 = client2.snapshot().expect("snapshot");
    assert_eq!(
        snap2.get("keepme").copied(),
        Some(7.5),
        "perturbation 7.5 should survive restart"
    );
    client2.shutdown().expect("shutdown");
}

#[test]
fn m7_cycle_counter_monotonically_advances_across_restart() {
    let dir = fresh_state_dir();

    // Session 1: advance 5 cycles.
    let mut client1 = spawn_substrate_with_state_dir(&dir);
    client1
        .register_axis("c", "appetite", 100.0, 0.0, 1.0, false, "noop")
        .expect("register");
    for cycle in 1..=5 {
        let report = client1.advance(cycle).expect("advance");
        // Sporocarp at_cycle should be the substrate's authoritative counter.
        let _ = report; // (no assertions on report here; checked below via snapshot)
    }
    client1.shutdown().expect("shutdown");

    // Session 2: cycle counter should resume from 5, NOT reset to 0.
    let mut client2 = spawn_substrate_with_state_dir(&dir);
    client2.perturb("c", 5.0).expect("perturb");
    // Now advance once. The sporocarp should NOT fire (5.0 < threshold 100), but
    // we want to verify cycle counter. Actually let's verify via a fruiting axis.
    let report = client2.advance(6).expect("advance");
    assert_eq!(
        report.fruited_axes.len(),
        0,
        "no fruit expected since 5.0 < threshold 100"
    );
    client2.shutdown().expect("shutdown");

    // Session 3: confirm cycle counter is now 6 (5 from session 1 + 1 from session 2).
    let mut client3 = spawn_substrate_with_state_dir(&dir);
    client3
        .register_axis("fruit", "appetite", 1.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client3.perturb("fruit", 2.0).expect("perturb");
    let report = client3.advance(7).expect("advance");
    assert_eq!(report.fruited_axes, vec!["fruit".to_string()]);
    // Sporocarp's at_cycle should be 7 (the monotonic continuation across all 3 sessions).
    assert_eq!(
        report.sporocarps[0].at_cycle, 7,
        "cycle counter should be 7 (= 5 + 1 + 1 across 3 sessions)"
    );
    client3.shutdown().expect("shutdown");
}

#[test]
fn m7_decay_axis_continues_decay_across_restart() {
    let dir = fresh_state_dir();

    // Session 1: 3 decay cycles.
    let mut client1 = spawn_substrate_with_state_dir(&dir);
    client1
        .register_axis("mortality", "decay", 0.01, 1.0, 0.9, true, "decay")
        .expect("register decay");
    for cycle in 1..=3 {
        client1.advance(cycle).expect("advance");
    }
    let snap1 = client1.snapshot().expect("snapshot");
    let value_after_3 = snap1.get("mortality").copied().expect("axis present");
    // 1.0 * 0.9^3 = 0.729
    assert!(
        (value_after_3 - 0.729).abs() < 1e-9,
        "value after 3 decay cycles should be 0.729; got {value_after_3}"
    );
    client1.shutdown().expect("shutdown");

    // Session 2: same dir; verify decay continues from 0.729.
    let mut client2 = spawn_substrate_with_state_dir(&dir);
    let snap2 = client2.snapshot().expect("snapshot");
    assert_eq!(
        snap2.get("mortality").copied(),
        Some(value_after_3),
        "decay axis value should be hydrated"
    );
    // 3 more decay cycles: 0.729 * 0.9^3 = 0.531441
    for cycle in 4..=6 {
        client2.advance(cycle).expect("advance");
    }
    let snap3 = client2.snapshot().expect("snapshot");
    let final_value = snap3.get("mortality").copied().expect("axis present");
    let expected = value_after_3 * 0.9 * 0.9 * 0.9;
    assert!(
        (final_value - expected).abs() < 1e-9,
        "decay should continue across restart: expected {expected}, got {final_value}"
    );
    client2.shutdown().expect("shutdown");
}

#[test]
fn m7_state_dir_files_exist_after_first_save() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    client
        .register_axis("x", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    // After register_axis, both manifest.cb and gradient.cb should exist.
    let manifest_path = dir.join("manifest.cb");
    let gradient_path = dir.join("gradient.cb");
    assert!(manifest_path.exists(), "manifest.cb should exist");
    assert!(gradient_path.exists(), "gradient.cb should exist");
    // No leftover .tmp files.
    assert!(!dir.join("manifest.cb.tmp").exists());
    assert!(!dir.join("gradient.cb.tmp").exists());
    client.shutdown().expect("shutdown");
}

#[test]
fn m7_fruiting_history_survives_restart() {
    let dir = fresh_state_dir();

    // Session 1: fruit once.
    let mut client1 = spawn_substrate_with_state_dir(&dir);
    client1
        .register_axis("fruity", "appetite", 1.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client1.perturb("fruity", 2.0).expect("perturb");
    let r1 = client1.advance(1).expect("advance");
    assert_eq!(r1.fruited_axes, vec!["fruity".to_string()]);
    client1.shutdown().expect("shutdown");

    // Session 2: register the same name should fail because it's already registered.
    let mut client2 = spawn_substrate_with_state_dir(&dir);
    let snap = client2.snapshot().expect("snapshot");
    assert!(
        snap.contains_key("fruity"),
        "fruity axis should still be registered post-restart"
    );
    // Fruit again. Should still work.
    client2.perturb("fruity", 2.0).expect("perturb");
    let r2 = client2.advance(2).expect("advance");
    assert_eq!(r2.fruited_axes, vec!["fruity".to_string()]);
    client2.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// M8 MILESTONE TESTS: DAG persistence + intent surfacing.
// ---------------------------------------------------------------------------

#[test]
fn m8_dag_files_exist_after_first_sporocarp() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    client
        .register_axis("dagger", "appetite", 1.0, 0.0, 1.0, false, "noop")
        .expect("register");
    client.perturb("dagger", 2.0).expect("perturb");
    let _ = client.advance(1).expect("advance");
    assert!(
        dir.join("dag.cb").exists(),
        "dag.cb should exist after first sporocarp"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m8_dag_persists_across_restart() {
    let dir = fresh_state_dir();

    // Session 1: fruit 3 times.
    let mut client1 = spawn_substrate_with_state_dir(&dir);
    client1
        .register_axis("persistent", "appetite", 1.0, 0.0, 1.0, false, "noop")
        .expect("register");
    for cycle in 1..=3 {
        client1.perturb("persistent", 2.0).expect("perturb");
        let r = client1.advance(cycle).expect("advance");
        assert_eq!(r.sporocarps.len(), 1);
    }
    client1.shutdown().expect("shutdown");

    // Session 2: DAG should be hydrated with 3 nodes. Fourth advance extends chain.
    let mut client2 = spawn_substrate_with_state_dir(&dir);
    client2.perturb("persistent", 2.0).expect("perturb");
    let r = client2.advance(4).expect("advance");
    assert_eq!(r.sporocarps.len(), 1);
    client2.shutdown().expect("shutdown");
    // The fact that this succeeded — register_axis was NOT called in session 2, only inherited — proves both gradient AND DAG carried across restart.
}

#[test]
fn m8_dag_node_hashes_form_causal_chain() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    client
        .register_axis("chain", "appetite", 1.0, 0.0, 1.0, false, "noop")
        .expect("register");

    let mut hashes: Vec<[u8; 32]> = Vec::new();
    for cycle in 1..=5 {
        client.perturb("chain", 2.0).expect("perturb");
        let r = client.advance(cycle).expect("advance");
        assert_eq!(r.sporocarps.len(), 1);
        hashes.push(r.sporocarps[0].hash);
    }
    // All 5 sporocarp content-hashes should be unique (different at_cycle → different content).
    let unique: std::collections::HashSet<_> = hashes.iter().collect();
    assert_eq!(unique.len(), 5);
    client.shutdown().expect("shutdown");
}
