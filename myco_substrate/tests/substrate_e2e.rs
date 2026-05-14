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

/// Helper: spawn the myco-substrate binary and complete handshake.
///
/// We reuse BridgeClient (which speaks the M5 protocol on both stdin and
/// stdout) to simulate the operator runtime. The BridgeClient configuration
/// just points at our compiled myco-substrate binary instead of the Python
/// daemon.
fn spawn_substrate() -> BridgeClient {
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
    })
    .expect("spawn myco-substrate binary")
}

#[test]
fn substrate_handshake_reports_versions() {
    let client = spawn_substrate();
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
    let mut client = spawn_substrate();
    client
        .register_axis("test_axis", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register_axis through substrate");
    client.shutdown().expect("clean shutdown");
}

#[test]
fn substrate_forwards_perturb_to_python() {
    let mut client = spawn_substrate();
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
    let mut client = spawn_substrate();
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
    let mut client = spawn_substrate();
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
    let mut client = spawn_substrate();
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
    let mut client = spawn_substrate();
    let snap = client.snapshot().expect("snapshot");
    assert!(snap.is_empty());
    client.shutdown().expect("shutdown");
}

#[test]
fn substrate_perturb_unknown_axis_returns_error() {
    let mut client = spawn_substrate();
    let result = client.perturb("never_registered", 1.0);
    assert!(result.is_err());
    client.shutdown().expect("shutdown");
}
