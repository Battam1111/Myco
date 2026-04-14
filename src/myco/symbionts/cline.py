"""Myco Hosts Adapter: Cline (Claude Dev VS Code extension)."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def _cline_settings_path() -> Path:
    r"""Return the OS-specific path for Cline's global MCP settings file.

    Path format varies by OS:
    - Windows: %APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
    - macOS: ~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
    - Linux: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        # Fallback if APPDATA is not set
        return Path.home() / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    else:
        # Linux and other Unix-like systems
        return Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*, preserving nested dicts."""
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _json_merge_write(path: Path, patch: dict) -> str:
    """Deep-merge patch into JSON file at path.

    If file exists, parse and recursively merge. Preserves other keys.
    If file does not exist or is invalid JSON, write patch as-is.

    Returns: "merged", "created", or "created — old file was invalid"
    """
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
            return "created — old file was invalid"
        existing = _deep_merge(existing, patch)
        path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
        return "merged"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
        return "created"


def detect() -> bool:
    """Detect if running in Cline environment.

    Checks for:
    1. .clinerules directory or .clinerules file in cwd
    2. VS Code environment with Cline extension
    3. Cline global MCP settings file existence
    """
    cwd = Path.cwd()

    # Check for .clinerules directory or file
    if (cwd / ".clinerules").exists():
        return True

    # Check for .roo/rules (Roo Code variant)
    if (cwd / ".roo" / "rules").exists():
        return True

    # Check for .vscode directory (VS Code context)
    if (cwd / ".vscode").exists():
        # Additional check: Cline global settings should exist
        if _cline_settings_path().exists():
            return True

    return False


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Cline session hooks are installed.

    Cline uses rules-based approach (primary):
    - .clinerules/00-myco-boot.md with stable marker (idempotent marker design)
    - Global MCP registration in cline_mcp_settings.json (secondary)

    Returns dict with:
    - host: "cline"
    - session_start: bool (true if rules_injected)
    - session_end: bool (false — Cline has no session_end equivalent)
    - hook_level: "rules" (primary) or "mcp_only" (fallback)
    - rules_injected: bool (00-myco-boot.md exists with marker)
    - mcp_registered: bool (myco entry in cline_mcp_settings.json)
    - notes: str
    - issues: [str]
    """
    issues = []
    rules_injected = False
    mcp_registered = False

    # Check .clinerules presence
    clinerules_dir = root / ".clinerules"
    clinerules_file = root / ".clinerules"

    if not (clinerules_dir.is_dir() or clinerules_file.is_file()):
        issues.append(".clinerules directory or file not found")

    # Check for boot rule marker in .clinerules/00-myco-boot.md
    if clinerules_dir.is_dir():
        boot_rule = clinerules_dir / "00-myco-boot.md"
        if boot_rule.exists():
            try:
                content = boot_rule.read_text(encoding="utf-8")
                if "<!-- myco-boot: v1 -->" in content:
                    rules_injected = True
            except Exception as e:
                issues.append(f"failed to read .clinerules/00-myco-boot.md: {e}")

    # Check global MCP settings
    try:
        cline_settings = _cline_settings_path()
        if cline_settings.exists():
            try:
                settings = json.loads(cline_settings.read_text(encoding="utf-8"))
                mcp_servers = settings.get("mcpServers", {})
                if "myco" in mcp_servers:
                    mcp_registered = True
            except (json.JSONDecodeError, ValueError) as e:
                issues.append(f"failed to parse cline_mcp_settings.json: {e}")
    except Exception as e:
        issues.append(f"failed to access cline_mcp_settings.json path: {e}")

    # Determine hook level
    hook_level = "rules" if rules_injected else ("mcp_only" if mcp_registered else "none")

    # Check .myco_state (optional validation)
    myco_state = root / ".myco_state"
    if not myco_state.exists():
        issues.append("missing .myco_state directory (bootstrap not run)")

    return {
        "host": "cline",
        "session_start": rules_injected,  # rules are the primary boot mechanism
        "session_end": False,  # Cline has no session_end hook equivalent
        "hook_level": hook_level,
        "rules_injected": rules_injected,
        "mcp_registered": mcp_registered,
        "notes": "Cline uses rules-based boot (.clinerules/00-myco-boot.md) + optional MCP registration",
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """Install Cline hooks via rules + optional MCP registration.

    Strategy:
    1. Create .clinerules/00-myco-boot.md with boot instructions and stable marker
    2. Register myco in global cline_mcp_settings.json (idempotent JSON merge)
    3. If .roo/rules/ exists (Roo Code), also write .roo/rules/00-myco-boot.md

    Idempotent via stable marker: <!-- myco-boot: v1 -->

    Returns True if both main hooks installed successfully, False otherwise.
    """
    success = True

    # Determine .clinerules location: prefer directory over file
    clinerules_dir = root / ".clinerules"
    clinerules_file = root / ".clinerules"

    # If .clinerules is a file, convert to directory (or skip if mixed state)
    if clinerules_file.is_file():
        # For safety, we keep the existing file and just write alongside
        # In practice, .clinerules should be a directory
        pass

    # Ensure .clinerules directory exists
    if not clinerules_dir.exists():
        try:
            clinerules_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False

    # Write .clinerules/00-myco-boot.md with stable marker
    boot_rule_content = """<!-- myco-boot: v1 -->

# Myco Boot Rules for Cline

These rules inject Myco knowledge-metabolism framework initialization into Cline sessions.

## Automatic Boot Ritual

On each session start in Cline:

1. **Check substrate health** via MCP or CLI:
   - MCP preferred: `myco_hunger(execute=true, project_dir=<root>)`
   - CLI fallback: `myco hunger --execute --json`

2. **Address REFLEX HIGH signals** before other work.

3. **Load working memory** from CLAUDE.md or equivalent.

## Myco Integration

This project is Myco-enabled. The framework provides:

- **Knowledge metabolism**: Automatic capture of decisions, friction, insights via `myco_eat`
- **Health checks**: Substrate linting + immune system via `myco_immune`
- **Search integration**: Retrieve prior knowledge via `myco_search`
- **Memory management**: Persistent notes via `myco_memory`

## MCP Registration

Myco is registered in:
- Global: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- Project: (optional) `.clinerules/` rules concatenated into prompt

Verify MCP connection at session start:
- If MCP tools unavailable, fall back to CLI via Bash (`myco hunger --help`).

## First Boot

On first session in a new Cline environment:

1. Run `myco hunger --execute` to bootstrap `.myco_state/`
2. Read `.claude/CLAUDE.md` (or project CLAUDE.md) for hot-zone context
3. Pin any Cline-specific workflows (e.g., how to trigger skills)

## Idempotency

This rule file is **idempotent** — it can be re-read multiple times without side effects.
Tooling recognizes the marker at the top to avoid duplicate updates.
"""

    boot_rule_path = clinerules_dir / "00-myco-boot.md"
    try:
        boot_rule_path.write_text(boot_rule_content, encoding="utf-8")
    except Exception:
        success = False

    # Register MCP in global cline_mcp_settings.json
    try:
        cline_settings_path = _cline_settings_path()
        # Minimal myco server config (Cline expects stdio or HTTP)
        payload = {
            "mcpServers": {
                "myco": {
                    "command": "python",
                    "args": ["-m", "myco.mcp_server"],
                    "env": {},
                }
            }
        }
        _json_merge_write(cline_settings_path, payload)
    except Exception:
        success = False

    # Support Roo Code variant
    roo_rules_dir = root / ".roo" / "rules"
    if roo_rules_dir.exists():
        try:
            roo_boot_path = roo_rules_dir / "00-myco-boot.md"
            roo_boot_path.write_text(boot_rule_content, encoding="utf-8")
        except Exception:
            pass  # Roo Code support is optional; don't fail main install

    return success
