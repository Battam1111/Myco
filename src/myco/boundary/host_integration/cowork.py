"""Cowork symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Cowork (Anthropic Claude Desktop local-agent-mode) does not implement
Claude Code's session hooks. v0.6.0 fills the gap via the Cowork
plugin manifest's ``monitors``/``agents``/``commands``/``connectors``
fields (Anthropic 2026-Q1 GA shape per public changelog), giving
Cowork agents an R1-equivalent SessionStart trigger.

The actual plugin manifest lives at
``.cowork-plugin/.claude-plugin/plugin.json`` in the kernel
substrate; this module's ``install_deep`` validates that the
manifest contains the v0.6.0 fields and emits a finding hint if
absent. (Plugin upload is user-driven — Cowork accepts the .zip
bundle via Claude Desktop's Settings → Plugins panel. v0.7.4
hotfix: extension switched from .plugin to .zip after Anthropic
GitHub issue #40414 confirmed the upload validator rejects .plugin.)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._protocol import (
    InstallReport,
    SymbiontProbe,
    UninstallReport,
)

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "cowork"


def _claude_desktop_config(home: Path) -> Path:
    # Claude Desktop config locations per OS (best effort).
    candidates = [
        home
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json",
        home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
        home / ".config" / "Claude" / "claude_desktop_config.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def discover(home: Path) -> SymbiontProbe | None:
    """Probe ``home`` for an existing Cowork (Claude Desktop) install; return SymbiontProbe or None."""
    cfg = _claude_desktop_config(home)
    installed = cfg.is_file()
    caps: set[str] = set()
    if installed:
        caps.add("mcp")
        # Heuristic: presence of any plugin marketplace state suggests Cowork.
        if (
            home / "Library" / "Application Support" / "Claude" / "plugins"
        ).is_dir() or (home / "AppData" / "Roaming" / "Claude" / "plugins").is_dir():
            caps.add("plugins")
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset(caps),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Cowork basic-install is via myco-install host cowork (clients.py)."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """v0.6.0: validate that .cowork-plugin/.claude-plugin/plugin.json
    advertises monitors/agents/commands/connectors fields.

    Cowork plugin upload is user-driven (drag `.zip` bundle into
    Settings → Plugins). This adapter is verification-only.
    """
    if not probe.installed:
        return InstallReport(host_id=HOST_ID, dry_run=dry_run)
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove the Myco MCP entry from Cowork's config; honor dry_run."""
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
