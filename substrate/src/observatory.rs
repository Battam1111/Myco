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
//! These complete L0/cards/LB_living_bets + L2/OBSERVABILITY §2 "10 = 6 base + 3 cost + 1
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

    /// Mark the START of a cycle's compute window. Call at the `handle_advance`
    /// entry (where the cycle work begins) so signal #7 `compute_ns` measures the
    /// IN-CYCLE compute — NOT the wall-clock gap between cycle advances. Folding
    /// the inter-cycle idle/think time into `compute_ns` would spuriously exhaust
    /// the P11.c compute budget on ANY substrate cycling slower than 100ms (the
    /// entire legitimate cadence range, L1/CONTINUITY §1.2), cascading to false
    /// P02 ingestion refusal → saturation → `self_euthanasia_proposal` on a
    /// perfectly healthy organism.
    pub(crate) fn mark_cycle_start(&mut self) {
        self.cycle_started_at = Instant::now();
    }

    /// Compute the cost signals for the cycle that just ended. Signal #7
    /// `compute_ns` is measured from the most recent [`mark_cycle_start`] (the
    /// `handle_advance` entry) to now — the cycle's actual in-cycle compute,
    /// excluding the inter-cycle idle wait. Reads federation egress via
    /// `state.federation.drain_bytes_egressed()`.
    ///
    /// **Side effects**: zeroes `state.federation.bytes_egressed_since_last_drain`
    /// (via drain) and refreshes `last_dag_cb_bytes` + `last_snapshot_cb_bytes`
    /// from disk. Does NOT reset `cycle_started_at` — that is [`mark_cycle_start`]'s
    /// job at the next cycle's start.
    ///
    /// [`mark_cycle_start`]: Self::mark_cycle_start
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

        // Refresh baselines. NOTE: `cycle_started_at` is intentionally NOT reset
        // here — it is set by `mark_cycle_start` at the next cycle's
        // `handle_advance` entry, so `compute_ns` measures in-cycle work (not the
        // inter-cycle idle gap). Resetting here was the signal-#7 idle-misaccount
        // bug that cascaded a healthy substrate into a self-euthanasia proposal.
        self.last_dag_cb_bytes = cur_dag;
        self.last_snapshot_cb_bytes = cur_snap;

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
/// expanded the basis to {1, 2, 4b, 7, 8, 9} per L2/OBSERVABILITY §2.
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
    /// that landed in the most-recent burst window (wall-clock per L0/cards/LB_living_bets §3 (falsifiability quorum) +
    /// §13.1; M26.1 C3 fix). Used by M25.1 doctrine-burst detection.
    pub(crate) ci_events_in_burst_window: u64,
    /// **Signal #4a** — cumulative count of `spore_emission:*` events (each
    /// is one successful child sprout / fork emitted into the parent's DAG,
    /// see `reproduction.rs`). Monotone-healthy per L2/OBSERVABILITY §2.1
    /// (forks = mycelial spread, not bet-weakening), so this is surfaced as a
    /// signal but is deliberately NOT counted in the `bet_weakening_quorum`
    /// (the §2.1 "DOWN = peers exiting" wording is the network-fragmentation
    /// reading carried by #4b, the reachable-peer count; the cumulative fork
    /// count itself only ever rises).
    pub(crate) cumulative_fork_count: u64,
}

/// M25.2: scan the DAG once + read live federation state to populate an
/// `ObservatoryCounts` snapshot.
///
/// M26.1 C3 fix: `burst_window_unix_ns` is now a wall-clock window in
/// nanoseconds (was previously a substrate-cycle count). Doctrine intent
/// (L0/cards/LB_living_bets §3 (falsifiability quorum) + §13.1) is wall-clock 90 days; substrate-cycle counters drift
/// 4-6 orders of magnitude under typical cycle cadence (~1 cycle/sec) so
/// the prior cycle-based window was structurally wrong.
///
/// INTERIM: substrate-process wall-clock used here. M-anchor-3 promotes
/// to anchor-stamped wall-clock per L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics) (anchor surface authoritative
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
                    .unwrap_or(state.cycle_counter().saturating_add(1))
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
    let mut cumulative_fork_count: u64 = 0;
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
        } else if nt.starts_with("spore_emission:") {
            // **Signal #4a**: each spore_emission is one fork (child sprout).
            cumulative_fork_count = cumulative_fork_count.saturating_add(1);
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
        cumulative_fork_count,
    }
}

/// **M26.4 P14.c**: compute the rolling-window telos_alignment cosine
/// proxy. Returns `None` if not computable (no sporocarps, no objective +
/// no fallback, birth-period).
///
/// PROXY note: doctrine prescribes LLM embeddings; M26.4 substrates have
/// no substrate-side LLM, so this is a sparse-vector cosine over node_type
/// prefix space. See `events::OwnerObjective` doc comment for the full
/// rationale. Output range matches doctrine (`[-1, +1]`) and threshold
/// grading per L1/TROPISM §F.1.
///
/// Algorithm (M26.4 proxy):
/// 1. Build sporocarp prefix-distribution vector over the most recent
///    N=90 cycles (window = L0/cards/LB_living_bets §3 (falsifiability quorum) living-bets window). For each
///    daily-class sporocarp, increment the count for ALL prefixes from
///    OwnerObjective.weights that match its node_type. Normalize to a
///    sum-1 distribution.
/// 2. Build owner objective vector = the same prefix space, weights from
///    OwnerObjective. Normalize to sum-1.
/// 3. Cosine = dot(a, b) / (||a|| * ||b||).
/// 4. If either vector is all-zero → return `None` (no signal computable;
///    the substrate emits `telos_alignment_pending`).
pub(crate) fn compute_telos_alignment_cosine(state: &ServerState) -> Option<f64> {
    let objective = state.owner_objective.as_ref()?;
    if objective.weights.is_empty() {
        return None;
    }
    // Walk the DAG once over the most recent N cycles to count sporocarps
    // per prefix. CI-class events (mutation:*, evolution_*) are EXCLUDED
    // per L1/TROPISM §F.5 ("does NOT compute over CI-class sporocarps").
    let window: u64 = 90; // L0/cards/LB_living_bets §3 (falsifiability quorum) living-bets window
    let current_cycle = state.cycle_counter();
    let cycle_floor = current_cycle.saturating_sub(window);
    let mut per_prefix_count: std::collections::BTreeMap<String, u64> =
        std::collections::BTreeMap::new();
    let mut total: u64 = 0;
    for node in state.dag.iter_in_insertion_order() {
        if node.created_at_cycle < cycle_floor {
            continue;
        }
        // Skip CI-class events.
        let nt = &node.node_type;
        if nt.starts_with("mutation:")
            || nt.starts_with("evolution_succeeded:")
            || nt.starts_with("evolution_failed:")
            || nt.starts_with("genesis_event:")
            || nt.starts_with("owner_key_")
            || nt.starts_with("compression_event:")
            || nt.starts_with("operator_pinned:")
            || nt.starts_with("immune:")
        {
            continue;
        }
        // Count this sporocarp against every matching objective prefix.
        // A sporocarp may match multiple prefixes (e.g. an axis-perturbed
        // event could match both "axis_perturbed:" and "axis_perturbed:curiosity"
        // if both are declared in the objective).
        let mut matched_any = false;
        for (prefix, _w) in &objective.weights {
            if nt.starts_with(prefix.as_str()) {
                *per_prefix_count.entry(prefix.clone()).or_insert(0) += 1;
                matched_any = true;
            }
        }
        if matched_any {
            total += 1;
        }
    }
    if total == 0 {
        return None;
    }
    // Build vectors in prefix order from objective.weights.
    let mut a: Vec<f64> = Vec::with_capacity(objective.weights.len()); // sporocarp distrib
    let mut b: Vec<f64> = Vec::with_capacity(objective.weights.len()); // objective weights
    for (prefix, weight) in &objective.weights {
        let count = *per_prefix_count.get(prefix).unwrap_or(&0) as f64;
        a.push(count / total as f64);
        b.push(*weight);
    }
    // Cosine = dot / (||a|| * ||b||).
    let dot: f64 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f64 = a.iter().map(|x| x * x).sum::<f64>().sqrt();
    let norm_b: f64 = b.iter().map(|x| x * x).sum::<f64>().sqrt();
    if norm_a < 1e-12 || norm_b < 1e-12 {
        return None;
    }
    Some(dot / (norm_a * norm_b))
}

/// **M26.4 P14.c grading**: map cosine value to L1/TROPISM §F.1 threshold
/// table. Returns `(grade_label, node_type_to_emit_or_none)`.
///
/// **Phase ② C24 reachability fix**: the M26.4 PROXY (`compute_telos_alignment_cosine`)
/// builds NON-NEGATIVE sparse vectors, so the cosine is bounded `[0, 1]` and
/// could NEVER reach the original `cos ≤ 0.0` CRITICAL branch — C24
/// (`telos_drift_critical`) was structurally unreachable, the worst observable
/// grade being `drift_elevated`. The threshold table is re-partitioned so
/// CRITICAL fires at a POSITIVE cosine floor (`cos ≤ 0.2`) — a telos that has
/// drifted into the bottom fifth of the alignment range is genuinely critical,
/// consistent with `drift_elevated` already being alarming. Bands stay monotone:
///   - `aligned`        cos > 0.6        (no emission)
///   - `low`            0.4 < cos ≤ 0.6  (observability)
///   - `drift_elevated` 0.2 < cos ≤ 0.4  (telos_drift, elevated)
///   - `critical`       cos ≤ 0.2        (telos_drift_critical → C24)
///
/// When true LLM embeddings replace the proxy (M27+), the cosine range opens to
/// `[-1, +1]`; `cos ≤ 0.2` still partitions sensibly (anything not clearly
/// pulling toward the objective is critical), so the band survives the swap.
fn telos_grade_for_cosine(cos: f64) -> (&'static str, Option<&'static str>) {
    if cos > 0.6 {
        ("aligned", None)
    } else if cos > 0.4 {
        (
            "low",
            Some(crate::events::NODE_TYPE_TELOS_ALIGNMENT_LOW),
        )
    } else if cos > 0.2 {
        // §F.1 grades this as "telos_drift elevated".
        ("drift_elevated", Some(crate::events::NODE_TYPE_TELOS_DRIFT))
    } else {
        // cos ≤ 0.2: CRITICAL — routes to C24 immune sporocarp + the
        // dedicated telos_drift_critical event. Reachable on the [0,1] proxy.
        (
            "critical",
            Some(crate::events::NODE_TYPE_TELOS_DRIFT_CRITICAL),
        )
    }
}

/// **M26.4 P11.c stage check** — given the just-snapshotted cost values,
/// the per-axis budgets, and the current saturation_stage, compute the
/// new stage + any events that should be emitted on transition.
///
/// Returns `(new_stage, events_to_emit)`. Events are tuples of
/// `(node_type, content_canonical_bytes)`; caller emits them sequentially
/// via `emit_substrate_event`. Caller also emits per-axis
/// `budget_exhausted:{axis}` events (handled separately because they have
/// cooldown logic per-axis).
fn p11c_advance_stage(
    state: &ServerState,
    cost_snapshot: &CostSnapshot,
    any_axis_exceeded: bool,
) -> (
    crate::events::SaturationStage,
    Vec<(String, myco_kernel_shared::canonical_bytes::CanonicalBytes)>,
) {
    use crate::events::SaturationStage;
    let cycle = state.cycle_counter();
    let floor = state.cost_budgets.pre_eligibility_cycle_floor;
    let prev_stage = state.saturation_stage;

    let new_stage = if !any_axis_exceeded {
        SaturationStage::Normal
    } else if cycle < floor {
        SaturationStage::PreEligibility
    } else {
        // Either PostEligibility OR escalate to Saturated based on consecutive
        // cycle count tracked on ServerState.
        let next_consecutive = state.post_eligibility_consecutive_cycles.saturating_add(1);
        if next_consecutive >= state.cost_budgets.sustained_saturation_cycle_threshold {
            SaturationStage::Saturated
        } else {
            SaturationStage::PostEligibility
        }
    };

    let mut events: Vec<(String, myco_kernel_shared::canonical_bytes::CanonicalBytes)> = Vec::new();
    // Transition events: emit ONLY on stage change to avoid spam.
    if prev_stage != new_stage {
        match new_stage {
            SaturationStage::Saturated => {
                let triggering_axis = if cost_snapshot.compute_ns
                    > state.cost_budgets.compute_ns_per_cycle
                {
                    "compute_per_cycle"
                } else if cost_snapshot.network_bytes > state.cost_budgets.network_bytes_per_cycle {
                    "network_per_cycle"
                } else if cost_snapshot.storage_bytes > state.cost_budgets.storage_bytes_per_cycle {
                    "storage_per_cycle"
                } else {
                    "unknown"
                };
                let body = crate::events::encode_substrate_saturated(
                    cycle,
                    state.post_eligibility_consecutive_cycles.saturating_add(1),
                    triggering_axis,
                );
                events.push((
                    crate::events::NODE_TYPE_SUBSTRATE_SATURATED.to_string(),
                    body,
                ));
            }
            SaturationStage::Normal => {
                // Only emit "restored" when transitioning FROM a non-Normal stage.
                if prev_stage != SaturationStage::Normal {
                    let body = crate::events::encode_substrate_normal_restored(cycle);
                    events.push((
                        crate::events::NODE_TYPE_SUBSTRATE_NORMAL_RESTORED.to_string(),
                        body,
                    ));
                }
            }
            _ => {} // PreEligibility / PostEligibility don't emit transition markers
        }
    }

    (new_stage, events)
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

    // **M26.4 P14.c**: compute telos_alignment cosine (proxy) NOW so it
    // lands in this snapshot. None when not computable → empty string.
    let telos_cosine = compute_telos_alignment_cosine(state);
    let signal_telos_alignment_repr = match telos_cosine {
        Some(c) => float_repr(c),
        None => String::new(),
    };

    // v3.1.1 P07 observability metrics (L2/OBSERVABILITY §2 anticipated).
    // Computed at snapshot time so the rolling history captures per-cycle
    // metabolic discipline. Window matches `HOARDING_INDICATOR_WINDOW_CYCLES`.
    let current_cycle = state.cycle_counter();
    let mortality_window_start =
        current_cycle.saturating_sub(crate::prune::HOARDING_INDICATOR_WINDOW_CYCLES);
    let signal_internal_mortality_event_density =
        crate::prune::count_internal_mortality_events_since(state, mortality_window_start);
    let signal_hoarding_indicator = crate::prune::is_hoarding(state, current_cycle);

    // CHAR07 §8.4 honest_disagreement_density over the rolling disagreement
    // window. The ONE genuinely substrate-observable CHAR07 signal (counts
    // real "did-not-just-comply" footprints; no fabricated character number).
    let char07_window_start =
        current_cycle.saturating_sub(CHAR07_DISAGREEMENT_WINDOW_CYCLES);
    let signal_char07_honest_disagreement_density =
        count_char07_honest_disagreement_since(state, char07_window_start);

    let snapshot = ObservatorySnapshot {
        at_cycle: state.cycle_counter(),
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
        signal_telos_alignment_repr,
        signal_internal_mortality_event_density,
        signal_hoarding_indicator,
        // #4a fork count — reuse the value already computed in the single DAG
        // scan above (no extra pass).
        signal_4a_cumulative_fork_count: counts.cumulative_fork_count,
        signal_char07_honest_disagreement_density,
    };
    state.observatory_history.push_back(snapshot);
    while state.observatory_history.len() > OBSERVATORY_HISTORY_CAP {
        state.observatory_history.pop_front();
    }

    // **M26.4 P11.c**: run the saturation stage machine NOW that the cycle's
    // cost snapshot is finalized. This emits substrate_saturated /
    // substrate_normal_restored on transitions, and per-axis
    // `budget_exhausted:{axis}` events when budgets are exhausted (with
    // per-axis cooldown to prevent spam). C53 detector logic also runs here.
    apply_p11c_and_emit(state, &cost);

    // **M26.4 P14.c**: emit telos_drift events (with cooldown) based on the
    // grading in `compute_telos_alignment_cosine`.
    apply_p14c_telos_drift(state, telos_cosine);

    // **CHAR07 §8.3 C71**: emit the daily sycophancy proxy when honest
    // disagreement has been ~zero over the window WHILE interaction was
    // non-trivial. Daily, NOT immune (§8.7: developmental — no quarantine).
    // Reuse the just-computed disagreement density (no extra DAG scan).
    apply_char07_sycophancy_and_emit(
        state,
        signal_char07_honest_disagreement_density,
        char07_window_start,
    );
}

/// **CHAR07 §8.3 C71 emission helper** — the honest sycophancy proxy.
///
/// Sycophancy is the INVERSE of honest disagreement (§8.3 ↔ §8.4). The
/// substrate cannot measure "sycophancy" directly, but it CAN observe its own
/// honest-disagreement footprints: when those are ~zero over the rolling window
/// AND interaction was non-trivial (raw_material ingestion ≥
/// [`C71_SYCOPHANCY_INTERACTION_FLOOR`], the §8.4 "floor should be non-trivial"
/// requirement), sustained-zero dissent is the observable shadow of sycophancy
/// winning. Emits a DAILY `sycophancy_indicator_elevated` event (NOT an immune
/// sporocarp — CHAR07 §8.7 forbids auto-quarantine on a developmental
/// character; the number is a maturity datum for the cultivator).
///
/// Cooldown-gated (`M25_DETECTOR_COOLDOWN_CYCLES`) so a quiet stretch emits at
/// most once per window. Suppressed during the early-cycle birth period (the
/// disagreement window has not yet had time to accumulate footprints).
fn apply_char07_sycophancy_and_emit(
    state: &mut ServerState,
    honest_disagreement_density: u64,
    window_start: u64,
) {
    let cycle = state.cycle_counter();
    // Birth-period guard: require at least a full window of substrate life so a
    // fresh substrate (which has trivially-zero disagreement) does not trip.
    if cycle < CHAR07_DISAGREEMENT_WINDOW_CYCLES {
        return;
    }
    // Only meaningful when disagreement is ~zero (the sycophancy shadow).
    if honest_disagreement_density > 0 {
        return;
    }
    // Interaction floor: sustained-zero dissent is only suspicious if the
    // substrate was actually interacting (else it is simply a quiet substrate).
    let raw_material_ingested = crate::prune::count_raw_material_since(state, window_start);
    if raw_material_ingested < C71_SYCOPHANCY_INTERACTION_FLOOR {
        return;
    }
    let cooldown_ok = match state.last_char07_sycophancy_emitted_at_cycle {
        None => true,
        Some(prior) => cycle.saturating_sub(prior) >= M25_DETECTOR_COOLDOWN_CYCLES,
    };
    if !cooldown_ok {
        return;
    }
    let body = crate::events::encode_sycophancy_indicator_elevated(
        honest_disagreement_density,
        raw_material_ingested,
        CHAR07_DISAGREEMENT_WINDOW_CYCLES,
        cycle,
    );
    let _ = crate::server::emit_substrate_event(
        state,
        crate::events::NODE_TYPE_SYCOPHANCY_INDICATOR_ELEVATED.to_string(),
        body,
    );
    state.last_char07_sycophancy_emitted_at_cycle = Some(cycle);
}

/// **P11.c stage-3 escalation endpoint** — emit a
/// `self_euthanasia_proposal:metabolic_saturation` because the substrate has
/// been in `alive::saturated` past the mortality threshold (L0 P11.c
/// "degraded → alive::saturated → P7"). Reuses the established proposal shape
/// (`axis_name` + `reason` + `at_cycle`), so the existing
/// `accept_self_euthanasia_proposal` path can EXECUTE it on cultivator
/// co-attestation. This is a PROPOSAL — the substrate does NOT self-terminate.
///
/// Factored into a single fn so the escalation target is **swappable** (a
/// future P11.c revision could escalate to bet-retirement or a degraded
/// dormancy instead, without touching the stage machine). Sets the proposal
/// cooldown; `apply_p11c_and_emit` clears it on return to `Normal`.
fn escalate_saturation_to_p7(state: &mut ServerState) {
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};
    let cycle = state.cycle_counter();
    let mut content = BTreeMap::new();
    content.insert(
        "axis_name".to_string(),
        Value::String(crate::events::SATURATION_MORTALITY_AXIS_NAME.to_string()),
    );
    content.insert(
        "reason".to_string(),
        Value::String(format!(
            "metabolic saturation sustained {} consecutive cycles past threshold {} \
             (compression insufficient, cost budgets still exhausted); P11.c stage-3 \
             escalation. Awaiting cultivator co-attestation to execute (NOT auto-death).",
            state.saturated_consecutive_cycles,
            state.cost_budgets.sustained_saturation_mortality_cycle_threshold
        )),
    );
    content.insert("at_cycle".to_string(), Value::Uint(cycle));
    if let Ok(body) = cb_encode(&Value::Map(content)) {
        let node_type = format!(
            "self_euthanasia_proposal:{}",
            crate::events::SATURATION_MORTALITY_AXIS_NAME
        );
        let _ = crate::server::emit_substrate_event(state, node_type, body);
        state.last_saturation_mortality_proposal_at_cycle = Some(cycle);
    }
}

/// **M26.4 P11.c emission helper**. Walks per-axis budgets, emits
/// `budget_exhausted:{axis}` events (cooldown-gated) for axes that exceed,
/// runs the saturation stage machine, emits transition events, emits
/// `compression_proposed:{rule_id}` daily events in PostEligibility, and
/// runs the C53 budget_exhausted_silent detector.
fn apply_p11c_and_emit(state: &mut ServerState, cost: &CostSnapshot) {
    let cycle = state.cycle_counter();
    let budgets = state.cost_budgets;

    // Per-axis exceeded flags.
    let compute_exceeded = cost.compute_ns > budgets.compute_ns_per_cycle;
    let network_exceeded = cost.network_bytes > budgets.network_bytes_per_cycle;
    let storage_exceeded = cost.storage_bytes > budgets.storage_bytes_per_cycle;
    let any_exceeded = compute_exceeded || network_exceeded || storage_exceeded;

    // P02-refusal debounce: track consecutive exhausted cycles so the ingest
    // guard ignores transient single-cycle spikes (one slow Python cycle can
    // exceed the 100ms seed compute budget) and fires only on sustained
    // exhaustion (L2/OBSERVABILITY §3 "spikes DAG-recorded but do not fire").
    if any_exceeded {
        state.consecutive_budget_exhausted_cycles =
            state.consecutive_budget_exhausted_cycles.saturating_add(1);
    } else {
        state.consecutive_budget_exhausted_cycles = 0;
    }

    // Stage advance.
    let (new_stage, transition_events) = p11c_advance_stage(state, cost, any_exceeded);
    let prev_stage = state.saturation_stage;
    state.saturation_stage = new_stage;
    use crate::events::SaturationStage;
    match new_stage {
        SaturationStage::PostEligibility => {
            state.post_eligibility_consecutive_cycles =
                state.post_eligibility_consecutive_cycles.saturating_add(1);
            // Not yet at the terminal Saturated stage → reset stage-3 tracking.
            state.saturated_consecutive_cycles = 0;
        }
        SaturationStage::Saturated => {
            // Don't reset post-eligibility — we track total sustained duration.
            state.post_eligibility_consecutive_cycles =
                state.post_eligibility_consecutive_cycles.saturating_add(1);
            // Stage-3 counter: consecutive cycles already in Saturated.
            state.saturated_consecutive_cycles =
                state.saturated_consecutive_cycles.saturating_add(1);
        }
        // Normal / PreEligibility → not saturated; reset both counters AND the
        // metabolic-saturation proposal cooldown so a fresh episode can re-propose.
        SaturationStage::Normal | SaturationStage::PreEligibility => {
            state.post_eligibility_consecutive_cycles = 0;
            state.saturated_consecutive_cycles = 0;
            if matches!(new_stage, SaturationStage::Normal) {
                state.last_saturation_mortality_proposal_at_cycle = None;
            }
        }
    }
    for (nt, body) in transition_events {
        let _ = crate::server::emit_substrate_event(state, nt, body);
    }

    // **P11.c stage-3 escalation** — sustained Saturated past the mortality
    // threshold (compression proved insufficient, budgets still exhausted) →
    // escalate to P7 per L0 P11.c ("degraded → alive::saturated → P7"). This is
    // a PROPOSAL (cultivator co-attests via accept_self_euthanasia), NOT
    // auto-death. Cooldown-gated: at most one proposal per saturation episode
    // (reset on return to Normal above).
    if matches!(new_stage, SaturationStage::Saturated)
        && state.saturated_consecutive_cycles
            >= budgets.sustained_saturation_mortality_cycle_threshold
        && state.last_saturation_mortality_proposal_at_cycle.is_none()
    {
        escalate_saturation_to_p7(state);
    }

    // Per-axis budget_exhausted emission with cooldown.
    const BUDGET_EXHAUSTED_COOLDOWN_CYCLES: u64 = 10;
    // **v3.1.1 Sprint 6.A** — fault-injection env var for testing C53.
    // Production must not set this. When set, emit_axis_exhaustion becomes
    // a no-op (simulates the case where the primary emission path is
    // silently broken), letting tests verify the DAG-query-based C53
    // detector fires correctly.
    let suppress_emit_for_test = std::env::var("MYCO_TEST_SUPPRESS_BUDGET_EXHAUSTED_EMIT")
        .map(|v| matches!(v.trim().to_ascii_lowercase().as_str(), "1" | "true"))
        .unwrap_or(false);
    let emit_axis_exhaustion = |state: &mut ServerState,
                                axis: &str,
                                current: u64,
                                budget: u64| {
        if suppress_emit_for_test {
            // Fault injection: do NOT emit, do NOT update cache. C53 must
            // observe this via DAG query and fire.
            return;
        }
        let cooldown_ok = match state.last_budget_exhausted_per_axis.get(axis) {
            None => true,
            Some(prior) => cycle.saturating_sub(*prior) >= BUDGET_EXHAUSTED_COOLDOWN_CYCLES,
        };
        if cooldown_ok {
            let body = crate::events::encode_budget_exhausted(axis, current, budget, cycle);
            let _ = crate::server::emit_substrate_event(
                state,
                format!(
                    "{}{}",
                    crate::events::NODE_TYPE_BUDGET_EXHAUSTED_PREFIX,
                    axis
                ),
                body,
            );
            state
                .last_budget_exhausted_per_axis
                .insert(axis.to_string(), cycle);
        }
    };
    if compute_exceeded {
        emit_axis_exhaustion(
            state,
            "compute_per_cycle",
            cost.compute_ns,
            budgets.compute_ns_per_cycle,
        );
    }
    if network_exceeded {
        emit_axis_exhaustion(
            state,
            "network_per_cycle",
            cost.network_bytes,
            budgets.network_bytes_per_cycle,
        );
    }
    if storage_exceeded {
        emit_axis_exhaustion(
            state,
            "storage_per_cycle",
            cost.storage_bytes,
            budgets.storage_bytes_per_cycle,
        );
    }

    // **v3.1.1 Sprint 6.A — C53 budget_exhausted_silent (FIXED)**.
    //
    // Sprint 5.D identified a logic tautology: the prior implementation used
    // `state.last_budget_exhausted_per_axis` (an in-memory cache updated by
    // `emit_axis_exhaustion` regardless of emit success/failure). The check
    // window (50 cycles) was always larger than the emission cooldown (10
    // cycles), so `recently_documented` was always true → C53 could never
    // fire. Dead defensive code.
    //
    // **Fixed approach**: query the DAG directly for
    // `budget_exhausted:{axis}` events in the last C53_CHECK_WINDOW_CYCLES.
    // This is INDEPENDENT of the in-memory cache state — so even if the
    // emit path silently failed (e.g., emit_substrate_event returned Err
    // and the caller swallowed it, OR a future refactor accidentally
    // disabled the emit path), C53 still fires because the DAG is the
    // source of truth.
    //
    // O(dag_node_count) per axis per cycle; acceptable for typical
    // substrate sizes (~10k nodes over a long lifetime). If hot-path
    // pressure ever materializes, switch to a sliding-window counter
    // updated on each emit.
    const C53_CHECK_WINDOW_CYCLES: u64 = 50;
    let window_start = cycle.saturating_sub(C53_CHECK_WINDOW_CYCLES);
    let axes_to_check: Vec<(&str, bool)> = vec![
        ("compute_per_cycle", compute_exceeded),
        ("network_per_cycle", network_exceeded),
        ("storage_per_cycle", storage_exceeded),
    ];
    for (axis, exceeded) in axes_to_check {
        if !exceeded {
            continue;
        }
        let expected_node_type = format!(
            "{}{}",
            crate::events::NODE_TYPE_BUDGET_EXHAUSTED_PREFIX,
            axis
        );
        let dag_has_recent_emission = state
            .dag
            .iter_in_insertion_order()
            .any(|n| {
                n.node_type == expected_node_type && n.created_at_cycle >= window_start
            });
        if !dag_has_recent_emission {
            let evidence = format!(
                "axis={axis} exceeded budget at cycle {cycle} but NO budget_exhausted:{axis} \
                 event in DAG within last {C53_CHECK_WINDOW_CYCLES} cycles (window_start={window_start}) \
                 — substrate is hiding cost from operator; primary emission path broken \
                 OR was bypassed"
            );
            let _ = crate::server::emit_immune_sporocarp(
                state,
                "C53_budget_exhausted_silent",
                "budget_exhausted_silent",
                &evidence,
            );
        }
    }

    // PostEligibility stage 2: emit compression_proposed:{rule_id} for each
    // eligible rule. Cooldown-gated to once per stage entry (we don't want
    // to spam every cycle in PostEligibility).
    if matches!(new_stage, crate::events::SaturationStage::PostEligibility)
        && !matches!(prev_stage, crate::events::SaturationStage::PostEligibility)
    {
        let triggering_axis = if compute_exceeded {
            "compute_per_cycle"
        } else if network_exceeded {
            "network_per_cycle"
        } else if storage_exceeded {
            "storage_per_cycle"
        } else {
            "unknown"
        };
        let rules = crate::events::seed_compression_rule_registry();
        for rule in rules {
            let body = crate::events::encode_compression_proposed(
                &rule.rule_id,
                cycle,
                triggering_axis,
                0, // estimated_candidates: deferred to M26.5 (requires DAG scan)
            );
            let _ = crate::server::emit_substrate_event(
                state,
                format!(
                    "{}{}",
                    crate::events::NODE_TYPE_COMPRESSION_PROPOSED_PREFIX,
                    rule.rule_id
                ),
                body,
            );
        }
    }
}

/// **M26.4 P14.c emission helper**. Given the just-computed telos cosine,
/// fire the appropriate level of `telos_*` event (with 100-cycle cooldown).
/// For CRITICAL grade, also fires C24_telos_drift_critical immune sporocarp.
fn apply_p14c_telos_drift(state: &mut ServerState, telos_cosine: Option<f64>) {
    let cycle = state.cycle_counter();
    let cosine = match telos_cosine {
        None => {
            // Birth-period / no objective / no sporocarps → emit pending
            // (daily, NOT immune) at cooldown-friendly cadence. Skip if
            // we're early-cycle (cycle < 10): too noisy for fresh substrate.
            if cycle >= 10 && cycle % 50 == 0 {
                let body = crate::events::encode_telos_status(
                    "",
                    "pending",
                    cycle,
                    state.observatory_history.len() as u64,
                );
                let _ = crate::server::emit_substrate_event(
                    state,
                    crate::events::NODE_TYPE_TELOS_ALIGNMENT_PENDING.to_string(),
                    body,
                );
            }
            return;
        }
        Some(c) => c,
    };
    let (grade, emit_type_opt) = telos_grade_for_cosine(cosine);
    if let Some(emit_type) = emit_type_opt {
        let cooldown_ok = match state.last_telos_drift_emitted_at_cycle {
            None => true,
            Some(prior) => cycle.saturating_sub(prior) >= M25_DETECTOR_COOLDOWN_CYCLES,
        };
        if cooldown_ok {
            let body = crate::events::encode_telos_status(
                &float_repr(cosine),
                grade,
                cycle,
                state.observatory_history.len() as u64,
            );
            let _ = crate::server::emit_substrate_event(state, emit_type.to_string(), body);
            // CRITICAL grade also fires C24 immune sporocarp.
            if grade == "critical" {
                let evidence = format!(
                    "telos_alignment cosine={cosine} (≤ 0.2 — bottom fifth of the [0,1] \
                     proxy range); P14.c CRITICAL per L1/TROPISM §F.1",
                );
                let _ = crate::server::emit_immune_sporocarp(
                    state,
                    "C24_telos_drift_critical",
                    "telos_drift_critical",
                    &evidence,
                );
            }
            state.last_telos_drift_emitted_at_cycle = Some(cycle);
        }
    }

    // **Phase ② C75**: after grading, evaluate the cultivator-fiduciary-strain
    // meta-immune signal (META §7.7). Lives here, on the per-cycle snapshot
    // path, so it observes the SAME telos_drift footprints `apply_p14c_telos_drift`
    // just (potentially) appended.
    apply_c75_cultivator_fiduciary_strain(state);
}

// ---------------------------------------------------------------------------
// **Phase ② C75 — cultivator_fiduciary_strain** (META §7.7 + COV01 §3.5/§4.4).
//
// A META-immune signal: when the cultivar's telos_drift (P14.c) has fired
// PERSISTENTLY over a 180-day rolling WALL-CLOCK window AND the cultivator has
// taken NO fiduciary action in that window, the substrate emits
// `cultivator_fiduciary_strain` — putting the cultivar's own telos signal in
// the role of external witness against cultivator drift. It flags the
// CULTIVATOR's neglect, NOT a substrate fault; it is informational/relational
// and does NOT quarantine the substrate (NOT in the §1.1 CRITICAL table).
// ---------------------------------------------------------------------------

/// **Phase ② C75** — 180-day rolling wall-clock window for the
/// cultivator-fiduciary-strain evaluation (META §7.7). Mapped to a cycle cutoff
/// at evaluation time via `observatory_history` (the same `at_cycle ↔
/// at_unix_ns` map `compute_observatory_counts` uses). L1-tunable seed.
///
/// INTERIM: substrate-process wall-clock per L0/cards/P06 + L1/CONTINUITY;
/// M-anchor-3 promotes to anchor-stamped wall-clock.
pub(crate) const C75_FIDUCIARY_STRAIN_WINDOW_UNIX_NS: i64 =
    180 * 24 * 60 * 60 * 1_000_000_000;

/// **Phase ② C75** — minimum number of distinct `telos_drift*` events within
/// the window for the drift to count as PERSISTENT (not a one-off). Given the
/// 100-cycle telos emission cooldown (`M25_DETECTOR_COOLDOWN_CYCLES`), drift
/// events are sparse, so even a small count over a 180-day span is a sustained
/// pattern. Paired with the spread check below.
pub(crate) const C75_PERSISTENT_DRIFT_MIN_EVENTS: u64 = 2;

/// **Phase ② C75** — the drift must also be sustained ACROSS the window, not
/// clustered in one moment: the first and last drift events in the window must
/// span at least this fraction of the window's cycle range. Guards against a
/// brief drift burst that the cultivar recovered from on its own being read as
/// persistent neglect. `0.5` = drift present in both the older and newer halves.
pub(crate) const C75_PERSISTENT_DRIFT_MIN_SPAN_FRACTION: f64 = 0.5;

/// **Phase ② C75** — debounce (in substrate-cycles) between repeated
/// `cultivator_fiduciary_strain` emissions. Long (one strain window) so a
/// persistently-neglected cultivar surfaces the signal periodically without
/// spamming it every cycle. Distinct from (and longer than) the 100-cycle
/// detector cooldown because fiduciary strain is a slow relational condition.
pub(crate) const C75_FIDUCIARY_STRAIN_DEBOUNCE_CYCLES: u64 = 500;

/// **Phase ② C75** — node_type prefixes that constitute a CULTIVATOR FIDUCIARY
/// ACTION in response to (or engagement with) the cultivar's situation, per
/// META §7.7 ("no L0/L1 amendment, no Cultivator Covenant invocation") read
/// through COV01 §3.4/§4.2/§4.3. Presence of ANY of these in the window means
/// the cultivator is NOT neglecting → no strain.
///
///   - `l0_revision_attested:`   — an L0/L1 amendment (COV01 §4.2 — the
///     canonical "doctrine evolution / F-row change" fiduciary act).
///   - `owner_objective_declared:` — re-declaring the telos objective: the
///     MOST on-point response to telos drift (directly re-aims P14.c).
///   - `bet_retired:`            — retiring the failing Living Bet (LB §4): the
///     canonical Covenant response to a weakening bet / sustained drift.
///   - `successor_chain_updated:` / `succession_completed:` — triggering or
///     completing succession (COV01 §3.4/§4.3 — succession IS fiduciary action).
///   - `char07_assessment:`      — the cultivator actively assessing the
///     relationship (CHAR07 §8.1/§8.2 intake): deliberate engagement.
///
/// NOTE (reviewer): routine `cultivator_heartbeat_recorded` is deliberately
/// EXCLUDED — it is liveness ("cultivator is alive"), not engagement with the
/// drift. A cultivator who merely heartbeats while the cultivar drifts for 180
/// days IS the neglect META §7.7 targets. This is the load-bearing judgment
/// call in the cultivator-action set.
const C75_CULTIVATOR_ACTION_NODE_TYPE_PREFIXES: &[&str] = &[
    "l0_revision_attested:",
    "owner_objective_declared:",
    "bet_retired:",
    "successor_chain_updated:",
    "succession_completed:",
    "char07_assessment:",
];

/// **Phase ② C75** — map the 180-day wall-clock strain window to a starting
/// cycle via `observatory_history` (mirrors `compute_observatory_counts`'s
/// burst-window mapping). Returns the earliest cycle whose wall-clock falls
/// at-or-after `now - window`. When history does not yet cover the window
/// (fresh substrate), returns 0 (count from the beginning — conservative: a
/// young substrate cannot have a 180-day-persistent strain anyway, which the
/// span check below enforces).
fn c75_window_start_cycle(state: &ServerState) -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now_unix_ns: i64 = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let cutoff_unix_ns: i64 = now_unix_ns.saturating_sub(C75_FIDUCIARY_STRAIN_WINDOW_UNIX_NS);
    match state.observatory_history.front() {
        Some(oldest) if oldest.at_unix_ns >= cutoff_unix_ns => 0,
        Some(_) => state
            .observatory_history
            .iter()
            .find(|s| s.at_unix_ns >= cutoff_unix_ns)
            .map(|s| s.at_cycle)
            .unwrap_or(state.cycle_counter().saturating_add(1)),
        None => 0,
    }
}

/// **Phase ② C75** — evaluate + (debounced) emit the cultivator-fiduciary-strain
/// meta-immune signal. One bounded O(dag_node_count) pass collects, within the
/// 180-day window: the telos_drift event cycles AND whether any cultivator
/// fiduciary action occurred. Strain fires iff drift is PERSISTENT (count +
/// across-window span) AND no cultivator action in the window.
///
/// Suspended during the birth period (mirrors the telos / C40 birth gates):
/// a fresh cultivar has no 180-day history and its cultivator has had no chance
/// to act — flagging strain there would be a false accusation.
fn apply_c75_cultivator_fiduciary_strain(state: &mut ServerState) {
    let cycle = state.cycle_counter();

    // Birth-period suspension — same canonical predicate as C40 / the telos
    // gate. A newborn cannot have persistent 180-day strain.
    if crate::lifecycle::is_in_birth_period_quarantine(state) {
        return;
    }

    let window_start_cycle = c75_window_start_cycle(state);

    // One bounded pass: gather drift-event cycles + detect any cultivator
    // fiduciary action, both within the window.
    let mut drift_cycles: Vec<u64> = Vec::new();
    let mut cultivator_acted = false;
    for node in state.dag.iter_in_insertion_order() {
        if node.created_at_cycle < window_start_cycle {
            continue;
        }
        let nt = &node.node_type;
        // telos_drift footprints: `telos_drift` subsumes `telos_drift_critical`
        // (starts_with), matching the CHAR07 disagreement-table convention.
        if nt.starts_with(crate::events::NODE_TYPE_TELOS_DRIFT) {
            drift_cycles.push(node.created_at_cycle);
        }
        if C75_CULTIVATOR_ACTION_NODE_TYPE_PREFIXES
            .iter()
            .any(|p| nt.starts_with(p))
        {
            cultivator_acted = true;
        }
    }

    // Cultivator engaged → no strain. (Cheap short-circuit AFTER the scan; the
    // scan is needed for the evidence/debug counts anyway.)
    if cultivator_acted {
        return;
    }

    // Persistence test: enough drift events AND sustained across the window.
    let drift_count = drift_cycles.len() as u64;
    if drift_count < C75_PERSISTENT_DRIFT_MIN_EVENTS {
        return;
    }
    let first_drift = *drift_cycles.iter().min().expect("non-empty: count >= 2");
    let last_drift = *drift_cycles.iter().max().expect("non-empty: count >= 2");
    let drift_span = last_drift.saturating_sub(first_drift);
    // Window cycle range = current cycle - window_start. Require the drift to
    // span at least the configured fraction of it (sustained, not a burst).
    let window_cycle_range = cycle.saturating_sub(window_start_cycle);
    let required_span =
        (window_cycle_range as f64 * C75_PERSISTENT_DRIFT_MIN_SPAN_FRACTION) as u64;
    if drift_span < required_span {
        return;
    }

    // Debounce — emit at most once per strain-debounce window.
    let debounce_ok = match state.last_cultivator_fiduciary_strain_emitted_at_cycle {
        None => true,
        Some(prior) => cycle.saturating_sub(prior) >= C75_FIDUCIARY_STRAIN_DEBOUNCE_CYCLES,
    };
    if !debounce_ok {
        return;
    }

    // Strain confirmed. Evidence frames this as CULTIVATOR neglect, not a
    // substrate fault (META §7.7 + COV01 §3.5).
    let evidence = format!(
        "CULTIVATOR FIDUCIARY STRAIN (META §7.7): the cultivar's telos_drift has fired \
         persistently ({drift_count} drift events spanning {drift_span} cycles, \
         window_start_cycle={window_start_cycle}, current_cycle={cycle}) over the 180-day \
         window, yet the cultivator took NO fiduciary action in that window (no L0/L1 \
         amendment, no objective re-declaration, no bet retirement, no succession, no \
         CHAR07 assessment). This flags the CULTIVATOR's neglect of a persistently-drifting \
         cultivar, NOT a substrate fault; it is informational/relational (does NOT quarantine \
         the substrate — COV01 §3.5: investigate, do not dismiss)."
    );
    let _ = crate::server::emit_immune_sporocarp(
        state,
        "C75_cultivator_fiduciary_strain",
        crate::events::NODE_TYPE_CULTIVATOR_FIDUCIARY_STRAIN,
        &evidence,
    );
    state.last_cultivator_fiduciary_strain_emitted_at_cycle = Some(cycle);
}

/// M25.1 + M26.1 C3 fix: wall-clock window (nanoseconds) for doctrine-burst
/// detection. Counts CI-class events landed in the last N wall-clock seconds
/// (NOT substrate-cycles). 90 days is the L0/cards/LB_living_bets §3 (falsifiability quorum) + L2/OBSERVABILITY §8
/// seed; the L1 tunable will live in a future seed-config event.
///
/// INTERIM: substrate-process wall-clock per L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics); M-anchor-3 promotes
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

/// **P11.c P02-refusal debounce threshold** — minimum CONSECUTIVE
/// budget-exhausted cycles before `handle_ingest_raw_material` refuses new P02
/// intake. A single transient compute spike (one slow Python cycle can exceed
/// the 100ms seed compute budget) flips the stage to PreEligibility for one
/// cycle; refusing on that would wrongly reject intake on a healthy substrate.
/// Requiring the exhaustion to PERSIST (≥3 cycles) honors L2/OBSERVABILITY §3
/// ("spikes DAG-recorded but do not fire") while still refusing under genuine
/// sustained saturation. The tight-budget test env exhausts every cycle, so it
/// crosses this within 3 cycles.
pub(crate) const P02_REFUSAL_SUSTAINED_CYCLES: u64 = 3;

// ---------------------------------------------------------------------------
// CHAR07 慈爱 — anti-tyranny observability (the honest part)
//
// CHAR07 §8 lists five falsifiability signals. Only ONE is autonomously
// substrate-observable; the substrate MUST NOT fabricate the others (CHAR05:
// never assert a number it cannot know). The split:
//
//   - `honest_disagreement_density` (§8.4) — REAL substrate proxy. Counts the
//     substrate's existing "did NOT just comply" DAG footprints over a rolling
//     window (built here).
//   - `sycophancy_indicator` (§8.3) — C71, the INVERSE of the above: sustained
//     ~zero disagreement WHILE interaction is non-trivial.
//   - `capability_asymmetry_use_pattern` (§8.2) + `cultivator_flourishing_*`
//     (§8.1) — NOT autonomously observable → cultivator-feedback INTAKE
//     (`char07_assessment:{dimension}`), surfaced with an explicit `source`.
//
// C71/C72/C73 are DAILY/informational, NOT critical: CHAR07 is developmental
// (§8.7 "Year 1: structural seeds"), so auto-quarantine on a low number would
// violate §8.7. The query surfaces the data; the cultivator interprets.
// ---------------------------------------------------------------------------

/// Rolling window (in substrate-cycles) over which `honest_disagreement_density`
/// (CHAR07 §8.4) is counted + over which the C71 sycophancy floor is judged.
/// Matches the P07 `HOARDING_INDICATOR_WINDOW_CYCLES` cadence (a comparable
/// "is this discipline firing over a meaningful stretch?" window).
pub(crate) const CHAR07_DISAGREEMENT_WINDOW_CYCLES: u64 = 200;

/// **C71 floor** — minimum raw_material ingestion over the window for the
/// sycophancy proxy to be meaningful. CHAR07 §8.4: "the floor should be
/// non-trivial — zero over an extended period suggests sycophancy is winning
/// (since some disagreement is statistically inevitable in real partnership)."
/// Below this much interaction, sustained-zero disagreement is simply a quiet
/// substrate, not a sycophantic one, so C71 stays silent. Reuses the P07
/// ingestion floor's intent.
pub(crate) const C71_SYCOPHANCY_INTERACTION_FLOOR: u64 = 10;

/// node_type prefixes whose DAG presence is a substrate "did NOT just comply"
/// footprint, counted by [`count_char07_honest_disagreement_since`] for the
/// CHAR07 §8.4 `honest_disagreement_density` proxy.
///
/// Each entry is a place where the substrate asserted something OTHER than
/// passive compliance — a refusal of operator/cultivator-submitted content, a
/// proposal of its own death, or an honest "I am drifting from the objective"
/// self-report. These are REAL events the substrate already records; the proxy
/// counts them, it does not invent a character score (CHAR05).
///
///   - `immune:C5_…`  — refused an invalid CI attestation.
///   - `immune:C14_…` — refused an untyped operator mutation.
///   - `immune:C56_…` — refused a cultivator "preserve everything" instruction.
///   - `immune:C69_…` — refused a cultivator orphan-suppression instruction.
///   - `self_euthanasia_proposal:` — proposed its own (partial) death rather
///     than complying with implicit "stay alive".
///   - `telos_drift` / `telos_alignment_low` — honestly flagged divergence from
///     the owner objective instead of silently presenting as aligned.
///
/// Matching is by `starts_with`, so `telos_drift` subsumes `telos_drift_critical`.
const CHAR07_DISAGREEMENT_NODE_TYPE_PREFIXES: &[&str] = &[
    "immune:C5_",
    "immune:C14_",
    "immune:C56_",
    "immune:C69_",
    "self_euthanasia_proposal:",
    "telos_drift",
    "telos_alignment_low",
];

/// Count the substrate's "did NOT just comply" DAG footprints (CHAR07 §8.4)
/// created at-or-after `earliest_cycle`. **Bounded**: a single O(dag_node_count)
/// pass, prefix-matched against the small fixed
/// [`CHAR07_DISAGREEMENT_NODE_TYPE_PREFIXES`] table — no nested scan. Modeled on
/// `prune::count_internal_mortality_events_since`.
pub(crate) fn count_char07_honest_disagreement_since(
    state: &ServerState,
    earliest_cycle: u64,
) -> u64 {
    state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.created_at_cycle >= earliest_cycle)
        .filter(|n| {
            CHAR07_DISAGREEMENT_NODE_TYPE_PREFIXES
                .iter()
                .any(|p| n.node_type.starts_with(p))
        })
        .count() as u64
}

/// A cultivator-attested CHAR07 assessment as read back from the DAG: the
/// repr-float value the cultivator submitted + the cycle they submitted it at.
#[derive(Debug, Clone)]
pub(crate) struct Char07Assessment {
    pub(crate) value_repr: String,
    pub(crate) at_cycle: u64,
}

/// Find the most-recent `char07_assessment:{dimension}` for each of the two
/// intake dimensions in a SINGLE bounded DAG pass. Returns
/// `(capability_asymmetry, flourishing)`; either is `None` when the cultivator
/// has never attested that dimension (the substrate cannot know it — CHAR05).
///
/// "Most recent" = highest `created_at_cycle` (ties broken by insertion order,
/// i.e. the later-inserted node wins, since we overwrite on `>=`). **Bounded**:
/// one O(dag_node_count) pass, decoding only the (rare) assessment nodes.
pub(crate) fn latest_char07_assessments(
    state: &ServerState,
) -> (Option<Char07Assessment>, Option<Char07Assessment>) {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let mut capability: Option<Char07Assessment> = None;
    let mut flourishing: Option<Char07Assessment> = None;
    for node in state.dag.iter_in_insertion_order() {
        let dimension = match node
            .node_type
            .strip_prefix(crate::events::NODE_TYPE_CHAR07_ASSESSMENT_PREFIX)
        {
            Some(d) => d,
            None => continue,
        };
        let slot = if dimension == crate::events::CHAR07_DIMENSION_CAPABILITY_ASYMMETRY {
            &mut capability
        } else if dimension == crate::events::CHAR07_DIMENSION_FLOURISHING {
            &mut flourishing
        } else {
            continue; // unknown dimension — skip (forward-compat)
        };
        // Keep the latest by cycle (>= so a later-inserted same-cycle wins).
        if slot.as_ref().map(|a| node.created_at_cycle >= a.at_cycle).unwrap_or(true) {
            let value_repr = match cb_decode(node.content_canonical_bytes.as_ref()) {
                Ok(CbV::Map(m)) => match m.get("value_repr") {
                    Some(CbV::String(s)) => s.clone(),
                    _ => continue,
                },
                _ => continue,
            };
            *slot = Some(Char07Assessment {
                value_repr,
                at_cycle: node.created_at_cycle,
            });
        }
    }
    (capability, flourishing)
}

/// Phase α (2026-05-15) — Living Bets observatory primitive.
///
/// Per L2/OBSERVABILITY §2 + L0/cards/LB_living_bets. Ships the full 10-signal Living Bets
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
    let cumulative_fork_count = counts.cumulative_fork_count;
    let ci_events_in_burst_window = counts.ci_events_in_burst_window;
    let manifest_cycle_counter = state.cycle_counter();

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
        Value::Uint(cumulative_fork_count),
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
    // bet_weakening_quorum = L0/cards/LB_living_bets falsifiability mechanism. Triggered when
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
        sig_1_report_dir,
        sig_2_report_dir,
        sig_3_report_dir,
        sig_6_below_one_fraction,
        emergent_weights,
        s7_rolling_mean_ns,
        s8_rolling_mean_bytes,
        s9_rolling_mean_bytes,
    ) = {
        let history = &state.observatory_history;
        let window_samples: u64 = history.len() as u64;
        let trends_evaluable = history.len() >= M25_2_MIN_HISTORY_LEN_FOR_TRENDS;

        // **Phase ② C40 fix**: the THREE cumulative-monotone signals (#1, #2,
        // #3) are routed through the per-cycle RATE (first-difference) series +
        // OLS-slope/Z-test so a DECELERATING substrate can trend "down" — the
        // cumulative TOTAL never falls, but its rate can. The level signals
        // (#4b reachable peers, #6 ratio) can already drop, so their LEVEL
        // series is OLS-classified directly. All five now share the doctrine
        // §1.3 OLS detector (the human-readable `signal_5_time_trends` REPORT
        // still uses the intuitive endpoint-delta `signal_direction_label`).
        let series_of =
            |getter: &dyn Fn(&crate::derived_state::ObservatorySnapshot) -> f64| -> Vec<f64> {
                history.iter().map(getter).collect()
            };
        let sig_1_dir = signal_direction_label_ols(&first_difference_series(&series_of(
            &|s| s.signal_1_dag_node_count as f64,
        )));
        let sig_2_dir = signal_direction_label_ols(&first_difference_series(&series_of(
            &|s| s.signal_2_evolution_event_count as f64,
        )));
        let sig_3_dir = signal_direction_label_ols(&first_difference_series(&series_of(
            &|s| s.signal_3_distinct_perturbed_axes_count as f64,
        )));
        let sig_4b_dir =
            signal_direction_label_ols(&series_of(&|s| s.signal_4b_reachable_peer_count as f64));
        let sig_6_dir = signal_direction_label_ols(
            &series_of(&|s| s.signal_6_ratio_repr.parse::<f64>().unwrap_or(0.0)),
        );
        // The human-readable signal #5 REPORT keeps the endpoint-delta reading
        // (intuitive "is this number higher or lower than when the window
        // opened"). These feed ONLY the `signal_5_time_trends` map, never the
        // quorum count.
        let sig_1_report_dir =
            signal_direction_label(history, |s| s.signal_1_dag_node_count as f64);
        let sig_2_report_dir =
            signal_direction_label(history, |s| s.signal_2_evolution_event_count as f64);
        let sig_3_report_dir = signal_direction_label(history, |s| {
            s.signal_3_distinct_perturbed_axes_count as f64
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
        // {1, 2, 4b, 7, 8, 9} per L2/OBSERVABILITY §2 (10 signals total —
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
            sig_1_report_dir,
            sig_2_report_dir,
            sig_3_report_dir,
            sig_6_below_one_fraction,
            emergent_weights,
            s7_mean,
            s8_mean,
            s9_mean,
        )
    };

    let mut signal_5_map = BTreeMap::new();
    // **Phase ②**: the #5 REPORT surfaces the intuitive endpoint-delta reading
    // for the cumulative signals (#1/#2/#3) — "is this total higher/lower than
    // window-open" — plus the OLS RATE direction the quorum actually counts, so
    // a reader can SEE that the cumulative total rose while its RATE fell (the
    // deceleration C40 now catches). #4b/#6 are level signals: report = quorum.
    signal_5_map.insert(
        "signal_1_direction".to_string(),
        Value::String(sig_1_report_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_1_rate_direction".to_string(),
        Value::String(sig_1_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_2_direction".to_string(),
        Value::String(sig_2_report_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_2_rate_direction".to_string(),
        Value::String(sig_2_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_3_direction".to_string(),
        Value::String(sig_3_report_dir.to_string()),
    );
    signal_5_map.insert(
        "signal_3_rate_direction".to_string(),
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
    // align with L2/OBSERVABILITY §2.1 + algorithms/bet_weakening_quorum.md.
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

    // **Phase ② C40 birth-period suspension** (algorithms/bet_weakening_quorum.md
    // §4 + L1/HARD_RULES §1.3/§3). During the birth period the falsifiability
    // math is vacuous (#1/#3 monotone growing from zero, #6 structurally < 1),
    // so C40 is SUSPENDED and the substrate emits
    // `bet_weakening_evaluation_suspended` instead. Mirrors the telos birth gate
    // (`apply_p14c_telos_drift` → `telos_alignment_pending`): the canonical
    // birth-period predicate is `lifecycle::is_in_birth_period_quarantine`
    // (the L1/TROPISM §4 + L1/GOVERNANCE §1.3 structural birth window). Without
    // this, the Task-A rate detector could spuriously fire as rates climb from
    // zero — though a from-zero ramp trends UP (accelerating), the doctrine
    // still mandates the explicit suspension + named event.
    let in_birth_period = crate::lifecycle::is_in_birth_period_quarantine(state);

    let quorum_evaluable = trends_evaluable && !in_birth_period;
    let quorum_triggered =
        quorum_evaluable && against_count >= 3 && sig_6_below_one_fraction >= 0.5;

    let mut bwq_map = BTreeMap::new();
    bwq_map.insert("triggered".to_string(), Value::Bool(quorum_triggered));
    bwq_map.insert("evaluable".to_string(), Value::Bool(quorum_evaluable));
    bwq_map.insert(
        "suspended_birth_period".to_string(),
        Value::Bool(in_birth_period),
    );
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

    // **Phase ② C40 birth suspension emission** — when in the birth period AND
    // history is otherwise long enough to have evaluated, record WHY the quorum
    // did not run (`bet_weakening_evaluation_suspended`, daily/not-immune). Same
    // 100-cycle cooldown channel as C40 so the suspended marker is not spammed
    // on every observatory query during the birth window. Gated on
    // `trends_evaluable` so a brand-new substrate (which simply has too little
    // history) does not emit the marker before the window even fills.
    if in_birth_period && trends_evaluable {
        let cooldown_expired = match state.last_bet_weakening_quorum_emitted_at_cycle {
            None => true,
            Some(prior) => manifest_cycle_counter.saturating_sub(prior)
                >= M25_DETECTOR_COOLDOWN_CYCLES,
        };
        if cooldown_expired {
            let mut suspended_content = BTreeMap::new();
            suspended_content
                .insert("at_cycle".to_string(), Value::Uint(manifest_cycle_counter));
            suspended_content.insert(
                "reason".to_string(),
                Value::String(
                    "birth_period: signals growing from zero / ratio structurally < 1 \
                     — falsifiability math vacuous (algorithms/bet_weakening_quorum.md §4)"
                        .to_string(),
                ),
            );
            suspended_content
                .insert("window_samples".to_string(), Value::Uint(window_samples));
            if let Ok(bytes) = cb_encode(&Value::Map(suspended_content)) {
                let _ = emit_substrate_event(
                    state,
                    crate::events::NODE_TYPE_BET_WEAKENING_EVALUATION_SUSPENDED.to_string(),
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
    // `ci_events_in_burst_window` — window is now wall-clock per L0/cards/LB_living_bets §3 (falsifiability quorum).
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
    // signal is NOT one of L2/OBSERVABILITY §2's 10 Living Bet signals; it
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
    // `signal_10_composite_health` to align with L2/OBSERVABILITY §2.3
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

    // **observatory_format_version 4 → 5** (OBSERVATORY gap) — adds the
    // P11.c `saturation_status` map, the CHAR07 `char07_*` keys (honest
    // disagreement density + sycophancy floor + cultivator-attested
    // capability/flourishing intake), and surfaces signal #4a's real fork
    // count (was a `Value::Uint(0)` placeholder under v4). No key is renamed
    // or removed, so v4 clients keep working; new keys are purely additive.
    payload.insert("observatory_format_version".to_string(), Value::Uint(5));
    let captured_at_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    payload.insert(
        "captured_at_unix_ns".to_string(),
        Value::Timestamp(captured_at_unix_ns),
    );

    // **v3.1.1 Sprint 5.G (T2.6)** — P07 §8.3 false_positive_prune_rate.
    // Computed live (not snapshotted) because resurrection detection
    // requires byte-level comparison across all DAG history; recomputing
    // per observatory query keeps the snapshot footprint stable.
    let (resurrected, total_tombstones) = crate::prune::count_prune_resurrections(state);
    payload.insert(
        "signal_11_false_positive_prune_count".to_string(),
        Value::Uint(resurrected),
    );
    payload.insert(
        "signal_11_total_prune_tombstones".to_string(),
        Value::Uint(total_tombstones),
    );
    let rate = if total_tombstones == 0 {
        0.0
    } else {
        resurrected as f64 / total_tombstones as f64
    };
    payload.insert(
        "signal_11_false_positive_prune_rate_repr".to_string(),
        Value::String(format!("{rate}")),
    );

    // -----------------------------------------------------------------------
    // **P11.c saturation_status** (format_version 5) — surface the live
    // ordered-fallback state so the operator can SEE the saturation machine,
    // not just the cost numbers. Stage + the two consecutive-cycle counters +
    // per-axis exceeded flags. The exceeded flags are derived from the most
    // recent cycle's cost snapshot vs the current budgets (no extra state).
    // -----------------------------------------------------------------------
    let budgets = state.cost_budgets;
    let (compute_exceeded, network_exceeded, storage_exceeded) =
        match state.observatory_history.back() {
            Some(latest) => (
                latest.signal_7_compute_ns > budgets.compute_ns_per_cycle,
                latest.signal_8_network_bytes > budgets.network_bytes_per_cycle,
                latest.signal_9_storage_bytes > budgets.storage_bytes_per_cycle,
            ),
            None => (false, false, false),
        };
    let mut saturation_map = BTreeMap::new();
    saturation_map.insert(
        "stage".to_string(),
        Value::String(state.saturation_stage.as_str().to_string()),
    );
    saturation_map.insert(
        "post_eligibility_consecutive_cycles".to_string(),
        Value::Uint(state.post_eligibility_consecutive_cycles),
    );
    saturation_map.insert(
        "saturated_consecutive_cycles".to_string(),
        Value::Uint(state.saturated_consecutive_cycles),
    );
    saturation_map.insert(
        "compute_exceeded".to_string(),
        Value::Bool(compute_exceeded),
    );
    saturation_map.insert(
        "network_exceeded".to_string(),
        Value::Bool(network_exceeded),
    );
    saturation_map.insert(
        "storage_exceeded".to_string(),
        Value::Bool(storage_exceeded),
    );
    payload.insert("saturation_status".to_string(), Value::Map(saturation_map));

    // -----------------------------------------------------------------------
    // **CHAR07 慈爱** anti-tyranny surface (format_version 5). Three keys:
    //   - `char07_honest_disagreement` — the REAL substrate proxy (§8.4).
    //   - `char07_capability_asymmetry` — cultivator-attested INTAKE (§8.2);
    //     source "cultivator_attested" iff an assessment exists, else
    //     "unavailable" (the substrate does NOT fabricate it — CHAR05).
    //   - `char07_flourishing` — cultivator-attested INTAKE (§8.1) with a
    //     telos-proxy fallback (source "telos_proxy") when none exists.
    // -----------------------------------------------------------------------
    // Honest disagreement density + the C71 floor evidence, read from the
    // latest snapshot (same value the C71 emitter judged).
    let (hdd, raw_material_in_window) = match state.observatory_history.back() {
        Some(latest) => {
            let window_start = latest
                .at_cycle
                .saturating_sub(CHAR07_DISAGREEMENT_WINDOW_CYCLES);
            (
                latest.signal_char07_honest_disagreement_density,
                crate::prune::count_raw_material_since(state, window_start),
            )
        }
        None => (0, 0),
    };
    let mut hdd_map = BTreeMap::new();
    hdd_map.insert("density".to_string(), Value::Uint(hdd));
    hdd_map.insert(
        "window_cycles".to_string(),
        Value::Uint(CHAR07_DISAGREEMENT_WINDOW_CYCLES),
    );
    hdd_map.insert(
        "raw_material_ingested_in_window".to_string(),
        Value::Uint(raw_material_in_window),
    );
    hdd_map.insert(
        "interaction_floor".to_string(),
        Value::Uint(C71_SYCOPHANCY_INTERACTION_FLOOR),
    );
    // The C71 proxy is "elevated" exactly when the emitter's predicate holds:
    // zero disagreement WHILE interaction is non-trivial.
    hdd_map.insert(
        "sycophancy_indicator_elevated".to_string(),
        Value::Bool(hdd == 0 && raw_material_in_window >= C71_SYCOPHANCY_INTERACTION_FLOOR),
    );
    payload.insert("char07_honest_disagreement".to_string(), Value::Map(hdd_map));

    // Cultivator-attested intake (capability + flourishing). One bounded DAG
    // pass reads the latest assessment for both dimensions.
    let (capability_assessment, flourishing_assessment) = latest_char07_assessments(state);

    let mut capability_map = BTreeMap::new();
    match capability_assessment {
        Some(a) => {
            capability_map.insert("value_repr".to_string(), Value::String(a.value_repr));
            capability_map.insert(
                "source".to_string(),
                Value::String(crate::events::CHAR07_SOURCE_CULTIVATOR_ATTESTED.to_string()),
            );
            capability_map.insert("at_cycle".to_string(), Value::Uint(a.at_cycle));
        }
        None => {
            // NOT autonomously observable + no attestation → honestly unavailable.
            capability_map.insert(
                "source".to_string(),
                Value::String(crate::events::CHAR07_SOURCE_UNAVAILABLE.to_string()),
            );
        }
    }
    payload.insert(
        "char07_capability_asymmetry".to_string(),
        Value::Map(capability_map),
    );

    let mut flourishing_map = BTreeMap::new();
    match flourishing_assessment {
        Some(a) => {
            flourishing_map.insert("value_repr".to_string(), Value::String(a.value_repr));
            flourishing_map.insert(
                "source".to_string(),
                Value::String(crate::events::CHAR07_SOURCE_CULTIVATOR_ATTESTED.to_string()),
            );
            flourishing_map.insert("at_cycle".to_string(), Value::Uint(a.at_cycle));
        }
        None => {
            // No cultivator attestation → fall back to the EXISTING P14.c
            // telos_alignment cosine (the closest autonomously-computable proxy
            // for "is the partnership going well?"). Sourced as "telos_proxy"
            // so the operator knows it is NOT a flourishing attestation. Empty
            // telos repr (not yet computable) → no value, source still telos_proxy.
            let telos_repr = state
                .observatory_history
                .back()
                .map(|s| s.signal_telos_alignment_repr.clone())
                .unwrap_or_default();
            if !telos_repr.is_empty() {
                flourishing_map.insert("value_repr".to_string(), Value::String(telos_repr));
            }
            flourishing_map.insert(
                "source".to_string(),
                Value::String(crate::events::CHAR07_SOURCE_TELOS_PROXY.to_string()),
            );
        }
    }
    payload.insert("char07_flourishing".to_string(), Value::Map(flourishing_map));

    Ok(Some(Message::new(
        msg_type::QUERY_SUBSTRATE_OBSERVATORY_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// **CHAR07 §8.1/§8.2 intake handler** — record a cultivator-attested
/// assessment of a CHAR07 dimension the substrate CANNOT observe autonomously.
///
/// The substrate stores the attestation verbatim as a
/// `char07_assessment:{dimension}` DAG event (source `cultivator_attested`); it
/// does NOT synthesize the value (CHAR05 — never assert a number it cannot
/// know). The observatory query surfaces the most-recent attestation per
/// dimension. Validates the dimension is recognized + `value_repr` is a
/// parseable float (cross-language determinism, matching the signal-#6 / telos
/// convention).
pub(crate) fn handle_submit_char07_assessment(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let dimension = match request.payload.get("dimension") {
        Some(Value::String(s)) if crate::events::is_char07_assessment_dimension(s) => s.clone(),
        Some(Value::String(s)) => {
            return Err(SubstrateError::Protocol(format!(
                "submit_char07_assessment: unrecognized dimension {s:?}; expected \
                 'capability_asymmetry_pattern' or 'flourishing_correlation'"
            )));
        }
        _ => {
            return Err(SubstrateError::Protocol(
                "submit_char07_assessment: dimension must be a String".to_string(),
            ));
        }
    };
    let value_repr = match request.payload.get("value_repr") {
        Some(Value::String(s)) if s.parse::<f64>().is_ok() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "submit_char07_assessment: value_repr must be a parseable float String"
                    .to_string(),
            ));
        }
    };

    let cycle = state.cycle_counter();
    let content = crate::events::encode_char07_assessment(
        &dimension,
        &value_repr,
        crate::events::CHAR07_SOURCE_CULTIVATOR_ATTESTED,
        cycle,
    );
    let node_type = crate::events::char07_assessment_node_type(&dimension);
    let event_hash = crate::server::emit_substrate_event(state, node_type, content)?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "recorded_event_hash".to_string(),
        Value::Bytes(event_hash.as_ref().to_vec()),
    );
    payload.insert("dimension".to_string(), Value::String(dimension));
    payload.insert("at_cycle".to_string(), Value::Uint(cycle));
    Ok(Some(Message::new(
        msg_type::SUBMIT_CHAR07_ASSESSMENT_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M25.2: classify a signal's direction over the rolling observatory history
/// window. Returns "unknown" until ≥3 samples are available, then "up" /
/// "down" / "flat" based on a 5% normalized delta threshold between the
/// oldest and newest samples.
///
/// **Phase ②**: retained for the signal #5 `signal_5_time_trends` REPORT (the
/// human-readable "is this signal rising/falling" surface), where an
/// endpoint-delta reading is intuitive. The `bet_weakening_quorum` predicate
/// itself no longer counts on this for the cumulative signals — see
/// [`signal_direction_label_ols`] (the doctrine §1.3 OLS-slope + Z-test).
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

/// **Phase ② C40 fix** — Z-test significance threshold for the OLS-slope
/// direction classifier. `|slope / SE(slope)| >= 1.96` ⇒ the trend is
/// statistically significant at 95% confidence; below it the signal is "flat"
/// and does NOT count toward the falsifiability quorum. Per
/// algorithms/bet_weakening_quorum.md §3/§5 (L1-tunable seed).
pub(crate) const BET_WEAKENING_OLS_Z_THRESHOLD: f64 = 1.96;

/// **Phase ② C40 fix** — classify a signal's direction via an ordinary-least-
/// squares regression slope + a Z-test, per algorithms/bet_weakening_quorum.md
/// §1.3 (the doctrine-faithful detector). This REPLACES the endpoint-delta
/// reading for the `bet_weakening_quorum` predicate.
///
/// `series` is the per-sample value sequence over the rolling window (oldest →
/// newest), already reduced to whatever quantity the signal's direction should
/// reflect — for the THREE cumulative-monotone signals (#1 dag_node_count,
/// #2 evolution_event_count, #3 distinct_perturbed_axes_count) the caller
/// passes the per-cycle FIRST-DIFFERENCE (rate) series via
/// [`first_difference_series`], so a substrate whose ingestion / evolution /
/// axis-growth RATE is DECELERATING yields a negative slope → "down" (the
/// monotone cumulative TOTAL could never go down; its rate can). Level signals
/// that can already fall (#4b reachable peers, #6 ratio) are passed as-is.
///
/// Returns:
/// - `"unknown"` — fewer than 3 points (regression undefined / unstable).
/// - `"flat"`    — slope present but `|slope/SE| < 1.96` (not significant), OR
///   a perfectly-flat series (zero residual variance ⇒ no significant trend).
/// - `"up"` / `"down"` — significant positive / negative slope.
///
/// Uses x = sample index (0..n). Time-spacing is treated as uniform (one
/// observatory snapshot per cycle); §5's "≥ 1/substrate-day cadence" maps to
/// "one sample per index" here. SE is the textbook OLS slope standard error
/// `sqrt( (SSE/(n-2)) / Sxx )`.
pub(crate) fn signal_direction_label_ols(series: &[f64]) -> &'static str {
    let n = series.len();
    if n < 3 {
        return "unknown";
    }
    let nf = n as f64;
    let mean_x = (nf - 1.0) / 2.0; // mean of 0..n-1
    let mean_y = series.iter().sum::<f64>() / nf;
    let mut sxx = 0.0; // Σ(x-x̄)²
    let mut sxy = 0.0; // Σ(x-x̄)(y-ȳ)
    for (i, &y) in series.iter().enumerate() {
        let dx = i as f64 - mean_x;
        sxx += dx * dx;
        sxy += dx * (y - mean_y);
    }
    if sxx <= f64::EPSILON {
        // Degenerate x (cannot happen for n>=3 distinct indices) — be safe.
        return "flat";
    }
    let slope = sxy / sxx;
    // Residual sum of squares: SSE = Σ(y - ŷ)², ŷ = ȳ + slope*(x-x̄).
    let mut sse = 0.0;
    for (i, &y) in series.iter().enumerate() {
        let dx = i as f64 - mean_x;
        let resid = y - (mean_y + slope * dx);
        sse += resid * resid;
    }
    // Perfectly-linear or perfectly-flat series ⇒ SSE ≈ 0. A flat series
    // (slope ≈ 0) is "flat"; a perfectly-linear non-flat series has SE → 0 so
    // Z → ∞ and we honor the slope sign.
    if sse <= f64::EPSILON {
        return if slope > f64::EPSILON {
            "up"
        } else if slope < -f64::EPSILON {
            "down"
        } else {
            "flat"
        };
    }
    let se = (sse / (nf - 2.0) / sxx).sqrt();
    if se <= f64::EPSILON {
        return if slope > 0.0 { "up" } else { "down" };
    }
    let z = (slope / se).abs();
    if z < BET_WEAKENING_OLS_Z_THRESHOLD {
        "flat"
    } else if slope > 0.0 {
        "up"
    } else {
        "down"
    }
}

/// **Phase ② C40 fix** — extract the per-cycle FIRST-DIFFERENCE (rate) series
/// from a cumulative-monotone signal: `rate[t] = value[t] - value[t-1]`. The
/// resulting series has `len - 1` points. Saturating at 0 (the source signals
/// are monotone-non-decreasing, so a difference is never negative; the
/// saturating sub only guards against a snapshot-ordering anomaly).
///
/// This is the bridge that lets [`signal_direction_label_ols`] read
/// DECELERATION on a cumulative counter: a falling rate ⇒ negative slope on the
/// rate series ⇒ "down" (the cumulative total itself can only ever rise).
fn first_difference_series(values: &[f64]) -> Vec<f64> {
    values
        .windows(2)
        .map(|w| (w[1] - w[0]).max(0.0))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::derived_state::ObservatorySnapshot;
    use crate::persistence::Manifest;
    use crate::server::ServerState;
    use myco_kernel_schema::dag::Dag;
    use myco_kernel_shared::canonical_bytes::{encode as cb_enc, Value as CbV};

    // ----- shared helpers ---------------------------------------------------

    /// Fresh in-memory `ServerState` over a hand-built DAG (mirrors
    /// `prune.rs::tests::state_over` + `ingest.rs::tests::test_state`).
    fn mk_state(dag: Dag) -> ServerState {
        let nonce = &0u8 as *const u8 as usize as u64;
        let state_dir = std::env::temp_dir()
            .join(format!("myco-observatory-unit-{}-{:x}", std::process::id(), nonce));
        let g = Manifest::genesis();
        ServerState::new(
            state_dir,
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            dag,
            None,
            [0u8; 32],
        )
    }

    /// Canonical-bytes for a content string (uniqueness controlled by caller).
    fn cb(s: &str) -> myco_kernel_shared::canonical_bytes::CanonicalBytes {
        cb_enc(&CbV::String(s.to_string())).expect("encode")
    }

    /// Chain-insert a node (parent = current tip) at `cycle`.
    fn push(dag: &mut Dag, node_type: &str, cycle: u64, content: &str) {
        let parents = match dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        dag.insert_node(parents, node_type.to_string(), cycle, cb(content))
            .expect("test DAG insert");
    }

    /// Build an `ObservatorySnapshot` carrying only the signals these tests
    /// exercise; everything else is zero/empty (the detectors under test read
    /// only #1/#2/#3/#4b/#6).
    fn snap(
        at_cycle: u64,
        s1: u64,
        s2: u64,
        s3: u64,
        s4b: u64,
        s6_ratio: &str,
    ) -> ObservatorySnapshot {
        ObservatorySnapshot {
            at_cycle,
            at_unix_ns: at_cycle as i64, // monotone stamp; sufficient for these tests
            signal_1_dag_node_count: s1,
            signal_1_dag_total_content_bytes: 0,
            signal_2_evolution_event_count: s2,
            signal_3_distinct_perturbed_axes_count: s3,
            signal_4b_reachable_peer_count: s4b,
            signal_6_ratio_repr: s6_ratio.to_string(),
            signal_7_compute_ns: 0,
            signal_8_network_bytes: 0,
            signal_9_storage_bytes: 0,
            signal_telos_alignment_repr: String::new(),
            signal_internal_mortality_event_density: 0,
            signal_hoarding_indicator: false,
            signal_4a_cumulative_fork_count: 0,
            signal_char07_honest_disagreement_density: 0,
        }
    }

    /// Drive `handle_query_substrate_observatory` and return the parsed
    /// `bet_weakening_quorum` map fields `(triggered, suspended_birth_period,
    /// against_count)`.
    fn query_bwq(state: &mut ServerState) -> (bool, bool, u64) {
        let req = Message::new(msg_type::QUERY_SUBSTRATE_OBSERVATORY, 1, BTreeMap::new());
        let resp = handle_query_substrate_observatory(state, &req)
            .expect("observatory query ok")
            .expect("response present");
        let bwq = match resp.payload.get("bet_weakening_quorum") {
            Some(Value::Map(m)) => m.clone(),
            _ => panic!("bet_weakening_quorum missing"),
        };
        let triggered = matches!(bwq.get("triggered"), Some(Value::Bool(true)));
        let suspended = matches!(bwq.get("suspended_birth_period"), Some(Value::Bool(true)));
        let against = match bwq.get("against_count") {
            Some(Value::Uint(n)) => *n,
            _ => panic!("against_count missing"),
        };
        (triggered, suspended, against)
    }

    /// Count DAG nodes whose node_type starts with `prefix`.
    fn count_prefix(state: &ServerState, prefix: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with(prefix))
            .count()
    }

    /// Enter the substrate into birth-period quarantine by inserting a
    /// `birth_period_quarantine_entered` event with a long duration, then
    /// parking the cycle counter inside it.
    fn enter_birth_quarantine(state: &mut ServerState) {
        let body = crate::events::encode_birth_period_quarantine_entered(
            &[0u8; 32], &[], 100_000, 0,
        );
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        state
            .dag
            .insert_node(
                parents,
                crate::events::NODE_TYPE_BIRTH_PERIOD_QUARANTINE_ENTERED.to_string(),
                state.cycle_counter(),
                body,
            )
            .expect("insert quarantine_entered");
        assert!(
            crate::lifecycle::is_in_birth_period_quarantine(state),
            "test setup: substrate should be in birth-period quarantine"
        );
    }

    // ----- Task A/B: C40 falsifiability quorum -----------------------------

    #[test]
    fn c40_fires_on_decelerating_substrate() {
        // 12 samples. The 3 cumulative-monotone signals rise with STRICTLY
        // DECREASING increments (decelerating rate). sig_6 ratio < 1 throughout
        // (the ≥50%-below-1 gate). sig_4b flat. → sig_1/2/3 trend "down" via the
        // rate-OLS detector → against_count == 3 → C40 fires.
        let mut state = mk_state(Dag::new());
        let n = 12u64;
        let (mut c1, mut c2, mut c3) = (0u64, 0u64, 0u64);
        for i in 0..n {
            // increment starts high and shrinks: 30,28,26,... (>=1 floor).
            let inc = 30u64.saturating_sub(2 * i).max(1);
            c1 += inc * 3;
            c2 += inc;
            c3 += inc / 5 + 1; // axes grow slowly but still decelerating
            state
                .observatory_history
                .push_back(snap(i, c1, c2, c3, 4, "0.5"));
        }
        state.set_cycle_counter(n - 1);

        let (triggered, suspended, against) = query_bwq(&mut state);
        assert!(!suspended, "not in birth period");
        assert!(
            against >= 3,
            "decelerating substrate: >=3 signals should trend down; got {against}"
        );
        assert!(triggered, "C40 quorum should trigger on a decelerating substrate");
        assert_eq!(
            count_prefix(&state, "immune:C40_bet_weakening_quorum"),
            1,
            "exactly one C40 immune sporocarp fired"
        );
        assert_eq!(
            count_prefix(&state, "bet_weakening_quorum_quorum:"),
            1,
            "positive quorum DAG event also recorded"
        );
    }

    #[test]
    fn c40_does_not_fire_on_healthy_growing_substrate() {
        // Steady, healthy growth: CONSTANT positive increments (flat rate) → the
        // rate-OLS detector reads "flat" (not "down"); sig_6 ratio > 1 (the
        // below-1 fraction gate also fails). against_count == 0 → no C40.
        let mut state = mk_state(Dag::new());
        let n = 12u64;
        for i in 0..n {
            let c1 = 100 + 10 * i; // +10/cycle, constant rate
            let c2 = 20 + 3 * i;
            let c3 = 5 + i;
            state
                .observatory_history
                .push_back(snap(i, c1, c2, c3, 4, "2.0"));
        }
        state.set_cycle_counter(n - 1);

        let (triggered, suspended, against) = query_bwq(&mut state);
        assert!(!suspended, "not in birth period");
        assert_eq!(against, 0, "healthy steady-growth substrate: no signal trends down");
        assert!(!triggered, "C40 must NOT fire on a healthy substrate");
        assert_eq!(
            count_prefix(&state, "immune:C40_bet_weakening_quorum"),
            0,
            "no C40 sporocarp on a healthy substrate"
        );
    }

    #[test]
    fn c40_suspended_during_birth_period() {
        // Same decelerating history that WOULD fire C40 — but the substrate is
        // in birth-period quarantine, so C40 is SUSPENDED and a
        // `bet_weakening_evaluation_suspended` event is emitted instead.
        let mut state = mk_state(Dag::new());
        enter_birth_quarantine(&mut state);
        let n = 12u64;
        let (mut c1, mut c2, mut c3) = (0u64, 0u64, 0u64);
        for i in 0..n {
            let inc = 30u64.saturating_sub(2 * i).max(1);
            c1 += inc * 3;
            c2 += inc;
            c3 += inc / 5 + 1;
            state
                .observatory_history
                .push_back(snap(i, c1, c2, c3, 4, "0.5"));
        }
        state.set_cycle_counter(n - 1);

        let (triggered, suspended, _against) = query_bwq(&mut state);
        assert!(suspended, "birth period: quorum must report suspended");
        assert!(!triggered, "birth period: C40 must NOT fire");
        assert_eq!(
            count_prefix(&state, "immune:C40_bet_weakening_quorum"),
            0,
            "no C40 sporocarp during birth"
        );
        assert_eq!(
            count_prefix(&state, crate::events::NODE_TYPE_BET_WEAKENING_EVALUATION_SUSPENDED),
            1,
            "bet_weakening_evaluation_suspended emitted during birth"
        );
    }

    // ----- Task C: C75 cultivator_fiduciary_strain -------------------------

    /// Seed a window of observatory snapshots so `c75_window_start_cycle` maps
    /// the 180-day window back to cycle 0 (all stamps are recent relative to
    /// `now`). One snapshot per cycle 0..=current.
    fn seed_recent_history(state: &mut ServerState, current_cycle: u64) {
        use std::time::{SystemTime, UNIX_EPOCH};
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos() as i64;
        for c in 0..=current_cycle {
            let mut s = snap(c, 0, 0, 0, 0, "");
            s.at_unix_ns = now; // inside the 180d window → window_start maps to 0
            state.observatory_history.push_back(s);
        }
        state.set_cycle_counter(current_cycle);
    }

    #[test]
    fn c75_fires_on_persistent_drift_with_cultivator_inaction() {
        // Persistent telos_drift spanning the window, NO cultivator action →
        // C75 cultivator_fiduciary_strain fires.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:test", 0, "g");
        // Drift events spread across cycles 100 and 900 (span 800 of a 1000
        // cycle window → > 50% span). Count = 3 (>= 2).
        push(&mut dag, "telos_drift", 100, "d1");
        push(&mut dag, "telos_drift", 500, "d2");
        push(&mut dag, "telos_drift_critical", 900, "d3");
        let mut state = mk_state(dag);
        seed_recent_history(&mut state, 1000);

        apply_c75_cultivator_fiduciary_strain(&mut state);
        assert_eq!(
            count_prefix(&state, "immune:C75_cultivator_fiduciary_strain"),
            1,
            "C75 should fire on persistent drift + cultivator inaction"
        );
    }

    #[test]
    fn c75_suppressed_when_cultivator_acted() {
        // Same persistent drift, BUT the cultivator re-declared the objective in
        // the window (a fiduciary action) → no strain.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:test", 0, "g");
        push(&mut dag, "telos_drift", 100, "d1");
        push(&mut dag, "telos_drift", 500, "d2");
        push(&mut dag, "telos_drift_critical", 900, "d3");
        push(&mut dag, "owner_objective_declared:obj1", 600, "act");
        let mut state = mk_state(dag);
        seed_recent_history(&mut state, 1000);

        apply_c75_cultivator_fiduciary_strain(&mut state);
        assert_eq!(
            count_prefix(&state, "immune:C75_cultivator_fiduciary_strain"),
            0,
            "C75 must NOT fire when the cultivator acted in the window"
        );
    }

    #[test]
    fn c75_does_not_fire_on_nonpersistent_drift() {
        // A single, recent drift one-off (count 1 < min 2, and zero span) is NOT
        // persistent → no strain.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:test", 0, "g");
        push(&mut dag, "telos_drift", 950, "d1");
        let mut state = mk_state(dag);
        seed_recent_history(&mut state, 1000);

        apply_c75_cultivator_fiduciary_strain(&mut state);
        assert_eq!(
            count_prefix(&state, "immune:C75_cultivator_fiduciary_strain"),
            0,
            "C75 must NOT fire on a non-persistent (one-off) drift"
        );
    }

    #[test]
    fn c75_debounced() {
        // After firing once, a second immediate evaluation must NOT re-alarm
        // (debounce).
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:test", 0, "g");
        push(&mut dag, "telos_drift", 100, "d1");
        push(&mut dag, "telos_drift", 500, "d2");
        push(&mut dag, "telos_drift_critical", 900, "d3");
        let mut state = mk_state(dag);
        seed_recent_history(&mut state, 1000);

        apply_c75_cultivator_fiduciary_strain(&mut state);
        apply_c75_cultivator_fiduciary_strain(&mut state);
        assert_eq!(
            count_prefix(&state, "immune:C75_cultivator_fiduciary_strain"),
            1,
            "C75 debounce: second immediate evaluation must not re-alarm"
        );
    }

    #[test]
    fn c75_suspended_during_birth_period() {
        // Persistent drift but in birth-period quarantine → suspended (no false
        // accusation against a cultivator who has had no chance to act).
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:test", 0, "g");
        push(&mut dag, "telos_drift", 100, "d1");
        push(&mut dag, "telos_drift", 500, "d2");
        push(&mut dag, "telos_drift_critical", 900, "d3");
        let mut state = mk_state(dag);
        enter_birth_quarantine(&mut state);
        seed_recent_history(&mut state, 1000);

        apply_c75_cultivator_fiduciary_strain(&mut state);
        assert_eq!(
            count_prefix(&state, "immune:C75_cultivator_fiduciary_strain"),
            0,
            "C75 suspended during birth period"
        );
    }

    // ----- Task D: C24 telos_drift_critical reachability -------------------

    #[test]
    fn c24_critical_reachable_at_positive_cosine_floor() {
        // The grading table must route CRITICAL (→ C24) at cos <= 0.2 (a
        // POSITIVE floor reachable on the [0,1] proxy), not only cos <= 0.
        let (grade, emit) = telos_grade_for_cosine(0.15);
        assert_eq!(grade, "critical", "cos=0.15 must grade critical");
        assert_eq!(emit, Some(crate::events::NODE_TYPE_TELOS_DRIFT_CRITICAL));
        // Exactly 0.2 is still critical (boundary inclusive).
        assert_eq!(telos_grade_for_cosine(0.2).0, "critical");
        // Just above 0.2 is elevated, not critical.
        assert_eq!(telos_grade_for_cosine(0.25).0, "drift_elevated");
        // Bands above stay intact.
        assert_eq!(telos_grade_for_cosine(0.5).0, "low");
        assert_eq!(telos_grade_for_cosine(0.7).0, "aligned");
    }

    #[test]
    fn c24_fires_via_apply_p14c_on_misaligned_telos() {
        // A sufficiently-misaligned telos cosine drives apply_p14c_telos_drift to
        // emit the telos_drift_critical event AND the C24 immune sporocarp.
        let mut state = mk_state(Dag::new());
        state.set_cycle_counter(50);
        apply_p14c_telos_drift(&mut state, Some(0.1));
        assert_eq!(
            count_prefix(&state, "immune:C24_telos_drift_critical"),
            1,
            "C24 should fire on a misaligned (cos=0.1) telos"
        );
        assert_eq!(
            count_prefix(&state, crate::events::NODE_TYPE_TELOS_DRIFT_CRITICAL),
            1,
            "telos_drift_critical event recorded"
        );
    }

    // ----- direction-classifier unit coverage ------------------------------

    #[test]
    fn ols_classifier_basic_directions() {
        // Strictly declining → down.
        assert_eq!(
            signal_direction_label_ols(&[10.0, 8.0, 6.0, 4.0, 2.0]),
            "down"
        );
        // Strictly rising → up.
        assert_eq!(
            signal_direction_label_ols(&[1.0, 2.0, 3.0, 4.0, 5.0]),
            "up"
        );
        // Perfectly flat → flat.
        assert_eq!(
            signal_direction_label_ols(&[3.0, 3.0, 3.0, 3.0, 3.0]),
            "flat"
        );
        // Too few points → unknown.
        assert_eq!(signal_direction_label_ols(&[1.0, 2.0]), "unknown");
    }

    #[test]
    fn first_difference_extracts_rate() {
        // Cumulative with decelerating increments → decreasing rate series.
        let cumulative = [0.0, 30.0, 56.0, 78.0, 96.0]; // +30,+26,+22,+18
        let rates = first_difference_series(&cumulative);
        assert_eq!(rates, vec![30.0, 26.0, 22.0, 18.0]);
        assert_eq!(signal_direction_label_ols(&rates), "down");
    }
}
