"""M1 — canon identity fields present and non-empty.

Checks that ``_canon.yaml::identity`` carries a non-empty
``substrate_id`` and ``entry_point``. The canon parser (Stage B.1)
requires ``identity`` to be present and non-empty as a mapping, but
does not force any particular key inside it. This dimension closes
that gap.

Severity: HIGH (a substrate that can't name itself or point at its
entry page is not usable by the agent surface).
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["M1CanonIdentityFields"]


class M1CanonIdentityFields(Dimension):
    """``identity.substrate_id`` and ``identity.entry_point`` non-empty."""

    id = "M1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        identity = ctx.substrate.canon.identity
        for key in ("substrate_id", "entry_point"):
            val = identity.get(key)
            if val is None or str(val).strip() == "":
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=f"canon.identity.{key} is missing or empty",
                    path="_canon.yaml",
                )
