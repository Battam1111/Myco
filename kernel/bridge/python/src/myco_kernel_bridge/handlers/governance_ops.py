"""Governance handler — classify a mutation + verify owner attestation (M10).

``submit_mutation`` is the bridge's policy gate: it classifies an
operator-submitted mutation (daily / contract-identity-level / untyped) via
``kernel/governance``'s classifier, verifies the owner attestation signature
for CI-level mutations (M10/M14 reveal-key path), and — when an accepted
mutation is a ``schema_evolution`` — applies the schema diff to the live
gradient with rollback on failure (M17 P3 永恒进化).

The response echoes the content canonical bytes so the Rust substrate can
wrap the mutation as a DAG node, and carries the evolution-outcome fields so
Rust can emit the matching ``evolution_succeeded`` / ``evolution_failed``
DAG nodes.
"""

from __future__ import annotations

from myco_kernel_governance.canonical_bytes import (
    Bool,
    Bytes as CbBytes,
    CanonicalBytesError,
    Map as CbMap,
    String as CbString,
    expect_array,
    expect_bool,
    expect_bytes,
    expect_string,
)
from myco_kernel_governance.classifier import (
    Classification,
    MutationEnvelope,
    classify,
)
from myco_kernel_governance.crypto import (
    CryptoError,
    verify_signature,
)
from myco_kernel_governance.schema_evolution import (
    SchemaEvolutionError,
    apply_schema_diff,
    apply_schema_diff_to_copy,
    parse_schema_diff,
)

from myco_kernel_bridge.handlers.registry import handler
from myco_kernel_bridge.handlers.state import DispatcherState
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
    empty_payload,
)


@handler(MessageType.SUBMIT_MUTATION)
def _handle_submit_mutation(
    state: DispatcherState, request: Message
) -> Message:
    """Classify an operator-submitted mutation + (for CI) verify owner attestation.

    Returns a submit_mutation_response carrying:
    - ``classification``: String ("daily" / "contract_identity_level" / "untyped")
    - ``accepted``: Bool — True if the substrate accepts the mutation.
    - ``rejection_reason``: String — empty if accepted.
    - ``content_canonical_bytes``: Bytes — echoes the request content so the
      Rust substrate can wrap it as a DAG node (Rust auto-computes the
      DAG-node hash from parent + content).
    """
    keys = dict(request.payload.value)
    try:
        mutation_type = expect_string(keys["mutation_type"])
        content_bytes = expect_bytes(keys["content_canonical_bytes"])
        touched_fields_arr = expect_array(keys["touched_fields"])
        touched_files_arr = expect_array(keys["touched_files"])
        touched_meta_arr = expect_array(keys["touched_meta_structures"])
    except (KeyError, CanonicalBytesError) as e:
        raise BridgeProtocolError(
            f"submit_mutation payload error: {e}"
        ) from e

    touched_fields = frozenset(expect_string(v) for v in touched_fields_arr)
    touched_files = frozenset(expect_string(v) for v in touched_files_arr)
    touched_meta = frozenset(expect_string(v) for v in touched_meta_arr)

    envelope = MutationEnvelope(
        mutation_type=mutation_type,
        touched_fields=touched_fields,
        touched_files=touched_files,
        touched_meta_structures=touched_meta,
    )
    classification = classify(envelope)

    accepted = False
    rejection_reason = ""

    if classification is Classification.DAILY:
        # Daily mutations: auto-accept. M11+ may add per-rule policies.
        accepted = True

    elif classification is Classification.CONTRACT_IDENTITY_LEVEL:
        # CI: require attestation_signature; verify against active owner key.
        if state.owner_keys is None:
            accepted = False
            rejection_reason = (
                "CI mutation requires owner_keys (M10 init missing; "
                "operator must complete TOFU handshake first)"
            )
        elif "attestation_signature" not in keys:
            accepted = False
            rejection_reason = (
                "CI mutation requires attestation_signature; none provided"
            )
        else:
            try:
                sig_bytes = expect_bytes(keys["attestation_signature"])
                if len(sig_bytes) != 64:
                    raise BridgeProtocolError(
                        f"attestation_signature must be 64 bytes; got {len(sig_bytes)}"
                    )
                # M14: when reveal_pubkey is present, the attestation signature
                # was made by the REVEAL key (fresh per-handshake), not the
                # IDENTITY key. The Rust substrate already verified the IDENTITY-
                # signature-over-REVEAL bundle; here we verify REVEAL-signed-content.
                # When reveal_pubkey is absent, fall back to M10 path (verify
                # against the active owner key, which == operator identity).
                if "reveal_pubkey" in keys:
                    reveal_pubkey_bytes = expect_bytes(keys["reveal_pubkey"])
                    if len(reveal_pubkey_bytes) != 32:
                        raise BridgeProtocolError(
                            f"reveal_pubkey must be 32 bytes; got {len(reveal_pubkey_bytes)}"
                        )
                    verify_signature(
                        reveal_pubkey_bytes,
                        sig_bytes,
                        content_bytes,
                    )
                else:
                    # M10 simplified verification: signature by current owner key.
                    active_key = state.owner_keys.current_active()
                    verify_signature(
                        active_key.bytes_,
                        sig_bytes,
                        content_bytes,
                    )
                accepted = True
            except (CryptoError, BridgeProtocolError) as e:
                accepted = False
                rejection_reason = f"attestation verification failed: {e}"

    else:
        # UNTYPED: per L1/HARD_RULES C14 untyped_mutation_blocked.
        accepted = False
        rejection_reason = (
            "untyped mutation (no classifier rule matched); "
            "L1/HARD_RULES C14 untyped_mutation_blocked"
        )

    # v3.1.1 Sprint 8.G (P03 §10.4): read the optional migration_mode flag.
    # When True, an accepted schema_evolution takes the TWO-PHASE path: build a
    # candidate gradient (deep-copy + apply-to-copy) and LEAVE the active
    # gradient untouched. Absent/False = the EXISTING single-cycle path, byte-
    # unchanged (the default).
    migration_mode = False
    if "migration_mode" in keys:
        try:
            migration_mode = expect_bool(keys["migration_mode"])
        except CanonicalBytesError as e:
            raise BridgeProtocolError(
                f"submit_mutation migration_mode must be Bool: {e}"
            ) from e

    # M17 P3 永恒进化: if the accepted mutation is a schema_evolution,
    # interpret content_canonical_bytes as a schema_diff and APPLY it to the
    # gradient configuration (with rollback on failure). Records evolution
    # outcome in the response so Rust can emit appropriate DAG nodes.
    #
    # Sprint 8.G: in migration mode we do NOT apply to the live gradient —
    # schema_apply_attempted stays False (so Rust's M17 evolution_event block
    # does not fire) and instead candidate_built reports whether the candidate
    # construction succeeded.
    schema_apply_attempted = False
    schema_apply_succeeded = False
    schema_apply_failure_reason = ""
    schema_apply_op = ""
    schema_apply_summary = ""
    candidate_built = False
    if accepted and mutation_type == "schema_evolution":
        try:
            diff = parse_schema_diff(content_bytes)
            schema_apply_op = diff.op.value
            schema_apply_summary = diff.summary()
            if migration_mode:
                # Two-phase: build the candidate; active gradient untouched.
                candidate, result = apply_schema_diff_to_copy(diff, state.gradient)
                if result.succeeded and candidate is not None:
                    candidate_built = True
                    state.candidate_gradient = candidate
                    state.candidate_op = schema_apply_op
                    state.candidate_diff_bytes = content_bytes
                else:
                    candidate_built = False
                    schema_apply_failure_reason = result.failure_reason
            else:
                # Single-cycle path (unchanged): apply to the live gradient.
                schema_apply_attempted = True
                result = apply_schema_diff(diff, state.gradient)
                if result.succeeded:
                    schema_apply_succeeded = True
                else:
                    schema_apply_succeeded = False
                    schema_apply_failure_reason = result.failure_reason
        except SchemaEvolutionError as e:
            if migration_mode:
                candidate_built = False
            else:
                schema_apply_attempted = True
                schema_apply_succeeded = False
            schema_apply_failure_reason = f"schema_diff parse: {e}"

    response_dict: dict[str, object] = {
        "classification": CbString(classification.value),
        "accepted": Bool(accepted),
        "rejection_reason": CbString(rejection_reason),
        "content_canonical_bytes": CbBytes(content_bytes),
        "mutation_type": CbString(mutation_type),
        # M17 P3 永恒进化 evolution result fields. Rust uses these to emit
        # evolution_succeeded:{op} or evolution_failed:{op} DAG nodes.
        "schema_apply_attempted": Bool(schema_apply_attempted),
        "schema_apply_succeeded": Bool(schema_apply_succeeded),
        "schema_apply_failure_reason": CbString(schema_apply_failure_reason),
        "schema_apply_op": CbString(schema_apply_op),
        "schema_apply_summary": CbString(schema_apply_summary),
        # v3.1.1 Sprint 8.G (P03 §10.4) two-phase migration result fields.
        # Rust branches on migration_mode: True + candidate_built → open the
        # dual-validation window; True + !candidate_built → terminal rollback.
        "migration_mode": Bool(migration_mode),
        "candidate_built": Bool(candidate_built),
    }
    response_payload = CbMap.from_dict(response_dict)
    return Message(
        type=MessageType.SUBMIT_MUTATION_RESPONSE,
        request_id=request.request_id,
        payload=response_payload,
    )


@handler(MessageType.COMMIT_MIGRATION)
def _handle_commit_migration(
    state: DispatcherState, request: Message
) -> Message:
    """v3.1.1 Sprint 8.G (P03 §10.4): promote the in-flight migration candidate
    to the active gradient.

    The candidate's dual-validation window completed with the candidate
    equivalent throughout, so the substrate decided to commit. We swap the
    active gradient for the candidate and clear the candidate slot. Idempotent:
    if there is no candidate (already committed/aborted), this is a no-op ack —
    the substrate's commit decision is authoritative and must not fail just
    because the candidate was already consumed.
    """
    if state.candidate_gradient is not None:
        state.gradient = state.candidate_gradient
    state.candidate_gradient = None
    state.candidate_op = ""
    state.candidate_diff_bytes = b""
    return Message(
        type=MessageType.COMMIT_MIGRATION_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


@handler(MessageType.ABORT_MIGRATION)
def _handle_abort_migration(
    state: DispatcherState, request: Message
) -> Message:
    """v3.1.1 Sprint 8.G (P03 §10.4): drop the in-flight migration candidate.

    The active gradient is left UNTOUCHED (P03 §3.5 substrate-identity
    preservation) — only the candidate slot is cleared. Reached on divergence,
    C66 window-exceeded, or an operator ``abort_migration`` mutation. Idempotent
    (no-op ack when no candidate is in flight).
    """
    state.candidate_gradient = None
    state.candidate_op = ""
    state.candidate_diff_bytes = b""
    return Message(
        type=MessageType.ABORT_MIGRATION_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )
