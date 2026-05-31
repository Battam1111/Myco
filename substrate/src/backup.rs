//! **v3.1.1 Sprint 5.I (T1.3)** — substrate backup export mechanism.
//!
//! Closes the COV01 fiduciary-duty gap identified in the v3.1.1 audit:
//! prior to Sprint 5.I, substrate state was a single point of failure.
//! A disk failure killed the substrate permanently. The Sprint 2.C
//! `backup_encryption_status` mutation let the cultivator DECLARE that a
//! backup exists, but no actual backup mechanism shipped.
//!
//! Sprint 5.I ships the substrate-side half: operator calls
//! `EXPORT_BACKUP_TO_DIR { backup_dir }`. Substrate copies every state
//! file to `backup_dir/` and writes `backup_metadata.cb` carrying
//! BLAKE3 content hashes, substrate identity, and cycle counter. The
//! cultivator's job is then to copy `backup_dir` to external encrypted
//! media (per L1/SKIN §8: substrate stores the status pointer; cultivator
//! owns the key + the off-site copy).
//!
//! ## Restore path
//!
//! Restore is operator-driven, not substrate-driven:
//!   1. Operator copies backup_dir/* back to a fresh state_dir
//!   2. Boot a new substrate against the restored state_dir
//!   3. Boot integrity checks (Sprint 5.C C57/C58/C59 + the older C9 path)
//!      validate the restoration succeeded
//!
//! The substrate has no `IMPORT_FROM_BACKUP_DIR` operation because doing so
//! at-runtime would violate P06 (causal chain continuity): a running
//! substrate can't replace its own identity. Restoring = booting fresh
//! against the restored files.
//!
//! ## Files exported
//!
//! Every state file present in `state_dir` is copied. Missing files are
//! silently skipped (legitimate for substrates that haven't reached the
//! milestone that creates each file). Specifically:
//!   - manifest.cb
//!   - dag.cb
//!   - gradient.cb
//!   - owner_keys.cb
//!   - operator_identity_pubkey.cb (deprecated post-M21.4 but tolerated)
//!   - nonces.cb
//!   - snapshot.cb
//!   - substrate_signing_key.cb
//!
//! ## Doctrine traceability
//!
//! - L0/cards/COV01 fiduciary_duty: substrate state recovery is a cultivator
//!   covenant; this gives the substrate side of the contract.
//! - L0/cards/P06 §3.3: every backup event is recorded as a DAG node
//!   (backup_exported:{cycle_prefix}). Future backups are causally chained.
//! - L1/SKIN §8 backup encryption: the substrate emits ONLY the metadata
//!   pointer; the actual key + off-site copy live with the cultivator.

use std::collections::BTreeMap;
use std::path::Path;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};

use crate::persistence::{
    DAG_FILENAME, GRADIENT_FILENAME, MANIFEST_FILENAME, NONCE_LOG_FILENAME,
    OPERATOR_IDENTITY_PUBKEY_FILENAME, SNAPSHOT_FILENAME, SUBSTRATE_SIGNING_KEY_FILENAME,
};
use crate::server::{emit_substrate_event, save_dag_state, ServerState};
use crate::SubstrateError;

/// Owner-keys filename (Python-side). Mirrored here so the backup logic can
/// enumerate it without depending on the Python side at compile time.
const OWNER_KEYS_FILENAME: &str = "owner_keys.cb";

/// The fixed set of state files that comprise a full substrate backup. Each
/// file is OPTIONAL — missing files are silently skipped (legitimate for
/// substrates that haven't reached the milestone that creates each).
pub const BACKUP_FILE_NAMES: &[&str] = &[
    MANIFEST_FILENAME,
    DAG_FILENAME,
    GRADIENT_FILENAME,
    OWNER_KEYS_FILENAME,
    OPERATOR_IDENTITY_PUBKEY_FILENAME,
    NONCE_LOG_FILENAME,
    SNAPSHOT_FILENAME,
    SUBSTRATE_SIGNING_KEY_FILENAME,
];

/// Filename written into the backup directory describing the backup.
pub const BACKUP_METADATA_FILENAME: &str = "backup_metadata.cb";

/// Handle `EXPORT_BACKUP_TO_DIR` request.
///
/// 1. Validates `backup_dir` payload field
/// 2. Creates the directory if it doesn't exist
/// 3. For each file in `BACKUP_FILE_NAMES`: copy from state_dir to
///    backup_dir; compute BLAKE3 hash; track in metadata
/// 4. Writes `backup_metadata.cb` with substrate identity + file table
/// 5. Emits `backup_exported:{cycle_prefix}` DAG event
pub(crate) fn handle_export_backup_to_dir(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let backup_dir_str = match request.payload.get("backup_dir") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "export_backup_to_dir: backup_dir String required".to_string(),
            ));
        }
    };
    let backup_dir = Path::new(&backup_dir_str);

    // Refuse to backup into the state_dir itself — that's a self-overwrite trap.
    if backup_dir == state.state_dir.as_path() {
        return Err(SubstrateError::Protocol(
            "export_backup_to_dir: backup_dir MUST NOT equal state_dir \
             (would corrupt the original)"
                .to_string(),
        ));
    }

    // Create backup_dir if needed. Best-effort; fails surface as IO errors.
    std::fs::create_dir_all(backup_dir).map_err(|e| {
        SubstrateError::Protocol(format!(
            "export_backup_to_dir: create_dir_all({backup_dir_str}) failed: {e}"
        ))
    })?;

    // Copy each present state file; track {filename → (size_bytes, blake3_hash)}.
    let mut file_table: BTreeMap<String, (u64, [u8; 32])> = BTreeMap::new();
    let mut total_bytes: u64 = 0;
    for name in BACKUP_FILE_NAMES {
        let src = state.state_dir.join(name);
        if !src.exists() {
            continue; // skip files this substrate hasn't generated yet
        }
        let bytes = std::fs::read(&src).map_err(|e| {
            SubstrateError::Protocol(format!(
                "export_backup_to_dir: read({}) failed: {e}",
                src.display()
            ))
        })?;
        let size_bytes = bytes.len() as u64;
        total_bytes = total_bytes.saturating_add(size_bytes);
        let hash: [u8; 32] = blake3::hash(&bytes).into();
        // Write to backup_dir/{name}.
        let dst = backup_dir.join(name);
        std::fs::write(&dst, &bytes).map_err(|e| {
            SubstrateError::Protocol(format!(
                "export_backup_to_dir: write({}) failed: {e}",
                dst.display()
            ))
        })?;
        file_table.insert((*name).to_string(), (size_bytes, hash));
    }

    // Build backup_metadata.cb content.
    let captured_at_unix_ns: i64 = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let mut metadata_map = BTreeMap::new();
    metadata_map.insert("format_version".to_string(), Value::Uint(1));
    metadata_map.insert(
        "substrate_id".to_string(),
        Value::Bytes(state.substrate_id().to_vec()),
    );
    metadata_map.insert(
        "cycle_counter".to_string(),
        Value::Uint(state.cycle_counter()),
    );
    metadata_map.insert(
        "captured_at_unix_ns".to_string(),
        Value::Timestamp(captured_at_unix_ns),
    );
    // File table: Map<filename, Map<size_bytes + blake3_hash>>.
    let mut files_value = BTreeMap::new();
    for (name, (size, hash)) in &file_table {
        let mut entry = BTreeMap::new();
        entry.insert("size_bytes".to_string(), Value::Uint(*size));
        entry.insert("blake3_hash".to_string(), Value::Bytes(hash.to_vec()));
        files_value.insert(name.clone(), Value::Map(entry));
    }
    metadata_map.insert("files".to_string(), Value::Map(files_value));

    let metadata_bytes = cb_encode(&Value::Map(metadata_map))
        .map_err(|e| {
            SubstrateError::Protocol(format!(
                "export_backup_to_dir: metadata encode failed: {e}"
            ))
        })?
        .0;
    let metadata_path = backup_dir.join(BACKUP_METADATA_FILENAME);
    std::fs::write(&metadata_path, &metadata_bytes).map_err(|e| {
        SubstrateError::Protocol(format!(
            "export_backup_to_dir: metadata write({}) failed: {e}",
            metadata_path.display()
        ))
    })?;
    let manifest_blake3: [u8; 32] = blake3::hash(&metadata_bytes).into();

    // Emit backup_exported:{prefix} DAG event for the causal record.
    let cycle = state.cycle_counter();
    let event_node_type = format!("backup_exported:{cycle:016x}");
    let mut event_content_map = BTreeMap::new();
    event_content_map.insert(
        "backup_dir".to_string(),
        Value::String(backup_dir_str.clone()),
    );
    event_content_map.insert(
        "files_copied".to_string(),
        Value::Uint(file_table.len() as u64),
    );
    event_content_map.insert("total_bytes".to_string(), Value::Uint(total_bytes));
    event_content_map.insert(
        "manifest_blake3".to_string(),
        Value::Bytes(manifest_blake3.to_vec()),
    );
    event_content_map.insert(
        "captured_at_unix_ns".to_string(),
        Value::Timestamp(captured_at_unix_ns),
    );
    event_content_map.insert(
        "at_cycle".to_string(),
        Value::Uint(state.cycle_counter()),
    );
    let event_content = cb_encode(&Value::Map(event_content_map))
        .map_err(|e| SubstrateError::Protocol(format!("backup event encode: {e}")))?;
    let _ = emit_substrate_event(state, event_node_type, event_content);
    let _ = save_dag_state(state);

    // Build operator response.
    let mut payload = BTreeMap::new();
    payload.insert(
        "files_copied".to_string(),
        Value::Uint(file_table.len() as u64),
    );
    payload.insert("total_bytes".to_string(), Value::Uint(total_bytes));
    payload.insert(
        "manifest_blake3".to_string(),
        Value::Bytes(manifest_blake3.to_vec()),
    );
    payload.insert(
        "captured_at_unix_ns".to_string(),
        Value::Timestamp(captured_at_unix_ns),
    );
    payload.insert(
        "substrate_id".to_string(),
        Value::Bytes(state.substrate_id().to_vec()),
    );

    Ok(Some(Message::new(
        msg_type::EXPORT_BACKUP_TO_DIR_RESPONSE,
        request.request_id,
        payload,
    )))
}
