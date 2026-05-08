"""Codex CLI symbiont (v0.6.0 stub).

OpenAI Codex CLI uses TOML-based config at ``~/.codex/config.toml``
with [mcp_servers.<name>] sections. The myco-install host writer
already covers the basic install. This adapter is detection-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._protocol import InstallReport, SymbiontProbe, UninstallReport

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "codex-cli"


def discover(home: Path) -> SymbiontProbe | None:
    """Probe ``home`` for an existing Codex CLI install; return SymbiontProbe or None."""
    cfg = home / ".codex" / "config.toml"
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=cfg.exists(),
        home=home,
        capabilities=frozenset({"mcp"}) if cfg.exists() else frozenset(),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write the minimal Myco MCP entry to Codex CLI's config; honor dry_run."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Like install_basic plus Codex CLI-specific extras (none beyond MCP at v0.6.0)."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove the Myco MCP entry from Codex CLI's config; honor dry_run."""
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
