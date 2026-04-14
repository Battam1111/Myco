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
