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
    let substrate_binary = env!("CARGO_BIN_EXE_myco-substrate");
    let extra_env = vec![(
        "MYCO_STATE_DIR".to_string(),
        state_dir.to_string_lossy().into_owned(),
    )];
    BridgeClient::spawn_and_handshake(BridgeClientConfig {
        python_executable: substrate_binary.to_string(),
        session_secret: None,
        extra_env,
        operator_signing_seed: Some(seed),
    })
    .expect("spawn myco-substrate binary with signing seed")
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
