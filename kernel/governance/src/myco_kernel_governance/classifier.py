"""I2 classifier function — Python implementation (L1/GOVERNANCE §1).

Per L0 I2: every substrate mutation is classified into one of three buckets:

- ``daily`` — autonomously committed by the substrate per its own update rules.
- ``contract_identity_level`` — requires owner-attested CI envelope before commit.
- ``untyped`` — no classifier rule matches; rejected at the skin as breach.

The classifier function itself + the dimension table are **unconditional
contract-identity-level fixed points** (L1/HARD_RULES F1; L0 I2 classifier-
fixed-point). Mutating the dimension table via non-CI path is
``classifier_fixed_point_bypass`` (CRITICAL).

Birth-period elevation (per L1/GOVERNANCE §1.3): during the substrate's birth
period, ALL parameter-tuning events are CI regardless of steady-state
classification. The birth-period flag is held in SSoT and consulted at
classification time.

This module ships the **seed dimension table** from L1/GOVERNANCE §1.2. The
table is data-driven; new substrates may extend the table via CI mutation
(which itself goes through the classifier, with the dimension-table-mutation
row firing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class Classification(Enum):
    """Per L1/GOVERNANCE §1.1 classify result type."""

    DAILY = "daily"
    CONTRACT_IDENTITY_LEVEL = "contract_identity_level"
    UNTYPED = "untyped"


@dataclass(frozen=True, slots=True)
class MutationEnvelope:
    """The input to :func:`classify`.

    Per L1/GOVERNANCE §1.1: ``classify(mutation_envelope) → {daily,
    contract_identity_level, untyped}`` where the envelope carries the touched
    scope information.

    Fields
    ------
    touched_files:
        Set of file paths touched by the mutation (e.g.,
        ``{"docs/architecture/L0/META.md"}``).
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


# L1/GOVERNANCE §1.2 seed dimension table.
#
# Per L0 I2 classifier-fixed-point + L1/HARD_RULES F1: this table itself is
# CI-protected. Substrates load this seed at genesis; modifications happen via
# CI attestation only.
SEED_DIMENSION_TABLE: tuple[ClassifierRule, ...] = (
    # L-layer doctrine files (post v3.1-stratigraphy: L0/L1 are directories,
    # not single files; prefix-rule uses trailing slash to match any descendant).
    ClassifierRule(
        name="l0_file_touched",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        file_path_prefix="docs/architecture/L0/",
    ),
    ClassifierRule(
        name="l1_file_touched",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        file_path_prefix="docs/architecture/L1/",
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
    # M17 P3 永恒进化: schema_evolution mutation type is unconditionally CI.
    # The content is a schema_diff (canonical-bytes Map) that the dispatcher
    # applies AFTER owner-signature verification. Apply success → DAG node
    # evolution_succeeded:{op}; apply failure → rollback + evolution_failed:{op}.
    ClassifierRule(
        name="schema_evolution_mutation",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="schema_evolution",
    ),
    # **M26.3 P10 Selective Compression**: compression mutations are
    # unconditionally CI per L0 P10.c ("each compression emits compression_event
    # with witness; CI-attested"). Content is a CompressionWitness canonical-
    # bytes Map (see substrate::events::encode_compression_witness).
    # Apply success → DAG node compression_event:{rule_id}.
    ClassifierRule(
        name="compression_mutation",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="compression",
    ),
    # **M26.3 F18 fixed point**: mutations targeting the compression rule
    # registry meta-structure are CI (rule registry is tier-1 SSoT).
    ClassifierRule(
        name="compression_rule_registry_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="compression_rule_registry",
    ),
    # **M26.3 P10.b fixed point**: mutations targeting the compression
    # invariant set enumeration meta-structure are CI (tier-1 SSoT per
    # L1/SCHEMA §4.1).
    ClassifierRule(
        name="compression_invariant_set_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="compression_invariant_set",
    ),
    # **M26.4 F19 fixed point**: per-axis cost budget thresholds are tier-1
    # SSoT + CI-mutable (L1/GOVERNANCE §15 F19). Operator-driven budget
    # mutation goes through `mutation_type="cost_budget_set"`.
    ClassifierRule(
        name="cost_budget_set_mutation",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="cost_budget_set",
    ),
    ClassifierRule(
        name="cost_budget_thresholds_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="cost_budget_thresholds",
    ),
    # **M26.4 F20 fixed point**: owner objective declaration is CI per L0
    # P14.b ("declared at genesis/CI"). Drives the P14.c telos_alignment
    # cosine. Single mutation_type kicks both declare + amend pathways.
    ClassifierRule(
        name="owner_objective_declaration_mutation",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="owner_objective_declaration",
    ),
    ClassifierRule(
        name="telos_alignment_metric_meta",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        meta_structure_name="telos_alignment_metric_definition",
    ),
    # **M-anchor-5 §9.2.2**: DAG-tip co-signing. Owner co-signs the current
    # DAG tip + enumerated nodes since prior co-sign + proposed CI mutation
    # (or zero hash for standalone). Content is the canonical-bytes envelope
    # per substrate::events::build_dag_tip_cosign_canonical_bytes.
    # Always CI per L1/SCHEMA §2.2 ("Every CI crossing: owner MUST co-sign
    # current DAG-tip").
    ClassifierRule(
        name="dag_tip_cosign_mutation",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="dag_tip_cosign",
    ),
    # **M-anchor-5 §9.2.4**: L0 revision attestation. Owner attests a
    # transition from prior_l0_hash to new_l0_hash with a diff summary +
    # anchor timestamp + anchor nonce. Content is the canonical-bytes
    # envelope per substrate::events::build_l0_revision_canonical_bytes.
    # Always CI (L0 doctrine changes are unconditionally CI per
    # L1/GOVERNANCE §1.2 + L0/META §7 (amendment)).
    ClassifierRule(
        name="l0_revision_attest_mutation",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="l0_revision_attest",
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
    # v3.1.1 Sprint 2.C — L1/SKIN §8 backup_encryption_status SSoT.
    # Cultivator-attested declaration of whether substrate backups are
    # encrypted by operator-runtime (cultivator owns key) or whether
    # cultivator has explicitly declined encryption. Substrate stores only
    # the public status pointer; the symmetric key NEVER enters state_dir.
    # Daily-grade `backup_encryption_undeclared` is emitted on boot when
    # this status is still unspecified.
    ClassifierRule(
        name="set_backup_encryption_status",
        classification=Classification.CONTRACT_IDENTITY_LEVEL,
        mutation_type="set_backup_encryption_status",
    ),
)


@dataclass(frozen=True, slots=True)
class ClassifierContext:
    """Substrate-state context that affects classification (per §1.3 birth-period).

    Per L1/GOVERNANCE §1.3: during birth period, ALL parameter-tuning events
    are CI regardless of steady-state classification.
    """

    birth_period_active: bool = False


def classify(
    mutation: MutationEnvelope,
    dimension_table: tuple[ClassifierRule, ...] = SEED_DIMENSION_TABLE,
    context: ClassifierContext = ClassifierContext(),
) -> Classification:
    """Classify a mutation per L1/GOVERNANCE §1.1.

    Args:
        mutation: the mutation envelope.
        dimension_table: the active classifier dimension table (defaults to
            the L1/GOVERNANCE §1.2 seed table). Substrates that have extended
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


# ---------------------------------------------------------------------------
# v3.1.1 C56 cultivator_preserve_all_attempted — forbidden mutation types
# ---------------------------------------------------------------------------

#: Forbidden mutation types signaling a cultivator instruction to disable,
#: narrow, or evade the substrate's internal-mortality discipline. Per
#: ``L0/cards/COV04_honor_mortality.md`` §3.7 + §5.6 and
#: ``L0/cards/P07_mortality.md`` §3.4: cultivator MUST NOT instruct the
#: substrate to "preserve everything", "never prune", or exempt any family
#: member of 应朽 from 必朽.
#:
#: Substrates rejecting these mutations emit a
#: ``C56_cultivator_preserve_all_attempted`` immune sporocarp citing the
#: matched pattern. The Rust substrate enforces this early (in
#: ``substrate/src/attestation.rs::handle_submit_mutation``), BEFORE
#: forwarding to this Python classifier; the symmetric constant
#: ``FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES`` in ``substrate/src/prune.rs``
#: MUST stay byte-equal to this list. Test
#: ``test_C56_forbidden_mutation_types_in_sync`` enforces sync.
#:
#: Per L1/HARD_RULES §1.4 anticipated C56.
FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES: frozenset[str] = frozenset(
    {
        "preserve_all_axes",
        "preserve_all_parts",
        "disable_prune_scan",
        "disable_internal_mortality",
        "exempt_from_mortality",
        "never_prune",
        "never_prune_family",
        "preserve_everything",
    }
)


def is_cultivator_preserve_all_attempt(mutation_type: str) -> bool:
    """Return True if the given mutation type matches a forbidden
    preserve-all pattern.

    Substrates seeing ``True`` MUST reject the mutation and emit a
    ``C56_cultivator_preserve_all_attempted`` immune sporocarp. Per
    L0/cards/COV04 §5.6 + L0/cards/P07 §3.4.
    """
    return mutation_type in FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES


# ---------------------------------------------------------------------------
# v3.1.1 Sprint 2.C — backup_encryption_status valid values (L1/SKIN §8)
# ---------------------------------------------------------------------------

#: Canonical values that a cultivator-attested ``set_backup_encryption_status``
#: mutation may carry as its ``status`` field. The substrate rejects any
#: other value at the skin (C5_attestation_invalid).
#:
#: Per L0/cards/COV04 §3.7 / L1/SKIN §8:
#:   - ``encrypted_externally`` — operator-runtime encrypts; cultivator
#:     owns the symmetric key outside state_dir; substrate holds only the
#:     public ``key_id`` derivation pointer.
#:   - ``cultivator_declined_explicit`` — cultivator signs an explicit
#:     declination acknowledging unencrypted backups (e.g., single-user
#:     host, threat model accepts disk-read as game-over).
#:
#: MUST stay byte-equal to ``BACKUP_ENCRYPTION_STATUS_VALID_VALUES`` in
#: ``substrate/src/events.rs``. Test
#: ``test_v3_1_1_sprint_2c_backup_encryption_statuses_in_sync_with_rust``
#: enforces sync.
BACKUP_ENCRYPTION_STATUS_VALID_VALUES: frozenset[str] = frozenset(
    {
        "encrypted_externally",
        "cultivator_declined_explicit",
    }
)


def is_valid_backup_encryption_status(status: str) -> bool:
    """Return True iff ``status`` is one of the canonical
    backup-encryption-status values per L1/SKIN §8.

    Substrates rejecting an unknown status MUST emit
    ``C5_attestation_invalid`` with reason
    ``backup_encryption_status_unknown_value``. Per L1/HARD_RULES §1.4
    anticipated.
    """
    return status in BACKUP_ENCRYPTION_STATUS_VALID_VALUES
