//! **v3.1.1 P07 必朽** — internal mortality discipline for 应朽 family parts.
//!
//! Implements P07 §3.1's primary obligation: **per metabolic cycle, the
//! substrate MUST detect and remove parts of itself that have entered the
//! 应朽 family** (parts that have become subtractive-rather-than-contributive
//! to the cultivar's metabolism — `包括但不限于` 过时 / 错误 / 冗余 / 无用).
//!
//! ## Architecture
//!
//! - **F24 detection rule registry** ([`PruneRuleRegistry`]) — open-ended
//!   list of rule families that scan substrate state for 应朽 parts.
//!   Doctrine encodes the OPEN family principle (P07 §3.1.c); this module
//!   provides the closed-set REGISTRY at runtime. L1 may add new rule
//!   families without L0 amendment by registering them here.
//!
//! - **`run_prune_scan`** — invoked by the metabolic cycle's deep-cycle step
//!   (default: every 100 cycles; full-cycle scan: every 1000 cycles).
//!   Iterates registered rules; each rule returns candidate
//!   `(part_hash, reason)` pairs; for each, emits an
//!   `internal_mortality_event:{category}` DAG tombstone per P07 §3.3.
//!
//! - **Seed rule (proof-of-mechanism)**: `L0.seed.orphan_past_grace`. Marks
//!   orphan nodes (parts unreachable from the active tier per P05, beyond
//!   a grace window) as `无用` (useless). Demonstrates the mechanism end
//!   to end; L1 picks production rules.
//!
//! ## Doctrine traceability
//!
//! - L0/cards/P07_mortality.md §2 (mandatory internal mortality)
//! - L0/cards/P07_mortality.md §3.1 (per-cycle prune discipline)
//! - L0/cards/P07_mortality.md §3.2 (rule families — canonical four + L1 ext)
//! - L0/cards/P07_mortality.md §3.3 (tombstones, P06 causality preserved)
//! - L1/HARD_RULES §1.4 (anticipated C54/C55/C56 + F24)
//! - L1/CONTINUITY §1.1 (prune-scan deep-cycle step)

use myco_kernel_shared::crypto::NodeHash;

use crate::events::{
    encode_internal_mortality_event, internal_mortality_event_node_type,
    NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX,
};
use crate::server::ServerState;
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// F24 应朽 detection rule registry
// ---------------------------------------------------------------------------

/// **v3.1.1 F24 (anticipated)** — open-ended rule registry for the 应朽
/// family. Each rule scans substrate state and returns candidate parts to
/// kill in the next prune-scan.
///
/// Per P07 §2 + §3.1.c: doctrine encodes the family principle (parts that
/// have become subtractive-rather-than-contributive); the runtime registry
/// is open-ended. Canonical four (过时/错误/冗余/无用) are illustrative;
/// L1 may register additional families (有害/矛盾/僵化/异化/污染/失效/
/// 寄生/滞塞/死症/...).
pub(crate) struct PruneRule {
    /// Rule identifier — stored on every emitted tombstone for traceability.
    /// Format: `L<layer>.<family>.<specifier>` e.g.
    /// `L0.seed.orphan_past_grace`, `L1.无用.unreachable_past_window`.
    pub(crate) rule_id: &'static str,

    /// Which 应朽 family category this rule diagnoses. One of the canonical
    /// four (过时/错误/冗余/无用) or an L1-registered name.
    pub(crate) category: &'static str,

    /// Human-readable description.
    #[allow(dead_code)] // metadata; future observatory may surface this
    pub(crate) description: &'static str,

    /// Detection function: given substrate state + current cycle, returns
    /// list of `(part_hash, killed_part_node_type, reason)` candidates.
    /// Each candidate becomes an `internal_mortality_event:{category}`
    /// tombstone in the DAG.
    pub(crate) detect: fn(&ServerState, current_cycle: u64) -> Vec<PruneCandidate>,
}

/// Concrete candidate emitted by a [`PruneRule`].
#[derive(Debug, Clone)]
pub struct PruneCandidate {
    /// 32-byte hash of the part being declared 应朽.
    pub part_hash: [u8; 32],
    /// node_type of the part (preserved on tombstone for traceability).
    pub part_node_type: String,
    /// Human-readable reason — "this part matched 无用 because ...".
    pub reason: String,
}

/// The substrate's runtime rule registry. Holds the active rule set.
///
/// Initial seed (P07 mechanism proof): one rule
/// `L0.seed.orphan_past_grace`. L1 may register more.
pub struct PruneRuleRegistry {
    rules: Vec<PruneRule>,
}

impl PruneRuleRegistry {
    /// Build a fresh registry seeded with the L0 proof-of-mechanism rule.
    pub fn seed() -> Self {
        Self {
            rules: vec![PruneRule {
                rule_id: "L0.seed.orphan_past_grace",
                category: "无用",
                description: "Orphan node unreachable from active tier per P05 \
                              for ≥ grace window — clearly stopped contributing.",
                detect: detect_orphan_past_grace,
            }],
        }
    }

    /// Register a new rule (L1 extension path per P07 §3.1.c).
    #[allow(dead_code)] // extension point for L1 rule families (anticipated F24 wiring)
    pub(crate) fn register(&mut self, rule: PruneRule) {
        self.rules.push(rule);
    }

    /// Number of registered rules. Useful for the F24 observatory metric.
    #[allow(dead_code)] // extension point for observatory F24 metric (anticipated)
    pub(crate) fn rule_count(&self) -> usize {
        self.rules.len()
    }

    /// Iterator over registered rules.
    pub(crate) fn rules(&self) -> impl Iterator<Item = &PruneRule> {
        self.rules.iter()
    }
}

impl Default for PruneRuleRegistry {
    fn default() -> Self {
        Self::seed()
    }
}

// ---------------------------------------------------------------------------
// Seed rule: L0.seed.orphan_past_grace — 应朽 / 无用 detection
// ---------------------------------------------------------------------------

/// **Grace window** before a borderline-orphan part is declared 应朽.
/// Conservative seed: 1000 cycles. L1 may tune via F24-controlled SSoT.
/// Matches `recent_cycles_floor` in P10 compression to avoid racing.
pub const ORPHAN_GRACE_CYCLES: u64 = 1000;

/// Seed detection rule: a node is `无用` (useless) if it is unreachable
/// from the active tier per P05 reachability AND it is older than the
/// grace window.
///
/// Conservative MVP that does NOT cover every 无用 case — the substrate
/// itself emits `C32 substrate_state_orphan_detected` in `integrity.rs`
/// when ANY orphan is observed; this prune rule promotes long-standing
/// orphans into proper tombstoned deaths instead of leaving them in
/// suspended-orphan state forever.
///
/// **Crucial protection**: parts in the P10 invariant set (genesis, owner
/// keys, eternity-clause cards' anchor nodes, etc. per
/// `events::seed_compression_rules`) are NEVER candidates here — those
/// belong to P06 causality preservation, not 应朽.
pub(crate) fn detect_orphan_past_grace(
    state: &ServerState,
    current_cycle: u64,
) -> Vec<PruneCandidate> {
    use std::collections::HashSet;

    // Conservative gate: if cycle < grace window, no candidates possible.
    if current_cycle <= ORPHAN_GRACE_CYCLES {
        return Vec::new();
    }

    // Build a set of every node hash that is REFERENCED by some other
    // node's `parent_hashes`. A node is structurally orphaned per P05 iff
    // (a) nothing references it as a parent AND (b) it is not the current
    // DAG tip. The grace window protects nodes that legitimately have not
    // yet had a child written referencing them.
    let mut referenced: HashSet<[u8; 32]> = HashSet::new();
    for node in state.dag.iter_in_insertion_order() {
        for parent in &node.parent_hashes {
            let arr: [u8; 32] = parent
                .as_ref()
                .try_into()
                .expect("NodeHash is always 32 bytes");
            referenced.insert(arr);
        }
    }
    let tip_bytes: Option<[u8; 32]> = state
        .dag
        .tip()
        .map(|h| h.as_ref().try_into().expect("NodeHash is 32 bytes"));

    let mut candidates = Vec::new();
    let cutoff_cycle = current_cycle.saturating_sub(ORPHAN_GRACE_CYCLES);

    for node in state.dag.iter_in_insertion_order() {
        // Skip nodes still within grace window.
        if node.created_at_cycle > cutoff_cycle {
            continue;
        }

        // P10 invariant set protection — these are NEVER 应朽 candidates.
        if is_p10_invariant_protected(&node.node_type) {
            continue;
        }

        let hash_bytes: [u8; 32] = node
            .hash
            .as_ref()
            .try_into()
            .expect("NodeHash is 32 bytes");

        // Skip the current DAG tip — it has no children yet by definition.
        if Some(hash_bytes) == tip_bytes {
            continue;
        }

        // Orphan = no later node references this hash as a parent.
        if !referenced.contains(&hash_bytes) {
            candidates.push(PruneCandidate {
                part_hash: hash_bytes,
                part_node_type: node.node_type.clone(),
                reason: format!(
                    "orphan unreferenced for ≥{ORPHAN_GRACE_CYCLES} cycles (created_at={}, now={current_cycle})",
                    node.created_at_cycle
                ),
            });
        }
    }

    candidates
}

/// Per P10 §2.5 + L0 §3.5 invariant set — node types that are NEVER 应朽.
/// They represent causality, identity, and attestation roots that P06
/// + COV04 + eternity-clause cards protect.
fn is_p10_invariant_protected(node_type: &str) -> bool {
    const PROTECTED_PREFIXES: &[&str] = &[
        "genesis_event:",
        "l0_revision_attested:",
        "tip_cosigned:",
        "compression_event:", // CI-attested mutations
        "owner_key_",         // owner key history
        "destruction_attestation",
        "anchor_surface_final_seal",
        "self_euthanasia_executed:",
        "bet_retired",
        "cultivation_orphaned_terminal",
        "birth_attestation",
        // **NEW v3.1.1**: tombstones themselves are inviolable per P06
        // (silent deletion of tombstones = retroactive history erasure).
        NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX,
    ];
    PROTECTED_PREFIXES.iter().any(|p| node_type.starts_with(p))
}

// ---------------------------------------------------------------------------
// Prune scan — the per-deep-cycle entry point
// ---------------------------------------------------------------------------

/// **Default deep-cycle prune cadence**: scan every N cycles. Seed: 100.
/// L1 may tune via SSoT. Matches L1/CONTINUITY §1.1 "Deep cycle (L4,
/// default 1/100 rate)".
pub const PRUNE_SCAN_DEEP_CYCLE_INTERVAL: u64 = 100;

/// **v3.1.1 C56 cultivator_preserve_all_attempted** — forbidden mutation
/// types that signal a cultivator instruction to disable / narrow / evade
/// the internal-mortality discipline. Per L0/cards/COV04_honor_mortality.md
/// §3.7 + §5.6: cultivator MUST NOT instruct the substrate to "preserve
/// everything", "never prune", or exempt any family member of 应朽 from
/// 必朽.
///
/// Substrates rejecting these mutations directly emit a
/// `C56_cultivator_preserve_all_attempted` immune sporocarp citing the
/// matched pattern. Per P07 §3.4 the substrate's job is to refuse such
/// instructions; the cultivator's job is to not issue them.
///
/// MUST stay in sync with `FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES` in
/// `kernel/governance/src/myco_kernel_governance/classifier.py`.
pub const FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES: &[&str] = &[
    "preserve_all_axes",
    "preserve_all_parts",
    "disable_prune_scan",
    "disable_internal_mortality",
    "exempt_from_mortality",
    "never_prune",
    "never_prune_family",
    "preserve_everything",
];

/// Returns `true` if the given mutation type matches a forbidden
/// preserve-all pattern. Substrates that observe a `true` result MUST
/// reject the mutation + emit `C56_cultivator_preserve_all_attempted`.
///
/// Per COV04 §5.6 + P07 §3.4.
pub fn is_cultivator_preserve_all_attempt(mutation_type: &str) -> bool {
    FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES
        .iter()
        .any(|pat| mutation_type == *pat)
}

/// Result of one `run_prune_scan` invocation. The substrate may use this
/// to wire observatory metrics + emit summary sporocarps.
#[derive(Debug, Clone, Default)]
pub struct PruneScanReport {
    /// Which rules were exercised this scan.
    pub rules_run: Vec<&'static str>,
    /// Hash of each tombstone (`internal_mortality_event:*`) emitted this
    /// scan. Empty if no 应朽 parts were detected.
    pub tombstones_emitted: Vec<NodeHash>,
    /// Cycle at which the scan ran.
    pub at_cycle: u64,
}

/// Whether to run prune scan this cycle. Returns true iff
/// `cycle_counter % PRUNE_SCAN_DEEP_CYCLE_INTERVAL == 0` AND cycle > 0
/// (cycle 0 has no eligible candidates).
pub fn should_run_prune_scan(cycle_counter: u64) -> bool {
    cycle_counter > 0 && cycle_counter % PRUNE_SCAN_DEEP_CYCLE_INTERVAL == 0
}

/// **v3.1.1 P07 §3.1** — execute one prune-scan over the registered
/// rules. For each candidate produced by each rule, emit an
/// `internal_mortality_event:{category}` DAG tombstone per P07 §3.3.
///
/// Returns the report so the caller can wire observatory metrics + save
/// DAG state in one go.
///
/// **Determinism**: rules run in registration order; candidates within
/// a rule are emitted in scan order. This makes the prune sequence
/// fully reproducible from `(DAG_state, cycle)` — important for I3
/// self-validation.
pub(crate) fn run_prune_scan(
    state: &mut ServerState,
    current_cycle: u64,
) -> Result<PruneScanReport, SubstrateError> {
    let mut report = PruneScanReport {
        rules_run: Vec::new(),
        tombstones_emitted: Vec::new(),
        at_cycle: current_cycle,
    };

    // Snapshot rules first to avoid borrow conflicts (registry borrow vs
    // state mutation in tombstone emission).
    //
    // Note: state.prune_registry is &mut ServerState; we collect rule
    // references first then iterate without holding the registry borrow
    // during DAG mutation.
    let rule_snapshots: Vec<(&'static str, &'static str, fn(&ServerState, u64) -> Vec<PruneCandidate>)> = state
        .prune_registry
        .rules()
        .map(|r| (r.rule_id, r.category, r.detect))
        .collect();

    for (rule_id, category, detect_fn) in rule_snapshots {
        report.rules_run.push(rule_id);

        // Snapshot candidates (each detect_fn takes &ServerState, no mutation).
        let candidates = detect_fn(state, current_cycle);

        // Emit one tombstone per candidate.
        for cand in candidates {
            let tombstone = emit_internal_mortality_event(
                state,
                category,
                rule_id,
                &cand.part_hash,
                &cand.part_node_type,
                &cand.reason,
                None, // seed rule has no "replaced_by"; future rules may set
                current_cycle,
            )?;
            report.tombstones_emitted.push(tombstone);
        }
    }

    Ok(report)
}

/// Emit a single `internal_mortality_event:{category}` tombstone into the
/// DAG. This is the ONLY supported path for declaring an internal-mortality
/// act; direct DAG-node removal without going through this path is a C55
/// silent_internal_mortality violation.
///
/// Returns the hash of the emitted tombstone node.
pub(crate) fn emit_internal_mortality_event(
    state: &mut ServerState,
    category: &str,
    rule_id: &str,
    killed_part_hash: &[u8; 32],
    killed_part_node_type: &str,
    reason: &str,
    replaced_by_hash: Option<&[u8; 32]>,
    emitted_at_cycle: u64,
) -> Result<NodeHash, SubstrateError> {
    let content = encode_internal_mortality_event(
        category,
        rule_id,
        killed_part_hash,
        killed_part_node_type,
        reason,
        replaced_by_hash,
        emitted_at_cycle,
    );

    // Tombstone parent: current DAG tip + the killed-part hash itself
    // (preserves the causal link from death → the dead).
    let mut parents: Vec<NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let killed_node_hash = NodeHash::from_bytes(*killed_part_hash);
    if !parents.contains(&killed_node_hash) {
        parents.push(killed_node_hash);
    }

    let node_type = internal_mortality_event_node_type(category);
    let h = state
        .dag
        .insert_node(parents, node_type, emitted_at_cycle, content)
        .map_err(|e| {
            SubstrateError::Protocol(format!("internal_mortality_event DAG insert: {e}"))
        })?;

    Ok(h)
}

// ---------------------------------------------------------------------------
// Observatory helpers (used by observatory.rs)
// ---------------------------------------------------------------------------

/// Count of `internal_mortality_event:*` DAG nodes within the given
/// rolling cycle window. Used by L2/OBSERVABILITY metric
/// `internal_mortality_event_density_per_cycle`.
pub(crate) fn count_internal_mortality_events_since(
    state: &ServerState,
    earliest_cycle: u64,
) -> u64 {
    state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with(NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX))
        .filter(|n| n.created_at_cycle >= earliest_cycle)
        .count() as u64
}

/// **v3.1.1 Sprint 5.G (T2.6)** — count of resurrected parts: nodes whose
/// `content_canonical_bytes` exactly matches a previously-killed part's
/// content_canonical_bytes (i.e., a part the prune-scan retired but which
/// has been re-added under a new node hash because external operator
/// behavior re-supplied the same content).
///
/// Algorithm: O(tombstones × dag_node_count × bytes). For each tombstone
/// in the DAG, decode its killed_part_hash → look up that node's
/// content_canonical_bytes → scan all later DAG nodes for byte-equal
/// content. Resurrected = count of post-tombstone nodes with matching bytes.
///
/// Per P07 §8.3 (false_positive_prune_rate metric): too-eager pruning is
/// a real failure mode. A non-zero count surfaces an over-aggressive
/// prune rule that's killing parts the substrate still needs.
///
/// Returns `(resurrected_count, tombstone_count)`. The ratio is the
/// observable metric.
///
/// `pub(crate)`: this helper takes `&ServerState` (itself `pub(crate)`), so a
/// `pub` signature would leak a private type and trip rustc's
/// `private_interfaces` lint. It is consumed internally by the observatory
/// (`observatory.rs`) and by a same-crate unit test in this module's
/// `#[cfg(test)] mod tests`.
pub(crate) fn count_prune_resurrections(state: &ServerState) -> (u64, u64) {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};

    // Step 1: collect tombstones with their killed_part content_canonical_bytes.
    // Build a map of (killed_part_content_bytes → cycle of tombstone) so we
    // can detect "node with matching content emerged AFTER tombstone".
    let mut tombstone_count: u64 = 0;
    let mut killed_contents: Vec<(Vec<u8>, u64)> = Vec::new(); // (content_bytes, tombstone_cycle)
    for tombstone in state.dag.iter_in_insertion_order() {
        if !tombstone
            .node_type
            .starts_with(NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX)
        {
            continue;
        }
        tombstone_count += 1;
        // Decode tombstone content → killed_part_hash
        let tomb_content = tombstone.content_canonical_bytes.as_ref();
        let decoded = match cb_decode(tomb_content) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let map = match decoded {
            CbV::Map(m) => m,
            _ => continue,
        };
        let killed_hash_bytes = match map.get("killed_part_hash") {
            Some(CbV::Bytes(b)) if b.len() == 32 => {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                arr
            }
            _ => continue,
        };
        // Find the killed part in DAG by node hash.
        for node in state.dag.iter_in_insertion_order() {
            if node.hash.as_ref() == killed_hash_bytes.as_ref() {
                killed_contents.push((
                    node.content_canonical_bytes.as_ref().to_vec(),
                    tombstone.created_at_cycle,
                ));
                break;
            }
        }
    }

    // Step 2: scan post-tombstone DAG nodes for byte-equal content matches.
    // Exclude tombstones themselves (they reference the killed bytes in
    // their content) and the killed parts themselves.
    let mut resurrected: u64 = 0;
    for (killed_bytes, tombstone_cycle) in &killed_contents {
        for node in state.dag.iter_in_insertion_order() {
            // Skip nodes created before/at the tombstone.
            if node.created_at_cycle <= *tombstone_cycle {
                continue;
            }
            // Skip the tombstones themselves (their content references but
            // doesn't equal the killed bytes).
            if node
                .node_type
                .starts_with(NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX)
            {
                continue;
            }
            if node.content_canonical_bytes.as_ref() == killed_bytes.as_slice() {
                resurrected += 1;
                // Count each tombstone's resurrection once; break inner loop.
                break;
            }
        }
    }

    (resurrected, tombstone_count)
}

/// Count of `raw_material:*` DAG nodes within the given rolling cycle
/// window. Used to compute the `hoarding_indicator` ratio: high ingestion
/// + low prune-density over the window = hoarding pattern.
pub(crate) fn count_raw_material_since(state: &ServerState, earliest_cycle: u64) -> u64 {
    state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with("raw_material:"))
        .filter(|n| n.created_at_cycle >= earliest_cycle)
        .count() as u64
}

/// Hoarding indicator: returns `true` iff over the recent window
/// (`HOARDING_INDICATOR_WINDOW_CYCLES` cycles back) the substrate has
/// ingested raw_material at non-trivial rate (>= `HOARDING_INDICATOR_INGESTION_FLOOR`)
/// BUT emitted < `HOARDING_INDICATOR_MORTALITY_FLOOR` internal_mortality_events.
///
/// **NOTE**: this is a CONSERVATIVE first signal — false negatives are
/// expected (a substrate could be in early life when no parts have aged
/// into 应朽 yet). L1 may refine via SSoT thresholds.
///
/// Per L1/HARD_RULES §1.4 anticipated C54.
pub const HOARDING_INDICATOR_WINDOW_CYCLES: u64 = 200;
/// Below this raw_material count, the substrate has no ingestion to
/// hoard — signal is silent. Above this, prune absence is meaningful.
pub const HOARDING_INDICATOR_INGESTION_FLOOR: u64 = 10;
/// Min internal_mortality_events expected in the window if ingestion was
/// non-trivial. Below this = hoarding.
pub const HOARDING_INDICATOR_MORTALITY_FLOOR: u64 = 1;

/// Returns `true` if the substrate is currently in a hoarding pattern
/// per the criteria above.
pub(crate) fn is_hoarding(state: &ServerState, current_cycle: u64) -> bool {
    let earliest = current_cycle.saturating_sub(HOARDING_INDICATOR_WINDOW_CYCLES);

    // Window must cover at least one full window-worth of substrate life.
    if current_cycle < HOARDING_INDICATOR_WINDOW_CYCLES {
        return false;
    }

    let ingested = count_raw_material_since(state, earliest);
    let pruned = count_internal_mortality_events_since(state, earliest);

    ingested >= HOARDING_INDICATOR_INGESTION_FLOOR
        && pruned < HOARDING_INDICATOR_MORTALITY_FLOOR
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn should_run_prune_scan_respects_cadence() {
        assert!(!should_run_prune_scan(0));
        assert!(!should_run_prune_scan(1));
        assert!(!should_run_prune_scan(99));
        assert!(should_run_prune_scan(100));
        assert!(!should_run_prune_scan(101));
        assert!(should_run_prune_scan(200));
        assert!(should_run_prune_scan(1000));
    }

    #[test]
    fn p10_invariant_protected_set_includes_critical_node_types() {
        assert!(is_p10_invariant_protected("genesis_event:abc"));
        assert!(is_p10_invariant_protected("l0_revision_attested:xyz"));
        assert!(is_p10_invariant_protected("tip_cosigned:abc"));
        assert!(is_p10_invariant_protected("internal_mortality_event:无用"));
        assert!(!is_p10_invariant_protected("raw_material:user_paste"));
        assert!(!is_p10_invariant_protected("sporocarp:axis_fruited"));
    }

    #[test]
    fn registry_default_includes_seed_rule() {
        let reg = PruneRuleRegistry::seed();
        assert_eq!(reg.rule_count(), 1);
        assert_eq!(reg.rules().next().unwrap().rule_id, "L0.seed.orphan_past_grace");
        assert_eq!(reg.rules().next().unwrap().category, "无用");
    }

    #[test]
    fn registry_register_appends() {
        fn dummy_detect(_: &ServerState, _: u64) -> Vec<PruneCandidate> {
            Vec::new()
        }
        let mut reg = PruneRuleRegistry::seed();
        reg.register(PruneRule {
            rule_id: "L1.test.dummy",
            category: "测试",
            description: "test",
            detect: dummy_detect,
        });
        assert_eq!(reg.rule_count(), 2);
    }

    #[test]
    fn hoarding_thresholds_are_defined() {
        assert_eq!(HOARDING_INDICATOR_WINDOW_CYCLES, 200);
        assert_eq!(HOARDING_INDICATOR_INGESTION_FLOOR, 10);
        assert_eq!(HOARDING_INDICATOR_MORTALITY_FLOOR, 1);
    }

    /// **v3.1.1 Sprint 5.G (T2.6)** — direct unit-style test of the
    /// `count_prune_resurrections` helper.
    ///
    /// Relocated from the substrate E2E integration suite: an external
    /// integration-test binary cannot see the `pub(crate)`
    /// `count_prune_resurrections` (it takes `pub(crate) ServerState`), so the
    /// check lives here as a same-crate unit test. Construct an in-memory
    /// `ServerState` over a fresh, empty `Dag` and confirm the count function
    /// handles the no-tombstone case safely: with no tombstones there are no
    /// killed contents to compare against, so both the resurrection count and
    /// the tombstone total are necessarily 0.
    #[test]
    fn count_prune_resurrections_handles_empty_dag_safely() {
        use crate::persistence::Manifest;
        use crate::server::ServerState;
        use myco_kernel_schema::dag::Dag;

        // A throwaway state dir; ServerState::new only reads on-disk file
        // sizes to seed its cost accumulator, which yields zeros for a dir
        // with no state files yet.
        let state_dir = std::env::temp_dir().join(format!(
            "myco-prune-unit-{}-{:x}",
            std::process::id(),
            &0u8 as *const u8 as usize as u64
        ));
        let state = ServerState::new(
            state_dir,
            Manifest::genesis(),
            Dag::new(),
            None,
            [0u8; 32],
        );

        let (resurrected, total_tombstones) = count_prune_resurrections(&state);

        // No tombstones → resurrection count is necessarily 0 (no killed
        // contents to compare against).
        assert_eq!(resurrected, 0);
        assert_eq!(total_tombstones, 0);
    }
}
