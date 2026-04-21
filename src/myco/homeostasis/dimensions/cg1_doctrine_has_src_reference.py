"""CG1 — every L2 doctrine page is referenced by at least one src module.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


L2 doctrine pages (``docs/architecture/L2_DOCTRINE/*.md``) describe
subsystems; every page that describes a real subsystem must have at
least one ``code_doc_ref`` edge landing at it (from
:mod:`myco.circulation.graph_src`). A doctrine page with no
incoming code edge is either:

- aspirational doctrine (the subsystem is planned, not built), or
- bit-rotted doctrine (the subsystem was renamed or removed and
  the doctrine page was left orphaned).

Either way it is worth surfacing at LOW severity: the agent
reading doctrine cannot navigate down to implementation, which
weakens L0 principle "万物互联" (everything connected).

Severity: LOW. Detection-only — creating fake references would
make the problem worse, not better. Operator repair.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["CG1DoctrineHasSrcReference"]


_L2_DIR = "docs/architecture/L2_DOCTRINE"


class CG1DoctrineHasSrcReference(Dimension):
    """Every L2 doctrine page has at least one ``code_doc_ref`` edge."""

    id = "CG1"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        l2_dir = ctx.substrate.root / _L2_DIR
        if not l2_dir.is_dir():
            return
        # Collect the L2 pages present on disk.
        pages: set[str] = set()
        for md in l2_dir.rglob("*.md"):
            try:
                rel = md.relative_to(ctx.substrate.root).as_posix()
            except ValueError:
                continue
            pages.add(rel)
        if not pages:
            return
        # Build the graph once; extract destinations of ``code_doc_ref``
        # edges. Lazy import so the dimension registry stays cheap.
        from myco.circulation.graph import build_graph

        graph = build_graph(ctx)
        referenced = {e.dst for e in graph.edges if e.kind == "code_doc_ref"}
        for page in sorted(pages):
            if page in referenced:
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"L2 doctrine page {page} has no incoming "
                    f"`code_doc_ref` edge — either the subsystem is "
                    f"aspirational (state this) or the reference was "
                    f"lost in a refactor (restore from src docstrings)."
                ),
                path=page,
            )
