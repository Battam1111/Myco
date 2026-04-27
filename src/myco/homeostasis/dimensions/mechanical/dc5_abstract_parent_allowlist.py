"""DC5 — abstract-parent-allowlist sourced from canon.

Governing doctrine: replaces hardcoded ``_ABSTRACT_PARENT_NAMES`` in
``dc2_public_function_docstring.py:158`` with a canon-driven allowlist.
Per craft ``v0_5_9_immune_zero_craft_2026-04-21.md:100-102`` and v0.6.0
craft §F18.

Severity: LOW. DC5 emits when canon's ``lint.abstract_parent_allowlist``
is missing and DC2 falls back to its hardcoded 3-name set. DC5's intent
is to prompt substrate authors to declare their own ABCs.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["DC5AbstractParentAllowlist"]

#: DC2's historical hardcode (kept here for documentation; the canon
#: field replaces this when present).
_DEFAULT_ALLOWLIST: tuple[str, ...] = ("ABC", "Protocol", "TypedDict")


class DC5AbstractParentAllowlist(Dimension):
    """canon should declare lint.abstract_parent_allowlist explicitly."""

    id = "DC5"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        lint = ctx.substrate.canon.lint or {}
        allowlist = (
            lint.get("abstract_parent_allowlist") if isinstance(lint, dict) else None
        )
        if allowlist is None:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"canon.lint.abstract_parent_allowlist not declared; "
                    f"DC2 falls back to hardcoded {_DEFAULT_ALLOWLIST}"
                ),
                path="_canon.yaml",
            )
