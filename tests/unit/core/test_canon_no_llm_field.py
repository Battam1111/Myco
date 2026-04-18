"""Tests for ``canon.system.no_llm_in_substrate`` (v0.5.6 MP1 field).

The field is **optional-with-default-true**. A v0.5.5 substrate whose
canon predates v0.5.6 must round-trip cleanly through ``load_canon``
and its ``system.get('no_llm_in_substrate', True)`` lookup must
return ``True`` (the MP1 default).

An explicit ``true`` or ``false`` must round-trip to the same boolean
so MP1's severity-tiering logic can trust what it reads.

No change to ``_REQUIRED_TOP_LEVEL`` is expected — this field is
nested under ``system`` and read lazily by MP1, so an older kernel
reading a newer canon (or vice versa) still parses without error.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.canon import load_canon


def _write_canon(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "_canon.yaml"
    p.write_text(body, encoding="utf-8")
    return p


def test_canon_without_no_llm_field_defaults_to_true(tmp_path: Path) -> None:
    """A v0.5.5-style canon missing the field defaults to ``True``."""
    body = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.5"
        identity:
          substrate_id: "old-substrate"
          entry_point: "MYCO.md"
        system:
          hard_contract:
            rule_count: 7
        subsystems:
          homeostasis:
            doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
        """
    )
    c = load_canon(_write_canon(tmp_path, body))
    assert c.system.get("no_llm_in_substrate", True) is True
    # Explicit absence check: the field truly is not in the mapping.
    assert "no_llm_in_substrate" not in c.system


def test_canon_with_no_llm_true_parses(tmp_path: Path) -> None:
    """Explicit ``true`` round-trips."""
    body = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.6"
        identity:
          substrate_id: "mycelium-pure"
          entry_point: "MYCO.md"
        system:
          hard_contract:
            rule_count: 7
          no_llm_in_substrate: true
        subsystems:
          homeostasis:
            doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
        """
    )
    c = load_canon(_write_canon(tmp_path, body))
    assert c.system["no_llm_in_substrate"] is True
    assert c.system.get("no_llm_in_substrate", True) is True


def test_canon_with_no_llm_false_parses(tmp_path: Path) -> None:
    """Explicit ``false`` round-trips — the MP1 opt-out shape."""
    body = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.6"
        identity:
          substrate_id: "provider-bridge"
          entry_point: "MYCO.md"
        system:
          hard_contract:
            rule_count: 7
          no_llm_in_substrate: false
        subsystems:
          homeostasis:
            doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
        """
    )
    c = load_canon(_write_canon(tmp_path, body))
    assert c.system["no_llm_in_substrate"] is False
    assert c.system.get("no_llm_in_substrate", True) is False


def test_canon_without_system_block_still_parses(tmp_path: Path) -> None:
    """Edge case: a canon whose ``system`` block contains only the
    minimum required field still loads, and a missing
    ``no_llm_in_substrate`` still defaults to True when accessed via
    ``.get``.

    (Myco's parser requires ``system`` to be non-empty as a mapping,
    but it does not force any particular keys inside it. So the
    minimum-viable ``system`` is a single field — typically
    ``hard_contract`` — with no ``no_llm_in_substrate``. MP1 must
    still be able to make a decision.)
    """
    body = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.6"
        identity:
          substrate_id: "spartan"
          entry_point: "MYCO.md"
        system:
          hard_contract:
            rule_count: 7
        subsystems:
          homeostasis:
            doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
        """
    )
    c = load_canon(_write_canon(tmp_path, body))
    # The ``system`` block loaded, but carries no llm field.
    assert "no_llm_in_substrate" not in c.system
    # MP1's access pattern still yields a usable default.
    assert c.system.get("no_llm_in_substrate", True) is True
