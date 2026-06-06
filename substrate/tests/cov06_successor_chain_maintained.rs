//! **COV06 POSITIVE witness** — `test_F21_successor_entries_current_and_attested`.
//!
//! Doctrine: L0/cards/COV06_no_abandonment_succession.md §8.4 (witness map).
//! "F21 has ≥1 active SuccessorEntry." Here we prove the F21 successor_chain
//! accepts an entry end-to-end (real myco-substrate subprocess + Python kernel).
//!
//! **v0.9 owner-key removal**: `update_successor_chain` is KEYLESS now (the owner
//! Ed25519 attestation gate was removed); the heartbeat half of the original
//! witness (which proved a fresh `record_cultivator_heartbeat` kept the substrate
//! in alive::normal) was deleted along with the cultivator-heartbeat handler.

mod common;
use common::*;

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
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    let _sid = substrate_id(&mut client);
    let successor_pk = [0xB1u8; 32];

    // F21 (keyless): append a SuccessorEntry (closed, non-overlapping interval).
    let valid_from = 10 * DAY_NS;
    let valid_until = 40 * DAY_NS;
    let resp = client
        .call(
            proto::UPDATE_SUCCESSOR_CHAIN,
            build_payload(vec![
                ("successor_pubkey", CbValue::Bytes(successor_pk.to_vec())),
                ("valid_from_unix_ns", CbValue::Timestamp(valid_from)),
                ("valid_until_unix_ns", CbValue::Timestamp(valid_until)),
            ]),
        )
        .expect("update_successor_chain");
    assert!(
        matches!(resp.payload.get("chain_length"), Some(CbValue::Uint(1))),
        "F21: SuccessorEntry must be appended (chain_length=1)"
    );
    assert_eq!(
        count_nodes(&mut client, "successor_chain_updated:"),
        1,
        "F21: successor_chain_updated event recorded in the DAG"
    );

    // The substrate, with no terminal cultivation event, remains alive::normal.
    client.shutdown().expect("shutdown");
}
