"""Zed symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md``.

Zed has native ``context_servers`` (MCP) support via
``~/.config/zed/settings.json`` and slash-command extensibility via
``~/.config/zed/commands/<name>.toml``. v0.6.0 deep-install writes
``~/.config/zed/commands/myco.toml`` exposing /myco-hunger,
/myco-senesce, /myco-brief.
"""

from __future__ import annotations

import sys
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

HOST_ID = "zed"


def _zed_dir(home: Path) -> Path:
    if sys.platform == "darwin":
        cfg = home / "Library" / "Application Support" / "Zed"
        if cfg.is_dir():
            return cfg
    return home / ".config" / "zed"


def _commands_path(home: Path) -> Path:
    return _zed_dir(home) / "commands" / "myco.toml"


def discover(home: Path) -> SymbiontProbe | None:
    zd = _zed_dir(home)
    installed = zd.is_dir()
    caps: set[str] = set()
    if installed:
        if (zd / "settings.json").is_file():
            caps.add("settings")
        if (zd / "commands").is_dir():
            caps.add("slash_commands")
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset(caps),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    if not probe.installed:
        return InstallReport(host_id=HOST_ID, dry_run=dry_run)
    target = _commands_path(probe.home)
    substrate_id = "unknown"
    try:
        substrate_id = substrate.canon.substrate_id
    except Exception:
        pass
    sig = f"{SYMBIONT_SIG_PREFIX} {substrate_id}:0.6.0\n"
    body = sig + _COMMANDS_BODY
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
    target = _commands_path(probe.home)
    if not target.is_file():
        return UninstallReport(
            host_id=HOST_ID, files_not_found=(str(target),), dry_run=dry_run
        )
    if dry_run:
        return UninstallReport(
            host_id=HOST_ID, files_removed=(str(target),), dry_run=True
        )
    try:
        target.unlink()
    except OSError:
        return UninstallReport(
            host_id=HOST_ID, files_not_found=(str(target),), dry_run=dry_run
        )
    return UninstallReport(host_id=HOST_ID, files_removed=(str(target),))


_COMMANDS_BODY = """[[command]]
name = "myco-hunger"
description = "Run myco hunger (R1 boot ritual)."
template = "python -m myco hunger"

[[command]]
name = "myco-senesce"
description = "Run myco senesce (R2 session-end ritual)."
template = "python -m myco senesce"

[[command]]
name = "myco-brief"
description = "Show substrate state rollup."
template = "python -m myco brief"
"""
