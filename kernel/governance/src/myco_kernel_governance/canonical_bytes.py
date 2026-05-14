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


# ---------------------------------------------------------------------------
# Decoder — reverse of encode. Added at M5 to support the cross-process
# bridge (kernel/bridge_python) which needs to decode canonical-bytes frames
# arriving from the Rust controller over stdio.
# ---------------------------------------------------------------------------


def read_varint(buf: bytes, offset: int) -> tuple[int, int]:
    """Read a varint from ``buf`` starting at ``offset``.

    Returns ``(value, new_offset)``. Mirrors the Rust ``read_varint``.

    Raises:
        CanonicalBytesError: on truncation or overflow (more than 10 bytes).
    """
    result = 0
    shift = 0
    cur = offset
    for _ in range(10):
        if cur >= len(buf):
            raise CanonicalBytesError("varint truncated")
        byte = buf[cur]
        cur += 1
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            return result, cur
        shift += 7
    raise CanonicalBytesError("varint too long (>10 bytes)")


def decode(buf: bytes) -> Value:
    """Decode canonical bytes into a :class:`Value` tree.

    Inverse of :func:`encode`: ``encode(decode(b)) == b`` for any canonical
    bytes produced by :func:`encode`. Drift between any implementation's
    decode and any other's encode = L1_HARD_RULES C18.

    Raises:
        CanonicalBytesError: on malformed input (unknown tag, truncated
            payload, trailing bytes, oversized varint, invalid UTF-8, etc.).
    """
    value, cursor = _decode_into(buf, 0)
    if cursor != len(buf):
        raise CanonicalBytesError(
            f"trailing bytes after decode: consumed {cursor}/{len(buf)}"
        )
    return value


def _decode_into(buf: bytes, offset: int) -> tuple[Value, int]:
    if offset >= len(buf):
        raise CanonicalBytesError("decode: input truncated")
    tag = buf[offset]
    cursor = offset + 1

    if tag == TAG_NULL:
        return Null(), cursor

    if tag == TAG_BOOL:
        if cursor >= len(buf):
            raise CanonicalBytesError("decode: bool payload truncated")
        b = buf[cursor]
        if b not in (0x00, 0x01):
            raise CanonicalBytesError(f"decode: invalid bool byte {b:#x}")
        return Bool(b == 0x01), cursor + 1

    if tag == TAG_INT:
        if cursor + 8 > len(buf):
            raise CanonicalBytesError("decode: int payload truncated")
        (value,) = struct.unpack(">q", buf[cursor : cursor + 8])
        return Int(value), cursor + 8

    if tag == TAG_UINT:
        if cursor + 8 > len(buf):
            raise CanonicalBytesError("decode: uint payload truncated")
        (value,) = struct.unpack(">Q", buf[cursor : cursor + 8])
        return Uint(value), cursor + 8

    if tag == TAG_STRING:
        length, cursor = read_varint(buf, cursor)
        if cursor + length > len(buf):
            raise CanonicalBytesError("decode: string payload truncated")
        raw = bytes(buf[cursor : cursor + length])
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            raise CanonicalBytesError(f"decode: invalid utf-8: {e}") from e
        return String(text), cursor + length

    if tag == TAG_BYTES:
        length, cursor = read_varint(buf, cursor)
        if cursor + length > len(buf):
            raise CanonicalBytesError("decode: bytes payload truncated")
        raw = bytes(buf[cursor : cursor + length])
        return Bytes(raw), cursor + length

    if tag == TAG_ARRAY:
        count, cursor = read_varint(buf, cursor)
        items: list[Value] = []
        for _ in range(count):
            item, cursor = _decode_into(buf, cursor)
            items.append(item)
        return Array(tuple(items)), cursor

    if tag == TAG_MAP:
        count, cursor = read_varint(buf, cursor)
        entries: list[tuple[str, Value]] = []
        prev_key_bytes: bytes | None = None
        for _ in range(count):
            # Each entry: canonical-bytes-of-key followed by canonical-bytes-of-value.
            key_value, key_end = _decode_into(buf, cursor)
            if not isinstance(key_value, String):
                raise CanonicalBytesError(
                    f"decode: map key is not String: {type(key_value).__name__}"
                )
            key_canonical = bytes(buf[cursor:key_end])
            # Enforce strict canonical ordering during decode (defense in depth
            # against malformed input that bypassed the encoder's sort step).
            if prev_key_bytes is not None and key_canonical <= prev_key_bytes:
                raise CanonicalBytesError(
                    "decode: map keys not in strict canonical order"
                )
            prev_key_bytes = key_canonical
            val, cursor = _decode_into(buf, key_end)
            entries.append((key_value.value, val))
        return Map(tuple(entries)), cursor

    if tag == TAG_TIMESTAMP:
        if cursor + 8 > len(buf):
            raise CanonicalBytesError("decode: timestamp payload truncated")
        (value,) = struct.unpack(">q", buf[cursor : cursor + 8])
        return Timestamp(value), cursor + 8

    if tag == TAG_HASH:
        if cursor + 32 > len(buf):
            raise CanonicalBytesError("decode: hash payload truncated")
        raw = bytes(buf[cursor : cursor + 32])
        return Hash(raw), cursor + 32

    raise CanonicalBytesError(f"decode: unknown tag {tag:#x}")


def map_get(value: Value, key: str) -> Value:
    """Helper: extract a key from a :class:`Map` value. Raises on type or key error."""
    if not isinstance(value, Map):
        raise CanonicalBytesError(f"map_get: not a Map: {type(value).__name__}")
    for k, v in value.value:
        if k == key:
            return v
    raise CanonicalBytesError(f"map_get: missing key {key!r}")


def expect_string(value: Value) -> str:
    """Helper: assert ``value`` is a :class:`String` and return its content."""
    if not isinstance(value, String):
        raise CanonicalBytesError(f"expect_string: not a String: {type(value).__name__}")
    return value.value


def expect_uint(value: Value) -> int:
    """Helper: assert ``value`` is a :class:`Uint` and return its content."""
    if not isinstance(value, Uint):
        raise CanonicalBytesError(f"expect_uint: not a Uint: {type(value).__name__}")
    return value.value


def expect_bytes(value: Value) -> bytes:
    """Helper: assert ``value`` is a :class:`Bytes` and return its content."""
    if not isinstance(value, Bytes):
        raise CanonicalBytesError(f"expect_bytes: not a Bytes: {type(value).__name__}")
    return value.value


def expect_map(value: Value) -> Map:
    """Helper: assert ``value`` is a :class:`Map` and return it."""
    if not isinstance(value, Map):
        raise CanonicalBytesError(f"expect_map: not a Map: {type(value).__name__}")
    return value


def expect_array(value: Value) -> tuple[Value, ...]:
    """Helper: assert ``value`` is an :class:`Array` and return its content."""
    if not isinstance(value, Array):
        raise CanonicalBytesError(f"expect_array: not an Array: {type(value).__name__}")
    return value.value


def expect_bool(value: Value) -> bool:
    """Helper: assert ``value`` is a :class:`Bool` and return its content."""
    if not isinstance(value, Bool):
        raise CanonicalBytesError(f"expect_bool: not a Bool: {type(value).__name__}")
    return value.value
