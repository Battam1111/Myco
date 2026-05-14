//! Myco v0.9 — kernel/bridge (Rust controller side of the cross-process bridge).
//!
//! ## Doctrine
//!
//! Per L1_CONTINUITY §1.1, the substrate's metabolic cycle is orchestrated by
//! [`myco_kernel_continuity`] (Rust). Step 2 (gradient advance) and the
//! sporocarp-emission part of step 3 are L3-mapped to `kernel/tropism` (Python).
//! Crossing that language boundary requires a stable IPC contract — this crate
//! is the Rust controller side of that contract.
//!
//! ## Architecture
//!
//! ```text
//!  ┌─────────────────────────┐   stdio    ┌──────────────────────────┐
//!  │ Rust kernel/continuity  │ ◄────────► │ Python kernel/tropism    │
//!  │   CycleEngine           │            │   GradientConfiguration  │
//!  │     └ TropismBridge ────┼── send ──► │     ↑                    │
//!  │       (impls Grad-      │ ◄─ recv ─┤      └ daemon loop         │
//!  │       Advancer)         │            │                          │
//!  └─────────────────────────┘            └──────────────────────────┘
//! ```
//!
//! The [`BridgeClient`](client::BridgeClient) struct spawns a Python subprocess
//! running `python -m myco_kernel_bridge` and drives it through the
//! length-prefixed canonical-bytes protocol defined in [`mod@protocol`].
//!
//! [`TropismBridge`](tropism_bridge::TropismBridge) wraps a `BridgeClient`
//! and implements the [`myco_kernel_continuity::cycle::GradientAdvancer`]
//! trait, plugging the cross-process worker into the metabolic-cycle engine.
//!
//! ## Wire protocol (M5 v1)
//!
//! Each on-the-wire frame is:
//!
//! ```text
//!  [u32 BE length, 4 bytes][hmac, 32 bytes][body, length-32 bytes]
//! ```
//!
//! The body is a canonical-bytes [`Map`](myco_kernel_shared::canonical_bytes::Value::Map)
//! with four keys (canonically sorted):
//!
//! - `v`: Uint (protocol version = 1)
//! - `type`: String (message type)
//! - `request_id`: Uint (correlation ID)
//! - `payload`: Map (type-specific payload)
//!
//! The HMAC is HMAC-SHA256 over the body bytes, keyed by `session_secret`
//! (established during the `hello` handshake). The `hello` message itself
//! uses the deterministic [`BOOTSTRAP_KEY`](protocol::BOOTSTRAP_KEY).
//!
//! ## Doctrine traceability
//!
//! - L1_CONTINUITY §1.1 — gradient_advance dispatch.
//! - L1_TROPISM §3 — kernel/tropism is the gradient-state owner.
//! - L3_PACKAGE_MAP §6 — Python is the L3-mapped language for tropism.
//! - L1_SKIN §2 — envelope_digest HMAC discipline preserved across IPC.
//! - L0 §9.3 — canonical-bytes determinism preserved across IPC.
//!
//! ## Status
//!
//! DRAFT 1 — M5 minimum-viable. Future M6+ work: networked transport,
//! async I/O, multiplexing workers, hardened crash recovery, OS-sealed
//! session secret derivation.

#![warn(missing_docs)]
#![warn(clippy::all)]
// Same clippy 1.95 contradictory-pair workaround as kernel/shared.
#![allow(clippy::doc_lazy_continuation)]
#![allow(clippy::doc_overindented_list_items)]
#![forbid(unsafe_code)]

pub mod client;
pub mod framing;
pub mod protocol;
pub mod tropism_bridge;

use thiserror::Error;

/// Crate-level error type.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum BridgeError {
    /// Protocol-level error (malformed body, HMAC mismatch, version skew, etc.).
    #[error("bridge protocol: {0}")]
    Protocol(String),

    /// I/O error reading or writing the stdio framed transport.
    #[error("bridge I/O: {0}")]
    Io(#[from] std::io::Error),

    /// Underlying canonical-bytes serialization error.
    #[error("bridge canonical bytes: {0}")]
    CanonicalBytes(#[from] myco_kernel_shared::canonical_bytes::CanonicalBytesError),

    /// Subprocess management error (spawn failed, process died unexpectedly).
    #[error("bridge subprocess: {0}")]
    Subprocess(String),

    /// Frame body or HMAC size exceeded the configured cap.
    #[error("bridge frame too large: {0}")]
    FrameTooLarge(String),

    /// HMAC verification failed on an incoming frame.
    #[error("bridge HMAC mismatch: {0}")]
    HmacMismatch(String),

    /// Request and response correlation IDs did not match.
    #[error("bridge correlation mismatch: expected {expected}, got {got}")]
    CorrelationMismatch {
        /// The expected request_id.
        expected: u64,
        /// The actual request_id received.
        got: u64,
    },
}

/// Result alias for crate-level errors.
pub type Result<T> = std::result::Result<T, BridgeError>;
