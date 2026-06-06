//! **COV06 EDGE witness** — `test_F21_activation_requires_layer_d_catechumenate`.
//!
//! Doctrine: L0/cards/COV06_no_abandonment_succession.md §8.4 + §5.3 + §10.2.
//! Boundary: a successor F21 activation attempt WITHOUT ≥50 dual-signed Layer-D
//! Catechumenate sessions → owner_succession_bypass (C46). This is the
//! un-fabricable production gate: synthetic tests pass a count directly
//! (49 → C46 refusal; 50 → proceeds), but a real successor must accumulate 50
//! real dual-signed sessions before activation. META §6.3 floor is operational.
//!
//! **v0.9 owner-key removal**: `accept_succession` is KEYLESS now — the successor
//! Ed25519 signature gate + the C12 fresh-owner-heartbeat takeover guard were
//! removed with the anchor surface, so the C46 catechumenate floor is the sole
//! activation gate (which is exactly what this edge witness proves).

mod common;
use common::*;

const DAY_NS: i64 = 86_400_000_000_000;

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

/// Keyless `accept_succession` — only the C46 catechumenate floor gates it.
fn try_accept_succession(
    client: &mut BridgeClient,
    succ_pk: &[u8; 32],
    prior_pk: &[u8; 32],
    anchor_ts: i64,
    session_count: u64,
) -> Result<(), String> {
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
        .map(|_| ())
        .map_err(|e| e.to_string())
}

#[test]
fn test_F21_activation_requires_layer_d_catechumenate() {
    let dir = fresh_state_dir();
    let mut client = spawn_substrate_with_state_dir(&dir);
    let owner_pk = [0xABu8; 32];
    let succ_pk = [0xC3u8; 32];

    // BELOW the floor: 49 sessions → C46 owner_succession_bypass.
    let below = try_accept_succession(&mut client, &succ_pk, &owner_pk, 100 * DAY_NS, 49);
    assert!(below.is_err(), "49 sessions < 50 → succession MUST be refused (C46)");
    assert_eq!(
        count_nodes(&mut client, "succession_completed:"),
        0,
        "no succession_completed event when below the catechumenate floor"
    );
    assert!(
        count_nodes(&mut client, "immune:C46") >= 1,
        "C46 owner_succession_bypass immune sporocarp emitted"
    );

    // AT the floor: 50 sessions → succession proceeds (keyless).
    let at = try_accept_succession(&mut client, &succ_pk, &owner_pk, 101 * DAY_NS, 50);
    assert!(at.is_ok(), "50 sessions ≥ 50 → succession proceeds: {at:?}");
    assert_eq!(
        count_nodes(&mut client, "succession_completed:"),
        1,
        "META §6.3 floor is operational: 50 sessions activates F21 succession"
    );
    client.shutdown().expect("shutdown");
}
