"""Canonical-bytes serializer — Python implementation (L1_SCHEMA §3.1 + L0 §9.3).

MUST produce byte-identical output to:

- ``kernel/shared/src/canonical_bytes.rs`` (Rust reference)
- ``anchor_client/src/canonical_bytes.ts`` (TypeScript)

Cross-language test vectors at ``test_vectors/canonical_bytes_v1.json``.

Drift from spec = L1_HARD_RULES C18 ``canonical_bytes_render_drift`` (CRITICAL).

Doctrine traceability
---------------------

- L0 §9.3: canonical-bytes doctrine. Substrate emits canonical bytes; the
  anchor-surface client renders deterministically for owner review.
- L1_SCHEMA §3.1 + §4.1: the serializer spec is itself part of the spore-schema
  (spore-inheritable) AND a tier-1 SSoT field.
- L1_HARD_RULES C18: any render drift between implementations is a CRITICAL
  skin breach.
- L1_HARD_RULES F16: ``canonical_bytes_serializer_spec`` is an unconditional
  contract-identity-level fixed point.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Final


# ---------------------------------------------------------------------------
# Type tags (must match Rust + TypeScript byte-for-byte).
# ---------------------------------------------------------------------------

TAG_NULL: Final[int] = 0x00
TAG_BOOL: Final[int] = 0x01
TAG_INT: Final[int] = 0x10
TAG_UINT: Final[int] = 0x11
TAG_STRING: Final[int] = 0x20
TAG_BYTES: Final[int] = 0x21
TAG_ARRAY: Final[int] = 0x30
TAG_MAP: Final[int] = 0x31
TAG_TIMESTAMP: Final[int] = 0x40
TAG_HASH: Final[int] = 0x41


# ---------------------------------------------------------------------------
# Typed value tree.
# ---------------------------------------------------------------------------


class Value:
    """Sealed base class — typed values that can be canonically encoded.

    Subclasses correspond 1:1 to variants in Rust ``Value`` enum.
    """

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Null(Value):
    """Null / None / missing."""


@dataclass(frozen=True, slots=True)
class Bool(Value):
    """Boolean."""

    value: bool


@dataclass(frozen=True, slots=True)
class Int(Value):
    """Signed 64-bit integer (two's-complement)."""

    value: int


@dataclass(frozen=True, slots=True)
class Uint(Value):
    """Unsigned 64-bit integer."""

    value: int


@dataclass(frozen=True, slots=True)
class String(Value):
    """UTF-8 string."""

    value: str


@dataclass(frozen=True, slots=True)
class Bytes(Value):
    """Raw byte sequence."""

    value: bytes


@dataclass(frozen=True, slots=True)
class Array(Value):
    """Ordered array; items remain in declared order."""

    value: tuple[Value, ...]


@dataclass(frozen=True, slots=True)
class Map(Value):
    """Map with string keys.

    Keys are stored as a tuple of ``(name, value)`` pairs but sorted by the
    canonical-bytes of the key (NOT alphabetical of the raw string) at
    encoding time.
    """

    value: tuple[tuple[str, Value], ...]

    @classmethod
    def from_dict(cls, d: dict[str, Value]) -> Map:
        """Construct a Map from a dict — preserves dict insertion order."""
        return cls(tuple(d.items()))


@dataclass(frozen=True, slots=True)
class Timestamp(Value):
    """Unix-nanoseconds timestamp."""

    value: int


@dataclass(frozen=True, slots=True)
class Hash(Value):
    """32-byte hash (BLAKE3 / SHA-256 fixed length)."""

    value: bytes


# ---------------------------------------------------------------------------
# Newtype wrapper.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CanonicalBytes:
    """Canonical bytes — newtype wrapping ``bytes`` to prevent accidental mixing.

    Identical inputs MUST produce identical outputs across all language
    implementations.
    """

    bytes_: bytes

    def to_hex(self) -> str:
        """Hex representation (lowercase, no separator)."""
        return self.bytes_.hex()

    def __len__(self) -> int:
        return len(self.bytes_)


class CanonicalBytesError(Exception):
    """Canonical-bytes serialization error."""


# ---------------------------------------------------------------------------
# Varint encoding.
# ---------------------------------------------------------------------------


def write_varint(n: int, buf: bytearray) -> None:
    """Write a varint (7 bits per byte; MSB=1 if more bytes follow; MSB=0 on last).

    Identical to the Rust ``write_varint`` and TypeScript ``writeVarint``.

    Args:
        n: non-negative integer.
        buf: mutable byte buffer to append into.

    Raises:
        CanonicalBytesError: if ``n`` is negative.
    """
    if n < 0:
        raise CanonicalBytesError(f"varint cannot encode negative: {n}")
    while n >= 0x80:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    buf.append(n)


# ---------------------------------------------------------------------------
# Primary encode function.
# ---------------------------------------------------------------------------


def encode(value: Value) -> CanonicalBytes:
    """Encode a :class:`Value` to canonical bytes.

    Deterministic: same input → byte-identical output across all language
    implementations.
    """
    buf = bytearray()
    _encode_into(value, buf)
    return CanonicalBytes(bytes(buf))


def _encode_into(value: Value, buf: bytearray) -> None:
    if isinstance(value, Null):
        buf.append(TAG_NULL)
        return

    if isinstance(value, Bool):
        buf.append(TAG_BOOL)
        buf.append(0x01 if value.value else 0x00)
        return

    if isinstance(value, Int):
        if not (-(1 << 63) <= value.value <= (1 << 63) - 1):
            raise CanonicalBytesError(f"i64 out of range: {value.value}")
        buf.append(TAG_INT)
        # struct '>q' = big-endian signed 8-byte int (two's-complement).
        buf.extend(struct.pack(">q", value.value))
        return

    if isinstance(value, Uint):
        if not (0 <= value.value <= (1 << 64) - 1):
            raise CanonicalBytesError(f"u64 out of range: {value.value}")
        buf.append(TAG_UINT)
        buf.extend(struct.pack(">Q", value.value))
        return

    if isinstance(value, String):
        buf.append(TAG_STRING)
        utf8 = value.value.encode("utf-8")
        write_varint(len(utf8), buf)
        buf.extend(utf8)
        return

    if isinstance(value, Bytes):
        buf.append(TAG_BYTES)
        write_varint(len(value.value), buf)
        buf.extend(value.value)
        return

    if isinstance(value, Array):
        buf.append(TAG_ARRAY)
        write_varint(len(value.value), buf)
        for item in value.value:
            _encode_into(item, buf)
        return

    if isinstance(value, Map):
        buf.append(TAG_MAP)
        write_varint(len(value.value), buf)
        # Sort entries by canonical-bytes of the key (key is String).
        keyed: list[tuple[bytes, Value]] = []
        for k, v in value.value:
            key_cb = encode(String(k))
            keyed.append((key_cb.bytes_, v))
        keyed.sort(key=lambda kv: kv[0])
        for key_canonical, val in keyed:
            buf.extend(key_canonical)
            _encode_into(val, buf)
        return

    if isinstance(value, Timestamp):
        if not (-(1 << 63) <= value.value <= (1 << 63) - 1):
            raise CanonicalBytesError(f"timestamp out of i64 range: {value.value}")
        buf.append(TAG_TIMESTAMP)
        buf.extend(struct.pack(">q", value.value))
        return

    if isinstance(value, Hash):
        if len(value.value) != 32:
            raise CanonicalBytesError(
                f"hash must be exactly 32 bytes; got {len(value.value)}"
            )
        buf.append(TAG_HASH)
        buf.extend(value.value)
        return

    raise CanonicalBytesError(f"unknown value type: {type(value).__name__}")
