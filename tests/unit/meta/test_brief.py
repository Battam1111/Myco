"""Tests for ``myco.cycle.brief`` — the one human-facing verb (v0.5.5 MAJOR-G).

``brief`` is L0 principle 1's single carved exception: it produces a
stable-section markdown rollup of substrate state for a human
reading moment. Tests pin the section order, the json mode, and the
next-action suggestion logic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.cycle.brief import run as brief_run


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_brief_default_is_markdown(genesis_substrate: Path) -> None:
    ctx = _ctx(genesis_substrate)
    r = brief_run({}, ctx=ctx)
    assert r.exit_code == 0
    assert "markdown" in r.payload
    md = r.payload["markdown"]
    # Stable-order section headings.
    assert "## 1. Identity" in md
    assert "## 2. Hunger" in md
    assert "## 3. Immune" in md
    assert "## 4. Notes" in md
    assert "## 5. Recent primordia" in md
    assert "## 6. Local plugins" in md
    assert "## 7. Suggested next" in md


def test_brief_sections_appear_in_stable_order(genesis_substrate: Path) -> None:
    ctx = _ctx(genesis_substrate)
    md = brief_run({}, ctx=ctx).payload["markdown"]
    ordered = [
        "## 1. Identity",
        "## 2. Hunger",
        "## 3. Immune",
        "## 4. Notes",
        "## 5. Recent primordia",
        "## 6. Local plugins",
        "## 7. Suggested next",
    ]
    positions = [md.index(h) for h in ordered]
    assert positions == sorted(positions)


def test_brief_identity_lists_canon_fields(genesis_substrate: Path) -> None:
    ctx = _ctx(genesis_substrate)
    md = brief_run({}, ctx=ctx).payload["markdown"]
    assert "**substrate_id**:" in md
    assert "**contract_version**:" in md
    assert "**entry_point**:" in md


def test_brief_json_payload_matches_markdown_data(genesis_substrate: Path) -> None:
    """Markdown mode also exposes the raw payload structure so the
    agent can introspect the same data programmatically."""
    ctx = _ctx(genesis_substrate)
    payload = brief_run({}, ctx=ctx).payload
    assert payload["identity"]["substrate_id"]
    assert "hunger" in payload
    assert "immune" in payload
    assert "notes" in payload
    assert "primordia" in payload
    assert "local_plugins" in payload
    assert "suggested_next" in payload


def test_brief_suggestions_are_nonempty(genesis_substrate: Path) -> None:
    ctx = _ctx(genesis_substrate)
    suggestions = brief_run({}, ctx=ctx).payload["suggested_next"]
    assert isinstance(suggestions, list)
    assert len(suggestions) >= 1
    # Calm substrate: at least the "no action" message.


def test_brief_suggests_assimilate_on_raw_backlog(
    genesis_substrate: Path,
) -> None:
    """When raw notes exist but integrated is empty, brief nudges
    toward assimilate."""
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for i in range(3):
        (raw / f"test_{i}.md").write_text(
            f"---\ntags: [x]\n---\n\ntest note {i}\n", encoding="utf-8"
        )

    ctx = _ctx(genesis_substrate)
    suggestions = brief_run({}, ctx=ctx).payload["suggested_next"]
    joined = " ".join(suggestions).lower()
    assert "assimilate" in joined


def test_brief_does_not_crash_on_missing_primordia(
    tmp_path: Path, minimal_canon_text: str,
) -> None:
    """Substrates without docs/primordia/ (freshly germinated) still
    produce a valid brief."""
    (tmp_path / "_canon.yaml").write_text(minimal_canon_text, encoding="utf-8")
    ctx = _ctx(tmp_path)
    r = brief_run({}, ctx=ctx)
    assert r.exit_code == 0
    assert r.payload["primordia"] == []


def test_brief_renders_immune_findings_table_when_present(
    tmp_path: Path, minimal_canon_text: str,
) -> None:
    """If immune produces findings, they surface as a markdown table.
    seeded substrate lacks write_surface + entry-point file → M2+M3
    fire."""
    (tmp_path / "_canon.yaml").write_text(minimal_canon_text, encoding="utf-8")
    ctx = _ctx(tmp_path)
    md = brief_run({}, ctx=ctx).payload["markdown"]
    # The immune section should either report findings or ok: True.
    assert "## 3. Immune" in md
    # At least one of M2 / M3 is expected on the seeded fixture.
    assert "M2" in md or "M3" in md
