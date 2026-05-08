"""Claude Desktop symbiont (v0.6.0 stub).

Claude Desktop (the standalone Anthropic Mac/Windows/Linux app)
shares config with Cowork (claude_desktop_config.json) but does NOT
implement the Cowork plugin manifest or hooks surface. This adapter
mirrors the Cowork detection path with a simpler payload.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import cowork as _cowork
from ._protocol import InstallReport, SymbiontProbe, UninstallReport

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "claude-desktop"


def discover(home: Path) -> SymbiontProbe | None:
    """Probe ``home`` for an existing Claude Desktop install; return SymbiontProbe or None."""
    base = _cowork.discover(home)
    if base is None:
        return None
    # Re-tag as claude-desktop.
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=base.installed,
        home=base.home,
        capabilities=base.capabilities,
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write the minimal Myco MCP entry to Claude Desktop's config; honor dry_run."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Like install_basic plus Claude Desktop-specific extras (none beyond MCP at v0.6.0)."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove the Myco MCP entry from Claude Desktop's config; honor dry_run."""
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
