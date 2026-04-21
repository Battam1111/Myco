"""MB3 — raw-notes high watermark escalation.

Companion to :class:`MB1RawNotesBacklog`. MB1 fires MEDIUM at >10
and LOW in the 1-10 band. MB3 fires HIGH at an absolute ceiling
(default 50): at that point the substrate has accumulated enough
pending state that assimilate failures silently pile up and
hunger's advice becomes noise.

Severity: HIGH when the watermark is crossed. The kernel's
default ``--severity-threshold`` of MEDIUM already gates CI at
MB1's level; MB3 raises the ladder so operators / agents see the
loud alarm at an absolute pain threshold regardless of local
tuning.

Fixable: True. ``--fix`` delegates to the shared ``reflect``
helper (same contract as MB1.fix) so one autorun drains as many
notes as possible.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["MB3RawNotesHighWatermark"]

#: Absolute ceiling on raw-notes backlog before MB3 fires HIGH.
#: Tuned to match the 500-item MCP context budget: a raw-note list
#: approaching this size swamps an ``eat --path`` preview or a
#: ``sense`` query.
_HIGH_WATERMARK: int = 50


class MB3RawNotesHighWatermark(Dimension):
    """Raw-notes backlog over the high watermark (default 50)."""

    id = "MB3"
    category = Category.METABOLIC
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        raw_dir = ctx.substrate.paths.notes / "raw"
        if not raw_dir.is_dir():
            return
        count = sum(1 for _ in raw_dir.glob("*.md"))
        if count < _HIGH_WATERMARK:
            return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"{count} raw notes in notes/raw/ (over high watermark "
                f"{_HIGH_WATERMARK}); backlog at this size makes "
                f"`sense` and `eat --path` previews unusable. Run "
                f"`myco assimilate` immediately."
            ),
            path="notes/raw",
            fixable=True,
        )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Bulk-promote raw notes via the shared ``reflect`` helper."""
        _ = finding
        from myco.digestion.assimilate import reflect

        summary = reflect(ctx=ctx)
        _promoted = summary.get("promoted", 0)
        promoted = _promoted if isinstance(_promoted, int) else 0
        errors = summary.get("errors") or []
        err_count = len(errors) if isinstance(errors, list) else 0
        if promoted > 0:
            return {
                "applied": True,
                "detail": (
                    f"assimilated {promoted} raw note(s) ({err_count} error(s))"
                ),
                "promoted": promoted,
                "errors": err_count,
            }
        return {
            "applied": False,
            "detail": f"no notes promoted ({err_count} error(s))",
            "promoted": 0,
            "errors": err_count,
        }
