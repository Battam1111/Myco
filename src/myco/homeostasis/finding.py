"""Finding type emitted by lint dimensions.

See ``docs/architecture/L1_CONTRACT/exit_codes.md`` for the four-
category taxonomy and the severity ladder.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from myco.core.severity import Severity

__all__ = ["Category", "Finding"]


class Category(str, Enum):
    """The four lint-dimension categories from L1 exit_codes.md."""

    MECHANICAL = "mechanical"
    SHIPPED = "shipped"
    METABOLIC = "metabolic"
    SEMANTIC = "semantic"

    @classmethod
    def from_name(cls, name: str) -> Category:
        """Parse a category name (case-insensitive) into a ``Category``.

        Raises ``ValueError`` with the offending input echoed back
        on any name that's not one of the four canonical categories.
        """
        try:
            return cls(name.lower())
        except ValueError as exc:
            raise ValueError(f"unknown category: {name!r}") from exc


@dataclass(frozen=True)
class Finding:
    """A single lint finding emitted by one dimension.

    ``path`` is stored as ``str | None`` rather than ``Path | None`` to
    avoid platform-dependent hashing surprises and to keep ``Finding``
    trivially serializable for ``--json`` output in Stage B.7.
    """

    dimension_id: str
    category: Category
    severity: Severity
    message: str
    path: str | None = None
    line: int | None = None
    fixable: bool = False  # consumed by auto-fix; no dimension declares
    # itself fixable at B.2 (first fixable dim in B.8)

    @classmethod
    def from_path(
        cls,
        *,
        dimension_id: str,
        category: Category,
        severity: Severity,
        message: str,
        path: Path | None = None,
        line: int | None = None,
        fixable: bool = False,
    ) -> Finding:
        """Ergonomic constructor that accepts a ``Path`` instead of a string."""
        return cls(
            dimension_id=dimension_id,
            category=category,
            severity=severity,
            message=message,
            path=str(path) if path is not None else None,
            line=line,
            fixable=fixable,
        )
