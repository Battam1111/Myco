"""Myco Hosts Adapter: Cowork (Claude Code in Cowork environment)."""

from pathlib import Path
from typing import Any, Dict, Optional


def detect() -> bool:
    """Detect if running in Cowork environment."""
    import os
    return (os.getenv("COWORK_SESSION") is not None or
            str(Path.cwd()).startswith("/sessions/"))


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Cowork session hooks are installed.

    For Cowork, hooks are provided by the platform plugin.
    Returns {session_start: bool, session_end: bool, notes: str, issues: [str]}.
    """
    issues = []

    # Check if .myco_state/ exists (suggests bootstrap)
    myco_state = root / ".myco_state"
    if not myco_state.exists():
        issues.append("missing .myco_state directory (bootstrap not run)")

    # Check if boot_brief.md exists
    boot_brief = myco_state / "boot_brief.md" if myco_state.exists() else None
    if not boot_brief or not boot_brief.exists():
        issues.append("missing .myco_state/boot_brief.md (hunger not run recently)")

    # For Cowork, we assume native hooks are available (provided by plugin)
    return {
        "host": "cowork",
        "session_start": not bool(issues),  # optimistic
        "session_end": not bool(issues),
        "notes": "Cowork native hooks provided by plugin",
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """Install Cowork hooks (typically pre-installed by plugin).

    For Cowork, hooks are provided by the platform.
    This is a no-op but returns status.
    """
    return check_hooks(root)["session_start"] == True
