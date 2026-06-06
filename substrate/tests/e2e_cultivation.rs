//! E2E: COV06 不弃不孤 — cultivation-succession (KEYLESS v0.9).
//!
//! Spawns the real `myco-substrate` binary (which spawns the Python kernel
//! worker) and drives the surviving keyless cultivation-succession operations
//! end-to-end via the M5 protocol as the operator:
//!
//!   - successor_chain append (keyless; non-overlapping monotone intervals).
//!   - succession_acceptance (keyless; C46 catechumenate floor is the only gate).
//!   - catechumenate_session_count=12 → C46 (owner_succession_bypass).
//!   - C69 cultivation_orphaned suppression refusal.
//!   - cold-resume re-derives successor_chain identically.
//!
//! **v0.9 owner-key removal**: the cultivator-heartbeat handler + the
//! heartbeat-staleness watchdog (T1 stale / T4 orphaned / T6-T7 terminal-window
//! proposal emission) + the owner Ed25519 signature gates were removed with the
//! anchor surface. The E2E tests that exercised them (heartbeat sig, stale-clock
//! FSM walk, terminal-window bet_retired_proposal emission, and the owner-attested
//! whole-substrate destruction edge that depended on the watchdog minting the
//! proposal) are deleted; the keyless seal → archive → metabolism-halt path is
//! covered by `substrate/src/cultivation.rs`'s unit tests + the `is_archived`
//! metabolism guard.
//!
//! Mirrors the `e2e_schema_migration.rs` harness; shared spawn/build helpers live
//! in `tests/common/mod.rs`.

mod common;
use common::*;

use myco_kernel_shared::canonical_bytes::Value;

const DAY_NS: i64 = 86_400_000_000_000;

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
    let node = &nodes[0];
    let content = match node {
        CbValue::Map(m) => m.get("content_canonical_bytes").cloned(),
        _ => None,
    };
    if let Some(CbValue::Bytes(b)) = content {
        if let Ok(Value::Map(m)) = myco_kernel_shared::canonical_bytes::decode(&b) {
            if let Some(Value::Bytes(sid)) = m.get("substrate_id") {
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

/// Keyless `update_successor_chain` — no attestation signature.
fn update_successor(
    client: &mut BridgeClient,
    succ: &[u8; 32],
    valid_from: i64,
    valid_until: Option<i64>,
) -> Result<std::collections::BTreeMap<String, CbValue>, String> {
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
            ]),
        )
        .map(|r| r.payload)
        .map_err(|e| e.to_string())
}

/// Keyless `accept_succession` — only the C46 catechumenate floor gates it.
fn accept_succession(
    client: &mut BridgeClient,
    succ_pk: &[u8; 32],
    prior_pk: &[u8; 32],
    anchor_ts: i64,
    session_count: u64,
) -> Result<std::collections::BTreeMap<String, CbValue>, String> {
    client
        .call(
            proto::ACCEPT_SUCCESSION,
            build_payload(vec![
                ("successor_pubkey", CbValue::Bytes(succ_pk.to_vec())),
                ("prior_cultivator_pubkey", CbValue::Bytes(prior_pk.to_vec())),
                ("anchor_timestamp_unix_ns", CbValue::Timestamp(anchor_ts)),
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

// ===========================================================================
// 1. successor_chain + succession_acceptance → succession_completed (T3) FSM=normal.
//    Keyless: the C46 catechumenate floor is the only gate.
// ===========================================================================

#[test]
fn successor_chain_then_succession_completes() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    let _sid = substrate_id(&mut client);
    let owner_pk = [0xABu8; 32];
    let succ_pk = [0x99u8; 32];

    // Populate a successor entry (closed interval so it is a valid F21 entry).
    let r = update_successor(&mut client, &succ_pk, 10 * DAY_NS, Some(50 * DAY_NS))
        .expect("update_successor");
    assert!(matches!(r.get("chain_length"), Some(CbValue::Uint(1))));
    assert_eq!(count_nodes(&mut client, "successor_chain_updated:"), 1);

    // Succession with 50 sessions (passes C46). No owner signature, no
    // fresh-heartbeat C12 check, no owner_key_added side effect (all keyless now).
    let resp = accept_succession(&mut client, &succ_pk, &owner_pk, 100 * DAY_NS, 50)
        .expect("accept_succession should complete");
    assert_eq!(get_string(&resp, "cultivation_state"), "alive::normal");
    assert_eq!(count_nodes(&mut client, "succession_completed:"), 1);
    client.shutdown().expect("shutdown");
}

// ===========================================================================
// 2. C46: catechumenate_session_count=12 → owner_succession_bypass.
// ===========================================================================

#[test]
fn succession_below_50_sessions_rejected_c46() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    let _sid = substrate_id(&mut client);
    let owner_pk = [0xABu8; 32];
    let succ_pk = [0x88u8; 32];

    // 12 sessions (COV06 §10.2 borderline) → C46 rejection (the kept gate).
    let err = accept_succession(&mut client, &succ_pk, &owner_pk, 100 * DAY_NS, 12);
    assert!(err.is_err(), "12 sessions < 50 must be rejected (C46)");
    assert_eq!(count_nodes(&mut client, "succession_completed:"), 0);
    assert!(
        count_nodes(&mut client, "immune:C46") >= 1,
        "expected a C46 owner_succession_bypass immune sporocarp"
    );
    client.shutdown().expect("shutdown");
}

// ===========================================================================
// 3. C69: a mutation attempting to suppress cultivation_orphaned is REFUSED
//    at the skin (covenant_violation; un-suppressible per COV06 §5.5).
// ===========================================================================

#[test]
fn c69_cultivation_orphaned_suppression_refused() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);

    // Submit a suppression mutation (rejected at the early skin gate before
    // classification, like C56 — no attestation needed in keyless mode).
    let resp = client
        .call(
            proto::SUBMIT_MUTATION,
            build_payload(vec![
                ("mutation_type", CbValue::String("suppress_cultivation_orphaned".to_string())),
                ("content_canonical_bytes", CbValue::Bytes(vec![])),
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
    assert!(
        count_nodes(&mut client, "immune:C69") >= 1,
        "C69_cultivation_orphaned_suppression_attempted immune sporocarp emitted"
    );
    client.shutdown().expect("shutdown");
}

// ===========================================================================
// 4. Cold-resume re-derives successor_chain identically.
// ===========================================================================

#[test]
fn cold_resume_rederives_successor_chain() {
    let dir = fresh_state_dir();
    let succ1 = [0xA1u8; 32];
    let succ2 = [0xA2u8; 32];
    {
        let mut client = spawn_substrate_with_state_dir(&dir);
        let _sid = substrate_id(&mut client);
        // Two successor entries (non-overlapping, monotone).
        update_successor(&mut client, &succ1, 10 * DAY_NS, Some(20 * DAY_NS)).expect("succ1");
        update_successor(&mut client, &succ2, 30 * DAY_NS, Some(40 * DAY_NS)).expect("succ2");
        assert_eq!(count_nodes(&mut client, "successor_chain_updated:"), 2);
        // Pump cycles past the snapshot interval (K=10) so a snapshot.cb lands —
        // exercises the snapshot-accelerated boot path (tail replay) where
        // cultivation events predate the snapshot tip.
        pump_cycles(&mut client, 15);
        client.call(proto::SHUTDOWN, build_payload(vec![])).ok();
    }
    // Cold-resume: the chain must re-derive from the DAG identically.
    {
        let mut client = spawn_substrate_with_state_dir(&dir);
        assert_eq!(
            count_nodes(&mut client, "successor_chain_updated:"),
            2,
            "cold-resume must re-derive both successor_chain entries from the DAG"
        );
        // A NEW append must compute chain_position=2 (proving the in-memory
        // mirror was rebuilt — not reset to empty).
        let _sid = substrate_id(&mut client);
        let succ3 = [0xA3u8; 32];
        let r = update_successor(&mut client, &succ3, 50 * DAY_NS, Some(60 * DAY_NS))
            .expect("succ3 after resume");
        assert!(
            matches!(r.get("chain_length"), Some(CbValue::Uint(3))),
            "post-resume append must extend the re-derived chain to length 3"
        );
        client.shutdown().expect("shutdown");
    }
}
