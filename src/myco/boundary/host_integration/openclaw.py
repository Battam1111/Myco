"""OpenClaw symbiont (v0.6.0 stub).

OpenClaw provides a CLI for adding MCP servers. The myco-install
host writer shells out to it. This adapter is detection-only.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ._protocol import InstallReport, SymbiontProbe, UninstallReport

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "openclaw"


def discover(home: Path) -> SymbiontProbe | None:
    installed = shutil.which("openclaw") is not None
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset({"mcp"}) if installed else frozenset(),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
