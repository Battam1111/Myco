"""PA4 — core/ does not import subsystem packages.

Governing doctrine: ``docs/architecture/L3_IMPLEMENTATION/package_map.md``
invariant 2 ("core/ has no downstream dependency on any subsystem").

Severity: LOW at land, ramps to HIGH after 30 sessions per craft v0.6.0
``severity_promotion``. PA4 specifically allow-lists schema_upgraders
metaprogramming registration in ``core/canon.py`` — those registrations
do not import the upgraded packages, just register callables.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["PA4CoreNoSubsystemDeps"]

_FORBIDDEN_INTERNAL_PREFIXES: tuple[str, ...] = (
    "myco.ingestion",
    "myco.digestion",
    "myco.circulation",
    "myco.homeostasis",
    "myco.cycle",
    "myco.germination",
    "myco.boundary.surface",
    "myco.boundary.install",
    "myco.boundary",
    "myco.boundary.mcp",
)

#: Files inside core/ that may legitimately reference subsystem
#: package names by string (NOT by import). Allow-list is path-based.
_PA4_PERMITS: frozenset[str] = frozenset(
    {
        # canon.py registers schema_upgraders by string-keyed callable;
        # the callables don't import subsystems either, but if a future
        # registration grows complexity it would land here first.
        "src/myco/core/canon.py",
    }
)


class PA4CoreNoSubsystemDeps(Dimension):
    """core/ may not import any subsystem package."""

    id = "PA4"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        core_root = ctx.substrate.root / "src" / "myco" / "core"
        if not core_root.is_dir():
            return
        for path in core_root.rglob("*.py"):
            rel = path.relative_to(ctx.substrate.root).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
            for node in ast.walk(tree):
                module: str | None = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        break
                if not module:
                    continue
                if any(module.startswith(p) for p in _FORBIDDEN_INTERNAL_PREFIXES):
                    if rel in _PA4_PERMITS:
                        continue
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"core/ imports subsystem package {module!r} "
                            f"(invariant 2 in package_map.md)"
                        ),
                        path=rel,
                    )
