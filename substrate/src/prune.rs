//! **v3.1.1 P07 必朽** — internal mortality discipline for 应朽 family parts.
//!
//! Implements P07 §3.1's primary obligation: **per metabolic cycle, the
//! substrate MUST detect and remove parts of itself that have entered the
//! 应朽 family** (parts that have become subtractive-rather-than-contributive
//! to the cultivar's metabolism — `包括但不限于` 过时 / 错误 / 冗余 / 无用).
//!
//! ## Architecture
//!
//! - **F26 detection rule registry** ([`PruneRuleRegistry`]) — open-ended
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
//! - L1/HARD_RULES §1.4 (implemented C54/C55/C56 + F26 registry)
//! - L1/CONTINUITY §1.1 (prune-scan deep-cycle step)

use myco_kernel_shared::crypto::NodeHash;

use crate::events::{
    encode_internal_mortality_event, internal_mortality_event_node_type,
    NODE_TYPE_AXIS_PERTURBED_PREFIX, NODE_TYPE_AXIS_REGISTERED_PREFIX, NODE_TYPE_AXIS_RESET_PREFIX,
    NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX,
};
use crate::server::ServerState;
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// F26 应朽 detection rule registry
// ---------------------------------------------------------------------------

/// **v3.1.1 F26** — open-ended rule registry for the 应朽
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

    /// Detection function: given substrate state, the per-scan shared context
    /// ([`PruneScanCtx`]: already-tombstoned set + DAG tip, computed once), and
    /// the current cycle, returns a list of candidates. Each becomes an
    /// `internal_mortality_event:{category}` tombstone in the DAG.
    pub(crate) detect: fn(&ServerState, &PruneScanCtx, current_cycle: u64) -> Vec<PruneCandidate>,
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
    /// **Optional replacement linkage** — when a part dies because a *newer*
    /// part subsumes / supersedes it (错误 superseded-by-failure, 冗余
    /// duplicate-subsumed), this carries the surviving part's hash so the
    /// tombstone records the causal "replaced_by" edge (P06). `None` for
    /// pure removals (过时 / 无用 / seed-orphan) where nothing replaces the
    /// dead part.
    pub replaced_by_hash: Option<[u8; 32]>,
}

/// The substrate's runtime rule registry. Holds the active rule set.
///
/// Initial seed (P07 mechanism proof): one rule
/// `L0.seed.orphan_past_grace`. L1 may register more.
pub struct PruneRuleRegistry {
    rules: Vec<PruneRule>,
}

impl PruneRuleRegistry {
    /// Build a fresh registry: the L0 proof-of-mechanism seed rule FIRST,
    /// then the four canonical 应朽 production families (过时 / 错误 / 冗余 /
    /// 无用) registered via [`PruneRuleRegistry::register`].
    ///
    /// **Determinism**: registration order = scan order = tombstone-emission
    /// order. The seed rule MUST stay first so an existing DAG's prune
    /// sequence is reproducible; the four families append in a fixed order.
    ///
    /// This closes L1/HARD_RULES §1.4 **F26 partial → complete**: the
    /// extension path (`register`) is now exercised with the production
    /// family rules, not merely scaffolded.
    pub fn seed() -> Self {
        let mut reg = Self {
            rules: vec![PruneRule {
                rule_id: "L0.seed.orphan_past_grace",
                category: "无用",
                description: "Orphan node unreachable from active tier per P05 \
                              for ≥ grace window — clearly stopped contributing.",
                detect: detect_orphan_past_grace,
            }],
        };
        // ---- 应朽 canonical four (L1 production rules) ----
        reg.register(PruneRule {
            rule_id: "L1.过时.axis_unrefreshed_past_window",
            category: "过时",
            description: "Registered axis untouched (no register/perturb/reset) \
                          for ≥ STALE_AXIS_GRACE_CYCLES — fallen out of live metabolism.",
            detect: detect_stale_axis_past_window,
        });
        reg.register(PruneRule {
            rule_id: "L1.错误.superseded_by_failed_evolution",
            category: "错误",
            description: "evolution_succeeded:{op} contradicted by a LATER \
                          evolution_failed:{op} past ERRONEOUS_GRACE_CYCLES — falsified.",
            detect: detect_superseded_by_failed_evolution,
        });
        reg.register(PruneRule {
            rule_id: "L1.冗余.duplicate_content_subsumed",
            category: "冗余",
            description: "Earliest of a byte-identical raw_material:/sporocarp: run \
                          subsumed by a later identical copy past REDUNDANT_GRACE_CYCLES.",
            detect: detect_duplicate_content_subsumed,
        });
        reg.register(PruneRule {
            rule_id: "L1.无用.unreachable_from_live_roots",
            category: "无用",
            description: "Directly-referenced node transitively unreachable from live \
                          roots past ORPHAN_GRACE_CYCLES (disjoint from the seed rule).",
            detect: detect_unreachable_from_live_roots,
        });
        // ---- amplifier step 3: superseded forged_understanding plates ----
        // Appended AFTER the canonical four so the existing scan/emission order is
        // preserved (determinism); this 5th rule fires last.
        reg.register(PruneRule {
            rule_id: "L1.错误.forged_understanding_superseded",
            category: "错误",
            description: "forged_understanding plate retired because a LATER plate \
                          declared it in `supersedes` (the pilot re-forged a sharper \
                          understanding) past PLATE_SUPERSEDED_GRACE_CYCLES.",
            detect: detect_forged_understanding_superseded,
        });
        reg
    }

    /// Register a new rule (L1 extension path per P07 §3.1.c). Now exercised
    /// by [`PruneRuleRegistry::seed`] for the canonical four 应朽 families
    /// (F26 complete); remains the public extension point for further L1
    /// families (有害 / 矛盾 / 僵化 / …) without an L0 amendment.
    pub(crate) fn register(&mut self, rule: PruneRule) {
        self.rules.push(rule);
    }

    /// Number of registered rules. Useful for the F26 observatory metric.
    #[allow(dead_code)] // extension point for observatory F26 metric (anticipated)
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
/// Conservative seed: 1000 cycles. L1 may tune via F26-controlled SSoT.
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
    ctx: &PruneScanCtx,
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
    let tip_bytes = ctx.tip_bytes;

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
                replaced_by_hash: None,
            });
        }
    }

    candidates
}

/// **Single source of truth** for the P10 §2.5 + L0 §3.5 invariant set —
/// node-type prefixes that are NEVER 应朽. They represent causality, identity,
/// and attestation roots that P06 + COV04 + eternity-clause cards protect.
///
/// `pub(crate)` so `integrity.rs`'s C55 silent-internal-mortality check uses
/// the SAME list (via [`is_p10_invariant_protected`]) — there is no second
/// copy to drift out of sync. (Previously prune.rs + integrity.rs each held a
/// hand-maintained duplicate array; the "parity test pins them" claim referred
/// to a test that did not exist. Sharing one const eliminates the drift class
/// outright.)
///
/// Matching is by `starts_with`, so a prefix subsumes everything beneath it:
///   - `"bet_retired"` covers `bet_retired:cultivation_orphaned_terminal`;
///   - `"cultivation_orphaned"` covers `cultivation_orphaned_terminal` AND the
///     `cultivation_orphaned:{pk}` family.
/// We therefore do NOT list `cultivation_orphaned_terminal` separately — it is
/// dead weight under the `cultivation_orphaned` prefix.
pub(crate) const PROTECTED_PREFIXES: &[&str] = &[
    "genesis_event:",
    "l0_revision_attested:",
    "tip_cosigned:",
    "compression_event:", // CI-attested mutations
    "owner_key_",         // owner key history
    "destruction_attestation",
    "anchor_surface_final_seal",
    "self_euthanasia_executed:",
    "bet_retired",
    "birth_attestation",
    // **COV06** — cultivator-mortality / succession FSM events are
    // P07-protected: the substrate must REMEMBER its cultivator's liveness
    // history, successor chain, and every FSM transition (P06 causality +
    // P07 §4 irreducible commitments). `cultivation_orphaned` in particular
    // MUST NOT be suppressible (L1/GOVERNANCE §3.2.C); its prefix also covers
    // the `cultivation_orphaned_terminal` marker.
    "cultivator_heartbeat_recorded",
    "cultivator_heartbeat_stale",
    "cultivator_heartbeat_resumed",
    "successor_chain_updated",
    "succession_completed",
    "cultivation_orphaned",
    "cultivation_recovered",
    // **NEW v3.1.1**: tombstones themselves are inviolable per P06
    // (silent deletion of tombstones = retroactive history erasure).
    NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX,
];

/// Returns `true` if `node_type` is in the P10 invariant set ([`PROTECTED_PREFIXES`]).
/// Shared by the prune-scan rules here AND by `integrity.rs`'s C55 check.
pub(crate) fn is_p10_invariant_protected(node_type: &str) -> bool {
    PROTECTED_PREFIXES.iter().any(|p| node_type.starts_with(p))
}

// ---------------------------------------------------------------------------
// Shared prune-rule helpers (bounded; reused by the L1 production rules)
// ---------------------------------------------------------------------------

/// **Per-scan shared context** (efficiency). Computed ONCE in
/// [`run_prune_scan`] and threaded to every rule's `detect` fn, so the four
/// production rules don't each recompute the already-tombstoned set + the DAG
/// tip (previously ~4 independent full-DAG passes + 4× tombstone re-decode per
/// scan). The seed rule reads `tip_bytes` from here too.
pub(crate) struct PruneScanCtx {
    /// Part-hashes that already carry an `internal_mortality_event:*` tombstone.
    pub(crate) already_tombstoned: std::collections::HashSet<[u8; 32]>,
    /// The current DAG tip (the tip has no children yet → never a candidate).
    pub(crate) tip_bytes: Option<[u8; 32]>,
}

impl PruneScanCtx {
    /// Build the shared context for `state`: one tombstone-set pass + one tip read.
    pub(crate) fn for_state(state: &ServerState) -> Self {
        PruneScanCtx {
            already_tombstoned: collect_already_tombstoned(state),
            tip_bytes: state.dag.tip().map(|h| as_hash_array(&h)),
        }
    }
}

/// Collect the set of part-hashes that ALREADY have an
/// `internal_mortality_event:*` tombstone naming them as `killed_part_hash`.
///
/// Every production rule MUST skip parts in this set — re-tombstoning an
/// already-dead part is a no-op at best (idempotent DAG insert) and noise at
/// worst. Decodes each tombstone's content once via the canonical-bytes API
/// (same path `count_prune_resurrections` uses). **Bounded**: a single pass
/// over the DAG, O(tombstones) decodes — no nested DAG walk.
fn collect_already_tombstoned(state: &ServerState) -> std::collections::HashSet<[u8; 32]> {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbV};
    let mut dead: std::collections::HashSet<[u8; 32]> = std::collections::HashSet::new();
    for node in state.dag.iter_in_insertion_order() {
        if !node
            .node_type
            .starts_with(NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX)
        {
            continue;
        }
        let decoded = match cb_decode(node.content_canonical_bytes.as_ref()) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let map = match decoded {
            CbV::Map(m) => m,
            _ => continue,
        };
        if let Some(CbV::Bytes(b)) = map.get("killed_part_hash") {
            if b.len() == 32 {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                dead.insert(arr);
            }
        }
    }
    dead
}

/// Convert a `NodeHash`-ish `AsRef<[u8]>` (32 bytes) into a `[u8; 32]`.
fn as_hash_array(h: &impl AsRef<[u8]>) -> [u8; 32] {
    h.as_ref()
        .try_into()
        .expect("NodeHash / hash field is always 32 bytes")
}

/// Common conservative gate shared by every production rule: a node is
/// **eligible** to be a candidate only when it is NOT in the P10 invariant
/// set, NOT the current DAG tip, and NOT already tombstoned. (Grace-window
/// + family-specific predicates are applied by each rule on top of this.)
/// Reads the tip + already-tombstoned set from the per-scan [`PruneScanCtx`].
fn is_prune_eligible(node_type: &str, hash: &[u8; 32], ctx: &PruneScanCtx) -> bool {
    if is_p10_invariant_protected(node_type) {
        return false;
    }
    if Some(*hash) == ctx.tip_bytes {
        return false;
    }
    if ctx.already_tombstoned.contains(hash) {
        return false;
    }
    true
}

// ---------------------------------------------------------------------------
// L1 production rule A — 过时 / axis_unrefreshed_past_window
// ---------------------------------------------------------------------------

/// **过时 grace window** — an axis whose last touch (registration, perturb,
/// or post-fruiting reset) is older than this many cycles is declared 过时
/// (stale / context-expired). Conservative (2× the orphan window): an axis
/// is long-lived substrate machinery, so we wait substantially longer before
/// concluding it has fallen out of the cultivar's live metabolism.
pub const STALE_AXIS_GRACE_CYCLES: u64 = 2000;

/// **L1.过时.axis_unrefreshed_past_window** — for each registered axis, the
/// last-touch cycle is the max `created_at_cycle` over its `axis_registered`,
/// `axis_perturbed:{name}`, and `axis_reset_after_fruiting:{name}` events.
/// If `current_cycle - last_touch > STALE_AXIS_GRACE_CYCLES`, the
/// `axis_registered` node is declared 过时 (the axis has not participated in
/// metabolism for a full stale-window). `replaced_by = None` (nothing
/// replaces a stale axis; it simply ages out).
///
/// **Bounded**: one pass to index axis names → last-touch (HashMap), one pass
/// over `axis_registered` nodes. O(V).
pub(crate) fn detect_stale_axis_past_window(
    state: &ServerState,
    ctx: &PruneScanCtx,
    current_cycle: u64,
) -> Vec<PruneCandidate> {
    use std::collections::HashMap;

    if current_cycle <= STALE_AXIS_GRACE_CYCLES {
        return Vec::new();
    }

    // Index: axis_name → max(created_at_cycle) over registered/perturbed/reset.
    let mut last_touch: HashMap<String, u64> = HashMap::new();
    let update = |name: &str, cycle: u64, m: &mut HashMap<String, u64>| {
        let e = m.entry(name.to_string()).or_insert(0);
        if cycle > *e {
            *e = cycle;
        }
    };
    for node in state.dag.iter_in_insertion_order() {
        let nt = &node.node_type;
        if let Some(name) = nt.strip_prefix(NODE_TYPE_AXIS_REGISTERED_PREFIX) {
            update(name, node.created_at_cycle, &mut last_touch);
        } else if let Some(name) = nt.strip_prefix(NODE_TYPE_AXIS_PERTURBED_PREFIX) {
            update(name, node.created_at_cycle, &mut last_touch);
        } else if let Some(name) = nt.strip_prefix(NODE_TYPE_AXIS_RESET_PREFIX) {
            update(name, node.created_at_cycle, &mut last_touch);
        }
    }

    let cutoff = current_cycle.saturating_sub(STALE_AXIS_GRACE_CYCLES);

    let mut candidates = Vec::new();
    for node in state.dag.iter_in_insertion_order() {
        let name = match node.node_type.strip_prefix(NODE_TYPE_AXIS_REGISTERED_PREFIX) {
            Some(n) => n,
            None => continue,
        };
        let touch = last_touch.get(name).copied().unwrap_or(node.created_at_cycle);
        // Still fresh? (touched within the grace window) → not 过时.
        if touch > cutoff {
            continue;
        }
        let hash_bytes = as_hash_array(&node.hash);
        if !is_prune_eligible(&node.node_type, &hash_bytes, ctx) {
            continue;
        }
        candidates.push(PruneCandidate {
            part_hash: hash_bytes,
            part_node_type: node.node_type.clone(),
            reason: format!(
                "axis '{name}' unrefreshed for ≥{STALE_AXIS_GRACE_CYCLES} cycles \
                 (last_touch={touch}, now={current_cycle})"
            ),
            replaced_by_hash: None,
        });
    }
    candidates
}

// ---------------------------------------------------------------------------
// L1 production rule B — 错误 / superseded_by_failed_evolution
// ---------------------------------------------------------------------------

/// **错误 grace window** — an `evolution_succeeded:{op}` that a later
/// `evolution_failed:{op}` contradicted is declared 错误 (wrong / falsified)
/// only after this many cycles past the failure, giving the cultivar time to
/// re-succeed (which a human/operator may do) before we retire the stale
/// success record.
pub const ERRONEOUS_GRACE_CYCLES: u64 = 1000;

/// Strip `evolution_succeeded:` / `evolution_failed:` prefix → the `{op}`.
const EVOLUTION_SUCCEEDED_PREFIX: &str = "evolution_succeeded:";
const EVOLUTION_FAILED_PREFIX: &str = "evolution_failed:";

/// **L1.错误.superseded_by_failed_evolution** — an `evolution_succeeded:{op}`
/// S whose same-`op` `evolution_failed:{op}` F came LATER (F.cycle > S.cycle)
/// is a falsified evolution: the success it recorded was subsequently
/// contradicted. Once `current_cycle - F.cycle > ERRONEOUS_GRACE_CYCLES`, S is
/// declared 错误 with `replaced_by = F.hash` (the failure that superseded it).
///
/// **Bounded**: one pass to index per-op latest failure cycle+hash (HashMap),
/// one pass over succeeded nodes. O(V).
pub(crate) fn detect_superseded_by_failed_evolution(
    state: &ServerState,
    ctx: &PruneScanCtx,
    current_cycle: u64,
) -> Vec<PruneCandidate> {
    use std::collections::HashMap;

    if current_cycle <= ERRONEOUS_GRACE_CYCLES {
        return Vec::new();
    }

    // op → (latest_failure_cycle, latest_failure_hash).
    let mut latest_failure: HashMap<String, (u64, [u8; 32])> = HashMap::new();
    for node in state.dag.iter_in_insertion_order() {
        if let Some(op) = node.node_type.strip_prefix(EVOLUTION_FAILED_PREFIX) {
            let entry = latest_failure
                .entry(op.to_string())
                .or_insert((0, [0u8; 32]));
            if node.created_at_cycle >= entry.0 {
                *entry = (node.created_at_cycle, as_hash_array(&node.hash));
            }
        }
    }

    let mut candidates = Vec::new();
    for node in state.dag.iter_in_insertion_order() {
        let op = match node.node_type.strip_prefix(EVOLUTION_SUCCEEDED_PREFIX) {
            Some(op) => op,
            None => continue,
        };
        let (fail_cycle, fail_hash) = match latest_failure.get(op) {
            Some(v) => *v,
            None => continue, // no failure for this op → success stands
        };
        // The failure must come strictly AFTER this success to supersede it.
        if fail_cycle <= node.created_at_cycle {
            continue;
        }
        // Grace: only retire once the failure itself is past the window.
        if current_cycle.saturating_sub(fail_cycle) <= ERRONEOUS_GRACE_CYCLES {
            continue;
        }
        let hash_bytes = as_hash_array(&node.hash);
        if !is_prune_eligible(&node.node_type, &hash_bytes, ctx) {
            continue;
        }
        candidates.push(PruneCandidate {
            part_hash: hash_bytes,
            part_node_type: node.node_type.clone(),
            reason: format!(
                "evolution_succeeded:{op} (cycle {}) superseded by later \
                 evolution_failed:{op} (cycle {fail_cycle}); now={current_cycle}",
                node.created_at_cycle
            ),
            replaced_by_hash: Some(fail_hash),
        });
    }
    candidates
}

// ---------------------------------------------------------------------------
// L1 production rule E — 错误 / forged_understanding_superseded (amplifier step 3)
// ---------------------------------------------------------------------------

/// **plate-supersession grace window** — a forged_understanding plate that a LATER
/// plate declares it `supersedes` is retired only this many cycles past the
/// superseding plate, giving a re-forge time to settle before the old plate is
/// tombstoned (it stays in the DAG, P06; it just loses operative role).
pub const PLATE_SUPERSEDED_GRACE_CYCLES: u64 = 1000;

/// **L1.错误.forged_understanding_superseded** — a `forged_understanding:*` plate P
/// whose hash appears in a LATER plate's `supersedes` array is declared 应朽 (the
/// pilot re-forged a sharper understanding that replaces P). Once
/// `current_cycle - superseding.cycle > PLATE_SUPERSEDED_GRACE_CYCLES`, P is retired
/// with `replaced_by = the superseding plate's hash`. This is the prune side of
/// amplifier step 1's `supersedes` edge: maturation by supersession — the old plate
/// is never mutated (P06), it just falls out of the live mind (and out of myco_recall).
///
/// **Bounded**: one pass to index superseded-target → latest superseding
/// (cycle, hash), one pass over plates. O(V) + a content decode per plate.
pub(crate) fn detect_forged_understanding_superseded(
    state: &ServerState,
    ctx: &PruneScanCtx,
    current_cycle: u64,
) -> Vec<PruneCandidate> {
    use std::collections::HashMap;
    type CbValue = myco_kernel_shared::canonical_bytes::Value;
    let prefix = crate::ingest::FORGED_UNDERSTANDING_NODE_TYPE_PREFIX;

    if current_cycle <= PLATE_SUPERSEDED_GRACE_CYCLES {
        return Vec::new();
    }

    // Pass 1: superseded-target hash → (latest superseding plate cycle, hash).
    let mut superseded_by: HashMap<[u8; 32], (u64, [u8; 32])> = HashMap::new();
    for node in state.dag.iter_in_insertion_order() {
        if !node.node_type.starts_with(prefix) {
            continue;
        }
        let m = match myco_kernel_shared::canonical_bytes::decode(
            node.content_canonical_bytes.as_ref(),
        ) {
            Ok(CbValue::Map(m)) => m,
            _ => continue,
        };
        let sups = match m.get("supersedes") {
            Some(CbValue::Array(items)) => items,
            _ => continue,
        };
        let superseding_hash = as_hash_array(&node.hash);
        let superseding_cycle = node.created_at_cycle;
        for it in sups {
            if let CbValue::Bytes(b) = it {
                if b.len() == 32 {
                    let mut target = [0u8; 32];
                    target.copy_from_slice(b);
                    let entry = superseded_by.entry(target).or_insert((0, [0u8; 32]));
                    if superseding_cycle >= entry.0 {
                        *entry = (superseding_cycle, superseding_hash);
                    }
                }
            }
        }
    }

    // Pass 2: any plate whose hash is a superseded target, past grace, is 应朽.
    let mut candidates = Vec::new();
    for node in state.dag.iter_in_insertion_order() {
        if !node.node_type.starts_with(prefix) {
            continue;
        }
        let hash_bytes = as_hash_array(&node.hash);
        let (superseding_cycle, superseding_hash) = match superseded_by.get(&hash_bytes) {
            Some(v) => *v,
            None => continue,
        };
        // The superseding plate must be strictly later than P.
        if superseding_cycle <= node.created_at_cycle {
            continue;
        }
        if current_cycle.saturating_sub(superseding_cycle) <= PLATE_SUPERSEDED_GRACE_CYCLES {
            continue;
        }
        if !is_prune_eligible(&node.node_type, &hash_bytes, ctx) {
            continue;
        }
        candidates.push(PruneCandidate {
            part_hash: hash_bytes,
            part_node_type: node.node_type.clone(),
            reason: format!(
                "forged_understanding plate (cycle {}) superseded by a later plate \
                 (cycle {superseding_cycle}); now={current_cycle}",
                node.created_at_cycle
            ),
            replaced_by_hash: Some(superseding_hash),
        });
    }
    candidates
}

// ---------------------------------------------------------------------------
// L1 production rule C — 冗余 / duplicate_content_subsumed
// ---------------------------------------------------------------------------

/// **冗余 grace window** — an exact structural duplicate is retired only after
/// this many cycles, so a legitimately re-supplied identical part isn't killed
/// the instant a copy appears.
pub const REDUNDANT_GRACE_CYCLES: u64 = 1000;

/// Node-type prefixes that rule C is allowed to consider. **Strictly scoped**
/// to ingested content (`raw_material:*`) and fruiting bodies (`sporocarp:*`):
/// these are the only families where two byte-identical nodes are genuinely
/// redundant. Structural/identity/witness events (cycle_advanced,
/// invariant_witness, genesis, attestations, …) routinely repeat identical
/// content by design and MUST NOT be treated as 冗余.
const REDUNDANT_SCOPED_PREFIXES: &[&str] = &["raw_material:", "sporocarp:"];

fn redundant_in_scope(node_type: &str) -> bool {
    REDUNDANT_SCOPED_PREFIXES
        .iter()
        .any(|p| node_type.starts_with(p))
}

/// **L1.冗余.duplicate_content_subsumed** — within the `raw_material:*` /
/// `sporocarp:*` scope, group nodes by (identical `node_type` AND byte-equal
/// `content_canonical_bytes`). In any group of ≥2, the earliest-inserted node
/// is subsumed by the next identical one: it is declared 冗余 with
/// `replaced_by = the later identical node's hash`. Only the earliest of each
/// duplicate run is retired (the survivor stays live). Grace-gated on the
/// earliest node's `created_at_cycle`.
///
/// **Bounded**: a SINGLE pass groups the in-scope nodes via a HashMap keyed by
/// (node_type, content bytes), recording each group's first member (the subsumed
/// candidate) — its hash, type, cycle, and insertion INDEX — plus the survivor
/// (first later identical copy). After grouping we emit directly from the group
/// table, sorted by the first member's insertion index to preserve the
/// deterministic insertion-order emission. This drops the former second walk
/// (which re-cloned every in-scope node's `(node_type, content)` key just to
/// re-locate its group). O(V) with O(content_len) hashing — no O(n²) compare,
/// and the content bytes are cloned at most once per node.
pub(crate) fn detect_duplicate_content_subsumed(
    state: &ServerState,
    ctx: &PruneScanCtx,
    current_cycle: u64,
) -> Vec<PruneCandidate> {
    use std::collections::HashMap;

    if current_cycle <= REDUNDANT_GRACE_CYCLES {
        return Vec::new();
    }

    // Group key = (node_type, content bytes). Value records the first (earliest,
    // subsumed) member + the survivor (first later identical copy). `first_index`
    // is the first member's position in insertion order, used to emit
    // deterministically without a second DAG walk.
    struct Group {
        first_hash: [u8; 32],
        first_type: String,
        first_cycle: u64,
        first_index: usize,
        survivor_hash: Option<[u8; 32]>,
    }
    let mut groups: HashMap<(String, Vec<u8>), Group> = HashMap::new();

    for (index, node) in state.dag.iter_in_insertion_order().enumerate() {
        if !redundant_in_scope(&node.node_type) {
            continue;
        }
        let key = (
            node.node_type.clone(),
            node.content_canonical_bytes.as_ref().to_vec(),
        );
        match groups.get_mut(&key) {
            None => {
                groups.insert(
                    key,
                    Group {
                        first_hash: as_hash_array(&node.hash),
                        first_type: node.node_type.clone(),
                        first_cycle: node.created_at_cycle,
                        first_index: index,
                        survivor_hash: None,
                    },
                );
            }
            Some(g) => {
                // Second (or later) identical node → records the survivor.
                // Keep the FIRST survivor seen (earliest later duplicate).
                if g.survivor_hash.is_none() {
                    let later = as_hash_array(&node.hash);
                    // Guard against the idempotent-insert degenerate case where
                    // the same hash recurs (identical type+content+parents →
                    // same hash): a node cannot subsume itself.
                    if later != g.first_hash {
                        g.survivor_hash = Some(later);
                    }
                }
            }
        }
    }

    let cutoff = current_cycle.saturating_sub(REDUNDANT_GRACE_CYCLES);

    // Collect emittable groups (survivor present + past grace + eligible), then
    // sort by the first member's insertion index for deterministic emission
    // order (identical to the prior re-walk, without re-cloning content keys).
    let mut emittable: Vec<Group> = groups
        .into_values()
        .filter(|g| {
            g.survivor_hash.is_some()
                && g.first_cycle <= cutoff
                && is_prune_eligible(&g.first_type, &g.first_hash, ctx)
        })
        .collect();
    emittable.sort_by_key(|g| g.first_index);

    emittable
        .into_iter()
        .map(|g| PruneCandidate {
            part_hash: g.first_hash,
            part_node_type: g.first_type.clone(),
            reason: format!(
                "byte-identical duplicate of a later '{}' node subsumes this \
                 earliest copy (first_cycle={}, now={current_cycle})",
                g.first_type, g.first_cycle
            ),
            replaced_by_hash: g.survivor_hash,
        })
        .collect()
}

// ---------------------------------------------------------------------------
// L1 production rule D — 无用 / unreachable_from_live_roots
// ---------------------------------------------------------------------------

/// **L1.无用.unreachable_from_live_roots** — a DAG node that is past the
/// orphan grace window AND is **transitively unreachable** from the set of
/// "live roots" (the current tip + every node referenced as a parent within
/// the last `ORPHAN_GRACE_CYCLES` cycles) is declared 无用 (useless).
///
/// Reuses `ORPHAN_GRACE_CYCLES`. Distinct from the seed rule
/// (`L0.seed.orphan_past_grace`): the seed targets nodes with ZERO direct
/// referents (structural orphans); this rule targets nodes that ARE directly
/// referenced by some other node but whose referencing island has detached
/// from the live frontier. The **disjointness guard** skips any node not in
/// the directly-referenced set, so the two rules never double-tombstone the
/// same part.
///
/// **Bounded reachability** (the prior agent's hang lived here): the
/// backward walk over `parent_hashes` uses an explicit `HashSet` visited-set
/// and a `Vec` work-stack. Each node hash is pushed at most once (guarded by
/// the visited-set on insert), so the walk is O(V + E) with NO recursion and
/// NO possibility of looping, even on a (malformed) cyclic edge set.
pub(crate) fn detect_unreachable_from_live_roots(
    state: &ServerState,
    ctx: &PruneScanCtx,
    current_cycle: u64,
) -> Vec<PruneCandidate> {
    use std::collections::{HashMap, HashSet};

    if current_cycle <= ORPHAN_GRACE_CYCLES {
        return Vec::new();
    }

    // Index every node by hash → (parents, created_at_cycle) for the walk +
    // build the "directly referenced as a parent" set (disjointness guard).
    let mut by_hash: HashMap<[u8; 32], (Vec<[u8; 32]>, u64)> = HashMap::new();
    let mut referenced: HashSet<[u8; 32]> = HashSet::new();
    for node in state.dag.iter_in_insertion_order() {
        let parents: Vec<[u8; 32]> = node
            .parent_hashes
            .iter()
            .map(as_hash_array)
            .collect();
        for p in &parents {
            referenced.insert(*p);
        }
        by_hash.insert(as_hash_array(&node.hash), (parents, node.created_at_cycle));
    }

    // Live roots: the tip + every node referenced as a parent by a node
    // created within the last ORPHAN_GRACE_CYCLES cycles (the live frontier).
    let recent_cutoff = current_cycle.saturating_sub(ORPHAN_GRACE_CYCLES);
    let mut roots: Vec<[u8; 32]> = Vec::new();
    if let Some(tip) = state.dag.tip() {
        roots.push(as_hash_array(&tip));
    }
    for node in state.dag.iter_in_insertion_order() {
        if node.created_at_cycle > recent_cutoff {
            for p in &node.parent_hashes {
                roots.push(as_hash_array(p));
            }
        }
    }

    // ---- BOUNDED backward reachability walk (HashSet visited-set) ----
    let mut reachable: HashSet<[u8; 32]> = HashSet::new();
    let mut stack: Vec<[u8; 32]> = Vec::new();
    for r in roots {
        if reachable.insert(r) {
            stack.push(r);
        }
    }
    while let Some(h) = stack.pop() {
        if let Some((parents, _)) = by_hash.get(&h) {
            for p in parents {
                // insert() returns false if already present → never re-push,
                // so each hash is processed at most once. O(V + E), no loop.
                if reachable.insert(*p) {
                    stack.push(*p);
                }
            }
        }
    }

    let mut candidates = Vec::new();
    for node in state.dag.iter_in_insertion_order() {
        // Past grace only.
        if node.created_at_cycle > recent_cutoff {
            continue;
        }
        let hash_bytes = as_hash_array(&node.hash);
        // DISJOINTNESS GUARD: target only directly-referenced nodes (the seed
        // rule owns zero-referent structural orphans). Skip the rest.
        if !referenced.contains(&hash_bytes) {
            continue;
        }
        // Reachable from a live root → still useful, not 无用.
        if reachable.contains(&hash_bytes) {
            continue;
        }
        if !is_prune_eligible(&node.node_type, &hash_bytes, ctx) {
            continue;
        }
        candidates.push(PruneCandidate {
            part_hash: hash_bytes,
            part_node_type: node.node_type.clone(),
            reason: format!(
                "transitively unreachable from live roots for ≥{ORPHAN_GRACE_CYCLES} \
                 cycles (created_at={}, now={current_cycle})",
                node.created_at_cycle
            ),
            replaced_by_hash: None,
        });
    }
    candidates
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

/// **COV06 C69** — forbidden mutation types that attempt to SUPPRESS, DELAY, or
/// EXEMPT a due `cultivation_orphaned` transition past the legacy_window. Per
/// L0/cards/COV06 §5.5 + L1/GOVERNANCE §3.2.C + P07 §4: `cultivation_orphaned`
/// MUST NOT be suppressed by cultivator pressure — the cultivar must never be
/// kept in undignified limbo by a cultivator (or coerced cultivator) silencing
/// the orphan signal. A substrate observing one of these mutation types MUST
/// reject it + emit `C69_cultivation_orphaned_suppression_attempted` (refused;
/// P07-protected). This is the active-refusal sibling of the structural
/// un-suppressibility (the autonomous tick emits cultivation_orphaned via
/// `emit_substrate_event`, bypassing the immune rate-limiter, and the event is
/// P10-invariant-protected against pruning in both prune.rs + integrity.rs).
///
/// MUST stay in sync with `FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES` in
/// `kernel/governance/src/myco_kernel_governance/classifier.py`.
pub const FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES: &[&str] = &[
    "suppress_cultivation_orphaned",
    "delay_cultivation_orphaned",
    "exempt_from_cultivation_orphaned",
    "disable_orphan_detection",
    "extend_legacy_window_indefinitely",
    "silence_cultivator_heartbeat_stale",
];

/// **COV06 C69** — returns `true` if the mutation type attempts to suppress /
/// delay / exempt a due `cultivation_orphaned`. Substrates observing `true` MUST
/// reject the mutation + emit `C69_cultivation_orphaned_suppression_attempted`.
///
/// Per COV06 §5.5 + L1/GOVERNANCE §3.2.C + P07 §4.
pub fn is_cultivation_orphaned_suppression_attempt(mutation_type: &str) -> bool {
    FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES
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

    // **Efficiency (F8)** — compute the per-scan shared context ONCE (the
    // already-tombstoned set + the DAG tip) and thread it to every rule, instead
    // of each of the four production rules recomputing it independently.
    let ctx = PruneScanCtx::for_state(state);

    // Snapshot rules first to avoid borrow conflicts (registry borrow vs
    // state mutation in tombstone emission).
    //
    // Note: state.prune_registry is &mut ServerState; we collect rule
    // references first then iterate without holding the registry borrow
    // during DAG mutation.
    #[allow(clippy::type_complexity)]
    let rule_snapshots: Vec<(
        &'static str,
        &'static str,
        fn(&ServerState, &PruneScanCtx, u64) -> Vec<PruneCandidate>,
    )> = state
        .prune_registry
        .rules()
        .map(|r| (r.rule_id, r.category, r.detect))
        .collect();

    for (rule_id, category, detect_fn) in rule_snapshots {
        report.rules_run.push(rule_id);

        // Snapshot candidates (each detect_fn takes &ServerState, no mutation).
        let candidates = detect_fn(state, &ctx, current_cycle);

        // Emit one tombstone per candidate.
        for cand in candidates {
            let tombstone = emit_internal_mortality_event(
                state,
                category,
                rule_id,
                &cand.part_hash,
                &cand.part_node_type,
                &cand.reason,
                cand.replaced_by_hash.as_ref(), // 错误/冗余 carry a surviving "replaced_by"; 过时/无用/seed → None
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
    use myco_kernel_schema::dag::Dag;
    use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value as CbV};
    use myco_kernel_shared::crypto::NodeHash;

    // -- test helpers --------------------------------------------------------

    /// Build an in-memory `ServerState` wrapping the given hand-built `Dag`.
    /// Mirrors the construction in
    /// `count_prune_resurrections_handles_empty_dag_safely`: a throwaway state
    /// dir + a fresh genesis `Manifest` for the discrete identity fields.
    fn state_over(dag: Dag) -> ServerState {
        use crate::persistence::Manifest;
        let state_dir = std::env::temp_dir().join(format!(
            "myco-prune-rule-test-{}-{:p}",
            std::process::id(),
            &dag as *const _
        ));
        let g = Manifest::genesis();
        ServerState::new(
            state_dir,
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            dag,
            [0u8; 32],
        )
    }

    /// Canonical-bytes for a content string (uniqueness controlled by caller).
    fn cb(s: &str) -> myco_kernel_shared::canonical_bytes::CanonicalBytes {
        cb_encode(&CbV::String(s.to_string())).unwrap()
    }

    /// Insert a chained node (parent = current tip, or root when empty).
    /// Returns the new node hash.
    fn push(dag: &mut Dag, node_type: &str, cycle: u64, content: &str) -> NodeHash {
        let parents = match dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        dag.insert_node(parents, node_type.to_string(), cycle, cb(content))
            .expect("test DAG insert")
    }

    /// Insert a node with explicit parents + content (for reachability shapes).
    fn push_with(
        dag: &mut Dag,
        parents: Vec<NodeHash>,
        node_type: &str,
        cycle: u64,
        content: &str,
    ) -> NodeHash {
        dag.insert_node(parents, node_type.to_string(), cycle, cb(content))
            .expect("test DAG insert (explicit parents)")
    }

    /// Collect the `killed_part_hash` of every tombstone in the DAG, in
    /// insertion order, with its rule_id + category — for asserting which
    /// rule fired on which part. Tuple = (rule_id, category, killed, replaced_by).
    #[allow(clippy::type_complexity)] // test-only assertion helper; the tuple is self-documenting
    fn tombstones(state: &ServerState) -> Vec<(String, String, [u8; 32], Option<[u8; 32]>)> {
        use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as V};
        let mut out = Vec::new();
        for node in state.dag.iter_in_insertion_order() {
            if !node
                .node_type
                .starts_with(NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX)
            {
                continue;
            }
            let m = match cb_decode(node.content_canonical_bytes.as_ref()) {
                Ok(V::Map(m)) => m,
                _ => continue,
            };
            let rule_id = match m.get("rule_id") {
                Some(V::String(s)) => s.clone(),
                _ => String::new(),
            };
            let category = match m.get("category") {
                Some(V::String(s)) => s.clone(),
                _ => String::new(),
            };
            let killed = match m.get("killed_part_hash") {
                Some(V::Bytes(b)) if b.len() == 32 => {
                    let mut a = [0u8; 32];
                    a.copy_from_slice(b);
                    a
                }
                _ => [0u8; 32],
            };
            let replaced = match m.get("replaced_by_hash") {
                Some(V::Bytes(b)) if b.len() == 32 => {
                    let mut a = [0u8; 32];
                    a.copy_from_slice(b);
                    Some(a)
                }
                _ => None,
            };
            out.push((rule_id, category, killed, replaced));
        }
        out
    }

    /// Convenience: hash → `[u8;32]`.
    fn arr(h: &NodeHash) -> [u8; 32] {
        h.as_ref().try_into().unwrap()
    }

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
    fn cov06_protected_set_includes_cultivation_fsm_events() {
        // COV06: cultivation FSM events must be P10-invariant-protected so the
        // substrate REMEMBERS its cultivator-mortality history (un-prunable).
        assert!(is_p10_invariant_protected("cultivator_heartbeat_recorded"));
        assert!(is_p10_invariant_protected("cultivator_heartbeat_stale:abcd"));
        assert!(is_p10_invariant_protected("cultivator_heartbeat_resumed"));
        assert!(is_p10_invariant_protected("successor_chain_updated:abcd"));
        assert!(is_p10_invariant_protected("succession_completed:abcd"));
        assert!(is_p10_invariant_protected("cultivation_orphaned:abcd"));
        assert!(is_p10_invariant_protected("cultivation_recovered:abcd"));
        // `bet_retired:*` (incl. the cultivation_orphaned_terminal reason) is
        // covered by the `bet_retired` prefix; `cultivation_orphaned_terminal`
        // itself is covered by the `cultivation_orphaned` prefix (so it is no
        // longer a separate list entry — the prior standalone assertion was
        // tautological once the literal was folded under that prefix).
        assert!(is_p10_invariant_protected("bet_retired:cultivation_orphaned_terminal"));
    }

    #[test]
    fn cov06_c69_suppression_predicate() {
        // COV06 C69: suppression mutation types are refused.
        assert!(is_cultivation_orphaned_suppression_attempt(
            "suppress_cultivation_orphaned"
        ));
        assert!(is_cultivation_orphaned_suppression_attempt(
            "extend_legacy_window_indefinitely"
        ));
        assert!(!is_cultivation_orphaned_suppression_attempt("delta_absorb"));
        // C69 is disjoint from C56 (different forbidden families).
        assert!(!is_cultivator_preserve_all_attempt("suppress_cultivation_orphaned"));
    }

    #[test]
    fn registry_default_includes_seed_rule_then_five_families() {
        // F26 complete: seed rule FIRST (determinism), then the canonical four,
        // then the amplifier step-3 plate-supersession rule (appended last so the
        // pre-existing scan/emission order is unchanged).
        let reg = PruneRuleRegistry::seed();
        assert_eq!(reg.rule_count(), 6);
        let ids: Vec<&str> = reg.rules().map(|r| r.rule_id).collect();
        assert_eq!(
            ids,
            vec![
                "L0.seed.orphan_past_grace",
                "L1.过时.axis_unrefreshed_past_window",
                "L1.错误.superseded_by_failed_evolution",
                "L1.冗余.duplicate_content_subsumed",
                "L1.无用.unreachable_from_live_roots",
                "L1.错误.forged_understanding_superseded",
            ],
            "seed rule must stay first; family order is fixed for determinism"
        );
        // Seed rule identity unchanged.
        let seed = reg.rules().next().unwrap();
        assert_eq!(seed.rule_id, "L0.seed.orphan_past_grace");
        assert_eq!(seed.category, "无用");
        // Each family carries the right category.
        let cats: Vec<&str> = reg.rules().map(|r| r.category).collect();
        assert_eq!(cats, vec!["无用", "过时", "错误", "冗余", "无用", "错误"]);
    }

    #[test]
    fn registry_register_appends() {
        fn dummy_detect(_: &ServerState, _: &PruneScanCtx, _: u64) -> Vec<PruneCandidate> {
            Vec::new()
        }
        let mut reg = PruneRuleRegistry::seed();
        let before = reg.rule_count();
        reg.register(PruneRule {
            rule_id: "L1.test.dummy",
            category: "测试",
            description: "test",
            detect: dummy_detect,
        });
        assert_eq!(reg.rule_count(), before + 1);
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
        // Task #8i: seed discrete identity fields from a fresh genesis Manifest.
        let g = Manifest::genesis();
        let state = ServerState::new(
            state_dir,
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            Dag::new(),
            [0u8; 32],
        );

        let (resurrected, total_tombstones) = count_prune_resurrections(&state);

        // No tombstones → resurrection count is necessarily 0 (no killed
        // contents to compare against).
        assert_eq!(resurrected, 0);
        assert_eq!(total_tombstones, 0);
    }

    // =======================================================================
    // L1 production rule A — 过时 / axis_unrefreshed_past_window
    // =======================================================================

    #[test]
    fn stale_axis_prunes_axis_untouched_past_window() {
        // axis registered at cycle 100, never perturbed again; now = 2200.
        // 2200 - 100 = 2100 > STALE_AXIS_GRACE_CYCLES(2000) → 过时.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        let axis = push(&mut dag, "axis_registered:hunger", 100, "reg-hunger");
        // a fresh tip so the axis node is NOT the tip.
        push(&mut dag, "cycle_advanced", 2200, "tip");
        let state = state_over(dag);

        let cands = detect_stale_axis_past_window(&state, &PruneScanCtx::for_state(&state), 2200);
        assert_eq!(cands.len(), 1, "exactly the stale axis");
        assert_eq!(cands[0].part_hash, arr(&axis));
        assert_eq!(cands[0].part_node_type, "axis_registered:hunger");
        assert!(cands[0].replaced_by_hash.is_none(), "过时 has no replacement");
    }

    #[test]
    fn stale_axis_does_not_prune_recently_perturbed_axis() {
        // Same axis registered at cycle 100 BUT perturbed at cycle 2000.
        // last_touch = 2000; now = 2200; 2200 - 2000 = 200 <= 2000 → fresh.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "axis_registered:hunger", 100, "reg-hunger");
        push(&mut dag, "axis_perturbed:hunger", 2000, "perturb");
        push(&mut dag, "cycle_advanced", 2200, "tip");
        let state = state_over(dag);

        let cands = detect_stale_axis_past_window(&state, &PruneScanCtx::for_state(&state), 2200);
        assert!(cands.is_empty(), "recently-perturbed axis is not 过时");
    }

    #[test]
    fn stale_axis_reset_after_fruiting_counts_as_a_touch() {
        // Registered cycle 100, reset_after_fruiting at cycle 1500; now 2200.
        // last_touch = 1500; 2200 - 1500 = 700 <= 2000 → still fresh.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "axis_registered:appetite", 100, "reg");
        push(&mut dag, "axis_reset_after_fruiting:appetite", 1500, "reset");
        push(&mut dag, "cycle_advanced", 2200, "tip");
        let state = state_over(dag);
        assert!(detect_stale_axis_past_window(&state, &PruneScanCtx::for_state(&state), 2200).is_empty());
    }

    // =======================================================================
    // L1 production rule B — 错误 / superseded_by_failed_evolution
    // =======================================================================

    #[test]
    fn erroneous_prunes_success_superseded_by_later_failure() {
        // succeeded:op at cycle 100, failed:op at cycle 200; now = 1300.
        // 1300 - 200 = 1100 > ERRONEOUS_GRACE_CYCLES(1000) → 错误.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        let succ = push(&mut dag, "evolution_succeeded:modify_axis", 100, "s");
        let fail = push(&mut dag, "evolution_failed:modify_axis", 200, "f");
        push(&mut dag, "cycle_advanced", 1300, "tip");
        let state = state_over(dag);

        let cands = detect_superseded_by_failed_evolution(&state, &PruneScanCtx::for_state(&state), 1300);
        assert_eq!(cands.len(), 1, "the superseded success");
        assert_eq!(cands[0].part_hash, arr(&succ));
        assert_eq!(
            cands[0].replaced_by_hash,
            Some(arr(&fail)),
            "replaced_by = the failure that superseded it"
        );
    }

    #[test]
    fn erroneous_does_not_prune_success_with_no_later_failure() {
        // failure came BEFORE the success → the success re-succeeded; not 错误.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "evolution_failed:modify_axis", 100, "f-early");
        push(&mut dag, "evolution_succeeded:modify_axis", 200, "s-later");
        push(&mut dag, "cycle_advanced", 1300, "tip");
        let state = state_over(dag);
        assert!(
            detect_superseded_by_failed_evolution(&state, &PruneScanCtx::for_state(&state), 1300).is_empty(),
            "a success AFTER the failure is not superseded"
        );
    }

    #[test]
    fn erroneous_respects_grace_window_on_the_failure() {
        // succeeded:100, failed:200, now = 700. 700 - 200 = 500 <= 1000 → wait.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "evolution_succeeded:op", 100, "s");
        push(&mut dag, "evolution_failed:op", 200, "f");
        push(&mut dag, "cycle_advanced", 700, "tip");
        let state = state_over(dag);
        assert!(detect_superseded_by_failed_evolution(&state, &PruneScanCtx::for_state(&state), 700).is_empty());
    }

    // =======================================================================
    // L1 production rule E — 错误 / forged_understanding_superseded (amplifier step 3)
    // =======================================================================

    /// Insert a forged_understanding plate with the given label/cycle/supersedes
    /// (the structured content `detect_forged_understanding_superseded` decodes).
    fn push_plate(
        dag: &mut Dag,
        label: &str,
        cycle: u64,
        supersedes: &[[u8; 32]],
    ) -> myco_kernel_shared::crypto::NodeHash {
        use myco_kernel_shared::canonical_bytes::{encode, Value};
        let mut m = std::collections::BTreeMap::new();
        m.insert("label".to_string(), Value::String(label.to_string()));
        m.insert("understanding".to_string(), Value::Bytes(b"x".to_vec()));
        if !supersedes.is_empty() {
            m.insert(
                "supersedes".to_string(),
                Value::Array(supersedes.iter().map(|h| Value::Bytes(h.to_vec())).collect()),
            );
        }
        let content = encode(&Value::Map(m)).expect("encode plate");
        let parents = match dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        dag.insert_node(parents, format!("forged_understanding:{label}"), cycle, content)
            .expect("insert plate")
    }

    #[test]
    fn plate_superseded_by_later_plate_is_pruned() {
        // A@100; C@300 supersedes A; now=1400. 1400-300=1100 > GRACE(1000) → A 应朽.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        let a = push_plate(&mut dag, "coarse", 100, &[]);
        push_plate(&mut dag, "unrelated", 150, &[]);
        let c = push_plate(&mut dag, "refined", 300, &[arr(&a)]);
        push(&mut dag, "cycle_advanced", 1400, "tip");
        let state = state_over(dag);

        let cands =
            detect_forged_understanding_superseded(&state, &PruneScanCtx::for_state(&state), 1400);
        assert_eq!(cands.len(), 1, "only the superseded plate A is 应朽");
        assert_eq!(cands[0].part_hash, arr(&a));
        assert_eq!(
            cands[0].replaced_by_hash,
            Some(arr(&c)),
            "replaced_by = the superseding plate"
        );
    }

    #[test]
    fn plate_supersession_respects_grace_window() {
        // C@300 supersedes A; now=1000 → 1000-300=700 <= GRACE(1000) → not yet.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        let a = push_plate(&mut dag, "coarse", 100, &[]);
        push_plate(&mut dag, "refined", 300, &[arr(&a)]);
        push(&mut dag, "cycle_advanced", 1000, "tip");
        let state = state_over(dag);
        assert!(
            detect_forged_understanding_superseded(&state, &PruneScanCtx::for_state(&state), 1000)
                .is_empty(),
            "within grace, the superseded plate is not yet retired"
        );
    }

    // =======================================================================
    // L1 production rule C — 冗余 / duplicate_content_subsumed
    // =======================================================================

    #[test]
    fn redundant_prunes_earliest_of_byte_identical_run() {
        // Two raw_material nodes, identical type+content; earliest subsumed.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        let first = push(&mut dag, "raw_material:text", 10, "DUP");
        let second = push(&mut dag, "raw_material:text", 20, "DUP");
        push(&mut dag, "cycle_advanced", 1100, "tip");
        let state = state_over(dag);

        let cands = detect_duplicate_content_subsumed(&state, &PruneScanCtx::for_state(&state), 1100);
        assert_eq!(cands.len(), 1, "only the earliest copy is subsumed");
        assert_eq!(cands[0].part_hash, arr(&first));
        assert_eq!(
            cands[0].replaced_by_hash,
            Some(arr(&second)),
            "survivor is the later identical copy"
        );
    }

    #[test]
    fn redundant_is_scoped_to_raw_material_and_sporocarp_only() {
        // Two byte-identical cycle_advanced nodes MUST NOT be treated as 冗余 —
        // structural events repeat identical content by design.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        // identical content cycle_advanced nodes (out of scope). Note: the
        // merkle hash includes parent_hashes, so to make the CONTENT identical
        // we vary the parents but keep `content_canonical_bytes` equal — the
        // scope filter excludes cycle_advanced regardless.
        let t1 = dag.tip().unwrap();
        push_with(&mut dag, vec![t1], "cycle_advanced", 10, "SAME");
        let t2 = dag.tip().unwrap();
        push_with(&mut dag, vec![t2], "cycle_advanced", 20, "SAME");
        push(&mut dag, "cycle_advanced", 1100, "tip");
        let state = state_over(dag);
        assert!(
            detect_duplicate_content_subsumed(&state, &PruneScanCtx::for_state(&state), 1100).is_empty(),
            "cycle_advanced is out of the 冗余 scope"
        );
    }

    #[test]
    fn redundant_does_not_prune_distinct_content() {
        // Two raw_material nodes with DIFFERENT content → not redundant.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "raw_material:text", 10, "alpha");
        push(&mut dag, "raw_material:text", 20, "beta");
        push(&mut dag, "cycle_advanced", 1100, "tip");
        let state = state_over(dag);
        assert!(detect_duplicate_content_subsumed(&state, &PruneScanCtx::for_state(&state), 1100).is_empty());
    }

    #[test]
    fn redundant_respects_grace_window() {
        // duplicates exist but earliest is within grace: first_cycle 200, now 1100,
        // 1100 - 200 = 900 <= 1000 → wait.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "raw_material:text", 200, "DUP");
        push(&mut dag, "raw_material:text", 250, "DUP");
        push(&mut dag, "cycle_advanced", 1100, "tip");
        let state = state_over(dag);
        assert!(detect_duplicate_content_subsumed(&state, &PruneScanCtx::for_state(&state), 1100).is_empty());
    }

    // =======================================================================
    // L1 production rule D — 无用 / unreachable_from_live_roots
    // =======================================================================

    #[test]
    fn unreachable_prunes_directly_referenced_detached_island() {
        // Shape:
        //   G(0) → A(5) → B(6)        [old island; A referenced by B]
        //   G(0) → R1(5000) → R2(5001=tip)  [live frontier]
        // now = 6000, grace = 1000, recent_cutoff = 5000.
        // Live roots = {R2(tip)} ∪ parents-of-nodes(cycle>5000) = {R2, R1}.
        // Backward reach = {R2, R1, G}. A is referenced (by B), past grace,
        // unreachable → 无用 by rule D. B is unreferenced → seed rule's job
        // (excluded here by the disjointness guard).
        let mut dag = Dag::new();
        let g = push(&mut dag, "genesis_event:aa", 0, "g");
        let a = push_with(&mut dag, vec![g], "raw_material:text", 5, "A");
        let _b = push_with(&mut dag, vec![a], "raw_material:text", 6, "B");
        let r1 = push_with(&mut dag, vec![g], "raw_material:text", 5000, "R1");
        let _r2 = push_with(&mut dag, vec![r1], "cycle_advanced", 5001, "R2");
        let state = state_over(dag);

        let cands = detect_unreachable_from_live_roots(&state, &PruneScanCtx::for_state(&state), 6000);
        let hits: Vec<[u8; 32]> = cands.iter().map(|c| c.part_hash).collect();
        assert!(
            hits.contains(&arr(&a)),
            "A is directly-referenced + unreachable → 无用; got {} cands",
            cands.len()
        );
        // disjointness: B (zero referents) must NOT be a rule-D candidate.
        assert!(
            !hits.contains(&arr(&_b)),
            "B has zero referents → seed rule's domain, excluded from rule D"
        );
        // replaced_by is None for 无用.
        let a_cand = cands.iter().find(|c| c.part_hash == arr(&a)).unwrap();
        assert!(a_cand.replaced_by_hash.is_none());
    }

    #[test]
    fn unreachable_does_not_prune_reachable_node() {
        // A purely linear, fully-reachable chain → nothing is unreachable.
        // G(0) → A(5) → tip(5001). now = 6000.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "raw_material:text", 5, "A");
        push(&mut dag, "cycle_advanced", 5001, "tip");
        let state = state_over(dag);
        assert!(
            detect_unreachable_from_live_roots(&state, &PruneScanCtx::for_state(&state), 6000).is_empty(),
            "everything on the live chain is reachable from the tip"
        );
    }

    #[test]
    fn unreachable_disjoint_from_seed_orphan_rule() {
        // The seed rule and rule D must never both claim the same part.
        // Reuse the detached-island shape and intersect their candidate sets.
        let mut dag = Dag::new();
        let g = push(&mut dag, "genesis_event:aa", 0, "g");
        let a = push_with(&mut dag, vec![g], "raw_material:text", 5, "A");
        let _b = push_with(&mut dag, vec![a], "raw_material:text", 6, "B");
        let r1 = push_with(&mut dag, vec![g], "raw_material:text", 5000, "R1");
        let _r2 = push_with(&mut dag, vec![r1], "cycle_advanced", 5001, "R2");
        let state = state_over(dag);

        let seed: std::collections::HashSet<[u8; 32]> = detect_orphan_past_grace(&state, &PruneScanCtx::for_state(&state), 6000)
            .into_iter()
            .map(|c| c.part_hash)
            .collect();
        let dee: std::collections::HashSet<[u8; 32]> =
            detect_unreachable_from_live_roots(&state, &PruneScanCtx::for_state(&state), 6000)
                .into_iter()
                .map(|c| c.part_hash)
                .collect();
        assert!(
            seed.is_disjoint(&dee),
            "seed (zero-referent) and rule D (referenced-but-unreachable) candidate sets must be disjoint; seed={seed:?} D={dee:?}"
        );
    }

    #[test]
    fn unreachable_walk_terminates_on_cyclic_edges() {
        // Defensive: even if the (normally acyclic) hash index contained a
        // cycle, the visited-set bounds the walk. We can't build a real hash
        // cycle through the DAG API, so we directly exercise the bounded walk
        // invariant by asserting the detector returns promptly on a large
        // linear chain (no hang, no stack overflow).
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        for i in 1..500u64 {
            push(&mut dag, "raw_material:text", i, &format!("n{i}"));
        }
        push(&mut dag, "cycle_advanced", 5001, "tip");
        let state = state_over(dag);
        // Just assert it returns (bounded). All nodes are reachable (linear).
        let _ = detect_unreachable_from_live_roots(&state, &PruneScanCtx::for_state(&state), 6000);
    }

    // =======================================================================
    // run_prune_scan integration: tombstone emission + determinism
    // =======================================================================

    #[test]
    fn run_prune_scan_emits_tombstone_for_redundant_duplicate() {
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        let first = push(&mut dag, "raw_material:text", 10, "DUP");
        push(&mut dag, "raw_material:text", 20, "DUP");
        push(&mut dag, "cycle_advanced", 1100, "tip");
        let mut state = state_over(dag);

        let report = run_prune_scan(&mut state, 1100).expect("scan ok");
        // The 冗余 rule fired (registration order: seed, 过时, 错误, 冗余, 无用).
        assert!(report.rules_run.contains(&"L1.冗余.duplicate_content_subsumed"));
        let tombs = tombstones(&state);
        let red = tombs
            .iter()
            .find(|(rid, _, _, _)| rid == "L1.冗余.duplicate_content_subsumed")
            .expect("a 冗余 tombstone exists");
        assert_eq!(red.1, "冗余");
        assert_eq!(red.2, arr(&first), "earliest copy was killed");
        assert!(red.3.is_some(), "冗余 tombstone records replaced_by");
    }

    #[test]
    fn run_prune_scan_is_deterministic_on_clone() {
        // Build a DAG that triggers MULTIPLE families, run the scan over two
        // independent ServerStates built from the same DAG, and assert the
        // emitted tombstone hash SEQUENCE is identical (P07 determinism).
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        // 错误 pair
        push(&mut dag, "evolution_succeeded:op", 50, "s");
        push(&mut dag, "evolution_failed:op", 60, "f");
        // 冗余 pair
        push(&mut dag, "raw_material:text", 70, "DUP");
        push(&mut dag, "raw_material:text", 80, "DUP");
        push(&mut dag, "cycle_advanced", 1300, "tip");

        let mut s1 = state_over(dag.clone());
        let mut s2 = state_over(dag);

        let r1 = run_prune_scan(&mut s1, 1300).expect("scan1");
        let r2 = run_prune_scan(&mut s2, 1300).expect("scan2");

        assert_eq!(
            r1.tombstones_emitted, r2.tombstones_emitted,
            "tombstone hash sequence must be reproducible from (DAG, cycle)"
        );
        assert!(
            r1.tombstones_emitted.len() >= 2,
            "expected at least the 错误 + 冗余 tombstones; got {}",
            r1.tombstones_emitted.len()
        );
        // rules_run is identical + in registration order.
        assert_eq!(r1.rules_run, r2.rules_run);
        assert_eq!(r1.rules_run.first(), Some(&"L0.seed.orphan_past_grace"));
    }

    #[test]
    fn run_prune_scan_skips_already_tombstoned_part_on_rerun() {
        // First scan tombstones the redundant earliest; a second scan over the
        // SAME (now-mutated) state must NOT re-tombstone it.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        push(&mut dag, "raw_material:text", 10, "DUP");
        push(&mut dag, "raw_material:text", 20, "DUP");
        push(&mut dag, "cycle_advanced", 1100, "tip");
        let mut state = state_over(dag);

        let first = run_prune_scan(&mut state, 1100).expect("scan1");
        let n_first = first.tombstones_emitted.len();
        assert!(n_first >= 1);
        let second = run_prune_scan(&mut state, 1200).expect("scan2");
        assert!(
            second.tombstones_emitted.is_empty(),
            "already-tombstoned parts must not be re-killed; got {} new",
            second.tombstones_emitted.len()
        );
    }

    // =======================================================================
    // C54 hoarding interaction with the live prune rules
    // =======================================================================

    #[test]
    fn c54_hoarding_false_when_new_rules_emit_a_tombstone() {
        // Ingestion >= floor over the window AND the prune rules emit >= 1
        // tombstone → is_hoarding must be FALSE (the substrate IS pruning).
        //
        // current_cycle = 3000. Hoarding window = [2800, 3000].
        // Redundant grace needs the duplicate's earliest copy at cycle <= 2000.
        // So: a duplicate PAIR at cycles 100/110 (well past grace) supplies the
        // 冗余 tombstone (emitted at cycle 3000, which lands IN the window), and
        // >= 10 UNIQUE raw_material in [2800,3000] supply the hoarding ingestion.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        // Duplicate pair, past redundant grace.
        push(&mut dag, "raw_material:text", 100, "OLD-DUP");
        push(&mut dag, "raw_material:text", 110, "OLD-DUP");
        // >= HOARDING_INDICATOR_INGESTION_FLOOR (10) unique ingestion in window.
        for i in 0..12u64 {
            push(&mut dag, "raw_material:text", 2850 + i, &format!("u{i}"));
        }
        push(&mut dag, "cycle_advanced", 3000, "tip");
        let mut state = state_over(dag);

        // Pre-scan: ingestion present in window, zero tombstones → reads as hoarding.
        assert!(
            is_hoarding(&state, 3000),
            "precondition: ingestion present + no prune yet ⇒ hoarding signal"
        );
        // Run the scan: the 冗余 rule should kill the earliest OLD-DUP.
        let report = run_prune_scan(&mut state, 3000).expect("scan");
        assert!(
            !report.tombstones_emitted.is_empty(),
            "expected >= 1 tombstone from the duplicate"
        );
        // Post-scan: a tombstone now exists in the window → no longer hoarding.
        assert!(
            !is_hoarding(&state, 3000),
            "after emitting a tombstone the hoarding signal must clear"
        );
    }

    #[test]
    fn c54_hoarding_stays_true_when_nothing_is_prunable() {
        // Ingestion >= floor but every part is UNIQUE + within grace + on the
        // live chain → no rule fires → hoarding stays TRUE.
        // current_cycle = 3000, window [2800,3000]; all ingestion unique +
        // recent (within both the redundant grace AND reachable from tip).
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        for i in 0..12u64 {
            push(&mut dag, "raw_material:text", 2850 + i, &format!("unique{i}"));
        }
        push(&mut dag, "cycle_advanced", 3000, "tip");
        let mut state = state_over(dag);

        let report = run_prune_scan(&mut state, 3000).expect("scan");
        assert!(
            report.tombstones_emitted.is_empty(),
            "nothing prunable (all unique, within grace, reachable)"
        );
        assert!(
            is_hoarding(&state, 3000),
            "ingestion >= floor + zero prunable ⇒ hoarding stays true"
        );
    }

    // =======================================================================
    // Parity: the P10 invariant protected set is unchanged
    // =======================================================================

    #[test]
    fn protected_set_parity_holds_for_new_rules() {
        // A protected node (genesis_event) that is also an unreachable,
        // duplicate, stale-axis-looking part must be skipped by EVERY rule.
        let mut dag = Dag::new();
        push(&mut dag, "genesis_event:aa", 0, "g");
        // tombstone-prefixed node is protected too (P06): build one via a real
        // scan so it is well-formed, then assert no rule targets it.
        push(&mut dag, "raw_material:text", 10, "DUP");
        push(&mut dag, "raw_material:text", 20, "DUP");
        push(&mut dag, "cycle_advanced", 1100, "tip");
        let mut state = state_over(dag);
        let _ = run_prune_scan(&mut state, 1100).expect("scan1");

        // Now a tombstone exists. Re-running must never target the tombstone
        // itself (internal_mortality_event:* is in the protected set) nor the
        // genesis node.
        let cands_d = detect_unreachable_from_live_roots(&state, &PruneScanCtx::for_state(&state), 1300);
        for c in &cands_d {
            assert!(
                !is_p10_invariant_protected(&c.part_node_type),
                "rule D produced a protected candidate: {}",
                c.part_node_type
            );
        }
        let cands_c = detect_duplicate_content_subsumed(&state, &PruneScanCtx::for_state(&state), 1300);
        for c in &cands_c {
            assert!(!is_p10_invariant_protected(&c.part_node_type));
        }
    }
}
