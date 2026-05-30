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
    Bool,
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
    GradientConfiguration,
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

    # v3.1.1 Sprint 8.G (P03 §10.4): if a two-phase migration is in flight,
    # advance the CANDIDATE gradient alongside the active one and compute
    # divergence. The active advance above already ran; we now mirror it on the
    # candidate and compare. The candidate's fruiting list is what drives the
    # OPTION-A divergence test (see _compute_candidate_divergence).
    candidate_active = state.candidate_gradient is not None
    candidate_diverged = False
    divergence_reason = ""
    active_fingerprint = _gradient_fingerprint(state.gradient)
    candidate_fingerprint = ""
    if candidate_active:
        (
            candidate_diverged,
            divergence_reason,
            candidate_fingerprint,
        ) = _advance_candidate_and_check_divergence(
            state, int(current_cycle), fruited_names
        )

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
            # v3.1.1 Sprint 8.G (P03 §10.4) dual-validation outcome. Rust's
            # run_migration_step reads these to drive the commit/rollback
            # decision. candidate_active=False (no migration in flight) makes
            # the rest meaningless — Rust ignores them in that case.
            "candidate_active": Bool(candidate_active),
            "candidate_diverged": Bool(candidate_diverged),
            "divergence_reason": CbString(divergence_reason),
            "active_fingerprint": CbString(active_fingerprint),
            "candidate_fingerprint": CbString(candidate_fingerprint),
        }
    )

    return Message(
        type=MessageType.ADVANCE_RESPONSE,
        request_id=request.request_id,
        payload=response_payload,
    )


def _gradient_fingerprint(gradient: GradientConfiguration) -> str:
    """A deterministic, order-independent fingerprint of a gradient's current
    axis values.

    Used as observability evidence (active_fingerprint / candidate_fingerprint
    in the advance_response): if two gradients that should be equivalent
    produce different fingerprints, an operator can SEE the divergence. The
    fingerprint sorts axis names so it is independent of dict insertion order,
    and renders each value via ``repr`` (the same float convention used across
    the wire) so it is byte-deterministic.
    """
    items = sorted(gradient.snapshot_values().items())
    return ";".join(f"{name}={value!r}" for name, value in items)


def _advance_candidate_and_check_divergence(
    state: DispatcherState,
    current_cycle: int,
    active_fruited_names: list[str],
) -> tuple[bool, str, str]:
    """Advance the in-flight candidate gradient one cycle and apply the OPTION-A
    divergence test (P03 §10.4).

    OPTION A — the candidate is considered DIVERGED iff ANY of:
      1. the candidate raises during ``advance`` (structurally broken schema);
      2. the candidate fruits its mortality_signal axis when the ACTIVE
         gradient did NOT (the candidate would kill the substrate where the
         active schema keeps it alive — the canonical "this migration is
         dangerous" signal);
      3. the candidate produces a non-finite value (NaN / ±inf) on any axis
         (numerically degenerate schema).

    Otherwise the cycle is EQUIVALENT.

    Returns ``(diverged, reason, candidate_fingerprint)``. On a structural
    raise the fingerprint is best-effort empty (we could not snapshot).

    The candidate gradient is mutated in place (it advances one cycle); the
    ACTIVE gradient is NOT touched here (the caller already advanced it).
    """
    import math

    candidate = state.candidate_gradient
    assert candidate is not None  # guarded by caller

    # (1) candidate raises during advance → diverged.
    try:
        candidate_fruited = candidate.advance(current_cycle)
    except Exception as e:  # noqa: BLE001 — any failure during candidate
        # advance is a divergence signal, not a dispatcher crash.
        return (
            True,
            f"candidate raised during advance at cycle {current_cycle}: "
            f"{type(e).__name__}: {e}",
            "",
        )

    # (3) candidate produced a non-finite value → diverged. Check BEFORE the
    # post-fruiting reset so we observe the raw advanced values.
    for name, value in candidate.snapshot_values().items():
        if not math.isfinite(value):
            return (
                True,
                f"candidate axis {name!r} became non-finite ({value!r}) at "
                f"cycle {current_cycle}",
                _gradient_fingerprint(candidate),
            )

    # (2) candidate fruits its mortality_signal where active did not → diverged.
    active_fruited_set = set(active_fruited_names)
    for axis_name in candidate_fruited:
        try:
            axis = candidate.get_axis(axis_name)
        except Exception:  # noqa: BLE001 — defensive; treat as divergence
            return (
                True,
                f"candidate fruited unknown axis {axis_name!r} at cycle "
                f"{current_cycle}",
                _gradient_fingerprint(candidate),
            )
        if axis.schema.is_mortality_signal and axis_name not in active_fruited_set:
            return (
                True,
                f"candidate fruited mortality_signal axis {axis_name!r} at "
                f"cycle {current_cycle} when active did not — migration would "
                "cross the substrate's mortality threshold",
                _gradient_fingerprint(candidate),
            )

    # Reset the candidate's APPETITE axes after fruiting, mirroring the active
    # gradient's lifecycle so the two stay comparable cycle-over-cycle.
    candidate.reset_after_fruiting(candidate_fruited, current_cycle)

    return (False, "", _gradient_fingerprint(candidate))


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
