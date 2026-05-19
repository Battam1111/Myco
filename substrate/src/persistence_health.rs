//! **v3.1.1 Sprint 6.G (T2.12)** — persistence-health observability +
//! graceful degradation hooks.
//!
//! ## Problem
//!
//! Before Sprint 6.G, every `save_dag_state` / `save_manifest` failure
//! propagated as `SubstrateError::Protocol`/`SubstrateError::Io` directly
//! to the operator. The operator saw cryptic per-call errors with no
//! summary view. Worse: if the state_dir became read-only mid-session
//! (filesystem remounted, disk full, permission revoked), every
//! subsequent request hit the same wall — the substrate offered no
//! coherent "persistence unavailable" signal.
//!
//! ## Solution
//!
//! A process-global persistence-failure counter, analogous to
//! `wall_clock::SKEW_DETECTION_COUNT`. Every `save_dag_state` call
//! that fails increments the counter; every success resets it. The
//! autonomous tick polls [`take_persistence_failure_observation`] and
//! emits a single `C64_persistence_unavailable` immune sporocarp per
//! sustained failure burst (best-effort: if the DAG emit also fails,
//! the failure surfaces via stderr).
//!
//! ## Doctrine traceability
//!
//! - L1/HARD_RULES anticipated C64 persistence_unavailable
//! - L1/SCHEMA §1.1: state_dir is the substrate's persistent ground;
//!   inability to persist is a tier-1 health concern even if the
//!   in-memory state remains intact.
//!
//! ## Scope limits (Sprint 6.G.2 follow-up, ~3-4h)
//!
//! - The autonomous-tick C64 emission path is BEST-EFFORT: if DAG
//!   emit also fails (likely, since same disk), only stderr surfaces it.
//!   A robust path needs an alternative "stderr-only diagnostic
//!   channel" or a memory-only ring buffer the operator can query.
//! - True read-only mode (substrate continues answering read-only
//!   queries while rejecting mutations) requires a per-request gate
//!   that consults this counter — implementable as a follow-up once
//!   the observability surface is stable.

use std::sync::atomic::{AtomicU64, Ordering};

/// Count of consecutive `save_dag_state` failures since last success.
/// Reset to 0 on each successful save.
static CONSECUTIVE_FAILURES: AtomicU64 = AtomicU64::new(0);

/// Cumulative count of failure events since substrate start (not reset
/// on success; provides "total failures over substrate lifetime"
/// observability).
static LIFETIME_FAILURE_COUNT: AtomicU64 = AtomicU64::new(0);

/// Threshold at which the substrate emits C64. 1 = on first failure;
/// higher values suppress single-shot blips. Set to 1 — persistence
/// failures are rare and serious; surface immediately.
pub const C64_EMISSION_THRESHOLD: u64 = 1;

/// Record a save-success. Resets the consecutive-failure counter.
pub fn record_save_success() {
    CONSECUTIVE_FAILURES.store(0, Ordering::Relaxed);
}

/// Record a save-failure. Increments both counters.
pub fn record_save_failure() {
    CONSECUTIVE_FAILURES.fetch_add(1, Ordering::Relaxed);
    LIFETIME_FAILURE_COUNT.fetch_add(1, Ordering::Relaxed);
}

/// Observation snapshot for the autonomous tick.
#[derive(Debug, Clone, Copy)]
pub struct PersistenceHealthObservation {
    /// Number of consecutive failures since the last successful save.
    pub consecutive_failures: u64,
    /// Cumulative failure count over substrate lifetime.
    pub lifetime_failures: u64,
    /// Whether a C64 emission threshold has been reached and the caller
    /// SHOULD attempt to emit one. The flag is RESET by this call (sticky
    /// only until first observation); subsequent observations within the
    /// same failure burst return false to prevent C64 spam.
    pub should_emit_c64: bool,
}

/// Static one-shot flag: `should_emit_c64` returns true exactly once per
/// failure burst (transition from <threshold to >=threshold). Resets on
/// `record_save_success`.
static EMISSION_PENDING: AtomicU64 = AtomicU64::new(0);

/// Take one observation. The caller (autonomous tick) emits C64 if
/// `should_emit_c64` is true.
pub fn take_persistence_health_observation() -> PersistenceHealthObservation {
    let consecutive = CONSECUTIVE_FAILURES.load(Ordering::Relaxed);
    let lifetime = LIFETIME_FAILURE_COUNT.load(Ordering::Relaxed);
    let should_emit = consecutive >= C64_EMISSION_THRESHOLD
        && EMISSION_PENDING
            .compare_exchange(0, 1, Ordering::Relaxed, Ordering::Relaxed)
            .is_ok();
    PersistenceHealthObservation {
        consecutive_failures: consecutive,
        lifetime_failures: lifetime,
        should_emit_c64: should_emit,
    }
}

/// Wrapper around `record_save_success` that ALSO clears the C64
/// emission-pending flag so the next failure burst can re-trigger.
pub fn record_save_success_and_clear_emission() {
    record_save_success();
    EMISSION_PENDING.store(0, Ordering::Relaxed);
}

/// **Test-only**: reset all counters.
#[doc(hidden)]
pub fn _test_reset_state() {
    CONSECUTIVE_FAILURES.store(0, Ordering::Relaxed);
    LIFETIME_FAILURE_COUNT.store(0, Ordering::Relaxed);
    EMISSION_PENDING.store(0, Ordering::Relaxed);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    static TEST_LOCK: Mutex<()> = Mutex::new(());

    #[test]
    fn fresh_state_has_zero_counters() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        let obs = take_persistence_health_observation();
        assert_eq!(obs.consecutive_failures, 0);
        assert_eq!(obs.lifetime_failures, 0);
        assert!(!obs.should_emit_c64);
    }

    #[test]
    fn first_failure_triggers_c64_once() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        record_save_failure();
        let obs1 = take_persistence_health_observation();
        assert_eq!(obs1.consecutive_failures, 1);
        assert!(obs1.should_emit_c64, "first observation should trigger C64");
        // Second observation while still in failure: should NOT trigger again.
        let obs2 = take_persistence_health_observation();
        assert!(
            !obs2.should_emit_c64,
            "C64 emission must be one-shot per failure burst"
        );
    }

    #[test]
    fn success_resets_consecutive_but_keeps_lifetime() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        record_save_failure();
        record_save_failure();
        record_save_failure();
        let pre = take_persistence_health_observation();
        assert_eq!(pre.consecutive_failures, 3);
        assert_eq!(pre.lifetime_failures, 3);
        record_save_success_and_clear_emission();
        let post = take_persistence_health_observation();
        assert_eq!(
            post.consecutive_failures, 0,
            "success must reset consecutive counter"
        );
        assert_eq!(
            post.lifetime_failures, 3,
            "lifetime counter persists across success"
        );
    }

    #[test]
    fn new_failure_burst_after_recovery_re_triggers_c64() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        // First burst.
        record_save_failure();
        let _ = take_persistence_health_observation();
        // Recovery.
        record_save_success_and_clear_emission();
        // New burst.
        record_save_failure();
        let obs = take_persistence_health_observation();
        assert!(
            obs.should_emit_c64,
            "new burst after recovery should re-trigger C64 once"
        );
    }
}
