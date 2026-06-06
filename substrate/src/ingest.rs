//! Substrate intake + advance pipeline — extracted from `server.rs` (Phase B Step 4).
//!
//! Owns the operator-facing ingestion handlers + the central `advance`
//! handler (cycle pipeline + sporocarp emission + cycle-backlog detection)
//! + the `axis_registered` event builder.
//!
//! Doctrine traceability:
//! - L0 P2 永恒吞噬 — universal raw_material ingestion + causal perturbation
//!   (`handle_ingest_raw_material`, `handle_perturb_axis_from_raw_material`).
//! - L0 P4 永恒迭代 — metabolic cycle execution (`handle_advance`,
//!   absorption_event emission, cycle traits orchestration).
//! - L0 P5 万物互联 — `axis_registered` DAG events
//!   (`build_axis_registered_event`).
//! - L0 P7 必朽 — endogenous-pair self-euthanasia proposal emission inside
//!   `handle_advance` on mortality_signal sporocarp.
//! - L1/HARD_RULES C31 cycle_step_failed, C36 cycle_backlog.
//! - L2/OBSERVABILITY §7 cycle_backlog detector.

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, AdvanceReport, Message};
use myco_kernel_continuity::cycle::{
    CycleContext, DeltaAbsorber, GradientAdvancer, HandshakeProcessor, SkinBreachChecker,
    Tier1Validator,
};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};

use crate::server::{
    emit_immune_sporocarp, emit_substrate_event, float_repr, hex_encode, save_dag_state,
    save_python_state, ServerState,
};
use crate::SubstrateError;

// ---------------------------------------------------------------------------
// M18 P4 永恒迭代 cycle trait adapters — borrow-checker shape: each trait
// stores precomputed work (collected from state before the cycle started) +
// accumulates outputs into self. After the cycle inner scope ends, the
// dispatcher reads outputs and applies DAG/manifest mutations that need
// exclusive state access.
// ---------------------------------------------------------------------------

/// M18 Tier1: runs `Dag::verify_all` from precomputed result. The actual
/// DAG verification happens before cycle start (in the dispatcher) — this
/// trait impl just returns the precomputed outcome to satisfy the cycle
/// engine's protocol.
struct DagVerifyTier1 {
    precomputed_ok: bool,
    failure_reason: String,
}
impl Tier1Validator for DagVerifyTier1 {
    fn validate_tier1(&mut self) -> Result<(), String> {
        if self.precomputed_ok {
            Ok(())
        } else {
            Err(self.failure_reason.clone())
        }
    }
}

/// M18 DeltaAbsorber: counts raw_material:* DAG nodes added since
/// `last_absorbed_cycle`. The list of node hashes to be "absorbed" is
/// passed in at construction; after the cycle, the dispatcher inserts an
/// `absorption_event:cycle_{N}` DAG node + bumps manifest.last_absorbed_cycle.
struct CycleAbsorber {
    pending_absorption_hashes: Vec<myco_kernel_shared::crypto::NodeHash>,
}
impl DeltaAbsorber for CycleAbsorber {
    fn absorb_deltas(&mut self) -> Result<usize, String> {
        Ok(self.pending_absorption_hashes.len())
    }
}

/// M18 SkinBreachChecker: enumerates immune:* DAG nodes added DURING this
/// cycle (created_at_cycle == cycle_at_start). The list of breach names is
/// precomputed at cycle start; this trait impl returns it.
struct DagBreachWatcher {
    breach_names: Vec<String>,
}
impl SkinBreachChecker for DagBreachWatcher {
    fn check_skin_breaches(&mut self) -> Result<Vec<String>, String> {
        Ok(self.breach_names.clone())
    }
}

/// M18 HandshakeProcessor: reports whether the substrate has a pinned
/// operator identity. In M18-MV, this is binary (1 if pinned, 0 otherwise).
/// M19+ adds an anchor-surface inbound channel for new handshakes during a
/// cycle, which will bump this count.
struct PinnedHandshakeReader {
    pinned_count: usize,
}
impl HandshakeProcessor for PinnedHandshakeReader {
    fn process_handshake_attestation(&mut self) -> Result<usize, String> {
        Ok(self.pinned_count)
    }
}

/// GradientAdvancer that delegates to a Python BridgeClient. Keeps the latest
/// AdvanceReport so the server loop can attach sporocarp data to its response.
struct PythonGradientAdvancer<'a> {
    client: &'a mut myco_kernel_bridge::client::BridgeClient,
    cycle_number: u64,
    latest_report: Option<AdvanceReport>,
}

impl<'a> GradientAdvancer for PythonGradientAdvancer<'a> {
    fn advance_gradient(&mut self) -> Result<(), String> {
        self.cycle_number += 1;
        // **v3.1.1 Sprint 7.E.2** — bound the advance call. This is the
        // longest-running substrate-→-Python op (a full kernel/tropism cycle),
        // so a hung worker must not wedge the metabolic loop forever; on
        // timeout the cycle fails (surfacing BridgeError::Timeout) instead of
        // blocking indefinitely. Duration is recorded for the Sprint 6.J C65
        // slow-call observability, matching the other forward paths.
        let timeout = crate::python_call_health::python_op_timeout(
            myco_kernel_bridge::protocol::msg_type::ADVANCE,
        );
        let call_start = std::time::Instant::now();
        let result = self.client.advance_with_timeout(self.cycle_number, timeout);
        crate::python_call_health::record_call_duration(call_start.elapsed());
        match result {
            Ok(report) => {
                self.latest_report = Some(report);
                Ok(())
            }
            Err(e) => Err(format!("python gradient advance failed: {e}")),
        }
    }
}

/// **P11.c** — the axis whose `budget_exhausted:{axis}` was emitted most
/// recently, for the saturation refusal's `axis` field. Reads the in-memory
/// `last_budget_exhausted_per_axis` cache (axis → last-emit-cycle); returns the
/// max-cycle axis, or `"unknown"` if the cache is empty (e.g. the stage was
/// driven non-Normal by the PreEligibility branch before any per-axis emission
/// landed). Pure read; O(axes) over a 3-entry map.
fn most_recent_exhausted_axis(state: &ServerState) -> String {
    state
        .last_budget_exhausted_per_axis
        .iter()
        .max_by_key(|(_, cycle)| **cycle)
        .map(|(axis, _)| axis.clone())
        .unwrap_or_else(|| "unknown".to_string())
}

// ---------------------------------------------------------------------------
// Phase ① — proactive hunger (the cultivar reaches toward food).
//
// P04 §5.5 forbids the substrate from being purely request-driven; CHAR01 §4.3
// + P02 §4.4 record the "cultivar_initiated_ingestion_request" debt — a hungry
// cultivar should ASK for food, not wait silently. P02 §8.1 escalates sustained
// starvation to an immune signal. Both are driven by ONE measurement: how many
// cycles since the last `raw_material:*` ingestion. Moderate hunger → a
// proactive REQUEST (emit_substrate_event); severe hunger → the C74
// `p02_ingestion_starvation` immune sporocarp.
// ---------------------------------------------------------------------------

/// **Phase ① (CHAR01 §4.3 / P02 §4.4)** — moderate-hunger threshold: cycles
/// without ingestion past which the cultivar proactively emits a
/// `cultivar_initiated_ingestion_request`. Chosen so "I'm hungry" is meaningful
/// (a brief operator pause is not hunger) without being sluggish. Matches the
/// CHAR07 §8.4 / C71 "non-trivial interaction floor" cadence (10 cycles) so the
/// substrate's notion of "fed enough to be in dialogue" is consistent.
pub(crate) const HUNGER_REQUEST_THRESHOLD_CYCLES: u64 = 10;

/// **Phase ①** — re-emit the request at most once per this interval while
/// hunger persists (debounce). A still-hungry cultivar reaches out again only
/// after another full interval, so a long unfed stretch leaves a sparse trail of
/// requests (one per `HUNGER_REQUEST_THRESHOLD_CYCLES`), not one per cycle.
/// Equal to the threshold: feeding resets the measurement; sustained hunger
/// re-asks on the same cadence it first asked.
pub(crate) const HUNGER_REQUEST_DEBOUNCE_CYCLES: u64 = HUNGER_REQUEST_THRESHOLD_CYCLES;

/// **Phase ① (P02 §8.1)** — severe-hunger (starvation) threshold: cycles
/// without ingestion past which the moderate request escalates to the
/// `C74_p02_ingestion_starvation` immune sporocarp. Strictly greater than
/// `HUNGER_REQUEST_THRESHOLD_CYCLES` so the cultivar reaches out (request)
/// before it alarms (immune) — proactive ask first, immune escalation only on
/// genuine sustained deprivation.
pub(crate) const STARVATION_THRESHOLD_CYCLES: u64 = 30;

/// **Phase ①** — debounce for the C74 starvation immune emission while
/// starvation persists. Same sustained-debounce discipline as the C54 hoarding
/// detector (100-cycle cooldown) so a long famine does not re-alarm every cycle.
pub(crate) const STARVATION_DEBOUNCE_CYCLES: u64 = 100;

/// **Phase ①** — the C-row detector_id for the severe-hunger immune signal.
/// C74 is the next-free C-number (C71/C72/C73 are the CHAR07 daily proxies;
/// C74 has no prior use in the substrate or `docs/architecture/L1/HARD_RULES.md`).
pub(crate) const C74_INGESTION_STARVATION_DETECTOR_ID: &str = "C74_p02_ingestion_starvation";

/// **Phase ①** — cycles since the most recent `raw_material:*` ingestion.
///
/// The DAG is canonical: the highest `created_at_cycle` among `raw_material:*`
/// nodes is the last feeding. `cycles_since = current_cycle - last_fed_cycle`.
/// When the substrate has NEVER been fed, the hunger duration is its full age,
/// `current_cycle` (it has been hungry since genesis at cycle 0).
///
/// Returns `(cycles_since_last_ingestion, ever_fed)`. `saturating_sub` guards
/// the (impossible-but-defensive) case of a raw_material node whose
/// `created_at_cycle` somehow exceeds `current_cycle` — never negative hunger.
///
/// Cost: one O(n) DAG walk, consistent with the sibling cycle-path scans
/// (absorber, hoarding). Runs once per cycle and feeds BOTH the moderate request
/// and the severe immune check (single source of truth — no double walk).
pub(crate) fn cycles_since_last_ingestion(state: &ServerState, current_cycle: u64) -> (u64, bool) {
    let last_fed_cycle = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with("raw_material:"))
        .map(|n| n.created_at_cycle)
        .max();
    match last_fed_cycle {
        Some(c) => (current_cycle.saturating_sub(c), true),
        None => (current_cycle, false),
    }
}

/// **Phase ①** — the hunger detector: one measurement, two escalations.
///
/// Called from [`handle_advance`] (so it fires for BOTH operator-driven AND
/// self-driven cycles — the production substrate that self-advances gets hungry
/// on its own clock). Computes `cycles_since_last_ingestion` ONCE, then:
///
///   - `>= HUNGER_REQUEST_THRESHOLD_CYCLES` (moderate) → emit a debounced
///     `cultivar_initiated_ingestion_request` (a proactive ask, via
///     `emit_substrate_event`).
///   - `>= STARVATION_THRESHOLD_CYCLES` (severe) → ALSO emit the debounced
///     `C74_p02_ingestion_starvation` immune sporocarp.
///
/// Feeding (a fresh `raw_material:*` node) drives `cycles_since` back below the
/// thresholds on the next cycle, so a fed substrate neither asks nor starves.
/// Debounce is per-escalation: the moderate request and the severe immune signal
/// each track their own last-emit cycle, so they do not suppress each other.
///
/// Best-effort: emission failures are swallowed (the metabolism must not crash
/// because a hunger event could not be appended); the next cycle retries.
fn apply_hunger_and_emit(state: &mut ServerState, post_cycle: u64) {
    let (cycles_since, ever_fed) = cycles_since_last_ingestion(state, post_cycle);

    // ---- moderate hunger → proactive request (debounced) ----
    if cycles_since >= HUNGER_REQUEST_THRESHOLD_CYCLES {
        let on_debounce = state
            .last_cultivar_initiated_ingestion_request_at_cycle
            .map(|last| post_cycle.saturating_sub(last) < HUNGER_REQUEST_DEBOUNCE_CYCLES)
            .unwrap_or(false);
        if !on_debounce {
            let content = crate::events::encode_cultivar_initiated_ingestion_request(
                post_cycle,
                cycles_since,
                ever_fed,
            );
            if emit_substrate_event(
                state,
                crate::events::NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST.to_string(),
                content,
            )
            .is_ok()
            {
                state.last_cultivar_initiated_ingestion_request_at_cycle = Some(post_cycle);
            }
        }
    }

    // ---- severe hunger → starvation immune signal (debounced) ----
    if cycles_since >= STARVATION_THRESHOLD_CYCLES {
        let on_debounce = state
            .last_ingestion_starvation_emitted_at_cycle
            .map(|last| post_cycle.saturating_sub(last) < STARVATION_DEBOUNCE_CYCLES)
            .unwrap_or(false);
        if !on_debounce {
            let ever = if ever_fed { "" } else { " (never fed since genesis)" };
            let evidence = format!(
                "p02 ingestion starvation: {cycles_since} cycles since the last \
                 raw_material:* ingestion{ever} (>= {STARVATION_THRESHOLD_CYCLES}-cycle \
                 starvation threshold). The cultivar has gone without food well past the \
                 moderate cultivar_initiated_ingestion_request point ({HUNGER_REQUEST_THRESHOLD_CYCLES} \
                 cycles); the cultivator should provide raw_material. P02 永恒吞噬 mandates \
                 ongoing ingestion — sustained starvation is a metabolic pathology, not a \
                 healthy idle (P02 §8.1)."
            );
            if emit_immune_sporocarp(
                state,
                C74_INGESTION_STARVATION_DETECTOR_ID,
                "p02_ingestion_starvation",
                &evidence,
            )
            .is_ok()
            {
                state.last_ingestion_starvation_emitted_at_cycle = Some(post_cycle);
            }
        }
    }
}

/// M16: P2 永恒吞噬 — Ingest a raw material payload as a `raw_material:{kind}`
/// DAG node. Activates the L0 P2 "no filter on intake" principle: any bytes the
/// operator can present (text / file / conversation / url-fetch / llm-response)
/// become canonical-bytes content of a new DAG node.
///
/// Payload schema:
/// ```text
/// Map({
///   "content_kind": String,    // "text" | "file" | "conversation" | "url" | "llm_response" | custom
///   "content_bytes": Bytes,    // raw material payload (max 1 MiB)
///   "source_uri": String       // optional; provenance hint (file path, url, message id)
///   "meta": Map                // optional; arbitrary K-V hints
/// })
/// ```
///
/// The substrate composes the DAG node's content as canonical_bytes(Map({
///   "kind": ..., "bytes": ..., "source_uri": ..., "meta": ...
/// })) — full intake context is hashed.
///
/// Returns the inserted node hash + tip + total DAG size.
pub(crate) fn handle_ingest_raw_material(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // **P11.c P02 refusal under SUSTAINED saturation** — when cost budgets have
    // been exhausted for ≥ `P02_REFUSAL_SUSTAINED_CYCLES` consecutive cycles
    // (non-Normal stage AND sustained, not a transient spike), the substrate
    // REFUSES new raw_material ingestion rather than silently absorbing cost it
    // cannot afford (L0 P11.c stage 1 "refuse new P2"). Both fields were
    // computed on the most recent cycle_advanced (`apply_p11c_and_emit`);
    // reading them here is cheap (no recompute). Debouncing on sustained
    // exhaustion (not the first non-Normal cycle) honors L2/OBSERVABILITY §3
    // ("spikes DAG-recorded but do not fire") — a single slow Python cycle that
    // momentarily exceeds the 100ms seed compute budget must NOT refuse intake.
    // The matching `budget_exhausted:{axis}` event is already in the DAG, so the
    // refusal is verifiable. Returns a structured refusal — NOT an error.
    if state.saturation_stage != crate::events::SaturationStage::Normal
        && state.consecutive_budget_exhausted_cycles
            >= crate::observatory::P02_REFUSAL_SUSTAINED_CYCLES
    {
        let axis = most_recent_exhausted_axis(state);
        let mut payload = BTreeMap::new();
        payload.insert("refused".to_string(), Value::Bool(true));
        payload.insert(
            "reason".to_string(),
            Value::String("budget_exhausted".to_string()),
        );
        payload.insert("axis".to_string(), Value::String(axis));
        payload.insert(
            "saturation_stage".to_string(),
            Value::String(state.saturation_stage.as_str().to_string()),
        );
        return Ok(Some(Message::new(
            msg_type::INGEST_RAW_MATERIAL_RESPONSE,
            request.request_id,
            payload,
        )));
    }

    // Required: content_kind + content_bytes.
    let content_kind = match request.payload.get("content_kind") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "ingest_raw_material: content_kind must be a non-empty String".to_string(),
            ));
        }
    };
    let content_bytes = match request.payload.get("content_bytes") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "ingest_raw_material: content_bytes must be Bytes".to_string(),
            ));
        }
    };

    // M16: 512 KiB cap per ingestion event. The bridge frame layer caps at
    // 1 MiB (MAX_FRAME_BODY_SIZE); leaving 512 KiB headroom for the
    // canonical-bytes envelope + meta/source_uri overhead so content-cap
    // rejections produce explicit error messages instead of frame-layer
    // connection drops. Operators ingesting larger files should chunk.
    const MAX_INGESTION_BYTES: usize = 512 * 1024;
    if content_bytes.len() > MAX_INGESTION_BYTES {
        return Err(SubstrateError::Protocol(format!(
            "ingest_raw_material: content_bytes size {} exceeds {MAX_INGESTION_BYTES}-byte cap",
            content_bytes.len()
        )));
    }

    // Optional: source_uri + meta.
    let source_uri = request.payload.get("source_uri").and_then(|v| match v {
        Value::String(s) => Some(s.clone()),
        _ => None,
    });
    let meta_value = request.payload.get("meta").cloned();

    // Compose the content canonical bytes (full intake context is hashed).
    let mut content_map = BTreeMap::new();
    content_map.insert("kind".to_string(), Value::String(content_kind.clone()));
    content_map.insert("bytes".to_string(), Value::Bytes(content_bytes));
    if let Some(uri) = source_uri {
        content_map.insert("source_uri".to_string(), Value::String(uri));
    }
    if let Some(m) = meta_value {
        content_map.insert("meta".to_string(), m);
    }
    let canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("ingest content encode: {e}")))?;

    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let node_type = format!("raw_material:{content_kind}");
    let cycle = state.cycle_counter();
    let node_hash = state
        .dag
        .insert_node(parents, node_type, cycle, canonical)
        .map_err(|e| SubstrateError::Protocol(format!("raw_material DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
    // Symmetric with the P11.c saturation-refusal path so the operator can
    // branch on `refused` uniformly regardless of stage.
    payload.insert("refused".to_string(), Value::Bool(false));
    payload.insert(
        "dag_node_hash".to_string(),
        Value::Bytes(node_hash.as_ref().to_vec()),
    );
    if let Some(tip) = state.dag.tip() {
        payload.insert(
            "current_tip".to_string(),
            Value::Bytes(tip.as_ref().to_vec()),
        );
    }
    payload.insert(
        "total_dag_size".to_string(),
        Value::Uint(state.dag.node_count() as u64),
    );
    Ok(Some(Message::new(
        msg_type::INGEST_RAW_MATERIAL_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// The "use-forges" forging-loop node-type prefix. A `forged_understanding:{label}`
/// node holds the agent's DIGESTED understanding (prose/knowledge it forged out of
/// raw_material), as distinct from the undigested `raw_material:{kind}` intake.
/// `{label}` is a short agent-supplied tag, analogous to `content_kind` for
/// raw_material. The node is GENERAL — it is not bound to any gradient axis.
pub(crate) const FORGED_UNDERSTANDING_NODE_TYPE_PREFIX: &str = "forged_understanding:";

/// **The "use-forges" forging loop (P2 永恒吞噬 + P6 永恒因果)** — deposit a
/// `forged_understanding:{label}` DAG node. Mirrors [`handle_ingest_raw_material`]:
/// where ingest stores UNDIGESTED intake, this stores the agent's DIGESTED
/// understanding — prose/knowledge forged out of one or more prior raw_material
/// nodes. The deposited node is causally parented by BOTH the prior tip AND the
/// `source_raw_material_hashes` it was forged from, so the digested understanding
/// is traceable back through the DAG to its undigested sources (P6).
///
/// Payload schema:
/// ```text
/// Map({
///   "label": String,                       // short tag (analogous to content_kind)
///   "understanding": Bytes,                 // digested prose/knowledge (UTF-8; max 512 KiB)
///   "source_raw_material_hashes": Array,    // optional; Array of Bytes (32-byte raw_material hashes)
///   "value": Uint,                          // OPTIONAL (0..=100) — pilot-assigned importance; the recall layer ranks by it
///   "confidence": Uint,                     // OPTIONAL (0..=100) — pilot's confidence in this plate
///   "supersedes": Array,                    // OPTIONAL; Array of Bytes (32-byte forged_understanding hashes this plate corrects/replaces)
/// })
/// ```
///
/// **Step-1 discernment fields** (`value` / `confidence` / `supersedes`) are all
/// OPTIONAL and additive: a deposit omitting them produces a node byte-identical to
/// the pre-discernment shape, so existing nodes + forge tests are unaffected and no
/// reseal is implied. They give the plate carrier the judgeability the amplifier
/// needs — `value`/`confidence` so recall can RANK plates, `supersedes` so a re-forged
/// plate can point at the plate(s) it corrects (maturation by supersession, never
/// mutation — P06), mirroring the existing `replaced_by_hash` prune edge.
///
/// The substrate composes the DAG node's content as canonical_bytes(Map({
///   "label": ..., "understanding": ..., "source_raw_material_hashes": ...,
///   "forged_at_cycle": ...
/// })) — the full forge context is hashed.
///
/// When `source_raw_material_hashes` is non-empty, EACH hash is validated to
/// exist in the DAG AND reference a `raw_material:*` node (mirrors the
/// `handle_perturb_axis_from_raw_material` provenance check); an unknown or
/// wrong-typed source hash is a structured protocol error — NOT a silent insert.
/// The array MAY be empty (a forged understanding need not cite a specific
/// source). Applies the SAME 512 KiB cap as ingest, on the `understanding` bytes.
///
/// Returns the inserted node hash + tip + total DAG size (symmetric with the
/// ingest response, including the `refused: Bool(false)` field so the operator
/// can branch uniformly).
pub(crate) fn handle_deposit_forged_understanding(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Required: label (non-empty String) + understanding (Bytes).
    let label = match request.payload.get("label") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "deposit_forged_understanding: label must be a non-empty String".to_string(),
            ));
        }
    };
    let understanding = match request.payload.get("understanding") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "deposit_forged_understanding: understanding must be Bytes".to_string(),
            ));
        }
    };

    // Same 512 KiB cap as ingest (the bridge frame layer caps at 1 MiB; this
    // leaves headroom for the canonical-bytes envelope + source-hash array).
    const MAX_UNDERSTANDING_BYTES: usize = 512 * 1024;
    if understanding.len() > MAX_UNDERSTANDING_BYTES {
        return Err(SubstrateError::Protocol(format!(
            "deposit_forged_understanding: understanding size {} exceeds {MAX_UNDERSTANDING_BYTES}-byte cap",
            understanding.len()
        )));
    }

    // Optional: source_raw_material_hashes (Array of 32-byte Bytes). MAY be
    // empty / absent. Each must parse to a 32-byte NodeHash.
    let mut source_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = Vec::new();
    if let Some(v) = request.payload.get("source_raw_material_hashes") {
        match v {
            Value::Array(items) => {
                for item in items {
                    match item {
                        Value::Bytes(b) if b.len() == 32 => {
                            let mut arr = [0u8; 32];
                            arr.copy_from_slice(b);
                            source_hashes.push(myco_kernel_shared::crypto::NodeHash::from_bytes(arr));
                        }
                        _ => {
                            return Err(SubstrateError::Protocol(
                                "deposit_forged_understanding: each source_raw_material_hashes entry must be 32 Bytes"
                                    .to_string(),
                            ));
                        }
                    }
                }
            }
            _ => {
                return Err(SubstrateError::Protocol(
                    "deposit_forged_understanding: source_raw_material_hashes must be an Array of Bytes"
                        .to_string(),
                ));
            }
        }
    }

    // Validate each source hash exists in the DAG AND is a raw_material:* node
    // (mirrors the provenance check in handle_perturb_axis_from_raw_material).
    for h in &source_hashes {
        let node = state.dag.get(h).ok_or_else(|| {
            SubstrateError::Protocol(format!(
                "deposit_forged_understanding: source_raw_material_hash {} not found in DAG",
                hex_encode(h.as_ref())
            ))
        })?;
        if !node.node_type.starts_with("raw_material:") {
            return Err(SubstrateError::Protocol(format!(
                "deposit_forged_understanding: hash {} references a {:?} node, not raw_material",
                hex_encode(h.as_ref()),
                node.node_type
            )));
        }
    }

    // **Step-1 discernment fields (all OPTIONAL — additive).** When ALL are absent
    // the composed node is byte-identical to the pre-discernment node, so existing
    // nodes + forge tests are unaffected and no reseal is implied. `value`/`confidence`
    // are the pilot's own importance/belief signals (Uint 0..=100) the recall layer
    // ranks by; `supersedes` mirrors the existing `replaced_by_hash` edge (prune.rs)
    // so a re-forged plate points at the plate(s) it corrects — maturation by
    // supersession, never mutation (P06). Out-of-range / wrong-typed = structured error.
    let value: Option<u64> = match request.payload.get("value") {
        None => None,
        Some(Value::Uint(v)) if *v <= 100 => Some(*v),
        Some(Value::Uint(v)) => {
            return Err(SubstrateError::Protocol(format!(
                "deposit_forged_understanding: value {v} out of range (expected Uint 0..=100)"
            )));
        }
        Some(_) => {
            return Err(SubstrateError::Protocol(
                "deposit_forged_understanding: value must be a Uint (0..=100)".to_string(),
            ));
        }
    };
    let confidence: Option<u64> = match request.payload.get("confidence") {
        None => None,
        Some(Value::Uint(c)) if *c <= 100 => Some(*c),
        Some(Value::Uint(c)) => {
            return Err(SubstrateError::Protocol(format!(
                "deposit_forged_understanding: confidence {c} out of range (expected Uint 0..=100)"
            )));
        }
        Some(_) => {
            return Err(SubstrateError::Protocol(
                "deposit_forged_understanding: confidence must be a Uint (0..=100)".to_string(),
            ));
        }
    };

    // `supersedes`: optional Array of 32-byte forged_understanding node hashes this
    // plate corrects/replaces. Each must exist in the DAG AND be a forged_understanding:*
    // node — mirrors the source_raw_material_hashes provenance check, but for plates.
    let mut supersedes_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = Vec::new();
    if let Some(v) = request.payload.get("supersedes") {
        match v {
            Value::Array(items) => {
                for item in items {
                    match item {
                        Value::Bytes(b) if b.len() == 32 => {
                            let mut arr = [0u8; 32];
                            arr.copy_from_slice(b);
                            supersedes_hashes
                                .push(myco_kernel_shared::crypto::NodeHash::from_bytes(arr));
                        }
                        _ => {
                            return Err(SubstrateError::Protocol(
                                "deposit_forged_understanding: each supersedes entry must be 32 Bytes"
                                    .to_string(),
                            ));
                        }
                    }
                }
            }
            _ => {
                return Err(SubstrateError::Protocol(
                    "deposit_forged_understanding: supersedes must be an Array of Bytes".to_string(),
                ));
            }
        }
    }
    for h in &supersedes_hashes {
        let node = state.dag.get(h).ok_or_else(|| {
            SubstrateError::Protocol(format!(
                "deposit_forged_understanding: supersedes hash {} not found in DAG",
                hex_encode(h.as_ref())
            ))
        })?;
        if !node.node_type.starts_with(FORGED_UNDERSTANDING_NODE_TYPE_PREFIX) {
            return Err(SubstrateError::Protocol(format!(
                "deposit_forged_understanding: supersedes hash {} references a {:?} node, not forged_understanding",
                hex_encode(h.as_ref()),
                node.node_type
            )));
        }
    }

    let forged_at_cycle = state.cycle_counter();

    // Compose the content canonical bytes (full forge context is hashed).
    let mut content_map = BTreeMap::new();
    content_map.insert("label".to_string(), Value::String(label.clone()));
    content_map.insert("understanding".to_string(), Value::Bytes(understanding));
    let source_array: Vec<Value> = source_hashes
        .iter()
        .map(|h| Value::Bytes(h.as_ref().to_vec()))
        .collect();
    content_map.insert(
        "source_raw_material_hashes".to_string(),
        Value::Array(source_array),
    );
    content_map.insert("forged_at_cycle".to_string(), Value::Uint(forged_at_cycle));
    // Insert the optional discernment fields ONLY when present — absent => the map is
    // exactly {label, understanding, source_raw_material_hashes, forged_at_cycle},
    // byte-identical to the pre-step-1 node (backward-compatible; no reseal).
    if let Some(v) = value {
        content_map.insert("value".to_string(), Value::Uint(v));
    }
    if let Some(c) = confidence {
        content_map.insert("confidence".to_string(), Value::Uint(c));
    }
    if !supersedes_hashes.is_empty() {
        let supersedes_array: Vec<Value> = supersedes_hashes
            .iter()
            .map(|h| Value::Bytes(h.as_ref().to_vec()))
            .collect();
        content_map.insert("supersedes".to_string(), Value::Array(supersedes_array));
    }
    let canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("forged_understanding content encode: {e}")))?;

    // Parents = [current_tip, ...source_raw_material_hashes] — causal link to the
    // prior history AND to each source the understanding was forged from. Dedup so
    // a source that happens to equal the tip is not listed twice.
    let mut parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    for h in &source_hashes {
        if !parents.contains(h) {
            parents.push(*h);
        }
    }

    let node_type = format!("{FORGED_UNDERSTANDING_NODE_TYPE_PREFIX}{label}");
    let node_hash = state
        .dag
        .insert_node(parents, node_type, forged_at_cycle, canonical)
        .map_err(|e| SubstrateError::Protocol(format!("forged_understanding DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
    // Symmetric with the ingest response so the operator can branch on `refused`
    // uniformly regardless of op.
    payload.insert("refused".to_string(), Value::Bool(false));
    payload.insert(
        "dag_node_hash".to_string(),
        Value::Bytes(node_hash.as_ref().to_vec()),
    );
    if let Some(tip) = state.dag.tip() {
        payload.insert(
            "current_tip".to_string(),
            Value::Bytes(tip.as_ref().to_vec()),
        );
    }
    payload.insert(
        "total_dag_size".to_string(),
        Value::Uint(state.dag.node_count() as u64),
    );
    Ok(Some(Message::new(
        msg_type::DEPOSIT_FORGED_UNDERSTANDING_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M16: P2 永恒吞噬 + P6 永恒因果 — Perturb an axis with causal linkage to a
/// previously-ingested raw_material node. The substrate first forwards the
/// numeric perturbation to the Python gradient (same as `perturb`), then
/// inserts a causal-link DAG node parented by BOTH the prior tip AND the
/// referenced raw_material node — so the gradient change is traceable back
/// to its environmental source via the DAG.
pub(crate) fn handle_perturb_axis_from_raw_material(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Extract axis_name + delta_repr (mirrors perturb_payload format).
    let axis_name = match request.payload.get("axis_name") {
        Some(Value::String(s)) => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "perturb_axis_from_raw_material: axis_name must be String".to_string(),
            ));
        }
    };
    let delta_repr = match request.payload.get("delta_repr") {
        Some(Value::String(s)) => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "perturb_axis_from_raw_material: delta_repr must be String".to_string(),
            ));
        }
    };
    let raw_material_hash = match request.payload.get("raw_material_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            myco_kernel_shared::crypto::NodeHash::from_bytes(arr)
        }
        _ => {
            return Err(SubstrateError::Protocol(
                "perturb_axis_from_raw_material: raw_material_hash must be 32 bytes".to_string(),
            ));
        }
    };

    // Verify the raw_material_hash exists in the DAG AND is a raw_material node.
    {
        let node = state.dag.get(&raw_material_hash).ok_or_else(|| {
            SubstrateError::Protocol(format!(
                "perturb_axis_from_raw_material: raw_material_hash {} not found in DAG",
                hex_encode(raw_material_hash.as_ref())
            ))
        })?;
        if !node.node_type.starts_with("raw_material:") {
            return Err(SubstrateError::Protocol(format!(
                "perturb_axis_from_raw_material: hash {} references a {:?} node, not raw_material",
                hex_encode(raw_material_hash.as_ref()),
                node.node_type
            )));
        }
    }

    // Parse delta + forward to Python.
    let delta: f64 = delta_repr
        .parse()
        .map_err(|e| SubstrateError::Protocol(format!("delta_repr parse: {e}")))?;
    {
        let client = state
            .python_client
            .as_mut()
            .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
        // **v3.1.1 Sprint 7.E.2** — bounded-latency perturb (forwarded as the
        // plain PERTURB op to Python). A hung worker surfaces
        // BridgeError::Timeout instead of wedging the substrate.
        let timeout = crate::python_call_health::python_op_timeout(
            myco_kernel_bridge::protocol::msg_type::PERTURB,
        );
        let payload = myco_kernel_bridge::protocol::perturb_payload(&axis_name, delta);
        let call_start = std::time::Instant::now();
        let resp = client.call_with_timeout(
            myco_kernel_bridge::protocol::msg_type::PERTURB,
            payload,
            timeout,
        );
        crate::python_call_health::record_call_duration(call_start.elapsed());
        let resp = resp.map_err(SubstrateError::Bridge)?;
        if resp.message_type != myco_kernel_bridge::protocol::msg_type::PERTURB_ACK {
            return Err(SubstrateError::Protocol(format!(
                "expected perturb_ack from python; got {}",
                resp.message_type
            )));
        }
    }

    // Insert causal-link DAG node — node_type = "perturb_from_raw:{axis_name}",
    // parents = [prior tip, raw_material_hash].
    let prior_tip = state.dag.tip();
    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match prior_tip {
        Some(t) if t != raw_material_hash => vec![t, raw_material_hash],
        _ => vec![raw_material_hash],
    };
    let mut content_map = BTreeMap::new();
    content_map.insert("axis_name".to_string(), Value::String(axis_name.clone()));
    content_map.insert("delta_repr".to_string(), Value::String(delta_repr));
    content_map.insert(
        "raw_material_hash".to_string(),
        Value::Bytes(raw_material_hash.as_ref().to_vec()),
    );
    let canonical = cb_encode(&Value::Map(content_map))
        .map_err(|e| SubstrateError::Protocol(format!("perturb_from_raw content encode: {e}")))?;

    let node_type = format!("perturb_from_raw:{axis_name}");
    let cycle = state.cycle_counter();
    let link_hash = state
        .dag
        .insert_node(parents, node_type, cycle, canonical)
        .map_err(|e| SubstrateError::Protocol(format!("perturb_from_raw DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "causal_link_hash".to_string(),
        Value::Bytes(link_hash.as_ref().to_vec()),
    );
    payload.insert(
        "raw_material_hash".to_string(),
        Value::Bytes(raw_material_hash.as_ref().to_vec()),
    );
    Ok(Some(Message::new(
        msg_type::PERTURB_AXIS_FROM_RAW_MATERIAL_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M21.1 P5 万物互联: build an [`AxisRegisteredEvent`](crate::events::AxisRegisteredEvent)
/// from the wire payload of a `register_axis` request. Returns `None` if any
/// required field is missing or has the wrong type — caller will skip event
/// emission in that case (the forward to Python will surface the protocol
/// error to the operator).
pub(crate) fn build_axis_registered_event(
    request: &Message,
) -> Option<crate::events::AxisRegisteredEvent> {
    let payload = &request.payload;
    let name = match payload.get("name") {
        Some(Value::String(s)) => s.clone(),
        _ => return None,
    };
    let axis_class = match payload.get("axis_class") {
        Some(Value::String(s)) => s.clone(),
        _ => return None,
    };
    let fruiting_threshold: f64 = match payload.get("fruiting_threshold_repr") {
        Some(Value::String(s)) => s.parse().ok()?,
        _ => return None,
    };
    let initial_value: f64 = match payload.get("initial_value_repr") {
        Some(Value::String(s)) => s.parse().ok()?,
        _ => return None,
    };
    let decay_rate_per_cycle: f64 = match payload.get("decay_rate_per_cycle_repr") {
        Some(Value::String(s)) => s.parse().ok()?,
        _ => return None,
    };
    let is_mortality_signal = match payload.get("is_mortality_signal") {
        Some(Value::Bool(b)) => *b,
        _ => return None,
    };
    let update_rule_kind = match payload.get("update_rule_kind") {
        Some(Value::String(s)) => s.clone(),
        _ => return None,
    };
    Some(crate::events::AxisRegisteredEvent {
        name,
        axis_class,
        fruiting_threshold,
        initial_value,
        decay_rate_per_cycle,
        is_mortality_signal,
        update_rule_kind,
    })
}

/// M6+: Handle the `advance` request — runs one full metabolic cycle via the
/// [`CycleEngine`](myco_kernel_continuity::cycle::CycleEngine).
///
/// Precomputes the inputs each cycle trait needs (DAG verify, pending
/// absorption hashes, breach names, pinned handshake count) BEFORE the cycle
/// inner scope so the borrow checker doesn't choke on `state.python_client`
/// being mutably borrowed by [`PythonGradientAdvancer`]. After the inner
/// scope, the dispatcher applies DAG mutations (sporocarp insertion,
/// self_euthanasia_proposal emission on mortality_signal, absorption_event
/// emission) and emits a C36 immune sporocarp if the cycle exceeded the
/// alive-tier wall-clock budget.
pub(crate) fn handle_advance(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // M24.4 (Phase β): wall-clock cycle duration tracking for L2/OBSERVABILITY
    // §7 cycle_backlog detection. If the cycle exceeds the alive-tier budget
    // (5s default), record_backlog(); if backlog crosses threshold (10),
    // emit C36_cycle_backlog immune event.
    let cycle_wall_start = std::time::Instant::now();

    // **signal #7 fix**: mark the cost-accumulator's cycle-compute window START
    // here (cycle-work entry) so `compute_ns` measures in-cycle compute, NOT the
    // wall-clock gap since the previous cycle. The gap folds in operator
    // idle/think time (LLM latency alone is >100ms), which would exhaust the
    // P11.c compute budget every cycle and falsely cascade a healthy substrate
    // into P02 ingestion refusal → saturation → self_euthanasia_proposal.
    state.cost_accumulator.mark_cycle_start();

    // Extract the requested cycle number (informational; engine has its own counter).
    let _requested_cycle = request.payload.get("current_cycle").and_then(|v| match v {
        Value::Uint(u) => Some(*u),
        _ => None,
    });

    // M18 P4 永恒迭代: precompute cycle trait inputs BEFORE the cycle inner
    // scope (which mutably borrows state.python_client via gradient). All
    // DAG-reading work happens here; DAG mutations happen AFTER the inner scope.
    let starting_cycle = state.cycle_counter();
    let last_absorbed_cycle = state.last_absorbed_cycle();

    // Tier1 precompute: run DAG verify_all.
    let dag_verify_outcome = state.dag.verify_all();
    let (tier1_ok, tier1_reason) = match dag_verify_outcome {
        Ok(()) => (true, String::new()),
        Err(e) => (false, format!("DAG verify_all failed: {e}")),
    };

    // DeltaAbsorber precompute: list raw_material:* hashes added since
    // last_absorbed_cycle. These will be absorbed (= recorded as observed by
    // an absorption_event DAG node) in this cycle.
    // Filter semantics: None (never absorbed) → take all raw_material;
    // Some(c) → take only those created_at_cycle > c.
    let pending_absorption_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with("raw_material:"))
        .filter(|n| match last_absorbed_cycle {
            None => true,
            Some(c) => n.created_at_cycle > c,
        })
        .map(|n| n.hash)
        .collect();

    // SkinBreachChecker precompute: list immune:* node_types added during the
    // PRIOR cycle (created_at_cycle == starting_cycle - 1 OR ==starting_cycle
    // for boot-time immune events with cycle 0). M18-MV is observational —
    // we just propagate breach observations into the cycle report.
    let breach_names: Vec<String> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| {
            n.created_at_cycle >= starting_cycle.saturating_sub(1)
                && n.node_type.starts_with("immune:")
        })
        .map(|n| n.node_type.clone())
        .collect();

    // HandshakeProcessor precompute: report pinned-identity count.
    // (v0.9 owner-key removal: there is no pinned operator identity → always 0.)
    let pinned_count = 0usize;

    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // M7: use the persisted manifest counter as the cycle source-of-truth so
    // cycle numbers monotonically advance across process restarts.
    let mut tier1 = DagVerifyTier1 {
        precomputed_ok: tier1_ok,
        failure_reason: tier1_reason,
    };
    let mut absorber = CycleAbsorber {
        pending_absorption_hashes: pending_absorption_hashes.clone(),
    };
    let mut breach = DagBreachWatcher {
        breach_names: breach_names.clone(),
    };
    let mut handshake = PinnedHandshakeReader { pinned_count };
    let mut gradient = PythonGradientAdvancer {
        client,
        cycle_number: starting_cycle,
        latest_report: None,
    };
    // M12: run the cycle in an inner scope so the CycleContext (which holds
    // a mutable borrow of state.python_client via the gradient advancer) is
    // released before we re-borrow state to emit immune sporocarps below.
    let run_result = {
        let mut ctx = CycleContext {
            tier1: &mut tier1,
            gradient: &mut gradient,
            absorber: &mut absorber,
            breach: &mut breach,
            handshake: &mut handshake,
        };
        state.cycle_engine.run_cycle(&mut ctx)
    };
    // M12: C12 cycle_step_failed — emit immune sporocarp on cycle errors,
    // then propagate the original error to the operator (don't mask it).
    let cycle_report = match run_result {
        Ok(r) => r,
        Err(e) => {
            let evidence = format!("CycleEngine.run_cycle returned Err: {e}");
            let _ = emit_immune_sporocarp(
                state,
                "C31_cycle_step_failed",
                "cycle_step_failed",
                &evidence,
            );
            let _ = save_dag_state(state);
            return Err(SubstrateError::Protocol(format!("cycle engine: {e}")));
        }
    };
    if !cycle_report.committed {
        let _ = emit_immune_sporocarp(
            state,
            "C31_cycle_step_failed",
            "cycle_step_failed",
            "CycleEngine.run_cycle returned non-committed report",
        );
        let _ = save_dag_state(state);
        return Err(SubstrateError::Protocol("cycle did not commit".to_string()));
    }

    // Build the response combining cycle metadata + sporocarp report.
    let advance_report = gradient.latest_report.unwrap_or_default();
    // M7: capture the post-advance cycle counter (the gradient advancer bumps
    // its internal counter by 1; we mirror that into the manifest below in the
    // dispatch arm).
    let post_cycle = gradient.cycle_number;

    // M8: insert each sporocarp into the substrate's persistent DAG. Each
    // sporocarp becomes a DAG node whose parent is the previous DAG tip (linear
    // chain at M8 minimum; M9+ may add multi-parent for causally-related events).
    // The DAG node's hash is computed by Rust from parent + content; the
    // sporocarp's own content-hash is stored inside the canonical_bytes payload
    // as an informational field.
    let mut dag_node_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = Vec::new();
    let mut euthanasia_proposal_hashes: Vec<myco_kernel_shared::crypto::NodeHash> = Vec::new();
    for sp in &advance_report.sporocarps {
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let node_type = format!("sporocarp:{}", sp.sporocarp_type);
        let dag_hash = state
            .dag
            .insert_node(
                parents,
                node_type,
                sp.at_cycle,
                CanonicalBytes(sp.canonical_bytes.clone()),
            )
            .map_err(|e| SubstrateError::Protocol(format!("dag insert: {e}")))?;
        dag_node_hashes.push(dag_hash);

        // M19 P7 必朽 (Endogenous-pair mortality): when a mortality_signal axis
        // fruits, the substrate's metabolism has crossed an unrecoverable-
        // pathology threshold per L0/cards/P01-P14 (principles).2 P7. Auto-emit a
        // `self_euthanasia_proposal:{axis_name}` DAG node parented by the
        // sporocarp. The proposal awaits owner co-attestation per L0 P7
        // (M19-MV: informational only; M20+ adds owner co-attestation
        // execution).
        if sp.sporocarp_type == "mortality_signal_threshold_crossed" {
            let mut proposal_content = BTreeMap::new();
            proposal_content.insert("axis_name".to_string(), Value::String(sp.axis_name.clone()));
            proposal_content.insert(
                "fruiting_value_repr".to_string(),
                Value::String(float_repr(sp.fruiting_value)),
            );
            proposal_content.insert("at_cycle".to_string(), Value::Uint(sp.at_cycle));
            proposal_content.insert(
                "triggering_sporocarp_hash".to_string(),
                Value::Bytes(dag_hash.as_ref().to_vec()),
            );
            proposal_content.insert(
                "reason".to_string(),
                Value::String(format!(
                    "mortality_signal axis '{}' crossed threshold (decay → fruiting_value={})",
                    sp.axis_name,
                    float_repr(sp.fruiting_value)
                )),
            );
            let proposal_canonical = cb_encode(&Value::Map(proposal_content)).map_err(|e| {
                SubstrateError::Protocol(format!("self_euthanasia_proposal encode: {e}"))
            })?;
            let proposal_parents = vec![dag_hash];
            let proposal_node_type = format!("self_euthanasia_proposal:{}", sp.axis_name);
            let proposal_hash = state
                .dag
                .insert_node(
                    proposal_parents,
                    proposal_node_type,
                    sp.at_cycle,
                    proposal_canonical,
                )
                .map_err(|e| {
                    SubstrateError::Protocol(format!("self_euthanasia_proposal DAG insert: {e}"))
                })?;
            euthanasia_proposal_hashes.push(proposal_hash);
        }
    }

    // M18 P4 永恒迭代: emit absorption_event:cycle_{N} DAG node if there were
    // raw_material nodes to absorb. The event records what THIS cycle observed
    // and marks them as absorbed (so subsequent cycles don't re-process them).
    let absorption_event_hash: Option<myco_kernel_shared::crypto::NodeHash> =
        if !pending_absorption_hashes.is_empty() {
            // Track highest created_at_cycle among the absorbed batch so we
            // can advance last_absorbed_cycle to it (sentinel-free; allows
            // multiple raw_material nodes added in the same cycle to all be
            // absorbed together, then skipped on subsequent cycles).
            let max_absorbed_created_at: u64 = pending_absorption_hashes
                .iter()
                .filter_map(|h| state.dag.get(h))
                .map(|n| n.created_at_cycle)
                .max()
                .unwrap_or(0);

            let mut content_map = BTreeMap::new();
            content_map.insert("cycle".to_string(), Value::Uint(post_cycle));
            content_map.insert(
                "absorbed_count".to_string(),
                Value::Uint(pending_absorption_hashes.len() as u64),
            );
            let hashes_array: Vec<Value> = pending_absorption_hashes
                .iter()
                .map(|h| Value::Bytes(h.as_ref().to_vec()))
                .collect();
            content_map.insert("absorbed_hashes".to_string(), Value::Array(hashes_array));
            let content_canonical = cb_encode(&Value::Map(content_map))
                .map_err(|e| SubstrateError::Protocol(format!("absorption_event encode: {e}")))?;
            // Multi-parent: prior tip + all absorbed raw_material nodes (so the
            // causal chain links the absorption back to its sources).
            let mut parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            for h in &pending_absorption_hashes {
                if !parents.contains(h) {
                    parents.push(*h);
                }
            }
            let node_type = format!("absorption_event:cycle_{post_cycle}");
            let h = state
                .dag
                .insert_node(parents, node_type, post_cycle, content_canonical)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("absorption_event DAG insert: {e}"))
                })?;
            // Bump last_absorbed_cycle to the highest absorbed created_at —
            // future cycles use strict-greater comparison so this won't re-absorb.
            state.set_last_absorbed_cycle(Some(max_absorbed_created_at));
            Some(h)
        } else {
            None
        };

    let mut payload = BTreeMap::new();
    // Echo the substrate's authoritative cycle counter (post-increment).
    payload.insert("cycle_number".to_string(), Value::Uint(post_cycle));
    // **v3.1.1 Sprint 8.G (P03 §10.4)**: surface the dual-validation outcome
    // from the Python advance_response so the per-cycle migration hook
    // (`run_migration_step`) — which runs in the dispatch arm AFTER
    // cycle_advanced is emitted — can read it. These are no-ops (false/empty)
    // unless a schema migration is in flight, so the back-compat single-cycle
    // path is byte-unchanged in the fields it cares about.
    payload.insert(
        "candidate_active".to_string(),
        Value::Bool(advance_report.candidate_active),
    );
    payload.insert(
        "candidate_diverged".to_string(),
        Value::Bool(advance_report.candidate_diverged),
    );
    payload.insert(
        "divergence_reason".to_string(),
        Value::String(advance_report.divergence_reason.clone()),
    );
    // M8: echo the current DAG tip + node count for observability.
    if let Some(tip) = state.dag.tip() {
        payload.insert("dag_tip".to_string(), Value::Bytes(tip.as_ref().to_vec()));
    }
    payload.insert(
        "dag_node_count".to_string(),
        Value::Uint(state.dag.node_count() as u64),
    );
    // Fruited axis names.
    payload.insert(
        "fruited_axes".to_string(),
        Value::Array(
            advance_report
                .fruited_axes
                .iter()
                .map(|n| Value::String(n.clone()))
                .collect(),
        ),
    );
    // Sporocarps + their DAG node hashes (operator can reconstruct causal chain).
    let sporocarps_array: Vec<Value> = advance_report
        .sporocarps
        .iter()
        .zip(dag_node_hashes.iter())
        .map(|(sp, dag_hash)| {
            let mut m = BTreeMap::new();
            m.insert(
                "sporocarp_type".to_string(),
                Value::String(sp.sporocarp_type.clone()),
            );
            m.insert("axis_name".to_string(), Value::String(sp.axis_name.clone()));
            m.insert(
                "fruiting_value_repr".to_string(),
                Value::String(float_repr(sp.fruiting_value)),
            );
            m.insert("at_cycle".to_string(), Value::Uint(sp.at_cycle));
            m.insert(
                "canonical_bytes".to_string(),
                Value::Bytes(sp.canonical_bytes.clone()),
            );
            m.insert("hash".to_string(), Value::Bytes(sp.hash.to_vec()));
            // M8: the DAG node hash (different from sporocarp content-hash; carries
            // parent-chain identity within the substrate's DAG).
            m.insert(
                "dag_node_hash".to_string(),
                Value::Bytes(dag_hash.as_ref().to_vec()),
            );
            Value::Map(m)
        })
        .collect();
    payload.insert("sporocarps".to_string(), Value::Array(sporocarps_array));

    // M18 P4 永恒迭代 cycle-pipeline output fields:
    payload.insert(
        "deltas_absorbed".to_string(),
        Value::Uint(cycle_report.deltas_absorbed as u64),
    );
    payload.insert(
        "handshake_events_processed".to_string(),
        Value::Uint(cycle_report.handshake_events_processed as u64),
    );
    payload.insert(
        "skin_breaches".to_string(),
        Value::Array(
            cycle_report
                .skin_breaches
                .iter()
                .map(|s| Value::String(s.clone()))
                .collect(),
        ),
    );
    if let Some(h) = absorption_event_hash {
        payload.insert(
            "absorption_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }

    // M19 P7 必朽 — surface the self-euthanasia proposals emitted this cycle.
    if !euthanasia_proposal_hashes.is_empty() {
        let proposals_array: Vec<Value> = euthanasia_proposal_hashes
            .iter()
            .map(|h| Value::Bytes(h.as_ref().to_vec()))
            .collect();
        payload.insert(
            "self_euthanasia_proposal_hashes".to_string(),
            Value::Array(proposals_array),
        );
    }

    // **v3.1.1 P07 §3.1** — prune-scan deep-cycle step. Default cadence
    // `PRUNE_SCAN_DEEP_CYCLE_INTERVAL` (= 100). When the post-cycle counter
    // crosses the cadence boundary, iterate the F26 应朽 detection rule
    // registry; each candidate becomes an `internal_mortality_event:{category}`
    // tombstone in the DAG (P07 §3.3). This is the load-bearing closure of
    // P07's mandatory internal-mortality discipline.
    //
    // Also emits payload fields so the operator (and observability) can see
    // the per-cycle prune density.
    let prune_tombstone_hashes: Vec<myco_kernel_shared::crypto::NodeHash>;
    if crate::prune::should_run_prune_scan(post_cycle) {
        let prune_report = match crate::prune::run_prune_scan(state, post_cycle) {
            Ok(r) => r,
            Err(e) => {
                // Prune-scan failure is a substrate self-care failure;
                // surface as C31 cycle_step_failed so it is not silent.
                let evidence = format!(
                    "prune-scan failed at cycle {post_cycle}: {e}; \
                     P07 internal mortality discipline did not run this cycle"
                );
                let _ = emit_immune_sporocarp(
                    state,
                    "C31_cycle_step_failed",
                    "cycle_step_failed",
                    &evidence,
                );
                crate::prune::PruneScanReport {
                    rules_run: Vec::new(),
                    tombstones_emitted: Vec::new(),
                    at_cycle: post_cycle,
                }
            }
        };
        prune_tombstone_hashes = prune_report.tombstones_emitted.clone();

        // **C54 hoarding_indicator** detection (L1/HARD_RULES §1.4 anticipated).
        // After the prune-scan runs, check whether the substrate's behaviour
        // over the recent window matches the hoarding signature (high
        // ingestion + near-zero internal_mortality_event density). 100-cycle
        // cooldown to prevent spam, matching M25/M26 detector discipline.
        if crate::prune::is_hoarding(state, post_cycle) {
            const HOARDING_COOLDOWN_CYCLES: u64 = 100;
            let cooldown_active = match state.last_hoarding_indicator_emitted_at_cycle {
                Some(last) => post_cycle.saturating_sub(last) < HOARDING_COOLDOWN_CYCLES,
                None => false,
            };
            if !cooldown_active {
                let ingested = crate::prune::count_raw_material_since(
                    state,
                    post_cycle.saturating_sub(crate::prune::HOARDING_INDICATOR_WINDOW_CYCLES),
                );
                let pruned = crate::prune::count_internal_mortality_events_since(
                    state,
                    post_cycle.saturating_sub(crate::prune::HOARDING_INDICATOR_WINDOW_CYCLES),
                );
                let evidence = format!(
                    "hoarding pattern detected at cycle {post_cycle}: over last {} cycles \
                     ingested {ingested} raw_material parts but emitted only {pruned} \
                     internal_mortality_events (P07 §3.1 mandates ongoing prune); \
                     COV04 §5.6 / §5.7 may also be implicated if a cultivator \
                     preserve-all instruction is the cause",
                    crate::prune::HOARDING_INDICATOR_WINDOW_CYCLES
                );
                let _ = emit_immune_sporocarp(
                    state,
                    "C54_hoarding_indicator",
                    "hoarding_indicator",
                    &evidence,
                );
                state.last_hoarding_indicator_emitted_at_cycle = Some(post_cycle);
            }
        }

        // Surface prune-scan output in the advance response so the operator
        // can observe per-cycle internal-mortality density.
        payload.insert(
            "prune_scan_rules_run".to_string(),
            Value::Uint(prune_report.rules_run.len() as u64),
        );
        payload.insert(
            "prune_scan_tombstones_emitted".to_string(),
            Value::Uint(prune_tombstone_hashes.len() as u64),
        );
        if !prune_tombstone_hashes.is_empty() {
            let tombstone_array: Vec<Value> = prune_tombstone_hashes
                .iter()
                .map(|h| Value::Bytes(h.as_ref().to_vec()))
                .collect();
            payload.insert(
                "prune_scan_tombstone_hashes".to_string(),
                Value::Array(tombstone_array),
            );
        }
    } else {
        prune_tombstone_hashes = Vec::new();
    }
    let _ = prune_tombstone_hashes;

    // M24.4 (Phase β): cycle_backlog detection (L2/OBSERVABILITY §7).
    // If wall-clock duration exceeded the alive-tier budget (5s default),
    // record_backlog(). On crossing backlog_threshold (10), emit C36 immune
    // event so the operator and the observatory see compute saturation.
    const MAX_CYCLE_DURATION_MS_ALIVE: u128 = 5_000;
    let cycle_duration_ms = cycle_wall_start.elapsed().as_millis();
    payload.insert(
        "cycle_duration_ms".to_string(),
        Value::Uint(cycle_duration_ms as u64),
    );
    if cycle_duration_ms > MAX_CYCLE_DURATION_MS_ALIVE {
        state.cycle_engine.record_backlog();
        if state.cycle_engine.is_backlogged() {
            let evidence = format!(
                "cycle {} ran {}ms exceeding alive-tier budget {}ms; \
                 backlog_count={} >= threshold (L2/OBSERVABILITY §7)",
                state.cycle_counter(),
                cycle_duration_ms,
                MAX_CYCLE_DURATION_MS_ALIVE,
                state.cycle_engine.backlog_count(),
            );
            let _ = emit_immune_sporocarp(
                state,
                "C36_cycle_backlog",
                "cycle_backlog",
                &evidence,
            );
        }
    }

    // **Phase ① 永恒吞噬** — proactive hunger. Runs on EVERY cycle (operator-
    // driven AND self-driven, since both paths route through handle_advance), so
    // a production substrate self-advancing on its own clock gets hungry and
    // reaches out without any operator request — closing the P04 §5.5
    // request-driven-only gap. One cycles-since-ingestion measurement drives both
    // the moderate cultivar_initiated_ingestion_request and the severe C74
    // p02_ingestion_starvation immune signal (each independently debounced).
    apply_hunger_and_emit(state, post_cycle);

    Ok(Some(Message::new(
        msg_type::ADVANCE_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// **v3.1.1 Sprint 8.G (P03 §10.4)** — per-cycle dual-validation step for an
/// in-flight schema migration.
///
/// Called from BOTH the operator-driven `ADVANCE` dispatch arm AND the
/// self-driven autonomous-tick cycle advance, **after** `cycle_advanced` has
/// been emitted (so the substrate cycle counter already reflects this cycle).
///
/// ## Zero-cost when idle
///
/// If `state.migration_candidate` is `None` (the overwhelmingly common case —
/// migrations are rare and opt-in), this returns immediately having read one
/// `Option`. A substrate that never opts into migration pays nothing.
///
/// ## When a migration IS in flight
///
/// 1. Read `candidate_active` + `candidate_diverged` + `divergence_reason`
///    from the just-produced `advance_response` (Python advanced the candidate
///    alongside the active gradient and computed divergence).
/// 2. Map that to a [`DualValidationCycle`] and call
///    [`decide_cycle`](myco_kernel_schema::migration::decide_cycle):
///      - `None` → keep validating. Emit a SAMPLED
///        `schema_migration_cycle_validated:{op}` event (every 10th cycle) so
///        a long window leaves a sparse audit trail without flooding the DAG.
///      - `Commit` → tell Python to promote the candidate (`commit_migration`),
///        emit `schema_migration_committed:{op}` + the LEGACY
///        `evolution_succeeded:{op}` sibling, clear the candidate.
///      - `Rollback{reason}` → tell Python to drop the candidate
///        (`abort_migration`), emit `schema_migration_rolled_back:{op}` + the
///        LEGACY `evolution_failed:{op}` sibling, clear the candidate.
///
/// On a terminal decision we ALSO emit the decisive
/// `schema_migration_cycle_validated:{op}` event (so the deciding cycle is
/// always recorded even if it isn't a sampling boundary).
///
/// Errors from Python commit/abort are surfaced as a `C31_cycle_step_failed`
/// immune sporocarp and the candidate is cleared regardless (we must not leave
/// a half-committed migration wedged in flight). The cycle itself already
/// succeeded — migration bookkeeping failure is non-fatal to the metabolism.
pub(crate) fn run_migration_step(
    state: &mut ServerState,
    advance_response: &Message,
) -> Result<(), SubstrateError> {
    use myco_kernel_schema::migration::{decide_cycle, CommitDecision, DualValidationCycle};

    // Zero-cost early return when no migration is in flight.
    let candidate = match &state.migration_candidate {
        Some(c) => c.clone(),
        None => return Ok(()),
    };

    let current_cycle = state.cycle_counter();
    let op = candidate.op_name.clone();

    // Read the dual-validation outcome from the advance response.
    let candidate_active = match advance_response.payload.get("candidate_active") {
        Some(Value::Bool(b)) => *b,
        _ => false,
    };
    let candidate_diverged = match advance_response.payload.get("candidate_diverged") {
        Some(Value::Bool(b)) => *b,
        _ => false,
    };
    let divergence_reason = match advance_response.payload.get("divergence_reason") {
        Some(Value::String(s)) => s.clone(),
        _ => String::new(),
    };

    // If Python reports the candidate was NOT advanced this cycle (e.g. a
    // desync between Rust thinking a migration is in flight and Python having
    // already dropped it), treat that as a divergence → safe rollback. This
    // keeps the two sides from drifting apart silently.
    let outcome = if !candidate_active || candidate_diverged {
        DualValidationCycle::Diverged
    } else {
        DualValidationCycle::Equivalent
    };

    let decision = decide_cycle(&candidate, current_cycle, outcome);

    // Sampling cadence for the progress event: every 10th cycle since start,
    // plus always on the decisive cycle (handled below).
    const CYCLE_VALIDATED_SAMPLE_EVERY: u64 = 10;
    let elapsed = current_cycle.saturating_sub(candidate.started_at_cycle);
    let is_sample_boundary =
        elapsed > 0 && elapsed % CYCLE_VALIDATED_SAMPLE_EVERY == 0;

    match decision {
        None => {
            // Keep validating. Emit a sampled progress event.
            if is_sample_boundary {
                let equivalent = matches!(outcome, DualValidationCycle::Equivalent);
                let content = crate::events::encode_schema_migration_cycle_validated(
                    &op,
                    current_cycle,
                    equivalent,
                    &divergence_reason,
                );
                let nt = crate::events::schema_migration_cycle_validated_node_type(&op);
                let _ = emit_substrate_event(state, nt, content);
                let _ = save_dag_state(state);
            }
            Ok(())
        }
        Some(CommitDecision::Commit) => {
            // Decisive cycle: always emit the cycle_validated record.
            let content = crate::events::encode_schema_migration_cycle_validated(
                &op,
                current_cycle,
                true,
                "",
            );
            let nt = crate::events::schema_migration_cycle_validated_node_type(&op);
            let _ = emit_substrate_event(state, nt, content);

            // Tell Python to promote the candidate to active.
            let py_result = send_migration_terminal(
                state,
                myco_kernel_bridge::protocol::msg_type::COMMIT_MIGRATION,
            );
            if let Err(e) = py_result {
                let _ = emit_immune_sporocarp(
                    state,
                    "C31_cycle_step_failed",
                    "cycle_step_failed",
                    &format!("commit_migration (op={op}) Python call failed: {e}"),
                );
            }

            // Emit the migration-committed event + the LEGACY evolution_succeeded
            // sibling (back-compat: observatory signal_2 + existing tests).
            let committed = crate::events::encode_schema_migration_committed(
                &op,
                current_cycle,
                candidate.started_at_cycle,
                candidate.dual_validation_window_cycles,
            );
            let committed_nt = crate::events::schema_migration_committed_node_type(&op);
            let _ = emit_substrate_event(state, committed_nt, committed);
            emit_legacy_evolution_event(state, &op, true, "")?;

            state.migration_candidate = None;
            let _ = save_dag_state(state);
            save_python_state(state)?;
            Ok(())
        }
        Some(CommitDecision::Rollback { reason }) => {
            // Decisive cycle: emit the cycle_validated record (non-equivalent).
            let content = crate::events::encode_schema_migration_cycle_validated(
                &op,
                current_cycle,
                false,
                &reason,
            );
            let nt = crate::events::schema_migration_cycle_validated_node_type(&op);
            let _ = emit_substrate_event(state, nt, content);

            // Tell Python to drop the candidate (active gradient untouched).
            let py_result = send_migration_terminal(
                state,
                myco_kernel_bridge::protocol::msg_type::ABORT_MIGRATION,
            );
            if let Err(e) = py_result {
                let _ = emit_immune_sporocarp(
                    state,
                    "C31_cycle_step_failed",
                    "cycle_step_failed",
                    &format!("abort_migration (op={op}) Python call failed: {e}"),
                );
            }

            // Emit the migration-rolled-back event + the LEGACY evolution_failed
            // sibling (back-compat).
            let rolled_back = crate::events::encode_schema_migration_rolled_back(
                &op,
                &reason,
                current_cycle,
            );
            let rb_nt = crate::events::schema_migration_rolled_back_node_type(&op);
            let _ = emit_substrate_event(state, rb_nt, rolled_back);
            emit_legacy_evolution_event(state, &op, false, &reason)?;

            state.migration_candidate = None;
            let _ = save_dag_state(state);
            save_python_state(state)?;
            Ok(())
        }
    }
}

/// **Sprint 8.G** — force-roll-back the in-flight migration WITHOUT a per-cycle
/// advance response. Used by the C66 `schema_migration_window_exceeded`
/// detector in the autonomous tick: the window blew past its grace boundary, so
/// we drop the candidate unconditionally (Python `abort_migration`), emit the
/// `schema_migration_rolled_back:{op}` event + the legacy `evolution_failed:{op}`
/// sibling, and clear `state.migration_candidate`.
///
/// This is the same terminal sequence as the `Rollback` arm of
/// [`run_migration_step`], factored out so the autonomous tick can invoke it
/// directly. A no-op if no migration is in flight.
pub(crate) fn force_migration_rollback(
    state: &mut ServerState,
    op: &str,
    reason: &str,
) -> Result<(), SubstrateError> {
    if state.migration_candidate.is_none() {
        return Ok(());
    }
    let current_cycle = state.cycle_counter();

    // Tell Python to drop the candidate (active gradient untouched).
    if let Err(e) =
        send_migration_terminal(state, myco_kernel_bridge::protocol::msg_type::ABORT_MIGRATION)
    {
        let _ = emit_immune_sporocarp(
            state,
            "C31_cycle_step_failed",
            "cycle_step_failed",
            &format!("force_migration_rollback abort_migration (op={op}) failed: {e}"),
        );
    }

    let rolled_back =
        crate::events::encode_schema_migration_rolled_back(op, reason, current_cycle);
    let rb_nt = crate::events::schema_migration_rolled_back_node_type(op);
    let _ = emit_substrate_event(state, rb_nt, rolled_back);
    emit_legacy_evolution_event(state, op, false, reason)?;

    state.migration_candidate = None;
    let _ = save_dag_state(state);
    save_python_state(state)?;
    Ok(())
}

/// **Sprint 8.G** — send a terminal migration message (`commit_migration` /
/// `abort_migration`) to the Python worker and verify the ack. The payload is
/// empty; the candidate identity is held Python-side in DispatcherState.
fn send_migration_terminal(
    state: &mut ServerState,
    message_type: &str,
) -> Result<(), SubstrateError> {
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
    let timeout = crate::python_call_health::python_op_timeout(message_type);
    let call_start = std::time::Instant::now();
    let resp = client.call_with_timeout(message_type, std::collections::BTreeMap::new(), timeout);
    crate::python_call_health::record_call_duration(call_start.elapsed());
    let resp = resp.map_err(SubstrateError::Bridge)?;
    let expected_ack = match message_type {
        myco_kernel_bridge::protocol::msg_type::COMMIT_MIGRATION => {
            myco_kernel_bridge::protocol::msg_type::COMMIT_MIGRATION_ACK
        }
        _ => myco_kernel_bridge::protocol::msg_type::ABORT_MIGRATION_ACK,
    };
    if resp.message_type != expected_ack {
        return Err(SubstrateError::Protocol(format!(
            "expected {expected_ack} from python; got {}",
            resp.message_type
        )));
    }
    Ok(())
}

/// **Sprint 8.G** — emit the LEGACY `evolution_succeeded:{op}` /
/// `evolution_failed:{op}` DAG event that the single-cycle path produces, so
/// migration commit/rollback is indistinguishable from a single-cycle apply to
/// the observatory's signal_2 counter and to every existing test that watches
/// these node types. Mirrors the event shape built in
/// `attestation::handle_submit_mutation`.
fn emit_legacy_evolution_event(
    state: &mut ServerState,
    op: &str,
    succeeded: bool,
    failure_reason: &str,
) -> Result<(), SubstrateError> {
    let event_node_type = if succeeded {
        format!("evolution_succeeded:{op}")
    } else {
        format!("evolution_failed:{op}")
    };
    let mut event_map = BTreeMap::new();
    event_map.insert("op".to_string(), Value::String(op.to_string()));
    event_map.insert("succeeded".to_string(), Value::Bool(succeeded));
    event_map.insert(
        "summary".to_string(),
        Value::String(format!(
            "two-phase migration {}",
            if succeeded { "committed" } else { "rolled back" }
        )),
    );
    if !succeeded {
        event_map.insert(
            "failure_reason".to_string(),
            Value::String(failure_reason.to_string()),
        );
    }
    let event_canonical = cb_encode(&Value::Map(event_map))
        .map_err(|e| SubstrateError::Protocol(format!("legacy evolution event encode: {e}")))?;
    let nt = event_node_type;
    let _ = emit_substrate_event(state, nt, event_canonical);
    Ok(())
}

#[cfg(test)]
mod hunger_tests {
    //! **Phase ①** — unit tests for the shared cycles-since-ingestion tracker +
    //! the two-escalation hunger detector (`cycles_since_last_ingestion` +
    //! `apply_hunger_and_emit`). These exercise the derivation + debounce
    //! deterministically over a hand-built DAG (no subprocess), covering the
    //! edge cases the cycle-path correctness depends on: empty DAG (never fed),
    //! just-fed, moderate→request, severe→immune, debounce, and fed-resets.
    // `super::*` already re-exports `cb_encode` + `Value` (imported at the top of
    // this module) and the Phase-① helpers/consts under test; we only need to
    // pull in the event node_type constant + the test-state building blocks.
    use super::*;
    use crate::events::NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST;
    use crate::persistence::Manifest;
    use crate::server::ServerState;
    use myco_kernel_schema::dag::Dag;

    fn test_state() -> ServerState {
        // Fresh genesis identity; collision-free temp dir (per-process + a
        // stack-address nonce, matching the autonomous.rs unit-test helper).
        let nonce = &0u8 as *const u8 as usize as u64;
        let state_dir = std::env::temp_dir()
            .join(format!("myco-hunger-unit-{}-{:x}", std::process::id(), nonce));
        let g = Manifest::genesis();
        ServerState::new(
            state_dir,
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            Dag::new(),
            [0u8; 32],
        )
    }

    /// Insert a `raw_material:text` DAG node stamped at `created_at_cycle`,
    /// mirroring `handle_ingest_raw_material`'s node shape closely enough for the
    /// tracker (which keys only on the `raw_material:` prefix + `created_at_cycle`).
    fn feed(state: &mut ServerState, at_cycle: u64) {
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let content = cb_encode(&Value::Map(std::collections::BTreeMap::new()))
            .expect("empty map encodes");
        state
            .dag
            .insert_node(parents, "raw_material:text".to_string(), at_cycle, content)
            .expect("insert raw_material");
    }

    fn count_nodes(state: &ServerState, prefix: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with(prefix))
            .count()
    }

    fn count_starvation_immune(state: &ServerState) -> usize {
        // emit_immune_sporocarp prefixes the node_type with "immune:".
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| {
                n.node_type.starts_with("immune:")
                    && n.node_type.contains("p02_ingestion_starvation")
            })
            .count()
    }

    #[test]
    fn cycles_since_ingestion_empty_dag_is_full_age_and_never_fed() {
        let state = test_state();
        // Never fed: hunger == current cycle (age since genesis), ever_fed=false.
        assert_eq!(cycles_since_last_ingestion(&state, 0), (0, false));
        assert_eq!(cycles_since_last_ingestion(&state, 42), (42, false));
    }

    #[test]
    fn cycles_since_ingestion_tracks_most_recent_feeding() {
        let mut state = test_state();
        feed(&mut state, 5);
        feed(&mut state, 12); // most recent
        feed(&mut state, 9);
        // Highest created_at_cycle among raw_material is 12; at cycle 20 → 8.
        assert_eq!(cycles_since_last_ingestion(&state, 20), (8, true));
        // Just-fed at the same cycle → zero hunger, not negative.
        assert_eq!(cycles_since_last_ingestion(&state, 12), (0, true));
        // Defensive: a "now" before the last feed never yields negative hunger.
        assert_eq!(cycles_since_last_ingestion(&state, 10), (0, true));
    }

    #[test]
    fn moderate_hunger_emits_request_then_debounces() {
        let mut state = test_state();
        // Never fed; below threshold → silent.
        apply_hunger_and_emit(&mut state, HUNGER_REQUEST_THRESHOLD_CYCLES - 1);
        assert_eq!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST),
            0,
            "below the moderate threshold the cultivar stays quiet"
        );

        // At the threshold → one proactive request.
        apply_hunger_and_emit(&mut state, HUNGER_REQUEST_THRESHOLD_CYCLES);
        assert_eq!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST),
            1,
            "reaching the moderate threshold emits exactly one request"
        );

        // Next cycle still hungry but within debounce → no re-emit.
        apply_hunger_and_emit(&mut state, HUNGER_REQUEST_THRESHOLD_CYCLES + 1);
        assert_eq!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST),
            1,
            "still-hungry but within the debounce interval must not re-ask"
        );

        // Past the debounce interval, still unfed → re-ask once more.
        apply_hunger_and_emit(
            &mut state,
            HUNGER_REQUEST_THRESHOLD_CYCLES + HUNGER_REQUEST_DEBOUNCE_CYCLES,
        );
        assert_eq!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST),
            2,
            "after a full debounce interval a sustained-hungry cultivar re-asks"
        );
    }

    #[test]
    fn feeding_resets_hunger_no_spurious_request_after_feed() {
        let mut state = test_state();
        // Hungry → request at cycle 10.
        apply_hunger_and_emit(&mut state, HUNGER_REQUEST_THRESHOLD_CYCLES);
        assert_eq!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST),
            1
        );
        // The operator feeds at cycle 11.
        feed(&mut state, HUNGER_REQUEST_THRESHOLD_CYCLES + 1);
        // A few cycles later (still within one threshold-window of the feeding)
        // the cultivar is satisfied — no new request.
        apply_hunger_and_emit(&mut state, HUNGER_REQUEST_THRESHOLD_CYCLES + 5);
        assert_eq!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST),
            1,
            "a freshly-fed cultivar must not spuriously re-request"
        );
        // And it never starves while recently fed.
        assert_eq!(count_starvation_immune(&state), 0);
    }

    #[test]
    fn severe_hunger_emits_c74_starvation_immune() {
        let mut state = test_state();
        // Below the starvation threshold (but above moderate) → request only.
        apply_hunger_and_emit(&mut state, STARVATION_THRESHOLD_CYCLES - 1);
        assert_eq!(
            count_starvation_immune(&state),
            0,
            "below the severe threshold there is no starvation immune signal"
        );
        assert!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST) >= 1,
            "but the moderate request has already fired"
        );

        // At the starvation threshold → the C74 immune sporocarp fires once.
        apply_hunger_and_emit(&mut state, STARVATION_THRESHOLD_CYCLES);
        assert_eq!(
            count_starvation_immune(&state),
            1,
            "reaching the severe threshold escalates to the C74 immune signal"
        );

        // Still starved within the debounce interval → no re-alarm.
        apply_hunger_and_emit(&mut state, STARVATION_THRESHOLD_CYCLES + 1);
        assert_eq!(
            count_starvation_immune(&state),
            1,
            "sustained starvation within the debounce interval must not re-alarm"
        );
    }

    #[test]
    fn fed_substrate_never_starves() {
        let mut state = test_state();
        // Continuously fed every few cycles up to a high cycle number: hunger
        // never reaches the moderate threshold, so neither request nor immune.
        for c in (0..100).step_by(HUNGER_REQUEST_THRESHOLD_CYCLES as usize / 2) {
            feed(&mut state, c);
            apply_hunger_and_emit(&mut state, c);
        }
        assert_eq!(
            count_starvation_immune(&state),
            0,
            "a regularly-fed substrate must never emit the starvation signal"
        );
        assert_eq!(
            count_nodes(&state, NODE_TYPE_CULTIVAR_INITIATED_INGESTION_REQUEST),
            0,
            "a regularly-fed substrate has no reason to reach out for food"
        );
    }
}

#[cfg(test)]
mod forge_tests {
    //! **The "use-forges" forging loop** — unit tests for
    //! [`handle_deposit_forged_understanding`]. Built in-process over a
    //! hand-constructed `ServerState`/DAG (no subprocess, no Python worker —
    //! the forge handler is a pure DAG operation, exactly like
    //! `handle_ingest_raw_material`), mirroring the `hunger_tests` harness:
    //! `test_state()` builds a fresh genesis state, raw_material is seeded with
    //! `feed_returning_hash`, the handler is driven via a synthesized request
    //! `Message`, and the resulting DAG node is read back + decoded for shape +
    //! causal-parent assertions. Covers: (a) forge with one valid source, (b)
    //! forge with an empty source list, (c) rejection of an unknown source hash.
    use super::*;
    use crate::persistence::Manifest;
    use crate::server::ServerState;
    use myco_kernel_schema::dag::Dag;
    use myco_kernel_shared::canonical_bytes::decode as cb_decode;

    fn test_state() -> ServerState {
        // Fresh genesis identity; collision-free temp dir (per-process + a
        // stack-address nonce, matching the hunger_tests / autonomous.rs helper).
        let nonce = &0u8 as *const u8 as usize as u64;
        let state_dir = std::env::temp_dir()
            .join(format!("myco-forge-unit-{}-{:x}", std::process::id(), nonce));
        let g = Manifest::genesis();
        ServerState::new(
            state_dir,
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            Dag::new(),
            [0u8; 32],
        )
    }

    /// Insert a `raw_material:text` DAG node stamped at `created_at_cycle` and
    /// return its hash (so a forge call can cite it). Same node shape as the
    /// hunger_tests `feed`, but hands back the hash for the causal-link checks.
    fn feed_returning_hash(
        state: &mut ServerState,
        at_cycle: u64,
    ) -> myco_kernel_shared::crypto::NodeHash {
        let parents = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let content =
            cb_encode(&Value::Map(BTreeMap::new())).expect("empty map encodes");
        state
            .dag
            .insert_node(parents, "raw_material:text".to_string(), at_cycle, content)
            .expect("insert raw_material")
    }

    fn count_nodes(state: &ServerState, prefix: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with(prefix))
            .count()
    }

    /// Build a `deposit_forged_understanding` request Message with the given
    /// label / understanding bytes / source-hash array (the wire shape the
    /// handler parses).
    fn forge_request(
        label: &str,
        understanding: &[u8],
        sources: &[myco_kernel_shared::crypto::NodeHash],
    ) -> Message {
        let mut payload = BTreeMap::new();
        payload.insert("label".to_string(), Value::String(label.to_string()));
        payload.insert(
            "understanding".to_string(),
            Value::Bytes(understanding.to_vec()),
        );
        let arr: Vec<Value> = sources
            .iter()
            .map(|h| Value::Bytes(h.as_ref().to_vec()))
            .collect();
        payload.insert(
            "source_raw_material_hashes".to_string(),
            Value::Array(arr),
        );
        Message::new(msg_type::DEPOSIT_FORGED_UNDERSTANDING, 7, payload)
    }

    /// Decode a response payload's Bytes field into a `NodeHash`.
    fn response_node_hash(
        payload: &BTreeMap<String, Value>,
        key: &str,
    ) -> myco_kernel_shared::crypto::NodeHash {
        match payload.get(key) {
            Some(Value::Bytes(b)) if b.len() == 32 => {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(b);
                myco_kernel_shared::crypto::NodeHash::from_bytes(arr)
            }
            other => panic!("response field {key:?} is not 32 Bytes: {other:?}"),
        }
    }

    #[test]
    fn forge_with_one_valid_source_links_and_decodes() {
        let mut state = test_state();
        // Seed a raw_material node the understanding will be forged from.
        let source = feed_returning_hash(&mut state, 3);
        let dag_size_before = state.dag.node_count();

        let understanding = b"digested prose forged out of the raw material";
        let req = forge_request("synthesis", understanding, &[source]);
        let resp = handle_deposit_forged_understanding(&mut state, &req)
            .expect("forge handler ok")
            .expect("forge handler returns a response message");

        // ---- response envelope ----
        assert_eq!(resp.message_type, msg_type::DEPOSIT_FORGED_UNDERSTANDING_RESPONSE);
        assert_eq!(resp.request_id, 7, "response echoes the request_id");
        assert_eq!(
            resp.payload.get("refused"),
            Some(&Value::Bool(false)),
            "a well-formed forge is never refused"
        );
        assert_eq!(
            resp.payload.get("total_dag_size"),
            Some(&Value::Uint((dag_size_before + 1) as u64)),
            "the forge inserts exactly one new DAG node"
        );
        let dag_node_hash = response_node_hash(&resp.payload, "dag_node_hash");
        // current_tip must equal the just-inserted node (it is the new tip).
        let tip = response_node_hash(&resp.payload, "current_tip");
        assert_eq!(tip, dag_node_hash, "the forged node becomes the DAG tip");

        // Exactly one forged_understanding:* node now exists.
        assert_eq!(
            count_nodes(&state, FORGED_UNDERSTANDING_NODE_TYPE_PREFIX),
            1
        );

        // ---- read the node back out of the DAG ----
        let node = state.dag.get(&dag_node_hash).expect("forged node in DAG");
        assert_eq!(node.node_type, "forged_understanding:synthesis");
        // Causal link: the source raw_material hash is among the parents.
        assert!(
            node.parent_hashes.contains(&source),
            "forged node must be causally parented by its source raw_material (P6)"
        );

        // ---- decode the canonical content ----
        let content = match cb_decode(node.content_canonical_bytes.as_ref())
            .expect("content decodes")
        {
            Value::Map(m) => m,
            other => panic!("forged content is not a Map: {other:?}"),
        };
        assert_eq!(
            content.get("label"),
            Some(&Value::String("synthesis".to_string()))
        );
        assert_eq!(
            content.get("understanding"),
            Some(&Value::Bytes(understanding.to_vec())),
            "understanding bytes round-trip verbatim"
        );
        assert_eq!(
            content.get("source_raw_material_hashes"),
            Some(&Value::Array(vec![Value::Bytes(source.as_ref().to_vec())])),
            "the cited source hash is recorded in the content"
        );
        // forged_at_cycle == the substrate's cycle counter at forge time (0 in a
        // fresh test state — the in-process state never advances the counter).
        assert_eq!(
            content.get("forged_at_cycle"),
            Some(&Value::Uint(0)),
            "forged_at_cycle stamps the substrate's current cycle"
        );
    }

    #[test]
    fn forge_with_empty_source_list_parents_tip_only() {
        let mut state = test_state();
        // Give the DAG a tip so we can assert parents == [tip] (and only that).
        let tip_before = feed_returning_hash(&mut state, 1);

        let req = forge_request("standalone", b"an understanding citing no source", &[]);
        let resp = handle_deposit_forged_understanding(&mut state, &req)
            .expect("forge handler ok")
            .expect("forge handler returns a response message");
        assert_eq!(
            resp.payload.get("refused"),
            Some(&Value::Bool(false))
        );
        let dag_node_hash = response_node_hash(&resp.payload, "dag_node_hash");

        let node = state.dag.get(&dag_node_hash).expect("forged node in DAG");
        assert_eq!(node.node_type, "forged_understanding:standalone");
        // Empty source list → parents == [prior tip] only.
        assert_eq!(
            node.parent_hashes,
            vec![tip_before],
            "with no cited sources the forged node parents the prior tip only"
        );

        let content = match cb_decode(node.content_canonical_bytes.as_ref())
            .expect("content decodes")
        {
            Value::Map(m) => m,
            other => panic!("forged content is not a Map: {other:?}"),
        };
        // The source array is present but empty.
        assert_eq!(
            content.get("source_raw_material_hashes"),
            Some(&Value::Array(Vec::new())),
            "an empty source list is recorded as an empty array"
        );
    }

    #[test]
    fn forge_with_unknown_source_hash_is_rejected() {
        let mut state = test_state();
        // A 32-byte hash that was never inserted into the DAG.
        let bogus = myco_kernel_shared::crypto::NodeHash::from_bytes([0xABu8; 32]);

        let req = forge_request("bad-source", b"understanding citing a phantom", &[bogus]);
        let result = handle_deposit_forged_understanding(&mut state, &req);
        // Mirrors handle_perturb_axis_from_raw_material's provenance check: an
        // unknown source hash is a structured Protocol error, NOT a silent insert.
        match result {
            Err(SubstrateError::Protocol(msg)) => {
                assert!(
                    msg.contains("not found in DAG"),
                    "rejection message should explain the missing source: {msg}"
                );
            }
            other => panic!("expected Protocol error for unknown source, got {other:?}"),
        }
        // Nothing was inserted.
        assert_eq!(
            count_nodes(&state, FORGED_UNDERSTANDING_NODE_TYPE_PREFIX),
            0,
            "a rejected forge must not insert a forged_understanding node"
        );
    }

    // ---- step-1 discernment fields (value / confidence / supersedes) ----

    /// Like [`forge_request`] but also sets the optional step-1 discernment fields.
    /// `value`/`confidence` are inserted only when `Some`; `supersedes` only when
    /// non-empty — so omitting all three reproduces the exact pre-step-1 wire shape.
    fn forge_request_full(
        label: &str,
        understanding: &[u8],
        sources: &[myco_kernel_shared::crypto::NodeHash],
        value: Option<u64>,
        confidence: Option<u64>,
        supersedes: &[myco_kernel_shared::crypto::NodeHash],
    ) -> Message {
        let mut payload = BTreeMap::new();
        payload.insert("label".to_string(), Value::String(label.to_string()));
        payload.insert(
            "understanding".to_string(),
            Value::Bytes(understanding.to_vec()),
        );
        let src: Vec<Value> = sources
            .iter()
            .map(|h| Value::Bytes(h.as_ref().to_vec()))
            .collect();
        payload.insert("source_raw_material_hashes".to_string(), Value::Array(src));
        if let Some(v) = value {
            payload.insert("value".to_string(), Value::Uint(v));
        }
        if let Some(c) = confidence {
            payload.insert("confidence".to_string(), Value::Uint(c));
        }
        if !supersedes.is_empty() {
            let arr: Vec<Value> = supersedes
                .iter()
                .map(|h| Value::Bytes(h.as_ref().to_vec()))
                .collect();
            payload.insert("supersedes".to_string(), Value::Array(arr));
        }
        Message::new(msg_type::DEPOSIT_FORGED_UNDERSTANDING, 7, payload)
    }

    #[test]
    fn forge_with_discernment_fields_roundtrip() {
        let mut state = test_state();
        let source = feed_returning_hash(&mut state, 2);
        // Forge a first plate so there is a real forged_understanding node to supersede.
        let first = handle_deposit_forged_understanding(
            &mut state,
            &forge_request("first-pass", b"a coarse early understanding", &[source]),
        )
        .expect("first forge ok")
        .expect("first forge response");
        let first_hash = response_node_hash(&first.payload, "dag_node_hash");

        // Forge a sharper plate that supersedes the first, carrying value + confidence.
        let req = forge_request_full(
            "refined",
            b"a sharper understanding correcting the first",
            &[source],
            Some(80),
            Some(60),
            &[first_hash],
        );
        let resp = handle_deposit_forged_understanding(&mut state, &req)
            .expect("forge ok")
            .expect("forge response");
        let node_hash = response_node_hash(&resp.payload, "dag_node_hash");

        let node = state.dag.get(&node_hash).expect("plate in DAG");
        let content = match cb_decode(node.content_canonical_bytes.as_ref()).expect("decodes") {
            Value::Map(m) => m,
            other => panic!("not a Map: {other:?}"),
        };
        assert_eq!(content.get("value"), Some(&Value::Uint(80)));
        assert_eq!(content.get("confidence"), Some(&Value::Uint(60)));
        assert_eq!(
            content.get("supersedes"),
            Some(&Value::Array(vec![Value::Bytes(first_hash.as_ref().to_vec())])),
            "the superseded plate hash is recorded (maturation by supersession, not mutation)"
        );
    }

    #[test]
    fn forge_without_discernment_is_byte_identical() {
        // The backward-compat guarantee: a forge omitting value/confidence/supersedes
        // composes EXACTLY {forged_at_cycle, label, source_raw_material_hashes,
        // understanding} — NO new keys — so pre-step-1 nodes + the seal are unaffected.
        let mut state = test_state();
        let req = forge_request("plain", b"no discernment fields set", &[]);
        let resp = handle_deposit_forged_understanding(&mut state, &req)
            .expect("forge ok")
            .expect("forge response");
        let node_hash = response_node_hash(&resp.payload, "dag_node_hash");
        let node = state.dag.get(&node_hash).expect("plate in DAG");
        let content = match cb_decode(node.content_canonical_bytes.as_ref()).expect("decodes") {
            Value::Map(m) => m,
            other => panic!("not a Map: {other:?}"),
        };
        let keys: Vec<String> = content.keys().cloned().collect();
        assert_eq!(
            keys,
            vec![
                "forged_at_cycle".to_string(),
                "label".to_string(),
                "source_raw_material_hashes".to_string(),
                "understanding".to_string(),
            ],
            "a discernment-free forge must add NO new keys (byte-identical to pre-step-1)"
        );
    }

    #[test]
    fn forge_supersedes_unknown_hash_is_rejected() {
        let mut state = test_state();
        let bogus = myco_kernel_shared::crypto::NodeHash::from_bytes([0x11u8; 32]);
        let req = forge_request_full("re-forge", b"corrects a phantom", &[], None, None, &[bogus]);
        match handle_deposit_forged_understanding(&mut state, &req) {
            Err(SubstrateError::Protocol(msg)) => assert!(
                msg.contains("supersedes") && msg.contains("not found in DAG"),
                "rejection should name the missing supersedes target: {msg}"
            ),
            other => panic!("expected Protocol error for unknown supersedes, got {other:?}"),
        }
        assert_eq!(count_nodes(&state, FORGED_UNDERSTANDING_NODE_TYPE_PREFIX), 0);
    }

    #[test]
    fn forge_supersedes_must_reference_a_plate_not_raw_material() {
        let mut state = test_state();
        // A raw_material node is NOT a valid supersedes target — only plates are.
        let raw = feed_returning_hash(&mut state, 1);
        let req = forge_request_full("mis-target", b"tries to supersede ore", &[], None, None, &[raw]);
        match handle_deposit_forged_understanding(&mut state, &req) {
            Err(SubstrateError::Protocol(msg)) => assert!(
                msg.contains("not forged_understanding"),
                "supersedes must reject a non-plate target: {msg}"
            ),
            other => panic!("expected Protocol error superseding raw_material, got {other:?}"),
        }
    }

    #[test]
    fn forge_value_out_of_range_is_rejected() {
        let mut state = test_state();
        let req = forge_request_full("too-hot", b"value 101", &[], Some(101), None, &[]);
        match handle_deposit_forged_understanding(&mut state, &req) {
            Err(SubstrateError::Protocol(msg)) => assert!(
                msg.contains("value") && msg.contains("out of range"),
                "value > 100 must be rejected: {msg}"
            ),
            other => panic!("expected Protocol error for value out of range, got {other:?}"),
        }
    }
}
