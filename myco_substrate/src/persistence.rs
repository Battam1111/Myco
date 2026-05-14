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
//! - L1_CONTINUITY §6 — disk-backed WAL is the L4-pick; this M7 implementation
//!   is snapshot-only (every state change → full manifest rewrite). M8+ adds
//!   true append-only WAL for performance.
//! - L0 §9.3 — canonical-bytes determinism preserved across persistence.

use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use myco_kernel_shared::canonical_bytes::{
    decode as cb_decode, encode as cb_encode, map_get_bytes, map_get_uint, Value,
};

use crate::SubstrateError;

/// Current manifest file format version. Bumped on any breaking change to
/// the canonical-bytes schema.
pub const MANIFEST_FORMAT_VERSION: u64 = 1;

/// Filename for the Rust-managed manifest within a state directory.
pub const MANIFEST_FILENAME: &str = "manifest.cb";

/// Filename for the Python-managed gradient state within a state directory.
pub const GRADIENT_FILENAME: &str = "gradient.cb";

/// Filename for the Rust-managed DAG state within a state directory (M8).
pub const DAG_FILENAME: &str = "dag.cb";

/// Save a DAG to `<state_dir>/dag.cb` atomically (M8).
///
/// Same pattern as [`Manifest::save`]: write to `.tmp`, fsync, atomic rename.
pub fn save_dag(
    dag: &myco_kernel_schema::dag::Dag,
    state_dir: &Path,
) -> Result<(), SubstrateError> {
    ensure_state_dir(state_dir)?;
    let final_path = state_dir.join(DAG_FILENAME);
    let tmp_path = state_dir.join(format!("{DAG_FILENAME}.tmp"));
    let bytes = dag.to_canonical_bytes();
    {
        let mut f = fs::File::create(&tmp_path)?;
        f.write_all(bytes.as_ref())?;
        f.sync_all()?;
    }
    fs::rename(&tmp_path, &final_path)?;
    Ok(())
}

/// Load a DAG from `<state_dir>/dag.cb` (M8).
///
/// Returns `Ok(None)` if the file does not exist (genesis condition) or if
/// the on-disk format version is incompatible.
pub fn load_dag(state_dir: &Path) -> Result<Option<myco_kernel_schema::dag::Dag>, SubstrateError> {
    let path = state_dir.join(DAG_FILENAME);
    match fs::File::open(&path) {
        Ok(mut f) => {
            let mut bytes = Vec::new();
            f.read_to_end(&mut bytes)?;
            myco_kernel_schema::dag::Dag::from_canonical_bytes(&bytes)
                .map_err(|e| SubstrateError::Protocol(format!("dag load: {e}")))
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(e) => Err(SubstrateError::Io(e)),
    }
}

/// Substrate identity + metabolic-cycle position. Persisted to `manifest.cb`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Manifest {
    /// 32-byte substrate identifier, set once at genesis.
    pub substrate_id: [u8; 32],
    /// Genesis wall-clock time, in nanoseconds since UNIX epoch.
    pub genesis_time_unix_ns: i64,
    /// Current authoritative metabolic-cycle counter.
    pub cycle_counter: u64,
    /// Most recent save wall-clock time (informational; bumped on every save).
    pub last_save_time_unix_ns: i64,
}

impl Manifest {
    /// Generate a fresh genesis manifest with a random substrate_id and
    /// current wall-clock time.
    pub fn genesis() -> Self {
        Manifest {
            substrate_id: generate_substrate_id(),
            genesis_time_unix_ns: current_unix_ns(),
            cycle_counter: 0,
            last_save_time_unix_ns: current_unix_ns(),
        }
    }

    /// Encode the manifest as canonical bytes (the on-disk representation).
    pub fn to_canonical_bytes(&self) -> Vec<u8> {
        let mut map = BTreeMap::new();
        map.insert(
            "format_version".to_string(),
            Value::Uint(MANIFEST_FORMAT_VERSION),
        );
        map.insert(
            "substrate_id".to_string(),
            Value::Bytes(self.substrate_id.to_vec()),
        );
        map.insert(
            "genesis_time_unix_ns".to_string(),
            Value::Timestamp(self.genesis_time_unix_ns),
        );
        map.insert("cycle_counter".to_string(), Value::Uint(self.cycle_counter));
        map.insert(
            "last_save_time_unix_ns".to_string(),
            Value::Timestamp(self.last_save_time_unix_ns),
        );
        cb_encode(&Value::Map(map))
            .expect("manifest canonical-bytes encode is infallible")
            .0
    }

    /// Decode a manifest from canonical bytes. Returns None on version
    /// mismatch (caller falls back to genesis).
    pub fn from_canonical_bytes(bytes: &[u8]) -> Result<Option<Self>, SubstrateError> {
        let decoded = cb_decode(bytes)
            .map_err(|e| SubstrateError::Protocol(format!("manifest decode: {e}")))?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(SubstrateError::Protocol(format!(
                    "manifest is not a Map: {other:?}"
                )))
            }
        };
        let format_version = map_get_uint(&map, "format_version")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        if format_version != MANIFEST_FORMAT_VERSION {
            // Unknown future version → caller can choose genesis.
            return Ok(None);
        }
        let substrate_id_slice = map_get_bytes(&map, "substrate_id")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        if substrate_id_slice.len() != 32 {
            return Err(SubstrateError::Protocol(format!(
                "substrate_id is {} bytes; expected 32",
                substrate_id_slice.len()
            )));
        }
        let mut substrate_id = [0u8; 32];
        substrate_id.copy_from_slice(substrate_id_slice);
        let genesis_time = match map.get("genesis_time_unix_ns") {
            Some(Value::Timestamp(ts)) => *ts,
            _ => {
                return Err(SubstrateError::Protocol(
                    "manifest missing genesis_time_unix_ns".to_string(),
                ))
            }
        };
        let cycle_counter = map_get_uint(&map, "cycle_counter")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        let last_save_time = match map.get("last_save_time_unix_ns") {
            Some(Value::Timestamp(ts)) => *ts,
            _ => {
                return Err(SubstrateError::Protocol(
                    "manifest missing last_save_time_unix_ns".to_string(),
                ))
            }
        };
        Ok(Some(Manifest {
            substrate_id,
            genesis_time_unix_ns: genesis_time,
            cycle_counter,
            last_save_time_unix_ns: last_save_time,
        }))
    }

    /// Atomically write the manifest to `<state_dir>/manifest.cb`.
    ///
    /// Creates `state_dir` if it doesn't exist. Updates
    /// [`last_save_time_unix_ns`](Self::last_save_time_unix_ns) to the
    /// current wall-clock time before writing.
    pub fn save(&mut self, state_dir: &Path) -> Result<(), SubstrateError> {
        self.last_save_time_unix_ns = current_unix_ns();
        ensure_state_dir(state_dir)?;
        let final_path = state_dir.join(MANIFEST_FILENAME);
        let tmp_path = state_dir.join(format!("{MANIFEST_FILENAME}.tmp"));
        let bytes = self.to_canonical_bytes();
        {
            let mut f = fs::File::create(&tmp_path)?;
            f.write_all(&bytes)?;
            f.sync_all()?; // fsync — durability across crash
        }
        fs::rename(&tmp_path, &final_path)?;
        Ok(())
    }

    /// Load the manifest from `<state_dir>/manifest.cb`. Returns:
    ///
    /// - `Ok(Some(manifest))` — file exists, parses cleanly, format matches.
    /// - `Ok(None)` — file does not exist OR format is incompatible (caller
    ///   should treat as a genesis condition).
    /// - `Err(...)` — I/O or parse error.
    pub fn load(state_dir: &Path) -> Result<Option<Self>, SubstrateError> {
        let path = state_dir.join(MANIFEST_FILENAME);
        match fs::File::open(&path) {
            Ok(mut f) => {
                let mut bytes = Vec::new();
                f.read_to_end(&mut bytes)?;
                Manifest::from_canonical_bytes(&bytes)
            }
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(e) => Err(SubstrateError::Io(e)),
        }
    }
}

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

/// Generate a fresh random 32-byte substrate identifier.
///
/// M7 uses time + process + stack-address SHA-256 mix (same pattern as the
/// kernel/bridge session_secret generator). M8+ may switch to OS-level
/// `getrandom` once that's wired everywhere.
fn generate_substrate_id() -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-substrate-id-v1");
    h.update(current_unix_ns().to_le_bytes());
    h.update(std::process::id().to_le_bytes());
    let stack_var = 0u8;
    let addr = &stack_var as *const u8 as usize;
    h.update(addr.to_le_bytes());
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

fn current_unix_ns() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;
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
}
