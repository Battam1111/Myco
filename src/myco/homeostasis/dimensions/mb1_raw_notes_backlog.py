"""MB1 — raw-notes backlog.

Counts ``notes/raw/*.md`` and emits a single finding sized by the
backlog. >10 files is MEDIUM; 1-10 is LOW; empty is silent.

Severity default is MEDIUM; the dimension downgrades to LOW when the
count is within the soft band. Reflect is the primary backpressure —
this dimension only surfaces that the queue has grown.
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["MB1RawNotesBacklog"]


_BACKLOG_MEDIUM_THRESHOLD = 10


class MB1RawNotesBacklog(Dimension):
    """``notes/raw/`` backlog; >10 files is MEDIUM, 1-10 is LOW."""

    id = "MB1"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        raw_dir = ctx.substrate.paths.notes / "raw"
        if not raw_dir.is_dir():
            return
        raws = [p for p in raw_dir.glob("*.md") if p.is_file()]
        n = len(raws)
        if n == 0:
            return
        if n > _BACKLOG_MEDIUM_THRESHOLD:
            severity = Severity.MEDIUM
            msg = (
                f"{n} raw notes in notes/raw/ (over threshold "
                f"{_BACKLOG_MEDIUM_THRESHOLD}); run `myco reflect`"
            )
        else:
            severity = Severity.LOW
            msg = f"{n} raw note(s) in notes/raw/ pending digest"
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=severity,
            message=msg,
            path="notes/raw",
        )
