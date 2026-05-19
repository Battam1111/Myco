//! **v3.1.1 Sprint 6.C (T1.7)** — wall-clock time-skew defense.
//!
//! ## Problem
//!
//! Substrate uses `SystemTime::now()` in 30+ places: immune-emission rate
//! limits (Sprint 5.F), nonce expiry, federation peer pinning timestamps,
//! observatory snapshots, backup metadata. If the system clock jumps
//! BACKWARD (NTP correction, manual change, VM clock-drift, DST in
//! environments that mistakenly use local time), several failures cascade:
//!
//! - Sprint 5.F rate limit: `now - prior_emit` underflows or becomes a
//!   spuriously small Duration → rate limit defeated → DoS surface
//!   reopens.
//! - Nonce expiry: nonces that should have expired now appear fresh again
//!   → replay attack window opens.
//! - Observability: cost-signal time series shows impossible "negative
//!   cycle duration" entries.
//!
//! ## Solution
//!
//! A process-global monotonic-guard counter: every `monotonic_unix_ns()`
//! call atomically reads `SystemTime::now()`, compares to the highest
//! previously-observed value, and returns `max(now, last_seen + 1)`.
//! Subsequent calls are guaranteed strictly increasing even if the system
//! clock goes back to the 1970s.
//!
//! On detected skew (now < last_seen by ≥ 1ms), the helper sets a sticky
//! flag and increments a counter. The substrate's existing immune
//! pipeline polls this flag via [`take_skew_observation`] and emits
//! `C63_wall_clock_skew_detected` per detection burst.
//!
//! ## Scope
//!
//! Sprint 6.C wires this into `emit_immune_sporocarp` (the most
//! exploitable rate-limit path). Other call sites (federation peer
//! timestamps, backup metadata) continue to use raw `SystemTime::now()`
//! for now — they are observability-only and time-skew there causes
//! confusion but not security failures. Migrating all 30 sites is
//! tracked as Sprint 6.C.2 follow-up.
//!
//! ## Doctrine traceability
//!
//! - L1/HARD_RULES anticipated C63 wall_clock_skew_detected
//! - L1/SCHEMA dual-clock check (substrate-cycle counter + wall-clock):
//!   the substrate-cycle counter is already monotonic-by-construction;
//!   this module makes the wall-clock half of the dual-clock check
//!   equally monotonic at substrate-internal observation points.

use std::sync::atomic::{AtomicI64, AtomicU64, Ordering};

/// Highest unix_ns value observed via [`monotonic_unix_ns`] so far.
/// Initialized to 0 (epoch); on a healthy system the first call lifts it
/// to ~1.7e18 (2026 wall-clock in ns).
static LAST_OBSERVED_UNIX_NS: AtomicI64 = AtomicI64::new(0);

/// Sticky count of detected backward-clock jumps since substrate start
/// (or since last [`take_skew_observation`] reset, whichever is later).
static SKEW_DETECTION_COUNT: AtomicU64 = AtomicU64::new(0);

/// Largest magnitude of skew observed since last reset, in nanoseconds.
/// 0 = no skew observed. Updated atomically on each detection.
static LARGEST_BACKWARD_JUMP_NS: AtomicI64 = AtomicI64::new(0);

/// **Skew threshold**: a `now < last_seen` delta of less than this many
/// nanoseconds is treated as natural jitter (process scheduling, clock
/// granularity) and NOT flagged. Larger deltas count as a real skew.
/// 1 ms is well above typical jitter and well below any malicious
/// adjustment worth investigating.
pub const SKEW_THRESHOLD_NS: i64 = 1_000_000;

/// Return a monotonically-non-decreasing unix_ns timestamp.
///
/// Algorithm: read `SystemTime::now()`, atomically CAS-update
/// [`LAST_OBSERVED_UNIX_NS`] to `max(observed, last+1)`. Returns the
/// stored value. If the wall clock jumped backward by more than
/// [`SKEW_THRESHOLD_NS`], increment the skew counter so the substrate's
/// immune pipeline can emit C63.
///
/// **Race-free property**: even under concurrent calls, the returned
/// value is strictly greater than any value returned by a prior call.
/// Two concurrent callers may observe the same `now` from `SystemTime`,
/// but the CAS loop guarantees they get distinct outputs.
///
/// **Side effect**: on backward-skew detection, side-effect counters are
/// updated. The substrate's normal flow polls
/// [`take_skew_observation`] periodically to emit C63.
pub fn monotonic_unix_ns() -> i64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let observed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);

    loop {
        let last = LAST_OBSERVED_UNIX_NS.load(Ordering::Relaxed);
        // Backward-skew check: observed strictly less than (last - threshold)
        // is a real skew worth recording. Equal or near-equal values are
        // expected jitter.
        if last > 0 && observed < last.saturating_sub(SKEW_THRESHOLD_NS) {
            let jump = last.saturating_sub(observed);
            SKEW_DETECTION_COUNT.fetch_add(1, Ordering::Relaxed);
            // Atomically update largest_backward_jump if this exceeds it.
            let mut prior_max = LARGEST_BACKWARD_JUMP_NS.load(Ordering::Relaxed);
            while jump > prior_max {
                match LARGEST_BACKWARD_JUMP_NS.compare_exchange_weak(
                    prior_max,
                    jump,
                    Ordering::Relaxed,
                    Ordering::Relaxed,
                ) {
                    Ok(_) => break,
                    Err(actual) => prior_max = actual,
                }
            }
        }
        // Compute monotonic output.
        let new = if observed > last {
            observed
        } else {
            last.saturating_add(1)
        };
        match LAST_OBSERVED_UNIX_NS.compare_exchange_weak(
            last,
            new,
            Ordering::Relaxed,
            Ordering::Relaxed,
        ) {
            Ok(_) => return new,
            Err(_) => continue, // retry with refreshed `last`
        }
    }
}

/// Skew-observation snapshot returned by [`take_skew_observation`].
#[derive(Debug, Clone, Copy)]
pub struct SkewObservation {
    /// Number of backward-skew detections since the last call to this
    /// function (or since substrate start, whichever is later).
    pub detection_count_since_last_take: u64,
    /// Largest single backward jump observed (in nanoseconds) over the
    /// same window. 0 if no skew observed.
    pub largest_backward_jump_ns: i64,
}

/// Atomically read AND RESET the skew observation counters. The caller
/// (typically the substrate's autonomous tick or boot-time scan) then
/// emits one `C63_wall_clock_skew_detected` immune sporocarp per
/// non-zero observation window.
///
/// Reset semantics: if this is called once per second from the tick
/// loop, every C63 emission covers exactly the prior 1-second window's
/// skew events. Bursts of small skews collapse to a single C63 per
/// window (good for rate limiting).
pub fn take_skew_observation() -> SkewObservation {
    let count = SKEW_DETECTION_COUNT.swap(0, Ordering::Relaxed);
    let jump = LARGEST_BACKWARD_JUMP_NS.swap(0, Ordering::Relaxed);
    SkewObservation {
        detection_count_since_last_take: count,
        largest_backward_jump_ns: jump,
    }
}

/// **Test-only helper** — reset the global monotonic state. Use ONLY
/// in tests to isolate runs from each other. In production this is a
/// no-op-equivalent (callers never need to reset).
#[doc(hidden)]
pub fn _test_reset_state() {
    LAST_OBSERVED_UNIX_NS.store(0, Ordering::Relaxed);
    SKEW_DETECTION_COUNT.store(0, Ordering::Relaxed);
    LARGEST_BACKWARD_JUMP_NS.store(0, Ordering::Relaxed);
}

/// **Test-only helper** — directly inject a value into LAST_OBSERVED_UNIX_NS
/// to simulate "the clock has previously been observed at time T". Use
/// to test the backward-skew detection path.
#[doc(hidden)]
pub fn _test_set_last_observed(value: i64) {
    LAST_OBSERVED_UNIX_NS.store(value, Ordering::Relaxed);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    /// Test serialization mutex. The wall-clock state is process-global,
    /// so concurrent tests would race. Hold this for the duration of each
    /// test body.
    static TEST_LOCK: Mutex<()> = Mutex::new(());

    #[test]
    fn monotonic_returns_strictly_increasing_values() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        let a = monotonic_unix_ns();
        let b = monotonic_unix_ns();
        let c = monotonic_unix_ns();
        assert!(b > a, "second call must be > first: {a} vs {b}");
        assert!(c > b, "third call must be > second: {b} vs {c}");
    }

    #[test]
    fn backward_skew_is_detected_and_compensated() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        // Seed LAST with a far-future value.
        let future_ns: i64 = 2_000_000_000_000_000_000; // ~year 2033
        _test_set_last_observed(future_ns);
        // Next call's observed (~year 2026) is far below seeded last → skew detected.
        let returned = monotonic_unix_ns();
        assert!(
            returned >= future_ns,
            "monotonic guard must return >= prior last; got {returned} < {future_ns}"
        );
        // Take observation.
        let obs = take_skew_observation();
        assert_eq!(obs.detection_count_since_last_take, 1);
        assert!(
            obs.largest_backward_jump_ns > 0,
            "skew jump should be positive; got {}",
            obs.largest_backward_jump_ns
        );
    }

    #[test]
    fn small_jitter_is_not_flagged_as_skew() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        let now = monotonic_unix_ns();
        // Manually pull LAST back by 100us — less than the 1ms threshold.
        _test_set_last_observed(now.saturating_add(SKEW_THRESHOLD_NS / 10));
        // Next call's observed is slightly below — well within threshold.
        let _ = monotonic_unix_ns();
        let obs = take_skew_observation();
        assert_eq!(
            obs.detection_count_since_last_take, 0,
            "sub-threshold jitter must NOT count as skew"
        );
    }

    #[test]
    fn take_observation_resets_counters() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        _test_reset_state();
        _test_set_last_observed(2_000_000_000_000_000_000);
        let _ = monotonic_unix_ns();
        let first = take_skew_observation();
        assert_eq!(first.detection_count_since_last_take, 1);
        // Second take should report 0.
        let second = take_skew_observation();
        assert_eq!(
            second.detection_count_since_last_take, 0,
            "take must atomically reset"
        );
    }
}
