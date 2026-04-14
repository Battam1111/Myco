"""Myco Hosts Adapter: Zed (editor)."""

from pathlib import Path
from typing import Any, Dict
import json
import shutil
import os
import platform


def _get_zed_config_path() -> Path:
    """Get platform-specific Zed config directory path.
    
    Linux/macOS: $XDG_CONFIG_HOME/zed or ~/.config/zed
    Windows: %APPDATA%/Zed
    """
    if platform.system() == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "Zed"
    else:
        # Linux/macOS
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home:
            return Path(xdg_config_home) / "zed"
        return Path.home() / ".config" / "zed"
    
    # Fallback
    return Path.home() / ".config" / "zed"


def detect() -> bool:
    """Detect if running in Zed environment or if Zed is available.
    
    Checks in order:
    1. .zed/ directory at project root
    2. zed executable in PATH
    3. Zed global config directory exists
    """
    # Check project-level .zed/
    if (Path.cwd() / ".zed").exists():
        return True
    
    # Check if zed is in PATH
    if shutil.which("zed") is not None:
        return True
    
    # Check if global config directory exists
    global_config = _get_zed_config_path()
    if global_config.exists():
        return True
    
    return False


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Zed MCP context_servers registration is installed.
    
    Zed uses project-level .zed/settings.json with context_servers block.
    The `source: "custom"` field is REQUIRED or Zed silently skips registration.
    No native session hooks — context servers load when Assistant Panel opens.
    
    Returns {host: "zed", hook_level: "mcp_only", mcp_registered: bool,
             rules_injected: False, session_hooks: False, issues: [str]}.
    """
    issues = []
    mcp_registered = False
    
    # Check project-level .zed/settings.json (preferred)
    project_settings = root / ".zed" / "settings.json"
    if project_settings.exists():
        try:
            with open(project_settings, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # Check for context_servers.myco with source: "custom"
            context_servers = settings.get("context_servers", {})
            myco_server = context_servers.get("myco", {})
            
            if isinstance(myco_server, dict):
                # Verify required field source: "custom"
                if myco_server.get("source") == "custom":
                    mcp_registered = True
                else:
                    if myco_server:  # myco entry exists but source is wrong
                        issues.append(
                            ".zed/settings.json has context_servers.myco but "
                            "source != 'custom' (required)"
                        )
        except (OSError, ValueError) as e:
            issues.append(f"failed to read .zed/settings.json: {e}")
    
    if not mcp_registered:
        if not project_settings.exists():
            issues.append(".zed/settings.json not found")
        elif not issues:  # no parse errors, just missing myco entry
            issues.append("context_servers.myco not registered in .zed/settings.json")
    
    return {
        "host": "zed",
        "hook_level": "mcp_only",
        "mcp_registered": mcp_registered,
        "rules_injected": False,  # Zed has no rule injection
        "session_hooks": False,    # Context servers load on demand, no hooks
        "notes": "Zed MCP registration via .zed/settings.json context_servers block",
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """Install Zed MCP context_servers registration.
    
    Creates or updates .zed/settings.json with context_servers.myco entry.
    The source: "custom" field is REQUIRED.
    Idempotent — preserves other context_servers and settings entries.
    
    Returns True if installation successful, False otherwise.
    """
    zed_dir = root / ".zed"
    zed_dir.mkdir(parents=True, exist_ok=True)
    
    settings_file = zed_dir / "settings.json"
    
    # Load existing config or start fresh
    try:
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        else:
            settings = {}
    except Exception:
        settings = {}
    
    # Ensure context_servers dict exists
    if not isinstance(settings.get("context_servers"), dict):
        settings["context_servers"] = {}
    
    # Define Myco context server entry with REQUIRED source: "custom"
    myco_server = {
        "source": "custom",
        "command": "python",
        "args": ["-m", "myco.mcp_server"],
        "env": {
            "PYTHONUNBUFFERED": "1"
        }
    }
    
    # Idempotent: skip if already present with same config
    existing = settings["context_servers"].get("myco", {})
    if existing == myco_server:
        return True
    
    # Merge or create
    settings["context_servers"]["myco"] = myco_server
    
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
