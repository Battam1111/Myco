"""SE3 — substrate graph contains no self-cycles.

A node whose outgoing edge set includes itself is a one-step
cycle: the file references itself as a source-of-truth. This
usually means a copy-paste error ("references: [./this_file.md]")
or a docstring that names its own module path as the governing
doctrine. Either way it's a sign of bit-rot: the author forgot
which file they were editing.

SE3 detects; repair is operator work. Severity: LOW. A self-cycle
is a readability problem, not a correctness issue — the reference
loop does not corrupt state.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["SE3LinkSelfCycle"]


class SE3LinkSelfCycle(Dimension):
    """No substrate file references itself as a graph edge."""

    id = "SE3"
    category = Category.SEMANTIC
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Lazy import to avoid pulling circulation into the dimension
        # package import graph.
        from myco.circulation.graph import build_graph

        graph = build_graph(ctx)
        for edge in graph.edges:
            if edge.src == edge.dst:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"{edge.src} references itself "
                        f"({edge.kind} edge) — drop the self-reference."
                    ),
                    path=edge.src,
                )
