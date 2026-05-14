"""Bridge dispatcher — map incoming requests to kernel/tropism operations.

This module is the Python worker's business logic: each request type
corresponds to one operation on a held :class:`GradientConfiguration`,
and each response carries the canonical-bytes-encoded result.

## Why a separate dispatcher module?

The :mod:`myco_kernel_bridge.daemon` module owns the I/O loop and session
state (session_secret, sequence). This module owns the **stateful kernel
work** — the gradient configuration that lives across requests, the
sporocarp emissions queued for response, the substrate metabolic-cycle
counter delegated from the Rust side.

Separating these two concerns lets the dispatcher be unit-tested without
spawning a subprocess.

## Doctrine

Per L1_TROPISM §3: kernel/tropism owns gradient state. The dispatcher is
a thin adapter — it does not contain new doctrine; it only routes
requests across the IPC boundary.

The dispatcher's responses are deterministic given the same request
sequence: replaying the same requests on a fresh dispatcher yields
identical gradient state and identical sporocarp hashes. This is
critical for L1_HARD_RULES C7 retro-edit detection: every sporocarp's
canonical bytes are reproducible from its inputs.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass, field
from typing import Final

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Bytes as CbBytes,
    Map as CbMap,
    String as CbString,
    Uint as CbUint,
    Value,
    expect_array,
    expect_bool,
    expect_bytes,
    expect_map,
    expect_string,
    expect_uint,
)
from myco_kernel_tropism.appetite_axis import (
    AxisClass,
    AxisSchema,
    DecayRule,
    NoOpRule,
    UpdateRule,
)
from myco_kernel_tropism.gradient import (
    AxisAlreadyRegistered,
    AxisNotFound,
    GradientConfiguration,
)
from myco_kernel_tropism.sporocarp import (
    Sporocarp,
    emit_appetite_fruiting,
    emit_mortality_signal,
)

from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
    empty_payload,
    error_payload,
    hello_ack_payload,
    load_state_ack_payload,
)
from myco_kernel_tropism.persistence import (
    PersistenceError,
    load_gradient,
    save_gradient,
)
from myco_kernel_governance.classifier import (
    Classification,
    MutationEnvelope,
    classify,
)
from myco_kernel_governance.crypto import (
    CryptoError,
    Ed25519PublicKey,
    verify_signature,
)
from myco_kernel_governance.owner_keys import OwnerKeyHistory, init_with_genesis_key
from myco_kernel_governance.owner_keys_persistence import (
    OwnerKeysPersistenceError,
    load_owner_key_history,
    save_owner_key_history,
)
from myco_kernel_governance.schema_evolution import (
    SchemaEvolutionError,
    apply_schema_diff,
    parse_schema_diff,
)


KERNEL_TROPISM_VERSION: Final[str] = "0.9.0-alpha.1"
"""Version reported in hello_ack. Tracks kernel/tropism's pyproject version."""


# ---------------------------------------------------------------------------
# Dispatcher state.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class DispatcherState:
    """Mutable state held by the dispatcher across requests.

    Fields
    ------
    gradient:
        The live gradient configuration. Initially empty; populated by
        ``register_axis`` requests from the Rust controller.
    handshake_complete:
        Whether the ``hello`` handshake has occurred. Must be True before
        any other message type is accepted.
    session_secret:
        The session secret transported by ``hello``. Used by the daemon
        loop to verify subsequent message HMACs.
    owner_keys:
        Owner-key history (M10). Initialized either by load_state from disk
        or by the load_state's ``genesis_owner_pubkey`` field on first sight.
        Consulted by ``submit_mutation`` for CI-attestation verification.
    """

    gradient: GradientConfiguration = field(default_factory=GradientConfiguration)
    handshake_complete: bool = False
    session_secret: bytes | None = None
    owner_keys: OwnerKeyHistory | None = None


# ---------------------------------------------------------------------------
# Dispatcher.
# ---------------------------------------------------------------------------


def dispatch(state: DispatcherState, request: Message) -> Message | None:
    """Process one request and return the response (or None for shutdown).

    Args:
        state: mutable dispatcher state.
        request: decoded incoming message.

    Returns:
        The response message, or ``None`` if the daemon should exit
        (after sending the response).

    Raises:
        BridgeProtocolError: on invalid request structure (caller catches
            and returns an ERROR envelope).
    """
    # Handshake gating: only HELLO is accepted before handshake_complete.
    if not state.handshake_complete and request.type is not MessageType.HELLO:
        raise BridgeProtocolError(
            f"received {request.type.value!r} before hello handshake"
        )

    if request.type is MessageType.HELLO:
        return _handle_hello(state, request)
    if request.type is MessageType.REGISTER_AXIS:
        return _handle_register_axis(state, request)
    if request.type is MessageType.PERTURB:
        return _handle_perturb(state, request)
    if request.type is MessageType.ADVANCE:
        return _handle_advance(state, request)
    if request.type is MessageType.SNAPSHOT:
        return _handle_snapshot(state, request)
    if request.type is MessageType.SHUTDOWN:
        return _handle_shutdown(state, request)
    if request.type is MessageType.SAVE_STATE:
        return _handle_save_state(state, request)
    if request.type is MessageType.LOAD_STATE:
        return _handle_load_state(state, request)
    if request.type is MessageType.COMPUTE_INTENT:
        return _handle_compute_intent(state, request)
    if request.type is MessageType.SUBMIT_MUTATION:
        return _handle_submit_mutation(state, request)
    if request.type is MessageType.SNAPSHOT_GRADIENT_TO_DIR:
        return _handle_snapshot_gradient_to_dir(state, request)
    if request.type is MessageType.QUERY_GRADIENT_SCHEMAS:
        return _handle_query_gradient_schemas(state, request)
    raise BridgeProtocolError(
        f"dispatcher cannot handle {request.type.value!r} (not a request type)"
    )


def _handle_query_gradient_schemas(
    state: DispatcherState, request: Message
) -> Message:
    """M21.3 P5 万物互联: return full schemas + current values + update rules
    for every registered axis. Used by Rust for legacy-substrate back-fill —
    emitting axis_registered + axis_perturbed DAG events for axes that exist
    in Python's loaded state but not yet in the DAG.
    """
    from myco_kernel_tropism.appetite_axis import DecayRule, NoOpRule  # noqa: PLC0415

    axes_array: list[Value] = []
    for name in sorted(state.gradient.axes.keys()):
        axis = state.gradient.axes[name]
        rule = state.gradient.update_rules.get(name)
        if isinstance(rule, DecayRule):
            update_rule_kind = "decay"
        elif isinstance(rule, NoOpRule):
            update_rule_kind = "noop"
        else:
            update_rule_kind = "unknown"
        axes_array.append(
            CbMap.from_dict(
                {
                    "name": CbString(name),
                    "axis_class": CbString(axis.schema.axis_class.value),
                    "fruiting_threshold_repr": CbString(
                        repr(axis.schema.fruiting_threshold)
                    ),
                    "initial_value_repr": CbString(repr(axis.schema.initial_value)),
                    "current_value_repr": CbString(repr(axis.value)),
                    "decay_rate_per_cycle_repr": CbString(
                        repr(axis.schema.decay_rate_per_cycle)
                    ),
                    "is_mortality_signal": Bool(axis.schema.is_mortality_signal),
                    "update_rule_kind": CbString(update_rule_kind),
                }
            )
        )
    return Message(
        type=MessageType.QUERY_GRADIENT_SCHEMAS_RESPONSE,
        request_id=request.request_id,
        payload=CbMap.from_dict({"axes": Array(tuple(axes_array))}),
    )


def _handle_snapshot_gradient_to_dir(
    state: DispatcherState, request: Message
) -> Message:
    """M20 P8 永恒繁衍: snapshot the gradient state to a target directory.

    This is the Python-side primitive used by sprout_child: writes a fresh
    `gradient.cb` containing the parent's axes + schemas + current values
    into the child substrate's state_dir.

    The child receives a CLONE of the parent's gradient (axes registered;
    initial axis values = parent's current values). The L1 decision: M20-MV
    transfers gradient state but NOT the parent's causal DAG (child starts
    its own causal history per L1 design).
    """
    keys = dict(request.payload.value)
    try:
        target_dir = expect_string(keys["target_dir"])
    except KeyError as e:
        raise BridgeProtocolError(
            f"snapshot_gradient_to_dir missing target_dir: {e}"
        ) from e
    try:
        save_gradient(state.gradient, target_dir)
    except (PersistenceError, OSError) as e:
        raise BridgeProtocolError(
            f"snapshot_gradient_to_dir save failed: {e}"
        ) from e
    return Message(
        type=MessageType.SNAPSHOT_GRADIENT_TO_DIR_ACK,
        request_id=request.request_id,
        payload=CbMap.from_dict(
            {"axis_count": CbUint(state.gradient.axis_count())}
        ),
    )


# ---------------------------------------------------------------------------
# Handlers.
# ---------------------------------------------------------------------------


def _handle_hello(state: DispatcherState, request: Message) -> Message:
    if state.handshake_complete:
        raise BridgeProtocolError("hello received after handshake already complete")
    keys = dict(request.payload.value)
    session_secret_value = keys.get("session_secret")
    if session_secret_value is None or not isinstance(session_secret_value, CbBytes):
        raise BridgeProtocolError("hello payload missing session_secret bytes")
    if len(session_secret_value.value) != 32:
        raise BridgeProtocolError(
            f"hello session_secret must be 32 bytes; got {len(session_secret_value.value)}"
        )
    state.session_secret = session_secret_value.value
    state.handshake_complete = True
    return Message(
        type=MessageType.HELLO_ACK,
        request_id=request.request_id,
        payload=hello_ack_payload(
            kernel_tropism_version=KERNEL_TROPISM_VERSION,
            python_version=platform.python_version(),
        ),
    )


def _handle_register_axis(
    state: DispatcherState, request: Message
) -> Message:
    keys = dict(request.payload.value)
    try:
        name = expect_string(keys["name"])
        axis_class_str = expect_string(keys["axis_class"])
        fruiting_threshold = float(expect_string(keys["fruiting_threshold_repr"]))
        initial_value = float(expect_string(keys["initial_value_repr"]))
        decay_rate_per_cycle = float(
            expect_string(keys["decay_rate_per_cycle_repr"])
        )
        is_mortality_signal = expect_bool(keys["is_mortality_signal"])
        update_rule_kind = expect_string(keys["update_rule_kind"])
    except KeyError as e:
        raise BridgeProtocolError(f"register_axis payload missing key: {e}") from e
    except (ValueError, Exception) as e:
        raise BridgeProtocolError(
            f"register_axis payload parse error: {e}"
        ) from e

    if axis_class_str == "appetite":
        axis_class = AxisClass.APPETITE
    elif axis_class_str == "decay":
        axis_class = AxisClass.DECAY
    else:
        raise BridgeProtocolError(f"unknown axis_class: {axis_class_str!r}")

    schema = AxisSchema(
        name=name,
        axis_class=axis_class,
        fruiting_threshold=fruiting_threshold,
        initial_value=initial_value,
        decay_rate_per_cycle=decay_rate_per_cycle,
        is_mortality_signal=is_mortality_signal,
    )

    rule: UpdateRule
    if update_rule_kind == "decay":
        rule = DecayRule()
    elif update_rule_kind == "noop":
        rule = NoOpRule()
    else:
        raise BridgeProtocolError(f"unknown update_rule_kind: {update_rule_kind!r}")

    try:
        state.gradient.register_axis(schema, rule)
    except AxisAlreadyRegistered as e:
        raise BridgeProtocolError(str(e)) from e

    return Message(
        type=MessageType.REGISTER_AXIS_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


def _handle_perturb(state: DispatcherState, request: Message) -> Message:
    keys = dict(request.payload.value)
    try:
        axis_name = expect_string(keys["axis_name"])
        delta = float(expect_string(keys["delta_repr"]))
    except KeyError as e:
        raise BridgeProtocolError(f"perturb payload missing key: {e}") from e
    except ValueError as e:
        raise BridgeProtocolError(f"perturb delta parse error: {e}") from e
    try:
        state.gradient.perturb_axis(axis_name, delta)
    except AxisNotFound as e:
        raise BridgeProtocolError(str(e)) from e
    return Message(
        type=MessageType.PERTURB_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


def _handle_advance(state: DispatcherState, request: Message) -> Message:
    keys = dict(request.payload.value)
    try:
        current_cycle = expect_uint(keys["current_cycle"])
    except KeyError as e:
        raise BridgeProtocolError(
            f"advance payload missing current_cycle: {e}"
        ) from e

    fruited_names = state.gradient.advance(int(current_cycle))

    sporocarps: list[Sporocarp] = []
    for axis_name in fruited_names:
        axis = state.gradient.get_axis(axis_name)
        if axis.schema.is_mortality_signal:
            sporocarps.append(
                emit_mortality_signal(
                    axis_name=axis_name,
                    fruiting_value=axis.value,
                    at_cycle=int(current_cycle),
                )
            )
        else:
            sporocarps.append(
                emit_appetite_fruiting(
                    axis_name=axis_name,
                    fruiting_value=axis.value,
                    at_cycle=int(current_cycle),
                )
            )

    # Reset APPETITE axes after fruiting (kernel/tropism semantics).
    state.gradient.reset_after_fruiting(fruited_names, int(current_cycle))

    # Build response payload.
    sporocarp_values: list[Value] = []
    for sporocarp in sporocarps:
        cb_bytes = sporocarp.to_canonical_bytes()
        sp_hash = sporocarp.hash()
        sp_map = CbMap.from_dict(
            {
                "sporocarp_type": CbString(sporocarp.sporocarp_type),
                "axis_name": CbString(sporocarp.axis_name),
                "fruiting_value_repr": CbString(repr(sporocarp.fruiting_value)),
                "at_cycle": CbUint(sporocarp.at_cycle),
                "canonical_bytes": CbBytes(cb_bytes.bytes_),
                "hash": CbBytes(sp_hash.bytes_),
            }
        )
        sporocarp_values.append(sp_map)

    response_payload = CbMap.from_dict(
        {
            "fruited_axes": Array(
                tuple(CbString(name) for name in fruited_names)
            ),
            "sporocarps": Array(tuple(sporocarp_values)),
        }
    )

    return Message(
        type=MessageType.ADVANCE_RESPONSE,
        request_id=request.request_id,
        payload=response_payload,
    )


def _handle_snapshot(state: DispatcherState, request: Message) -> Message:
    values = state.gradient.snapshot_values()
    values_map = CbMap.from_dict(
        {name: CbString(repr(value)) for name, value in sorted(values.items())}
    )
    return Message(
        type=MessageType.SNAPSHOT_RESPONSE,
        request_id=request.request_id,
        payload=CbMap.from_dict({"values": values_map}),
    )


def _handle_shutdown(state: DispatcherState, request: Message) -> Message:
    _ = state  # Shutdown is stateless; clean exit signaled by returning sentinel.
    return Message(
        type=MessageType.SHUTDOWN_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


def _handle_save_state(state: DispatcherState, request: Message) -> Message:
    """Persist the current gradient state + owner_keys to a directory on disk."""
    keys = dict(request.payload.value)
    try:
        state_dir = expect_string(keys["state_dir"])
    except KeyError as e:
        raise BridgeProtocolError(f"save_state missing state_dir: {e}") from e
    try:
        save_gradient(state.gradient, state_dir)
        # M10: also persist owner_keys if initialized.
        if state.owner_keys is not None:
            save_owner_key_history(state.owner_keys, state_dir)
    except (PersistenceError, OSError, OwnerKeysPersistenceError) as e:
        raise BridgeProtocolError(f"save_state failed: {e}") from e
    return Message(
        type=MessageType.SAVE_STATE_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


def _handle_compute_intent(state: DispatcherState, request: Message) -> Message:
    """Run kernel/trajectory's intent algorithm over a DAG subset (M8).

    The Rust substrate sends its DAG nodes; we build an in-memory DagSource,
    run neighborhood + ancestors+descendants + cluster_C, and return the
    clusters.
    """
    from myco_kernel_trajectory.cluster import cluster_connected_components  # noqa: PLC0415
    from myco_kernel_trajectory.query import (  # noqa: PLC0415
        DagNode,
        InMemoryDagSource,
        causal_ancestors_and_descendants,
        neighborhood,
    )

    _ = state  # this handler is stateless across calls
    keys = dict(request.payload.value)
    try:
        pivot_hash_bytes = expect_bytes(keys["pivot_hash"])
        radius_cycles = expect_uint(keys["radius_cycles"])
        dag_nodes_array = expect_array(keys["dag_nodes"])
    except (KeyError, Exception) as e:
        raise BridgeProtocolError(
            f"compute_intent payload error: {e}"
        ) from e

    # Reconstruct an in-memory DagSource from the transported subset.
    dag = InMemoryDagSource()
    for node_value in dag_nodes_array:
        node_map = expect_map(node_value)
        node_fields = dict(node_map.value)
        try:
            node_hash = expect_bytes(node_fields["hash"]).hex()
            parents_arr = expect_array(node_fields["parent_hashes"])
            parent_ids = tuple(expect_bytes(p).hex() for p in parents_arr)
            at_cycle = expect_uint(node_fields["at_cycle"])
            node_type = expect_string(node_fields["node_type"])
        except (KeyError, Exception) as e:
            raise BridgeProtocolError(
                f"compute_intent dag_node decode error: {e}"
            ) from e
        dag.add(
            DagNode(
                node_id=node_hash,
                parent_ids=parent_ids,
                at_cycle=int(at_cycle),
                node_type=node_type,
            )
        )

    pivot_id = pivot_hash_bytes.hex()
    nbr = neighborhood(dag, pivot_id, int(radius_cycles))
    full_set = causal_ancestors_and_descendants(dag, nbr.node_ids)
    intent = cluster_connected_components(dag, full_set)

    # Build response.
    cluster_values: list[Value] = []
    for cluster in intent.clusters:
        cluster_map = CbMap.from_dict(
            {
                "cluster_id": CbUint(cluster.cluster_id),
                "node_count": CbUint(len(cluster.node_ids)),
                "node_hashes": Array(
                    tuple(CbBytes(bytes.fromhex(nid)) for nid in sorted(cluster.node_ids))
                ),
            }
        )
        cluster_values.append(cluster_map)

    response_payload = CbMap.from_dict(
        {
            "cold_start": Bool(nbr.cold_start),
            "neighborhood_node_count": CbUint(len(nbr.node_ids)),
            "full_set_node_count": CbUint(len(full_set)),
            "cluster_count": CbUint(len(intent.clusters)),
            "clusters": Array(tuple(cluster_values)),
        }
    )
    return Message(
        type=MessageType.COMPUTE_INTENT_RESPONSE,
        request_id=request.request_id,
        payload=response_payload,
    )


def _handle_load_state(state: DispatcherState, request: Message) -> Message:
    """Hydrate gradient state + owner_keys from a directory on disk.

    M10: also accepts an optional ``genesis_owner_pubkey`` field; if no
    owner_keys.cb exists on disk and this field is provided, initialize
    a fresh owner-key history with the given pubkey as the genesis key.

    M21.3 P5 万物互联: accepts an optional ``skip_disk_load`` Bool field.
    When True, Python does NOT read gradient.cb or owner_keys.cb from disk;
    Rust will subsequently REPLAY DAG events (axis_registered / axis_perturbed
    / etc.) to reconstruct state in-memory. This is the path used when the
    DAG is the authoritative source of truth (post-M21 substrate).
    """
    keys = dict(request.payload.value)
    try:
        state_dir = expect_string(keys["state_dir"])
    except KeyError as e:
        raise BridgeProtocolError(f"load_state missing state_dir: {e}") from e

    # M21.3: skip_disk_load flag — Python won't read state files; Rust
    # will reconstruct state via DAG event replay.
    skip_disk_load = False
    if "skip_disk_load" in keys:
        skip_disk_value = keys["skip_disk_load"]
        if not isinstance(skip_disk_value, Bool):
            raise BridgeProtocolError(
                f"skip_disk_load must be Bool; got {type(skip_disk_value).__name__}"
            )
        skip_disk_load = bool(skip_disk_value.value)

    # Load gradient (M7) — skipped under M21.3 skip_disk_load.
    if skip_disk_load:
        loaded_gradient = None
    else:
        try:
            loaded_gradient = load_gradient(state_dir)
        except PersistenceError as e:
            raise BridgeProtocolError(f"load_state gradient failed: {e}") from e
        except OSError as e:
            raise BridgeProtocolError(f"load_state I/O: {e}") from e
    if loaded_gradient is not None:
        state.gradient = loaded_gradient

    # M10: load owner_keys from disk, or initialize from genesis_owner_pubkey if absent.
    # M21.3: when skip_disk_load=true, don't read owner_keys.cb from disk.
    if skip_disk_load:
        loaded_owner_keys = None
    else:
        try:
            loaded_owner_keys = load_owner_key_history(state_dir)
        except OwnerKeysPersistenceError as e:
            raise BridgeProtocolError(f"load_state owner_keys failed: {e}") from e

    if loaded_owner_keys is not None:
        state.owner_keys = loaded_owner_keys
    elif "genesis_owner_pubkey" in keys:
        # First-time init: substrate is supplying the genesis owner pubkey.
        # M21.4 P5 万物互联: do NOT save owner_keys.cb. The owner key history
        # is event-sourced via the owner_key_initialized DAG event emitted
        # by Rust at the same hello.
        pubkey_bytes = expect_bytes(keys["genesis_owner_pubkey"])
        if len(pubkey_bytes) != 32:
            raise BridgeProtocolError(
                f"genesis_owner_pubkey must be 32 bytes; got {len(pubkey_bytes)}"
            )
        import time  # noqa: PLC0415

        genesis_ts = int(time.time())
        state.owner_keys = init_with_genesis_key(
            genesis_key=Ed25519PublicKey(pubkey_bytes),
            genesis_anchor_timestamp_unix_seconds=genesis_ts,
        )
    # else: legacy mode (no owner_keys; CI mutations will be rejected).

    axis_count = state.gradient.axis_count()
    hydrated = loaded_gradient is not None or loaded_owner_keys is not None
    return Message(
        type=MessageType.LOAD_STATE_ACK,
        request_id=request.request_id,
        payload=load_state_ack_payload(
            axis_count=axis_count,
            hydrated=hydrated,
        ),
    )


# ---------------------------------------------------------------------------
# M10: submit_mutation handler.
# ---------------------------------------------------------------------------


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
    except (KeyError, Exception) as e:
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
        # UNTYPED: per L1_HARD_RULES C14 untyped_mutation_blocked.
        accepted = False
        rejection_reason = (
            "untyped mutation (no classifier rule matched); "
            "L1_HARD_RULES C14 untyped_mutation_blocked"
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


# ---------------------------------------------------------------------------
# Error envelope builder.
# ---------------------------------------------------------------------------


def build_error_response(
    in_response_to: int, code: str, message: str
) -> Message:
    """Construct an ``error`` envelope echoing a failed request's ID."""
    return Message(
        type=MessageType.ERROR,
        request_id=in_response_to,
        payload=error_payload(
            code=code,
            message=message,
            in_response_to=in_response_to,
        ),
    )
