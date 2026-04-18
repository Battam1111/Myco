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
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

# tomllib is stdlib on Python 3.11+. Myco's pyproject floor is 3.10,
# so on 3.10 we fall back to tomli (if installed) and finally to a
# narrow regex parser that only understands our own ``[mcp_servers.myco]``
# block — which is all we ever need to read or write anyway.
try:  # Python 3.11+
    import tomllib as _tomllib  # type: ignore[import-not-found]
    _HAVE_TOMLLIB = True
except ImportError:  # pragma: no cover — 3.10 path
    try:
        import tomli as _tomllib  # type: ignore[import-not-found,no-redef]
        _HAVE_TOMLLIB = True
    except ImportError:
        _tomllib = None  # type: ignore[assignment]
        _HAVE_TOMLLIB = False

import yaml


class MycoInstallError(Exception):
    """Raised on user-recoverable install failures. Does not indicate
    a bug — the user sees the message and acts.
    """


# GUI MCP hosts (Claude Desktop, Cursor, Windsurf, Zed) do NOT
# inherit the user's shell PATH. Bare "mcp-server-myco" → ENOENT.
# Fix: use the absolute Python executable path that has myco installed
# plus "-m myco.mcp". This is the MCP-docs-recommended pattern for
# Python servers and guarantees the right interpreter finds the
# right package regardless of PATH or venv state.
#
# Terminal hosts (Claude Code, Codex CLI, Gemini CLI) DO inherit PATH,
# so the bare console script works there. The .mcp.json at repo root
# still uses "mcp-server-myco" for that reason. But myco-install
# targets GUI-heavy users, so we default to the robust absolute form.
MCP_COMMAND = sys.executable  # e.g. "/usr/bin/python3" or "C:\Python313\python.exe"
MCP_ARGS: list[str] = ["-m", "myco.mcp"]


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
# YAML helpers (Goose-style ``extensions`` schema)
# ---------------------------------------------------------------------------


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise MycoInstallError(
            f"existing config at {path} is not valid YAML: {exc}. "
            f"Fix it or back it up before re-running."
        ) from exc
    if not isinstance(data, dict):
        raise MycoInstallError(
            f"existing config at {path} is not a YAML mapping "
            f"(got {type(data).__name__}). Fix it or back it up."
        )
    return data


def _write_yaml(path: Path, data: dict, dry_run: bool) -> str:
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if dry_run:
        return f"[dry-run] would write {path}:\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return f"wrote {path}"


def _mutate_yaml_extensions(
    path: Path,
    dry_run: bool,
    uninstall: bool,
    *,
    entry: dict[str, Any] | None = None,
) -> str:
    """Add or remove ``extensions.myco`` in a YAML config file.

    Goose (``~/.config/goose/config.yaml``) is the only client using
    this shape today. Sibling ``extensions.*`` entries are preserved.
    """
    data = _read_yaml(path)
    exts = data.setdefault("extensions", {})
    if not isinstance(exts, dict):
        raise MycoInstallError(
            f"{path}: 'extensions' key exists but is not a mapping."
        )
    if uninstall:
        exts.pop("myco", None)
    else:
        exts["myco"] = entry or {
            "type": "stdio",
            "command": MCP_COMMAND,
            "args": MCP_ARGS,
            "enabled": True,
        }
    return _write_yaml(path, data, dry_run)


# ---------------------------------------------------------------------------
# TOML helpers (Codex CLI ``[mcp_servers.<name>]`` schema)
# ---------------------------------------------------------------------------


# Match the entire ``[mcp_servers.myco]`` block: the header line plus
# every subsequent line until the next TOML table header (``[...]``)
# or end of file. Anchored to start-of-line so it does not match a
# comment or string that happens to contain ``[mcp_servers.myco]``.
_CODEX_MYCO_BLOCK = re.compile(
    r"(?ms)^\[mcp_servers\.myco\]\s*\n"      # header
    r"(?:(?!^\[).*\n?)*"                     # body up to next [header]
)


def _render_codex_myco_block() -> str:
    """Hand-render the ``[mcp_servers.myco]`` TOML section.

    We render by hand rather than pull in a TOML writer dependency:
    the block is small, the schema is fixed, and the string encoding
    is unambiguous (command is a filesystem path, args are short
    flag tokens — no embedded quotes or newlines).
    """
    args_toml = "[" + ", ".join(json.dumps(a) for a in MCP_ARGS) + "]"
    return (
        "[mcp_servers.myco]\n"
        f"command = {json.dumps(MCP_COMMAND)}\n"
        f"args = {args_toml}\n"
    )


def _mutate_codex_toml(path: Path, dry_run: bool, uninstall: bool) -> str:
    """Upsert or remove ``[mcp_servers.myco]`` in ``~/.codex/config.toml``.

    We never fully re-serialize the TOML file — that would destroy
    user comments and formatting. Instead we do block-level surgery
    on the raw text, preserving everything outside our own section.

    If ``tomllib`` is available we validate the existing file parses
    before touching it (so we fail loud on a pre-existing syntax
    error rather than silently clobbering a broken config).
    """
    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    # Validate existing TOML parses (when we can). Missing file or
    # empty file are both fine; we are about to write a fresh block.
    if existing.strip() and _HAVE_TOMLLIB:
        try:
            _tomllib.loads(existing)  # type: ignore[union-attr]
        except Exception as exc:  # tomllib raises TOMLDecodeError
            raise MycoInstallError(
                f"existing config at {path} is not valid TOML: {exc}. "
                f"Fix it or back it up before re-running."
            ) from exc

    # Strip any pre-existing ``[mcp_servers.myco]`` block.
    stripped = _CODEX_MYCO_BLOCK.sub("", existing)
    # Normalize trailing whitespace so repeated runs are idempotent.
    stripped = stripped.rstrip() + ("\n" if stripped.strip() else "")

    if uninstall:
        body = stripped
    else:
        block = _render_codex_myco_block()
        if stripped:
            body = stripped.rstrip() + "\n\n" + block
        else:
            body = block

    if dry_run:
        return f"[dry-run] would write {path}:\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return f"wrote {path}"


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


def install_gemini_cli(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """Gemini CLI reads ``~/.gemini/settings.json`` with the standard
    ``mcpServers`` schema. ``--global`` is a no-op here — there is
    only one settings path.
    """
    path = home / ".gemini" / "settings.json"
    return _mutate_mcp_servers_json(path, dry_run, uninstall)


def install_codex_cli(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """Codex CLI uses ``~/.codex/config.toml`` with a nested
    ``[mcp_servers.<name>]`` table per server. We do block-level
    surgery on the raw text so that other tables and user comments
    survive untouched. ``--global`` is ignored; there is only one path.
    """
    path = home / ".codex" / "config.toml"
    return _mutate_codex_toml(path, dry_run, uninstall)


def install_goose(
    home: Path, cwd: Path, dry_run: bool, global_: bool, uninstall: bool
) -> str:
    """Goose reads ``~/.config/goose/config.yaml`` with its own
    ``extensions.<name>`` schema (not ``mcpServers``). ``--global``
    is ignored; there is only one settings path.
    """
    path = home / ".config" / "goose" / "config.yaml"
    return _mutate_yaml_extensions(path, dry_run, uninstall)


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
    "gemini-cli": install_gemini_cli,
    "codex-cli": install_codex_cli,
    "goose": install_goose,
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
