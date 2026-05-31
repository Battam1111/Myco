"""Cross-language parity tests for canonical-bytes serializer.

Loads ``test_vectors/canonical_bytes_v1.json`` and verifies that the Python
implementation produces byte-identical output to the spec. Same JSON is
consumed by Rust and TypeScript implementations.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import pytest

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Bytes,
    CanonicalBytes,
    CanonicalBytesError,
    Hash,
    Int,
    Map,
    Null,
    String,
    Timestamp,
    Uint,
    Value,
    encode,
    write_varint,
)


# Locate the shared test vectors file relative to this test file.
_VECTORS_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "test_vectors"
    / "canonical_bytes_v1.json"
)


def _load_vectors() -> dict[str, Any]:
    with _VECTORS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


_VECTORS = _load_vectors()


# ---------------------------------------------------------------------------
# Spec → Value converter.
# ---------------------------------------------------------------------------


def _load_value(spec: dict[str, Any]) -> Value:
    """Convert a test-vector InputSpec dict into a runtime Value."""
    tag = spec["type"]

    if tag == "null":
        return Null()

    if tag == "bool":
        return Bool(spec["value"])

    if tag == "int":
        v = (
            int(spec["value_decimal_str"])
            if "value_decimal_str" in spec
            else spec["value"]
        )
        return Int(v)

    if tag == "uint":
        v = (
            int(spec["value_decimal_str"])
            if "value_decimal_str" in spec
            else spec["value"]
        )
        return Uint(v)

    if tag == "string":
        if "value" in spec:
            return String(spec["value"])
        if "value_utf8_hex" in spec:
            return String(bytes.fromhex(spec["value_utf8_hex"]).decode("utf-8"))
        raise ValueError("string case missing value/value_utf8_hex")

    if tag == "bytes":
        if "value_hex" in spec:
            return Bytes(bytes.fromhex(spec["value_hex"]))
        if "value_hex_repeat" in spec:
            byte = int(spec["value_hex_repeat"]["byte"], 16)
            count = spec["value_hex_repeat"]["count"]
            return Bytes(bytes([byte] * count))
        raise ValueError("bytes case missing value_hex/value_hex_repeat")

    if tag == "array":
        items = tuple(_load_value(item) for item in spec["value"])
        return Array(items)

    if tag == "map":
        # Preserve insertion order; Map sorts at encode time.
        pairs = tuple((k, _load_value(v)) for k, v in spec["value"].items())
        return Map(pairs)

    if tag == "timestamp":
        v = (
            int(spec["value_decimal_str"])
            if "value_decimal_str" in spec
            else spec["value"]
        )
        return Timestamp(v)

    if tag == "hash":
        return Hash(bytes.fromhex(spec["value_hex"]))

    raise ValueError(f"unknown tag: {tag}")


# ---------------------------------------------------------------------------
# Cross-language parity tests — one per vector.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vector",
    _VECTORS["vectors"],
    ids=lambda v: v["name"],
)
def test_canonical_bytes_vector(vector: dict[str, Any]) -> None:
    value = _load_value(vector["input"])
    got = encode(value)
    expected_hex = vector["output_hex"]
    assert got.to_hex() == expected_hex, (
        f'vector "{vector["name"]}" mismatch:\n'
        f"  expected: {expected_hex}\n"
        f"  got:      {got.to_hex()}"
    )


@pytest.mark.parametrize(
    "varint",
    _VECTORS["varint_vectors"],
    ids=lambda v: f"varint_{v['input']}",
)
def test_varint_vector(varint: dict[str, Any]) -> None:
    buf = bytearray()
    write_varint(varint["input"], buf)
    got_hex = bytes(buf).hex()
    assert got_hex == varint["output_hex"], (
        f"varint({varint['input']}) mismatch:\n"
        f"  expected: {varint['output_hex']}\n"
        f"  got:      {got_hex}"
    )


@pytest.mark.parametrize(
    "vector",
    _VECTORS["float_vectors"],
    ids=lambda v: v["name"],
)
def test_float_vector(vector: dict[str, Any]) -> None:
    """Cross-language float-render parity (Python side / oracle).

    Floats are encoded in canonical-bytes as ``String(repr(x))`` (there is no
    float tag). CPython ``repr(float)`` is the canonical oracle the Rust and
    TypeScript implementations must reproduce; this test pins the vectors'
    ``expected_repr`` against the live CPython ``repr`` so that (a) the vector
    file can never drift from the oracle it documents, and (b) a CPython version
    whose ``repr`` changed would be caught here. Drift = the float facet of
    L1/HARD_RULES C18 ``canonical_bytes_render_drift`` (CRITICAL).
    """
    x = struct.unpack(">d", bytes.fromhex(vector["f64_be_hex"]))[0]
    got = repr(x)
    assert got == vector["expected_repr"], (
        f'float vector "{vector["name"]}" mismatch:\n'
        f"  expected: {vector['expected_repr']}\n"
        f"  got:      {got}"
    )


# ---------------------------------------------------------------------------
# Property + error tests.
# ---------------------------------------------------------------------------


def test_determinism() -> None:
    """Encoding the same value twice gives identical bytes."""
    v = Map.from_dict(
        {
            "a": Bool(True),
            "b": Int(42),
            "c": Array((Null(), String("x"))),
        }
    )
    assert encode(v).to_hex() == encode(v).to_hex()


def test_hash_wrong_length() -> None:
    with pytest.raises(CanonicalBytesError, match="32 bytes"):
        encode(Hash(b"\x00" * 16))


def test_varint_negative() -> None:
    with pytest.raises(CanonicalBytesError, match="negative"):
        write_varint(-1, bytearray())


def test_int_overflow_positive() -> None:
    with pytest.raises(CanonicalBytesError, match="i64 out of range"):
        encode(Int(1 << 63))


def test_int_overflow_negative() -> None:
    with pytest.raises(CanonicalBytesError, match="i64 out of range"):
        encode(Int(-(1 << 63) - 1))


def test_uint_negative() -> None:
    with pytest.raises(CanonicalBytesError, match="u64 out of range"):
        encode(Uint(-1))


def test_uint_overflow() -> None:
    with pytest.raises(CanonicalBytesError, match="u64 out of range"):
        encode(Uint(1 << 64))


def test_canonical_bytes_repr_round_trip() -> None:
    """CanonicalBytes(b) → to_hex() → back-decode → original bytes."""
    raw = b"\x00\x01\x02\xff\xaa"
    cb = CanonicalBytes(raw)
    assert cb.bytes_ == raw
    assert bytes.fromhex(cb.to_hex()) == raw
    assert len(cb) == 5


def test_map_insertion_order_independent() -> None:
    """Different insertion orders of the same key-value set produce identical bytes."""
    m1 = Map.from_dict({"z": Int(1), "a": Int(2), "m": Int(3)})
    m2 = Map.from_dict({"a": Int(2), "m": Int(3), "z": Int(1)})
    m3 = Map.from_dict({"m": Int(3), "z": Int(1), "a": Int(2)})
    assert encode(m1).to_hex() == encode(m2).to_hex() == encode(m3).to_hex()
