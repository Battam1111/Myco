"""Tests for L1_HARD_RULES CRITICAL detectors."""

from __future__ import annotations

import pytest

from myco_kernel_hard_rules.detectors import (
    AttestationVerification,
    BreachId,
    DagNodeAttempt,
    DetectorRegistry,
    EgressAttempt,
    HandshakeAttempt,
    ImmuneEvent,
    MutationClassification,
    OperatorWitnessVerification,
    build_default_registry,
    detect_c1_appetite_locality_breach,
    detect_c2_output_endpoint_breach,
    detect_c5_attestation_invalid,
    detect_c7_dag_retro_edit,
    detect_c11_concurrent_operator,
    detect_c14_untyped_mutation,
    detect_c17_operator_witness_forgery,
    detect_c18_canonical_bytes_render_drift,
)


# ---------------------------------------------------------------------------
# C1 + C2: egress detectors.
# ---------------------------------------------------------------------------


def test_c1_fires_on_undeclared_egress() -> None:
    event = detect_c1_appetite_locality_breach(
        EgressAttempt(
            target_uri="https://attacker.evil",
            declared_endpoints=("https://anchor",),
        ),
        at_cycle=100,
    )
    assert event is not None
    assert event.breach_id is BreachId.C1_APPETITE_LOCALITY_BREACH


def test_c1_passes_on_declared_egress() -> None:
    event = detect_c1_appetite_locality_breach(
        EgressAttempt(
            target_uri="https://anchor",
            declared_endpoints=("https://anchor",),
        ),
        at_cycle=100,
    )
    assert event is None


def test_c2_fires_on_undeclared_output() -> None:
    event = detect_c2_output_endpoint_breach(
        EgressAttempt(
            target_uri="https://unknown",
            declared_endpoints=("https://anchor",),
        ),
        at_cycle=100,
    )
    assert event is not None
    assert event.breach_id is BreachId.C2_OUTPUT_ENDPOINT_BREACH


# ---------------------------------------------------------------------------
# C7: DAG retro-edit.
# ---------------------------------------------------------------------------


def test_c7_fires_on_hash_mismatch() -> None:
    event = detect_c7_dag_retro_edit(
        DagNodeAttempt(
            stored_hash_hex="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            recomputed_hash_hex="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        ),
        at_cycle=42,
    )
    assert event is not None
    assert event.breach_id is BreachId.C7_DAG_RETRO_EDIT_DETECTED
    assert event.at_cycle == 42


def test_c7_passes_on_hash_match() -> None:
    h = "aa" * 32
    event = detect_c7_dag_retro_edit(
        DagNodeAttempt(stored_hash_hex=h, recomputed_hash_hex=h),
        at_cycle=42,
    )
    assert event is None


# ---------------------------------------------------------------------------
# C5: attestation invalid.
# ---------------------------------------------------------------------------


def test_c5_fires_on_invalid_attestation() -> None:
    event = detect_c5_attestation_invalid(
        AttestationVerification(verified=False, failure_reason="bad signature"),
        at_cycle=100,
    )
    assert event is not None
    assert event.breach_id is BreachId.C5_ATTESTATION_INVALID


def test_c5_passes_on_valid_attestation() -> None:
    event = detect_c5_attestation_invalid(
        AttestationVerification(verified=True, failure_reason=None),
        at_cycle=100,
    )
    assert event is None


# ---------------------------------------------------------------------------
# C11: concurrent operator.
# ---------------------------------------------------------------------------


def test_c11_fires_on_active_operator_collision() -> None:
    event = detect_c11_concurrent_operator(
        HandshakeAttempt(has_active_operator=True),
        at_cycle=200,
    )
    assert event is not None
    assert event.breach_id is BreachId.C11_CONCURRENT_OPERATOR_PERSISTENT


def test_c11_passes_when_no_active_operator() -> None:
    event = detect_c11_concurrent_operator(
        HandshakeAttempt(has_active_operator=False),
        at_cycle=200,
    )
    assert event is None


# ---------------------------------------------------------------------------
# C14: untyped mutation.
# ---------------------------------------------------------------------------


def test_c14_fires_on_untyped() -> None:
    event = detect_c14_untyped_mutation(
        MutationClassification(classification="untyped"),
        at_cycle=5,
    )
    assert event is not None


def test_c14_passes_on_classified() -> None:
    for cls in ["daily", "contract_identity_level"]:
        event = detect_c14_untyped_mutation(
            MutationClassification(classification=cls), at_cycle=5
        )
        assert event is None


# ---------------------------------------------------------------------------
# C17: operator witness forgery.
# ---------------------------------------------------------------------------


def test_c17_fires_on_unverified_witness() -> None:
    event = detect_c17_operator_witness_forgery(
        OperatorWitnessVerification(verified=False, operator_pubkey_hex="ff" * 32),
        at_cycle=1,
    )
    assert event is not None


def test_c17_passes_on_verified() -> None:
    event = detect_c17_operator_witness_forgery(
        OperatorWitnessVerification(verified=True, operator_pubkey_hex="ff" * 32),
        at_cycle=1,
    )
    assert event is None


# ---------------------------------------------------------------------------
# C18: render drift.
# ---------------------------------------------------------------------------


def test_c18_fires_on_render_mismatch() -> None:
    event = detect_c18_canonical_bytes_render_drift(
        expected_canonical_hex="abcd",
        actual_render_hex="abce",
        at_cycle=10,
    )
    assert event is not None
    assert event.breach_id is BreachId.C18_CANONICAL_BYTES_RENDER_DRIFT


def test_c18_passes_on_render_match() -> None:
    event = detect_c18_canonical_bytes_render_drift(
        expected_canonical_hex="abcd",
        actual_render_hex="abcd",
        at_cycle=10,
    )
    assert event is None


# ---------------------------------------------------------------------------
# DetectorRegistry behavior.
# ---------------------------------------------------------------------------


def test_default_registry_has_8_detectors() -> None:
    reg = build_default_registry()
    assert len(reg.registered_ids()) == 8


def test_default_registry_contains_expected_ids() -> None:
    reg = build_default_registry()
    expected = {
        BreachId.C1_APPETITE_LOCALITY_BREACH,
        BreachId.C2_OUTPUT_ENDPOINT_BREACH,
        BreachId.C5_ATTESTATION_INVALID,
        BreachId.C7_DAG_RETRO_EDIT_DETECTED,
        BreachId.C11_CONCURRENT_OPERATOR_PERSISTENT,
        BreachId.C14_UNTYPED_MUTATION,
        BreachId.C17_OPERATOR_WITNESS_FORGERY,
        BreachId.C18_CANONICAL_BYTES_RENDER_DRIFT,
    }
    assert set(reg.registered_ids()) == expected


def test_registry_lookup_returns_detector() -> None:
    reg = build_default_registry()
    detector = reg.get(BreachId.C1_APPETITE_LOCALITY_BREACH)
    assert detector is not None


def test_registry_lookup_unregistered_returns_none() -> None:
    reg = DetectorRegistry()
    assert reg.get(BreachId.C1_APPETITE_LOCALITY_BREACH) is None


def test_registry_has_method() -> None:
    reg = build_default_registry()
    assert reg.has(BreachId.C1_APPETITE_LOCALITY_BREACH)
    assert not reg.has(BreachId.C3_POST_HANDSHAKE_CI_UNATTESTED)


# ---------------------------------------------------------------------------
# 20 breach-id enum completeness.
# ---------------------------------------------------------------------------


def test_breach_id_enum_has_20_members() -> None:
    """Per L1_HARD_RULES §1: exactly 20 C-row CRITICAL detectors."""
    assert len(list(BreachId)) == 20


def test_immune_event_with_evidence() -> None:
    event = ImmuneEvent(
        breach_id=BreachId.C7_DAG_RETRO_EDIT_DETECTED,
        at_cycle=100,
        description="test",
        evidence={"key": "value"},
    )
    assert event.evidence == {"key": "value"}
