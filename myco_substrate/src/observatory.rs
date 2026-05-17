//! M25.x P5 万物互联 + **M26.2 P11 代谢经济** — substrate observatory primitives.
//!
//! Extracted from `server.rs` (Phase B M27 follow-up): owns the
//! `query_substrate_observatory` request handler, the cycle-tick snapshot
//! append hook, the shared DAG scan, the signal-direction classifier, and
//! (M26.2) the per-cycle cost accumulator that drives signals #7/#8/#9.
//!
//! ## M26.2 P11.b cost signals
//!
//! Three new Living Bets signals land in this milestone:
//!
//! - **#7 compute/cycle**: wall-clock nanoseconds in the cycle. Measured
//!   from previous `cycle_advanced` to current `cycle_advanced`.
//! - **#8 network/cycle**: federation egress wire bytes in the cycle.
//!   Sourced from `FederationState::drain_bytes_egressed`.
//! - **#9 storage/cycle**: bytes added to `dag.cb` + `snapshot.cb` on disk
//!   in the cycle. Derived from file-metadata delta — no instrumentation
//!   of save call sites needed.
//!
//! These complete L0 §7 + L2_OBSERVABILITY §2 "10 = 6 base + 3 cost + 1
//! composite". With them in place, `bet_weakening_quorum` can run on
//! full-cost-aware data and the P11.c ordered fallback (M26.3) becomes
//! mechanically possible.

use std::collections::BTreeMap;
use std::path::Path;
use std::time::Instant;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};

use crate::server::{
    emit_immune_sporocarp, emit_substrate_event, float_repr, ServerState,
};
use crate::SubstrateError;

/// **M26.2 P11.b**: per-cycle cost accumulator. One instance lives on
/// `ServerState`; the cycle-advance handler reads + resets it each cycle.
///
/// Three cost dimensions per L0 P11.a:
/// - **Compute** (`signal_7_compute_ns`): wall-clock ns elapsed since cycle
///   start (= previous `cycle_advanced` emission, or substrate boot for
///   cycle 0). Measured via `Instant::elapsed` — substrate-process clock.
/// - **Network** (`signal_8_network_bytes`): drained from
///   `FederationState::bytes_egressed_since_last_drain` at cycle boundary.
///   Counts wire bytes (4-byte length prefix + frame body) for every
///   successful `write_fed_frame` call within the cycle.
/// - **Storage** (`signal_9_storage_bytes`): byte delta of on-disk
///   `dag.cb` + `snapshot.cb` versus the previously-recorded sizes. File-
///   metadata-based — avoids instrumenting every `save_dag_state` call site
///   and HONESTLY reflects what actually grew on disk this cycle (rather
///   than write amplification from intra-cycle file rewrites).
#[derive(Debug)]
pub(crate) struct CostAccumulator {
    /// When the CURRENT cycle began (substrate-process `Instant`). Set at
    /// `ServerState::new` and reset at each `snapshot_and_reset`.
    cycle_started_at: Instant,
    /// Last-observed `dag.cb` file size in bytes (0 if file does not yet
    /// exist). Snapshotted at the END of the previous cycle so the next
    /// cycle's delta is `current_size - last_dag_cb_bytes`.
    last_dag_cb_bytes: u64,
    /// Last-observed `snapshot.cb` file size in bytes (0 if file does not
    /// yet exist).
    last_snapshot_cb_bytes: u64,
}

impl CostAccumulator {
    /// Construct a fresh accumulator. `state_dir` is read to seed the
    /// last-known file sizes (so the FIRST cycle's signal_9 is the delta
    /// from boot-time sizes, not a misleading "all bytes are new").
    pub(crate) fn new(state_dir: &Path) -> Self {
        Self {
            cycle_started_at: Instant::now(),
            last_dag_cb_bytes: file_size_or_zero(
                &state_dir.join(crate::persistence::DAG_FILENAME),
            ),
            last_snapshot_cb_bytes: file_size_or_zero(
                &state_dir.join(crate::persistence::SNAPSHOT_FILENAME),
            ),
        }
    }

    /// Compute the cost signals for the cycle that just ended, then reset
    /// the timer + file-size baseline for the next cycle. Reads federation
    /// egress via `state.federation.drain_bytes_egressed()`.
    ///
    /// **Side effects**: zeroes `state.federation.bytes_egressed_since_last_drain`
    /// (via drain), refreshes `cycle_started_at` to `Instant::now()`, and
    /// refreshes `last_dag_cb_bytes` + `last_snapshot_cb_bytes` from disk.
    pub(crate) fn snapshot_and_reset(
        &mut self,
        federation: &mut crate::federation::FederationState,
        state_dir: &Path,
    ) -> CostSnapshot {
        // #7: compute wall-clock from cycle start to now.
        let elapsed = self.cycle_started_at.elapsed();
        let compute_ns = u64::try_from(elapsed.as_nanos()).unwrap_or(u64::MAX);

        // #8: drain network egress counter from federation.
        let network_bytes = federation.drain_bytes_egressed();

        // #9: storage delta = current file sizes - last recorded.
        let cur_dag = file_size_or_zero(&state_dir.join(crate::persistence::DAG_FILENAME));
        let cur_snap =
            file_size_or_zero(&state_dir.join(crate::persistence::SNAPSHOT_FILENAME));
        // Saturating-sub: if a file shrinks (e.g., snapshot rewritten smaller
        // due to compression), don't underflow — report 0 for that cycle. The
        // semantic is "bytes ADDED"; shrinks are accounted as zero-add (not
        // negative). Future P10 compression milestone may refine this to track
        // shrinks as a separate "bytes_reclaimed" signal.
        let dag_delta = cur_dag.saturating_sub(self.last_dag_cb_bytes);
        let snap_delta = cur_snap.saturating_sub(self.last_snapshot_cb_bytes);
        let storage_bytes = dag_delta.saturating_add(snap_delta);

        // Refresh baselines.
        self.last_dag_cb_bytes = cur_dag;
        self.last_snapshot_cb_bytes = cur_snap;
        self.cycle_started_at = Instant::now();

        CostSnapshot {
            compute_ns,
            network_bytes,
            storage_bytes,
        }
    }
}

/// Read the file size on disk, returning 0 if the file does not exist or is
/// unreadable. Used by `CostAccumulator` for storage delta computation.
fn file_size_or_zero(path: &Path) -> u64 {
    std::fs::metadata(path).map(|m| m.len()).unwrap_or(0)
}

/// **M26.2 P11.b**: one cycle's recorded costs. Produced by
/// `CostAccumulator::snapshot_and_reset` and forwarded into the
/// per-cycle `ObservatorySnapshot`.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(crate) struct CostSnapshot {
    /// Wall-clock nanoseconds elapsed in the cycle (signal #7).
    pub(crate) compute_ns: u64,
    /// Federation egress bytes in the cycle (signal #8).
    pub(crate) network_bytes: u64,
    /// `dag.cb` + `snapshot.cb` byte delta in the cycle (signal #9).
    pub(crate) storage_bytes: u64,
}

/// **M26.2 P11.b** + M25.3: variance-derived weights for composite #10.
///
/// Each `w_i` is `Var(signal_i over rolling window) / sum(Var over all
/// signals)`. M25.3 introduced the variance scheme over {1, 2, 4b}; M26.2
/// expanded the basis to {1, 2, 4b, 7, 8, 9} per L2_OBSERVABILITY §2.
///
/// `sum(w_i) = 1.0` (modulo floating-point error). When history is too
/// short or every signal is flat, falls back to equal weights (1/6 each).
#[derive(Debug, Clone, Copy)]
struct EmergentWeights {
    w1: f64,
    w2: f64,
    w4b: f64,
    w7: f64,
    w8: f64,
    w9: f64,
}

/// M25.2 P5 万物互联: aggregated counts produced by one full O(N) DAG scan
/// for the observatory. Used both by `handle_query_substrate_observatory`
/// (for the live response) and by the per-cycle snapshot hook
/// `append_observatory_snapshot_to_state` (for the trend window).
///
/// This avoids walking the DAG twice when the observatory is queried right
/// after a cycle advance, AND keeps signal definitions in one place — the
/// time-trend signal in the query handler MUST agree with what gets logged
/// to the history.
pub(crate) struct ObservatoryCounts {
    /// `state.dag.node_count()`. Cheap, but included so callers don't need a
    /// second DAG borrow.
    pub(crate) dag_node_count: u64,
    /// Sum of `parent_hashes.len()` over all DAG nodes.
    pub(crate) dag_edge_count: u64,
    /// Sum of `content_canonical_bytes.len()` over all DAG nodes.
    pub(crate) dag_total_content_bytes: u64,
    /// Cumulative count of `axis_registered:*` + `evolution_succeeded:*` +
    /// `evolution_failed:*` events.
    pub(crate) evolution_event_count: u64,
    /// Cumulative count of `axis_registered:*` events (subset of the above).
    pub(crate) axis_register_count: u64,
    /// Distinct axis names that ever appeared in `axis_perturbed:*` events.
    pub(crate) distinct_perturbed_axes_count: u64,
    /// Cumulative count of `federation_received:*` events.
    pub(crate) federation_received_count: u64,
    /// Currently-Established federation peers (live state, not DAG-derived).
    pub(crate) established_peers: u64,
    /// Count of CI-class events (axis_registered + owner_key_* + evolution_*)
    /// that landed in the most-recent burst window (wall-clock per L0 §7.4 +
    /// §13.1; M26.1 C3 fix). Used by M25.1 doctrine-burst detection.
    pub(crate) ci_events_in_burst_window: u64,
}

/// M25.2: scan the DAG once + read live federation state to populate an
/// `ObservatoryCounts` snapshot.
///
/// M26.1 C3 fix: `burst_window_unix_ns` is now a wall-clock window in
/// nanoseconds (was previously a substrate-cycle count). Doctrine intent
/// (L0 §7.4 + §13.1) is wall-clock 90 days; substrate-cycle counters drift
/// 4-6 orders of magnitude under typical cycle cadence (~1 cycle/sec) so
/// the prior cycle-based window was structurally wrong.
///
/// INTERIM: substrate-process wall-clock used here. M-anchor-3 promotes
/// to anchor-stamped wall-clock per L0 §13.1 (anchor surface authoritative
/// for time-bound defenses).
///
/// Mapping cycle → wall-clock uses `state.observatory_history` (each
/// snapshot stamps `at_unix_ns` alongside `at_cycle`). When observatory
/// history does not yet cover the window (fresh substrate / first cycles),
/// the cutoff falls back to cycle 0 = count all CI events. This is the
/// conservative-aggressive choice: the burst threshold (10 events) still
/// fires correctly during the test-bench `m25_1_doctrine_burst_detector_*`
/// scenarios where a substrate registers 12 axes in a fresh DAG.
pub(crate) fn compute_observatory_counts(
    state: &ServerState,
    burst_window_unix_ns: i64,
) -> ObservatoryCounts {
    use std::time::{SystemTime, UNIX_EPOCH};

    let dag_node_count = state.dag.node_count() as u64;

    // M26.1 C3 fix: derive a cycle cutoff from the wall-clock window via
    // observatory_history. Each observatory snapshot is appended on
    // `cycle_advanced` (see `append_observatory_snapshot_to_state`), so
    // history.at_cycle ↔ history.at_unix_ns is the cycle ↔ wall-clock map.
    let now_unix_ns: i64 = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let cutoff_unix_ns: i64 = now_unix_ns.saturating_sub(burst_window_unix_ns);
    let burst_cutoff_cycle: u64 = match state.observatory_history.front() {
        // History exists.
        Some(oldest) => {
            if oldest.at_unix_ns >= cutoff_unix_ns {
                // The oldest snapshot is already inside the window — window
                // exceeds available history. Count from cycle 0.
                0
            } else {
                // Find the first snapshot whose wall-clock is at-or-after
                // cutoff. Its at_cycle is the cycle cutoff.
                state
                    .observatory_history
                    .iter()
                    .find(|s| s.at_unix_ns >= cutoff_unix_ns)
                    .map(|s| s.at_cycle)
                    // Fallback: every snapshot predates the window → no
                    // events in window.
                    .unwrap_or(state.manifest.cycle_counter.saturating_add(1))
            }
        }
        // No history yet (fresh substrate, no cycles advanced): count all CI
        // events. INTERIM behavior; refines as observatory history grows.
        None => 0,
    };

    let mut dag_edge_count: u64 = 0;
    let mut dag_total_content_bytes: u64 = 0;
    let mut evolution_event_count: u64 = 0;
    let mut axis_register_count: u64 = 0;
    let mut perturbed_axes: std::collections::BTreeSet<String> =
        std::collections::BTreeSet::new();
    let mut federation_received_count: u64 = 0;
    let mut ci_events_in_burst_window: u64 = 0;

    for n in state.dag.iter_in_insertion_order() {
        dag_edge_count = dag_edge_count.saturating_add(n.parent_hashes.len() as u64);
        dag_total_content_bytes = dag_total_content_bytes
            .saturating_add(n.content_canonical_bytes.as_ref().len() as u64);
        let nt = &n.node_type;
        let mut is_ci = false;
        if nt.starts_with("axis_registered:") {
            axis_register_count = axis_register_count.saturating_add(1);
            evolution_event_count = evolution_event_count.saturating_add(1);
            is_ci = true;
        } else if nt.starts_with("evolution_succeeded:") || nt.starts_with("evolution_failed:") {
            evolution_event_count = evolution_event_count.saturating_add(1);
            is_ci = true;
        } else if let Some(axis_name) = nt.strip_prefix("axis_perturbed:") {
            perturbed_axes.insert(axis_name.to_string());
        } else if nt.starts_with("federation_received:") {
            federation_received_count = federation_received_count.saturating_add(1);
        }
        // M25.1 doctrine-burst: owner_key_* events are also CI-class.
        if nt == crate::events::NODE_TYPE_OWNER_KEY_INITIALIZED
            || nt == crate::events::NODE_TYPE_OWNER_KEY_ADDED
            || nt == crate::events::NODE_TYPE_OWNER_KEY_ARCHIVED
        {
            is_ci = true;
        }
        if is_ci && n.created_at_cycle >= burst_cutoff_cycle {
            ci_events_in_burst_window = ci_events_in_burst_window.saturating_add(1);
        }
    }

    let established_peers = state
        .federation
        .peers
        .iter()
        .filter(|p| p.state == crate::federation::transport::PeerConnectionState::Established)
        .count() as u64;

    ObservatoryCounts {
        dag_node_count,
        dag_edge_count,
        dag_total_content_bytes,
        evolution_event_count,
        axis_register_count,
        distinct_perturbed_axes_count: perturbed_axes.len() as u64,
        federation_received_count,
        established_peers,
        ci_events_in_burst_window,
    }
}

/// M25.2 + **M26.2**: append a fresh observatory snapshot to
/// `state.observatory_history` and enforce the cap. Called on every
/// `cycle_advanced` emission.
///
/// `signal_6_ratio_repr` is filled from `state.last_operator_context_window_bytes`
/// if present (empty string otherwise — substrate cannot derive autonomously).
///
/// **M26.2 P11.b**: also drains `state.cost_accumulator` and writes the
/// per-cycle compute / network / storage costs into the snapshot. This is
/// the chokepoint where signals #7/#8/#9 land in the rolling history; the
/// `query_substrate_observatory` handler then computes per-cycle and
/// trend-window views from this same history.
pub(crate) fn append_observatory_snapshot_to_state(state: &mut ServerState) {
    use crate::derived_state::{ObservatorySnapshot, OBSERVATORY_HISTORY_CAP};
    use std::time::{SystemTime, UNIX_EPOCH};

    let counts = compute_observatory_counts(state, M25_1_DOCTRINE_BURST_WINDOW_UNIX_NS);
    let at_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);

    let signal_6_ratio_repr = match state.last_operator_context_window_bytes {
        Some(0) => "inf".to_string(),
        Some(w) => float_repr((counts.dag_total_content_bytes as f64) / (w as f64)),
        None => String::new(),
    };

    // M26.2 P11.b: drain the cost accumulator. This atomically reads the
    // three cost signals AND resets the timer + file-size baselines for
    // the next cycle. MUST happen at most once per cycle_advanced.
    let cost = state
        .cost_accumulator
        .snapshot_and_reset(&mut state.federation, &state.state_dir);

    let snapshot = ObservatorySnapshot {
        at_cycle: state.manifest.cycle_counter,
        at_unix_ns,
        signal_1_dag_node_count: counts.dag_node_count,
        signal_1_dag_total_content_bytes: counts.dag_total_content_bytes,
        signal_2_evolution_event_count: counts.evolution_event_count,
        signal_3_distinct_perturbed_axes_count: counts.distinct_perturbed_axes_count,
        signal_4b_reachable_peer_count: counts.established_peers,
        signal_6_ratio_repr,
        signal_7_compute_ns: cost.compute_ns,
        signal_8_network_bytes: cost.network_bytes,
        signal_9_storage_bytes: cost.storage_bytes,
    };
    state.observatory_history.push_back(snapshot);
    while state.observatory_history.len() > OBSERVATORY_HISTORY_CAP {
        state.observatory_history.pop_front();
    }
}

/// M25.1 + M26.1 C3 fix: wall-clock window (nanoseconds) for doctrine-burst
/// detection. Counts CI-class events landed in the last N wall-clock seconds
/// (NOT substrate-cycles). 90 days is the L0 §7.4 + L2_OBSERVABILITY §8
/// seed; the L1 tunable will live in a future seed-config event.
///
/// INTERIM: substrate-process wall-clock per L0 §13.1; M-anchor-3 promotes
/// to anchor-stamped wall-clock.
pub(crate) const M25_1_DOCTRINE_BURST_WINDOW_UNIX_NS: i64 =
    90 * 24 * 60 * 60 * 1_000_000_000;
/// M25.1: threshold above which the CI-event burst window fires a C37
/// immune sporocarp.
pub(crate) const M25_1_DOCTRINE_BURST_THRESHOLD: u64 = 10;
/// M25.1 + M25.2: cooldown (in substrate-cycles) between repeated emissions
/// of the doctrine-burst / bet-weakening-quorum sporocarps so a single
/// burst is not amplified into hundreds of immune events.
pub(crate) const M25_DETECTOR_COOLDOWN_CYCLES: u64 = 100;
/// M25.2: minimum history length before signal #5 (time trends) and the
/// `bet_weakening_quorum` quorum predicate become evaluable. Below this
/// the trend signals are reported as "unknown" / "evaluable=false".
pub(crate) const M25_2_MIN_HISTORY_LEN_FOR_TRENDS: usize = 10;

/// Phase α (2026-05-15) — Living Bets observatory primitive.
///
/// Per L2_OBSERVABILITY §2 + L0 §7. Ships the full 10-signal Living Bets
/// observatory: 6 base (#1/#2/#3/#4a/#4b/#5/#6, with #5 meta) + 3 cost
/// (#7/#8/#9, M26.2) + 1 composite (#10, M26.2 — was signal_7_composite_health
/// under the v3 schema, renamed to match doctrine §2.3 numbering).
///
/// **Format version 4** (M26.2 P11.b): adds `signal_7_compute_per_cycle`,
/// `signal_8_network_per_cycle`, `signal_9_storage_per_cycle`, renames
/// `signal_7_composite_health` → `signal_10_composite_health`, renames
/// `signal_8_doctrine_revision_burst` → `doctrine_revision_burst_status`
/// (the latter is NOT one of the 10 Living Bet signals; it's a C37 detector
/// output and the old "signal_8" naming was a pre-doctrine-alignment artifact).
///
/// Payload:
/// ```text
/// Map({
///   "operator_attested_context_window_bytes": Uint [optional],
/// })
/// ```
///
/// Response payload (format_version=4):
/// ```text
/// Map({
///   "signal_1_persistence_budget": Map({...}),
///   "signal_2_evolution_rate": Map({...}),
///   "signal_3_read_pattern_diversity": Map({...}),
///   "signal_4_federation_health": Map({...}),
///   "signal_5_time_trends": Map({...}),
///   "signal_6_read_window_position": Map({...}) [iff operator supplied window],
///   "signal_7_compute_per_cycle": Map({  // M26.2 NEW
///     "current_cycle_ns": Uint,
///     "rolling_mean_ns_repr": String,
///   }),
///   "signal_8_network_per_cycle": Map({  // M26.2 NEW
///     "current_cycle_bytes": Uint,
///     "rolling_mean_bytes_repr": String,
///   }),
///   "signal_9_storage_per_cycle": Map({  // M26.2 NEW
///     "current_cycle_bytes": Uint,
///     "rolling_mean_bytes_repr": String,
///   }),
///   "signal_10_composite_health": Map({  // M26.2 RENAMED from signal_7
///     "composite_health_score_repr": String,
///     "composite_format_version": Uint,
///     "weights": Map({"signal_1": String, "signal_2": String, ...}),
///     "weights_method": String,
///   }),
///   "doctrine_revision_burst_status": Map({...}),  // M26.2 RENAMED from signal_8
///   "bet_weakening_quorum": Map({...}),
///   "observatory_format_version": Uint,            // = 4
///   "captured_at_unix_ns": Timestamp,
/// })
/// ```
pub(crate) fn handle_query_substrate_observatory(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};

    // Single O(N) DAG scan shared with the cycle-tick snapshot path so
    // signal definitions cannot drift between the live response and the
    // history series.
    let counts = compute_observatory_counts(state, M25_1_DOCTRINE_BURST_WINDOW_UNIX_NS);
    let dag_node_count = counts.dag_node_count;
    let dag_edge_count = counts.dag_edge_count;
    let dag_total_content_bytes = counts.dag_total_content_bytes;
    let evolution_event_count = counts.evolution_event_count;
    let axis_register_count = counts.axis_register_count;
    let distinct_perturbed_axes_count = counts.distinct_perturbed_axes_count;
    let federation_received_count = counts.federation_received_count;
    let established_peers = counts.established_peers;
    let ci_events_in_burst_window = counts.ci_events_in_burst_window;
    let manifest_cycle_counter = state.manifest.cycle_counter;

    // Signal #6: read-window-relative position. Only computed if the
    // operator attests their context window size. M25.2: the attested
    // window is cached on ServerState so subsequent cycle-tick snapshots
    // can keep populating `signal_6_ratio_repr` between operator queries.
    let operator_window = match request.payload.get("operator_attested_context_window_bytes") {
        Some(Value::Uint(n)) => Some(*n),
        _ => None,
    };
    if let Some(w) = operator_window {
        state.last_operator_context_window_bytes = Some(w);
    }

    let mut signal_1_map = BTreeMap::new();
    signal_1_map.insert("dag_node_count".to_string(), Value::Uint(dag_node_count));
    signal_1_map.insert("dag_edge_count".to_string(), Value::Uint(dag_edge_count));
    signal_1_map.insert(
        "dag_total_content_bytes".to_string(),
        Value::Uint(dag_total_content_bytes),
    );
    signal_1_map.insert(
        "manifest_cycle_counter".to_string(),
        Value::Uint(manifest_cycle_counter),
    );

    let mut payload = BTreeMap::new();
    payload.insert(
        "signal_1_persistence_budget".to_string(),
        Value::Map(signal_1_map),
    );

    if let Some(window_bytes) = operator_window {
        let mut signal_6_map = BTreeMap::new();
        signal_6_map.insert(
            "substrate_total_bytes".to_string(),
            Value::Uint(dag_total_content_bytes),
        );
        signal_6_map.insert(
            "operator_attested_context_window_bytes".to_string(),
            Value::Uint(window_bytes),
        );
        // Ratio: substrate_total / context_window. Repr-float for cross-language
        // determinism.
        let ratio = if window_bytes == 0 {
            // Convention: ratio "+inf" when window is zero (no window = unbounded).
            "inf".to_string()
        } else {
            float_repr((dag_total_content_bytes as f64) / (window_bytes as f64))
        };
        signal_6_map.insert("ratio_repr".to_string(), Value::String(ratio));
        payload.insert(
            "signal_6_read_window_position".to_string(),
            Value::Map(signal_6_map),
        );
    }

    let mut signal_2_map = BTreeMap::new();
    signal_2_map.insert(
        "evolution_event_count".to_string(),
        Value::Uint(evolution_event_count),
    );
    signal_2_map.insert(
        "axis_register_count".to_string(),
        Value::Uint(axis_register_count),
    );
    signal_2_map.insert(
        "rate_repr".to_string(),
        Value::String(if manifest_cycle_counter == 0 {
            "0.0".to_string()
        } else {
            float_repr(
                (evolution_event_count as f64) / (manifest_cycle_counter.max(1) as f64),
            )
        }),
    );
    payload.insert(
        "signal_2_evolution_rate".to_string(),
        Value::Map(signal_2_map),
    );

    let mut signal_3_map = BTreeMap::new();
    signal_3_map.insert(
        "distinct_perturbed_axes_count".to_string(),
        Value::Uint(distinct_perturbed_axes_count),
    );
    payload.insert(
        "signal_3_read_pattern_diversity".to_string(),
        Value::Map(signal_3_map),
    );

    // signal_4: federation health (4a/4b).
    let mut signal_4_map = BTreeMap::new();
    signal_4_map.insert(
        "signal_4a_cumulative_fork_count".to_string(),
        Value::Uint(0), // placeholder — fork tracking M25+
    );
    signal_4_map.insert(
        "signal_4b_reachable_peer_count".to_string(),
        Value::Uint(established_peers),
    );
    signal_4_map.insert(
        "events_received_from_peers".to_string(),
        Value::Uint(federation_received_count),
    );
    payload.insert("signal_4_federation_health".to_string(), Value::Map(signal_4_map));

    // -----------------------------------------------------------------------
    // M25.2: signal #5 time trends + bet_weakening_quorum predicate.
    //
    // signal_5 = per-signal direction ("up" / "down" / "flat" / "unknown")
    // computed over the rolling observatory_history window. Becomes evaluable
    // after `M25_2_MIN_HISTORY_LEN_FOR_TRENDS` snapshots are accumulated.
    //
    // bet_weakening_quorum = L0 §7 falsifiability mechanism. Triggered when
    // ≥3 of signals 1/2/3/4b/6 trend AGAINST the bet (i.e. "down" for the
    // signals where "up" means substrate-favorable) AND signal #6 stays < 1
    // for ≥50% of cycles in the window. Emits a C38 immune sporocarp +
    // bet_weakening_quorum_quorum:<cycle> positive DAG event.
    // -----------------------------------------------------------------------
    // Extract everything we need from history into owned locals so the
    // immutable borrow drops here. Subsequent mutable state.emit_* calls
    // would otherwise conflict with `&state.observatory_history`.
    let (
        window_samples,
        trends_evaluable,
        sig_1_dir,
        sig_2_dir,
        sig_3_dir,
        sig_4b_dir,
        sig_6_dir,
        sig_6_below_one_fraction,
        emergent_weights,
        s7_rolling_mean_ns,
        s8_rolling_mean_bytes,
        s9_rolling_mean_bytes,
    ) = {
        let history = &state.observatory_history;
        let window_samples: u64 = history.len() as u64;
        let trends_evaluable = history.len() >= M25_2_MIN_HISTORY_LEN_FOR_TRENDS;

        let sig_1_dir = signal_direction_label(history, |s| s.signal_1_dag_node_count as f64);
        let sig_2_dir =
            signal_direction_label(history, |s| s.signal_2_evolution_event_count as f64);
        let sig_3_dir = signal_direction_label(history, |s| {
            s.signal_3_distinct_perturbed_axes_count as f64
        });
        let sig_4b_dir =
            signal_direction_label(history, |s| s.signal_4b_reachable_peer_count as f64);
        let sig_6_dir = signal_direction_label(history, |s| {
            s.signal_6_ratio_repr.parse::<f64>().unwrap_or(0.0)
        });

        let (sig_6_below_one_count, sig_6_measured_count) = history
            .iter()
            .filter(|s| !s.signal_6_ratio_repr.is_empty())
            .fold((0u64, 0u64), |(below, total), s| {
                let r = s.signal_6_ratio_repr.parse::<f64>().unwrap_or(0.0);
                (below + (r < 1.0) as u64, total + 1)
            });
        let sig_6_below_one_fraction: f64 = if sig_6_measured_count == 0 {
            0.0
        } else {
            sig_6_below_one_count as f64 / sig_6_measured_count as f64
        };

        // M25.3 + **M26.2** emergent weights: compute here while we still
        // hold the immutable borrow on history. The weights flow out as an
        // owned value. M26.2 expands the basis from {1, 2, 4b} to
        // {1, 2, 4b, 7, 8, 9} per L2_OBSERVABILITY §2 (10 signals total —
        // 6 base + 3 cost + 1 composite).
        let log_normalized_local = |x: u64| -> f64 {
            if x == 0 {
                0.0
            } else {
                ((x as f64).ln() / 10.0_f64.ln()).max(0.0).min(10.0)
            }
        };
        // M26.2: cost-signal rolling-mean for the per-cycle response shape.
        // Rolling mean = arithmetic mean over the entire history window.
        // If history is empty, mean = 0.
        let mean_u64 = |v: &[u64]| -> f64 {
            if v.is_empty() {
                0.0
            } else {
                v.iter().map(|x| *x as f64).sum::<f64>() / v.len() as f64
            }
        };
        let s7_history: Vec<u64> =
            history.iter().map(|s| s.signal_7_compute_ns).collect();
        let s8_history: Vec<u64> =
            history.iter().map(|s| s.signal_8_network_bytes).collect();
        let s9_history: Vec<u64> =
            history.iter().map(|s| s.signal_9_storage_bytes).collect();
        let s7_mean = mean_u64(&s7_history);
        let s8_mean = mean_u64(&s8_history);
        let s9_mean = mean_u64(&s9_history);

        let emergent_weights: (EmergentWeights, &'static str) =
            if history.len() >= M25_2_MIN_HISTORY_LEN_FOR_TRENDS {
                let s1: Vec<f64> = history
                    .iter()
                    .map(|s| log_normalized_local(s.signal_1_dag_node_count))
                    .collect();
                let s2: Vec<f64> = history
                    .iter()
                    .map(|s| log_normalized_local(s.signal_2_evolution_event_count))
                    .collect();
                let s4b: Vec<f64> = history
                    .iter()
                    .map(|s| log_normalized_local(s.signal_4b_reachable_peer_count))
                    .collect();
                let s7v: Vec<f64> = history
                    .iter()
                    .map(|s| log_normalized_local(s.signal_7_compute_ns))
                    .collect();
                let s8v: Vec<f64> = history
                    .iter()
                    .map(|s| log_normalized_local(s.signal_8_network_bytes))
                    .collect();
                let s9v: Vec<f64> = history
                    .iter()
                    .map(|s| log_normalized_local(s.signal_9_storage_bytes))
                    .collect();
                let stddev = |v: &[f64]| -> f64 {
                    if v.is_empty() {
                        return 0.0;
                    }
                    let m: f64 = v.iter().sum::<f64>() / v.len() as f64;
                    let var =
                        v.iter().map(|x| (x - m).powi(2)).sum::<f64>() / v.len() as f64;
                    var.sqrt()
                };
                let v1 = stddev(&s1);
                let v2 = stddev(&s2);
                let v4 = stddev(&s4b);
                let v7 = stddev(&s7v);
                let v8 = stddev(&s8v);
                let v9 = stddev(&s9v);
                let sum = v1 + v2 + v4 + v7 + v8 + v9;
                if sum > 1e-9 {
                    (
                        EmergentWeights {
                            w1: v1 / sum,
                            w2: v2 / sum,
                            w4b: v4 / sum,
                            w7: v7 / sum,
                            w8: v8 / sum,
                            w9: v9 / sum,
                        },
                        "emergent_variance",
                    )
                } else {
                    // Degenerate: every signal flat → equal weights across 6 dims.
                    let e = 1.0 / 6.0;
                    (
                        EmergentWeights {
                            w1: e,
                            w2: e,
                            w4b: e,
                            w7: e,
                            w8: e,
                            w9: e,
                        },
                        "equal_degenerate",
                    )
                }
            } else {
                // Cold-start: insufficient history; equal across 6 dims.
                let e = 1.0 / 6.0;
                (
                    EmergentWeights {
                        w1: e,
                        w2: e,
                        w4b: e,
                        w7: e,
                        w8: e,
                        w9: e,
                    },
                    "equal_cold_start",
                )
            };

        (
            window_samples,
            trends_evaluable,
            sig_1_dir,
            sig_2_dir,
            sig_3_dir,
            sig_4b_dir,
            sig_6_dir,
            sig_6_below_one_fraction,
            emergent_weights,
            s7_mean,
            s8_mean,
            s9_mean,
        )
    };

    let mut signal_5_map = BTreeMap::new();
    signal_5_map.insert(
        "signal_1_direction".to_string(),
        Value::String(sig_1_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_2_direction".to_string(),
        Value::String(sig_2_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_3_direction".to_string(),
        Value::String(sig_3_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_4b_direction".to_string(),
        Value::String(sig_4b_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_6_direction".to_string(),
        Value::String(sig_6_dir.to_string()),
    );
    signal_5_map.insert("window_samples".to_string(), Value::Uint(window_samples));
    signal_5_map.insert(
        "evaluable".to_string(),
        Value::Bool(trends_evaluable),
    );
    payload.insert("signal_5_time_trends".to_string(), Value::Map(signal_5_map));

    // bet_weakening_quorum predicate. M26.1 C4 fix: comment rewritten to
    // align with L2_OBSERVABILITY §2.1 + algorithms/bet_weakening_quorum.md.
    //
    // Per the §2.1 direction table:
    //   - Signal #1 (persistence budget): DOWN = "not growing" = against bet.
    //   - Signal #2 (evolution rate): DOWN = "stagnating" = against bet.
    //   - Signal #3 (read-pattern diversity): DOWN = "not being read" = against bet.
    //   - Signal #4b (reachable peers): DOWN = "mycelial fragmentation" = against bet.
    //   - Signal #6 (read-window-relative ratio = substrate_total/context_window):
    //     DOWN = "shrinking vs context" = ratio decreasing over time = substrate
    //     becoming RELATIVELY SMALLER than the read-window = substrate failing
    //     its persistence bet = against bet. The §2.1 "DOWN <1.0" notation
    //     captures the combined condition: counts against bet when DOWN AND
    //     ratio is already below 1 (substrate cannot fill the read-window).
    //     The "ratio < 1 for ≥ 50% of window" check is enforced separately
    //     below as `sig_6_below_one_fraction >= 0.5`; here we only count
    //     the trend direction.
    //
    // Prior comment (replaced) said signal_6 DOWN means "substrate-relative-
    // to-window improving" — that was inverted relative to doctrine and was
    // flagged as Phase γ.2 C4. The behavior here (counting sig_6_dir == "down"
    // as against bet) was correct; only the comment misrepresented spec.
    let against_count: u64 = [
        sig_1_dir == "down",
        sig_2_dir == "down",
        sig_3_dir == "down",
        sig_4b_dir == "down",
        sig_6_dir == "down",
    ]
    .iter()
    .filter(|&&b| b)
    .count() as u64;

    let quorum_evaluable = trends_evaluable;
    let quorum_triggered =
        quorum_evaluable && against_count >= 3 && sig_6_below_one_fraction >= 0.5;

    let mut bwq_map = BTreeMap::new();
    bwq_map.insert("triggered".to_string(), Value::Bool(quorum_triggered));
    bwq_map.insert("evaluable".to_string(), Value::Bool(quorum_evaluable));
    bwq_map.insert("against_count".to_string(), Value::Uint(against_count));
    bwq_map.insert(
        "signal_6_below_one_fraction_repr".to_string(),
        Value::String(float_repr(sig_6_below_one_fraction)),
    );
    bwq_map.insert("window_samples".to_string(), Value::Uint(window_samples));
    payload.insert("bet_weakening_quorum".to_string(), Value::Map(bwq_map));

    // Fire C38 sporocarp on quorum trigger (deduped via cooldown).
    if quorum_triggered {
        let cooldown_expired = match state.last_bet_weakening_quorum_emitted_at_cycle {
            None => true,
            Some(prior) => manifest_cycle_counter.saturating_sub(prior)
                >= M25_DETECTOR_COOLDOWN_CYCLES,
        };
        if cooldown_expired {
            let evidence = format!(
                "against_count={against_count}, sig_6_below_one_fraction={:.4}, \
                 window_samples={window_samples}, dirs=[1:{sig_1_dir},2:{sig_2_dir},\
                 3:{sig_3_dir},4b:{sig_4b_dir},6:{sig_6_dir}]",
                sig_6_below_one_fraction
            );
            let _ = emit_immune_sporocarp(
                state,
                "C40_bet_weakening_quorum",
                "bet_weakening_quorum_detected",
                &evidence,
            );
            // Positive (non-immune) DAG event preserving the trigger.
            let mut quorum_content = BTreeMap::new();
            quorum_content.insert("at_cycle".to_string(), Value::Uint(manifest_cycle_counter));
            quorum_content.insert("against_count".to_string(), Value::Uint(against_count));
            quorum_content.insert(
                "signal_6_below_one_fraction_repr".to_string(),
                Value::String(float_repr(sig_6_below_one_fraction)),
            );
            quorum_content.insert("window_samples".to_string(), Value::Uint(window_samples));
            if let Ok(bytes) = cb_encode(&Value::Map(quorum_content)) {
                let _ = emit_substrate_event(
                    state,
                    format!("bet_weakening_quorum_quorum:{}", manifest_cycle_counter),
                    bytes,
                );
            }
            state.last_bet_weakening_quorum_emitted_at_cycle = Some(manifest_cycle_counter);
        }
    }

    // -----------------------------------------------------------------------
    // M25.1: doctrine-instability burst detection.
    //
    // CI-class events (axis_registered + evolution_succeeded/failed +
    // owner_key_*) over the rolling wall-clock window (M26.1 C3 fix). If
    // burst threshold exceeded, fruit a C37 immune sporocarp (deduped via
    // cooldown).
    // -----------------------------------------------------------------------
    let is_burst = ci_events_in_burst_window > M25_1_DOCTRINE_BURST_THRESHOLD;
    let mut burst_status_map = BTreeMap::new();
    // M26.1 C3 fix: field renamed from `ci_events_recent_100_cycles` to
    // `ci_events_in_burst_window` — window is now wall-clock per L0 §7.4.
    burst_status_map.insert(
        "ci_events_in_burst_window".to_string(),
        Value::Uint(ci_events_in_burst_window),
    );
    burst_status_map.insert(
        "burst_window_unix_ns".to_string(),
        Value::Uint(M25_1_DOCTRINE_BURST_WINDOW_UNIX_NS as u64),
    );
    burst_status_map.insert(
        "burst_threshold".to_string(),
        Value::Uint(M25_1_DOCTRINE_BURST_THRESHOLD),
    );
    burst_status_map.insert("is_burst".to_string(), Value::Bool(is_burst));
    // **M26.2 RENAME**: was `signal_8_doctrine_revision_burst` (v3 schema)
    // → `doctrine_revision_burst_status` (v4 schema). The doctrine-burst
    // signal is NOT one of L2_OBSERVABILITY §2's 10 Living Bet signals; it
    // is a C37 detector output. Reusing the "signal_8" key collided with
    // the actual signal #8 (network/cycle) introduced in this milestone.
    payload.insert(
        "doctrine_revision_burst_status".to_string(),
        Value::Map(burst_status_map),
    );

    if is_burst {
        let cooldown_expired = match state.last_doctrine_burst_emitted_at_cycle {
            None => true,
            Some(prior) => manifest_cycle_counter.saturating_sub(prior)
                >= M25_DETECTOR_COOLDOWN_CYCLES,
        };
        if cooldown_expired {
            let evidence = format!(
                "ci_events_in_window={ci_events_in_burst_window}, \
                 threshold={}, window_unix_ns={}",
                M25_1_DOCTRINE_BURST_THRESHOLD, M25_1_DOCTRINE_BURST_WINDOW_UNIX_NS
            );
            let _ = emit_immune_sporocarp(
                state,
                "C37_doctrine_instability_burst",
                "doctrine_instability_burst",
                &evidence,
            );
            state.last_doctrine_burst_emitted_at_cycle = Some(manifest_cycle_counter);
        }
    }

    // -----------------------------------------------------------------------
    // **M26.2 P11.b**: signals #7/#8/#9 (compute / network / storage per cycle).
    //
    // Each emits the CURRENT cycle's value (drawn from the most recent
    // ObservatorySnapshot in history) plus a ROLLING MEAN over the entire
    // history window. The rolling mean stabilizes the signal across the
    // boot-time jitter and makes trend-window inspection meaningful.
    //
    // When history is empty (substrate just booted, no cycles advanced),
    // current = 0 and rolling_mean = 0 — clients should treat this as
    // "not yet measured" rather than "zero cost".
    // -----------------------------------------------------------------------
    let (current_s7, current_s8, current_s9) = match state.observatory_history.back() {
        Some(latest) => (
            latest.signal_7_compute_ns,
            latest.signal_8_network_bytes,
            latest.signal_9_storage_bytes,
        ),
        None => (0u64, 0u64, 0u64),
    };

    let mut signal_7_cost_map = BTreeMap::new();
    signal_7_cost_map.insert(
        "current_cycle_ns".to_string(),
        Value::Uint(current_s7),
    );
    signal_7_cost_map.insert(
        "rolling_mean_ns_repr".to_string(),
        Value::String(float_repr(s7_rolling_mean_ns)),
    );
    payload.insert(
        "signal_7_compute_per_cycle".to_string(),
        Value::Map(signal_7_cost_map),
    );

    let mut signal_8_cost_map = BTreeMap::new();
    signal_8_cost_map.insert(
        "current_cycle_bytes".to_string(),
        Value::Uint(current_s8),
    );
    signal_8_cost_map.insert(
        "rolling_mean_bytes_repr".to_string(),
        Value::String(float_repr(s8_rolling_mean_bytes)),
    );
    payload.insert(
        "signal_8_network_per_cycle".to_string(),
        Value::Map(signal_8_cost_map),
    );

    let mut signal_9_cost_map = BTreeMap::new();
    signal_9_cost_map.insert(
        "current_cycle_bytes".to_string(),
        Value::Uint(current_s9),
    );
    signal_9_cost_map.insert(
        "rolling_mean_bytes_repr".to_string(),
        Value::String(float_repr(s9_rolling_mean_bytes)),
    );
    payload.insert(
        "signal_9_storage_per_cycle".to_string(),
        Value::Map(signal_9_cost_map),
    );

    // -----------------------------------------------------------------------
    // M25.3 + **M26.2 RENAME**: emergent composite #10.
    //
    // Was `signal_7_composite_health` under v3 schema. v4 renames to
    // `signal_10_composite_health` to align with L2_OBSERVABILITY §2.3
    // numbering (10 signals = 6 base + 3 cost + 1 composite).
    //
    // Composite formula (M26.2):
    //   composite = sum_i ( w_i * direction_i * log_normalized(value_i) )
    //
    // where direction_i = +1 for production signals (1, 2, 4b) and -1 for
    // cost signals (7, 8, 9). Production UP increases composite (good);
    // cost UP decreases composite (bad). Higher composite = healthier
    // substrate. Weights w_i are variance-derived per `EmergentWeights`.
    //
    // Direction-inverted blend gives `composite` a stable "more = better"
    // semantic. Doctrine §2.3 leaves direction handling unspecified; this
    // choice is documented as part of M26.2 and can be revisited in
    // M26.3+ when the correlation-weighted steady-state variant lands.
    // -----------------------------------------------------------------------
    let log_normalized = |x: u64| -> f64 {
        if x == 0 {
            0.0
        } else {
            ((x as f64).ln() / 10.0_f64.ln()).max(0.0).min(10.0)
        }
    };
    let (w, weights_method) = emergent_weights;
    let composite = w.w1 * log_normalized(dag_node_count)
        + w.w2 * log_normalized(evolution_event_count)
        + w.w4b * log_normalized(established_peers)
        - w.w7 * log_normalized(current_s7)
        - w.w8 * log_normalized(current_s8)
        - w.w9 * log_normalized(current_s9);
    let mut signal_10_map = BTreeMap::new();
    signal_10_map.insert(
        "composite_health_score_repr".to_string(),
        Value::String(float_repr(composite)),
    );
    // composite_format_version bumped 3 → 4 alongside outer
    // observatory_format_version: schema now includes negative cost
    // contributions from signals 7/8/9.
    signal_10_map.insert("composite_format_version".to_string(), Value::Uint(4));
    let mut weights_map = BTreeMap::new();
    weights_map.insert("signal_1".to_string(), Value::String(float_repr(w.w1)));
    weights_map.insert("signal_2".to_string(), Value::String(float_repr(w.w2)));
    weights_map.insert("signal_4b".to_string(), Value::String(float_repr(w.w4b)));
    weights_map.insert("signal_7".to_string(), Value::String(float_repr(w.w7)));
    weights_map.insert("signal_8".to_string(), Value::String(float_repr(w.w8)));
    weights_map.insert("signal_9".to_string(), Value::String(float_repr(w.w9)));
    signal_10_map.insert("weights".to_string(), Value::Map(weights_map));
    signal_10_map.insert(
        "weights_method".to_string(),
        Value::String(weights_method.to_string()),
    );
    payload.insert(
        "signal_10_composite_health".to_string(),
        Value::Map(signal_10_map),
    );

    // **M26.2**: observatory_format_version 3 → 4 — adds signals 7/8/9
    // (cost), renames signal_7_composite_health → signal_10_composite_health,
    // renames signal_8_doctrine_revision_burst → doctrine_revision_burst_status.
    payload.insert("observatory_format_version".to_string(), Value::Uint(4));
    let captured_at_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    payload.insert(
        "captured_at_unix_ns".to_string(),
        Value::Timestamp(captured_at_unix_ns),
    );

    Ok(Some(Message::new(
        msg_type::QUERY_SUBSTRATE_OBSERVATORY_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M25.2: classify a signal's direction over the rolling observatory history
/// window. Returns "unknown" until ≥3 samples are available, then "up" /
/// "down" / "flat" based on a 5% normalized delta threshold between the
/// oldest and newest samples.
pub(crate) fn signal_direction_label(
    history: &std::collections::VecDeque<crate::derived_state::ObservatorySnapshot>,
    getter: impl Fn(&crate::derived_state::ObservatorySnapshot) -> f64,
) -> &'static str {
    if history.len() < 3 {
        return "unknown";
    }
    let first = match history.front() {
        Some(s) => getter(s),
        None => return "unknown",
    };
    let last = match history.back() {
        Some(s) => getter(s),
        None => return "unknown",
    };
    let delta = last - first;
    let scale = first.abs().max(1.0);
    let normalized = delta / scale;
    if normalized > 0.05 {
        "up"
    } else if normalized < -0.05 {
        "down"
    } else {
        "flat"
    }
}
