"""MB4 — sporulated-reabsorbed integrity.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md``
state machine ``raw → digesting → integrated → sporulated``;
v0.6.0 craft §F6 closes the loop by promoting distilled to sporulated
when consumed by a craft (fruit), and MB4 verifies the closure.

Each ``stage: sporulated`` distilled note must reference a real
doctrine document via frontmatter ``propagated_doctrine: <docpath>``.

Severity: LOW at land, ramps to MEDIUM after 30 sessions.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MB4SporulatedReabsorbed"]

_FRONTMATTER_RE: re.Pattern[str] = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_STAGE_RE: re.Pattern[str] = re.compile(r"^stage:\s*sporulated\s*$", re.MULTILINE)
_PROP_RE: re.Pattern[str] = re.compile(
    r"^propagated_doctrine:\s*(.+?)\s*$", re.MULTILINE
)


class MB4SporulatedReabsorbed(Dimension):
    """sporulated distilled notes must reference a real doctrine doc."""

    id = "MB4"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # v0.8.5 — canon-configurable notes_dir (Myco-self uses .myco/notes/).
        distilled_root = ctx.substrate.paths.notes / "distilled"
        if not distilled_root.is_dir():
            return
        for path in distilled_root.glob("*.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fm_match = _FRONTMATTER_RE.search(text)
            if not fm_match:
                continue
            fm = fm_match.group(1)
            if not _STAGE_RE.search(fm):
                continue  # not sporulated
            prop_match = _PROP_RE.search(fm)
            rel = path.relative_to(ctx.substrate.root).as_posix()
            if not prop_match:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        "distilled note marked stage=sporulated has no "
                        "propagated_doctrine: <docpath> frontmatter field"
                    ),
                    path=rel,
                )
                continue
            doctrine_path = prop_match.group(1).strip().strip("\"'")
            if not (ctx.substrate.root / doctrine_path).is_file():
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"propagated_doctrine target {doctrine_path!r} "
                        f"does not exist on disk"
                    ),
                    path=rel,
                )
