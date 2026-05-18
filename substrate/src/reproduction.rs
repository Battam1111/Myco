//! Substrate reproduction handler — extracted from `server.rs` (Phase B Step 4).
//!
//! Owns the single P8 永恒繁衍 (perpetual reproduction) entry point:
//! `handle_sprout_child` synthesizes a fresh child substrate's DAG from the
//! parent's spore-schema (gradient axes + operator pinning + federation
//! hint + birth-period quarantine if parent has unresolved immune signals)
//! and emits a `spore_emission:{child_id_prefix}` DAG event in the parent.
//!
//! Doctrine traceability:
//! - L0 P8 永恒繁衍 — first-class reproduction operation; child inherits
//!   spore-schema, NOT parent's causal DAG.
//! - L0 P8 集体免疫 — inherited disease via parent's immune-summary
//!   triggering birth-period quarantine entry event in child.
//! - L1/HARD_RULES C34 birth_period_violation_during_quarantine.

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};

use crate::persistence::{save_dag, Manifest};
use crate::server::ServerState;
use crate::SubstrateError;

/// M20 P8 永恒繁衍 — Sprout a child substrate from the parent's spore-schema.
///
/// Per L0/cards/P01-P14 (principles).2 P8: "The substrate can spawn child substrates. Reproduction is
/// a first-class operation. The new substrate inherits the parent's
/// spore-schema (minimum structural form for the child to begin its own
/// symbiosis)."
///
/// M20-MV spore-schema = (gradient axes + schemas + current values) +
/// (operator identity pubkey for continuity) + (fresh substrate_id +
/// fresh genesis_time + cycle_counter=0 + last_absorbed_cycle=None).
///
/// The parent's causal DAG is NOT transferred — the child starts its own
/// causal history (L1 decision per L0 P8). The parent emits a
/// `spore_emission:{child_id_hex_prefix}` DAG node recording the reproduction.
///
/// Payload schema:
/// ```text
/// Map({
///   "child_state_dir": String,  // target directory (must not exist or must be empty)
///   "spore_metadata": Map       // optional; arbitrary K-V hints recorded in the spore_emission node
/// })
/// ```
///
/// Returns:
/// ```text
/// Map({
///   "child_substrate_id": Bytes(32),
///   "child_state_dir": String,
///   "spore_emission_hash": Bytes(32),   // in parent's DAG
/// })
/// ```
pub(crate) fn handle_sprout_child(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let child_state_dir = match request.payload.get("child_state_dir") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "sprout_child: child_state_dir must be a non-empty String".to_string(),
            ));
        }
    };
    let spore_metadata = request.payload.get("spore_metadata").cloned();

    let child_path = std::path::PathBuf::from(&child_state_dir);

    // Guard: child_state_dir must not contain an existing dag.cb (don't
    // overwrite an existing substrate's identity). Post-M21.4, dag.cb is
    // the sole persistent artifact; its presence indicates a live child.
    if child_path.join("dag.cb").exists() {
        return Err(SubstrateError::Protocol(format!(
            "sprout_child: refusing to overwrite existing dag.cb at {child_state_dir}"
        )));
    }
    // Also reject if legacy manifest.cb is present (pre-M21.4 child).
    if child_path.join("manifest.cb").exists() {
        return Err(SubstrateError::Protocol(format!(
            "sprout_child: refusing to overwrite existing manifest.cb at {child_state_dir}"
        )));
    }

    // Create the child state_dir.
    std::fs::create_dir_all(&child_path).map_err(SubstrateError::Io)?;

    // M21.4 P5 万物互联: build the child's DAG directly — no legacy state
    // files. The child's first DAG node is its genesis_event; operator_pinned
    // event records parent's identity for operator continuity; axis_registered
    // + axis_perturbed events seed the child's gradient.
    let child_manifest = Manifest::genesis();

    // Query parent's axis schemas to seed the child's gradient as events.
    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;
    let parent_schemas = client
        .query_gradient_schemas()
        .map_err(SubstrateError::Bridge)?;
    let child_axis_count = parent_schemas.len() as u64;

    // Build child's DAG: genesis_event → operator_pinned (if parent had one)
    // → per-axis (axis_registered + optional axis_perturbed for non-initial value).
    let mut child_dag = myco_kernel_schema::dag::Dag::new();

    // 1. genesis_event
    let child_genesis_nt = crate::events::genesis_event_node_type(&child_manifest.substrate_id);
    let child_genesis_content = crate::events::encode_genesis_event(
        &child_manifest.substrate_id,
        child_manifest.genesis_time_unix_ns,
    );
    let child_cycle = child_manifest.cycle_counter;
    child_dag
        .insert_node(vec![], child_genesis_nt, child_cycle, child_genesis_content)
        .map_err(|e| SubstrateError::Protocol(format!("child genesis_event insert: {e}")))?;

    // 2. operator_pinned (inherited from parent for operator continuity)
    if let Some(parent_pinned) = &state.pinned_operator_identity {
        let nt = crate::events::operator_pinned_node_type(&parent_pinned.pubkey);
        let content = crate::events::encode_operator_pinned(
            &parent_pinned.pubkey,
            parent_pinned.first_pinned_unix_ns,
        );
        let parents = vec![child_dag.tip().unwrap()];
        child_dag
            .insert_node(parents, nt, child_cycle, content)
            .map_err(|e| SubstrateError::Protocol(format!("child operator_pinned insert: {e}")))?;
    }

    // 2b. M22.4 P5 万物互联: if the parent has an open federation listener,
    // record its address in the child's DAG so the child can dial back. The
    // child substrate, after boot, can call `federation_link_to_parent_from_hint`
    // to consume this hint, connect to the parent, and emit
    // `federation_parent_linked`.
    if let Some(parent_listener_addr) = state.federation.listener_addr() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let hinted_at_unix_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let nt = crate::events::NODE_TYPE_PARENT_FEDERATION_HINT.to_string();
        let content = crate::events::encode_parent_federation_hint(
            &state.manifest.substrate_id,
            &parent_listener_addr.to_string(),
            hinted_at_unix_ns,
        );
        let parents = vec![child_dag.tip().unwrap()];
        child_dag
            .insert_node(parents, nt, child_cycle, content)
            .map_err(|e| SubstrateError::Protocol(format!("parent_federation_hint insert: {e}")))?;
    }

    // 2c. M22.5 P8 永恒繁衍: compute parent's immune-summary (list of
    // immune sporocarp hashes) and, if non-empty, write a
    // birth_period_quarantine_entered event into child's DAG. The child
    // enters quarantine on boot. This implements L0/cards/P01-P14 (principles).2 P8 + pass-1
    // mycoparasite-13: "child enters birth-period quarantine if parent had
    // unresolved immune signals".
    let immune_summary: Vec<[u8; 32]> = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type.starts_with("immune:"))
        .map(|n| n.hash.0)
        .collect();
    let quarantine_duration_cycles: u64 = 10; // M22.5 default; future: configurable
    if !immune_summary.is_empty() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let entered_at_unix_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let nt = crate::events::NODE_TYPE_BIRTH_PERIOD_QUARANTINE_ENTERED.to_string();
        let content = crate::events::encode_birth_period_quarantine_entered(
            &state.manifest.substrate_id,
            &immune_summary,
            quarantine_duration_cycles,
            entered_at_unix_ns,
        );
        let parents = vec![child_dag.tip().unwrap()];
        child_dag.insert_node(parents, nt, child_cycle, content).map_err(|e| {
            SubstrateError::Protocol(format!("birth_period_quarantine_entered insert: {e}"))
        })?;
    }

    // 3. Per-axis events: axis_registered, then axis_perturbed for any delta.
    for schema in &parent_schemas {
        let reg_nt = crate::events::axis_registered_node_type(&schema.name);
        let reg_event = crate::events::AxisRegisteredEvent {
            name: schema.name.clone(),
            axis_class: schema.axis_class.clone(),
            fruiting_threshold: schema.fruiting_threshold,
            initial_value: schema.initial_value,
            decay_rate_per_cycle: schema.decay_rate_per_cycle,
            is_mortality_signal: schema.is_mortality_signal,
            update_rule_kind: schema.update_rule_kind.clone(),
        };
        let reg_content = crate::events::encode_axis_registered(&reg_event);
        let parents = vec![child_dag.tip().unwrap()];
        child_dag
            .insert_node(parents, reg_nt, child_cycle, reg_content)
            .map_err(|e| SubstrateError::Protocol(format!("child axis_registered insert: {e}")))?;
        let delta = schema.current_value - schema.initial_value;
        if delta != 0.0 {
            let pert_nt = crate::events::axis_perturbed_node_type(&schema.name);
            let pert_content = crate::events::encode_axis_perturbed(&schema.name, delta);
            let parents = vec![child_dag.tip().unwrap()];
            child_dag
                .insert_node(parents, pert_nt, child_cycle, pert_content)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("child axis_perturbed insert: {e}"))
                })?;
        }
    }

    // Persist child's DAG (the SOLE child state file post-M21.4).
    save_dag(&child_dag, &child_path)?;

    // Emit spore_emission:{child_id_prefix} DAG node in PARENT's DAG.
    let child_id_hex_prefix: String = child_manifest
        .substrate_id
        .iter()
        .take(8)
        .map(|b| format!("{b:02x}"))
        .collect();
    let mut spore_content = BTreeMap::new();
    spore_content.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(child_manifest.substrate_id.to_vec()),
    );
    spore_content.insert(
        "child_state_dir".to_string(),
        Value::String(child_state_dir.clone()),
    );
    spore_content.insert(
        "child_axis_count".to_string(),
        Value::Uint(child_axis_count),
    );
    spore_content.insert(
        "parent_substrate_id".to_string(),
        Value::Bytes(state.manifest.substrate_id.to_vec()),
    );
    spore_content.insert(
        "parent_cycle_at_emission".to_string(),
        Value::Uint(state.manifest.cycle_counter),
    );
    if let Some(m) = spore_metadata {
        spore_content.insert("spore_metadata".to_string(), m);
    }
    let spore_canonical = cb_encode(&Value::Map(spore_content))
        .map_err(|e| SubstrateError::Protocol(format!("spore_emission encode: {e}")))?;
    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let spore_node_type = format!("spore_emission:{child_id_hex_prefix}");
    let cycle = state.manifest.cycle_counter;
    let spore_hash = state
        .dag
        .insert_node(parents, spore_node_type, cycle, spore_canonical)
        .map_err(|e| SubstrateError::Protocol(format!("spore_emission DAG insert: {e}")))?;

    let mut payload = BTreeMap::new();
    payload.insert(
        "child_substrate_id".to_string(),
        Value::Bytes(child_manifest.substrate_id.to_vec()),
    );
    payload.insert(
        "child_state_dir".to_string(),
        Value::String(child_state_dir),
    );
    payload.insert(
        "child_axis_count".to_string(),
        Value::Uint(child_axis_count),
    );
    payload.insert(
        "spore_emission_hash".to_string(),
        Value::Bytes(spore_hash.as_ref().to_vec()),
    );

    Ok(Some(Message::new(
        msg_type::SPROUT_CHILD_RESPONSE,
        request.request_id,
        payload,
    )))
}
