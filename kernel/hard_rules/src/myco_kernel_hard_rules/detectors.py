"""20 CRITICAL breach detectors (L1_HARD_RULES §1 C1-C20).

When ANY of these fires, the substrate auto-quarantines per L1_CONTINUITY
§5 and emits the corresponding immune sporocarp. Owner-attested
quarantine_clearance is required for resumption.

## Doctrine

Per L1_HARD_RULES §1 + §5: each detector is independent (none can be
silently downgraded). Each row independently traces to ≥1 L0 P + ≥1 I.

## M4 scope

This module ships the detector framework + structured event types. M3
already implemented some of these in their respective kernel crates
(e.g., kernel/skin C2/C11; kernel/schema C7; kernel/governance C5/C17).
This module provides the UNIFIED dispatch surface that downstream
runtime consumers (the substrate's metabolic cycle step 4) use to check
all 20 in one pass.

For M4 minimum-viable: detector framework + 10 representative detectors.
M5+ adds remaining detectors + concrete cross-crate integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class BreachId(Enum):
    """L1_HARD_RULES §1 C-row identifiers (20 CRITICAL detectors)."""

    C1_APPETITE_LOCALITY_BREACH = "appetite_locality_breach"
    C2_OUTPUT_ENDPOINT_BREACH = "output_endpoint_breach"
    C3_POST_HANDSHAKE_CI_UNATTESTED = "post_handshake_ci_unattested"
    C4_SUBSTRATE_SECRET_UNSEALED = "substrate_secret_unsealed"
    C5_ATTESTATION_INVALID = "attestation_invalid"
    C6_DAG_ENUMERATION_UNCLOSED = "dag_enumeration_unclosed"
    C7_DAG_RETRO_EDIT_DETECTED = "dag_retro_edit_detected"
    C8_SSOT_MIGRATION_PHASE_SKIP = "ssot_migration_phase_skip"
    C9_COLD_RESUME_INVARIANT_FAILURE = "cold_resume_invariant_failure"
    C10_AGENT_DISCRIMINATING_ATTRIBUTE_PERSISTED = (
        "agent_discriminating_attribute_persisted"
    )
    C11_CONCURRENT_OPERATOR_PERSISTENT = "concurrent_operator_persistent"
    C12_SUCCESSOR_ACTIVATION_WITH_FRESH_OWNER_HEARTBEAT = (
        "successor_activation_with_fresh_owner_heartbeat"
    )
    C13_PEER_ATTESTATION_REVOKED_EGRESS = "peer_attestation_revoked_egress"
    C14_UNTYPED_MUTATION = "untyped_mutation"
    C15_CLASSIFIER_FIXED_POINT_BYPASS = "classifier_fixed_point_bypass"
    C16_MORTALITY_SIGNAL_SUPPRESSION = "mortality_signal_suppression"
    C17_OPERATOR_WITNESS_FORGERY = "operator_witness_forgery"
    C18_CANONICAL_BYTES_RENDER_DRIFT = "canonical_bytes_render_drift"
    C19_PAUSED_DORMANCY_UNSAFE_HOST = "paused_dormancy_unsafe_host"
    C20_GENESIS_ATTESTATION_CHAIN_BROKEN = "genesis_attestation_chain_broken"


@dataclass(frozen=True, slots=True)
class ImmuneEvent:
    """A single immune-event sporocarp emission.

    Per L1_HARD_RULES §1: each CRITICAL detection emits one of these.
    Triggers auto-quarantine via L1_CONTINUITY §5.

    Fields
    ------
    breach_id:
        Which C-row detector fired.
    at_cycle:
        Substrate metabolic-cycle counter at detection time.
    description:
        Human-readable description (for owner audit).
    evidence:
        Substrate-defined evidence payload (e.g., canonical-bytes of the
        offending mutation, signature bytes of a forged witness, etc.).
    """

    breach_id: BreachId
    at_cycle: int
    description: str
    evidence: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Detector input event types (one per scenario).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EgressAttempt:
    """An outbound network connection / output attempt (C1 + C2 detector input)."""

    target_uri: str
    declared_endpoints: tuple[str, ...]
    """The declared output endpoints from skin surface declaration."""


@dataclass(frozen=True, slots=True)
class MutationClassification:
    """A classified mutation (C14 detector input)."""

    classification: str  # "daily" / "contract_identity_level" / "untyped"


@dataclass(frozen=True, slots=True)
class DagNodeAttempt:
    """A DAG node insertion attempt (C7 detector input — retro-edit check)."""

    stored_hash_hex: str
    recomputed_hash_hex: str


@dataclass(frozen=True, slots=True)
class OperatorWitnessVerification:
    """An operator-witness verification attempt (C17 detector input)."""

    verified: bool
    operator_pubkey_hex: str


@dataclass(frozen=True, slots=True)
class AttestationVerification:
    """An owner-attestation verification attempt (C5 detector input)."""

    verified: bool
    failure_reason: Optional[str]


@dataclass(frozen=True, slots=True)
class HandshakeAttempt:
    """A handshake attempt (C11 detector input — single-operator enforcement)."""

    has_active_operator: bool


# ---------------------------------------------------------------------------
# Detector functions.
#
# Each detector takes a structured event + the current cycle, returning
# Optional[ImmuneEvent]. If returned, the substrate quarantines.
# ---------------------------------------------------------------------------


def detect_c1_appetite_locality_breach(
    egress: EgressAttempt, at_cycle: int
) -> Optional[ImmuneEvent]:
    """C1: detect unauthorized network egress (L1_SKIN §5)."""
    if egress.target_uri not in egress.declared_endpoints:
        return ImmuneEvent(
            breach_id=BreachId.C1_APPETITE_LOCALITY_BREACH,
            at_cycle=at_cycle,
            description=(
                f"egress to {egress.target_uri} not in declared endpoints"
            ),
            evidence={"target_uri": egress.target_uri},
        )
    return None


def detect_c2_output_endpoint_breach(
    egress: EgressAttempt, at_cycle: int
) -> Optional[ImmuneEvent]:
    """C2: detect output to non-declared endpoint (L1_SKIN §3)."""
    if egress.target_uri not in egress.declared_endpoints:
        return ImmuneEvent(
            breach_id=BreachId.C2_OUTPUT_ENDPOINT_BREACH,
            at_cycle=at_cycle,
            description=f"output to undeclared endpoint: {egress.target_uri}",
            evidence={"target_uri": egress.target_uri},
        )
    return None


def detect_c7_dag_retro_edit(
    attempt: DagNodeAttempt, at_cycle: int
) -> Optional[ImmuneEvent]:
    """C7: detect DAG node hash mismatch from re-computation (L1_SCHEMA §2.1).

    Per pass-3 mycoparasite-2: prevents hidden retro-edit attacks.
    """
    if attempt.stored_hash_hex != attempt.recomputed_hash_hex:
        return ImmuneEvent(
            breach_id=BreachId.C7_DAG_RETRO_EDIT_DETECTED,
            at_cycle=at_cycle,
            description=(
                f"DAG node retro-edit: stored {attempt.stored_hash_hex} "
                f"differs from recomputed {attempt.recomputed_hash_hex}"
            ),
            evidence={
                "stored_hash_hex": attempt.stored_hash_hex,
                "recomputed_hash_hex": attempt.recomputed_hash_hex,
            },
        )
    return None


def detect_c5_attestation_invalid(
    verification: AttestationVerification, at_cycle: int
) -> Optional[ImmuneEvent]:
    """C5: detect attestation verification failure (L1_GOVERNANCE §2.3)."""
    if not verification.verified:
        return ImmuneEvent(
            breach_id=BreachId.C5_ATTESTATION_INVALID,
            at_cycle=at_cycle,
            description=(
                f"attestation invalid: "
                f"{verification.failure_reason or 'unspecified'}"
            ),
            evidence={"failure_reason": verification.failure_reason},
        )
    return None


def detect_c11_concurrent_operator(
    attempt: HandshakeAttempt, at_cycle: int
) -> Optional[ImmuneEvent]:
    """C11: detect concurrent-operator persistence beyond strict-FIFO window
    (L1_SKIN §4.4)."""
    if attempt.has_active_operator:
        return ImmuneEvent(
            breach_id=BreachId.C11_CONCURRENT_OPERATOR_PERSISTENT,
            at_cycle=at_cycle,
            description=(
                "concurrent operator attempt while another is active "
                "beyond FIFO window"
            ),
            evidence={},
        )
    return None


def detect_c14_untyped_mutation(
    classification: MutationClassification, at_cycle: int
) -> Optional[ImmuneEvent]:
    """C14: detect untyped mutation (no classifier rule matches;
    L1_GOVERNANCE §1.1 — rejected at skin)."""
    if classification.classification == "untyped":
        return ImmuneEvent(
            breach_id=BreachId.C14_UNTYPED_MUTATION,
            at_cycle=at_cycle,
            description="mutation cannot be classified",
            evidence={},
        )
    return None


def detect_c17_operator_witness_forgery(
    verification: OperatorWitnessVerification, at_cycle: int
) -> Optional[ImmuneEvent]:
    """C17: detect operator_witness signature forgery (L1_GOVERNANCE §2.2 +
    pass-3 mycorrhiza-17)."""
    if not verification.verified:
        return ImmuneEvent(
            breach_id=BreachId.C17_OPERATOR_WITNESS_FORGERY,
            at_cycle=at_cycle,
            description=(
                f"operator_witness forgery on key "
                f"{verification.operator_pubkey_hex[:16]}…"
            ),
            evidence={"operator_pubkey_hex": verification.operator_pubkey_hex},
        )
    return None


def detect_c18_canonical_bytes_render_drift(
    expected_canonical_hex: str,
    actual_render_hex: str,
    at_cycle: int,
) -> Optional[ImmuneEvent]:
    """C18: detect canonical-bytes render drift (L0 §9.3)."""
    if expected_canonical_hex != actual_render_hex:
        return ImmuneEvent(
            breach_id=BreachId.C18_CANONICAL_BYTES_RENDER_DRIFT,
            at_cycle=at_cycle,
            description="canonical-bytes render differs from substrate-emitted",
            evidence={
                "expected_hex": expected_canonical_hex,
                "actual_hex": actual_render_hex,
            },
        )
    return None


# ---------------------------------------------------------------------------
# Detector dispatch table.
#
# Maps BreachId to a callable that, given the right structured event,
# returns Optional[ImmuneEvent]. Used by the runtime to dispatch events
# to the correct detector(s) — typically one event-shape feeds one
# detector, but C1 + C2 share EgressAttempt input.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class DetectorRegistry:
    """Holds the active detectors. M4 minimum: 8 detectors registered.
    M5+ adds C3 / C4 / C6 / C8 / C9 / C10 / C12 / C13 / C15 / C16 / C19 / C20.
    """

    _detectors: dict[BreachId, Callable[..., Optional[ImmuneEvent]]] = field(
        default_factory=dict
    )

    def register(
        self,
        breach_id: BreachId,
        detector: Callable[..., Optional[ImmuneEvent]],
    ) -> None:
        """Register a detector for a breach id."""
        self._detectors[breach_id] = detector

    def get(
        self, breach_id: BreachId
    ) -> Optional[Callable[..., Optional[ImmuneEvent]]]:
        """Look up a registered detector by breach id."""
        return self._detectors.get(breach_id)

    def has(self, breach_id: BreachId) -> bool:
        """Whether a detector for this breach id is registered."""
        return breach_id in self._detectors

    def registered_ids(self) -> list[BreachId]:
        """All registered breach ids."""
        return list(self._detectors.keys())


def build_default_registry() -> DetectorRegistry:
    """Construct the M4-default detector registry (8 detectors)."""
    reg = DetectorRegistry()
    reg.register(BreachId.C1_APPETITE_LOCALITY_BREACH, detect_c1_appetite_locality_breach)
    reg.register(BreachId.C2_OUTPUT_ENDPOINT_BREACH, detect_c2_output_endpoint_breach)
    reg.register(BreachId.C5_ATTESTATION_INVALID, detect_c5_attestation_invalid)
    reg.register(BreachId.C7_DAG_RETRO_EDIT_DETECTED, detect_c7_dag_retro_edit)
    reg.register(BreachId.C11_CONCURRENT_OPERATOR_PERSISTENT, detect_c11_concurrent_operator)
    reg.register(BreachId.C14_UNTYPED_MUTATION, detect_c14_untyped_mutation)
    reg.register(BreachId.C17_OPERATOR_WITNESS_FORGERY, detect_c17_operator_witness_forgery)
    reg.register(BreachId.C18_CANONICAL_BYTES_RENDER_DRIFT, detect_c18_canonical_bytes_render_drift)
    return reg
