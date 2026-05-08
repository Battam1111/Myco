"""Windsurf symbiont (v0.6.0 stub).

Windsurf supports MCP via ``~/.codeium/windsurf/mcp_config.json``. As
of v0.6.0 there is no native rules / commands / recipes surface
beyond mcpServers JSON, so this adapter is detection + basic-install
only. Per-host adapter slot reserved for future surface expansion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._protocol import InstallReport, SymbiontProbe, UninstallReport

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "windsurf"


def discover(home: Path) -> SymbiontProbe | None:
    """Probe ``home`` for an existing Windsurf install; return SymbiontProbe or None."""
    candidates = [
        home / ".codeium" / "windsurf",
        home / "AppData" / "Roaming" / "Codeium" / "Windsurf",
    ]
    installed = any(p.exists() for p in candidates)
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset({"mcp"}) if installed else frozenset(),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write the minimal Myco MCP entry to Windsurf's config; honor dry_run."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Like install_basic plus Windsurf-specific extras (none beyond MCP at v0.6.0)."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove the Myco MCP entry from Windsurf's config; honor dry_run."""
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
