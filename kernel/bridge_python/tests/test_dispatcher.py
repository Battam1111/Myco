"""Tests for kernel/bridge_python dispatcher — in-process, no subprocess."""

from __future__ import annotations

import pytest

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bytes as CbBytes,
    Map as CbMap,
    String as CbString,
    Uint as CbUint,
    expect_array,
    expect_string,
)

from myco_kernel_bridge.dispatcher import (
    DispatcherState,
    build_error_response,
    dispatch,
)
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
    advance_payload,
    empty_payload,
    error_payload,
    hello_payload,
    perturb_payload,
    register_axis_payload,
)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _do_handshake(state: DispatcherState, request_id: int = 1) -> None:
    """Run the hello handshake to put state into the post-handshake mode."""
    response = dispatch(
        state,
        Message(
            type=MessageType.HELLO,
            request_id=request_id,
            payload=hello_payload(b"\xaa" * 32),
        ),
    )
    assert response is not None
    assert response.type is MessageType.HELLO_ACK


# ---------------------------------------------------------------------------
# Handshake gating.
# ---------------------------------------------------------------------------


def test_advance_before_hello_rejected() -> None:
    state = DispatcherState()
    with pytest.raises(BridgeProtocolError, match="before hello"):
        dispatch(
            state,
            Message(
                type=MessageType.ADVANCE,
                request_id=1,
                payload=advance_payload(0),
            ),
        )


def test_hello_completes_handshake() -> None:
    state = DispatcherState()
    assert not state.handshake_complete
    response = dispatch(
        state,
        Message(
            type=MessageType.HELLO,
            request_id=1,
            payload=hello_payload(b"\x55" * 32),
        ),
    )
    assert state.handshake_complete
    assert state.session_secret == b"\x55" * 32
    assert response is not None
    assert response.type is MessageType.HELLO_ACK
    assert response.request_id == 1


def test_double_hello_rejected() -> None:
    state = DispatcherState()
    _do_handshake(state)
    with pytest.raises(BridgeProtocolError, match="already complete"):
        dispatch(
            state,
            Message(
                type=MessageType.HELLO,
                request_id=2,
                payload=hello_payload(b"\xbb" * 32),
            ),
        )


def test_hello_with_wrong_secret_length_rejected() -> None:
    state = DispatcherState()
    with pytest.raises(BridgeProtocolError, match="32 bytes"):
        dispatch(
            state,
            Message(
                type=MessageType.HELLO,
                request_id=1,
                payload=CbMap.from_dict(
                    {"session_secret": CbBytes(b"\x00" * 16)}
                ),
            ),
        )


# ---------------------------------------------------------------------------
# Register axis.
# ---------------------------------------------------------------------------


def test_register_appetite_axis() -> None:
    state = DispatcherState()
    _do_handshake(state)
    response = dispatch(
        state,
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=10,
            payload=register_axis_payload(
                name="curiosity",
                axis_class="appetite",
                fruiting_threshold=5.0,
                initial_value=0.0,
                decay_rate_per_cycle=1.0,
                is_mortality_signal=False,
                update_rule_kind="noop",
            ),
        ),
    )
    assert response is not None
    assert response.type is MessageType.REGISTER_AXIS_ACK
    assert state.gradient.axis_count() == 1
    assert state.gradient.get_axis("curiosity").value == 0.0


def test_register_decay_axis_for_mortality() -> None:
    state = DispatcherState()
    _do_handshake(state)
    response = dispatch(
        state,
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=11,
            payload=register_axis_payload(
                name="mortality_signal",
                axis_class="decay",
                fruiting_threshold=0.01,
                initial_value=1.0,
                decay_rate_per_cycle=0.5,
                is_mortality_signal=True,
                update_rule_kind="decay",
            ),
        ),
    )
    assert response is not None
    assert response.type is MessageType.REGISTER_AXIS_ACK
    axis = state.gradient.get_axis("mortality_signal")
    assert axis.value == 1.0
    assert axis.schema.is_mortality_signal


def test_register_duplicate_axis_rejected() -> None:
    state = DispatcherState()
    _do_handshake(state)
    msg = Message(
        type=MessageType.REGISTER_AXIS,
        request_id=12,
        payload=register_axis_payload(
            name="dup",
            axis_class="appetite",
            fruiting_threshold=1.0,
            initial_value=0.0,
            decay_rate_per_cycle=1.0,
            is_mortality_signal=False,
            update_rule_kind="noop",
        ),
    )
    dispatch(state, msg)
    with pytest.raises(BridgeProtocolError, match="already registered"):
        dispatch(state, msg)


# ---------------------------------------------------------------------------
# Perturb.
# ---------------------------------------------------------------------------


def test_perturb_increments_axis_value() -> None:
    state = DispatcherState()
    _do_handshake(state)
    dispatch(
        state,
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=20,
            payload=register_axis_payload(
                name="x",
                axis_class="appetite",
                fruiting_threshold=10.0,
                initial_value=0.0,
                decay_rate_per_cycle=1.0,
                is_mortality_signal=False,
                update_rule_kind="noop",
            ),
        ),
    )
    response = dispatch(
        state,
        Message(
            type=MessageType.PERTURB,
            request_id=21,
            payload=perturb_payload("x", 3.5),
        ),
    )
    assert response is not None
    assert response.type is MessageType.PERTURB_ACK
    assert state.gradient.get_axis("x").value == 3.5


def test_perturb_unknown_axis_rejected() -> None:
    state = DispatcherState()
    _do_handshake(state)
    with pytest.raises(BridgeProtocolError, match="not registered"):
        dispatch(
            state,
            Message(
                type=MessageType.PERTURB,
                request_id=22,
                payload=perturb_payload("unknown", 1.0),
            ),
        )


# ---------------------------------------------------------------------------
# Advance.
# ---------------------------------------------------------------------------


def test_advance_no_fruit() -> None:
    state = DispatcherState()
    _do_handshake(state)
    dispatch(
        state,
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=30,
            payload=register_axis_payload(
                name="x",
                axis_class="appetite",
                fruiting_threshold=10.0,
                initial_value=0.0,
                decay_rate_per_cycle=1.0,
                is_mortality_signal=False,
                update_rule_kind="noop",
            ),
        ),
    )
    response = dispatch(
        state,
        Message(
            type=MessageType.ADVANCE,
            request_id=31,
            payload=advance_payload(1),
        ),
    )
    assert response is not None
    assert response.type is MessageType.ADVANCE_RESPONSE
    fruited_arr = expect_array(dict(response.payload.value)["fruited_axes"])
    assert fruited_arr == ()


def test_advance_with_fruit_emits_sporocarp() -> None:
    state = DispatcherState()
    _do_handshake(state)
    dispatch(
        state,
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=40,
            payload=register_axis_payload(
                name="x",
                axis_class="appetite",
                fruiting_threshold=2.0,
                initial_value=0.0,
                decay_rate_per_cycle=1.0,
                is_mortality_signal=False,
                update_rule_kind="noop",
            ),
        ),
    )
    dispatch(
        state,
        Message(
            type=MessageType.PERTURB,
            request_id=41,
            payload=perturb_payload("x", 5.0),
        ),
    )
    response = dispatch(
        state,
        Message(
            type=MessageType.ADVANCE,
            request_id=42,
            payload=advance_payload(5),
        ),
    )
    assert response is not None
    payload = dict(response.payload.value)
    fruited = expect_array(payload["fruited_axes"])
    assert len(fruited) == 1
    assert expect_string(fruited[0]) == "x"
    sporocarps = expect_array(payload["sporocarps"])
    assert len(sporocarps) == 1
    sp_map = sporocarps[0]
    assert isinstance(sp_map, CbMap)
    sp_dict = dict(sp_map.value)
    assert expect_string(sp_dict["sporocarp_type"]) == "appetite_fruiting"
    assert expect_string(sp_dict["axis_name"]) == "x"
    # Axis is reset after fruiting.
    assert state.gradient.get_axis("x").value == 0.0


def test_advance_mortality_signal_emits_correct_sporocarp_type() -> None:
    state = DispatcherState()
    _do_handshake(state)
    dispatch(
        state,
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=50,
            payload=register_axis_payload(
                name="mortality",
                axis_class="decay",
                fruiting_threshold=0.1,
                initial_value=1.0,
                decay_rate_per_cycle=0.5,
                is_mortality_signal=True,
                update_rule_kind="decay",
            ),
        ),
    )
    # 4 cycles of 0.5x decay: 1 → 0.5 → 0.25 → 0.125 → 0.0625 (below 0.1).
    response = None
    for cycle in range(1, 5):
        response = dispatch(
            state,
            Message(
                type=MessageType.ADVANCE,
                request_id=50 + cycle,
                payload=advance_payload(cycle),
            ),
        )
    assert response is not None
    payload = dict(response.payload.value)
    fruited = expect_array(payload["fruited_axes"])
    assert len(fruited) == 1
    sporocarps = expect_array(payload["sporocarps"])
    sp_dict = dict(sporocarps[0].value)  # type: ignore[union-attr]
    assert (
        expect_string(sp_dict["sporocarp_type"])
        == "mortality_signal_threshold_crossed"
    )


# ---------------------------------------------------------------------------
# Snapshot.
# ---------------------------------------------------------------------------


def test_snapshot_returns_axis_values() -> None:
    state = DispatcherState()
    _do_handshake(state)
    dispatch(
        state,
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=60,
            payload=register_axis_payload(
                name="a",
                axis_class="appetite",
                fruiting_threshold=10.0,
                initial_value=0.0,
                decay_rate_per_cycle=1.0,
                is_mortality_signal=False,
                update_rule_kind="noop",
            ),
        ),
    )
    dispatch(
        state,
        Message(
            type=MessageType.PERTURB,
            request_id=61,
            payload=perturb_payload("a", 2.5),
        ),
    )
    response = dispatch(
        state,
        Message(
            type=MessageType.SNAPSHOT,
            request_id=62,
            payload=empty_payload(),
        ),
    )
    assert response is not None
    assert response.type is MessageType.SNAPSHOT_RESPONSE
    values_map = dict(response.payload.value)["values"]
    assert isinstance(values_map, CbMap)
    values_dict = dict(values_map.value)
    assert expect_string(values_dict["a"]) == "2.5"


# ---------------------------------------------------------------------------
# Shutdown.
# ---------------------------------------------------------------------------


def test_shutdown_returns_ack() -> None:
    state = DispatcherState()
    _do_handshake(state)
    response = dispatch(
        state,
        Message(
            type=MessageType.SHUTDOWN,
            request_id=999,
            payload=empty_payload(),
        ),
    )
    assert response is not None
    assert response.type is MessageType.SHUTDOWN_ACK
    assert response.request_id == 999


# ---------------------------------------------------------------------------
# Error envelope construction.
# ---------------------------------------------------------------------------


def test_build_error_response() -> None:
    err = build_error_response(42, "test_code", "test message")
    assert err.type is MessageType.ERROR
    assert err.request_id == 42
    payload = dict(err.payload.value)
    assert expect_string(payload["code"]) == "test_code"
    assert expect_string(payload["message"]) == "test message"
