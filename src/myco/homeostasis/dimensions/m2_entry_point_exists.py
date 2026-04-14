"""M2 — the canon-declared entry point file exists on disk.

Reads ``canon.identity.entry_point`` (default ``"MYCO.md"``) and
confirms a file at that substrate-relative path exists. A missing
entry-point file breaks the boot-brief contract (ingestion/hunger
reads it) and leaves agents without a reliable anchor page.

Severity: HIGH.
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["M2EntryPointExists"]


class M2EntryPointExists(Dimension):
    """Canon entry-point file must exist under the substrate root."""

    id = "M2"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        entry = ctx.substrate.canon.entry_point  # defaults to "MYCO.md"
        if not entry:
            return
        path = ctx.substrate.root / entry
        if not path.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"entry point {entry!r} declared in canon "
                    f"but no file found at that path"
                ),
                path=entry,
            )
