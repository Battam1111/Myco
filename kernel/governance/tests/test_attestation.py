"""Tests for the attestation envelope (L1_GOVERNANCE §2)."""

from __future__ import annotations

import pytest

from myco_kernel_governance.attestation import (
    AttestationInvalid,
    AttestationRequest,
    ExpiredAttestation,
    ExpiryConstraints,
    NonceMismatch,
    OperatorWitnessForgery,
    OwnerSignedAttestation,
    VerificationContext,
    construct_owner_signed_from_request,
    verify_operator_witness,
    verify_owner_signed_attestation,
)
from myco_kernel_governance.canonical_bytes import CanonicalBytes
from myco_kernel_governance.crypto import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
    Ed25519Signature,
    NodeHash,
    merkle_hash,
)


def _owner_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Reusable test owner key pair."""
    priv = Ed25519PrivateKey.from_seed(b"\x01" * 32)
    return priv, priv.public_key()


def _operator_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Reusable test operator key pair."""
    priv = Ed25519PrivateKey.from_seed(b"\x02" * 32)
    return priv, priv.public_key()


def _make_request(
    operator_priv: Ed25519PrivateKey,
    operator_pub: Ed25519PublicKey,
    mutation_bytes: bytes = b"proposed_mutation_payload",
    nonce: bytes = b"\xaa" * 32,
    cycles_max: int = 100,
    wall_clock_seconds_max: int = 300,
) -> AttestationRequest:
    """Build a valid attestation request signed by the given operator key."""
    proposed_canonical = CanonicalBytes(mutation_bytes)
    mutation_hash = merkle_hash([], mutation_bytes)
    operator_sig = operator_priv.sign(mutation_bytes)
    return AttestationRequest(
        substrate_id="test_substrate_001",
        dag_tip_hash=NodeHash(b"\xbb" * 32),
        enumerated_dag_nodes_since_last_co_sign=(
            NodeHash(b"\xcc" * 32),
            NodeHash(b"\xdd" * 32),
        ),
        proposed_mutation_canonical_bytes=proposed_canonical,
        proposed_mutation_hash=mutation_hash,
        operator_witness=operator_sig,
        operator_signing_key_public=operator_pub,
        request_timestamp_substrate_cycles=1000,
        anchor_surface_nonce=nonce,
        expiry_constraints=ExpiryConstraints(
            cycles_max=cycles_max,
            wall_clock_seconds_max=wall_clock_seconds_max,
        ),
    )


# ---------------------------------------------------------------------------
# AttestationRequest canonical-bytes encoding.
# ---------------------------------------------------------------------------


def test_attestation_request_canonical_bytes_deterministic() -> None:
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub)
    assert req.to_canonical_bytes().bytes_ == req.to_canonical_bytes().bytes_


def test_attestation_request_canonical_bytes_changes_on_field_change() -> None:
    op_priv, op_pub = _operator_keypair()
    req1 = _make_request(op_priv, op_pub, mutation_bytes=b"a")
    req2 = _make_request(op_priv, op_pub, mutation_bytes=b"b")
    assert req1.to_canonical_bytes().bytes_ != req2.to_canonical_bytes().bytes_


# ---------------------------------------------------------------------------
# Operator-witness verification (L1_HARD_RULES C17).
# ---------------------------------------------------------------------------


def test_operator_witness_valid_signature() -> None:
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub)
    verify_operator_witness(req)  # should not raise


def test_operator_witness_forgery_detected() -> None:
    """Per L1_HARD_RULES C17: operator_witness_forgery (CRITICAL).

    Construct a request where the operator_witness is signed by a DIFFERENT
    key than the declared operator_signing_key_public. Anchor surface
    detects the mismatch.
    """
    op_priv_a, op_pub_a = _operator_keypair()
    impostor_priv = Ed25519PrivateKey.from_seed(b"\xff" * 32)
    # Request claims op_pub_a but signature was made by impostor_priv.
    proposed = b"payload"
    forged_sig = impostor_priv.sign(proposed)
    req = AttestationRequest(
        substrate_id="x",
        dag_tip_hash=NodeHash(b"\x00" * 32),
        enumerated_dag_nodes_since_last_co_sign=(),
        proposed_mutation_canonical_bytes=CanonicalBytes(proposed),
        proposed_mutation_hash=merkle_hash([], proposed),
        operator_witness=forged_sig,
        operator_signing_key_public=op_pub_a,
        request_timestamp_substrate_cycles=0,
        anchor_surface_nonce=b"\xaa" * 32,
        expiry_constraints=ExpiryConstraints(100, 300),
    )
    with pytest.raises(OperatorWitnessForgery):
        verify_operator_witness(req)


def test_operator_witness_tampered_payload_detected() -> None:
    """If proposed_mutation_canonical_bytes changes after the operator signed,
    the witness must fail to verify."""
    op_priv, op_pub = _operator_keypair()
    proposed_original = b"original_payload"
    sig = op_priv.sign(proposed_original)
    # Substitute a different payload but keep the (now-stale) signature.
    proposed_tampered = b"tampered_payloadxx"  # same length as original
    req = AttestationRequest(
        substrate_id="x",
        dag_tip_hash=NodeHash(b"\x00" * 32),
        enumerated_dag_nodes_since_last_co_sign=(),
        proposed_mutation_canonical_bytes=CanonicalBytes(proposed_tampered),
        proposed_mutation_hash=merkle_hash([], proposed_tampered),
        operator_witness=sig,
        operator_signing_key_public=op_pub,
        request_timestamp_substrate_cycles=0,
        anchor_surface_nonce=b"\xaa" * 32,
        expiry_constraints=ExpiryConstraints(100, 300),
    )
    with pytest.raises(OperatorWitnessForgery):
        verify_operator_witness(req)


# ---------------------------------------------------------------------------
# Owner signed attestation: full round-trip.
# ---------------------------------------------------------------------------


def test_owner_signed_round_trip() -> None:
    """End-to-end happy path: substrate constructs request, owner signs the
    tuple, substrate verifies."""
    owner_priv, owner_pub = _owner_keypair()
    op_priv, op_pub = _operator_keypair()

    # Substrate side: build the request.
    req = _make_request(op_priv, op_pub)

    # Anchor surface side: build the signed tuple, owner signs.
    anchor_timestamp = 1_700_000_000  # fictional unix seconds
    # Use the helper without a signature first to derive the canonical bytes,
    # then sign, then re-construct with the real signature.
    placeholder = OwnerSignedAttestation(
        substrate_id=req.substrate_id,
        dag_tip_hash=req.dag_tip_hash,
        proposed_mutation_hash=req.proposed_mutation_hash,
        operator_witness=req.operator_witness,
        operator_signing_key_public=req.operator_signing_key_public,
        anchor_surface_nonce=req.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=anchor_timestamp,
        owner_signature=Ed25519Signature(b"\x00" * 64),  # placeholder for canonical-bytes
    )
    canonical = placeholder.signed_tuple_canonical_bytes()
    owner_sig = owner_priv.sign(canonical.bytes_)
    attestation = construct_owner_signed_from_request(req, anchor_timestamp, owner_sig)

    # Substrate side: verify.
    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=owner_pub,
        current_substrate_cycle=req.request_timestamp_substrate_cycles + 50,
        current_wall_clock_unix_seconds=anchor_timestamp + 100,
        consumed_nonces=frozenset(),
        original_request_substrate_cycle=req.request_timestamp_substrate_cycles,
        original_request_constraints=req.expiry_constraints,
    )
    verify_owner_signed_attestation(attestation, ctx)  # should not raise


def test_owner_signature_tampered_rejected() -> None:
    """Tampered owner signature → AttestationInvalid."""
    owner_priv, owner_pub = _owner_keypair()
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub)
    anchor_timestamp = 1_700_000_000

    # Build with a fake owner signature.
    fake_sig = Ed25519Signature(b"\xff" * 64)
    attestation = construct_owner_signed_from_request(req, anchor_timestamp, fake_sig)

    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=owner_pub,
        current_substrate_cycle=req.request_timestamp_substrate_cycles + 50,
        current_wall_clock_unix_seconds=anchor_timestamp + 100,
        consumed_nonces=frozenset(),
        original_request_substrate_cycle=req.request_timestamp_substrate_cycles,
        original_request_constraints=req.expiry_constraints,
    )
    with pytest.raises(AttestationInvalid):
        verify_owner_signed_attestation(attestation, ctx)


def test_owner_signature_wrong_owner_rejected() -> None:
    """Attestation signed by a different owner key → AttestationInvalid."""
    _, owner_pub_correct = _owner_keypair()
    wrong_owner_priv = Ed25519PrivateKey.from_seed(b"\xee" * 32)
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub)
    anchor_timestamp = 1_700_000_000

    # Sign with the WRONG owner key.
    placeholder = OwnerSignedAttestation(
        substrate_id=req.substrate_id,
        dag_tip_hash=req.dag_tip_hash,
        proposed_mutation_hash=req.proposed_mutation_hash,
        operator_witness=req.operator_witness,
        operator_signing_key_public=req.operator_signing_key_public,
        anchor_surface_nonce=req.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=anchor_timestamp,
        owner_signature=Ed25519Signature(b"\x00" * 64),
    )
    canonical = placeholder.signed_tuple_canonical_bytes()
    wrong_sig = wrong_owner_priv.sign(canonical.bytes_)
    attestation = construct_owner_signed_from_request(req, anchor_timestamp, wrong_sig)

    # Substrate uses the CORRECT pubkey for verification → fails.
    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=owner_pub_correct,
        current_substrate_cycle=req.request_timestamp_substrate_cycles + 50,
        current_wall_clock_unix_seconds=anchor_timestamp + 100,
        consumed_nonces=frozenset(),
        original_request_substrate_cycle=req.request_timestamp_substrate_cycles,
        original_request_constraints=req.expiry_constraints,
    )
    with pytest.raises(AttestationInvalid):
        verify_owner_signed_attestation(attestation, ctx)


# ---------------------------------------------------------------------------
# Dual-clock expiry (L1_GOVERNANCE §2.3 step 3).
# ---------------------------------------------------------------------------


def test_substrate_cycle_expiry() -> None:
    owner_priv, owner_pub = _owner_keypair()
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub, cycles_max=10, wall_clock_seconds_max=3600)
    anchor_timestamp = 1_700_000_000

    placeholder = OwnerSignedAttestation(
        substrate_id=req.substrate_id,
        dag_tip_hash=req.dag_tip_hash,
        proposed_mutation_hash=req.proposed_mutation_hash,
        operator_witness=req.operator_witness,
        operator_signing_key_public=req.operator_signing_key_public,
        anchor_surface_nonce=req.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=anchor_timestamp,
        owner_signature=Ed25519Signature(b"\x00" * 64),
    )
    canonical = placeholder.signed_tuple_canonical_bytes()
    owner_sig = owner_priv.sign(canonical.bytes_)
    attestation = construct_owner_signed_from_request(req, anchor_timestamp, owner_sig)

    # 20 cycles elapsed > 10 max → expired.
    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=owner_pub,
        current_substrate_cycle=req.request_timestamp_substrate_cycles + 20,
        current_wall_clock_unix_seconds=anchor_timestamp + 100,
        consumed_nonces=frozenset(),
        original_request_substrate_cycle=req.request_timestamp_substrate_cycles,
        original_request_constraints=req.expiry_constraints,
    )
    with pytest.raises(ExpiredAttestation, match="substrate-cycle expiry"):
        verify_owner_signed_attestation(attestation, ctx)


def test_wall_clock_expiry() -> None:
    owner_priv, owner_pub = _owner_keypair()
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub, cycles_max=10000, wall_clock_seconds_max=300)
    anchor_timestamp = 1_700_000_000

    placeholder = OwnerSignedAttestation(
        substrate_id=req.substrate_id,
        dag_tip_hash=req.dag_tip_hash,
        proposed_mutation_hash=req.proposed_mutation_hash,
        operator_witness=req.operator_witness,
        operator_signing_key_public=req.operator_signing_key_public,
        anchor_surface_nonce=req.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=anchor_timestamp,
        owner_signature=Ed25519Signature(b"\x00" * 64),
    )
    canonical = placeholder.signed_tuple_canonical_bytes()
    owner_sig = owner_priv.sign(canonical.bytes_)
    attestation = construct_owner_signed_from_request(req, anchor_timestamp, owner_sig)

    # 600s wall-clock elapsed > 300 max → expired.
    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=owner_pub,
        current_substrate_cycle=req.request_timestamp_substrate_cycles + 1,
        current_wall_clock_unix_seconds=anchor_timestamp + 600,
        consumed_nonces=frozenset(),
        original_request_substrate_cycle=req.request_timestamp_substrate_cycles,
        original_request_constraints=req.expiry_constraints,
    )
    with pytest.raises(ExpiredAttestation, match="wall-clock expiry"):
        verify_owner_signed_attestation(attestation, ctx)


# ---------------------------------------------------------------------------
# Nonce replay (L1_GOVERNANCE §2.3 step 4).
# ---------------------------------------------------------------------------


def test_nonce_replay_rejected() -> None:
    owner_priv, owner_pub = _owner_keypair()
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub, nonce=b"\x42" * 32)
    anchor_timestamp = 1_700_000_000

    placeholder = OwnerSignedAttestation(
        substrate_id=req.substrate_id,
        dag_tip_hash=req.dag_tip_hash,
        proposed_mutation_hash=req.proposed_mutation_hash,
        operator_witness=req.operator_witness,
        operator_signing_key_public=req.operator_signing_key_public,
        anchor_surface_nonce=req.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=anchor_timestamp,
        owner_signature=Ed25519Signature(b"\x00" * 64),
    )
    canonical = placeholder.signed_tuple_canonical_bytes()
    owner_sig = owner_priv.sign(canonical.bytes_)
    attestation = construct_owner_signed_from_request(req, anchor_timestamp, owner_sig)

    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=owner_pub,
        current_substrate_cycle=req.request_timestamp_substrate_cycles + 5,
        current_wall_clock_unix_seconds=anchor_timestamp + 60,
        consumed_nonces=frozenset({b"\x42" * 32}),  # already consumed
        original_request_substrate_cycle=req.request_timestamp_substrate_cycles,
        original_request_constraints=req.expiry_constraints,
    )
    with pytest.raises(NonceMismatch):
        verify_owner_signed_attestation(attestation, ctx)


# ---------------------------------------------------------------------------
# Signed-tuple canonical-bytes determinism.
# ---------------------------------------------------------------------------


def test_signed_tuple_canonical_bytes_deterministic() -> None:
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub)
    fake_sig = Ed25519Signature(b"\x00" * 64)
    a1 = construct_owner_signed_from_request(req, 1_700_000_000, fake_sig)
    a2 = construct_owner_signed_from_request(req, 1_700_000_000, fake_sig)
    assert a1.signed_tuple_canonical_bytes().bytes_ == a2.signed_tuple_canonical_bytes().bytes_


def test_signed_tuple_excludes_owner_signature() -> None:
    """The owner signs the canonical bytes of the signed tuple — those bytes
    must NOT include the owner_signature itself (chicken-and-egg)."""
    op_priv, op_pub = _operator_keypair()
    req = _make_request(op_priv, op_pub)
    a1 = construct_owner_signed_from_request(req, 1_700_000_000, Ed25519Signature(b"\xaa" * 64))
    a2 = construct_owner_signed_from_request(req, 1_700_000_000, Ed25519Signature(b"\xbb" * 64))
    # Different owner_signatures → identical signed_tuple_canonical_bytes
    # (the canonical bytes are the input to signing, not the output).
    assert a1.signed_tuple_canonical_bytes().bytes_ == a2.signed_tuple_canonical_bytes().bytes_
