"""Tests for ``DC3PublicClassDocstring``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.dc3_public_class_docstring import (
    DC3PublicClassDocstring,
)


def test_clean_public_class(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\nclass Public:\n    """docstring."""\n    pass\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC3PublicClassDocstring().run(ctx)) == []


def test_missing_class_docstring_fires(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\nclass Public:\n    x = 1\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(DC3PublicClassDocstring().run(ctx))
    assert len(findings) == 1
    assert "Public" in findings[0].message


def test_private_class_exempt(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\nclass _Private:\n    pass\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC3PublicClassDocstring().run(ctx)) == []
