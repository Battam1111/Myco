"""Goose symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Goose (block.github.io/goose) supports MCP via
``~/.config/goose/config.yaml`` ``extensions`` block and recipes via
``~/.config/goose/recipes/<name>.yaml``. v0.6.0 deep-install writes
``~/.config/goose/recipes/myco-bootstrap.yaml``.
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

HOST_ID = "goose"


def _goose_dir(home: Path) -> Path:
    return home / ".config" / "goose"


def _recipe_path(home: Path) -> Path:
    return _goose_dir(home) / "recipes" / "myco-bootstrap.yaml"


def discover(home: Path) -> SymbiontProbe | None:
    gd = _goose_dir(home)
    installed = gd.is_dir() or (home / ".goose").is_dir()
    caps: set[str] = set()
    if installed:
        if (gd / "config.yaml").is_file():
            caps.add("config")
        if (gd / "recipes").is_dir():
            caps.add("recipes")
    return SymbiontProbe(
        host_id=HOST_ID, installed=installed, home=home, capabilities=frozenset(caps)
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
    target = _recipe_path(probe.home)
    substrate_id = "unknown"
    try:
        substrate_id = substrate.canon.substrate_id
    except Exception:
        pass
    sig = f"{SYMBIONT_SIG_PREFIX} {substrate_id}:0.6.0\n"
    body = sig + _RECIPE_BODY
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
    target = _recipe_path(probe.home)
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


_RECIPE_BODY = """version: "1.0"
title: "Myco substrate bootstrap"
description: "R1 boot ritual + R3 sense-before-assert priming for any Myco substrate."
prompt: |
  Before any factual claim about the current Myco substrate:
  1. Call mcp__myco__myco_hunger to get current state.
  2. Call mcp__myco__myco_sense for any specific lookup (R3).
  3. Call mcp__myco__myco_eat the moment any decision occurs (R4).
  At session end: mcp__myco__myco_senesce.
"""
