//! Myco v0.9 — kernel/schema
//!
//! The substrate's state representation layer. Implements L1_SCHEMA §1-§4:
//!
//! - **SSoT — Single Source of Truth** ([`ssot`]) — substrate state fields with
//!   tier classification (tier-1 every-cycle validation; tier-2 deep-cycle).
//!   The SSoT designation is itself a contract-identity-level object (per
//!   L1_HARD_RULES F8); migration is two-phase per L0 I3.
//! - **Causal DAG** ([`dag`]) — content-addressed Merkle DAG storage. Each node
//!   carries a hash incorporating parent-hashes; node ID = node hash. The
//!   substrate's identity record carries the current DAG-tip hash. Per L0 §9.2,
//!   at every CI boundary the substrate emits an enumerated list of all DAG
//!   node hashes added since the prior co-sign — NOT just a summary diff.
//! - **Spore-schema** ([`spore`]) — substrate's reproductive payload (per L0
//!   P8 / I7). At spawn, parent constructs a spore-schema with the minimum
//!   fields from L1_SCHEMA §3.1; child verifies closure (per I7 +
//!   L1_HARD_RULES C9 cold_resume invariants).
//! - **Validation tier dispatch** ([`validation`]) — per L1_SCHEMA §4: tier-1
//!   identity-critical fields validated every metabolic cycle; tier-2
//!   everything-else owner-triggered or per-deep-cycle. The L4 escalation to
//!   3-tier is documented as a future option.
//!
//! ## Doctrine traceability
//!
//! - **L0** §9.2 (anchor-surface co-sign with enumerated DAG nodes),
//!   §9.3 (canonical-bytes doctrine), I3 (SSoT consistency check),
//!   I4 (full-fidelity causal DAG), I7 (spore-schema closure)
//! - **L1_SCHEMA** §1 (SSoT), §2 (causal DAG), §3 (spore-schema),
//!   §4 (validation tiers)
//! - **L1_HARD_RULES** C6 (`dag_enumeration_unclosed`),
//!   C7 (`dag_retro_edit_detected`), C8 (`ssot_migration_phase_skip`),
//!   C9 (`cold_resume_invariant_failure`), F8 (SSoT designation),
//!   F9 (DAG retention policy), F10 (storage tier exemption from I5),
//!   F16 (canonical-bytes serializer spec)
//! - **L3_PACKAGE_MAP** §4 (kernel/schema spec, 5 sub-modules)
//!
//! ## M1 implementation status
//!
//! Logic + in-memory storage. Persistence to disk (per L1_SCHEMA §1.1 format
//! TBD-L4 within YAML/TOML/JSON/SQLite/custom candidates) is deferred to M2
//! via `kernel/continuity` WAL + format-specific backend.
//!
//! ## What is and is not in M1
//!
//! **In M1**:
//! - DAG node insertion + Merkle-hash content-addressing + tip maintenance.
//! - DAG enumeration since prior tip (for CI co-sign envelope construction).
//! - In-memory SSoT with tier-1/tier-2 field classification.
//! - Spore-schema struct + canonical-bytes round-trip + hash.
//! - Validation tier dispatch trait + minimal tier-1 validator interface.
//! - Retro-edit detection via hash recomputation (closes L1_HARD_RULES C7
//!   for in-memory tampering; persistence-level detection lands in M2).
//!
//! **Deferred to M2+**:
//! - On-disk storage layout (L1_SCHEMA §1.1 leading candidates: YAML / TOML /
//!   JSON+JSONL / SQLite / custom binary+WAL). L4 picks.
//! - SSoT migration two-phase commit (L1_SCHEMA §1.3).
//! - DAG retention tiering (hot / warm / cold per §2.3); cold-tier
//!   inaccessibility markers.
//! - Recoverability budget + tiered recovery drills (L1_SCHEMA §2.4) —
//!   the entire `kernel/schema/recovery` sub-module per L3_PACKAGE_MAP §4.2.
//! - Disk-pressure handling (L1_SCHEMA §2.5 storage_pressure immune
//!   sporocarp).
//! - Spore-schema spawn closure verification protocol (L1_SCHEMA §3.3).

#![warn(missing_docs)]
#![warn(clippy::all)]
#![forbid(unsafe_code)]

pub mod dag;
pub mod spore;
pub mod ssot;
pub mod validation;

/// Crate-level error type aggregating sub-module errors.
#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum Error {
    /// DAG error.
    #[error("dag: {0}")]
    Dag(#[from] dag::DagError),

    /// SSoT error.
    #[error("ssot: {0}")]
    Ssot(#[from] ssot::SsotError),

    /// Spore-schema error.
    #[error("spore: {0}")]
    Spore(#[from] spore::SporeError),

    /// Validation error.
    #[error("validation: {0}")]
    Validation(#[from] validation::ValidationError),

    /// Shared-kernel error (propagated from `myco-kernel-shared`).
    #[error("shared: {0}")]
    Shared(#[from] myco_kernel_shared::Error),
}

/// Result alias.
pub type Result<T> = std::result::Result<T, Error>;
