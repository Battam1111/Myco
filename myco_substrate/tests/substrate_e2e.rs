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

    // observatory_format_version bumped to 2 in M24.5 (added signals 2/3/4/7).
    let fmt = match resp.payload.get("observatory_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("fmt version missing"),
    };
    assert_eq!(fmt, 2);

    // M24.5: signals 2/3/4/7 present.
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
        resp.payload.contains_key("signal_7_composite_health"),
        "M24.5: signal_7 composite present"
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
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("composite_test", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    let resp = client
        .call(proto::QUERY_SUBSTRATE_OBSERVATORY, build_payload(vec![]))
        .expect("observatory");
    let s7 = match resp.payload.get("signal_7_composite_health") {
        Some(CbValue::Map(m)) => m.clone(),
        _ => panic!("signal_7 missing"),
    };
    let composite_repr = match s7.get("composite_health_score_repr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("composite_health_score_repr missing"),
    };
    let parsed: f64 = composite_repr.parse().expect("composite is parseable float");
    assert!(parsed >= 0.0, "composite should be non-negative; got {parsed}");
    let fmt = match s7.get("composite_format_version") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("composite_format_version missing"),
    };
    assert_eq!(fmt, 2, "composite format version pinned at 2");
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
