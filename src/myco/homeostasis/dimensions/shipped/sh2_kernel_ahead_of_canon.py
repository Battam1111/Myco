"""SH2 — kernel version is at least canon contract version.

Governing doctrine: ``docs/architecture/L1_CONTRACT/versioning.md``
defense-against-ahead-of-kernel-canon. v0.6.0 mechanical anchor.

If a substrate's ``contract_version`` exceeds the running kernel's
``__version__``, the canon was bumped by a newer kernel and is being
read by an older one. SH2 prevents the older kernel from silently
writing v(N) shape while reading v(N+1) substrate — a common drift
when users pin Myco to an older release.

Severity: LOW at land, ramps to HIGH after 30 sessions.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["SH2KernelAheadOfCanon"]

_VERSION_RE: re.Pattern[str] = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def _parse(v: str) -> tuple[int, int, int] | None:
    m = _VERSION_RE.match(v.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


class SH2KernelAheadOfCanon(Dimension):
    """Canon contract_version must not exceed kernel __version__."""

    id = "SH2"
    category = Category.SHIPPED
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        from myco import __version__ as kernel_version

        canon_version = ctx.substrate.canon.contract_version
        kparts = _parse(kernel_version)
        cparts = _parse(canon_version)
        if kparts is None or cparts is None:
            return
        if cparts > kparts:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"canon contract_version {canon_version!r} exceeds "
                    f"running kernel __version__ {kernel_version!r}; "
                    f"upgrade kernel before continuing to write canon"
                ),
                path="_canon.yaml",
            )
