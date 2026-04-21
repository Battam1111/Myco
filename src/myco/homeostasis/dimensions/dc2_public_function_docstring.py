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
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                name = node.name
                if name.startswith("_") and name not in _EXEMPT_DUNDERS:
                    # Private name; not in scope.
                    continue
                if name in _EXEMPT_DUNDERS:
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
