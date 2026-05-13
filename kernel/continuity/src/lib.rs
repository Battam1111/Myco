//! Myco v0.9 — kernel/continuity
//!
//! The substrate's operating-regime engine. Implements L1_CONTINUITY §1-§5:
//!
//! - **Metabolic cycle** ([`cycle`]) — 5-step cycle structure (tier-1 →
//!   gradient → delta-absorb → DAG-commit → skin-breach check); cadence
//!   dispatch; backlog detection.
//! - **Dormancy state machine** ([`dormancy`]) — alive ↔ dormant; throttled /
//!   paused modes; wake-on-attestation-arrival.
//! - **Cold-resume protocol** ([`cold_resume`]) — pre-handshake invariant
//!   checks (I1/I3/I4/I5/I8); witness emission; quarantine entry on failure.
//! - **Delta atomicity (WAL)** ([`wal`]) — WAL-based commit; crash-recovery
//!   procedure; partial-delta handling.
//! - **Quarantine** ([`quarantine`]) — quarantine sub-state metabolism
//!   (intake-closed; federation-suspended).
//!
//! ## Doctrine traceability
//!
//! - **L0** I1 (lifecycle states), §6 (dormancy host-observability)
//! - **L1_CONTINUITY** §1-§5 (full document)
//! - **L1_HARD_RULES** C9 (`cold_resume_invariant_failure`),
//!   C19 (`paused_dormancy_unsafe_host`)
//! - **L3_PACKAGE_MAP** §6 (kernel/continuity spec, 5 sub-modules)
//!
//! ## M3 implementation status
//!
//! Logic + in-memory state. Real persistence layer (WAL on disk, SSoT
//! snapshot files) is L4-platform-pick within {filesystem-level WAL,
//! embedded library, custom append log} per L1_CONTINUITY §6 default.
//! M3 ships in-memory WAL for testing; M4+ adds disk-backed implementation.
//!
//! Cross-crate integration with kernel/skin (handshake state) and
//! kernel/schema (DAG insertion) is via the public APIs of those crates;
//! kernel/tropism (Python) integration is via separate process / IPC
//! abstraction (M4 wiring).

#![warn(missing_docs)]
#![warn(clippy::all)]
// clippy 1.95+ has a contradictory pair of lints
// (doc_lazy_continuation vs doc_overindented_list_items) — see kernel/shared
// for explanation. Allow them at the doc-style level.
#![allow(clippy::doc_lazy_continuation)]
#![allow(clippy::doc_overindented_list_items)]
#![forbid(unsafe_code)]

pub mod cold_resume;
pub mod cycle;
pub mod dormancy;
pub mod quarantine;
pub mod wal;

/// Crate-level error type aggregating sub-module errors.
#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum Error {
    /// Metabolic-cycle error.
    #[error("cycle: {0}")]
    Cycle(#[from] cycle::CycleError),

    /// Dormancy state-machine error.
    #[error("dormancy: {0}")]
    Dormancy(#[from] dormancy::DormancyError),

    /// Cold-resume error.
    #[error("cold_resume: {0}")]
    ColdResume(#[from] cold_resume::ColdResumeError),

    /// WAL error.
    #[error("wal: {0}")]
    Wal(#[from] wal::WalError),

    /// Quarantine error.
    #[error("quarantine: {0}")]
    Quarantine(#[from] quarantine::QuarantineError),

    /// Shared-kernel error.
    #[error("shared: {0}")]
    Shared(#[from] myco_kernel_shared::Error),
}

/// Result alias for crate-level operations.
pub type Result<T> = std::result::Result<T, Error>;
