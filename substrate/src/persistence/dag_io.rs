//! DAG persistence (M8) — `<state_dir>/dag.cb` save/load.

use std::fs;
use std::io::{Read, Write};
use std::path::Path;

use super::ensure_state_dir;
use crate::SubstrateError;

/// Filename for the Rust-managed DAG state within a state directory (M8).
pub const DAG_FILENAME: &str = "dag.cb";

/// Save a DAG to `<state_dir>/dag.cb` atomically (M8).
///
/// Same pattern as [`super::Manifest::save`]: write to `.tmp`, fsync, atomic
/// rename.
///
/// **M26.2 P11.b**: returns the number of bytes written. Callers tracking
/// signal #9 (storage/cycle) forward this into `CostAccumulator::record_storage_write`.
pub fn save_dag(
    dag: &myco_kernel_schema::dag::Dag,
    state_dir: &Path,
) -> Result<usize, SubstrateError> {
    ensure_state_dir(state_dir)?;
    let final_path = state_dir.join(DAG_FILENAME);
    let tmp_path = state_dir.join(format!("{DAG_FILENAME}.tmp"));
    let bytes = dag.to_canonical_bytes();
    // **v3.1.1 Sprint 6.K (T1.6)** — wrap through at-rest envelope. On
    // Windows this DPAPI-encrypts the body; on non-Windows it adds a
    // v1 plain envelope for format-consistency (no encryption gain, but
    // unified migration shape for future Linux keyring / macOS Secure
    // Enclave).
    let sealed = crate::at_rest_seal::seal_for_at_rest(bytes.as_ref())?;
    let n = sealed.len();
    {
        let mut f = fs::File::create(&tmp_path)?;
        f.write_all(&sealed)?;
        f.sync_all()?;
    }
    fs::rename(&tmp_path, &final_path)?;
    Ok(n)
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
            // **v3.1.1 Sprint 6.K (T1.6)** — try envelope first; falls
            // back to raw legacy bytes on magic mismatch (backward compat
            // for pre-Sprint-6.K substrates). DPAPI unwrap happens inside
            // unseal_from_at_rest when format_version=v2.
            let plaintext = crate::at_rest_seal::unseal_from_at_rest(&bytes)?;
            myco_kernel_schema::dag::Dag::from_canonical_bytes(&plaintext)
                .map_err(|e| SubstrateError::Protocol(format!("dag load: {e}")))
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(e) => Err(SubstrateError::Io(e)),
    }
}
