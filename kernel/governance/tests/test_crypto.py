"""Cross-language crypto parity tests.

Loads ``test_vectors/crypto_v1.json`` and verifies that the Python
implementations of ``merkle_hash`` and ``hmac_sign`` produce byte-identical
output to every vector in the JSON. Same JSON is consumed by Rust and
TypeScript implementations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from myco_kernel_governance.crypto import (
    HmacEmptyKey,
    HmacInvalid,
    HmacTag,
    NodeHash,
    SignatureInvalid,
    hmac_sign,
    hmac_verify,
    merkle_hash,
    verify_signature,
)


_VECTORS_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "test_vectors"
    / "crypto_v1.json"
)


def _load_vectors() -> dict[str, Any]:
    with _VECTORS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


_VECTORS = _load_vectors()


@pytest.mark.parametrize(
    "vector",
    _VECTORS["merkle_hash"]["vectors"],
    ids=lambda v: v["name"],
)
def test_merkle_hash_vector(vector: dict[str, Any]) -> None:
    parents = [NodeHash(bytes.fromhex(h)) for h in vector["parents_hex"]]
    content = bytes.fromhex(vector["content_hex"])
    got = merkle_hash(parents, content)
    assert got.to_hex() == vector["output_hex"], (
        f'merkle vector "{vector["name"]}" mismatch:\n'
        f"  expected: {vector['output_hex']}\n"
        f"  got:      {got.to_hex()}"
    )


@pytest.mark.parametrize(
    "vector",
    _VECTORS["hmac_sha256"]["vectors"],
    ids=lambda v: v["name"],
)
def test_hmac_sha256_vector(vector: dict[str, Any]) -> None:
    key = bytes.fromhex(vector["key_hex"])
    msg = bytes.fromhex(vector["msg_hex"])
    got = hmac_sign(key, msg)
    assert got.to_hex() == vector["output_hex"], (
        f'hmac vector "{vector["name"]}" mismatch:\n'
        f"  expected: {vector['output_hex']}\n"
        f"  got:      {got.to_hex()}"
    )


@pytest.mark.parametrize(
    "case",
    _VECTORS["empty_key_must_error"]["test_cases"],
    ids=lambda c: f"empty_key_msg_{c['msg_hex']}",
)
def test_empty_key_rejected(case: dict[str, Any]) -> None:
    key = bytes.fromhex(case["key_hex"])
    msg = bytes.fromhex(case["msg_hex"])
    with pytest.raises(HmacEmptyKey):
        hmac_sign(key, msg)


# ---------------------------------------------------------------------------
# Property tests.
# ---------------------------------------------------------------------------


def test_merkle_hash_determinism() -> None:
    parent = NodeHash(b"\x01" * 32)
    content = b"hello"
    assert merkle_hash([parent], content) == merkle_hash([parent], content)


def test_merkle_hash_different_parents_different_hash() -> None:
    p1 = NodeHash(b"\x01" * 32)
    p2 = NodeHash(b"\x02" * 32)
    content = b"hello"
    h1 = merkle_hash([p1], content)
    h2 = merkle_hash([p2], content)
    assert h1 != h2


def test_merkle_hash_parent_count_disambiguation() -> None:
    """Per pass-3 mycoparasite-2: parent_count prefix prevents ambiguity.

    Without prefix, ``1 parent (32 bytes) + 32-byte content`` and
    ``2 parents (64 bytes) + 0-byte content`` would produce identical
    BLAKE3 input. With prefix, they differ.
    """
    p = NodeHash(b"\xab" * 32)
    h_one_parent_with_content = merkle_hash([p], b"\xcd" * 32)
    h_two_parents_no_content = merkle_hash([p, NodeHash(b"\xcd" * 32)], b"")
    assert h_one_parent_with_content != h_two_parents_no_content


def test_hmac_round_trip() -> None:
    key = b"operator_token_test"
    msg = b"canonical_envelope_bytes"
    tag = hmac_sign(key, msg)
    hmac_verify(key, msg, tag)  # should not raise


def test_hmac_wrong_key_fails_verify() -> None:
    msg = b"hello"
    tag = hmac_sign(b"correct_key", msg)
    with pytest.raises(HmacInvalid):
        hmac_verify(b"wrong_key", msg, tag)


def test_hmac_tampered_msg_fails_verify() -> None:
    key = b"test_key"
    tag = hmac_sign(key, b"original")
    with pytest.raises(HmacInvalid):
        hmac_verify(key, b"tampered", tag)


def test_hmac_verify_empty_key_rejected() -> None:
    fake_tag = HmacTag(b"\x00" * 32)
    with pytest.raises(HmacEmptyKey):
        hmac_verify(b"", b"msg", fake_tag)


def test_node_hash_wrong_length_rejected() -> None:
    from myco_kernel_governance.crypto import CryptoError

    with pytest.raises(CryptoError, match="32 bytes"):
        NodeHash(b"\x00" * 16)


def test_hmac_tag_wrong_length_rejected() -> None:
    from myco_kernel_governance.crypto import CryptoError

    with pytest.raises(CryptoError, match="32 bytes"):
        HmacTag(b"\x00" * 16)


def test_verify_signature_is_stub() -> None:
    """M2 stub MUST raise SignatureInvalid pending algorithm choice."""
    with pytest.raises(SignatureInvalid):
        verify_signature(b"pubkey", b"sig", b"content")
