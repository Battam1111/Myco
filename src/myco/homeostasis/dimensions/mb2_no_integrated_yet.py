"""MB2 — raw notes exist but nothing has been integrated yet.

Fires a single LOW finding when ``notes/raw/`` is non-empty and
``notes/integrated/`` contains zero files. Signals that digest has
never run in this substrate; newborn substrates that haven't ingested
anything yet (no raws either) do not trip this.

Severity: LOW.
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["MB2NoIntegratedYet"]


class MB2NoIntegratedYet(Dimension):
    """Raw notes exist but ``notes/integrated/`` is empty."""

    id = "MB2"
    category = Category.METABOLIC
    default_severity = Severity.LOW

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        notes = ctx.substrate.paths.notes
        raw_dir = notes / "raw"
        integrated_dir = notes / "integrated"
        if not raw_dir.is_dir():
            return
        raws = [p for p in raw_dir.glob("*.md") if p.is_file()]
        if not raws:
            return
        integrated = (
            [p for p in integrated_dir.glob("*.md") if p.is_file()]
            if integrated_dir.is_dir()
            else []
        )
        if integrated:
            return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"{len(raws)} raw note(s) present but notes/integrated/ "
                f"is empty; `myco digest` or `myco reflect` to promote"
            ),
            path="notes/integrated",
        )
