"""Tests for the I2 classifier (L1_GOVERNANCE §1)."""

from __future__ import annotations

import pytest

from myco_kernel_governance.classifier import (
    SEED_DIMENSION_TABLE,
    Classification,
    ClassifierContext,
    ClassifierRule,
    MutationEnvelope,
    classify,
    matched_rules,
)


# ---------------------------------------------------------------------------
# Untyped (no rule matches) — rejected at skin (I8).
# ---------------------------------------------------------------------------


def test_untyped_no_match() -> None:
    env = MutationEnvelope(mutation_type="unknown_kind")
    assert classify(env) is Classification.UNTYPED


def test_untyped_empty_envelope() -> None:
    env = MutationEnvelope()
    assert classify(env) is Classification.UNTYPED


# ---------------------------------------------------------------------------
# Daily classification — autonomous, no owner attestation.
# ---------------------------------------------------------------------------


def test_daily_delta_absorb() -> None:
    env = MutationEnvelope(mutation_type="delta_absorb")
    assert classify(env) is Classification.DAILY


def test_daily_gradient_update_non_mortality() -> None:
    env = MutationEnvelope(mutation_type="gradient_update_non_mortality")
    assert classify(env) is Classification.DAILY


def test_daily_sporocarp_fruit() -> None:
    env = MutationEnvelope(mutation_type="sporocarp_fruit")
    assert classify(env) is Classification.DAILY


def test_daily_federation_coupling() -> None:
    env = MutationEnvelope(mutation_type="federation_coupling")
    assert classify(env) is Classification.DAILY


# ---------------------------------------------------------------------------
# CI classification — file-prefix rules (L-layer doctrine).
# ---------------------------------------------------------------------------


def test_ci_l0_file() -> None:
    env = MutationEnvelope(
        touched_files=frozenset({"docs/architecture/L0_VISION.md"}),
        mutation_type="doc_edit",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_l1_file() -> None:
    env = MutationEnvelope(
        touched_files=frozenset({"docs/architecture/L1_GOVERNANCE.md"}),
        mutation_type="doc_edit",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_non_doctrine_file_not_ci_by_path() -> None:
    """A README edit by itself isn't CI — only L0/L1 file prefixes elevate."""
    env = MutationEnvelope(
        touched_files=frozenset({"README.md"}),
        mutation_type="doc_edit",
    )
    # No rule matches → UNTYPED (mutation_type "doc_edit" has no daily rule).
    assert classify(env) is Classification.UNTYPED


# ---------------------------------------------------------------------------
# CI classification — field-name rules (identity-critical SSoT fields).
# ---------------------------------------------------------------------------


def test_ci_substrate_id_field() -> None:
    env = MutationEnvelope(
        touched_fields=frozenset({"substrate_id"}),
        mutation_type="field_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_owner_key_history_field() -> None:
    env = MutationEnvelope(
        touched_fields=frozenset({"owner_key_history"}),
        mutation_type="field_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_anchor_surface_endpoint_field() -> None:
    env = MutationEnvelope(
        touched_fields=frozenset({"anchor_surface_endpoint_public_key"}),
        mutation_type="field_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_dag_tip_hash_field() -> None:
    env = MutationEnvelope(
        touched_fields=frozenset({"dag_tip_hash"}),
        mutation_type="field_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


# ---------------------------------------------------------------------------
# CI classification — meta-structure rules.
# ---------------------------------------------------------------------------


def test_ci_classifier_dimension_table_meta() -> None:
    """L0 I2 classifier-fixed-point: the table itself is CI-protected."""
    env = MutationEnvelope(
        touched_meta_structures=frozenset({"classifier_dimension_table"}),
        mutation_type="meta_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_mortality_signal_threshold_meta() -> None:
    env = MutationEnvelope(
        touched_meta_structures=frozenset({"mortality_signal_threshold"}),
        mutation_type="meta_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_mortality_signal_update_rule_meta() -> None:
    env = MutationEnvelope(
        touched_meta_structures=frozenset({"mortality_signal_update_rule"}),
        mutation_type="meta_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_skin_surface_declaration_meta() -> None:
    env = MutationEnvelope(
        touched_meta_structures=frozenset({"skin_surface_declaration"}),
        mutation_type="meta_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_federation_peer_attestation_list_meta() -> None:
    env = MutationEnvelope(
        touched_meta_structures=frozenset({"federation_peer_attestation_list"}),
        mutation_type="meta_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


# ---------------------------------------------------------------------------
# Mortality-axis gradient update is CI (special-cased per §1.2).
# ---------------------------------------------------------------------------


def test_ci_mortality_gradient_update() -> None:
    env = MutationEnvelope(mutation_type="gradient_update_mortality")
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


# ---------------------------------------------------------------------------
# CI dominates daily when both match (L0 I2 — CI never downgrades).
# ---------------------------------------------------------------------------


def test_ci_dominates_daily_when_both_match() -> None:
    env = MutationEnvelope(
        touched_fields=frozenset({"substrate_id"}),  # CI rule
        mutation_type="delta_absorb",  # daily rule
    )
    # CI wins.
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


# ---------------------------------------------------------------------------
# Birth-period elevation (§1.3).
# ---------------------------------------------------------------------------


def test_birth_period_elevates_daily_to_ci() -> None:
    env = MutationEnvelope(mutation_type="delta_absorb")
    ctx_steady = ClassifierContext(birth_period_active=False)
    ctx_birth = ClassifierContext(birth_period_active=True)

    assert classify(env, context=ctx_steady) is Classification.DAILY
    assert classify(env, context=ctx_birth) is Classification.CONTRACT_IDENTITY_LEVEL


def test_birth_period_does_not_elevate_untyped() -> None:
    env = MutationEnvelope(mutation_type="unknown_kind")
    ctx_birth = ClassifierContext(birth_period_active=True)
    # UNTYPED has no matched rules, so birth-period elevation doesn't apply.
    assert classify(env, context=ctx_birth) is Classification.UNTYPED


# ---------------------------------------------------------------------------
# matched_rules helper for debugging / immune sporocarp construction.
# ---------------------------------------------------------------------------


def test_matched_rules_returns_all_matching() -> None:
    env = MutationEnvelope(
        touched_fields=frozenset({"substrate_id"}),
        mutation_type="delta_absorb",
    )
    rules = matched_rules(env)
    rule_names = {r.name for r in rules}
    assert "substrate_id_field" in rule_names
    assert "daily_delta_absorb" in rule_names
    # Exactly 2 rules match (no others share these scopes).
    assert len(rules) == 2


def test_matched_rules_empty_for_untyped() -> None:
    env = MutationEnvelope(mutation_type="unknown_kind")
    assert matched_rules(env) == []


# ---------------------------------------------------------------------------
# Custom dimension table (substrate has extended via CI mutation).
# ---------------------------------------------------------------------------


def test_custom_dimension_table() -> None:
    custom_table = SEED_DIMENSION_TABLE + (
        ClassifierRule(
            name="custom_field_xyz",
            classification=Classification.CONTRACT_IDENTITY_LEVEL,
            field_name="xyz",
        ),
    )
    env = MutationEnvelope(
        touched_fields=frozenset({"xyz"}),
        mutation_type="field_update",
    )
    # Seed table alone: UNTYPED (no rule matches).
    assert classify(env) is Classification.UNTYPED
    # Custom table: CI.
    assert classify(env, dimension_table=custom_table) is Classification.CONTRACT_IDENTITY_LEVEL


# ---------------------------------------------------------------------------
# Sanity: seed table size matches L1_GOVERNANCE §1.2.
# ---------------------------------------------------------------------------


def test_seed_table_size() -> None:
    """L1_GOVERNANCE §1.2 lists 18 rows; allow for some L4-level expansion.

    This test pins the current seed-table size so future edits are
    intentional (any add/remove of a seed rule will require updating this
    test, which serves as a tripwire).
    """
    assert len(SEED_DIMENSION_TABLE) == 22  # 2 file-prefix + 4 identity-fields + 10 meta-structures + 4 daily + 1 mortality-detail + 1 schema_evolution (M17)


def test_classifier_rule_predicate_or_logic() -> None:
    """A single rule with multiple predicates matches if ANY predicate fires."""
    rule = ClassifierRule(
        name="combo",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        field_name="x",
        mutation_type="t",
    )
    # Match via field only.
    assert rule.matches(
        MutationEnvelope(touched_fields=frozenset({"x"}), mutation_type="other")
    )
    # Match via mutation_type only.
    assert rule.matches(
        MutationEnvelope(touched_fields=frozenset(), mutation_type="t")
    )
    # No match.
    assert not rule.matches(MutationEnvelope(mutation_type="other"))
