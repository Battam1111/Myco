"""Tests for ``SE2OrphanIntegrated``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.se2_orphan_integrated import SE2OrphanIntegrated


def test_silent_when_no_integrated(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    assert list(SE2OrphanIntegrated().run(ctx)) == []


def test_fires_on_unreferenced_integrated(genesis_substrate: Path) -> None:
    integ = genesis_substrate / "notes" / "integrated"
    integ.mkdir(parents=True, exist_ok=True)
    (integ / "n_lonely.md").write_text("---\nid: lonely\n---\nbody\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(SE2OrphanIntegrated().run(ctx))
    assert any("n_lonely.md" in f.message for f in findings)


def test_silent_when_referenced(genesis_substrate: Path) -> None:
    integ = genesis_substrate / "notes" / "integrated"
    raw = genesis_substrate / "notes" / "raw"
    integ.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    (integ / "n_a.md").write_text("---\nid: a\n---\nbody\n", encoding="utf-8")
    # Frontmatter `references:` resolves against the substrate root
    # (anchor="root"), so "notes/integrated/n_a.md" is the exact key
    # SE2 checks.
    (raw / "r.md").write_text(
        "---\nid: r\nreferences:\n  - notes/integrated/n_a.md\n---\nbody\n",
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = [f for f in SE2OrphanIntegrated().run(ctx) if "n_a.md" in f.message]
    assert findings == []
