"""Tests for the v0.7.5 schema v2 → v3 upgrader.

Governing craft:
``docs/primordia/v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md`` § P2
("First real schema migration since v0.6.0").

L1 doctrine:
``docs/architecture/L1_CONTRACT/canon_schema.md`` § "v0.6.0+ schema v2
additions" (extended at v0.7.5 to cover ``metrics.lint_dim_count``).

The single semantic of v3 is the additive optional field
``metrics.lint_dim_count: int | null``. The upgrader is intentionally
narrow per the v0.6.0 narrowness principle (one partial = one
semantic). These tests pin:

1. The named partial in isolation (per-semantic).
2. Idempotence (calling twice == calling once).
3. Smoke through the full chain (v1 → v2 → v3 in one ``load_canon``).

The downstream ``test_canon.py`` and ``test_canon_v2.py`` end-to-end
tests already exercise ``load_canon``-level chain semantics; this
file targets the partial layer specifically.
"""

from __future__ import annotations

import textwrap
import warnings
from pathlib import Path

from myco.core.canon import (
    KNOWN_SCHEMA_VERSIONS,
    _apply_upgraders,
    _v2_to_v3,
    _v2_to_v3_lint_dim_count_field,
    load_canon,
    schema_upgraders,
)

# ---------------------------------------------------------------------------
# Phase F — registration smoke
# ---------------------------------------------------------------------------


def test_v2_to_v3_upgrader_is_registered() -> None:
    """v0.7.5 registers ``schema_upgraders["2"] = _v2_to_v3`` at module
    import time so v2 substrates lift transparently on first hunger."""
    assert "2" in schema_upgraders
    assert callable(schema_upgraders["2"])


def test_known_schema_versions_includes_v3() -> None:
    """KNOWN_SCHEMA_VERSIONS retains "1" and "2" for cold-read backward
    compatibility (their absence-of-upgrader is what stops the chain
    when no v3 upgrader is registered) and adds "3" so a substrate
    that has been on-disk-flipped to v3 also reads without warning."""
    assert "1" in KNOWN_SCHEMA_VERSIONS
    assert "2" in KNOWN_SCHEMA_VERSIONS
    assert "3" in KNOWN_SCHEMA_VERSIONS


# ---------------------------------------------------------------------------
# Per-partial behaviour: _v2_to_v3_lint_dim_count_field
# ---------------------------------------------------------------------------


def test_v2_canon_promotes_to_v3_with_null_lint_dim_count() -> None:
    """A v2 canon missing ``metrics`` entirely gains an empty mapping
    seeded with ``lint_dim_count: None``. The composed wrapper stamps
    ``schema_version`` to "3"."""
    raw = {
        "schema_version": "2",
        "contract_version": "v0.7.4",
        "identity": {"substrate_id": "x", "entry_point": "MYCO.md"},
        "system": {"llm_policy": "forbidden"},
        "subsystems": {"germination": {"doc": "x"}},
    }

    # Partial only.
    partial = _v2_to_v3_lint_dim_count_field(raw)
    assert partial["metrics"] == {"lint_dim_count": None}
    # Partial does NOT stamp schema_version — that's the wrapper's job.
    assert partial["schema_version"] == "2"
    # Unrelated keys preserved.
    assert partial["identity"] == {"substrate_id": "x", "entry_point": "MYCO.md"}
    assert partial["system"] == {"llm_policy": "forbidden"}

    # Wrapper composes + stamps.
    out = _v2_to_v3(raw)
    assert out["schema_version"] == "3"
    assert out["metrics"] == {"lint_dim_count": None}


def test_v2_canon_with_existing_metrics_retains_other_fields() -> None:
    """A v2 canon with pre-existing ``metrics.test_count`` keeps that
    field; ``lint_dim_count`` is added alongside without clobbering."""
    raw = {
        "schema_version": "2",
        "metrics": {
            "test_count": 1566,
            "repo_size_max_bytes": 52428800,
        },
    }

    out = _v2_to_v3_lint_dim_count_field(raw)
    assert out["metrics"]["test_count"] == 1566
    assert out["metrics"]["repo_size_max_bytes"] == 52428800
    assert out["metrics"]["lint_dim_count"] is None
    # Original raw dict is not mutated (defensive copy at entry).
    assert "lint_dim_count" not in raw["metrics"]


def test_v2_canon_with_explicit_lint_dim_count_preserved() -> None:
    """If ``metrics.lint_dim_count`` is already set (operator
    hand-edited or fresh germinate), the upgrader does NOT overwrite
    it. This guards against silent data loss when re-running the
    upgrader against a partially-migrated canon."""
    raw = {
        "schema_version": "2",
        "metrics": {"lint_dim_count": 50, "test_count": 1568},
    }

    out = _v2_to_v3_lint_dim_count_field(raw)
    assert out["metrics"]["lint_dim_count"] == 50
    assert out["metrics"]["test_count"] == 1568


def test_v2_canon_with_malformed_metrics_seeds_fresh_dict() -> None:
    """Defensive: a non-dict ``metrics`` value (e.g. a string from a
    typo) is replaced with a fresh ``{lint_dim_count: None}`` mapping.
    ``load_canon``'s downstream ``_mapping`` check would have raised
    on the original shape; the upgrader does not propagate the
    malformation."""
    raw = {
        "schema_version": "2",
        "metrics": "broken-string",
    }

    out = _v2_to_v3_lint_dim_count_field(raw)
    assert out["metrics"] == {"lint_dim_count": None}


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------


def test_upgrader_is_idempotent() -> None:
    """Calling the partial twice yields the same shape as calling it
    once. This is the canonical safety property: a substrate that
    accidentally re-runs the upgrader (e.g. a half-completed molt
    interrupted by a kill signal) does not corrupt the metrics
    block."""
    raw = {
        "schema_version": "2",
        "metrics": {"test_count": 1566},
    }

    once = _v2_to_v3_lint_dim_count_field(raw)
    twice = _v2_to_v3_lint_dim_count_field(once)
    assert once == twice

    # Wrapper-level idempotence too: applying _v2_to_v3 twice should
    # land on the same v3 shape (the schema_version stamp is the only
    # bit that "changes" but it's already "3" after the first pass).
    wrap_once = _v2_to_v3(raw)
    wrap_twice = _v2_to_v3(wrap_once)
    assert wrap_once == wrap_twice
    assert wrap_twice["schema_version"] == "3"


# ---------------------------------------------------------------------------
# Smoke — full chain
# ---------------------------------------------------------------------------


def test_v3_smoke_through_full_chain() -> None:
    """A schema_version: "1" canon lifts through the full upgrader
    chain in a single ``_apply_upgraders`` call. This is the v0.7.5
    P2 promise: the chain machinery walks to the latest registered
    version naturally, not just one hop.

    v0.8.0 update: the chain extends one more hop to "4" via the
    production v3→v4 upgrader, so end-state is now "4". The v2→v3
    partial's contribution (``metrics.lint_dim_count`` seeded to
    None) is still verified here as a chain-traversal property.

    Verifies:
    - ``schema_version`` lands at "4".
    - ``system.llm_policy`` was rewritten by the v1→v2 partial.
    - ``identity.federation_peers`` was added by the v1→v2 partial.
    - ``lint.dimensions_ref`` pointer was added by the v1→v2 partial.
    - ``metrics.lint_dim_count`` was seeded by the v2→v3 partial.
    """
    v1_raw = {
        "schema_version": "1",
        "contract_version": "v0.5.24",
        "identity": {
            "substrate_id": "chain-smoke",
            "entry_point": "MYCO.md",
        },
        "system": {
            "no_llm_in_substrate": True,
            "hard_contract": {"rule_count": 7},
        },
        "lint": {"dimensions": {"M1": "mechanical"}},
        "subsystems": {"germination": {"doc": "x"}},
    }

    out = _apply_upgraders("1", v1_raw)
    assert out["schema_version"] == "4"
    # v1 → v2 partials' work survives.
    assert out["system"]["llm_policy"] == "forbidden"
    assert "no_llm_in_substrate" not in out["system"]
    assert out["identity"]["federation_peers"] == []
    assert out["lint"]["dimensions_ref"] == "_canon_lint.yaml"
    # v2 → v3 partial's work present.
    assert out["metrics"]["lint_dim_count"] is None


def test_v3_smoke_through_load_canon(tmp_path: Path) -> None:
    """End-to-end: a v1 canon on disk parses through ``load_canon``
    without warning. The v2→v3 partial's contribution
    (``metrics.lint_dim_count`` populated to ``None``) is verified
    as part of the chain traversal. This pins the "you never migrate
    again" promise across the v0.7.5 boundary.

    v0.8.0 update: chain end-state shifts from "3" to "4" because the
    v3→v4 upgrader is now registered. The v2→v3 contribution is still
    checked here."""
    canon_text = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.24"
        identity:
          substrate_id: "v3-smoke"
          tags: ["test"]
          entry_point: "MYCO.md"
        system:
          write_surface:
            allowed: ["_canon.yaml", "MYCO.md"]
          hard_contract: {rule_count: 7}
          no_llm_in_substrate: true
        subsystems:
          germination:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        """
    )
    p = tmp_path / "_canon.yaml"
    p.write_text(canon_text, encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any UserWarning would raise
        canon = load_canon(p)

    assert canon.schema_version == "4"
    assert canon.substrate_id == "v3-smoke"
    assert canon.system["llm_policy"] == "forbidden"
    assert canon.identity["federation_peers"] == []
    assert canon.metrics["lint_dim_count"] is None


def test_v3_canon_on_disk_parses_without_chain(tmp_path: Path) -> None:
    """A canon authored at ``schema_version: "3"`` parses without
    warning. The v2→v3 partial's idempotence guarantees that the
    populated ``lint_dim_count`` value (50) is preserved.

    v0.8.0 update: the v3 canon now lifts to v4 in-memory via the
    registered v3→v4 upgrader. ``lint_dim_count`` is still preserved
    (the v3→v4 partials touch ``system.governance``, not
    ``metrics``); the chain end-state shifts to "4". A canon flipped
    on disk to "4" is exercised separately in
    ``test_canon_schema_upgrader_v3_to_v4.py``."""
    canon_text = textwrap.dedent(
        """\
        schema_version: "3"
        contract_version: "v0.7.5"
        identity:
          substrate_id: "v3-fresh"
          entry_point: "MYCO.md"
        system:
          write_surface:
            allowed: ["_canon.yaml"]
          llm_policy: "forbidden"
          hard_contract: {rule_count: 7}
        subsystems:
          germination:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        metrics:
          test_count: 1568
          lint_dim_count: 50
        """
    )
    p = tmp_path / "_canon.yaml"
    p.write_text(canon_text, encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        canon = load_canon(p)

    assert canon.schema_version == "4"
    assert canon.metrics["lint_dim_count"] == 50
    assert canon.metrics["test_count"] == 1568


# ---------------------------------------------------------------------------
# Backward compatibility: v2 canon still parses cleanly
# ---------------------------------------------------------------------------


def test_v2_canon_on_disk_lifts_to_v3_silently(tmp_path: Path) -> None:
    """A v2 canon (the on-disk shape pre-v0.7.5 molt) still parses
    silently and the v2→v3 partial's contribution
    (``lint_dim_count`` seeded to None) is verified. The disk shape
    is unchanged — ``_canon.yaml`` on the operator's filesystem stays
    at "2" until they run a contract-bumping molt.

    v0.8.0 update: chain end-state shifts from "3" to "4"; the v2→v3
    partial's contribution still lands as a chain-traversal property."""
    canon_text = textwrap.dedent(
        """\
        schema_version: "2"
        contract_version: "v0.7.4"
        identity:
          substrate_id: "v2-on-disk"
          entry_point: "MYCO.md"
          federation_peers: []
        system:
          write_surface:
            allowed: ["_canon.yaml"]
          llm_policy: "forbidden"
          hard_contract: {rule_count: 7}
        subsystems:
          germination:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        metrics:
          test_count: 1566
        """
    )
    p = tmp_path / "_canon.yaml"
    p.write_text(canon_text, encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        canon = load_canon(p)

    assert canon.schema_version == "4"
    assert canon.metrics["lint_dim_count"] is None
    assert canon.metrics["test_count"] == 1566
