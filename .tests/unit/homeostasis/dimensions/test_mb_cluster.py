"""Tests for ``mb_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.dimensions.metabolic.mb_cluster import (
    MB1RawNotesBacklog,
    MB2NoIntegratedYet,
    MB3RawNotesHighWatermark,
)

# =========================================================================
# test_mb1_raw_notes_backlog — see git history for original per-dim file
# =========================================================================


def _seed_raws(root: Path, n: int) -> None:
    raw = root / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (raw / f"r_{i:03d}.md").write_text(
            f"---\nid: r_{i}\n---\nbody\n", encoding="utf-8"
        )


def test_mb1_silent_when_no_raws(seeded_substrate: Path) -> None:
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


# =========================================================================
# test_mb2_no_integrated_yet — see git history for original per-dim file
# =========================================================================


def test_mb2_silent_when_no_raws(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(MB2NoIntegratedYet().run(ctx)) == []


def test_fires_when_raws_but_no_integrated(seeded_substrate: Path) -> None:
    raw = seeded_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "r.md").write_text("---\nid: r\n---\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(MB2NoIntegratedYet().run(ctx))
    assert len(findings) == 1


def test_silent_when_integrated_exists(seeded_substrate: Path) -> None:
    raw = seeded_substrate / "notes" / "raw"
    integ = seeded_substrate / "notes" / "integrated"
    raw.mkdir(parents=True, exist_ok=True)
    integ.mkdir(parents=True, exist_ok=True)
    (raw / "r.md").write_text("---\nid: r\n---\n", encoding="utf-8")
    (integ / "n_x.md").write_text("---\nid: x\n---\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(MB2NoIntegratedYet().run(ctx)) == []


# =========================================================================
# test_mb3_raw_notes_high_watermark — see git history for original per-dim file
# =========================================================================


def test_empty_silent(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(MB3RawNotesHighWatermark().run(ctx)) == []


def test_below_watermark_silent(seeded_substrate: Path) -> None:
    raw = seeded_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for i in range(10):
        (raw / f"n{i}.md").write_text("---\n---\nbody\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(MB3RawNotesHighWatermark().run(ctx)) == []


def test_at_watermark_fires_high(seeded_substrate: Path) -> None:
    raw = seeded_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for i in range(50):
        (raw / f"n{i}.md").write_text("---\n---\nbody\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(MB3RawNotesHighWatermark().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH
