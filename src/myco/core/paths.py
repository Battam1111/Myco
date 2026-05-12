"""Canonical paths within a substrate.

Governing doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
(the canon declares ``system.write_surface.allowed`` globs against
which these canonical paths are matched).

Pure functions of the substrate root, plus a small set of
discovery helpers (``find_substrate_canon`` / ``has_substrate``) that
do touch the filesystem — kept here as the canonical resolution
point for the v0.8.4+ dual-location canon layout.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = ["SubstratePaths", "find_substrate_canon", "has_substrate"]


# v0.8.4 root-cleanup (2026-05-12): canon file relocated from
# `<root>/_canon.yaml` (visible top-level file) to `<root>/.myco/canon.yaml`
# (consolidated under the .myco/ Myco-internal parent). The two helpers
# below are the SSoT for resolving the canon path at runtime; every
# subsystem (substrate loader, MCP workspace discovery, auth helpers,
# graph builder, propagate, molt) goes through these instead of
# hardcoding either filename.
#
# Resolution order: .myco/canon.yaml (new) wins; _canon.yaml (legacy)
# is the fallback so downstream substrates that haven't migrated keep
# working unchanged. germinate templates emit the legacy filename by
# default so new substrates start at the conservative location; the
# Myco-self substrate explicitly opts into the new layout.
_CANON_CANDIDATES: tuple[str, ...] = (".myco/canon.yaml", "_canon.yaml")


def find_substrate_canon(root: Path) -> Path:
    """Return the canon file path for a substrate root.

    Tries ``.myco/canon.yaml`` first (v0.8.4+ layout); falls back to
    ``_canon.yaml`` (legacy / downstream substrates). Returns the new
    path even when neither exists (caller can ``is_file()``-check the
    result for graceful "not a substrate" handling).
    """
    for filename in _CANON_CANDIDATES:
        p = root / filename
        if p.is_file():
            return p
    # Neither exists — return the new-layout path so callers that
    # raise a clear error mention the canonical location.
    return root / _CANON_CANDIDATES[0]


def has_substrate(root: Path) -> bool:
    """True when ``root`` contains a Myco canon (either layout)."""
    return any((root / fn).is_file() for fn in _CANON_CANDIDATES)


@dataclass(frozen=True)
class SubstratePaths:
    """The canonical directory/file layout of a Myco substrate.

    Every path is absolute and derived from ``root``. Whether a path
    *exists* on disk is a separate question — callers check as needed.

    v0.8.4 root-cleanup (2026-05-12): the canon filename is now a
    constructor parameter so substrates on the new ``.myco/canon.yaml``
    layout and substrates on the legacy ``_canon.yaml`` layout share
    the same paths object. ``Substrate.load`` determines which layout
    the substrate uses (via :func:`find_substrate_canon`) and passes
    the resolved relative path here.
    """

    root: Path
    canon_filename: str = "_canon.yaml"
    # v0.8.4 root-cleanup (2026-05-12): notes_dir is canon-configurable.
    # Defaults to "notes" (downstream substrates unchanged); Myco-self
    # declares `system.notes_dir: ".myco/notes"` in canon, which
    # Substrate.load propagates here.
    notes_dir: str = "notes"

    @property
    def canon(self) -> Path:
        """The substrate's L4 single source of truth.

        Default is the legacy ``_canon.yaml`` at root; Myco-self (and
        any v0.8.4+-layout substrate) sets this to
        ``.myco/canon.yaml`` via the ``canon_filename`` ctor arg.
        """
        return self.root / self.canon_filename

    @property
    def notes(self) -> Path:
        """Substrate notes tree (raw/integrated/distilled).

        Default ``notes/`` at root; Myco-self overrides to
        ``.myco/notes/`` via canon ``system.notes_dir``.
        """
        return self.root / self.notes_dir

    @property
    def docs(self) -> Path:
        """``docs/`` — the doctrine and primordia tree."""
        return self.root / "docs"

    @property
    def state(self) -> Path:
        """``.myco/state/`` — runtime state (not source of truth)."""
        return self.root / ".myco/state"

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
        """``.myco/state/graph.json`` — persisted circulation graph.

        The graph cache is written by :func:`myco.circulation.graph.build_graph`
        when ``use_cache=True`` (the default) and read on the next call as
        long as the canon + src fingerprint matches. Lives under
        ``.myco/state/`` because it's runtime state, not source of truth —
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
