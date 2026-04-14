"""Canonical paths within a substrate.

Pure functions of the substrate root. No I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = ["SubstratePaths"]


@dataclass(frozen=True)
class SubstratePaths:
    """The canonical directory/file layout of a Myco substrate.

    Every path is absolute and derived from ``root``. Whether a path
    *exists* on disk is a separate question — callers check as needed.
    """

    root: Path

    @property
    def canon(self) -> Path:
        """``_canon.yaml`` — the substrate's L4 single source of truth."""
        return self.root / "_canon.yaml"

    @property
    def notes(self) -> Path:
        """``notes/`` — where ingested + digested notes live."""
        return self.root / "notes"

    @property
    def docs(self) -> Path:
        """``docs/`` — the doctrine and primordia tree."""
        return self.root / "docs"

    @property
    def state(self) -> Path:
        """``.myco_state/`` — runtime state (not source of truth)."""
        return self.root / ".myco_state"

    @property
    def autoseeded_marker(self) -> Path:
        """Skeleton-mode marker consumed by the immune kernel."""
        return self.state / "autoseeded.txt"

    @property
    def boot_brief(self) -> Path:
        """Session boot brief written by ``myco hunger``."""
        return self.state / "boot_brief.md"

    @property
    def entry_point(self) -> Path:
        """Default agent entry page.

        The *actual* entry point comes from ``canon.identity.entry_point``;
        this property exposes the default (``MYCO.md``). The canon-
        driven version is resolved in ``Substrate.load``.
        """
        return self.root / "MYCO.md"
