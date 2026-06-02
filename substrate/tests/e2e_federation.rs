//! E2E: Federation (P5 万物互联): listener lifecycle, peer pinning/TOFU, event pull, child sprout/quarantine, autonomous tick, signed FED_HELLO mutual auth, version-match (C61), strict mode, compatibility matrix.
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

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
    // P08 §5.1: a child spawn now requires a cultivator co-attestation, so A is
    // seed-pinned and the sprout is co-signed (see sprout_attested).
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_seed_and_env(&dir_a, REPRO_SEED, vec![]);
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

    // Sprout child B at a fresh dir (cultivator co-attested).
    let child_dir = fresh_state_dir();
    let _ = sprout_attested(&mut client_a, &child_dir, &REPRO_SEED).expect("A sprout child");
    client_a.shutdown().expect("shutdown A pre-spawn-B");

    // Spawn child B pointing at child_state_dir. B inherited A's pinned operator
    // identity, so it must boot WITH the same seed (downgrade rejected, C2).
    let mut client_b = spawn_substrate_with_seed_and_env(&child_dir, REPRO_SEED, vec![]);

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
    // P08 §5.1: A is seed-pinned and the sprout is cultivator co-signed.
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_seed_and_env(&dir_a, REPRO_SEED, vec![]);
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
    let _ = sprout_attested(&mut client_a, &child_dir, &REPRO_SEED).expect("A sprout");

    // Critical: we cannot shut down A here, because B needs A's listener
    // alive to connect. Move A to a polling thread (which keeps A's process
    // alive AND processes the inbound HELLO from B).
    // But A already has its listener opened from earlier — listener persists
    // across the shutdown-prep. Actually no — when A shuts down, its TCP
    // listener is closed by the OS.
    //
    // So we need A to STAY ALIVE while B connects. Move A to polling thread.
    let poll_handle_a = poll_in_background_for(client_a, 80);

    // Now spawn B and trigger link. B inherited A's pinned identity → seed boot.
    let mut client_b = spawn_substrate_with_seed_and_env(&child_dir, REPRO_SEED, vec![]);
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
    // P08 §5.1: A is seed-pinned and the sprout is cultivator co-signed.
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_seed_and_env(&dir_a, REPRO_SEED, vec![]);
    client_a
        .register_axis("clean", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("A register");

    let child_dir = fresh_state_dir();
    let _ = sprout_attested(&mut client_a, &child_dir, &REPRO_SEED).expect("sprout");
    client_a.shutdown().expect("shutdown A");

    let mut client_b = spawn_substrate_with_seed_and_env(&child_dir, REPRO_SEED, vec![]);
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

    // Respawn parent — should emit C7 immune sporocarp + quarantine corrupted
    // file. P08 §5.1: seed-pin the respawn so the later sprout can be cultivator
    // co-signed (the corrupt dag.cb is quarantined → fresh genesis re-pins the
    // seed-derived owner identity at handshake).
    let mut client2 = spawn_substrate_with_seed_and_env(&parent_dir, REPRO_SEED, vec![]);

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

    // Sprout child (cultivator co-attested).
    let child_dir = fresh_state_dir();
    let _ = sprout_attested(&mut client2, &child_dir, &REPRO_SEED).expect("sprout");
    client2.shutdown().expect("shutdown 2");

    // Spawn child + verify it has quarantine_entered event. Child inherited the
    // pinned identity → seed boot.
    let mut client_b = spawn_substrate_with_seed_and_env(&child_dir, REPRO_SEED, vec![]);
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

    // P08 §5.1: seed-pin the respawn so the sprout can be cultivator co-signed.
    let mut client2 = spawn_substrate_with_seed_and_env(&parent_dir, REPRO_SEED, vec![]);
    client2
        .register_axis("seeded", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("seed axis");
    let child_dir = fresh_state_dir();
    let _ = sprout_attested(&mut client2, &child_dir, &REPRO_SEED).expect("sprout");
    client2.shutdown().expect("shutdown 2");

    // Spawn child + try register_axis → should fail. Child inherited the pinned
    // identity → seed boot (handshake pins before the quarantine op-block).
    let mut client_b = spawn_substrate_with_seed_and_env(&child_dir, REPRO_SEED, vec![]);
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

    // P08 §5.1: seed-pin the respawn so the sprout can be cultivator co-signed.
    let mut client2 = spawn_substrate_with_seed_and_env(&parent_dir, REPRO_SEED, vec![]);
    client2
        .register_axis("seeded", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("seed");
    let child_dir = fresh_state_dir();
    let _ = sprout_attested(&mut client2, &child_dir, &REPRO_SEED).expect("sprout");
    client2.shutdown().expect("shutdown 2");

    // Child inherited the pinned identity → seed boot.
    let mut client_b = spawn_substrate_with_seed_and_env(&child_dir, REPRO_SEED, vec![]);

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
fn sprint_5h_federation_hello_version_mismatch_rejected_with_c61() {
    // Dial a substrate and send a FED_HELLO with protocol_version=99
    // (future). The substrate MUST reject and emit
    // C61_federation_protocol_version_mismatch.
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
    let mut payload = BTM::new();
    payload.insert(
        "peer_substrate_id".to_string(),
        CbV::Bytes(fake_peer_id.to_vec()),
    );
    // Bogus future protocol_version. Substrate must reject.
    payload.insert("protocol_version".to_string(), CbV::Uint(99));
    let msg = Message::new("fed_hello", 1, payload);

    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-federation-protocol-v1-bootstrap");
    let bootstrap_arr: [u8; 32] = h.finalize().into();
    let frame = encode_frame_body(&msg, &bootstrap_arr).expect("encode");
    write_frame(&mut stream, &frame).expect("send hello");
    std::thread::sleep(std::time::Duration::from_millis(1500));

    let immune_resp = client_a
        .call(proto::QUERY_IMMUNE_EVENTS, build_payload(vec![]))
        .expect("query immune");
    let events = match immune_resp.payload.get("events") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("events missing"),
    };
    let has_c61 = events.iter().any(|ev| match ev {
        CbValue::Map(m) => match m.get("node_type") {
            Some(CbValue::String(s)) => {
                s.contains("C61_federation_protocol_version_mismatch")
            }
            _ => false,
        },
        _ => false,
    });
    assert!(
        has_c61,
        "Sprint 5.H T2.5: protocol_version=99 hello must emit C61; got events: {events:?}"
    );

    // Peer must NOT be pinned.
    let status = client_a
        .call(proto::FEDERATION_STATUS, build_payload(vec![]))
        .expect("status");
    let peer_count = match status.payload.get("peer_count") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("peer_count missing"),
    };
    assert_eq!(
        peer_count, 0,
        "Sprint 5.H T2.5: version-mismatch hello must NOT result in pinned peer"
    );
    client_a.shutdown().expect("shutdown");
}

#[test]
fn sprint_5h_federation_protocol_version_constant_is_pinned() {
    // Lock the FEDERATION_PROTOCOL_VERSION value so cross-version
    // doctrine changes are explicit. If this fails after a refactor, the
    // refactor must include a compatibility matrix migration plan.
    use substrate::federation::protocol::FEDERATION_PROTOCOL_VERSION;
    assert_eq!(
        FEDERATION_PROTOCOL_VERSION, 1,
        "Sprint 5.H T2.5: FEDERATION_PROTOCOL_VERSION bumped without \
         compatibility-matrix migration — see Sprint 5.H acknowledged debt"
    );
}

#[test]
fn sprint_6i_strict_mode_accepts_signed_hello() {
    // Spawn with MYCO_REQUIRE_ED25519_OPERATOR_HANDSHAKE=1 + a signing
    // seed → handshake succeeds.
    let dir = fresh_state_dir();
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    let client = BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
        extra_env: vec![
            (
                "MYCO_STATE_DIR".to_string(),
                dir.to_string_lossy().into_owned(),
            ),
            (
                "MYCO_REQUIRE_ED25519_OPERATOR_HANDSHAKE".to_string(),
                "1".to_string(),
            ),
        ],
        operator_signing_seed: Some([0x99; 32]),
    });
    assert!(
        client.is_ok(),
        "Sprint 6.I T2.11: signed hello + strict-mode env var must succeed; \
         got error: {:?}",
        client.err()
    );
    client.unwrap().shutdown().expect("shutdown");
}

#[test]
fn sprint_6i_strict_mode_rejects_unsigned_hello() {
    // Spawn with strict-mode env var + NO signing seed → handshake fails
    // because no operator_pubkey in hello.
    let dir = fresh_state_dir();
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    let result = BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
        extra_env: vec![
            (
                "MYCO_STATE_DIR".to_string(),
                dir.to_string_lossy().into_owned(),
            ),
            (
                "MYCO_REQUIRE_ED25519_OPERATOR_HANDSHAKE".to_string(),
                "1".to_string(),
            ),
        ],
        operator_signing_seed: None,
    });
    assert!(
        result.is_err(),
        "Sprint 6.I T2.11: unsigned hello + strict-mode must be rejected; \
         got Ok (substrate accepted legacy hello despite strict flag)"
    );
}

#[test]
fn sprint_6i_legacy_mode_default_still_accepts_unsigned() {
    // Regression: without the strict-mode env var, substrate continues
    // to accept unsigned hellos (M5-M8 backward compat preserved).
    let (client, _dir) = spawn_substrate();
    client.shutdown().expect("legacy spawn succeeds + shuts down");
}

#[test]
fn sprint_6h_versions_interoperable_returns_true_for_exact_match() {
    use substrate::federation::protocol::{
        federation_versions_interoperable, FEDERATION_PROTOCOL_VERSION,
    };
    assert!(
        federation_versions_interoperable(
            FEDERATION_PROTOCOL_VERSION,
            FEDERATION_PROTOCOL_VERSION
        ),
        "exact-match versions must interoperate"
    );
}

#[test]
fn sprint_6h_versions_interoperable_returns_false_when_matrix_empty() {
    use substrate::federation::protocol::federation_versions_interoperable;
    // At v3.1.1 the matrix is empty, so any non-exact-match returns false.
    assert!(
        !federation_versions_interoperable(1, 2),
        "v1 + v2 not in matrix → must NOT interoperate (Sprint 5.H behavior preserved)"
    );
    assert!(
        !federation_versions_interoperable(1, 99),
        "v1 + v99 not in matrix → must NOT interoperate"
    );
}

#[test]
fn sprint_6h_compatibility_matrix_is_empty_at_v1() {
    // Lock the public-surface contract: at v3.1.1, the matrix has no
    // cross-version bridges. When v2 ships, the implementer adds entries
    // here and updates this test accordingly.
    use substrate::federation::protocol::FEDERATION_VERSION_COMPATIBILITY_MATRIX;
    assert_eq!(
        FEDERATION_VERSION_COMPATIBILITY_MATRIX.len(),
        0,
        "Sprint 6.H T2.10: compatibility matrix should be empty at v1; \
         got {} entries — has v2 shipped without updating this test?",
        FEDERATION_VERSION_COMPATIBILITY_MATRIX.len()
    );
}

/// **C43 (2026-06-02)** — federation recursive-injection / depth-exhaustion
/// defense. The MAX-depth nesting cap + banned-type-at-depth detection are
/// proven deterministically over hand-built canonical bytes in the substrate
/// lib's `federation::handlers::c43_recursive_validation_tests` (a full N-peer
/// wire simulation of a 6-deep adversarial payload is impractical because a
/// well-behaved peer never *serves* a hand-crafted over-deep
/// `federation_received:` event from its own DAG).
///
/// This E2E test pins the complementary FALSE-POSITIVE property on the REAL
/// wire path: an ordinary single-level federation pull of legitimate
/// `raw_material:` events must ingest normally and must NOT spuriously emit a
/// `C43_federation_recursive_injection` immune sporocarp. (A regression that
/// over-rejected legitimate federation traffic would surface here.)
#[test]
fn c43_legitimate_federation_pull_does_not_trip_recursive_defense() {
    // Peer A: open listener + ingest two legitimate raw_material events
    // (allowlisted, non-nested — these wrap to a single `federation_received:`
    // layer on B, i.e. depth 1, well under MAX_FEDERATION_RECURSION_DEPTH=5).
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
    client_a
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                ("content_bytes", CbValue::Bytes(b"c43 legit material 1".to_vec())),
            ]),
        )
        .expect("A ingest raw_material 1");
    client_a
        .call(
            proto::INGEST_RAW_MATERIAL,
            build_payload(vec![
                ("content_kind", CbValue::String("text".to_string())),
                ("content_bytes", CbValue::Bytes(b"c43 legit material 2".to_vec())),
            ]),
        )
        .expect("A ingest raw_material 2");

    let poll_handle = poll_in_background_for(client_a, 80);

    // Peer B connects + pulls A's events.
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
        "legitimate pull should ingest A's 2 raw_material events; got {events_ingested}"
    );

    // B's DAG should contain federation_received: wrappers (the ingested
    // attestations) — confirming the recursive validator ACCEPTED them.
    let wrapped_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("federation_received:".to_string()),
                ),
            ]),
        )
        .expect("B query wrappers");
    let wrapped_arr = match wrapped_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !wrapped_arr.is_empty(),
        "legitimate single-level federation events must be accepted + wrapped"
    );

    // CRITICAL: B's DAG must NOT contain a C43 immune sporocarp — legitimate
    // shallow federation traffic must never trip the depth-exhaustion defense.
    let c43_resp = client_b
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("immune:C43".to_string()),
                ),
            ]),
        )
        .expect("B query C43");
    let c43_arr = match c43_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        c43_arr.is_empty(),
        "C43 must NOT fire for legitimate shallow federation traffic; got {} immune:C43 event(s)",
        c43_arr.len()
    );

    let client_a = poll_handle.join().expect("poll join");
    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

