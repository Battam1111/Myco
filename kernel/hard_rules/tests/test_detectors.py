"""Tests for L1/HARD_RULES CRITICAL detectors."""

from __future__ import annotations

from myco_kernel_hard_rules.detectors import (
    BreachId,
    DagNodeAttempt,
    DetectorRegistry,
    EgressAttempt,
    HandshakeAttempt,
    ImmuneEvent,
    MutationClassification,
    build_default_registry,
    detect_c1_appetite_locality_breach,
    detect_c2_output_endpoint_breach,
    detect_c7_dag_retro_edit,
    detect_c11_concurrent_operator,
    detect_c14_untyped_mutation,
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


def test_default_registry_has_6_detectors() -> None:
    # v0.9 owner-key removal: C5 (attestation_invalid) + C17
    # (operator_witness_forgery) were removed → 8 - 2 = 6.
    reg = build_default_registry()
    assert len(reg.registered_ids()) == 6


def test_default_registry_contains_expected_ids() -> None:
    reg = build_default_registry()
    expected = {
        BreachId.C1_APPETITE_LOCALITY_BREACH,
        BreachId.C2_OUTPUT_ENDPOINT_BREACH,
        BreachId.C7_DAG_RETRO_EDIT_DETECTED,
        BreachId.C11_CONCURRENT_OPERATOR_PERSISTENT,
        BreachId.C14_UNTYPED_MUTATION,
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
# breach-id enum completeness.
# ---------------------------------------------------------------------------


def test_breach_id_enum_has_16_members() -> None:
    """v0.9 owner-key removal: the catalog of 20 C-rows dropped the four
    owner-attestation rows (C5 attestation_invalid, C12
    successor_activation_with_fresh_owner_heartbeat, C17
    operator_witness_forgery, C20 genesis_attestation_chain_broken) → 16.
    The surviving rows keep their historical numbers (no renumbering)."""
    assert len(list(BreachId)) == 16
    # The removed owner-attestation rows must be gone.
    names = {b.name for b in BreachId}
    assert "C5_ATTESTATION_INVALID" not in names
    assert "C12_SUCCESSOR_ACTIVATION_WITH_FRESH_OWNER_HEARTBEAT" not in names
    assert "C17_OPERATOR_WITNESS_FORGERY" not in names
    assert "C20_GENESIS_ATTESTATION_CHAIN_BROKEN" not in names
    # A representative non-owner-key row (mortality discipline) is retained.
    assert "C16_MORTALITY_SIGNAL_SUPPRESSION" in names


def test_immune_event_with_evidence() -> None:
    event = ImmuneEvent(
        breach_id=BreachId.C7_DAG_RETRO_EDIT_DETECTED,
        at_cycle=100,
        description="test",
        evidence={"key": "value"},
    )
    assert event.evidence == {"key": "value"}
