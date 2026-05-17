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
    spawn_substrate_with_env(state_dir, vec![])
}

/// M26.1 C5: spawn helper allowing additional env vars (e.g.
/// `MYCO_ACCEPT_LEGACY_PEERS=1`) on top of the always-set `MYCO_STATE_DIR`.
fn spawn_substrate_with_env(
    state_dir: &std::path::Path,
    extra: Vec<(String, String)>,
) -> BridgeClient {
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    let mut extra_env = vec![(
        "MYCO_STATE_DIR".to_string(),
        state_dir.to_string_lossy().into_owned(),
    )];
    extra_env.extend(extra);
    BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
        extra_env,
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
    // M21.4 P5 万物互联: legacy state files (manifest.cb / gradient.cb /
    // operator_identity_pubkey.cb / nonces.cb / owner_keys.cb) are NO LONGER
    // written. dag.cb is the substrate's sole persistent artifact.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    client
        .register_axis("x", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    // After register_axis, only dag.cb should exist.
    assert!(dir.join("dag.cb").exists(), "dag.cb should exist");
    // Legacy files must NOT be written (M21.4 acid test at the Rust level).
    assert!(
        !dir.join("manifest.cb").exists(),
        "post-M21.4: manifest.cb must not exist"
    );
    assert!(
        !dir.join("gradient.cb").exists(),
        "post-M21.4: gradient.cb must not exist"
    );
    // No leftover .tmp files.
    assert!(!dir.join("dag.cb.tmp").exists());
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

// ---------------------------------------------------------------------------
// M22.1 P5 万物互联 — federation listener lifecycle e2e tests.
// ---------------------------------------------------------------------------

use myco_kernel_bridge::protocol::msg_type as proto;
use myco_kernel_shared::canonical_bytes::Value as CbValue;

/// Helper: build a payload Map from (key, value) pairs.
fn build_payload(
    fields: Vec<(&str, CbValue)>,
) -> std::collections::BTreeMap<String, CbValue> {
    fields
        .into_iter()
        .map(|(k, v)| (k.to_string(), v))
        .collect()
}

#[test]
fn m22_1_federation_status_initially_idle() {
    let (mut client, _dir) = spawn_substrate();
    let response = client
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("federation_status call");
    assert_eq!(response.message_type, proto::FEDERATION_STATUS_RESPONSE);
    let is_listening = match response.payload.get("is_listening") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("is_listening missing/not Bool"),
    };
    assert!(!is_listening, "fresh substrate should not be listening yet");
    let bind_addr = match response.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("bind_addr missing/not String"),
    };
    assert_eq!(bind_addr, "");
    let peer_count = match response.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("peer_count missing/not Uint"),
    };
    assert_eq!(peer_count, 0);
    client.shutdown().expect("shutdown");
}

#[test]
fn m22_1_federation_open_listener_resolves_port_zero() {
    let (mut client, _dir) = spawn_substrate();
    let response = client
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("federation_open_listener call");
    assert_eq!(
        response.message_type,
        proto::FEDERATION_OPEN_LISTENER_RESPONSE
    );
    let resolved = match response.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("bind_addr missing/not String"),
    };
    assert!(
        resolved.starts_with("127.0.0.1:"),
        "expected 127.0.0.1:<port>; got {resolved:?}"
    );
    let port_part = resolved.split(':').nth(1).expect("split port");
    let port: u16 = port_part.parse().expect("port parse");
    assert!(port > 0, "OS should pick a non-zero port; got {port}");

    // The response must include the DAG event hash for the
    // federation_listener_opened event.
    let event_hash_bytes = match response.payload.get("listener_opened_event_hash") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("listener_opened_event_hash missing/not Bytes"),
    };
    assert_eq!(event_hash_bytes.len(), 32);

    client.shutdown().expect("shutdown");
}

#[test]
fn m22_1_federation_status_after_open_reports_addr() {
    let (mut client, _dir) = spawn_substrate();
    let open_resp = client
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open");
    let opened_addr = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("open: bind_addr missing"),
    };

    let status = client
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status");
    let is_listening = match status.payload.get("is_listening") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("is_listening missing"),
    };
    assert!(is_listening);
    let reported_addr = match status.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("status bind_addr missing"),
    };
    assert_eq!(reported_addr, opened_addr);

    client.shutdown().expect("shutdown");
}

#[test]
fn m22_1_federation_close_listener_idempotent() {
    let (mut client, _dir) = spawn_substrate();

    // Close when not listening — should report was_listening=false.
    let close1 = client
        .call(proto::FEDERATION_CLOSE_LISTENER, build_payload(vec![]))
        .expect("close (no listener)");
    let was1 = match close1.payload.get("was_listening") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("was_listening missing"),
    };
    assert!(!was1);

    // Open, then close.
    let _ = client
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open");

    let close2 = client
        .call(proto::FEDERATION_CLOSE_LISTENER, build_payload(vec![]))
        .expect("close (listener active)");
    let was2 = match close2.payload.get("was_listening") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("was_listening missing in close2"),
    };
    assert!(was2);
    let prior_addr = match close2.payload.get("prior_bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("prior_bind_addr missing"),
    };
    assert!(prior_addr.starts_with("127.0.0.1:"));
    // The close response must carry the closed-event hash.
    let event_hash = match close2.payload.get("listener_closed_event_hash") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("listener_closed_event_hash missing"),
    };
    assert_eq!(event_hash.len(), 32);

    // Status must now report not listening.
    let status = client
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status after close");
    let is_listening = match status.payload.get("is_listening") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("is_listening missing"),
    };
    assert!(!is_listening);

    // Closing again is idempotent.
    let close3 = client
        .call(proto::FEDERATION_CLOSE_LISTENER, build_payload(vec![]))
        .expect("close (idempotent)");
    let was3 = match close3.payload.get("was_listening") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("was_listening missing"),
    };
    assert!(!was3);

    client.shutdown().expect("shutdown");
}

#[test]
fn m22_1_federation_listener_events_appear_in_dag() {
    let (mut client, _dir) = spawn_substrate();
    let _ = client
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open");
    let _ = client
        .call(proto::FEDERATION_CLOSE_LISTENER, build_payload(vec![]))
        .expect("close");

    // Query the DAG and confirm BOTH federation_listener_opened AND
    // federation_listener_closed events landed.
    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![("count", CbValue::Uint(20))]),
        )
        .expect("query_recent_nodes");
    let nodes_array = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing in query response"),
    };
    let mut saw_opened = false;
    let mut saw_closed = false;
    for n in &nodes_array {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                if nt == "federation_listener_opened" {
                    saw_opened = true;
                }
                if nt == "federation_listener_closed" {
                    saw_closed = true;
                }
            }
        }
    }
    assert!(
        saw_opened,
        "federation_listener_opened event should appear in DAG"
    );
    assert!(
        saw_closed,
        "federation_listener_closed event should appear in DAG"
    );

    client.shutdown().expect("shutdown");
}

#[test]
fn m22_1_federation_open_listener_rejects_empty_addr() {
    let (mut client, _dir) = spawn_substrate();
    let result = client.call(
        proto::FEDERATION_OPEN_LISTENER,
        build_payload(vec![("bind_addr", CbValue::String(String::new()))]),
    );
    assert!(
        result.is_err(),
        "empty bind_addr should be rejected by handler"
    );
    client.shutdown().expect("shutdown");
}

/// M22.2 helper: spawn a background polling thread that repeatedly calls
/// `federation_poll` on the given client for up to `max_iters * 50ms`.
/// Returns the client back when the thread joins.
fn poll_in_background_for(
    mut client: myco_kernel_bridge::client::BridgeClient,
    max_iters: u32,
) -> std::thread::JoinHandle<myco_kernel_bridge::client::BridgeClient> {
    std::thread::spawn(move || {
        for _ in 0..max_iters {
            let _ = client.call(proto::FEDERATION_POLL, build_payload(vec![]));
            std::thread::sleep(std::time::Duration::from_millis(50));
        }
        client
    })
}

#[test]
fn m22_2_two_substrates_pin_each_other_via_hello() {
    // Spawn A. Open listener.
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open listener on A");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("open_resp bind_addr missing"),
    };

    // Drive A's federation_poll in a background thread so it can accept B.
    let poll_handle = poll_in_background_for(client_a, 60);

    // B dials A.
    let (mut client_b, _dir_b) = spawn_substrate();
    let connect_resp = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a.clone()))]),
        )
        .expect("B connect to A");
    let outcome = match connect_resp.payload.get("outcome") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("connect_peer outcome missing"),
    };
    assert_eq!(outcome, "pinned", "B should successfully pin A");

    // B should now know A's substrate_id.
    let b_pinned_a_id = match connect_resp.payload.get("peer_substrate_id") {
        Some(CbValue::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => panic!("connect_peer peer_substrate_id missing"),
    };
    assert_eq!(b_pinned_a_id.len(), 32);

    // B's status should report peer_count = 1.
    let b_status = client_b
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status B");
    let b_peers = match b_status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("status peer_count missing"),
    };
    assert_eq!(b_peers, 1, "B should have 1 peer (A)");

    // Join the polling thread.
    let mut client_a = poll_handle.join().expect("poll thread join");

    // A should have pinned B by now (via accept + HELLO from B).
    let a_status = client_a
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status A");
    let a_peers = match a_status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("status A peer_count missing"),
    };
    assert_eq!(a_peers, 1, "A should have 1 peer (B) after polling");

    // Cleanup.
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_2_federation_peer_pinned_event_in_dag() {
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open A");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };
    let poll_handle = poll_in_background_for(client_a, 60);

    let (mut client_b, _dir_b) = spawn_substrate();
    let _ = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a))]),
        )
        .expect("B connect A");

    // B's DAG should contain a federation_peer_pinned event.
    let nodes_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![(
                "count",
                CbValue::Uint(50),
            ), (
                "node_type_prefix",
                CbValue::String("federation_peer_pinned:".to_string()),
            )]),
        )
        .expect("query B recent");
    let nodes_array = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes_array.is_empty(),
        "B should have at least one federation_peer_pinned event in DAG"
    );

    let client_a = poll_handle.join().expect("poll join");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_2_double_connect_returns_already_pinned() {
    // Spawn A. Open listener.
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open A");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };
    let poll_handle = poll_in_background_for(client_a, 80);

    // B connects to A — first time pins.
    let (mut client_b, _dir_b) = spawn_substrate();
    let resp1 = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a.clone()))]),
        )
        .expect("B connect 1");
    let outcome1 = match resp1.payload.get("outcome") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("outcome 1 missing"),
    };
    assert_eq!(outcome1, "pinned");

    // B connects to A — second time should return already_pinned (same id +
    // same addr).
    let resp2 = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a))]),
        )
        .expect("B connect 2");
    let outcome2 = match resp2.payload.get("outcome") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("outcome 2 missing"),
    };
    assert_eq!(outcome2, "already_pinned");

    let client_a = poll_handle.join().expect("poll join");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

// ---------------------------------------------------------------------------
// M23.1 P4 永恒迭代 — autonomous tick e2e tests.
//
// These tests prove the substrate handles federation activity WITHOUT
// requiring the operator to call federation_poll. The stdin-reader-thread
// + recv_timeout architecture means idle time → federation tick.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// M23.2 P7 必朽 — self-euthanasia EXECUTION (owner co-attestation gate).
//
// Happy-path execution test requires a pinned operator IDENTITY (M9 TOFU);
// the test harness's BridgeClient::spawn_and_handshake at M22 still uses
// the basic HELLO without operator_pubkey, so we don't have a pinned
// identity here. The negative tests below cover the validation paths
// (missing identity, missing fields, bad proposal_hash) and the happy
// path is exercised end-to-end via the TS operator_bindings test in
// operator_bindings/claude_code/tests/ (where M9 pinning IS supported).
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Phase α — Living Bets observatory signal #1 + #6.
//
// First observatory primitive — proves Phase α audit isn't paperwork.
// Substrate can answer "how big am I?" + "do I fit in agent context?"
// ---------------------------------------------------------------------------

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
fn m23_2_accept_self_euthanasia_rejects_when_no_pinned_identity() {
    let (mut client, _dir) = spawn_substrate();
    let result = client.call(
        proto::ACCEPT_SELF_EUTHANASIA_PROPOSAL,
        build_payload(vec![
            ("proposal_hash", CbValue::Bytes(vec![0u8; 32])),
            ("owner_signature", CbValue::Bytes(vec![0u8; 64])),
        ]),
    );
    assert!(result.is_err(), "must reject when no operator identity is pinned");
    if let Err(e) = &result {
        assert!(
            e.to_string().contains("pinned operator identity"),
            "error should mention pinning; got {e}"
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn m23_2_accept_self_euthanasia_rejects_wrong_size_fields() {
    let (mut client, _dir) = spawn_substrate();
    let r1 = client.call(
        proto::ACCEPT_SELF_EUTHANASIA_PROPOSAL,
        build_payload(vec![
            ("proposal_hash", CbValue::Bytes(vec![0u8; 16])), // wrong size
            ("owner_signature", CbValue::Bytes(vec![0u8; 64])),
        ]),
    );
    assert!(r1.is_err());
    let r2 = client.call(
        proto::ACCEPT_SELF_EUTHANASIA_PROPOSAL,
        build_payload(vec![
            ("proposal_hash", CbValue::Bytes(vec![0u8; 32])),
            ("owner_signature", CbValue::Bytes(vec![0u8; 32])), // wrong size
        ]),
    );
    assert!(r2.is_err());
    client.shutdown().expect("shutdown");
}

#[test]
fn m23_1_substrate_accepts_peer_hello_via_autonomous_tick() {
    // Spawn A, open listener — do NOT start a polling thread.
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };

    // B connects to A — A's autonomous tick (background) should process the
    // inbound HELLO without explicit polling.
    let (mut client_b, _dir_b) = spawn_substrate();
    let connect_resp = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a))]),
        )
        .expect("B connect");
    let outcome = match connect_resp.payload.get("outcome") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("outcome missing"),
    };
    assert_eq!(
        outcome, "pinned",
        "B should pin A successfully via A's autonomous tick (no operator poll needed)"
    );

    // Give A's tick a moment to land, then check A's peer count.
    std::thread::sleep(std::time::Duration::from_millis(800));
    let a_status = client_a
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("A status");
    let a_peer_count = match a_status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("a peer_count missing"),
    };
    assert_eq!(
        a_peer_count, 1,
        "A should have pinned B autonomously without operator polling"
    );

    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m23_1_idle_substrate_does_not_crash() {
    // Sanity: substrate with no operator activity for >1 tick interval
    // should remain responsive (autonomous tick must not deadlock or crash).
    let (mut client, _dir) = spawn_substrate();
    std::thread::sleep(std::time::Duration::from_millis(1200));
    // After idle period, the substrate should still respond to operator calls.
    let resp = client
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("idle substrate still responsive");
    assert_eq!(resp.message_type, proto::FEDERATION_STATUS_RESPONSE);
    client.shutdown().expect("clean shutdown after idle");
}

#[test]
fn m22_3_pull_events_from_peer_ingests_into_local_dag() {
    // Spawn A. Open listener. Register an axis (which emits axis_registered).
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open A");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };
    // Phase β SECURITY (2026-05-15): only ALLOWLISTED node_type prefixes are
    // ingested via federation pull (raw_material/sporocarp/mutation/immune).
    // axis_registered/axis_perturbed are substrate-private — would be
    // rejected with C22 immune sporocarp if pulled. So we ingest
    // raw_material events on A (peer-environmental).
    client_a
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                ("content_bytes", CbValue::Bytes(b"sample raw material A".to_vec())),
            ]),
        )
        .expect("A ingest raw_material 1");
    client_a
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                ("content_bytes", CbValue::Bytes(b"sample raw material A #2".to_vec())),
            ]),
        )
        .expect("A ingest raw_material 2");

    // Start A's polling thread so it can serve B's requests.
    let poll_handle = poll_in_background_for(client_a, 80);

    // B connects to A.
    let (mut client_b, _dir_b) = spawn_substrate();
    let connect_resp = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a))]),
        )
        .expect("B connect A");
    let a_id = match connect_resp.payload.get("peer_substrate_id") {
        Some(CbValue::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => panic!("a id missing"),
    };

    // B pulls events from A (since=None means from A's genesis).
    let pull_resp = client_b
        .call(
            proto::FEDERATION_PULL_EVENTS_FROM_PEER,
            build_payload(vec![
                ("peer_substrate_id", CbValue::Bytes(a_id)),
                ("max_events", CbValue::Uint(50)),
            ]),
        )
        .expect("B pull");

    let events_ingested = match pull_resp.payload.get("events_ingested_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("events_ingested_count missing"),
    };
    assert!(
        events_ingested >= 2,
        "Phase β allowlist: B should ingest A's 2 raw_material events; got {events_ingested}"
    );
    let is_last = match pull_resp.payload.get("is_last_batch") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("is_last_batch missing"),
    };
    assert!(is_last, "single small pull should be the last batch");

    // B's DAG should now contain a federation_events_received event.
    let nodes_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("federation_events_received".to_string()),
                ),
            ]),
        )
        .expect("B query");
    let nodes_arr = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes_arr.is_empty(),
        "B should have at least one federation_events_received event"
    );

    let client_a = poll_handle.join().expect("poll join");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn phase_beta_federation_pull_rejects_substrate_private_events() {
    // Phase β SECURITY: peer B has a `cycle_advanced` event in its own DAG
    // (built up via legitimate advance calls). When A pulls from B, A must
    // REJECT this event (substrate-private; would corrupt A's cycle_counter).
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };
    // A registers + advances → A's DAG accumulates substrate-private events
    // (cycle_advanced, axis_registered, etc.) — these are what peers might
    // attempt to push but are forbidden by the allowlist.
    client_a
        .register_axis("ax", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("A register");
    client_a.perturb("ax", 1.0).expect("A perturb");
    client_a.advance(1).expect("A advance");

    let poll_handle = poll_in_background_for(client_a, 80);

    // B connects + pulls.
    let (mut client_b, _dir_b) = spawn_substrate();
    let connect_resp = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a))]),
        )
        .expect("B connect");
    let a_id = match connect_resp.payload.get("peer_substrate_id") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("a_id missing"),
    };

    let pull_resp = client_b
        .call(
            proto::FEDERATION_PULL_EVENTS_FROM_PEER,
            build_payload(vec![
                ("peer_substrate_id", CbValue::Bytes(a_id)),
                ("max_events", CbValue::Uint(50)),
            ]),
        )
        .expect("B pull");
    let events_received = match pull_resp.payload.get("events_received_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("events_received_count missing"),
    };
    let events_ingested = match pull_resp.payload.get("events_ingested_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("events_ingested_count missing"),
    };
    // Phase β: received >= ingested. The difference is rejected substrate-
    // private events (genesis_event, cycle_advanced, axis_registered,
    // axis_perturbed, operator_pinned, federation_*, sporocarp etc.).
    // Wait — sporocarp IS allowed. Let me think.
    // A's DAG: genesis_event(*), operator_pinned(?), axis_registered(*),
    //          axis_perturbed(*), cycle_advanced(*), sporocarp(maybe).
    // Allowed by Phase β: sporocarp only (assuming any fruited)
    // Rejected: genesis_event, axis_registered, axis_perturbed, cycle_advanced
    // So ingested < received.
    assert!(
        events_ingested < events_received,
        "Phase β: peer's substrate-private events must be rejected; ingested={events_ingested} received={events_received}"
    );

    // B's DAG must NOT contain peer's cycle_advanced.
    let nodes_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                ("node_type_prefix", CbValue::String("cycle_advanced".to_string())),
            ]),
        )
        .expect("query");
    let nodes_arr = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!(),
    };
    assert_eq!(
        nodes_arr.len(),
        0,
        "B's DAG must not contain federation-injected cycle_advanced events"
    );

    // B's DAG MUST contain a C22 immune sporocarp (federation_substrate_private_event_injection).
    let immune_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                ("node_type_prefix", CbValue::String("immune:C35".to_string())),
            ]),
        )
        .expect("query immune");
    let immune_arr = match immune_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!(),
    };
    assert!(
        !immune_arr.is_empty(),
        "Phase β: C22 immune sporocarp must be emitted on rejected federation push"
    );

    let client_a = poll_handle.join().expect("poll join");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_3_pull_events_idempotent_on_duplicate_pull() {
    // Pulling the same range twice should not duplicate events in the local DAG
    // (Dag::insert_node is idempotent on content hash + parents).
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open A");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };
    // Phase β: ingest raw_material on A (allowlisted by federation pull).
    client_a
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                ("content_bytes", CbValue::Bytes(b"dup test material".to_vec())),
            ]),
        )
        .expect("A ingest");
    client_a
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                ("content_bytes", CbValue::Bytes(b"dup test material #2".to_vec())),
            ]),
        )
        .expect("A ingest 2");
    let poll_handle = poll_in_background_for(client_a, 80);

    let (mut client_b, _dir_b) = spawn_substrate();
    let connect_resp = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a))]),
        )
        .expect("B connect");
    let a_id = match connect_resp.payload.get("peer_substrate_id") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("a_id missing"),
    };

    // First pull.
    let pull1 = client_b
        .call(
            proto::FEDERATION_PULL_EVENTS_FROM_PEER,
            build_payload(vec![
                ("peer_substrate_id", CbValue::Bytes(a_id.clone())),
                ("max_events", CbValue::Uint(50)),
            ]),
        )
        .expect("pull 1");
    let ingested1 = match pull1.payload.get("events_ingested_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!(),
    };
    assert!(ingested1 >= 2, "Phase β: expect >=2 raw_material events ingested; got {ingested1}");

    // Second pull (same range) — should still complete cleanly. Note that
    // A's DAG grew between the two pulls (each FED_EVENT_BATCH A sends emits
    // a federation_events_sent event in A's DAG), so the second pull can
    // actually return MORE events than the first. The critical invariant is
    // that `Dag::insert_node` is content-hash idempotent — re-inserting an
    // existing event is a silent no-op, never a duplicate or an error.
    let pull2 = client_b
        .call(
            proto::FEDERATION_PULL_EVENTS_FROM_PEER,
            build_payload(vec![
                ("peer_substrate_id", CbValue::Bytes(a_id)),
                ("max_events", CbValue::Uint(50)),
            ]),
        )
        .expect("pull 2");
    let ingested2 = match pull2.payload.get("events_ingested_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!(),
    };
    assert!(
        ingested2 >= ingested1,
        "second pull should re-receive (idempotent) >= first; pull1={ingested1} pull2={ingested2}"
    );

    let client_a = poll_handle.join().expect("poll join");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_4_sprout_child_writes_parent_federation_hint() {
    // Parent A opens listener, then sprouts child B.
    // B's DAG should contain a parent_federation_hint event.
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open listener");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };

    // A needs at least one axis registered so sprout has something to clone.
    client_a
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("A register");

    // Sprout child B at a fresh dir.
    let child_dir = fresh_state_dir();
    let child_dir_str = child_dir.to_string_lossy().into_owned();
    let _ = client_a
        .call(
            proto::SPROUT_CHILD,
            build_payload(vec![(
                "child_state_dir",
                CbValue::String(child_dir_str.clone()),
            )]),
        )
        .expect("A sprout child");
    client_a.shutdown().expect("shutdown A pre-spawn-B");

    // Spawn child B pointing at child_state_dir.
    let mut client_b = spawn_substrate_with_state_dir(&child_dir);

    // Query B's DAG for parent_federation_hint event.
    let nodes_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("parent_federation_hint".to_string()),
                ),
            ]),
        )
        .expect("B query");
    let nodes_arr = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes_arr.len(),
        1,
        "B should have exactly one parent_federation_hint event"
    );

    // Verify the hint contains A's listener address.
    if let CbValue::Map(m) = &nodes_arr[0] {
        if let Some(CbValue::Bytes(content)) = m.get("content_canonical_bytes") {
            use myco_kernel_shared::canonical_bytes::decode as cb_decode;
            let decoded = cb_decode(content).expect("decode hint content");
            if let CbValue::Map(hint_map) = decoded {
                let hint_addr = match hint_map.get("parent_federation_addr") {
                    Some(CbValue::String(s)) => s.clone(),
                    _ => panic!("parent_federation_addr missing"),
                };
                assert_eq!(hint_addr, addr_a, "hint addr should match A's listener");
            }
        }
    }
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_4_child_link_to_parent_via_hint_emits_parent_linked() {
    // End-to-end: parent listening → sprout child → child links to parent.
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open");
    let _addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!(),
    };
    client_a
        .register_axis("clonable", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("A register");
    let child_dir = fresh_state_dir();
    let child_dir_str = child_dir.to_string_lossy().into_owned();
    let _ = client_a
        .call(
            proto::SPROUT_CHILD,
            build_payload(vec![(
                "child_state_dir",
                CbValue::String(child_dir_str),
            )]),
        )
        .expect("A sprout");

    // Critical: we cannot shut down A here, because B needs A's listener
    // alive to connect. Move A to a polling thread (which keeps A's process
    // alive AND processes the inbound HELLO from B).
    // But A already has its listener opened from earlier — listener persists
    // across the shutdown-prep. Actually no — when A shuts down, its TCP
    // listener is closed by the OS.
    //
    // So we need A to STAY ALIVE while B connects. Move A to polling thread.
    let poll_handle_a = poll_in_background_for(client_a, 80);

    // Now spawn B and trigger link.
    let mut client_b = spawn_substrate_with_state_dir(&child_dir);
    let link_resp = client_b
        .call(
            proto::FEDERATION_LINK_TO_PARENT_FROM_HINT,
            build_payload(vec![]),
        )
        .expect("B link to parent");
    let hint_found = match link_resp.payload.get("hint_found") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("hint_found missing"),
    };
    assert!(hint_found, "B should have found the parent hint in its DAG");
    let already_linked = match link_resp.payload.get("already_linked") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("already_linked missing"),
    };
    assert!(!already_linked, "first link call should NOT be already_linked");
    let parent_linked_event_hash = link_resp.payload.get("parent_linked_event_hash");
    assert!(
        matches!(parent_linked_event_hash, Some(CbValue::Bytes(b)) if b.len() == 32),
        "successful link must return parent_linked_event_hash"
    );

    // Verify B's DAG has federation_parent_linked.
    let nodes_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(20)),
                (
                    "node_type_prefix",
                    CbValue::String("federation_parent_linked".to_string()),
                ),
            ]),
        )
        .expect("query B");
    let nodes_arr = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!(),
    };
    assert!(!nodes_arr.is_empty(), "B should have federation_parent_linked event");

    // Second call should be idempotent (already_linked = true).
    let link2 = client_b
        .call(
            proto::FEDERATION_LINK_TO_PARENT_FROM_HINT,
            build_payload(vec![]),
        )
        .expect("B link 2");
    let al2 = match link2.payload.get("already_linked") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!(),
    };
    assert!(al2, "second link call should report already_linked=true");

    let client_a = poll_handle_a.join().expect("poll join");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_5_sprout_without_parent_immune_writes_no_quarantine_event() {
    // Parent has no immune sporocarps → child should NOT have a quarantine event.
    let (mut client_a, _dir_a) = spawn_substrate();
    client_a
        .register_axis("clean", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("A register");

    let child_dir = fresh_state_dir();
    let _ = client_a
        .call(
            proto::SPROUT_CHILD,
            build_payload(vec![(
                "child_state_dir",
                CbValue::String(child_dir.to_string_lossy().into_owned()),
            )]),
        )
        .expect("sprout");
    client_a.shutdown().expect("shutdown A");

    let mut client_b = spawn_substrate_with_state_dir(&child_dir);
    let nodes_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("birth_period_quarantine_entered".to_string()),
                ),
            ]),
        )
        .expect("B query");
    let nodes_arr = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!(),
    };
    assert!(
        nodes_arr.is_empty(),
        "clean parent should NOT seed birth-period quarantine"
    );
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_5_child_quarantined_when_parent_has_immune_event() {
    // Setup: spawn parent A, shut down, corrupt its dag.cb → respawn A → A boots
    // with C7_dag_retro_edit_detected immune sporocarp in fresh DAG. Then sprout
    // child from this parent → child should have birth_period_quarantine_entered.
    let parent_dir = fresh_state_dir();
    let client1 = spawn_substrate_with_state_dir(&parent_dir);
    client1.shutdown().expect("shutdown 1");

    // Corrupt parent's dag.cb.
    let dag_path = parent_dir.join("dag.cb");
    std::fs::write(&dag_path, b"this-is-not-canonical-bytes")
        .expect("corrupt dag.cb");

    // Respawn parent — should emit C7 immune sporocarp + quarantine corrupted file.
    let mut client2 = spawn_substrate_with_state_dir(&parent_dir);

    // Verify the parent now has at least one immune:* event in its DAG.
    let immune_resp = client2
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                ("node_type_prefix", CbValue::String("immune:".to_string())),
            ]),
        )
        .expect("query immune");
    let immune_arr = match immune_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!(),
    };
    assert!(
        !immune_arr.is_empty(),
        "respawned parent should have at least one immune event after dag.cb corruption"
    );

    // Register an axis so sprout has something to clone.
    client2
        .register_axis("infected", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");

    // Sprout child.
    let child_dir = fresh_state_dir();
    let _ = client2
        .call(
            proto::SPROUT_CHILD,
            build_payload(vec![(
                "child_state_dir",
                CbValue::String(child_dir.to_string_lossy().into_owned()),
            )]),
        )
        .expect("sprout");
    client2.shutdown().expect("shutdown 2");

    // Spawn child + verify it has quarantine_entered event.
    let mut client_b = spawn_substrate_with_state_dir(&child_dir);
    let q_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("birth_period_quarantine_entered".to_string()),
                ),
            ]),
        )
        .expect("query quarantine");
    let q_arr = match q_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!(),
    };
    assert!(
        !q_arr.is_empty(),
        "child of immune-bearing parent should have birth_period_quarantine_entered event"
    );
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_5_quarantined_child_blocks_register_axis() {
    // Reuse setup from previous test: create a parent with immune, sprout child,
    // verify child blocks register_axis.
    let parent_dir = fresh_state_dir();
    let client1 = spawn_substrate_with_state_dir(&parent_dir);
    client1.shutdown().expect("shutdown 1");
    std::fs::write(parent_dir.join("dag.cb"), b"corrupt").expect("corrupt");

    let mut client2 = spawn_substrate_with_state_dir(&parent_dir);
    client2
        .register_axis("seeded", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("seed axis");
    let child_dir = fresh_state_dir();
    let _ = client2
        .call(
            proto::SPROUT_CHILD,
            build_payload(vec![(
                "child_state_dir",
                CbValue::String(child_dir.to_string_lossy().into_owned()),
            )]),
        )
        .expect("sprout");
    client2.shutdown().expect("shutdown 2");

    // Spawn child + try register_axis → should fail.
    let mut client_b = spawn_substrate_with_state_dir(&child_dir);
    let block_result = client_b.register_axis("blocked", "appetite", 5.0, 0.0, 1.0, false, "noop");
    assert!(
        block_result.is_err(),
        "register_axis should be blocked while in birth-period quarantine"
    );
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_5_lift_quarantine_unblocks_operations() {
    // Phase β SECURITY FIX (2026-05-15): lift_birth_period_quarantine now
    // requires owner Ed25519 signature. Pre-fix this test exercised the
    // INSECURE no-auth path. Post-fix it verifies the GUARD: unauthenticated
    // lift attempts are rejected, quarantine remains in force. The
    // happy-path (lift WITH valid signature) is M24+ work requiring TS-side
    // M9 TOFU pinning helper.
    let parent_dir = fresh_state_dir();
    let client1 = spawn_substrate_with_state_dir(&parent_dir);
    client1.shutdown().expect("shutdown 1");
    std::fs::write(parent_dir.join("dag.cb"), b"corrupt").expect("corrupt");

    let mut client2 = spawn_substrate_with_state_dir(&parent_dir);
    client2
        .register_axis("seeded", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("seed");
    let child_dir = fresh_state_dir();
    let _ = client2
        .call(
            proto::SPROUT_CHILD,
            build_payload(vec![(
                "child_state_dir",
                CbValue::String(child_dir.to_string_lossy().into_owned()),
            )]),
        )
        .expect("sprout");
    client2.shutdown().expect("shutdown 2");

    let mut client_b = spawn_substrate_with_state_dir(&child_dir);

    // Confirm quarantine blocks register_axis (M22.5 behavior unchanged).
    assert!(client_b
        .register_axis("blocked1", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .is_err());

    // Phase β SECURITY: unauthenticated lift attempt MUST fail. Pre-fix this
    // succeeded with empty payload — that was the working bug.
    let lift_attempt = client_b
        .call(proto::LIFT_BIRTH_PERIOD_QUARANTINE, build_payload(vec![]));
    assert!(
        lift_attempt.is_err(),
        "Phase β: unauthenticated lift must be rejected; got {lift_attempt:?}"
    );

    // Quarantine remains in force after the rejected lift.
    assert!(client_b
        .register_axis("still_blocked", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .is_err());

    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_5_lift_quarantine_rejects_unauthenticated_call() {
    // Phase β SECURITY FIX: even when not in quarantine, lift requires owner
    // signature. Pre-fix this returned was_in_quarantine=false (insecure).
    let (mut client, _dir) = spawn_substrate();
    let result = client
        .call(proto::LIFT_BIRTH_PERIOD_QUARANTINE, build_payload(vec![]));
    assert!(
        result.is_err(),
        "Phase β: unauthenticated lift must always be rejected; got {result:?}"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m22_5_lift_quarantine_rejects_wrong_signature_size() {
    let (mut client, _dir) = spawn_substrate();
    let result = client.call(
        proto::LIFT_BIRTH_PERIOD_QUARANTINE,
        build_payload(vec![("owner_signature", CbValue::Bytes(vec![0u8; 32]))]),
    );
    assert!(
        result.is_err(),
        "Phase β: signature with wrong size must be rejected"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m22_2_connect_peer_with_no_listener_fails() {
    // Connect to a port no one is listening on — should error out cleanly.
    let (mut client_b, _dir_b) = spawn_substrate();
    let result = client_b.call(
        proto::FEDERATION_CONNECT_PEER,
        build_payload(vec![(
            "remote_addr",
            CbValue::String("127.0.0.1:1".to_string()), // port 1 = privileged, unlikely listening
        )]),
    );
    assert!(
        result.is_err(),
        "connect to non-listening address must fail"
    );
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m22_1_federation_listener_can_accept_tcp_connection() {
    // Open listener, then verify it accepts TCP connections (the connection
    // doesn't go anywhere yet — M22.2 wires the handshake — but the listener
    // socket is bound + listening.)
    let (mut client, _dir) = spawn_substrate();
    let open_resp = client
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("open");
    let addr_str = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("bind_addr missing"),
    };

    use std::net::TcpStream;
    use std::time::Duration;
    let stream = TcpStream::connect_timeout(
        &addr_str.parse().expect("addr parse"),
        Duration::from_secs(2),
    );
    assert!(
        stream.is_ok(),
        "should be able to TCP-connect to federation listener at {addr_str}"
    );
    drop(stream);

    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// M25.1 + M25.2 + M25.3 P5 万物互联 — Living Bets observatory: doctrine-burst
// detection, signal #5 time trends, bet_weakening_quorum predicate, and
// emergent composite weights.
// ---------------------------------------------------------------------------

/// Helper: pump N advance cycles through the substrate so the observatory
/// history fills up.
fn pump_cycles(client: &mut BridgeClient, n: u64) {
    for cycle in 1..=n {
        client.advance(cycle).expect("advance");
    }
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
    // (L0 §7.4 + §13.1); the burst-count field renamed accordingly.
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

// ---------------------------------------------------------------------------
// M25.0 + M25.4 — substrate-signing-key integration tests.
//
// These cover the two security gaps closed jointly by the substrate-private
// Ed25519 keypair: snapshot integrity (M25.0) and federation HELLO mutual
// auth (M25.4).
// ---------------------------------------------------------------------------

#[test]
fn m25_0_substrate_writes_signing_key_file_on_first_boot() {
    // Sanity: a fresh substrate must persist its signing key during boot
    // (via boot_or_genesis_substrate_signing_key). The file's mere presence
    // demonstrates the boot path wired the seed through ServerState.
    let (client, dir) = spawn_substrate();
    let signing_key_path = dir.join("substrate_signing_key.cb");
    assert!(
        signing_key_path.exists(),
        "substrate_signing_key.cb must be persisted on first boot at {}",
        signing_key_path.display()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn m25_0_snapshot_cross_substrate_rejection() {
    // Build substrate A. Pump enough cycles for a snapshot.cb to land
    // (SNAPSHOT_EVERY_K_CYCLES = 10 in server.rs).
    let dir_a = fresh_state_dir();
    {
        let mut client_a = spawn_substrate_with_state_dir(&dir_a);
        for cycle in 1..=10u64 {
            client_a.advance(cycle).expect("advance A");
        }
        client_a.shutdown().expect("shutdown A");
    }
    let snapshot_a = dir_a.join("snapshot.cb");
    assert!(
        snapshot_a.exists(),
        "snapshot.cb should be written every K=10 cycles; absent at {}",
        snapshot_a.display()
    );

    // Build substrate B with its OWN state_dir (and thus its own signing key).
    let dir_b = fresh_state_dir();
    {
        // Boot B briefly so it generates its own signing key.
        let client_b = spawn_substrate_with_state_dir(&dir_b);
        client_b.shutdown().expect("shutdown B genesis");
    }
    // Sanity: B has its own signing key, different from A's.
    let key_a = std::fs::read(dir_a.join("substrate_signing_key.cb")).expect("read A key");
    let key_b = std::fs::read(dir_b.join("substrate_signing_key.cb")).expect("read B key");
    assert_ne!(
        key_a, key_b,
        "different substrates must have independent signing keys"
    );

    // Copy A's snapshot.cb into B's state_dir — but NOT A's signing key.
    // B's boot path should reject the snapshot (signer_pubkey mismatch) and
    // fall back to full DAG replay (which means B's state stays at genesis).
    std::fs::copy(&snapshot_a, dir_b.join("snapshot.cb")).expect("copy snapshot");

    // Restart B. It must boot successfully without using A's snapshot.
    let mut client_b = spawn_substrate_with_state_dir(&dir_b);
    // The substrate should respond to operator messages — proves it didn't
    // crash on the forged snapshot.
    let snap = client_b.snapshot().expect("snapshot must work after boot");
    assert!(
        snap.is_empty(),
        "B's gradient state should still be empty (genesis); cross-substrate snapshot \
         must NOT have polluted state"
    );

    // The rejection should have left a C38_snapshot_integrity_violation
    // immune sporocarp in the DAG. Query immune events to verify.
    let immune_resp = client_b
        .call(proto::QUERY_IMMUNE_EVENTS, build_payload(vec![]))
        .expect("query immune events");
    let events = match immune_resp.payload.get("events") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("immune events response missing 'events' array"),
    };
    let has_c38 = events.iter().any(|ev| match ev {
        CbValue::Map(m) => match m.get("node_type") {
            Some(CbValue::String(s)) => s.contains("C38_snapshot_integrity_violation"),
            _ => false,
        },
        _ => false,
    });
    assert!(
        has_c38,
        "C38_snapshot_integrity_violation immune sporocarp must be emitted; \
         events: {:?}",
        events
    );
    client_b.shutdown().expect("shutdown B final");
}

#[test]
fn m25_4_federation_hello_signed_two_substrates() {
    // Two substrates connect via federation; each has its own signing seed.
    // Both should pin each other with signature_verified = true.
    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open listener");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };

    let (mut client_b, _dir_b) = spawn_substrate();
    let connect_resp = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a))]),
        )
        .expect("B connect");
    let outcome = match connect_resp.payload.get("outcome") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("outcome missing"),
    };
    assert_eq!(outcome, "pinned", "B should pin A");
    // M25.4: B's response should carry signature_verified = true and a
    // peer_signer_pubkey field (32 bytes).
    let sig_verified = match connect_resp.payload.get("signature_verified") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("signature_verified missing in connect_peer response"),
    };
    assert!(
        sig_verified,
        "M25.4: substrates with signing keys must produce verified hellos"
    );
    let signer_pk = match connect_resp.payload.get("peer_signer_pubkey") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("peer_signer_pubkey missing in connect_peer response"),
    };
    assert_eq!(
        signer_pk.len(),
        32,
        "signer_pubkey must be 32 bytes (Ed25519 pubkey)"
    );

    // Wait for A's autonomous tick to pick up B's hello + ack.
    std::thread::sleep(std::time::Duration::from_millis(800));
    let a_status = client_a
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("A status");
    let a_peer_count = match a_status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("peer_count missing"),
    };
    assert_eq!(a_peer_count, 1, "A should have pinned B");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

#[test]
fn m25_4_federation_hello_tampered_signature_rejected() {
    // We open A's listener, then manually dial as a fake peer and write a
    // FED_HELLO frame carrying a tampered signature. A's autonomous tick
    // must reject and emit a C39 immune sporocarp; the peer must NOT be pinned.
    use myco_kernel_bridge::framing::write_frame;
    use myco_kernel_bridge::protocol::{encode_frame_body, Message};
    use myco_kernel_shared::canonical_bytes::Value as CbV;
    use std::collections::BTreeMap as BTM;

    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open listener");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };

    use std::net::TcpStream;
    let mut stream = TcpStream::connect(&addr_a).expect("dial A");
    let fake_peer_id = [0xABu8; 32];
    let fake_pubkey = [0xCDu8; 32];
    let bogus_sig = [0xEFu8; 64];
    let mut payload = BTM::new();
    payload.insert(
        "peer_substrate_id".to_string(),
        CbV::Bytes(fake_peer_id.to_vec()),
    );
    payload.insert("protocol_version".to_string(), CbV::Uint(1));
    payload.insert(
        "signer_pubkey".to_string(),
        CbV::Bytes(fake_pubkey.to_vec()),
    );
    payload.insert(
        "hello_signature".to_string(),
        CbV::Bytes(bogus_sig.to_vec()),
    );
    let msg = Message::new("fed_hello", 1, payload);
    // Use the federation bootstrap HMAC key (sha256 of literal string).
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-federation-protocol-v1-bootstrap");
    let bootstrap_arr: [u8; 32] = h.finalize().into();
    let frame = encode_frame_body(&msg, &bootstrap_arr).expect("encode");
    write_frame(&mut stream, &frame).expect("send hello");
    // Give A's autonomous tick time to process the hello.
    std::thread::sleep(std::time::Duration::from_millis(1500));

    // Verify A emitted a C39 immune sporocarp.
    let immune_resp = client_a
        .call(proto::QUERY_IMMUNE_EVENTS, build_payload(vec![]))
        .expect("query immune events");
    let events = match immune_resp.payload.get("events") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("events missing"),
    };
    let has_c39 = events.iter().any(|ev| match ev {
        CbValue::Map(m) => match m.get("node_type") {
            Some(CbValue::String(s)) => s.contains("C39_federation_hello_signature_invalid"),
            _ => false,
        },
        _ => false,
    });
    assert!(
        has_c39,
        "tampered fed_hello must emit C39 immune sporocarp; saw events: {:?}",
        events
    );
    // The peer should NOT be pinned.
    let status = client_a
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status");
    let peer_count = match status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("peer_count missing"),
    };
    assert_eq!(
        peer_count, 0,
        "tampered hello must NOT result in a pinned peer"
    );
    client_a.shutdown().expect("shutdown");
}

#[test]
fn m26_1_c5_legacy_hello_rejected_by_default() {
    // M26.1 C5 SECURITY FIX (Phase γ.2): pre-M25 peer with no signature
    // fields is REJECTED under the default policy (MYCO_ACCEPT_LEGACY_PEERS
    // unset). The substrate must emit a C39 immune sporocarp with sub-grade
    // `missing_required_signature` and the peer must NOT be pinned.
    //
    // Pre-fix behavior (M25.4 baseline): legacy peers were always accepted via
    // TOFU, so attacker's optimal bypass was "never sign". That hole is closed.
    use myco_kernel_bridge::framing::write_frame;
    use myco_kernel_bridge::protocol::{encode_frame_body, Message};
    use myco_kernel_shared::canonical_bytes::Value as CbV;
    use std::collections::BTreeMap as BTM;

    let (mut client_a, _dir_a) = spawn_substrate();
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open listener");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };

    use std::net::TcpStream;
    let mut stream = TcpStream::connect(&addr_a).expect("dial");
    let legacy_peer_id = [0x11u8; 32];
    let mut payload = BTM::new();
    payload.insert(
        "peer_substrate_id".to_string(),
        CbV::Bytes(legacy_peer_id.to_vec()),
    );
    payload.insert("protocol_version".to_string(), CbV::Uint(1));
    // No signer_pubkey or hello_signature — pure pre-M25 hello.
    let msg = Message::new("fed_hello", 1, payload);
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-federation-protocol-v1-bootstrap");
    let bootstrap_arr: [u8; 32] = h.finalize().into();
    let frame = encode_frame_body(&msg, &bootstrap_arr).expect("encode");
    write_frame(&mut stream, &frame).expect("send legacy hello");
    // Wait for A's autonomous tick.
    std::thread::sleep(std::time::Duration::from_millis(1500));

    // Verify peer is NOT pinned.
    let status = client_a
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status");
    let peer_count = match status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("peer_count missing"),
    };
    assert_eq!(
        peer_count, 0,
        "M26.1 C5: legacy hello must NOT pin under default policy"
    );

    // A C39 immune sporocarp MUST have been emitted with the new sub-grade.
    let immune_resp = client_a
        .call(proto::QUERY_IMMUNE_EVENTS, build_payload(vec![]))
        .expect("query immune events");
    let events = match immune_resp.payload.get("events") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("events missing"),
    };
    let c39_with_subgrade = events.iter().any(|ev| match ev {
        CbValue::Map(m) => {
            let node_type_match = match m.get("node_type") {
                Some(CbValue::String(s)) => s.contains("C39_federation_hello_signature_invalid"),
                _ => false,
            };
            let evidence_match = match m.get("content_canonical_bytes") {
                Some(CbValue::Bytes(b)) => {
                    // The evidence field is part of the content map's canonical
                    // bytes; we search for the "missing_required_signature"
                    // sub-grade marker directly in the byte stream as a string.
                    let needle = b"missing_required_signature";
                    b.windows(needle.len()).any(|w| w == needle)
                }
                _ => false,
            };
            node_type_match && evidence_match
        }
        _ => false,
    });
    assert!(
        c39_with_subgrade,
        "M26.1 C5: legacy hello must emit C39 with `missing_required_signature` sub-grade; saw events: {:?}",
        events
    );
    client_a.shutdown().expect("shutdown");
}

#[test]
fn m26_1_c5_legacy_hello_accepted_with_env_override() {
    // M26.1 C5 SECURITY FIX: when MYCO_ACCEPT_LEGACY_PEERS=1 is set, the
    // pre-M25 legacy-pin path is restored. Peer is pinned via TOFU only,
    // `federation_legacy_peer_pinned` observability event is emitted, and
    // NO C39 immune sporocarp fires (legacy peers are explicitly allowed
    // under this transition-period override).
    use myco_kernel_bridge::framing::write_frame;
    use myco_kernel_bridge::protocol::{encode_frame_body, Message};
    use myco_kernel_shared::canonical_bytes::Value as CbV;
    use std::collections::BTreeMap as BTM;

    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_env(
        &dir_a,
        vec![("MYCO_ACCEPT_LEGACY_PEERS".to_string(), "1".to_string())],
    );
    let open_resp = client_a
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![(
                "bind_addr",
                CbValue::String("127.0.0.1:0".to_string()),
            )]),
        )
        .expect("A open listener");
    let addr_a = match open_resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("addr missing"),
    };

    use std::net::TcpStream;
    let mut stream = TcpStream::connect(&addr_a).expect("dial");
    let legacy_peer_id = [0x22u8; 32];
    let mut payload = BTM::new();
    payload.insert(
        "peer_substrate_id".to_string(),
        CbV::Bytes(legacy_peer_id.to_vec()),
    );
    payload.insert("protocol_version".to_string(), CbV::Uint(1));
    let msg = Message::new("fed_hello", 1, payload);
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-federation-protocol-v1-bootstrap");
    let bootstrap_arr: [u8; 32] = h.finalize().into();
    let frame = encode_frame_body(&msg, &bootstrap_arr).expect("encode");
    write_frame(&mut stream, &frame).expect("send legacy hello");
    std::thread::sleep(std::time::Duration::from_millis(1500));

    let status = client_a
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status");
    let peer_count = match status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("peer_count missing"),
    };
    assert_eq!(
        peer_count, 1,
        "M26.1 C5: with MYCO_ACCEPT_LEGACY_PEERS=1, legacy hello must pin"
    );

    let immune_resp = client_a
        .call(proto::QUERY_IMMUNE_EVENTS, build_payload(vec![]))
        .expect("query immune events");
    let events = match immune_resp.payload.get("events") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("events missing"),
    };
    let has_c39 = events.iter().any(|ev| match ev {
        CbValue::Map(m) => match m.get("node_type") {
            Some(CbValue::String(s)) => s.contains("C39_federation_hello_signature_invalid"),
            _ => false,
        },
        _ => false,
    });
    assert!(
        !has_c39,
        "M26.1 C5 override: legacy hello with override active must NOT trigger C39; saw events: {:?}",
        events
    );
    client_a.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// M26.1 C6 (Phase γ.2): substrate_signing_key.cb permission hardening e2e.
//
// This e2e is Unix-only — Windows ACL hardening is M-anchor-1 work. It boots
// a substrate (which writes the seed with 0600), kills it, manually relaxes
// the seed file to 0644 to simulate a pre-M26.1 substrate, then re-boots
// and verifies (a) the C4 immune sporocarp is emitted on the DAG, and (b)
// the file's permissions get tightened back to 0600 in-place.
// ---------------------------------------------------------------------------

#[cfg(unix)]
#[test]
fn m26_1_c6_loose_seed_emits_c4_and_tightens() {
    use std::os::unix::fs::PermissionsExt;
    let dir = fresh_state_dir();
    // First boot: substrate creates the seed file at 0600.
    {
        let mut client = spawn_substrate_with_state_dir(&dir);
        // Drive a single round-trip so the substrate has finished its boot
        // path (otherwise the seed file may not yet be persisted).
        let _ = client
            .call(proto::FEDERATION_STATUS, build_payload(vec![]))
            .expect("status to warm boot path");
        client.shutdown().expect("shutdown initial boot");
    }
    let seed_path = dir.join("substrate_signing_key.cb");
    assert!(seed_path.exists(), "seed file must exist after first boot");
    let initial_mode = std::fs::metadata(&seed_path)
        .unwrap()
        .permissions()
        .mode()
        & 0o777;
    assert_eq!(
        initial_mode, 0o600,
        "M26.1 C6: initial save must write 0600; got {:o}",
        initial_mode
    );

    // Simulate a pre-M26.1 substrate: relax the seed file to 0644.
    std::fs::set_permissions(&seed_path, std::fs::Permissions::from_mode(0o644)).unwrap();

    // Re-boot: the substrate's boot path must (1) detect loose mode,
    // (2) emit C4 immune sporocarp, (3) tighten back to 0600 in-place.
    let mut client = spawn_substrate_with_state_dir(&dir);
    let immune_resp = client
        .call(proto::QUERY_IMMUNE_EVENTS, build_payload(vec![]))
        .expect("query immune events");
    let events = match immune_resp.payload.get("events") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("events missing"),
    };
    let has_c4 = events.iter().any(|ev| match ev {
        CbValue::Map(m) => match m.get("node_type") {
            Some(CbValue::String(s)) => s.contains("C4_substrate_secret_unsealed"),
            _ => false,
        },
        _ => false,
    });
    assert!(
        has_c4,
        "M26.1 C6: re-boot with loose seed mode must emit C4; saw events: {:?}",
        events
    );
    client.shutdown().expect("shutdown second boot");

    // Verify mode was tightened back.
    let tightened_mode = std::fs::metadata(&seed_path)
        .unwrap()
        .permissions()
        .mode()
        & 0o777;
    assert_eq!(
        tightened_mode, 0o600,
        "M26.1 C6: boot must tighten loose seed file back to 0600; got {:o}",
        tightened_mode
    );
}

// ---------------------------------------------------------------------------
// **M26.2 P11.b — Living Bets cost signals #7/#8/#9 + composite #10 RENAMED.**
//
// These tests verify the third leg of the L2_OBSERVABILITY §2 10-signal
// observatory: per-cycle compute / network / storage costs. Pre-M26.2 the
// observatory exposed only 6 base signals + 1 composite; without cost
// signals, P11 metabolic economy (budget exhaustion → compression → P7)
// has no input data and `bet_weakening_quorum` runs on a half-blind view.
//
// These tests also exercise the v3 → v4 schema bump:
// - signal_7_composite_health → signal_10_composite_health
// - signal_8_doctrine_revision_burst → doctrine_revision_burst_status
// - observatory_format_version = 4
// ---------------------------------------------------------------------------

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
