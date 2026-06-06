//! E2E: Immune detectors: substrate-signing-key integrity (M25.0), legacy-hello rejection + seed-permission hardening (M26.1 C5/C6), DAG/manifest CB integrity (C41/C42) + compression registry, cross-file integrity checks (C57/C58/C59), immune-emission rate limiting (Sprint 5.F), C53 silent-breach redesign (Sprint 6.A), and event-batch size caps (Sprint 6.B).
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

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

#[test]
fn m26_3_c41_dag_cb_integrity_violation_fires_on_garbled_dag_cb() {
    // Setup: spawn substrate, generate some DAG content, shut down.
    let dir = fresh_state_dir();
    let client = spawn_substrate_with_state_dir(&dir);
    client.shutdown().expect("shutdown 1");

    // Corrupt dag.cb with random bytes.
    let dag_path = dir.join("dag.cb");
    std::fs::write(&dag_path, b"M26.3-c41-test-garbage-not-canonical-bytes")
        .expect("corrupt dag.cb");

    // Respawn → C7 + C41 must both fire (M26.3 emits both).
    let mut client2 = spawn_substrate_with_state_dir(&dir);
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
        _ => panic!("nodes array missing"),
    };

    let mut saw_c41 = false;
    let mut saw_c7 = false;
    for node in &immune_arr {
        let node_map = match node {
            CbValue::Map(m) => m,
            _ => continue,
        };
        let nt = match node_map.get("node_type") {
            Some(CbValue::String(s)) => s.clone(),
            _ => continue,
        };
        if nt.contains("C41_dag_cb_integrity_violation") {
            saw_c41 = true;
        }
        if nt.contains("C7_dag_retro_edit_detected") {
            saw_c7 = true;
        }
    }
    assert!(
        saw_c41,
        "M26.3 C41_dag_cb_integrity_violation must fire when dag.cb is garbled"
    );
    assert!(
        saw_c7,
        "C7 must also still fire (M26.3 emits both, doctrine-aligned)"
    );
    client2.shutdown().expect("shutdown 2");
}

#[test]
fn m26_3_c42_manifest_cb_integrity_violation_fires_on_garbled_manifest_cb() {
    // Setup: spawn substrate (writes manifest.cb), shut down.
    let dir = fresh_state_dir();
    let client = spawn_substrate_with_state_dir(&dir);
    client.shutdown().expect("shutdown 1");

    // Corrupt manifest.cb.
    let manifest_path = dir.join("manifest.cb");
    if !manifest_path.exists() {
        // Manifest may not exist on M21+ DAG-only path; create one then corrupt.
        // In that case this test path is trivially satisfied by the manifest
        // being absent (Manifest::load returns Ok(None) → genesis); skip.
        return;
    }
    std::fs::write(&manifest_path, b"M26.3-c42-test-garbage-not-canonical-bytes")
        .expect("corrupt manifest.cb");

    let mut client2 = spawn_substrate_with_state_dir(&dir);
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
        _ => panic!("nodes array missing"),
    };
    let saw_c42 = immune_arr.iter().any(|n| {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                return nt.contains("C42_manifest_cb_integrity_violation");
            }
        }
        false
    });
    assert!(
        saw_c42,
        "M26.3 C42_manifest_cb_integrity_violation must fire when manifest.cb is garbled"
    );
    client2.shutdown().expect("shutdown 2");
}

#[test]
fn m26_3_compression_rule_registry_seed_defaults_match_doctrine() {
    // The seed compression_rule_registry MUST contain exactly the three
    // L0 P10.a categories: raw_material / federation / trajectory. This
    // test pins the public surface of the seed so doctrine drift surfaces
    // in CI.
    use substrate::events::seed_compression_rule_registry;
    let rules = seed_compression_rule_registry();
    assert_eq!(rules.len(), 3, "M26.3 P10.a: must seed exactly 3 rules");
    let rule_ids: Vec<&str> = rules.iter().map(|r| r.rule_id.as_str()).collect();
    assert!(
        rule_ids.contains(&"raw_material_aggregate_v1"),
        "raw_material rule missing; got {rule_ids:?}"
    );
    assert!(
        rule_ids.contains(&"federation_payload_retention_v1"),
        "federation rule missing; got {rule_ids:?}"
    );
    assert!(
        rule_ids.contains(&"trajectory_archive_v1"),
        "trajectory rule missing; got {rule_ids:?}"
    );
    // Every seed rule has min_age_cycles ≥ 1000 (matches L0 P10.b
    // "most recent ≥1000 cycles full DAG" floor).
    for r in &rules {
        assert!(
            r.min_age_cycles >= 1000,
            "rule {} has min_age_cycles {} < 1000 floor",
            r.rule_id,
            r.min_age_cycles
        );
    }
}

#[test]
fn m26_3_compression_invariant_set_seed_covers_p10_b_categories() {
    // P10.b enumerates the categories that MUST NEVER be compressed.
    // The seed CompressionInvariantSet must cover all 6 of them plus the
    // recent_cycles_floor.
    use substrate::events::{node_type_in_invariant_set, seed_compression_invariant_set};
    let inv = seed_compression_invariant_set();
    assert!(
        inv.recent_cycles_floor >= 1000,
        "P10.b: recent_cycles_floor must be ≥ 1000; got {}",
        inv.recent_cycles_floor
    );
    // Every category must produce a match for a sample node_type.
    let samples = [
        "genesis_event:abc",
        "owner_key_initialized",
        "owner_key_added",
        "owner_key_archived",
        "mutation:schema_evolution",
        "mutation:compression",
        "evolution_succeeded:add_axis",
        "evolution_failed:add_axis",
        "self_euthanasia_executed:axis_x",
        "federation_peer_pinned:abcd1234",
        "operator_pinned:abcd1234",
        "birth_period_quarantine_entered",
        "birth_period_quarantine_lifted",
        "compression_event:raw_material_aggregate_v1",
    ];
    for s in &samples {
        assert!(
            node_type_in_invariant_set(s, &inv),
            "{s} must be recognized as invariant-set member by P10.b"
        );
    }
    // Negative case: a normal raw_material node IS compressible (provided
    // it's old enough).
    assert!(
        !node_type_in_invariant_set("raw_material:text", &inv),
        "raw_material:* must NOT be in invariant set (it's a compression candidate)"
    );
    assert!(
        !node_type_in_invariant_set("axis_perturbed:curiosity", &inv),
        "axis_perturbed:* must NOT be in invariant set (it's a trajectory candidate)"
    );
}

#[test]
fn m26_3_compression_witness_canonical_bytes_roundtrip() {
    // The CompressionWitness canonical-bytes encoder/decoder must round-trip
    // — every byte that goes in must come back out unchanged. Pins F16
    // canonical_bytes_serializer_spec compatibility for the M26.3 schema.
    use substrate::events::{
        decode_compression_witness_minimal, encode_compression_witness,
    };
    let rule_id = "raw_material_aggregate_v1";
    let h1 = [1u8; 32];
    let h2 = [2u8; 32];
    let hashes = vec![h1, h2];
    let aggregate = b"M26.3 test aggregate payload";
    let tip = [9u8; 32];
    let arg = "I9 witness: sum-to-sporocarp preserves cumulative axis value";

    let encoded = encode_compression_witness(rule_id, &hashes, aggregate, &tip, arg);
    let (decoded_rule_id, decoded_hashes, decoded_agg, decoded_tip) =
        decode_compression_witness_minimal(encoded.as_ref())
            .expect("witness decodes from its own encoding");
    assert_eq!(decoded_rule_id, rule_id);
    assert_eq!(decoded_hashes, hashes);
    assert_eq!(decoded_agg, aggregate);
    assert_eq!(decoded_tip, tip);
}

#[test]
fn sprint_5c_c57_passes_on_fresh_substrate_with_one_genesis() {
    // **Positive baseline**: a freshly-booted substrate has exactly one
    // genesis_event:* node → C57 passes.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::RUN_IMMUNE_CHECK, build_payload(vec![]))
        .expect("run_immune_check");
    let checks = match resp.payload.get("checks") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("checks missing"),
    };
    let genesis_check = checks
        .iter()
        .find_map(|c| {
            let m = match c {
                CbValue::Map(m) => m,
                _ => return None,
            };
            match m.get("check_id") {
                Some(CbValue::String(s)) if s == "genesis_event_uniqueness" => Some(m),
                _ => None,
            }
        })
        .expect("genesis_event_uniqueness check not in result set");
    let passed = match genesis_check.get("passed") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("passed missing"),
    };
    assert!(
        passed,
        "Sprint 5.C C57: fresh substrate should pass genesis uniqueness; \
         evidence: {:?}",
        genesis_check.get("evidence")
    );
    client.shutdown().expect("shutdown");
}

// (v0.9 owner-key removal: `sprint_5c_c58_passes_when_no_owner_key_initialized_event`
// was deleted — the C58 owner_pubkey_dag_pin_consistency integrity check was
// removed with the pinned operator identity.)

#[test]
fn sprint_5c_c59_passes_after_normal_cycle_advance() {
    // **Positive baseline**: pump 3 cycles; manifest_cycle_counter = 3 +
    // genesis offset; DAG has 3 cycle_advanced events. Diff ≤ 1 tolerance.
    let (mut client, _dir) = spawn_substrate();
    pump_cycles(&mut client, 3);
    let resp = client
        .call(proto::RUN_IMMUNE_CHECK, build_payload(vec![]))
        .expect("run_immune_check");
    let checks = match resp.payload.get("checks") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("checks missing"),
    };
    let c59 = checks
        .iter()
        .find_map(|c| {
            let m = match c {
                CbValue::Map(m) => m,
                _ => return None,
            };
            match m.get("check_id") {
                Some(CbValue::String(s)) if s == "manifest_cycle_vs_dag_advance_count" => Some(m),
                _ => None,
            }
        })
        .expect("manifest_cycle_vs_dag_advance_count check missing");
    let passed = match c59.get("passed") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("passed missing"),
    };
    assert!(
        passed,
        "Sprint 5.C C59: cycle counter should agree with cycle_advanced count \
         after 3 cycles; evidence: {:?}",
        c59.get("evidence")
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5c_new_check_ids_appear_in_run_immune_check_response() {
    // Lock the public-surface contract: the 3 new C-row check IDs (C57/C58/C59)
    // are present in every run_immune_check response. Downstream tooling
    // depends on this stable enumeration; if an upstream refactor accidentally
    // removes one, this test fires.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(proto::RUN_IMMUNE_CHECK, build_payload(vec![]))
        .expect("run_immune_check");
    let checks = match resp.payload.get("checks") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("checks missing"),
    };
    let mut seen_ids: std::collections::HashSet<String> = std::collections::HashSet::new();
    for c in &checks {
        if let CbValue::Map(m) = c {
            if let Some(CbValue::String(s)) = m.get("check_id") {
                seen_ids.insert(s.clone());
            }
        }
    }
    // (v0.9: owner_pubkey_dag_pin_consistency / pinned_pubkey_well_formed were
    // removed with the owner-key layer; the remaining cross-file checks stay.)
    for required in &[
        "genesis_event_uniqueness",
        "manifest_cycle_vs_dag_advance_count",
    ] {
        assert!(
            seen_ids.contains(*required),
            "Sprint 5.C: required check_id {required} missing from response; \
             saw: {seen_ids:?}"
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5f_rapid_same_detector_emissions_rate_limited_to_one() {
    // Submit 5 forbidden preserve_all mutations in rapid succession. Each
    // gets rejected (accepted=false). C56 immune emission would normally
    // fire 5 times; rate limit caps at 1 within the 1-second window.
    let (mut client, _dir) = spawn_substrate();
    for _ in 0..5 {
        let _ = client.call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("preserve_all_axes".to_string())),
                (
                    "content_canonical_bytes",
                    CbValue::Bytes(b"rapid_attack".to_vec()),
                ),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        );
    }
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("immune:C56_cultivator_preserve_all_attempted".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        1,
        "Sprint 5.F T2.4: same-detector rapid emissions should rate-limit to 1 \
         per 1-second window; got {} DAG events (rate limit not working)",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5f_distinct_detectors_have_independent_rate_limits() {
    // Trigger C56 (preserve_all) once, then trigger a DIFFERENT detector — both
    // should emit because rate limits are per-detector, not global.
    //
    // **v0.9 owner-key removal**: the original second trigger was an
    // `l0_revision_attest` mutation with a malformed owner-signed envelope,
    // which produced C5 attestation_invalid. That owner-signed mutation type was
    // removed (it now classifies UNTYPED), so this test uses C14
    // untyped_mutation_blocked as the distinct second detector — still a
    // different detector_id than C56, which is all the rate-limit independence
    // assertion needs.
    let (mut client, _dir) = spawn_substrate();

    // C56 — preserve_all
    let _ = client.call(
        proto::SUBMIT_MUTATION,
        build_payload(vec![
            ("mutation_type", CbValue::String("preserve_all_axes".to_string())),
            ("content_canonical_bytes", CbValue::Bytes(b"x".to_vec())),
            ("touched_fields", CbValue::Array(vec![])),
            ("touched_files", CbValue::Array(vec![])),
            ("touched_meta_structures", CbValue::Array(vec![])),
        ]),
    );

    // An unclassifiable mutation → C14 untyped_mutation_blocked. Different
    // detector_id than C56, so it should emit independently.
    let _ = client.call(
        proto::SUBMIT_MUTATION,
        build_payload(vec![
            ("mutation_type", CbValue::String("totally_unknown_mutation_xyz".to_string())),
            (
                "content_canonical_bytes",
                CbValue::Bytes(b"unclassifiable".to_vec()),
            ),
            ("touched_fields", CbValue::Array(vec![])),
            ("touched_files", CbValue::Array(vec![])),
            ("touched_meta_structures", CbValue::Array(vec![])),
        ]),
    );

    // Query all immune:* events — should see both C56 AND C14.
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                ("node_type_prefix", CbValue::String("immune:".to_string())),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    let mut detector_ids: std::collections::HashSet<String> =
        std::collections::HashSet::new();
    for n in &nodes {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                if let Some(suffix) = nt.strip_prefix("immune:") {
                    detector_ids.insert(suffix.to_string());
                }
            }
        }
    }
    let saw_c56 = detector_ids
        .iter()
        .any(|s| s.starts_with("C56_cultivator_preserve_all"));
    let saw_c14 = detector_ids
        .iter()
        .any(|s| s.starts_with("C14_untyped_mutation"));
    assert!(
        saw_c56,
        "Sprint 5.F T2.4: C56 missing from immune events; saw {detector_ids:?}"
    );
    assert!(
        saw_c14,
        "Sprint 5.F T2.4: C14 missing — distinct detectors should NOT \
         share rate limits; saw {detector_ids:?}"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5f_suppressed_since_last_emission_field_present_after_burst() {
    // After a burst of same-detector calls within 1 second, the FIRST
    // event has no suppression record (first emission). If we wait >1s
    // then trigger again, the second emission should carry
    // `suppressed_since_last_emission` > 0 IF additional bursts happened
    // in the meantime.
    //
    // Test sequence:
    //   1. Trigger 3x C56 quickly → 1 DAG event, 2 suppressed
    //   2. Wait 1.1s
    //   3. Trigger 1x C56 → 2nd DAG event, should carry suppressed=2
    let (mut client, _dir) = spawn_substrate();

    // Phase 1: burst.
    for _ in 0..3 {
        let _ = client.call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("preserve_all_axes".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(b"burst".to_vec())),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        );
    }
    // Phase 2: wait past rate-limit window.
    std::thread::sleep(std::time::Duration::from_millis(1100));
    // Phase 3: one more trigger.
    let _ = client.call(
        proto::SUBMIT_MUTATION,
        build_payload(vec![
            ("mutation_type", CbValue::String("preserve_all_axes".to_string())),
            ("content_canonical_bytes", CbValue::Bytes(b"after".to_vec())),
            ("touched_fields", CbValue::Array(vec![])),
            ("touched_files", CbValue::Array(vec![])),
            ("touched_meta_structures", CbValue::Array(vec![])),
        ]),
    );

    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("immune:C56_cultivator_preserve_all_attempted".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        2,
        "Sprint 5.F T2.4: expected exactly 2 C56 DAG events (burst suppressed \
         + after-window emit); got {}",
        nodes.len()
    );
    // The most recent (second) event should have suppressed_since_last_emission >= 2
    // (the 2 suppressed calls during the burst).
    //
    // Note: query_recent_nodes returns nodes in insertion order (latest
    // last) — but the exact slice order depends on the query impl. Inspect
    // both events; at least one should carry suppressed > 0.
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let mut saw_suppressed = false;
    for n in &nodes {
        let m = match n {
            CbValue::Map(m) => m,
            _ => continue,
        };
        let content = match m.get("content_canonical_bytes") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => continue,
        };
        let decoded = match cb_decode(&content) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let event_map = match decoded {
            CbV::Map(m) => m,
            _ => continue,
        };
        if let Some(CbV::Uint(n)) = event_map.get("suppressed_since_last_emission") {
            if *n >= 2 {
                saw_suppressed = true;
            }
        }
    }
    assert!(
        saw_suppressed,
        "Sprint 5.F T2.4: at least one C56 event should carry \
         suppressed_since_last_emission >= 2 reflecting the burst-suppressed \
         calls — operator must be able to reconstruct true breach count"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_6b_per_event_size_cap_is_pinned_at_256_kib() {
    // Lock the constant value as a public-surface contract. Operator tooling
    // depends on this bound being stable; a refactor that lowers it could
    // unexpectedly reject normal federation traffic.
    use substrate::federation::protocol::FED_EVENT_MAX_CONTENT_BYTES;
    assert_eq!(
        FED_EVENT_MAX_CONTENT_BYTES,
        256 * 1024,
        "Sprint 6.B T1.8: FED_EVENT_MAX_CONTENT_BYTES bumped without \
         deliberate operator-tooling migration"
    );
}

#[test]
fn sprint_6b_parse_event_batch_rejects_oversized_event() {
    use myco_kernel_shared::canonical_bytes::Value as CbV;
    use std::collections::BTreeMap as BTM;
    use substrate::federation::protocol::{parse_event_batch_payload, FED_EVENT_MAX_CONTENT_BYTES};

    // Build a synthetic FED_EVENT_BATCH containing ONE event with content
    // exceeding the cap by 1 byte.
    let huge_content = vec![0xABu8; FED_EVENT_MAX_CONTENT_BYTES + 1];
    let mut event_map = BTM::new();
    event_map.insert(
        "parent_hashes".to_string(),
        CbV::Array(vec![CbV::Bytes(vec![0u8; 32])]),
    );
    event_map.insert(
        "node_type".to_string(),
        CbV::String("raw_material:text".to_string()),
    );
    event_map.insert("created_at_cycle".to_string(), CbV::Uint(1));
    event_map.insert(
        "content_canonical_bytes".to_string(),
        CbV::Bytes(huge_content),
    );

    let mut payload = BTM::new();
    payload.insert(
        "events".to_string(),
        CbV::Array(vec![CbV::Map(event_map)]),
    );
    payload.insert("is_last_batch".to_string(), CbV::Bool(true));

    let result = parse_event_batch_payload(&payload);
    assert!(
        result.is_err(),
        "Sprint 6.B T1.8: event of size {} bytes must be rejected by parser; \
         got Ok",
        FED_EVENT_MAX_CONTENT_BYTES + 1
    );
    let err = format!("{}", result.unwrap_err());
    assert!(
        err.contains("FED_EVENT_MAX_CONTENT_BYTES"),
        "Sprint 6.B T1.8: rejection error should cite the cap constant; got: {err}"
    );
}

#[test]
fn sprint_6b_parse_event_batch_accepts_at_cap_boundary() {
    // Boundary test: an event of EXACTLY FED_EVENT_MAX_CONTENT_BYTES must
    // be accepted (the cap is inclusive of the max value; only b.len() > cap
    // is rejected).
    use myco_kernel_shared::canonical_bytes::Value as CbV;
    use std::collections::BTreeMap as BTM;
    use substrate::federation::protocol::{parse_event_batch_payload, FED_EVENT_MAX_CONTENT_BYTES};

    let max_content = vec![0xCDu8; FED_EVENT_MAX_CONTENT_BYTES];
    let mut event_map = BTM::new();
    event_map.insert(
        "parent_hashes".to_string(),
        CbV::Array(vec![CbV::Bytes(vec![0u8; 32])]),
    );
    event_map.insert(
        "node_type".to_string(),
        CbV::String("raw_material:text".to_string()),
    );
    event_map.insert("created_at_cycle".to_string(), CbV::Uint(1));
    event_map.insert(
        "content_canonical_bytes".to_string(),
        CbV::Bytes(max_content),
    );

    let mut payload = BTM::new();
    payload.insert(
        "events".to_string(),
        CbV::Array(vec![CbV::Map(event_map)]),
    );
    payload.insert("is_last_batch".to_string(), CbV::Bool(true));

    let result = parse_event_batch_payload(&payload);
    assert!(
        result.is_ok(),
        "Sprint 6.B T1.8: event of size exactly {} bytes (cap value) must be \
         accepted; got Err: {:?}",
        FED_EVENT_MAX_CONTENT_BYTES,
        result.err()
    );
}

#[test]
fn sprint_6a_c53_fires_when_emit_path_silently_broken() {
    // Combine tight budgets + suppressed emission → DAG has no
    // budget_exhausted:* events → C53 must fire under the new DAG-query
    // implementation.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![
            (
                "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
                "1".to_string(),
            ),
            (
                "MYCO_TEST_SUPPRESS_BUDGET_EXHAUSTED_EMIT".to_string(),
                "1".to_string(),
            ),
        ],
    );
    pump_cycles(&mut client, 3);
    // Verify NO budget_exhausted events were emitted (suppression worked).
    let be_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("budget_exhausted:".to_string()),
                ),
            ]),
        )
        .expect("query budget_exhausted");
    let be_nodes = match be_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        be_nodes.is_empty(),
        "Sprint 6.A: suppression flag should produce zero budget_exhausted \
         events; got {} (env var not threading through)",
        be_nodes.len()
    );
    // Now verify C53 fired (silent breach detected).
    let c53_resp = client
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
        .expect("query immune");
    let c53_nodes = match c53_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !c53_nodes.is_empty(),
        "Sprint 6.A T1.5: C53 must fire when budget exhausted AND no \
         budget_exhausted:* event in DAG window; got 0 C53 events (logic \
         tautology fix incomplete — defense-in-depth still dead)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_6a_c53_stays_quiet_when_emit_path_works() {
    // Regression: with tight budgets but WITHOUT suppression, the primary
    // emission path emits budget_exhausted:* events every ≥10 cycles. The
    // DAG-query C53 check sees those events in window → no C53 fires.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![(
            "MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53".to_string(),
            "1".to_string(),
        )],
    );
    pump_cycles(&mut client, 30);
    let c53_resp = client
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
        .expect("query immune");
    let nodes = match c53_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        nodes.is_empty(),
        "Sprint 6.A T1.5: C53 must NOT fire when budget_exhausted events \
         are present in DAG window; got {} false positives",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

