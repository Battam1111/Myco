"""Tests for ``cg_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.mechanical.cg_cluster import (
    CG1DoctrineHasSrcReference,
    CG2SubpackageHasDoctrineLink,
)

# =========================================================================
# test_cg1_doctrine_has_src_reference — see git history for original per-dim file
# =========================================================================


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


# =========================================================================
# test_cg2_subpackage_has_doctrine_link — see git history for original per-dim file
# =========================================================================


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
