//! Substrate persistence — manifest save/load.
//!
//! ## State directory layout (M7 v1)
//!
//! ```text
//!   <state_dir>/
//!   ├── manifest.cb       Rust-managed: substrate_id + genesis + cycle counter
//!   └── gradient.cb       Python-managed: gradient axis schemas + values
//! ```
//!
//! The Rust side owns `manifest.cb`; Python owns `gradient.cb`. Both files
//! are canonical-bytes serialized for consistency with the wire protocol.
//!
//! ## Atomicity
//!
//! Writes go to `manifest.cb.tmp` first, then atomically rename onto
//! `manifest.cb`. On POSIX this is atomic by spec; on Windows
//! `std::fs::rename` calls `MoveFileExW` with replace semantics, which is
//! atomic for files on the same filesystem.
//!
//! ## Failure modes
//!
//! Read failures (missing file, malformed canonical-bytes, version mismatch)
//! return `Ok(None)` and the caller treats this as a genesis condition.
//! Write failures bubble up as `SubstrateError::Io`.
//!
//! ## Doctrine traceability
//!
//! - L1/CONTINUITY §6 — disk-backed WAL is the L4-pick; this M7 implementation
//!   is snapshot-only (every state change → full manifest rewrite). M8+ adds
//!   true append-only WAL for performance.
//! - L0/cards/AS_anchor_surface §3 — canonical-bytes determinism preserved across persistence.
//!
//! ## Module organization
//!
//! The persistence areas are grouped into submodules by the file each owns;
//! every item is re-exported here at `crate::persistence::*` so existing call
//! paths resolve unchanged:
//!
//! - [`manifest`] — `manifest.cb` (substrate identity + cycle counter)
//! - [`dag_io`] — `dag.cb` (causal DAG)
//! - [`snapshot`] — `snapshot.cb` (signed derived-state cache)
//! - [`nonce_log`] — `nonces.cb` (attestation nonce log)
//! - [`operator_identity`] — `operator_identity_pubkey.cb` (M9 TOFU pin)
//! - [`signing_key`] — `substrate_signing_key.cb` (substrate-private Ed25519 seed custody)

use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::SubstrateError;

mod dag_io;
mod manifest;
mod nonce_log;
mod operator_identity;
mod signing_key;
mod snapshot;

pub use dag_io::*;
pub use manifest::*;
pub use nonce_log::*;
pub use operator_identity::*;
pub use signing_key::*;
pub use snapshot::*;

/// Resolve the default state directory for the substrate.
///
/// Priority:
/// 1. `MYCO_STATE_DIR` environment variable (absolute path expected).
/// 2. `$HOME/.myco/substrate/default/` on Unix.
/// 3. `%USERPROFILE%\.myco\substrate\default\` on Windows.
/// 4. Falls back to `./myco-state/` if none of the above resolve.
pub fn default_state_dir() -> PathBuf {
    if let Ok(custom) = std::env::var("MYCO_STATE_DIR") {
        return PathBuf::from(custom);
    }
    // Try $HOME (Unix) or %USERPROFILE% (Windows).
    let home = std::env::var("HOME")
        .ok()
        .or_else(|| std::env::var("USERPROFILE").ok());
    if let Some(home_str) = home {
        PathBuf::from(home_str)
            .join(".myco")
            .join("substrate")
            .join("default")
    } else {
        PathBuf::from("./myco-state")
    }
}

/// Ensure the state directory exists; create it (and any parents) if not.
pub fn ensure_state_dir(state_dir: &Path) -> Result<(), SubstrateError> {
    if !state_dir.exists() {
        fs::create_dir_all(state_dir)?;
    }
    Ok(())
}

pub(crate) fn current_unix_ns() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    use std::collections::BTreeMap;
    use std::fs;
    use std::path::PathBuf;

    fn temp_state_dir() -> PathBuf {
        let base = std::env::temp_dir().join(format!(
            "myco-test-{}-{}",
            std::process::id(),
            current_unix_ns()
        ));
        fs::create_dir_all(&base).unwrap();
        base
    }

    #[test]
    fn manifest_genesis_has_non_zero_substrate_id() {
        let m = Manifest::genesis();
        assert_ne!(m.substrate_id, [0u8; 32]);
    }

    #[test]
    fn manifest_roundtrip_canonical_bytes() {
        let mut m = Manifest::genesis();
        m.cycle_counter = 42;
        let bytes = m.to_canonical_bytes();
        let decoded = Manifest::from_canonical_bytes(&bytes).unwrap().unwrap();
        assert_eq!(decoded.substrate_id, m.substrate_id);
        assert_eq!(decoded.cycle_counter, 42);
        assert_eq!(decoded.genesis_time_unix_ns, m.genesis_time_unix_ns);
        // 8f: a fresh-genesis manifest is a root → depth 0 round-trips.
        assert_eq!(decoded.generation_depth, 0);
    }

    #[test]
    fn manifest_generation_depth_roundtrip() {
        // 8f / §16.A: a non-zero generation_depth survives the canonical-bytes
        // round-trip (child manifest persistence).
        let mut m = Manifest::genesis();
        m.generation_depth = 5;
        let bytes = m.to_canonical_bytes();
        let decoded = Manifest::from_canonical_bytes(&bytes).unwrap().unwrap();
        assert_eq!(decoded.generation_depth, 5);
    }

    #[test]
    fn manifest_pre_8f_bytes_decode_depth_zero() {
        // 8f back-compat: a manifest encoded WITHOUT generation_depth (root /
        // pre-8f) decodes to depth 0. We assert the field is omitted for a
        // root (byte-compat) and decodes back to 0.
        use myco_kernel_shared::canonical_bytes::{decode, Value};
        let m = Manifest::genesis(); // depth 0
        let bytes = m.to_canonical_bytes();
        // Field must be ABSENT in the encoding for a root substrate.
        let decoded_map = match decode(&bytes).unwrap() {
            Value::Map(map) => map,
            _ => panic!("manifest not a Map"),
        };
        assert!(
            !decoded_map.contains_key("generation_depth"),
            "root manifest must omit generation_depth (byte-compat)"
        );
        // And it decodes back to 0.
        let decoded = Manifest::from_canonical_bytes(&bytes).unwrap().unwrap();
        assert_eq!(decoded.generation_depth, 0);
    }

    #[test]
    fn manifest_save_and_load_via_disk() {
        let dir = temp_state_dir();
        let mut m = Manifest::genesis();
        m.cycle_counter = 7;
        m.save(&dir).unwrap();
        let loaded = Manifest::load(&dir).unwrap().unwrap();
        assert_eq!(loaded.substrate_id, m.substrate_id);
        assert_eq!(loaded.cycle_counter, 7);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn manifest_load_returns_none_when_file_missing() {
        let dir = temp_state_dir();
        let loaded = Manifest::load(&dir).unwrap();
        assert!(loaded.is_none());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn manifest_save_is_atomic_no_tmp_leftover() {
        let dir = temp_state_dir();
        let mut m = Manifest::genesis();
        m.save(&dir).unwrap();
        let tmp_path = dir.join(format!("{MANIFEST_FILENAME}.tmp"));
        assert!(!tmp_path.exists(), "tmp file should have been renamed away");
        let final_path = dir.join(MANIFEST_FILENAME);
        assert!(final_path.exists());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn manifest_save_creates_state_dir() {
        let base = std::env::temp_dir().join(format!(
            "myco-test-nested-{}-{}",
            std::process::id(),
            current_unix_ns()
        ));
        let nested = base.join("nested").join("deeper");
        let mut m = Manifest::genesis();
        m.save(&nested).unwrap();
        assert!(nested.join(MANIFEST_FILENAME).exists());
        let _ = fs::remove_dir_all(&base);
    }

    #[test]
    fn manifest_load_returns_none_on_version_mismatch() {
        let dir = temp_state_dir();
        // Write a manifest with format_version = 999.
        let mut bad_map = BTreeMap::new();
        bad_map.insert("format_version".to_string(), Value::Uint(999));
        bad_map.insert("substrate_id".to_string(), Value::Bytes(vec![0u8; 32]));
        bad_map.insert("genesis_time_unix_ns".to_string(), Value::Timestamp(0));
        bad_map.insert("cycle_counter".to_string(), Value::Uint(0));
        bad_map.insert("last_save_time_unix_ns".to_string(), Value::Timestamp(0));
        let bad_bytes = cb_encode(&Value::Map(bad_map)).unwrap().0;
        fs::write(dir.join(MANIFEST_FILENAME), bad_bytes).unwrap();
        let loaded = Manifest::load(&dir).unwrap();
        assert!(loaded.is_none(), "version mismatch should yield None");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn manifest_load_errors_on_malformed_bytes() {
        let dir = temp_state_dir();
        fs::write(dir.join(MANIFEST_FILENAME), b"not-canonical-bytes-junk").unwrap();
        let result = Manifest::load(&dir);
        assert!(result.is_err());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn default_state_dir_respects_env_override() {
        std::env::set_var("MYCO_STATE_DIR", "/tmp/custom-myco-state");
        let dir = default_state_dir();
        assert_eq!(dir, PathBuf::from("/tmp/custom-myco-state"));
        std::env::remove_var("MYCO_STATE_DIR");
    }

    // -----------------------------------------------------------------------
    // M9 pinned operator identity tests.
    // -----------------------------------------------------------------------

    #[test]
    fn pinned_operator_identity_roundtrips_canonical_bytes() {
        let id = PinnedOperatorIdentity::pin_now([0xab; 32]);
        let bytes = id.to_canonical_bytes();
        let decoded = PinnedOperatorIdentity::from_canonical_bytes(&bytes)
            .unwrap()
            .unwrap();
        assert_eq!(decoded.pubkey, [0xab; 32]);
        assert_eq!(decoded.first_pinned_unix_ns, id.first_pinned_unix_ns);
    }

    #[test]
    fn pinned_operator_identity_save_load_via_disk() {
        let dir = temp_state_dir();
        let id = PinnedOperatorIdentity::pin_now([0x42; 32]);
        save_pinned_operator_identity(&id, &dir).unwrap();
        let loaded = load_pinned_operator_identity(&dir).unwrap().unwrap();
        assert_eq!(loaded.pubkey, [0x42; 32]);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn pinned_operator_identity_missing_returns_none() {
        let dir = temp_state_dir();
        let loaded = load_pinned_operator_identity(&dir).unwrap();
        assert!(loaded.is_none());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn pinned_operator_identity_version_mismatch_returns_none() {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        let dir = temp_state_dir();
        let mut bad_map = BTreeMap::new();
        bad_map.insert("format_version".to_string(), Value::Uint(999));
        bad_map.insert("pubkey".to_string(), Value::Bytes(vec![0u8; 32]));
        bad_map.insert("first_pinned_unix_ns".to_string(), Value::Timestamp(0));
        let bad_bytes = encode(&Value::Map(bad_map)).unwrap().0;
        fs::write(dir.join(OPERATOR_IDENTITY_PUBKEY_FILENAME), bad_bytes).unwrap();
        let loaded = load_pinned_operator_identity(&dir).unwrap();
        assert!(loaded.is_none());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn pinned_operator_identity_atomic_save_no_tmp_leftover() {
        let dir = temp_state_dir();
        let id = PinnedOperatorIdentity::pin_now([0x33; 32]);
        save_pinned_operator_identity(&id, &dir).unwrap();
        let tmp = dir.join(format!("{OPERATOR_IDENTITY_PUBKEY_FILENAME}.tmp"));
        assert!(!tmp.exists());
        let final_path = dir.join(OPERATOR_IDENTITY_PUBKEY_FILENAME);
        assert!(final_path.exists());
        let _ = fs::remove_dir_all(&dir);
    }

    // -----------------------------------------------------------------------
    // M14 nonce log persistence tests.
    // -----------------------------------------------------------------------

    fn make_nonce(byte: u8, consumed: bool, expiry_ns: i64) -> PersistedNonceEntry {
        PersistedNonceEntry {
            nonce: [byte; 32],
            bound_content_hash: [byte.wrapping_add(1); 32],
            bound_dag_tip: [byte.wrapping_add(2); 32],
            substrate_issued_at_unix_ns: expiry_ns
                .saturating_sub(NONCE_TTL_DEFAULT_SECONDS * 1_000_000_000),
            expiry_unix_ns: expiry_ns,
            anchor_clock_issued_at_unix_ns: None,
            anchor_clock_expiry_unix_ns: None,
            consumed,
        }
    }

    /// M15: make a nonce with dual-clock fields populated.
    fn make_nonce_dual_clock(
        byte: u8,
        consumed: bool,
        expiry_ns: i64,
        anchor_issued: i64,
        anchor_expiry: i64,
    ) -> PersistedNonceEntry {
        PersistedNonceEntry {
            nonce: [byte; 32],
            bound_content_hash: [byte.wrapping_add(1); 32],
            bound_dag_tip: [byte.wrapping_add(2); 32],
            substrate_issued_at_unix_ns: expiry_ns
                .saturating_sub(NONCE_TTL_DEFAULT_SECONDS * 1_000_000_000),
            expiry_unix_ns: expiry_ns,
            anchor_clock_issued_at_unix_ns: Some(anchor_issued),
            anchor_clock_expiry_unix_ns: Some(anchor_expiry),
            consumed,
        }
    }

    #[test]
    fn nonce_log_empty_roundtrips() {
        let dir = temp_state_dir();
        save_nonce_log(&[], &dir).unwrap();
        let loaded = load_nonce_log(&dir).unwrap().unwrap();
        assert_eq!(loaded.len(), 0);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn nonce_log_single_entry_roundtrips() {
        let dir = temp_state_dir();
        let entries = vec![make_nonce(0x11, false, 1_000_000)];
        save_nonce_log(&entries, &dir).unwrap();
        let loaded = load_nonce_log(&dir).unwrap().unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(loaded[0], entries[0]);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn nonce_log_multi_entry_with_consumed_state() {
        let dir = temp_state_dir();
        let entries = vec![
            make_nonce(0x01, true, 1_000),
            make_nonce(0x02, false, 2_000),
            make_nonce(0x03, true, 3_000),
        ];
        save_nonce_log(&entries, &dir).unwrap();
        let loaded = load_nonce_log(&dir).unwrap().unwrap();
        assert_eq!(loaded.len(), 3);
        // Verify consumed flags survive.
        assert!(loaded[0].consumed);
        assert!(!loaded[1].consumed);
        assert!(loaded[2].consumed);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn nonce_log_missing_returns_none() {
        let dir = temp_state_dir();
        let loaded = load_nonce_log(&dir).unwrap();
        assert!(loaded.is_none());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn nonce_log_atomic_save_no_tmp_leftover() {
        let dir = temp_state_dir();
        save_nonce_log(&[make_nonce(0xff, false, 9_999)], &dir).unwrap();
        let tmp = dir.join(format!("{NONCE_LOG_FILENAME}.tmp"));
        assert!(!tmp.exists());
        let target = dir.join(NONCE_LOG_FILENAME);
        assert!(target.exists());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn nonce_log_version_mismatch_returns_none() {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        let dir = temp_state_dir();
        let mut bad = BTreeMap::new();
        bad.insert("format_version".to_string(), Value::Uint(999));
        bad.insert("entries".to_string(), Value::Array(vec![]));
        let bad_bytes = encode(&Value::Map(bad)).unwrap();
        fs::write(dir.join(NONCE_LOG_FILENAME), bad_bytes.as_ref()).unwrap();
        let loaded = load_nonce_log(&dir).unwrap();
        assert!(loaded.is_none());
        let _ = fs::remove_dir_all(&dir);
    }

    // -----------------------------------------------------------------------
    // M15 dual-clock + v1↔v2 backward-compat persistence tests.
    // -----------------------------------------------------------------------

    #[test]
    fn m15_nonce_log_v2_with_dual_clock_roundtrips() {
        let dir = temp_state_dir();
        let entries = vec![make_nonce_dual_clock(
            0x42,
            false,
            5_000_000_000,
            1_000_000_000,
            4_000_000_000,
        )];
        save_nonce_log(&entries, &dir).unwrap();
        let loaded = load_nonce_log(&dir).unwrap().unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(
            loaded[0].anchor_clock_issued_at_unix_ns,
            Some(1_000_000_000)
        );
        assert_eq!(loaded[0].anchor_clock_expiry_unix_ns, Some(4_000_000_000));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn m15_nonce_log_v1_file_loads_with_anchor_clock_none() {
        // Hand-write a v1 nonce log (no anchor-clock fields, no substrate_issued_at).
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        let dir = temp_state_dir();
        let mut entry_map = BTreeMap::new();
        entry_map.insert("nonce".to_string(), Value::Bytes(vec![0xab; 32]));
        entry_map.insert(
            "bound_content_hash".to_string(),
            Value::Bytes(vec![0xcd; 32]),
        );
        entry_map.insert("bound_dag_tip".to_string(), Value::Bytes(vec![0xef; 32]));
        entry_map.insert(
            "expiry_unix_ns".to_string(),
            Value::Timestamp(10_000_000_000),
        );
        entry_map.insert("consumed".to_string(), Value::Bool(false));
        let mut root = BTreeMap::new();
        root.insert(
            "format_version".to_string(),
            Value::Uint(NONCE_LOG_FORMAT_VERSION_V1),
        );
        root.insert(
            "entries".to_string(),
            Value::Array(vec![Value::Map(entry_map)]),
        );
        let bytes = encode(&Value::Map(root)).unwrap();
        fs::write(dir.join(NONCE_LOG_FILENAME), bytes.as_ref()).unwrap();

        let loaded = load_nonce_log(&dir).unwrap().unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(loaded[0].nonce, [0xab; 32]);
        // M15: missing anchor-clock fields → None (single-clock mode preserved).
        assert!(loaded[0].anchor_clock_issued_at_unix_ns.is_none());
        assert!(loaded[0].anchor_clock_expiry_unix_ns.is_none());
        // M15: missing substrate_issued_at → defaulted to expiry - TTL.
        let expected_default =
            10_000_000_000_i64.saturating_sub(NONCE_TTL_DEFAULT_SECONDS * 1_000_000_000);
        assert_eq!(loaded[0].substrate_issued_at_unix_ns, expected_default);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn m15_nonce_log_v2_writes_format_version_2() {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_uint, Value};
        let dir = temp_state_dir();
        save_nonce_log(&[make_nonce(0x10, false, 9_999)], &dir).unwrap();
        let bytes = fs::read(dir.join(NONCE_LOG_FILENAME)).unwrap();
        let decoded = decode(&bytes).unwrap();
        if let Value::Map(m) = decoded {
            let version = map_get_uint(&m, "format_version").unwrap();
            assert_eq!(version, NONCE_LOG_FORMAT_VERSION);
            assert_eq!(version, 2); // pinned: M15 writes v2.
        } else {
            panic!("expected Map");
        }
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn m15_nonce_entry_without_anchor_clock_omits_those_fields() {
        // Re-encoding a nonce with anchor_clock = None should NOT emit those keys.
        use myco_kernel_shared::canonical_bytes::Value;
        let entry = make_nonce(0x77, false, 1_000_000);
        let value = entry.to_value();
        if let Value::Map(m) = value {
            assert!(!m.contains_key("anchor_clock_issued_at_unix_ns"));
            assert!(!m.contains_key("anchor_clock_expiry_unix_ns"));
            assert!(m.contains_key("substrate_issued_at_unix_ns")); // always present in v2
        } else {
            panic!("expected Map");
        }
    }

    #[test]
    fn save_then_load_preserves_cycle_counter() {
        let dir = temp_state_dir();
        let mut m = Manifest::genesis();
        let original_id = m.substrate_id;
        m.cycle_counter = 123;
        m.save(&dir).unwrap();

        // Load fresh.
        let loaded = Manifest::load(&dir).unwrap().unwrap();
        assert_eq!(loaded.substrate_id, original_id);
        assert_eq!(loaded.cycle_counter, 123);

        // Bump and re-save.
        let mut loaded = loaded;
        loaded.cycle_counter = 456;
        loaded.save(&dir).unwrap();

        let loaded_again = Manifest::load(&dir).unwrap().unwrap();
        assert_eq!(loaded_again.cycle_counter, 456);
        assert_eq!(loaded_again.substrate_id, original_id);
        let _ = fs::remove_dir_all(&dir);
    }

    // -----------------------------------------------------------------------
    // M25.0 substrate-private signing key + snapshot signature tests.
    // -----------------------------------------------------------------------

    #[test]
    fn substrate_signing_key_roundtrips_canonical_bytes() {
        let dir = temp_state_dir();
        let seed = [0x42u8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        let loaded = load_substrate_signing_key(&dir).unwrap().unwrap();
        assert_eq!(loaded, seed);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn substrate_signing_key_missing_returns_none() {
        let dir = temp_state_dir();
        let loaded = load_substrate_signing_key(&dir).unwrap();
        assert!(loaded.is_none());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn substrate_signing_key_version_mismatch_returns_none() {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        let dir = temp_state_dir();
        let mut bad = BTreeMap::new();
        bad.insert("format_version".to_string(), Value::Uint(999));
        bad.insert("seed".to_string(), Value::Bytes(vec![0u8; 32]));
        bad.insert("created_at_unix_ns".to_string(), Value::Timestamp(0));
        let bad_bytes = encode(&Value::Map(bad)).unwrap();
        fs::write(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME), bad_bytes.as_ref()).unwrap();
        let loaded = load_substrate_signing_key(&dir).unwrap();
        assert!(loaded.is_none());
        let _ = fs::remove_dir_all(&dir);
    }

    // -----------------------------------------------------------------------
    // **v3.1.1 Sprint 2** — Windows DPAPI sealing tests.
    // -----------------------------------------------------------------------

    #[test]
    #[cfg(windows)]
    fn v3_1_1_sprint_2_save_uses_dpapi_protected_field_on_windows() {
        use myco_kernel_shared::canonical_bytes::{decode, Value};
        let dir = temp_state_dir();
        let seed = [0x77u8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        // On disk: must be v2 + have seed_dpapi_protected, NOT plain seed.
        let raw = fs::read(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME)).unwrap();
        let decoded = decode(&raw).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        match map.get("format_version") {
            Some(Value::Uint(n)) => assert_eq!(
                *n,
                SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V2,
                "Windows save must produce v2"
            ),
            _ => panic!("format_version missing"),
        }
        assert!(
            map.get("seed_dpapi_protected").is_some(),
            "v2 file MUST carry seed_dpapi_protected field"
        );
        assert!(
            map.get("seed").is_none(),
            "v2 file MUST NOT carry plain seed field (the whole point of the wrap)"
        );
        // Plaintext bytes must NOT appear in the on-disk file bytes — easy
        // smoke test that DPAPI actually altered the seed.
        let needle: &[u8] = &seed;
        assert!(
            !raw.windows(needle.len()).any(|w| w == needle),
            "plaintext seed bytes leaked into v2 on-disk file"
        );
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    #[cfg(windows)]
    fn v3_1_1_sprint_2_dpapi_round_trip_via_save_load() {
        let dir = temp_state_dir();
        let seed = [0x88u8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        let loaded = load_substrate_signing_key(&dir).unwrap().unwrap();
        assert_eq!(loaded, seed, "DPAPI round-trip must recover original seed");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    #[cfg(windows)]
    fn v3_1_1_sprint_2_v1_to_v2_migration_on_boot() {
        use myco_kernel_shared::canonical_bytes::{decode, encode, Value};

        let dir = temp_state_dir();
        let legacy_seed = [0x55u8; 32];

        // Write a v1-format file manually (simulating an old substrate's
        // on-disk state).
        let mut m = BTreeMap::new();
        m.insert(
            "format_version".to_string(),
            Value::Uint(SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1),
        );
        m.insert("seed".to_string(), Value::Bytes(legacy_seed.to_vec()));
        m.insert("created_at_unix_ns".to_string(), Value::Timestamp(0));
        let v1_bytes = encode(&Value::Map(m)).unwrap();
        fs::write(
            dir.join(SUBSTRATE_SIGNING_KEY_FILENAME),
            v1_bytes.as_ref(),
        )
        .unwrap();

        // Boot path: should load the v1 seed AND migrate the on-disk file
        // to v2 atomically.
        let (loaded_seed, _was_restrictive) =
            boot_or_genesis_substrate_signing_key_with_permission_status(&dir).unwrap();
        assert_eq!(
            loaded_seed, legacy_seed,
            "v1 → v2 migration must preserve seed exactly"
        );

        // On-disk file must now be v2.
        let raw = fs::read(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME)).unwrap();
        let decoded = decode(&raw).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("post-migration file not a map"),
        };
        match map.get("format_version") {
            Some(Value::Uint(n)) => assert_eq!(
                *n,
                SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V2,
                "post-migration on-disk format must be v2"
            ),
            _ => panic!("format_version missing post-migration"),
        }
        assert!(
            map.get("seed").is_none(),
            "post-migration file MUST NOT carry plain seed field"
        );
        assert!(
            map.get("seed_dpapi_protected").is_some(),
            "post-migration file MUST carry seed_dpapi_protected"
        );

        // Subsequent boot loads from v2 (no further migration needed).
        let (loaded_again, _) =
            boot_or_genesis_substrate_signing_key_with_permission_status(&dir).unwrap();
        assert_eq!(
            loaded_again, legacy_seed,
            "post-migration load must continue to recover same seed"
        );

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    #[cfg(not(windows))]
    fn v3_1_1_sprint_2_non_windows_save_stays_v1_plain() {
        use myco_kernel_shared::canonical_bytes::{decode, Value};
        let dir = temp_state_dir();
        let seed = [0xAAu8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        let raw = fs::read(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME)).unwrap();
        let decoded = decode(&raw).unwrap();
        let map = match decoded {
            Value::Map(m) => m,
            _ => panic!("not a map"),
        };
        match map.get("format_version") {
            Some(Value::Uint(n)) => assert_eq!(
                *n,
                SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1,
                "non-Windows save must produce v1 (no DPAPI available)"
            ),
            _ => panic!("format_version missing"),
        }
        assert!(
            map.get("seed").is_some(),
            "v1 must carry plain seed field on non-Windows"
        );
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn boot_or_genesis_generates_when_missing() {
        let dir = temp_state_dir();
        // First call: file missing → should generate and persist a non-zero seed.
        let seed1 = boot_or_genesis_substrate_signing_key(&dir).unwrap();
        assert_ne!(seed1, [0u8; 32]);
        assert!(dir.join(SUBSTRATE_SIGNING_KEY_FILENAME).exists());
        // Second call: should load the same seed (not regenerate).
        let seed2 = boot_or_genesis_substrate_signing_key(&dir).unwrap();
        assert_eq!(seed1, seed2);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn m25_0_snapshot_save_load_with_signature_verifies() {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        use myco_kernel_shared::crypto::{verify_signature, Ed25519PrivateKey};
        let dir = temp_state_dir();
        let seed = [0xAB; 32];
        let key = Ed25519PrivateKey::from_seed(&seed);
        // Build a synthetic payload (any canonical-bytes will do for this test).
        let mut payload_map = BTreeMap::new();
        payload_map.insert("hello".to_string(), Value::String("world".to_string()));
        let payload = encode(&Value::Map(payload_map)).unwrap();
        // Save the snapshot wrapper around this payload.
        save_snapshot(&payload, &key, &dir).unwrap();
        // Load and inspect.
        let loaded = load_snapshot(&dir).unwrap().expect("snapshot present");
        // The unwrapped payload bytes match the original.
        assert_eq!(loaded.payload, payload.as_ref());
        // The signer_pubkey matches the key's public_key.
        assert_eq!(loaded.signer_pubkey, key.public_key().0);
        // The embedded signature verifies against the embedded pubkey + payload.
        verify_signature(&loaded.signer_pubkey, &loaded.signature, &loaded.payload)
            .expect("snapshot signature must verify");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn m25_0_snapshot_load_returns_none_on_corruption() {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        use myco_kernel_shared::crypto::{verify_signature, CryptoError, Ed25519PrivateKey};
        let dir = temp_state_dir();
        let seed = [0xCD; 32];
        let key = Ed25519PrivateKey::from_seed(&seed);
        // Save a valid snapshot first.
        let mut payload_map = BTreeMap::new();
        payload_map.insert("k".to_string(), Value::Uint(7));
        let payload = encode(&Value::Map(payload_map)).unwrap();
        save_snapshot(&payload, &key, &dir).unwrap();
        // Tamper with the file: flip one signature byte. We re-encode the
        // wrapper Map with a corrupted signature so the canonical-bytes shape
        // stays valid (so load_snapshot returns Some) but the signature won't
        // verify.
        let path = dir.join(SNAPSHOT_FILENAME);
        let bytes = fs::read(&path).unwrap();
        let decoded = myco_kernel_shared::canonical_bytes::decode(&bytes).unwrap();
        let mut wrapper = match decoded {
            Value::Map(m) => m,
            _ => panic!("wrapper not a Map"),
        };
        let mut sig = match wrapper.get("signature") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => panic!("signature missing"),
        };
        sig[0] ^= 0xFF; // flip a bit in the signature
        wrapper.insert("signature".to_string(), Value::Bytes(sig));
        let bad_wrapper = encode(&Value::Map(wrapper)).unwrap();
        fs::write(&path, bad_wrapper.as_ref()).unwrap();
        // load_snapshot still returns Some — the wrapper is well-formed — but
        // the caller's verify_signature call will reject the corrupted sig.
        let loaded = load_snapshot(&dir).unwrap().expect("wrapper still parses");
        let verify_result = verify_signature(
            &loaded.signer_pubkey,
            &loaded.signature,
            &loaded.payload,
        );
        assert_eq!(verify_result, Err(CryptoError::SignatureInvalid));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn m25_0_snapshot_legacy_v1_format_returns_none() {
        // A pre-M25 (v1, unsigned) snapshot.cb must not be silently trusted.
        // load_snapshot returns None so the caller falls back to DAG replay.
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        let dir = temp_state_dir();
        let mut legacy = BTreeMap::new();
        legacy.insert("format_version".to_string(), Value::Uint(1));
        // Some arbitrary legacy fields (the old DerivedState canonical form).
        legacy.insert("cycle_counter".to_string(), Value::Uint(0));
        let legacy_bytes = encode(&Value::Map(legacy)).unwrap();
        fs::write(dir.join(SNAPSHOT_FILENAME), legacy_bytes.as_ref()).unwrap();
        let loaded = load_snapshot(&dir).unwrap();
        assert!(loaded.is_none(), "legacy v1 snapshot must return None");
        let _ = fs::remove_dir_all(&dir);
    }

    // -----------------------------------------------------------------------
    // M26.1 C6 (Phase γ.2): substrate_signing_key.cb permission hardening.
    //
    // On Unix the seed file MUST be 0600 (owner read+write only). On Windows
    // ACL hardening is M-anchor-1 work; the C6 tests assert restrictive ==
    // true unconditionally there (no exposure surfaced via the metadata API).
    // -----------------------------------------------------------------------

    #[cfg(unix)]
    #[test]
    fn m26_1_c6_save_writes_seed_with_0600_mode() {
        use std::os::unix::fs::PermissionsExt;
        let dir = temp_state_dir();
        let seed = [0x55u8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        let path = dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
        let mode = fs::metadata(&path).unwrap().permissions().mode();
        // Mask off the file-type bits — we only care about the perm bits.
        let perm_bits = mode & 0o777;
        assert_eq!(
            perm_bits, 0o600,
            "M26.1 C6: seed file must be 0600; got {:o}",
            perm_bits
        );
        let _ = fs::remove_dir_all(&dir);
    }

    #[cfg(unix)]
    #[test]
    fn m26_1_c6_loose_mode_reported_by_permission_check() {
        // Manually create a seed file with loose permissions, then verify the
        // load-with-permission-check function reports `was_restrictive=false`.
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        use std::os::unix::fs::PermissionsExt;
        let dir = temp_state_dir();
        let seed = [0x66u8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        let path = dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
        // Manually loosen to 0644 (the pre-fix exposure class).
        fs::set_permissions(&path, fs::Permissions::from_mode(0o644)).unwrap();
        let (loaded_seed, was_restrictive) =
            load_substrate_signing_key_with_permission_check(&dir)
                .unwrap()
                .expect("seed file present");
        assert_eq!(loaded_seed, seed);
        assert!(
            !was_restrictive,
            "M26.1 C6: 0644-mode seed file must report was_restrictive=false"
        );
        // Encode used to keep the use statement non-dead in case other tests
        // get removed; documents what the file shape is.
        let _ = encode(&Value::Uint(0));
        let _ = fs::remove_dir_all(&dir);
    }

    #[cfg(unix)]
    #[test]
    fn m26_1_c6_tighten_in_place_restores_0600() {
        use std::os::unix::fs::PermissionsExt;
        let dir = temp_state_dir();
        let seed = [0x77u8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        let path = dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
        // Loosen, then tighten.
        fs::set_permissions(&path, fs::Permissions::from_mode(0o666)).unwrap();
        tighten_substrate_signing_key_permissions(&dir).unwrap();
        let mode_after = fs::metadata(&path).unwrap().permissions().mode() & 0o777;
        assert_eq!(
            mode_after, 0o600,
            "tighten must restore 0600; got {:o}",
            mode_after
        );
        let _ = fs::remove_dir_all(&dir);
    }

    #[cfg(unix)]
    #[test]
    fn m26_1_c6_boot_helper_reports_loose_mode() {
        // boot_or_genesis_substrate_signing_key_with_permission_status must
        // bubble the loose-mode signal through to its caller (server.rs uses
        // this to emit the C4 immune sporocarp).
        use std::os::unix::fs::PermissionsExt;
        let dir = temp_state_dir();
        let seed = [0x88u8; 32];
        save_substrate_signing_key(&seed, &dir).unwrap();
        let path = dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
        // Loosen permissions, simulating a pre-M26.1 substrate that wrote
        // the seed before the C6 fix landed.
        fs::set_permissions(&path, fs::Permissions::from_mode(0o644)).unwrap();
        let (loaded_seed, was_restrictive) =
            boot_or_genesis_substrate_signing_key_with_permission_status(&dir).unwrap();
        assert_eq!(loaded_seed, seed);
        assert!(
            !was_restrictive,
            "boot helper must surface loose-mode signal to server.rs"
        );
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn m26_1_c6_genesis_path_reports_restrictive() {
        // On the genesis (fresh-seed) branch, the file is written by
        // save_substrate_signing_key with 0600 from the start — the boot
        // helper must report was_restrictive=true so no spurious C4
        // sporocarp gets emitted.
        let dir = temp_state_dir();
        let (_seed, was_restrictive) =
            boot_or_genesis_substrate_signing_key_with_permission_status(&dir).unwrap();
        assert!(
            was_restrictive,
            "fresh genesis must report was_restrictive=true (no exposure window)"
        );
        let _ = fs::remove_dir_all(&dir);
    }
}
