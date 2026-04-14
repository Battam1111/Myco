"""Tests for ``SE1DanglingRefs``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.se1_dangling_refs import SE1DanglingRefs


def test_clean_substrate_no_findings(seeded_substrate: Path) -> None:
    # The minimal fixture has no _ref keys and no notes → zero edges.
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(SE1DanglingRefs().run(ctx)) == []


def test_dangling_markdown_link_fires(seeded_substrate: Path) -> None:
    raw = seeded_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "r.md").write_text(
        "---\nid: r\n---\nSee [missing](../../docs/nope.md).\n",
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(SE1DanglingRefs().run(ctx))
    assert any("docs/nope.md" in f.message for f in findings)


def test_external_url_ignored(seeded_substrate: Path) -> None:
    raw = seeded_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "r.md").write_text(
        "---\nid: r\n---\nSee [site](https://example.com).\n",
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(SE1DanglingRefs().run(ctx)) == []
