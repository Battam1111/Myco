//! Substrate lifecycle primitives, extracted from `server.rs` (Phase B Step 3).
//!
//! Owns the two P7-必朽 (mortality) lifecycle entry points, keyless
//! self-euthanasia execution + birth-period quarantine lifting, plus the
//! M22.5 quarantine-state helpers used by `dispatch()` to gate
//! `register_axis`/`perturb` while the substrate is in inherited quarantine.
//!
//! **v0.9 keyless**: the owner Ed25519 gates (on both self-euthanasia execution
//! and quarantine lifting) were removed with the owner-key + anchor surface.
//! Whole-death / lift are now authorized by a DELIBERATE call referencing a real
//! DAG proposal node (the non-arbitrary structural gate); the authorization root
//! is the live human-in-the-loop, not an owner signature.
//!
//! Doctrine traceability:
//! - L0 P7 必朽, keyless self-euthanasia execution path (proposal-referenced).
//! - L0 P8 集体免疫, birth-period quarantine on child sprouting.
//! - L1/HARD_RULES §1, C34 birth_period_violation_during_quarantine.

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::Value;

use crate::server::{
    emit_immune_sporocarp, emit_substrate_event, hex_first_8_bytes, ServerState,
};
use crate::SubstrateError;

/// M23.2 P7 必朽: handle `accept_self_euthanasia_proposal`.
///
/// Keyless deliberate-action gate (v3.1.5, owner-key/anchor layer removed):
/// 1. The `proposal_hash` MUST point to a real `self_euthanasia_proposal:*`
///    event in the substrate's DAG, the non-arbitrary, deliberate gate that
///    replaces the (removed) owner Ed25519 signature. Whole-death cannot happen
///    by accident or on an arbitrary value; the authorization root is the live
///    human-in-the-loop, with this proposal-reference as the structural gate.
/// 2. Emit `self_euthanasia_executed:{axis_name}` DAG event (keyless).
/// 3. Return response. The main loop, observing the request type, will then
///    `graceful_shutdown_python` and exit cleanly.
///
/// Payload:
/// ```text
/// Map({ "proposal_hash": Bytes(32) })
/// ```
///
/// Response payload:
/// ```text
/// Map({
///   "axis_name": String,
///   "executed_event_hash": Bytes(32),
/// })
/// ```
pub(crate) fn handle_accept_self_euthanasia_proposal(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, map_get_string, Value as CbV};
    use std::time::{SystemTime, UNIX_EPOCH};

    // Keyless (v3.1.5): whole-death is authorized by a DELIBERATE call that
    // references a real `self_euthanasia_proposal:*` node (verified below),
    // NOT an owner signature. The owner-key/anchor layer was removed; the
    // authorization root is re-grounded in the live human-in-the-loop, with the
    // proposal-reference as the non-arbitrary structural gate.
    let proposal_hash_bytes = match request.payload.get("proposal_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "accept_self_euthanasia_proposal: proposal_hash must be 32 Bytes".to_string(),
            ));
        }
    };
    let mut proposal_hash = [0u8; 32];
    proposal_hash.copy_from_slice(&proposal_hash_bytes);

    // Look up the proposal in DAG; extract axis_name.
    let proposal_node_hash = myco_kernel_shared::crypto::NodeHash::from_bytes(proposal_hash);
    let proposal_node = state.dag.get(&proposal_node_hash).ok_or_else(|| {
        SubstrateError::Protocol(format!(
            "accept_self_euthanasia_proposal: proposal_hash {} not found in DAG",
            hex_first_8_bytes(&proposal_hash),
        ))
    })?;
    if !proposal_node.node_type.starts_with("self_euthanasia_proposal:") {
        return Err(SubstrateError::Protocol(format!(
            "accept_self_euthanasia_proposal: proposal_hash points to {} (not a self_euthanasia_proposal)",
            proposal_node.node_type
        )));
    }
    let axis_name = match cb_decode(proposal_node.content_canonical_bytes.as_ref())
        .map_err(|e| SubstrateError::Protocol(format!("decode proposal content: {e}")))?
    {
        CbV::Map(m) => map_get_string(&m, "axis_name")
            .map_err(|e| SubstrateError::Protocol(e.to_string()))?
            .to_string(),
        _ => {
            return Err(SubstrateError::Protocol(
                "proposal content not a Map".to_string(),
            ));
        }
    };

    // Emit the self_euthanasia_executed event.
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let nt = crate::events::self_euthanasia_executed_node_type(&axis_name);
    let content = crate::events::encode_self_euthanasia_executed(
        &axis_name,
        &proposal_hash,
        state.cycle_counter(),
        now,
    );
    let event_hash = emit_substrate_event(state, nt, content)?;

    let mut payload = BTreeMap::new();
    payload.insert("axis_name".to_string(), Value::String(axis_name));
    payload.insert(
        "executed_event_hash".to_string(),
        Value::Bytes(event_hash.0.to_vec()),
    );
    Ok(Some(Message::new(
        msg_type::ACCEPT_SELF_EUTHANASIA_PROPOSAL_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M22.5: information about the substrate's current quarantine state, derived
/// from DAG events. `None` if no quarantine has ever been entered.
#[derive(Debug, Clone)]
pub(crate) struct QuarantineState {
    /// Cycle when the most recent quarantine_entered event landed. Retained
    /// for diagnostic surfacing (M22.5 minimal flow only inspects `expires_at_cycle`).
    #[allow(dead_code)]
    pub(crate) entered_at_cycle: u64,
    /// Cycle by which the quarantine should auto-lift.
    pub(crate) expires_at_cycle: u64,
    /// Whether a subsequent quarantine_lifted event has been emitted.
    pub(crate) lifted: bool,
}

/// M22.5: scan DAG for the most recent birth_period_quarantine_entered event +
/// any subsequent lifted event. Returns the current quarantine status.
pub(crate) fn current_quarantine_state(state: &ServerState) -> Option<QuarantineState> {
    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbValue};
    let mut entered_at: Option<(u64, u64)> = None; // (entered_at_cycle, expires_at_cycle)
    let mut lifted_after_entered = false;
    for n in state.dag.iter_in_insertion_order() {
        if n.node_type == crate::events::NODE_TYPE_BIRTH_PERIOD_QUARANTINE_ENTERED {
            // Reset (a new quarantine cycle takes over from any previous one).
            lifted_after_entered = false;
            // Read quarantine_duration_cycles from content.
            let duration = match cb_decode(n.content_canonical_bytes.as_ref()) {
                Ok(CbValue::Map(m)) => match m.get("quarantine_duration_cycles") {
                    Some(CbValue::Uint(d)) => *d,
                    _ => 10, // default fallback
                },
                _ => 10,
            };
            let entered_cycle = n.created_at_cycle;
            entered_at = Some((entered_cycle, entered_cycle.saturating_add(duration)));
        } else if n.node_type == crate::events::NODE_TYPE_BIRTH_PERIOD_QUARANTINE_LIFTED
            && entered_at.is_some()
        {
            lifted_after_entered = true;
        }
    }
    entered_at.map(|(entered, expires)| QuarantineState {
        entered_at_cycle: entered,
        expires_at_cycle: expires,
        lifted: lifted_after_entered,
    })
}

/// M22.5: check whether the substrate is currently in active birth-period
/// quarantine. Active = quarantine_entered event exists AND no subsequent
/// lifted event AND current cycle has NOT passed the expiry.
pub(crate) fn is_in_birth_period_quarantine(state: &ServerState) -> bool {
    match current_quarantine_state(state) {
        Some(q) if !q.lifted => state.cycle_counter() < q.expires_at_cycle,
        _ => false,
    }
}

/// M22.5: emit a C21 immune sporocarp + return a Protocol error indicating
/// the operation was blocked due to active birth-period quarantine.
pub(crate) fn quarantine_block(
    state: &mut ServerState,
    op_name: &str,
) -> Result<Option<Message>, SubstrateError> {
    let evidence = format!(
        "operation {op_name} blocked: substrate is in birth-period quarantine \
         (inherited from parent's immune signals). Operator may call \
         lift_birth_period_quarantine after verifying signals."
    );
    let _ = emit_immune_sporocarp(
        state,
        "C34_birth_period_violation_during_quarantine",
        "birth_period_violation_detected",
        &evidence,
    );
    Err(SubstrateError::Protocol(evidence))
}

/// M22.5: handle `lift_birth_period_quarantine` (KEYLESS v0.9). Emits a
/// `birth_period_quarantine_lifted` event so the substrate exits quarantine.
///
/// The owner Ed25519 signature gate was removed with the anchor surface; the
/// quarantine-lift is now a plain operator-driven action (the birth-period
/// quarantine itself remains structurally enforced via `dispatch`'s
/// register_axis/perturb gating until lifted or expired).
///
/// Idempotent, calling when not in quarantine returns `was_in_quarantine=false`.
pub(crate) fn handle_lift_birth_period_quarantine(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};

    let q = current_quarantine_state(state);
    let mut payload = BTreeMap::new();
    let was_in_q = q.as_ref().map(|s| !s.lifted).unwrap_or(false);
    payload.insert("was_in_quarantine".to_string(), Value::Bool(was_in_q));
    if was_in_q {
        let lifted_at_unix_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .ok()
            .and_then(|d| i64::try_from(d.as_nanos()).ok())
            .unwrap_or(0);
        let content = crate::events::encode_birth_period_quarantine_lifted(
            "operator_signed_lift",
            state.cycle_counter(),
            lifted_at_unix_ns,
        );
        let event_hash = emit_substrate_event(
            state,
            crate::events::NODE_TYPE_BIRTH_PERIOD_QUARANTINE_LIFTED.to_string(),
            content,
        )?;
        payload.insert(
            "quarantine_lifted_event_hash".to_string(),
            Value::Bytes(event_hash.0.to_vec()),
        );
    }
    Ok(Some(Message::new(
        msg_type::LIFT_BIRTH_PERIOD_QUARANTINE_RESPONSE,
        request.request_id,
        payload,
    )))
}
