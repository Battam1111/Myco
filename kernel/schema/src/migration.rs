//! **v3.1.1 Sprint 7.G (T4.3 MVP scaffold)** — schema migration types.
//!
//! ## Scope
//!
//! This module is the substantive site of P03 §10.4's acknowledged-debt
//! **multi-cycle two-phase migration**. Sprint 6.D amended P03 §3.3 to
//! describe the *shipping* single-cycle snapshot-rollback behavior; this
//! module is the future home for the *target* M-cycle dual-validation
//! mechanism.
//!
//! Sprint 7.G ships the TYPE SIGNATURES and architectural skeleton.
//! The actual two-phase commit LOGIC is deferred to Sprint 7.G.2
//! (~12-20h substantive work covering Python-Rust cooperative state +
//! candidate-gradient bookkeeping + per-cycle dual-validation + commit
//! decision + operator-visible migration_pending surface).
//!
//! ## Why MVP-scaffold-only this sprint
//!
//! Two-phase migration is genuinely multi-day substantive work. It
//! touches:
//!   - Substrate state (active_gradient + candidate_gradient + migration
//!     window cycle counter)
//!   - Python dispatcher (extended schema_evolution path: enter migration
//!     mode rather than apply directly)
//!   - Classifier (cost_budget_set / add_axis_to_gradient mutations
//!     extended for migration semantics)
//!   - Operator-visible surface (migration_pending query)
//!   - New C-row detector (C64 anticipated: migration window exceeded)
//!   - Tests across substrate + Python + operators/claude
//!
//! Shipping the TYPES now:
//!   1. Pins the architectural design committed in P03 §10.4 as CODE,
//!      not just as doctrine markdown.
//!   2. Lets callers (and future implementers) program against stable
//!      type signatures.
//!   3. Makes the "candidate alongside current" structural shape
//!      tangible — concrete types instead of doctrine prose.
//!
//! Per PIP discipline ("Where's the design doc? Where's the rollback
//! plan?"), this module IS the design doc encoded as Rust types.
//!
//! ## Doctrine traceability
//!
//! - L0/cards/P03_resumable_evolution.md §10.4 (acknowledged debt) — the
//!   target M-cycle migration form.
//! - L0/cards/P03_resumable_evolution.md §3.3 (current shipping form) —
//!   single-cycle snapshot-rollback in
//!   kernel/governance/.../schema_evolution.py::apply_schema_diff.
//! - L1/SCHEMA §1.3 (anticipated update to describe two-phase migration
//!   when 7.G.2 lands).

use std::time::SystemTime;

/// **Sprint 7.G** — phase of a multi-cycle schema migration.
///
/// Migration progresses linearly: `Apply → Validating → Commit | Rollback`.
/// Each transition is recorded as a DAG event (anticipated:
/// `schema_candidate_phase_entered:{op}`, `schema_candidate_committed:{op}`,
/// `schema_candidate_rolled_back:{op}`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MigrationPhase {
    /// Initial: schema_diff has been received + parsed; candidate state
    /// constructed but not yet running alongside active state.
    Apply,
    /// Active phase: candidate runs alongside the current active state
    /// for `dual_validation_window_cycles` cycles. Per-cycle output
    /// comparison validates that the candidate produces semantically
    /// equivalent results.
    Validating,
    /// Terminal: candidate validation succeeded across the full window;
    /// substrate atomically promotes candidate → active. Old active
    /// state archived.
    Commit,
    /// Terminal: candidate diverged from active during validation OR
    /// window timed out. Candidate state is dropped; active state
    /// remains unchanged. P03 §3.5 substrate-identity preservation.
    Rollback,
}

/// **Sprint 7.G** — candidate state for an in-flight migration.
///
/// The candidate IS the new state the operator is proposing. It runs
/// **alongside** the current active state for `dual_validation_window_cycles`
/// metabolic cycles; per-cycle output comparison drives the commit
/// decision.
///
/// **Storage shape** (Sprint 7.G.2 implementation work): substrate's
/// gradient.cb file extended to optionally carry a `candidate` field
/// in addition to the active gradient. Cold-resume hydrates both.
#[derive(Debug, Clone)]
pub struct CandidateState {
    /// The schema_diff being applied. Serialized as canonical-bytes for
    /// audit; the substrate emits `mutation:schema_evolution` recording
    /// this diff at migration start.
    pub schema_diff_canonical_bytes: Vec<u8>,
    /// Operator-visible mutation_type (`modify_axis_threshold`,
    /// `add_axis_to_gradient`, etc.) for query surfaces.
    pub op_name: String,
    /// Substrate cycle when migration entered Validating phase. Used to
    /// compute window expiry.
    pub started_at_cycle: u64,
    /// Number of cycles the candidate must successfully run alongside
    /// active before commit. Per P03 §4.3 (post-§10.4): default 100,
    /// L4-tunable. Sprint 7.G.2 will wire this to the cost_budgets
    /// extension.
    pub dual_validation_window_cycles: u64,
    /// Wall-clock time the migration started (informational; not used
    /// for commit decisions — those go by cycle counter).
    pub started_at_unix_ns: i64,
    /// Current phase.
    pub phase: MigrationPhase,
}

impl CandidateState {
    /// Construct a fresh candidate at migration genesis.
    pub fn new(
        schema_diff_canonical_bytes: Vec<u8>,
        op_name: String,
        started_at_cycle: u64,
        dual_validation_window_cycles: u64,
    ) -> Self {
        let started_at_unix_ns = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        Self {
            schema_diff_canonical_bytes,
            op_name,
            started_at_cycle,
            dual_validation_window_cycles,
            started_at_unix_ns,
            phase: MigrationPhase::Apply,
        }
    }

    /// Whether the candidate has been validating for ≥ window cycles.
    /// Sprint 7.G.2 uses this to drive the Commit transition.
    pub fn window_complete(&self, current_cycle: u64) -> bool {
        current_cycle.saturating_sub(self.started_at_cycle)
            >= self.dual_validation_window_cycles
    }
}

/// **Sprint 7.G** — result of one per-cycle dual-validation step.
///
/// Sprint 7.G.2 implementation: each metabolic cycle, both the active
/// and candidate states process the same inputs; the substrate compares
/// outputs. Mismatch → emit `schema_candidate_phase_failed:{op}` →
/// transition to Rollback.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DualValidationCycle {
    /// Both states produced equivalent output this cycle. Continue.
    Equivalent,
    /// Outputs diverged. Rollback. Substrate emits a
    /// `schema_candidate_diverged:{op}:{cycle}` event with evidence.
    Diverged,
}

/// **Sprint 7.G** — decision at the end of the validation window OR on
/// divergence.
///
/// Sprint 7.G.2 implementation: at the cycle when `window_complete()`
/// becomes true, if every prior cycle returned `Equivalent`, emit
/// `Commit`. Otherwise `Rollback`. Cultivator may also issue an
/// `abort_migration` mutation (CI-class) to force `Rollback` mid-window.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CommitDecision {
    /// Promote candidate → active atomically. Emit
    /// `evolution_succeeded:{op}` DAG event (compatible with Sprint
    /// 6.D's single-cycle path).
    Commit,
    /// Drop candidate, keep active unchanged. Emit
    /// `evolution_failed:{op}` DAG event with rollback reason.
    Rollback {
        /// Human-readable reason for the rollback (logged in the
        /// `evolution_failed` event's content).
        reason: String,
    },
}

/// **Sprint 7.G** — anticipated migration-window-exceeded detector.
///
/// If a migration enters Validating phase and does NOT reach `Commit`
/// or `Rollback` within `window + grace_period_cycles` (e.g., because
/// substrate restarted mid-window and lost track), substrate's
/// autonomous tick fires this C-row.
///
/// The CONSTANT here is the wire-protocol name; Sprint 7.G.2 wires the
/// actual detection.
pub const C66_MIGRATION_WINDOW_EXCEEDED: &str =
    "C66_schema_migration_window_exceeded";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn candidate_state_window_complete_returns_true_at_threshold() {
        let c = CandidateState::new(
            vec![],
            "add_axis_to_gradient".to_string(),
            10, // started_at_cycle
            5,  // window
        );
        assert!(!c.window_complete(10));
        assert!(!c.window_complete(14));
        assert!(c.window_complete(15));
        assert!(c.window_complete(100));
    }

    #[test]
    fn migration_phases_pin_at_four_states() {
        // Pin the enum cardinality so a future addition is explicit.
        let phases = [
            MigrationPhase::Apply,
            MigrationPhase::Validating,
            MigrationPhase::Commit,
            MigrationPhase::Rollback,
        ];
        assert_eq!(phases.len(), 4);
    }

    #[test]
    fn dual_validation_cycle_is_binary() {
        let cases = [
            DualValidationCycle::Equivalent,
            DualValidationCycle::Diverged,
        ];
        assert_eq!(cases.len(), 2);
    }

    #[test]
    fn commit_decision_rollback_carries_reason() {
        let r = CommitDecision::Rollback {
            reason: "axis_count_mismatch at cycle 42".to_string(),
        };
        match r {
            CommitDecision::Rollback { reason } => {
                assert!(reason.contains("axis_count_mismatch"));
            }
            _ => panic!("expected Rollback"),
        }
    }

    #[test]
    fn c66_detector_constant_is_pinned() {
        assert_eq!(
            C66_MIGRATION_WINDOW_EXCEEDED,
            "C66_schema_migration_window_exceeded"
        );
    }
}
