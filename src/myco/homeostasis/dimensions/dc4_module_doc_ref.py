"""DC4 — every non-trivial module has at least one doctrine reference.

A module's docstring should name the L0/L1/L2/L3 doctrine page it
implements — that's how the circulation graph builds
``code_doc_ref`` edges (see :mod:`myco.circulation.graph_src`).
Without a doc-ref, a module is reachable from imports but not from
doctrine traversal, which breaks the "everything connected" L0
principle in a one-way direction (agents reading code can find
doctrine; agents reading doctrine can't find code).

Scope: modules over 40 non-comment/non-blank lines. Tiny stubs,
``__init__.py`` re-exports, and tests are intentionally excluded —
they don't carry enough logic to warrant a doctrine anchor and
would dominate the finding list with false positives.

Severity: LOW. Missing doc-refs slow down navigation but do not
corrupt state.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["DC4ModuleDocRef"]


_DOC_PATH_RE = re.compile(r"(?:\.{1,2}/)?(?:docs|notes)/[A-Za-z0-9_./\-]+\.md")
#: Modules smaller than this (in non-blank, non-comment lines) are
#: exempt. Counted on the pre-parsed source text to stay cheap.
_MIN_LINES: int = 40


class DC4ModuleDocRef(Dimension):
    """Non-trivial modules reference at least one doctrine page."""

    id = "DC4"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        src_dir = ctx.substrate.root / "src" / "myco"
        if not src_dir.is_dir():
            return
        for py_file in _walk_py(src_dir):
            if py_file.name == "__init__.py":
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if _effective_lines(source) < _MIN_LINES:
                continue
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue
            docstring = ast.get_docstring(tree) or ""
            if _DOC_PATH_RE.search(docstring):
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
                    f"{rel} module docstring contains no doctrine or "
                    f"notes reference; add a ``docs/architecture/...md`` "
                    f"or ``notes/integrated/...md`` path so the "
                    f"circulation graph can anchor it."
                ),
                path=rel,
                line=1,
            )


def _effective_lines(source: str) -> int:
    """Count non-blank, non-comment lines. Cheap stand-in for SLOC.

    Doesn't handle triple-quoted strings or inline comments exactly;
    that level of precision isn't worth the cost. The goal is to
    separate trivial shims from real modules with a clear gap.
    """
    n = 0
    for line in source.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        n += 1
    return n


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
