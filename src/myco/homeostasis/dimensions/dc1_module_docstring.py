"""DC1 — every ``src/myco/**/*.py`` file has a module docstring.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


A module without a docstring is an orphan from the circulation
graph's perspective: the docstring is where ``code_doc_ref`` edges
come from (see :mod:`myco.circulation.graph_src`). No docstring
means no doc-ref, which means the module is unreachable from
doctrine traversal — a quiet break of L2 principle 5 (万物互联,
everything connected).

DC1 detects. Repair is human/agent work: writing a meaningful
docstring is not a template fill-in.

Severity: LOW. Missing docstrings don't corrupt state; they just
make the substrate harder to navigate. Per :mod:`myco.core.severity`
low findings do not gate CI by default.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["DC1ModuleDocstring"]


class DC1ModuleDocstring(Dimension):
    """Every ``src/myco/**/*.py`` file has a module-level docstring."""

    id = "DC1"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        src_dir = ctx.substrate.root / "src" / "myco"
        if not src_dir.is_dir():
            return
        for py_file in _walk_py(src_dir):
            try:
                source = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue
            docstring = ast.get_docstring(tree)
            if docstring and docstring.strip():
                continue
            try:
                rel = py_file.relative_to(ctx.substrate.root).as_posix()
            except ValueError:
                rel = py_file.as_posix()
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"{rel} has no module docstring — write one that "
                    f"states the module's purpose and, where relevant, "
                    f"references the governing L2 doctrine page."
                ),
                path=rel,
                line=1,
            )


def _walk_py(src_dir: Path) -> Iterable[Path]:
    """DFS under ``src_dir`` yielding ``*.py`` files, pruning skip-dirs.

    Shares skip semantics with every other walker in Myco
    (:mod:`myco.core.skip_dirs`) so a ``.venv/`` inside the substrate
    cannot dominate DC1's runtime.
    """
    if not src_dir.is_dir():
        return
    stack: list[Path] = [src_dir]
    while stack:
        here = stack.pop()
        try:
            entries = list(here.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if should_skip_dir(entry.name):
                    continue
                stack.append(entry)
            elif entry.is_file() and entry.suffix == ".py":
                yield entry
