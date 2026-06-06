"""Cryptographic primitives — Python implementation (L1/SCHEMA §2.1 + L1/SKIN §2).

MUST produce byte-identical output to:

- ``kernel/shared/src/crypto.rs`` (Rust reference)
- ``operators/claude/src/canonical/crypto.ts`` (TypeScript)

Cross-language test vectors at ``test_vectors/crypto_v1.json``.

Primitives
----------

- :func:`merkle_hash` — BLAKE3 with parent-count prefix
  (per L1/SCHEMA §2.1 + pass-3 mycoparasite-2).
- :func:`hmac_sign` — HMAC-SHA256 (per L1/SKIN §2 envelope_digest).
- :func:`hmac_verify` — constant-time HMAC verification.
- :func:`verify_signature` — Ed25519 (RFC 8032).

v0.9 keyless: there is no owner key. The Ed25519 primitives verify the
substrate's OWN F24 signing keypair (snapshot.cb + federation FED_HELLO) and
the per-handshake operator keypair — substrate/session crypto, not an owner
key. The suite choice per L1/GOVERNANCE §7 is L4-pick within {Ed25519,
ECDSA-P256, post-quantum}; Ed25519 is the current pick.
"""

from __future__ import annotations

import hashlib
import hmac
import struct
from dataclasses import dataclass

from blake3 import blake3
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey as _RawEd25519PrivateKey,
    Ed25519PublicKey as _RawEd25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


# ---------------------------------------------------------------------------
# Error types.
# ---------------------------------------------------------------------------


class CryptoError(Exception):
    """Base crypto error (mirrors Rust ``CryptoError``)."""


class HmacEmptyKey(CryptoError):
    """HMAC keyed by an empty key (forbidden per L1/SKIN §2)."""


class HmacInvalid(CryptoError):
    """HMAC verification failed."""


class SignatureInvalid(CryptoError):
    """Signature verification failed."""


class PublicKeyMalformed(CryptoError):
    """Public key bytes are malformed for Ed25519."""


class SignatureMalformed(CryptoError):
    """Signature bytes are malformed for Ed25519."""


class PrivateKeyMalformed(CryptoError):
    """Private key seed bytes are malformed for Ed25519."""


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
    encodings (per pass-3 mycoparasite-2 + L1/HARD_RULES C6/C7).

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

    Per L1/SKIN §2: ``envelope_digest = HMAC(operator_token,
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


# ---------------------------------------------------------------------------
# Ed25519 signature scheme (RFC 8032).
#
# Selected for M2 per L1/GOVERNANCE §7 candidate set. L4-owner-changeable at
# genesis time; M2 hard-codes Ed25519.
# ---------------------------------------------------------------------------


PUBLIC_KEY_LENGTH = 32
SECRET_KEY_LENGTH = 32
SIGNATURE_LENGTH = 64


@dataclass(frozen=True, slots=True)
class Ed25519PublicKey:
    """Ed25519 public key (32 bytes; RFC 8032 compressed form)."""

    bytes_: bytes

    def __post_init__(self) -> None:
        if len(self.bytes_) != PUBLIC_KEY_LENGTH:
            raise PublicKeyMalformed(
                f"expected {PUBLIC_KEY_LENGTH} bytes, got {len(self.bytes_)}"
            )
        # Validate by attempting to construct the underlying pubkey object.
        # ``from_public_bytes`` raises ValueError on malformed encoding and
        # UnsupportedAlgorithm if the backend lacks Ed25519 — both mean the
        # key bytes are unusable. Other exceptions (e.g. TypeError) signal a
        # caller bug and should propagate unmasked.
        try:
            _RawEd25519PublicKey.from_public_bytes(self.bytes_)
        except (ValueError, UnsupportedAlgorithm) as e:
            raise PublicKeyMalformed(str(e)) from e

    def to_hex(self) -> str:
        return self.bytes_.hex()

    @classmethod
    def from_hex(cls, hex_str: str) -> Ed25519PublicKey:
        return cls(bytes.fromhex(hex_str))


@dataclass(frozen=True, slots=True)
class Ed25519Signature:
    """Ed25519 signature (64 bytes; RFC 8032)."""

    bytes_: bytes

    def __post_init__(self) -> None:
        if len(self.bytes_) != SIGNATURE_LENGTH:
            raise SignatureMalformed(
                f"expected {SIGNATURE_LENGTH} bytes, got {len(self.bytes_)}"
            )

    def to_hex(self) -> str:
        return self.bytes_.hex()

    @classmethod
    def from_hex(cls, hex_str: str) -> Ed25519Signature:
        return cls(bytes.fromhex(hex_str))


class Ed25519PrivateKey:
    """Ed25519 private key (32-byte seed).

    v0.9 keyless: there is no owner key, so this is never a foreign/owner
    private key. It is held only by the substrate (for its OWN F24 signing
    keypair — snapshot.cb + federation FED_HELLO; sealed at rest), by operators
    (per-handshake keypair), and by cross-language parity vectors + tests.
    """

    __slots__ = ("_inner",)

    def __init__(self, seed: bytes) -> None:
        if len(seed) != SECRET_KEY_LENGTH:
            raise PrivateKeyMalformed(
                f"expected {SECRET_KEY_LENGTH} bytes, got {len(seed)}"
            )
        self._inner = _RawEd25519PrivateKey.from_private_bytes(seed)

    @classmethod
    def from_seed(cls, seed: bytes) -> Ed25519PrivateKey:
        return cls(seed)

    @classmethod
    def from_hex(cls, hex_str: str) -> Ed25519PrivateKey:
        return cls(bytes.fromhex(hex_str))

    def public_key(self) -> Ed25519PublicKey:
        raw = self._inner.public_key().public_bytes(
            encoding=Encoding.Raw, format=PublicFormat.Raw
        )
        return Ed25519PublicKey(raw)

    def sign(self, message: bytes) -> Ed25519Signature:
        """Sign a message. Per RFC 8032 Ed25519 is deterministic."""
        sig = self._inner.sign(message)
        return Ed25519Signature(sig)

    def seed_bytes(self) -> bytes:
        """Return the private key seed bytes.

        Handle with care: only the substrate's own sealed-storage path (for the
        F24 keypair) and operator-side code legitimately need the raw seed; a
        seed MUST NOT be exported into an unsealed location.
        """
        return self._inner.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption(),
        )

    def __repr__(self) -> str:
        # Never leak the seed in repr/debug output.
        return "Ed25519PrivateKey(seed=<redacted>)"


def verify_signature(
    public_key: bytes,
    signature: bytes,
    message: bytes,
) -> None:
    """Verify an Ed25519 signature against a public key and message.

    Per L1/GOVERNANCE §2.3. v0.9 keyless: there is no owner signature to
    verify. This verifies a signature: the substrate's OWN F24 keypair
    (snapshot.cb integrity), a federation peer's FED_HELLO, or a per-handshake
    operator signature, never an owner key.

    Raises:
        PublicKeyMalformed: if ``public_key`` is not 32 bytes or not a valid
            Ed25519 point.
        SignatureMalformed: if ``signature`` is not 64 bytes.
        SignatureInvalid: if the signature does not verify against
            ``(public_key, message)``.
    """
    if len(public_key) != PUBLIC_KEY_LENGTH:
        raise PublicKeyMalformed(
            f"expected {PUBLIC_KEY_LENGTH} bytes, got {len(public_key)}"
        )
    if len(signature) != SIGNATURE_LENGTH:
        raise SignatureMalformed(
            f"expected {SIGNATURE_LENGTH} bytes, got {len(signature)}"
        )

    try:
        pk = _RawEd25519PublicKey.from_public_bytes(public_key)
    except (ValueError, UnsupportedAlgorithm) as e:
        raise PublicKeyMalformed(str(e)) from e

    try:
        pk.verify(signature, message)
    except InvalidSignature as e:
        raise SignatureInvalid("signature does not verify") from e
