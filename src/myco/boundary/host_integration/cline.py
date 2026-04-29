"""Cline symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Cline (cline.bot) supports MCP servers via its v3.4 MCP Marketplace.
Detection looks for the VS Code extension storage path. Deep-install
writes a Cline-specific ``.clinerules/myco.md`` file with R1-R7
priming.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from myco.core.io_atomic import atomic_utf8_write

from ._protocol import (
    SYMBIONT_SIG_PREFIX,
    InstallReport,
    SymbiontProbe,
    UninstallReport,
)

__all__ = ["HOST_ID", "discover", "install_basic", "install_deep", "uninstall"]

HOST_ID = "cline"


def discover(home: Path) -> SymbiontProbe | None:
    cline_paths = [
        home / ".vscode" / "extensions",
        home / ".vscode-server" / "extensions",
        home
        / "AppData"
        / "Roaming"
        / "Code"
        / "User"
        / "globalStorage"
        / "saoudrizwan.claude-dev",
    ]
    installed = any(p.exists() for p in cline_paths)
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset({"mcp", "rules"}) if installed else frozenset(),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write substrate-local .clinerules/myco.md with R1-R7 priming."""
    if not probe.installed:
        return InstallReport(host_id=HOST_ID, dry_run=dry_run)
    try:
        substrate_root: Path = substrate.root
        substrate_id = substrate.canon.substrate_id
    except Exception:
        return InstallReport(host_id=HOST_ID, dry_run=dry_run)
    target = substrate_root / ".clinerules" / "myco.md"
    sig = f"{SYMBIONT_SIG_PREFIX} {substrate_id}:0.6.0\n"
    body = sig + _RULE_BODY
    if dry_run:
        return InstallReport(
            host_id=HOST_ID, files_written=(str(target),), dry_run=True
        )
    if target.is_file():
        try:
            existing = target.read_text(encoding="utf-8")
            if SYMBIONT_SIG_PREFIX in existing:
                return InstallReport(host_id=HOST_ID, files_skipped=(str(target),))
        except OSError:
            pass
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_utf8_write(target, body)
    return InstallReport(host_id=HOST_ID, files_written=(str(target),))


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)


_RULE_BODY = """# Myco Hard Contract — R1 to R7 (Cline rule)

When working in a Myco substrate (workspace with `_canon.yaml`),
honor R1-R7 mechanically. Full contract:
`docs/architecture/L1_CONTRACT/protocol.md`.
"""
