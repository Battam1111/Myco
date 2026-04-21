"""M3 — ``system.write_surface.allowed`` is a non-empty list.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (mechanical / MEDIUM).

Governance depends on an explicit write-surface declaration: tools
that auto-create files (genesis, eat, digest) promise to stay within
it. An empty or absent list means anything can be written anywhere —
no drift detection possible.

Severity: MEDIUM. The absence is recoverable via a canon edit; it
does not corrupt state, it only weakens enforcement.
"""

from __future__ import annotations

from collections.abc import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["M3WriteSurfaceDeclared"]


class M3WriteSurfaceDeclared(Dimension):
    """``system.write_surface.allowed`` must be a non-empty list."""

    id = "M3"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        system = ctx.substrate.canon.system or {}
        ws = system.get("write_surface")
        if not isinstance(ws, dict):
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message="canon.system.write_surface is missing or not a mapping",
                path="_canon.yaml",
            )
            return
        allowed = ws.get("allowed")
        if not isinstance(allowed, list) or len(allowed) == 0:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "canon.system.write_surface.allowed is empty or not a list; "
                    "declare at least one permitted path pattern"
                ),
                path="_canon.yaml",
            )
