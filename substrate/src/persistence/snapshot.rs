//! Snapshot persistence (M21.5 + M25.0) — `<state_dir>/snapshot.cb`.
//!
//! The snapshot is a CACHE — substrate boot works without it via full DAG
//! replay. When present + valid, it accelerates boot by restoring Rust-side
//! derived state from a known DAG tip. M25.0 wraps the payload in an Ed25519
//! signed envelope so a forged snapshot cannot masquerade.

use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;

use super::ensure_state_dir;
use crate::SubstrateError;

/// Filename for the Rust-managed snapshot cache (M21.5).
pub const SNAPSHOT_FILENAME: &str = "snapshot.cb";

/// Current snapshot file format version (M21.5; bumped to v2 in M25.0 for
/// Ed25519 wrapper integrity).
///
/// The loader ALSO ACCEPTS legacy v1 (M21.5 unsigned format) by returning
/// `None` — caller treats absence/legacy as "snapshot cache not usable, do
/// full DAG replay" exactly as if the file were missing.
pub const SNAPSHOT_FORMAT_VERSION: u64 = 2;

/// M25.0: parsed snapshot wrapper returned by [`load_snapshot`].
///
/// `payload` is the unwrapped `DerivedState` canonical bytes (suitable for
/// `DerivedState::from_canonical_bytes`). `signer_pubkey` is the Ed25519
/// public key that signed this snapshot; the caller MUST compare it against
/// the substrate's own signing pubkey before accepting the snapshot, AND MUST
/// call `verify_signature(signer_pubkey, signature, payload)` to confirm the
/// signature is intact.
///
/// Signature verification happens at the caller (server boot path) rather than
/// inside `load_snapshot` itself — this is deliberate. The caller has access
/// to the substrate's own loaded signing keypair and can compare
/// `signer_pubkey` against its own pubkey before trusting the signature.
/// Folding verification into load would inadvertently trust whatever pubkey
/// was embedded in the wrapper.
#[derive(Debug, Clone)]
pub struct LoadedSnapshot {
    /// The unwrapped `DerivedState` canonical bytes — pass this to
    /// `DerivedState::from_canonical_bytes`.
    pub payload: Vec<u8>,
    /// The Ed25519 public key (32 bytes) declared by the signer of this snapshot.
    pub signer_pubkey: [u8; 32],
    /// The Ed25519 signature (64 bytes) over `payload`. Caller verifies via
    /// `verify_signature(signer_pubkey, signature, payload)`.
    pub signature: [u8; 64],
}

/// M21.5 P5 万物互联 + M25.0: atomically save `snapshot.cb` to
/// `<state_dir>/snapshot.cb`, wrapping the payload in a signed envelope.
///
/// The snapshot is a CACHE — substrate boot works without it via full DAG replay.
/// When present + valid, it accelerates boot by restoring Rust-side derived state
/// from a known DAG tip; only events newer than the snapshot's recorded tip need
/// to be replayed.
///
/// ## M25.0 wrapper schema (format_version = 2)
///
/// ```text
/// Map({
///   "format_version": Uint(2),
///   "payload": Bytes,                 // DerivedState canonical bytes
///   "signature": Bytes(64),           // Ed25519(payload) under signer_pubkey
///   "signer_pubkey": Bytes(32),       // who signed
/// })
/// ```
///
/// The signature is computed over the BARE `payload` bytes (not the wrapped
/// canonical-bytes encoding). This means snapshot bytes can be re-wrapped
/// (e.g., upgraded to a newer wrapper format) without re-signing the inner
/// payload — preserving signature stability across wrapper schema bumps.
/// **M26.2 P11.b**: returns the number of bytes written (wrapper + payload +
/// signature). Callers tracking signal #9 (storage/cycle) forward this into
/// `CostAccumulator::record_storage_write`.
pub fn save_snapshot(
    snapshot_payload: &myco_kernel_shared::canonical_bytes::CanonicalBytes,
    signing_key: &myco_kernel_shared::crypto::Ed25519PrivateKey,
    state_dir: &Path,
) -> Result<usize, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{encode, Value};
    ensure_state_dir(state_dir)?;
    let final_path = state_dir.join(SNAPSHOT_FILENAME);
    let tmp_path = state_dir.join(format!("{SNAPSHOT_FILENAME}.tmp"));

    let payload_bytes = snapshot_payload.as_ref();
    let signature = signing_key.sign(payload_bytes);
    let signer_pubkey = signing_key.public_key();

    let mut wrapper = BTreeMap::new();
    wrapper.insert(
        "format_version".to_string(),
        Value::Uint(SNAPSHOT_FORMAT_VERSION),
    );
    wrapper.insert(
        "payload".to_string(),
        Value::Bytes(payload_bytes.to_vec()),
    );
    wrapper.insert(
        "signature".to_string(),
        Value::Bytes(signature.as_ref().to_vec()),
    );
    wrapper.insert(
        "signer_pubkey".to_string(),
        Value::Bytes(signer_pubkey.as_ref().to_vec()),
    );
    let wrapped = encode(&Value::Map(wrapper))
        .map_err(|e| SubstrateError::Protocol(format!("snapshot wrapper encode: {e}")))?;
    let n = wrapped.as_ref().len();

    {
        let mut f = fs::File::create(&tmp_path)?;
        f.write_all(wrapped.as_ref())?;
        f.sync_all()?;
    }
    fs::rename(&tmp_path, &final_path)?;
    Ok(n)
}

/// M21.5 + M25.0: load `snapshot.cb` from `<state_dir>/snapshot.cb` and parse
/// the wrapper.
///
/// Returns:
/// - `Ok(Some(LoadedSnapshot))` — file exists, parses cleanly, format = v2.
///   Caller MUST `verify_signature(signer_pubkey, signature, payload)` AND
///   compare `signer_pubkey` against the substrate's own loaded signing
///   pubkey before trusting the payload. On either failure, caller falls
///   back to full DAG replay.
/// - `Ok(None)` — file missing, OR legacy v1 (M21.5 unsigned format), OR
///   any wrapper-schema mismatch. Caller falls back to full DAG replay.
/// - `Err(...)` — I/O error reading the file, or canonical-bytes decode
///   error on otherwise-readable bytes. The caller should treat decode
///   errors as "corrupted snapshot → discard + DAG replay" but bubbling the
///   error preserves visibility for the operator.
pub fn load_snapshot(state_dir: &Path) -> Result<Option<LoadedSnapshot>, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    let path = state_dir.join(SNAPSHOT_FILENAME);
    let mut f = match fs::File::open(&path) {
        Ok(f) => f,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(e) => return Err(SubstrateError::Io(e)),
    };
    let mut bytes = Vec::new();
    f.read_to_end(&mut bytes)?;
    let decoded = decode(&bytes)
        .map_err(|e| SubstrateError::Protocol(format!("snapshot wrapper decode: {e}")))?;
    let map = match decoded {
        Value::Map(m) => m,
        _ => return Ok(None), // not a wrapper Map → treat as legacy/corrupted
    };
    // Version gate. v1 (legacy M21.5 unsigned) and unknown future versions both
    // return None: caller treats as "no usable snapshot" and falls back to DAG
    // replay. Only v2 enters the LoadedSnapshot construction path.
    let version = match map.get("format_version") {
        Some(Value::Uint(n)) => *n,
        _ => return Ok(None),
    };
    if version != SNAPSHOT_FORMAT_VERSION {
        return Ok(None);
    }
    let payload = match map.get("payload") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => return Ok(None),
    };
    let signature_bytes = match map.get("signature") {
        Some(Value::Bytes(b)) if b.len() == 64 => b,
        _ => return Ok(None),
    };
    let signer_pubkey_bytes = match map.get("signer_pubkey") {
        Some(Value::Bytes(b)) if b.len() == 32 => b,
        _ => return Ok(None),
    };
    let mut signature = [0u8; 64];
    signature.copy_from_slice(signature_bytes);
    let mut signer_pubkey = [0u8; 32];
    signer_pubkey.copy_from_slice(signer_pubkey_bytes);
    Ok(Some(LoadedSnapshot {
        payload,
        signer_pubkey,
        signature,
    }))
}
