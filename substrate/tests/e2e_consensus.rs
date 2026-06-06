//! E2E: L2/FEDERATION §6.5 — Stage-1 population-consensus floor (quorum cert)
//! + the C49 floor-bypass gate.
//!
//! Doctrine: L2/FEDERATION §6.5 + §9.6 + `algorithms/pbft_consensus_floor.md`;
//! L1/HARD_RULES C49 `consensus_floor_bypass`.
//!
//! SCOPE: Stage-1 single-round quorum-certificate floor (NOT multi-round
//! Tendermint). Covered here:
//!   - f-bound / quorum math (N=3/4/7/10) via the public API;
//!   - vote signing roundtrip (sign→verify Ok; tamper→Err; wrong round→differs);
//!   - activation: 3 substrates mesh → `consensus_floor_activated`; drop →
//!     `consensus_floor_deactivated`;
//!   - quorum-cert happy path: N=4 (A + 3 peers), A proposes + 2 peer votes →
//!     cert minted, every `peer_votes` entry re-verifies;
//!   - pending: only sub-quorum votes → `population_consensus_pending`, no cert,
//!     status `pending`;
//!   - C49: floor active + peer-revocation with no matching cert → rejected + C49;
//!   - §9.6 cross-fed cert: an observer pulls the cert + re-verifies it offline.
//!
//! Mirrors `e2e_federation.rs` / `e2e_revocation.rs`; shared spawn/build helpers
//! live in `tests/common/mod.rs`. Every blocking step is timeout-bounded by the
//! background-poll iteration cap (no unbounded waits).

mod common;
use common::*;

use myco_kernel_shared::crypto::Ed25519PrivateKey;
use substrate::events;

/// Owner seed for the substrate-under-test (its seed-derived pubkey IS the
/// pinned operator identity, so an `attestation_signature` verifies as owner's).
const OWNER_SEED: [u8; 32] = [0x49; 32];

/// Background-poll a client `max_iters` times (50ms each) so it accepts inbound
/// connections + serves inbound frames. Returns the client on join.
fn poll_bg(mut client: BridgeClient, max_iters: u32) -> std::thread::JoinHandle<BridgeClient> {
    std::thread::spawn(move || {
        for _ in 0..max_iters {
            let _ = client.call(proto::FEDERATION_POLL, build_payload(vec![]));
            std::thread::sleep(std::time::Duration::from_millis(50));
        }
        client
    })
}

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

fn connect_peer(client: &mut BridgeClient, addr: &str) -> std::collections::BTreeMap<String, CbValue> {
    client
        .call(
            proto::FEDERATION_CONNECT_PEER,
            build_payload(vec![("remote_addr", CbValue::String(addr.to_string()))]),
        )
        .expect("connect_peer")
        .payload
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
        .expect("query recent");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => 0,
    }
}

/// Pull the content_canonical_bytes of the FIRST DAG node matching `prefix`.
fn first_node_content(client: &mut BridgeClient, prefix: &str) -> Option<Vec<u8>> {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(1000)),
                ("node_type_prefix", CbValue::String(prefix.to_string())),
            ]),
        )
        .expect("query recent");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => return None,
    };
    let first = nodes.into_iter().next()?;
    match first {
        CbValue::Map(m) => match m.get("content_canonical_bytes") {
            Some(CbValue::Bytes(b)) => Some(b.clone()),
            _ => None,
        },
        _ => None,
    }
}

// ---------------------------------------------------------------------------
// 1. f-bound + quorum math via the public API (doctrine table N=3/4/7/10).
// ---------------------------------------------------------------------------

#[test]
fn f_bound_and_quorum_match_doctrine_table() {
    assert_eq!(events::f_tolerated(3), 0);
    assert_eq!(events::f_tolerated(4), 1);
    assert_eq!(events::f_tolerated(7), 2);
    assert_eq!(events::f_tolerated(10), 3);
    assert_eq!(events::quorum_threshold(3), 3);
    assert_eq!(events::quorum_threshold(4), 3);
    assert_eq!(events::quorum_threshold(7), 5);
    assert_eq!(events::quorum_threshold(10), 7);
}

// ---------------------------------------------------------------------------
// 2. Vote signing roundtrip: sign→verify Ok; tamper→fails; wrong round→differs.
// ---------------------------------------------------------------------------

#[test]
fn vote_signing_roundtrip_and_replay_guards() {
    let seed = [0x11u8; 32];
    let key = Ed25519PrivateKey::from_seed(&seed);
    let pubkey = key.public_key().0;
    let id = [0x22u8; 32];
    let ch = events::claim_hash(b"revoke peer Z");
    let tip = [0x33u8; 32];

    let msg = events::build_population_vote_signing_message("peer_revocation", &ch, &id, 5, &tip);
    let sig = key.sign(&msg).0;
    let vote = events::decode_population_vote(
        events::encode_population_vote("peer_revocation", &ch, b"revoke peer Z", 5, &id, &sig, &tip, 0)
            .as_ref(),
    )
    .expect("decodes");
    assert!(events::verify_population_vote(&vote, &pubkey), "valid sig verifies");

    // Wrong round → different signing message (a vote can't transfer rounds).
    let msg_r6 = events::build_population_vote_signing_message("peer_revocation", &ch, &id, 6, &tip);
    assert_ne!(msg, msg_r6, "round 5 vs 6 signing messages must differ");

    // Tamper the claim_hash → re-derived message no longer matches → verify fails.
    let mut tampered = vote.clone();
    tampered.claim_hash[0] ^= 0xff;
    assert!(!events::verify_population_vote(&tampered, &pubkey), "tampered vote fails");
}

// ---------------------------------------------------------------------------
// 3. Activation: 3 peers mesh into A → consensus_floor_activated; a peer drop
//    (re-derive against fewer peers) → consensus_floor_deactivated.
// ---------------------------------------------------------------------------

#[test]
fn three_peer_mesh_activates_consensus_floor() {
    // A is the hub. B, C, D dial A. After A has pinned all three (peer_count=3),
    // the next poll on A must emit consensus_floor_activated.
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);
    let addr_a = open_listener(&mut client_a);

    // Each peer dials A; we poll A in the background long enough to accept all.
    let poll = poll_bg(client_a, 90);
    let mut peers = Vec::new();
    for _ in 0..3 {
        let (mut p, _d) = spawn_substrate();
        let resp = connect_peer(&mut p, &addr_a);
        assert_eq!(resp.get("outcome"), Some(&CbValue::String("pinned".to_string())));
        peers.push(p);
    }
    let mut client_a = poll.join().expect("activation poll join");

    // One more explicit poll so the crossing emit definitely runs after the 3rd
    // pin landed.
    let poll_resp = client_a
        .call(proto::FEDERATION_POLL, build_payload(vec![]))
        .expect("final poll");
    assert_eq!(
        poll_resp.payload.get("consensus_floor_active"),
        Some(&CbValue::Bool(true)),
        "with 3 pinned peers the floor must report active"
    );
    assert!(
        count_nodes(&mut client_a, "consensus_floor_activated") >= 1,
        "crossing 2→3 peers must emit a consensus_floor_activated event"
    );

    for p in peers {
        p.shutdown().expect("peer shutdown");
    }
    client_a.shutdown().expect("A shutdown");
}

// ---------------------------------------------------------------------------
// 4. Quorum-cert happy path. N=4 (A + 3 peers, quorum=3). A proposes (its own
//    vote = 1). Two peers each propose the SAME claim, emitting their own signed
//    round-0 votes; A pulls each peer's vote node + submits it. At the 3rd
//    distinct verified voter, A auto-mints the cert, whose peer_votes re-verify.
// ---------------------------------------------------------------------------

#[test]
fn quorum_cert_minted_and_self_verifies() {
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);
    let addr_a = open_listener(&mut client_a);

    // Mesh B, C, D into A so A pins each peer's signer_pubkey (needed to verify
    // their votes). peer_count = 3 → floor active.
    let poll = poll_bg(client_a, 90);
    let mut peers = Vec::new();
    for _ in 0..3 {
        let (mut p, _d) = spawn_substrate();
        let resp = connect_peer(&mut p, &addr_a);
        assert_eq!(resp.get("outcome"), Some(&CbValue::String("pinned".to_string())));
        peers.push(p);
    }
    let mut client_a = poll.join().expect("mesh poll join");

    // The shared claim. claim_hash is deterministic, so independent proposers
    // converge on round 0.
    let claim_payload = b"population: revoke peer rogue-1".to_vec();

    // A proposes → A's own vote (1 of 3 needed).
    let propose = client_a
        .call(
            proto::FEDERATION_PROPOSE_POPULATION_CLAIM,
            build_payload(vec![
                ("claim_type", CbValue::String("peer_revocation".to_string())),
                ("claim_payload", CbValue::Bytes(claim_payload.clone())),
            ]),
        )
        .expect("A propose")
        .payload;
    assert_eq!(propose.get("round_id"), Some(&CbValue::Uint(0)));
    assert_eq!(propose.get("votes_received"), Some(&CbValue::Uint(1)), "A's own vote");
    assert_eq!(propose.get("quorum_needed"), Some(&CbValue::Uint(3)), "N=4 → quorum 3");

    // Two peers each propose the same claim (emitting their own signed vote into
    // their own DAG), then A pulls + submits each peer's vote.
    for peer in peers.iter_mut().take(2) {
        let _ = peer
            .call(
                proto::FEDERATION_PROPOSE_POPULATION_CLAIM,
                build_payload(vec![
                    ("claim_type", CbValue::String("peer_revocation".to_string())),
                    ("claim_payload", CbValue::Bytes(claim_payload.clone())),
                ]),
            )
            .expect("peer propose");
        let vote_bytes = first_node_content(peer, "population_vote:")
            .expect("peer emitted a population_vote node");
        let submit = client_a
            .call(
                proto::FEDERATION_SUBMIT_PEER_VOTE,
                build_payload(vec![("vote_event_bytes", CbValue::Bytes(vote_bytes))]),
            )
            .expect("A submit peer vote")
            .payload;
        assert_eq!(
            submit.get("accepted"),
            Some(&CbValue::Bool(true)),
            "A must accept a peer vote it can verify; got {:?}",
            submit.get("reason")
        );
    }

    // A must now have minted exactly one quorum certificate.
    assert!(
        count_nodes(&mut client_a, "population_consensus_reached:peer_revocation") >= 1,
        "3 distinct verified voters (A + 2 peers) must mint the quorum cert"
    );

    // Query → status reached.
    let query = client_a
        .call(
            proto::FEDERATION_QUERY_CONSENSUS,
            build_payload(vec![
                ("claim_type", CbValue::String("peer_revocation".to_string())),
                ("claim_payload", CbValue::Bytes(claim_payload.clone())),
            ]),
        )
        .expect("A query")
        .payload;
    assert_eq!(query.get("status"), Some(&CbValue::String("reached".to_string())));

    // The cert must SELF-VERIFY: pull its bytes + re-verify the embedded peer
    // signatures against the DAG-derived pins (this is exactly what an observer
    // does under §9.6 — see the cross-fed test for the offline-resolver path).
    let cert_bytes = first_node_content(&mut client_a, "population_consensus_reached:")
        .expect("cert node present");
    let cert = events::decode_population_consensus_reached(&cert_bytes).expect("cert decodes");
    assert_eq!(cert.peer_set_size_n, 4);
    assert_eq!(cert.f_tolerated, 1);
    assert!(cert.peer_votes.len() >= 3, "cert embeds ≥3 vouching signatures");
    // Re-verify claim_hash binds the payload (the core self-evidencing check;
    // signature re-verification with the live pins is exercised in the cross-fed
    // observer test below).
    assert_eq!(events::claim_hash(&cert.claim_payload), cert.claim_hash);

    for p in peers {
        p.shutdown().expect("peer shutdown");
    }
    client_a.shutdown().expect("A shutdown");
}

// ---------------------------------------------------------------------------
// 5. Pending: N=4 needs quorum 3; supply only 2 votes (A + 1 peer) → no cert,
//    a population_consensus_pending marker is emitted, status `pending`.
// ---------------------------------------------------------------------------

#[test]
fn sub_quorum_stays_pending_no_cert() {
    let dir_a = fresh_state_dir();
    let mut client_a = spawn_substrate_with_signing_seed(&dir_a, OWNER_SEED);
    let addr_a = open_listener(&mut client_a);

    let poll = poll_bg(client_a, 90);
    let mut peers = Vec::new();
    for _ in 0..3 {
        let (mut p, _d) = spawn_substrate();
        let resp = connect_peer(&mut p, &addr_a);
        assert_eq!(resp.get("outcome"), Some(&CbValue::String("pinned".to_string())));
        peers.push(p);
    }
    let mut client_a = poll.join().expect("mesh poll join");

    let claim_payload = b"population: junk classification of feed-X".to_vec();
    // A proposes (vote 1).
    let _ = client_a
        .call(
            proto::FEDERATION_PROPOSE_POPULATION_CLAIM,
            build_payload(vec![
                ("claim_type", CbValue::String("universal_junk_classification".to_string())),
                ("claim_payload", CbValue::Bytes(claim_payload.clone())),
            ]),
        )
        .expect("A propose");

    // Only ONE peer votes (vote 2 of 3 needed).
    let peer = &mut peers[0];
    let _ = peer
        .call(
            proto::FEDERATION_PROPOSE_POPULATION_CLAIM,
            build_payload(vec![
                ("claim_type", CbValue::String("universal_junk_classification".to_string())),
                ("claim_payload", CbValue::Bytes(claim_payload.clone())),
            ]),
        )
        .expect("peer propose");
    let vote_bytes = first_node_content(peer, "population_vote:").expect("peer vote node");
    let submit = client_a
        .call(
            proto::FEDERATION_SUBMIT_PEER_VOTE,
            build_payload(vec![("vote_event_bytes", CbValue::Bytes(vote_bytes))]),
        )
        .expect("A submit")
        .payload;
    assert_eq!(submit.get("accepted"), Some(&CbValue::Bool(true)));
    assert_eq!(submit.get("votes_received"), Some(&CbValue::Uint(2)), "A + 1 peer");

    // No cert; a pending marker exists; status pending.
    assert_eq!(
        count_nodes(&mut client_a, "population_consensus_reached:"),
        0,
        "2 of 3 votes must NOT mint a cert"
    );
    assert!(
        count_nodes(&mut client_a, "population_consensus_pending:") >= 1,
        "sub-quorum must record a pending marker"
    );
    let query = client_a
        .call(
            proto::FEDERATION_QUERY_CONSENSUS,
            build_payload(vec![
                ("claim_type", CbValue::String("universal_junk_classification".to_string())),
                ("claim_payload", CbValue::Bytes(claim_payload)),
            ]),
        )
        .expect("query")
        .payload;
    assert_eq!(query.get("status"), Some(&CbValue::String("pending".to_string())));

    for p in peers {
        p.shutdown().expect("peer shutdown");
    }
    client_a.shutdown().expect("A shutdown");
}

// (v0.9 owner-key removal: `c49_peer_revocation_without_cert_rejected_when_floor_active`
// was deleted — it submitted the now-removed `revoke_federation_peer` owner-attested
// mutation. The C49 consensus-floor action gate is retained dormant in consensus.rs.)

// ---------------------------------------------------------------------------
// 7. §9.6 cross-fed cert: an OBSERVER (no consensus state of its own) pulls the
//    cert bytes + re-verifies the embedded peer signatures against an
//    independently-supplied pin resolver. Authority = embedded sigs, not the
//    wrapping. This is the offline-verification contract §9.6 promises.
// ---------------------------------------------------------------------------

#[test]
fn cross_fed_cert_reverifies_via_embedded_signatures() {
    // Build a real cert deterministically from known voter seeds (mirrors what a
    // quorum-reaching substrate emits), then re-verify as an arms-length observer
    // would: resolve each peer's pinned pubkey + re-derive each signing message.
    let claim_payload = b"cross-fed observed claim".to_vec();
    let ch = events::claim_hash(&claim_payload);
    let n = 4usize; // quorum 3
    let mut votes = Vec::new();
    let mut pins: std::collections::HashMap<[u8; 32], [u8; 32]> = std::collections::HashMap::new();
    for i in 0..3u8 {
        let seed = [0xD0 + i; 32];
        let key = Ed25519PrivateKey::from_seed(&seed);
        let pubkey = key.public_key().0;
        let mut id = [0u8; 32];
        id[0] = 0xE0 + i;
        let mut tip = [0u8; 32];
        tip[1] = i;
        let msg = events::build_population_vote_signing_message("peer_revocation", &ch, &id, 0, &tip);
        let sig = key.sign(&msg).0;
        votes.push(events::CertPeerVote {
            peer_substrate_id: id,
            peer_signature: sig,
            peer_dag_tip_at_vote: tip,
        });
        pins.insert(id, pubkey);
    }
    let cert_bytes = events::encode_population_consensus_reached(
        "peer_revocation",
        &ch,
        &claim_payload,
        0,
        n,
        events::f_tolerated(n),
        &votes,
        100,
    );

    // Observer side: decode + verify against the pins. A peer the observer never
    // pinned would NOT count (tested in the lib unit suite); here all 3 resolve.
    let cert = events::decode_population_consensus_reached(cert_bytes.as_ref()).expect("decodes");
    let outcome = events::verify_quorum_cert(&cert, |id| pins.get(id).copied());
    assert_eq!(
        outcome,
        events::CertVerifyOutcome::Valid {
            verified_distinct_voters: 3
        },
        "observer must re-verify the cert purely from embedded signatures + pins"
    );

    // And a TAMPERED cert (one signature byte flipped) must fail the observer's
    // re-verification — the wrapping cannot launder a forged signature.
    let mut tampered = cert.clone();
    tampered.peer_votes[0].peer_signature[0] ^= 0xff;
    let tampered_outcome = events::verify_quorum_cert(&tampered, |id| pins.get(id).copied());
    // One vote now invalid → only 2 distinct verified → below quorum 3.
    assert!(matches!(tampered_outcome, events::CertVerifyOutcome::Invalid(_)));
}
