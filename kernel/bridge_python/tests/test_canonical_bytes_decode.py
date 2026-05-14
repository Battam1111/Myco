"""Decoder roundtrip tests for myco_kernel_governance.canonical_bytes.decode.

The decoder was added at M5 to support the cross-process bridge. These
tests verify that ``decode(encode(v)) == v`` for every supported value
shape and that malformed inputs are rejected.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Bytes,
    CanonicalBytesError,
    Hash,
    Int,
    Map,
    Null,
    String,
    Timestamp,
    Uint,
    Value,
    decode,
    encode,
    read_varint,
)


# ---------------------------------------------------------------------------
# Roundtrip property tests.
# ---------------------------------------------------------------------------


def _roundtrip(value: Value) -> None:
    """Assert encode → decode → encode produces identical bytes."""
    bytes1 = encode(value)
    decoded = decode(bytes1.bytes_)
    bytes2 = encode(decoded)
    assert bytes1.bytes_ == bytes2.bytes_


def test_roundtrip_null() -> None:
    _roundtrip(Null())


def test_roundtrip_bool_true() -> None:
    _roundtrip(Bool(True))


def test_roundtrip_bool_false() -> None:
    _roundtrip(Bool(False))


def test_roundtrip_int_zero() -> None:
    _roundtrip(Int(0))


def test_roundtrip_int_positive() -> None:
    _roundtrip(Int(42))


def test_roundtrip_int_negative() -> None:
    _roundtrip(Int(-12345))


def test_roundtrip_int_min() -> None:
    _roundtrip(Int(-(1 << 63)))


def test_roundtrip_int_max() -> None:
    _roundtrip(Int((1 << 63) - 1))


def test_roundtrip_uint_zero() -> None:
    _roundtrip(Uint(0))


def test_roundtrip_uint_max() -> None:
    _roundtrip(Uint((1 << 64) - 1))


def test_roundtrip_string_empty() -> None:
    _roundtrip(String(""))


def test_roundtrip_string_ascii() -> None:
    _roundtrip(String("hello world"))


def test_roundtrip_string_unicode() -> None:
    _roundtrip(String("Мусоиёр 蘑菇 кружок"))


def test_roundtrip_bytes_empty() -> None:
    _roundtrip(Bytes(b""))


def test_roundtrip_bytes_short() -> None:
    _roundtrip(Bytes(b"\x00\x01\x02\xff"))


def test_roundtrip_bytes_long() -> None:
    _roundtrip(Bytes(bytes(range(256)) * 4))


def test_roundtrip_array_empty() -> None:
    _roundtrip(Array(()))


def test_roundtrip_array_mixed() -> None:
    _roundtrip(
        Array((Null(), Bool(True), Int(42), String("x"), Bytes(b"\xab")))
    )


def test_roundtrip_array_nested() -> None:
    _roundtrip(
        Array(
            (
                Array((Int(1), Int(2))),
                Array((String("a"),)),
            )
        )
    )


def test_roundtrip_map_empty() -> None:
    _roundtrip(Map(()))


def test_roundtrip_map_basic() -> None:
    _roundtrip(
        Map.from_dict(
            {
                "z": Int(1),
                "a": String("alpha"),
                "m": Bool(False),
            }
        )
    )


def test_roundtrip_map_nested() -> None:
    _roundtrip(
        Map.from_dict(
            {
                "outer": Map.from_dict(
                    {
                        "inner_a": Int(1),
                        "inner_b": Array((Int(2), Int(3))),
                    }
                ),
                "sibling": Null(),
            }
        )
    )


def test_roundtrip_timestamp() -> None:
    _roundtrip(Timestamp(1_700_000_000_000_000_000))


def test_roundtrip_hash() -> None:
    _roundtrip(Hash(b"\xab" * 32))


def test_roundtrip_deeply_nested() -> None:
    v: Value = Int(0)
    for i in range(20):
        v = Map.from_dict({f"level_{i}": v, "i": Uint(i)})
    _roundtrip(v)


# ---------------------------------------------------------------------------
# Error-path tests.
# ---------------------------------------------------------------------------


def test_decode_unknown_tag() -> None:
    with pytest.raises(CanonicalBytesError, match="unknown tag"):
        decode(b"\xff")


def test_decode_truncated() -> None:
    with pytest.raises(CanonicalBytesError, match="truncated"):
        decode(b"\x10\x00")  # int tag but only 2 bytes (need 8)


def test_decode_trailing_bytes() -> None:
    # A valid Null + an extra byte = trailing bytes error.
    with pytest.raises(CanonicalBytesError, match="trailing bytes"):
        decode(b"\x00\xff")


def test_decode_invalid_bool() -> None:
    with pytest.raises(CanonicalBytesError, match="invalid bool"):
        decode(b"\x01\x02")  # bool tag + 0x02 (invalid)


def test_decode_invalid_utf8() -> None:
    # String tag + length 1 + 0xff (invalid UTF-8 start byte).
    with pytest.raises(CanonicalBytesError, match="utf-8"):
        decode(b"\x20\x01\xff")


def test_decode_map_keys_unsorted_rejected() -> None:
    """An attacker-crafted byte stream with out-of-order map keys must be rejected."""
    # Map tag + count=2 + key "z" + value Null + key "a" + value Null.
    # This is INVALID because "z" should sort after "a" in canonical order.
    payload = (
        b"\x31\x02"
        + b"\x20\x01z\x00"  # key "z", value Null
        + b"\x20\x01a\x00"  # key "a", value Null
    )
    with pytest.raises(CanonicalBytesError, match="canonical order"):
        decode(payload)


# ---------------------------------------------------------------------------
# Cross-language JSON-vector roundtrip parity.
# ---------------------------------------------------------------------------


def _project_root() -> Path:
    # __file__ → kernel/bridge_python/tests/this_file.py
    # parents[0]=tests, [1]=bridge_python, [2]=kernel, [3]=workspace root.
    return Path(__file__).resolve().parents[3]


def test_all_canonical_bytes_vectors_roundtrip() -> None:
    """Every canonical-bytes test vector should decode and re-encode to its
    exact original bytes."""
    vectors_path = _project_root() / "test_vectors" / "canonical_bytes_v1.json"
    data = json.loads(vectors_path.read_text(encoding="utf-8"))
    cases = data["vectors"]
    for case in cases:
        hex_bytes = case["output_hex"]
        original = bytes.fromhex(hex_bytes)
        decoded = decode(original)
        reencoded = encode(decoded)
        assert reencoded.bytes_ == original, (
            f"roundtrip drift on case {case.get('name')!r}: "
            f"original={hex_bytes}, reencoded={reencoded.to_hex()}"
        )


# ---------------------------------------------------------------------------
# Varint reader edge cases.
# ---------------------------------------------------------------------------


def test_read_varint_zero() -> None:
    value, cursor = read_varint(b"\x00", 0)
    assert value == 0
    assert cursor == 1


def test_read_varint_one_byte_max() -> None:
    value, cursor = read_varint(b"\x7f", 0)
    assert value == 127
    assert cursor == 1


def test_read_varint_two_byte() -> None:
    value, cursor = read_varint(b"\x80\x01", 0)
    assert value == 128
    assert cursor == 2


def test_read_varint_truncated() -> None:
    with pytest.raises(CanonicalBytesError, match="truncated"):
        read_varint(b"\x80", 0)  # MSB=1 but no continuation byte


def test_read_varint_too_long() -> None:
    # 11 bytes with MSB=1 each — should reject as overflow.
    with pytest.raises(CanonicalBytesError, match="too long"):
        read_varint(b"\x80" * 11, 0)
