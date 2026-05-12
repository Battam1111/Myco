"""CG-cluster — merged dimensions (CG1, CG2).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/mechanical/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.identity_cluster import MycoContext, Severity
from myco.core.io_cluster import should_skip_dir
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "CG1DoctrineHasSrcReference",
    "CG2SubpackageHasDoctrineLink",
]


# =========================================================================
# CG1 — see module docstring + original git history at parent commits
# =========================================================================

# v0.8.6 — canon-driven docs path. Substrates may relocate their
# docs tree to `.docs/` (Myco-self) or keep the legacy `docs/`
# default (downstream). Hardcoded `"docs/"` silently returned an
# empty L2 page set on Myco-self for every release v0.8.4…v0.8.5
# (the directory does not exist at that name).
_L2_DOCTRINE_SUBPATH = "architecture/L2_DOCTRINE"


class CG1DoctrineHasSrcReference(Dimension):
    """Every L2 doctrine page has at least one ``code_doc_ref`` edge."""

    id = "CG1"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        l2_dir = ctx.substrate.paths.docs / _L2_DOCTRINE_SUBPATH
        if not l2_dir.is_dir():
            return
        # Collect the L2 pages present on disk.
        pages: set[str] = set()
        for md in l2_dir.rglob("*.md"):
            try:
                rel = md.relative_to(ctx.substrate.root).as_posix()
            except ValueError:
                continue
            pages.add(rel)
        if not pages:
            return
        # Build the graph once; extract destinations of ``code_doc_ref``
        # edges. Lazy import so the dimension registry stays cheap.
        from myco.circulation.graph import build_graph

        graph = build_graph(ctx)
        referenced = {e.dst for e in graph.edges if e.kind == "code_doc_ref"}
        for page in sorted(pages):
            if page in referenced:
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"L2 doctrine page {page} has no incoming "
                    f"`code_doc_ref` edge — either the subsystem is "
                    f"aspirational (state this) or the reference was "
                    f"lost in a refactor (restore from src docstrings)."
                ),
                path=page,
            )


# =========================================================================
# CG2 — see module docstring + original git history at parent commits
# =========================================================================

# v0.8.6 — accept hidden-prefix doctrine paths. Substrates may
# relocate doctrine to `.docs/` and notes to `.myco/notes/` (Myco-
# self post-v0.8.4) or keep legacy `docs/`+`notes/` (downstream).
# The old regex only matched the un-prefixed default, so every
# Myco-self subpackage falsely flagged "no doctrine link" even
# when the module docstring named `.docs/architecture/L2_DOCTRINE/X.md`.
_DOC_PATH_RE = re.compile(
    r"(?:\.{1,2}/)?"
    r"(?:\.docs|docs|\.myco/notes|notes)/"
    r"[A-Za-z0-9_./\-]+\.md"
)


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
        # doc/notes token at all. v0.8.6 — also accept hidden-prefix
        # `.docs/` and `.myco/notes/` patterns so Myco-self substrates
        # don't false-flag every subpackage.
        if (
            "docs/" not in source
            and "notes/" not in source
            and ".docs/" not in source
            and ".myco/notes/" not in source
        ):
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
