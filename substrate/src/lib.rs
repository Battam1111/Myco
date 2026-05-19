//! Myco v0.9 — substrate daemon (L4 M6).
//!
//! ## Role in the stack
//!
//! `myco-substrate` is the **substrate process** — the binary the operator
//! runtime (e.g. `operators/claude`) spawns to bring a substrate
//! to life. It is both:
//!
//! - **Server** for the operator runtime (reads request frames from stdin,
//!   writes response frames to stdout) — using the same wire protocol as
//!   the M5 kernel/bridge.
//! - **Client** of the Python `kernel/tropism` worker — spawning it via
//!   the existing [`myco_kernel_bridge::client::BridgeClient`] and routing
//!   gradient operations to it.
//!
//! ```text
//!   operators/claude  (TypeScript)
//!         │
//!         │ M5 protocol over stdio (length-prefixed canonical-bytes + HMAC)
//!         ▼
//!   myco-substrate (THIS BINARY)
//!         │
//!         │ M5 protocol over stdio (same bytes, different socket)
//!         ▼
//!   python -m myco_kernel_bridge  (Python worker)
//! ```
//!
//! ## Architecture
//!
//! The TS↔Rust direction reuses the M5 message types verbatim — operations
//! like `register_axis` / `perturb` / `snapshot` are forwarded straight to
//! the Python worker. Operations like `advance` trigger a full
//! [`CycleEngine`](myco_kernel_continuity::cycle::CycleEngine) cycle which
//! internally uses the Python bridge for the gradient-advance step (M5 path)
//! and uses Rust-native stubs for the other 4 steps (M6 minimum).
//!
//! ## Doctrine traceability
//!
//! - L3/PACKAGE_MAP §11 — operators/<host>: this is the substrate
//!   side that bindings talk to.
//! - L1/SKIN §4.1 — operator handshake + envelope discipline (M6 uses the
//!   M5 protocol's session_secret + HMAC; M7+ upgrades to per-handshake
//!   Ed25519 keypair + bootstrap pinning).
//! - L1/CONTINUITY §1.1 — `advance` request triggers the metabolic cycle.

#![warn(missing_docs)]
#![warn(clippy::all)]
#![allow(clippy::doc_lazy_continuation)]
#![allow(clippy::doc_overindented_list_items)]
// **v3.1.1 Sprint 2 doctrine note**: the substrate-wide ban on unsafe code is
// softened from `forbid` to `deny` so OS-sealing FFI modules (Windows DPAPI
// at present; Linux keyring / macOS Secure Enclave in follow-up sprints) can
// override per-module with `#[allow(unsafe_code)]`. Every override MUST:
//   - be a Windows-gated or platform-gated module
//   - live entirely within an FFI-adapter file that carries no business logic
//   - document each `unsafe` block with its safety contract
// The auditable scope of unsafe is therefore the union of those FFI adapters
// — searchable via `git grep "allow(unsafe_code)"` in the substrate crate.
#![deny(unsafe_code)]

pub mod attestation;
pub mod backup;
pub mod dag_query;
pub mod derived_state;
#[cfg(windows)]
#[allow(unsafe_code)] // FFI adapter for Windows DPAPI — see module-level doc.
pub mod dpapi;
pub mod events;
pub mod federation;
pub mod handshake;
pub mod ingest;
pub mod integrity;
pub mod lifecycle;
pub mod observatory;
pub mod persistence;
pub mod persistence_health;
pub mod persistence_runtime;
pub mod python_call_health;
pub mod prune;
pub mod reproduction;
pub mod sealing;
pub mod server;
pub mod wall_clock;

use thiserror::Error;

/// Crate-level error type.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum SubstrateError {
    /// Underlying bridge error (talking to the Python worker).
    #[error("substrate bridge: {0}")]
    Bridge(#[from] myco_kernel_bridge::BridgeError),

    /// Substrate protocol error (the operator runtime sent something invalid).
    #[error("substrate protocol: {0}")]
    Protocol(String),

    /// I/O error reading or writing the operator stdio transport.
    #[error("substrate I/O: {0}")]
    Io(#[from] std::io::Error),

    /// Operator handshake did not complete cleanly.
    #[error("substrate handshake: {0}")]
    Handshake(String),
}

/// Result alias for crate-level errors.
pub type Result<T> = std::result::Result<T, SubstrateError>;
