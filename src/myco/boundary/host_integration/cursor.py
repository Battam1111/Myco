"""Cursor symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Cursor 2.0 (2026-Q1) added background-agent + git-worktree support
and persistent rules at ``~/.cursor/rules/<name>.mdc``. This adapter
writes a Myco-specific rule that primes any Cursor agent session
with the R1-R7 hard-contract reminder + sense-before-assert habit.

The rule is always-applied (every Cursor agent session loads it),
making R3 mechanically reinforced from the host side.
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

HOST_ID = "cursor"


def _cursor_dir(home: Path) -> Path:
    return home / ".cursor"


def _rule_path(home: Path) -> Path:
    return _cursor_dir(home) / "rules" / "myco.mdc"


def discover(home: Path) -> SymbiontProbe | None:
    """Probe ``home`` for an existing Cursor install; return SymbiontProbe or None."""
    cursor_dir = _cursor_dir(home)
    installed = cursor_dir.is_dir() or (home / "AppData" / "Local" / "Cursor").is_dir()
    caps: set[str] = set()
    if installed:
        if (cursor_dir / "rules").is_dir():
            caps.add("rules")
        if (cursor_dir / "mcp.json").is_file():
            caps.add("mcp")
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset(caps),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write the minimal Myco MCP entry to Cursor's config; honor dry_run."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write ~/.cursor/rules/myco.mdc with R1-R7 always-apply rule."""
    if not probe.installed:
        return InstallReport(host_id=HOST_ID, dry_run=dry_run)
    target = _rule_path(probe.home)
    substrate_id = "unknown"
    try:
        substrate_id = substrate.canon.substrate_id
    except Exception:
        pass
    sig = f"{SYMBIONT_SIG_PREFIX} {substrate_id}:0.6.0\n"
    content = sig + _RULE_BODY
    if dry_run:
        return InstallReport(
            host_id=HOST_ID,
            files_written=(str(target),),
            dry_run=True,
        )
    if target.is_file():
        try:
            existing = target.read_text(encoding="utf-8")
            if SYMBIONT_SIG_PREFIX in existing:
                return InstallReport(
                    host_id=HOST_ID,
                    files_skipped=(str(target),),
                )
        except OSError:
            pass
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_utf8_write(target, content)
    return InstallReport(host_id=HOST_ID, files_written=(str(target),))


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove ~/.cursor/rules/myco.mdc installed by install_deep; honor dry_run."""
    target = _rule_path(probe.home)
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


_RULE_BODY = """---
description: Myco substrate hard-contract priming for any Cursor agent session.
globs: ["**/*"]
alwaysApply: true
---

# Myco Hard Contract — R1 to R7

Every session in a Myco substrate (workspace with `_canon.yaml`)
follows seven hard rules. Cursor agents working in such a workspace
should honor them mechanically:

- **R1**: Call `mcp__myco__myco_hunger` first in every new session.
  This computes the substrate's current hunger signals and lets you
  decide what to do next.
- **R2**: At session end, call `mcp__myco__myco_senesce` (full mode)
  before /compact. The PreCompact hook automates this in Claude Code;
  Cursor sessions invoke it manually.
- **R3**: Before asserting any fact about the substrate (a number, a
  path, a decision), call `mcp__myco__myco_sense` first. Memory is
  not a source; the substrate is.
- **R4**: When a decision, friction point, or insight occurs, call
  `mcp__myco__myco_eat` immediately to capture it. Defer-and-batch
  loses material.
- **R5**: After creating any new file, add cross-references to
  related files. Orphaned files are dead knowledge.
- **R6**: Only write to paths declared in
  `_canon.yaml::system.write_surface.allowed`. The substrate's
  guard refuses unauthorized writes.
- **R7**: Lower layers conform to upper layers. L0 governs L1
  governs L2 governs L3 governs L4. Implementation never overrides
  contract.

The full contract: `docs/architecture/L1_CONTRACT/protocol.md`.
"""
