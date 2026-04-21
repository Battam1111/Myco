"""Canonical paths within a substrate.

Governing doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
(the canon declares ``system.write_surface.allowed`` globs against
which these canonical paths are matched).

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
    def graph_cache(self) -> Path:
        """``.myco_state/graph.json`` — persisted circulation graph.

        The graph cache is written by :func:`myco.circulation.graph.build_graph`
        when ``use_cache=True`` (the default) and read on the next call as
        long as the canon + src fingerprint matches. Lives under
        ``.myco_state/`` because it's runtime state, not source of truth —
        safe to delete at any time (next ``build_graph`` rebuilds).
        """
        return self.state / "graph.json"

    @property
    def entry_point(self) -> Path:
        """Default agent entry page.

        The *actual* entry point comes from ``canon.identity.entry_point``;
        this property exposes the default (``MYCO.md``). The canon-
        driven version is resolved in ``Substrate.load``.
        """
        return self.root / "MYCO.md"

    # --- v0.5.3 substrate-local plugin surface ---
    # Governing doctrine: docs/architecture/L2_DOCTRINE/homeostasis.md
    # (substrate-local plugin health) and
    # docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md.

    @property
    def local_plugins_dir(self) -> Path:
        """``.myco/plugins/`` — substrate-local plugin package root."""
        return self.root / ".myco" / "plugins"

    @property
    def local_plugins_init(self) -> Path:
        """``.myco/plugins/__init__.py`` — the entry-point importer."""
        return self.root / ".myco" / "plugins" / "__init__.py"

    @property
    def manifest_overlay(self) -> Path:
        """``.myco/manifest_overlay.yaml`` — per-substrate verb overlay."""
        return self.root / ".myco" / "manifest_overlay.yaml"
