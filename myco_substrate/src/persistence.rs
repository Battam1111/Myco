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

/// Filename for the pinned operator identity public key (M9).
pub const OPERATOR_IDENTITY_PUBKEY_FILENAME: &str = "operator_identity_pubkey.cb";

/// Filename for the Rust-managed nonce log (M14).
pub const NONCE_LOG_FILENAME: &str = "nonces.cb";

/// Current nonce log file format version (M14).
pub const NONCE_LOG_FORMAT_VERSION: u64 = 1;

/// One persisted nonce entry (M14).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PersistedNonceEntry {
    /// 32-byte nonce.
    pub nonce: [u8; 32],
    /// Content hash this nonce was bound to.
    pub bound_content_hash: [u8; 32],
    /// DAG tip at issuance.
    pub bound_dag_tip: [u8; 32],
    /// Wall-clock expiry (unix nanoseconds).
    pub expiry_unix_ns: i64,
    /// Whether this nonce has been consumed.
    pub consumed: bool,
}

impl PersistedNonceEntry {
    /// Serialize this entry as a canonical-bytes Map.
    fn to_value(&self) -> myco_kernel_shared::canonical_bytes::Value {
        use myco_kernel_shared::canonical_bytes::Value;
        let mut m = BTreeMap::new();
        m.insert("nonce".to_string(), Value::Bytes(self.nonce.to_vec()));
        m.insert(
            "bound_content_hash".to_string(),
            Value::Bytes(self.bound_content_hash.to_vec()),
        );
        m.insert(
            "bound_dag_tip".to_string(),
            Value::Bytes(self.bound_dag_tip.to_vec()),
        );
        m.insert(
            "expiry_unix_ns".to_string(),
            Value::Timestamp(self.expiry_unix_ns),
        );
        m.insert("consumed".to_string(), Value::Bool(self.consumed));
        Value::Map(m)
    }

    fn from_value(v: &myco_kernel_shared::canonical_bytes::Value) -> Result<Self, SubstrateError> {
        use myco_kernel_shared::canonical_bytes::Value;
        let m = match v {
            Value::Map(m) => m,
            other => {
                return Err(SubstrateError::Protocol(format!(
                    "nonce entry is not a Map: {other:?}"
                )))
            }
        };
        let bytes_field = |key: &str, expected_len: usize| -> Result<[u8; 32], SubstrateError> {
            match m.get(key) {
                Some(Value::Bytes(b)) if b.len() == expected_len => {
                    let mut arr = [0u8; 32];
                    arr.copy_from_slice(b);
                    Ok(arr)
                }
                _ => Err(SubstrateError::Protocol(format!(
                    "nonce entry missing/malformed field {key}"
                ))),
            }
        };
        let nonce = bytes_field("nonce", 32)?;
        let bound_content_hash = bytes_field("bound_content_hash", 32)?;
        let bound_dag_tip = bytes_field("bound_dag_tip", 32)?;
        let expiry_unix_ns = match m.get("expiry_unix_ns") {
            Some(Value::Timestamp(ts)) => *ts,
            _ => {
                return Err(SubstrateError::Protocol(
                    "nonce entry missing expiry_unix_ns".to_string(),
                ))
            }
        };
        let consumed = match m.get("consumed") {
            Some(Value::Bool(b)) => *b,
            _ => {
                return Err(SubstrateError::Protocol(
                    "nonce entry missing consumed flag".to_string(),
                ))
            }
        };
        Ok(PersistedNonceEntry {
            nonce,
            bound_content_hash,
            bound_dag_tip,
            expiry_unix_ns,
            consumed,
        })
    }
}

/// Atomically save the nonce log to `<state_dir>/nonces.cb` (M14).
///
/// The nonce log is a snapshot of every nonce ever issued (active + consumed +
/// expired). Callers SHOULD prune past-expiry consumed nonces periodically to
/// bound disk growth.
pub fn save_nonce_log(
    entries: &[PersistedNonceEntry],
    state_dir: &Path,
) -> Result<(), SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{encode, Value};
    ensure_state_dir(state_dir)?;
    let final_path = state_dir.join(NONCE_LOG_FILENAME);
    let tmp_path = state_dir.join(format!("{NONCE_LOG_FILENAME}.tmp"));

    let entry_values: Vec<Value> = entries.iter().map(|e| e.to_value()).collect();
    let mut root = BTreeMap::new();
    root.insert(
        "format_version".to_string(),
        Value::Uint(NONCE_LOG_FORMAT_VERSION),
    );
    root.insert("entries".to_string(), Value::Array(entry_values));
    let bytes = encode(&Value::Map(root))
        .map_err(|e| SubstrateError::Protocol(format!("nonce log encode: {e}")))?;

    {
        let mut f = fs::File::create(&tmp_path)?;
        f.write_all(bytes.as_ref())?;
        f.sync_all()?;
    }
    fs::rename(&tmp_path, &final_path)?;
    Ok(())
}

/// Load the nonce log from `<state_dir>/nonces.cb` (M14).
///
/// Returns:
/// - `Ok(Some(entries))` on success.
/// - `Ok(None)` if file missing OR version mismatch.
/// - `Err(...)` on I/O or malformed-bytes error.
pub fn load_nonce_log(
    state_dir: &Path,
) -> Result<Option<Vec<PersistedNonceEntry>>, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode, map_get_array, map_get_uint, Value};
    let path = state_dir.join(NONCE_LOG_FILENAME);
    let mut f = match fs::File::open(&path) {
        Ok(f) => f,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(e) => return Err(SubstrateError::Io(e)),
    };
    let mut bytes = Vec::new();
    f.read_to_end(&mut bytes)?;
    let decoded =
        decode(&bytes).map_err(|e| SubstrateError::Protocol(format!("nonce log decode: {e}")))?;
    let map = match decoded {
        Value::Map(m) => m,
        other => {
            return Err(SubstrateError::Protocol(format!(
                "nonce log is not a Map: {other:?}"
            )))
        }
    };
    let version = map_get_uint(&map, "format_version")
        .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
    if version != NONCE_LOG_FORMAT_VERSION {
        return Ok(None);
    }
    let entries_array =
        map_get_array(&map, "entries").map_err(|e| SubstrateError::Protocol(e.to_string()))?;
    let entries: Result<Vec<_>, _> = entries_array
        .iter()
        .map(PersistedNonceEntry::from_value)
        .collect();
    Ok(Some(entries?))
}

/// Current operator-identity-pubkey file format version (M9).
pub const OPERATOR_IDENTITY_PUBKEY_FORMAT_VERSION: u64 = 1;

/// Pinned operator identity public key (M9).
///
/// On first sight of a hello message, the substrate writes this file with
/// the operator's pubkey. On subsequent hellos, the substrate verifies that
/// the operator presents the SAME pubkey and rejects otherwise.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PinnedOperatorIdentity {
    /// 32-byte Ed25519 public key.
    pub pubkey: [u8; 32],
    /// When the substrate first pinned this key (unix nanoseconds).
    pub first_pinned_unix_ns: i64,
}

impl PinnedOperatorIdentity {
    /// Construct from a pubkey + current time.
    pub fn pin_now(pubkey: [u8; 32]) -> Self {
        PinnedOperatorIdentity {
            pubkey,
            first_pinned_unix_ns: current_unix_ns(),
        }
    }

    /// Serialize as canonical bytes.
    pub fn to_canonical_bytes(&self) -> Vec<u8> {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        let mut m = BTreeMap::new();
        m.insert(
            "format_version".to_string(),
            Value::Uint(OPERATOR_IDENTITY_PUBKEY_FORMAT_VERSION),
        );
        m.insert("pubkey".to_string(), Value::Bytes(self.pubkey.to_vec()));
        m.insert(
            "first_pinned_unix_ns".to_string(),
            Value::Timestamp(self.first_pinned_unix_ns),
        );
        encode(&Value::Map(m))
            .expect("PinnedOperatorIdentity encode is infallible")
            .0
    }

    /// Decode from canonical bytes. Returns None on version mismatch.
    pub fn from_canonical_bytes(bytes: &[u8]) -> Result<Option<Self>, SubstrateError> {
        use myco_kernel_shared::canonical_bytes::{decode, map_get_bytes, map_get_uint, Value};
        let decoded = decode(bytes)
            .map_err(|e| SubstrateError::Protocol(format!("pinned identity decode: {e}")))?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(SubstrateError::Protocol(format!(
                    "pinned identity is not a Map: {other:?}"
                )))
            }
        };
        let v = map_get_uint(&map, "format_version")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        if v != OPERATOR_IDENTITY_PUBKEY_FORMAT_VERSION {
            return Ok(None);
        }
        let pubkey_slice =
            map_get_bytes(&map, "pubkey").map_err(|e| SubstrateError::Protocol(e.to_string()))?;
        if pubkey_slice.len() != 32 {
            return Err(SubstrateError::Protocol(format!(
                "pubkey is {} bytes; expected 32",
                pubkey_slice.len()
            )));
        }
        let mut pubkey = [0u8; 32];
        pubkey.copy_from_slice(pubkey_slice);
        let first_pinned_unix_ns = match map.get("first_pinned_unix_ns") {
            Some(Value::Timestamp(ts)) => *ts,
            _ => {
                return Err(SubstrateError::Protocol(
                    "missing first_pinned_unix_ns".to_string(),
                ))
            }
        };
        Ok(Some(PinnedOperatorIdentity {
            pubkey,
            first_pinned_unix_ns,
        }))
    }
}

/// Atomically save a pinned operator identity to `<state_dir>/operator_identity_pubkey.cb`.
pub fn save_pinned_operator_identity(
    identity: &PinnedOperatorIdentity,
    state_dir: &Path,
) -> Result<(), SubstrateError> {
    ensure_state_dir(state_dir)?;
    let final_path = state_dir.join(OPERATOR_IDENTITY_PUBKEY_FILENAME);
    let tmp_path = state_dir.join(format!("{OPERATOR_IDENTITY_PUBKEY_FILENAME}.tmp"));
    let bytes = identity.to_canonical_bytes();
    {
        let mut f = fs::File::create(&tmp_path)?;
        f.write_all(&bytes)?;
        f.sync_all()?;
    }
    fs::rename(&tmp_path, &final_path)?;
    Ok(())
}

/// Load the pinned operator identity from `<state_dir>/operator_identity_pubkey.cb`.
/// Returns `Ok(None)` if no key has been pinned yet (first-boot TOFU condition).
pub fn load_pinned_operator_identity(
    state_dir: &Path,
) -> Result<Option<PinnedOperatorIdentity>, SubstrateError> {
    let path = state_dir.join(OPERATOR_IDENTITY_PUBKEY_FILENAME);
    match fs::File::open(&path) {
        Ok(mut f) => {
            let mut bytes = Vec::new();
            f.read_to_end(&mut bytes)?;
            PinnedOperatorIdentity::from_canonical_bytes(&bytes)
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(e) => Err(SubstrateError::Io(e)),
    }
}

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
            expiry_unix_ns: expiry_ns,
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
