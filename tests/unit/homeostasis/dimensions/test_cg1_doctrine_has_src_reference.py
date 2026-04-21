"""Tests for ``CG1DoctrineHasSrcReference``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.cg1_doctrine_has_src_reference import (
    CG1DoctrineHasSrcReference,
)


def test_no_l2_dir_silent(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(CG1DoctrineHasSrcReference().run(ctx)) == []


def test_unreferenced_l2_page_fires(seeded_substrate: Path) -> None:
    l2 = seeded_substrate / "docs" / "architecture" / "L2_DOCTRINE"
    l2.mkdir(parents=True)
    (l2 / "ingestion.md").write_text("# ingestion\n", encoding="utf-8")
    # No src/ tree → no code_doc_ref edges → L2 page is unreferenced.
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(CG1DoctrineHasSrcReference().run(ctx))
    assert any("ingestion.md" in f.message for f in findings)
