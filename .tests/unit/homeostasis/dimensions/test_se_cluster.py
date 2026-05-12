"""Tests for ``se_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.semantic.se_cluster import (
    SE1DanglingRefs,
    SE2OrphanIntegrated,
    SE3LinkSelfCycle,
)

# =========================================================================
# test_se1_dangling_refs — see git history for original per-dim file
# =========================================================================


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


# =========================================================================
# test_se2_orphan_integrated — see git history for original per-dim file
# =========================================================================


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


# =========================================================================
# test_se3_link_self_cycle — see git history for original per-dim file
# =========================================================================


def test_clean_substrate_no_finding(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(SE3LinkSelfCycle().run(ctx)) == []


def test_self_reference_fires(seeded_substrate: Path) -> None:
    raw = seeded_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "self.md").write_text(
        "---\nid: self\n---\nSee [me](./self.md).\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(SE3LinkSelfCycle().run(ctx))
    assert any("references itself" in f.message for f in findings)
