"""Tests for ``CG2SubpackageHasDoctrineLink``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.cg2_subpackage_has_doctrine_link import (
    CG2SubpackageHasDoctrineLink,
)


def test_subpackage_with_doc_ref_clean(seeded_substrate: Path) -> None:
    pkg = seeded_substrate / "src" / "myco" / "ingestion"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mod.py").write_text(
        '"""ingestion.\n\nGoverns docs/architecture/L2_DOCTRINE/ingestion.md.\n"""\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(CG2SubpackageHasDoctrineLink().run(ctx)) == []


def test_subpackage_without_doc_ref_fires(seeded_substrate: Path) -> None:
    pkg = seeded_substrate / "src" / "myco" / "weirdpkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mod.py").write_text('"""no doctrine reference here."""\n', encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(CG2SubpackageHasDoctrineLink().run(ctx))
    assert any("weirdpkg" in f.message for f in findings)
