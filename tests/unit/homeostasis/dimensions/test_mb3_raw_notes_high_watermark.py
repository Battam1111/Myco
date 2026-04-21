"""Tests for ``MB3RawNotesHighWatermark``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.mb3_raw_notes_high_watermark import (
    MB3RawNotesHighWatermark,
)


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
