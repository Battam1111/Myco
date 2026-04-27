"""Tests for ``digestion.promote_sporulated`` (v0.6.0)."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.digestion.promote_sporulated import promote_consumed_distilled


def test_no_distilled_no_promotions(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    out = promote_consumed_distilled(ctx)
    assert out["promoted"] == []
    assert out["already_sporulated"] == 0


def test_distilled_with_matching_craft_promoted(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    distilled_dir = genesis_substrate / "notes" / "distilled"
    distilled_dir.mkdir(parents=True, exist_ok=True)
    primordia_dir = genesis_substrate / "docs" / "primordia"
    primordia_dir.mkdir(parents=True, exist_ok=True)

    slug = "my-test-topic"
    distilled = distilled_dir / f"d_{slug}.md"
    distilled.write_text(
        "---\nstage: distilled\n---\ndistilled body\n", encoding="utf-8"
    )
    craft = primordia_dir / f"{slug}_craft_2026-01-01.md"
    craft.write_text("# craft", encoding="utf-8")

    out = promote_consumed_distilled(ctx)
    assert len(out["promoted"]) == 1
    assert out["promoted"][0]["slug"] == slug


def test_already_sporulated_skipped(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    distilled_dir = genesis_substrate / "notes" / "distilled"
    distilled_dir.mkdir(parents=True, exist_ok=True)
    primordia_dir = genesis_substrate / "docs" / "primordia"
    primordia_dir.mkdir(parents=True, exist_ok=True)  # required by run guard
    slug = "already-done"
    (distilled_dir / f"d_{slug}.md").write_text(
        "---\nstage: sporulated\n---\nbody\n", encoding="utf-8"
    )
    out = promote_consumed_distilled(ctx)
    assert out["already_sporulated"] == 1


def test_dry_run_does_not_write(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    distilled_dir = genesis_substrate / "notes" / "distilled"
    distilled_dir.mkdir(parents=True, exist_ok=True)
    primordia_dir = genesis_substrate / "docs" / "primordia"
    primordia_dir.mkdir(parents=True, exist_ok=True)
    slug = "dry-topic"
    distilled = distilled_dir / f"d_{slug}.md"
    distilled.write_text("---\nstage: distilled\n---\nbody\n", encoding="utf-8")
    (primordia_dir / f"{slug}_craft_2026-01-01.md").write_text("# c", encoding="utf-8")
    original = distilled.read_text(encoding="utf-8")
    out = promote_consumed_distilled(ctx, dry_run=True)
    assert out["dry_run"] is True
    # File unchanged
    assert distilled.read_text(encoding="utf-8") == original
