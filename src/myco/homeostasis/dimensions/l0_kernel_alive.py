"""Smoke dimension proving the immune kernel is wired end-to-end.

Always emits a single LOW finding stating that the kernel ran. Has no
real purpose beyond integration testing the registry / orchestrator /
exit-policy path. Scheduled for removal when the first real mechanical
dimension lands in Stage B.8.
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["L0KernelAlive"]


class L0KernelAlive(Dimension):
    """Proves the immune kernel wired end-to-end.

    Emits one LOW finding per run. Removed at Stage B.8 when real
    mechanical dimensions arrive.
    """

    id = "L0"
    category = Category.MECHANICAL
    default_severity = Severity.LOW

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"immune kernel ran on substrate "
                f"{ctx.substrate.canon.substrate_id!r}"
            ),
        )
