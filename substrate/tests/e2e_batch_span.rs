//! E2E: P04 §3.1 batch-summarized idle cycle_advanced — end-to-end coverage.
//!
//! Split out of the per-domain e2e suite. Shared spawn / build helpers live in
//! `tests/common/mod.rs`; this binary pulls them in via `use common::*`.
//!
//! BACKGROUND. A provably-inert idle cultivar (no axes / migration /
//! federation) batches its self-driven no-op heartbeats: instead of one
//! `cycle_advanced` DAG node per tick, it accumulates `pending_self_driven_noop_cycles`
//! in memory and emits ONE spanning `cycle_advanced(prior, prior + span)` node
//! at a FLUSH boundary (a real metabolic cycle, the `SELF_DRIVEN_BATCH_MAX = 9`
//! cap, a prune-scan boundary, an operator request, or shutdown). C59
//! (`integrity.rs::check_manifest_cycle_vs_dag_advance_count`) therefore SUMS
//! the spans of all cycle_advanced nodes (Σ `new_cycle − prior_cycle`) and
//! asserts that sum == `cycle_counter`, rather than counting nodes.
//!
//! The white-box unit tests (in `server/autonomous.rs`) prove the in-memory
//! gate + sum math. THIS file closes the end-to-end hole the audit flagged:
//! that a real flush-forcing cap cycle produces a genuine batched spanning node
//! on disk, and that the batched span survives a full disk round-trip (shutdown
//! + reload + DAG replay) with C59 still holding on reload.

mod common;
use common::*;

/// `SELF_DRIVEN_BATCH_MAX` mirrored from `server/autonomous.rs` (private const).
/// The gate batches a tick iff `pending + 1 < SELF_DRIVEN_BATCH_MAX`, so a run
/// of inert ticks accumulates a span of up to `SELF_DRIVEN_BATCH_MAX - 1 = 8`
/// before a flush + real cycle seals it.
const SELF_DRIVEN_BATCH_MAX: u64 = 9;

/// Read every `cycle_advanced` node from a (booted) substrate and return
/// `(node_count, span_sum)`:
///   - `node_count`   = number of `cycle_advanced` DAG nodes.
///   - `span_sum`     = Σ (`new_cycle − prior_cycle`) over those nodes — equals
///                      the metabolic cycle_counter by the C59 invariant.
///
/// A node whose content does not decode as `{prior_cycle, new_cycle}` is
/// conservatively counted as a span of 1 (the legacy per-node assumption,
/// matching C59's own fallback).
fn read_cycle_advanced_node_count_and_span_sum(client: &mut BridgeClient) -> (u64, u64) {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};

    let resp = client
        .call(
            proto::QUERY_RECENT_NODES,
            build_payload(vec![
                ("count", CbValue::Uint(10_000)),
                (
                    "node_type_prefix",
                    CbValue::String("cycle_advanced".to_string()),
                ),
            ]),
        )
        .expect("query cycle_advanced nodes");
    let nodes = match resp.payload.get("nodes") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("nodes missing"),
    };
    let node_count = nodes.len() as u64;
    let mut span_sum: u64 = 0;
    for node in &nodes {
        let m = match node {
            CbValue::Map(m) => m,
            _ => panic!("cycle_advanced node not a Map"),
        };
        let content = match m.get("content_canonical_bytes") {
            Some(CbValue::Bytes(b)) => b.clone(),
            _ => panic!("cycle_advanced node missing content_canonical_bytes"),
        };
        let span = match cb_decode(&content) {
            Ok(CbV::Map(cm)) => {
                let prior = match cm.get("prior_cycle") {
                    Some(CbV::Uint(u)) => *u,
                    _ => {
                        span_sum = span_sum.saturating_add(1);
                        continue;
                    }
                };
                let new = match cm.get("new_cycle") {
                    Some(CbV::Uint(u)) => *u,
                    _ => {
                        span_sum = span_sum.saturating_add(1);
                        continue;
                    }
                };
                new.saturating_sub(prior)
            }
            // Undecodable / non-map content → legacy span of 1.
            _ => 1,
        };
        span_sum = span_sum.saturating_add(span);
    }
    (node_count, span_sum)
}

/// Run the substrate's ad-hoc integrity pipeline (the RUN_IMMUNE_CHECK / C59
/// path) and assert that NO check failed AND that the C59
/// `manifest_cycle_vs_dag_advance_count` check specifically passed. Returns the
/// C59 evidence string for diagnostics.
fn assert_c59_holds(client: &mut BridgeClient) -> String {
    let check_resp = client
        .call(proto::RUN_IMMUNE_CHECK, build_payload(vec![]))
        .expect("run_immune_check");
    let failed_checks = match check_resp.payload.get("failed_checks") {
        Some(CbValue::Uint(n)) => *n,
        _ => panic!("failed_checks missing from RUN_IMMUNE_CHECK response"),
    };
    // Locate the C59 check specifically so a regression in its math is reported
    // with its own evidence, not just buried in the aggregate count.
    let checks = match check_resp.payload.get("checks") {
        Some(CbValue::Array(a)) => a.clone(),
        _ => panic!("checks array missing"),
    };
    let mut c59_passed: Option<bool> = None;
    let mut c59_evidence = String::new();
    for c in &checks {
        let m = match c {
            CbValue::Map(m) => m,
            _ => continue,
        };
        let id = match m.get("check_id") {
            Some(CbValue::String(s)) => s.clone(),
            _ => continue,
        };
        if id == "manifest_cycle_vs_dag_advance_count" {
            c59_passed = match m.get("passed") {
                Some(CbValue::Bool(b)) => Some(*b),
                _ => None,
            };
            c59_evidence = match m.get("evidence") {
                Some(CbValue::String(s)) => s.clone(),
                _ => String::new(),
            };
        }
    }
    assert_eq!(
        c59_passed,
        Some(true),
        "C59 manifest_cycle_vs_dag_advance_count must PASS after reload; \
         evidence: {c59_evidence}"
    );
    assert_eq!(
        failed_checks, 0,
        "no integrity check may fail after reload of a batched-span substrate; \
         C59 evidence: {c59_evidence}"
    );
    c59_evidence
}

/// **The audit-flagged hardening.** An inert substrate idles long enough to
/// cross the `SELF_DRIVEN_BATCH_MAX` cap (forcing a flush + a real metabolic
/// cycle, which seals a genuine BATCHED spanning `cycle_advanced` node on
/// disk), then shuts down and RELOADS on the SAME state_dir — proving that
/// Σ-of-spans == cycle_counter survives the disk round-trip + DAG replay and
/// that C59 still holds on the reloaded substrate.
///
/// This idles PURELY (no operator advance calls): the only driver of the cycle
/// counter is the self-driven autonomous tick. A short tick interval (50ms)
/// keeps the idle wait small while still crossing the cap several times.
///
/// Robust by construction:
///   - generous sleep (> several full cap windows) so at least one batched span
///     is guaranteed even under CI scheduling jitter;
///   - the batching ASSERTION tolerates timing (it asserts `node_count <
///     span_sum`, the batching signature, not an exact count);
///   - C59 is the disk-round-trip invariant being proven, so it is asserted
///     exactly (must pass).
#[test]
fn batch_span_survives_reload_and_c59_holds() {
    let dir = fresh_state_dir();

    // Tick interval: short enough that the idle wait crosses the cap several
    // times, long enough that the substrate isn't pathologically busy.
    let tick_ms: u64 = 50;

    let (pre_node_count, pre_span_sum) = {
        let mut client = spawn_substrate_with_env(
            &dir,
            vec![
                (
                    "MYCO_SELF_DRIVEN_CYCLE_ADVANCE".to_string(),
                    "1".to_string(),
                ),
                (
                    "MYCO_TICK_INTERVAL_MS".to_string(),
                    tick_ms.to_string(),
                ),
            ],
        );

        // INERT: register NO axes, open NO federation, request NO migration —
        // so `is_provably_inert_for_batch` holds and the self-driven path
        // batches. Idle with NO operator call (which would itself force a
        // flush) long enough to cross the cap several times.
        //
        // One cap window = SELF_DRIVEN_BATCH_MAX ticks (8 batched accumulations
        // + 1 flush+real-cycle). We sleep for ~6 cap windows + a fixed margin,
        // so even with handshake-settle latency + scheduler jitter the cap
        // fires multiple times and at least one genuine span-8 node lands.
        let cap_windows: u64 = 6;
        let sleep_ms = cap_windows
            .saturating_mul(SELF_DRIVEN_BATCH_MAX)
            .saturating_mul(tick_ms)
            .saturating_add(1000); // generous fixed margin
        std::thread::sleep(std::time::Duration::from_millis(sleep_ms));

        let (node_count, span_sum) =
            read_cycle_advanced_node_count_and_span_sum(&mut client);

        // The cycle counter must have advanced by SEVERAL (the substrate cycled
        // autonomously while idle). We require enough advance to guarantee the
        // cap fired at least once (span_sum >= SELF_DRIVEN_BATCH_MAX).
        assert!(
            span_sum >= SELF_DRIVEN_BATCH_MAX,
            "inert substrate should have self-advanced past one cap window \
             ({SELF_DRIVEN_BATCH_MAX} cycles) after idling; span_sum={span_sum}, \
             node_count={node_count} (self-driven scheduler not firing?)"
        );

        // THE BATCHING SIGNATURE. If every cycle emitted its own node, node_count
        // would equal span_sum. Batching collapses runs of inert ticks into one
        // spanning node, so node_count is STRICTLY FEWER than the cycle delta.
        assert!(
            node_count < span_sum,
            "batching signature absent: node_count ({node_count}) should be \
             STRICTLY FEWER than the cycle delta span_sum ({span_sum}) — a \
             batched span (span > 1) must have collapsed multiple cycles into \
             one cycle_advanced node"
        );

        // Shut down cleanly. Shutdown is itself a flush boundary, so any
        // still-pending in-memory span is sealed into a final spanning node
        // before the DAG is persisted — exactly the path we want to reload.
        client.shutdown().expect("shutdown original");
        (node_count, span_sum)
    };

    // RELOAD on the SAME state_dir. Boot replays the DAG: each cycle_advanced
    // node (including the batched spanning ones) sets the counter to its
    // absolute `new_cycle` (derived_state::apply_cycle_advanced). After boot,
    // run the C59 / RUN_IMMUNE_CHECK path and assert it holds — proving
    // Σ-of-spans == cycle_counter survived disk + replay.
    //
    // Spawn the reloaded substrate WITHOUT the self-driven flag so it does not
    // race ahead between our reads (we want a stable post-reload snapshot to
    // compare against the pre-shutdown one).
    let mut client_reloaded = spawn_substrate_with_state_dir(&dir);

    let c59_evidence = assert_c59_holds(&mut client_reloaded);

    // The reloaded DAG must carry forward the same (or more — boot may append
    // an invariant_witness, never a cycle_advanced) batched-span history. In
    // particular the span_sum must be PRESERVED across the round-trip, and the
    // batching signature must still be visible (node_count < span_sum).
    let (post_node_count, post_span_sum) =
        read_cycle_advanced_node_count_and_span_sum(&mut client_reloaded);
    assert_eq!(
        post_span_sum, pre_span_sum,
        "Σ-of-spans must be preserved across disk round-trip + replay: \
         pre={pre_span_sum}, post={post_span_sum}; C59 evidence: {c59_evidence}"
    );
    assert!(
        post_node_count < post_span_sum,
        "batching signature must survive reload: post_node_count \
         ({post_node_count}) should be strictly fewer than post_span_sum \
         ({post_span_sum})"
    );
    // No new cycle_advanced node should be synthesized by boot/replay alone.
    assert_eq!(
        post_node_count, pre_node_count,
        "reload must not invent or drop cycle_advanced nodes: \
         pre={pre_node_count}, post={post_node_count}"
    );

    client_reloaded.shutdown().expect("shutdown reloaded");
}
