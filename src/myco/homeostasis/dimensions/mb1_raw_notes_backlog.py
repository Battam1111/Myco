"""MB1 — raw-notes backlog.

Counts ``notes/raw/*.md`` and emits a single finding sized by the
backlog. >10 files is MEDIUM; 1-10 is LOW; empty is silent.

Severity default is MEDIUM; the dimension downgrades to LOW when the
count is within the soft band. Reflect is the primary backpressure —
this dimension only surfaces that the queue has grown.

v0.5.5 — **fixable**. ``myco immune --fix`` triggers an implicit
bulk-assimilate pass (``myco.digestion.assimilate.reflect(ctx=ctx)``)
and reports how many notes were promoted. The fix is narrow: it
shells nothing out, promotes whatever ``reflect`` promotes, and
never retries individual errors — they're surfaced in the fix entry
so the user can see what the queue rejected.
"""

from __future__ import annotations

from typing import Any, ClassVar, Iterable

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

    #: v0.5.5 — MB1 delegates to :func:`myco.digestion.assimilate.reflect`
    #: to drain the raw-notes backlog in place. See :meth:`fix`.
    fixable: ClassVar[bool] = True

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

    def fix(
        self, ctx: MycoContext, finding: Finding
    ) -> dict[str, Any]:
        """Bulk-promote raw notes by calling ``reflect`` in-process.

        Narrow contract (v0.5.5):

        - Does **not** shell out to ``myco reflect`` — calls the
          Python API directly so the fix is deterministic and can
          surface per-note errors without scraping stdout.
        - Promotes whatever ``reflect`` decides to promote; this
          dimension does not second-guess the pipeline.
        - Reports back promoted / already-integrated / error counts
          in the fix entry (exposed via ``**outcome`` extras in
          :func:`myco.homeostasis.kernel._apply_fix`).
        - ``applied`` is True iff at least one note was promoted.
          An empty raw dir (should be impossible if MB1 fired, but
          harmless) or an all-errors run reports ``applied=False``.
        """
        # Imported here rather than at module top-level to keep
        # ``myco.homeostasis.dimensions`` importable before the
        # digestion subsystem has loaded (and to keep the dimension
        # module cheap for ``myco immune --list``).
        from myco.digestion.assimilate import reflect

        summary = reflect(ctx=ctx)
        promoted = int(summary.get("promoted", 0))
        already = int(summary.get("already_integrated", 0))
        errors = summary.get("errors") or []
        err_count = len(errors) if isinstance(errors, list) else 0

        if promoted > 0:
            detail = (
                f"assimilated {promoted} raw note(s)"
                + (
                    f" ({already} already-integrated, {err_count} error(s))"
                    if (already or err_count)
                    else ""
                )
            )
            return {
                "applied": True,
                "detail": detail,
                "promoted": promoted,
                "already_integrated": already,
                "errors": err_count,
            }

        # Nothing promoted — either the queue was empty by the time we
        # got here (unlikely race), or every candidate errored. Either
        # way, not counted as an applied fix.
        detail = (
            f"no notes promoted "
            f"({already} already-integrated, {err_count} error(s))"
        )
        return {
            "applied": False,
            "detail": detail,
            "promoted": 0,
            "already_integrated": already,
            "errors": err_count,
        }
