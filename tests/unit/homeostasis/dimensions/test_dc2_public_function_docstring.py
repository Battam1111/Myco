"""Tests for ``DC2PublicFunctionDocstring``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.dc2_public_function_docstring import (
    DC2PublicFunctionDocstring,
)


def test_clean_public_function(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\ndef public():\n    """summary."""\n    return 1\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC2PublicFunctionDocstring().run(ctx)) == []


def test_missing_docstring_fires(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\ndef public():\n    return 1\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(DC2PublicFunctionDocstring().run(ctx))
    assert len(findings) == 1
    assert "public" in findings[0].message


def test_private_function_exempt(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\ndef _private():\n    return 1\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC2PublicFunctionDocstring().run(ctx)) == []


def test_dunder_exempt(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\n'
        "class X:\n"
        "    def __init__(self):\n"
        "        self.x = 1\n"
        "    def __repr__(self):\n"
        "        return 'X'\n",
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC2PublicFunctionDocstring().run(ctx)) == []
