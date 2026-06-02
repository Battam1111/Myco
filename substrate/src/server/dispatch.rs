//! Operator-facing M5 message dispatch.
//!
//! `dispatch` routes a decoded [`Message`] to the appropriate per-message-family
//! handler. Extracted from `server/mod.rs` (was the inline `dispatch` fn); the
//! routing semantics + post-handler bookkeeping (DAG-event emission, persistence)
//! are unchanged.

use myco_kernel_bridge::protocol::{empty_payload, msg_type, Message};
use myco_kernel_shared::canonical_bytes::Value;

use super::{
    emit_substrate_event, forward_to_python, save_dag_state, save_python_state,
    save_snapshot_for_state, ServerState,
};
use crate::SubstrateError;

pub(super) fn dispatch(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // Pre-handshake: only HELLO is allowed.
    if !state.handshake_complete && request.message_type != msg_type::HELLO {
        return Err(SubstrateError::Handshake(format!(
            "received {} before hello",
            request.message_type
        )));
    }

    match request.message_type.as_str() {
        msg_type::HELLO => crate::handshake::handle_hello(state, request),
        msg_type::REGISTER_AXIS => {
            // M22.5: block register_axis during birth-period quarantine.
            // Inherited disease + structural mutation == bad combination.
            if crate::lifecycle::is_in_birth_period_quarantine(state) {
                return crate::lifecycle::quarantine_block(state, "register_axis");
            }
            let response = forward_to_python(state, request, msg_type::REGISTER_AXIS_ACK)?;
            // M21.1 P5 万物互联: emit axis_registered DAG event so the schema
            // addition is recorded in the causal graph (was an orphan prior).
            // The wire payload fields for register_axis are documented in
            // kernel/bridge::protocol::register_axis_payload — we extract them
            // here for the event content.
            if let Some(event) = crate::ingest::build_axis_registered_event(request) {
                let nt = crate::events::axis_registered_node_type(&event.name);
                let content = crate::events::encode_axis_registered(&event);
                let _ = emit_substrate_event(state, nt, content);
                let _ = save_dag_state(state);
            }
            // M7: persist gradient state after a mutation.
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::PERTURB => {
            // M22.5: block perturb during birth-period quarantine.
            if crate::lifecycle::is_in_birth_period_quarantine(state) {
                return crate::lifecycle::quarantine_block(state, "perturb");
            }
            let response = forward_to_python(state, request, msg_type::PERTURB_ACK)?;
            // M21.1 P5 万物互联: emit axis_perturbed DAG event so the
            // perturbation is recorded in the causal graph. Plain perturb
            // (no raw_material binding) was an orphan prior to M21.1.
            if let (Some(axis_name), Some(delta)) = (
                request.payload.get("axis_name").and_then(|v| match v {
                    Value::String(s) => Some(s.clone()),
                    _ => None,
                }),
                request.payload.get("delta_repr").and_then(|v| match v {
                    Value::String(s) => s.parse::<f64>().ok(),
                    _ => None,
                }),
            ) {
                let nt = crate::events::axis_perturbed_node_type(&axis_name);
                let content = crate::events::encode_axis_perturbed(&axis_name, delta);
                let _ = emit_substrate_event(state, nt, content);
                let _ = save_dag_state(state);
            }
            save_python_state(state)?;
            Ok(response)
        }
        msg_type::SNAPSHOT => forward_to_python(state, request, msg_type::SNAPSHOT_RESPONSE),
        msg_type::ADVANCE => {
            // **COV06 T7**: an alive::archived substrate has halted metabolism
            // (terminal via bet-retirement). Refuse cycle advance; the state_dir
            // stays cold-readable but no new metabolic cycles run.
            if crate::cultivation::is_archived(state) {
                return Err(SubstrateError::Protocol(
                    "advance refused: substrate is alive::archived (bet-retired); \
                     metabolism halted — state_dir is cold-readable only"
                        .to_string(),
                ));
            }
            let response = crate::ingest::handle_advance(state, request)?;
            // M7: bump the persisted cycle counter (matches the value echoed in
            // the advance_response payload). save_manifest() also bumps
            // last_save_time for observability.
            let prior_cycle = state.cycle_counter();
            let new_cycle = prior_cycle.saturating_add(1);
            state.set_cycle_counter(new_cycle);
            // M21.1 P5 万物互联: emit cycle_advanced DAG event so cycle counter
            // progression is recorded in the causal graph.
            let event_content = crate::events::encode_cycle_advanced(prior_cycle, new_cycle);
            let _ = emit_substrate_event(
                state,
                crate::events::NODE_TYPE_CYCLE_ADVANCED.to_string(),
                event_content,
            );
            // **v3.1.1 Sprint 8.G (P03 §10.4)**: per-cycle dual-validation step
            // for an in-flight schema migration. MUST run AFTER cycle_advanced
            // is emitted (so the cycle counter reflects this cycle) and reads
            // the candidate-divergence fields from the advance_response. Zero
            // cost when no migration is in flight.
            if let Some(resp_msg) = response.as_ref() {
                let _ = crate::ingest::run_migration_step(state, resp_msg);
            }
            // M25.2 P5 万物互联: append a fresh observatory snapshot to the
            // trend window. Must happen AFTER the cycle_advanced DAG event
            // is appended (so dag_node_count reflects the new state) and
            // BEFORE save_dag_state (so the snapshot is built against the
            // same state that gets persisted). The signal #5 / quorum /
            // emergent-weights logic in `handle_query_substrate_observatory`
            // walks this history.
            crate::observatory::append_observatory_snapshot_to_state(state);
            state.save_manifest()?;
            save_python_state(state)?;
            // M8: persist the DAG (sporocarps inserted during handle_advance).
            save_dag_state(state)?;
            // M21.5 P5 万物互联: opportunistic snapshot. Every K cycles, save
            // a snapshot.cb to accelerate next boot. K=10 for fast feedback in
            // tests; production may tune. If snapshot save fails, log + continue
            // (snapshot is a CACHE — substrate works without it).
            const SNAPSHOT_EVERY_K_CYCLES: u64 = 10;
            if new_cycle % SNAPSHOT_EVERY_K_CYCLES == 0 {
                let _ = save_snapshot_for_state(state);
            }
            Ok(response)
        }
        msg_type::SHUTDOWN => {
            // M7+M8: final state save before exit (best-effort; ignore errors here).
            let _ = save_python_state(state);
            let _ = state.save_manifest();
            let _ = save_dag_state(state);
            Ok(Some(Message::new(
                msg_type::SHUTDOWN_ACK,
                request.request_id,
                empty_payload(),
            )))
        }
        // M8: DAG-related operator requests handled substrate-side.
        msg_type::QUERY_RECENT_NODES => crate::dag_query::handle_query_recent_nodes(state, request),
        msg_type::COMPUTE_INTENT => crate::dag_query::handle_compute_intent(state, request),
        // M10: classified-mutation submission.
        msg_type::SUBMIT_MUTATION => {
            let response = crate::attestation::handle_submit_mutation(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // M11: immune event query (filters DAG by "immune:" prefix).
        msg_type::QUERY_IMMUNE_EVENTS => crate::dag_query::handle_query_immune_events(state, request),
        // M12: ad-hoc immune check (operator can verify integrity any time).
        msg_type::RUN_IMMUNE_CHECK => crate::integrity::handle_run_immune_check(state, request),
        // M13: anchor-surface attestation nonce (operator pre-submit step).
        msg_type::REQUEST_ATTESTATION_NONCE => {
            crate::attestation::handle_request_attestation_nonce(state, request)
        }
        // M15: DAG enumeration closure for owner-side Merkle chain reconstruction.
        msg_type::ENUMERATE_DAG_SINCE => crate::dag_query::handle_enumerate_dag_since(state, request),
        // M16: P2 永恒吞噬 — universal raw_material ingestion + causal perturbation.
        msg_type::INGEST_RAW_MATERIAL => {
            let response = crate::ingest::handle_ingest_raw_material(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::PERTURB_AXIS_FROM_RAW_MATERIAL => {
            let response = crate::ingest::handle_perturb_axis_from_raw_material(state, request)?;
            save_python_state(state)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // M20 P8 永恒繁衍 — sprout a child substrate from parent's spore-schema.
        msg_type::SPROUT_CHILD => {
            let response = crate::reproduction::handle_sprout_child(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // **v3.1.1 Sprint 5.I (T1.3)** — export full state backup to a
        // directory. Closes COV01 fiduciary-duty gap. Operator copies
        // resulting backup_dir to external encrypted media; the substrate
        // emits a `backup_exported:{cycle}` DAG event for the causal record.
        msg_type::EXPORT_BACKUP_TO_DIR => {
            crate::backup::handle_export_backup_to_dir(state, request)
        }
        // M22 P5 万物互联 — inter-substrate federation. Operator-driven; all
        // federation handlers mutate state.federation + emit DAG events through
        // emit_substrate_event. Listener/peer sockets are nonblocking; the
        // substrate's main loop does no I/O multiplexing of its own.
        msg_type::FEDERATION_OPEN_LISTENER => {
            let response = crate::federation::handle_federation_open_listener(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_CLOSE_LISTENER => {
            let response = crate::federation::handle_federation_close_listener(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_STATUS => {
            crate::federation::handle_federation_status(state, request)
        }
        msg_type::FEDERATION_CONNECT_PEER => {
            let response = crate::federation::handle_federation_connect_peer(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_POLL => {
            let response = crate::federation::handle_federation_poll(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_PULL_EVENTS_FROM_PEER => {
            let response =
                crate::federation::handle_federation_pull_events_from_peer(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_LINK_TO_PARENT_FROM_HINT => {
            let response =
                crate::federation::handle_federation_link_to_parent_from_hint(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // **L2/FEDERATION §6.5** — Stage-1 population-consensus floor. The three
        // handlers mint the substrate's own vote / ingest a verified peer vote
        // (auto-emitting the quorum cert at ≥2/3) / query a claim's status. Each
        // emits DAG events (votes / cert / pending / byzantine_threshold_check)
        // and persists; consensus state is fully DAG-derived.
        msg_type::FEDERATION_PROPOSE_POPULATION_CLAIM => {
            let response =
                crate::consensus::handle_federation_propose_population_claim(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_SUBMIT_PEER_VOTE => {
            let response = crate::consensus::handle_federation_submit_peer_vote(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::FEDERATION_QUERY_CONSENSUS => {
            crate::consensus::handle_federation_query_consensus(state, request)
        }
        msg_type::LIFT_BIRTH_PERIOD_QUARANTINE => {
            let response = crate::lifecycle::handle_lift_birth_period_quarantine(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::ACCEPT_SELF_EUTHANASIA_PROPOSAL => {
            let response = crate::lifecycle::handle_accept_self_euthanasia_proposal(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // **COV06 不弃不孤** — cultivator-mortality + succession FSM. The
        // operator threads the anchor-signed heartbeat / successor-chain /
        // succession-acceptance in (the substrate has no anchor socket; AS §5.2).
        // Each handler verifies its signature + emits the FSM transition events.
        msg_type::RECORD_CULTIVATOR_HEARTBEAT => {
            let response = crate::cultivation::handle_record_cultivator_heartbeat(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::UPDATE_SUCCESSOR_CHAIN => {
            let response = crate::cultivation::handle_update_successor_chain(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::ACCEPT_SUCCESSION => {
            let response = crate::cultivation::handle_accept_succession(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // **COV06 T7 / LB §4** — cultivator co-attests a bet_retired_proposal →
        // bet_retired:{reason} archive seal → alive::archived. The main loop
        // exits cleanly after the response (metabolism halts; state_dir cold-
        // readable). Serves both COV06 orphaned-terminal + LB living-bet retire.
        msg_type::ACCEPT_BET_RETIRED_PROPOSAL => {
            let response = crate::cultivation::handle_accept_bet_retired_proposal(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        msg_type::QUERY_SUBSTRATE_OBSERVATORY => {
            crate::observatory::handle_query_substrate_observatory(state, request)
        }
        // **CHAR07 §8.1/§8.2 intake** — cultivator attests a capability-asymmetry
        // or flourishing assessment the substrate cannot observe autonomously.
        // Emits a `char07_assessment:{dimension}` DAG event (source
        // cultivator_attested); the observatory query surfaces the latest per
        // dimension. Substrate records but never synthesizes the value (CHAR05).
        msg_type::SUBMIT_CHAR07_ASSESSMENT => {
            let response = crate::observatory::handle_submit_char07_assessment(state, request)?;
            save_dag_state(state)?;
            Ok(response)
        }
        // **v3.1.1 Sprint 8.G (P03 §10.4)** — read whether a two-phase schema
        // migration is in flight. Pure read of `state.migration_candidate`; no
        // Python round-trip, no DAG mutation. Survives cold-resume because the
        // candidate is hydrated from the DAG / snapshot at boot.
        msg_type::QUERY_MIGRATION_PENDING => {
            let mut payload = std::collections::BTreeMap::new();
            payload.insert(
                "current_cycle".to_string(),
                Value::Uint(state.cycle_counter()),
            );
            match &state.migration_candidate {
                Some(c) => {
                    payload.insert("pending".to_string(), Value::Bool(true));
                    payload.insert("op".to_string(), Value::String(c.op_name.clone()));
                    payload.insert(
                        "started_at_cycle".to_string(),
                        Value::Uint(c.started_at_cycle),
                    );
                    payload.insert(
                        "window".to_string(),
                        Value::Uint(c.dual_validation_window_cycles),
                    );
                }
                None => {
                    payload.insert("pending".to_string(), Value::Bool(false));
                    payload.insert("op".to_string(), Value::String(String::new()));
                    payload.insert("started_at_cycle".to_string(), Value::Uint(0));
                    payload.insert("window".to_string(), Value::Uint(0));
                }
            }
            Ok(Some(Message::new(
                msg_type::QUERY_MIGRATION_PENDING_RESPONSE,
                request.request_id,
                payload,
            )))
        }
        other => Err(SubstrateError::Protocol(format!(
            "substrate cannot handle message type {other:?}"
        ))),
    }
}
