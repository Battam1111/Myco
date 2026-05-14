"""Daemon smoke tests — in-process via BytesIO (no subprocess).

These tests drive the full daemon loop end-to-end without an actual
subprocess. The Rust↔Python subprocess e2e test lives in the Rust
``kernel/bridge`` crate.
"""

from __future__ import annotations

import io
import struct

from myco_kernel_bridge.daemon import run_loop
from myco_kernel_bridge.framing import write_frame
from myco_kernel_bridge.protocol import (
    BOOTSTRAP_KEY,
    Message,
    MessageType,
    advance_payload,
    decode_message,
    empty_payload,
    encode_message,
    hello_payload,
    perturb_payload,
    register_axis_payload,
)


SESSION_SECRET = b"\xa5" * 32


def _write_request(
    stream: io.BytesIO, msg: Message, key: bytes
) -> None:
    frame = encode_message(msg, key)
    write_frame(stream, frame)


def _build_input_stream(messages: list[tuple[Message, bytes]]) -> io.BytesIO:
    """Build an input stream from a sequence of (message, key) pairs."""
    out = io.BytesIO()
    for msg, key in messages:
        _write_request(out, msg, key)
    out.seek(0)
    return out


def _read_responses(stream: io.BytesIO, key: bytes) -> list[Message]:
    """Decode all responses from a stream."""
    stream.seek(0)
    raw = stream.read()
    responses = []
    cursor = 0
    while cursor < len(raw):
        if cursor + 4 > len(raw):
            break
        (length,) = struct.unpack(">I", raw[cursor : cursor + 4])
        cursor += 4
        if cursor + length > len(raw):
            break
        frame_body = raw[cursor : cursor + length]
        cursor += length
        responses.append(decode_message(frame_body, key))
    return responses


def test_daemon_handshake_only() -> None:
    """Daemon receives hello → writes hello_ack → exits on EOF."""
    inputs = _build_input_stream(
        [
            (
                Message(
                    type=MessageType.HELLO,
                    request_id=1,
                    payload=hello_payload(SESSION_SECRET),
                ),
                BOOTSTRAP_KEY,
            ),
        ]
    )
    outputs = io.BytesIO()
    exit_code = run_loop(inputs, outputs)
    assert exit_code == 0
    responses = _read_responses(outputs, SESSION_SECRET)
    assert len(responses) == 1
    assert responses[0].type is MessageType.HELLO_ACK
    assert responses[0].request_id == 1


def test_daemon_handshake_then_shutdown() -> None:
    """Daemon completes handshake, processes shutdown, exits cleanly."""
    inputs = _build_input_stream(
        [
            (
                Message(
                    type=MessageType.HELLO,
                    request_id=1,
                    payload=hello_payload(SESSION_SECRET),
                ),
                BOOTSTRAP_KEY,
            ),
            (
                Message(
                    type=MessageType.SHUTDOWN,
                    request_id=2,
                    payload=empty_payload(),
                ),
                SESSION_SECRET,
            ),
        ]
    )
    outputs = io.BytesIO()
    exit_code = run_loop(inputs, outputs)
    assert exit_code == 0
    responses = _read_responses(outputs, SESSION_SECRET)
    assert len(responses) == 2
    assert responses[0].type is MessageType.HELLO_ACK
    assert responses[1].type is MessageType.SHUTDOWN_ACK


def test_daemon_full_cycle_flow() -> None:
    """Register axis → perturb → advance → snapshot → shutdown."""
    inputs = _build_input_stream(
        [
            (
                Message(
                    type=MessageType.HELLO,
                    request_id=1,
                    payload=hello_payload(SESSION_SECRET),
                ),
                BOOTSTRAP_KEY,
            ),
            (
                Message(
                    type=MessageType.REGISTER_AXIS,
                    request_id=2,
                    payload=register_axis_payload(
                        name="curiosity",
                        axis_class="appetite",
                        fruiting_threshold=2.0,
                        initial_value=0.0,
                        decay_rate_per_cycle=1.0,
                        is_mortality_signal=False,
                        update_rule_kind="noop",
                    ),
                ),
                SESSION_SECRET,
            ),
            (
                Message(
                    type=MessageType.PERTURB,
                    request_id=3,
                    payload=perturb_payload("curiosity", 3.0),
                ),
                SESSION_SECRET,
            ),
            (
                Message(
                    type=MessageType.ADVANCE,
                    request_id=4,
                    payload=advance_payload(1),
                ),
                SESSION_SECRET,
            ),
            (
                Message(
                    type=MessageType.SHUTDOWN,
                    request_id=5,
                    payload=empty_payload(),
                ),
                SESSION_SECRET,
            ),
        ]
    )
    outputs = io.BytesIO()
    exit_code = run_loop(inputs, outputs)
    assert exit_code == 0
    responses = _read_responses(outputs, SESSION_SECRET)
    assert [r.type for r in responses] == [
        MessageType.HELLO_ACK,
        MessageType.REGISTER_AXIS_ACK,
        MessageType.PERTURB_ACK,
        MessageType.ADVANCE_RESPONSE,
        MessageType.SHUTDOWN_ACK,
    ]
    # Verify advance response carries a fruited axis.
    advance = responses[3]
    payload_map = dict(advance.payload.value)
    fruited = payload_map["fruited_axes"]
    from myco_kernel_governance.canonical_bytes import expect_array, expect_string  # noqa: PLC0415

    fruited_names = [expect_string(v) for v in expect_array(fruited)]
    assert fruited_names == ["curiosity"]


def test_daemon_pre_handshake_rejected_with_session_error() -> None:
    """Sending a non-hello message before hello → daemon exits 2."""
    inputs = _build_input_stream(
        [
            (
                Message(
                    type=MessageType.ADVANCE,
                    request_id=1,
                    payload=advance_payload(0),
                ),
                BOOTSTRAP_KEY,  # signed with bootstrap key, but wrong type
            ),
        ]
    )
    outputs = io.BytesIO()
    exit_code = run_loop(inputs, outputs)
    # Daemon detected a non-hello message pre-handshake; returns 2.
    assert exit_code == 2


def test_daemon_eof_before_handshake_exits_2() -> None:
    """EOF without any frame at all = exit 2."""
    inputs = io.BytesIO(b"")
    outputs = io.BytesIO()
    exit_code = run_loop(inputs, outputs)
    assert exit_code == 2
