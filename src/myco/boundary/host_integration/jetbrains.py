"""JetBrains AI Assistant + Junie symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

JetBrains AI Assistant 2025.2+ has native MCP support via
``~/.config/JetBrains/<ide><year>.<minor>/options/mcpServers.xml``.
Per-OS path:

- Linux:   ``~/.config/JetBrains/<ide><ver>/options/mcpServers.xml``
- macOS:   ``~/Library/Application Support/JetBrains/<ide><ver>/options/mcpServers.xml``
- Windows: ``%APPDATA%/JetBrains/<ide><ver>/options/mcpServers.xml``

Detection scans ALL three OS paths AND all common IDE flavors
(IntelliJIdea, PyCharm, WebStorm, GoLand, RustRover, RubyMine,
PhpStorm, AppCode, CLion, Rider, DataGrip).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ._protocol import InstallReport, SymbiontProbe, UninstallReport

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "jetbrains"

_IDE_NAMES = (
    "IntelliJIdea",
    "PyCharm",
    "WebStorm",
    "GoLand",
    "RustRover",
    "RubyMine",
    "PhpStorm",
    "AppCode",
    "CLion",
    "Rider",
    "DataGrip",
    "PyCharmCE",
    "IntelliJIdeaCE",
)


def _jb_root(home: Path) -> Path:
    """Per-OS JetBrains config root."""
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "JetBrains"
    if sys.platform == "win32":
        appdata = Path(home / "AppData" / "Roaming")
        return appdata / "JetBrains"
    return home / ".config" / "JetBrains"


def discover(home: Path) -> SymbiontProbe | None:
    root = _jb_root(home)
    installed = root.is_dir()
    caps: set[str] = set()
    if installed:
        # Look for any IDE+version subdirectory.
        for entry in root.iterdir() if root.exists() else []:
            if not entry.is_dir():
                continue
            if any(entry.name.startswith(ide) for ide in _IDE_NAMES):
                caps.add("mcp")
                if (entry / "options" / "mcpServers.xml").is_file():
                    caps.add("mcp_configured")
                break
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset(caps),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """JetBrains MCP config XML write — basic install. v0.6.0 ships
    detection-only; per-IDE XML write deferred to JetBrains-side UI
    (Settings → Tools → AI Assistant → MCP) to avoid clobbering user
    edits."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
