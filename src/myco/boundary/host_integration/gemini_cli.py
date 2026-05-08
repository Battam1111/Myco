"""Gemini CLI symbiont (v0.6.0 stub).

Google Gemini CLI uses ``~/.config/gemini-cli/config.json``.
Detection-only adapter; basic install handled by myco-install.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._protocol import InstallReport, SymbiontProbe, UninstallReport

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "gemini-cli"


def discover(home: Path) -> SymbiontProbe | None:
    """Probe ``home`` for an existing Gemini CLI install; return SymbiontProbe or None."""
    cfg = home / ".config" / "gemini-cli" / "config.json"
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=cfg.exists(),
        home=home,
        capabilities=frozenset({"mcp"}) if cfg.exists() else frozenset(),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write the minimal Myco MCP entry to Gemini CLI's config; honor dry_run."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Like install_basic plus Gemini CLI-specific extras (none beyond MCP at v0.6.0)."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove the Myco MCP entry from Gemini CLI's config; honor dry_run."""
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
