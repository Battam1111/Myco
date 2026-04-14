"""Myco Hosts Adapter: VS Code."""

from pathlib import Path
from typing import Any, Dict, Optional


def detect() -> bool:
    """Detect if running in VS Code environment."""
    return (Path.cwd() / ".vscode").exists()


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if VS Code hook support is available.

    VS Code does not provide native session hooks, so this adapter
    always degrades to protocol level.

    Returns {session_start: bool, session_end: bool, notes: str, issues: [str]}.
    """
    issues = []

    vscode_dir = Path.cwd() / ".vscode"
    if not vscode_dir.exists():
        issues.append("not in VS Code environment")

    # VS Code has no native session hooks
    issues.append("VS Code does not support native session hooks; degrading to protocol level")

    # Check .myco_state
    myco_state = root / ".myco_state"
    if not myco_state.exists():
        issues.append("missing .myco_state directory (bootstrap not run)")

    return {
        "host": "vscode",
        "session_start": False,  # no native hooks
        "session_end": False,
        "notes": "VS Code requires protocol-level hooks (text-based reminders)",
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """VS Code hooks require protocol-level only.

    This is a no-op — the user must follow text-based protocol reminders.
    """
    return False  # native hooks unavailable
