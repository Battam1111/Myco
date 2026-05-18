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
    emit_immune_sporocarp, float_repr, hex_encode, save_dag_state, ServerState,
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
        match self.client.advance(self.cycle_number) {
            Ok(report) => {
                self.latest_report = Some(report);
                Ok(())
            }
            Err(e) => Err(format!("python gradient advance failed: {e}")),
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
    let cycle = state.manifest.cycle_counter;
    let node_hash = state
        .dag
        .insert_node(parents, node_type, cycle, canonical)
        .map_err(|e| SubstrateError::Protocol(format!("raw_material DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
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
        client
            .perturb(&axis_name, delta)
            .map_err(SubstrateError::Bridge)?;
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
    let cycle = state.manifest.cycle_counter;
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

    // Extract the requested cycle number (informational; engine has its own counter).
    let _requested_cycle = request.payload.get("current_cycle").and_then(|v| match v {
        Value::Uint(u) => Some(*u),
        _ => None,
    });

    // M18 P4 永恒迭代: precompute cycle trait inputs BEFORE the cycle inner
    // scope (which mutably borrows state.python_client via gradient). All
    // DAG-reading work happens here; DAG mutations happen AFTER the inner scope.
    let starting_cycle = state.manifest.cycle_counter;
    let last_absorbed_cycle = state.manifest.last_absorbed_cycle;

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
    let pinned_count = if state.pinned_operator_identity.is_some() {
        1
    } else {
        0
    };

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
        // pathology threshold per L0 §2.2 P7. Auto-emit a
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
            state.manifest.last_absorbed_cycle = Some(max_absorbed_created_at);
            Some(h)
        } else {
            None
        };

    let mut payload = BTreeMap::new();
    // Echo the substrate's authoritative cycle counter (post-increment).
    payload.insert("cycle_number".to_string(), Value::Uint(post_cycle));
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
                state.manifest.cycle_counter,
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

    Ok(Some(Message::new(
        msg_type::ADVANCE_RESPONSE,
        request.request_id,
        payload,
    )))
}
