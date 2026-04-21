"""Tests for ``DC4ModuleDocRef``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.dc4_module_doc_ref import DC4ModuleDocRef


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
