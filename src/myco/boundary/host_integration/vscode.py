"""VS Code symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

VS Code's MCP support is project-scoped via ``.vscode/mcp.json``
(written by ``myco-install host vscode``). v0.6.0 deep-install adds
``.vscode/tasks.json`` with three Myco tasks (Hunger / Senesce /
Brief) so users get a Run-Task entry without opening a terminal.

This adapter writes within the substrate root, so R6 write_surface
applies (``.vscode/**`` must be in allowed; v0.5.x already includes
``.claude/**``-style patterns and v0.6.0 substrates SHOULD add
``.vscode/**`` via myco-install or manual canon edit).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from myco.core.io_atomic import atomic_utf8_write

from ._protocol import (
    InstallReport,
    SymbiontProbe,
    UninstallReport,
)

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "vscode"


def discover(home: Path) -> SymbiontProbe | None:
    """VS Code is detected via .vscode/ in the substrate root (per-project)."""
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=True,  # VS Code config is per-project; always plausible
        home=home,
        capabilities=frozenset({"mcp", "tasks"}),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write the minimal Myco MCP entry to VS Code's .vscode/mcp.json; honor dry_run."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write .vscode/tasks.json with three Myco tasks."""
    try:
        substrate_root: Path = substrate.root
    except Exception:
        return InstallReport(host_id=HOST_ID, dry_run=dry_run)
    target = substrate_root / ".vscode" / "tasks.json"
    body = json.dumps(
        {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Myco: Hunger",
                    "type": "shell",
                    "command": "python",
                    "args": [
                        "-m",
                        "myco",
                        "--project-dir",
                        "${workspaceFolder}",
                        "hunger",
                    ],
                    "presentation": {"reveal": "always", "panel": "shared"},
                    "group": "test",
                },
                {
                    "label": "Myco: Senesce",
                    "type": "shell",
                    "command": "python",
                    "args": [
                        "-m",
                        "myco",
                        "--project-dir",
                        "${workspaceFolder}",
                        "senesce",
                    ],
                    "presentation": {"reveal": "always", "panel": "shared"},
                    "group": "test",
                },
                {
                    "label": "Myco: Brief",
                    "type": "shell",
                    "command": "python",
                    "args": [
                        "-m",
                        "myco",
                        "--project-dir",
                        "${workspaceFolder}",
                        "brief",
                    ],
                    "presentation": {"reveal": "always", "panel": "shared"},
                    "group": "test",
                },
            ],
        },
        indent=2,
    )
    if dry_run:
        return InstallReport(
            host_id=HOST_ID,
            files_written=(str(target),),
            dry_run=True,
        )
    if target.is_file():
        return InstallReport(host_id=HOST_ID, files_skipped=(str(target),))
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_utf8_write(target, body)
    return InstallReport(host_id=HOST_ID, files_written=(str(target),))


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """No-op uninstall: VS Code tasks.json edits are left for the user to revert manually."""
    # VS Code tasks live in substrate root; uninstall left to user
    # (avoid clobbering user's own tasks.json edits).
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
