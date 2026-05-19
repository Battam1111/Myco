//! **v3.1.1 Sprint 6.J (T2.8)** — Python worker call-duration observability.
//!
//! ## Problem
//!
//! Sprint 5.E detects Python worker PROCESS DEATH via `is_child_alive()` in
//! the autonomous tick. But a Python worker can be **alive but blocked**
//! (deadlock, infinite loop, GIL contention, blocking I/O) — alive enough
//! that try_wait returns "still running", broken enough that no calls
//! complete. The substrate's outbound `client.call()` then hangs forever.
//!
//! ## Solution (this sprint: observability)
//!
//! Every substrate-→-Python call records its wall-clock duration. Calls
//! that exceed a threshold (env-tunable, default 30 seconds) increment
//! a slow-call counter. The autonomous tick polls the counter and emits
//! `C65_python_worker_slow_call` immune sporocarp for each detected
//! slow-call burst (one-shot per burst per Sprint 5.F rate-limit).
//!
//! ## Scope limit (Sprint 6.J.2 follow-up, ~3-4h)
//!
//! Sprint 6.J ships **after-the-fact observability** — a call must
//! return for its duration to be recorded. A genuine deadlock (call
//! never returns) is still terminal for the substrate. The true
//! deadlock-recovery solution requires either:
//!   (a) BridgeClient refactor with reader-thread + recv_timeout
//!       (replaces blocking BufReader<ChildStdout> with channel-based
//!       reads), OR
//!   (b) Watchdog thread that issues `child.kill()` after N seconds of
//!       no progress on the substrate's main loop.
//! Both are deferred to Sprint 6.J.2 because the architectural surface
//! change deserves a dedicated sprint. The current observability is
//! valuable on its own: ops monitoring sees "Python getting slow"
//! events BEFORE the eventual hang, providing time to intervene.
//!
//! ## Doctrine traceability
//!
//! - L1/HARD_RULES anticipated C65 python_worker_slow_call
//! - P11 §3.4 silent absorption: a Python call that never returns is
//!   silent cost; Sprint 6.J surfaces near-misses as observability.

use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;

/// Default slow-call threshold (30 seconds). Override via
/// `MYCO_PYTHON_SLOW_CALL_THRESHOLD_MS` env var.
pub const DEFAULT_SLOW_CALL_THRESHOLD_MS: u64 = 30_000;

/// Read the configured slow-call threshold from env var, falling back to
/// the default. Called once per call site (cheap — env read is one syscall).
pub fn slow_call_threshold() -> Duration {
    let ms = std::env::var("MYCO_PYTHON_SLOW_CALL_THRESHOLD_MS")
        .ok()
        .and_then(|s| s.parse::<u64>().ok())
        .unwrap_or(DEFAULT_SLOW_CALL_THRESHOLD_MS);
    Duration::from_millis(ms)
}

/// Count of calls that exceeded the threshold since substrate start.
static LIFETIME_SLOW_CALL_COUNT: AtomicU64 = AtomicU64::new(0);

/// Largest single-call duration observed (in ms) since substrate start.
static LARGEST_CALL_DURATION_MS: AtomicU64 = AtomicU64::new(0);

/// One-shot flag: returned `should_emit_c65=true` exactly once per
/// "slow-call burst" (transition from no-recent-slow to recent-slow).
static EMISSION_PENDING: AtomicU64 = AtomicU64::new(0);

/// Record a Python call's observed duration. Call this AFTER each
/// substrate-→-Python call returns (regardless of success/failure).
/// Sets the emission flag if duration exceeds the configured threshold.
pub fn record_call_duration(duration: Duration) {
    let ms = u64::try_from(duration.as_millis()).unwrap_or(u64::MAX);
    // Update largest-observed.
    let mut prior = LARGEST_CALL_DURATION_MS.load(Ordering::Relaxed);
    while ms > prior {
        match LARGEST_CALL_DURATION_MS.compare_exchange_weak(
            prior,
            ms,
            Ordering::Relaxed,
            Ordering::Relaxed,
        ) {
            Ok(_) => break,
            Err(actual) => prior = actual,
        }
    }
    // Check threshold + arm emission.
    let threshold_ms = u64::try_from(slow_call_threshold().as_millis()).unwrap_or(u64::MAX);
    if ms > threshold_ms {
        LIFETIME_SLOW_CALL_COUNT.fetch_add(1, Ordering::Relaxed);
        EMISSION_PENDING.store(1, Ordering::Relaxed);
    }
}

/// Observation snapshot for the autonomous tick.
#[derive(Debug, Clone, Copy)]
pub struct PythonCallHealthObservation {
    /// Total slow-call events since substrate start.
    pub lifetime_slow_call_count: u64,
    /// Largest single-call duration observed (milliseconds).
    pub largest_call_duration_ms: u64,
    /// Whether C65 should be emitted (one-shot per burst).
    pub should_emit_c65: bool,
}

/// Take one observation. If `should_emit_c65` is true, the caller
/// (autonomous tick) emits C65_python_worker_slow_call.
pub fn take_python_call_health_observation() -> PythonCallHealthObservation {
    let should_emit = EMISSION_PENDING
        .compare_exchange(1, 0, Ordering::Relaxed, Ordering::Relaxed)
        .is_ok();
    PythonCallHealthObservation {
        lifetime_slow_call_count: LIFETIME_SLOW_CALL_COUNT.load(Ordering::Relaxed),
        largest_call_duration_ms: LARGEST_CALL_DURATION_MS.load(Ordering::Relaxed),
        should_emit_c65: should_emit,
    }
}

/// **Test-only**: reset all counters.
#[doc(hidden)]
pub fn _test_reset_state() {
    LIFETIME_SLOW_CALL_COUNT.store(0, Ordering::Relaxed);
    LARGEST_CALL_DURATION_MS.store(0, Ordering::Relaxed);
    EMISSION_PENDING.store(0, Ordering::Relaxed);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    static TEST_LOCK: Mutex<()> = Mutex::new(());

    #[test]
    fn fast_call_does_not_trigger_c65() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        record_call_duration(Duration::from_millis(100));
        let obs = take_python_call_health_observation();
        assert!(
            !obs.should_emit_c65,
            "100ms call must not trigger C65 (threshold 30000ms by default)"
        );
        assert_eq!(obs.lifetime_slow_call_count, 0);
    }

    #[test]
    fn slow_call_triggers_c65_once_per_burst() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        // 60s = 2x default threshold
        record_call_duration(Duration::from_secs(60));
        let obs1 = take_python_call_health_observation();
        assert!(obs1.should_emit_c65, "60s call must trigger C65");
        assert_eq!(obs1.lifetime_slow_call_count, 1);
        // Second observation without new slow call: no re-trigger.
        let obs2 = take_python_call_health_observation();
        assert!(!obs2.should_emit_c65);
    }

    #[test]
    fn threshold_override_via_env_var() {
        // Use a per-test env var that doesn't leak (set + unset).
        std::env::set_var("MYCO_PYTHON_SLOW_CALL_THRESHOLD_MS", "100");
        let threshold = slow_call_threshold();
        assert_eq!(threshold.as_millis(), 100);
        std::env::remove_var("MYCO_PYTHON_SLOW_CALL_THRESHOLD_MS");
    }

    #[test]
    fn largest_duration_tracks_maximum() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        record_call_duration(Duration::from_millis(500));
        record_call_duration(Duration::from_millis(1500));
        record_call_duration(Duration::from_millis(800));
        let obs = take_python_call_health_observation();
        assert_eq!(obs.largest_call_duration_ms, 1500);
    }
}
