//! **M26.3 P10 Selective Compression** (L0/META §7 (amendment) + L1/SCHEMA §2.5).
//!
//! L0 P10 mandates that the substrate selectively compress prior states
//! under CI attestation; lossy semantically; preserves causal recoverability
//! of identity-critical state (I9). Each compression emits `compression_event`
//! with witness. The rules + invariant set + witness shape live below.
//!
//! **M26.4 P11.c Ordered Fallback** also lives here: budgets + automatic
//! fallback (saturation stage machine).
//!
//! M26.2 made cost signals OBSERVABLE; M26.3 made compression POSSIBLE; M26.4
//! closes the loop: budgets + automatic fallback + telos drift.
//!
//! L0/META §10 (negative space).c ordered fallback semantics:
//!   (1) pre-eligibility (cycle <N, default 1000):  refuse new P2 + budget_exhausted:{axis}
//!   (2) post-eligibility (cycle ≥N):               trigger P10 compression proposal
//!   (3) compression-insufficient (sustained):       degraded → alive::saturated
//!   (sustained at stage 3 → P7 mortality)

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

/// Prefix for `compression_event:{rule_id}` DAG nodes (M26.3). Emitted AFTER
/// a `mutation:compression` carrying valid owner attestation has been
/// accepted. Carries the rule_id applied, the list of compressed-out node
/// hashes (originals being aggregated/forgotten), the aggregate summary, and
/// the I9 witness payload.
pub const NODE_TYPE_COMPRESSION_EVENT_PREFIX: &str = "compression_event:";

/// **M26.3 P10 default rule registry** (F18 fixed point seed). Real
/// production substrates load this from `compression_rule_registry` SSoT
/// (CI-mutable); these are the seed values. Each rule has:
///
/// - `rule_id`: unique identifier (used as DAG node suffix)
/// - `description`: human-readable
/// - `target_node_type_prefix`: which node types this rule targets
/// - `min_age_cycles`: candidate nodes must be at least this old
/// - `aggregator`: name of the aggregation strategy
///
/// Rule mutation requires CI per F18; the seed values land at genesis
/// and stay in effect until a CI-attested `schema_evolution:compression_rule_*`
/// modifies them.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompressionRule {
    /// Stable identifier (e.g. "raw_material_aggregate_v1").
    pub rule_id: String,
    /// Human-readable description.
    pub description: String,
    /// Targets DAG nodes whose `node_type` starts with this prefix.
    pub target_node_type_prefix: String,
    /// Originals must be at least this many cycles old to be eligible.
    pub min_age_cycles: u64,
    /// Aggregation strategy: "sum_to_sporocarp" / "drop_after_retention" / "archive".
    pub aggregator: String,
}

/// Seed compression rule registry (P10.a categories + F18 default set).
/// Three rules covering L0 P10.a "compressible" inventory:
///
/// 1. **raw_material_aggregate_v1** — old `raw_material:*` nodes → aggregate sporocarp
/// 2. **federation_payload_retention_v1** — old `federation_received:*` past retention → drop
/// 3. **trajectory_archive_v1** — old `axis_perturbed:*` past active window → archive
///
/// `min_age_cycles` seed = 1000 (matches L0 P10.b "most recent ≥1000 cycles").
pub fn seed_compression_rule_registry() -> Vec<CompressionRule> {
    vec![
        CompressionRule {
            rule_id: "raw_material_aggregate_v1".to_string(),
            description:
                "Aggregate raw_material:* nodes older than 1000 cycles into a summary sporocarp."
                    .to_string(),
            target_node_type_prefix: "raw_material:".to_string(),
            min_age_cycles: 1000,
            aggregator: "sum_to_sporocarp".to_string(),
        },
        CompressionRule {
            rule_id: "federation_payload_retention_v1".to_string(),
            description:
                "Drop federation_received:* payloads past 1000-cycle retention."
                    .to_string(),
            target_node_type_prefix: "federation_received:".to_string(),
            min_age_cycles: 1000,
            aggregator: "drop_after_retention".to_string(),
        },
        CompressionRule {
            rule_id: "trajectory_archive_v1".to_string(),
            description:
                "Archive axis_perturbed:* trajectory clusters past the active 1000-cycle window."
                    .to_string(),
            target_node_type_prefix: "axis_perturbed:".to_string(),
            min_age_cycles: 1000,
            aggregator: "archive".to_string(),
        },
    ]
}

/// **M26.3 P10.b compression invariant set enumeration** (L1/SCHEMA §4.1 tier-1).
///
/// Categories that MUST NEVER be compressed (loss of any of these would
/// violate I1/I4/I7/I9). Substrate enforces this set on every compression
/// mutation; C51 fires if a compression event ever names a member of this
/// set in its `compressed_node_hashes`.
///
/// The seven categories:
/// - `genesis_event:*` — substrate-ID + genesis attestation chain (P10.b first)
/// - `owner_key_*` — owner_key_history (active-prefix + archived-tail)
/// - `mutation:*` — every CI-attested mutation (audit trail)
/// - `evolution_succeeded:*` / `evolution_failed:*` — CI mutation outcomes
/// - `self_euthanasia_*` — mortality signals
/// - `federation_peer_pinned:*` — federation peer pin records
/// - the most-recent-N-cycles floor (default N=1000; orthogonal "recency" guard)
#[derive(Debug, Clone)]
pub struct CompressionInvariantSet {
    /// Node-type prefixes that are NEVER compressible regardless of age.
    pub forbidden_prefixes: Vec<String>,
    /// Most recent N cycles of ANY node type are protected (per L0 P10.b
    /// "most recent ≥1000 cycles full DAG"). Default 1000.
    pub recent_cycles_floor: u64,
}

/// Seed P10.b invariant set per L0/META §7 (amendment).
pub fn seed_compression_invariant_set() -> CompressionInvariantSet {
    CompressionInvariantSet {
        forbidden_prefixes: vec![
            // Substrate-ID + genesis attestation chain.
            "genesis_event:".to_string(),
            // Owner key history (initialized / added / archived).
            "owner_key_".to_string(),
            // Every CI-attested mutation + its outcome.
            "mutation:".to_string(),
            "evolution_succeeded:".to_string(),
            "evolution_failed:".to_string(),
            // Mortality signals.
            "self_euthanasia_".to_string(),
            // Federation peer pins.
            "federation_peer_pinned:".to_string(),
            // Birth-period quarantine markers (lifecycle).
            "birth_period_quarantine_".to_string(),
            // Operator pinning (substrate-ID-class).
            "operator_pinned:".to_string(),
            // Compression events themselves are CI-attested mutations and
            // must NEVER be compressed away (audit chain).
            "compression_event:".to_string(),
        ],
        recent_cycles_floor: 1000,
    }
}

/// Returns true if `node_type` is forbidden from compression by P10.b.
/// (Recent-cycles floor is enforced separately because it requires the
/// current cycle counter.)
pub fn node_type_in_invariant_set(
    node_type: &str,
    invariant_set: &CompressionInvariantSet,
) -> bool {
    invariant_set
        .forbidden_prefixes
        .iter()
        .any(|p| node_type.starts_with(p.as_str()))
}

/// **M26.3 P10.c CompressionWitness** (I9 attestation payload).
///
/// Every `mutation:compression` carries one of these as its
/// `content_canonical_bytes`. The substrate verifies it before accepting
/// the mutation; the owner signs it via the standard CI envelope.
///
/// Canonical form:
/// ```text
/// Map({
///   "rule_id": String,                       // which compression rule produced this
///   "compressed_node_hashes": Array(Bytes),  // originals being compressed (BLAKE3 hashes)
///   "aggregate_summary": Bytes,              // canonical-bytes of the aggregate (rule-specific shape)
///   "attestation_dag_tip": Bytes(32),        // DAG tip at attestation time
///   "semantic_lossy": Bool,                  // ALWAYS true per L0 P10
///   "causal_recoverability_argument": String,// human-readable I9 argument
/// })
/// ```
pub fn encode_compression_witness(
    rule_id: &str,
    compressed_node_hashes: &[[u8; 32]],
    aggregate_summary: &[u8],
    attestation_dag_tip: &[u8; 32],
    causal_recoverability_argument: &str,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    let hashes_array: Vec<Value> = compressed_node_hashes
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert(
        "compressed_node_hashes".to_string(),
        Value::Array(hashes_array),
    );
    m.insert(
        "aggregate_summary".to_string(),
        Value::Bytes(aggregate_summary.to_vec()),
    );
    m.insert(
        "attestation_dag_tip".to_string(),
        Value::Bytes(attestation_dag_tip.to_vec()),
    );
    m.insert("semantic_lossy".to_string(), Value::Bool(true));
    m.insert(
        "causal_recoverability_argument".to_string(),
        Value::String(causal_recoverability_argument.to_string()),
    );
    cb_encode(&Value::Map(m)).expect("compression_witness encode infallible")
}

/// Decode a CompressionWitness from its canonical bytes. Returns
/// `(rule_id, compressed_node_hashes, aggregate_summary, attestation_dag_tip)`
/// or `None` if the shape is wrong.
pub fn decode_compression_witness_minimal(
    bytes: &[u8],
) -> Option<(String, Vec<[u8; 32]>, Vec<u8>, [u8; 32])> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    let rule_id = match m.get("rule_id")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let hashes_array = match m.get("compressed_node_hashes")? {
        Value::Array(a) => a.clone(),
        _ => return None,
    };
    let mut hashes: Vec<[u8; 32]> = Vec::with_capacity(hashes_array.len());
    for v in hashes_array {
        let b = match v {
            Value::Bytes(b) => b,
            _ => return None,
        };
        if b.len() != 32 {
            return None;
        }
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&b);
        hashes.push(arr);
    }
    let aggregate_summary = match m.get("aggregate_summary")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let attestation_dag_tip = match m.get("attestation_dag_tip")? {
        Value::Bytes(b) => {
            if b.len() != 32 {
                return None;
            }
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            arr
        }
        _ => return None,
    };
    Some((rule_id, hashes, aggregate_summary, attestation_dag_tip))
}

/// Encode a `compression_event:{rule_id}` DAG node content (M26.3). The
/// content is essentially the witness PLUS the post-emission tip hash.
/// Form:
/// ```text
/// Map({
///   "rule_id": String,
///   "compressed_node_hashes": Array(Bytes),
///   "aggregate_summary": Bytes,
///   "witness_at_dag_tip": Bytes(32),
///   "emitted_at_cycle": Uint,
/// })
/// ```
pub fn encode_compression_event(
    rule_id: &str,
    compressed_node_hashes: &[[u8; 32]],
    aggregate_summary: &[u8],
    witness_at_dag_tip: &[u8; 32],
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    let hashes_array: Vec<Value> = compressed_node_hashes
        .iter()
        .map(|h| Value::Bytes(h.to_vec()))
        .collect();
    m.insert(
        "compressed_node_hashes".to_string(),
        Value::Array(hashes_array),
    );
    m.insert(
        "aggregate_summary".to_string(),
        Value::Bytes(aggregate_summary.to_vec()),
    );
    m.insert(
        "witness_at_dag_tip".to_string(),
        Value::Bytes(witness_at_dag_tip.to_vec()),
    );
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("compression_event encode infallible")
}

/// Convenience: full `compression_event:{rule_id}` node_type string.
pub fn compression_event_node_type(rule_id: &str) -> String {
    format!("{NODE_TYPE_COMPRESSION_EVENT_PREFIX}{rule_id}")
}

/// **M26.4 F19 cost budgets** — per-axis thresholds firing P11.c.
/// Tier-1 SSoT (CI-mutable per F19 fixed point). Defaults seeded; substrates
/// MAY tighten via owner-attested mutation (mutation_type="cost_budget_set").
#[derive(Debug, Clone, Copy)]
pub struct CostBudgets {
    /// Max wall-clock nanoseconds per metabolic cycle (signal #7).
    /// Seed: 100ms — reasonable upper bound for one cycle on commodity
    /// hardware. Cycles exceeding this are budget-exhausted on axis "compute".
    pub compute_ns_per_cycle: u64,
    /// Max federation egress wire bytes per cycle (signal #8).
    /// Seed: 1 MiB — bounds the substrate's outbound traffic.
    pub network_bytes_per_cycle: u64,
    /// Max bytes added to `dag.cb` + `snapshot.cb` per cycle (signal #9).
    /// Seed: 10 MiB — bounds the rate of disk growth.
    pub storage_bytes_per_cycle: u64,
    /// Cycle count below which the substrate is in P11.c pre-eligibility
    /// stage (no compression yet). Seed: 1000 — matches L0 P11.c "cycle <N,
    /// default 1000" and the P10.b recent_cycles_floor.
    pub pre_eligibility_cycle_floor: u64,
    /// Sustained-saturation threshold: number of CONSECUTIVE cycles in
    /// PostEligibility (compression proposed but budgets still exhausted)
    /// before transitioning to alive::saturated. Seed: 100.
    pub sustained_saturation_cycle_threshold: u64,
}

/// Seed F19 cost budget defaults.
pub fn seed_cost_budgets() -> CostBudgets {
    CostBudgets {
        compute_ns_per_cycle: 100_000_000,     // 100 ms
        network_bytes_per_cycle: 1_048_576,    // 1 MiB
        storage_bytes_per_cycle: 10_485_760,   // 10 MiB
        pre_eligibility_cycle_floor: 1000,
        sustained_saturation_cycle_threshold: 100,
    }
}

/// **M26.4 P11.c saturation stage** — substrate-state machine for ordered
/// fallback under budget exhaustion. Persists in `ServerState` and emits a
/// DAG event on each transition.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SaturationStage {
    /// Cost signals within budget. Default state.
    Normal,
    /// Budget exhausted but cycle < pre_eligibility_cycle_floor.
    /// Substrate refuses NEW raw_material ingestion; emits
    /// `budget_exhausted:{axis}` daily events.
    PreEligibility,
    /// Budget exhausted AND cycle ≥ floor. Substrate emits
    /// `compression_proposed:{rule_id}` daily events for each rule
    /// with eligible candidates (per L0 P11.c stage 2).
    PostEligibility,
    /// Budget exhausted AND PostEligibility has persisted ≥
    /// sustained_saturation_cycle_threshold consecutive cycles. Substrate
    /// transitions to `alive::saturated`; subsequent sustained saturation
    /// leads to P7 mortality.
    Saturated,
}

impl SaturationStage {
    /// Stable string label for the stage; used by observatory response
    /// payload + DAG event content. MUST NOT change without doctrine
    /// migration (operator clients pin on these strings).
    pub fn as_str(self) -> &'static str {
        match self {
            SaturationStage::Normal => "normal",
            SaturationStage::PreEligibility => "pre_eligibility",
            SaturationStage::PostEligibility => "post_eligibility",
            SaturationStage::Saturated => "saturated",
        }
    }
}

/// Prefix for `budget_exhausted:{axis}` daily events (M26.4 P11.c stage 1).
/// Axis ∈ {`compute_per_cycle`, `network_per_cycle`, `storage_per_cycle`}.
pub const NODE_TYPE_BUDGET_EXHAUSTED_PREFIX: &str = "budget_exhausted:";

/// Prefix for `compression_proposed:{rule_id}` daily events (M26.4 P11.c
/// stage 2). Operator picks these up + submits a matching CI-attested
/// `mutation:compression` to actually compress.
pub const NODE_TYPE_COMPRESSION_PROPOSED_PREFIX: &str = "compression_proposed:";

/// `substrate_saturated` event — M26.4 P11.c stage 3 transition into
/// `alive::saturated` substrate sub-state.
pub const NODE_TYPE_SUBSTRATE_SATURATED: &str = "substrate_saturated";

/// `substrate_normal_restored` event — M26.4 P11.c reverse transition when
/// budget exhaustion clears across all axes.
pub const NODE_TYPE_SUBSTRATE_NORMAL_RESTORED: &str = "substrate_normal_restored";

/// Encode a `budget_exhausted:{axis}` event.
/// ```text
/// Map({ "axis": String, "current_value": Uint, "budget": Uint, "at_cycle": Uint })
/// ```
pub fn encode_budget_exhausted(
    axis: &str,
    current_value: u64,
    budget: u64,
    at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("axis".to_string(), Value::String(axis.to_string()));
    m.insert("current_value".to_string(), Value::Uint(current_value));
    m.insert("budget".to_string(), Value::Uint(budget));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("budget_exhausted encode infallible")
}

/// Encode a `compression_proposed:{rule_id}` event.
/// ```text
/// Map({ "rule_id": String, "at_cycle": Uint, "proposed_axis": String, "estimated_candidates": Uint })
/// ```
pub fn encode_compression_proposed(
    rule_id: &str,
    at_cycle: u64,
    proposed_axis: &str,
    estimated_candidates: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "proposed_axis".to_string(),
        Value::String(proposed_axis.to_string()),
    );
    m.insert(
        "estimated_candidates".to_string(),
        Value::Uint(estimated_candidates),
    );
    cb_encode(&Value::Map(m)).expect("compression_proposed encode infallible")
}

/// Encode a `substrate_saturated` event.
pub fn encode_substrate_saturated(
    at_cycle: u64,
    sustained_cycles: u64,
    triggering_axis: &str,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert("sustained_cycles".to_string(), Value::Uint(sustained_cycles));
    m.insert(
        "triggering_axis".to_string(),
        Value::String(triggering_axis.to_string()),
    );
    cb_encode(&Value::Map(m)).expect("substrate_saturated encode infallible")
}

/// Encode a `substrate_normal_restored` event.
pub fn encode_substrate_normal_restored(at_cycle: u64) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("substrate_normal_restored encode infallible")
}
