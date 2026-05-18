//! Myco v0.9 — anchor_surface_host (M-anchor-1).
//!
//! ## Doctrine origin (Phase γ.5)
//!
//! The Phase γ.5 fungal-critic audit found the most critical surviving
//! finding in DRAFT 9 SEALED: «operator-IS-anchor honor-system collapse».
//! Pre-M-anchor-1, the operator process held the owner Ed25519 private key
//! in its own memory. Any agent that could read the operator's memory
//! (or its `~/.myco/operator_keys/identity.key` file) could forge owner
//! signatures — the cornerstone of the trust model was an honor system.
//!
//! ## Architecture
//!
//! ```text
//!  ┌──────────────────────────────┐    local TCP    ┌─────────────────────────────┐
//!  │  Operator process            │ ◄─────────────► │  anchor_surface_host        │
//!  │  (operators/...)     │  127.0.0.1:R    │  (this crate, separate bin) │
//!  │     ▲                        │                  │     ▲                       │
//!  │     │ AnchorSurfaceClient    │                  │     │ owner Ed25519 key     │
//!  │     │ .sign(msg)             │                  │     │ (NEVER leaves this    │
//!  │     │ .getPubkey()           │                  │     │  process; sealed 0600)│
//!  │     ▼                        │                  │     ▼                       │
//!  └──────────────────────────────┘                  └─────────────────────────────┘
//! ```
//!
//! The host binary listens on `127.0.0.1:0` (OS-assigned port) and writes
//! the chosen port to `~/.myco/anchor_surface/port.txt` (0600 on Unix) for
//! the operator client to discover. The owner key is persisted in
//! `~/.myco/anchor_surface/owner_key.cb` (0600).
//!
//! ## What's deferred to M-anchor-1.5
//!
//! - OS sealing (TPM, Secure Enclave, Linux keyring, Windows DPAPI)
//! - Cross-process authentication (HMAC shared secret on the local socket)
//! - TLS on the socket (localhost-only binding + 0600 file permissions
//!   are the interim defense layer)
//!
//! ## Hard rules
//!
//! 1. Owner Ed25519 private key NEVER appears in operator process memory.
//! 2. The host is a SEPARATE binary; operator talks over local TCP.
//! 3. The owner key file is `~/.myco/anchor_surface/owner_key.cb` (0600).
//! 4. `OperatorIdentity` on the operator side is a thin TCP client.
//! 5. ALL existing tests must still pass through the new layer.
//!
//! ## Doctrine traceability
//!
//! - L0 §9 anchor surface (owner-key-out-of-substrate decomposition).
//! - L1/GOVERNANCE §2.1 — owner's private key never enters substrate memory;
//!   M-anchor-1 extends this to: owner's private key never enters operator
//!   memory either.
//! - Phase γ.5 finding: honor-system collapse mitigation.
//! - L1/HARD_RULES C4 substrate_secret_unsealed (analogue: operator never
//!   sees the owner's private seed bytes).

#![warn(missing_docs)]
#![warn(clippy::all)]
#![allow(clippy::doc_lazy_continuation)]
#![allow(clippy::doc_overindented_list_items)]
#![forbid(unsafe_code)]

pub mod identity;
pub mod protocol;

use thiserror::Error;

/// Crate-level error type.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum HostError {
    /// I/O error reading or writing the owner key file or the TCP socket.
    #[error("anchor surface host I/O: {0}")]
    Io(#[from] std::io::Error),

    /// Canonical-bytes encode/decode error.
    #[error("anchor surface host canonical bytes: {0}")]
    CanonicalBytes(#[from] myco_kernel_shared::canonical_bytes::CanonicalBytesError),

    /// Underlying crypto error (signing or key load).
    #[error("anchor surface host crypto: {0}")]
    Crypto(#[from] myco_kernel_shared::crypto::CryptoError),

    /// Protocol-level error (malformed envelope, unknown message type, etc.).
    #[error("anchor surface host protocol: {0}")]
    Protocol(String),

    /// Owner key file has unexpected size or format.
    #[error("anchor surface host identity: {0}")]
    Identity(String),
}

/// Result alias for crate-level errors.
pub type Result<T> = std::result::Result<T, HostError>;

use std::path::PathBuf;

/// Resolve the default state directory for the anchor surface host.
///
/// Priority:
/// 1. `MYCO_ANCHOR_SURFACE_DIR` environment variable (absolute path expected).
/// 2. `$HOME/.myco/anchor_surface/` on Unix.
/// 3. `%USERPROFILE%\.myco\anchor_surface\` on Windows.
/// 4. Falls back to `./myco-anchor-surface/` if neither resolves.
pub fn default_anchor_surface_dir() -> PathBuf {
    if let Ok(custom) = std::env::var("MYCO_ANCHOR_SURFACE_DIR") {
        return PathBuf::from(custom);
    }
    let home = std::env::var("HOME")
        .ok()
        .or_else(|| std::env::var("USERPROFILE").ok());
    if let Some(home_str) = home {
        PathBuf::from(home_str).join(".myco").join("anchor_surface")
    } else {
        PathBuf::from("./myco-anchor-surface")
    }
}

/// Filename for the persisted owner Ed25519 identity (canonical-bytes envelope).
pub const OWNER_KEY_FILENAME: &str = "owner_key.cb";

/// Filename for the port-discovery file used by the operator client to find
/// the running anchor_surface_host's TCP port.
pub const PORT_DISCOVERY_FILENAME: &str = "port.txt";
