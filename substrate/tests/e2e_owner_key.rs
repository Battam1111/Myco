//! E2E: Owner-key rotation: CI classification of owner_key_history mutations, attestation-gate rejection, rotate-owner-key envelope encode/decode, pinned node-type constants, and the **C70 rotation FSM** (request → 30d cooldown veto → dual-cosign activate; C70 on pre-cooldown activation).
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

// ---------------------------------------------------------------------------
// **C70 — owner key-rotation FSM** (L1/GOVERNANCE §3.1).
//
// request(current-key) → 30d cooldown (any pre-registered key may veto) →
// activate(dual-cosign old+new). Synthetic keys; anchor-time is the
// operator-supplied envelope timestamp (anchor-sig-verify is follow-up).
// ---------------------------------------------------------------------------

use myco_kernel_shared::crypto::Ed25519PrivateKey;
use substrate::events::OWNER_KEY_ROTATION_COOLDOWN_SECS as COOLDOWN;

/// The owner signing seed pinned on the substrate-under-test. The seed-derived
/// pubkey IS the pinned operator identity / genesis owner key.
const OWNER_SEED: [u8; 32] = [0x55; 32];
/// The new candidate key's seed (the key the rotation installs).
const NEW_SEED: [u8; 32] = [0x66; 32];
/// A request anchor timestamp (operator-supplied). Set far in the future
/// (~year 2100) so the rotation's activate timestamp is monotonic relative to
/// the genesis key's wall-clock `valid_from` (`int(time.time())` at boot) — the
/// owner_keys storage primitive enforces a non-decreasing `valid_from`, and in
/// production the real anchor clock is always at/ahead of "now". A fixed
/// past-relative-to-now constant would trip that invariant once wall-clock
/// passes it.
const REQUEST_TS: u64 = 4_100_000_000;
/// A fixed anchor nonce for the envelopes (the MVP does not consume it).
const NONCE: [u8; 32] = [0x77; 32];

fn pubkey(seed: &[u8; 32]) -> [u8; 32] {
    Ed25519PrivateKey::from_seed(seed).public_key().0
}

fn sign(seed: &[u8; 32], content: &[u8]) -> Vec<u8> {
    Ed25519PrivateKey::from_seed(seed).sign(content).as_ref().to_vec()
}

/// Submit a `rotate_owner_key` CI mutation. `body` is the phase envelope; the
/// owner `attestation_signature` is signed by `attest_seed` (Python's CI gate
/// verifies it against the active owner key). Returns the response payload.
fn submit_rotation(
    client: &mut BridgeClient,
    body: &[u8],
    attest_seed: &[u8; 32],
) -> std::collections::BTreeMap<String, CbValue> {
    client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("rotate_owner_key".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(body.to_vec())),
                (
                    "touched_fields",
                    CbValue::Array(vec![CbValue::String("owner_key_history".to_string())]),
                ),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                ("attestation_signature", CbValue::Bytes(sign(attest_seed, body))),
            ]),
        )
        .expect("submit rotation")
        .payload
}

/// Build + submit a rotation REQUEST (current owner signs). Returns the payload.
fn request_rotation(client: &mut BridgeClient) -> std::collections::BTreeMap<String, CbValue> {
    let body = substrate::events::build_rotate_owner_key_request(
        &pubkey(&OWNER_SEED),
        &pubkey(&NEW_SEED),
        REQUEST_TS,
        REQUEST_TS + COOLDOWN,
        &NONCE,
    );
    submit_rotation(client, &body, &OWNER_SEED)
}

/// Build + submit an ACTIVATE at `activate_ts`. The OLD key signs the full
/// envelope (attestation_signature); the NEW key co-signs the activate-core.
fn activate_rotation(
    client: &mut BridgeClient,
    activate_ts: u64,
) -> std::collections::BTreeMap<String, CbValue> {
    let prior = pubkey(&OWNER_SEED);
    let new_pk = pubkey(&NEW_SEED);
    let cooldown = REQUEST_TS + COOLDOWN;
    let core = substrate::events::build_rotate_owner_key_activate_core(
        &prior, &new_pk, REQUEST_TS, cooldown, activate_ts, &NONCE,
    );
    let mut cosig = [0u8; 64];
    cosig.copy_from_slice(&sign(&NEW_SEED, &core));
    let body = substrate::events::build_rotate_owner_key_activate(
        &prior, &new_pk, REQUEST_TS, cooldown, activate_ts, &NONCE, &cosig,
    );
    submit_rotation(client, &body, &OWNER_SEED)
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
        .expect("query recent");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => 0,
    }
}

fn accepted(payload: &std::collections::BTreeMap<String, CbValue>) -> bool {
    matches!(payload.get("accepted"), Some(CbValue::Bool(true)))
}

#[test]
fn c70_request_opens_cooldown_and_emits_requested_event() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);

    let resp = request_rotation(&mut client);
    assert!(
        accepted(&resp),
        "rotation request must be accepted; got {:?}",
        resp.get("rejection_reason")
    );
    assert_eq!(
        count_nodes(&mut client, "owner_key_rotation_requested"),
        1,
        "request must emit exactly one owner_key_rotation_requested event"
    );
    // The cooldown_expires_at in the emitted event must equal request_ts + 30d.
    let req_resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(10)),
                (
                    "node_type_prefix",
                    CbValue::String("owner_key_rotation_requested".to_string()),
                ),
            ]),
        )
        .expect("query");
    let nodes = match req_resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes"),
    };
    let content = match &nodes[0] {
        CbValue::Map(m) => match m.get("content_canonical_bytes") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("content"),
        },
        _ => panic!("node"),
    };
    let (_new, _prior, _rts, cooldown) =
        substrate::events::decode_owner_key_rotation_requested(&content).expect("decode");
    assert_eq!(cooldown, REQUEST_TS + COOLDOWN);

    // No owner_key_added yet (cooldown not elapsed, no activation).
    assert_eq!(count_nodes(&mut client, "owner_key_added"), 0);
    client.shutdown().expect("shutdown");
}

#[test]
fn c70_veto_within_window_clears_pending_no_owner_key_added() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);

    assert!(accepted(&request_rotation(&mut client)));

    // Veto within the window (the OLD/current key vetoes — Python verifies the
    // sig against current_active, which during cooldown is the old key).
    let veto_body = substrate::events::build_rotate_owner_key_veto(
        &pubkey(&NEW_SEED),
        REQUEST_TS + 1, // well within the window
        &NONCE,
    );
    let resp = submit_rotation(&mut client, &veto_body, &OWNER_SEED);
    assert!(
        accepted(&resp),
        "in-window veto must be accepted; got {:?}",
        resp.get("rejection_reason")
    );
    assert_eq!(count_nodes(&mut client, "owner_key_rotation_vetoed"), 1);
    // No key was added; the candidate is discarded.
    assert_eq!(count_nodes(&mut client, "owner_key_added"), 0);

    // Pending is cleared → a SECOND request now succeeds (single-in-flight
    // released by the veto).
    assert!(
        accepted(&request_rotation(&mut client)),
        "after veto, a fresh request must be allowed"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn c70_activate_before_cooldown_rejected_with_c70() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);

    assert!(accepted(&request_rotation(&mut client)));

    // Activate BEFORE the cooldown elapses → C70 + reject.
    let resp = activate_rotation(&mut client, REQUEST_TS + 100);
    assert!(
        !accepted(&resp),
        "pre-cooldown activation must be rejected"
    );
    let reason = match resp.get("rejection_reason") {
        Some(CbValue::String(s)) => s.clone(),
        _ => String::new(),
    };
    assert!(
        reason.contains("C70"),
        "pre-cooldown activation must cite C70; got {reason:?}"
    );
    assert!(
        count_nodes(&mut client, "immune:C70") >= 1,
        "pre-cooldown activation must fruit a C70 rotation_veto_window_violation sporocarp"
    );
    // No key rotated.
    assert_eq!(count_nodes(&mut client, "owner_key_added"), 0);
    client.shutdown().expect("shutdown");
}

#[test]
fn c70_activate_after_cooldown_dual_cosign_adds_and_archives() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);

    assert!(accepted(&request_rotation(&mut client)));

    // Activate AT/AFTER the cooldown with a valid dual-cosign → success.
    let resp = activate_rotation(&mut client, REQUEST_TS + COOLDOWN);
    assert!(
        accepted(&resp),
        "post-cooldown dual-cosign activation must be accepted; got {:?}",
        resp.get("rejection_reason")
    );
    // **Flipped sentinel**: owner_key_added IS now emitted on activation.
    assert_eq!(
        count_nodes(&mut client, "owner_key_added"),
        1,
        "activation must emit owner_key_added (the rotation FSM is live — this \
         replaces the former acknowledged-debt sentinel)"
    );
    assert_eq!(count_nodes(&mut client, "owner_key_archived"), 1);

    // The rotation truly took effect: a NEW CI mutation now verifies against the
    // ROTATED key. A duress registration signed by the NEW key must be accepted;
    // the OLD key must now be rejected (it is no longer the active owner key).
    let duress_body = substrate::events::build_duress_keypair_registration_canonical_bytes(
        &[0xABu8; 32],
        "post-rotation duress",
        REQUEST_TS + COOLDOWN + 1,
    );
    let new_signed = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("duress_keypair_registration".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(duress_body.clone())),
                (
                    "touched_fields",
                    CbValue::Array(vec![CbValue::String("owner_key_history".to_string())]),
                ),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                ("attestation_signature", CbValue::Bytes(sign(&NEW_SEED, &duress_body))),
            ]),
        )
        .expect("submit")
        .payload;
    assert!(
        accepted(&new_signed),
        "post-rotation, a CI mutation signed by the NEW key must be accepted; got {:?}",
        new_signed.get("rejection_reason")
    );

    let old_signed = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("duress_keypair_registration".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(duress_body.clone())),
                (
                    "touched_fields",
                    CbValue::Array(vec![CbValue::String("owner_key_history".to_string())]),
                ),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                ("attestation_signature", CbValue::Bytes(sign(&OWNER_SEED, &duress_body))),
            ]),
        )
        .expect("submit")
        .payload;
    assert!(
        !accepted(&old_signed),
        "post-rotation, a CI mutation signed by the OLD key must be rejected"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn c70_second_request_while_pending_rejected_single_in_flight() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);

    assert!(accepted(&request_rotation(&mut client)));
    // A second request while one is pending → rejected (single-in-flight).
    let resp = request_rotation(&mut client);
    assert!(
        !accepted(&resp),
        "a second request while a rotation is pending must be rejected"
    );
    assert_eq!(
        count_nodes(&mut client, "owner_key_rotation_requested"),
        1,
        "the rejected second request must NOT emit another requested event"
    );
    client.shutdown().expect("shutdown");
}

#[test]
fn c70_restart_mid_cooldown_redrives_pending() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);
    assert!(accepted(&request_rotation(&mut client)));
    assert_eq!(count_nodes(&mut client, "owner_key_rotation_requested"), 1);
    client.shutdown().expect("shutdown pre-restart");

    // Restart against the SAME state_dir → the pending rotation is re-derived
    // from the DAG. Proof: a SECOND request is still refused (single-in-flight
    // survived the reboot), and an in-window veto still clears it.
    let mut client2 = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);
    let second = request_rotation(&mut client2);
    assert!(
        !accepted(&second),
        "after restart mid-cooldown, the pending rotation must still block a \
         second request (single-in-flight re-derived from the DAG)"
    );

    // And the re-derived pending can still be activated post-cooldown.
    let resp = activate_rotation(&mut client2, REQUEST_TS + COOLDOWN);
    assert!(
        accepted(&resp),
        "the DAG-re-derived pending rotation must be activatable; got {:?}",
        resp.get("rejection_reason")
    );
    assert_eq!(count_nodes(&mut client2, "owner_key_added"), 1);
    client2.shutdown().expect("shutdown");
}

#[test]
fn c70_activate_without_pending_rejected() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);
    // Activate with no prior request → rejected (requires a pending rotation).
    let resp = activate_rotation(&mut client, REQUEST_TS + COOLDOWN);
    assert!(
        !accepted(&resp),
        "activation without a pending rotation must be rejected"
    );
    assert_eq!(count_nodes(&mut client, "owner_key_added"), 0);
    client.shutdown().expect("shutdown");
}

#[test]
fn c70_activate_with_forged_new_key_cosignature_rejected() {
    // Adversarial: a stolen-OLD-key holder tries to activate with a BOGUS
    // new-key cosignature (they cannot produce the new key's signature). Even
    // post-cooldown, the dual-cosign check must reject.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);
    assert!(accepted(&request_rotation(&mut client)));

    let prior = pubkey(&OWNER_SEED);
    let new_pk = pubkey(&NEW_SEED);
    let cooldown = REQUEST_TS + COOLDOWN;
    let activate_ts = REQUEST_TS + COOLDOWN;
    // Forge the cosignature: sign the core with the WRONG key (the old key),
    // not the new key. verify(new_pk, sig, core) must fail.
    let core = substrate::events::build_rotate_owner_key_activate_core(
        &prior, &new_pk, REQUEST_TS, cooldown, activate_ts, &NONCE,
    );
    let mut forged = [0u8; 64];
    forged.copy_from_slice(&sign(&OWNER_SEED, &core)); // wrong signer
    let body = substrate::events::build_rotate_owner_key_activate(
        &prior, &new_pk, REQUEST_TS, cooldown, activate_ts, &NONCE, &forged,
    );
    let resp = submit_rotation(&mut client, &body, &OWNER_SEED);
    assert!(
        !accepted(&resp),
        "activation with a forged new-key cosignature must be rejected"
    );
    assert_eq!(count_nodes(&mut client, "owner_key_added"), 0);
    client.shutdown().expect("shutdown");
}

#[test]
fn c70_phased_envelope_roundtrips() {
    use substrate::events::{
        build_rotate_owner_key_activate, build_rotate_owner_key_request,
        build_rotate_owner_key_veto, decode_rotate_owner_key_activate,
        decode_rotate_owner_key_request, decode_rotate_owner_key_veto,
        rotate_owner_key_phase, ROTATE_PHASE_ACTIVATE, ROTATE_PHASE_REQUEST,
        ROTATE_PHASE_VETO,
    };
    let prior = [0x11u8; 32];
    let new_pk = [0x22u8; 32];
    let nonce = [0x33u8; 32];

    let req = build_rotate_owner_key_request(&prior, &new_pk, 1000, 1000 + COOLDOWN, &nonce);
    assert_eq!(rotate_owner_key_phase(&req).as_deref(), Some(ROTATE_PHASE_REQUEST));
    let (p, n, rts, cd, no) = decode_rotate_owner_key_request(&req).expect("req");
    assert_eq!((p, n, rts, cd, no), (prior, new_pk, 1000, 1000 + COOLDOWN, nonce));

    let veto = build_rotate_owner_key_veto(&new_pk, 1500, &nonce);
    assert_eq!(rotate_owner_key_phase(&veto).as_deref(), Some(ROTATE_PHASE_VETO));
    let (n, vts, no) = decode_rotate_owner_key_veto(&veto).expect("veto");
    assert_eq!((n, vts, no), (new_pk, 1500, nonce));

    let cosig = [0x44u8; 64];
    let act = build_rotate_owner_key_activate(
        &prior, &new_pk, 1000, 1000 + COOLDOWN, 1000 + COOLDOWN, &nonce, &cosig,
    );
    assert_eq!(rotate_owner_key_phase(&act).as_deref(), Some(ROTATE_PHASE_ACTIVATE));
    let (p, n, rts, cd, ats, no, cs, _core) =
        decode_rotate_owner_key_activate(&act).expect("act");
    assert_eq!(
        (p, n, rts, cd, ats, no, cs),
        (prior, new_pk, 1000, 1000 + COOLDOWN, 1000 + COOLDOWN, nonce, cosig)
    );

    // Legacy single-shot envelope has NO phase.
    let legacy = substrate::events::build_rotate_owner_key_canonical_bytes(
        &prior, &new_pk, 1000, &nonce,
    );
    assert_eq!(rotate_owner_key_phase(&legacy), None);
}

