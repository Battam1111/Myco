//! **COV06 EDGE witness** — `test_F21_activation_requires_layer_d_catechumenate`.
//!
//! Doctrine: L0/cards/COV06_no_abandonment_succession.md §8.4 + §5.3 + §10.2.
//! Boundary: a successor F21 activation attempt WITHOUT ≥50 dual-signed Layer-D
//! Catechumenate sessions → owner_succession_bypass (C46). This is the
//! un-fabricable production gate: synthetic tests pass a count directly
//! (49 → C46 refusal; 50 → proceeds), but a real successor must accumulate 50
//! real dual-signed sessions before activation. META §6.3 floor is operational.

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

/// Record a STALE heartbeat (so the C12 fresh-heartbeat gate does not pre-empt
/// the C46 catechumenate-floor gate we are testing).
fn record_stale_heartbeat(client: &mut BridgeClient, seed: &[u8; 32], sid: &[u8; 32], owner_pk: &[u8; 32]) {
    let nonce = [0x01u8; 32];
    let valid_until = 30 * DAY_NS;
    let mut hm = BTreeMap::new();
    hm.insert("context".to_string(), Value::String("myco-cultivator-liveness-heartbeat-v1".to_string()));
    hm.insert("substrate_id".to_string(), Value::Bytes(sid.to_vec()));
    hm.insert("cultivator_pubkey".to_string(), Value::Bytes(owner_pk.to_vec()));
    hm.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(0));
    hm.insert("valid_until_unix_ns".to_string(), Value::Timestamp(valid_until));
    hm.insert("heartbeat_nonce".to_string(), Value::Bytes(nonce.to_vec()));
    let hsig = Ed25519PrivateKey::from_seed(seed)
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
}

fn try_accept_succession(
    client: &mut BridgeClient,
    successor_seed: &[u8; 32],
    sid: &[u8; 32],
    prior_pk: &[u8; 32],
    anchor_ts: i64,
    session_count: u64,
) -> Result<(), String> {
    let succ_pk = Ed25519PrivateKey::from_seed(successor_seed).public_key().0;
    let mut m = BTreeMap::new();
    m.insert("context".to_string(), Value::String("myco-succession-acceptance-v1".to_string()));
    m.insert("substrate_id".to_string(), Value::Bytes(sid.to_vec()));
    m.insert("successor_pubkey".to_string(), Value::Bytes(succ_pk.to_vec()));
    m.insert("prior_cultivator_pubkey".to_string(), Value::Bytes(prior_pk.to_vec()));
    m.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(anchor_ts));
    let sig = Ed25519PrivateKey::from_seed(successor_seed)
        .sign(&cb_encode(&Value::Map(m)).unwrap().0)
        .as_ref()
        .to_vec();
    client
        .call(
            proto::ACCEPT_SUCCESSION,
            build_payload(vec![
                ("successor_pubkey", CbValue::Bytes(succ_pk.to_vec())),
                ("prior_cultivator_pubkey", CbValue::Bytes(prior_pk.to_vec())),
                ("anchor_timestamp_unix_ns", CbValue::Timestamp(anchor_ts)),
                ("successor_signature", CbValue::Bytes(sig)),
                ("catechumenate_session_count", CbValue::Uint(session_count)),
            ]),
        )
        .map(|_| ())
        .map_err(|e| e.to_string())
}

#[test]
fn test_F21_activation_requires_layer_d_catechumenate() {
    let seed: [u8; 32] = [0x73; 32];
    let successor_seed: [u8; 32] = [0xC3; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_seed_and_env(
        &dir,
        seed,
        vec![("MYCO_TEST_ANCHOR_NOW_NS".to_string(), (100 * DAY_NS).to_string())],
    );
    let sid = substrate_id(&mut client);
    let owner_pk = derive_operator_pubkey_from_seed(&seed);

    // Stale heartbeat → incapacity (so C12 does not pre-empt; C46 is what we test).
    record_stale_heartbeat(&mut client, &seed, &sid, &owner_pk);

    // BELOW the floor: 49 dual-signed sessions → C46 owner_succession_bypass.
    let below = try_accept_succession(&mut client, &successor_seed, &sid, &owner_pk, 100 * DAY_NS, 49);
    assert!(below.is_err(), "49 sessions < 50 → succession MUST be refused (C46)");
    assert_eq!(
        count_nodes(&mut client, "succession_completed:"),
        0,
        "no succession_completed event when below the catechumenate floor"
    );
    assert!(
        count_nodes(&mut client, "immune:") >= 1,
        "C46 owner_succession_bypass immune sporocarp emitted"
    );

    // AT the floor: 50 dual-signed sessions → succession proceeds.
    let at = try_accept_succession(&mut client, &successor_seed, &sid, &owner_pk, 101 * DAY_NS, 50);
    assert!(at.is_ok(), "50 sessions ≥ 50 → succession proceeds: {at:?}");
    assert_eq!(
        count_nodes(&mut client, "succession_completed:"),
        1,
        "META §6.3 floor is operational: 50 sessions activates F21 succession"
    );
}
