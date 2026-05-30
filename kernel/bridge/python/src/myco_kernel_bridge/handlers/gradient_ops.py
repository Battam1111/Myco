"""Gradient handlers — the core appetite-axis lifecycle operations.

These four handlers are the heart of the bridge: they mutate and read the
live :class:`GradientConfiguration` held in :class:`DispatcherState`.

- ``register_axis`` — declare a new axis with its schema + update rule.
- ``perturb`` — apply a delta to an axis value.
- ``advance`` — run one metabolic cycle; emit sporocarps for fruited axes.
- ``snapshot`` — read the current axis values.

Per L1/TROPISM §3, kernel/tropism owns gradient state; these handlers are
the thin IPC adapters over that state.
"""

from __future__ import annotations

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bytes as CbBytes,
    CanonicalBytesError,
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
)
from myco_kernel_tropism.sporocarp import (
    Sporocarp,
    emit_appetite_fruiting,
    emit_mortality_signal,
)

from myco_kernel_bridge.handlers.registry import handler
from myco_kernel_bridge.handlers.state import DispatcherState
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
    empty_payload,
)


@handler(MessageType.REGISTER_AXIS)
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
    except (ValueError, CanonicalBytesError) as e:
        # float() raises ValueError on bad repr; expect_* raise
        # CanonicalBytesError on wrong value type.
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


@handler(MessageType.PERTURB)
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


@handler(MessageType.ADVANCE)
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


@handler(MessageType.SNAPSHOT)
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
