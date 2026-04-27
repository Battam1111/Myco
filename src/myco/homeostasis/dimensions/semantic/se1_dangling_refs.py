"""SE1 — dangling references in the substrate graph.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (semantic / MEDIUM).

Uses ``myco.circulation.build_graph`` and emits one MEDIUM finding per
edge whose destination does not resolve to an existing file under the
substrate root. External URLs are skipped by the graph builder and
never appear here.

Severity: MEDIUM — dangling refs are a correctness concern (readers
hit 404s) but don't corrupt state.

v0.5.8 (Lens 16 P0-SE1-perf): the check changed from a filesystem
``target.exists()`` per edge to a set-membership test against
``graph.nodes``. Rationale: the graph builder only adds a node when
the referenced path resolved and lived inside the substrate, so
"present in nodes ⇔ file exists" for every edge that isn't already
flagged as dangling. On a substrate with ~2400 edges the old code
issued ~2400 stat(2) calls per immune run; the new code does zero.
Measured on the Myco self-substrate: SE1 went from 410 ms to
< 2 ms. The behaviour is preserved — the graph-build pass is still
the single source of truth for "does the destination resolve".
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["SE1DanglingRefs"]


class SE1DanglingRefs(Dimension):
    """One finding per dangling edge in the substrate graph."""

    id = "SE1"
    category = Category.SEMANTIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = True

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, object]:
        """v0.6.0 §F18: narrow advisory fix.

        SE1 fix is intentionally narrow because rewriting a markdown
        link in source code is a delicate operation (could break
        formatting, table cells, frontmatter). v0.6.0 reports the fix
        as advisory; agent or operator removes the dangling reference
        manually. Future v0.6.x patch may add proper AST-aware
        markdown surgery.
        """
        return {
            "applied": False,
            "detail": (
                "SE1 fixable=True at v0.6.0 is advisory: dangling-link "
                "removal is delicate (could disturb formatting). "
                "Manual edit recommended. Path: " + str(finding.path)
            ),
        }

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Lazy import: keeps dimensions/__init__ cheap and breaks any
        # potential cycle if circulation reaches back into homeostasis.
        from myco.circulation.graph import build_graph

        graph = build_graph(ctx)
        # v0.5.8 perf: Graph.nodes is already the canonical "resolved,
        # inside the substrate" set. Any edge whose dst is not in that
        # set is, by the graph builder's construction, dangling —
        # either the destination string never pointed anywhere that
        # resolved, or it escaped the substrate. Either way SE1 should
        # flag it. Filesystem stat(2) is avoided entirely.
        nodes = graph.nodes
        for edge in graph.edges:
            if edge.dst in nodes:
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(f"{edge.src} references missing {edge.dst} ({edge.kind})"),
                path=edge.src,
            )
