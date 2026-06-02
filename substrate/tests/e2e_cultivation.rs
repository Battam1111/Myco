//! E2E: COV06 不弃不孤 — cultivator-mortality + succession FSM.
//!
//! Spawns the real `myco-substrate` binary (which spawns the Python kernel
//! worker) and drives the COV06 cultivation-succession FSM end-to-end across all
//! three languages via the M5 protocol as the operator:
//!
//!   - heartbeat (valid anchor sig) → cultivator_heartbeat_recorded event.
//!   - heartbeat (bad sig) → rejected; no event.
//!   - stale anchor clock → cultivator_heartbeat_stale + FSM=alive::legacy.
//!   - empty successor_chain + stale → cultivation_orphaned (un-suppressible).
//!   - successor_chain + succession_acceptance → succession_completed FSM=normal.
//!   - catechumenate_session_count=12 → C46 (owner_succession_bypass).
//!   - alive::archived for LB bet-retirement.
//!   - cold-resume re-derives successor_chain identically.
//!
//! The substrate has NO anchor socket (AS §5.2 forbids self-clock); the operator
//! threads the anchor-signed envelopes in. In production the anchor signs; here
//! the operator's own seed-derived key is the pinned owner key, so signing with
//! the seed verifies. The autonomous staleness watchdog reads
//! `MYCO_TEST_ANCHOR_NOW_NS` (set per-subprocess, env-isolated) as "now".
//!
//! Mirrors the `e2e_schema_migration.rs` harness; shared spawn/build helpers live
//! in `tests/common/mod.rs`.

mod common;
use common::*;

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
use myco_kernel_shared::crypto::Ed25519PrivateKey;
use std::collections::BTreeMap;

const DAY_NS: i64 = 86_400_000_000_000;

// ---------------------------------------------------------------------------
// Signing-input reconstruction — MUST byte-match the Rust handler in
// substrate/src/cultivation.rs. One byte off breaks the signature check.
// ---------------------------------------------------------------------------

fn heartbeat_signing_input(
    substrate_id: &[u8; 32],
    cultivator_pubkey: &[u8; 32],
    anchor_ts: i64,
    valid_until: i64,
    nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("context".to_string(), Value::String("myco-cultivator-liveness-heartbeat-v1".to_string()));
    m.insert("substrate_id".to_string(), Value::Bytes(substrate_id.to_vec()));
    m.insert("cultivator_pubkey".to_string(), Value::Bytes(cultivator_pubkey.to_vec()));
    m.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(anchor_ts));
    m.insert("valid_until_unix_ns".to_string(), Value::Timestamp(valid_until));
    m.insert("heartbeat_nonce".to_string(), Value::Bytes(nonce.to_vec()));
    cb_encode(&Value::Map(m)).expect("encode").0
}

fn successor_chain_signing_input(
    substrate_id: &[u8; 32],
    successor_pubkey: &[u8; 32],
    valid_from: i64,
    valid_until: Option<i64>,
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("context".to_string(), Value::String("myco-successor-chain-entry-v1".to_string()));
    m.insert("substrate_id".to_string(), Value::Bytes(substrate_id.to_vec()));
    m.insert("successor_pubkey".to_string(), Value::Bytes(successor_pubkey.to_vec()));
    m.insert("valid_from_unix_ns".to_string(), Value::Timestamp(valid_from));
    m.insert(
        "valid_until_unix_ns".to_string(),
        match valid_until {
            Some(t) => Value::Timestamp(t),
            None => Value::Null,
        },
    );
    cb_encode(&Value::Map(m)).expect("encode").0
}

fn succession_acceptance_signing_input(
    substrate_id: &[u8; 32],
    successor_pubkey: &[u8; 32],
    prior_pubkey: &[u8; 32],
    anchor_ts: i64,
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert("context".to_string(), Value::String("myco-succession-acceptance-v1".to_string()));
    m.insert("substrate_id".to_string(), Value::Bytes(substrate_id.to_vec()));
    m.insert("successor_pubkey".to_string(), Value::Bytes(successor_pubkey.to_vec()));
    m.insert("prior_cultivator_pubkey".to_string(), Value::Bytes(prior_pubkey.to_vec()));
    m.insert("anchor_timestamp_unix_ns".to_string(), Value::Timestamp(anchor_ts));
    cb_encode(&Value::Map(m)).expect("encode").0
}

fn sign(seed: &[u8; 32], content: &[u8]) -> Vec<u8> {
    Ed25519PrivateKey::from_seed(seed).sign(content).as_ref().to_vec()
}

// ---------------------------------------------------------------------------
// Operator-side helpers.
// ---------------------------------------------------------------------------

/// Read the substrate_id by querying the genesis_event node.
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
    // The genesis node content carries substrate_id; decode the first node's content.
    let node = &nodes[0];
    let content = match node {
        CbValue::Map(m) => m.get("content_canonical_bytes").cloned(),
        _ => None,
    };
    if let Some(CbValue::Bytes(b)) = content {
        if let Ok(CbValue::Map(m)) = myco_kernel_shared::canonical_bytes::decode(&b) {
            if let Some(CbValue::Bytes(sid)) = m.get("substrate_id") {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(sid);
                return arr;
            }
        }
    }
    panic!("could not extract substrate_id from genesis node");
}

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

fn record_heartbeat(
    client: &mut BridgeClient,
    seed: &[u8; 32],
    sid: &[u8; 32],
    cpk: &[u8; 32],
    anchor_ts: i64,
    nonce: u8,
    valid_sig: bool,
) -> Result<std::collections::BTreeMap<String, CbValue>, String> {
    let nonce_arr = [nonce; 32];
    let valid_until = anchor_ts + 30 * DAY_NS;
    let signing_input = heartbeat_signing_input(sid, cpk, anchor_ts, valid_until, &nonce_arr);
    let sig = if valid_sig {
        sign(seed, &signing_input)
    } else {
        vec![0u8; 64]
    };
    client
        .call(
            proto::RECORD_CULTIVATOR_HEARTBEAT,
            build_payload(vec![
                ("cultivator_pubkey", CbValue::Bytes(cpk.to_vec())),
                ("anchor_timestamp_unix_ns", CbValue::Timestamp(anchor_ts)),
                ("valid_until_unix_ns", CbValue::Timestamp(valid_until)),
                ("heartbeat_nonce", CbValue::Bytes(nonce_arr.to_vec())),
                ("anchor_signature", CbValue::Bytes(sig)),
            ]),
        )
        .map(|r| r.payload)
        .map_err(|e| e.to_string())
}

fn update_successor(
    client: &mut BridgeClient,
    seed: &[u8; 32],
    sid: &[u8; 32],
    succ: &[u8; 32],
    valid_from: i64,
    valid_until: Option<i64>,
) -> Result<std::collections::BTreeMap<String, CbValue>, String> {
    let signing_input = successor_chain_signing_input(sid, succ, valid_from, valid_until);
    let sig = sign(seed, &signing_input);
    client
        .call(
            proto::UPDATE_SUCCESSOR_CHAIN,
            build_payload(vec![
                ("successor_pubkey", CbValue::Bytes(succ.to_vec())),
                ("valid_from_unix_ns", CbValue::Timestamp(valid_from)),
                (
                    "valid_until_unix_ns",
                    match valid_until {
                        Some(t) => CbValue::Timestamp(t),
                        None => CbValue::Null,
                    },
                ),
                ("attestation_signature", CbValue::Bytes(sig)),
            ]),
        )
        .map(|r| r.payload)
        .map_err(|e| e.to_string())
}

fn accept_succession(
    client: &mut BridgeClient,
    successor_seed: &[u8; 32],
    sid: &[u8; 32],
    prior_pk: &[u8; 32],
    anchor_ts: i64,
    session_count: u64,
) -> Result<std::collections::BTreeMap<String, CbValue>, String> {
    let succ_pk = Ed25519PrivateKey::from_seed(successor_seed).public_key().0;
    let signing_input = succession_acceptance_signing_input(sid, &succ_pk, prior_pk, anchor_ts);
    let sig = sign(successor_seed, &signing_input);
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
        .map(|r| r.payload)
        .map_err(|e| e.to_string())
}

fn get_string(payload: &std::collections::BTreeMap<String, CbValue>, key: &str) -> String {
    match payload.get(key) {
        Some(CbValue::String(s)) => s.clone(),
        _ => String::new(),
    }
}

/// Poll for a node-prefix count to reach `want` (or timeout). The autonomous
/// staleness watchdog runs on the substrate's idle `recv_timeout` branch, so we
/// must let the substrate sit idle (no operator frames) for several tick
/// intervals. We sleep in the TEST thread (not via the Bash `sleep` command);
/// each iteration leaves the substrate idle so its tick fires. Returns the final
/// count observed (the caller asserts).
fn poll_count_until(client: &mut BridgeClient, prefix: &str, want: usize, max_iters: u32) -> usize {
    let mut last = count_nodes(client, prefix);
    let mut i = 0;
    while last < want && i < max_iters {
        // Idle window: the substrate's main loop hits recv_timeout → tick fires.
        std::thread::sleep(std::time::Duration::from_millis(120));
        last = count_nodes(client, prefix);
        i += 1;
    }
    last
}

// ===========================================================================
// 1. Heartbeat happy path + bad signature.
// ===========================================================================

#[test]
fn heartbeat_valid_sig_records_event_bad_sig_rejected() {
    let seed: [u8; 32] = [0x11; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);
    let sid = substrate_id(&mut client);
    let cpk = derive_operator_pubkey_from_seed(&seed);

    // Valid signature → recorded.
    let resp = record_heartbeat(&mut client, &seed, &sid, &cpk, 1000, 0x01, true).expect("ok");
    assert!(matches!(resp.get("resumed"), Some(CbValue::Bool(false))));
    assert_eq!(count_nodes(&mut client, "cultivator_heartbeat_recorded"), 1);

    // Bad signature → rejected (BridgeError), no new event.
    let err = record_heartbeat(&mut client, &seed, &sid, &cpk, 2000, 0x02, false);
    assert!(err.is_err(), "bad anchor signature must be rejected");
    assert_eq!(
        count_nodes(&mut client, "cultivator_heartbeat_recorded"),
        1,
        "rejected heartbeat must not add an event"
    );
}

// ===========================================================================
// 2. Stale clock → cultivator_heartbeat_stale (T1) → FSM legacy → orphaned (T4).
//    Empty successor_chain → orphan fires.
// ===========================================================================

#[test]
fn stale_clock_emits_stale_then_orphaned_with_empty_chain() {
    let seed: [u8; 32] = [0x22; 32];
    let dir = fresh_state_dir();
    // Anchor "now" = 100 days; cadence default 30d → threshold 90d → stale.
    // Short tick interval so the idle watchdog fires quickly during the poll.
    let mut client = spawn_substrate_with_seed_and_env(
        &dir,
        seed,
        vec![
            ("MYCO_TICK_INTERVAL_MS".to_string(), "30".to_string()),
            ("MYCO_TEST_ANCHOR_NOW_NS".to_string(), (100 * DAY_NS).to_string()),
        ],
    );
    let sid = substrate_id(&mut client);
    let cpk = derive_operator_pubkey_from_seed(&seed);

    // Record a heartbeat at t=0 (so latest_heartbeat is set; now=100d → 100d stale).
    record_heartbeat(&mut client, &seed, &sid, &cpk, 0, 0x01, true).expect("hb");

    // T1: the idle watchdog emits cultivator_heartbeat_stale → FSM alive::legacy.
    let stale = poll_count_until(&mut client, "cultivator_heartbeat_stale:", 1, 40);
    assert!(stale >= 1, "T1: expected cultivator_heartbeat_stale, got {stale}");

    // T4: once legacy + empty successor_chain, the next idle tick emits
    // cultivation_orphaned (un-suppressible).
    let orphaned = poll_count_until(&mut client, "cultivation_orphaned:", 1, 40);
    assert!(
        orphaned >= 1,
        "T4: empty successor_chain in legacy must emit cultivation_orphaned, got {orphaned}"
    );
}

// ===========================================================================
// 3. successor_chain + succession_acceptance → succession_completed (T3) FSM=normal.
//    (The seed-derived owner key signs the chain; a distinct successor key signs
//    the acceptance. Heartbeat is stale so C12 does not pre-empt.)
// ===========================================================================

#[test]
fn successor_chain_then_succession_completes() {
    let seed: [u8; 32] = [0x33; 32];
    let successor_seed: [u8; 32] = [0x99; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_seed_and_env(
        &dir,
        seed,
        vec![
            ("MYCO_SELF_DRIVEN_CYCLE_ADVANCE".to_string(), "1".to_string()),
            ("MYCO_TEST_ANCHOR_NOW_NS".to_string(), (100 * DAY_NS).to_string()),
        ],
    );
    let sid = substrate_id(&mut client);
    let owner_pk = derive_operator_pubkey_from_seed(&seed);
    let succ_pk = derive_operator_pubkey_from_seed(&successor_seed);

    // Populate a successor entry (closed interval so it is a valid F21 entry).
    let r = update_successor(&mut client, &seed, &sid, &succ_pk, 10 * DAY_NS, Some(50 * DAY_NS))
        .expect("update_successor");
    assert!(matches!(r.get("chain_length"), Some(CbValue::Uint(1))));
    assert_eq!(count_nodes(&mut client, "successor_chain_updated:"), 1);

    // Record a STALE heartbeat (t=0; now=100d → 100d > 90d threshold) so the
    // prior cultivator is "incapacitated" and C12 does not pre-empt.
    record_heartbeat(&mut client, &seed, &sid, &owner_pk, 0, 0x01, true).expect("hb");

    // Succession with 50 sessions (passes C46) + stale heartbeat (passes C12).
    let resp = accept_succession(&mut client, &successor_seed, &sid, &owner_pk, 100 * DAY_NS, 50)
        .expect("accept_succession should complete");
    assert_eq!(get_string(&resp, "cultivation_state"), "alive::normal");
    assert_eq!(count_nodes(&mut client, "succession_completed:"), 1);
    // owner_key_added emitted (FSM T3 effect).
    assert!(count_nodes(&mut client, "owner_key_added") >= 1);
}

// ===========================================================================
// 4. C46: catechumenate_session_count=12 → owner_succession_bypass.
// ===========================================================================

#[test]
fn succession_below_50_sessions_rejected_c46() {
    let seed: [u8; 32] = [0x44; 32];
    let successor_seed: [u8; 32] = [0x88; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_seed_and_env(
        &dir,
        seed,
        vec![("MYCO_TEST_ANCHOR_NOW_NS".to_string(), (100 * DAY_NS).to_string())],
    );
    let sid = substrate_id(&mut client);
    let owner_pk = derive_operator_pubkey_from_seed(&seed);

    // Stale heartbeat so C12 does not pre-empt C46.
    record_heartbeat(&mut client, &seed, &sid, &owner_pk, 0, 0x01, true).expect("hb");

    // 12 sessions (COV06 §10.2 borderline) → C46 rejection.
    let err = accept_succession(&mut client, &successor_seed, &sid, &owner_pk, 100 * DAY_NS, 12);
    assert!(err.is_err(), "12 sessions < 50 must be rejected (C46)");
    assert_eq!(count_nodes(&mut client, "succession_completed:"), 0);
    // C46 immune sporocarp emitted.
    assert!(
        count_nodes(&mut client, "immune:") >= 1,
        "expected a C46 owner_succession_bypass immune sporocarp"
    );
}

// ===========================================================================
// 5. alive::archived for LB bet-retirement: bet_retired_proposal (operator-
//    submitted as if from an LB quorum) + cultivator co-attest → bet_retired
//    seal → metabolism halts (advance refused).
// ===========================================================================

#[test]
fn bet_retired_proposal_emitted_at_terminal_window() {
    let seed: [u8; 32] = [0x55; 32];
    let dir = fresh_state_dir();
    // Orphan + terminal: anchor-now far past the 730d terminal window, choice=
    // bet_retirement, self-driven scheduler ON so the watchdog walks the FSM
    // normal→legacy→orphaned→terminal across autonomous ticks.
    let mut client = spawn_substrate_with_seed_and_env(
        &dir,
        seed,
        vec![
            ("MYCO_TICK_INTERVAL_MS".to_string(), "30".to_string()),
            ("MYCO_TEST_ANCHOR_NOW_NS".to_string(), (900 * DAY_NS).to_string()),
            ("MYCO_TEST_CULTIVATION_TERMINAL_CHOICE".to_string(), "bet_retirement".to_string()),
        ],
    );
    let sid = substrate_id(&mut client);
    let owner_pk = derive_operator_pubkey_from_seed(&seed);
    // Record a heartbeat at t=0 (now=900d → 900d stale > all windows).
    record_heartbeat(&mut client, &seed, &sid, &owner_pk, 0, 0x01, true).expect("hb");
    // The idle watchdog walks the FSM across ticks: T1 (legacy) → T4 (orphaned)
    // → T7 (bet_retired_proposal). Poll for the terminal proposal.
    let proposals = poll_count_until(&mut client, "bet_retired_proposal", 1, 80);
    assert!(
        proposals >= 1,
        "T7: terminal window + bet_retirement choice must emit bet_retired_proposal, got {proposals}"
    );
    // The substrate is now alive::orphaned with a terminal proposal pending; an
    // operator co-attestation (accept_bet_retired_proposal) would seal it to
    // alive::archived (covered by the cultivation.rs unit tests + the metabolism
    // guard). We assert the proposal landed end-to-end here.
}

// ===========================================================================
// 6b. C69: a mutation attempting to suppress cultivation_orphaned is REFUSED
//     at the skin (covenant_violation; un-suppressible per COV06 §5.5).
// ===========================================================================

#[test]
fn c69_cultivation_orphaned_suppression_refused() {
    let seed: [u8; 32] = [0x6c; 32];
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_signing_seed(&dir, seed);

    // Submit a suppression mutation (no valid attestation needed — it is
    // rejected at the early skin gate before classification, like C56).
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("suppress_cultivation_orphaned".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(vec![])),
                ("attestation_signature", CbValue::Bytes(vec![0u8; 64])),
                ("touched_fields", CbValue::Array(vec![])),
                ("touched_files", CbValue::Array(vec![])),
                ("touched_meta_structures", CbValue::Array(vec![])),
            ]),
        )
        .expect("submit_mutation call");
    assert!(
        matches!(resp.payload.get("accepted"), Some(CbValue::Bool(false))),
        "C69: cultivation_orphaned suppression must be refused"
    );
    assert!(
        matches!(
            resp.payload.get("classification"),
            Some(CbValue::String(s)) if s == "covenant_violation"
        ),
        "C69 rejection classified as covenant_violation"
    );
    // C69 immune sporocarp emitted.
    assert!(
        count_nodes(&mut client, "immune:C69") >= 1,
        "C69_cultivation_orphaned_suppression_attempted immune sporocarp emitted"
    );
}

// ===========================================================================
// 6. Cold-resume re-derives successor_chain identically.
// ===========================================================================

#[test]
fn cold_resume_rederives_successor_chain() {
    let seed: [u8; 32] = [0x66; 32];
    let dir = fresh_state_dir();
    let succ1 = [0xA1u8; 32];
    let succ2 = [0xA2u8; 32];
    {
        let mut client = spawn_substrate_with_signing_seed(&dir, seed);
        let sid = substrate_id(&mut client);
        // Two successor entries (non-overlapping, monotone).
        update_successor(&mut client, &seed, &sid, &succ1, 10 * DAY_NS, Some(20 * DAY_NS))
            .expect("succ1");
        update_successor(&mut client, &seed, &sid, &succ2, 30 * DAY_NS, Some(40 * DAY_NS))
            .expect("succ2");
        assert_eq!(count_nodes(&mut client, "successor_chain_updated:"), 2);
        // Pump cycles past the snapshot interval (K=10) so a snapshot.cb lands —
        // this exercises the snapshot-accelerated boot path (tail replay) where
        // cultivation events predate the snapshot tip.
        pump_cycles(&mut client, 15);
        client.call(proto::SHUTDOWN, build_payload(vec![])).ok();
    }
    // Cold-resume: the chain must re-derive from the DAG identically (the 2
    // successor_chain_updated events are replayed / re-derived at boot).
    {
        let mut client = spawn_substrate_with_signing_seed(&dir, seed);
        assert_eq!(
            count_nodes(&mut client, "successor_chain_updated:"),
            2,
            "cold-resume must re-derive both successor_chain entries from the DAG"
        );
        // And a NEW append must compute chain_position=2 (proving the in-memory
        // mirror was rebuilt — not reset to empty).
        let sid = substrate_id(&mut client);
        let succ3 = [0xA3u8; 32];
        let r = update_successor(&mut client, &seed, &sid, &succ3, 50 * DAY_NS, Some(60 * DAY_NS))
            .expect("succ3 after resume");
        assert!(
            matches!(r.get("chain_length"), Some(CbValue::Uint(3))),
            "post-resume append must extend the re-derived chain to length 3"
        );
    }
}
