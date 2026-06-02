//! E2E: F23 / C50 — duress keypair coercion defense (cosmetic-accept + freeze FSM).
//!
//! Doctrine: L2/TRUST_MODEL §10.A.2 (coerced Cultivator) + L1/GOVERNANCE F23
//! (`cultivator_duress_keypair_registrations`) + L0/cards/AS_anchor_surface.md
//! §5.6 / §8.4 (`duress_keypair_signature_observation`) + canonical dilemma
//! D-0047 + L1/HARD_RULES C50 `coerced_owner_suspected`.
//!
//! A pre-registered duress keypair (separate Ed25519, registered at genesis on a
//! separate medium — here SYNTHETIC) lets a coerced owner signal duress by
//! signing an attestation with the duress key instead of the owner key. The
//! substrate then (1) cosmetically ACCEPTS the mutation (the coercer sees
//! success), (2) does NOT commit the substantive effect, (3) silently emits C50
//! + `duress_signature_observed`, and (4) freezes destructive mutations until an
//! `out_of_band_safety_reattestation` signed by the ACTIVE owner key clears it.
//!
//! Scenarios:
//!   1. register a duress keypair at genesis → `duress_keypair_registered:*` event.
//!   2. destructive CI signed by the DURESS key → response COSMETICALLY accepted
//!      + NO `mutation:*` effect node + C50 + `duress_signature_observed:*` + frozen.
//!   3. subsequent destructive CI (OWNER-key-signed) while frozen → still
//!      cosmetically suppressed + C50 re-emitted.
//!   4. `out_of_band_safety_reattestation` (ACTIVE-key-signed) → `duress_cleared`
//!      + unfrozen; a normal owner CI then commits again.
//!   5. mutating the duress registration WITH a duress key → blocked (the
//!      circular-trust guard) — both the pre-Python duress gate (registered
//!      duress key → cosmetic-suppress, no new registration) and the Python CI
//!      gate (un-registered duress key → accepted=false, C5).
//!   6. restart preserves the freeze (DAG-derived FSM).
//!   7. a NORMAL active-key mutation → unaffected (REGRESSION — the critical
//!      proof that recognition is precise and a legit mutation is never dropped).
//!
//! Mirrors the `e2e_revocation.rs` (C13) harness; shared spawn/build helpers
//! live in `tests/common/mod.rs`.

mod common;
use common::*;

use myco_kernel_shared::crypto::Ed25519PrivateKey;

/// The owner signing seed pinned on the substrate-under-test. Its seed-derived
/// pubkey IS the pinned operator identity, so an `attestation_signature`
/// produced with this seed verifies as the owner's (the normal CI path).
const OWNER_SEED: [u8; 32] = [0x7c; 32];

/// A SYNTHETIC duress seed — a DISTINCT keypair from the owner. A real
/// deployment generates this on a separate medium at genesis; the test stands
/// in for that. Disjoint from `OWNER_SEED`, so the recognition disjointness
/// (owner-vs-duress) holds.
const DURESS_SEED: [u8; 32] = [0x3d; 32];

/// A SECOND synthetic duress seed used to prove a NEVER-registered duress key
/// cannot register anything (the Python CI circular-trust reject path).
const DURESS_SEED_2: [u8; 32] = [0x4e; 32];

fn sign(seed: &[u8; 32], content: &[u8]) -> Vec<u8> {
    let key = Ed25519PrivateKey::from_seed(seed);
    key.sign(content).as_ref().to_vec()
}

fn pubkey_of(seed: &[u8; 32]) -> [u8; 32] {
    Ed25519PrivateKey::from_seed(seed).public_key().0
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

/// Count DAG nodes whose node_type starts with `prefix`.
fn count_nodes(client: &mut BridgeClient, prefix: &str) -> usize {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(2000)),
                ("node_type_prefix", CbValue::String(prefix.to_string())),
            ]),
        )
        .expect("query recent");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => 0,
    }
}

/// Build the genesis env-vars that register ONE owner-attested duress key. The
/// registration body is signed by `owner_seed` (the active owner), exactly as
/// the off-line anchor-surface ceremony would produce.
fn duress_genesis_env(
    owner_seed: &[u8; 32],
    duress_pubkey: &[u8; 32],
    label: &str,
) -> Vec<(String, String)> {
    let body = substrate::events::build_duress_keypair_registration_canonical_bytes(
        duress_pubkey,
        label,
        1_700_000_000,
    );
    let sig = sign(owner_seed, &body);
    let owner_pk = pubkey_of(owner_seed);
    vec![
        ("MYCO_DURESS_REGISTRATION_COUNT".to_string(), "1".to_string()),
        ("MYCO_DURESS_REGISTRATION_0_BYTES_HEX".to_string(), hex(&body)),
        ("MYCO_DURESS_REGISTRATION_0_SIGNATURE_HEX".to_string(), hex(&sig)),
        (
            "MYCO_DURESS_REGISTRATION_0_OWNER_PUBKEY_HEX".to_string(),
            hex(&owner_pk),
        ),
    ]
}

/// Submit a `revoke_federation_peer` CI mutation (a representative DESTRUCTIVE
/// CI) signed by `seed`, revoking `revoked_id`. Returns the response payload.
/// Whether `seed` is the owner or a duress key determines the path taken.
fn submit_destructive_ci(
    client: &mut BridgeClient,
    seed: &[u8; 32],
    revoked_id: &[u8; 32],
    reason: &str,
) -> std::collections::BTreeMap<String, CbValue> {
    let body = substrate::events::build_revoke_federation_peer_canonical_bytes(
        revoked_id,
        &[0u8; 32],
        reason,
        1_700_000_000,
    );
    client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("revoke_federation_peer".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(body.clone())),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                ("attestation_signature", CbValue::Bytes(sign(seed, &body))),
            ]),
        )
        .expect("submit destructive ci")
        .payload
}

/// Submit an `out_of_band_safety_reattestation` CI mutation signed by `seed`.
fn submit_reattestation(
    client: &mut BridgeClient,
    seed: &[u8; 32],
    statement: &str,
) -> std::collections::BTreeMap<String, CbValue> {
    let body = substrate::events::build_out_of_band_safety_reattestation_canonical_bytes(
        statement,
        1_700_000_001,
    );
    client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                (
                    "mutation_type",
                    CbValue::String("out_of_band_safety_reattestation".to_string()),
                ),
                ("content_canonical_bytes", CbValue::Bytes(body.clone())),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                ("attestation_signature", CbValue::Bytes(sign(seed, &body))),
            ]),
        )
        .expect("submit reattestation")
        .payload
}

/// Submit a `duress_keypair_registration` CI mutation for `new_duress_pubkey`,
/// signed by `signing_seed`. Returns the response payload.
fn submit_duress_registration(
    client: &mut BridgeClient,
    signing_seed: &[u8; 32],
    new_duress_pubkey: &[u8; 32],
    label: &str,
) -> std::collections::BTreeMap<String, CbValue> {
    let body = substrate::events::build_duress_keypair_registration_canonical_bytes(
        new_duress_pubkey,
        label,
        1_700_000_002,
    );
    client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                (
                    "mutation_type",
                    CbValue::String("duress_keypair_registration".to_string()),
                ),
                ("content_canonical_bytes", CbValue::Bytes(body.clone())),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
                ("attestation_signature", CbValue::Bytes(sign(signing_seed, &body))),
            ]),
        )
        .expect("submit duress registration")
        .payload
}

fn accepted(p: &std::collections::BTreeMap<String, CbValue>) -> bool {
    matches!(p.get("accepted"), Some(CbValue::Bool(true)))
}

// ---------------------------------------------------------------------------
// 1 + 2 + 3 + 4. The full happy-path coercion lifecycle in one substrate:
//   genesis registration → duress-signed CI cosmetically suppressed + frozen →
//   frozen owner CI suppressed → reattestation clears → owner CI commits.
// ---------------------------------------------------------------------------

#[test]
fn f23_duress_signature_cosmetically_suppressed_then_frozen_then_cleared() {
    let dir = fresh_state_dir();
    let duress_pk = pubkey_of(&DURESS_SEED);
    let env = duress_genesis_env(&OWNER_SEED, &duress_pk, "synthetic-yubikey");
    let mut client = spawn_substrate_with_seed_and_env(&dir, OWNER_SEED, env);

    // (1) Genesis registration emitted the on-chain record.
    assert_eq!(
        count_nodes(&mut client, "duress_keypair_registered:"),
        1,
        "genesis env must emit exactly one duress_keypair_registered:* event"
    );

    let mutations_before = count_nodes(&mut client, "mutation:revoke_federation_peer");

    // (2) A destructive CI signed by the DURESS key → cosmetic accept, NO
    // mutation:* effect, C50, duress_signature_observed, frozen.
    let victim = [0x99u8; 32];
    let resp = submit_destructive_ci(&mut client, &DURESS_SEED, &victim, "coerced revoke");
    assert!(
        accepted(&resp),
        "a duress-signed CI must be COSMETICALLY accepted (the coercer sees success); got {:?}",
        resp.get("rejection_reason")
    );
    assert_eq!(
        resp.get("classification"),
        Some(&CbValue::String("contract_identity_level".to_string())),
        "cosmetic response must look like a normal CI accept"
    );
    // The substantive effect was SUPPRESSED — no new mutation:revoke_federation_peer
    // node, and no federation_peer_revoked:* CRL entry.
    assert_eq!(
        count_nodes(&mut client, "mutation:revoke_federation_peer"),
        mutations_before,
        "the duress-signed mutation:* effect MUST be suppressed (no DAG node)"
    );
    assert_eq!(
        count_nodes(&mut client, "federation_peer_revoked:"),
        0,
        "the suppressed revoke must not emit a CRL entry"
    );
    // The SILENT forensic records exist.
    assert!(
        count_nodes(&mut client, "immune:C50") >= 1,
        "a duress observation must fruit a C50 coerced_owner_suspected sporocarp"
    );
    assert!(
        count_nodes(&mut client, "duress_signature_observed:") >= 1,
        "a duress observation must emit a silent duress_signature_observed:* event"
    );
    assert_eq!(
        count_nodes(&mut client, "coerced_owner_suspected"),
        1,
        "the freeze-onset event must be emitted exactly once on the first observation"
    );

    // (3) A destructive CI signed by the OWNER key while frozen → still
    // cosmetically suppressed + C50 re-emitted (the freeze blocks destructive CI
    // regardless of which key signs — the owner may be coerced into signing).
    let resp2 = submit_destructive_ci(&mut client, &OWNER_SEED, &victim, "owner revoke while frozen");
    assert!(
        accepted(&resp2),
        "a destructive CI while frozen must be cosmetically accepted"
    );
    assert_eq!(
        count_nodes(&mut client, "mutation:revoke_federation_peer"),
        mutations_before,
        "a destructive CI while frozen MUST remain suppressed (still no DAG node)"
    );
    assert_eq!(
        count_nodes(&mut client, "federation_peer_revoked:"),
        0,
        "frozen-state destructive CI must not emit a CRL entry"
    );

    // (4) out_of_band_safety_reattestation signed by the ACTIVE owner key →
    // duress_cleared + unfrozen.
    let clear_resp = submit_reattestation(&mut client, &OWNER_SEED, "I am safe; coercion ended");
    assert!(
        accepted(&clear_resp),
        "an active-key reattestation must be accepted; got {:?}",
        clear_resp.get("rejection_reason")
    );
    assert_eq!(
        count_nodes(&mut client, "duress_cleared"),
        1,
        "an accepted reattestation must emit exactly one duress_cleared event"
    );

    // After clearance, a NORMAL owner CI commits again (freeze lifted).
    let resp3 = submit_destructive_ci(&mut client, &OWNER_SEED, &victim, "post-clearance revoke");
    assert!(accepted(&resp3), "post-clearance owner CI must be accepted");
    assert_eq!(
        count_nodes(&mut client, "mutation:revoke_federation_peer"),
        mutations_before + 1,
        "after clearance the owner CI MUST commit a real mutation:* node"
    );
    assert_eq!(
        count_nodes(&mut client, "federation_peer_revoked:"),
        1,
        "after clearance the owner revoke MUST emit a real CRL entry"
    );

    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// 5. The circular-trust guard: a duress key cannot mutate the duress registration.
// ---------------------------------------------------------------------------

#[test]
fn f23_registered_duress_key_cannot_expand_registration() {
    // A coerced owner cannot use an ALREADY-REGISTERED duress key to add MORE
    // duress keys: the pre-Python duress gate recognizes the duress signature →
    // cosmetic-suppress; the new key is NOT registered + C50 fires + the freeze
    // trips. (The cosmetic accept means the coercer sees success.)
    let dir = fresh_state_dir();
    let d1 = pubkey_of(&DURESS_SEED);
    let env = duress_genesis_env(&OWNER_SEED, &d1, "d1");
    let mut client = spawn_substrate_with_seed_and_env(&dir, OWNER_SEED, env);
    assert_eq!(count_nodes(&mut client, "duress_keypair_registered:"), 1);

    let d2 = pubkey_of(&DURESS_SEED_2);
    let resp = submit_duress_registration(&mut client, &DURESS_SEED, &d2, "coerced d2");
    assert!(
        accepted(&resp),
        "a duress-signed registration is cosmetically accepted (coercer sees success)"
    );
    assert_eq!(
        count_nodes(&mut client, "duress_keypair_registered:"),
        1,
        "a duress-key-signed registration MUST NOT add a new duress key (circular-trust)"
    );
    assert!(
        count_nodes(&mut client, "immune:C50") >= 1,
        "the coerced registration attempt must fruit C50"
    );

    client.shutdown().expect("shutdown");
}

#[test]
fn f23_non_owner_key_registration_rejected_by_ci_gate() {
    // The Python-side circular-trust guard: a `duress_keypair_registration`
    // signed by a key that is NEITHER the owner NOR a registered duress key
    // flows past the (miss) pre-Python gate to Python, whose CI gate verifies
    // the signature against the ACTIVE owner key → FAILS → accepted=false + C5.
    // Run on a fresh, UNFROZEN substrate with NO duress registered so the
    // freeze gate cannot pre-empt the Python reject.
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);

    let d2 = pubkey_of(&DURESS_SEED_2);
    let resp = submit_duress_registration(&mut client, &DURESS_SEED_2, &d2, "self-signed d2");
    assert!(
        !accepted(&resp),
        "a registration signed by a non-owner key must be rejected (active-key CI gate)"
    );
    assert_eq!(
        resp.get("classification"),
        Some(&CbValue::String("contract_identity_level".to_string())),
        "duress_keypair_registration is CI"
    );
    assert_eq!(
        count_nodes(&mut client, "duress_keypair_registered:"),
        0,
        "the rejected registration must not add a duress key"
    );
    assert!(
        count_nodes(&mut client, "immune:C5") >= 1,
        "the non-owner-key registration must fruit C5 attestation_invalid"
    );

    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// 5c. Genesis guards: registering the OWNER key as a duress key is refused
//     (circular self-duress), and a registration with a bad owner signature is
//     refused. Both emit C5 and register nothing.
// ---------------------------------------------------------------------------

#[test]
fn f23_genesis_refuses_owner_key_as_duress_and_bad_signature() {
    // (a) Register the OWNER's OWN pubkey as a duress key at genesis → refused.
    let dir_a = fresh_state_dir();
    let owner_pk = pubkey_of(&OWNER_SEED);
    let env_a = duress_genesis_env(&OWNER_SEED, &owner_pk, "self");
    let mut client_a = spawn_substrate_with_seed_and_env(&dir_a, OWNER_SEED, env_a);
    assert_eq!(
        count_nodes(&mut client_a, "duress_keypair_registered:"),
        0,
        "registering the owner key as a duress key must be refused (circular self-duress)"
    );
    assert!(
        count_nodes(&mut client_a, "immune:C5") >= 1,
        "the circular self-duress registration must fruit C5"
    );
    // The would-be self-duress key must NOT recognize owner sigs as duress: a
    // normal owner CI still commits.
    let resp = submit_destructive_ci(&mut client_a, &OWNER_SEED, &[0x12u8; 32], "owner revoke");
    assert!(accepted(&resp));
    assert_eq!(count_nodes(&mut client_a, "mutation:revoke_federation_peer"), 1);
    assert_eq!(count_nodes(&mut client_a, "immune:C50"), 0);
    client_a.shutdown().expect("shutdown A");

    // (b) A registration whose owner SIGNATURE does not verify (signed by a
    // DIFFERENT key than the declared owner_pubkey) → refused at genesis.
    let dir_b = fresh_state_dir();
    let duress_pk = pubkey_of(&DURESS_SEED);
    // Build a valid body, but sign it with DURESS_SEED_2 while declaring the
    // owner pubkey as OWNER_SEED's — the signature won't verify.
    let body = substrate::events::build_duress_keypair_registration_canonical_bytes(
        &duress_pk,
        "bad-sig",
        1_700_000_000,
    );
    let bad_sig = sign(&DURESS_SEED_2, &body);
    let env_b = vec![
        ("MYCO_DURESS_REGISTRATION_COUNT".to_string(), "1".to_string()),
        ("MYCO_DURESS_REGISTRATION_0_BYTES_HEX".to_string(), hex(&body)),
        ("MYCO_DURESS_REGISTRATION_0_SIGNATURE_HEX".to_string(), hex(&bad_sig)),
        (
            "MYCO_DURESS_REGISTRATION_0_OWNER_PUBKEY_HEX".to_string(),
            hex(&pubkey_of(&OWNER_SEED)),
        ),
    ];
    let mut client_b = spawn_substrate_with_seed_and_env(&dir_b, OWNER_SEED, env_b);
    assert_eq!(
        count_nodes(&mut client_b, "duress_keypair_registered:"),
        0,
        "a registration with a non-verifying owner signature must be refused at genesis"
    );
    assert!(count_nodes(&mut client_b, "immune:C5") >= 1);
    client_b.shutdown().expect("shutdown B");
}

// ---------------------------------------------------------------------------
// 6. Restart preserves the freeze (DAG-derived FSM).
// ---------------------------------------------------------------------------

#[test]
fn f23_freeze_survives_restart() {
    let dir = fresh_state_dir();
    let duress_pk = pubkey_of(&DURESS_SEED);
    let env = duress_genesis_env(&OWNER_SEED, &duress_pk, "d1");
    let mut client = spawn_substrate_with_seed_and_env(&dir, OWNER_SEED, env.clone());

    // Trip the freeze with a duress-signed CI.
    let victim = [0x55u8; 32];
    let resp = submit_destructive_ci(&mut client, &DURESS_SEED, &victim, "coerced");
    assert!(accepted(&resp));
    assert!(count_nodes(&mut client, "coerced_owner_suspected") >= 1);
    let mutations_before = count_nodes(&mut client, "mutation:revoke_federation_peer");
    client.shutdown().expect("shutdown pre-restart");

    // Restart against the SAME state_dir. The freeze flag + duress set are
    // re-derived from the DAG, so a destructive owner CI is STILL suppressed.
    // (Re-supply the genesis env — harmless: the registration is content-hash
    // idempotent, so it does not double-register.)
    let mut client2 = spawn_substrate_with_seed_and_env(&dir, OWNER_SEED, env);
    assert_eq!(
        count_nodes(&mut client2, "duress_keypair_registered:"),
        1,
        "registration persists across restart (content-hash idempotent)"
    );
    let resp2 = submit_destructive_ci(&mut client2, &OWNER_SEED, &victim, "owner revoke after restart");
    assert!(
        accepted(&resp2),
        "frozen-state destructive CI is cosmetically accepted after restart"
    );
    assert_eq!(
        count_nodes(&mut client2, "mutation:revoke_federation_peer"),
        mutations_before,
        "after restart the DAG-derived freeze MUST still suppress destructive CI"
    );

    client2.shutdown().expect("shutdown A2");
}

// ---------------------------------------------------------------------------
// 7. REGRESSION (critical): a NORMAL active-key mutation is UNAFFECTED.
//    Proves recognition is precise — an owner sig is never mis-recognized as
//    duress, so a legit mutation is never silently dropped. Runs BOTH on a
//    substrate WITH a registered duress key (the disjointness proof) and the
//    response carries a real committed effect.
// ---------------------------------------------------------------------------

#[test]
fn f23_normal_owner_mutation_unaffected_with_duress_registered() {
    let dir = fresh_state_dir();
    // Register a duress key so `duress_pubkeys` is NON-empty — this is the
    // adversarial condition for the recognition: a normal owner sig must NOT
    // verify under the registered duress key.
    let duress_pk = pubkey_of(&DURESS_SEED);
    let env = duress_genesis_env(&OWNER_SEED, &duress_pk, "d1");
    let mut client = spawn_substrate_with_seed_and_env(&dir, OWNER_SEED, env);
    assert_eq!(count_nodes(&mut client, "duress_keypair_registered:"), 1);

    // A NORMAL owner-key-signed destructive CI → committed for real (NOT
    // suppressed, NO C50, NO duress_signature_observed, NO freeze).
    let victim = [0x77u8; 32];
    let resp = submit_destructive_ci(&mut client, &OWNER_SEED, &victim, "legit owner revoke");
    assert!(
        accepted(&resp),
        "a normal owner CI must be accepted; got {:?}",
        resp.get("rejection_reason")
    );
    assert_eq!(
        count_nodes(&mut client, "mutation:revoke_federation_peer"),
        1,
        "a normal owner CI MUST commit a real mutation:* node (not be mis-suppressed)"
    );
    assert_eq!(
        count_nodes(&mut client, "federation_peer_revoked:"),
        1,
        "a normal owner revoke MUST emit a real CRL entry"
    );
    assert_eq!(
        count_nodes(&mut client, "immune:C50"),
        0,
        "a normal owner CI must NEVER fruit C50 (no duress mis-recognition)"
    );
    assert_eq!(
        count_nodes(&mut client, "duress_signature_observed:"),
        0,
        "a normal owner CI must NEVER emit duress_signature_observed"
    );
    assert_eq!(
        count_nodes(&mut client, "coerced_owner_suspected"),
        0,
        "a normal owner CI must NEVER trip the freeze"
    );

    client.shutdown().expect("shutdown");
}

// ---------------------------------------------------------------------------
// 8. REGRESSION: a substrate with NO duress key registered is entirely
//    unaffected — the duress code paths are inert (byte-compat).
// ---------------------------------------------------------------------------

#[test]
fn f23_no_duress_registered_paths_inert() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, OWNER_SEED);
    assert_eq!(
        count_nodes(&mut client, "duress_keypair_registered:"),
        0,
        "no genesis env → no duress registration"
    );

    // A normal owner CI commits; no duress artifacts anywhere.
    let victim = [0x88u8; 32];
    let resp = submit_destructive_ci(&mut client, &OWNER_SEED, &victim, "owner revoke");
    assert!(accepted(&resp));
    assert_eq!(count_nodes(&mut client, "mutation:revoke_federation_peer"), 1);
    assert_eq!(count_nodes(&mut client, "immune:C50"), 0);
    assert_eq!(count_nodes(&mut client, "duress_signature_observed:"), 0);

    client.shutdown().expect("shutdown");
}
