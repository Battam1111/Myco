"""Myco Hosts Adapter: Cursor."""

from pathlib import Path
from typing import Any, Dict, Optional


def detect() -> bool:
    """Detect if running in Cursor environment."""
    import os
    return (os.getenv("CURSOR_SESSION") is not None or
            (Path.cwd() / ".cursor").exists())


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Cursor session hooks are installed.

    Looks for .cursor/rules with myco rule configuration.
    Returns {session_start: bool, session_end: bool, notes: str, issues: [str]}.
    """
    issues = []

    cursor_dir = Path.cwd() / ".cursor"
    if not cursor_dir.exists():
        issues.append("not in Cursor environment")
        return {
            "host": "cursor",
            "session_start": False,
            "session_end": False,
            "notes": "Cursor not detected",
            "issues": issues,
        }

    # Check for rules file with myco directives
    rules_file = cursor_dir / "rules"
    has_rules = False
    if rules_file.exists():
        try:
            with open(rules_file, "r") as f:
                content = f.read()
            has_rules = "myco" in content.lower()
        except Exception as e:
            issues.append(f"failed to read .cursor/rules: {e}")

    if not has_rules:
        issues.append(".cursor/rules missing myco rule configuration")

    # Check .myco_state
    myco_state = root / ".myco_state"
    if not myco_state.exists():
        issues.append("missing .myco_state directory (bootstrap not run)")

    return {
        "host": "cursor",
        "session_start": not bool(issues),
        "session_end": not bool(issues),
        "notes": "Cursor native hooks via .cursor/rules",
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """Install Cursor hooks (requires manual setup in .cursor/rules).

    This is a placeholder — actual hook installation requires user to
    configure .cursor/rules manually.
    """
    return check_hooks(root)["session_start"] == True
