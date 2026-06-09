//! Substrate integrity checks, extracted from `server.rs` (Phase B Step 4).
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
use myco_kernel_shared::canonical_bytes::{decode as cb_decode, encode as cb_encode, Value};

use crate::server::{
    emit_immune_sporocarp, emit_substrate_event, hex_encode, save_dag_state,
    ServerState,
};
use crate::SubstrateError;

/// M12: Result of one integrity check (C9 cold_resume_invariant_failure sub-check).
///
/// **M-anchor-4 §9.3.4**: extended with `witness_inputs_canonical_bytes`, the
/// raw inputs re-fed into the canonical check at the CI gate. The substrate
/// itself does not emit pass/fail per doctrine §9.3.4; the `passed` field
/// remains for backward-compat with the immune-emission pipeline (which fires
/// on detected failures) but the witness emission path treats it as
/// substrate's CLAIM only, verified independently at the CI gate.
#[derive(Debug, Clone)]
pub(crate) struct IntegrityCheckResult {
    pub(crate) check_id: String,
    pub(crate) passed: bool,
    pub(crate) evidence: String,
    /// **M-anchor-4**: witness inputs (canonical-bytes Map encoding the raw
    /// check inputs). Empty `Vec` if the check has no structured inputs
    /// worth witnessing.
    pub(crate) witness_inputs_canonical_bytes: Vec<u8>,
    /// **M-anchor-4**: which doctrine tier this check belongs to per
    /// L1/SCHEMA §4.1. Used to route verification at the CI gate.
    pub(crate) tier: &'static str,
}

/// M12: Run the substrate's comprehensive integrity checks ad-hoc.
///
/// Runs the same checks as boot-time C9 (substrate_id_well_formed,
/// cycle_counter_monotonic, dag_verify_all, canonical_bytes_render_drift,
/// substrate_state_orphan_detected, silent_internal_mortality,
/// genesis_event_uniqueness, manifest_cycle_vs_dag_advance_count). For each
/// failing check, emits a new C9 immune sporocarp. Always returns a structured
/// report regardless of outcome.
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
            } else if result.check_id == "silent_internal_mortality" {
                (
                    "C55_silent_internal_mortality",
                    "silent_internal_mortality".to_string(),
                )
            } else if result.check_id == "genesis_event_uniqueness" {
                (
                    "C57_genesis_event_non_unique",
                    "genesis_event_non_unique".to_string(),
                )
            } else if result.check_id == "manifest_cycle_vs_dag_advance_count" {
                (
                    "C59_manifest_cycle_vs_dag_advance_mismatch",
                    "manifest_cycle_vs_dag_advance_mismatch".to_string(),
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
/// **v0.9 keyless**: the `pinned_pubkey_well_formed` and `owner_keys_consistency`
/// checks were removed with the owner-key + anchor surface (there is no pinned
/// operator identity and no owner key to cross-validate). The live checks are:
/// 1. `substrate_id_well_formed`, substrate_id is non-zero
/// 2. `cycle_counter_monotonic`, cycle_counter ≥ max(DAG node at_cycle)
/// 3. `dag_verify_all`, every DAG node's hash recomputes correctly
/// 4. `canonical_bytes_render_drift`, C18 substrate-generated nodes round-trip
/// 5. `substrate_state_orphan_detected`, C19/C32 live↔DAG reconciliation
/// 6. `silent_internal_mortality`, C55 orphan-without-tombstone detection
/// 7. `genesis_event_uniqueness`, C57 at most one genesis_event
/// 8. `manifest_cycle_vs_dag_advance_count`, C59 cycle-counter vs DAG advances
///
/// Returns a vec of results. Caller emits a C9 immune sporocarp for each failure.
pub(crate) fn run_integrity_checks(state: &ServerState) -> Vec<IntegrityCheckResult> {
    let mut results = Vec::new();

    // 1. substrate_id well-formed.
    // **M-anchor-4**: witness inputs = {substrate_id: Bytes(32)}. Owner re-checks
    // by asserting non-zero.
    let substrate_id_zero = state.substrate_id().iter().all(|b| *b == 0);
    let witness_inputs_substrate_id = {
        let mut m = BTreeMap::new();
        m.insert(
            "substrate_id".to_string(),
            Value::Bytes(state.substrate_id().to_vec()),
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
    let monotonic = state.cycle_counter() >= max_dag_cycle;
    let witness_inputs_cycle_monotonic = {
        let mut m = BTreeMap::new();
        m.insert(
            "manifest_cycle_counter".to_string(),
            Value::Uint(state.cycle_counter()),
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
                state.cycle_counter(), max_dag_cycle
            )
        } else {
            format!(
                "manifest.cycle_counter={} < max(DAG.at_cycle)={} (manifest may have rolled back)",
                state.cycle_counter(), max_dag_cycle
            )
        },
        witness_inputs_canonical_bytes: witness_inputs_cycle_monotonic,
        tier: "tier_1",
    });

    // 3. (REMOVED v0.9) pinned_pubkey_well_formed, there is no pinned operator
    //    identity in the keyless build, so there is no pinned pubkey to check.

    // 4. DAG.verify_all(), every node's hash recomputes correctly.
    // **M-anchor-4 §9.3.5**: witness inputs include {node_count, dag_tip_hash}.
    // For tier-2 sampled re-verification (deferred), the CI gate derives sample
    // indices from a substrate/DAG-tip-derived seed and pulls (hash,
    // parent_hashes, content_hash) tuples for those indices via the existing
    // enumerate_dag_since RPC. The witness here is the SUFFICIENT INPUT to know
    // which leaves to sample + check. (keyless; acknowledged-debt: no external
    // anchor-minted nonce, the sampling seed is substrate/DAG-tip-derived.)
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

    // 5. (REMOVED v0.9) owner_keys_consistency, there is no owner key and no
    //    pinned operator pubkey in the keyless build, so there is nothing to
    //    cross-validate. The old check was an unconditional `passed: true`
    //    placeholder describing retired owner-key vs pinned-pubkey
    //    cross-validation; it is deleted rather than left lying.

    // 6. M19 P9 皮肤 / L1/HARD_RULES C18 canonical_bytes_render_drift:
    //    decode each DAG node's content_canonical_bytes, re-encode, and compare.
    //    Any divergence indicates canonical-bytes rendering is non-deterministic
    //    (e.g., map keys not sorted, repr drift, integer encoding inconsistency)
    //   , a CRITICAL skin breach that would let an attacker present the same
    //    semantic content with different byte sequences.
    //
    //    M19-MV scope: scan substrate-self-generated DAG nodes. Operator-
    //    supplied content (mutation:*) is opaque to the substrate, the
    //    operator chooses the encoding, so we skip those nodes. Substrate-
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
    //    fields (substrate_id, genesis_time, cycle_counter, last_absorbed_cycle)
    //    can be derived from DAG events. Python-owned state (gradient) is
    //    deferred to M21.3 when Python becomes a derived-view consumer. (v0.9
    //    keyless: the pinned_operator_identity + nonce_log reconciliations were
    //    removed with the owner-key + anchor surface.)
    let (orphan_passed, orphan_evidence) = check_substrate_state_orphans(state);
    // **M-anchor-4**: witness inputs = {substrate_id, manifest_cycle, dag_node_count}.
    // Owner re-runs DerivedState::from_dag and compares against these values.
    let witness_inputs_orphan = {
        let mut m = BTreeMap::new();
        m.insert(
            "substrate_id".to_string(),
            Value::Bytes(state.substrate_id().to_vec()),
        );
        m.insert(
            "manifest_cycle_counter".to_string(),
            Value::Uint(state.cycle_counter()),
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

    // 8. **v3.1.1 P07 §3.3 / L1/HARD_RULES §1.4 C55 silent_internal_mortality**:
    //    every graph-orphan past the prune grace window MUST have a
    //    corresponding `internal_mortality_event:*` tombstone in the DAG
    //    referencing it as `killed_part_hash`. An orphan without a tombstone
    //    means a part was logically retired without the audit trail P07
    //    §3.3 mandates, silent removal, forbidden.
    //
    //    Under healthy substrate operation the prune-scan deep-cycle step
    //    catches all such orphans every PRUNE_SCAN_DEEP_CYCLE_INTERVAL
    //    cycles, so this check stays quiet. It fires only when prune-scan
    //    has been broken/disabled or a rule has a bug that lets a candidate
    //    slip through.
    let (silent_mortality_passed, silent_mortality_evidence, silent_mortality_witness) =
        check_silent_internal_mortality(state);
    results.push(IntegrityCheckResult {
        check_id: "silent_internal_mortality".to_string(),
        passed: silent_mortality_passed,
        evidence: silent_mortality_evidence,
        witness_inputs_canonical_bytes: silent_mortality_witness,
        tier: "tier_1",
    });

    // 9. **v3.1.1 Sprint 5.C / C57 genesis_event_non_unique**, the DAG MUST
    //    contain at most one `genesis_event:*` node. Multiple genesis events
    //    indicate a boot-time ambiguity: either the substrate booted twice
    //    against the same state_dir without proper genesis-already-present
    //    detection, or a DAG corruption let two genesis events through. Either
    //    way the substrate identity is unstable, refuse to operate silently.
    //    Per P06 §3.5: every causal chain has exactly one root.
    let (genesis_passed, genesis_evidence, genesis_witness) =
        check_genesis_event_uniqueness(state);
    results.push(IntegrityCheckResult {
        check_id: "genesis_event_uniqueness".to_string(),
        passed: genesis_passed,
        evidence: genesis_evidence,
        witness_inputs_canonical_bytes: genesis_witness,
        tier: "tier_1",
    });

    // 10. (REMOVED v0.9) C58 owner_pubkey_dag_pin_inconsistent, there is no
    //     pinned operator identity and no owner_key_initialized event in the
    //     keyless build, so there is nothing to cross-check.

    // 11. **v3.1.1 Sprint 5.C / C59 manifest_cycle_vs_dag_advance_mismatch**,
    //     manifest.cycle_counter SHOULD equal the count of `cycle_advanced`
    //     DAG events (with tolerance of ±1 to account for the pre-first-cycle
    //     genesis substrate). Mismatch beyond tolerance indicates either
    //     manifest tamper (cycle_counter advanced without DAG emission, silent
    //     mutation, P06 violation) or DAG truncation (cycle_advanced events
    //     removed, retro-edit). Either is a boot-time correctness alarm.
    let (cycle_count_passed, cycle_count_evidence, cycle_count_witness) =
        check_manifest_cycle_vs_dag_advance_count(state);
    results.push(IntegrityCheckResult {
        check_id: "manifest_cycle_vs_dag_advance_count".to_string(),
        passed: cycle_count_passed,
        evidence: cycle_count_evidence,
        witness_inputs_canonical_bytes: cycle_count_witness,
        tier: "tier_1",
    });

    results
}

// ---------------------------------------------------------------------------
// **v3.1.1 Sprint 5.C**, new cross-file consistency checks (C57/C58/C59).
// ---------------------------------------------------------------------------

/// **C57 genesis_event_uniqueness**, DAG must contain at most one
/// `genesis_event:*` node.
fn check_genesis_event_uniqueness(state: &ServerState) -> (bool, String, Vec<u8>) {
    let mut count: u64 = 0;
    let mut first_hash_hex = String::new();
    for node in state.dag.iter_in_insertion_order() {
        if node
            .node_type
            .starts_with(crate::events::NODE_TYPE_GENESIS_PREFIX)
        {
            count += 1;
            if count == 1 {
                first_hash_hex = hex_encode(node.hash.as_ref());
            }
        }
    }
    let witness = {
        let mut m = BTreeMap::new();
        m.insert("genesis_event_count".to_string(), Value::Uint(count));
        m.insert(
            "first_genesis_event_hash".to_string(),
            Value::String(first_hash_hex.clone()),
        );
        cb_encode(&Value::Map(m))
            .map(|cb| cb.0)
            .unwrap_or_default()
    };
    if count <= 1 {
        (true, format!("ok ({count} genesis_event:* in DAG)"), witness)
    } else {
        (
            false,
            format!(
                "DAG contains {count} genesis_event:* nodes; expected ≤ 1 (P06 §3.5 \
                 root-of-causal-chain uniqueness violated)"
            ),
            witness,
        )
    }
}

/// **C59 manifest_cycle_vs_dag_advance_count**, sum the spans of cycle_advanced
/// events (Σ `new_cycle − prior_cycle`) and compare to manifest.cycle_counter;
/// ±1 tolerance for the pre-first-cycle genesis case.
///
/// **P04 §3.1 batch-summarized advance**: a single `cycle_advanced` node may
/// span more than one cycle (a provably-inert idle cultivar batch-summarizes
/// its no-op heartbeats into one node `prior → prior+N`). The metabolic-
/// position invariant is therefore the SUM OF SPANS == cycle_counter, NOT the
/// node COUNT (which would undercount any batched run). Backward-compatible: a
/// pre-batch node spans exactly 1 (`new = prior + 1`), so the sum equals the
/// old count for every legacy DAG. A node whose content cannot be decoded as
/// `{prior_cycle, new_cycle}` conservatively contributes a span of 1 (the
/// legacy per-node assumption).
fn check_manifest_cycle_vs_dag_advance_count(
    state: &ServerState,
) -> (bool, String, Vec<u8>) {
    let advance_span_sum: u64 = state
        .dag
        .iter_in_insertion_order()
        .filter(|n| n.node_type == crate::events::NODE_TYPE_CYCLE_ADVANCED)
        .map(|n| decode_cycle_advanced_span(n).unwrap_or(1))
        .fold(0u64, |acc, span| acc.saturating_add(span));
    let counter = state.cycle_counter();
    let diff = counter.abs_diff(advance_span_sum);
    let passed = diff <= 1;
    let witness = {
        let mut m = BTreeMap::new();
        m.insert(
            "manifest_cycle_counter".to_string(),
            Value::Uint(counter),
        );
        m.insert(
            "dag_cycle_advanced_span_sum".to_string(),
            Value::Uint(advance_span_sum),
        );
        cb_encode(&Value::Map(m))
            .map(|cb| cb.0)
            .unwrap_or_default()
    };
    if passed {
        (
            true,
            format!(
                "ok (manifest_cycle_counter={counter}, dag_cycle_advanced_span_sum={advance_span_sum})"
            ),
            witness,
        )
    } else {
        (
            false,
            format!(
                "manifest_cycle_counter={counter} but DAG cycle_advanced spans sum to \
                 {advance_span_sum} (diff={diff}, exceeds tolerance 1; either manifest mutated \
                 without DAG emission or DAG truncated)"
            ),
            witness,
        )
    }
}

/// Decode a `cycle_advanced` node's span (`new_cycle − prior_cycle`). Returns
/// `None` if the content is not the expected `{prior_cycle, new_cycle}` map;
/// C59 then treats the node as the legacy span of 1. Decodes identically to
/// `derived_state::apply_cycle_advanced` (same canonical-bytes map fields).
fn decode_cycle_advanced_span(node: &myco_kernel_schema::dag::DagNode) -> Option<u64> {
    let decoded = cb_decode(node.content_canonical_bytes.as_ref()).ok()?;
    let map = match decoded {
        Value::Map(m) => m,
        _ => return None,
    };
    let prior = match map.get("prior_cycle")? {
        Value::Uint(u) => *u,
        _ => return None,
    };
    let new = match map.get("new_cycle")? {
        Value::Uint(u) => *u,
        _ => return None,
    };
    Some(new.saturating_sub(prior))
}

/// **v3.1.1 C55 silent_internal_mortality** detection.
///
/// Returns `(passed, evidence, witness_inputs_canonical_bytes)`. Passes iff
/// every graph-orphan past `prune::ORPHAN_GRACE_CYCLES` has a corresponding
/// `internal_mortality_event:*` tombstone in the DAG that references the
/// orphan's hash as `killed_part_hash`.
///
/// Algorithm:
/// 1. Build set of all hashes referenced by some node's `parent_hashes`.
/// 2. Build set of all `killed_part_hash` values from existing tombstones.
/// 3. For each DAG node past grace window that is (a) not referenced by
///    any later node AND (b) not the current tip AND (c) not in the P10
///    invariant-protected set AND (d) not itself a tombstone, check if it
///    appears in the tombstone-killed-set. If not, it is a C55 violation.
fn check_silent_internal_mortality(
    state: &ServerState,
) -> (bool, String, Vec<u8>) {
    use std::collections::HashSet;

    use myco_kernel_shared::canonical_bytes::{decode as cb_decode, Value as CbValue};

    let current_cycle = state.cycle_counter();

    // Build referenced-by-anyone set.
    let mut referenced: HashSet<[u8; 32]> = HashSet::new();
    for node in state.dag.iter_in_insertion_order() {
        for parent in &node.parent_hashes {
            let arr: [u8; 32] = parent
                .as_ref()
                .try_into()
                .expect("NodeHash is 32 bytes");
            referenced.insert(arr);
        }
    }

    let tip_bytes: Option<[u8; 32]> = state
        .dag
        .tip()
        .map(|h| h.as_ref().try_into().expect("NodeHash is 32 bytes"));

    // Build tombstone-killed set: for each internal_mortality_event:* node,
    // decode its content and extract the `killed_part_hash` field. Add to
    // killed-set.
    let mut tombstoned: HashSet<[u8; 32]> = HashSet::new();
    for node in state.dag.iter_in_insertion_order() {
        if !node
            .node_type
            .starts_with(crate::events::NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX)
        {
            continue;
        }
        let content = node.content_canonical_bytes.as_ref();
        let decoded = match cb_decode(content) {
            Ok(v) => v,
            Err(_) => continue, // malformed tombstone, skipped here; would
                                // be a C18 finding via the canonical_bytes
                                // round-trip check.
        };
        if let CbValue::Map(m) = decoded {
            if let Some(CbValue::Bytes(b)) = m.get("killed_part_hash") {
                if b.len() == 32 {
                    let mut arr = [0u8; 32];
                    arr.copy_from_slice(b);
                    tombstoned.insert(arr);
                }
            }
        }
    }

    // Identify violations: graph-orphan past grace, not protected, not a
    // tombstone itself, not in tombstoned-set.
    let cutoff_cycle = current_cycle.saturating_sub(crate::prune::ORPHAN_GRACE_CYCLES);
    let mut violations: Vec<(String, [u8; 32], u64)> = Vec::new();
    if current_cycle > crate::prune::ORPHAN_GRACE_CYCLES {
        for node in state.dag.iter_in_insertion_order() {
            if node.created_at_cycle > cutoff_cycle {
                continue;
            }
            // Tombstones themselves are not subject to C55 (they are the
            // audit trail, not orphans of substrate state).
            if node
                .node_type
                .starts_with(crate::events::NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX)
            {
                continue;
            }
            // P10 invariant-protected, never 应朽, so never expected to
            // have a tombstone. Shared SSoT with the prune-scan rules.
            if crate::prune::is_p10_invariant_protected(&node.node_type) {
                continue;
            }
            let hash_bytes: [u8; 32] = node
                .hash
                .as_ref()
                .try_into()
                .expect("NodeHash is 32 bytes");
            if Some(hash_bytes) == tip_bytes {
                continue;
            }
            if referenced.contains(&hash_bytes) {
                continue;
            }
            // This is a graph orphan past grace. Is it tombstoned?
            if tombstoned.contains(&hash_bytes) {
                continue;
            }
            violations.push((node.node_type.clone(), hash_bytes, node.created_at_cycle));
        }
    }

    let passed = violations.is_empty();
    let evidence = if passed {
        format!(
            "ok (cycle {current_cycle}; all graph-orphans past {grace}-cycle grace have internal_mortality tombstones — no silent prune detected; {tombstone_count} tombstones in DAG)",
            grace = crate::prune::ORPHAN_GRACE_CYCLES,
            tombstone_count = tombstoned.len()
        )
    } else {
        let example = &violations[0];
        format!(
            "{} silent prune(s) detected — orphan parts past grace with NO internal_mortality_event tombstone. Example: node_type={:?} hash={} created_at_cycle={}",
            violations.len(),
            example.0,
            hex_encode(&example.1),
            example.2
        )
    };

    // Witness inputs: violation count + first violation hash (if any) +
    // current cycle. Owner can re-run the same check on enumerated DAG
    // nodes and reproduce.
    let witness = {
        let mut m = BTreeMap::new();
        m.insert(
            "violation_count".to_string(),
            Value::Uint(violations.len() as u64),
        );
        m.insert(
            "current_cycle".to_string(),
            Value::Uint(current_cycle),
        );
        m.insert(
            "grace_cycles".to_string(),
            Value::Uint(crate::prune::ORPHAN_GRACE_CYCLES),
        );
        if let Some(first) = violations.first() {
            m.insert(
                "first_violation_hash".to_string(),
                Value::Bytes(first.1.to_vec()),
            );
            m.insert(
                "first_violation_node_type".to_string(),
                Value::String(first.0.clone()),
            );
        }
        cb_encode(&Value::Map(m)).map(|cb| cb.0).unwrap_or_default()
    };

    (passed, evidence, witness)
}

/// **M-anchor-4 §9.3.4**: emit `invariant_witness:{check_id}` DAG events
/// for each integrity check result. Witnesses are emitted REGARDLESS of
/// pass/fail per doctrine, the substrate provides raw inputs; the owner
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
    let at_cycle = state.cycle_counter();
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
            // No structured inputs, skip emission.
            continue;
        }
        if already_witnessed.contains(&result.check_id) {
            // Same cycle, already witnessed, skip.
            continue;
        }
        let body = crate::events::encode_invariant_witness(
            &result.check_id,
            result.tier,
            at_cycle,
            at_unix_ns,
            &result.witness_inputs_canonical_bytes,
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
/// What this checks (live values read via the Task #8i discrete-field
/// accessors `state.substrate_id()` / `genesis_time_unix_ns()` /
/// `cycle_counter()` / `last_absorbed_cycle()`; the legacy `manifest` mirror
/// no longer exists):
/// - substrate_id: live state.substrate_id() == derived.substrate_id
/// - genesis_time_unix_ns: live state.genesis_time_unix_ns() == derived.genesis_time_unix_ns
/// - cycle_counter: live state.cycle_counter() == derived.cycle_counter
/// - last_absorbed_cycle: live state.last_absorbed_cycle() == derived.last_absorbed_cycle
///
/// (v0.9 keyless: the nonce_log + pinned_operator_identity reconciliations were
/// removed with the owner-key + anchor surface.)
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
    // genesis_event in DAG, this is exactly the M21.1 migration condition
    // (existing substrates pre-M21 have no genesis_event). To avoid false
    // positives during migration, we ONLY report divergence when derived
    // HAS substrate_id and it differs from live.
    if let Some(d_id) = derived.substrate_id {
        if d_id != state.substrate_id() {
            divergences.push(format!(
                "substrate_id mismatch: live={}, derived={}",
                hex_encode(&state.substrate_id()),
                hex_encode(&d_id)
            ));
        }
    }

    // genesis_time: same migration-friendly check.
    if let Some(d_time) = derived.genesis_time_unix_ns {
        if d_time != state.genesis_time_unix_ns() {
            divergences.push(format!(
                "genesis_time_unix_ns mismatch: live={}, derived={}",
                state.genesis_time_unix_ns(), d_time
            ));
        }
    }

    // cycle_counter: this is INCREMENTED in the dispatch arm AFTER handle_advance
    // returns, but the cycle_advanced event is emitted from inside the dispatch
    // arm too. So derived.cycle_counter should EQUAL live.cycle_counter after
    // an advance. For pre-M21 manifests that never emitted cycle_advanced, the
    // derived value will be 0 while live can be > 0, only report divergence
    // when derived.cycle_counter > 0 OR (derived.substrate_id is Some, i.e. we
    // have a genesis event and thus the substrate is post-M21).
    if (derived.cycle_counter > 0 || derived.substrate_id.is_some())
        && derived.cycle_counter != state.cycle_counter()
    {
        divergences.push(format!(
            "cycle_counter mismatch: live={}, derived={}",
            state.cycle_counter(), derived.cycle_counter
        ));
    }

    // last_absorbed_cycle: derived from absorption_event events (already in DAG
    // since M18). Should always match.
    if derived.last_absorbed_cycle != state.last_absorbed_cycle() {
        // BUT: absorption_event was added in M18; pre-M21 last_absorbed_cycle
        // tracking is via manifest only. Migration tolerance:
        // - derived is Some → strict match required
        // - derived is None → tolerate live Some (legacy)
        if derived.last_absorbed_cycle.is_some() {
            divergences.push(format!(
                "last_absorbed_cycle mismatch: live={:?}, derived={:?}",
                state.last_absorbed_cycle(), derived.last_absorbed_cycle
            ));
        }
    }

    // (v0.9 keyless removal: the pinned_operator_identity live↔derived
    // reconciliation AND the nonce_log entry-by-entry reconciliation were
    // removed with the owner-key + anchor surface, neither side carries a
    // pinned identity or a nonce ledger.)

    if divergences.is_empty() {
        (
            true,
            "ok (Rust-side identity / metabolic-position state fully derivable from DAG)"
                .to_string(),
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

#[cfg(test)]
mod tests {
    //! **Phase ③, P05 negative exact-polarity witness.**
    //!
    //! The shipped C32 (`substrate_state_orphan_detected`) is the live-state ↔
    //! DAG-derived reconciler: every Rust-side ServerState record MUST be
    //! re-derivable from the active-tier DAG; a live record with no causal DAG
    //! root is an "active-tier orphan" (detached, unreachable-from-tip live
    //! tissue) per P05 §3.2.
    //!
    //! This witness lives at the lib level (NOT in `substrate/tests/`) by
    //! necessity: a post-M21 substrate boots EVERY reconciled field
    //! (identity / cycle_counter / last_absorbed_cycle) FROM the DAG itself, so
    //! live and derived are sourced from the same graph and can never diverge
    //! through external-file tampering, the e2e operator surface cannot induce
    //! the divergence. We therefore construct a `ServerState` whose live
    //! `cycle_counter` exceeds what the DAG derives, and drive the REAL detector
    //! (`check_substrate_state_orphans` + the `handle_run_immune_check`
    //! C32-emission path) with exact negative polarity. This is byte-neutral
    //! (`#[cfg(test)]`, excluded from release) and changes no detector logic.
    //!
    //! **v0.9 keyless**: the original negative witness injected a live `nonce_log`
    //! entry with no DAG `nonce_issued` event. The attestation-nonce ledger was
    //! removed with the owner-key + anchor surface, so the witness now induces a
    //! `cycle_counter` orphan instead, an equivalent live↔DAG divergence that
    //! exercises the same reconciler + C32-emission path.

    use super::*;
    use crate::persistence::Manifest;
    use crate::server::ServerState;
    use myco_kernel_schema::dag::Dag;

    /// Build a `ServerState` over a DAG whose genesis_event carries the SAME
    /// identity the live state is constructed with, so the ONLY divergence the
    /// tests induce is the one under test (no spurious substrate_id mismatch).
    /// `live_cycle_counter` lets a test set the live counter independently of the
    /// DAG (whose only event is the genesis at cycle 0 → derived.cycle_counter=0).
    fn state_with_matching_genesis(live_cycle_counter: u64) -> ServerState {
        let g = Manifest::genesis();
        let mut dag = Dag::new();
        let genesis_content =
            crate::events::encode_genesis_event(&g.substrate_id, g.genesis_time_unix_ns, 0);
        let nt = crate::events::genesis_event_node_type(&g.substrate_id);
        dag.insert_node(Vec::new(), nt, 0, genesis_content)
            .expect("insert genesis_event");
        let state_dir = std::env::temp_dir().join(format!(
            "myco-integrity-orphan-test-{}-{:p}",
            std::process::id(),
            &g as *const _
        ));
        ServerState::new(
            state_dir,
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            live_cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            dag,
            [0u8; 32],
        )
    }

    fn count_immune(state: &ServerState, prefix: &str) -> usize {
        state
            .dag
            .iter_in_insertion_order()
            .filter(|n| n.node_type.starts_with(prefix))
            .count()
    }

    #[test]
    fn p05_negative_clean_substrate_passes_orphan_check() {
        // **Positive control**: a substrate whose live state is fully derivable
        // from its DAG (live cycle_counter == derived 0; no injected orphan) MUST
        // pass the orphan reconciler, so the negative test below proves
        // DETECTION, not a tautology.
        let state = state_with_matching_genesis(0);
        let (passed, evidence) = check_substrate_state_orphans(&state);
        assert!(
            passed,
            "P05: a clean DAG-derivable substrate must pass the orphan check; \
             got fail: {evidence}"
        );
    }

    #[test]
    fn p05_negative_active_tier_orphan_nonce_fires_c32() {
        // NOTE (keyless v3.1.5): this fn keeps the sealed-L0 witness name (the P05
        // card `negative:` field references "orphan_nonce"). After the keyless
        // nonce-ledger retirement there is no nonce orphan to inject, so the
        // scenario is re-grounded on an equivalent active-tier orphan (a live
        // cycle_counter with no cycle_advanced DAG events) that fires the SAME C32
        // check. The witness name will be renamed to match at the next L0 reseal;
        // until then the sealed name is the binding contract.
        // **P05 §3.2 negative witness**: build a substrate whose LIVE
        // cycle_counter (5) has no corresponding `cycle_advanced` events in the
        // active-tier DAG (which derives cycle_counter=0 from the lone genesis
        // event) → an orphaned live record. The reconciler MUST flag it, and the
        // ad-hoc immune-check path MUST emit the C32_substrate_state_orphan_detected
        // sporocarp.
        let mut state = state_with_matching_genesis(5);

        // (1) The reconciler itself flags the divergence (the detector's verdict).
        let (passed, evidence) = check_substrate_state_orphans(&state);
        assert!(
            !passed,
            "P05 §3.2 violated: a live cycle_counter with no cycle_advanced DAG \
             events is an active-tier orphan; the reconciler MUST fail"
        );
        assert!(
            evidence.to_lowercase().contains("cycle_counter"),
            "P05 §3.2: orphan evidence should name the orphaned cycle_counter; got: {evidence}"
        );

        // (2) The operator-driven immune-check path emits the C32 sporocarp.
        let req = Message::new(msg_type::RUN_IMMUNE_CHECK, 1, BTreeMap::new());
        let resp = handle_run_immune_check(&mut state, &req)
            .expect("run_immune_check ok")
            .expect("response present");
        let failed = match resp.payload.get("failed_checks") {
            Some(Value::Uint(n)) => *n,
            _ => panic!("failed_checks missing"),
        };
        assert!(failed >= 1, "P05 §3.2: at least the orphan check must fail");
        assert_eq!(
            count_immune(&state, "immune:C32_substrate_state_orphan_detected"),
            1,
            "P05 §3.2 violated: detected active-tier orphan MUST emit exactly one \
             C32_substrate_state_orphan_detected immune sporocarp"
        );
    }
}
