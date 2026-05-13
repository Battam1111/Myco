"""Cryptographic primitives — Python implementation (L1_SCHEMA §2.1 + L1_SKIN §2).

MUST produce byte-identical output to:

- ``kernel/shared/src/crypto.rs`` (Rust reference)
- ``anchor_client/src/crypto.ts`` (TypeScript)

Cross-language test vectors at ``test_vectors/crypto_v1.json``.

Primitives
----------

- :func:`merkle_hash` — BLAKE3 with parent-count prefix
  (per L1_SCHEMA §2.1 + pass-3 mycoparasite-2).
- :func:`hmac_sign` — HMAC-SHA256 (per L1_SKIN §2 envelope_digest).
- :func:`hmac_verify` — constant-time HMAC verification.

Signature verification is M2-deferred (algorithm choice per
L1_GOVERNANCE §7 is L4-pick within {Ed25519, ECDSA-P256, post-quantum}).
"""

from __future__ import annotations

import hashlib
import hmac
import struct
from dataclasses import dataclass

from blake3 import blake3


# ---------------------------------------------------------------------------
# Error types.
# ---------------------------------------------------------------------------


class CryptoError(Exception):
    """Base crypto error (mirrors Rust ``CryptoError``)."""


class HmacEmptyKey(CryptoError):
    """HMAC keyed by an empty key (forbidden per L1_SKIN §2)."""


class HmacInvalid(CryptoError):
    """HMAC verification failed."""


class SignatureInvalid(CryptoError):
    """Signature verification failed (M2 stub)."""


# ---------------------------------------------------------------------------
# Newtype wrappers for type-safety + clarity.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NodeHash:
    """Content-addressed Merkle hash. 32 bytes; BLAKE3-default."""

    bytes_: bytes

    def __post_init__(self) -> None:
        if len(self.bytes_) != 32:
            raise CryptoError(
                f"NodeHash must be exactly 32 bytes; got {len(self.bytes_)}"
            )

    def to_hex(self) -> str:
        """Lowercase 64-char hex representation."""
        return self.bytes_.hex()

    @classmethod
    def from_hex(cls, hex_str: str) -> NodeHash:
        """Construct from a 64-char hex string."""
        return cls(bytes.fromhex(hex_str))


@dataclass(frozen=True, slots=True)
class HmacTag:
    """HMAC-SHA256 tag. 32 bytes."""

    bytes_: bytes

    def __post_init__(self) -> None:
        if len(self.bytes_) != 32:
            raise CryptoError(
                f"HmacTag must be exactly 32 bytes; got {len(self.bytes_)}"
            )

    def to_hex(self) -> str:
        return self.bytes_.hex()

    @classmethod
    def from_hex(cls, hex_str: str) -> HmacTag:
        return cls(bytes.fromhex(hex_str))


# ---------------------------------------------------------------------------
# Primitives.
# ---------------------------------------------------------------------------


def merkle_hash(parent_hashes: list[NodeHash] | tuple[NodeHash, ...], content_canonical_bytes: bytes) -> NodeHash:
    """Compute the Merkle hash of a DAG node from its parent hashes + content.

    Hash = BLAKE3(parent_count_be_u64 || parents_concat || content)

    The parent-count prefix prevents ambiguity attacks between
    ``(N parents, M-byte content)`` and ``(N+1 parents, (M - parent_hash_size)-byte content)``
    encodings (per pass-3 mycoparasite-2 + L1_HARD_RULES C6/C7).

    Args:
        parent_hashes: causal parent node hashes in declared order.
        content_canonical_bytes: canonical-bytes content of this node.

    Returns:
        :class:`NodeHash` — 32-byte BLAKE3 digest.
    """
    h = blake3()
    h.update(struct.pack(">Q", len(parent_hashes)))
    for ph in parent_hashes:
        h.update(ph.bytes_)
    h.update(content_canonical_bytes)
    return NodeHash(h.digest())


def hmac_sign(key: bytes, canonical_bytes: bytes) -> HmacTag:
    """Compute HMAC-SHA256 over ``canonical_bytes`` keyed by ``key``.

    Per L1_SKIN §2: ``envelope_digest = HMAC(operator_token,
    canonical_envelope_fields || payload)``. Empty key forbidden.

    Args:
        key: HMAC key bytes (typically the operator_token from handshake).
        canonical_bytes: the message bytes to authenticate.

    Returns:
        :class:`HmacTag` — 32-byte HMAC-SHA256 tag.

    Raises:
        HmacEmptyKey: if ``key`` is empty.
    """
    if not key:
        raise HmacEmptyKey("HMAC key cannot be empty")
    mac = hmac.new(key, canonical_bytes, hashlib.sha256)
    return HmacTag(mac.digest())


def hmac_verify(key: bytes, canonical_bytes: bytes, tag: HmacTag) -> None:
    """Verify an HMAC-SHA256 tag matches the canonical bytes under the given key.

    Constant-time comparison via :func:`hmac.compare_digest`.

    Raises:
        HmacEmptyKey: if ``key`` is empty.
        HmacInvalid: if the recomputed tag does not match ``tag``.
    """
    if not key:
        raise HmacEmptyKey("HMAC key cannot be empty")
    expected = hmac_sign(key, canonical_bytes)
    if not hmac.compare_digest(expected.bytes_, tag.bytes_):
        raise HmacInvalid("HMAC verification failed")


def verify_signature(
    _public_key: bytes,
    _signature: bytes,
    _canonical_bytes: bytes,
) -> None:
    """Verify a signature (M2 stub — actual algorithm M2-decided).

    L1_GOVERNANCE §7 lists Ed25519, ECDSA-P256, post-quantum candidates as
    L4 options. M2 stub returns SignatureInvalid for any non-empty signature;
    M3+ lands the production path with the chosen algorithm.
    """
    raise SignatureInvalid("verify_signature M2 stub — algorithm choice pending")
