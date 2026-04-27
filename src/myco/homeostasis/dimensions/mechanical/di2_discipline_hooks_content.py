"""DI2 — discipline-hooks content present (R1 + R2 hook lines).

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md``
R1 + R2 mechanical-enforcement table; DI1 ensures
``hooks/hooks.json`` exists when ``.claude/`` is declared, DI2
verifies the file's content matches R1/R2 expectations.

Severity: LOW at land, ramps to MEDIUM after 30 sessions.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["DI2DisciplineHooksContent"]


class DI2DisciplineHooksContent(Dimension):
    """hooks.json must include SessionStart→hunger and PreCompact→senesce lines."""

    id = "DI2"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        hooks_path = root / "hooks" / "hooks.json"
        if not hooks_path.is_file():
            return
        try:
            data = json.loads(hooks_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=f"hooks.json failed to parse: {exc}",
                path="hooks/hooks.json",
            )
            return
        text = json.dumps(data) if isinstance(data, dict | list) else str(data)
        # R1: SessionStart fires hunger.
        if "SessionStart" not in text or "hunger" not in text:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "hooks.json does not bind SessionStart → myco hunger "
                    "(R1 boot ritual)"
                ),
                path="hooks/hooks.json",
            )
        # R2: PreCompact fires senesce.
        if "PreCompact" not in text or "senesce" not in text:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "hooks.json does not bind PreCompact → myco senesce "
                    "(R2 session-end ritual)"
                ),
                path="hooks/hooks.json",
            )
