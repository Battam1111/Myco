"""Tests for ``DC1ModuleDocstring``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.dc1_module_docstring import DC1ModuleDocstring


def test_no_src_dir_silent(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC1ModuleDocstring().run(ctx)) == []


def test_clean_module_no_finding(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "plugin"
    src.mkdir(parents=True)
    (src / "mod.py").write_text('"""docstring."""\n', encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC1ModuleDocstring().run(ctx)) == []


def test_missing_docstring_fires(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "plugin"
    src.mkdir(parents=True)
    (src / "bare.py").write_text("x = 1\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(DC1ModuleDocstring().run(ctx))
    assert len(findings) == 1
    assert "no module docstring" in findings[0].message
    assert findings[0].path is not None
    assert "bare.py" in findings[0].path
