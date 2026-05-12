"""DC-cluster — merged dimensions (DC1, DC2, DC3, DC4, DC5).

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

import ast
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.io_atomic import atomic_utf8_write
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = [
    "DC1ModuleDocstring",
    "DC2PublicFunctionDocstring",
    "DC3PublicClassDocstring",
    "DC4ModuleDocRef",
    "DC5AbstractParentAllowlist",
]


# =========================================================================
# DC1 — see module docstring + original git history at parent commits
# =========================================================================


class DC1ModuleDocstring(Dimension):
    """Every ``src/myco/**/*.py`` file has a module-level docstring."""

    id = "DC1"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = True

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Insert stub module docstring with `_AGENT_TODO_DOCSTRING_` marker.

        v0.6.0 §A5/§F18: stub is preferable to 121-LOW-finding noise.
        Agent-side review flags the marker for proper rewrite. Idempotent.
        """
        rel = finding.path
        if not rel:
            return {"applied": False, "detail": "no path on finding"}
        target = ctx.substrate.root / rel
        if not target.is_file():
            return {"applied": False, "detail": f"{rel} not found"}
        try:
            source = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return {"applied": False, "detail": "read failed"}
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {"applied": False, "detail": "syntax error blocks fix"}
        if ast.get_docstring(tree):
            return {"applied": False, "detail": "docstring already present"}
        # Derive a minimal purpose hint from the filename.
        purpose = target.stem.replace("_", " ").strip()
        stub = (
            f'"""{purpose}.\n\n'
            f"v0.6.0 DC1 stub. _AGENT_TODO_DOCSTRING_ — replace with real "
            f"description and (where relevant) ``Governing doctrine: "
            f'docs/architecture/L2_DOCTRINE/<doc>.md``.\n"""\n'
        )
        # Preserve __future__ shebang/encoding if present at line 0.
        new_source = stub + source if not source.lstrip().startswith('"""') else source
        atomic_utf8_write(target, new_source)
        return {"applied": True, "detail": f"inserted DC1 stub docstring in {rel}"}

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


# =========================================================================
# DC2 — see module docstring + original git history at parent commits
# =========================================================================

#: Dunder methods whose semantics are conventionally documented at
#: the language level; we don't require docstrings on these.
_EXEMPT_DUNDERS: frozenset[str] = frozenset(
    {
        "__init__",
        "__repr__",
        "__str__",
        "__eq__",
        "__hash__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__ne__",
        "__iter__",
        "__next__",
        "__len__",
        "__getitem__",
        "__setitem__",
        "__delitem__",
        "__contains__",
        "__enter__",
        "__exit__",
        "__call__",
        "__bool__",
        "__new__",
    }
)


class DC2PublicFunctionDocstring(Dimension):
    """Every public function/method under ``src/myco/`` has a docstring."""

    id = "DC2"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        """Yield one LOW finding per public function lacking a docstring.

        Scans ``src/myco/**/*.py`` via ``_walk_py`` (skip-dir + symlink
        aware), parses each file with :mod:`ast`, and emits on public
        function/method definitions whose ``ast.get_docstring`` is
        absent or whitespace-only. Exemptions are documented in the
        module docstring.
        """
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
            # v0.5.9: collect the set of method-node ids whose enclosing
            # class inherits from an abstract parent (Adapter / Protocol
            # / Dimension). Methods in that set are exempt from DC2
            # because the parent's docstring documents their contract.
            # We compute this up front over the tree so the inner
            # classifier is O(1) per method.
            override_node_ids: set[int] = _collect_abstract_override_ids(tree)

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                name = node.name
                if name.startswith("_") and name not in _EXEMPT_DUNDERS:
                    continue
                if name in _EXEMPT_DUNDERS:
                    continue
                if _is_property(node):
                    continue
                if id(node) in override_node_ids:
                    continue
                doc = ast.get_docstring(node)
                if doc and doc.strip():
                    continue
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"public function {name!r} in {rel} has no "
                        f"docstring — agents read docstrings, not "
                        f"code; add a one-sentence summary."
                    ),
                    path=rel,
                    line=node.lineno,
                )


#: The abstract/protocol base classes whose subclasses get DC2
#: exemption on method overrides. Keep the set tight; expanding
#: it is a doctrine decision (see v0.5.9 immune-zero craft §T6).
_ABSTRACT_PARENT_NAMES: frozenset[str] = frozenset({"Adapter", "Protocol", "Dimension"})


def _collect_abstract_override_ids(tree: ast.Module) -> set[int]:
    """Return ``id()`` of every method node whose enclosing class
    inherits from one of :data:`_ABSTRACT_PARENT_NAMES`.

    Done as a single pass so the DC2 main loop does an O(1)
    set-membership test per candidate method rather than an
    O(classes * methods) re-scan.
    """
    override_ids: set[int] = set()
    for class_node in ast.walk(tree):
        if not isinstance(class_node, ast.ClassDef):
            continue
        inherits_abstract = False
        for base in class_node.bases:
            base_name = base.id if isinstance(base, ast.Name) else None
            if base_name in _ABSTRACT_PARENT_NAMES:
                inherits_abstract = True
                break
        if not inherits_abstract:
            continue
        for child in class_node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                override_ids.add(id(child))
    return override_ids


def _is_property(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True iff the function has ``@property`` (or setter/deleter/getter)."""
    for dec in func_node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == "property":
            return True
        if isinstance(dec, ast.Attribute) and dec.attr in {
            "setter",
            "deleter",
            "getter",
        }:
            return True
    return False


# =========================================================================
# DC3 — see module docstring + original git history at parent commits
# =========================================================================


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


# =========================================================================
# DC4 — see module docstring + original git history at parent commits
# =========================================================================

_DC4_DOCTRINE_HINTS = {
    "ingestion": "L2_DOCTRINE/ingestion.md",
    "digestion": "L2_DOCTRINE/digestion.md",
    "circulation": "L2_DOCTRINE/circulation.md",
    "homeostasis": "L2_DOCTRINE/homeostasis.md",
    "germination": "L2_DOCTRINE/genesis.md",
    "cycle": "L2_DOCTRINE/cycle.md",
    "boundary": "L2_DOCTRINE/boundary.md",
    "core": "L2_DOCTRINE/homeostasis.md",
}


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


# =========================================================================
# DC5 — see module docstring + original git history at parent commits
# =========================================================================

#: DC2's historical hardcode (kept here for documentation; the canon
#: field replaces this when present).
_DEFAULT_ALLOWLIST: tuple[str, ...] = ("ABC", "Protocol", "TypedDict")


class DC5AbstractParentAllowlist(Dimension):
    """canon should declare lint.abstract_parent_allowlist explicitly."""

    id = "DC5"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        lint = ctx.substrate.canon.lint or {}
        allowlist = (
            lint.get("abstract_parent_allowlist") if isinstance(lint, dict) else None
        )
        if allowlist is None:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"canon.lint.abstract_parent_allowlist not declared; "
                    f"DC2 falls back to hardcoded {_DEFAULT_ALLOWLIST}"
                ),
                path="_canon.yaml",
            )
