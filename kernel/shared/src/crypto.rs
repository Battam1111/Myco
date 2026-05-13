//! Cryptographic primitives — Merkle hash, HMAC, signature verification.
//!
//! ## Doctrine traceability
//!
//! - L1_SCHEMA §2.1: Merkle DAG content-addressing (BLAKE3 default).
//! - L1_SKIN §2: HMAC envelope_digest keyed by `operator_token`.
//! - L0 §9.2: Owner signature verification at attestation receipt.
//!
//! ## M1 status
//!
//! Merkle hash + HMAC implemented. Signature verification is stubbed for M1;
//! actual signature algorithm choice (Ed25519, ECDSA-P256, etc.) is L4 per
//! L1_GOVERNANCE §7 deferred items. M2 lands the production signature path.

use blake3::Hasher;
use hmac::{Hmac, Mac};
use sha2::Sha256;
use thiserror::Error;

/// Cryptographic primitive errors.
#[derive(Debug, Error, PartialEq, Eq)]
pub enum CryptoError {
    /// HMAC keyed by an empty key (forbidden).
    #[error("HMAC key cannot be empty")]
    HmacEmptyKey,

    /// HMAC verification failed.
    #[error("HMAC verification failed")]
    HmacInvalid,

    /// Signature verification failed (stubbed M1).
    #[error("signature invalid")]
    SignatureInvalid,
}

/// A content-addressed hash. 32 bytes; BLAKE3-default.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct NodeHash(pub [u8; 32]);

impl AsRef<[u8]> for NodeHash {
    fn as_ref(&self) -> &[u8] {
        &self.0
    }
}

impl NodeHash {
    /// Construct from raw bytes (e.g., for tests).
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        NodeHash(bytes)
    }

    /// Hex representation (lowercase, 64 chars).
    pub fn to_hex(&self) -> String {
        let mut s = String::with_capacity(64);
        for b in &self.0 {
            s.push_str(&format!("{:02x}", b));
        }
        s
    }
}

/// Compute the Merkle hash of a DAG node from its parent hashes + content
/// canonical bytes (per L1_SCHEMA §2.1).
///
/// Hash = BLAKE3(parents_concat || content_canonical_bytes)
///
/// where parents_concat is the concatenation of parent NodeHash bytes in
/// declared order.
pub fn merkle_hash(parent_hashes: &[NodeHash], content_canonical_bytes: &[u8]) -> NodeHash {
    let mut hasher = Hasher::new();
    // Include parent count as a length prefix to prevent ambiguity between
    // (1 parent of 64 bytes content) and (2 parents of 0 bytes content).
    let parent_count = parent_hashes.len() as u64;
    hasher.update(&parent_count.to_be_bytes());
    for ph in parent_hashes {
        hasher.update(&ph.0);
    }
    hasher.update(content_canonical_bytes);
    NodeHash(*hasher.finalize().as_bytes())
}

/// HMAC-SHA256 tag.
///
/// Used for envelope_digest in L1_SKIN §2 (keyed by operator_token).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct HmacTag(pub [u8; 32]);

impl AsRef<[u8]> for HmacTag {
    fn as_ref(&self) -> &[u8] {
        &self.0
    }
}

/// Compute HMAC-SHA256 over the given canonical bytes, keyed by the given key.
///
/// Empty keys are forbidden (CryptoError::HmacEmptyKey).
pub fn hmac_sign(key: &[u8], canonical_bytes: &[u8]) -> Result<HmacTag, CryptoError> {
    if key.is_empty() {
        return Err(CryptoError::HmacEmptyKey);
    }
    let mut mac = <Hmac<Sha256>>::new_from_slice(key).expect("HMAC accepts any key length");
    mac.update(canonical_bytes);
    let result = mac.finalize().into_bytes();
    let mut tag = [0u8; 32];
    tag.copy_from_slice(&result);
    Ok(HmacTag(tag))
}

/// Verify an HMAC-SHA256 tag matches the canonical bytes under the given key.
///
/// Returns Ok(()) on match; Err(CryptoError::HmacInvalid) on mismatch.
/// Constant-time comparison (the `Mac` trait's verify is constant-time).
pub fn hmac_verify(key: &[u8], canonical_bytes: &[u8], tag: &HmacTag) -> Result<(), CryptoError> {
    if key.is_empty() {
        return Err(CryptoError::HmacEmptyKey);
    }
    let mut mac = <Hmac<Sha256>>::new_from_slice(key).expect("HMAC accepts any key length");
    mac.update(canonical_bytes);
    mac.verify_slice(&tag.0).map_err(|_| CryptoError::HmacInvalid)
}

/// Verify a signature (M1 stub — actual algorithm M2-decided).
///
/// L1_GOVERNANCE §7 lists Ed25519, ECDSA-P256, post-quantum candidates as L4
/// options. M1 ships this stub returning SignatureInvalid for any non-empty
/// signature; M2 lands the production path with the chosen algorithm.
pub fn verify_signature(
    _public_key: &[u8],
    _signature: &[u8],
    _canonical_bytes: &[u8],
) -> Result<(), CryptoError> {
    // M1 stub: not yet implemented.
    Err(CryptoError::SignatureInvalid)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_merkle_hash_determinism() {
        let parent = NodeHash([1; 32]);
        let content = b"hello";
        let h1 = merkle_hash(&[parent], content);
        let h2 = merkle_hash(&[parent], content);
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_merkle_hash_parents_matter() {
        let p1 = NodeHash([1; 32]);
        let p2 = NodeHash([2; 32]);
        let content = b"hello";
        let h_with_p1 = merkle_hash(&[p1], content);
        let h_with_p2 = merkle_hash(&[p2], content);
        assert_ne!(h_with_p1, h_with_p2);
    }

    #[test]
    fn test_merkle_hash_content_matters() {
        let parent = NodeHash([1; 32]);
        let h1 = merkle_hash(&[parent], b"hello");
        let h2 = merkle_hash(&[parent], b"world");
        assert_ne!(h1, h2);
    }

    #[test]
    fn test_merkle_hash_parent_count_disambiguated() {
        // The parent-count prefix ensures these don't collide:
        //   1 parent (32 bytes) + 32-byte content
        //   2 parents (64 bytes) + 0-byte content
        let p = NodeHash([0xab; 32]);
        let h_one_parent = merkle_hash(&[p], &[0xcd; 32]);
        let h_two_parents = merkle_hash(&[p, NodeHash([0xcd; 32])], &[]);
        assert_ne!(h_one_parent, h_two_parents);
    }

    #[test]
    fn test_hmac_round_trip() {
        let key = b"operator_token_test";
        let canonical = b"envelope_canonical_bytes";
        let tag = hmac_sign(key, canonical).unwrap();
        hmac_verify(key, canonical, &tag).unwrap();
    }

    #[test]
    fn test_hmac_wrong_key_fails() {
        let canonical = b"envelope_canonical_bytes";
        let tag = hmac_sign(b"correct_key", canonical).unwrap();
        let result = hmac_verify(b"wrong_key", canonical, &tag);
        assert!(matches!(result, Err(CryptoError::HmacInvalid)));
    }

    #[test]
    fn test_hmac_wrong_content_fails() {
        let key = b"key";
        let tag = hmac_sign(key, b"original").unwrap();
        let result = hmac_verify(key, b"tampered", &tag);
        assert!(matches!(result, Err(CryptoError::HmacInvalid)));
    }

    #[test]
    fn test_hmac_empty_key_fails() {
        let result = hmac_sign(&[], b"content");
        assert!(matches!(result, Err(CryptoError::HmacEmptyKey)));
    }

    #[test]
    fn test_signature_stub_returns_invalid() {
        let result = verify_signature(b"pubkey", b"sig", b"content");
        assert!(matches!(result, Err(CryptoError::SignatureInvalid)));
    }

    #[test]
    fn test_node_hash_to_hex() {
        let h = NodeHash([
            0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0,
        ]);
        assert_eq!(
            h.to_hex(),
            "123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0"
        );
    }
}
