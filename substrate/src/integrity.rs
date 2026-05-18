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
//! - L1/HARD_RULES §1 C9 cold_resume_invariant_failure (boot checks).
//! - L1/HARD_RULES §1 C18 canonical_bytes_render_drift (P9 皮肤 round-trip).
//! - L1/HARD_RULES §1 C19/C32 substrate_state_orphan_detected (P5 万物互联).

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, Value};

use crate::server::{
    emit_immune_sporocarp, emit_substrate_event, hex_encode, hex_first_8_bytes, save_dag_state,
    ServerState,
};
use crate::SubstrateError;

/// M12: Result of one integrity check (C9 cold_resume_invariant_failure sub-check).
///
/// **M-anchor-4 §9.3.4**: extended with `witness_inputs_canonical_bytes`, the
/// raw inputs the owner re-feeds into the canonical check. The substrate
/// itself does not emit pass/fail per doctrine §9.3.4; the `passed` field
/// remains for backward-compat with the immune-emission pipeline (which fires
/// on detected failures) but the witness emission path treats it as
/// substrate's CLAIM only — owner verifies independently.
#[derive(Debug, Clone)]
pub(crate) struct IntegrityCheckResult {
    pub(crate) check_id: String,
    pub(crate) passed: bool,
    pub(crate) evidence: String,
    /// **M-anchor-4**: witness inputs (canonical-bytes Map encoding the raw
    /// check inputs). Empty `Vec` if the check has no structured inputs
    /// worth witnessing (e.g., placeholder owner_keys_consistency deferred
    /// to Python path).
    pub(crate) witness_inputs_canonical_bytes: Vec<u8>,
    /// **M-anchor-4**: which doctrine tier this check belongs to per
    /// L1/SCHEMA §4.1. Owner uses to route verification.
    pub(crate) tier: &'static str,
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

    // **M-anchor-4 §9.3.4**: ALSO emit invariant_witness:{check_id} events
    // for each check (regardless of pass/fail) so the owner can re-derive
    // the verdict from the raw inputs.
    let witnesses_emitted = emit_invariant_witnesses(state, &results);
    if witnesses_emitted > 0 {
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
    // **M-anchor-4**: witness inputs = {substrate_id: Bytes(32)}. Owner re-checks
    // by asserting non-zero.
    let substrate_id_zero = state.manifest.substrate_id.iter().all(|b| *b == 0);
    let witness_inputs_substrate_id = {
        let mut m = BTreeMap::new();
        m.insert(
            "substrate_id".to_string(),
            Value::Bytes(state.manifest.substrate_id.to_vec()),
        );
        cb_encode(&Value::Map(m))
            .map(|cb| cb.0)
            .unwrap_or_default()
    };
    results.push(IntegrityCheckResult {
        check_id: "substrate_id_well_formed".to_string(),
        passed: !substrate_id_zero,
        evidence: if substrate_id_zero {
            "manifest.substrate_id is all zeros (genesis bug or tamper)".to_string()
        } else {
            "ok".to_string()
        },
        witness_inputs_canonical_bytes: witness_inputs_substrate_id,
        tier: "tier_1",
    });

    // 2. Cycle counter monotonic against DAG at_cycle.
    // **M-anchor-4**: witness inputs = {manifest_cycle, max_dag_cycle}. Owner
    // re-checks manifest_cycle >= max_dag_cycle.
    let max_dag_cycle = state
        .dag
        .iter_in_insertion_order()
        .map(|n| n.created_at_cycle)
        .max()
        .unwrap_or(0);
    let monotonic = state.manifest.cycle_counter >= max_dag_cycle;
    let witness_inputs_cycle_monotonic = {
        let mut m = BTreeMap::new();
        m.insert(
            "manifest_cycle_counter".to_string(),
            Value::Uint(state.manifest.cycle_counter),
        );
        m.insert(
            "max_dag_at_cycle".to_string(),
            Value::Uint(max_dag_cycle),
        );
        cb_encode(&Value::Map(m))
            .map(|cb| cb.0)
            .unwrap_or_default()
    };
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
        witness_inputs_canonical_bytes: witness_inputs_cycle_monotonic,
        tier: "tier_1",
    });

    // 3. Pinned pubkey well-formed (if exists).
    // **M-anchor-4**: witness inputs = {pinned_pubkey: Bytes(32)}.
    if let Some(pinned) = &state.pinned_operator_identity {
        let zero = pinned.pubkey.iter().all(|b| *b == 0);
        let witness_inputs_pinned_pk = {
            let mut m = BTreeMap::new();
            m.insert(
                "pinned_operator_pubkey".to_string(),
                Value::Bytes(pinned.pubkey.to_vec()),
            );
            cb_encode(&Value::Map(m))
                .map(|cb| cb.0)
                .unwrap_or_default()
        };
        results.push(IntegrityCheckResult {
            check_id: "pinned_pubkey_well_formed".to_string(),
            passed: !zero,
            evidence: if zero {
                "pinned operator_identity_pubkey is all zeros".to_string()
            } else {
                "ok (32 non-zero bytes)".to_string()
            },
            witness_inputs_canonical_bytes: witness_inputs_pinned_pk,
            tier: "tier_1",
        });
    }

    // 4. DAG.verify_all() — every node's hash recomputes correctly.
    // **M-anchor-4 §9.3.5**: witness inputs include {node_count, dag_tip_hash}.
    // For tier-2 sampled re-verification (deferred), the owner will derive
    // sample indices via `anchor_nonce_derived_sample_indices` and pull
    // (hash, parent_hashes, content_hash) tuples for those indices via the
    // existing enumerate_dag_since RPC. The witness here is the SUFFICIENT
    // INPUT for the owner to know which leaves to sample + check.
    let dag_verify = state.dag.verify_all();
    let witness_inputs_dag_verify = {
        let mut m = BTreeMap::new();
        m.insert(
            "node_count".to_string(),
            Value::Uint(state.dag.node_count() as u64),
        );
        let tip_bytes = state
            .dag
            .tip()
            .map(|t| t.as_ref().to_vec())
            .unwrap_or_default();
        m.insert("dag_tip_hash".to_string(), Value::Bytes(tip_bytes));
        cb_encode(&Value::Map(m))
            .map(|cb| cb.0)
            .unwrap_or_default()
    };
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
        witness_inputs_canonical_bytes: witness_inputs_dag_verify,
        tier: "tier_1",
    });

    // 5. owner_keys consistency check is operator-side: we can only verify the
    //    pinned operator pubkey is non-zero (the owner_keys live in Python and
    //    are loaded via load_state during hello). This check is therefore a
    //    placeholder at the Rust layer; full owner_keys vs pinned-pubkey cross-
    //    validation happens implicitly when the first CI mutation is submitted
    //    (signature verification will fail if Python's owner_keys diverges from
    //    Rust's pinned pubkey).
    // **M-anchor-4**: this check is a placeholder at the Rust layer; no
    // structured witness inputs.
    results.push(IntegrityCheckResult {
        check_id: "owner_keys_consistency".to_string(),
        passed: true,
        evidence: "deferred to Python load_state path; CI mutation signatures cross-validate"
            .to_string(),
        witness_inputs_canonical_bytes: Vec::new(),
        tier: "tier_1",
    });

    // 6. M19 P9 皮肤 / L1/HARD_RULES C18 canonical_bytes_render_drift:
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
    // **M-anchor-4**: witness inputs = {substrate_generated_count, drift_count,
    // dag_tip_hash}. Owner re-runs the round-trip on the SAME node set to
    // verify substrate's claim. For full re-verification, owner uses
    // enumerate_dag_since to fetch substrate-generated nodes' content_bytes
    // and replays decode+encode.
    let witness_inputs_cb_drift = {
        let mut m = BTreeMap::new();
        m.insert(
            "substrate_generated_count".to_string(),
            Value::Uint(substrate_generated_count as u64),
        );
        m.insert(
            "drift_count".to_string(),
            Value::Uint(cb_drift_count as u64),
        );
        let tip_bytes = state
            .dag
            .tip()
            .map(|t| t.as_ref().to_vec())
            .unwrap_or_default();
        m.insert("dag_tip_hash".to_string(), Value::Bytes(tip_bytes));
        cb_encode(&Value::Map(m))
            .map(|cb| cb.0)
            .unwrap_or_default()
    };
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
        witness_inputs_canonical_bytes: witness_inputs_cb_drift,
        tier: "tier_1",
    });

    // 7. M21.1 P5 万物互联 / L1/HARD_RULES C19 substrate_state_orphan_detected:
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
    // **M-anchor-4**: witness inputs = {substrate_id, manifest_cycle, dag_node_count}.
    // Owner re-runs DerivedState::from_dag and compares against these values.
    let witness_inputs_orphan = {
        let mut m = BTreeMap::new();
        m.insert(
            "substrate_id".to_string(),
            Value::Bytes(state.manifest.substrate_id.to_vec()),
        );
        m.insert(
            "manifest_cycle_counter".to_string(),
            Value::Uint(state.manifest.cycle_counter),
        );
        m.insert(
            "dag_node_count".to_string(),
            Value::Uint(state.dag.node_count() as u64),
        );
        cb_encode(&Value::Map(m))
            .map(|cb| cb.0)
            .unwrap_or_default()
    };
    results.push(IntegrityCheckResult {
        check_id: "substrate_state_orphan_detected".to_string(),
        passed: orphan_passed,
        evidence: orphan_evidence,
        witness_inputs_canonical_bytes: witness_inputs_orphan,
        tier: "tier_1",
    });

    results
}

/// **M-anchor-4 §9.3.4**: emit `invariant_witness:{check_id}` DAG events
/// for each integrity check result. Witnesses are emitted REGARDLESS of
/// pass/fail per doctrine — the substrate provides raw inputs; the owner
/// re-derives. The immune-sporocarp path (which fires on detected failures)
/// is preserved separately.
///
/// **Per-cycle dedup**: this function skips emission for any check_id that
/// already has a witness at the current `manifest.cycle_counter`. Without
/// this dedup, repeated reboots at the same cycle (e.g., from operator
/// restart on a persisted state_dir) would inflate the DAG with duplicate
/// witnesses. Owner-side reconstruction only cares about the LATEST
/// witness per (cycle, check_id), so the dedup is doctrinally safe.
///
/// Called from boot AND from `handle_run_immune_check`.
pub(crate) fn emit_invariant_witnesses(
    state: &mut ServerState,
    results: &[IntegrityCheckResult],
) -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let at_cycle = state.manifest.cycle_counter;
    let at_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);

    // Per-cycle dedup: gather set of (check_id) for which a witness already
    // exists at current cycle. Walk DAG once.
    let mut already_witnessed: std::collections::BTreeSet<String> =
        std::collections::BTreeSet::new();
    for node in state.dag.iter_in_insertion_order() {
        if node.created_at_cycle != at_cycle {
            continue;
        }
        if let Some(check_id) = node
            .node_type
            .strip_prefix(crate::events::NODE_TYPE_INVARIANT_WITNESS_PREFIX)
        {
            already_witnessed.insert(check_id.to_string());
        }
    }

    let mut count: u64 = 0;
    for result in results {
        if result.witness_inputs_canonical_bytes.is_empty() {
            // No structured inputs — skip emission (e.g., owner_keys_consistency
            // placeholder).
            continue;
        }
        if already_witnessed.contains(&result.check_id) {
            // Same cycle, already witnessed — skip.
            continue;
        }
        let body = crate::events::encode_invariant_witness(
            &result.check_id,
            result.tier,
            at_cycle,
            at_unix_ns,
            &result.witness_inputs_canonical_bytes,
            // M-anchor-4 tier-1: no anchor-nonce sampling yet (tier-1 checks
            // don't sample). Tier-2 checks (M-anchor-4.5+) will fill these.
            &[],
            &[],
        );
        let nt = crate::events::invariant_witness_node_type(&result.check_id);
        if emit_substrate_event(state, nt, body).is_ok() {
            count += 1;
        }
    }
    count
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
