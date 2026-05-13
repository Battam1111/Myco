"""M2 milestone end-to-end attestation flow test.

Proves the L1_GOVERNANCE §2 attestation flow works end-to-end across:

- Substrate side (kernel/governance Python): classifier + attestation
  envelope construction + verification + owner_keys lookup.
- Operator side (operator_bindings — M3+; for M2 we use the Ed25519
  primitives directly to simulate the per-handshake operator keypair).
- Anchor-surface side (anchor_client TypeScript — for M2 we simulate
  in Python since cross-language parity is verified by separate tests).
- Owner side (anchor_client TypeScript — for M2 we simulate the
  owner-signing operation using Python crypto, which produces identical
  results per the verified cross-language Ed25519 parity).

## Flow under test (per L1_GOVERNANCE §2.2)

1. Substrate proposes a CI mutation: ``edit substrate_id`` (forbidden in
   real life post-genesis, but maximally CI-classified for the test).
2. Substrate runs :func:`classify` → ``CONTRACT_IDENTITY_LEVEL`` confirmed.
3. Substrate computes ``proposed_mutation_hash`` from canonical bytes.
4. (Simulated anchor surface): :meth:`NonceLog.issueNonce` binds a nonce
   to ``(mutation_hash, dag_tip_hash)``.
5. Substrate constructs an :class:`AttestationRequest` with the
   operator_witness signature over the canonical mutation bytes.
6. (Simulated anchor-surface client): verifies operator_witness
   (:func:`verify_operator_witness`); renders canonical bytes for owner
   review (skipped in this test); owner signs the tuple.
7. Substrate receives :class:`OwnerSignedAttestation`; calls
   :func:`verify_owner_signed_attestation` against active owner key from
   :class:`OwnerKeyHistory`; if valid, commits.
8. Replay protection: a second attempt to use the same nonce is rejected
   by both anchor-surface (NonceAlreadyConsumed in NonceLog — N/A since
   we don't run TS in this test) and substrate-side
   (NonceMismatch with the consumed_nonces set populated).

## Why this is the M2 milestone

L1_GOVERNANCE §2 is the linchpin of the substrate's CI mutation pipeline.
Without a working attestation flow, no CI mutation can land — substrate is
permanently in birth-period quarantine. This test proves the flow works
for at least one CI mutation type with one substrate, one operator, one
owner. M3+ extends to: multiple substrates, federation peers, owner-key
rotation, succession.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pytest

from myco_kernel_governance.attestation import (
    AttestationRequest,
    ExpiryConstraints,
    NonceMismatch,
    OwnerSignedAttestation,
    VerificationContext,
    construct_owner_signed_from_request,
    verify_operator_witness,
    verify_owner_signed_attestation,
)
from myco_kernel_governance.canonical_bytes import (
    Bytes,
    CanonicalBytes,
    Map,
    String,
    Value,
    encode,
)
from myco_kernel_governance.classifier import (
    Classification,
    MutationEnvelope,
    classify,
)
from myco_kernel_governance.crypto import (
    Ed25519PrivateKey,
    Ed25519Signature,
    NodeHash,
    merkle_hash,
)
from myco_kernel_governance.owner_keys import init_with_genesis_key


# ---------------------------------------------------------------------------
# Test fixtures: simulated parties.
# ---------------------------------------------------------------------------


@dataclass
class SimulatedAnchorSurface:
    """Anchor-surface state: nonce log + consumed-nonces (substrate-visible mirror).

    Per L1_HARD_RULES §4: substrate cannot author this state. In production,
    this lives on a separate machine / hardware token / cloud HSM. For the
    M2 e2e test, simulated in-process.
    """

    issued_nonces: dict[bytes, tuple[NodeHash, NodeHash]]  # nonce -> (mut_hash, dag_tip)
    consumed_nonces: set[bytes]

    @classmethod
    def new(cls) -> "SimulatedAnchorSurface":
        return cls(issued_nonces={}, consumed_nonces=set())

    def issue_nonce(
        self,
        mutation_hash: NodeHash,
        dag_tip_hash: NodeHash,
        seed: int = 0,
    ) -> bytes:
        """Issue a deterministic test nonce bound to (mutation_hash, dag_tip_hash)."""
        nonce = bytes([(seed + i) & 0xFF for i in range(32)])
        self.issued_nonces[nonce] = (mutation_hash, dag_tip_hash)
        return nonce

    def consume_nonce(
        self,
        nonce: bytes,
        expected_mutation_hash: NodeHash,
        expected_dag_tip_hash: NodeHash,
    ) -> None:
        """Validate binding + mark consumed."""
        if nonce in self.consumed_nonces:
            raise ValueError("nonce already consumed")
        binding = self.issued_nonces.get(nonce)
        if binding is None:
            raise ValueError("unknown nonce")
        actual_mutation_hash, actual_dag_tip_hash = binding
        if actual_mutation_hash != expected_mutation_hash:
            raise ValueError("nonce mutation_hash binding mismatch")
        if actual_dag_tip_hash != expected_dag_tip_hash:
            raise ValueError("nonce dag_tip_hash binding mismatch")
        self.consumed_nonces.add(nonce)


def _build_mutation_canonical_bytes(target_field: str, new_value: str) -> CanonicalBytes:
    """Build canonical bytes representing a hypothetical SSoT mutation.

    For the M2 e2e: a structured map describing the proposed change.
    Real substrates serialize their own per-mutation-type structure;
    this is just a placeholder shape demonstrating the canonical-bytes
    flow.
    """
    v: Value = Map.from_dict(
        {
            "mutation_kind": String("field_update"),
            "target_field": String(target_field),
            "new_value": Bytes(new_value.encode("utf-8")),
        }
    )
    return encode(v)


# ---------------------------------------------------------------------------
# M2 milestone end-to-end happy path.
# ---------------------------------------------------------------------------


def test_m2_e2e_attestation_flow_happy_path() -> None:
    """The full M2 attestation flow, end-to-end."""

    # === Setup: substrate identity + key infrastructure ===

    substrate_id = "myco_substrate_e2e_001"

    # Owner key: lives in the anchor_client sealed-key store (simulated by
    # direct Ed25519PrivateKey here).
    owner_priv = Ed25519PrivateKey.from_seed(b"\x01" * 32)
    owner_pub = owner_priv.public_key()

    # Substrate's owner_key_history: bootstrap with the genesis owner key.
    genesis_anchor_timestamp = 1_700_000_000
    owner_key_history = init_with_genesis_key(owner_pub, genesis_anchor_timestamp)

    # Operator: per-handshake keypair (L1_SKIN §4.1). Per pass-3 mycorrhiza-17 +
    # rhizomorph-1: operator has a real signing surface.
    operator_priv = Ed25519PrivateKey.from_seed(b"\x02" * 32)
    operator_pub = operator_priv.public_key()

    # Substrate's current DAG-tip (simulating M1 milestone test had it
    # advance through some sequence of cycles).
    dag_tip_hash = NodeHash(b"\xab" * 32)

    # Anchor surface state.
    anchor = SimulatedAnchorSurface.new()

    # === Step 1: Substrate proposes a CI mutation ===

    # The mutation: substrate proposes updating the (hypothetically-mutable)
    # ``substrate_id`` field. In real life this is impossible post-genesis;
    # for the test we use it because it maximally exercises the CI path.
    mutation_canonical = _build_mutation_canonical_bytes(
        target_field="substrate_id",
        new_value="new_id_value",
    )

    # === Step 2: classifier confirms CI ===

    mutation_envelope = MutationEnvelope(
        touched_fields=frozenset({"substrate_id"}),
        mutation_type="field_update",
    )
    classification = classify(mutation_envelope)
    assert classification is Classification.CONTRACT_IDENTITY_LEVEL

    # === Step 3: Substrate computes mutation hash ===

    mutation_hash = merkle_hash([], mutation_canonical.bytes_)

    # === Step 4: Anchor surface issues a nonce ===

    nonce = anchor.issue_nonce(mutation_hash, dag_tip_hash, seed=0x10)

    # === Step 5: Substrate constructs AttestationRequest ===

    # Operator witness: signs the mutation canonical bytes.
    operator_witness = operator_priv.sign(mutation_canonical.bytes_)

    substrate_cycle_at_request = 5000
    request = AttestationRequest(
        substrate_id=substrate_id,
        dag_tip_hash=dag_tip_hash,
        enumerated_dag_nodes_since_last_co_sign=(
            NodeHash(b"\xcc" * 32),
            NodeHash(b"\xdd" * 32),
        ),
        proposed_mutation_canonical_bytes=mutation_canonical,
        proposed_mutation_hash=mutation_hash,
        operator_witness=operator_witness,
        operator_signing_key_public=operator_pub,
        request_timestamp_substrate_cycles=substrate_cycle_at_request,
        anchor_surface_nonce=nonce,
        expiry_constraints=ExpiryConstraints(
            cycles_max=100,
            wall_clock_seconds_max=600,
        ),
    )

    # === Step 6: Anchor-surface client side — verify + render + owner-sign ===

    # 6a. Anchor surface verifies operator_witness against
    #     operator_signing_key_public (L1_HARD_RULES C17 detector).
    verify_operator_witness(request)  # raises OperatorWitnessForgery on failure

    # 6b. (Skipped: DAG enumeration closure — verified by re-walking the
    #     enumerated_dag_nodes_since_last_co_sign back to the prior co-signed
    #     tip. M3+ wires this with kernel/schema DAG operations.)

    # 6c. (Skipped: render canonical bytes for owner review — exercised by
    #     anchor_client/tests/renderer.test.ts.)

    # 6d. Anchor surface marks nonce as consumed.
    anchor.consume_nonce(nonce, mutation_hash, dag_tip_hash)

    # 6e. Owner signs the tuple. We construct the placeholder owner-signed
    #     envelope to get the canonical bytes that the owner signs.
    anchor_surface_timestamp = 1_700_005_000  # 5000s after genesis
    placeholder = OwnerSignedAttestation(
        substrate_id=request.substrate_id,
        dag_tip_hash=request.dag_tip_hash,
        proposed_mutation_hash=request.proposed_mutation_hash,
        operator_witness=request.operator_witness,
        operator_signing_key_public=request.operator_signing_key_public,
        anchor_surface_nonce=request.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=anchor_surface_timestamp,
        owner_signature=Ed25519Signature(b"\x00" * 64),
    )
    canonical_to_sign = placeholder.signed_tuple_canonical_bytes()
    owner_signature = owner_priv.sign(canonical_to_sign.bytes_)

    attestation = construct_owner_signed_from_request(
        request,
        anchor_surface_timestamp_unix_seconds=anchor_surface_timestamp,
        owner_signature=owner_signature,
    )

    # === Step 7: Substrate verifies owner-signed attestation ===

    # Substrate looks up the owner key active at the anchor-surface timestamp.
    owner_key_at_timestamp = owner_key_history.active_at(anchor_surface_timestamp)
    assert owner_key_at_timestamp == owner_pub

    # Verification context: simulating substrate state.
    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=owner_key_at_timestamp,
        current_substrate_cycle=substrate_cycle_at_request + 50,
        current_wall_clock_unix_seconds=anchor_surface_timestamp + 100,
        consumed_nonces=frozenset(),  # not yet consumed substrate-side
        original_request_substrate_cycle=substrate_cycle_at_request,
        original_request_constraints=request.expiry_constraints,
    )

    # Full verification must pass.
    verify_owner_signed_attestation(attestation, ctx)

    # === Step 8: Replay protection ===

    # Substrate marks the nonce as consumed in its own tracker.
    ctx_after_consume = VerificationContext(
        owner_public_key_active_at_timestamp=owner_key_at_timestamp,
        current_substrate_cycle=substrate_cycle_at_request + 60,
        current_wall_clock_unix_seconds=anchor_surface_timestamp + 110,
        consumed_nonces=frozenset({nonce}),
        original_request_substrate_cycle=substrate_cycle_at_request,
        original_request_constraints=request.expiry_constraints,
    )

    # Second verification attempt with the same nonce → NonceMismatch.
    with pytest.raises(NonceMismatch):
        verify_owner_signed_attestation(attestation, ctx_after_consume)


# ---------------------------------------------------------------------------
# Negative paths — verify the gates block bad attestations.
# ---------------------------------------------------------------------------


def test_m2_e2e_forged_operator_witness_blocked() -> None:
    """If the operator_witness signature is forged (signed by wrong key),
    the anchor-surface verification step blocks the request before owner
    signs (L1_HARD_RULES C17 operator_witness_forgery)."""
    substrate_id = "myco_substrate_e2e_002"
    legit_operator_priv = Ed25519PrivateKey.from_seed(b"\x02" * 32)
    legit_operator_pub = legit_operator_priv.public_key()
    impostor_priv = Ed25519PrivateKey.from_seed(b"\xff" * 32)

    mutation_canonical = _build_mutation_canonical_bytes("substrate_id", "evil")
    mutation_hash = merkle_hash([], mutation_canonical.bytes_)

    # Forged signature: signed by impostor, but request claims legit pubkey.
    forged_witness = impostor_priv.sign(mutation_canonical.bytes_)

    request = AttestationRequest(
        substrate_id=substrate_id,
        dag_tip_hash=NodeHash(b"\xab" * 32),
        enumerated_dag_nodes_since_last_co_sign=(),
        proposed_mutation_canonical_bytes=mutation_canonical,
        proposed_mutation_hash=mutation_hash,
        operator_witness=forged_witness,
        operator_signing_key_public=legit_operator_pub,
        request_timestamp_substrate_cycles=5000,
        anchor_surface_nonce=b"\x00" * 32,
        expiry_constraints=ExpiryConstraints(100, 600),
    )

    from myco_kernel_governance.attestation import OperatorWitnessForgery

    with pytest.raises(OperatorWitnessForgery):
        verify_operator_witness(request)


def test_m2_e2e_owner_key_rotation_validates_old_attestations() -> None:
    """After owner-key rotation, attestations signed under the OLD key
    (with old anchor_surface_timestamp) must still validate using the
    timestamp-active key from owner_key_history.

    This is the L1_GOVERNANCE §2.3 step 2 requirement: substrate looks up
    the key valid at the attestation's anchor-surface timestamp, not the
    currently-active key.
    """
    from myco_kernel_governance.owner_keys import OwnerKeyEntry, OwnerKeyHistory

    substrate_id = "myco_substrate_e2e_003"

    # Two owner keys; key1 active at t=1_000..2_000, key2 active at t=2_000+.
    owner1_priv = Ed25519PrivateKey.from_seed(b"\x01" * 32)
    owner1_pub = owner1_priv.public_key()
    owner2_priv = Ed25519PrivateKey.from_seed(b"\x03" * 32)
    owner2_pub = owner2_priv.public_key()

    history = OwnerKeyHistory()
    history.add_key(
        OwnerKeyEntry(
            public_key=owner1_pub,
            valid_from_anchor_timestamp=1_000,
            valid_until_anchor_timestamp=2_000,
        )
    )
    history.add_key(
        OwnerKeyEntry(public_key=owner2_pub, valid_from_anchor_timestamp=2_000)
    )

    # OLD attestation signed under owner1 at t=1_500 (within owner1's window).
    operator_priv = Ed25519PrivateKey.from_seed(b"\x02" * 32)
    operator_pub = operator_priv.public_key()

    mutation_canonical = _build_mutation_canonical_bytes("substrate_id", "v_old")
    mutation_hash = merkle_hash([], mutation_canonical.bytes_)
    operator_witness = operator_priv.sign(mutation_canonical.bytes_)

    request = AttestationRequest(
        substrate_id=substrate_id,
        dag_tip_hash=NodeHash(b"\xab" * 32),
        enumerated_dag_nodes_since_last_co_sign=(),
        proposed_mutation_canonical_bytes=mutation_canonical,
        proposed_mutation_hash=mutation_hash,
        operator_witness=operator_witness,
        operator_signing_key_public=operator_pub,
        request_timestamp_substrate_cycles=500,
        anchor_surface_nonce=b"\x10" * 32,
        expiry_constraints=ExpiryConstraints(10000, 10000),
    )

    # Owner1 signs the tuple at t=1_500.
    old_anchor_timestamp = 1_500
    placeholder = OwnerSignedAttestation(
        substrate_id=request.substrate_id,
        dag_tip_hash=request.dag_tip_hash,
        proposed_mutation_hash=request.proposed_mutation_hash,
        operator_witness=request.operator_witness,
        operator_signing_key_public=request.operator_signing_key_public,
        anchor_surface_nonce=request.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=old_anchor_timestamp,
        owner_signature=Ed25519Signature(b"\x00" * 64),
    )
    canonical = placeholder.signed_tuple_canonical_bytes()
    owner1_sig = owner1_priv.sign(canonical.bytes_)
    attestation = construct_owner_signed_from_request(
        request, old_anchor_timestamp, owner1_sig
    )

    # SUBSTRATE NOW operates at t=3_000 (after owner1 -> owner2 rotation).
    # The substrate looks up the key active at the attestation's anchor
    # timestamp (1_500, within owner1's window) → owner1_pub.
    key_at_old_timestamp = history.active_at(old_anchor_timestamp)
    assert key_at_old_timestamp == owner1_pub

    # Verification succeeds because we used the right historical key.
    ctx = VerificationContext(
        owner_public_key_active_at_timestamp=key_at_old_timestamp,
        current_substrate_cycle=600,
        current_wall_clock_unix_seconds=3_000,
        consumed_nonces=frozenset(),
        original_request_substrate_cycle=500,
        original_request_constraints=request.expiry_constraints,
    )
    verify_owner_signed_attestation(attestation, ctx)

    # If we mistakenly use the CURRENT owner key (owner2), verification fails.
    ctx_wrong = VerificationContext(
        owner_public_key_active_at_timestamp=history.current_active(),  # owner2
        current_substrate_cycle=600,
        current_wall_clock_unix_seconds=3_000,
        consumed_nonces=frozenset(),
        original_request_substrate_cycle=500,
        original_request_constraints=request.expiry_constraints,
    )
    from myco_kernel_governance.attestation import AttestationInvalid

    with pytest.raises(AttestationInvalid):
        verify_owner_signed_attestation(attestation, ctx_wrong)


def test_m2_e2e_birth_period_daily_mutation_elevates_to_ci() -> None:
    """During birth-period, normally-daily mutations elevate to CI per
    L1_GOVERNANCE §1.3."""
    from myco_kernel_governance.classifier import ClassifierContext

    # Normally: delta_absorb is DAILY (no owner attestation needed).
    daily_mutation = MutationEnvelope(mutation_type="delta_absorb")
    assert classify(daily_mutation) is Classification.DAILY

    # During birth-period: elevated to CI (requires owner attestation).
    ctx_birth = ClassifierContext(birth_period_active=True)
    assert (
        classify(daily_mutation, context=ctx_birth)
        is Classification.CONTRACT_IDENTITY_LEVEL
    )
