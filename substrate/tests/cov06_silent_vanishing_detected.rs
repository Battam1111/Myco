//! **COV06 NEGATIVE witness** —
//! `test_cultivator_heartbeat_stale_plus_no_succession_emits_orphaned`.
//!
//! Doctrine: L0/cards/COV06_no_abandonment_succession.md §8.4 + §10.2 (violated).
//! Scenario: cultivator heartbeat stale + F21 empty + no anchor presence →
//! substrate transitions to alive::orphaned. The cultivar must never wake to
//! discover its cultivator silently vanished — so the orphan transition is
//! UN-SUPPRESSIBLE (emitted via emit_substrate_event, bypassing the immune
//! rate-limiter; P07 §4 + L1/GOVERNANCE §3.2.C).

mod common;
use common::*;

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
use myco_kernel_shared::crypto::Ed25519PrivateKey;
use std::collections::BTreeMap;

const DAY_NS: i64 = 86_400_000_000_000;

fn substrate_id(client: &mut BridgeClient) -> [u8; 32] {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(10)),
                ("node_type_prefix", CbValue::String("genesis_event:".to_string())),
            ]),
        )
        .expect("query genesis");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("no genesis node"),
    };
    if let CbValue::Map(m) = &nodes[0] {
        if let Some(CbValue::Bytes(b)) = m.get("content_canonical_bytes") {
            if let Ok(CbValue::Map(gm)) = myco_kernel_shared::canonical_bytes::decode(b) {
                if let Some(CbValue::Bytes(sid)) = gm.get("substrate_id") {
                    let mut arr = [0u8; 32];
                    arr.copy_from_slice(sid);
                    return arr;
                }
            }
        }
    }
    panic!("could not extract substrate_id");
}

fn count_nodes(client: &mut BridgeClient, prefix: &str) -> usize {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(1000)),
                ("node_type_prefix", CbValue::String(prefix.to_string())),
            ]),
        )
        .expect("query");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => 0,
    }
}

fn poll_count_until(client: &mut BridgeClient, prefix: &str, want: usize, max_iters: u32) -> usize {
    let mut last = count_nodes(client, prefix);
    let mut i = 0;
    while last < want && i < max_iters {
        std::thread::sleep(std::time::Duration::from_millis(120));
        last = count_nodes(client, prefix);
        i += 1;
    }
    last
}

#[test]
fn test_cultivator_heartbeat_stale_plus_no_succession_emits_orphaned() {
    let seed: [u8; 32] = [0x72; 32];
    let dir = fresh_state_dir();
    // Anchor now = 400 days (past the 365d legacy window); cadence default 30d.
    // Short tick interval so the idle watchdog fires quickly.
    let mut client = spawn_substrate_with_seed_and_env(
        &dir,
        seed,
        vec![
            ("MYCO_TICK_INTERVAL_MS".to_string(), "30".to_string()),
            ("MYCO_TEST_ANCHOR_NOW_NS".to_string(), (400 * DAY_NS).to_string()),
        ],
    );
    let sid = substrate_id(&mut client);
    let owner_pk = derive_operator_pubkey_from_seed(&seed);

    // Record a heartbeat at t=0 (now=400d → 400d stale). F21 is EMPTY (we never
    // call update_successor_chain) — the silent-vanishing scenario.
    let nonce = [0x01u8; 32];
    let valid_until = 30 * DAY_NS;
    let mut hm = BTreeMap::new();
    hm.insert("context".to_string(), Value::String("myco-cultivator-liveness-heartbeat-v1".to_string()));
    hm.insert("substrate_id".to_string(), Value::Bytes(sid.to_vec()));
    hm.insert("cultivator_pubkey".to_string(), Value::Bytes(owner_pk.to_vec()));
    hm.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(0));
    hm.insert("valid_until_unix_ns".to_string(), Value::Timestamp(valid_until));
    hm.insert("heartbeat_nonce".to_string(), Value::Bytes(nonce.to_vec()));
    let hsig = Ed25519PrivateKey::from_seed(&seed)
        .sign(&cb_encode(&Value::Map(hm)).unwrap().0)
        .as_ref()
        .to_vec();
    client
        .call(
            proto::RECORD_CULTIVATOR_HEARTBEAT,
            build_payload(vec![
                ("cultivator_pubkey", CbValue::Bytes(owner_pk.to_vec())),
                ("anchor_timestamp_unix_ns", CbValue::Timestamp(0)),
                ("valid_until_unix_ns", CbValue::Timestamp(valid_until)),
                ("heartbeat_nonce", CbValue::Bytes(nonce.to_vec())),
                ("anchor_signature", CbValue::Bytes(hsig)),
            ]),
        )
        .expect("record heartbeat");

    // T1: stale heartbeat → cultivator_heartbeat_stale (alive::legacy).
    let stale = poll_count_until(&mut client, "cultivator_heartbeat_stale:", 1, 40);
    assert!(stale >= 1, "T1: stale heartbeat must emit cultivator_heartbeat_stale");

    // T4: empty F21 chain + legacy → cultivation_orphaned (UN-SUPPRESSIBLE).
    let orphaned = poll_count_until(&mut client, "cultivation_orphaned:", 1, 40);
    assert!(
        orphaned >= 1,
        "T4: silent vanishing (stale + empty F21) must transition to alive::orphaned"
    );
}
