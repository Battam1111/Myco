"""
First-run auto-setup — detects IDE/agent and installs hooks transparently.

Design:
    - Run once per installation (~/.config/myco/.init-complete marker)
    - TTY-aware prompt (batch mode: default yes)
    - Respect MYCO_NO_AUTOINSTALL=1 env var
    - Dispatch to each adapter's install_hooks(root) method
    - Never crash — wrap errors gracefully
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

from myco.symbionts import detect_active_symbiont


def _get_myco_home() -> Path:
    """Return Myco's home directory.
    
    - Linux/macOS: $XDG_CONFIG_HOME/myco (fallback ~/.config/myco)
    - Windows: %APPDATA%/Myco
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "Myco"
        return Path.home() / "AppData" / "Roaming" / "Myco"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        if xdg:
            return Path(xdg) / "myco"
        return Path.home() / ".config" / "myco"


def is_first_run() -> bool:
    """Return True iff .init-complete marker is absent and MYCO_NO_AUTOINSTALL not set."""
    if os.environ.get("MYCO_NO_AUTOINSTALL"):
        return False
    marker = _get_myco_home() / ".init-complete"
    return not marker.exists()


def prompt_auto_detect() -> bool:
    """Prompt user for auto-detect confirmation (TTY-aware).
    
    - If not TTY or non-interactive shell: return True (default yes)
    - If TTY: prompt with [Y/n] and return user choice
    """
    if not sys.stdin.isatty():
        return True
    try:
        response = input("Myco: auto-detect and install hooks for this IDE? [Y/n] ").strip().lower()
        return response in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def run_auto_setup(cwd: Path) -> Dict[str, str]:
    """Run auto-setup: detect host and call install_hooks.
    
    Returns summary dict: {host, installed, level, notes}
    Never raises; errors are logged in 'notes' field.
    """
    try:
        host = detect_active_symbiont()
        if not host:
            return {
                "host": "unknown",
                "installed": "false",
                "level": "none",
                "notes": "No IDE detected; skipped auto-setup",
            }

        # Import adapter modules
        adapters = {
            "cowork": __import__("myco.symbionts.cowork", fromlist=["install_hooks"]),
            "claude_code": __import__("myco.symbionts.claude_code", fromlist=["install_hooks"]),
            "cursor": __import__("myco.symbionts.cursor", fromlist=["install_hooks"]),
            "vscode": __import__("myco.symbionts.vscode", fromlist=["install_hooks"]),
            "continue": __import__("myco.symbionts.continue_", fromlist=["install_hooks"]),
            "zed": __import__("myco.symbionts.zed", fromlist=["install_hooks"]),
            "codex": __import__("myco.symbionts.codex", fromlist=["install_hooks"]),
            "cline": __import__("myco.symbionts.cline", fromlist=["install_hooks"]),
            "windsurf": __import__("myco.symbionts.windsurf", fromlist=["install_hooks"]),
        }

        if host not in adapters:
            return {
                "host": host,
                "installed": "false",
                "level": "none",
                "notes": f"Host '{host}' not in adapter registry",
            }

        adapter = adapters[host]
        if not hasattr(adapter, "install_hooks"):
            return {
                "host": host,
                "installed": "false",
                "level": "none",
                "notes": f"Adapter for '{host}' has no install_hooks() method",
            }

        result = adapter.install_hooks(cwd)
        return {
            "host": host,
            "installed": "true",
            "level": result.get("hook_level", "unknown"),
            "notes": result.get("notes", "Hooks installed"),
        }

    except Exception as e:
        return {
            "host": "error",
            "installed": "false",
            "level": "none",
            "notes": f"Auto-setup failed: {str(e)[:100]}",
        }


def mark_first_run_done() -> None:
    """Create .init-complete marker in myco home."""
    home = _get_myco_home()
    home.mkdir(parents=True, exist_ok=True)
    marker = home / ".init-complete"
    marker.touch()


def run_if_first_time(cwd: Path) -> Optional[Dict[str, str]]:
    """Run auto-setup if this is first run; return summary or None.
    
    Returns:
        - Dict with result if first run and MYCO_NO_AUTOINSTALL not set
        - None otherwise
    """
    if not is_first_run():
        return None

    if not prompt_auto_detect():
        return None

    summary = run_auto_setup(cwd)
    if summary["installed"] == "true":
        mark_first_run_done()

    return summary
