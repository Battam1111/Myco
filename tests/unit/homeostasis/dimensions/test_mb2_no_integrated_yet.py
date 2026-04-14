"""Tests for ``MB2NoIntegratedYet``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.mb2_no_integrated_yet import MB2NoIntegratedYet


def test_silent_when_no_raws(seeded_substrate: Path) -> None:
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
