//! Nonce-log persistence (M14; extended M15 with dual-clock).
//!
//! The nonce log is a snapshot of every attestation nonce ever issued
//! (active + consumed + expired), persisted to `<state_dir>/nonces.cb`.

use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;

use super::ensure_state_dir;
use crate::SubstrateError;

/// Filename for the Rust-managed nonce log (M14).
pub const NONCE_LOG_FILENAME: &str = "nonces.cb";

/// Current nonce log file format version (bumped M15: v2 adds optional
/// anchor-clock fields for dual-clock expiry defense against clock skew).
///
/// The loader accepts BOTH v1 (no anchor-clock fields) AND v2 (with anchor-clock
/// fields). Writers always emit v2; v1 → v2 migration on first re-save.
pub const NONCE_LOG_FORMAT_VERSION: u64 = 2;
/// Legacy v1 format version (still accepted by load_nonce_log for backward
/// compat — no anchor-clock fields present).
pub const NONCE_LOG_FORMAT_VERSION_V1: u64 = 1;

/// One persisted nonce entry (M14; extended M15 with dual-clock).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PersistedNonceEntry {
    /// 32-byte nonce.
    pub nonce: [u8; 32],
    /// Content hash this nonce was bound to.
    pub bound_content_hash: [u8; 32],
    /// DAG tip at issuance.
    pub bound_dag_tip: [u8; 32],
    /// Substrate-clock issuance time (unix nanoseconds). M15 — was implicit
    /// in M14 (substrate computed `expiry = now + TTL`); now stored explicitly
    /// so the dual-clock elapsed-time check can verify substrate's own clock
    /// has neither jumped backward nor advanced past TTL.
    pub substrate_issued_at_unix_ns: i64,
    /// Substrate-clock expiry (unix nanoseconds). M14's `expiry_unix_ns`.
    pub expiry_unix_ns: i64,
    /// Operator-supplied anchor-clock issuance time (M15). `None` for v1
    /// nonces or nonces issued without a `client_clock_unix_ns` field.
    pub anchor_clock_issued_at_unix_ns: Option<i64>,
    /// Anchor-clock expiry = anchor_issued + TTL (M15). `None` when
    /// anchor_clock_issued_at is None.
    pub anchor_clock_expiry_unix_ns: Option<i64>,
    /// Whether this nonce has been consumed.
    pub consumed: bool,
}

impl PersistedNonceEntry {
    /// Serialize this entry as a canonical-bytes Map (v2 schema — emits
    /// anchor-clock fields when present).
    ///
    /// `pub(super)`: the `persistence` module's unit tests
    /// (`m15_nonce_entry_without_anchor_clock_omits_those_fields`) call this
    /// directly. It was a private method in the pre-split monolith where the
    /// test lived in the same module; the split moved the test up to
    /// `persistence/mod.rs`, so the method is widened from private to
    /// crate-parent-visible. Not part of the public API.
    pub(super) fn to_value(&self) -> myco_kernel_shared::canonical_bytes::Value {
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
            "substrate_issued_at_unix_ns".to_string(),
            Value::Timestamp(self.substrate_issued_at_unix_ns),
        );
        m.insert(
            "expiry_unix_ns".to_string(),
            Value::Timestamp(self.expiry_unix_ns),
        );
        // M15: optional anchor-clock fields — absent for v1-style nonces.
        if let Some(ts) = self.anchor_clock_issued_at_unix_ns {
            m.insert(
                "anchor_clock_issued_at_unix_ns".to_string(),
                Value::Timestamp(ts),
            );
        }
        if let Some(ts) = self.anchor_clock_expiry_unix_ns {
            m.insert(
                "anchor_clock_expiry_unix_ns".to_string(),
                Value::Timestamp(ts),
            );
        }
        m.insert("consumed".to_string(), Value::Bool(self.consumed));
        Value::Map(m)
    }

    /// Decode a nonce entry from canonical bytes. Tolerates v1 entries
    /// (missing `substrate_issued_at_unix_ns` + anchor-clock fields) by
    /// defaulting to backward-compatible behavior.
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
        // M15: substrate_issued_at_unix_ns is v2 — absent in v1 entries; for
        // back-compat, default to `expiry_unix_ns - 5min` (which makes the
        // dual-clock elapsed-time check pass trivially).
        let substrate_issued_at_unix_ns = match m.get("substrate_issued_at_unix_ns") {
            Some(Value::Timestamp(ts)) => *ts,
            _ => expiry_unix_ns.saturating_sub(NONCE_TTL_DEFAULT_SECONDS * 1_000_000_000),
        };
        // M15: anchor-clock fields are optional. Absence → single-clock mode
        // (M13 semantics preserved).
        let anchor_clock_issued_at_unix_ns = match m.get("anchor_clock_issued_at_unix_ns") {
            Some(Value::Timestamp(ts)) => Some(*ts),
            _ => None,
        };
        let anchor_clock_expiry_unix_ns = match m.get("anchor_clock_expiry_unix_ns") {
            Some(Value::Timestamp(ts)) => Some(*ts),
            _ => None,
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
            substrate_issued_at_unix_ns,
            expiry_unix_ns,
            anchor_clock_issued_at_unix_ns,
            anchor_clock_expiry_unix_ns,
            consumed,
        })
    }
}

/// Nonce TTL in seconds — the substrate-clock window between issuance and
/// expiry. Used both at issuance (server.rs:handle_request_attestation_nonce)
/// and as a back-compat default when migrating v1 → v2 persistence.
pub const NONCE_TTL_DEFAULT_SECONDS: i64 = 300;

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
    // M15: accept both v1 (M14 schema, no anchor-clock fields) and v2 (M15 schema).
    // Higher versions are treated as unknown future — caller falls back to genesis.
    if version != NONCE_LOG_FORMAT_VERSION && version != NONCE_LOG_FORMAT_VERSION_V1 {
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
