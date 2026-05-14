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
    Bytes as CbBytes,
    Map as CbMap,
    String as CbString,
    Uint as CbUint,
    Value,
    expect_bool,
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
    """

    gradient: GradientConfiguration = field(default_factory=GradientConfiguration)
    handshake_complete: bool = False
    session_secret: bytes | None = None


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
    raise BridgeProtocolError(
        f"dispatcher cannot handle {request.type.value!r} (not a request type)"
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
    """Persist the current gradient state to a directory on disk."""
    keys = dict(request.payload.value)
    try:
        state_dir = expect_string(keys["state_dir"])
    except KeyError as e:
        raise BridgeProtocolError(f"save_state missing state_dir: {e}") from e
    try:
        save_gradient(state.gradient, state_dir)
    except (PersistenceError, OSError) as e:
        raise BridgeProtocolError(f"save_state failed: {e}") from e
    return Message(
        type=MessageType.SAVE_STATE_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


def _handle_load_state(state: DispatcherState, request: Message) -> Message:
    """Hydrate gradient state from a directory on disk (or fall back to genesis)."""
    keys = dict(request.payload.value)
    try:
        state_dir = expect_string(keys["state_dir"])
    except KeyError as e:
        raise BridgeProtocolError(f"load_state missing state_dir: {e}") from e
    try:
        loaded = load_gradient(state_dir)
    except PersistenceError as e:
        raise BridgeProtocolError(f"load_state failed: {e}") from e
    except OSError as e:
        raise BridgeProtocolError(f"load_state I/O: {e}") from e
    if loaded is None:
        # No state file → genesis condition (caller hydrates from owner-provided schemas).
        return Message(
            type=MessageType.LOAD_STATE_ACK,
            request_id=request.request_id,
            payload=load_state_ack_payload(axis_count=0, hydrated=False),
        )
    # Replace the dispatcher's gradient atomically.
    state.gradient = loaded
    return Message(
        type=MessageType.LOAD_STATE_ACK,
        request_id=request.request_id,
        payload=load_state_ack_payload(
            axis_count=loaded.axis_count(),
            hydrated=True,
        ),
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
