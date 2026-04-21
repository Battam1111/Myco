"""CG2 — every ``src/myco/`` subpackage links out to doctrine.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


Inverse of :class:`CG1DoctrineHasSrcReference`: CG1 asks "does
every L2 doctrine page have a code anchor?"; CG2 asks "does every
src subpackage have at least one outgoing doctrine reference?"
Together they fence off the 万物互联 principle at both ends.

A subpackage (a directory under ``src/myco/`` containing
``__init__.py``) is flagged if **none** of its ``*.py`` files
have a module docstring that mentions a ``docs/`` or ``notes/``
path. This is weaker than DC4 (which asks the same of individual
files): one link per subpackage suffices.

Severity: LOW. Same reasoning as DC4 / CG1 — missing doctrine
anchors erode navigability, don't corrupt runtime.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["CG2SubpackageHasDoctrineLink"]


_DOC_PATH_RE = re.compile(r"(?:\.{1,2}/)?(?:docs|notes)/[A-Za-z0-9_./\-]+\.md")


class CG2SubpackageHasDoctrineLink(Dimension):
    """Every ``src/myco/`` subpackage has at least one doctrine link."""

    id = "CG2"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        src_root = ctx.substrate.root / "src" / "myco"
        if not src_root.is_dir():
            return
        for pkg_dir in _iter_subpackages(src_root):
            if _has_any_doc_link(pkg_dir):
                continue
            try:
                rel = pkg_dir.relative_to(ctx.substrate.root).as_posix()
            except ValueError:
                rel = str(pkg_dir)
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"subpackage {rel}/ has no module docstring "
                    f"linking to ``docs/`` or ``notes/`` — add a "
                    f"doctrine anchor in at least one module's "
                    f"docstring so the subsystem is reachable from "
                    f"doctrine navigation."
                ),
                path=rel,
            )


def _iter_subpackages(src_root: Path) -> Iterable[Path]:
    """Yield directories under ``src_root`` that contain ``__init__.py``.

    Skip-dirs are honored; symlinks are not followed.
    """
    if not src_root.is_dir():
        return
    stack: list[Path] = [src_root]
    while stack:
        here = stack.pop()
        try:
            entries = list(here.iterdir())
        except OSError:
            continue
        has_init = any(e.is_file() and e.name == "__init__.py" for e in entries)
        if has_init and here != src_root:
            yield here
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if should_skip_dir(entry.name):
                    continue
                stack.append(entry)


def _has_any_doc_link(pkg_dir: Path) -> bool:
    """True if any ``*.py`` module docstring in ``pkg_dir`` names a
    ``docs/`` or ``notes/`` path. Scans only the immediate directory
    (nested subpackages have their own CG2 check).
    """
    for py_file in pkg_dir.glob("*.py"):
        if not py_file.is_file():
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # Cheap pre-check: avoid full AST parse if the file has no
        # doc/notes token at all.
        if "docs/" not in source and "notes/" not in source:
            continue
        import ast

        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        doc = ast.get_docstring(tree) or ""
        if _DOC_PATH_RE.search(doc):
            return True
    return False
