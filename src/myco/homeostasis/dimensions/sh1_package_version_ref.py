"""SH1 — declared package-version ref resolves to an existing file.

If ``canon.versioning.package_version_ref`` is declared, the file at
that substrate-relative path must exist. Silently no-ops when
``versioning`` is absent from the canon — not every substrate ships a
Python package, and the dimension refuses to manufacture a grievance.

Severity: MEDIUM. A missing version file breaks release tooling but
not substrate integrity.
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["SH1PackageVersionRef"]


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
