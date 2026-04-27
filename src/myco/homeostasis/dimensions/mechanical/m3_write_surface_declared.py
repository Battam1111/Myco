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
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["M3WriteSurfaceDeclared"]


class M3WriteSurfaceDeclared(Dimension):
    """``system.write_surface.allowed`` must be a non-empty list."""

    fixable: ClassVar[bool] = True

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """v0.6.0 §F18 narrow fix: detect missing write_surface but defer
        write to operator; canon-shape-edits are too high-stakes for
        autofix to silently rewrite (per safety four-rule §homeostasis.md
        narrow). The fix surfaces a structured advisory.
        """
        return {
            "applied": False,
            "detail": (
                "M3 fixable=True at v0.6.0 is advisory: write_surface is "
                "high-stakes; manual edit required. See canon_schema.md "
                "for the canonical default list."
            ),
        }

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
