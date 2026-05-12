"""SH-cluster — merged dimensions (SH1, SH2).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/shipped/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = [
    "SH1PackageVersionRef",
    "SH2KernelAheadOfCanon",
]


# =========================================================================
# SH1 — see module docstring + original git history at parent commits
# =========================================================================


class SH1PackageVersionRef(Dimension):
    """If canon declares ``versioning.package_version_ref``, the file exists."""

    id = "SH1"
    category = Category.SHIPPED
    default_severity = Severity.MEDIUM

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        versioning = ctx.substrate.canon.versioning or {}
        ref = versioning.get("package_version_ref")
        if not ref:
            return  # silently skip — not every substrate ships a package
        ref_str = str(ref)
        target = ctx.substrate.root / ref_str
        if not target.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"canon.versioning.package_version_ref points to "
                    f"{ref_str!r} but no file exists there"
                ),
                path=ref_str,
            )


# =========================================================================
# SH2 — see module docstring + original git history at parent commits
# =========================================================================

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
