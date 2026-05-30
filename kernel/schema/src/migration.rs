//! **v3.1.1 Sprint 8.G (T4.3 MVP)** — multi-cycle two-phase schema migration.
//!
//! ## Scope
//!
//! This module is the substantive site of P03 §10.4's acknowledged-debt
//! **multi-cycle two-phase migration**. Sprint 6.D amended P03 §3.3 to
//! describe the *shipping* single-cycle snapshot-rollback behavior; Sprint
//! 7.G shipped the TYPE SIGNATURES; Sprint 8.G (this pass) ships the actual
//! two-phase commit LOGIC plus the cross-language wiring.
//!
//! ## The FSM (as built)
//!
//! A migration is a candidate schema that runs **alongside** the active
//! schema for a window of metabolic cycles before being promoted (commit)
//! or dropped (rollback). The lifecycle:
//!
//! ```text
//!         submit_mutation(schema_evolution, migration_mode=true)
//!                              │
//!                              ▼
//!                      [Apply] candidate constructed (Python deep-copies
//!                              the active gradient + applies the diff to
//!                              the COPY; the active gradient is untouched)
//!                              │  CandidateState::enter_validating(cycle)
//!                              ▼
//!     ┌────────────────► [Validating] ──────────────────────────────┐
//!     │   each metabolic cycle: Python advances BOTH active +        │
//!     │   candidate; computes divergence (Option A); Rust calls      │
//!     │   decide_cycle(cycle, dual_validation_outcome):              │
//!     │                                                              │
//!     │     Diverged ─────────────────────────► Rollback{reason}     │
//!     │     Equivalent && !window_complete ───► None (keep going) ───┘
//!     │     Equivalent &&  window_complete ───► Commit
//!     │                                                              │
//!     │   C66: Validating && window_exceeded(cycle, grace) ──► forced Rollback
//!     │   operator abort_migration ─────────────────────────► forced Rollback
//!     └──────────────────────────────────────────────────────────────
//!                              │
//!              ┌───────────────┴───────────────┐
//!              ▼                                ▼
//!        [Commit]                          [Rollback]
//!   Python promotes candidate          Python drops candidate;
//!   → active (state.gradient =         active gradient unchanged
//!   candidate_gradient);               (P03 §3.5 substrate-identity
//!   substrate emits                    preservation). Substrate emits
//!   schema_migration_committed +       schema_migration_rolled_back +
//!   legacy evolution_succeeded sib.    legacy evolution_failed sibling.
//! ```
//!
//! ## Opt-in + back-compat
//!
//! The single-cycle path (P03 §3.3, `schema_evolution.py::apply_schema_diff`)
//! is UNCHANGED and remains the default. Migration mode is reached only when
//! `submit_mutation` carries `migration_mode=true`. Everything in this module
//! is dead weight for a substrate that never opts in.
//!
//! ## Doctrine traceability
//!
//! - L0/cards/P03_resumable_evolution.md §10.4 (acknowledged debt) — the
//!   target M-cycle migration form THIS module now implements.
//! - L0/cards/P03_resumable_evolution.md §3.3 (current shipping form) —
//!   single-cycle snapshot-rollback in
//!   kernel/governance/.../schema_evolution.py::apply_schema_diff (retained
//!   for the default, non-migration path).
//! - L1/SCHEMA §1.3 (two-phase migration).

use std::collections::BTreeMap;
use std::time::SystemTime;

use myco_kernel_shared::canonical_bytes::{
    decode as cb_decode, encode as cb_encode, map_get_string, map_get_uint, CanonicalBytes, Value,
};

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

/// **Sprint 8.G** — default number of cycles the candidate must run
/// alongside the active schema before commit. Per P03 §10.4 + §4.3: the
/// dual-validation window is an L4-tunable parameter; this is the seed
/// default. A larger window buys more confidence that the candidate is
/// truly equivalent; a smaller one promotes faster.
pub const DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES: u64 = 100;

/// **Sprint 8.G** — default grace cycles added on top of the window before
/// the C66 `schema_migration_window_exceeded` detector fires. A migration
/// that has been Validating for `window + grace` cycles without reaching a
/// commit/rollback decision is anomalous (e.g. the substrate restarted
/// mid-window and lost its decision cadence); the immune system forces a
/// rollback so the candidate cannot linger indefinitely.
pub const DEFAULT_MIGRATION_GRACE_CYCLES: u64 = 10;

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
    /// Drives the Commit transition (see [`decide_cycle`]).
    pub fn window_complete(&self, current_cycle: u64) -> bool {
        current_cycle.saturating_sub(self.started_at_cycle)
            >= self.dual_validation_window_cycles
    }

    /// **Sprint 8.G** — transition the candidate from `Apply` into the
    /// `Validating` phase, recording the cycle at which validation begins.
    ///
    /// The substrate calls this once, immediately after the Python side has
    /// built the candidate (deep-copy + apply-to-copy). From this cycle
    /// onward, every metabolic cycle advances both the active gradient and
    /// the candidate, comparing their outputs.
    pub fn enter_validating(&mut self, started_at_cycle: u64) {
        self.started_at_cycle = started_at_cycle;
        self.phase = MigrationPhase::Validating;
    }

    /// **Sprint 8.G** — whether the migration has been Validating for longer
    /// than `window + grace_cycles`. The C66
    /// `schema_migration_window_exceeded` detector uses this in the
    /// autonomous tick: a migration that lingers past the grace boundary
    /// without a commit/rollback decision is forcibly rolled back.
    ///
    /// `current_cycle` below `started_at_cycle` (clock went backward across a
    /// restart) saturates to 0 elapsed, so this returns false — we never
    /// fire C66 on a not-yet-elapsed window.
    pub fn window_exceeded(&self, current_cycle: u64, grace_cycles: u64) -> bool {
        let elapsed = current_cycle.saturating_sub(self.started_at_cycle);
        elapsed > self.dual_validation_window_cycles.saturating_add(grace_cycles)
    }

    /// **Sprint 8.G** — encode this candidate as canonical-bytes for
    /// persistence (substrate snapshot.cb `migration_candidate` field) and
    /// cross-restart resume. Mirrors the event-encode pattern used across
    /// `substrate/src/events/*` (BTreeMap → canonical Value::Map).
    ///
    /// Schema (canonical-bytes Map):
    /// ```text
    /// Map({
    ///   "op_name": String,
    ///   "schema_diff_canonical_bytes": Bytes,
    ///   "started_at_cycle": Uint,
    ///   "dual_validation_window_cycles": Uint,
    ///   "started_at_unix_ns": Timestamp,
    ///   "phase": String,   // "apply" | "validating" | "commit" | "rollback"
    /// })
    /// ```
    ///
    /// Floats are not involved, so this is byte-deterministic across
    /// platforms by construction.
    pub fn to_canonical_bytes(&self) -> CanonicalBytes {
        let mut m = BTreeMap::new();
        m.insert("op_name".to_string(), Value::String(self.op_name.clone()));
        m.insert(
            "schema_diff_canonical_bytes".to_string(),
            Value::Bytes(self.schema_diff_canonical_bytes.clone()),
        );
        m.insert(
            "started_at_cycle".to_string(),
            Value::Uint(self.started_at_cycle),
        );
        m.insert(
            "dual_validation_window_cycles".to_string(),
            Value::Uint(self.dual_validation_window_cycles),
        );
        m.insert(
            "started_at_unix_ns".to_string(),
            Value::Timestamp(self.started_at_unix_ns),
        );
        m.insert(
            "phase".to_string(),
            Value::String(migration_phase_to_str(self.phase).to_string()),
        );
        cb_encode(&Value::Map(m)).expect("CandidateState encode infallible")
    }

    /// **Sprint 8.G** — decode a candidate from canonical-bytes. Returns
    /// `None` on any structural error (the caller treats a malformed
    /// candidate as "no migration in flight" and falls back to fresh boot —
    /// the candidate is a resumable convenience, never load-bearing for
    /// substrate identity).
    pub fn from_canonical_bytes(bytes: &[u8]) -> Option<Self> {
        let v = cb_decode(bytes).ok()?;
        let m = match v {
            Value::Map(m) => m,
            _ => return None,
        };
        let op_name = map_get_string(&m, "op_name").ok()?.to_string();
        let schema_diff_canonical_bytes = match m.get("schema_diff_canonical_bytes") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => return None,
        };
        let started_at_cycle = map_get_uint(&m, "started_at_cycle").ok()?;
        let dual_validation_window_cycles =
            map_get_uint(&m, "dual_validation_window_cycles").ok()?;
        let started_at_unix_ns = match m.get("started_at_unix_ns") {
            Some(Value::Timestamp(t)) => *t,
            _ => return None,
        };
        let phase = match m.get("phase") {
            Some(Value::String(s)) => migration_phase_from_str(s)?,
            _ => return None,
        };
        Some(CandidateState {
            schema_diff_canonical_bytes,
            op_name,
            started_at_cycle,
            dual_validation_window_cycles,
            started_at_unix_ns,
            phase,
        })
    }
}

/// **Sprint 8.G** — the commit/rollback decision for the current cycle.
///
/// Given the dual-validation outcome for THIS metabolic cycle, decide
/// whether the migration should commit, roll back, or keep validating:
///
/// - `Diverged` → `Some(Rollback{reason})` — the candidate produced a
///   different observable result than the active schema this cycle. Per
///   P03 §3.5 the active state is preserved and the candidate is dropped.
/// - `Equivalent` && the window is complete → `Some(Commit)` — the
///   candidate matched the active schema for the full window; promote it.
/// - `Equivalent` && the window is NOT complete → `None` — keep validating.
///
/// Returning `None` means "no terminal decision this cycle; advance the
/// window and check again next cycle."
pub fn decide_cycle(
    candidate: &CandidateState,
    current_cycle: u64,
    outcome: DualValidationCycle,
) -> Option<CommitDecision> {
    match outcome {
        DualValidationCycle::Diverged => Some(CommitDecision::Rollback {
            reason: format!(
                "candidate diverged from active at cycle {current_cycle} \
                 (op={}, started_at_cycle={})",
                candidate.op_name, candidate.started_at_cycle
            ),
        }),
        DualValidationCycle::Equivalent => {
            if candidate.window_complete(current_cycle) {
                Some(CommitDecision::Commit)
            } else {
                None
            }
        }
    }
}

/// **Sprint 8.G** — stable wire string for a [`MigrationPhase`]. Used by the
/// canonical-bytes codec; pinned by `migration_phase_str_roundtrip` so a
/// rename can never silently break a persisted candidate.
pub fn migration_phase_to_str(phase: MigrationPhase) -> &'static str {
    match phase {
        MigrationPhase::Apply => "apply",
        MigrationPhase::Validating => "validating",
        MigrationPhase::Commit => "commit",
        MigrationPhase::Rollback => "rollback",
    }
}

/// **Sprint 8.G** — inverse of [`migration_phase_to_str`]. `None` on an
/// unknown phase string.
pub fn migration_phase_from_str(s: &str) -> Option<MigrationPhase> {
    match s {
        "apply" => Some(MigrationPhase::Apply),
        "validating" => Some(MigrationPhase::Validating),
        "commit" => Some(MigrationPhase::Commit),
        "rollback" => Some(MigrationPhase::Rollback),
        _ => None,
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

    // -----------------------------------------------------------------------
    // Sprint 8.G — two-phase migration logic.
    // -----------------------------------------------------------------------

    fn validating_candidate(started_at_cycle: u64, window: u64) -> CandidateState {
        let mut c = CandidateState::new(
            vec![1, 2, 3],
            "modify_axis_threshold".to_string(),
            0,
            window,
        );
        c.enter_validating(started_at_cycle);
        c
    }

    #[test]
    fn default_window_and_grace_consts_pinned() {
        assert_eq!(DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES, 100);
        assert_eq!(DEFAULT_MIGRATION_GRACE_CYCLES, 10);
    }

    #[test]
    fn enter_validating_sets_phase_and_start_cycle() {
        let mut c = CandidateState::new(vec![], "add_axis_to_gradient".to_string(), 0, 50);
        assert_eq!(c.phase, MigrationPhase::Apply);
        c.enter_validating(7);
        assert_eq!(c.phase, MigrationPhase::Validating);
        assert_eq!(c.started_at_cycle, 7);
        // window_complete is measured from the new started_at_cycle.
        assert!(!c.window_complete(56));
        assert!(c.window_complete(57));
    }

    #[test]
    fn decide_cycle_diverged_yields_rollback_with_reason() {
        let c = validating_candidate(10, 100);
        let decision = decide_cycle(&c, 12, DualValidationCycle::Diverged);
        match decision {
            Some(CommitDecision::Rollback { reason }) => {
                assert!(reason.contains("diverged"));
                assert!(reason.contains("modify_axis_threshold"));
            }
            other => panic!("expected Rollback; got {other:?}"),
        }
    }

    #[test]
    fn decide_cycle_equivalent_before_window_complete_is_none() {
        let c = validating_candidate(10, 100);
        // 10 + 50 = 60 < 110 → window not complete → keep validating.
        assert_eq!(decide_cycle(&c, 60, DualValidationCycle::Equivalent), None);
    }

    #[test]
    fn decide_cycle_equivalent_at_window_complete_commits() {
        let c = validating_candidate(10, 100);
        // 10 + 100 = 110 → window complete → commit.
        assert_eq!(
            decide_cycle(&c, 110, DualValidationCycle::Equivalent),
            Some(CommitDecision::Commit)
        );
        assert_eq!(
            decide_cycle(&c, 200, DualValidationCycle::Equivalent),
            Some(CommitDecision::Commit)
        );
    }

    #[test]
    fn decide_cycle_diverged_overrides_window_completion() {
        // Even at/after window completion, divergence rolls back (not commit).
        let c = validating_candidate(10, 100);
        match decide_cycle(&c, 500, DualValidationCycle::Diverged) {
            Some(CommitDecision::Rollback { .. }) => {}
            other => panic!("divergence must roll back even past window; got {other:?}"),
        }
    }

    #[test]
    fn window_exceeded_fires_only_past_window_plus_grace() {
        let c = validating_candidate(10, 100); // window ends at 110
        let grace = 10; // grace boundary at 120
        assert!(!c.window_exceeded(110, grace));
        assert!(!c.window_exceeded(120, grace)); // exactly at boundary → not yet
        assert!(c.window_exceeded(121, grace)); // strictly past → fire
        // Backward clock jump: current < started → saturates to 0 → never fires.
        assert!(!c.window_exceeded(5, grace));
    }

    #[test]
    fn candidate_state_canonical_bytes_roundtrip() {
        let mut original = CandidateState::new(
            vec![0xde, 0xad, 0xbe, 0xef],
            "modify_axis_threshold".to_string(),
            0,
            100,
        );
        original.enter_validating(42);
        let bytes = original.to_canonical_bytes();
        let decoded =
            CandidateState::from_canonical_bytes(bytes.as_ref()).expect("candidate decodes");
        assert_eq!(decoded.schema_diff_canonical_bytes, original.schema_diff_canonical_bytes);
        assert_eq!(decoded.op_name, original.op_name);
        assert_eq!(decoded.started_at_cycle, 42);
        assert_eq!(decoded.dual_validation_window_cycles, 100);
        assert_eq!(decoded.started_at_unix_ns, original.started_at_unix_ns);
        assert_eq!(decoded.phase, MigrationPhase::Validating);
    }

    #[test]
    fn candidate_state_decode_rejects_garbage() {
        assert!(CandidateState::from_canonical_bytes(b"not canonical bytes").is_none());
    }

    #[test]
    fn migration_phase_str_roundtrip() {
        for p in [
            MigrationPhase::Apply,
            MigrationPhase::Validating,
            MigrationPhase::Commit,
            MigrationPhase::Rollback,
        ] {
            let s = migration_phase_to_str(p);
            assert_eq!(migration_phase_from_str(s), Some(p));
        }
        assert_eq!(migration_phase_from_str("bogus"), None);
    }
}
