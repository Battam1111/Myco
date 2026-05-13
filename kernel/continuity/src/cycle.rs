//! Metabolic cycle engine (L1_CONTINUITY §1).
//!
//! ## Doctrine
//!
//! Per L1_CONTINUITY §1.1: each cycle has 5 steps:
//!
//! 1. **Tier-1 invariant checks** (L1_SCHEMA §4.1).
//! 2. **Gradient configuration advances** (L1_TROPISM, or equivalent under
//!    chosen dispatch).
//! 3. **Deltas absorbed** atomically; sporocarps emitted; DAG commits with
//!    new tip-hash.
//! 4. **Skin breach check** (I8) over events absorbed this cycle.
//! 5. **Skin handshake / attestation arrival** processed.
//!
//! A cycle is atomic — either all 5 steps complete and DAG-tip advances,
//! or the cycle aborts and substrate state rolls back to the previous
//! cycle's DAG-tip.
//!
//! ## M3 scope
//!
//! This module ships the cycle engine **state machine + orchestration logic**.
//! The actual per-step work is delegated to caller-supplied trait
//! implementations:
//!
//! - [`Tier1Validator`] — runs tier-1 invariant checks (implemented by
//!   downstream code that has access to kernel/schema::Ssot).
//! - [`GradientAdvancer`] — advances appetite gradient state (implemented by
//!   kernel/tropism cross-process bridge in M4).
//! - [`DeltaAbsorber`] — absorbs queued deltas into the substrate
//!   (implemented by kernel/skin + kernel/schema integration in M4).
//! - [`SkinBreachChecker`] — runs I8 breach detection (kernel/hard_rules; M4).
//! - [`HandshakeProcessor`] — processes new handshake / attestation arrivals
//!   (kernel/skin integration).
//!
//! For M3, these are trait stubs that the engine calls; concrete
//! implementations land at M4 integration.

use thiserror::Error;

/// Cycle-engine errors.
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum CycleError {
    /// A cycle step failed; the engine rolls back to the previous tip.
    #[error("cycle step failed at {step}: {reason}")]
    StepFailed {
        /// Which of the 5 steps failed.
        step: CycleStep,
        /// Free-form description of the failure.
        reason: String,
    },

    /// Cycle execution timeout: a step took longer than the cycle budget.
    /// Sustained backlog triggers `cycle_backlog` (L1_CONTINUITY §1.2).
    #[error("cycle timeout: step {step} exceeded budget")]
    Timeout {
        /// Which step timed out.
        step: CycleStep,
    },
}

/// Identifier for each step in the 5-step metabolic cycle.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CycleStep {
    /// Step 1: tier-1 invariant checks per L1_SCHEMA §4.1.
    Tier1Invariants,
    /// Step 2: gradient configuration advance per L1_TROPISM.
    GradientAdvance,
    /// Step 3: delta absorption + sporocarp emission + DAG commit.
    DeltaAbsorption,
    /// Step 4: skin breach check (I8) per L1_HARD_RULES C-row family.
    SkinBreachCheck,
    /// Step 5: skin handshake / attestation arrival processing.
    HandshakeAttestation,
}

impl std::fmt::Display for CycleStep {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let name = match self {
            CycleStep::Tier1Invariants => "tier1_invariants",
            CycleStep::GradientAdvance => "gradient_advance",
            CycleStep::DeltaAbsorption => "delta_absorption",
            CycleStep::SkinBreachCheck => "skin_breach_check",
            CycleStep::HandshakeAttestation => "handshake_attestation",
        };
        f.write_str(name)
    }
}

/// Step traits — caller-supplied implementations of the 5 cycle steps.
///
/// Step 1: tier-1 invariant checks per L1_SCHEMA §4.1.
pub trait Tier1Validator {
    /// Run tier-1 invariant checks; returns `Err` on any failure.
    fn validate_tier1(&mut self) -> Result<(), String>;
}

/// Step 2: appetite gradient advance per L1_TROPISM.
pub trait GradientAdvancer {
    /// Advance the substrate's appetite gradient state for one cycle.
    fn advance_gradient(&mut self) -> Result<(), String>;
}

/// Step 3: delta absorption + sporocarp emission + DAG commit.
pub trait DeltaAbsorber {
    /// Absorb pending deltas; commit sporocarps to DAG; return number absorbed.
    fn absorb_deltas(&mut self) -> Result<usize, String>;
}

/// Step 4: skin breach check (I8) — observes events from this cycle.
pub trait SkinBreachChecker {
    /// Check for I8 skin breaches; return list of breach immune-event names.
    fn check_skin_breaches(&mut self) -> Result<Vec<String>, String>;
}

/// Step 5: skin handshake / attestation arrival processing.
pub trait HandshakeProcessor {
    /// Process any new handshake / attestation arrivals queued at the skin.
    /// Returns number of envelopes processed.
    fn process_handshake_attestation(&mut self) -> Result<usize, String>;
}

/// Cycle execution context — bundle of trait references the engine drives.
pub struct CycleContext<'a> {
    /// Step 1 implementation.
    pub tier1: &'a mut dyn Tier1Validator,
    /// Step 2 implementation.
    pub gradient: &'a mut dyn GradientAdvancer,
    /// Step 3 implementation.
    pub absorber: &'a mut dyn DeltaAbsorber,
    /// Step 4 implementation.
    pub breach: &'a mut dyn SkinBreachChecker,
    /// Step 5 implementation.
    pub handshake: &'a mut dyn HandshakeProcessor,
}

/// Per-cycle outcome report.
///
/// Emitted by the engine after a successful (or aborted) cycle. Used by
/// the dormancy state machine + observability layer.
#[derive(Debug, Clone)]
pub struct CycleReport {
    /// Cycle number that just completed.
    pub cycle_number: u64,
    /// Number of deltas absorbed during step 3.
    pub deltas_absorbed: usize,
    /// Number of handshake/attestation envelopes processed during step 5.
    pub handshake_events_processed: usize,
    /// Skin breach immune events detected during step 4.
    pub skin_breaches: Vec<String>,
    /// Whether the cycle completed cleanly (true) or aborted (false).
    pub committed: bool,
}

/// Configuration for the cycle engine.
///
/// Per L1_CONTINUITY §1.2: cycle cadence is L4-tunable. M3 ships in-memory
/// engine; M4+ adds the cadence-dispatch loop (wall-clock timer).
#[derive(Debug, Clone)]
pub struct CycleConfig {
    /// Backlog threshold per L1_CONTINUITY §1.2 default 10.
    pub backlog_threshold: u32,
}

impl Default for CycleConfig {
    fn default() -> Self {
        CycleConfig {
            backlog_threshold: 10,
        }
    }
}

/// The metabolic-cycle engine.
///
/// Maintains the cycle counter + backlog state + last committed report.
#[derive(Debug, Clone)]
pub struct CycleEngine {
    cycle_number: u64,
    backlog_count: u32,
    config: CycleConfig,
}

impl CycleEngine {
    /// Construct a new engine starting at cycle 0.
    pub fn new(config: CycleConfig) -> Self {
        CycleEngine {
            cycle_number: 0,
            backlog_count: 0,
            config,
        }
    }

    /// Current metabolic cycle number.
    pub fn current_cycle(&self) -> u64 {
        self.cycle_number
    }

    /// Current backlog count (cycles that ran past their budget).
    pub fn backlog_count(&self) -> u32 {
        self.backlog_count
    }

    /// Whether the substrate is currently in a backlog state per L1_CONTINUITY §1.2.
    pub fn is_backlogged(&self) -> bool {
        self.backlog_count >= self.config.backlog_threshold
    }

    /// Run one metabolic cycle through the 5 steps.
    ///
    /// On success: cycle counter increments; returns a [`CycleReport`].
    /// On failure: cycle counter does NOT increment (rollback); the previous
    /// DAG-tip remains the substrate's authoritative state. Returns a
    /// [`CycleError::StepFailed`] identifying which step failed.
    ///
    /// The atomicity guarantee (L1_CONTINUITY §1.1) requires that the
    /// caller's [`DeltaAbsorber`] implements its own WAL + rollback for
    /// step 3 (see [`crate::wal`]). M3 engine does not directly own the
    /// WAL; it orchestrates the steps.
    pub fn run_cycle(&mut self, ctx: &mut CycleContext) -> Result<CycleReport, CycleError> {
        // Step 1: tier-1 invariants.
        if let Err(reason) = ctx.tier1.validate_tier1() {
            return Err(CycleError::StepFailed {
                step: CycleStep::Tier1Invariants,
                reason,
            });
        }

        // Step 2: gradient advance.
        if let Err(reason) = ctx.gradient.advance_gradient() {
            return Err(CycleError::StepFailed {
                step: CycleStep::GradientAdvance,
                reason,
            });
        }

        // Step 3: delta absorption.
        let deltas_absorbed = match ctx.absorber.absorb_deltas() {
            Ok(n) => n,
            Err(reason) => {
                return Err(CycleError::StepFailed {
                    step: CycleStep::DeltaAbsorption,
                    reason,
                })
            }
        };

        // Step 4: skin breach check.
        let skin_breaches = match ctx.breach.check_skin_breaches() {
            Ok(b) => b,
            Err(reason) => {
                return Err(CycleError::StepFailed {
                    step: CycleStep::SkinBreachCheck,
                    reason,
                })
            }
        };

        // Step 5: handshake / attestation processing.
        let handshake_events_processed = match ctx.handshake.process_handshake_attestation() {
            Ok(n) => n,
            Err(reason) => {
                return Err(CycleError::StepFailed {
                    step: CycleStep::HandshakeAttestation,
                    reason,
                })
            }
        };

        // All 5 steps succeeded; commit cycle.
        self.cycle_number += 1;
        Ok(CycleReport {
            cycle_number: self.cycle_number,
            deltas_absorbed,
            handshake_events_processed,
            skin_breaches,
            committed: true,
        })
    }

    /// Mark the substrate as having missed a cycle budget (caller-detected
    /// via wall-clock timer; not modeled in the M3 engine).
    pub fn record_backlog(&mut self) {
        self.backlog_count += 1;
    }

    /// Reset backlog count (e.g., after catch-up or recovery).
    pub fn reset_backlog(&mut self) {
        self.backlog_count = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Split-environment pattern: 5 separate small mock structs the engine
    /// treats as independent borrows. (A single combined MockEnv won't work
    /// because Rust's borrow checker rejects splitting one `&mut` across
    /// the 5 trait references CycleContext needs.)
    struct SplitEnv {
        tier1: TierMock,
        gradient: GradientMock,
        absorber: AbsorberMock,
        breach: BreachMock,
        handshake: HandshakeMock,
    }

    struct TierMock {
        fail: bool,
        calls: usize,
    }
    impl Tier1Validator for TierMock {
        fn validate_tier1(&mut self) -> Result<(), String> {
            self.calls += 1;
            if self.fail {
                Err("tier1".to_string())
            } else {
                Ok(())
            }
        }
    }

    struct GradientMock {
        fail: bool,
        calls: usize,
    }
    impl GradientAdvancer for GradientMock {
        fn advance_gradient(&mut self) -> Result<(), String> {
            self.calls += 1;
            if self.fail {
                Err("gradient".to_string())
            } else {
                Ok(())
            }
        }
    }

    struct AbsorberMock {
        fail: bool,
        deltas: usize,
        calls: usize,
    }
    impl DeltaAbsorber for AbsorberMock {
        fn absorb_deltas(&mut self) -> Result<usize, String> {
            self.calls += 1;
            if self.fail {
                Err("absorb".to_string())
            } else {
                Ok(self.deltas)
            }
        }
    }

    struct BreachMock {
        fail: bool,
        breaches: Vec<String>,
        calls: usize,
    }
    impl SkinBreachChecker for BreachMock {
        fn check_skin_breaches(&mut self) -> Result<Vec<String>, String> {
            self.calls += 1;
            if self.fail {
                Err("breach".to_string())
            } else {
                Ok(self.breaches.clone())
            }
        }
    }

    struct HandshakeMock {
        fail: bool,
        events: usize,
        calls: usize,
    }
    impl HandshakeProcessor for HandshakeMock {
        fn process_handshake_attestation(&mut self) -> Result<usize, String> {
            self.calls += 1;
            if self.fail {
                Err("handshake".to_string())
            } else {
                Ok(self.events)
            }
        }
    }

    fn empty_env() -> SplitEnv {
        SplitEnv {
            tier1: TierMock {
                fail: false,
                calls: 0,
            },
            gradient: GradientMock {
                fail: false,
                calls: 0,
            },
            absorber: AbsorberMock {
                fail: false,
                deltas: 0,
                calls: 0,
            },
            breach: BreachMock {
                fail: false,
                breaches: Vec::new(),
                calls: 0,
            },
            handshake: HandshakeMock {
                fail: false,
                events: 0,
                calls: 0,
            },
        }
    }

    fn run_one(engine: &mut CycleEngine, env: &mut SplitEnv) -> Result<CycleReport, CycleError> {
        let mut ctx = CycleContext {
            tier1: &mut env.tier1,
            gradient: &mut env.gradient,
            absorber: &mut env.absorber,
            breach: &mut env.breach,
            handshake: &mut env.handshake,
        };
        engine.run_cycle(&mut ctx)
    }

    #[test]
    fn test_happy_path_one_cycle() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        let mut env = empty_env();
        env.absorber.deltas = 3;
        env.handshake.events = 1;

        let report = run_one(&mut engine, &mut env).unwrap();

        assert_eq!(report.cycle_number, 1);
        assert_eq!(report.deltas_absorbed, 3);
        assert_eq!(report.handshake_events_processed, 1);
        assert!(report.committed);
        assert_eq!(engine.current_cycle(), 1);
    }

    #[test]
    fn test_multiple_cycles_increment_counter() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        for i in 1..=5 {
            let mut env = empty_env();
            let report = run_one(&mut engine, &mut env).unwrap();
            assert_eq!(report.cycle_number, i);
        }
        assert_eq!(engine.current_cycle(), 5);
    }

    #[test]
    fn test_tier1_failure_aborts_cycle() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        let mut env = empty_env();
        env.tier1.fail = true;

        let result = run_one(&mut engine, &mut env);
        assert!(matches!(
            result,
            Err(CycleError::StepFailed {
                step: CycleStep::Tier1Invariants,
                ..
            })
        ));
        // Cycle counter does NOT increment on abort.
        assert_eq!(engine.current_cycle(), 0);
        // Subsequent steps NOT called.
        assert_eq!(env.gradient.calls, 0);
        assert_eq!(env.absorber.calls, 0);
        assert_eq!(env.breach.calls, 0);
        assert_eq!(env.handshake.calls, 0);
    }

    #[test]
    fn test_gradient_failure_aborts_after_tier1() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        let mut env = empty_env();
        env.gradient.fail = true;

        let result = run_one(&mut engine, &mut env);
        assert!(matches!(
            result,
            Err(CycleError::StepFailed {
                step: CycleStep::GradientAdvance,
                ..
            })
        ));
        assert_eq!(env.tier1.calls, 1);
        assert_eq!(env.gradient.calls, 1);
        // Step 3+ NOT called.
        assert_eq!(env.absorber.calls, 0);
    }

    #[test]
    fn test_absorber_failure_aborts_step3() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        let mut env = empty_env();
        env.absorber.fail = true;

        let result = run_one(&mut engine, &mut env);
        assert!(matches!(
            result,
            Err(CycleError::StepFailed {
                step: CycleStep::DeltaAbsorption,
                ..
            })
        ));
        assert_eq!(env.absorber.calls, 1);
        assert_eq!(env.breach.calls, 0);
    }

    #[test]
    fn test_breach_failure_aborts_step4() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        let mut env = empty_env();
        env.breach.fail = true;

        let result = run_one(&mut engine, &mut env);
        assert!(matches!(
            result,
            Err(CycleError::StepFailed {
                step: CycleStep::SkinBreachCheck,
                ..
            })
        ));
        assert_eq!(env.handshake.calls, 0);
    }

    #[test]
    fn test_handshake_failure_aborts_step5() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        let mut env = empty_env();
        env.handshake.fail = true;

        let result = run_one(&mut engine, &mut env);
        assert!(matches!(
            result,
            Err(CycleError::StepFailed {
                step: CycleStep::HandshakeAttestation,
                ..
            })
        ));
        // Step 5 was called and failed; counter does NOT increment.
        assert_eq!(env.handshake.calls, 1);
        assert_eq!(engine.current_cycle(), 0);
    }

    #[test]
    fn test_breaches_emitted_in_report() {
        let mut engine = CycleEngine::new(CycleConfig::default());
        let mut env = empty_env();
        env.breach.breaches = vec![
            "envelope_malformed".to_string(),
            "concurrent_connect_attempt".to_string(),
        ];

        let report = run_one(&mut engine, &mut env).unwrap();
        assert_eq!(report.skin_breaches.len(), 2);
        assert!(report
            .skin_breaches
            .contains(&"envelope_malformed".to_string()));
    }

    #[test]
    fn test_backlog_count() {
        let mut engine = CycleEngine::new(CycleConfig {
            backlog_threshold: 10,
        });
        assert!(!engine.is_backlogged());
        for _ in 0..10 {
            engine.record_backlog();
        }
        assert!(engine.is_backlogged());
        engine.reset_backlog();
        assert!(!engine.is_backlogged());
    }

    #[test]
    fn test_cycle_step_display() {
        assert_eq!(CycleStep::Tier1Invariants.to_string(), "tier1_invariants");
        assert_eq!(CycleStep::DeltaAbsorption.to_string(), "delta_absorption");
    }

    #[test]
    fn test_rollback_does_not_advance_cycle_counter() {
        let mut engine = CycleEngine::new(CycleConfig::default());

        // First cycle succeeds.
        let mut env = empty_env();
        run_one(&mut engine, &mut env).unwrap();
        assert_eq!(engine.current_cycle(), 1);

        // Second cycle fails at step 3.
        let mut env = empty_env();
        env.absorber.fail = true;
        let _ = run_one(&mut engine, &mut env);
        assert_eq!(engine.current_cycle(), 1); // unchanged
    }
}
