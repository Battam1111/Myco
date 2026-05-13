"""Attestation envelope construction + verification (L1_GOVERNANCE §2).

The CI-level mutation flow per L1_GOVERNANCE §2.2:

1. Substrate requests an anchor-surface nonce bound to
   ``(proposed_mutation_hash, dag_tip_hash)``.
2. Substrate emits an :class:`AttestationRequest` envelope carrying the
   proposed CI mutation's canonical bytes + the operator's witness signature
   over those canonical bytes.
3. The owner verifies independently at the anchor-surface:
   - re-renders the proposed mutation from canonical bytes,
   - verifies the operator_witness signature,
   - performs DAG enumeration closure (L1_HARD_RULES C6),
   - verifies nonce binding + TTL,
   - and signs the tuple
     ``(substrate_id, dag_tip_hash, proposed_mutation_hash,
        operator_witness_signature, operator_signing_key_public,
        anchor_surface_nonce, anchor_surface_timestamp)``.
4. The substrate receives the owner signature, verifies it against the
   active owner public key, checks dual-clock expiry, checks that the
   nonce has not been consumed, and commits the mutation.

This module implements the data shapes + the construction/verification
functions. The actual transport (substrate ↔ anchor surface) is L4-picked.

## Doctrine traceability

- L1_GOVERNANCE §2 (full attestation protocol)
- L1_GOVERNANCE §2.2 (envelope schema; closes pass-3 astronaut-1 +
  mycorrhiza-17 + rhizomorph-1)
- L1_GOVERNANCE §2.3 (verification on receipt)
- L1_HARD_RULES C5 (attestation_invalid CRITICAL — fired when signature /
  nonce / dual-clock check fails)
- L1_HARD_RULES C6 (dag_enumeration_unclosed — fired when enumerated nodes
  don't reconstruct the chain)
- L1_HARD_RULES C17 (operator_witness_forgery — fired when operator_witness
  signature doesn't verify against the substrate's logged
  operator_signing_key_public from the handshake)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bytes,
    CanonicalBytes,
    Hash,
    Map,
    String,
    Timestamp,
    Uint,
    Value,
    encode,
)
from myco_kernel_governance.crypto import (
    Ed25519PublicKey,
    Ed25519Signature,
    NodeHash,
    SignatureInvalid,
    verify_signature,
)


# ---------------------------------------------------------------------------
# Error types.
# ---------------------------------------------------------------------------


class AttestationError(Exception):
    """Base class for attestation errors."""


class AttestationInvalid(AttestationError):
    """Generic attestation verification failure (L1_HARD_RULES C5)."""


class OperatorWitnessForgery(AttestationError):
    """Operator witness signature does not verify against the operator pubkey
    from the substrate's handshake log (L1_HARD_RULES C17)."""


class DagEnumerationUnclosed(AttestationError):
    """The enumerated DAG nodes don't form a closed chain to the prior co-sign
    (L1_HARD_RULES C6)."""


class NonceMismatch(AttestationError):
    """The anchor-surface nonce binding doesn't match the declared mutation /
    dag_tip pair, or the nonce has been consumed already."""


class ExpiredAttestation(AttestationError):
    """The attestation's substrate-cycle OR anchor-surface wall-clock has
    expired."""


# ---------------------------------------------------------------------------
# Envelope schemas.
# ---------------------------------------------------------------------------


# String constants used in the envelope canonical-bytes representation.
ENVELOPE_TYPE_CI_ATTESTATION_REQUEST: Final[str] = (
    "contract_identity_attestation_request"
)


@dataclass(frozen=True, slots=True)
class ExpiryConstraints:
    """Dual-clock expiry — per L1_GOVERNANCE §2.2.

    The substrate verifies BOTH:

    - ``cycles_max``: substrate metabolic-cycle counter must not exceed
      ``request_timestamp_substrate_cycles + cycles_max``.
    - ``wall_clock_seconds_max``: anchor-surface timestamp must not be older
      than the request timestamp by more than this many seconds.

    Whichever expires first invalidates the attestation. The substrate cannot
    extend wall-clock budget by throttling cycles (per §2.3 step 3).
    """

    cycles_max: int
    wall_clock_seconds_max: int


@dataclass(frozen=True, slots=True)
class AttestationRequest:
    """The substrate-emitted attestation request envelope (L1_GOVERNANCE §2.2 step 2).

    Carries everything the anchor-surface client needs to render + verify the
    proposed mutation before the owner signs.
    """

    substrate_id: str
    """Substrate-ID (owner-signed at genesis; immutable per L1_HARD_RULES F2)."""

    dag_tip_hash: NodeHash
    """Current Merkle DAG tip hash."""

    enumerated_dag_nodes_since_last_co_sign: tuple[NodeHash, ...]
    """All DAG node hashes added since the prior CI co-sign. Per L0 §9.2 +
    L1_HARD_RULES C6: the owner reconstructs the Merkle chain from these."""

    proposed_mutation_canonical_bytes: CanonicalBytes
    """Canonical serialization of the proposed mutation. The owner's
    anchor-surface client renders these for review (substrate cannot
    narrate per §2.4)."""

    proposed_mutation_hash: NodeHash
    """Hash of ``proposed_mutation_canonical_bytes`` (substrate-computed;
    owner re-computes for verification)."""

    operator_witness: Ed25519Signature
    """Operator's signature over ``proposed_mutation_canonical_bytes`` using
    the per-handshake operator_signing_key_private (L1_SKIN §4.1).
    Closes pass-3 mycorrhiza-17 + rhizomorph-1: operator has a real signing
    surface distinct from operator_token."""

    operator_signing_key_public: Ed25519PublicKey
    """The operator's per-handshake signing pubkey (from handshake_complete
    log; cross-checked at anchor surface against the logged event)."""

    request_timestamp_substrate_cycles: int
    """Substrate's metabolic-cycle counter at request time (for dual-clock
    expiry — substrate-side)."""

    anchor_surface_nonce: bytes
    """Single-use nonce issued by anchor-surface for THIS request. Anchor
    binds it to ``(proposed_mutation_hash, dag_tip_hash)`` at issuance
    (closes pass-3 mycoparasite-5: no nonce hoarding)."""

    expiry_constraints: ExpiryConstraints
    """Dual-clock expiry bounds."""

    def to_canonical_bytes(self) -> CanonicalBytes:
        """Canonical-bytes encoding of the attestation request envelope.

        Owner uses this to derive the hash that goes into the owner-signed
        tuple. Per L0 §9.3 canonical-bytes doctrine: deterministic; all
        parties derive identical bytes.
        """
        m_value = Map.from_dict(
            {
                "type": String(ENVELOPE_TYPE_CI_ATTESTATION_REQUEST),
                "substrate_id": String(self.substrate_id),
                "dag_tip_hash": Hash(self.dag_tip_hash.bytes_),
                "enumerated_dag_nodes_since_last_co_sign": Array(
                    tuple(Hash(h.bytes_) for h in self.enumerated_dag_nodes_since_last_co_sign)
                ),
                "proposed_mutation_canonical_bytes": Bytes(
                    self.proposed_mutation_canonical_bytes.bytes_
                ),
                "proposed_mutation_hash": Hash(self.proposed_mutation_hash.bytes_),
                "operator_witness": Bytes(self.operator_witness.bytes_),
                "operator_signing_key_public": Bytes(
                    self.operator_signing_key_public.bytes_
                ),
                "request_timestamp_substrate_cycles": Uint(
                    self.request_timestamp_substrate_cycles
                ),
                "anchor_surface_nonce": Bytes(self.anchor_surface_nonce),
                "expiry_constraints": Map.from_dict(
                    {
                        "cycles_max": Uint(self.expiry_constraints.cycles_max),
                        "wall_clock_seconds_max": Uint(
                            self.expiry_constraints.wall_clock_seconds_max
                        ),
                    }
                ),
            }
        )
        return encode(m_value)


@dataclass(frozen=True, slots=True)
class OwnerSignedAttestation:
    """The owner-signed attestation returned from anchor surface to substrate.

    The owner signs the canonical bytes of the tuple
    ``(substrate_id, dag_tip_hash, proposed_mutation_hash,
       operator_witness_signature, operator_signing_key_public,
       anchor_surface_nonce, anchor_surface_timestamp)``
    using the active owner private key. The substrate verifies the signature
    against the active owner public key on receipt.

    Per L1_GOVERNANCE §2.4: substrate emits canonical bytes; substrate does
    not narrate. The owner-side anchor-surface client owns rendering.
    """

    substrate_id: str
    dag_tip_hash: NodeHash
    proposed_mutation_hash: NodeHash
    operator_witness: Ed25519Signature
    operator_signing_key_public: Ed25519PublicKey
    anchor_surface_nonce: bytes
    anchor_surface_timestamp_unix_seconds: int
    """Trusted wall-clock from anchor surface (owner-side; substrate cannot
    forge per L1_HARD_RULES §4 anchor-surface-resident state list)."""

    owner_signature: Ed25519Signature
    """Owner's Ed25519 signature over ``signed_tuple_canonical_bytes()``."""

    def signed_tuple_canonical_bytes(self) -> CanonicalBytes:
        """Canonical bytes of the tuple the owner signed."""
        m_value = Map.from_dict(
            {
                "substrate_id": String(self.substrate_id),
                "dag_tip_hash": Hash(self.dag_tip_hash.bytes_),
                "proposed_mutation_hash": Hash(self.proposed_mutation_hash.bytes_),
                "operator_witness": Bytes(self.operator_witness.bytes_),
                "operator_signing_key_public": Bytes(
                    self.operator_signing_key_public.bytes_
                ),
                "anchor_surface_nonce": Bytes(self.anchor_surface_nonce),
                "anchor_surface_timestamp_unix_seconds": Timestamp(
                    self.anchor_surface_timestamp_unix_seconds
                ),
            }
        )
        return encode(m_value)


# ---------------------------------------------------------------------------
# Substrate-side verification (L1_GOVERNANCE §2.3).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VerificationContext:
    """The substrate-state context needed to verify an owner-signed attestation.

    Provided by the substrate's runtime; this module is pure (no I/O).
    """

    owner_public_key_active_at_timestamp: Ed25519PublicKey
    """The owner public key active at ``OwnerSignedAttestation.anchor_surface_timestamp_unix_seconds``
    per L1_GOVERNANCE §3.1 owner_key_history. M2 minimum: pass the single
    active key. M3+ resolves via owner_keys.active_at(timestamp)."""

    current_substrate_cycle: int
    """The substrate's current metabolic-cycle counter (for dual-clock check)."""

    current_wall_clock_unix_seconds: int
    """The substrate's view of wall-clock seconds (for dual-clock check).
    Used to assess that the anchor_surface_timestamp is plausibly recent.

    Per L1_GOVERNANCE §2.3 step 3: substrate cannot extend wall-clock budget
    by throttling cycles; both clocks must agree."""

    consumed_nonces: frozenset[bytes] = field(default_factory=frozenset)
    """Set of anchor-surface nonces already consumed by this substrate. Per
    §2.3 step 4: the anchor surface maintains the authoritative log;
    substrate-side replay protection is non-authoritative but adds a layer."""

    original_request_substrate_cycle: int | None = None
    """The substrate-cycle counter when the original AttestationRequest was
    emitted. If None, dual-clock cycle check is skipped (caller is responsible
    for asserting it is supplied for production flow)."""

    original_request_constraints: ExpiryConstraints | None = None
    """Expiry constraints from the original request. Same caveat as above."""


def verify_owner_signed_attestation(
    attestation: OwnerSignedAttestation,
    ctx: VerificationContext,
) -> None:
    """Verify an owner-signed attestation per L1_GOVERNANCE §2.3.

    Steps (in order):

    1. Recompute signed tuple canonical bytes from the attestation fields.
    2. Verify owner signature against ``owner_public_key_active_at_timestamp``.
    3. Verify dual-clock expiry (substrate-cycle AND anchor wall-clock).
    4. Verify the anchor-surface nonce has not been previously consumed.

    Raises:
        AttestationInvalid: signature does not verify.
        ExpiredAttestation: either clock has expired.
        NonceMismatch: nonce has been consumed already.
    """
    # Step 1 + 2: signature verification.
    canonical = attestation.signed_tuple_canonical_bytes()
    try:
        verify_signature(
            ctx.owner_public_key_active_at_timestamp.bytes_,
            attestation.owner_signature.bytes_,
            canonical.bytes_,
        )
    except SignatureInvalid as e:
        raise AttestationInvalid("owner signature does not verify") from e

    # Step 3: dual-clock expiry (if context provided original-request state).
    if (
        ctx.original_request_substrate_cycle is not None
        and ctx.original_request_constraints is not None
    ):
        cycles_elapsed = (
            ctx.current_substrate_cycle - ctx.original_request_substrate_cycle
        )
        if cycles_elapsed > ctx.original_request_constraints.cycles_max:
            raise ExpiredAttestation(
                f"substrate-cycle expiry: {cycles_elapsed} cycles elapsed exceeds "
                f"max {ctx.original_request_constraints.cycles_max}"
            )

        wall_clock_delta = (
            ctx.current_wall_clock_unix_seconds
            - attestation.anchor_surface_timestamp_unix_seconds
        )
        if wall_clock_delta > ctx.original_request_constraints.wall_clock_seconds_max:
            raise ExpiredAttestation(
                f"wall-clock expiry: {wall_clock_delta}s elapsed since anchor timestamp "
                f"exceeds max {ctx.original_request_constraints.wall_clock_seconds_max}s"
            )

    # Step 4: nonce-replay protection.
    if attestation.anchor_surface_nonce in ctx.consumed_nonces:
        raise NonceMismatch(
            f"anchor-surface nonce already consumed: {attestation.anchor_surface_nonce.hex()}"
        )


# ---------------------------------------------------------------------------
# Anchor-surface-side verification helpers (used by anchor_client).
#
# These are exposed in the Python module so that test integration suites can
# simulate the anchor-surface verification flow without invoking TS code.
# In production, these verifications happen in the TypeScript anchor_client
# implementation.
# ---------------------------------------------------------------------------


def verify_operator_witness(
    request: AttestationRequest,
) -> None:
    """Verify the operator_witness signature in an attestation request
    (L1_HARD_RULES C17 detector).

    Per L1_GOVERNANCE §2.3 step 3 (anchor-surface side): the operator_witness
    must be a valid Ed25519 signature over
    ``proposed_mutation_canonical_bytes`` using ``operator_signing_key_public``.

    Raises:
        OperatorWitnessForgery: signature does not verify.
    """
    try:
        verify_signature(
            request.operator_signing_key_public.bytes_,
            request.operator_witness.bytes_,
            request.proposed_mutation_canonical_bytes.bytes_,
        )
    except SignatureInvalid as e:
        raise OperatorWitnessForgery(
            "operator_witness signature does not verify"
        ) from e


def construct_owner_signed_from_request(
    request: AttestationRequest,
    anchor_surface_timestamp_unix_seconds: int,
    owner_signature: Ed25519Signature,
) -> OwnerSignedAttestation:
    """Helper to construct an :class:`OwnerSignedAttestation` from a request
    + the owner's signature + the anchor-surface trusted timestamp.

    The actual signing happens in anchor_client (TypeScript) using the
    owner's sealed private key. This helper exists for tests + the M2
    end-to-end integration test (which simulates the owner side in Python).
    """
    return OwnerSignedAttestation(
        substrate_id=request.substrate_id,
        dag_tip_hash=request.dag_tip_hash,
        proposed_mutation_hash=request.proposed_mutation_hash,
        operator_witness=request.operator_witness,
        operator_signing_key_public=request.operator_signing_key_public,
        anchor_surface_nonce=request.anchor_surface_nonce,
        anchor_surface_timestamp_unix_seconds=anchor_surface_timestamp_unix_seconds,
        owner_signature=owner_signature,
    )
