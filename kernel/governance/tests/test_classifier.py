"""Tests for the I2 classifier (L1/GOVERNANCE §1)."""

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
        touched_files=frozenset({"docs/architecture/L0/META.md"}),
        mutation_type="doc_edit",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_ci_l1_file() -> None:
    env = MutationEnvelope(
        touched_files=frozenset({"docs/architecture/L1/GOVERNANCE.md"}),
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
# Sanity: seed table size matches L1/GOVERNANCE §1.2.
# ---------------------------------------------------------------------------


def test_seed_table_size() -> None:
    """L1/GOVERNANCE §1.2 lists 18 rows; allow for some L4-level expansion.

    This test pins the current seed-table size so future edits are
    intentional (any add/remove of a seed rule will require updating this
    test, which serves as a tripwire).
    """
    # 2 file-prefix + 4 identity-fields + 10 meta-structures + 4 daily +
    # 1 mortality-detail + 1 schema_evolution (M17) +
    # 3 M26.3 compression rules (compression_mutation + compression_rule_registry_meta + compression_invariant_set_meta) +
    # 4 M26.4 rules (cost_budget_set_mutation + cost_budget_thresholds_meta + owner_objective_declaration_mutation + telos_alignment_metric_meta) +
    # 2 M-anchor-5 rules (dag_tip_cosign_mutation + l0_revision_attest_mutation) +
    # 1 v3.1.1 Sprint 2.C rule (set_backup_encryption_status) +
    # 1 v3.1.1 Sprint 8.G rule (abort_migration_mutation, P03 §10.4 two-phase migration) +
    # 4 COV06 rules (update_successor_chain + accept_succession +
    #   record_cultivator_heartbeat + cultivation_successor_chain_meta;
    #   cultivator-mortality + F21 succession FSM, L1/GOVERNANCE §3.2).
    assert len(SEED_DIMENSION_TABLE) == 37


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


# ---------------------------------------------------------------------------
# v3.1.1 C56 cultivator_preserve_all_attempted — forbidden mutation types
# ---------------------------------------------------------------------------


def test_v3_1_1_C56_canonical_forbidden_patterns_detected() -> None:
    """Per L0/cards/COV04 §3.7 + §5.6: each canonical preserve-all instruction
    type must be flagged as a covenant violation."""
    from myco_kernel_governance.classifier import (
        is_cultivator_preserve_all_attempt,
    )

    for forbidden_type in [
        "preserve_all_axes",
        "preserve_all_parts",
        "disable_prune_scan",
        "disable_internal_mortality",
        "exempt_from_mortality",
        "never_prune",
        "never_prune_family",
        "preserve_everything",
    ]:
        assert is_cultivator_preserve_all_attempt(forbidden_type), (
            f"C56 must flag {forbidden_type!r}; missing from "
            f"FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES is a doctrine regression"
        )


def test_v3_1_1_C56_innocent_mutations_not_flagged() -> None:
    """No false positives: legitimate mutation types must pass the C56 check."""
    from myco_kernel_governance.classifier import (
        is_cultivator_preserve_all_attempt,
    )

    for legitimate_type in [
        "perturb_axis",
        "schema_evolution",
        "compression",
        "owner_objective_declaration",
        "cost_budget_set",
        "dag_tip_cosign",
        "l0_revision_attest",
        "key_rotation",
        "",
        "preserve",  # substring match should NOT trigger
        "all",
    ]:
        assert not is_cultivator_preserve_all_attempt(legitimate_type), (
            f"C56 must NOT flag {legitimate_type!r}; false positive"
        )


def test_v3_1_1_sprint_2c_set_backup_encryption_status_classified_as_CI() -> None:
    """Per L1/SKIN §8 + L1/HARD_RULES §1.4 anticipated: cultivator-attested
    backup encryption status declarations are CI-grade mutations (require
    owner attestation envelope)."""
    env = MutationEnvelope(mutation_type="set_backup_encryption_status")
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_v3_1_1_sprint_2c_backup_encryption_status_valid_values() -> None:
    """Per L1/SKIN §8: substrate accepts exactly two declared status values.
    Anything else is rejected at the skin (C5_attestation_invalid).
    """
    from myco_kernel_governance.classifier import (
        BACKUP_ENCRYPTION_STATUS_VALID_VALUES,
        is_valid_backup_encryption_status,
    )

    # Canonical valid values.
    assert is_valid_backup_encryption_status("encrypted_externally")
    assert is_valid_backup_encryption_status("cultivator_declined_explicit")

    # Anything else rejected. Includes "unspecified" — that is the DEFAULT
    # (no DAG event present) but is NEVER a value the cultivator may declare;
    # `None` in code, never a written string.
    assert not is_valid_backup_encryption_status("unspecified")
    assert not is_valid_backup_encryption_status("ENCRYPTED_EXTERNALLY")  # case-sensitive
    assert not is_valid_backup_encryption_status("")
    assert not is_valid_backup_encryption_status("encrypted")  # partial match
    assert not is_valid_backup_encryption_status("not_encrypted")

    # Set must be non-empty + frozen + small.
    assert len(BACKUP_ENCRYPTION_STATUS_VALID_VALUES) == 2


def test_v3_1_1_sprint_2c_backup_encryption_statuses_in_sync_with_rust() -> None:
    """Python BACKUP_ENCRYPTION_STATUS_VALID_VALUES MUST be byte-equal to the
    Rust ``substrate/src/events.rs::BACKUP_ENCRYPTION_STATUS_VALID_VALUES``
    array. Both sites validate cultivator-declared status strings; drift
    would let one side accept a value the other rejects (split-brain).
    """
    from pathlib import Path

    from myco_kernel_governance.classifier import (
        BACKUP_ENCRYPTION_STATUS_VALID_VALUES,
    )

    workspace_root = Path(__file__).resolve().parents[3]
    rust_src_dir = workspace_root / "substrate" / "src"
    assert rust_src_dir.is_dir(), f"Rust substrate/src not found at {rust_src_dir}"
    # Concatenate every substrate/src/**/*.rs so this check stays correct no
    # matter which module the constants live in (events.rs was decomposed into
    # an events/ module tree; the backup-encryption SSoT moved to
    # events/backup_encryption.rs).
    rust_text = "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(rust_src_dir.rglob("*.rs"))
    )

    marker = "pub const BACKUP_ENCRYPTION_STATUS_VALID_VALUES: &[&str] = &["
    idx = rust_text.find(marker)
    assert idx != -1, "Rust BACKUP_ENCRYPTION_STATUS_VALID_VALUES not found"
    closing = rust_text.find("];", idx)
    assert closing != -1, "Rust constant not properly closed"
    block = rust_text[idx + len(marker) : closing]

    # The block references named constants (BACKUP_ENCRYPTION_STATUS_*),
    # so extract those identifiers and dereference each to its quoted-string
    # definition earlier in the file.
    import re

    name_refs = re.findall(r"BACKUP_ENCRYPTION_STATUS_[A-Z_]+", block)
    resolved: list[str] = []
    for name in name_refs:
        if name == "BACKUP_ENCRYPTION_STATUS_VALID_VALUES":
            continue  # self-reference is the array's own identifier
        # Find the const definition: `pub const NAME: &str = "value";`
        # Allow whitespace (possibly newline) between `=` and the opening
        # quote — long const names get formatted across multiple lines.
        def_pattern = re.compile(
            r"pub const " + re.escape(name) + r":\s*&str\s*=\s*\"([^\"]+)\"",
        )
        m = def_pattern.search(rust_text)
        assert m is not None, f"Rust constant {name} not found in substrate/src"
        resolved.append(m.group(1))

    rust_set = frozenset(resolved)
    assert rust_set == BACKUP_ENCRYPTION_STATUS_VALID_VALUES, (
        f"Rust and Python backup-encryption-status lists drift!\n"
        f"  Rust only: {rust_set - BACKUP_ENCRYPTION_STATUS_VALID_VALUES}\n"
        f"  Python only: {BACKUP_ENCRYPTION_STATUS_VALID_VALUES - rust_set}\n"
        f"Fix: edit both the Rust substrate (events/backup_encryption.rs) AND "
        f"kernel/governance/src/myco_kernel_governance/classifier.py to match."
    )


def test_v3_1_1_C56_forbidden_mutation_types_in_sync_with_rust_substrate() -> None:
    """The Python FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES list MUST be byte-equal
    to the Rust ``substrate/src/prune.rs::FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES``
    constant.

    Test reads the Rust source directly (as a string) and verifies every
    Python entry appears + the count matches. This catches drift between the
    two enforcement points (Rust skin-layer + Python classifier).
    """
    from pathlib import Path

    from myco_kernel_governance.classifier import (
        FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES,
    )

    # Locate the Rust source. From this test file:
    # kernel/governance/tests/test_classifier.py
    # parents[0]=tests, [1]=governance, [2]=kernel, [3]=workspace root.
    workspace_root = Path(__file__).resolve().parents[3]
    rust_src = workspace_root / "substrate" / "src" / "prune.rs"
    assert rust_src.exists(), f"Rust prune.rs not found at {rust_src}"
    rust_text = rust_src.read_text(encoding="utf-8")

    # Find the constant definition and extract its string literals.
    marker = "pub const FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES: &[&str] = &["
    idx = rust_text.find(marker)
    assert idx != -1, "Rust FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES not found"
    # Find the closing `];` after the marker.
    closing = rust_text.find("];", idx)
    assert closing != -1, "Rust constant not properly closed"
    block = rust_text[idx + len(marker) : closing]
    # Extract quoted string literals.
    import re

    rust_entries = re.findall(r'"([^"]+)"', block)
    rust_set = frozenset(rust_entries)

    assert rust_set == FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES, (
        f"Rust and Python forbidden-preserve-all lists drift!\n"
        f"  Rust only: {rust_set - FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES}\n"
        f"  Python only: {FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES - rust_set}\n"
        f"Fix: edit both substrate/src/prune.rs AND "
        f"kernel/governance/src/myco_kernel_governance/classifier.py to match."
    )


# ---------------------------------------------------------------------------
# COV06 不弃不孤 — cultivator-mortality + succession FSM classification.
#
# The F21 cultivation_successor_chain, succession activation, and cultivator
# liveness heartbeat are contract-identity-level (they govern WHO holds the
# cultivation relation). L1/GOVERNANCE §3.2.A: successor_chain mutation
# "requires §2 attestation; without → untyped (C14)" — so these mutation types
# must classify CI, never daily/untyped.
# ---------------------------------------------------------------------------


def test_cov06_update_successor_chain_is_ci() -> None:
    env = MutationEnvelope(mutation_type="update_successor_chain")
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_cov06_accept_succession_is_ci() -> None:
    env = MutationEnvelope(mutation_type="accept_succession")
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_cov06_record_cultivator_heartbeat_is_ci() -> None:
    env = MutationEnvelope(mutation_type="record_cultivator_heartbeat")
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_cov06_successor_chain_meta_structure_is_ci() -> None:
    env = MutationEnvelope(
        touched_meta_structures=frozenset({"cultivation_successor_chain"}),
        mutation_type="field_update",
    )
    assert classify(env) is Classification.CONTRACT_IDENTITY_LEVEL


def test_cov06_unattested_successor_chain_field_remains_untyped() -> None:
    # An unrecognized mutation_type that does NOT match any COV06 rule stays
    # untyped (C14) — the F21 §3.2.A "without attestation → untyped" guarantee.
    env = MutationEnvelope(mutation_type="successor_chain_unattested_poke")
    assert classify(env) is Classification.UNTYPED


def test_cov06_C69_forbidden_suppression_types_in_sync_with_rust_substrate() -> None:
    """The Python FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES list MUST be
    byte-equal to the Rust
    ``substrate/src/prune.rs::FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES``.

    C69 (cultivation_orphaned_suppression_attempted) is enforced at the Rust
    skin layer; this test pins the two enforcement points in sync (COV06 §5.5).
    """
    import re
    from pathlib import Path

    from myco_kernel_governance.classifier import (
        FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES,
        is_cultivation_orphaned_suppression_attempt,
    )

    # Behavioral sanity: a known suppression type fires; a benign type does not.
    assert is_cultivation_orphaned_suppression_attempt("suppress_cultivation_orphaned")
    assert not is_cultivation_orphaned_suppression_attempt("delta_absorb")

    workspace_root = Path(__file__).resolve().parents[3]
    rust_src = workspace_root / "substrate" / "src" / "prune.rs"
    assert rust_src.exists(), f"Rust prune.rs not found at {rust_src}"
    rust_text = rust_src.read_text(encoding="utf-8")

    marker = "pub const FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES: &[&str] = &["
    idx = rust_text.find(marker)
    assert idx != -1, "Rust FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES not found"
    closing = rust_text.find("];", idx)
    assert closing != -1, "Rust constant not properly closed"
    block = rust_text[idx + len(marker) : closing]
    rust_set = frozenset(re.findall(r'"([^"]+)"', block))

    assert rust_set == FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES, (
        f"Rust and Python C69 suppression lists drift!\n"
        f"  Rust only: {rust_set - FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES}\n"
        f"  Python only: {FORBIDDEN_CULTIVATION_ORPHANED_SUPPRESSION_TYPES - rust_set}\n"
        f"Fix: edit both substrate/src/prune.rs AND "
        f"kernel/governance/src/myco_kernel_governance/classifier.py to match."
    )
