//! **COV06 POSITIVE witness** — `test_F21_successor_entries_current_and_attested`.
//!
//! Doctrine: L0/cards/COV06_no_abandonment_succession.md §8.4 (witness map).
//! "F21 has ≥1 active SuccessorEntry; heartbeat fresh; Layer D sessions
//! accumulating." Here we prove the F21 successor_chain accepts an attested
//! entry end-to-end (real myco-substrate subprocess + Python kernel), and that a
//! fresh heartbeat keeps the substrate in alive::normal.

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
                ("count", CbValue::Uint(500)),
                ("node_type_prefix", CbValue::String(prefix.to_string())),
            ]),
        )
        .expect("query");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => 0,
    }
}

#[test]
fn test_F21_successor_entries_current_and_attested() {
    let seed: [u8; 32] = [0x71; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);
    let sid = substrate_id(&mut client);
    let owner_pk = derive_operator_pubkey_from_seed(&seed);
    let successor_pk = [0xB1u8; 32];

    // F21: append an attested SuccessorEntry (closed, non-overlapping interval).
    let valid_from = 10 * DAY_NS;
    let valid_until = Some(40 * DAY_NS);
    let mut sm = BTreeMap::new();
    sm.insert("context".to_string(), Value::String("myco-successor-chain-entry-v1".to_string()));
    sm.insert("substrate_id".to_string(), Value::Bytes(sid.to_vec()));
    sm.insert("successor_pubkey".to_string(), Value::Bytes(successor_pk.to_vec()));
    sm.insert("valid_from_unix_ns".to_string(), Value::Timestamp(valid_from));
    sm.insert("valid_until_unix_ns".to_string(), Value::Timestamp(valid_until.unwrap()));
    let sig = Ed25519PrivateKey::from_seed(&seed)
        .sign(&cb_encode(&Value::Map(sm)).unwrap().0)
        .as_ref()
        .to_vec();
    let resp = client
        .call(
            proto::UPDATE_SUCCESSOR_CHAIN,
            build_payload(vec![
                ("successor_pubkey", CbValue::Bytes(successor_pk.to_vec())),
                ("valid_from_unix_ns", CbValue::Timestamp(valid_from)),
                ("valid_until_unix_ns", CbValue::Timestamp(valid_until.unwrap())),
                ("attestation_signature", CbValue::Bytes(sig)),
            ]),
        )
        .expect("update_successor_chain");
    assert!(
        matches!(resp.payload.get("chain_length"), Some(CbValue::Uint(1))),
        "F21: attested SuccessorEntry must be appended (chain_length=1)"
    );
    assert_eq!(
        count_nodes(&mut client, "successor_chain_updated:"),
        1,
        "F21: successor_chain_updated event recorded in the DAG"
    );

    // Fresh heartbeat keeps the substrate in alive::normal (positive presence).
    let anchor_ts = 50 * DAY_NS;
    let nonce = [0x01u8; 32];
    let valid_until_hb = anchor_ts + 30 * DAY_NS;
    let mut hm = BTreeMap::new();
    hm.insert("context".to_string(), Value::String("myco-cultivator-liveness-heartbeat-v1".to_string()));
    hm.insert("substrate_id".to_string(), Value::Bytes(sid.to_vec()));
    hm.insert("cultivator_pubkey".to_string(), Value::Bytes(owner_pk.to_vec()));
    hm.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(anchor_ts));
    hm.insert("valid_until_unix_ns".to_string(), Value::Timestamp(valid_until_hb));
    hm.insert("heartbeat_nonce".to_string(), Value::Bytes(nonce.to_vec()));
    let hsig = Ed25519PrivateKey::from_seed(&seed)
        .sign(&cb_encode(&Value::Map(hm)).unwrap().0)
        .as_ref()
        .to_vec();
    let hresp = client
        .call(
            proto::RECORD_CULTIVATOR_HEARTBEAT,
            build_payload(vec![
                ("cultivator_pubkey", CbValue::Bytes(owner_pk.to_vec())),
                ("anchor_timestamp_unix_ns", CbValue::Timestamp(anchor_ts)),
                ("valid_until_unix_ns", CbValue::Timestamp(valid_until_hb)),
                ("heartbeat_nonce", CbValue::Bytes(nonce.to_vec())),
                ("anchor_signature", CbValue::Bytes(hsig)),
            ]),
        )
        .expect("record_cultivator_heartbeat");
    assert!(
        matches!(
            hresp.payload.get("cultivation_state"),
            Some(CbValue::String(s)) if s == "alive::normal"
        ),
        "positive: fresh heartbeat + populated F21 chain → alive::normal"
    );
}
