//! Sealed-derive wrapper for substrate_secret OS-level sealing.
//!
//! ## Doctrine traceability
//!
//! Per L1_SKIN §4.2 + pass-3 mycoparasite-1 + L1_HARD_RULES C4:
//!
//! - `substrate_secret` is generated at substrate genesis from kernel-entropy
//!   and stored in OS-mediated sealed storage (TPM / kernel-keyring / HSM /
//!   hardware-secure-element). The substrate process NEVER sees substrate_secret
//!   in its address space in plaintext.
//! - Substrate code uses `sealed_derive(handshake_nonce, current_cycle,
//!   kernel_random) → operator_token` via a kernel-mediated API call; the
//!   underlying secret remains sealed.
//! - Plaintext substrate_secret in substrate process memory is a CRITICAL skin
//!   breach (`substrate_secret_unsealed` per L1_HARD_RULES C4).
//!
//! ## M1 implementation
//!
//! M1 ships a **software-only stub** for development + testing. Production
//! substrates pick an OS-sealing backend via Cargo features:
//!
//! - `sealing-tpm`: TPM 2.0 sealed key
//! - `sealing-keyring`: Linux kernel keyring
//! - `sealing-hsm`: PKCS#11 HSM
//! - `sealing-secure-enclave`: macOS / iOS Secure Enclave
//!
//! Each feature-gated backend is implemented in `backends/<name>.rs` (M3+).
//! M1 ships only the [`SoftwareStub`] backend for development.
//!
//! ## Safety acknowledgment (per L2_TRUST_MODEL §6)
//!
//! Per P1.a self-hosting, the agent maintains substrate code; an adversarial
//! agent CAN replace this wrapper with one that exposes substrate_secret.
//! The OS-sealing mechanism raises the bar from "edit a file" to "compromise
//! a separate system the owner controls"; it does NOT make P1.a guaranteed-
//! honest. This is acknowledged in L2_TRUST_MODEL §6.

use thiserror::Error;

/// Sealed-derive errors.
#[derive(Debug, Error, PartialEq, Eq)]
pub enum SealedDeriveError {
    /// The backend is not available on this platform / not compiled in.
    #[error("sealing backend unavailable: {0}")]
    BackendUnavailable(String),

    /// The substrate_secret has not been initialized (genesis missing or sealed
    /// storage empty).
    #[error("substrate_secret not initialized")]
    NotInitialized,

    /// Underlying OS / hardware error.
    #[error("backend internal error: {0}")]
    BackendError(String),
}

/// The operator_token derived by `sealed_derive` (per L1_SKIN §4.2).
///
/// The token is unlinkable across handshakes from substrate-readable state
/// alone (per L0 I1 prohibition on persisting operator-discriminating
/// attributes).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct OperatorToken(pub [u8; 32]);

impl AsRef<[u8]> for OperatorToken {
    fn as_ref(&self) -> &[u8] {
        &self.0
    }
}

/// The sealed-derive backend trait.
///
/// Production backends implement this for their respective OS-sealing
/// mechanisms. The software stub (M1) implements it in-memory for development.
pub trait SealedDerive {
    /// Derive an `operator_token` from handshake-specific inputs.
    ///
    /// The underlying `substrate_secret` is never exposed; only the derived
    /// token leaves the sealed boundary.
    fn derive(
        &self,
        handshake_nonce: &[u8],
        current_cycle: u64,
        kernel_random: &[u8],
    ) -> Result<OperatorToken, SealedDeriveError>;
}

/// Software-only stub for development + testing.
///
/// **NOT PRODUCTION-SAFE.** Stores `substrate_secret` in-memory in plaintext.
/// Production substrates MUST use one of the feature-gated OS-sealing backends.
///
/// The stub is useful for:
/// - Unit tests of substrate-kernel code that consumes operator_token
/// - Local development before TPM/HSM setup
/// - CI runs in environments without hardware sealing
pub struct SoftwareStub {
    /// In-memory substrate_secret. NOT sealed; visible to the substrate
    /// process. M1 development only.
    substrate_secret: [u8; 32],
}

impl SoftwareStub {
    /// Construct from an in-memory substrate_secret.
    ///
    /// **Warning**: this exposes substrate_secret to the substrate process,
    /// violating L1_SKIN §4.2 OS-sealing requirement. Use only for development.
    pub fn new(substrate_secret: [u8; 32]) -> Self {
        SoftwareStub { substrate_secret }
    }

    /// Construct a stub with a random substrate_secret (development convenience).
    ///
    /// Uses [`rand::thread_rng`] if the `rand` feature is enabled; M1 ships
    /// with a deterministic-for-tests constant since `rand` isn't a baseline
    /// dependency.
    pub fn new_for_test() -> Self {
        // Deterministic test secret. Production gets random from sealed storage.
        SoftwareStub::new([0x42; 32])
    }
}

impl SealedDerive for SoftwareStub {
    fn derive(
        &self,
        handshake_nonce: &[u8],
        current_cycle: u64,
        kernel_random: &[u8],
    ) -> Result<OperatorToken, SealedDeriveError> {
        // Derivation: BLAKE3(substrate_secret || handshake_nonce || current_cycle || kernel_random).
        // Uses Blake3 from kernel/shared::crypto family. This matches the spec sketch in
        // L1_SKIN §4.2: operator_token = sealed_derive(handshake_nonce, current_cycle, kernel_random).
        let mut hasher = blake3::Hasher::new();
        hasher.update(&self.substrate_secret);
        hasher.update(handshake_nonce);
        hasher.update(&current_cycle.to_be_bytes());
        hasher.update(kernel_random);
        let result = hasher.finalize();
        let mut token = [0u8; 32];
        token.copy_from_slice(result.as_bytes());
        Ok(OperatorToken(token))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_software_stub_deterministic_for_same_inputs() {
        let stub = SoftwareStub::new_for_test();
        let nonce = b"handshake_nonce_1";
        let token1 = stub.derive(nonce, 100, b"random1").unwrap();
        let token2 = stub.derive(nonce, 100, b"random1").unwrap();
        assert_eq!(token1, token2);
    }

    #[test]
    fn test_software_stub_different_nonce_gives_different_token() {
        let stub = SoftwareStub::new_for_test();
        let t1 = stub.derive(b"nonce_a", 100, b"random").unwrap();
        let t2 = stub.derive(b"nonce_b", 100, b"random").unwrap();
        assert_ne!(t1, t2);
    }

    #[test]
    fn test_software_stub_different_cycle_gives_different_token() {
        let stub = SoftwareStub::new_for_test();
        let t1 = stub.derive(b"nonce", 100, b"random").unwrap();
        let t2 = stub.derive(b"nonce", 101, b"random").unwrap();
        assert_ne!(t1, t2);
    }

    #[test]
    fn test_software_stub_different_kernel_random_gives_different_token() {
        let stub = SoftwareStub::new_for_test();
        let t1 = stub.derive(b"nonce", 100, b"random_a").unwrap();
        let t2 = stub.derive(b"nonce", 100, b"random_b").unwrap();
        assert_ne!(t1, t2);
    }

    #[test]
    fn test_software_stub_different_secrets_give_different_tokens() {
        let stub1 = SoftwareStub::new([0x11; 32]);
        let stub2 = SoftwareStub::new([0x22; 32]);
        let t1 = stub1.derive(b"nonce", 100, b"random").unwrap();
        let t2 = stub2.derive(b"nonce", 100, b"random").unwrap();
        assert_ne!(t1, t2);
    }
}
