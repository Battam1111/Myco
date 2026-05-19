//! **v3.1.1 Sprint 6.K (T1.6)** — at-rest encryption envelope for
//! substrate state files.
//!
//! ## Threat model gap closed
//!
//! Sprint 2.A added Windows DPAPI sealing for `substrate_signing_key.cb`
//! (the Ed25519 seed). But every OTHER state file on disk
//! (`dag.cb`, `manifest.cb`, `owner_keys.cb`, `snapshot.cb`,
//! `nonces.cb`) was plaintext. A filesystem-read attack on
//! `C:\Users\<owner>\.myco\substrate\state\` returned:
//!   - Owner public keys + their rotation history
//!   - All doctrine attestations (L0 revisions, schema evolutions)
//!   - All mutation content
//!   - Federation peer pinning history
//!   - Operator identity + handshake records
//!
//! For a system claiming to be a "永恒" custodian (P14 telos), this was
//! an L1/HARD_RULES C4-adjacent gap: substrate_secret_unsealed extended
//! across the entire state directory beyond just the signing seed.
//!
//! Sprint 6.K closes the gap on Windows by wrapping `dag.cb` and
//! `manifest.cb` through DPAPI. Non-Windows hosts continue with the
//! prior plain-bytes + `chmod 0600` discipline (Sprint 2.B BLAKE3
//! integrity covers bitrot detection; OS-keyring / Secure Enclave
//! migration deferred to Sprint 6.K.2 follow-up).
//!
//! `owner_keys.cb` is Python-side (kernel/governance) and requires
//! Python-Rust cooperative implementation — also Sprint 6.K.2.
//!
//! ## Envelope format
//!
//! The envelope is identifiable by a 4-byte magic prefix `MASR` (Myco
//! At-Rest Sealed). After the magic, canonical-bytes Map:
//!
//! ```text
//! magic_prefix: [u8; 4] = b"MASR"
//! payload_canonical_bytes: {
//!     "at_rest_format_version": Uint,       // 1 (plain) | 2 (DPAPI)
//!     "body": Bytes,                         // raw or DPAPI-wrapped
//! }
//! ```
//!
//! ## Backward compatibility
//!
//! Pre-Sprint-6.K files (raw canonical-bytes of dag/manifest) have NO
//! magic prefix. Load path tries the envelope first; on magic mismatch,
//! falls back to raw bytes. Re-save then upgrades the file to envelope
//! format atomically. No flag-day migration; existing substrates upgrade
//! on the next successful cycle.
//!
//! ## Doctrine traceability
//!
//! - L1/SKIN §4.2: substrate secrets MUST be sealed at rest
//! - L1/HARD_RULES C4 substrate_secret_unsealed: extended scope per
//!   Sprint 6.K (formerly applied only to substrate_signing_key)
//! - COV01 fiduciary duty: substrate state confidentiality protects
//!   the cultivator's strategic plans (mutation history, doctrine
//!   attestations) from filesystem-read attacks on shared hosts

use myco_kernel_shared::canonical_bytes::{decode as cb_decode, encode as cb_encode, Value};

use crate::SubstrateError;

/// Magic prefix identifying the at-rest envelope. 4 bytes ASCII so a
/// hex dump shows "MASR" at file offset 0.
pub const ENVELOPE_MAGIC: &[u8; 4] = b"MASR";

/// Format v1 — plain bytes inside the envelope. Cross-platform; no
/// encryption gain over legacy raw format, but provides a unified
/// envelope shape for future migrations.
pub const ENVELOPE_FORMAT_V1_PLAIN: u64 = 1;

/// Format v2 — DPAPI-wrapped bytes inside the envelope. Windows-only
/// (CryptProtectData / CryptUnprotectData). Reading on non-Windows
/// returns an error.
pub const ENVELOPE_FORMAT_V2_DPAPI: u64 = 2;

/// On Windows, prefer v2 (DPAPI). Elsewhere, prefer v1 (plain — adds
/// envelope identification but no encryption).
#[cfg(windows)]
pub const PREFERRED_WRITE_FORMAT: u64 = ENVELOPE_FORMAT_V2_DPAPI;
#[cfg(not(windows))]
pub const PREFERRED_WRITE_FORMAT: u64 = ENVELOPE_FORMAT_V1_PLAIN;

/// Seal arbitrary bytes for at-rest storage. On Windows, body is wrapped
/// through DPAPI. On non-Windows, body is stored plain (envelope still
/// added for future migration consistency).
///
/// Returns bytes ready to write to disk (magic prefix + canonical-bytes
/// envelope).
pub fn seal_for_at_rest(plaintext: &[u8]) -> Result<Vec<u8>, SubstrateError> {
    let (format_version, body) = match PREFERRED_WRITE_FORMAT {
        v if v == ENVELOPE_FORMAT_V2_DPAPI => {
            // Windows path.
            #[cfg(windows)]
            {
                let wrapped = crate::dpapi::protect(plaintext).map_err(|e| {
                    SubstrateError::Protocol(format!("at_rest_seal DPAPI protect: {e}"))
                })?;
                (ENVELOPE_FORMAT_V2_DPAPI, wrapped)
            }
            // Non-Windows must never compile this branch (PREFERRED_WRITE_FORMAT
            // is V1_PLAIN on non-Windows), but defensively fall back to plain.
            #[cfg(not(windows))]
            (ENVELOPE_FORMAT_V1_PLAIN, plaintext.to_vec())
        }
        _ => (ENVELOPE_FORMAT_V1_PLAIN, plaintext.to_vec()),
    };
    let mut map = std::collections::BTreeMap::new();
    map.insert(
        "at_rest_format_version".to_string(),
        Value::Uint(format_version),
    );
    map.insert("body".to_string(), Value::Bytes(body));
    let payload_bytes = cb_encode(&Value::Map(map))
        .map_err(|e| SubstrateError::Protocol(format!("envelope encode: {e}")))?
        .0;
    let mut out = Vec::with_capacity(ENVELOPE_MAGIC.len() + payload_bytes.len());
    out.extend_from_slice(ENVELOPE_MAGIC);
    out.extend_from_slice(&payload_bytes);
    Ok(out)
}

/// Unseal at-rest bytes. Tries the envelope format first (magic prefix
/// match); on magic mismatch, returns the input as-is treating it as
/// legacy raw bytes (pre-Sprint-6.K format).
///
/// Returns the plaintext body — caller decodes it according to its own
/// schema (Dag::from_canonical_bytes, Manifest::from_canonical_bytes,
/// etc.).
///
/// Returns Err on:
///   - Envelope magic present BUT canonical-bytes decode fails
///   - Format version unknown
///   - DPAPI unwrap fails (Windows)
///   - V2 envelope encountered on non-Windows (refuse silently-wrong load)
pub fn unseal_from_at_rest(bytes: &[u8]) -> Result<Vec<u8>, SubstrateError> {
    if bytes.len() < ENVELOPE_MAGIC.len() || &bytes[..ENVELOPE_MAGIC.len()] != ENVELOPE_MAGIC {
        // Legacy raw bytes (no envelope). Return as-is for backward compat.
        return Ok(bytes.to_vec());
    }
    let payload = &bytes[ENVELOPE_MAGIC.len()..];
    let decoded = cb_decode(payload)
        .map_err(|e| SubstrateError::Protocol(format!("envelope decode: {e}")))?;
    let map = match decoded {
        Value::Map(m) => m,
        _ => {
            return Err(SubstrateError::Protocol(
                "envelope payload is not a Map".to_string(),
            ));
        }
    };
    let format_version = match map.get("at_rest_format_version") {
        Some(Value::Uint(v)) => *v,
        _ => {
            return Err(SubstrateError::Protocol(
                "envelope missing at_rest_format_version Uint".to_string(),
            ));
        }
    };
    let body = match map.get("body") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "envelope missing body Bytes".to_string(),
            ));
        }
    };
    match format_version {
        v if v == ENVELOPE_FORMAT_V1_PLAIN => Ok(body),
        v if v == ENVELOPE_FORMAT_V2_DPAPI => {
            #[cfg(windows)]
            {
                let unwrapped = crate::dpapi::unprotect(&body).map_err(|e| {
                    SubstrateError::Protocol(format!("at_rest_unseal DPAPI unprotect: {e}"))
                })?;
                Ok(unwrapped)
            }
            #[cfg(not(windows))]
            {
                Err(SubstrateError::Protocol(format!(
                    "at_rest envelope is v2 (DPAPI-wrapped) but this is a non-Windows host; \
                     file was likely created on Windows and migrated to this host. \
                     Run a Windows substrate against the same state_dir to migrate to v1. \
                     ({} body bytes)",
                    body.len()
                )))
            }
        }
        unknown => Err(SubstrateError::Protocol(format!(
            "at_rest envelope format_version {unknown} is unknown; refusing to load"
        ))),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trip_seal_unseal() {
        let plain = b"hello world dag canonical bytes".to_vec();
        let sealed = seal_for_at_rest(&plain).expect("seal");
        let unsealed = unseal_from_at_rest(&sealed).expect("unseal");
        assert_eq!(unsealed, plain, "round-trip must be identity");
    }

    #[test]
    fn sealed_bytes_carry_magic_prefix() {
        let plain = b"some bytes".to_vec();
        let sealed = seal_for_at_rest(&plain).expect("seal");
        assert_eq!(
            &sealed[..ENVELOPE_MAGIC.len()],
            ENVELOPE_MAGIC,
            "sealed output must start with magic prefix"
        );
    }

    #[test]
    fn legacy_raw_bytes_unseal_as_passthrough() {
        // Bytes without the magic prefix → returned as-is (backward compat).
        let legacy = b"raw_canonical_bytes_no_envelope".to_vec();
        let unsealed = unseal_from_at_rest(&legacy).expect("legacy passthrough");
        assert_eq!(
            unsealed, legacy,
            "legacy (non-envelope) bytes must round-trip via unseal"
        );
    }

    #[test]
    fn unseal_rejects_corrupt_envelope() {
        // Magic prefix + garbage payload → decode error.
        let mut corrupt = ENVELOPE_MAGIC.to_vec();
        corrupt.extend_from_slice(b"not a valid canonical-bytes Map");
        let result = unseal_from_at_rest(&corrupt);
        assert!(result.is_err(), "corrupt envelope must error");
    }

    #[test]
    fn unseal_rejects_unknown_format_version() {
        // Build an envelope with format_version=99.
        let mut map = std::collections::BTreeMap::new();
        map.insert(
            "at_rest_format_version".to_string(),
            Value::Uint(99),
        );
        map.insert("body".to_string(), Value::Bytes(b"x".to_vec()));
        let payload = cb_encode(&Value::Map(map)).expect("encode").0;
        let mut sealed = ENVELOPE_MAGIC.to_vec();
        sealed.extend_from_slice(&payload);
        let result = unseal_from_at_rest(&sealed);
        assert!(result.is_err(), "unknown format_version must error");
        let err = format!("{}", result.unwrap_err());
        assert!(
            err.contains("99"),
            "error should mention the unknown version; got: {err}"
        );
    }

    #[test]
    fn empty_bytes_unseal_as_empty() {
        // Edge case: completely empty file → not an envelope (too short
        // for magic) → return as-is (empty).
        let result = unseal_from_at_rest(&[]).expect("empty unseal");
        assert!(result.is_empty());
    }
}
