"""DC1 — every ``src/myco/**/*.py`` file has a module docstring.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


A module without a docstring is an orphan from the circulation
graph's perspective: the docstring is where ``code_doc_ref`` edges
come from (see :mod:`myco.circulation.graph_src`). No docstring
means no doc-ref, which means the module is unreachable from
doctrine traversal — a quiet break of L2 principle 5 (万物互联,
everything connected).

DC1 detects. Repair (v0.6.0 §F18 §A5): NARROW stub docstring
inserted at module top with the marker `_AGENT_TODO_DOCSTRING_`
so RL3 + agent-side review can flag stubs for proper rewrite. The
stub is preferable to 121-LOW-finding noise that trains agents to
skim immune output (per craft v0_5_9_immune_zero §30-35 reasoning,
extended to fixable here).

Severity: LOW. Missing docstrings don't corrupt state; they just
make the substrate harder to navigate. Per :mod:`myco.core.severity`
low findings do not gate CI by default.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.io_atomic import atomic_utf8_write
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["DC1ModuleDocstring"]


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
