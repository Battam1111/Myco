//! **M26.4 P14.c Telos Drift** (L1/TROPISM §F + algorithms/telos_drift.md).
//!
//! L0/cards/P07_mortality (mortality protection) P14.c telos drift semantics:
//!   - Sparse-vector PROXY (no substrate-side LLM yet): owner objective declares
//!     weight vector over node_type prefixes; sporocarp centroid = fractional
//!     distribution of recent daily sporocarps; alignment = cosine similarity.
//!   - Birth-period suspended → telos_alignment_pending (daily, not immune).
//!   - Drift threshold grading per L1/TROPISM §F + algorithms/telos_drift.md.

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

/// **M26.4 F20 OwnerObjective** — owner-declared sparse weight vector over
/// `node_type_prefix` space, used by P14.c telos_alignment cosine proxy.
///
/// PROXY note: doctrine (L1/TROPISM §F + algorithms/telos_drift.md) prescribes
/// an LLM-embedding-based centroid. M26.4 substrates lack substrate-side LLM
/// (P2.a "adjacent tooling internalization" is M27+). We ship a faithful
/// PROXY: cosine over sparse prefix-weight vectors. Each `weight` is a
/// repr-float string for cross-language determinism (matches signal #6 ratio
/// convention). Future M27+ swaps cosine inputs to true embeddings without
/// breaking the substrate's surface contract — the cosine output remains
/// `[-1, +1]` and the threshold grading remains §F.1.
#[derive(Debug, Clone)]
pub struct OwnerObjective {
    /// Stable identifier for this objective declaration (operator-supplied).
    pub objective_id: String,
    /// Cycle at which this objective was declared. Anchors the I4 audit.
    pub declared_at_cycle: u64,
    /// Sparse weight vector: `node_type_prefix → weight`. Sum SHOULD be
    /// positive (substrate normalizes during cosine compute). All weights
    /// ≥ 0; negative weights MAY be added in future revisions to express
    /// "actively against" but are currently rejected.
    pub weights: Vec<(String, f64)>,
}

/// Seed F20 owner objective — empty by default. The substrate falls back to
/// the §F.1 branch-2 path (centroid over recent trajectory deltas) when no
/// owner objective is declared. Operator MAY declare via mutation_type=
/// "owner_objective_declaration" (CI per F20).
pub fn seed_owner_objective() -> Option<OwnerObjective> {
    None
}

/// Encode an OwnerObjective into canonical-bytes (the
/// `mutation:owner_objective_declaration` content payload).
/// ```text
/// Map({
///   "objective_id": String,
///   "declared_at_cycle": Uint,
///   "weights": Array(Map({"prefix": String, "weight_repr": String}))
/// })
/// ```
pub fn encode_owner_objective(obj: &OwnerObjective) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "objective_id".to_string(),
        Value::String(obj.objective_id.clone()),
    );
    m.insert(
        "declared_at_cycle".to_string(),
        Value::Uint(obj.declared_at_cycle),
    );
    let weights_array: Vec<Value> = obj
        .weights
        .iter()
        .map(|(prefix, w)| {
            let mut entry = BTreeMap::new();
            entry.insert("prefix".to_string(), Value::String(prefix.clone()));
            entry.insert("weight_repr".to_string(), Value::String(format!("{w:?}")));
            Value::Map(entry)
        })
        .collect();
    m.insert("weights".to_string(), Value::Array(weights_array));
    cb_encode(&Value::Map(m)).expect("owner_objective encode infallible")
}

/// Decode an OwnerObjective from canonical-bytes. Returns None if shape is
/// wrong (operator caller emits C5 attestation_invalid in that case).
pub fn decode_owner_objective(bytes: &[u8]) -> Option<OwnerObjective> {
    use myco_kernel_shared::canonical_bytes::decode;
    let v = decode(bytes).ok()?;
    let m = match v {
        Value::Map(m) => m,
        _ => return None,
    };
    let objective_id = match m.get("objective_id")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let declared_at_cycle = match m.get("declared_at_cycle")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let weights_arr = match m.get("weights")? {
        Value::Array(a) => a.clone(),
        _ => return None,
    };
    let mut weights: Vec<(String, f64)> = Vec::with_capacity(weights_arr.len());
    for entry_v in weights_arr {
        let entry = match entry_v {
            Value::Map(em) => em,
            _ => return None,
        };
        let prefix = match entry.get("prefix")? {
            Value::String(s) => s.clone(),
            _ => return None,
        };
        let weight_repr = match entry.get("weight_repr")? {
            Value::String(s) => s.clone(),
            _ => return None,
        };
        let w: f64 = weight_repr.parse().ok()?;
        if w < 0.0 || !w.is_finite() {
            // Reject negative / NaN / inf weights (see F20 doc comment).
            return None;
        }
        weights.push((prefix, w));
    }
    Some(OwnerObjective {
        objective_id,
        declared_at_cycle,
        weights,
    })
}

/// `owner_objective_declared:{objective_id}` event — emitted after a
/// successful CI-attested owner_objective_declaration mutation.
pub const NODE_TYPE_OWNER_OBJECTIVE_DECLARED_PREFIX: &str = "owner_objective_declared:";

/// Encode the `owner_objective_declared` event body.
pub fn encode_owner_objective_declared(
    objective_id: &str,
    declared_at_cycle: u64,
    weights_count: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "objective_id".to_string(),
        Value::String(objective_id.to_string()),
    );
    m.insert(
        "declared_at_cycle".to_string(),
        Value::Uint(declared_at_cycle),
    );
    m.insert("weights_count".to_string(), Value::Uint(weights_count));
    cb_encode(&Value::Map(m)).expect("owner_objective_declared encode infallible")
}

/// **M26.4 telos_drift events** (L1/TROPISM §F + algorithms/telos_drift.md).
///
/// Five grading levels per §F threshold table:
/// - `telos_alignment_pending` — birth-period suspended; daily, not immune
/// - `telos_alignment_low` — 0.4 < cos ≤ 0.6, observability, daily
/// - `telos_drift` (daily) — 0.2 < cos ≤ 0.4
/// - `telos_drift` (elevated) — 0.0 < cos ≤ 0.2
/// - `telos_drift_critical` (CRITICAL → C24) — cos ≤ 0
pub const NODE_TYPE_TELOS_ALIGNMENT_PENDING: &str = "telos_alignment_pending";
/// `telos_alignment_low` event — emitted when cosine ∈ (0.4, 0.6]: observability,
/// not yet drift. Daily class, not immune.
pub const NODE_TYPE_TELOS_ALIGNMENT_LOW: &str = "telos_alignment_low";
/// `telos_drift` event — emitted when cosine ∈ (0.2, 0.4] (regular) or
/// (0.0, 0.2] (elevated). Daily class. Content's `grade` field
/// distinguishes "drift" vs "drift_elevated".
pub const NODE_TYPE_TELOS_DRIFT: &str = "telos_drift";
/// `telos_drift_critical` event — emitted when cosine ≤ 0 (CRITICAL grade
/// per §F.1). Paired with C24_telos_drift_critical immune sporocarp.
pub const NODE_TYPE_TELOS_DRIFT_CRITICAL: &str = "telos_drift_critical";

/// **Phase ② C75** — `cultivator_fiduciary_strain` meta-immune sporocarp
/// subtype (META §7.7 + COV01 §3.5/§4.4). Emitted by the observatory when the
/// cultivar's `telos_drift` has fired PERSISTENTLY over a 180-day rolling
/// wall-clock window AND the cultivator has taken NO fiduciary action in that
/// window (no L0/L1 amendment, no objective re-declaration, no bet retirement,
/// no succession). This is a META-immune signal: it flags the CULTIVATOR's
/// neglect of a persistently-drifting cultivar, NOT a substrate fault. It is
/// informational/relational (NOT in the §1.1 CRITICAL auto-quarantine table —
/// it does NOT quarantine the substrate); it surfaces the drift to external
/// witnesses (successor cultivator, posterity-trustees). Fired via
/// `emit_immune_sporocarp` (detector_id `C75_cultivator_fiduciary_strain`).
pub const NODE_TYPE_CULTIVATOR_FIDUCIARY_STRAIN: &str = "cultivator_fiduciary_strain";

/// **Phase ② C40 birth-suspension** — `bet_weakening_evaluation_suspended`
/// event (algorithms/bet_weakening_quorum.md §4 + L1/HARD_RULES §1.3/§3).
/// Emitted INSTEAD of evaluating the `bet_weakening_quorum` while the substrate
/// is in the birth period: signals #1/#3 are monotone growing from zero, #6 is
/// structurally < 1, so the falsifiability math is vacuous. Daily class, NOT
/// immune — it records WHY C40 did not evaluate, so an observer does not read
/// the absence of C40 during birth as "the bet is healthy".
pub const NODE_TYPE_BET_WEAKENING_EVALUATION_SUSPENDED: &str =
    "bet_weakening_evaluation_suspended";

/// Encode a telos_alignment status event (any of the four levels above).
pub fn encode_telos_status(
    cosine_repr: &str,
    grade: &str,
    at_cycle: u64,
    sample_window_size: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "cosine_repr".to_string(),
        Value::String(cosine_repr.to_string()),
    );
    m.insert("grade".to_string(), Value::String(grade.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    m.insert(
        "sample_window_size".to_string(),
        Value::Uint(sample_window_size),
    );
    cb_encode(&Value::Map(m)).expect("telos_status encode infallible")
}
