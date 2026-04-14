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
    """Install Claude Code native hooks.

    Wave 56: merges SessionStart + SessionEnd hook entries into
    .claude/settings.json so `myco hunger --execute` fires on session
    start and `myco session-end` fires on close. Idempotent — skips if
    the exact hook is already present.
    """
    import json

    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_file = claude_dir / "settings.json"

    try:
        if settings_file.exists():
            settings = json.loads(settings_file.read_text(encoding="utf-8"))
        else:
            settings = {}
    except Exception:
        settings = {}

    hooks = settings.setdefault("hooks", {})

    start_hook = {"command": "myco hunger --execute", "description": "Myco boot ritual"}
    end_hook = {"command": "myco session-end", "description": "Myco close-out ritual"}

    # SessionStart
    ss = hooks.setdefault("SessionStart", [])
    if not any(h.get("command") == start_hook["command"] for h in ss if isinstance(h, dict)):
        ss.append(start_hook)
    # SessionEnd
    se = hooks.setdefault("SessionEnd", [])
    if not any(h.get("command") == end_hook["command"] for h in se if isinstance(h, dict)):
        se.append(end_hook)

    try:
        settings_file.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False
