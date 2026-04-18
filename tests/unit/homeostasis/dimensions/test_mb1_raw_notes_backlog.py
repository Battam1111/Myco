"""Tests for ``MB1RawNotesBacklog``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.mb1_raw_notes_backlog import MB1RawNotesBacklog


def _seed_raws(root: Path, n: int) -> None:
    raw = root / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (raw / f"r_{i:03d}.md").write_text(
            f"---\nid: r_{i}\n---\nbody\n", encoding="utf-8"
        )


def test_silent_when_no_raws(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(MB1RawNotesBacklog().run(ctx)) == []


def test_low_when_small_backlog(seeded_substrate: Path) -> None:
    _seed_raws(seeded_substrate, 3)
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(MB1RawNotesBacklog().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.LOW


def test_medium_when_over_threshold(seeded_substrate: Path) -> None:
    _seed_raws(seeded_substrate, 11)
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(MB1RawNotesBacklog().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.MEDIUM


# ---------------------------------------------------------------------------
# v0.5.5 MAJOR-A — fixable seam
# ---------------------------------------------------------------------------


def test_mb1_is_fixable_class_attribute() -> None:
    """MB1 declares itself fixable at the class level."""
    assert MB1RawNotesBacklog.fixable is True


def test_mb1_fix_runs_assimilate_and_promotes(seeded_substrate: Path) -> None:
    """Fix delegates to ``reflect()`` and reports promoted count.

    Seeds a small backlog, runs the dimension, then calls ``fix`` —
    expects every raw note to disappear from ``notes/raw/`` and land
    as ``notes/integrated/n_<id>.md``.
    """
    _seed_raws(seeded_substrate, 3)
    ctx = MycoContext.for_testing(root=seeded_substrate)
    dim = MB1RawNotesBacklog()

    findings = list(dim.run(ctx))
    assert len(findings) == 1

    outcome = dim.fix(ctx, findings[0])

    assert outcome["applied"] is True
    assert outcome["promoted"] == 3
    # The raw dir is drained.
    raw_dir = seeded_substrate / "notes" / "raw"
    remaining = list(raw_dir.glob("*.md")) if raw_dir.is_dir() else []
    assert remaining == []
    # Integrated has one file per raw.
    integrated = seeded_substrate / "notes" / "integrated"
    assert integrated.is_dir()
    integrated_files = sorted(p.name for p in integrated.glob("n_*.md"))
    assert len(integrated_files) == 3
