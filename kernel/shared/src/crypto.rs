//! Cryptographic primitives — Merkle hash, HMAC, Ed25519 signatures.
//!
//! ## Doctrine traceability
//!
//! - L1_SCHEMA §2.1: Merkle DAG content-addressing (BLAKE3 default).
//! - L1_SKIN §2: HMAC envelope_digest keyed by `operator_token`.
//! - L0 §9.2 + L1_GOVERNANCE §2.3: Owner signature verification at
//!   attestation receipt.
//!
//! ## M2 signature suite: Ed25519
//!
//! Per L1_GOVERNANCE §7 candidate set {Ed25519, ECDSA-P256, post-quantum
//! candidates}, Ed25519 is chosen for M2 (RFC 8032; deterministic; well-
//! audited; ed25519-dalek crate). The choice is L4-owner-changeable at
//! genesis time per L1_GOVERNANCE §2.1; for M2 the suite is hard-coded to
//! Ed25519. M3+ can add a suite-tag to allow rotation via L1_GOVERNANCE §3.1
//! cryptographic suite rotation.

use blake3::Hasher;
use ed25519_dalek::{
    Signature, SignatureError, SigningKey, Verifier, VerifyingKey, PUBLIC_KEY_LENGTH,
    SECRET_KEY_LENGTH, SIGNATURE_LENGTH,
};
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

    /// Signature verification failed.
    #[error("signature invalid")]
    SignatureInvalid,

    /// Public key bytes are malformed for the chosen signature suite.
    #[error("public key malformed: {0}")]
    PublicKeyMalformed(String),

    /// Signature bytes are malformed for the chosen signature suite.
    #[error("signature malformed: {0}")]
    SignatureMalformed(String),

    /// Private key seed bytes are malformed (must be exactly 32 bytes for Ed25519).
    #[error("private key seed malformed: {0}")]
    PrivateKeyMalformed(String),
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
    mac.verify_slice(&tag.0)
        .map_err(|_| CryptoError::HmacInvalid)
}

/// Ed25519 public key (32 bytes; RFC 8032 compressed form).
///
/// Per L1_GOVERNANCE §7 M2 suite choice. Substrate stores owner public keys
/// as `Ed25519PublicKey` in `owner_key_history` (L1_GOVERNANCE §3.1).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Ed25519PublicKey(pub [u8; PUBLIC_KEY_LENGTH]);

impl AsRef<[u8]> for Ed25519PublicKey {
    fn as_ref(&self) -> &[u8] {
        &self.0
    }
}

impl Ed25519PublicKey {
    /// Construct from raw 32-byte representation.
    pub fn from_bytes(bytes: [u8; PUBLIC_KEY_LENGTH]) -> Self {
        Ed25519PublicKey(bytes)
    }

    /// Construct from a slice; errors if wrong length OR if the bytes are
    /// not a valid Ed25519 point compression (a malformed pubkey would fail
    /// verification anyway, but we surface it at construction time).
    pub fn from_slice(bytes: &[u8]) -> Result<Self, CryptoError> {
        if bytes.len() != PUBLIC_KEY_LENGTH {
            return Err(CryptoError::PublicKeyMalformed(format!(
                "expected {PUBLIC_KEY_LENGTH} bytes, got {}",
                bytes.len()
            )));
        }
        let mut arr = [0u8; PUBLIC_KEY_LENGTH];
        arr.copy_from_slice(bytes);
        // Validate compression by attempting to build a VerifyingKey.
        VerifyingKey::from_bytes(&arr)
            .map_err(|e| CryptoError::PublicKeyMalformed(e.to_string()))?;
        Ok(Ed25519PublicKey(arr))
    }
}

/// Ed25519 signature (64 bytes; RFC 8032).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Ed25519Signature(pub [u8; SIGNATURE_LENGTH]);

impl AsRef<[u8]> for Ed25519Signature {
    fn as_ref(&self) -> &[u8] {
        &self.0
    }
}

impl Ed25519Signature {
    /// Construct from raw 64-byte representation.
    pub fn from_bytes(bytes: [u8; SIGNATURE_LENGTH]) -> Self {
        Ed25519Signature(bytes)
    }

    /// Construct from a slice; errors if wrong length.
    pub fn from_slice(bytes: &[u8]) -> Result<Self, CryptoError> {
        if bytes.len() != SIGNATURE_LENGTH {
            return Err(CryptoError::SignatureMalformed(format!(
                "expected {SIGNATURE_LENGTH} bytes, got {}",
                bytes.len()
            )));
        }
        let mut arr = [0u8; SIGNATURE_LENGTH];
        arr.copy_from_slice(bytes);
        Ok(Ed25519Signature(arr))
    }
}

/// Ed25519 private key seed (32 bytes). Substrate-side code should NEVER
/// have access to this — owner private keys live outside the substrate
/// process per L1_GOVERNANCE §2.1. This type exists for:
///
/// - operator_bindings (each operator generates a per-handshake keypair
///   that the operator-runtime holds).
/// - anchor_client tests + parity vectors.
///
/// **Substrate-side appearance of an `Ed25519PrivateKey` is a doctrine
/// breach.** L1_HARD_RULES has no direct row for this yet; treat as
/// C4-adjacent (substrate_secret_unsealed analogue).
#[derive(Clone)]
pub struct Ed25519PrivateKey(SigningKey);

impl Ed25519PrivateKey {
    /// Construct from a 32-byte seed.
    pub fn from_seed(seed: &[u8; SECRET_KEY_LENGTH]) -> Self {
        Ed25519PrivateKey(SigningKey::from_bytes(seed))
    }

    /// Construct from an arbitrary-length slice; errors if wrong length.
    pub fn from_slice(bytes: &[u8]) -> Result<Self, CryptoError> {
        if bytes.len() != SECRET_KEY_LENGTH {
            return Err(CryptoError::PrivateKeyMalformed(format!(
                "expected {SECRET_KEY_LENGTH} bytes, got {}",
                bytes.len()
            )));
        }
        let mut arr = [0u8; SECRET_KEY_LENGTH];
        arr.copy_from_slice(bytes);
        Ok(Self::from_seed(&arr))
    }

    /// Derive the corresponding public key.
    pub fn public_key(&self) -> Ed25519PublicKey {
        Ed25519PublicKey(self.0.verifying_key().to_bytes())
    }

    /// Sign a message. Per RFC 8032 Ed25519 is deterministic; identical
    /// inputs always produce identical signatures.
    pub fn sign(&self, message: &[u8]) -> Ed25519Signature {
        use ed25519_dalek::Signer;
        let sig: Signature = self.0.sign(message);
        Ed25519Signature(sig.to_bytes())
    }
}

impl std::fmt::Debug for Ed25519PrivateKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Never leak the seed in debug output — render as a redacted placeholder.
        f.debug_struct("Ed25519PrivateKey")
            .field("seed", &"<redacted>")
            .finish()
    }
}

/// Verify an Ed25519 signature against a public key and message.
///
/// Per L1_GOVERNANCE §2.3: substrate receives signed attestation envelopes
/// and verifies the owner signature against the active owner public key
/// (from `owner_key_history`).
///
/// Returns `Ok(())` on valid signature; [`CryptoError::SignatureInvalid`] on
/// invalid signature or any internal verification error.
pub fn verify_signature(
    public_key: &[u8],
    signature: &[u8],
    message: &[u8],
) -> Result<(), CryptoError> {
    // Reject obviously-wrong sizes early.
    if public_key.len() != PUBLIC_KEY_LENGTH {
        return Err(CryptoError::PublicKeyMalformed(format!(
            "expected {PUBLIC_KEY_LENGTH} bytes, got {}",
            public_key.len()
        )));
    }
    if signature.len() != SIGNATURE_LENGTH {
        return Err(CryptoError::SignatureMalformed(format!(
            "expected {SIGNATURE_LENGTH} bytes, got {}",
            signature.len()
        )));
    }

    let mut pk_arr = [0u8; PUBLIC_KEY_LENGTH];
    pk_arr.copy_from_slice(public_key);
    let verifying_key = VerifyingKey::from_bytes(&pk_arr)
        .map_err(|e| CryptoError::PublicKeyMalformed(e.to_string()))?;

    let mut sig_arr = [0u8; SIGNATURE_LENGTH];
    sig_arr.copy_from_slice(signature);
    let sig = Signature::from_bytes(&sig_arr);

    verifying_key
        .verify(message, &sig)
        .map_err(|_: SignatureError| CryptoError::SignatureInvalid)
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
    fn test_verify_signature_wrong_pubkey_length() {
        // 6-byte "pubkey" is rejected at length-check before crypto verify.
        let result = verify_signature(b"pubkey", b"sig", b"content");
        assert!(matches!(result, Err(CryptoError::PublicKeyMalformed(_))));
    }

    #[test]
    fn test_ed25519_sign_and_verify_round_trip() {
        let seed = [0x42u8; 32];
        let private = Ed25519PrivateKey::from_seed(&seed);
        let public = private.public_key();
        let msg = b"hello";
        let sig = private.sign(msg);
        verify_signature(public.as_ref(), sig.as_ref(), msg).unwrap();
    }

    #[test]
    fn test_ed25519_verify_tampered_signature_fails() {
        let seed = [0x42u8; 32];
        let private = Ed25519PrivateKey::from_seed(&seed);
        let public = private.public_key();
        let msg = b"hello";
        let sig = private.sign(msg);

        // Flip a bit in the signature.
        let mut tampered = sig.0;
        tampered[0] ^= 0x01;
        let result = verify_signature(public.as_ref(), &tampered, msg);
        assert_eq!(result, Err(CryptoError::SignatureInvalid));
    }

    #[test]
    fn test_ed25519_verify_wrong_message_fails() {
        let seed = [0x42u8; 32];
        let private = Ed25519PrivateKey::from_seed(&seed);
        let public = private.public_key();
        let sig = private.sign(b"original");
        let result = verify_signature(public.as_ref(), sig.as_ref(), b"tampered");
        assert_eq!(result, Err(CryptoError::SignatureInvalid));
    }

    #[test]
    fn test_ed25519_determinism() {
        // RFC 8032 Ed25519 is deterministic: same key + same message → same signature.
        let seed = [0xabu8; 32];
        let private = Ed25519PrivateKey::from_seed(&seed);
        let msg = b"determinism test";
        let sig1 = private.sign(msg);
        let sig2 = private.sign(msg);
        assert_eq!(sig1.0, sig2.0);
    }

    #[test]
    fn test_ed25519_private_key_debug_redacted() {
        // Per L1_GOVERNANCE §2.1 + L1_HARD_RULES C4-adjacent: never leak the
        // private key in debug output.
        let seed = [0xffu8; 32];
        let private = Ed25519PrivateKey::from_seed(&seed);
        let dbg = format!("{:?}", private);
        assert!(dbg.contains("<redacted>"));
        assert!(!dbg.contains("ff"));
    }

    #[test]
    fn test_ed25519_pubkey_wrong_length_from_slice() {
        let result = Ed25519PublicKey::from_slice(&[0u8; 16]);
        assert!(matches!(result, Err(CryptoError::PublicKeyMalformed(_))));
    }

    #[test]
    fn test_ed25519_signature_wrong_length_from_slice() {
        let result = Ed25519Signature::from_slice(&[0u8; 32]);
        assert!(matches!(result, Err(CryptoError::SignatureMalformed(_))));
    }

    #[test]
    fn test_ed25519_private_key_wrong_length_from_slice() {
        let result = Ed25519PrivateKey::from_slice(&[0u8; 16]);
        assert!(matches!(result, Err(CryptoError::PrivateKeyMalformed(_))));
    }

    #[test]
    fn test_node_hash_to_hex() {
        let h = NodeHash([
            0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc,
            0xde, 0xf0, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0, 0x12, 0x34, 0x56, 0x78,
            0x9a, 0xbc, 0xde, 0xf0,
        ]);
        assert_eq!(
            h.to_hex(),
            "123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0"
        );
    }
}
