//! E2E: P8 永恒繁衍 reproduction — cultivator co-attestation (P08 §3.2/§3.5/§5.1)
//! + generation discipline (forkbomb defense) + I7 spawn closure.
//!
//! **P08 §5.1 — cultivator co-attestation (C68).** Spawning a child substrate
//! is NOT a daily-mode mutation: it is a CI-class doctrine event that REQUIRES
//! the cultivator's `myco-spawn-cosign-v1` co-signature. The substrate verifies
//! the signed envelope BEFORE any side effect (pinned-identity → decode →
//! parent replay-guard → I7(a) static-schema → Ed25519 verify → §16.B rate
//! throttle); any failure → **C68 `reproduction_unattested_spawn`** immune
//! sporocarp + NO child DAG/file created (the §5.1 "daily-mode spawn = doctrine
//! collapse" signal). On success the child-id is the §5.6 owner-minted
//! `blake3(parent_id, spore_schema_hash, child_genesis_ts)`.
//!
//! **L1/GOVERNANCE §16 (F22) + L1/HARD_RULES C47/C48 — generation discipline.**
//! These guards run WITH a valid attestation (the co-attestation is the gate
//! *before* them; depth/quota still apply on a fully-attested spawn):
//! - **C47 `generation_depth_exceeded`** (§16.A): a substrate at
//!   `generation_depth == reproduction_lineage_depth_max` cannot sprout (child
//!   would be `+1` over the cap) UNLESS the cultivator's signed envelope carries
//!   `depth_override=true` (F22). Breach → refuse + immune C47.
//! - **C48 `reproduction_lifetime_quota_exceeded`** (§16.C QUOTA half): a
//!   substrate that has already spawned `reproduction_lifetime_quota` children
//!   cannot sprout again. Breach → refuse + immune C48.
//! - **§16.B rate throttle** (RATE half): two attested spawns must be ≥
//!   `reproduction_rate_min_interval` apart on the *anchor wall-clock* carried
//!   inside the cultivator-signed envelope (a clock-rewind is itself a refusal).
//!   Breach → refuse + immune C48 (rate).
//!
//! **P08 §3.5 — I7 spawn closure** is a three-party handshake exercised here:
//! (a) parent runs the child's STATIC-SCHEMA validation; (b) the cultivator's
//! co-sign lands as `genesis_attested:{child_prefix}` in the PARENT's DAG;
//! (c) the child runs its OWN I3 boot self-check (`birth_closure_pending` →
//! `birth_closure_complete`) as its first metabolic cycle before any operator
//! cycle.
//!
//! The deterministic test seams (`MYCO_TEST_REPRODUCTION_DEPTH_MAX`,
//! `MYCO_TEST_REPRODUCTION_QUOTA`, `MYCO_TEST_REPRODUCTION_RATE_MIN_INTERVAL_NS`,
//! `MYCO_GENERATION_DEPTH_OVERRIDE`) mirror the established
//! `MYCO_TEST_TIGHTEN_BUDGETS_FOR_C53` precedent; production runs at the §16
//! constitutional defaults (depth 10 / quota 100 / interval 24h).

mod common;
use common::*;

use myco_kernel_shared::canonical_bytes::decode as cb_decode;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value as Cb};
use myco_kernel_shared::crypto::Ed25519PrivateKey;
use std::collections::BTreeMap;

/// The known operator/owner signing seed every attested-spawn test pins. The
/// substrate, spawned via `spawn_substrate_with_signing_seed`, TOFU-pins the
/// matching pubkey; the test signs the spawn-cosign envelope with the matching
/// private key so the §3.5 gate-5 Ed25519 verify passes.
const KNOWN_SEED: [u8; 32] = [0x42u8; 32];

/// A round, distinct test anchor wall-clock base (ns) for the FIRST attested
/// spawn. Subsequent spawns in the same parent must advance this by ≥ the
/// effective rate interval (or the test sets the interval to 0).
const ANCHOR_TS_BASE_NS: i64 = 1_700_000_000_000_000_000;

// NOTE: `valid_spore_schema_bytes` + `read_substrate_id` are provided by
// `common` (shared with the federation suite). This file adds the
// reproduction-specific helpers below.

/// Build a spore-schema canonical-bytes blob MISSING one required field (the
/// rest present) — for the I7(a) static-schema-mismatch test. The hash is still
/// computed over THESE bytes (so gate-4 hash-match passes); the shape check
/// (gate-4 second half) is what must reject it.
fn spore_schema_bytes_missing_field(omit: &str) -> Vec<u8> {
    let mut m = BTreeMap::new();
    for field in [
        "schema_definitions",
        "canonical_bytes_serializer_spec",
        "sporocarp_type_tree",
        "classifier_dimension_table",
        "initial_appetite_axis_schema",
        "anchor_surface_config",
        "parent_immune_signal_summary",
    ] {
        if field != omit {
            m.insert(field.to_string(), Cb::String(format!("{field}_v1")));
        }
    }
    cb_encode(&Cb::Map(m)).expect("partial spore-schema encodes").0
}

/// The §5.6 owner-minted deterministic child-id:
/// `blake3(parent_id || spore_schema_hash || child_genesis_ts_le)`.
/// Mirrors `verify_spawn_co_attestation`'s minting so tests can re-derive it.
fn expected_child_id(
    parent_id: &[u8; 32],
    spore_schema_hash: &[u8; 32],
    child_genesis_ts: i64,
) -> [u8; 32] {
    let mut hasher = blake3::Hasher::new();
    hasher.update(parent_id);
    hasher.update(spore_schema_hash);
    hasher.update(&child_genesis_ts.to_le_bytes());
    hasher.finalize().into()
}

/// Build + sign a `myco-spawn-cosign-v1` envelope. Returns
/// `(envelope_bytes, signature_64, spore_schema_hash)`. Uses the substrate's
/// own `build_spawn_cosign_canonical_bytes` so the bytes byte-match what the
/// substrate decodes; signs with `Ed25519PrivateKey::from_seed(seed)`.
fn build_signed_cosign(
    seed: &[u8; 32],
    parent_id: &[u8; 32],
    spore_schema_bytes: &[u8],
    child_genesis_ts: i64,
    anchor_ts: i64,
    depth_override: bool,
) -> (Vec<u8>, [u8; 64], [u8; 32]) {
    let spore_schema_hash: [u8; 32] = blake3::hash(spore_schema_bytes).into();
    let anchor_nonce = [0x5au8; 32];
    let envelope = substrate::events::build_spawn_cosign_canonical_bytes(
        parent_id,
        &spore_schema_hash,
        child_genesis_ts,
        anchor_ts,
        &anchor_nonce,
        depth_override,
    );
    let key = Ed25519PrivateKey::from_seed(seed);
    let sig = key.sign(&envelope);
    let mut sig_arr = [0u8; 64];
    sig_arr.copy_from_slice(sig.as_ref());
    (envelope, sig_arr, spore_schema_hash)
}

/// Full attested-sprout call: builds + signs the cosign envelope for
/// `parent_id`, then sends the complete payload (envelope + signature +
/// spore-schema bytes + child_state_dir). Returns the raw `Result` so callers
/// can assert success or refusal.
#[allow(clippy::too_many_arguments)]
fn try_sprout_attested(
    client: &mut BridgeClient,
    child_dir: &std::path::Path,
    seed: &[u8; 32],
    parent_id: &[u8; 32],
    spore_schema_bytes: &[u8],
    child_genesis_ts: i64,
    anchor_ts: i64,
    depth_override: bool,
) -> Result<myco_kernel_bridge::protocol::Message, myco_kernel_bridge::BridgeError> {
    let (envelope, sig, _hash) = build_signed_cosign(
        seed,
        parent_id,
        spore_schema_bytes,
        child_genesis_ts,
        anchor_ts,
        depth_override,
    );
    send_sprout(client, child_dir, &envelope, &sig, spore_schema_bytes)
}

/// Send a SPROUT_CHILD with explicit (possibly hand-corrupted) attestation
/// fields. Used by the negative tests that tamper one field.
fn send_sprout(
    client: &mut BridgeClient,
    child_dir: &std::path::Path,
    envelope: &[u8],
    signature: &[u8],
    spore_schema_bytes: &[u8],
) -> Result<myco_kernel_bridge::protocol::Message, myco_kernel_bridge::BridgeError> {
    client.call(
        proto::SPROUT_CHILD,
        build_payload(vec![
            (
                "child_state_dir",
                CbValue::String(child_dir.to_string_lossy().into_owned()),
            ),
            (
                "spawn_cosign_envelope",
                CbValue::Bytes(envelope.to_vec()),
            ),
            (
                "attestation_signature",
                CbValue::Bytes(signature.to_vec()),
            ),
            (
                "spore_schema_canonical_bytes",
                CbValue::Bytes(spore_schema_bytes.to_vec()),
            ),
        ]),
    )
}

/// Count immune:* DAG nodes whose `node_type` contains `detector_id`.
fn count_immune(client: &mut BridgeClient, detector_id: &str) -> usize {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(100)),
                (
                    "node_type_prefix",
                    CbValue::String(format!("immune:{detector_id}")),
                ),
            ]),
        )
        .expect("query immune nodes");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => panic!("query_recent_nodes response missing 'nodes' array"),
    }
}

/// Count DAG nodes (in `client`'s substrate) whose node_type starts with
/// `prefix`.
fn count_nodes_with_prefix(client: &mut BridgeClient, prefix: &str) -> usize {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(200)),
                ("node_type_prefix", CbValue::String(prefix.to_string())),
            ]),
        )
        .expect("query nodes by prefix");
    match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.len(),
        _ => panic!("nodes missing"),
    }
}

/// Read the `generation_depth` recorded in a (booted) substrate's own
/// `genesis_event:*` DAG node. Absent field → 0 (root, byte-compat).
fn child_recorded_generation_depth(client: &mut BridgeClient) -> u64 {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(100)),
                (
                    "node_type_prefix",
                    CbValue::String("genesis_event:".to_string()),
                ),
            ]),
        )
        .expect("query genesis_event node");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    assert_eq!(
        nodes.len(),
        1,
        "a substrate must have exactly one genesis_event node; got {}",
        nodes.len()
    );
    let content = match &nodes[0] {
        CbValue::Map(m) => match m.get("content_canonical_bytes") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("genesis_event node missing content_canonical_bytes"),
        },
        _ => panic!("genesis_event node not a Map"),
    };
    let decoded = cb_decode(&content).expect("decode genesis_event content");
    match decoded {
        CbValue::Map(m) => match m.get("generation_depth") {
            Some(CbValue::Uint(n)) => *n,
            // Absent → 0 (root / pre-8f byte-compat).
            None => 0,
            other => panic!("generation_depth wrong type: {other:?}"),
        },
        _ => panic!("genesis_event content not a Map"),
    }
}

/// Spawn an attested-capable parent: seed-pinned owner identity + (by default)
/// the rate-throttle disabled so depth/quota tests can fire multiple sprouts
/// without §16.B interfering. Returns the booted client + its state dir + the
/// parent's substrate_id.
fn spawn_attested_parent(extra: Vec<(String, String)>) -> (BridgeClient, PathBuf, [u8; 32]) {
    let dir = fresh_state_dir();
    let mut env = vec![(
        // Disable the §16.B rate interval by default; rate tests override it.
        "MYCO_TEST_REPRODUCTION_RATE_MIN_INTERVAL_NS".to_string(),
        "0".to_string(),
    )];
    env.extend(extra);
    let mut client = spawn_substrate_with_seed_and_env(&dir, KNOWN_SEED, env);
    let id = read_substrate_id(&mut client);
    (client, dir, id)
}

// ===========================================================================
// P08 §5.1 / C68 — cultivator co-attestation gate
// ===========================================================================

#[test]
fn spawn_attested_succeeds_and_records_i7_closure() {
    // The happy path: a fully cultivator-co-signed spawn succeeds, the child
    // is created, the PARENT records a genesis_attested:{child_prefix} I7
    // closure, and the child-id is the §5.6 owner-minted deterministic id.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let spore_hash: [u8; 32] = blake3::hash(&spore).into();
    let child_genesis_ts = ANCHOR_TS_BASE_NS - 1_000_000; // slightly before anchor
    let child_dir = fresh_state_dir();
    let resp = try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        child_genesis_ts,
        ANCHOR_TS_BASE_NS,
        false,
    )
    .expect("attested spawn must succeed");

    // child_substrate_id == blake3(parent, spore_hash, child_genesis_ts).
    let want_child = expected_child_id(&parent_id, &spore_hash, child_genesis_ts);
    match resp.payload.get("child_substrate_id") {
        Some(CbValue::Bytes(b)) => assert_eq!(
            b.as_slice(),
            want_child.as_slice(),
            "child-id must be the §5.6 owner-minted blake3(parent, spore_hash, child_genesis_ts)"
        ),
        other => panic!("child_substrate_id missing/wrong: {other:?}"),
    }
    // The signed child genesis timestamp is surfaced.
    assert!(
        matches!(
            resp.payload.get("child_genesis_timestamp_unix_ns"),
            Some(CbValue::Timestamp(t)) if *t == child_genesis_ts
        ),
        "response must surface the signed child_genesis_timestamp_unix_ns"
    );
    // No C68 fired.
    assert_eq!(
        count_immune(&mut parent, "C68_reproduction_unattested_spawn"),
        0,
        "a valid attested spawn must NOT fire C68"
    );
    // The PARENT records exactly one genesis_attested:* I7-closure node.
    assert_eq!(
        count_nodes_with_prefix(&mut parent, "genesis_attested:"),
        1,
        "parent must record exactly one genesis_attested:{{child_prefix}} I7 closure"
    );
    // The child DAG file exists.
    assert!(
        child_dir.join("dag.cb").exists(),
        "a successful attested spawn must create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c68_unattested_spawn_refused_and_immune_no_child_dag() {
    // An UNSIGNED sprout (no spawn_cosign_envelope / signature / spore bytes)
    // is the §5.1 "daily-mode spawn = doctrine collapse" signal: refused, C68
    // immune sporocarp emitted, and NO child dag.cb created.
    let (mut parent, _dir, _parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let child_dir = fresh_state_dir();
    let result = client_unattested_sprout(&mut parent, &child_dir);
    assert!(
        result.is_err(),
        "C68: an unattested spawn must be REFUSED; got Ok"
    );
    assert_eq!(
        count_immune(&mut parent, "C68_reproduction_unattested_spawn"),
        1,
        "C68: exactly one reproduction_unattested_spawn immune node expected"
    );
    assert!(
        !child_dir.join("dag.cb").exists(),
        "C68: a refused unattested spawn must NOT create the child's dag.cb"
    );
    // And NO genesis_attested closure was recorded in the parent.
    assert_eq!(
        count_nodes_with_prefix(&mut parent, "genesis_attested:"),
        0,
        "C68: a refused spawn must NOT record a genesis_attested closure"
    );
    parent.shutdown().expect("shutdown parent");
}

/// Send the LEGACY unsigned sprout payload (child_state_dir only) — exercises
/// the C68 missing-envelope reject.
fn client_unattested_sprout(
    client: &mut BridgeClient,
    child_dir: &std::path::Path,
) -> Result<myco_kernel_bridge::protocol::Message, myco_kernel_bridge::BridgeError> {
    client.call(
        proto::SPROUT_CHILD,
        build_payload(vec![(
            "child_state_dir",
            CbValue::String(child_dir.to_string_lossy().into_owned()),
        )]),
    )
}

#[test]
fn c68_invalid_signature_refused() {
    // A well-formed envelope but a signature that does NOT verify against the
    // pinned owner pubkey → C68 (gate 5). We build a valid envelope, then flip
    // the signature bytes.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let (envelope, mut sig, _h) = build_signed_cosign(
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    );
    sig[0] ^= 0xFF; // corrupt the signature

    let child_dir = fresh_state_dir();
    let result = send_sprout(&mut parent, &child_dir, &envelope, &sig, &spore);
    assert!(
        result.is_err(),
        "C68: a spawn with an invalid signature must be REFUSED"
    );
    assert_eq!(
        count_immune(&mut parent, "C68_reproduction_unattested_spawn"),
        1,
        "C68: invalid-signature spawn must emit one C68 immune node"
    );
    assert!(
        !child_dir.join("dag.cb").exists(),
        "C68: invalid-signature spawn must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c68_wrong_parent_id_refused() {
    // An envelope minted for a DIFFERENT parent_substrate_id (replay guard,
    // gate 3) → C68, even though the signature is valid over those bytes.
    let (mut parent, _dir, _parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let wrong_parent = [0xeeu8; 32]; // not this substrate's id
    // Sign over the wrong-parent envelope with the correct key (so only the
    // parent-id mismatch — not the signature — triggers the refusal).
    let (envelope, sig, _h) = build_signed_cosign(
        &KNOWN_SEED,
        &wrong_parent,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    );

    let child_dir = fresh_state_dir();
    let result = send_sprout(&mut parent, &child_dir, &envelope, &sig, &spore);
    assert!(
        result.is_err(),
        "C68: an envelope minted for another parent must be REFUSED (replay guard)"
    );
    assert_eq!(
        count_immune(&mut parent, "C68_reproduction_unattested_spawn"),
        1,
        "C68: wrong-parent-id spawn must emit one C68 immune node"
    );
    assert!(
        !child_dir.join("dag.cb").exists(),
        "C68: wrong-parent-id spawn must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c68_unseeded_parent_cannot_attest() {
    // A substrate with NO pinned operator identity (legacy unseeded spawn)
    // cannot verify ANY co-attestation (gate 1) → every sprout is C68. This
    // is the regression guard that the co-attestation is mandatory: the old
    // unsigned path no longer silently spawns.
    let (mut parent, _dir) = spawn_substrate(); // unseeded — no pinned identity
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");
    // Even a "valid-looking" envelope can't verify with no pinned pubkey.
    let spore = valid_spore_schema_bytes();
    let parent_id = read_substrate_id(&mut parent);
    let child_dir = fresh_state_dir();
    let result = try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    );
    assert!(
        result.is_err(),
        "C68: an unseeded parent (no pinned identity) cannot attest a spawn"
    );
    assert_eq!(
        count_immune(&mut parent, "C68_reproduction_unattested_spawn"),
        1,
        "C68: unseeded parent must emit one C68 immune node on a spawn attempt"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn i7a_static_schema_mismatch_rejected() {
    // I7(a): the supplied spore_schema_canonical_bytes must (1) hash to the
    // co-signed spore_schema_hash AND (2) be a well-formed 7-field schema. Here
    // we co-sign over a MALFORMED schema (missing a required field) — the hash
    // matches (we sign over the same malformed bytes), so this isolates the
    // *shape* half of gate 4. Must reject with C68.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let bad_spore = spore_schema_bytes_missing_field("classifier_dimension_table");
    let child_dir = fresh_state_dir();
    // build_signed_cosign hashes `bad_spore` so gate-4 hash-match passes; the
    // shape check is what fires.
    let result = try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &bad_spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    );
    assert!(
        result.is_err(),
        "I7(a): a malformed (missing-field) spore-schema must be REFUSED"
    );
    assert_eq!(
        count_immune(&mut parent, "C68_reproduction_unattested_spawn"),
        1,
        "I7(a): static-schema mismatch must emit one C68 immune node"
    );
    assert!(
        !child_dir.join("dag.cb").exists(),
        "I7(a): a rejected spawn must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn i7a_spore_hash_mismatch_rejected() {
    // The other half of gate 4: the supplied spore bytes hash to something
    // OTHER than the co-signed spore_schema_hash (a swapped schema). We sign
    // over schema A but send schema B → C68.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore_a = valid_spore_schema_bytes();
    // Sign the envelope over spore_a's hash.
    let (envelope, sig, _h) = build_signed_cosign(
        &KNOWN_SEED,
        &parent_id,
        &spore_a,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    );
    // But SEND a different (still valid-shape) schema B.
    let mut m = BTreeMap::new();
    for field in [
        "schema_definitions",
        "canonical_bytes_serializer_spec",
        "sporocarp_type_tree",
        "classifier_dimension_table",
        "initial_appetite_axis_schema",
        "anchor_surface_config",
        "parent_immune_signal_summary",
    ] {
        m.insert(field.to_string(), Cb::String(format!("{field}_DIFFERENT")));
    }
    let spore_b = cb_encode(&Cb::Map(m)).unwrap().0;
    assert_ne!(spore_a, spore_b, "schemas A and B must differ");

    let child_dir = fresh_state_dir();
    let result = send_sprout(&mut parent, &child_dir, &envelope, &sig, &spore_b);
    assert!(
        result.is_err(),
        "I7(a): spore-hash mismatch (swapped schema) must be REFUSED"
    );
    assert_eq!(
        count_immune(&mut parent, "C68_reproduction_unattested_spawn"),
        1,
        "I7(a): spore-hash mismatch must emit one C68 immune node"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn i7_child_runs_i3_self_check_first_at_boot() {
    // P08 §3.5 I7 closure (b)→(c): a sprouted child carries a
    // birth_closure_pending marker (written by the parent right after the
    // child's genesis_event). On the child's FIRST boot it runs its OWN I3
    // self-check and emits birth_closure_complete. Assert the child's DAG has,
    // in order, genesis_event → birth_closure_pending → birth_closure_complete.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let child_dir = fresh_state_dir();
    try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    )
    .expect("attested spawn must succeed");
    parent.shutdown().expect("shutdown parent pre-child-boot");

    // Boot the child. The child INHERITED the parent's pinned operator identity
    // (the operator_pinned event is copied into the child's DAG at sprout), so
    // it must be re-booted WITH the same signing seed (an unseeded handshake
    // would be rejected as a downgrade, C2). Its first boot runs the I3
    // self-check and closes birth.
    let mut child = spawn_substrate_with_seed_and_env(&child_dir, KNOWN_SEED, vec![]);

    // birth_closure_pending must be present (written at sprout).
    assert_eq!(
        count_nodes_with_prefix(&mut child, "birth_closure_pending:"),
        1,
        "child DAG must carry exactly one birth_closure_pending marker"
    );
    // birth_closure_complete must be present after first boot (I3-first).
    assert_eq!(
        count_nodes_with_prefix(&mut child, "birth_closure_complete:"),
        1,
        "child's first boot must emit exactly one birth_closure_complete (I3-first)"
    );

    // Verify ORDERING + the I3 verdict via the full insertion-order DAG read:
    // genesis_event precedes birth_closure_pending precedes
    // birth_closure_complete; and birth_closure_complete records
    // i3_self_check_passed=true for a healthy child.
    let resp = child
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![("count", CbValue::Uint(500))]),
        )
        .expect("query all nodes");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    // QUERY_RECENT_NODES returns nodes in DAG INSERTION order (the handler
    // iterates `iter_in_insertion_order` then slices the last `count`), so the
    // array is already causal-order — no reversal needed.
    let mut types_insertion: Vec<String> = Vec::new();
    let mut complete_passed: Option<bool> = None;
    for n in &nodes {
        if let CbValue::Map(m) = n {
            if let Some(CbValue::String(nt)) = m.get("node_type") {
                types_insertion.push(nt.clone());
                if nt.starts_with("birth_closure_complete:") {
                    if let Some(CbValue::Bytes(b)) = m.get("content_canonical_bytes") {
                        if let Ok(CbValue::Map(cm)) = cb_decode(b) {
                            if let Some(CbValue::Bool(p)) = cm.get("i3_self_check_passed") {
                                complete_passed = Some(*p);
                            }
                        }
                    }
                }
            }
        }
    }
    let idx = |needle: &str| -> usize {
        types_insertion
            .iter()
            .position(|t| t.starts_with(needle))
            .unwrap_or_else(|| panic!("node {needle} not found in child DAG: {types_insertion:?}"))
    };
    let i_genesis = idx("genesis_event:");
    let i_pending = idx("birth_closure_pending:");
    let i_complete = idx("birth_closure_complete:");
    assert!(
        i_genesis < i_pending && i_pending < i_complete,
        "I7: child DAG order must be genesis_event → birth_closure_pending → \
         birth_closure_complete; got positions g={i_genesis} p={i_pending} c={i_complete}"
    );
    assert_eq!(
        complete_passed,
        Some(true),
        "I7(c): a healthy child's birth_closure_complete must record \
         i3_self_check_passed=true"
    );

    // Re-boot: the closure is idempotent — a second boot must NOT add another
    // birth_closure_complete (pending+complete already present). Re-boot WITH
    // the seed (inherited pinned identity).
    child.shutdown().expect("shutdown child first boot");
    let mut child2 = spawn_substrate_with_seed_and_env(&child_dir, KNOWN_SEED, vec![]);
    assert_eq!(
        count_nodes_with_prefix(&mut child2, "birth_closure_complete:"),
        1,
        "I7: birth closure must be idempotent — re-boot must NOT add a second \
         birth_closure_complete"
    );
    child2.shutdown().expect("shutdown child second boot");
}

// ===========================================================================
// §16.B rate throttle (RATE half of C48)
// ===========================================================================

#[test]
fn rate_throttle_second_too_soon_refused_far_apart_ok() {
    // Boot a parent with the §16.B interval forced to 1_000_000_000 ns (1s, in
    // anchor-clock units). The first attested spawn lands. A second spawn whose
    // signed anchor_timestamp is < interval later is refused with C48 (rate);
    // a third spawn far enough apart succeeds.
    let interval: i64 = 1_000_000_000; // 1s in ns
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![(
        "MYCO_TEST_REPRODUCTION_RATE_MIN_INTERVAL_NS".to_string(),
        interval.to_string(),
    )]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");
    let spore = valid_spore_schema_bytes();

    // Spawn #1 at anchor t0 — succeeds (no prior genesis_attested).
    let t0 = ANCHOR_TS_BASE_NS;
    let d1 = fresh_state_dir();
    try_sprout_attested(
        &mut parent, &d1, &KNOWN_SEED, &parent_id, &spore, t0 - 5, t0, false,
    )
    .expect("first attested spawn must succeed");
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        0,
        "rate: first spawn must NOT fire C48"
    );

    // Spawn #2 at t0 + interval/2 — too soon → C48 (rate), refused.
    let t_soon = t0 + interval / 2;
    let d2 = fresh_state_dir();
    let r2 = try_sprout_attested(
        &mut parent, &d2, &KNOWN_SEED, &parent_id, &spore, t_soon - 5, t_soon, false,
    );
    assert!(
        r2.is_err(),
        "rate: a second spawn < interval after the first must be REFUSED (§16.B)"
    );
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        1,
        "rate: too-soon spawn must emit exactly one C48 (rate) immune node"
    );
    assert!(
        !d2.join("dag.cb").exists(),
        "rate: a throttled spawn must NOT create the child's dag.cb"
    );

    // Spawn #3 at t0 + 2*interval — far enough apart → succeeds.
    let t_far = t0 + 2 * interval;
    let d3 = fresh_state_dir();
    try_sprout_attested(
        &mut parent, &d3, &KNOWN_SEED, &parent_id, &spore, t_far - 5, t_far, false,
    )
    .expect("rate: a far-apart spawn must succeed");
    assert!(
        d3.join("dag.cb").exists(),
        "rate: a far-apart spawn must create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn rate_throttle_anchor_clock_rewind_refused() {
    // §16.B clock-rewind guard: a second spawn whose signed anchor_timestamp is
    // <= the prior spawn's anchor_timestamp is a throttle-evasion signal →
    // refused, even with the interval otherwise satisfiable.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![(
        "MYCO_TEST_REPRODUCTION_RATE_MIN_INTERVAL_NS".to_string(),
        "1".to_string(),
    )]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");
    let spore = valid_spore_schema_bytes();

    let t0 = ANCHOR_TS_BASE_NS;
    let d1 = fresh_state_dir();
    try_sprout_attested(
        &mut parent, &d1, &KNOWN_SEED, &parent_id, &spore, t0 - 5, t0, false,
    )
    .expect("first spawn must succeed");

    // Second spawn with an EARLIER anchor stamp → rewind → refused.
    let t_back = t0 - 1_000;
    let d2 = fresh_state_dir();
    let r2 = try_sprout_attested(
        &mut parent, &d2, &KNOWN_SEED, &parent_id, &spore, t_back - 5, t_back, false,
    );
    assert!(
        r2.is_err(),
        "rate: an anchor clock-rewind (anchor_ts <= prior) must be REFUSED"
    );
    assert!(
        !d2.join("dag.cb").exists(),
        "rate: a rewind-refused spawn must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

// ===========================================================================
// C47 generation_depth_exceeded (§16.A) — WITH valid attestation
// ===========================================================================

#[test]
fn c47_positive_at_depth_max_refuses_and_emits() {
    // Parent boots with depth-max forced to 0 → a depth-0 root is AT the max,
    // so any sprout (child would be depth 1) must be refused with C47 — even
    // though the spawn is FULLY co-attested. (depth_override=false.)
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![(
        "MYCO_TEST_REPRODUCTION_DEPTH_MAX".to_string(),
        "0".to_string(),
    )]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let child_dir = fresh_state_dir();
    let result = try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false, // no depth_override
    );
    assert!(
        result.is_err(),
        "C47: an attested sprout at generation_depth == max must be REFUSED; got Ok"
    );
    // The breach must be recorded as an immune:C47 DAG node in the PARENT.
    assert_eq!(
        count_immune(&mut parent, "C47_generation_depth_exceeded"),
        1,
        "C47: exactly one C47_generation_depth_exceeded immune node expected"
    );
    // And NO child DAG must have been created (refuse-before-spawn).
    assert!(
        !child_dir.join("dag.cb").exists(),
        "C47: a refused sprout must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c47_positive_real_max_via_genesis_depth_override() {
    // End-to-end faithful variant: boot a substrate AT the real §16.A max
    // (depth 10) via the genesis-depth override. This exercises the full
    // depth-threading path at the production cap value, with NO test-only
    // depth-max override. A fully-attested sprout (no depth_override) is still
    // refused.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![(
        "MYCO_GENERATION_DEPTH_OVERRIDE".to_string(),
        "10".to_string(),
    )]);
    // Sanity: the substrate booted at depth 10 (read from its own genesis_event).
    assert_eq!(
        child_recorded_generation_depth(&mut parent),
        10,
        "parent must boot at generation_depth 10 via override"
    );
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let child_dir = fresh_state_dir();
    let result = try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    );
    assert!(
        result.is_err(),
        "C47: substrate at the real depth-max (10) must refuse to sprout"
    );
    assert_eq!(
        count_immune(&mut parent, "C47_generation_depth_exceeded"),
        1,
        "C47: real-max breach must emit C47"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c47_depth_override_past_max_succeeds() {
    // **§16.A depth_override (F22)**: the cultivator's signed envelope carries
    // depth_override=true. A substrate AT the depth cap may then sprout PAST it
    // for this one spawn — the override is honored because the signature
    // verified. C47 must NOT fire; a depth_override_exercised audit event is
    // recorded; the child is created at parent+1.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![(
        "MYCO_TEST_REPRODUCTION_DEPTH_MAX".to_string(),
        "0".to_string(),
    )]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let child_dir = fresh_state_dir();
    let resp = try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        true, // depth_override=true (cultivator-signed)
    )
    .expect("C47 depth_override: an over-cap spawn WITH signed override must succeed");

    // No C47 fired.
    assert_eq!(
        count_immune(&mut parent, "C47_generation_depth_exceeded"),
        0,
        "C47 depth_override: a signed override must NOT fire C47"
    );
    // An audit event records the override was exercised.
    assert_eq!(
        count_nodes_with_prefix(&mut parent, "depth_override_exercised"),
        1,
        "C47 depth_override: exactly one depth_override_exercised audit event expected"
    );
    // Child depth is parent (0) + 1 = 1.
    assert!(
        matches!(
            resp.payload.get("child_generation_depth"),
            Some(CbValue::Uint(1))
        ),
        "C47 depth_override: child_generation_depth must be parent+1=1; got {:?}",
        resp.payload.get("child_generation_depth")
    );
    assert!(
        child_dir.join("dag.cb").exists(),
        "C47 depth_override: an override-permitted spawn must create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c47_negative_below_max_sprouts_child_at_parent_plus_one() {
    // A normal root parent (depth 0, default max 10) is well below the cap →
    // the attested sprout SUCCEEDS, no C47 fires, and the child's genesis_event
    // records generation_depth = parent + 1 = 1.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");

    let spore = valid_spore_schema_bytes();
    let child_dir = fresh_state_dir();
    let resp = try_sprout_attested(
        &mut parent,
        &child_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    )
    .expect("C47 negative: attested sprout must succeed");

    // The response carries the child's depth = 1.
    assert!(
        matches!(resp.payload.get("child_generation_depth"), Some(CbValue::Uint(1))),
        "C47 negative: response child_generation_depth must be 1; got {:?}",
        resp.payload.get("child_generation_depth")
    );
    // No C47 immune node in the parent.
    assert_eq!(
        count_immune(&mut parent, "C47_generation_depth_exceeded"),
        0,
        "C47 negative: no C47 should fire for an under-max sprout"
    );
    parent.shutdown().expect("shutdown parent pre-child-boot");

    // Boot the child and confirm IT records generation_depth = 1 in its own
    // genesis_event (proves the additive field is threaded through the child's
    // DAG, the authoritative carrier the child reads at boot). The child
    // inherited the parent's pinned operator identity, so boot WITH the seed.
    let mut child = spawn_substrate_with_seed_and_env(&child_dir, KNOWN_SEED, vec![]);
    assert_eq!(
        child_recorded_generation_depth(&mut child),
        1,
        "C47 negative: child's genesis_event must record generation_depth = parent + 1"
    );
    child.shutdown().expect("shutdown child");
}

// ===========================================================================
// C48 reproduction_lifetime_quota_exceeded (§16.C, QUOTA half) — attested
// ===========================================================================

#[test]
fn c48_positive_over_quota_refuses_and_emits() {
    // Parent boots with the lifetime quota forced to 1 (rate disabled). The
    // FIRST attested sprout is allowed (count 0 + 1 <= 1). The SECOND attested
    // sprout would make it 1 + 1 = 2 > 1 → refused with C48 (quota).
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![(
        "MYCO_TEST_REPRODUCTION_QUOTA".to_string(),
        "1".to_string(),
    )]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");
    let spore = valid_spore_schema_bytes();

    // First sprout: under quota → succeeds.
    let first_dir = fresh_state_dir();
    try_sprout_attested(
        &mut parent,
        &first_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS - 1,
        ANCHOR_TS_BASE_NS,
        false,
    )
    .expect("first attested sprout (under quota) must succeed");
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        0,
        "C48: first (in-quota) sprout must NOT fire C48"
    );

    // Second sprout: over quota → refused + C48. Use a distinct (later) anchor
    // stamp so the §16.B rate-throttle (disabled) is not what blocks it.
    let second_dir = fresh_state_dir();
    let result = try_sprout_attested(
        &mut parent,
        &second_dir,
        &KNOWN_SEED,
        &parent_id,
        &spore,
        ANCHOR_TS_BASE_NS + 999,
        ANCHOR_TS_BASE_NS + 1_000,
        false,
    );
    assert!(
        result.is_err(),
        "C48: an attested sprout exceeding lifetime quota must be REFUSED; got Ok"
    );
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        1,
        "C48: over-quota sprout must emit exactly one C48 immune node"
    );
    // The over-quota child must NOT have been created.
    assert!(
        !second_dir.join("dag.cb").exists(),
        "C48: a refused over-quota sprout must NOT create the child's dag.cb"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn c48_negative_under_quota_sprouts_all_children() {
    // Parent boots with quota = 3 (rate disabled). Two attested sprouts (counts
    // 1 then 2, both <= 3) both succeed and NO C48 fires.
    let (mut parent, _dir, parent_id) = spawn_attested_parent(vec![(
        "MYCO_TEST_REPRODUCTION_QUOTA".to_string(),
        "3".to_string(),
    )]);
    parent
        .register_axis("clone_me", "appetite", 5.0, 0.0, 1.0, false, "noop")
        .expect("register axis");
    let spore = valid_spore_schema_bytes();

    for i in 0..2u64 {
        let child_dir = fresh_state_dir();
        // Distinct anchor stamps per sprout (rate disabled, so spacing is just
        // for hygiene / clock-rewind guard).
        let anchor = ANCHOR_TS_BASE_NS + (i as i64) * 1_000;
        let resp = try_sprout_attested(
            &mut parent,
            &child_dir,
            &KNOWN_SEED,
            &parent_id,
            &spore,
            anchor - 1,
            anchor,
            false,
        )
        .unwrap_or_else(|e| panic!("C48 negative: sprout #{i} under quota must succeed: {e}"));
        // All these children are depth 1 (parent is a depth-0 root).
        assert!(matches!(
            resp.payload.get("child_generation_depth"),
            Some(CbValue::Uint(1))
        ));
        assert!(
            child_dir.join("dag.cb").exists(),
            "C48 negative: in-quota sprout #{i} must create the child's dag.cb"
        );
    }
    assert_eq!(
        count_immune(&mut parent, "C48_reproduction_lifetime_quota_exceeded"),
        0,
        "C48 negative: under-quota sprouts must NOT fire C48"
    );
    parent.shutdown().expect("shutdown parent");
}

#[test]
fn reproduction_discipline_defaults_match_governance_s16() {
    // Pin the §16 constitutional defaults as a public-surface contract so a
    // refactor that silently changes depth=10 / quota=100 / interval=24h
    // surfaces in CI.
    use substrate::reproduction::{
        REPRODUCTION_LIFETIME_QUOTA, REPRODUCTION_LINEAGE_DEPTH_MAX,
        REPRODUCTION_RATE_MIN_INTERVAL_NS,
    };
    assert_eq!(
        REPRODUCTION_LINEAGE_DEPTH_MAX, 10,
        "L1/GOVERNANCE §16.A reproduction_lineage_depth_max default is 10"
    );
    assert_eq!(
        REPRODUCTION_LIFETIME_QUOTA, 100,
        "L1/GOVERNANCE §16.C reproduction_lifetime_quota default is 100"
    );
    assert_eq!(
        REPRODUCTION_RATE_MIN_INTERVAL_NS,
        86_400 * 1_000_000_000,
        "L1/GOVERNANCE §16.B reproduction_rate_min_interval default is 24h (ns)"
    );
}
