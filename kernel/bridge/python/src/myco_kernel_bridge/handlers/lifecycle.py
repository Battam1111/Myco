"""Lifecycle + introspection handlers — shutdown and schema query.

- ``shutdown`` — graceful-exit acknowledgment. The daemon loop detects the
  ``shutdown`` *request* type and exits after writing this ack; the handler
  itself is stateless.
- ``query_gradient_schemas`` — read-only introspection returning every
  registered axis's full schema + current value + update-rule kind (M21.3),
  used by Rust for legacy-substrate DAG back-fill.
"""

from __future__ import annotations

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Map as CbMap,
    String as CbString,
    Value,
)

from myco_kernel_bridge.handlers.registry import handler
from myco_kernel_bridge.handlers.state import DispatcherState
from myco_kernel_bridge.protocol import (
    Message,
    MessageType,
    empty_payload,
)


@handler(MessageType.SHUTDOWN)
def _handle_shutdown(state: DispatcherState, request: Message) -> Message:
    _ = state  # Shutdown is stateless; clean exit signaled by returning sentinel.
    return Message(
        type=MessageType.SHUTDOWN_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


@handler(MessageType.QUERY_GRADIENT_SCHEMAS)
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
