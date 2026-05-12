"""Tests for the v0.8.0 schema v3 → v4 upgrader.

Governing craft:
``docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md`` (L0
amendment opening v0.8.0 MAJOR) and the v0.8.0 omnibus craft
authorising the schema bump as item E.

L1 doctrine:
``docs/architecture/L1_CONTRACT/canon_schema.md`` § ``system.governance``
block (extended at v0.8.0 to cover ``last_living_bets_audit_at`` and
``persistence_metrics``).

The two semantics of v4 are additive optional fields under
``system.governance``:

1. ``last_living_bets_audit_at: str | null`` — ISO 8601 marker
   consumed by LB1 to skip its filesystem-O(N) walk.
2. ``persistence_metrics: dict`` — three nullable sub-fields
   (``session_count`` / ``host_count`` / ``peer_count``) consumed by
   LB2 as a regime-classifier cache.

Per the v0.6.0 narrowness principle (one partial = one semantic), the
two changes are split into independent partials. These tests pin:

1. Each partial in isolation (per-semantic).
2. The composer's stamp + idempotence.
3. Smoke through the full chain (v1 → v2 → v3 → v4 in one
   ``_apply_upgraders`` call).
4. Backward-compat regression: a fresh v4 canon parses without going
   through any upgrader.

The downstream ``test_canon.py`` and ``test_canon_v2.py`` end-to-end
tests already exercise ``load_canon``-level chain semantics; this file
targets the partial layer specifically.
"""

from __future__ import annotations

import textwrap
import warnings
from pathlib import Path

from myco.core.canon import (
    KNOWN_SCHEMA_VERSIONS,
    _apply_upgraders,
    _v3_to_v4,
    _v3_to_v4_living_bets_audit_marker_field,
    _v3_to_v4_persistence_metrics_field,
    load_canon,
    schema_upgraders,
)

# ---------------------------------------------------------------------------
# Phase F — registration smoke
# ---------------------------------------------------------------------------


def test_v3_to_v4_upgrader_is_registered() -> None:
    """v0.8.0 registers ``schema_upgraders["3"] = _v3_to_v4`` at module
    import time so v3 substrates lift transparently on first hunger."""
    assert "3" in schema_upgraders
    assert schema_upgraders["3"] is _v3_to_v4
    assert callable(schema_upgraders["3"])


def test_known_schema_versions_includes_v4() -> None:
    """KNOWN_SCHEMA_VERSIONS retains "1", "2", and "3" for cold-read
    backward compatibility (their absence-of-upgrader is what stops
    the chain when no v4 upgrader is registered) and adds "4" so a
    substrate that has been on-disk-flipped to v4 also reads without
    warning."""
    assert "1" in KNOWN_SCHEMA_VERSIONS
    assert "2" in KNOWN_SCHEMA_VERSIONS
    assert "3" in KNOWN_SCHEMA_VERSIONS
    assert "4" in KNOWN_SCHEMA_VERSIONS


# ---------------------------------------------------------------------------
# Per-partial behaviour: _v3_to_v4_living_bets_audit_marker_field
# ---------------------------------------------------------------------------


def test_partial_1_inserts_audit_marker_field_when_absent() -> None:
    """A v3 canon with a ``system.governance`` block but no
    ``last_living_bets_audit_at`` field gains the field, defaulted to
    ``None``. Other governance keys are preserved untouched."""
    raw = {
        "schema_version": "3",
        "system": {
            "llm_policy": "forbidden",
            "governance": {
                "auto_propose_enabled": False,
                "public_window_min_senesce_count": 7,
            },
        },
    }

    out = _v3_to_v4_living_bets_audit_marker_field(raw)
    g = out["system"]["governance"]
    assert g["last_living_bets_audit_at"] is None
    # Pre-existing keys preserved.
    assert g["auto_propose_enabled"] is False
    assert g["public_window_min_senesce_count"] == 7
    # Partial does NOT stamp schema_version — that's the wrapper's job.
    assert out["schema_version"] == "3"
    # Partial does NOT touch persistence_metrics — that's its sibling.
    assert "persistence_metrics" not in g
    # Original raw dict is not mutated (defensive copy at entry).
    assert "last_living_bets_audit_at" not in raw["system"]["governance"]


def test_partial_1_preserves_existing_audit_marker_value() -> None:
    """If ``system.governance.last_living_bets_audit_at`` is already
    set (operator hand-edited or fresh ``myco molt`` stamped), the
    upgrader does NOT overwrite it. Guards against silent data loss
    when re-running the upgrader against a partially-migrated canon."""
    raw = {
        "schema_version": "3",
        "system": {
            "governance": {
                "last_living_bets_audit_at": "2026-05-10T14:52:12Z",
                "auto_propose_enabled": True,
            },
        },
    }

    out = _v3_to_v4_living_bets_audit_marker_field(raw)
    g = out["system"]["governance"]
    assert g["last_living_bets_audit_at"] == "2026-05-10T14:52:12Z"
    assert g["auto_propose_enabled"] is True


def test_partial_1_inserts_governance_block_if_missing() -> None:
    """A v3 canon with ``system`` present but no ``governance`` block
    (e.g. a minimal substrate that pre-dates the v0.6.0 governance
    additions) gains a fresh governance dict carrying the new field.
    Other system keys are preserved untouched."""
    raw = {
        "schema_version": "3",
        "system": {
            "llm_policy": "forbidden",
            "write_surface": {"allowed": ["_canon.yaml"]},
        },
    }

    out = _v3_to_v4_living_bets_audit_marker_field(raw)
    assert out["system"]["governance"] == {"last_living_bets_audit_at": None}
    # Other system keys preserved.
    assert out["system"]["llm_policy"] == "forbidden"
    assert out["system"]["write_surface"] == {"allowed": ["_canon.yaml"]}


# ---------------------------------------------------------------------------
# Per-partial behaviour: _v3_to_v4_persistence_metrics_field
# ---------------------------------------------------------------------------


def test_partial_2_inserts_persistence_metrics_block_when_absent() -> None:
    """A v3 canon with ``system.governance`` but no
    ``persistence_metrics`` block gains a fresh dict with all three
    sub-keys defaulted to ``None``. Other governance keys are
    preserved."""
    raw = {
        "schema_version": "3",
        "system": {
            "governance": {
                "auto_evolve_critic_count": 5,
            },
        },
    }

    out = _v3_to_v4_persistence_metrics_field(raw)
    g = out["system"]["governance"]
    assert g["persistence_metrics"] == {
        "session_count": None,
        "host_count": None,
        "peer_count": None,
    }
    # Pre-existing key preserved.
    assert g["auto_evolve_critic_count"] == 5
    # Partial does NOT touch the audit-marker field — that's its sibling.
    assert "last_living_bets_audit_at" not in g


def test_partial_2_preserves_existing_persistence_metrics() -> None:
    """If ``system.governance.persistence_metrics`` is already fully
    populated, the upgrader does NOT overwrite any sub-key value."""
    raw = {
        "schema_version": "3",
        "system": {
            "governance": {
                "persistence_metrics": {
                    "session_count": 42,
                    "host_count": 3,
                    "peer_count": 0,
                },
            },
        },
    }

    out = _v3_to_v4_persistence_metrics_field(raw)
    pm = out["system"]["governance"]["persistence_metrics"]
    assert pm == {"session_count": 42, "host_count": 3, "peer_count": 0}


def test_partial_2_handles_partial_existing_metrics() -> None:
    """If ``persistence_metrics`` has SOME sub-keys (e.g. session_count
    observed but host_count not yet measured), the partial fills in the
    missing keys with None and preserves the observed values. This is
    the canonical "partial-existing-metrics" semantic — a half-populated
    cache must not be clobbered."""
    raw = {
        "schema_version": "3",
        "system": {
            "governance": {
                "persistence_metrics": {
                    "session_count": 17,
                    # host_count and peer_count missing — should be filled with None
                },
            },
        },
    }

    out = _v3_to_v4_persistence_metrics_field(raw)
    pm = out["system"]["governance"]["persistence_metrics"]
    assert pm["session_count"] == 17  # observed value preserved
    assert pm["host_count"] is None  # missing key filled
    assert pm["peer_count"] is None  # missing key filled


def test_partial_2_replaces_malformed_persistence_metrics() -> None:
    """Defensive: a non-dict ``persistence_metrics`` value (e.g. a
    string from a typo) is replaced with a fresh shape carrying all
    three ``None`` sub-keys. ``load_canon``'s downstream readers
    would have failed on the original malformed shape; the upgrader
    does not propagate the malformation."""
    raw = {
        "schema_version": "3",
        "system": {
            "governance": {
                "persistence_metrics": "broken-string",
            },
        },
    }

    out = _v3_to_v4_persistence_metrics_field(raw)
    assert out["system"]["governance"]["persistence_metrics"] == {
        "session_count": None,
        "host_count": None,
        "peer_count": None,
    }


# ---------------------------------------------------------------------------
# Composer behaviour
# ---------------------------------------------------------------------------


def test_composer_stamps_v4() -> None:
    """The ``_v3_to_v4`` composer chains both partials and stamps
    ``schema_version`` to "4". A minimal v3 raw (with ``system`` but
    no ``governance``) lifts cleanly: the audit marker field lands at
    None, the persistence_metrics block is seeded with all None
    sub-keys, and the version stamp arrives last."""
    raw = {
        "schema_version": "3",
        "contract_version": "v0.7.10",
        "system": {"llm_policy": "forbidden"},
    }

    out = _v3_to_v4(raw)

    assert out["schema_version"] == "4"
    g = out["system"]["governance"]
    assert g["last_living_bets_audit_at"] is None
    assert g["persistence_metrics"] == {
        "session_count": None,
        "host_count": None,
        "peer_count": None,
    }
    # Unrelated top-level keys preserved.
    assert out["contract_version"] == "v0.7.10"


def test_composer_is_idempotent() -> None:
    """Calling the composer twice yields the same shape as calling it
    once. This is the canonical safety property: a substrate that
    accidentally re-runs the upgrader (e.g. a half-completed molt
    interrupted by a kill signal) does not corrupt the governance
    block.

    Both partial-level and composer-level idempotence are pinned: the
    partials must individually be idempotent for the composer's
    composition to inherit the property."""
    raw = {
        "schema_version": "3",
        "system": {
            "governance": {
                "auto_propose_enabled": False,
                "persistence_metrics": {"session_count": 5},
            },
        },
    }

    # Partial-level idempotence.
    p1_once = _v3_to_v4_living_bets_audit_marker_field(raw)
    p1_twice = _v3_to_v4_living_bets_audit_marker_field(p1_once)
    assert p1_once == p1_twice

    p2_once = _v3_to_v4_persistence_metrics_field(raw)
    p2_twice = _v3_to_v4_persistence_metrics_field(p2_once)
    assert p2_once == p2_twice

    # Composer-level idempotence.
    wrap_once = _v3_to_v4(raw)
    wrap_twice = _v3_to_v4(wrap_once)
    assert wrap_once == wrap_twice
    assert wrap_twice["schema_version"] == "4"
    # The half-populated cache (session_count=5) is preserved across
    # both passes.
    assert (
        wrap_twice["system"]["governance"]["persistence_metrics"]["session_count"] == 5
    )
    assert (
        wrap_twice["system"]["governance"]["persistence_metrics"]["host_count"] is None
    )


# ---------------------------------------------------------------------------
# Smoke — full chain
# ---------------------------------------------------------------------------


def test_v4_smoke_through_full_chain() -> None:
    """A schema_version: "1" canon lifts all the way through to "4"
    via the full upgrader chain in a single ``_apply_upgraders`` call.
    This is the v0.8.0 promise: the chain machinery walks to the latest
    registered version naturally, not just one hop, across N=4
    chained versions for the first time.

    Verifies:
    - ``schema_version`` lands at "4".
    - ``system.llm_policy`` was rewritten by the v1→v2 partial.
    - ``identity.federation_peers`` was added by the v1→v2 partial.
    - ``lint.dimensions_ref`` pointer was added by the v1→v2 partial.
    - ``metrics.lint_dim_count`` was seeded by the v2→v3 partial.
    - ``system.governance.last_living_bets_audit_at`` was seeded by
      the v3→v4 partial 1.
    - ``system.governance.persistence_metrics`` was seeded by the
      v3→v4 partial 2.
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
    # v3 → v4 partials' work present.
    g = out["system"]["governance"]
    assert g["last_living_bets_audit_at"] is None
    assert g["persistence_metrics"] == {
        "session_count": None,
        "host_count": None,
        "peer_count": None,
    }


def test_v4_canon_on_disk_parses_without_chain(tmp_path: Path) -> None:
    """A canon authored fresh at ``schema_version: "4"`` (post-flip
    state) parses without warning and without going through any
    upgrader. The v4 partials' idempotence guarantees that even if a
    v4 canon is somehow piped through the upgrader, populated values
    (e.g. an audit timestamp + a partial cache) are preserved."""
    canon_text = textwrap.dedent(
        """\
        schema_version: "4"
        contract_version: "v0.8.0"
        identity:
          substrate_id: "v4-fresh"
          entry_point: "MYCO.md"
        system:
          write_surface:
            allowed: ["_canon.yaml"]
          llm_policy: "forbidden"
          hard_contract: {rule_count: 7}
          governance:
            last_living_bets_audit_at: "2026-05-10T14:52:12Z"
            persistence_metrics:
              session_count: 42
              host_count: 3
              peer_count: 0
        subsystems:
          germination:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        metrics:
          test_count: 1711
          lint_dim_count: 51
        """
    )
    p = tmp_path / "_canon.yaml"
    p.write_text(canon_text, encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any UserWarning would raise
        canon = load_canon(p)

    assert canon.schema_version == "4"
    g = canon.system.get("governance") or {}
    assert g.get("last_living_bets_audit_at") == "2026-05-10T14:52:12Z"
    assert g.get("persistence_metrics") == {
        "session_count": 42,
        "host_count": 3,
        "peer_count": 0,
    }


# ---------------------------------------------------------------------------
# Backward compatibility: v3 canon still parses cleanly
# ---------------------------------------------------------------------------


def test_v3_canon_on_disk_lifts_to_v4_silently(tmp_path: Path) -> None:
    """A v3 canon (the on-disk shape pre-v0.8.0 molt) still parses
    silently and surfaces as v4 in-memory with the two new governance
    fields seeded. The disk shape is unchanged — ``_canon.yaml`` on
    the operator's filesystem stays at "3" until they run the v0.8.0
    molt."""
    canon_text = textwrap.dedent(
        """\
        schema_version: "3"
        contract_version: "v0.7.10"
        identity:
          substrate_id: "v3-on-disk"
          entry_point: "MYCO.md"
          federation_peers: []
        system:
          write_surface:
            allowed: ["_canon.yaml"]
          llm_policy: "forbidden"
          hard_contract: {rule_count: 7}
          governance:
            auto_propose_enabled: false
            public_window_min_senesce_count: 7
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
    g = canon.system.get("governance") or {}
    # New v4 fields seeded.
    assert g.get("last_living_bets_audit_at") is None
    assert g.get("persistence_metrics") == {
        "session_count": None,
        "host_count": None,
        "peer_count": None,
    }
    # Pre-existing v3 governance keys preserved.
    assert g.get("auto_propose_enabled") is False
    assert g.get("public_window_min_senesce_count") == 7
