"""Myco Hosts Adapter: Codex (OpenAI Codex CLI)."""

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def detect() -> bool:
    """Detect if running in Codex environment.

    Checks:
    1. ~/.codex/ directory exists (Unix/Linux/macOS)
    2. $CODEX_HOME/.codex/config.toml exists (respects env override)
    3. 'codex' command on PATH
    """
    # Check CODEX_HOME env var first (allows override on any platform)
    codex_home = os.getenv("CODEX_HOME")
    if codex_home:
        if (Path(codex_home) / ".codex").exists():
            return True

    # Check default ~/.codex/ directory
    codex_dir = Path.home() / ".codex"
    if codex_dir.exists():
        return True

    # Check if 'codex' CLI is on PATH
    if shutil.which("codex") is not None:
        return True

    return False


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Codex hooks are installed.

    Codex supports hooks only on Unix-like systems (macOS/Linux).
    On Windows, hooks are disabled per official Codex docs.

    Returns extended dict with:
    - host: "codex"
    - session_start: bool
    - session_end: bool
    - hook_level: "native" | "mcp_only" | "none"
    - mcp_registered: bool (MCP server in config.toml)
    - rules_injected: bool (SessionStart hook in hooks.json on Unix)
    - notes: str
    - issues: [str]
    """
    issues = []
    mcp_registered = False
    rules_injected = False
    hook_level = "none"
    is_windows = platform.system() == "Windows"

    # Determine config directory (respects CODEX_HOME)
    codex_home = os.getenv("CODEX_HOME")
    if codex_home:
        config_dir = Path(codex_home) / ".codex"
    else:
        config_dir = Path.home() / ".codex"

    if not config_dir.exists():
        issues.append(f"Codex config directory not found: {config_dir}")
        return {
            "host": "codex",
            "session_start": False,
            "session_end": False,
            "hook_level": "none",
            "mcp_registered": False,
            "rules_injected": False,
            "notes": "Codex not detected or not configured",
            "issues": issues,
        }

    config_file = config_dir / "config.toml"

    # Check MCP server registration in config.toml
    if config_file.exists():
        try:
            content = config_file.read_text(encoding="utf-8")
            if "[mcp_servers.myco]" in content or "[mcp.servers.myco]" in content:
                mcp_registered = True
        except Exception as e:
            issues.append(f"failed to read {config_file}: {e}")

    if not mcp_registered:
        issues.append("Myco MCP server not registered in config.toml")

    # Check for native hooks (Unix-only)
    if not is_windows:
        hooks_file = config_dir / "hooks.json"
        if hooks_file.exists():
            try:
                import json

                hooks = json.loads(hooks_file.read_text(encoding="utf-8"))
                # Codex uses "SessionStart" / "PreToolUse" / "PostToolUse" events
                if "SessionStart" in hooks:
                    for hook in hooks.get("SessionStart", []):
                        if isinstance(hook, dict) and "myco" in str(hook).lower():
                            rules_injected = True
                            break
            except Exception as e:
                issues.append(f"failed to read {hooks_file}: {e}")

        if not rules_injected and mcp_registered:
            # MCP is registered but hooks not set; still functional but not optimal
            hook_level = "mcp_only"
        elif rules_injected and mcp_registered:
            hook_level = "native"
        elif not mcp_registered:
            hook_level = "none"
    else:
        # Windows: hooks disabled, MCP only
        if mcp_registered:
            hook_level = "mcp_only"
        else:
            hook_level = "none"

    # Check .myco_state
    myco_state = root / ".myco_state"
    if not myco_state.exists():
        issues.append("missing .myco_state directory (bootstrap not run)")

    # Build final status
    session_start = hook_level in ("native", "mcp_only")
    session_end = hook_level in ("native", "mcp_only")

    notes_parts = [f"Codex {hook_level} hooks"]
    if is_windows:
        notes_parts.append("(hooks disabled on Windows per Codex docs)")
    notes = "; ".join(notes_parts)

    return {
        "host": "codex",
        "session_start": session_start,
        "session_end": session_end,
        "hook_level": hook_level,
        "mcp_registered": mcp_registered,
        "rules_injected": rules_injected,
        "notes": notes,
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """Install Codex hooks idempotently.

    On Unix (macOS/Linux):
    1. Merges MCP server entry into ~/.codex/config.toml
    2. Creates/merges SessionStart hook into ~/.codex/hooks.json

    On Windows:
    1. Only registers MCP server (no hooks available)

    Idempotent: skips if already installed.
    Returns True if installation succeeded or already present.
    """
    is_windows = platform.system() == "Windows"

    # Determine config directory
    codex_home = os.getenv("CODEX_HOME")
    if codex_home:
        config_dir = Path(codex_home) / ".codex"
    else:
        config_dir = Path.home() / ".codex"

    config_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Register MCP server in config.toml
    config_file = config_dir / "config.toml"
    try:
        if config_file.exists():
            existing = config_file.read_text(encoding="utf-8")
            # Check if already registered (idempotency)
            if "[mcp_servers.myco]" in existing or "[mcp.servers.myco]" in existing:
                # Already installed, skip MCP block
                pass
            else:
                # Append MCP server block
                mcp_block = (
                    '\n[mcp_servers.myco]\n'
                    'command = "python"\n'
                    'args = ["-m", "myco.mcp_server"]\n'
                )
                config_file.write_text(existing.rstrip() + mcp_block, encoding="utf-8")
        else:
            # Create new config file with MCP server
            mcp_block = (
                '[mcp_servers.myco]\n'
                'command = "python"\n'
                'args = ["-m", "myco.mcp_server"]\n'
                '\n'
                '# Optional: enable hooks (Unix only)\n'
                '[features]\n'
                'codex_hooks = true\n'
            )
            config_file.write_text(mcp_block, encoding="utf-8")
    except Exception as e:
        # Log error but continue to hooks setup
        print(f"warning: failed to write {config_file}: {e}", file=sys.stderr)
        return False

    # Step 2: Install hooks (Unix-only)
    if not is_windows:
        hooks_file = config_dir / "hooks.json"
        try:
            import json

            # Read existing hooks or create empty
            if hooks_file.exists():
                hooks = json.loads(hooks_file.read_text(encoding="utf-8"))
            else:
                hooks = {}

            # Check if SessionStart already has myco hook
            session_start_hooks = hooks.setdefault("SessionStart", [])
            myco_hook_exists = any(
                isinstance(h, dict) and "myco" in str(h).lower()
                for h in session_start_hooks
            )

            if not myco_hook_exists:
                # Add SessionStart hook for myco hunger
                hook = {"type": "command", "command": "myco hunger --execute"}
                session_start_hooks.append(hook)

            # Write hooks file
            hooks_file.write_text(
                json.dumps(hooks, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except Exception as e:
            print(f"warning: failed to install hooks in {hooks_file}: {e}", file=sys.stderr)
            # Don't fail entirely — MCP is still functional
            pass

    return True
