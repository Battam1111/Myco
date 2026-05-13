"""I2 classifier function — Python implementation (L1_GOVERNANCE §1).

Per L0 I2: every substrate mutation is classified into one of three buckets:

- ``daily`` — autonomously committed by the substrate per its own update rules.
- ``contract_identity_level`` — requires owner-attested CI envelope before commit.
- ``untyped`` — no classifier rule matches; rejected at the skin as breach.

The classifier function itself + the dimension table are **unconditional
contract-identity-level fixed points** (L1_HARD_RULES F1; L0 I2 classifier-
fixed-point). Mutating the dimension table via non-CI path is
``classifier_fixed_point_bypass`` (CRITICAL).

Birth-period elevation (per L1_GOVERNANCE §1.3): during the substrate's birth
period, ALL parameter-tuning events are CI regardless of steady-state
classification. The birth-period flag is held in SSoT and consulted at
classification time.

This module ships the **seed dimension table** from L1_GOVERNANCE §1.2. The
table is data-driven; new substrates may extend the table via CI mutation
(which itself goes through the classifier, with the dimension-table-mutation
row firing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class Classification(Enum):
    """Per L1_GOVERNANCE §1.1 classify result type."""

    DAILY = "daily"
    CONTRACT_IDENTITY_LEVEL = "contract_identity_level"
    UNTYPED = "untyped"


@dataclass(frozen=True, slots=True)
class MutationEnvelope:
    """The input to :func:`classify`.

    Per L1_GOVERNANCE §1.1: ``classify(mutation_envelope) → {daily,
    contract_identity_level, untyped}`` where the envelope carries the touched
    scope information.

    Fields
    ------
    touched_files:
        Set of file paths touched by the mutation (e.g.,
        ``{"docs/architecture/L0_VISION.md"}``).
    touched_fields:
        Set of SSoT field names touched (e.g., ``{"substrate_id"}``).
    touched_meta_structures:
        Set of meta-structure names touched (e.g.,
        ``{"classifier_dimension_table"}``, ``{"appetite_axis_schema"}``).
    mutation_type:
        Free-form tag describing the mutation kind (e.g., ``"delta_absorb"``,
        ``"sporocarp_fruit"``, ``"key_rotation"``).
    source_event_id:
        Optional ID of the sporocarp/event that triggered this mutation
        (for causal tracking).
    """

    touched_files: FrozenSet[str] = field(default_factory=frozenset)
    touched_fields: FrozenSet[str] = field(default_factory=frozenset)
    touched_meta_structures: FrozenSet[str] = field(default_factory=frozenset)
    mutation_type: str = ""
    source_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class ClassifierRule:
    """One row of the dimension table.

    A rule matches if ANY of its predicates fire on the mutation envelope.
    Matching rules contribute their classification; the *strongest* (CI > daily)
    classification across all matched rules wins.

    Predicates
    ----------
    file_path_prefix:
        Match if any touched_files path startswith this prefix.
    field_name:
        Match if `field_name` is in touched_fields.
    meta_structure_name:
        Match if `meta_structure_name` is in touched_meta_structures.
    mutation_type:
        Match if `mutation_type` equals the envelope's mutation_type.
    """

    name: str
    classification: Classification
    file_path_prefix: str | None = None
    field_name: str | None = None
    meta_structure_name: str | None = None
    mutation_type: str | None = None

    def matches(self, env: MutationEnvelope) -> bool:
        if self.file_path_prefix is not None:
            if any(p.startswith(self.file_path_prefix) for p in env.touched_files):
                return True
        if self.field_name is not None:
            if self.field_name in env.touched_fields:
                return True
        if self.meta_structure_name is not None:
            if self.meta_structure_name in env.touched_meta_structures:
                return True
        if self.mutation_type is not None:
            if self.mutation_type == env.mutation_type:
                return True
        return False


# L1_GOVERNANCE §1.2 seed dimension table.
#
# Per L0 I2 classifier-fixed-point + L1_HARD_RULES F1: this table itself is
# CI-protected. Substrates load this seed at genesis; modifications happen via
# CI attestation only.
SEED_DIMENSION_TABLE: tuple[ClassifierRule, ...] = (
    # L-layer doctrine files.
    ClassifierRule(
        name="l0_file_touched",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        file_path_prefix="docs/architecture/L0_",
    ),
    ClassifierRule(
        name="l1_file_touched",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        file_path_prefix="docs/architecture/L1_",
    ),
    # Identity-critical SSoT fields.
    ClassifierRule(
        name="substrate_id_field",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        field_name="substrate_id",
    ),
    ClassifierRule(
        name="owner_key_history_field",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        field_name="owner_key_history",
    ),
    ClassifierRule(
        name="anchor_surface_endpoint_field",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        field_name="anchor_surface_endpoint_public_key",
    ),
    ClassifierRule(
        name="dag_tip_hash_field",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        field_name="dag_tip_hash",
    ),
    # Meta-structures (classifier-fixed-point family).
    ClassifierRule(
        name="classifier_dimension_table_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="classifier_dimension_table",
    ),
    ClassifierRule(
        name="mortality_signal_threshold_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="mortality_signal_threshold",
    ),
    ClassifierRule(
        name="mortality_signal_update_rule_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="mortality_signal_update_rule",
    ),
    ClassifierRule(
        name="threshold_emergence_rule_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="threshold_emergence_rule",
    ),
    ClassifierRule(
        name="appetite_axis_schema_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="appetite_axis_schema",
    ),
    ClassifierRule(
        name="sporocarp_type_tree_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="sporocarp_type_tree",
    ),
    ClassifierRule(
        name="skin_surface_declaration_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="skin_surface_declaration",
    ),
    ClassifierRule(
        name="ssot_designation_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="ssot_designation",
    ),
    ClassifierRule(
        name="dag_retention_policy_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="dag_retention_policy",
    ),
    ClassifierRule(
        name="federation_peer_attestation_list_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="federation_peer_attestation_list",
    ),
    # Daily-content mutation types.
    ClassifierRule(
        name="daily_delta_absorb",
        classification=Classification.DAILY,
        mutation_type="delta_absorb",
    ),
    ClassifierRule(
        name="daily_gradient_update_non_mortality",
        classification=Classification.DAILY,
        mutation_type="gradient_update_non_mortality",
    ),
    ClassifierRule(
        name="daily_sporocarp_fruit",
        classification=Classification.DAILY,
        mutation_type="sporocarp_fruit",
    ),
    ClassifierRule(
        name="daily_federation_coupling",
        classification=Classification.DAILY,
        mutation_type="federation_coupling",
    ),
    # Mortality-axis gradient update is CI per §1.2.
    ClassifierRule(
        name="mortality_signal_gradient_update",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="gradient_update_mortality",
    ),
)


@dataclass(frozen=True, slots=True)
class ClassifierContext:
    """Substrate-state context that affects classification (per §1.3 birth-period).

    Per L1_GOVERNANCE §1.3: during birth period, ALL parameter-tuning events
    are CI regardless of steady-state classification.
    """

    birth_period_active: bool = False


def classify(
    mutation: MutationEnvelope,
    dimension_table: tuple[ClassifierRule, ...] = SEED_DIMENSION_TABLE,
    context: ClassifierContext = ClassifierContext(),
) -> Classification:
    """Classify a mutation per L1_GOVERNANCE §1.1.

    Args:
        mutation: the mutation envelope.
        dimension_table: the active classifier dimension table (defaults to
            the L1_GOVERNANCE §1.2 seed table). Substrates that have extended
            the table via CI mutation pass their current table here.
        context: substrate-state context (e.g., birth-period flag).

    Returns:
        Classification — DAILY / CONTRACT_IDENTITY_LEVEL / UNTYPED.

    Decision logic:

    1. If any rule matches AND any matched rule is CI → CONTRACT_IDENTITY_LEVEL.
    2. Else if birth_period_active AND any rule matches AND any matched rule
       is DAILY → CONTRACT_IDENTITY_LEVEL (birth-period elevation per §1.3).
    3. Else if any rule matches AND all matched rules are DAILY → DAILY.
    4. Else (no rule matches) → UNTYPED.

    Note: the "any matched rule is CI" check honors L0 I2 classifier-fixed-
    point: if a mutation touches BOTH a CI-protected surface AND a daily
    surface (e.g., editing both substrate_id and a daily-content field), the
    CI grade dominates. The opposite (daily-down-grading) is forbidden.
    """
    matched = [r for r in dimension_table if r.matches(mutation)]
    if not matched:
        return Classification.UNTYPED

    # Strongest-classification-wins (CI > DAILY > UNTYPED).
    if any(r.classification is Classification.CONTRACT_IDENTITY_LEVEL for r in matched):
        return Classification.CONTRACT_IDENTITY_LEVEL

    # Birth-period elevation (§1.3).
    if context.birth_period_active and any(
        r.classification is Classification.DAILY for r in matched
    ):
        return Classification.CONTRACT_IDENTITY_LEVEL

    if any(r.classification is Classification.DAILY for r in matched):
        return Classification.DAILY

    return Classification.UNTYPED


def matched_rules(
    mutation: MutationEnvelope,
    dimension_table: tuple[ClassifierRule, ...] = SEED_DIMENSION_TABLE,
) -> list[ClassifierRule]:
    """Return the list of rules matching the mutation (for debugging / immune
    sporocarp construction)."""
    return [r for r in dimension_table if r.matches(mutation)]
