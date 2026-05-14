"""Tests for kernel/bridge_python protocol module: body + frame encode/decode."""

from __future__ import annotations

import pytest

from myco_kernel_governance.canonical_bytes import (
    Bytes as CbBytes,
    Map as CbMap,
    String as CbString,
    Uint as CbUint,
)

from myco_kernel_bridge.protocol import (
    BOOTSTRAP_KEY,
    BridgeProtocolError,
    FrameTooLargeError,
    HmacMismatchError,
    MAX_FRAME_BODY_SIZE,
    Message,
    MessageType,
    PROTOCOL_VERSION,
    VersionMismatchError,
    advance_payload,
    body_to_canonical_bytes,
    canonical_bytes_to_body,
    compute_hmac,
    decode_message,
    empty_payload,
    encode_message,
    error_payload,
    hello_ack_payload,
    hello_payload,
    perturb_payload,
    register_axis_payload,
)


# ---------------------------------------------------------------------------
# Bootstrap key.
# ---------------------------------------------------------------------------


def test_bootstrap_key_is_32_bytes() -> None:
    assert len(BOOTSTRAP_KEY) == 32


def test_bootstrap_key_is_deterministic() -> None:
    """Re-importing should yield identical bytes (deterministic constant)."""
    from myco_kernel_bridge import protocol as fresh_mod  # noqa: PLC0415

    assert fresh_mod.BOOTSTRAP_KEY == BOOTSTRAP_KEY


def test_bootstrap_key_specific_value() -> None:
    """Pin the bootstrap key bytes so any change is an explicit protocol bump."""
    import hashlib  # noqa: PLC0415

    expected = hashlib.sha256(b"myco-bridge-protocol-v1-bootstrap").digest()
    assert BOOTSTRAP_KEY == expected


# ---------------------------------------------------------------------------
# Body encode / decode roundtrip per message type.
# ---------------------------------------------------------------------------


def _roundtrip_body(message: Message) -> None:
    cb = body_to_canonical_bytes(message)
    decoded = canonical_bytes_to_body(cb.bytes_)
    assert decoded.type is message.type
    assert decoded.request_id == message.request_id
    assert decoded.version == PROTOCOL_VERSION
    # The decoded payload Map's tuple ordering reflects canonical-bytes order,
    # which differs from the original's insertion order. Compare via canonical
    # bytes (the actual source of truth for equality).
    assert body_to_canonical_bytes(decoded) == cb


def test_body_roundtrip_hello() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.HELLO,
            request_id=1,
            payload=hello_payload(b"\x42" * 32),
        )
    )


def test_body_roundtrip_hello_ack() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.HELLO_ACK,
            request_id=1,
            payload=hello_ack_payload("0.9.0-alpha.1", "3.13.3"),
        )
    )


def test_body_roundtrip_register_axis_appetite() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=10,
            payload=register_axis_payload(
                name="kernel_evolution_tension",
                axis_class="appetite",
                fruiting_threshold=10.0,
                initial_value=0.0,
                decay_rate_per_cycle=1.0,
                is_mortality_signal=False,
                update_rule_kind="noop",
            ),
        )
    )


def test_body_roundtrip_register_axis_decay() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.REGISTER_AXIS,
            request_id=11,
            payload=register_axis_payload(
                name="mortality_signal",
                axis_class="decay",
                fruiting_threshold=0.01,
                initial_value=1.0,
                decay_rate_per_cycle=0.9,
                is_mortality_signal=True,
                update_rule_kind="decay",
            ),
        )
    )


def test_body_roundtrip_perturb() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.PERTURB,
            request_id=100,
            payload=perturb_payload("x", 2.5),
        )
    )


def test_body_roundtrip_advance() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.ADVANCE,
            request_id=200,
            payload=advance_payload(7),
        )
    )


def test_body_roundtrip_snapshot() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.SNAPSHOT,
            request_id=300,
            payload=empty_payload(),
        )
    )


def test_body_roundtrip_shutdown() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.SHUTDOWN,
            request_id=999,
            payload=empty_payload(),
        )
    )


def test_body_roundtrip_error() -> None:
    _roundtrip_body(
        Message(
            type=MessageType.ERROR,
            request_id=42,
            payload=error_payload("test_code", "test message", 41),
        )
    )


# ---------------------------------------------------------------------------
# Body validation tests.
# ---------------------------------------------------------------------------


def test_body_missing_key_rejected() -> None:
    # Build a body Map with only 3 of 4 required keys.
    bad_body = CbMap.from_dict(
        {
            "v": CbUint(PROTOCOL_VERSION),
            "type": CbString("hello"),
            "request_id": CbUint(0),
            # payload missing
        }
    )
    from myco_kernel_governance.canonical_bytes import encode  # noqa: PLC0415

    bad_bytes = encode(bad_body).bytes_
    with pytest.raises(BridgeProtocolError, match="missing"):
        canonical_bytes_to_body(bad_bytes)


def test_body_unknown_message_type_rejected() -> None:
    bad_body = CbMap.from_dict(
        {
            "v": CbUint(PROTOCOL_VERSION),
            "type": CbString("bogus_type_xyz"),
            "request_id": CbUint(0),
            "payload": CbMap(()),
        }
    )
    from myco_kernel_governance.canonical_bytes import encode  # noqa: PLC0415

    bad_bytes = encode(bad_body).bytes_
    with pytest.raises(BridgeProtocolError, match="unknown message type"):
        canonical_bytes_to_body(bad_bytes)


def test_body_version_mismatch_rejected() -> None:
    bad_body = CbMap.from_dict(
        {
            "v": CbUint(999),  # wrong version
            "type": CbString("hello"),
            "request_id": CbUint(0),
            "payload": CbMap(()),
        }
    )
    from myco_kernel_governance.canonical_bytes import encode  # noqa: PLC0415

    bad_bytes = encode(bad_body).bytes_
    with pytest.raises(VersionMismatchError):
        canonical_bytes_to_body(bad_bytes)


# ---------------------------------------------------------------------------
# Full frame (HMAC + body) encode / decode.
# ---------------------------------------------------------------------------


def test_frame_roundtrip_with_session_key() -> None:
    key = b"\xee" * 32
    msg = Message(
        type=MessageType.ADVANCE,
        request_id=5,
        payload=advance_payload(42),
    )
    frame = encode_message(msg, key)
    decoded = decode_message(frame, key)
    assert decoded.type is MessageType.ADVANCE
    assert decoded.request_id == 5


def test_frame_roundtrip_with_bootstrap_key() -> None:
    msg = Message(
        type=MessageType.HELLO,
        request_id=0,
        payload=hello_payload(b"\x01" * 32),
    )
    frame = encode_message(msg, BOOTSTRAP_KEY)
    decoded = decode_message(frame, BOOTSTRAP_KEY)
    assert decoded.type is MessageType.HELLO


def test_frame_hmac_mismatch_rejected() -> None:
    msg = Message(
        type=MessageType.ADVANCE,
        request_id=5,
        payload=advance_payload(42),
    )
    correct_key = b"\xee" * 32
    wrong_key = b"\x11" * 32
    frame = encode_message(msg, correct_key)
    with pytest.raises(HmacMismatchError):
        decode_message(frame, wrong_key)


def test_frame_corrupted_body_rejected() -> None:
    msg = Message(
        type=MessageType.ADVANCE,
        request_id=5,
        payload=advance_payload(42),
    )
    key = b"\xee" * 32
    frame = bytearray(encode_message(msg, key))
    # Flip a bit in the body (after the 32-byte HMAC).
    frame[40] ^= 0x01
    with pytest.raises(HmacMismatchError):
        decode_message(bytes(frame), key)


def test_frame_too_small_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="too small"):
        decode_message(b"\x00" * 10, BOOTSTRAP_KEY)


def test_compute_hmac_empty_key_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="empty"):
        compute_hmac(b"foo", b"")


# ---------------------------------------------------------------------------
# Payload builder validation.
# ---------------------------------------------------------------------------


def test_hello_payload_invalid_secret_length_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="32 bytes"):
        hello_payload(b"\x00" * 16)


def test_register_axis_payload_invalid_class_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="axis_class"):
        register_axis_payload(
            name="x",
            axis_class="bogus",
            fruiting_threshold=1.0,
            initial_value=0.0,
            decay_rate_per_cycle=1.0,
            is_mortality_signal=False,
            update_rule_kind="noop",
        )


def test_register_axis_payload_invalid_rule_kind_rejected() -> None:
    with pytest.raises(BridgeProtocolError, match="update_rule_kind"):
        register_axis_payload(
            name="x",
            axis_class="appetite",
            fruiting_threshold=1.0,
            initial_value=0.0,
            decay_rate_per_cycle=1.0,
            is_mortality_signal=False,
            update_rule_kind="bogus",
        )
