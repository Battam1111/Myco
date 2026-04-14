"""
Myco Hosts Common Utilities — shared OS-aware path and file operations.

Provides centralized utilities for all host adapters (Cowork, Claude Code,
Cursor, VS Code, Codex, Cline, Continue, Zed, Windsurf) to avoid duplication
of path resolution, JSON/TOML merging, and configuration file handling.

Wave 55 (vision_closure_craft_2026-04-14.md, Partition B G7):
Extracts and unifies patterns from seed_cmd.py and existing adapters.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Optional

# Hook levels used across all adapters
HOOK_LEVEL_NATIVE = "native"
HOOK_LEVEL_RULES = "rules"
HOOK_LEVEL_MCP_ONLY = "mcp_only"
HOOK_LEVEL_PROTOCOL = "protocol"


def user_config_dir(app_name: str) -> Path:
    """
    Get OS-aware user config directory for an application.

    Returns <base_config_dir>/<app_name>.

    Platform mappings:
    - Linux: $XDG_CONFIG_HOME or ~/.config
    - macOS: ~/Library/Application Support (for .config convention) or ~/.config
    - Windows: %APPDATA% (Roaming) with fallback to %USERPROFILE%/AppData/Roaming

    Args:
        app_name: Application name (e.g., "myco", "continue")

    Returns:
        Path to config directory specific to app_name
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            base = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux and other Unix-like systems
        xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
        if xdg_config:
            base = Path(xdg_config)
        else:
            base = Path.home() / ".config"

    return base / app_name


def user_data_dir(app_name: str) -> Path:
    """
    Get OS-aware user data directory for an application.

    Platform mappings:
    - Linux: ~/.local/share/<app_name>
    - macOS: ~/Library/Application Support/<app_name>
    - Windows: %LOCALAPPDATA%/<app_name>

    Args:
        app_name: Application name

    Returns:
        Path to data directory specific to app_name
    """
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            base = Path(localappdata)
        else:
            base = Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux and other Unix-like systems
        xdg_data = os.environ.get("XDG_DATA_HOME", "")
        if xdg_data:
            base = Path(xdg_data)
        else:
            base = Path.home() / ".local" / "share"

    return base / app_name


def vscode_global_storage_dir() -> Path:
    """
    Get OS-specific path to VS Code globalStorage directory.

    Used by Cline, Windsurf, and other VS Code extensions.

    Platform mappings:
    - Linux: ~/.config/Code/User/globalStorage
    - macOS: ~/Library/Application Support/Code/User/globalStorage
    - Windows: %APPDATA%/Code/User/globalStorage

    Returns:
        Path to VS Code globalStorage directory
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            base = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux
        base = Path.home() / ".config"

    return base / "Code" / "User" / "globalStorage"


def safe_read_json(path: Path) -> dict:
    """
    Safely read a JSON file, returning {} if missing or unparseable.

    Never raises exceptions — always returns a dict.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON object (dict) or {} if file missing/invalid
    """
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, OSError, UnicodeDecodeError):
        return {}


def safe_read_toml(path: Path) -> dict:
    """
    Safely read a TOML file using tomllib (Python 3.11+).

    Returns {} if file missing or unparseable. Never raises.

    Args:
        path: Path to TOML file

    Returns:
        Parsed TOML object (dict) or {} if file missing/invalid
    """
    if not path.exists():
        return {}

    try:
        import tomllib  # Python 3.11+

        with open(path, "rb") as f:
            return tomllib.load(f)
    except (ImportError, Exception):
        # tomllib not available or parse error
        return {}


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge *override* into *base*, preserving nested dicts.

    Used by json_merge_write to deep-merge configuration patches.

    Args:
        base: Base dictionary to merge into
        override: Dictionary to merge from

    Returns:
        Merged dictionary
    """
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def json_merge_write(path: Path, patch: dict, marker_key: Optional[str] = None) -> bool:
    """
    Idempotently merge *patch* into JSON file at *path*.

    Deep-merges nested dictionaries so that existing top-level keys
    (e.g., ``mcpServers.other``) are preserved when adding
    ``mcpServers.myco``.

    Creates parent directories if needed. For non-dict types at the same
    key, *patch* value replaces the existing value.

    Args:
        path: Path to JSON file (created if missing)
        patch: Dictionary to merge in
        marker_key: Unused (reserved for future marker-based tracking)

    Returns:
        True if file changed (created or merged), False if no change
    """
    existing_content = ""
    if path.exists():
        try:
            existing_content = path.read_text(encoding="utf-8")
            existing = json.loads(existing_content)
        except (json.JSONDecodeError, ValueError, OSError):
            # Invalid JSON — write patch as-is, treating as changed
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
            return True
        merged = _deep_merge(existing, patch)
    else:
        # File doesn't exist — create with patch
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
        return True

    # Check if merged content differs from existing
    new_content = json.dumps(merged, indent=2) + "\n"
    if new_content == existing_content:
        return False  # No change

    path.write_text(new_content, encoding="utf-8")
    return True


def ensure_marker_block(path: Path, marker: str, content: str) -> bool:
    """
    Ensure a marker-bracketed block exists in a text file.

    For markdown/text files: find a block bracketed by comment markers
    (e.g., ``<!-- myco-boot: v1 -->``) and update its contents, or
    append the block if it doesn't exist.

    Marker format: ``<!-- myco-<marker>: v1 -->``. The block spans
    from the opening marker to ``<!-- /myco-<marker> -->``.

    Example:
        >>> path = Path("README.md")
        >>> ensure_marker_block(path, "boot", "# Auto-generated boot section")
        # Finds or creates: <!-- myco-boot: v1 -->...<!-- /myco-boot -->

    Args:
        path: Path to text file
        marker: Marker identifier (e.g., "boot", "config")
        content: Content to place inside the marker block

    Returns:
        True if file changed (created or updated), False if no change
    """
    open_marker = f"<!-- myco-{marker}: v1 -->"
    close_marker = f"<!-- /myco-{marker} -->"
    new_block = f"{open_marker}\n{content}\n{close_marker}"

    if not path.exists():
        # Create file with marker block
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_block + "\n", encoding="utf-8")
        return True

    try:
        existing = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Can't read — write new block
        path.write_text(new_block + "\n", encoding="utf-8")
        return True

    # Check if marker block already exists
    if open_marker in existing and close_marker in existing:
        # Replace existing block
        start = existing.index(open_marker)
        end = existing.index(close_marker) + len(close_marker)
        updated = existing[:start] + new_block + existing[end:]
    else:
        # Append new block
        updated = existing.rstrip() + "\n\n" + new_block + "\n"

    if updated == existing:
        return False  # No change

    path.write_text(updated, encoding="utf-8")
    return True


def toml_merge_write(path: Path, section: str, entries: dict) -> bool:
    """
    Idempotently merge entries into a TOML section at path.

    For known-schema TOML files (e.g., Codex config.toml). Targets a
    specific section (e.g., ``mcp_servers.myco``) and ensures entries
    are present.

    Example:
        >>> toml_merge_write(
        ...     Path.home() / ".codex" / "config.toml",
        ...     section="mcp_servers.myco",
        ...     entries={"command": "python", "args": ["-m", "myco.mcp_server"]}
        ... )

    Args:
        path: Path to TOML file
        section: Dot-separated section name (e.g., "mcp_servers.myco")
        entries: Dictionary of key-value pairs to merge into the section

    Returns:
        True if file changed (created or merged), False if no change
    """
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Can't read — create new
            existing = ""
    else:
        existing = ""

    # Check if section already exists (naive but correct for known schemas)
    section_header = f"[{section}]"
    if section_header in existing:
        # Section already present — skip (idempotency)
        return False

    # Append section with entries (hand-formatted for simplicity)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [section_header]
    for key, value in entries.items():
        if isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, list):
            # Format list as TOML array
            items = ', '.join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
            lines.append(f'{key} = [{items}]')
        else:
            lines.append(f"{key} = {value}")

    new_block = "\n".join(lines)
    if existing:
        updated = existing.rstrip() + "\n\n" + new_block + "\n"
    else:
        updated = new_block + "\n"

    path.write_text(updated, encoding="utf-8")
    return True
