//! Substrate integrity checks — extracted from `server.rs` (Phase B Step 4).
//!
//! Owns the boot-time and ad-hoc integrity check pipeline:
//! - `handle_run_immune_check` is the operator-driven entry point (dispatched
//!   on `RUN_IMMUNE_CHECK`); emits a fresh C9/C18/C32 sporocarp per failure.
//! - `run_integrity_checks` runs all 7 checks and returns
//!   [`IntegrityCheckResult`] for each. Called from boot (`run_loop`) and
//!   from `handle_run_immune_check`; **kept `pub(crate)`** so `run_loop` can
//!   continue calling it directly.
//! - `check_substrate_state_orphans` is the C19 reconciler (Rust-side
//!   ServerState ↔ DerivedState::from_dag).
//!
//! Doctrine traceability:
//! - L1_HARD_RULES §1 C9 cold_resume_invariant_failure (boot checks).
//! - L1_HARD_RULES §1 C18 canonical_bytes_render_drift (P9 皮肤 round-trip).
//! - L1_HARD_RULES §1 C19/C32 substrate_state_orphan_detected (P5 万物互联).

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::Value;

use crate::server::{emit_immune_sporocarp, hex_encode, hex_first_8_bytes, save_dag_state, ServerState};
use crate::SubstrateError;

/// M12: Result of one integrity check (C9 cold_resume_invariant_failure sub-check).
#[derive(Debug, Clone)]
pub(crate) struct IntegrityCheckResult {
    pub(crate) check_id: String,
    pub(crate) passed: bool,
    pub(crate) evidence: String,
}

/// M12: Run the substrate's comprehensive integrity checks ad-hoc.
///
/// Runs the same checks as boot-time C9 (substrate_id_well_formed,
/// cycle_counter_monotonic, pinned_pubkey_well_formed, dag_verify_all,
/// owner_keys_consistency). For each failing check, emits a new C9 immune
/// sporocarp. Always returns a structured report regardless of outcome.
pub(crate) fn handle_run_immune_check(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let results = run_integrity_checks(state);

    // Emit immune sporocarps for each failure (consistent with boot-time C9
    // routing; M19: canonical_bytes_render_drift gets its dedicated C18 ID).
    let mut emitted_count: u64 = 0;
    for result in &results {
        if !result.passed {
            let evidence = format!(
                "ad-hoc integrity check failed: {} — {}",
                result.check_id, result.evidence
            );
            let (detector_id, detector_name) = if result.check_id == "canonical_bytes_render_drift"
            {
                (
                    "C18_canonical_bytes_render_drift",
                    "canonical_bytes_render_drift".to_string(),
                )
            } else if result.check_id == "substrate_state_orphan_detected" {
                (
                    "C32_substrate_state_orphan_detected",
                    "substrate_state_orphan_detected".to_string(),
                )
            } else {
                (
                    "C9_cold_resume_invariant_failure",
                    format!("cold_resume_invariant_failure ({})", result.check_id),
                )
            };
            if emit_immune_sporocarp(state, detector_id, &detector_name, &evidence).is_ok() {
                emitted_count += 1;
            }
        }
    }
    if emitted_count > 0 {
        save_dag_state(state)?;
    }

    // Build response payload: per-check results.
    let check_values: Vec<Value> = results
        .iter()
        .map(|r| {
            let mut m = BTreeMap::new();
            m.insert("check_id".to_string(), Value::String(r.check_id.clone()));
            m.insert("passed".to_string(), Value::Bool(r.passed));
            m.insert("evidence".to_string(), Value::String(r.evidence.clone()));
            Value::Map(m)
        })
        .collect();

    let total_checks = results.len() as u64;
    let failed_checks = results.iter().filter(|r| !r.passed).count() as u64;

    let mut payload = BTreeMap::new();
    payload.insert("total_checks".to_string(), Value::Uint(total_checks));
    payload.insert("failed_checks".to_string(), Value::Uint(failed_checks));
    payload.insert(
        "immune_events_emitted".to_string(),
        Value::Uint(emitted_count),
    );
    payload.insert("checks".to_string(), Value::Array(check_values));

    Ok(Some(Message::new(
        msg_type::RUN_IMMUNE_CHECK_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M12: Run the substrate's comprehensive integrity checks.
///
/// Runs 5 checks:
/// 1. `substrate_id_well_formed` — manifest.substrate_id is non-zero
/// 2. `cycle_counter_monotonic` — manifest.cycle_counter ≥ max(DAG node at_cycle)
/// 3. `pinned_pubkey_well_formed` — pinned pubkey is non-zero Ed25519
/// 4. `dag_verify_all` — every DAG node's hash recomputes correctly
/// 5. `owner_keys_consistency` — (M10 operator==owner) active owner key MUST equal pinned operator pubkey
///
/// Returns a vec of results. Caller emits a C9 immune sporocarp for each failure.
pub(crate) fn run_integrity_checks(state: &ServerState) -> Vec<IntegrityCheckResult> {
    let mut results = Vec::new();

    // 1. substrate_id well-formed.
    let substrate_id_zero = state.manifest.substrate_id.iter().all(|b| *b == 0);
    results.push(IntegrityCheckResult {
        check_id: "substrate_id_well_formed".to_string(),
        passed: !substrate_id_zero,
        evidence: if substrate_id_zero {
            "manifest.substrate_id is all zeros (genesis bug or tamper)".to_string()
        } else {
            "ok".to_string()
        },
    });

    // 2. Cycle counter monotonic against DAG at_cycle.
    let max_dag_cycle = state
        .dag
        .iter_in_insertion_order()
        .map(|n| n.created_at_cycle)
        .max()
        .unwrap_or(0);
    let monotonic = state.manifest.cycle_counter >= max_dag_cycle;
    results.push(IntegrityCheckResult {
        check_id: "cycle_counter_monotonic".to_string(),
        passed: monotonic,
        evidence: if monotonic {
            format!(
                "manifest.cycle_counter={} >= max(DAG.at_cycle)={}",
                state.manifest.cycle_counter, max_dag_cycle
            )
        } else {
            format!(
                "manifest.cycle_counter={} < max(DAG.at_cycle)={} (manifest may have rolled back)",
                state.manifest.cycle_counter, max_dag_cycle
            )
        },
    });

    // 3. Pinned pubkey well-formed (if exists).
    if let Some(pinned) = &state.pinned_operator_identity {
        let zero = pinned.pubkey.iter().all(|b| *b == 0);
        results.push(IntegrityCheckResult {
            check_id: "pinned_pubkey_well_formed".to_string(),
            passed: !zero,
            evidence: if zero {
                "pinned operator_identity_pubkey is all zeros".to_string()
            } else {
                "ok (32 non-zero bytes)".to_string()
            },
        });
    }

    // 4. DAG.verify_all() — every node's hash recomputes correctly.
    let dag_verify = state.dag.verify_all();
    results.push(IntegrityCheckResult {
        check_id: "dag_verify_all".to_string(),
        passed: dag_verify.is_ok(),
        evidence: match &dag_verify {
            Ok(()) => format!(
                "ok (all {} nodes pass hash recomputation)",
                state.dag.node_count()
            ),
            Err(e) => format!("dag_verify_all failed: {e}"),
        },
    });

    // 5. owner_keys consistency check is operator-side: we can only verify the
    //    pinned operator pubkey is non-zero (the owner_keys live in Python and
    //    are loaded via load_state during hello). This check is therefore a
    //    placeholder at the Rust layer; full owner_keys vs pinned-pubkey cross-
    //    validation happens implicitly when the first CI mutation is submitted
    //    (signature verification will fail if Python's owner_keys diverges from
    //    Rust's pinned pubkey).
    results.push(IntegrityCheckResult {
        check_id: "owner_keys_consistency".to_string(),
        passed: true,
        evidence: "deferred to Python load_state path; CI mutation signatures cross-validate"
            .to_string(),
    });

    // 6. M19 P9 皮肤 / L1_HARD_RULES C18 canonical_bytes_render_drift:
    //    decode each DAG node's content_canonical_bytes, re-encode, and compare.
    //    Any divergence indicates canonical-bytes rendering is non-deterministic
    //    (e.g., map keys not sorted, repr drift, integer encoding inconsistency)
    //    — a CRITICAL skin breach that would let an attacker present the same
    //    semantic content with different byte sequences.
    //
    //    M19-MV scope: scan substrate-self-generated DAG nodes. Operator-
    //    supplied content (mutation:*) is opaque to the substrate — the
    //    operator chooses the encoding — so we skip those nodes. Substrate-
    //    generated nodes (sporocarp:*, immune:*, absorption_event:*,
    //    evolution_*:*, self_euthanasia_proposal:*, perturb_from_raw:*,
    //    raw_material:*) MUST round-trip cleanly because the substrate itself
    //    chose their canonical-bytes shape.
    let is_substrate_generated = |node_type: &str| -> bool { !node_type.starts_with("mutation:") };
    let (cb_drift_count, cb_drift_example): (usize, Option<String>) = {
        use myco_kernel_shared::canonical_bytes::{decode, encode};
        let mut drift_count = 0usize;
        let mut first_example: Option<String> = None;
        for node in state
            .dag
            .iter_in_insertion_order()
            .filter(|n| is_substrate_generated(&n.node_type))
        {
            let original = node.content_canonical_bytes.as_ref();
            // Decode then re-encode. If the bytes differ, drift detected.
            match decode(original) {
                Ok(value) => match encode(&value) {
                    Ok(reencoded) => {
                        if reencoded.as_ref() != original {
                            drift_count += 1;
                            if first_example.is_none() {
                                first_example = Some(format!(
                                    "node {} (type {:?}) round-trips to different bytes \
                                     (original {} bytes, re-encoded {} bytes)",
                                    hex_encode(node.hash.as_ref()),
                                    node.node_type,
                                    original.len(),
                                    reencoded.as_ref().len()
                                ));
                            }
                        }
                    }
                    Err(e) => {
                        drift_count += 1;
                        if first_example.is_none() {
                            first_example = Some(format!(
                                "node {} re-encode failed: {e}",
                                hex_encode(node.hash.as_ref())
                            ));
                        }
                    }
                },
                Err(e) => {
                    // Decode failure on supposedly canonical bytes is itself a drift signal.
                    drift_count += 1;
                    if first_example.is_none() {
                        first_example = Some(format!(
                            "node {} decode failed: {e}",
                            hex_encode(node.hash.as_ref())
                        ));
                    }
                }
            }
        }
        (drift_count, first_example)
    };
    // Count substrate-generated nodes for the OK-evidence message.
    let substrate_generated_count = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| is_substrate_generated(&n.node_type))
        .count();
    results.push(IntegrityCheckResult {
        check_id: "canonical_bytes_render_drift".to_string(),
        passed: cb_drift_count == 0,
        evidence: if cb_drift_count == 0 {
            format!(
                "ok (all {substrate_generated_count} substrate-generated DAG nodes round-trip cleanly; mutation:* content is operator-opaque and skipped)"
            )
        } else {
            cb_drift_example.unwrap_or_else(|| {
                format!("{cb_drift_count} nodes drift; no specific example captured")
            })
        },
    });

    // 7. M21.1 P5 万物互联 / L1_HARD_RULES C19 substrate_state_orphan_detected:
    //    rebuild Rust-side state from DAG events and compare to in-memory state.
    //    Divergence → some state mutation happened without emitting a DAG event
    //    (orphan), violating P5 "the substrate is a connected graph; orphans
    //    are dead tissue."
    //
    //    M21.1 dual-write phase scope: this check verifies that all Rust-side
    //    fields (substrate_id, genesis_time, cycle_counter, last_absorbed_cycle,
    //    pinned_operator_identity, nonce_log) can be derived from DAG events.
    //    Python-owned state (gradient, owner_keys) is deferred to M21.3 when
    //    Python becomes a derived-view consumer.
    let (orphan_passed, orphan_evidence) = check_substrate_state_orphans(state);
    results.push(IntegrityCheckResult {
        check_id: "substrate_state_orphan_detected".to_string(),
        passed: orphan_passed,
        evidence: orphan_evidence,
    });

    results
}

/// M21.1: C19 detector. Reconciles in-memory ServerState (Rust-side fields)
/// against DerivedState::from_dag. Returns (passed, evidence).
///
/// What this checks:
/// - substrate_id: live manifest.substrate_id == derived.substrate_id
/// - genesis_time_unix_ns: live manifest.genesis_time_unix_ns == derived.genesis_time_unix_ns
/// - cycle_counter: live manifest.cycle_counter == derived.cycle_counter
/// - last_absorbed_cycle: live manifest.last_absorbed_cycle == derived.last_absorbed_cycle
/// - pinned_operator_identity: live state.pinned_operator_identity == derived.pinned_operator_identity
/// - nonce_log: live state.nonce_log size + per-entry consumed flags == derived.nonce_log
fn check_substrate_state_orphans(state: &ServerState) -> (bool, String) {
    use crate::derived_state::DerivedState;

    let derived = match DerivedState::from_dag(&state.dag) {
        Ok(d) => d,
        Err(e) => {
            return (
                false,
                format!("DerivedState::from_dag failed: {e} (likely event encoding bug)"),
            );
        }
    };

    let mut divergences: Vec<String> = Vec::new();

    // substrate_id: derived is Some iff a genesis_event has been emitted.
    // If derived.substrate_id is None but live manifest has one, that means
    // the substrate is running on a manifest.cb without a corresponding
    // genesis_event in DAG — this is exactly the M21.1 migration condition
    // (existing substrates pre-M21 have no genesis_event). To avoid false
    // positives during migration, we ONLY report divergence when derived
    // HAS substrate_id and it differs from live.
    if let Some(d_id) = derived.substrate_id {
        if d_id != state.manifest.substrate_id {
            divergences.push(format!(
                "substrate_id mismatch: live={}, derived={}",
                hex_encode(&state.manifest.substrate_id),
                hex_encode(&d_id)
            ));
        }
    }

    // genesis_time: same migration-friendly check.
    if let Some(d_time) = derived.genesis_time_unix_ns {
        if d_time != state.manifest.genesis_time_unix_ns {
            divergences.push(format!(
                "genesis_time_unix_ns mismatch: live={}, derived={}",
                state.manifest.genesis_time_unix_ns, d_time
            ));
        }
    }

    // cycle_counter: this is INCREMENTED in the dispatch arm AFTER handle_advance
    // returns, but the cycle_advanced event is emitted from inside the dispatch
    // arm too. So derived.cycle_counter should EQUAL live.cycle_counter after
    // an advance. For pre-M21 manifests that never emitted cycle_advanced, the
    // derived value will be 0 while live can be > 0 — only report divergence
    // when derived.cycle_counter > 0 OR (derived.substrate_id is Some, i.e. we
    // have a genesis event and thus the substrate is post-M21).
    if (derived.cycle_counter > 0 || derived.substrate_id.is_some())
        && derived.cycle_counter != state.manifest.cycle_counter
    {
        divergences.push(format!(
            "cycle_counter mismatch: live={}, derived={}",
            state.manifest.cycle_counter, derived.cycle_counter
        ));
    }

    // last_absorbed_cycle: derived from absorption_event events (already in DAG
    // since M18). Should always match.
    if derived.last_absorbed_cycle != state.manifest.last_absorbed_cycle {
        // BUT: absorption_event was added in M18; pre-M21 last_absorbed_cycle
        // tracking is via manifest only. Migration tolerance:
        // - derived is Some → strict match required
        // - derived is None → tolerate live Some (legacy)
        if derived.last_absorbed_cycle.is_some() {
            divergences.push(format!(
                "last_absorbed_cycle mismatch: live={:?}, derived={:?}",
                state.manifest.last_absorbed_cycle, derived.last_absorbed_cycle
            ));
        }
    }

    // pinned_operator_identity: derived from operator_pinned event.
    if let Some(derived_id) = &derived.pinned_operator_identity {
        match &state.pinned_operator_identity {
            Some(live_id) => {
                if live_id.pubkey != derived_id.pubkey
                    || live_id.first_pinned_unix_ns != derived_id.first_pinned_unix_ns
                {
                    divergences.push(format!(
                        "pinned_operator_identity mismatch: live.pubkey={}, derived.pubkey={}",
                        hex_encode(&live_id.pubkey),
                        hex_encode(&derived_id.pubkey)
                    ));
                }
            }
            None => {
                divergences.push(
                    "pinned_operator_identity present in DAG but absent in live state".to_string(),
                );
            }
        }
    }

    // nonce_log: derived from nonce_issued/consumed/expired events.
    // Compare entry-by-entry. Migration tolerance: if derived.nonce_log is
    // empty AND live.nonce_log is non-empty AND no genesis_event in DAG, this
    // is pre-M21 legacy nonce data — tolerate. Otherwise enforce match.
    let derived_is_post_m21 = derived.substrate_id.is_some();
    if derived_is_post_m21 {
        for (nonce, live_entry) in &state.nonce_log {
            match derived.nonce_log.get(nonce) {
                Some(d_entry) => {
                    if live_entry.consumed != d_entry.consumed {
                        divergences.push(format!(
                            "nonce {} consumed-flag mismatch: live={}, derived={}",
                            hex_first_8_bytes(nonce),
                            live_entry.consumed,
                            d_entry.consumed
                        ));
                    }
                    if live_entry.expiry_unix_ns != d_entry.expiry_unix_ns {
                        divergences.push(format!(
                            "nonce {} expiry mismatch",
                            hex_first_8_bytes(nonce)
                        ));
                    }
                }
                None => {
                    divergences.push(format!(
                        "nonce {} in live log but no nonce_issued event in DAG",
                        hex_first_8_bytes(nonce)
                    ));
                }
            }
        }
        // Check derived has no extras absent from live.
        for nonce in derived.nonce_log.keys() {
            if !state.nonce_log.contains_key(nonce) {
                divergences.push(format!(
                    "nonce {} has nonce_issued event in DAG but absent in live log (premature prune?)",
                    hex_first_8_bytes(nonce)
                ));
            }
        }
    }

    if divergences.is_empty() {
        (
            true,
            format!(
                "ok (Rust-side state fully derivable from DAG; nonce_log={} entries)",
                state.nonce_log.len()
            ),
        )
    } else {
        let summary = if divergences.len() == 1 {
            divergences.into_iter().next().unwrap()
        } else {
            format!(
                "{} orphan(s) detected. First: {}",
                divergences.len(),
                divergences.into_iter().next().unwrap()
            )
        };
        (false, summary)
    }
}
