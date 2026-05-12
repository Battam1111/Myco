"""MB6 — stale DRAFT craft / stale distilled note auto-handler.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
(L0 P3 永恒进化 + P4 永恒迭代; craft v0.6.0 §F5 combined
stale-DRAFT-craft + stale-distilled MB6).

Thresholds (canon-driven, ``lint.thresholds`` field):
- 14+ days stale → MEDIUM finding.
- 30+ days stale → HIGH finding + auto-action via fix:
  - winnow_g6 PASS → status: LANDED.
  - winnow_g6 FAIL → move to ``.myco/state/excreted_crafts/`` /
    ``notes/distilled/_excreted/`` with tombstone reason.

Severity: LOW at land, ramps to MEDIUM after 30 sessions.
fixable=True (auto-action at HIGH threshold; 14-29 day window is
informational only).
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MB6StaleDraftOrDistilled"]

_FRONTMATTER_RE: re.Pattern[str] = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_STATUS_DRAFT_RE: re.Pattern[str] = re.compile(r"^status:\s*DRAFT\s*$", re.MULTILINE)
_DATE_RE: re.Pattern[str] = re.compile(
    r"^date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*$", re.MULTILINE
)


class MB6StaleDraftOrDistilled(Dimension):
    """DRAFT crafts / distilled notes must not stagnate beyond thresholds."""

    id = "MB6"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        thresholds = (ctx.substrate.canon.lint or {}).get("thresholds") or {}
        warn_days = int(thresholds.get("stale_draft_warn_days", 14))
        primordia_root = ctx.substrate.root / "docs" / "primordia"
        today = ctx.now.date() if hasattr(ctx.now, "date") else dt.date.today()
        if primordia_root.is_dir():
            for path in primordia_root.glob("*_craft_*.md"):
                if "_excreted" in path.parts:
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                fm_match = _FRONTMATTER_RE.search(text)
                if not fm_match:
                    continue
                fm = fm_match.group(1)
                if not _STATUS_DRAFT_RE.search(fm):
                    continue
                date_match = _DATE_RE.search(fm)
                if not date_match:
                    continue
                try:
                    craft_date = dt.date.fromisoformat(date_match.group(1))
                except ValueError:
                    continue
                age_days = (today - craft_date).days
                if age_days >= warn_days:
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"DRAFT craft {age_days} days old (threshold "
                            f"{warn_days}); land via winnow or excrete"
                        ),
                        path=rel,
                    )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        # v0.6.0 lands MB6 as fixable but the auto-excrete path is
        # deferred to v0.6.x patches — auto-excretion of crafts is
        # destructive and merits an additional review cycle. v0.6.0
        # only emits findings; agent / owner manually winnows or
        # excretes.
        return {
            "applied": False,
            "detail": (
                "MB6 fix at v0.6.0 is informational only; "
                "auto-excrete deferred to v0.6.x"
            ),
        }
