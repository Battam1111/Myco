"""Continue (continue.dev) symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Continue (continue.dev) supports MCP servers via ``~/.continue/config.yaml``
(``mcpServers`` block) and a Rule/Block system via ``~/.continue/rules/<name>.md``.
v0.6.0 deep-install writes a Myco-specific rule that primes Continue
agent sessions with the R1-R7 hard-contract reminder.
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

HOST_ID = "continue-dev"


def _continue_dir(home: Path) -> Path:
    return home / ".continue"


def _rule_path(home: Path) -> Path:
    return _continue_dir(home) / "rules" / "myco.md"


def discover(home: Path) -> SymbiontProbe | None:
    """Probe ``home`` for an existing Continue install; return SymbiontProbe or None."""
    cdir = _continue_dir(home)
    installed = cdir.is_dir()
    caps: set[str] = set()
    if installed:
        if (cdir / "config.yaml").is_file() or (cdir / "config.json").is_file():
            caps.add("config")
        if (cdir / "rules").is_dir():
            caps.add("rules")
    return SymbiontProbe(
        host_id=HOST_ID,
        installed=installed,
        home=home,
        capabilities=frozenset(caps),
    )


def install_basic(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Basic install via myco-install host continue (writes mcpServers)."""
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Write ~/.continue/rules/myco.md with R1-R7 priming."""
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
                return InstallReport(host_id=HOST_ID, files_skipped=(str(target),))
        except OSError:
            pass
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_utf8_write(target, content)
    return InstallReport(host_id=HOST_ID, files_written=(str(target),))


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove ~/.continue/rules/myco.md installed by install_deep; honor dry_run."""
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


_RULE_BODY = """# Myco Hard Contract — R1 to R7

When working in a Myco substrate (workspace with `_canon.yaml`),
honor these seven hard rules:

- R1: Call `mcp__myco__myco_hunger` first in every new session.
- R2: At session end, call `mcp__myco__myco_senesce` (full mode)
  before /compact.
- R3: Before asserting any fact about the substrate, call
  `mcp__myco__myco_sense` first. Memory is not a source.
- R4: When a decision, friction, or insight occurs, call
  `mcp__myco__myco_eat` immediately.
- R5: After creating any new file, add cross-references.
- R6: Only write to paths in
  `_canon.yaml::system.write_surface.allowed`.
- R7: Lower layers conform to upper layers (L0 > L1 > L2 > L3 > L4).

Full contract: `docs/architecture/L1_CONTRACT/protocol.md`.
"""
