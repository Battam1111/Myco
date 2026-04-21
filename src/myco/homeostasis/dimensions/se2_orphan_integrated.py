"""SE2 — integrated notes with no inbound references.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (semantic / LOW).

An integrated note (``notes/integrated/*.md``) that nothing else
references is likely forgotten knowledge. Emits one LOW finding per
orphan.

Severity: LOW — orphans are a maintenance signal, not an error. A
fresh substrate with zero integrated notes never fires this.
"""

from __future__ import annotations

from collections.abc import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["SE2OrphanIntegrated"]


class SE2OrphanIntegrated(Dimension):
    """Integrated notes with no inbound edges in the graph."""

    id = "SE2"
    category = Category.SEMANTIC
    default_severity = Severity.LOW

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        from myco.circulation.graph import build_graph

        integrated_dir = ctx.substrate.paths.notes / "integrated"
        if not integrated_dir.is_dir():
            return
        integrated = [p for p in integrated_dir.glob("*.md") if p.is_file()]
        if not integrated:
            return

        graph = build_graph(ctx)
        referenced = {edge.dst for edge in graph.edges}
        root = ctx.substrate.root

        for note_path in integrated:
            rel = note_path.relative_to(root).as_posix()
            if rel in referenced:
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=f"integrated note {rel} has no inbound references",
                path=rel,
            )
