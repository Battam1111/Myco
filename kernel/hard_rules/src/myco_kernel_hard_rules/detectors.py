"""CRITICAL breach detectors (L1/HARD_RULES §1).

When ANY of these fires, the substrate auto-quarantines per L1/CONTINUITY
§5 and emits the corresponding immune sporocarp.

## Doctrine

Per L1/HARD_RULES §1 + §5: each detector is independent (none can be
silently downgraded). Each row independently traces to ≥1 L0 P + ≥1 I.

## M4 scope

This module ships the detector framework + structured event types. M3
already implemented some of these in their respective kernel crates
(e.g., kernel/skin C2/C11; kernel/schema C7). This module provides the
UNIFIED dispatch surface that downstream runtime consumers (the substrate's
metabolic cycle step 4) use to check them in one pass.

## v0.9 owner-key removal

The owner-attestation breach rows — **C5** (attestation_invalid), **C12**
(successor_activation_with_fresh_owner_heartbeat), **C17**
(operator_witness_forgery), and **C20** (genesis_attestation_chain_broken) —
were removed with the rest of the owner-key/anchor subsystem (owner-signed
attestation envelopes, the operator witness signature, the cultivator
heartbeat, and the genesis birth-attestation chain no longer exist). All
non-owner-key detectors are retained, including C16 mortality_signal_suppression
(the P07 mortality-discipline watchdog).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class BreachId(Enum):
    """L1/HARD_RULES §1 C-row identifiers (CRITICAL detectors).

    **v0.9 owner-key removal**: C5 (attestation_invalid), C12
    (successor_activation_with_fresh_owner_heartbeat), C17
    (operator_witness_forgery), and C20 (genesis_attestation_chain_broken) were
    removed with the owner-key/anchor subsystem. The remaining C-rows keep their
    historical numbers (no renumbering).
    """

    C1_APPETITE_LOCALITY_BREACH = "appetite_locality_breach"
    C2_OUTPUT_ENDPOINT_BREACH = "output_endpoint_breach"
    C3_POST_HANDSHAKE_CI_UNATTESTED = "post_handshake_ci_unattested"
    C4_SUBSTRATE_SECRET_UNSEALED = "substrate_secret_unsealed"
    C6_DAG_ENUMERATION_UNCLOSED = "dag_enumeration_unclosed"
    C7_DAG_RETRO_EDIT_DETECTED = "dag_retro_edit_detected"
    C8_SSOT_MIGRATION_PHASE_SKIP = "ssot_migration_phase_skip"
    C9_COLD_RESUME_INVARIANT_FAILURE = "cold_resume_invariant_failure"
    C10_AGENT_DISCRIMINATING_ATTRIBUTE_PERSISTED = (
        "agent_discriminating_attribute_persisted"
    )
    C11_CONCURRENT_OPERATOR_PERSISTENT = "concurrent_operator_persistent"
    C13_PEER_ATTESTATION_REVOKED_EGRESS = "peer_attestation_revoked_egress"
    C14_UNTYPED_MUTATION = "untyped_mutation"
    C15_CLASSIFIER_FIXED_POINT_BYPASS = "classifier_fixed_point_bypass"
    C16_MORTALITY_SIGNAL_SUPPRESSION = "mortality_signal_suppression"
    C18_CANONICAL_BYTES_RENDER_DRIFT = "canonical_bytes_render_drift"
    C19_PAUSED_DORMANCY_UNSAFE_HOST = "paused_dormancy_unsafe_host"


@dataclass(frozen=True, slots=True)
class ImmuneEvent:
    """A single immune-event sporocarp emission.

    Per L1/HARD_RULES §1: each CRITICAL detection emits one of these.
    Triggers auto-quarantine via L1/CONTINUITY §5.

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
class HandshakeAttempt:
    """A handshake attempt (C11 detector input — single-operator enforcement)."""

    has_active_operator: bool


# ---------------------------------------------------------------------------
# Detector functions.
#
# Each detector takes a structured event + the current cycle, returning
# ImmuneEvent | None. If returned, the substrate quarantines.
# ---------------------------------------------------------------------------


def detect_c1_appetite_locality_breach(
    egress: EgressAttempt, at_cycle: int
) -> ImmuneEvent | None:
    """C1: detect unauthorized network egress (L1/SKIN §5)."""
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
) -> ImmuneEvent | None:
    """C2: detect output to non-declared endpoint (L1/SKIN §3)."""
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
) -> ImmuneEvent | None:
    """C7: detect DAG node hash mismatch from re-computation (L1/SCHEMA §2.1).

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


def detect_c11_concurrent_operator(
    attempt: HandshakeAttempt, at_cycle: int
) -> ImmuneEvent | None:
    """C11: detect concurrent-operator persistence beyond strict-FIFO window
    (L1/SKIN §4.4)."""
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
) -> ImmuneEvent | None:
    """C14: detect untyped mutation (no classifier rule matches;
    L1/GOVERNANCE §1.1 — rejected at skin)."""
    if classification.classification == "untyped":
        return ImmuneEvent(
            breach_id=BreachId.C14_UNTYPED_MUTATION,
            at_cycle=at_cycle,
            description="mutation cannot be classified",
            evidence={},
        )
    return None


def detect_c18_canonical_bytes_render_drift(
    expected_canonical_hex: str,
    actual_render_hex: str,
    at_cycle: int,
) -> ImmuneEvent | None:
    """C18: detect canonical-bytes render drift (L0/cards/AS_anchor_surface §3)."""
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
# returns ImmuneEvent | None. Used by the runtime to dispatch events
# to the correct detector(s) — typically one event-shape feeds one
# detector, but C1 + C2 share EgressAttempt input.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class DetectorRegistry:
    """Holds the active detectors. M4 minimum: 6 detectors registered
    (C5 + C17 removed with the v0.9 owner-key subsystem).
    M5+ adds C3 / C4 / C6 / C8 / C9 / C10 / C13 / C15 / C16 / C19.
    """

    _detectors: dict[BreachId, Callable[..., ImmuneEvent | None]] = field(
        default_factory=dict
    )

    def register(
        self,
        breach_id: BreachId,
        detector: Callable[..., ImmuneEvent | None],
    ) -> None:
        """Register a detector for a breach id."""
        self._detectors[breach_id] = detector

    def get(
        self, breach_id: BreachId
    ) -> Callable[..., ImmuneEvent | None] | None:
        """Look up a registered detector by breach id."""
        return self._detectors.get(breach_id)

    def has(self, breach_id: BreachId) -> bool:
        """Whether a detector for this breach id is registered."""
        return breach_id in self._detectors

    def registered_ids(self) -> list[BreachId]:
        """All registered breach ids."""
        return list(self._detectors.keys())


def build_default_registry() -> DetectorRegistry:
    """Construct the M4-default detector registry (6 detectors; C5 + C17 removed
    with the v0.9 owner-key subsystem)."""
    reg = DetectorRegistry()
    reg.register(BreachId.C1_APPETITE_LOCALITY_BREACH, detect_c1_appetite_locality_breach)
    reg.register(BreachId.C2_OUTPUT_ENDPOINT_BREACH, detect_c2_output_endpoint_breach)
    reg.register(BreachId.C7_DAG_RETRO_EDIT_DETECTED, detect_c7_dag_retro_edit)
    reg.register(BreachId.C11_CONCURRENT_OPERATOR_PERSISTENT, detect_c11_concurrent_operator)
    reg.register(BreachId.C14_UNTYPED_MUTATION, detect_c14_untyped_mutation)
    reg.register(BreachId.C18_CANONICAL_BYTES_RENDER_DRIFT, detect_c18_canonical_bytes_render_drift)
    return reg
