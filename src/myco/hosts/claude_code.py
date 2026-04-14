"""Myco Hosts Adapter: Claude Code."""

from pathlib import Path
from typing import Any, Dict, Optional


def detect() -> bool:
    """Detect if running in Claude Code environment."""
    return (Path.cwd() / ".claude").exists()


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Claude Code session hooks are installed.

    Looks for .claude/settings.json with myco hook configuration.
    Returns {session_start: bool, session_end: bool, notes: str, issues: [str]}.
    """
    issues = []

    claude_dir = Path.cwd() / ".claude"
    if not claude_dir.exists():
        issues.append("not in Claude Code environment")
        return {
            "host": "claude_code",
            "session_start": False,
            "session_end": False,
            "notes": "Claude Code not detected",
            "issues": issues,
        }

    # Check for settings.json with myco hooks
    settings_file = claude_dir / "settings.json"
    has_settings = False
    if settings_file.exists():
        try:
            import json
            with open(settings_file, "r") as f:
                settings = json.load(f)
            # Simple check: does config reference myco?
            config_str = json.dumps(settings)
            has_settings = "myco" in config_str.lower()
        except Exception as e:
            issues.append(f"failed to read .claude/settings.json: {e}")

    if not has_settings:
        issues.append(".claude/settings.json missing myco hook configuration")

    # Check .myco_state
    myco_state = root / ".myco_state"
    if not myco_state.exists():
        issues.append("missing .myco_state directory (bootstrap not run)")

    return {
        "host": "claude_code",
        "session_start": not bool(issues),
        "session_end": not bool(issues),
        "notes": "Claude Code native hooks via .claude/settings.json",
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """Install Claude Code hooks (requires manual setup in settings.json).

    This is a placeholder — actual hook installation requires user to
    configure .claude/settings.json manually.
    """
    return check_hooks(root)["session_start"] == True
