"""DEC1 — every ``decision``-tagged integrated note has an ``authors`` field.

Governing doctrine:
``https://github.com/Battam1111/Myco/blob/main/docs/architecture/L2_DOCTRINE/extensibility.md``
§ "Per-substrate (.myco/plugins/)" — this file is a reference
implementation of the substrate-local dimension axis.

A research substrate treats "decision" as a load-bearing
classification. Every integrated note tagged ``decision`` should
name the decision's authors in its frontmatter; a decision without
attribution is forgotten context. DEC1 raises a LOW finding per
orphan decision.

Detection only. Repair is one-line frontmatter edit; automating it
would second-guess the operator.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

import yaml

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding


class DEC1DecisionAuthors(Dimension):
    """Every ``decision``-tagged integrated note has an ``authors`` field."""

    id: ClassVar[str] = "DEC1"
    category: ClassVar[Category] = Category.SEMANTIC
    default_severity: ClassVar[Severity] = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        """Yield one LOW finding per unattributed decision note."""
        integrated_dir = ctx.substrate.paths.notes / "integrated"
        if not integrated_dir.is_dir():
            return
        for note_path in integrated_dir.glob("*.md"):
            try:
                text = note_path.read_text(encoding="utf-8")
            except OSError:
                continue
            if not text.startswith("---\n"):
                continue
            end = text.find("\n---\n", 4)
            if end == -1:
                continue
            try:
                fm = yaml.safe_load(text[4:end]) or {}
            except yaml.YAMLError:
                continue
            if not isinstance(fm, dict):
                continue
            tags = fm.get("tags") or []
            if not isinstance(tags, list) or "decision" not in tags:
                continue
            if fm.get("authors"):
                continue
            rel = note_path.relative_to(ctx.substrate.root).as_posix()
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"decision note {rel} has no `authors` frontmatter — "
                    f"a decision without attribution is forgotten context"
                ),
                path=rel,
            )
