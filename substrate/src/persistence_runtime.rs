//! Substrate persistence runtime — extracted from `server.rs` (Phase B Step 5).
//!
//! Owns the runtime-side persistence operations (file writes, snapshot
//! signing, DAG replay) that bridge `ServerState` with the lower-level
//! [`crate::persistence`] module's on-disk format.
//!
//! Specifically, this module hosts:
//! - `save_python_state` / `save_dag_state` / `save_nonce_state` — the three
//!   in-process persistence checkpoints invoked after each state-mutating
//!   message handler.
//! - `save_snapshot_for_state` — opportunistic snapshot.cb writer used every
//!   K cycles + on shutdown (M21.5 + M25.0).
//! - `replay_events_after_tip` — boot-time DAG replay helper that brings a
//!   snapshot-loaded DerivedState forward to the DAG tip (M21.5).
//! - `backfill_dag_from_python_state` — legacy → M21 migration: emits
//!   DAG events for axes that exist in Python but not yet in the DAG.
//! - `replay_python_events_from_dag` — boot-time DAG-to-Python replay
//!   that rebuilds the Python worker's gradient from event log.
//!
//! Doctrine traceability:
//! - L0 P5 万物互联: every state mutation must be reflected in the DAG event
//!   log; `save_dag_state` is the persistence boundary for that.
//! - L0 P6 永恒因果: snapshot.cb is a content-hash-derived cache; the DAG
//!   remains the authoritative source-of-truth.
//! - L1/SCHEMA C38 snapshot_integrity_violation — `save_snapshot_for_state`
//!   produces the Ed25519-signed envelope that `load_snapshot` validates.
//! - M21.3 / M21.4: state files (gradient.cb / owner_keys.cb / nonce_log.cb /
//!   manifest.cb) are now derived-from-DAG; `save_python_state` and
//!   `save_nonce_state` are intentionally no-ops to keep call sites stable.

use myco_kernel_bridge::client::BridgeClient;
use myco_kernel_schema::dag::Dag;
use myco_kernel_shared::canonical_bytes::Value;

use crate::persistence::save_dag;
use crate::server::{emit_substrate_event, ServerState};
use crate::SubstrateError;

/// M21.4 P5 万物互联: Python-side state persistence is now NO-OP.
/// Python's gradient + owner_keys are derived from DAG events at boot
/// (M21.3 replay). The legacy `gradient.cb` and `owner_keys.cb` files are
/// no longer maintained; dag.cb is the substrate's sole persistent artifact.
///
/// Kept as a function for call-site stability; future versions may remove
/// the call sites entirely.
#[allow(clippy::unnecessary_wraps)]
pub(crate) fn save_python_state(_state: &mut ServerState) -> Result<(), SubstrateError> {
    // M21.4: no-op. State is event-sourced via DAG.
    Ok(())
}

/// M8/M21.4: Persist the substrate's DAG to `<state_dir>/dag.cb`.
/// This remains the sole persistent operation in M21.4 — dag.cb is the
/// authoritative substrate state.
///
/// **M26.2 P11.b**: returns bytes-written for signal #9 (storage/cycle).
/// Callers in the cycle-advance path forward this into
/// `state.cost_accumulator.record_storage_write`. Pre-M26.2 callers that
/// discard the count keep working — the value is just an extra useful return.
pub(crate) fn save_dag_state(state: &ServerState) -> Result<usize, SubstrateError> {
    // **v3.1.1 Sprint 6.G (T2.12)** — track persistence health. Success
    // resets consecutive-failure counter + clears C64 emission-pending
    // flag. Failure increments counters; autonomous tick polls these to
    // emit C64_persistence_unavailable.
    match save_dag(&state.dag, &state.state_dir) {
        Ok(bytes) => {
            crate::persistence_health::record_save_success_and_clear_emission();
            Ok(bytes)
        }
        Err(e) => {
            crate::persistence_health::record_save_failure();
            // Best-effort stderr surfacing for ops monitoring even if
            // the operator-facing error path is swallowed by `let _ = ...`.
            use std::io::Write;
            let _ = writeln!(
                std::io::stderr(),
                "[substrate-persistence] save_dag_state failure: {e}"
            );
            Err(e)
        }
    }
}

/// M21.4 P5 万物互联: nonce log persistence is now NO-OP. The nonce_log is
/// derived from `nonce_issued` / `nonce_consumed` DAG events at boot.
#[allow(clippy::unnecessary_wraps)]
pub(crate) fn save_nonce_state(_state: &ServerState) -> Result<(), SubstrateError> {
    // M21.4: no-op. Nonce state is event-sourced via DAG.
    Ok(())
}

/// M21.5 P5 万物互联: apply DAG events that occur AFTER a snapshot's recorded
/// tip to a DerivedState already initialized from that snapshot.
///
/// Used at boot when snapshot.cb is found + valid: instead of replaying every
/// event from genesis, replay only the tail of the DAG.
pub(crate) fn replay_events_after_tip(
    state: &mut crate::derived_state::DerivedState,
    dag: &myco_kernel_schema::dag::Dag,
    after_tip: Option<&[u8; 32]>,
) -> Result<(), crate::derived_state::DerivedStateError> {
    let mut skipping = after_tip.is_some();
    for node in dag.iter_in_insertion_order() {
        if skipping {
            if let Some(tip) = after_tip {
                if node.hash.as_ref() == tip.as_slice() {
                    skipping = false;
                }
            }
            continue;
        }
        state.apply_event(node)?;
    }
    Ok(())
}

/// M21.5 P5 万物互联 + M25.0: save a snapshot of the current Rust-side derived
/// state, wrapped in an Ed25519-signed envelope. Used opportunistically every
/// K cycles to accelerate boot — boot can use the snapshot instead of full
/// DAG replay (replays only events after the snapshot's recorded tip).
///
/// M25.0: the signing key is reconstructed from the substrate's own seed
/// (`state.substrate_signing_seed`). The wrapper schema embeds the pubkey
/// + signature; boot verifies both before trusting the snapshot.
///
/// **M26.2 P11.b**: returns bytes-written for signal #9 (storage/cycle).
pub(crate) fn save_snapshot_for_state(state: &ServerState) -> Result<usize, SubstrateError> {
    use crate::derived_state::{DerivedNonce, DerivedState};
    use crate::persistence::save_snapshot;
    use myco_kernel_shared::crypto::Ed25519PrivateKey;

    // Build a DerivedState from the current in-memory ServerState fields.
    let derived = DerivedState {
        substrate_id: if state.substrate_id() == [0u8; 32] {
            None
        } else {
            Some(state.substrate_id())
        },
        genesis_time_unix_ns: if state.substrate_id() == [0u8; 32] {
            None
        } else {
            Some(state.genesis_time_unix_ns())
        },
        // 8f / §16.A: carry the live lineage depth into the persisted snapshot.
        generation_depth: state.generation_depth(),
        cycle_counter: state.cycle_counter(),
        last_absorbed_cycle: state.last_absorbed_cycle(),
        pinned_operator_identity: state.pinned_operator_identity.clone(),
        nonce_log: state
            .nonce_log
            .iter()
            .map(|(k, v)| {
                (
                    *k,
                    DerivedNonce {
                        nonce: v.nonce,
                        bound_content_hash: v.bound_content_hash,
                        bound_dag_tip: v.bound_dag_tip,
                        substrate_issued_at_unix_ns: v.substrate_issued_at_unix_ns,
                        expiry_unix_ns: v.expiry_unix_ns,
                        anchor_clock_issued_at_unix_ns: v.anchor_clock_issued_at_unix_ns,
                        anchor_clock_expiry_unix_ns: v.anchor_clock_expiry_unix_ns,
                        consumed: v.consumed,
                    },
                )
            })
            .collect(),
        // M25.2: persist the observatory history so the trend window
        // survives reboots when a fresh snapshot lands on disk.
        observatory_history: state.observatory_history.clone(),
        // 8.G: persist the in-flight schema migration candidate (P03 §10.4)
        // so a snapshot-accelerated boot resumes the migration mid-window
        // without re-walking the full DAG. None when no migration is in flight.
        migration_candidate: state.migration_candidate.as_ref().map(|c| {
            crate::derived_state::DerivedMigrationCandidate {
                op_name: c.op_name.clone(),
                schema_diff_canonical_bytes: c.schema_diff_canonical_bytes.clone(),
                started_at_cycle: c.started_at_cycle,
                dual_validation_window_cycles: c.dual_validation_window_cycles,
                started_at_unix_ns: c.started_at_unix_ns,
            }
        }),
    };
    // Record the DAG tip at snapshot time so boot knows where to resume replay.
    let snapshot_at_tip: Option<[u8; 32]> = state.dag.tip().map(|t| {
        let mut arr = [0u8; 32];
        arr.copy_from_slice(t.as_ref());
        arr
    });
    let bytes = derived.to_canonical_bytes(snapshot_at_tip.as_ref());
    let signing_key = Ed25519PrivateKey::from_seed(&state.substrate_signing_seed);
    save_snapshot(&bytes, &signing_key, &state.state_dir)
}

/// M21.3 P5 万物互联: back-fill DAG events for legacy substrates that loaded
/// state from disk (gradient.cb / owner_keys.cb / etc.).
///
/// Flow: Python loaded its state from disk; we query Python for the loaded
/// schemas; for each axis NOT yet recorded as an axis_registered event in
/// the DAG, we emit one. For each axis whose current_value != initial_value,
/// we also emit a synthetic axis_perturbed event capturing the delta.
///
/// Also emits the genesis_event if not yet present (so the substrate is now
/// post-M21 from this boot forward). Subsequent boots use the DAG-first path.
///
/// This is the one-shot legacy → M21 migration; idempotent (running it twice
/// is a no-op because all events would already be present after the first run).
pub(crate) fn backfill_dag_from_python_state(
    python_client: &mut BridgeClient,
    state: &mut ServerState,
    _genesis_owner: &Option<[u8; 32]>,
) -> Result<(), SubstrateError> {
    // First: emit genesis_event if missing.
    let has_genesis = state.dag.iter_in_insertion_order().any(|n| {
        n.node_type
            .starts_with(crate::events::NODE_TYPE_GENESIS_PREFIX)
    });
    if !has_genesis {
        let event_nt = crate::events::genesis_event_node_type(&state.substrate_id());
        // 8f / §16.A: stamp the substrate's lineage depth into the back-filled
        // genesis_event. For a legacy/root substrate this is 0; for a child
        // whose manifest carries a depth (e.g. via the override hook) it is
        // preserved so the backfilled DAG remains the authoritative source.
        let event_content = crate::events::encode_genesis_event(
            &state.substrate_id(),
            state.genesis_time_unix_ns(),
            state.generation_depth(),
        );
        let _ = emit_substrate_event(state, event_nt, event_content);
        let _ = save_dag_state(state);
    }

    // Emit operator_pinned if missing.
    let has_op_pinned = state.dag.iter_in_insertion_order().any(|n| {
        n.node_type
            .starts_with(crate::events::NODE_TYPE_OPERATOR_PINNED_PREFIX)
    });
    if !has_op_pinned {
        if let Some(pinned) = state.pinned_operator_identity.clone() {
            let event_nt = crate::events::operator_pinned_node_type(&pinned.pubkey);
            let event_content =
                crate::events::encode_operator_pinned(&pinned.pubkey, pinned.first_pinned_unix_ns);
            let _ = emit_substrate_event(state, event_nt, event_content);
            let _ = save_dag_state(state);
        }
    }

    // Query Python for its loaded axis schemas + current values.
    let schemas = python_client
        .query_gradient_schemas()
        .map_err(SubstrateError::Bridge)?;

    // For each axis, if no axis_registered event exists for it in the DAG,
    // emit one. If current_value != initial_value, also emit axis_perturbed.
    for schema in schemas {
        let want_reg_nt = crate::events::axis_registered_node_type(&schema.name);
        let has_reg = state
            .dag
            .iter_in_insertion_order()
            .any(|n| n.node_type == want_reg_nt);
        if !has_reg {
            let event = crate::events::AxisRegisteredEvent {
                name: schema.name.clone(),
                axis_class: schema.axis_class.clone(),
                fruiting_threshold: schema.fruiting_threshold,
                initial_value: schema.initial_value,
                decay_rate_per_cycle: schema.decay_rate_per_cycle,
                is_mortality_signal: schema.is_mortality_signal,
                update_rule_kind: schema.update_rule_kind.clone(),
            };
            let event_content = crate::events::encode_axis_registered(&event);
            let _ = emit_substrate_event(state, want_reg_nt, event_content);
        }
        // If current value differs from initial, emit a perturbed event for the delta.
        let delta = schema.current_value - schema.initial_value;
        if delta != 0.0 {
            let perturbed_nt = crate::events::axis_perturbed_node_type(&schema.name);
            let event_content = crate::events::encode_axis_perturbed(&schema.name, delta);
            let _ = emit_substrate_event(state, perturbed_nt, event_content);
        }
    }
    let _ = save_dag_state(state);
    Ok(())
}

/// M21.3 P5 万物互联: replay DAG events to a freshly-loaded Python worker.
///
/// Iterates DAG events in insertion order. For each event that affects
/// Python-side gradient state (axis_registered:* / axis_perturbed:*),
/// invokes the corresponding Python BridgeClient method to reconstruct
/// state in-memory.
///
/// This is the inverse of `_handle_load_state(skip_disk_load=true)`:
/// load empty, then replay events to derive state.
///
/// Errors during replay propagate up — a malformed event in the DAG
/// indicates corruption; substrate refuses to boot with partial state.
pub(crate) fn replay_python_events_from_dag(
    python_client: &mut BridgeClient,
    dag: &Dag,
) -> Result<(), SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode, map_get_string};
    for node in dag.iter_in_insertion_order() {
        let nt = &node.node_type;
        if let Some(axis_name) = nt.strip_prefix(crate::events::NODE_TYPE_AXIS_REGISTERED_PREFIX) {
            // Decode the axis_registered event and replay as register_axis call.
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode axis_registered:{axis_name}: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} content not Map: {other:?}"
                    )))
                }
            };
            let getf = |k: &str| -> Result<&str, SubstrateError> {
                map_get_string(&map, k).map_err(|e| {
                    SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} field {k}: {e}"
                    ))
                })
            };
            let axis_class = getf("axis_class")?.to_string();
            let fruiting_threshold: f64 =
                getf("fruiting_threshold_repr")?.parse().map_err(|e| {
                    SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} fruiting_threshold_repr parse: {e}"
                    ))
                })?;
            let initial_value: f64 = getf("initial_value_repr")?.parse().map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_registered:{axis_name} initial_value_repr parse: {e}"
                ))
            })?;
            let decay_rate: f64 = getf("decay_rate_per_cycle_repr")?.parse().map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_registered:{axis_name} decay_rate_per_cycle_repr parse: {e}"
                ))
            })?;
            let is_mortality_signal = match map.get("is_mortality_signal") {
                Some(Value::Bool(b)) => *b,
                _ => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay axis_registered:{axis_name} missing is_mortality_signal"
                    )))
                }
            };
            let update_rule_kind = getf("update_rule_kind")?.to_string();
            python_client
                .register_axis(
                    axis_name,
                    &axis_class,
                    fruiting_threshold,
                    initial_value,
                    decay_rate,
                    is_mortality_signal,
                    &update_rule_kind,
                )
                .map_err(SubstrateError::Bridge)?;
        } else if let Some(axis_name) =
            nt.strip_prefix(crate::events::NODE_TYPE_AXIS_PERTURBED_PREFIX)
        {
            // Decode the axis_perturbed event and replay as perturb call.
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode axis_perturbed:{axis_name}: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay axis_perturbed:{axis_name} content not Map: {other:?}"
                    )))
                }
            };
            let delta_repr = map_get_string(&map, "delta_repr").map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_perturbed:{axis_name} delta_repr: {e}"
                ))
            })?;
            let delta: f64 = delta_repr.parse().map_err(|e| {
                SubstrateError::Protocol(format!(
                    "replay axis_perturbed:{axis_name} delta parse: {e}"
                ))
            })?;
            python_client
                .perturb(axis_name, delta)
                .map_err(SubstrateError::Bridge)?;
        } else if nt.starts_with("perturb_from_raw:") {
            // M16 events: also a perturbation. Decode and replay.
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode perturb_from_raw: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay perturb_from_raw content not Map: {other:?}"
                    )))
                }
            };
            let axis_name = map_get_string(&map, "axis_name")
                .map_err(|e| {
                    SubstrateError::Protocol(format!("replay perturb_from_raw axis_name: {e}"))
                })?
                .to_string();
            let delta_repr = map_get_string(&map, "delta_repr").map_err(|e| {
                SubstrateError::Protocol(format!("replay perturb_from_raw delta_repr: {e}"))
            })?;
            let delta: f64 = delta_repr.parse().map_err(|e| {
                SubstrateError::Protocol(format!("replay perturb_from_raw delta parse: {e}"))
            })?;
            python_client
                .perturb(&axis_name, delta)
                .map_err(SubstrateError::Bridge)?;
        } else if nt == crate::events::NODE_TYPE_CYCLE_ADVANCED {
            // M21.3: replay cycle advance to Python so DECAY-rule axes get
            // their decay applied + APPETITE-axis fruiting resets fire.
            // Discards the advance_response (sporocarps were emitted during
            // the original cycle and are already DAG nodes; replay just
            // needs the gradient mutation side-effect).
            let decoded = decode(node.content_canonical_bytes.as_ref()).map_err(|e| {
                SubstrateError::Protocol(format!("replay decode cycle_advanced: {e}"))
            })?;
            let map = match decoded {
                Value::Map(m) => m,
                other => {
                    return Err(SubstrateError::Protocol(format!(
                        "replay cycle_advanced content not Map: {other:?}"
                    )))
                }
            };
            let new_cycle = match map.get("new_cycle") {
                Some(Value::Uint(u)) => *u,
                _ => {
                    return Err(SubstrateError::Protocol(
                        "replay cycle_advanced missing new_cycle".to_string(),
                    ))
                }
            };
            python_client
                .advance(new_cycle)
                .map_err(SubstrateError::Bridge)?;
        }
        // Other event types (genesis_event, operator_pinned, nonce_*,
        // sporocarp:*, mutation:*, immune:*, raw_material:*,
        // absorption_event:*, evolution_*:*, self_euthanasia_proposal:*,
        // spore_emission:*, owner_key_initialized) are NOT replayed to
        // Python (Rust-side state derived via DerivedState; Python doesn't
        // need them for gradient).
        //
        // NOTE: schema_evolution-driven schema changes (M17) are NOT
        // auto-replayed. M21.4+ may add `axis_threshold_modified` events
        // with replay paths.
    }
    Ok(())
}
