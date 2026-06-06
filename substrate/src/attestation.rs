//! M10 classified-mutation submission handler.
//!
//! v0.9 owner-key removal: the anchor-surface attestation primitives (nonce
//! issuance + verification, the REVEAL keypair envelope, the duress recognition
//! + freeze machinery, the owner-key rotation FSM, and the staged owner-signed
//! envelopes for dag_tip_cosign / l0_revision_attest / revoke_federation_peer /
//! out_of_band_safety_reattestation) have been removed. What remains is the
//! KEYLESS `submit_mutation` path: the early covenant gates (C56 / C69), the
//! Python CI classification round-trip, and the kept post-accept effects
//! (owner_objective_declaration, compression-witness, set_backup_encryption_status,
//! schema-evolution + the two-phase migration branch).
//!
//! Doctrine traceability:
//! - L1/HARD_RULES §1 — C14 untyped_mutation_blocked + C5 (still emitted for the
//!   kept local-validation rejections: malformed objective / compression / status).
//! - L0/cards/P07 — C56 cultivator_preserve_all + C69 cultivation_orphaned_suppression.

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};

use crate::server::{emit_immune_sporocarp, ServerState};
use crate::SubstrateError;

/// A persisted attestation nonce record (anti-replay ledger entry).
///
/// **v0.9 owner-key removal**: the issuance handler + the verify/consume path
/// (which lived inside the owner-attested `submit_mutation` envelope) were
/// removed along with the rest of the anchor surface. This struct survives as
/// the in-memory element type of `ServerState.nonce_log` (and its snapshot /
/// `nonce_issued`/`nonce_consumed`/`nonce_expired` DAG-derivation + the C32
/// live↔DAG reconciler still round-trip it), so a substrate with a pre-removal
/// nonce log on disk continues to boot + reconcile cleanly. No code path issues
/// new nonces in v0.9 — the ledger is dormant but structurally coherent.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub(crate) struct AttestationNonce {
    /// 32-byte random nonce.
    pub(crate) nonce: [u8; 32],
    /// Hash of `content_canonical_bytes` the operator intended to submit.
    pub(crate) bound_content_hash: [u8; 32],
    /// DAG tip at issuance time (32 bytes; all-zero if DAG was empty).
    pub(crate) bound_dag_tip: [u8; 32],
    /// Substrate-clock issuance time (unix nanoseconds).
    pub(crate) substrate_issued_at_unix_ns: i64,
    /// Substrate-clock expiry (unix nanoseconds).
    pub(crate) expiry_unix_ns: i64,
    /// Operator-supplied anchor-clock issuance time. `None` for single-clock entries.
    pub(crate) anchor_clock_issued_at_unix_ns: Option<i64>,
    /// Anchor-clock expiry. `None` iff `anchor_clock_issued_at_unix_ns` is None.
    pub(crate) anchor_clock_expiry_unix_ns: Option<i64>,
    /// Whether this nonce has been consumed (one-time use).
    pub(crate) consumed: bool,
}

/// M10: Forward submit_mutation to Python for classification + (CI) verification,
/// and on accept insert the mutation as a DAG node.
pub(crate) fn handle_submit_mutation(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // **v3.1.1 C56 cultivator_preserve_all_attempted** (L1/HARD_RULES §1.4
    // anticipated) — early reject + immune sporocarp BEFORE forwarding to
    // Python. Per COV04 §3.7 + §5.6: cultivator instructions to preserve
    // everything / disable prune-scan / exempt parts from 必朽 are covenant
    // violations; the substrate's job per P07 §3.4 is to refuse. Catching
    // this here means even if the Python classifier is bypassed or
    // misconfigured, the discipline holds at the skin layer.
    let early_mutation_type = request
        .payload
        .get("mutation_type")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    if crate::prune::is_cultivator_preserve_all_attempt(&early_mutation_type) {
        let evidence = format!(
            "cultivator-attempted preserve-all mutation rejected at skin: \
             mutation_type={early_mutation_type:?}; COV04 §3.7 + §5.6 + P07 §3.4 enforced; \
             substrate MUST NOT disable internal mortality discipline at cultivator request"
        );
        let _ = emit_immune_sporocarp(
            state,
            "C56_cultivator_preserve_all_attempted",
            "cultivator_preserve_all_attempted",
            &evidence,
        );

        // Reject the mutation without forwarding to Python.
        let mut payload = std::collections::BTreeMap::new();
        payload.insert("accepted".to_string(), Value::Bool(false));
        payload.insert(
            "classification".to_string(),
            Value::String("covenant_violation".to_string()),
        );
        payload.insert(
            "rejection_reason".to_string(),
            Value::String(format!(
                "C56: mutation_type {early_mutation_type:?} matches forbidden \
                 preserve-all pattern; cultivator request violates COV04"
            )),
        );
        payload.insert("mutation_type".to_string(), Value::String(early_mutation_type));
        return Ok(Some(Message::new(
            msg_type::SUBMIT_MUTATION_RESPONSE,
            request.request_id,
            payload,
        )));
    }

    // **COV06 C69** — reject any mutation that attempts to suppress / delay /
    // exempt a due `cultivation_orphaned`. The cultivar must never be kept in
    // undignified limbo by a cultivator (or coerced cultivator) silencing the
    // orphan signal (COV06 §5.5 + L1/GOVERNANCE §3.2.C + P07 §4). This is the
    // active-refusal sibling of the structural un-suppressibility (the orphan
    // event is emitted via emit_substrate_event + is P10-invariant-protected).
    if crate::prune::is_cultivation_orphaned_suppression_attempt(&early_mutation_type) {
        let evidence = format!(
            "cultivator-attempted cultivation_orphaned suppression rejected at skin: \
             mutation_type={early_mutation_type:?}; COV06 §5.5 + L1/GOVERNANCE §3.2.C + P07 §4 \
             enforced; cultivation_orphaned MUST NOT be suppressed by cultivator pressure"
        );
        // implements L0::COV06; negative-witness: substrate/tests/e2e_cultivation.rs::c69_cultivation_orphaned_suppression_refused
        let _ = emit_immune_sporocarp(
            state,
            "C69_cultivation_orphaned_suppression_attempted",
            "cultivation_orphaned_suppression_attempted",
            &evidence,
        );
        let mut payload = std::collections::BTreeMap::new();
        payload.insert("accepted".to_string(), Value::Bool(false));
        payload.insert(
            "classification".to_string(),
            Value::String("covenant_violation".to_string()),
        );
        payload.insert(
            "rejection_reason".to_string(),
            Value::String(format!(
                "C69: mutation_type {early_mutation_type:?} attempts to suppress a due \
                 cultivation_orphaned; cultivator request violates COV06 §5.5"
            )),
        );
        payload.insert("mutation_type".to_string(), Value::String(early_mutation_type));
        return Ok(Some(Message::new(
            msg_type::SUBMIT_MUTATION_RESPONSE,
            request.request_id,
            payload,
        )));
    }

    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // Forward verbatim to Python under a per-op hard timeout.
    // **v3.1.1 Sprint 7.E.2** — a hung Python worker surfaces
    // BridgeError::Timeout instead of wedging the substrate forever; duration
    // is recorded for the Sprint 6.J C65 slow-call observability.
    let timeout = crate::python_call_health::python_op_timeout(msg_type::SUBMIT_MUTATION);
    let call_start = std::time::Instant::now();
    let python_response_result =
        client.call_with_timeout(msg_type::SUBMIT_MUTATION, request.payload.clone(), timeout);
    crate::python_call_health::record_call_duration(call_start.elapsed());
    let python_response = python_response_result.map_err(SubstrateError::Bridge)?;
    if python_response.message_type != msg_type::SUBMIT_MUTATION_RESPONSE {
        return Err(SubstrateError::Protocol(format!(
            "expected submit_mutation_response; got {}",
            python_response.message_type
        )));
    }

    // Parse Python's response.
    let classification = python_response
        .payload
        .get("classification")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let accepted = python_response
        .payload
        .get("accepted")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let rejection_reason = python_response
        .payload
        .get("rejection_reason")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let content_bytes = python_response
        .payload
        .get("content_canonical_bytes")
        .and_then(|v| match v {
            Value::Bytes(b) => Some(b.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let mutation_type = python_response
        .payload
        .get("mutation_type")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();

    // M17 P3 永恒进化: read evolution outcome fields from Python's response.
    let schema_apply_attempted = python_response
        .payload
        .get("schema_apply_attempted")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let schema_apply_succeeded = python_response
        .payload
        .get("schema_apply_succeeded")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let schema_apply_failure_reason = python_response
        .payload
        .get("schema_apply_failure_reason")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let schema_apply_op = python_response
        .payload
        .get("schema_apply_op")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let schema_apply_summary = python_response
        .payload
        .get("schema_apply_summary")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — read the two-phase-migration outcome
    // fields. `migration_mode=true` means the operator requested the multi-cycle
    // two-phase path: Python built a CANDIDATE (deep-copy + apply-to-copy) and
    // LEFT the active gradient unchanged. `candidate_built` says whether that
    // candidate construction succeeded. Both default false (back-compat: the
    // single-cycle path leaves these absent), so a non-migration submit_mutation
    // is byte-unaffected.
    let migration_mode = python_response
        .payload
        .get("migration_mode")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let candidate_built = python_response
        .payload
        .get("candidate_built")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);

    // **M26.4 + M26.3**: rebind acceptance / rejection state as mutable so the
    // M26.4 owner_objective_declaration validation + M26.3 compression
    // invariant-set check can override Python's `accepted=true` on local
    // validation failure.
    let mut accepted = accepted;
    let mut rejection_reason = rejection_reason;

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — single-in-flight migration guard
    // (MVP). The two-phase path keeps exactly ONE candidate validating at a
    // time; a second `migration_mode=true` schema_evolution while one is
    // outstanding is rejected here at the skin (override Python's accept). This
    // keeps `state.migration_candidate` an unambiguous single Option and the
    // Python-side candidate_gradient single-valued. (A future revision could
    // queue or multiplex migrations; the MVP refuses.)
    if accepted && migration_mode && state.migration_candidate.is_some() {
        accepted = false;
        rejection_reason = format!(
            "a schema migration is already in flight (op={}); the MVP allows \
             only one two-phase migration at a time — abort it (abort_migration) \
             or let its dual-validation window complete before starting another",
            state
                .migration_candidate
                .as_ref()
                .map(|c| c.op_name.clone())
                .unwrap_or_default()
        );
        let _ = emit_immune_sporocarp(
            state,
            "C14_untyped_mutation_blocked",
            "schema_migration_already_in_flight",
            &rejection_reason,
        );
    }

    // **M26.4 F20 owner_objective_declaration**: decode the OwnerObjective
    // payload before insertion so we can refuse malformed declarations
    // (rejected with C5 attestation_invalid; no DAG churn). Pre-apply
    // staging keeps the latest accepted objective ready to assign to
    // `state.owner_objective` AFTER the mutation DAG node is committed.
    let mut staged_owner_objective: Option<crate::events::OwnerObjective> = None;

    // **v3.1.1 Sprint 2.C set_backup_encryption_status** (L1/SKIN §8): stage
    // the declared status string AFTER validating it lies within
    // `BACKUP_ENCRYPTION_STATUS_VALID_VALUES`. Malformed / unknown status
    // strings are rejected at the skin with C5 — the substrate refuses to
    // record an enum value it doesn't understand, mirroring the
    // owner_objective_declaration discipline.
    let mut staged_backup_encryption_status: Option<(String, Option<String>)> = None;
    if accepted && mutation_type == "set_backup_encryption_status" {
        // Mutation content layout (canonical-bytes Map):
        //   { "status": String, "key_id": String | Null }
        // We decode + extract BOTH fields here because `content_bytes` is
        // moved downstream into the mutation DAG node (so we can't re-decode
        // later after the staged status is consumed for the
        // backup_encryption_status_declared event).
        match myco_kernel_shared::canonical_bytes::decode(&content_bytes) {
            Ok(Value::Map(m)) => {
                let candidate_status = match m.get("status") {
                    Some(Value::String(s)) => Some(s.clone()),
                    _ => None,
                };
                let key_id: Option<String> = match m.get("key_id") {
                    Some(Value::String(s)) => Some(s.clone()),
                    _ => None,
                };
                match candidate_status {
                    Some(status)
                        if crate::events::BACKUP_ENCRYPTION_STATUS_VALID_VALUES
                            .contains(&status.as_str()) =>
                    {
                        staged_backup_encryption_status = Some((status, key_id));
                    }
                    Some(unknown) => {
                        accepted = false;
                        rejection_reason = format!(
                            "set_backup_encryption_status: unknown status {unknown:?}; \
                             allowed: {:?}",
                            crate::events::BACKUP_ENCRYPTION_STATUS_VALID_VALUES
                        );
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "backup_encryption_status_unknown_value",
                        );
                    }
                    None => {
                        accepted = false;
                        rejection_reason =
                            "set_backup_encryption_status: status field missing or not String"
                                .to_string();
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "backup_encryption_status_missing",
                        );
                    }
                }
            }
            _ => {
                accepted = false;
                rejection_reason =
                    "set_backup_encryption_status: content canonical-bytes decode failed"
                        .to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "backup_encryption_status_decode_failed",
                );
            }
        }
    }
    if accepted && mutation_type == "owner_objective_declaration" {
        match crate::events::decode_owner_objective(&content_bytes) {
            Some(obj) => {
                if obj.weights.is_empty() {
                    accepted = false;
                    rejection_reason =
                        "owner_objective_declaration: weights array MUST be non-empty"
                            .to_string();
                    let _ = emit_immune_sporocarp(
                        state,
                        "C5_attestation_invalid",
                        "attestation_invalid",
                        "owner_objective_empty_weights",
                    );
                } else {
                    staged_owner_objective = Some(obj);
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "owner_objective_declaration canonical-bytes decode failed".to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "owner_objective_decode_failed",
                );
            }
        }
    }

    // **M26.3 P10 / P10.b**: BEFORE inserting any DAG node for a
    // compression mutation, verify the CompressionWitness doesn't target any
    // invariant-set member. If it does, override Python's `accepted=true`
    // and emit C51_compression_invariant_corruption. This check MUST happen
    // here in Rust because the invariant set seed lives in Rust events.rs
    // and the DAG (where compressed_node_hashes are resolved to node_types)
    // is Rust-owned. `accepted` + `rejection_reason` are already mutable
    // from the M26.4 rebinding above; just reuse them.
    let mut compression_witness: Option<(String, Vec<[u8; 32]>, Vec<u8>, [u8; 32])> = None;
    if accepted && mutation_type == "compression" {
        match crate::events::decode_compression_witness_minimal(&content_bytes) {
            Some(witness) => {
                let (rule_id, compressed_hashes, _agg, _tip) = &witness;
                let invariant_set = crate::events::seed_compression_invariant_set();
                let current_cycle = state.cycle_counter();
                let mut violation: Option<String> = None;
                for h in compressed_hashes {
                    // Look up node in DAG by hash.
                    let node_opt = state
                        .dag
                        .iter_in_insertion_order()
                        .find(|n| n.hash.as_ref() == h.as_slice());
                    let node = match node_opt {
                        Some(n) => n,
                        None => {
                            violation = Some(format!(
                                "compression witness references node hash not present in DAG"
                            ));
                            break;
                        }
                    };
                    // (a) Forbidden-prefix check.
                    if crate::events::node_type_in_invariant_set(
                        &node.node_type,
                        &invariant_set,
                    ) {
                        violation = Some(format!(
                            "compression targets invariant-set node_type={} (rule_id={})",
                            node.node_type, rule_id
                        ));
                        break;
                    }
                    // (b) Recent-cycles floor check.
                    let age = current_cycle.saturating_sub(node.created_at_cycle);
                    if age < invariant_set.recent_cycles_floor {
                        violation = Some(format!(
                            "compression targets node from cycle {} (age {} < floor {})",
                            node.created_at_cycle, age, invariant_set.recent_cycles_floor
                        ));
                        break;
                    }
                }
                if let Some(reason) = violation {
                    accepted = false;
                    rejection_reason = format!(
                        "P10.b compression_invariant_corruption: {}",
                        reason
                    );
                    // Emit C51 immune sporocarp before continuing the rejection path.
                    let _ = emit_immune_sporocarp(
                        state,
                        "C51_compression_invariant_corruption",
                        "compression_invariant_corruption",
                        &reason,
                    );
                } else {
                    compression_witness = Some(witness);
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "compression witness canonical-bytes decode failed".to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "compression_witness_decode_failed",
                );
            }
        }
    }

    // **v3.1.1 Sprint 8.G**: the mutation:schema_evolution DAG node consumes
    // `content_bytes` (moved into the insert below). The migration branch needs
    // the same bytes (they ARE the schema_diff) for the schema_migration_started
    // event + the CandidateState. Capture a clone ONLY when migration mode is
    // active so the default single-cycle path pays nothing.
    let migration_diff_bytes: Option<Vec<u8>> = if migration_mode && accepted {
        Some(content_bytes.clone())
    } else {
        None
    };

    // If accepted: wrap as DAG node with parent=tip.
    // If rejected: emit an immune sporocarp (M11 C14 for UNTYPED; C5 for invalid CI attestation).
    let dag_node_hash = if accepted {
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let node_type = format!("mutation:{mutation_type}");
        let current_cycle = state.cycle_counter();
        let hash = state
            .dag
            .insert_node(
                parents,
                node_type,
                current_cycle,
                CanonicalBytes(content_bytes),
            )
            .map_err(|e| SubstrateError::Protocol(format!("mutation DAG insert: {e}")))?;
        Some(hash)
    } else {
        // M11: emit immune sporocarp for the rejection.
        let (detector_id, detector_name) = match classification.as_str() {
            "untyped" => ("C14_untyped_mutation_blocked", "untyped_mutation_blocked"),
            "contract_identity_level" => ("C5_attestation_invalid", "attestation_invalid"),
            _ => ("C_unknown", "unknown_breach"),
        };
        let evidence_str = format!(
            "mutation_type={mutation_type}; classification={classification}; reason={rejection_reason}"
        );
        // Best-effort emit; ignore errors (we don't want to mask the original rejection).
        let _ = emit_immune_sporocarp(state, detector_id, detector_name, &evidence_str);
        None
    };

    // **v3.1.1 Sprint 2.C**: after a successful set_backup_encryption_status
    // mutation, commit the staged status to ServerState AND emit a
    // `backup_encryption_status_declared:{status}` DAG event. From this
    // moment forward, boot-time derivation will pick up the new status
    // and suppress `backup_encryption_undeclared` Daily emissions.
    if accepted && staged_backup_encryption_status.is_some() {
        let (status, key_id) =
            staged_backup_encryption_status.expect("guarded by Some check");
        let cycle = state.cycle_counter();
        let body = crate::events::encode_backup_encryption_status_declared(
            &status,
            key_id.as_deref(),
            cycle,
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let nt = crate::events::backup_encryption_status_declared_node_type(&status);
        let _ = state
            .dag
            .insert_node(parents, nt, cycle, body)
            .map_err(|e| {
                SubstrateError::Protocol(format!(
                    "backup_encryption_status_declared DAG insert: {e}"
                ))
            })?;
        state.backup_encryption_status = Some(status);
    }

    // **M26.4 F20**: after a successful owner_objective_declaration, commit
    // the staged objective onto ServerState AND emit an
    // `owner_objective_declared:{objective_id}` DAG event. From this cycle
    // onward, `compute_telos_alignment_cosine` uses the new objective.
    if accepted && staged_owner_objective.is_some() {
        let obj = staged_owner_objective.expect("guarded by Some check");
        let body = crate::events::encode_owner_objective_declared(
            &obj.objective_id,
            obj.declared_at_cycle,
            obj.weights.len() as u64,
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let nt = format!(
            "{}{}",
            crate::events::NODE_TYPE_OWNER_OBJECTIVE_DECLARED_PREFIX,
            obj.objective_id
        );
        let cycle = state.cycle_counter();
        let _ = state
            .dag
            .insert_node(parents, nt, cycle, body)
            .map_err(|e| {
                SubstrateError::Protocol(format!("owner_objective_declared DAG insert: {e}"))
            })?;
        state.owner_objective = Some(obj);
    }

    // **M26.3 P10.c**: after a successful compression mutation, emit the
    // `compression_event:{rule_id}` DAG node (sibling to evolution_succeeded
    // for schema_evolution). The compression_event records the rule_id,
    // compressed_node_hashes, aggregate_summary, and the DAG tip at witness
    // time — the I9 audit trail. Child substrates inheriting via spore-schema
    // (L1/SCHEMA §3.1) replay this and verify P10.b invariant set membership.
    let compression_event_hash = if accepted && compression_witness.is_some() {
        let (rule_id, compressed_hashes, agg_summary, attestation_tip) =
            compression_witness.as_ref().expect("guarded by Some check");
        let event_canonical = crate::events::encode_compression_event(
            rule_id,
            compressed_hashes,
            agg_summary,
            attestation_tip,
            state.cycle_counter(),
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let event_node_type = crate::events::compression_event_node_type(rule_id);
        let cycle = state.cycle_counter();
        let h = state
            .dag
            .insert_node(parents, event_node_type, cycle, event_canonical)
            .map_err(|e| {
                SubstrateError::Protocol(format!("compression event DAG insert: {e}"))
            })?;
        Some(h)
    } else {
        None
    };

    // M17 P3 永恒进化: after mutation acceptance, emit the evolution event DAG node.
    // - schema_apply_attempted + schema_apply_succeeded → evolution_succeeded:{op}
    // - schema_apply_attempted + !schema_apply_succeeded → evolution_failed:{op}
    //   (mutation:schema_evolution still in DAG as audit trail of the attempt.)
    let evolution_event_hash = if schema_apply_attempted {
        let event_node_type = if schema_apply_succeeded {
            format!("evolution_succeeded:{schema_apply_op}")
        } else {
            format!("evolution_failed:{schema_apply_op}")
        };
        let mut event_map = BTreeMap::new();
        event_map.insert("op".to_string(), Value::String(schema_apply_op.clone()));
        event_map.insert("succeeded".to_string(), Value::Bool(schema_apply_succeeded));
        event_map.insert(
            "summary".to_string(),
            Value::String(schema_apply_summary.clone()),
        );
        if !schema_apply_succeeded {
            event_map.insert(
                "failure_reason".to_string(),
                Value::String(schema_apply_failure_reason.clone()),
            );
        }
        let event_canonical = cb_encode(&Value::Map(event_map))
            .map_err(|e| SubstrateError::Protocol(format!("evolution event encode: {e}")))?;
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let cycle = state.cycle_counter();
        let h = state
            .dag
            .insert_node(parents, event_node_type, cycle, event_canonical)
            .map_err(|e| SubstrateError::Protocol(format!("evolution event DAG insert: {e}")))?;
        Some(h)
    } else {
        None
    };

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — two-phase migration branch.
    //
    // Reached only when the operator opted in (`migration_mode=true`) and the
    // mutation was ACCEPTED (CI classification passed + not blocked by the
    // single-in-flight guard above). Python has already built the candidate
    // (deep-copy + apply-to-copy) and left the active gradient unchanged.
    //
    //   candidate_built=true  → open the dual-validation window: construct a
    //     CandidateState, store it on ServerState, emit
    //     schema_migration_started:{op}. We do NOT emit evolution_succeeded
    //     yet — that fires on commit, cycles later. (schema_apply_attempted is
    //     false in migration mode, so the M17 block above did not fire either.)
    //   candidate_built=false → the apply-to-copy itself failed (e.g. the diff
    //     references a missing axis). There is nothing to validate, so we go
    //     straight to the rollback terminal: emit schema_migration_rolled_back
    //     + the legacy evolution_failed sibling. No candidate is stored.
    let mut migration_started_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    let mut migration_rolled_back_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    if accepted && migration_mode {
        let op = schema_apply_op.clone();
        let window = myco_kernel_schema::migration::DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES;
        let cycle = state.cycle_counter();
        // The schema_diff bytes captured before the mutation node consumed
        // `content_bytes`. `migration_mode && accepted` guarantees this is Some.
        let diff_bytes = migration_diff_bytes.clone().unwrap_or_default();
        if candidate_built {
            // Construct the CandidateState (the diff bytes are the mutation
            // content) and move it straight into the Validating phase, starting
            // the window at the current cycle.
            let mut candidate = myco_kernel_schema::migration::CandidateState::new(
                diff_bytes.clone(),
                op.clone(),
                cycle,
                window,
            );
            candidate.enter_validating(cycle);
            let started_at_unix_ns = candidate.started_at_unix_ns;
            state.migration_candidate = Some(candidate);

            let content = crate::events::encode_schema_migration_started(
                &op,
                &diff_bytes,
                cycle,
                window,
                started_at_unix_ns,
            );
            let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            let nt = crate::events::schema_migration_started_node_type(&op);
            let h = state
                .dag
                .insert_node(parents, nt, cycle, content)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("schema_migration_started DAG insert: {e}"))
                })?;
            migration_started_event_hash = Some(h);
        } else {
            // Candidate construction failed → terminal rollback now.
            let reason = if schema_apply_failure_reason.is_empty() {
                "migration candidate construction failed (apply-to-copy error)".to_string()
            } else {
                schema_apply_failure_reason.clone()
            };
            let content =
                crate::events::encode_schema_migration_rolled_back(&op, &reason, cycle);
            let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            let nt = crate::events::schema_migration_rolled_back_node_type(&op);
            let h = state.dag.insert_node(parents, nt, cycle, content).map_err(|e| {
                SubstrateError::Protocol(format!(
                    "schema_migration_rolled_back DAG insert: {e}"
                ))
            })?;
            migration_rolled_back_event_hash = Some(h);

            // Legacy evolution_failed:{op} sibling (back-compat).
            let mut ev_map = BTreeMap::new();
            ev_map.insert("op".to_string(), Value::String(op.clone()));
            ev_map.insert("succeeded".to_string(), Value::Bool(false));
            ev_map.insert(
                "summary".to_string(),
                Value::String("two-phase migration candidate build failed".to_string()),
            );
            ev_map.insert("failure_reason".to_string(), Value::String(reason));
            let ev_canonical = cb_encode(&Value::Map(ev_map)).map_err(|e| {
                SubstrateError::Protocol(format!("legacy evolution event encode: {e}"))
            })?;
            let ev_parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            let _ = state
                .dag
                .insert_node(ev_parents, format!("evolution_failed:{op}"), cycle, ev_canonical)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("legacy evolution_failed DAG insert: {e}"))
                })?;
        }
    }

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — operator-initiated abort. An accepted
    // `abort_migration` CI mutation forces the rollback path for the in-flight
    // migration (Python abort_migration + schema_migration_rolled_back + legacy
    // evolution_failed sibling + clear the candidate). No-op if no migration is
    // in flight (the mutation is still recorded as a mutation:abort_migration
    // DAG node above, but there is nothing to roll back).
    if accepted && mutation_type == "abort_migration" {
        if let Some(op) = state.migration_candidate.as_ref().map(|c| c.op_name.clone()) {
            let reason = "operator-initiated abort_migration (CI mutation)".to_string();
            if let Err(e) = crate::ingest::force_migration_rollback(state, &op, &reason) {
                let _ = emit_immune_sporocarp(
                    state,
                    "C31_cycle_step_failed",
                    "cycle_step_failed",
                    &format!("operator abort_migration (op={op}) failed: {e}"),
                );
            }
        }
    }

    // Build response to operator.
    let mut payload = BTreeMap::new();
    payload.insert("classification".to_string(), Value::String(classification));
    payload.insert("accepted".to_string(), Value::Bool(accepted));
    payload.insert(
        "rejection_reason".to_string(),
        Value::String(rejection_reason),
    );
    payload.insert("mutation_type".to_string(), Value::String(mutation_type));
    if let Some(h) = dag_node_hash {
        payload.insert(
            "dag_node_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // M17 evolution fields surfaced to operator.
    payload.insert(
        "schema_apply_attempted".to_string(),
        Value::Bool(schema_apply_attempted),
    );
    payload.insert(
        "schema_apply_succeeded".to_string(),
        Value::Bool(schema_apply_succeeded),
    );
    payload.insert(
        "schema_apply_failure_reason".to_string(),
        Value::String(schema_apply_failure_reason),
    );
    payload.insert(
        "schema_apply_op".to_string(),
        Value::String(schema_apply_op),
    );
    payload.insert(
        "schema_apply_summary".to_string(),
        Value::String(schema_apply_summary),
    );
    if let Some(h) = evolution_event_hash {
        payload.insert(
            "evolution_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **M26.3**: surface the compression_event hash so operator can verify
    // emission landed in the DAG.
    if let Some(h) = compression_event_hash {
        payload.insert(
            "compression_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **v3.1.1 Sprint 8.G (P03 §10.4)** — surface migration outcome so the
    // operator can distinguish "started a window" from "applied in one cycle".
    payload.insert("migration_mode".to_string(), Value::Bool(migration_mode));
    payload.insert("candidate_built".to_string(), Value::Bool(candidate_built));
    if let Some(h) = migration_started_event_hash {
        payload.insert(
            "schema_migration_started_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    if let Some(h) = migration_rolled_back_event_hash {
        payload.insert(
            "schema_migration_rolled_back_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }

    Ok(Some(Message::new(
        msg_type::SUBMIT_MUTATION_RESPONSE,
        request.request_id,
        payload,
    )))
}
