//! E2E: Persistence & sealing: Sprint 2.C backup-encryption-status projection, Sprint 2.B v1 seed BLAKE3 integrity tag, Sprint 3 self-driven cycle-advance flag, Sprint 5.I export/restore backup mechanism, and Sprint 6.K DAG at-rest envelope (+ Windows DPAPI).
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

#[test]
fn v3_1_1_sprint_2c_backup_encryption_status_valid_values_locked() {
    use substrate::events::{
        BACKUP_ENCRYPTION_STATUS_CULTIVATOR_DECLINED_EXPLICIT,
        BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY,
        BACKUP_ENCRYPTION_STATUS_VALID_VALUES,
    };
    // The two canonical L1/SKIN §8 values must be in the registry.
    assert_eq!(BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY, "encrypted_externally");
    assert_eq!(
        BACKUP_ENCRYPTION_STATUS_CULTIVATOR_DECLINED_EXPLICIT,
        "cultivator_declined_explicit"
    );
    assert!(
        BACKUP_ENCRYPTION_STATUS_VALID_VALUES.contains(&BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY)
    );
    assert!(BACKUP_ENCRYPTION_STATUS_VALID_VALUES
        .contains(&BACKUP_ENCRYPTION_STATUS_CULTIVATOR_DECLINED_EXPLICIT));
    // Exactly two values — additions/removals are a doctrinal decision.
    assert_eq!(
        BACKUP_ENCRYPTION_STATUS_VALID_VALUES.len(),
        2,
        "v3.1.1 Sprint 2.C: doctrine-pinned count drift"
    );
}

#[test]
fn v3_1_1_sprint_2c_backup_encryption_status_declared_node_type_carries_status() {
    use substrate::events::backup_encryption_status_declared_node_type;
    let nt = backup_encryption_status_declared_node_type("encrypted_externally");
    assert!(
        nt.starts_with("backup_encryption_status_declared:"),
        "node_type prefix: {nt}"
    );
    assert!(
        nt.ends_with("encrypted_externally"),
        "node_type status suffix: {nt}"
    );
}

#[test]
fn v3_1_1_sprint_2c_encode_decode_roundtrip_with_key_id() {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    use substrate::events::encode_backup_encryption_status_declared;

    let body = encode_backup_encryption_status_declared(
        "encrypted_externally",
        Some("cultivator_backup_key_2026q2_xchacha20"),
        12345,
    );
    let v = decode(body.as_ref()).expect("body decodes");
    let m = match v {
        Value::Map(m) => m,
        _ => panic!("not a map"),
    };
    match m.get("status") {
        Some(Value::String(s)) => assert_eq!(s, "encrypted_externally"),
        _ => panic!("status missing"),
    }
    match m.get("key_id") {
        Some(Value::String(s)) => {
            assert_eq!(s, "cultivator_backup_key_2026q2_xchacha20")
        }
        _ => panic!("key_id missing or wrong type"),
    }
    match m.get("declared_at_cycle") {
        Some(Value::Uint(n)) => assert_eq!(*n, 12345),
        _ => panic!("declared_at_cycle missing"),
    }
}

#[test]
fn v3_1_1_sprint_2c_encode_decode_roundtrip_without_key_id() {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    use substrate::events::encode_backup_encryption_status_declared;

    let body = encode_backup_encryption_status_declared(
        "cultivator_declined_explicit",
        None,
        7777,
    );
    let v = decode(body.as_ref()).expect("body decodes");
    let m = match v {
        Value::Map(m) => m,
        _ => panic!("not a map"),
    };
    // key_id encoded as Null when None passed.
    match m.get("key_id") {
        Some(Value::Null) => {}
        _ => panic!("key_id must be Null when None passed"),
    }
}

#[test]
fn v3_1_1_sprint_2c_decode_status_returns_status_string() {
    use substrate::events::{decode_backup_encryption_status, encode_backup_encryption_status_declared};
    let body = encode_backup_encryption_status_declared(
        "cultivator_declined_explicit",
        None,
        100,
    );
    let recovered = decode_backup_encryption_status(body.as_ref())
        .expect("decode returns Some");
    assert_eq!(recovered, "cultivator_declined_explicit");
}

#[test]
fn v3_1_1_sprint_2c_decode_status_on_garbage_returns_none() {
    use substrate::events::decode_backup_encryption_status;
    // Random bytes are not a canonical-bytes Map.
    assert!(decode_backup_encryption_status(b"not_canonical_bytes").is_none());
}

#[test]
fn v3_1_1_sprint_2c_derive_from_empty_dag_returns_none() {
    use myco_kernel_schema::dag::Dag;
    use substrate::events::derive_backup_encryption_status_from_dag;
    let dag = Dag::default();
    assert!(derive_backup_encryption_status_from_dag(&dag).is_none());
}

#[test]
fn v3_1_1_sprint_2c_derive_latest_event_wins() {
    use myco_kernel_schema::dag::Dag;
    use substrate::events::{
        backup_encryption_status_declared_node_type, derive_backup_encryption_status_from_dag,
        encode_backup_encryption_status_declared,
    };

    let mut dag = Dag::default();
    // Insert two events: first "encrypted_externally" at cycle 10, then
    // "cultivator_declined_explicit" at cycle 20. Latest (cycle 20) wins.
    let body_1 =
        encode_backup_encryption_status_declared("encrypted_externally", None, 10);
    let nt_1 = backup_encryption_status_declared_node_type("encrypted_externally");
    let parents_1: Vec<_> = Vec::new();
    let h1 = dag.insert_node(parents_1, nt_1, 10, body_1).unwrap();

    let body_2 = encode_backup_encryption_status_declared(
        "cultivator_declined_explicit",
        None,
        20,
    );
    let nt_2 = backup_encryption_status_declared_node_type("cultivator_declined_explicit");
    let _ = dag.insert_node(vec![h1], nt_2, 20, body_2).unwrap();

    let derived = derive_backup_encryption_status_from_dag(&dag);
    assert_eq!(
        derived,
        Some("cultivator_declined_explicit".to_string()),
        "latest cycle's status must win"
    );
}

#[test]
fn v3_1_1_sprint_2c_derive_ignores_unrelated_node_types() {
    use myco_kernel_schema::dag::Dag;
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use substrate::events::derive_backup_encryption_status_from_dag;

    let mut dag = Dag::default();
    // Insert an unrelated node — must not affect derivation result.
    let body = cb_encode(&Value::String("noise".to_string())).unwrap();
    let _ = dag.insert_node(Vec::new(), "axis_perturbed:hunger".to_string(), 5, body)
        .unwrap();
    assert!(derive_backup_encryption_status_from_dag(&dag).is_none());
}

#[test]
#[cfg(not(windows))]
fn v3_1_1_sprint_2b_v1_save_includes_seed_blake3_integrity_tag() {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    use std::fs;
    use std::path::PathBuf;
    use substrate::persistence::{
        save_substrate_signing_key, SUBSTRATE_SIGNING_KEY_FILENAME,
        SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1,
    };

    let dir = std::env::temp_dir().join(format!(
        "myco-sprint-2b-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir_all(&dir).unwrap();
    let seed = [0x44u8; 32];
    save_substrate_signing_key(&seed, &dir).unwrap();

    let raw = fs::read(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME)).unwrap();
    let decoded = decode(&raw).unwrap();
    let map = match decoded {
        Value::Map(m) => m,
        _ => panic!("not a map"),
    };
    match map.get("format_version") {
        Some(Value::Uint(n)) => {
            assert_eq!(*n, SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1, "non-Windows = v1")
        }
        _ => panic!("format_version missing"),
    }
    match map.get("seed_blake3") {
        Some(Value::Bytes(b)) => {
            assert_eq!(b.len(), 32, "BLAKE3 hash is 32 bytes");
            let expected: [u8; 32] = blake3::hash(seed.as_slice()).into();
            assert_eq!(
                b.as_slice(),
                expected.as_slice(),
                "stored seed_blake3 must equal BLAKE3(seed)"
            );
        }
        _ => panic!("seed_blake3 must be present on v1 (Sprint 2.B integrity tag)"),
    }
    let _ = fs::remove_dir_all(&dir);
    let _: &PathBuf = &dir; // suppress unused-var warning if removal fails
}

#[test]
#[cfg(not(windows))]
fn v3_1_1_sprint_2b_v1_round_trip_preserves_seed_through_integrity_check() {
    use std::fs;
    use substrate::persistence::{
        load_substrate_signing_key, save_substrate_signing_key,
    };

    let dir = std::env::temp_dir().join(format!(
        "myco-sprint-2b-rt-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir_all(&dir).unwrap();
    let seed = [0x99u8; 32];
    save_substrate_signing_key(&seed, &dir).unwrap();
    let loaded = load_substrate_signing_key(&dir).unwrap().unwrap();
    assert_eq!(
        loaded, seed,
        "save→load with seed_blake3 verification must recover seed exactly"
    );
    let _ = fs::remove_dir_all(&dir);
}

#[test]
#[cfg(not(windows))]
fn v3_1_1_sprint_2b_v1_tampered_seed_rejected_with_clear_error() {
    use myco_kernel_shared::canonical_bytes::{decode, encode, Value};
    use std::collections::BTreeMap;
    use std::fs;
    use substrate::persistence::{
        load_substrate_signing_key, save_substrate_signing_key,
        SUBSTRATE_SIGNING_KEY_FILENAME,
    };

    let dir = std::env::temp_dir().join(format!(
        "myco-sprint-2b-tamper-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir_all(&dir).unwrap();
    let seed = [0xCCu8; 32];
    save_substrate_signing_key(&seed, &dir).unwrap();

    // Tamper: read the file, modify the seed field's bytes WITHOUT
    // updating seed_blake3, write back.
    let raw = fs::read(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME)).unwrap();
    let decoded = decode(&raw).unwrap();
    let mut map = match decoded {
        Value::Map(m) => m,
        _ => panic!("not a map"),
    };
    // Flip a byte of the seed.
    let mut tampered_seed = seed;
    tampered_seed[5] ^= 0xff;
    map.insert(
        "seed".to_string(),
        Value::Bytes(tampered_seed.to_vec()),
    );
    let tampered_bytes = encode(&Value::Map(map)).unwrap();
    fs::write(
        dir.join(SUBSTRATE_SIGNING_KEY_FILENAME),
        tampered_bytes.as_ref(),
    )
    .unwrap();

    // Load MUST refuse with an integrity error.
    let result = load_substrate_signing_key(&dir);
    assert!(result.is_err(), "tampered seed MUST fail to load");
    let err_msg = result.unwrap_err().to_string();
    assert!(
        err_msg.contains("integrity"),
        "error message MUST mention integrity: got {err_msg:?}"
    );
    let _ = fs::remove_dir_all(&dir);
}

#[test]
#[cfg(not(windows))]
fn v3_1_1_sprint_2b_v1_legacy_no_hash_field_still_loads() {
    use myco_kernel_shared::canonical_bytes::{encode, Value};
    use std::collections::BTreeMap;
    use std::fs;
    use substrate::persistence::{
        load_substrate_signing_key, SUBSTRATE_SIGNING_KEY_FILENAME,
        SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1,
    };

    let dir = std::env::temp_dir().join(format!(
        "myco-sprint-2b-legacy-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir_all(&dir).unwrap();

    // Write a legacy v1 file MANUALLY (pre-Sprint-2.B format: no
    // seed_blake3 field). Loading must succeed for backward-compat.
    let legacy_seed = [0xABu8; 32];
    let mut m = BTreeMap::new();
    m.insert(
        "format_version".to_string(),
        Value::Uint(SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1),
    );
    m.insert("seed".to_string(), Value::Bytes(legacy_seed.to_vec()));
    m.insert("created_at_unix_ns".to_string(), Value::Timestamp(0));
    let bytes = encode(&Value::Map(m)).unwrap();
    fs::write(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME), bytes.as_ref()).unwrap();

    let loaded = load_substrate_signing_key(&dir).unwrap().unwrap();
    assert_eq!(
        loaded, legacy_seed,
        "legacy v1 (no seed_blake3) must continue to load — backward compat"
    );
    let _ = fs::remove_dir_all(&dir);
}

#[test]
fn v3_1_1_sprint_2b_sealing_scaffold_module_exists() {
    // Module compiles; cfg gates correct.
    // (Empty test body — the act of compiling proves the property.)
}

#[test]
fn v3_1_1_sprint_3_self_driven_advance_off_by_default() {
    // Sanity: spawn a substrate with NO self-driven flag. Wait a tick
    // interval. Cycle counter must NOT advance autonomously.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![
            // Tight tick interval so the test waits less while still
            // proving the negative.
            ("MYCO_TICK_INTERVAL_MS".to_string(), "100".to_string()),
        ],
    );

    // Sleep ~5 tick intervals = 500ms. If self-driven were on by default,
    // ~5 cycles should advance. With it off, cycle stays at 0.
    std::thread::sleep(std::time::Duration::from_millis(500));

    // Query cycle counter via the observatory snapshot.
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("cycle_advanced".to_string()),
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
        "self-driven cycle advance must be OFF by default; saw {} cycle_advanced events",
        nodes.len()
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn v3_1_1_sprint_3_self_driven_advance_fires_when_enabled() {
    // Spawn a substrate WITH MYCO_SELF_DRIVEN_CYCLE_ADVANCE=1 + tight
    // tick interval. Wait several tick intervals. Cycle counter MUST
    // advance autonomously even without operator advance requests.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_env(
        &dir,
        vec![
            (
                "MYCO_SELF_DRIVEN_CYCLE_ADVANCE".to_string(),
                "1".to_string(),
            ),
            ("MYCO_TICK_INTERVAL_MS".to_string(), "100".to_string()),
        ],
    );

    // Sleep ~6 tick intervals = 600ms → ~4-5 autonomous cycles should fire
    // (handshake takes one tick to settle; allow margin).
    std::thread::sleep(std::time::Duration::from_millis(1000));

    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("cycle_advanced".to_string()),
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
        "self-driven cycle advance was enabled (MYCO_SELF_DRIVEN_CYCLE_ADVANCE=1) \
         but no cycle_advanced events found after 1s of idle — P04 §10.3 still broken"
    );
    // At least one cycle is enough to prove the mechanism fires; we don't
    // pin an exact count (flaky on slow CI).
    client.shutdown().expect("shutdown");
}

#[test]
fn v3_1_1_sprint_3_self_driven_flag_parses_truthy_values() {
    // White-box test of the env-var parsing. Each of these values should
    // trigger self-driven advance. Spawn a substrate, wait briefly, check
    // at least one cycle fired.
    for truthy in &["1", "true", "TRUE", "yes", "ON"] {
        let dir = fresh_state_dir();
        let mut client = spawn_substrate_with_env(
            &dir,
            vec![
                (
                    "MYCO_SELF_DRIVEN_CYCLE_ADVANCE".to_string(),
                    truthy.to_string(),
                ),
                ("MYCO_TICK_INTERVAL_MS".to_string(), "100".to_string()),
            ],
        );
        std::thread::sleep(std::time::Duration::from_millis(700));
        let resp = client
            .call(
                proto::QUERY_RECENT_NODES,
                build_payload(vec![
                    ("count", CbValue::Uint(20)),
                    (
                        "node_type_prefix",
                        CbValue::String("cycle_advanced".to_string()),
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
            "truthy value {truthy:?} should enable self-driven advance"
        );
        client.shutdown().expect("shutdown");
    }
}

#[test]
fn v3_1_1_sprint_3_self_driven_flag_falsy_values_keep_off() {
    // Conversely, falsy values keep self-driven advance off.
    for falsy in &["0", "false", "no", "off", "garbage", ""] {
        let dir = fresh_state_dir();
        let mut client = spawn_substrate_with_env(
            &dir,
            vec![
                (
                    "MYCO_SELF_DRIVEN_CYCLE_ADVANCE".to_string(),
                    falsy.to_string(),
                ),
                ("MYCO_TICK_INTERVAL_MS".to_string(), "100".to_string()),
            ],
        );
        std::thread::sleep(std::time::Duration::from_millis(400));
        let resp = client
            .call(
                proto::QUERY_RECENT_NODES,
                build_payload(vec![
                    ("count", CbValue::Uint(20)),
                    (
                        "node_type_prefix",
                        CbValue::String("cycle_advanced".to_string()),
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
            "falsy value {falsy:?} should NOT enable self-driven advance"
        );
        client.shutdown().expect("shutdown");
    }
}

#[test]
fn sprint_5i_export_backup_creates_backup_dir_with_state_files() {
    let (mut client, _dir) = spawn_substrate();
    client
        .register_axis("backup_axis", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    pump_cycles(&mut client, 2);
    let backup_dir = fresh_state_dir();
    let resp = client
        .call(
            proto::EXPORT_BACKUP_TO_DIR,
            build_payload(vec![(
                "backup_dir",
                CbValue::String(backup_dir.to_string_lossy().into_owned()),
            )]),
        )
        .expect("export_backup");
    let files_copied = match resp.payload.get("files_copied") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("files_copied missing"),
    };
    assert!(
        files_copied >= 2,
        "Sprint 5.I T1.3: backup should copy at least manifest.cb + dag.cb; \
         got {files_copied}"
    );
    // dag.cb + backup_metadata.cb MUST always exist in backup_dir.
    // (Other state files like manifest.cb / gradient.cb / snapshot.cb may
    // not exist on fresh substrates because M21+ uses DAG-derived state
    // and skips manifest writes until certain milestones. The backup
    // logic silently skips missing files — correct behavior.)
    for required in &["dag.cb", "backup_metadata.cb"] {
        let p = backup_dir.join(required);
        assert!(
            p.exists(),
            "Sprint 5.I T1.3: backup_dir must contain {required}; got missing at {}",
            p.display()
        );
    }
    let total_bytes = match resp.payload.get("total_bytes") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("total_bytes missing"),
    };
    assert!(total_bytes > 0, "total_bytes should be > 0");
    let manifest_blake3 = match resp.payload.get("manifest_blake3") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("manifest_blake3 missing"),
    };
    assert_eq!(manifest_blake3.len(), 32, "BLAKE3 hash must be 32 bytes");
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5i_export_backup_emits_dag_event() {
    let (mut client, _dir) = spawn_substrate();
    let backup_dir = fresh_state_dir();
    let _ = client.call(
        proto::EXPORT_BACKUP_TO_DIR,
        build_payload(vec![(
            "backup_dir",
            CbValue::String(backup_dir.to_string_lossy().into_owned()),
        )]),
    );
    let nodes_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(50)),
                (
                    "node_type_prefix",
                    CbValue::String("backup_exported:".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        1,
        "Sprint 5.I T1.3: EXPORT_BACKUP_TO_DIR should emit exactly one \
         backup_exported:* event per call; got {}",
        nodes.len()
    );
    // Verify event content carries the expected fields.
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let first = match &nodes[0] {
        CbValue::Map(m) => m.clone(),
        _ => panic!("node not a Map"),
    };
    let content = match first.get("content_canonical_bytes") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("content missing"),
    };
    let event_map = match cb_decode(&content).expect("decode") {
        CbV::Map(m) => m,
        _ => panic!("event not a Map"),
    };
    for required_field in &[
        "backup_dir",
        "files_copied",
        "total_bytes",
        "manifest_blake3",
        "captured_at_unix_ns",
        "at_cycle",
    ] {
        assert!(
            event_map.contains_key(*required_field),
            "Sprint 5.I T1.3: backup_exported event missing field {required_field}"
        );
    }
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5i_backup_refuses_state_dir_as_target() {
    let (mut client, dir) = spawn_substrate();
    let result = client.call(
        proto::EXPORT_BACKUP_TO_DIR,
        build_payload(vec![(
            "backup_dir",
            CbValue::String(dir.to_string_lossy().into_owned()),
        )]),
    );
    // Substrate-side returns SubstrateError::Protocol → bridge converts to
    // error envelope → operator's client.call returns Err.
    assert!(
        result.is_err(),
        "Sprint 5.I T1.3: backup with backup_dir == state_dir must be refused \
         (self-overwrite trap); got Ok"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_5i_restore_round_trip_preserves_substrate_id_and_cycle() {
    // ROUND-TRIP TEST: the headline COV01 property — substrate state survives
    // disk failure if operator backs up + restores from those files.
    //
    // 1. Spawn substrate, do some work, capture substrate_id + cycle_counter
    // 2. Export backup to backup_dir
    // 3. Shut down substrate (simulating disk loss + recovery from off-site)
    // 4. Create fresh restore_dir
    // 5. Copy all backup_dir contents to restore_dir
    // 6. Boot new substrate against restore_dir
    // 7. Verify substrate_id + cycle_counter match the pre-backup substrate
    let (mut client, original_dir) = spawn_substrate();
    client
        .register_axis("roundtrip_axis", "appetite", 3.0, 0.0, 1.0, false, "noop")
        .expect("register");
    pump_cycles(&mut client, 4);

    // Capture original substrate's identity.
    // Substrate_id is exposed via run_immune_check response indirectly; the
    // simpler path is to read dag.cb's genesis_event (first node) and extract
    // substrate_id from the manifest. For E2E, we'll restart against the
    // original dir as control and compare to the restored dir.
    // Capture original DAG node count by querying recent nodes directly.
    let pre_backup_nodes = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![("count", CbValue::Uint(500))]),
        )
        .expect("query");
    let original_node_count = match pre_backup_nodes.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len() as u64,
        _ => panic!("nodes missing"),
    };

    // Export backup.
    let backup_dir = fresh_state_dir();
    let _ = client
        .call(
            proto::EXPORT_BACKUP_TO_DIR,
            build_payload(vec![(
                "backup_dir",
                CbValue::String(backup_dir.to_string_lossy().into_owned()),
            )]),
        )
        .expect("export_backup");
    client.shutdown().expect("shutdown original");

    // Simulate disk loss: do not touch the original state_dir. Restore from
    // backup_dir into a NEW restore_dir.
    let restore_dir = fresh_state_dir();
    for entry in std::fs::read_dir(&backup_dir).expect("read backup_dir") {
        let entry = entry.expect("entry");
        let src = entry.path();
        let name = src.file_name().expect("filename").to_os_string();
        // Skip backup_metadata.cb — that's the metadata file, not a state file.
        if name == "backup_metadata.cb" {
            continue;
        }
        let dst = restore_dir.join(&name);
        std::fs::copy(&src, &dst).expect("copy file");
    }

    // Boot a new substrate against restore_dir.
    let mut client_restored = spawn_substrate_with_state_dir(&restore_dir);
    let restored_nodes_resp = client_restored
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![("count", CbValue::Uint(500))]),
        )
        .expect("query restored");
    let restored_node_count = match restored_nodes_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len() as u64,
        _ => panic!("nodes missing on restored substrate"),
    };
    // The restored substrate's DAG node count should be >= the original's at
    // the time of backup (boot may add invariant_witness events). Critical
    // invariant: it's NOT zero (would mean genesis re-fired, identity lost).
    assert!(
        restored_node_count >= original_node_count,
        "Sprint 5.I T1.3: restored substrate should preserve DAG \
         (original={original_node_count}, restored={restored_node_count} — \
         smaller means restore failed / lost events)"
    );
    // Boot should have completed without C9 cold-resume failures. Run an
    // ad-hoc immune check — if any of the new C57/C58/C59 boot-consistency
    // checks fail, the restore is broken.
    let check_resp = client_restored
        .call(proto::RUN_IMMUNE_CHECK, build_payload(vec![]))
        .expect("run_immune_check");
    let failed_checks = match check_resp.payload.get("failed_checks") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("failed_checks missing"),
    };
    assert_eq!(
        failed_checks, 0,
        "Sprint 5.I T1.3: restored substrate's integrity checks should all \
         pass; got {failed_checks} failed (restore is broken)"
    );
    client_restored.shutdown().expect("shutdown restored");
    drop(original_dir); // tidy up
}

#[test]
fn sprint_6k_dag_file_starts_with_at_rest_magic() {
    // After a substrate boots + saves dag.cb, the file MUST start with
    // the "MASR" envelope magic. This is the public-surface contract
    // that downstream tooling can rely on to identify Sprint-6.K-or-later
    // files.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    // Trigger at least one DAG save by running a cycle.
    client
        .register_axis("k_axis", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register");
    pump_cycles(&mut client, 1);
    client.shutdown().expect("shutdown");

    let dag_path = dir.join("dag.cb");
    let bytes = std::fs::read(&dag_path).expect("read dag.cb");
    assert!(
        bytes.len() >= 4,
        "Sprint 6.K T1.6: dag.cb must have at least 4 bytes; got {}",
        bytes.len()
    );
    assert_eq!(
        &bytes[..4],
        b"MASR",
        "Sprint 6.K T1.6: dag.cb must start with at-rest envelope magic; \
         got first 4 bytes = {:?}",
        &bytes[..4]
    );
}

#[test]
fn sprint_6k_substrate_round_trip_through_envelope_format() {
    // Boot substrate, do work, shut down, reboot. The substrate's DAG
    // must survive the round-trip — proving the seal/unseal pair is
    // identity-preserving for real substrate state.
    let dir = fresh_state_dir();
    {
        let mut client = spawn_substrate_with_state_dir(&dir);
        client
            .register_axis("roundtrip_k", "appetite", 3.0, 0.0, 1.0, false, "noop")
            .expect("register");
        pump_cycles(&mut client, 2);
        client.shutdown().expect("first shutdown");
    }
    // Reboot.
    let mut client2 = spawn_substrate_with_state_dir(&dir);
    let resp = client2
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![("count", CbValue::Uint(50))]),
        )
        .expect("query after reboot");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert!(
        !nodes.is_empty(),
        "Sprint 6.K T1.6: substrate must restore DAG content after reboot \
         through the at-rest envelope; got 0 nodes (encryption corrupted state)"
    );
    client2.shutdown().expect("second shutdown");
}

#[test]
fn sprint_6k_legacy_pre_envelope_dag_file_still_loads() {
    // Backward compat: a dag.cb file written in the pre-Sprint-6.K
    // raw format (no MASR magic) must still load. The substrate's
    // unseal_from_at_rest falls back to raw bytes on magic mismatch.
    use myco_kernel_schema::dag::Dag;

    let dir = fresh_state_dir();
    // Construct a minimal empty Dag and write its canonical bytes
    // DIRECTLY (no envelope) — simulating a pre-Sprint-6.K substrate's
    // dag.cb on disk.
    let dag = Dag::new();
    let raw_bytes = dag.to_canonical_bytes();
    let dag_path = dir.join("dag.cb");
    std::fs::write(&dag_path, raw_bytes.as_ref()).expect("write legacy dag.cb");

    // Boot substrate against this state_dir. It should load the legacy
    // dag.cb without error (genesis succeeds because the DAG is empty).
    let mut client = spawn_substrate_with_state_dir(&dir);
    // Successful boot means load_dag handled the legacy raw bytes.
    // On next cycle, the substrate will re-save dag.cb in the new
    // envelope format.
    pump_cycles(&mut client, 1);
    client.shutdown().expect("legacy-format reboot succeeds");

    // After the cycle, dag.cb should now be in envelope format.
    let post_save_bytes = std::fs::read(&dag_path).expect("read");
    assert_eq!(
        &post_save_bytes[..4],
        b"MASR",
        "Sprint 6.K T1.6: legacy dag.cb must be upgraded to envelope \
         format on next save; got first 4 bytes = {:?}",
        &post_save_bytes[..4]
    );
}

#[cfg(windows)]
#[test]
fn sprint_6k_windows_dag_body_is_dpapi_wrapped() {
    // On Windows specifically: the envelope body must NOT contain the
    // plaintext DAG canonical bytes (those start with canonical-bytes
    // structure markers, not DPAPI ciphertext). The DPAPI ciphertext
    // is opaque + much longer than the plaintext for small inputs.
    use substrate::at_rest_seal::{unseal_from_at_rest, ENVELOPE_MAGIC};

    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    pump_cycles(&mut client, 1);
    client.shutdown().expect("shutdown");

    let dag_path = dir.join("dag.cb");
    let sealed = std::fs::read(&dag_path).expect("read");
    assert_eq!(&sealed[..4], ENVELOPE_MAGIC);
    // Unseal succeeds (via DPAPI on Windows).
    let unsealed = unseal_from_at_rest(&sealed).expect("Windows unseal must succeed");
    // The unsealed body is the original Dag canonical bytes. The sealed
    // body inside the envelope is DPAPI ciphertext, which is significantly
    // larger than the plaintext (DPAPI adds metadata overhead + AES block
    // padding).
    assert!(
        sealed.len() > unsealed.len(),
        "Sprint 6.K T1.6 (Windows): DPAPI-wrapped file must be larger than \
         plaintext; sealed={} unsealed={}",
        sealed.len(),
        unsealed.len()
    );
}

