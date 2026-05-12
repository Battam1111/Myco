"""Tests for ``dc_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.identity_cluster import MycoContext
from myco.homeostasis.dimensions.mechanical.dc_cluster import (
    DC1ModuleDocstring,
    DC2PublicFunctionDocstring,
    DC3PublicClassDocstring,
    DC4ModuleDocRef,
)

# =========================================================================
# test_dc1_module_docstring — see git history for original per-dim file
# =========================================================================


def test_no_src_dir_silent(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC1ModuleDocstring().run(ctx)) == []


def test_clean_module_no_finding(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "plugin"
    src.mkdir(parents=True)
    (src / "mod.py").write_text('"""docstring."""\n', encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC1ModuleDocstring().run(ctx)) == []


def test_dc1_missing_module_docstring_fires(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "plugin"
    src.mkdir(parents=True)
    (src / "bare.py").write_text("x = 1\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(DC1ModuleDocstring().run(ctx))
    assert len(findings) == 1
    assert "no module docstring" in findings[0].message
    assert findings[0].path is not None
    assert "bare.py" in findings[0].path


# =========================================================================
# test_dc2_public_function_docstring — see git history for original per-dim file
# =========================================================================


def test_clean_public_function(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    (src / "mod.py").write_text(
        '"""module."""\ndef public():\n    """summary."""\n    return 1\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC2PublicFunctionDocstring().run(ctx)) == []


def test_dc2_missing_function_docstring_fires(seeded_substrate: Path) -> None:
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


# =========================================================================
# test_dc3_public_class_docstring — see git history for original per-dim file
# =========================================================================


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


# =========================================================================
# test_dc4_module_doc_ref — see git history for original per-dim file
# =========================================================================


def _write_module(src: Path, name: str, docstring: str, sloc: int = 60) -> None:
    lines = [f'"""{docstring}"""', ""]
    for i in range(sloc):
        lines.append(f"x{i} = {i}")
    (src / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_short_module_exempt(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    _write_module(src, "tiny.py", "small module.", sloc=5)
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC4ModuleDocRef().run(ctx)) == []


def test_doc_ref_present_no_finding(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    _write_module(
        src,
        "mod.py",
        "references docs/architecture/L2_DOCTRINE/ingestion.md.",
        sloc=60,
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(DC4ModuleDocRef().run(ctx)) == []


def test_no_doc_ref_fires(seeded_substrate: Path) -> None:
    src = seeded_substrate / "src" / "myco" / "util"
    src.mkdir(parents=True)
    _write_module(src, "mod.py", "substantive but unanchored.", sloc=60)
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(DC4ModuleDocRef().run(ctx))
    assert len(findings) == 1
    assert "no doctrine" in findings[0].message.lower()
