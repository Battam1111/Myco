//! Pinned operator identity persistence (M9 TOFU).
//!
//! On first sight of a hello message, the substrate writes the operator's
//! pubkey to `<state_dir>/operator_identity_pubkey.cb`. On subsequent hellos
//! the substrate verifies the operator presents the SAME pubkey.

use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;

use super::{current_unix_ns, ensure_state_dir};
use crate::SubstrateError;

/// Filename for the pinned operator identity public key (M9).
pub const OPERATOR_IDENTITY_PUBKEY_FILENAME: &str = "operator_identity_pubkey.cb";

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
