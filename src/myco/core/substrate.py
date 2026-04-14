"""Substrate discovery and loading.

A *substrate* is a directory containing a valid ``_canon.yaml``. This
module walks up from a starting directory to find the innermost such
directory, and bundles the resolved ``Canon`` with its ``SubstratePaths``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .canon import Canon, load_canon
from .errors import CanonSchemaError, SubstrateNotFound
from .paths import SubstratePaths

__all__ = ["Substrate", "find_substrate_root"]


def find_substrate_root(start: Path) -> Path:
    """Walk from ``start`` upward, returning the innermost substrate root.

    A directory counts as a substrate root only if ``_canon.yaml`` is
    present **and** parses under a known schema version. Unparseable
    canon files propagate as ``CanonSchemaError`` — the user gets a
    clear message rather than silent fall-through.

    Raises ``SubstrateNotFound`` if no substrate is found before the
    filesystem root.
    """
    start = start.resolve()
    candidates: list[Path] = []
    current = start if start.is_dir() else start.parent
    while True:
        candidates.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent

    for candidate in candidates:
        canon_path = candidate / "_canon.yaml"
        if not canon_path.is_file():
            continue
        # parse — propagate schema errors; a corrupt canon is a
        # substrate we found but can't use, not a miss.
        load_canon(canon_path)
        return candidate

    raise SubstrateNotFound(
        f"no _canon.yaml found walking up from {start}"
    )


@dataclass(frozen=True)
class Substrate:
    """A loaded Myco substrate: root path, canon, and canonical paths."""

    root: Path
    canon: Canon
    paths: SubstratePaths

    @classmethod
    def load(cls, root: Path) -> "Substrate":
        """Load a substrate given its root (no walk-up).

        Raises ``CanonSchemaError`` if ``root/_canon.yaml`` is missing
        or invalid.
        """
        root = root.resolve()
        canon_path = root / "_canon.yaml"
        if not canon_path.is_file():
            raise CanonSchemaError(
                f"_canon.yaml not found at substrate root: {root}"
            )
        canon = load_canon(canon_path)
        return cls(root=root, canon=canon, paths=SubstratePaths(root=root))

    @classmethod
    def discover(cls, start: Path) -> "Substrate":
        """Walk up from ``start`` and load the innermost substrate."""
        root = find_substrate_root(start)
        return cls.load(root)

    @property
    def is_skeleton(self) -> bool:
        """True iff the substrate is in auto-seeded skeleton mode.

        The immune kernel (B.2) consumes this via the canon-declared
        marker path; here we honor the default location (per
        ``canon_schema.md``: ``.myco_state/autoseeded.txt``).
        """
        return self.paths.autoseeded_marker.exists()
