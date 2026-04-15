"""Per-client MCP config writers.

Each writer is idempotent: running it twice produces the same file
contents. Running it after a user has added their own servers
preserves those servers. Running it with ``uninstall=True`` removes
only the ``myco`` entry and leaves sibling entries alone.

All writers take a ``home`` and ``cwd`` parameter for testability.
In production :func:`dispatch` fills them with ``Path.home()`` and
``Path.cwd()``.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


class MycoInstallError(Exception):
    """Raised on user-recoverable install failures. Does not indicate
    a bug — the user sees the message and acts.
    """


MCP_COMMAND = "mcp-server-myco"
MCP_ARGS: list[str] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise MycoInstallError(
            f"existing config at {path} is not valid JSON: {exc}. "
            f"Fix it or back it up before re-running."
        ) from exc


def _write_json(path: Path, data: dict, dry_run: bool) -> str:
    body = json.dumps(data, indent=2, ensure_ascii=False)
    if dry_run:
        return f"[dry-run] would write {path}:\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return f"wrote {path}"


def _mutate_mcp_servers_json(
    path: Path,
    dry_run: bool,
    uninstall: bool,
    *,
    key: str = "mcpServers",
    entry: dict | None = None,
) -> str:
    """Add or remove an entry under a named top-level dict in a JSON
    config file.

    Shared core for every client whose config is JSON with a
    ``mcpServers``-style key (Claude, Cursor, Windsurf, Roo, Cline,
    Gemini — and parametrizable to the VS Code ``servers`` variant).
    """
    data = _read_json(path)
    data.setdefault(key, {})
    if uninstall:
        data[key].pop("myco", None)
    else:
        data[key]["myco"] = entry or {"command": MCP_COMMAND, "args": MCP_ARGS}
    return _write_json(path, data, dry_run)


def _appdata(home: Path) -> Path:
    """Windows %APPDATA% / macOS Application Support / XDG config dir,
    resolved relative to the injected ``home`` (not the real user's
    environment). Tests override ``home`` to ``tmp_path``; in
    production it is ``Path.home()`` and the function falls back to
    env vars for XDG / APPDATA overrides.
    """
    if sys.platform == "darwin":
        return home / "Library" / "Application Support"
    if sys.platform == "win32":
        # Only honor %APPDATA% when home is the real home; otherwise
        # stay inside the injected home so tests do not escape tmp_path.
        if home == Path.home():
            return Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
        return home / "AppData" / "Roaming"
    if home == Path.home():
        return Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
    return home / ".config"


# ---------------------------------------------------------------------------
# Individual client writers
# ---------------------------------------------------------------------------


def install_claude_code(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """Claude Code auto-loads ``.mcp.json`` (project) or ``~/.claude.json``
    (user scope). The repo's own ``.mcp.json`` already wires myco, so
    this writer is chiefly for users who want a new standalone project
    without cloning this repo.
    """
    path = home / ".claude.json" if global_ else cwd / ".mcp.json"
    return _mutate_mcp_servers_json(path, dry_run, uninstall)


def install_claude_desktop(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """``claude_desktop_config.json`` location varies by OS; this picks
    the right one per :mod:`sys.platform`, anchored to the injected
    ``home`` so tests stay inside ``tmp_path``.
    """
    path = _appdata(home) / "Claude" / "claude_desktop_config.json"
    return _mutate_mcp_servers_json(path, dry_run, uninstall)


def install_cursor(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    path = home / ".cursor" / "mcp.json" if global_ else cwd / ".cursor" / "mcp.json"
    return _mutate_mcp_servers_json(path, dry_run, uninstall)


def install_windsurf(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    path = home / ".codeium" / "windsurf" / "mcp_config.json"
    return _mutate_mcp_servers_json(path, dry_run, uninstall)


def install_zed(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """Zed uses ``context_servers`` with an explicit ``source: custom``
    field rather than ``mcpServers``.
    """
    path = home / ".config" / "zed" / "settings.json"
    return _mutate_mcp_servers_json(
        path, dry_run, uninstall,
        key="context_servers",
        entry={"source": "custom", "command": MCP_COMMAND, "args": MCP_ARGS},
    )


def install_vscode(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """VS Code GitHub Copilot uses ``servers`` (not ``mcpServers``)
    inside ``.vscode/mcp.json``.
    """
    path = cwd / ".vscode" / "mcp.json"
    return _mutate_mcp_servers_json(
        path, dry_run, uninstall,
        key="servers",
        entry={"type": "stdio", "command": MCP_COMMAND, "args": MCP_ARGS},
    )


def install_openclaw(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """OpenClaw uses a nested ``mcp.servers.<name>`` schema and its own
    CLI to mutate config. We shell out to ``openclaw`` rather than
    re-parse whatever config file it happens to live in, because the
    CLI guarantees schema correctness across versions.
    """
    if shutil.which("openclaw") is None:
        raise MycoInstallError(
            "openclaw CLI not found on PATH. Install OpenClaw first "
            "(https://github.com/openclaw/openclaw), then re-run."
        )
    if uninstall:
        cmd = ["openclaw", "mcp", "remove", "myco"]
    else:
        payload = json.dumps({"command": MCP_COMMAND, "args": MCP_ARGS})
        cmd = ["openclaw", "mcp", "set", "myco", payload]
    if dry_run:
        return f"[dry-run] would run: {' '.join(cmd)}"
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MycoInstallError(
            f"openclaw returned {result.returncode}:\n"
            f"{result.stdout}{result.stderr}"
        )
    return (result.stdout + result.stderr).strip() or "openclaw: OK"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


ClientFunc = Callable[..., str]

CLIENTS: dict[str, ClientFunc] = {
    "claude-code": install_claude_code,
    "claude-desktop": install_claude_desktop,
    "cursor": install_cursor,
    "windsurf": install_windsurf,
    "zed": install_zed,
    "vscode": install_vscode,
    "openclaw": install_openclaw,
}


def dispatch(
    client: str,
    *,
    dry_run: bool,
    global_: bool,
    uninstall: bool,
    home: Path | None = None,
    cwd: Path | None = None,
) -> str:
    if client not in CLIENTS:
        raise MycoInstallError(
            f"unknown client {client!r}. Choose from: {sorted(CLIENTS)}."
        )
    return CLIENTS[client](
        home or Path.home(),
        cwd or Path.cwd(),
        dry_run, global_, uninstall,
    )
