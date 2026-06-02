//! Shared test-support harness for the `myco-substrate` E2E integration tests.
//!
//! Rust compiles each `tests/*.rs` file as a **separate** integration-test
//! binary. The substrate suite is split by domain (`e2e_bootstrap.rs`,
//! `e2e_federation.rs`, …) so that compilation and test execution parallelize
//! and the suite stays navigable. Every domain file starts with
//! `mod common;` + `use common::*;` and pulls the shared spawn/build helpers
//! from here.
//!
//! These helpers spawn the substrate binary as a subprocess and drive it
//! through the M5 protocol as if we were the operator runtime. The substrate
//! in turn spawns the Python kernel/tropism worker (3-tier process tree).
//! This proves the **TS-side ↔ Rust-side ↔ Python-side** chain works at the
//! Rust↔Rust level (using BridgeClient as the operator simulator). The full
//! TS-side e2e lives in `operators/claude/tests/`.
//!
//! `#![allow(dead_code)]` + `#![allow(unused_imports)]` are standard for
//! shared test support: not every domain binary uses every helper or every
//! re-exported symbol (e.g. `proto` / `CbValue`), which would otherwise emit
//! per-binary `dead_code` / `unused_imports` warnings for whatever a given
//! binary happens not to reference.
#![allow(dead_code)]
#![allow(unused_imports)]

pub use myco_kernel_bridge::client::{BridgeClient, BridgeClientConfig};
pub use myco_kernel_bridge::protocol::msg_type as proto;
pub use myco_kernel_shared::canonical_bytes::Value as CbValue;
pub use std::path::PathBuf;

/// Generate a fresh isolated state-dir path for this test run.
///
/// Each test gets a unique state directory so they don't share substrate
/// identity / persistence across the test suite.
pub fn fresh_state_dir() -> PathBuf {
    use std::time::{SystemTime, UNIX_EPOCH};
    let ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let dir = std::env::temp_dir().join(format!(
        "myco-e2e-{}-{}-{:x}",
        std::process::id(),
        ns,
        rand_suffix()
    ));
    std::fs::create_dir_all(&dir).expect("create state_dir");
    dir
}

pub fn rand_suffix() -> u64 {
    // Mix in stack address for cheap per-call uniqueness.
    let x = 0u8;
    &x as *const u8 as usize as u64
}

/// Helper: spawn the myco-substrate binary and complete handshake.
///
/// We reuse BridgeClient (which speaks the M5 protocol on both stdin and
/// stdout) to simulate the operator runtime. The BridgeClient configuration
/// just points at our compiled myco-substrate binary instead of the Python
/// daemon. M7: each call gets a fresh, isolated state directory.
pub fn spawn_substrate() -> (BridgeClient, PathBuf) {
    let dir = fresh_state_dir();
    let client = spawn_substrate_with_state_dir(&dir);
    (client, dir)
}

pub fn spawn_substrate_with_state_dir(state_dir: &std::path::Path) -> BridgeClient {
    spawn_substrate_with_env(state_dir, vec![])
}

/// M26.1 C5: spawn helper allowing additional env vars (e.g.
/// `MYCO_ACCEPT_LEGACY_PEERS=1`) on top of the always-set `MYCO_STATE_DIR`.
pub fn spawn_substrate_with_env(
    state_dir: &std::path::Path,
    extra: Vec<(String, String)>,
) -> BridgeClient {
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    let mut extra_env = vec![(
        "MYCO_STATE_DIR".to_string(),
        state_dir.to_string_lossy().into_owned(),
    )];
    extra_env.extend(extra);
    BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
        extra_env,
        operator_signing_seed: None,
    })
    .expect("spawn myco-substrate binary")
}

/// **v3.1.1 Sprint 6.E (T2.9)** — spawn a substrate with a pre-pinned
/// operator pubkey derived from a known seed. The returned client holds
/// the matching Ed25519 private key (test caller stores it separately
/// for attestation signing). This unblocks positive ceremony E2E tests
/// for l0_revision_attest / schema_evolution / cost_budget_set /
/// owner_key_history mutations.
pub fn spawn_substrate_with_signing_seed(
    state_dir: &std::path::Path,
    seed: [u8; 32],
) -> BridgeClient {
    spawn_substrate_with_seed_and_env(state_dir, seed, vec![])
}

/// **COV06** — spawn with BOTH a known operator signing seed (→ deterministic
/// pinned owner pubkey) AND extra env (e.g. `MYCO_TEST_ANCHOR_NOW_NS`,
/// `MYCO_SELF_DRIVEN_CYCLE_ADVANCE`). The cultivation e2e needs the operator's
/// seed-derived key to BE the pinned owner key (so heartbeat / chain / succession
/// signatures verify) WHILE also threading the test anchor clock + scheduler.
pub fn spawn_substrate_with_seed_and_env(
    state_dir: &std::path::Path,
    seed: [u8; 32],
    extra: Vec<(String, String)>,
) -> BridgeClient {
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    let mut extra_env = vec![(
        "MYCO_STATE_DIR".to_string(),
        state_dir.to_string_lossy().into_owned(),
    )];
    extra_env.extend(extra);
    BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
        extra_env,
        operator_signing_seed: Some(seed),
    })
    .expect("spawn myco-substrate binary with signing seed + env")
}

/// **v3.1.1 Sprint 6.E (T2.9)** — derive operator pubkey from seed using
/// the same Ed25519 construction the substrate uses for verification.
pub fn derive_operator_pubkey_from_seed(seed: &[u8; 32]) -> [u8; 32] {
    use myco_kernel_shared::crypto::Ed25519PrivateKey;
    let priv_key = Ed25519PrivateKey::from_seed(seed);
    priv_key.public_key().0
}

/// Helper: build a payload Map from (key, value) pairs.
pub fn build_payload(
    fields: Vec<(&str, CbValue)>,
) -> std::collections::BTreeMap<String, CbValue> {
    fields
        .into_iter()
        .map(|(k, v)| (k.to_string(), v))
        .collect()
}

/// Helper: pump N advance cycles through the substrate so the observatory
/// history fills up.
pub fn pump_cycles(client: &mut BridgeClient, n: u64) {
    for cycle in 1..=n {
        client.advance(cycle).expect("advance");
    }
}

// ---------------------------------------------------------------------------
// **P08 §3.5 / §5.1 — reproduction cultivator co-attestation test support.**
//
// A child spawn is a CI-class doctrine event: the substrate refuses any sprout
// (C68 reproduction_unattested_spawn) unless it carries a cultivator-signed
// `myco-spawn-cosign-v1` envelope. Every spawn-bearing E2E (reproduction +
// federation fixtures) therefore needs to (a) boot the PARENT with a pinned
// owner identity derived from a known seed, and (b) build + sign a real
// spawn-cosign envelope. These shared helpers provide both so each suite
// doesn't re-implement the orchestration. Children INHERIT the parent's pinned
// operator identity, so a child re-boot must also use `..._with_seed_and_env`
// (an unseeded handshake is rejected as a downgrade, C2).
// ---------------------------------------------------------------------------

/// The known operator/owner signing seed the attested-spawn helpers pin.
pub const REPRO_SEED: [u8; 32] = [0x42u8; 32];

/// A distinct test anchor wall-clock base (ns) for the FIRST attested spawn in
/// a parent. Subsequent spawns must advance this past the effective §16.B rate
/// interval (or the test disables the interval via
/// `MYCO_TEST_REPRODUCTION_RATE_MIN_INTERVAL_NS=0`).
pub const REPRO_ANCHOR_TS_BASE_NS: i64 = 1_700_000_000_000_000_000;

/// Build minimal-but-VALID spore-schema canonical bytes: a Map carrying all
/// seven required L1/SCHEMA §3.1 fields (each non-Null), so the substrate's
/// I7(a) `validate_canonical_bytes_shape` accepts it. The field *contents* are
/// irrelevant to I7(a) — only presence + the top-level Map shape matter.
pub fn valid_spore_schema_bytes() -> Vec<u8> {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    let mut m = std::collections::BTreeMap::new();
    for field in [
        "schema_definitions",
        "canonical_bytes_serializer_spec",
        "sporocarp_type_tree",
        "classifier_dimension_table",
        "initial_appetite_axis_schema",
        "anchor_surface_config",
        "parent_immune_signal_summary",
    ] {
        m.insert(field.to_string(), Value::String(format!("{field}_v1")));
    }
    cb_encode(&Value::Map(m))
        .expect("valid spore-schema encodes")
        .0
}

/// Read a (booted) substrate's own `substrate_id` from its `genesis_event:*`
/// DAG node — needed to mint a spawn-cosign envelope whose `parent_substrate_id`
/// matches (the substrate's replay guard).
pub fn read_substrate_id(client: &mut BridgeClient) -> [u8; 32] {
    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(10)),
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
    assert_eq!(nodes.len(), 1, "exactly one genesis_event node expected");
    let content = match &nodes[0] {
        CbValue::Map(m) => match m.get("content_canonical_bytes") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("genesis_event missing content_canonical_bytes"),
        },
        _ => panic!("genesis_event node not a Map"),
    };
    let decoded = myco_kernel_shared::canonical_bytes::decode(&content)
        .expect("decode genesis_event content");
    let id = match decoded {
        CbValue::Map(m) => match m.get("substrate_id") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("genesis_event missing substrate_id"),
        },
        _ => panic!("genesis_event content not a Map"),
    };
    assert_eq!(id.len(), 32, "substrate_id must be 32 bytes");
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&id);
    arr
}

/// Build + sign a `myco-spawn-cosign-v1` envelope. Returns
/// `(envelope_bytes, signature_64)`. Uses the substrate's own
/// `build_spawn_cosign_canonical_bytes` so the bytes byte-match what the
/// substrate decodes; signs with `Ed25519PrivateKey::from_seed(seed)`.
pub fn build_signed_spawn_cosign(
    seed: &[u8; 32],
    parent_id: &[u8; 32],
    spore_schema_bytes: &[u8],
    child_genesis_ts: i64,
    anchor_ts: i64,
    depth_override: bool,
) -> (Vec<u8>, [u8; 64]) {
    use myco_kernel_shared::crypto::Ed25519PrivateKey;
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
    (envelope, sig_arr)
}

/// Full attested-sprout call against `client` (a seed-pinned parent): reads the
/// parent's substrate_id, builds + signs the spawn-cosign envelope, and sends
/// the complete `sprout_child` payload. Defaults to a valid spore-schema, the
/// `REPRO_ANCHOR_TS_BASE_NS` anchor stamp, and `depth_override=false`. Returns
/// the raw `Result` so callers can assert success or refusal.
pub fn sprout_attested(
    client: &mut BridgeClient,
    child_dir: &std::path::Path,
    seed: &[u8; 32],
) -> Result<myco_kernel_bridge::protocol::Message, myco_kernel_bridge::BridgeError> {
    let parent_id = read_substrate_id(client);
    let spore = valid_spore_schema_bytes();
    let (envelope, sig) = build_signed_spawn_cosign(
        seed,
        &parent_id,
        &spore,
        REPRO_ANCHOR_TS_BASE_NS - 1,
        REPRO_ANCHOR_TS_BASE_NS,
        false,
    );
    client.call(
        proto::SPROUT_CHILD,
        build_payload(vec![
            (
                "child_state_dir",
                CbValue::String(child_dir.to_string_lossy().into_owned()),
            ),
            ("spawn_cosign_envelope", CbValue::Bytes(envelope)),
            ("attestation_signature", CbValue::Bytes(sig.to_vec())),
            (
                "spore_schema_canonical_bytes",
                CbValue::Bytes(spore),
            ),
        ]),
    )
}
