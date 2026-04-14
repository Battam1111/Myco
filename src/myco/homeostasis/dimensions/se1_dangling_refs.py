"""SE1 — dangling references in the substrate graph.

Uses ``myco.circulation.build_graph`` and emits one MEDIUM finding per
edge whose destination does not resolve to an existing file under the
substrate root. External URLs are skipped by the graph builder and
never appear here.

Severity: MEDIUM — dangling refs are a correctness concern (readers
hit 404s) but don't corrupt state.
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["SE1DanglingRefs"]


class SE1DanglingRefs(Dimension):
    """One finding per dangling edge in the substrate graph."""

    id = "SE1"
    category = Category.SEMANTIC
    default_severity = Severity.MEDIUM

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Lazy import: keeps dimensions/__init__ cheap and breaks any
        # potential cycle if circulation reaches back into homeostasis.
        from myco.circulation.graph import build_graph

        graph = build_graph(ctx)
        root = ctx.substrate.root.resolve()
        for edge in graph.edges:
            target = root / edge.dst
            if target.exists():
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"{edge.src} references missing {edge.dst} "
                    f"({edge.kind})"
                ),
                path=edge.src,
            )
