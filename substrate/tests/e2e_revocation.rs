//! E2E: C13 — local federation peer revocation (owner-attested CRL +
//! egress/ingest block).
//!
//! Doctrine: L1/GOVERNANCE §5.2 ("Revocation list at anchor; … every outbound
//! envelope verifies target freshness + non-revocation pre-emission;
//! stale/revoked → `federation_egress_blocked`") + L2/FEDERATION §6.5.b
//! per-peer OWNER revocation + L1/HARD_RULES C13 `peer_attestation_revoked_egress`.
//!
//! SCOPE: this exercises the LOCAL owner-revocation half only. The
//! quorum-revocation half (§6.5.b ≥2/3 Byzantine consensus at ≥3 peers) is
//! DEFERRED — it needs the absent PBFT layer.
//!
//! Scenarios:
//!   1. revoke_federation_peer (attested) → federation_peer_revoked:* event +
//!      revoked-set populated (asserted indirectly via the egress/ingest block
//!      + the on-chain CRL event).
//!   2. egress to a revoked peer → C13 + the FED_EVENT_BATCH suppressed.
//!   3. ingest of events from a revoked peer → refused (0 ingested) + C13.
//!   4. restart re-derives the revoked-set from the DAG (the block survives a
//!      respawn against the same state_dir).
//!   5. unattested revoke → C5 (no new HARD_RULES row).
//!
//! Mirrors the `e2e_federation.rs` + `e2e_schema_migration.rs` harnesses;
//! shared spawn/build helpers live in `tests/common/mod.rs`.

mod common;
use common::*;

use myco_kernel_shared::crypto::Ed25519PrivateKey;

/// The owner signing seed pinned on the substrate-under-test. The
/// seed-derived pubkey IS the pinned operator identity, so an
/// `attestation_signature` produced with this seed verifies as the owner's.
const OWNER_SEED: [u8; 32] = [0x7c; 32];

/// Sign content with the seed-derived owner key (M10 path).
fn sign(seed: &[u8; 32], content: &[u8]) -> Vec<u8> {
    let key = Ed25519PrivateKey::from_seed(seed);
    key.sign(content).as_ref().to_vec()
}

/// Background-poll a client `max_iters` times (50ms each) so it can accept
/// inbound connections / serve inbound requests. Returns the client on join.
fn poll_bg(
    mut client: BridgeClient,
    max_iters: u32,
) -> std::thread::JoinHandle<BridgeClient> {
    std::thread::spawn(move || {
        for _ in 0..max_iters {
            let _ = client.call(proto::FEDERATION_POLL, build_payload(vec![]));
            std::thread::sleep(std::time::Duration::from_millis(50));
        }
        client
    })
}

/// Open a federation listener on `client`, returning the resolved bind addr.
fn open_listener(client: &mut BridgeClient) -> String {
    let resp = client
        .call(
            proto::FEDERATION_OPEN_LISTENER,
            build_payload(vec![("bind_addr", CbValue::String("127.0.0.1:0".to_string()))]),
        )
        .expect("open listener");
    match resp.payload.get("bind_addr") {
        Some(CbValue::String(s)) => s.clone(),
        _ => panic!("bind_addr missing"),
    }
}

/// Count DAG nodes whose node_type starts with `prefix`.
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

/// Submit a `revoke_federation_peer` CI mutation against `client` revoking
/// `revoked_id`. Signs the revocation body with `seed`. Returns the response
/// payload. `attested=false` omits the signature (→ expect C5 rejection).
fn submit_revoke(
    client: &mut BridgeClient,
    seed: &[u8; 32],
    revoked_id: &[u8; 32],
    revoked_pubkey: &[u8; 32],
    reason: &str,
    attested: bool,
) -> std::collections::BTreeMap<String, CbValue> {
    let body = substrate::events::build_revoke_federation_peer_canonical_bytes(
        revoked_id,
        revoked_pubkey,
        reason,
        1_700_000_000, // anchor seconds (arbitrary but fixed)
    );
    let mut fields = vec![
        ("mutation_type", CbValue::String("revoke_federation_peer".to_string())),
        ("content_canonical_bytes", CbValue::Bytes(body.clone())),
        ("touched_fields", CbValue::Array(vec![])),
        ("touched_files", CbValue::Array(vec![])),
        ("touched_meta_structures", CbValue::Array(vec![])),
    ];
    if attested {
        fields.push(("attestation_signature", CbValue::Bytes(sign(seed, &body))));
    }
    client
        .call(proto::SUBMIT_MUTATION, build_payload(fields))
        .expect("submit revoke")
        .payload
}

// ---------------------------------------------------------------------------
// 1 + 2. Attested revoke emits the CRL event; egress to the revoked peer is
//        blocked with C13.
// ---------------------------------------------------------------------------

#[test]
fn c13_attested_revoke_emits_crl_event_and_blocks_egress() {
    // A = substrate-under-test (seeded owner). B = the peer A will revoke.
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);
    let addr_a = open_listener(&mut client_a);

    // Phase 1: B connects to A so A pins B (Established). Poll A briefly to
    // accept B, then reclaim A.
    let poll1 = poll_bg(client_a, 30);
    let (mut client_b, _dir_b) = spawn_substrate();
    let connect_resp = client_b
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_a.clone()))]),
        )
        .expect("B connect A");
    assert_eq!(
        connect_resp.payload.get("outcome"),
        Some(&CbValue::String("pinned".to_string())),
        "B should pin A"
    );
    let mut client_a = poll1.join().expect("poll1 join");

    // B's own substrate_id is what A will revoke.
    let b_id = read_substrate_id(&mut client_b);

    // Phase 2: A revokes B (attested CI mutation).
    let revoke_resp = submit_revoke(
        &mut client_a,
        &OWNER_SEED,
        &b_id,
        &[0u8; 32], // revoked_pubkey unknown to test → zero is acceptable
        "operator manually revoked peer B",
        true,
    );
    assert_eq!(
        revoke_resp.get("accepted"),
        Some(&CbValue::Bool(true)),
        "attested revoke must be accepted; got {:?}",
        revoke_resp.get("rejection_reason")
    );
    // The on-chain CRL entry must exist.
    assert!(
        count_nodes(&mut client_a, "federation_peer_revoked:") >= 1,
        "attested revoke must emit a federation_peer_revoked:* DAG event"
    );

    // Phase 3: B (revoked) pulls events from A → A's egress site blocks the
    // FED_EVENT_BATCH pre-emission + fruits C13. Drive A's poll in the
    // background while B issues the pull.
    let a_id = match connect_resp.payload.get("peer_substrate_id") {
        Some(CbValue::Bytes(b)) => b.clone(),
        _ => panic!("a_id missing"),
    };
    let poll2 = poll_bg(client_a, 60);
    // B's pull will time out (A sends no batch) — that's expected; we only care
    // that A blocked + recorded C13, so ignore B's pull result.
    let _ = client_b.call(
        proto::FEDERATION_PULL_EVENTS_FROM_PEER,
        build_payload(vec![
            ("peer_substrate_id", CbValue::Bytes(a_id)),
            ("max_events", CbValue::Uint(50)),
        ]),
    );
    let mut client_a = poll2.join().expect("poll2 join");

    // A's DAG must contain a C13 immune sporocarp.
    assert!(
        count_nodes(&mut client_a, "immune:C13") >= 1,
        "egress to a revoked peer must fruit a C13 peer_attestation_revoked_egress sporocarp"
    );

    client_a.shutdown().expect("shutdown A");
    client_b.shutdown().expect("shutdown B");
}

// ---------------------------------------------------------------------------
// 3 + 4. Ingest from a revoked peer is refused (0 ingested) + C13; the block
//        survives a restart (revoked-set re-derived from the DAG).
// ---------------------------------------------------------------------------

#[test]
fn c13_ingest_from_revoked_peer_refused_and_survives_restart() {
    // A = substrate-under-test (seeded owner). B = a peer with some pullable
    // raw_material events that A would normally ingest.
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);

    // B opens a listener + ingests two raw_material events (allowlisted, so A
    // would ingest them absent revocation).
    let (mut client_b, _dir_b) = spawn_substrate();
    let addr_b = open_listener(&mut client_b);
    for n in 0..2 {
        client_b
            .call(
                proto::INGEST_RAW_MATERIAL,
                build_payload(vec![
                    ("content_kind", CbValue::String("text".to_string())),
                    ("content_bytes", CbValue::Bytes(format!("rm {n}").into_bytes())),
                ]),
            )
            .expect("B ingest");
    }
    let b_id = read_substrate_id(&mut client_b);

    // A connects to B (so A→B is Established for the pull). Drive B's poll to
    // accept A.
    let poll_b = poll_bg(client_b, 40);
    let connect_resp = client_a
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr_b.clone()))]),
        )
        .expect("A connect B");
    assert_eq!(
        connect_resp.payload.get("outcome"),
        Some(&CbValue::String("pinned".to_string())),
        "A should pin B"
    );

    // A revokes B (attested).
    let revoke_resp = submit_revoke(
        &mut client_a,
        &OWNER_SEED,
        &b_id,
        &[0u8; 32],
        "revoke B before ingest",
        true,
    );
    assert_eq!(revoke_resp.get("accepted"), Some(&CbValue::Bool(true)));

    // A pulls from B → ingest gate refuses BEFORE pulling a frame.
    let pull_resp = client_a
        .call(
            proto::FEDERATION_PULL_EVENTS_FROM_PEER,
            build_payload(vec![
                ("peer_substrate_id", CbValue::Bytes(b_id.to_vec())),
                ("max_events", CbValue::Uint(50)),
            ]),
        )
        .expect("A pull from revoked B");
    assert_eq!(
        pull_resp.payload.get("events_ingested_count"),
        Some(&CbValue::Uint(0)),
        "no events from a revoked peer may be ingested"
    );
    let reason = match pull_resp.payload.get("rejection_reason") {
        Some(CbValue::String(s)) => s.clone(),
        _ => String::new(),
    };
    assert!(
        reason.contains("C13"),
        "ingest refusal must cite C13; got {reason:?}"
    );
    assert!(
        count_nodes(&mut client_a, "immune:C13") >= 1,
        "ingest from a revoked peer must fruit a C13 sporocarp"
    );
    // No federation_received:* wrapper from B may have entered A's DAG.
    assert_eq!(
        count_nodes(&mut client_a, "federation_received:"),
        0,
        "a revoked peer's events must not be wrapped/absorbed into the DAG"
    );

    let client_b = poll_b.join().expect("poll_b join");
    let crl_before = count_nodes(&mut client_a, "federation_peer_revoked:");
    assert!(crl_before >= 1, "CRL entry must exist before restart");

    // Phase 4: restart A against the SAME state_dir. The revoked-set is
    // re-derived from the DAG, so a fresh pull is STILL refused.
    client_a.shutdown().expect("shutdown A pre-restart");
    let mut client_a2 = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);
    assert_eq!(
        count_nodes(&mut client_a2, "federation_peer_revoked:"),
        crl_before,
        "CRL events persist across restart"
    );
    // A2 attempts to pull from B again → still refused via the DAG-derived set.
    let pull_resp2 = client_a2
        .call(
            proto::FEDERATION_PULL_EVENTS_FROM_PEER,
            build_payload(vec![
                ("peer_substrate_id", CbValue::Bytes(b_id.to_vec())),
                ("max_events", CbValue::Uint(50)),
            ]),
        )
        .expect("A2 pull from revoked B");
    assert_eq!(
        pull_resp2.payload.get("events_ingested_count"),
        Some(&CbValue::Uint(0)),
        "after restart, the DAG-derived revoked-set must still refuse ingest"
    );

    client_a2.shutdown().expect("shutdown A2");
    client_b.shutdown().expect("shutdown B");
}

// ---------------------------------------------------------------------------
// 5. Unattested revoke → C5 attestation_invalid (no new HARD_RULES row).
// ---------------------------------------------------------------------------

#[test]
fn c13_unattested_revoke_rejected_with_c5() {
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);

    let victim_id = [0x99u8; 32];
    let resp = submit_revoke(
        &mut client_a,
        &OWNER_SEED,
        &victim_id,
        &[0u8; 32],
        "unattested attempt",
        false, // NO attestation_signature
    );
    assert_eq!(
        resp.get("accepted"),
        Some(&CbValue::Bool(false)),
        "an unattested revoke must be rejected"
    );
    assert_eq!(
        resp.get("classification"),
        Some(&CbValue::String("contract_identity_level".to_string())),
        "revoke_federation_peer is CI"
    );
    // C5 (not a new row) must have fruited; no CRL entry, no C13.
    assert!(
        count_nodes(&mut client_a, "immune:C5") >= 1,
        "unattested revoke must fruit C5 attestation_invalid"
    );
    assert_eq!(
        count_nodes(&mut client_a, "federation_peer_revoked:"),
        0,
        "a rejected revoke must NOT emit a CRL entry"
    );

    client_a.shutdown().expect("shutdown A");
}

// ---------------------------------------------------------------------------
// 6. Re-revoking an already-revoked peer is idempotent (accepted, no error).
// ---------------------------------------------------------------------------

#[test]
fn c13_re_revoke_is_idempotent() {
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);

    let victim_id = [0x44u8; 32];
    let r1 = submit_revoke(
        &mut client_a,
        &OWNER_SEED,
        &victim_id,
        &[0u8; 32],
        "first revoke",
        true,
    );
    assert_eq!(r1.get("accepted"), Some(&CbValue::Bool(true)));

    // Re-revoke the SAME peer with the SAME body → idempotent. The DAG insert
    // is content-hash idempotent, so the CRL-entry count does not grow.
    let crl_after_first = count_nodes(&mut client_a, "federation_peer_revoked:");
    let r2 = submit_revoke(
        &mut client_a,
        &OWNER_SEED,
        &victim_id,
        &[0u8; 32],
        "first revoke",
        true,
    );
    assert_eq!(
        r2.get("accepted"),
        Some(&CbValue::Bool(true)),
        "re-revoke must not error"
    );
    assert_eq!(
        count_nodes(&mut client_a, "federation_peer_revoked:"),
        crl_after_first,
        "re-revoking the same peer with the same body must be content-hash idempotent"
    );

    client_a.shutdown().expect("shutdown A");
}
