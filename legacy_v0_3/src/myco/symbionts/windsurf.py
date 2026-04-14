"""Myco Hosts Adapter: Windsurf (Codeium's AI IDE)."""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def detect() -> bool:
    """Detect if running in Windsurf environment.

    Five-signal detection:
    1. windsurf CLI on PATH
    2. ~/.codeium/windsurf/ directory exists (global config)
    3. .windsurf/ directory in project (workspace rules)
    4. .windsurfrules file in project (legacy workspace rules)
    5. WINDSURF or CODEIUM_HOME environment variables set
    """
    # Signal 1: windsurf CLI on PATH
    if shutil.which("windsurf") is not None:
        return True

    # Signal 2: global Windsurf config directory
    home = Path.home()
    if (home / ".codeium" / "windsurf").is_dir():
        return True

    # Signal 3: project .windsurf/ directory
    cwd = Path.cwd()
    if (cwd / ".windsurf").is_dir():
        return True

    # Signal 4: legacy .windsurfrules file
    if (cwd / ".windsurfrules").is_file():
        return True

    # Signal 5: environment variables
    if os.getenv("WINDSURF") or os.getenv("CODEIUM_HOME"):
        return True

    return False


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Windsurf hooks are installed and configured.

    Windsurf has:
    - Rules files in .windsurf/rules/*.md (bootstrap + myco rules)
    - Global MCP config at ~/.codeium/windsurf/mcp_config.json (registration)
    - Optional hooks in .windsurf/hooks.json (knowledge capture)

    Note: Windsurf has NO SessionStart equivalent hook event.
    Bootstrap is triggered manually via `myco hunger --execute` command
    in rules, or the user invokes it themselves.

    Returns {host: "windsurf", session_start: bool, session_end: bool,
             hook_level: str, mcp_registered: bool, rules_injected: bool,
             session_hooks: bool, notes: str, issues: [str]}.
    """
    issues = []

    windsurf_dir = root / ".windsurf"
    rules_dir = windsurf_dir / "rules" if windsurf_dir.exists() else None

    # Check if .windsurf/ exists (workspace indicator)
    if not windsurf_dir.exists():
        # .windsurf/ is optional; only required if we're actively configuring
        pass

    # Check for myco rules in .windsurf/rules/
    rules_injected = False
    if rules_dir and rules_dir.exists():
        try:
            rule_files = list(rules_dir.glob("*.md"))
            for rf in rule_files:
                content = rf.read_text(encoding="utf-8")
                if "<!-- myco-boot:" in content or "myco" in content.lower():
                    rules_injected = True
                    break
        except Exception as e:
            issues.append(f"failed to read .windsurf/rules: {e}")

    if not rules_injected:
        issues.append(".windsurf/rules/ missing myco-boot rule")

    # Check global MCP registration
    mcp_registered = _check_mcp_registered(root)
    if not mcp_registered:
        issues.append("MCP not registered in ~/.codeium/windsurf/mcp_config.json")

    # Check .myco_state
    myco_state = root / ".myco_state"
    if not myco_state.exists():
        issues.append("missing .myco_state directory (bootstrap not run)")

    # Windsurf does NOT have SessionStart hooks; bootstrap must be manual
    session_start = False  # Windsurf has no SessionStart equivalent
    session_end = False    # Windsurf has no SessionEnd equivalent

    return {
        "host": "windsurf",
        "session_start": session_start,
        "session_end": session_end,
        "hook_level": "rules",
        "mcp_registered": mcp_registered,
        "rules_injected": rules_injected,
        "session_hooks": False,  # Windsurf has no SessionStart/SessionEnd
        "notes": "Windsurf uses rules + MCP; bootstrap triggered via 'myco hunger --execute' in rules",
        "issues": issues,
    }


def install_hooks(root: Path, write_hooks_json: bool = False) -> bool:
    """Install Windsurf hooks for Myco.

    Three-part installation:
    (a) Write .windsurf/rules/00-myco-boot.md with boot instructions (idempotent via marker)
    (b) Register MCP in global ~/.codeium/windsurf/mcp_config.json (idempotent JSON merge)
    (c) Optionally write .windsurf/hooks.json with post_write_code hook for knowledge capture

    Args:
        root: project root
        write_hooks_json: if True, write .windsurf/hooks.json (optional, defaults False)

    Returns: True if installation succeeded, False otherwise.
    """
    # Ensure .windsurf/ exists
    windsurf_dir = root / ".windsurf"
    windsurf_dir.mkdir(parents=True, exist_ok=True)

    # (a) Write rules file with myco-boot marker
    rules_dir = windsurf_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    boot_rule_file = rules_dir / "00-myco-boot.md"
    boot_rule_content = _generate_boot_rule(root)

    try:
        # Idempotent: check if already installed via marker
        if boot_rule_file.exists():
            existing = boot_rule_file.read_text(encoding="utf-8")
            if "<!-- myco-boot: v1 -->" in existing:
                # Already installed, skip
                pass
            else:
                # File exists but missing marker; replace it
                boot_rule_file.write_text(boot_rule_content, encoding="utf-8")
        else:
            boot_rule_file.write_text(boot_rule_content, encoding="utf-8")
    except Exception as e:
        return False

    # (b) Register MCP in global config
    try:
        if not _register_mcp_globally():
            return False
    except Exception as e:
        return False

    # (c) Optionally write hooks.json
    if write_hooks_json:
        try:
            hooks_file = windsurf_dir / "hooks.json"
            if not hooks_file.exists():
                hooks_content = {
                    "post_write_code": {
                        "command": "myco eat --auto-tag on-write-code",
                        "description": "Capture knowledge from code writes (optional)"
                    }
                }
                hooks_file.write_text(
                    json.dumps(hooks_content, indent=2) + "\n",
                    encoding="utf-8"
                )
        except Exception:
            # Hooks.json write failure is non-fatal
            pass

    # Verify installation
    return check_hooks(root)["mcp_registered"] and check_hooks(root)["rules_injected"]


def _get_windsurf_mcp_config_path() -> Path:
    """Return OS-specific path for Windsurf global MCP config.

    Linux/macOS: ~/.codeium/windsurf/mcp_config.json
    Windows: %APPDATA%\Codeium\Windsurf\mcp_config.json (with fallback to ~/.codeium/windsurf/)
    """
    home = Path.home()

    if sys.platform == "win32":
        # Windows: try APPDATA first
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Codeium" / "Windsurf" / "mcp_config.json"
        # Fallback to ~/.codeium/windsurf/
        return home / ".codeium" / "windsurf" / "mcp_config.json"
    else:
        # Linux/macOS: ~/.codeium/windsurf/
        return home / ".codeium" / "windsurf" / "mcp_config.json"


def _check_mcp_registered(root: Path) -> bool:
    """Check if myco MCP is registered in global Windsurf config."""
    try:
        config_path = _get_windsurf_mcp_config_path()
        if not config_path.exists():
            return False

        config = json.loads(config_path.read_text(encoding="utf-8"))
        mcp_servers = config.get("mcpServers", {})
        return "myco" in mcp_servers
    except Exception:
        return False


def _register_mcp_globally() -> bool:
    """Register myco MCP in global ~/.codeium/windsurf/mcp_config.json.

    Idempotent: if already registered, returns True without modification.
    """
    config_path = _get_windsurf_mcp_config_path()

    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing config or create empty
    try:
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            config = {}
    except (json.JSONDecodeError, ValueError):
        config = {}

    # Check if already registered
    mcp_servers = config.setdefault("mcpServers", {})
    if "myco" in mcp_servers:
        return True  # Already registered

    # Register myco
    mcp_servers["myco"] = {
        "command": "python",
        "args": ["-m", "myco.mcp_server"],
        "env": {"PYTHONUNBUFFERED": "1"},
    }

    # Write back
    try:
        config_path.write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8"
        )
        return True
    except Exception:
        return False


def _generate_boot_rule(root: Path) -> str:
    """Generate the content of .windsurf/rules/00-myco-boot.md.

    This rule contains the bootstrap instruction for myco, allowing the user
    to manually trigger `myco hunger --execute` when needed.
    """
    project_dir = root.resolve()

    return f"""# Myco Boot Instruction

<!-- myco-boot: v1 -->

When starting work on this Myco-powered project, run:

```bash
cd "{project_dir}"
python -m myco hunger --execute
```

This bootstrap ritual:
1. Checks project health (contract drift, knowledge staleness, lint violations)
2. Auto-heals common issues (missing state dirs, contract sync)
3. Emits boot signals so you know what state the substrate is in

**Optional**: If you want continuous knowledge capture, enable `.windsurf/hooks.json`:
- Edit `.windsurf/hooks.json` to set `post_write_code` event
- This captures knowledge from your code writes automatically

For full Windsurf + Myco integration, see:
- `MYCO.md` — kernel identity and protocols
- `.windsurf/rules/` — workspace rules and hooks
- `docs/` — workflow docs (if present)
"""
