"""Tests for ``SE3LinkSelfCycle``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.se3_link_self_cycle import SE3LinkSelfCycle


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
