"""PA3 — surface/ stays a pure adapter (imports only manifest + stdlib).

Governing doctrine: ``docs/architecture/L3_IMPLEMENTATION/package_map.md``
invariant 4 ("surface/ is pure adapter; imports come from
``myco.boundary.surface.manifest`` or stdlib only").

Severity: LOW. PA3 is informational — surface/ may legitimately import
``myco.core`` (the kernel primitives) and FastMCP/argparse helpers.
A finding here flags accidental subsystem leakage into the surface
layer.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["PA3SurfacePureAdapter"]

_ALLOWED_INTERNAL_PREFIXES: tuple[str, ...] = (
    "myco.core",
    "myco.boundary.surface",
)

_FORBIDDEN_INTERNAL_PREFIXES: tuple[str, ...] = (
    "myco.ingestion",
    "myco.digestion",
    "myco.circulation",
    "myco.homeostasis",
    "myco.cycle",
    "myco.germination",
)


class PA3SurfacePureAdapter(Dimension):
    """surface/ may not import subsystem packages directly."""

    id = "PA3"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        surface_root = ctx.substrate.root / "src" / "myco" / "surface"
        if not surface_root.is_dir():
            return
        for path in surface_root.rglob("*.py"):
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
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"surface/ imports subsystem package {module!r}; "
                            f"surface should be pure adapter "
                            f"(invariant 4 in package_map.md)"
                        ),
                        path=rel,
                    )
