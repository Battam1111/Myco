//! **v3.1.1 Sprint 2.C** — backup encryption status SSoT.
//!
//! Per L1/SKIN §8: cultivator owns the backup-encryption symmetric key; the
//! substrate stores ONLY a public status field declaring whether backups
//! are encrypted, declined-explicit, or unspecified. The key NEVER enters
//! state_dir. Operator-runtime performs the encryption; substrate provides
//! plaintext canonical-bytes.
//!
//! L1/HARD_RULES §1.4 (anticipated) + L1/SKIN §9 detection table:
//!   - `backup_encryption_undeclared` (Daily) — emitted on boot when the
//!     SSoT field is None ("unspecified" per L1/SKIN §8). Per L1/SKIN §9:
//!     Daily grade — visible but not breach-quarantine.
//!   - `backup_encryption_status_declared:{status}` — CI-attested DAG event
//!     setting the status. Cultivator chooses one of:
//!       - "encrypted_externally" — operator-runtime encrypts; key is held
//!         by the cultivator outside state_dir
//!       - "cultivator_declined_explicit" — cultivator signs an explicit
//!         declination acknowledging unencrypted backups

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

/// Prefix for `backup_encryption_status_declared:{status}` DAG events
/// (v3.1.1 Sprint 2.C). Emitted by `attestation.rs::handle_submit_mutation`
/// after a successful CI-attested `set_backup_encryption_status` mutation.
/// The substrate's `ServerState::backup_encryption_status` is the cached
/// projection of the latest such event's `status` field.
pub const NODE_TYPE_BACKUP_ENCRYPTION_STATUS_DECLARED_PREFIX: &str =
    "backup_encryption_status_declared:";

/// Canonical status values for `backup_encryption_status_declared:{status}`.
/// Must match the symmetric constant in
/// `kernel/governance/src/myco_kernel_governance/classifier.py`. See test
/// `test_v3_1_1_sprint_2c_backup_encryption_statuses_in_sync`.
pub const BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY: &str = "encrypted_externally";
/// See `BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY`.
pub const BACKUP_ENCRYPTION_STATUS_CULTIVATOR_DECLINED_EXPLICIT: &str =
    "cultivator_declined_explicit";

/// Canonical list of valid backup_encryption_status values. Anything else
/// rejected by the classifier rule + mutation handler.
pub const BACKUP_ENCRYPTION_STATUS_VALID_VALUES: &[&str] = &[
    BACKUP_ENCRYPTION_STATUS_ENCRYPTED_EXTERNALLY,
    BACKUP_ENCRYPTION_STATUS_CULTIVATOR_DECLINED_EXPLICIT,
];

/// Encode a `backup_encryption_status_declared:{status}` event body. Stored
/// alongside the cultivator's CI attestation in the substrate DAG.
///
/// Content (canonical-bytes Map):
/// ```ignore
/// {
///   "status": "encrypted_externally" | "cultivator_declined_explicit",
///   "key_id": "string" | null,    // public derivation pointer; never the key itself
///   "declared_at_cycle": uint,
/// }
/// ```
pub fn encode_backup_encryption_status_declared(
    status: &str,
    key_id: Option<&str>,
    declared_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("status".to_string(), Value::String(status.to_string()));
    match key_id {
        Some(id) => {
            m.insert("key_id".to_string(), Value::String(id.to_string()));
        }
        None => {
            m.insert("key_id".to_string(), Value::Null);
        }
    }
    m.insert(
        "declared_at_cycle".to_string(),
        Value::Uint(declared_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("backup_encryption_status_declared encode infallible")
}

/// Convenience: full `backup_encryption_status_declared:{status}` node_type.
pub fn backup_encryption_status_declared_node_type(status: &str) -> String {
    format!("{NODE_TYPE_BACKUP_ENCRYPTION_STATUS_DECLARED_PREFIX}{status}")
}

/// Decode a `backup_encryption_status_declared:*` event body, returning the
/// declared status string. Returns `None` on malformed content.
pub fn decode_backup_encryption_status(content: &[u8]) -> Option<String> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(content).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    match m.get("status") {
        Some(Value::String(s)) => Some(s.clone()),
        _ => None,
    }
}

/// **v3.1.1 Sprint 2.C** — walk the DAG, return the latest declared
/// backup_encryption_status (or None if no `backup_encryption_status_declared:*`
/// event is present). Called once at boot from `server::run_loop` to seed
/// `ServerState::backup_encryption_status`.
///
/// "Latest" = highest `created_at_cycle`. Ties broken by insertion order
/// (we take the last in insertion order; DAG iteration is deterministic).
pub fn derive_backup_encryption_status_from_dag(
    dag: &myco_kernel_schema::dag::Dag,
) -> Option<String> {
    let mut latest: Option<(u64, String)> = None;
    for node in dag.iter_in_insertion_order() {
        if !node
            .node_type
            .starts_with(NODE_TYPE_BACKUP_ENCRYPTION_STATUS_DECLARED_PREFIX)
        {
            continue;
        }
        if let Some(status) = decode_backup_encryption_status(node.content_canonical_bytes.as_ref())
        {
            // Replace if strictly later cycle, OR same cycle (last writer
            // wins on tie via in-order iteration).
            let replace = match &latest {
                Some((c, _)) => node.created_at_cycle >= *c,
                None => true,
            };
            if replace {
                latest = Some((node.created_at_cycle, status));
            }
        }
    }
    latest.map(|(_, s)| s)
}
