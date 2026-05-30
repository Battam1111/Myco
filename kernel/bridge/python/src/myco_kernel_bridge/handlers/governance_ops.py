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
    parse_schema_diff,
)

from myco_kernel_bridge.handlers.registry import handler
from myco_kernel_bridge.handlers.state import DispatcherState
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
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

    # M17 P3 永恒进化: if the accepted mutation is a schema_evolution,
    # interpret content_canonical_bytes as a schema_diff and APPLY it to the
    # gradient configuration (with rollback on failure). Records evolution
    # outcome in the response so Rust can emit appropriate DAG nodes.
    schema_apply_attempted = False
    schema_apply_succeeded = False
    schema_apply_failure_reason = ""
    schema_apply_op = ""
    schema_apply_summary = ""
    if accepted and mutation_type == "schema_evolution":
        schema_apply_attempted = True
        try:
            diff = parse_schema_diff(content_bytes)
            schema_apply_op = diff.op.value
            schema_apply_summary = diff.summary()
            result = apply_schema_diff(diff, state.gradient)
            if result.succeeded:
                schema_apply_succeeded = True
            else:
                schema_apply_succeeded = False
                schema_apply_failure_reason = result.failure_reason
        except SchemaEvolutionError as e:
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
    }
    response_payload = CbMap.from_dict(response_dict)
    return Message(
        type=MessageType.SUBMIT_MUTATION_RESPONSE,
        request_id=request.request_id,
        payload=response_payload,
    )
