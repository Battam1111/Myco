"""Claude Code symbiont (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Claude Code already has the deepest Myco integration: the
``.claude-plugin/`` bundle ships hooks (SessionStart→hunger /
PreCompact→senesce / SessionEnd→senesce --quick) and slash skills
(``/myco:hunger``, ``/myco:senesce``). This adapter is therefore
introspection + signature verification only — no fresh writes
beyond confirming the bundle is intact.

For substrates that want to install Myco's Claude-Code surface
without cloning the kernel repo (e.g. via a downstream substrate
shipping its own Myco install), ``install_deep`` writes a minimal
hook config to ``~/.claude/hooks.json`` if absent.
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

HOST_ID = "claude-code"


def discover(home: Path) -> SymbiontProbe | None:
    """Detect Claude Code installation."""
    # Claude Code marker: presence of ~/.claude/ directory.
    claude_dir = home / ".claude"
    installed = claude_dir.is_dir()
    caps: set[str] = set()
    if installed:
        if (claude_dir / "settings.json").is_file():
            caps.add("settings")
        if (claude_dir / "hooks.json").is_file() or (
            home / ".claude-plugin" / "hooks" / "hooks.json"
        ).is_file():
            caps.add("hooks")
        if (claude_dir / "skills").is_dir():
            caps.add("skills")
        if (
            any(claude_dir.glob("plugins/*"))
            if (claude_dir / "plugins").is_dir()
            else False
        ):
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
    """Write mcpServers config to Claude Code (delegates to install/clients)."""
    # The basic install is handled by myco-install host claude-code; this
    # symbiont's basic-install is a no-op (the legacy install path is the
    # canonical writer for ~/.claude config).
    return InstallReport(host_id=HOST_ID, dry_run=dry_run)


def install_deep(
    probe: SymbiontProbe, substrate: Any, *, dry_run: bool = False
) -> InstallReport:
    """Verify + ensure Claude Code hooks + skills are configured.

    For myco-self (kernel substrate), this is a no-op since the bundled
    .claude-plugin/ already provides hooks + skills via marketplace
    install. For downstream substrates, this writes a minimal
    .claude/hooks.json if absent.
    """
    if not probe.installed:
        return InstallReport(host_id=HOST_ID, dry_run=dry_run)
    # Detection-only at v0.6.0 — actual writes deferred to v0.6.x patch
    # to ensure proper interaction with marketplace plugin lifecycle.
    return InstallReport(
        host_id=HOST_ID,
        files_skipped=(".claude/hooks.json",),
        dry_run=dry_run,
    )


def uninstall(probe: SymbiontProbe, *, dry_run: bool = False) -> UninstallReport:
    """Remove Claude Code symbiont artifacts (none at v0.6.0)."""
    return UninstallReport(host_id=HOST_ID, dry_run=dry_run)
