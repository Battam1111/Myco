"""DC3 — every public class in ``src/myco/`` has a docstring.

"Public" = name does not start with an underscore. Class
docstrings carry the contract of the type: what it represents,
what invariants it holds, what fields the caller may rely on.
A class without one is an agent-readability regression.

Severity: LOW. Same reasoning as DC1/DC2 — missing docstrings
don't corrupt state; they erode navigability. Autofix is not
implemented: writing a meaningful class contract isn't a template
fill-in.
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

__all__ = ["DC3PublicClassDocstring"]


class DC3PublicClassDocstring(Dimension):
    """Every public class under ``src/myco/`` has a docstring."""

    id = "DC3"
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
            try:
                rel = py_file.relative_to(ctx.substrate.root).as_posix()
            except ValueError:
                rel = py_file.as_posix()
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if node.name.startswith("_"):
                    continue
                doc = ast.get_docstring(node)
                if doc and doc.strip():
                    continue
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"public class {node.name!r} in {rel} has no "
                        f"docstring — add one that names the invariants "
                        f"the type carries."
                    ),
                    path=rel,
                    line=node.lineno,
                )


def _walk_py(src_dir: Path) -> Iterable[Path]:
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
