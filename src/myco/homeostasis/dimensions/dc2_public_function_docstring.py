"""DC2 — every public function/method in ``src/myco/`` has a docstring.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


"Public" = name does not start with an underscore, and the
function is not a dunder (``__init__`` etc.). Docstrings on public
functions are the primary vehicle for agent-facing documentation:
every agent reading source does so by scanning docstrings.

DC2 emits one LOW finding per public function without a docstring.
Batch noise is controlled at LOW severity — immune --fix will not
act on DC2 (the repair is writing meaningful prose, not a
template).

Excluded:
- ``__init__``: the class docstring already documents construction.
- Dunder methods (``__repr__``, ``__eq__``, etc.): convention
  documents their semantics.
- Private functions (``_helper``, ``__mangle``): agents see them
  only when reading surrounding code in context.
- ``@property`` decorated methods: semantically they're attribute
  accessors; the owning class's docstring is expected to name the
  attribute, and a redundant one-line docstring here would just be
  noise. (v0.5.9 refinement — Adapter-protocol implementations
  and dataclass-like accessors were disproportionately penalised.)
- Methods that override a parent class's abstract method: when the
  parent (typically a Protocol / ABC) already documents the method
  contract, re-documenting in every concrete subclass is visual
  tax without information gain. Detected heuristically:
  ``class Foo(Parent)`` with Parent's name matching an import-time
  symbol that has ``@abstractmethod`` decoration. (v0.5.9 heuristic;
  not perfect, but catches the Adapter protocol case cleanly.)
- Generated code: files under ``.myco/plugins/`` (MF2 scope) and
  under skip-dirs.
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

__all__ = ["DC2PublicFunctionDocstring"]

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
