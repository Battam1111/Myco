//! Myco v0.9 — kernel/shared
//!
//! Foundation module for the v0.9 substrate-kernel. Provides:
//!
//! - **Canonical-bytes serializer** ([`canonical_bytes`]) — deterministic encoding
//!   from typed values to canonical bytes. Per L0 §9.3 + L2_TRUST_MODEL §3.4,
//!   the serializer spec is spore-inheritable + tier-1 SSoT (per L1_SCHEMA §3.1
//!   + §4.1). Every party (substrate, operator-runtime, anchor-client) computes
//!   identical canonical bytes from identical inputs.
//!
//! - **Cryptographic primitives** ([`crypto`]) — Merkle hash (per L1_SCHEMA §2.1
//!   Merkle DAG), HMAC (per L1_SKIN §2 envelope_digest), signature verification
//!   (per L0 §9.2 anchor-surface verification).
//!
//! - **Sealed-derive wrapper** ([`sealed_derive`]) — OS-level sealing API for
//!   substrate_secret. Substrate code uses sealed-derive without ever seeing
//!   substrate_secret in plaintext (per L1_SKIN §4.2 + pass-3 mycoparasite-1).
//!
//! - **Active-prefix + archived-tail data structure** ([`active_prefix`]) —
//!   generic primitive used for `owner_key_history`, `template_version_registry`,
//!   federation aggregate-reattestation chain (per L1_GOVERNANCE §3.1 +
//!   pass-3 saprotroph-1).
//!
//! ## Doctrine traceability
//!
//! This crate implements the following L0/L1/L2/L3 commitments:
//!
//! - L0 §9.3 canonical-bytes doctrine + §9.2 anchor-surface witness mechanism
//! - L1_SCHEMA §2.1 Merkle DAG content-addressing
//! - L1_SKIN §2 envelope_digest HMAC, §4.2 sealed_derive operator_token
//! - L1_GOVERNANCE §3.1 active-prefix + archived-tail discipline
//! - L1_HARD_RULES C4 substrate_secret_unsealed (CRITICAL detector hook)
//! - L3_PACKAGE_MAP §2 module specification
//!
//! ## Status
//!
//! DRAFT 1 — Milestone 1 (M1) scaffolding. Public API surface is the priority;
//! optimized implementations land in subsequent commits.

#![warn(missing_docs)]
#![warn(clippy::all)]
#![forbid(unsafe_code)]

pub mod canonical_bytes;
pub mod crypto;
pub mod sealed_derive;
pub mod active_prefix;

/// Crate-level error type. Specific errors per submodule are defined in
/// each submodule and converted to [`Error`] via [`thiserror`].
#[derive(Debug, thiserror::Error)]
pub enum Error {
    /// Canonical-bytes serializer error.
    #[error("canonical bytes: {0}")]
    CanonicalBytes(#[from] canonical_bytes::CanonicalBytesError),

    /// Cryptographic primitive error.
    #[error("crypto: {0}")]
    Crypto(#[from] crypto::CryptoError),

    /// Sealed-derive error.
    #[error("sealed derive: {0}")]
    SealedDerive(#[from] sealed_derive::SealedDeriveError),
}

/// Result alias for crate-level errors.
pub type Result<T> = std::result::Result<T, Error>;
