"""Myco Hosts Adapter: Continue (continue.dev)."""

from pathlib import Path
from typing import Any, Dict
import json


def detect() -> bool:
    """Detect if running in Continue environment.
    
    Continue integrates with MCP servers via .continue/mcpServers/
    configuration at project root.
    """
    return (Path.cwd() / ".continue").exists()


def check_hooks(root: Path) -> Dict[str, Any]:
    """Check if Continue MCP registration is installed.
    
    Continue uses project-level .continue/mcpServers/myco.json for
    MCP server registration (most stable path). No native session hooks
    available — MCP server loads when Continue starts.
    
    Returns {host: "continue", hook_level: "mcp_only", mcp_registered: bool,
             rules_injected: False, session_hooks: False, issues: [str]}.
    """
    issues = []
    
    continue_dir = Path.cwd() / ".continue"
    if not continue_dir.exists():
        issues.append("not in Continue environment")
        return {
            "host": "continue",
            "hook_level": "mcp_only",
            "mcp_registered": False,
            "rules_injected": False,
            "session_hooks": False,
            "notes": "Continue not detected",
            "issues": issues,
        }
    
    # Check for .continue/mcpServers/myco.json
    mcp_servers_dir = continue_dir / "mcpServers"
    mcp_config_file = mcp_servers_dir / "myco.json"
    mcp_registered = False
    
    if mcp_config_file.exists():
        try:
            with open(mcp_config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            # Verify structure: should have mcpServers.myco with type=stdio
            if isinstance(config.get("mcpServers"), dict):
                myco_server = config["mcpServers"].get("myco", {})
                if myco_server.get("type") == "stdio":
                    mcp_registered = True
        except (OSError, ValueError) as e:
            issues.append(f"failed to read .continue/mcpServers/myco.json: {e}")
    
    if not mcp_registered:
        issues.append(".continue/mcpServers/myco.json not found or malformed")
    
    return {
        "host": "continue",
        "hook_level": "mcp_only",
        "mcp_registered": mcp_registered,
        "rules_injected": False,  # Continue has no rule injection
        "session_hooks": False,    # MCP server starts on demand, no hooks
        "notes": "Continue MCP registration via .continue/mcpServers/myco.json",
        "issues": issues,
    }


def install_hooks(root: Path) -> bool:
    """Install Continue MCP registration.
    
    Creates .continue/mcpServers/myco.json with stdio MCP server config.
    Idempotent — preserves other mcpServers entries.
    
    Returns True if installation successful, False otherwise.
    """
    continue_dir = root / ".continue"
    continue_dir.mkdir(parents=True, exist_ok=True)
    
    mcp_servers_dir = continue_dir / "mcpServers"
    mcp_servers_dir.mkdir(parents=True, exist_ok=True)
    
    mcp_config_file = mcp_servers_dir / "myco.json"
    
    # Load existing config or start fresh
    try:
        if mcp_config_file.exists():
            with open(mcp_config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}}
    except Exception:
        config = {"mcpServers": {}}
    
    # Ensure mcpServers dict exists
    if not isinstance(config.get("mcpServers"), dict):
        config["mcpServers"] = {}
    
    # Define Myco MCP server entry
    myco_server = {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "myco.mcp_server"],
        "env": {
            "PYTHONUNBUFFERED": "1"
        }
    }
    
    # Idempotent: skip if already present with same config
    existing = config["mcpServers"].get("myco", {})
    if existing == myco_server:
        return True
    
    # Merge or create
    config["mcpServers"]["myco"] = myco_server
    
    try:
        with open(mcp_config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
