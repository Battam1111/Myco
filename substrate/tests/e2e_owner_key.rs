//! E2E: Owner-key rotation: CI classification of owner_key_history mutations, attestation-gate rejection, Sprint 7.F rotate-owner-key envelope encode/decode, pinned node-type constants, and the acknowledged rotation-FSM debt witness.
//!
//! Split out of the former monolithic `substrate_e2e.rs`. Shared spawn /
//! build helpers live in `tests/common/mod.rs`; this binary pulls them in
//! via `use common::*`. Tests are preserved verbatim from the original file.

mod common;
use common::*;

#[test]
fn sprint_6f_owner_key_history_mutation_classifies_as_ci() {
    // L1/GOVERNANCE §3.1 + classifier.py:135-144: mutations touching
    // owner_key_history field are CI-class. Verify the classifier path
    // returns contract_identity_level classification.
    let (mut client, _dir) = spawn_substrate();
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("rotate_owner_key".to_string())),
                (
                    "content_canonical_bytes",
                    CbValue::Bytes(b"rotation_envelope_stub".to_vec()),
                ),
                (
                    "touched_fields",
                    CbValue::Array(vec![CbValue::String("owner_key_history".to_string())]),
                ),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit_mutation");
    let classification = match resp.payload.get("classification") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("classification missing"),
    };
    assert_eq!(
        classification, "contract_identity_level",
        "Sprint 6.F T2.7: touched_fields=owner_key_history must classify as CI; \
         got {classification:?}"
    );
    let accepted = match resp.payload.get("accepted") {
        Some(CbValue::Bool(b)) => *b,
        _ => panic!("accepted missing"),
    };
    assert!(
        !accepted,
        "Sprint 6.F T2.7: CI mutation without attestation must be rejected; \
         got accepted=true (would silently rotate owner key without consent)"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn sprint_7f_rotate_owner_key_canonical_bytes_roundtrips() {
    use substrate::events::{
        build_rotate_owner_key_canonical_bytes, decode_rotate_owner_key,
        ROTATE_OWNER_KEY_DOMAIN,
    };
    let prior = [0x11u8; 32];
    let new_pk = [0x22u8; 32];
    let ts: u64 = 1_700_000_000;
    let nonce = [0x33u8; 32];

    let bytes = build_rotate_owner_key_canonical_bytes(&prior, &new_pk, ts, &nonce);
    let (p, n, t, no) = decode_rotate_owner_key(&bytes).expect("roundtrip");
    assert_eq!(p, prior);
    assert_eq!(n, new_pk);
    assert_eq!(t, ts);
    assert_eq!(no, nonce);
    // Domain constant pinned.
    assert_eq!(ROTATE_OWNER_KEY_DOMAIN, "rotate_owner_key_v1");
}

#[test]
fn sprint_7f_rotate_owner_key_decode_rejects_wrong_domain() {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use substrate::events::decode_rotate_owner_key;
    // Build canonical-bytes with wrong domain.
    let mut m = std::collections::BTreeMap::new();
    m.insert("domain".to_string(), Value::String("not_rotate".to_string()));
    m.insert(
        "prior_active_pubkey".to_string(),
        Value::Bytes(vec![0u8; 32]),
    );
    m.insert("new_pubkey".to_string(), Value::Bytes(vec![0u8; 32]));
    m.insert("anchor_timestamp_unix_seconds".to_string(), Value::Uint(0));
    m.insert("anchor_nonce".to_string(), Value::Bytes(vec![0u8; 32]));
    let bytes = cb_encode(&Value::Map(m)).expect("encode").0;
    assert!(
        decode_rotate_owner_key(&bytes).is_none(),
        "Sprint 7.F T4.2: wrong-domain envelope must be rejected"
    );
}

#[test]
fn sprint_7f_rotate_owner_key_decode_rejects_malformed() {
    use substrate::events::decode_rotate_owner_key;
    assert!(decode_rotate_owner_key(b"garbage").is_none());
    assert!(decode_rotate_owner_key(b"").is_none());
}

#[test]
fn sprint_6f_owner_key_event_node_type_constants_pinned() {
    // The `owner_key_added` / `owner_key_archived` constants exist in
    // events.rs even though no substrate-side path emits them yet. Pin
    // the values so when Sprint 6.F.2 implementation lands, the wire
    // format is locked.
    use substrate::events::{NODE_TYPE_OWNER_KEY_ADDED, NODE_TYPE_OWNER_KEY_ARCHIVED};
    assert_eq!(NODE_TYPE_OWNER_KEY_ADDED, "owner_key_added");
    assert_eq!(NODE_TYPE_OWNER_KEY_ARCHIVED, "owner_key_archived");
}

#[test]
fn sprint_6f_owner_key_rotation_e2e_acknowledged_debt() {
    // **Acknowledged-debt sentinel**: this test pins the current shipping
    // state — owner_key_added / owner_key_archived emission is NOT yet
    // wired into the substrate's CI mutation handler. Even after Sprint
    // 6.E provides operator-signing-seed infrastructure, the substrate
    // would not emit owner_key_added on an accepted CI mutation because
    // attestation.rs has no rotation-specific staging code.
    //
    // When Sprint 6.F.2 (full rotation FSM + emission) lands, this test
    // should FAIL: spawning a seeded substrate + verifying it works
    // baseline-correctly. The Sprint 6.F.2 implementer updates this
    // test to assert positive emission, and the rotation E2E becomes
    // a real positive witness.
    let seed: [u8; 32] = [0x55; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);

    // Currently: no owner_key_added events ever (because no rotation
    // mutation accepted in normal flow).
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(100)),
                (
                    "node_type_prefix",
                    CbValue::String("owner_key_added".to_string()),
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
        0,
        "Sprint 6.F T2.7 acknowledged-debt: pre-Sprint-6.F.2, no rotation \
         path emits owner_key_added. If this assertion starts failing, the \
         rotation FSM has been implemented — UPDATE THIS TEST to assert \
         positive emission instead (and convert the sentinel into a real \
         witness)."
    );
    client.shutdown().expect("shutdown");
}

