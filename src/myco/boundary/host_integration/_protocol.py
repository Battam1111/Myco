"""``symbionts._protocol`` — per-host adapter protocol (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.
v0.6.0 craft §F4 lands the protocol with full discover/install_basic/
install_deep/uninstall four-function interface.

A symbiont is a per-host integration adapter wiring Myco's manifest
verbs into one specific Agent-host environment's native extension
surface (Claude Code skills + hooks, Cursor rule files, Continue
rules, Zed slash commands, Goose recipes, etc.) without requiring
the host to know anything about Myco internals.

The protocol is intentionally minimal: each adapter is a single
Python module exposing four module-level functions:

    def discover(home: Path) -> SymbiontProbe | None
    def install_basic(probe: SymbiontProbe, substrate: Substrate, *, dry_run: bool) -> InstallReport
    def install_deep(probe: SymbiontProbe, substrate: Substrate, *, dry_run: bool) -> InstallReport
    def uninstall(probe: SymbiontProbe, *, dry_run: bool) -> UninstallReport

``install_basic`` writes the host's mcpServers config (the v0.5.x
behavior). ``install_deep`` writes additional native surface (skills,
rules, commands, recipes) — this is the v0.6.0 deep-integration
addition. ``uninstall`` removes both basic and deep artifacts.

All adapters honor R6: writes go to host config paths (outside
substrate root) which are governed by the host's own config
discipline; never to substrate paths outside `_canon.yaml::write_surface`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "SymbiontProbe",
    "InstallReport",
    "UninstallReport",
    "SYMBIONT_SIG_PREFIX",
]

#: Signature header marker written into every host-side artifact.
#: MF3 dim verifies presence + integrity. Format:
#:     # myco-symbiont-sig: <substrate_id>:<myco_version>
SYMBIONT_SIG_PREFIX: str = "# myco-symbiont-sig:"


@dataclass(frozen=True)
class SymbiontProbe:
    """Result of a host detection probe.

    ``host_id``: stable kebab-case host identifier (e.g. "claude-code",
        "cursor", "continue-dev").
    ``installed``: True if Myco can detect the host on this machine.
    ``home``: user home directory (for path-relative artifact writes).
    ``version``: optional detected host version string.
    ``capabilities``: set of native surfaces this host supports
        (e.g. ``{"hooks", "skills", "rules"}``).
    """

    host_id: str
    installed: bool
    home: Path
    version: str | None = None
    capabilities: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class InstallReport:
    """Result of an install_basic or install_deep call."""

    host_id: str
    files_written: tuple[str, ...] = ()
    files_skipped: tuple[str, ...] = ()  # already present + idempotent
    failures: tuple[dict[str, Any], ...] = ()
    dry_run: bool = False


@dataclass(frozen=True)
class UninstallReport:
    """Result of an uninstall call."""

    host_id: str
    files_removed: tuple[str, ...] = ()
    files_not_found: tuple[str, ...] = ()
    dry_run: bool = False
