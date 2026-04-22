"""Tests for the per-client install writers.

Uses ``tmp_path`` as a stand-in ``home`` / ``cwd`` so no real user
config is touched. Idempotency and sibling-preservation are pinned
because those are what make the helper safe to re-run.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from myco.install.clients import (
    MCP_ARGS,
    MCP_COMMAND,
    MycoInstallError,
    dispatch,
)

# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def _install(client: str, tmp_path: Path, **kwargs) -> str:
    return dispatch(
        client,
        dry_run=kwargs.pop("dry_run", False),
        global_=kwargs.pop("global_", False),
        uninstall=kwargs.pop("uninstall", False),
        home=tmp_path,
        cwd=tmp_path,
    )


# ---------------------------------------------------------------------------
# Universal behaviors
# ---------------------------------------------------------------------------


def test_dispatch_rejects_unknown_client(tmp_path: Path) -> None:
    with pytest.raises(MycoInstallError) as exc_info:
        dispatch(
            "does-not-exist",
            dry_run=False,
            global_=False,
            uninstall=False,
            home=tmp_path,
            cwd=tmp_path,
        )
    assert "unknown client" in str(exc_info.value).lower()


@pytest.mark.parametrize(
    "client",
    [
        "claude-code",
        "claude-desktop",
        "cursor",
        "windsurf",
        "zed",
        "vscode",
        "gemini-cli",
    ],
)
def test_install_creates_or_updates_file_for_json_clients(
    client: str, tmp_path: Path
) -> None:
    """Every JSON-schema client should produce a JSON file that uses
    the absolute-python-path form (sys.executable + -m myco.mcp)
    so GUI apps that don't inherit PATH can find the server.
    """
    _install(client, tmp_path)
    produced = list(tmp_path.rglob("*.json"))
    assert produced, f"{client} did not create any JSON file under {tmp_path}"
    text = produced[0].read_text(encoding="utf-8")
    # The command should contain "python" (the absolute interpreter path)
    # and the args should contain "-m" and "myco.mcp"
    assert "myco.mcp" in text, (client, produced[0], text)
    assert "-m" in text, (client, produced[0], text)


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    output = _install("cursor", tmp_path, dry_run=True)
    assert "[dry-run]" in output
    assert list(tmp_path.rglob("*.json")) == []


# ---------------------------------------------------------------------------
# Idempotency + sibling preservation (cursor as representative)
# ---------------------------------------------------------------------------


def test_cursor_install_preserves_existing_sibling_servers(tmp_path: Path) -> None:
    cfg = tmp_path / ".cursor" / "mcp.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "other-server": {"command": "other", "args": ["--flag"]},
                },
            }
        ),
        encoding="utf-8",
    )

    _install("cursor", tmp_path)

    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "other-server" in data["mcpServers"]
    assert data["mcpServers"]["other-server"]["command"] == "other"
    assert data["mcpServers"]["myco"]["command"] == MCP_COMMAND


def test_cursor_install_is_idempotent(tmp_path: Path) -> None:
    _install("cursor", tmp_path)
    first = (tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8")
    _install("cursor", tmp_path)
    second = (tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8")
    assert first == second


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------


def test_uninstall_removes_only_myco_entry(tmp_path: Path) -> None:
    cfg = tmp_path / ".cursor" / "mcp.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "other-server": {"command": "other", "args": []},
                    "myco": {"command": MCP_COMMAND, "args": []},
                },
            }
        ),
        encoding="utf-8",
    )

    _install("cursor", tmp_path, uninstall=True)

    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "myco" not in data["mcpServers"]
    assert "other-server" in data["mcpServers"]


# ---------------------------------------------------------------------------
# Schema variants
# ---------------------------------------------------------------------------


def test_zed_uses_context_servers_key_not_mcp_servers(tmp_path: Path) -> None:
    _install("zed", tmp_path)
    path = tmp_path / ".config" / "zed" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "context_servers" in data
    assert "mcpServers" not in data
    assert data["context_servers"]["myco"]["source"] == "custom"


def test_vscode_uses_servers_key_not_mcp_servers(tmp_path: Path) -> None:
    _install("vscode", tmp_path)
    path = tmp_path / ".vscode" / "mcp.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "servers" in data
    assert "mcpServers" not in data
    assert data["servers"]["myco"]["type"] == "stdio"


# ---------------------------------------------------------------------------
# OpenClaw (shell-out client)
# ---------------------------------------------------------------------------


def test_openclaw_errors_cleanly_when_cli_absent(tmp_path: Path) -> None:
    with patch("myco.install.clients.shutil.which", return_value=None):
        with pytest.raises(MycoInstallError) as exc_info:
            _install("openclaw", tmp_path)
    assert "openclaw CLI not found" in str(exc_info.value)


def test_openclaw_dry_run_shows_command_without_running(tmp_path: Path) -> None:
    with patch("myco.install.clients.shutil.which", return_value="/fake/openclaw"):
        output = _install("openclaw", tmp_path, dry_run=True)
    assert "[dry-run]" in output
    assert "openclaw mcp set myco" in output


def test_openclaw_invokes_cli_on_real_install(tmp_path: Path) -> None:
    fake_result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="ok\n",
        stderr="",
    )
    with (
        patch("myco.install.clients.shutil.which", return_value="/fake/openclaw"),
        patch(
            "myco.install.clients.subprocess.run", return_value=fake_result
        ) as runner,
    ):
        _install("openclaw", tmp_path)
    assert runner.called
    called_cmd = runner.call_args[0][0]
    assert called_cmd[:4] == ["openclaw", "mcp", "set", "myco"]
    payload = json.loads(called_cmd[4])
    # OpenClaw gets the absolute-path form too
    assert "python" in payload["command"].lower()
    assert payload["args"] == MCP_ARGS


# ---------------------------------------------------------------------------
# Gemini CLI (JSON via the shared mcpServers helper)
# ---------------------------------------------------------------------------


def test_gemini_cli_lands_at_gemini_settings_json(tmp_path: Path) -> None:
    """Gemini CLI reads ``~/.gemini/settings.json`` — make sure that's
    exactly where the writer lands (no stray files elsewhere).
    """
    _install("gemini-cli", tmp_path)
    path = tmp_path / ".gemini" / "settings.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["mcpServers"]["myco"]["command"] == MCP_COMMAND
    assert data["mcpServers"]["myco"]["args"] == MCP_ARGS


def test_gemini_cli_preserves_siblings_and_uninstalls_cleanly(
    tmp_path: Path,
) -> None:
    cfg = tmp_path / ".gemini" / "settings.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        json.dumps(
            {
                "theme": "dark",
                "mcpServers": {
                    "other": {"command": "other", "args": []},
                },
            }
        ),
        encoding="utf-8",
    )

    _install("gemini-cli", tmp_path)
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["theme"] == "dark"
    assert "other" in data["mcpServers"]
    assert "myco" in data["mcpServers"]

    _install("gemini-cli", tmp_path, uninstall=True)
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["theme"] == "dark"
    assert "other" in data["mcpServers"]
    assert "myco" not in data["mcpServers"]


# ---------------------------------------------------------------------------
# Codex CLI (TOML with ``[mcp_servers.<name>]`` nesting)
# ---------------------------------------------------------------------------


def _read_codex_toml(path: Path) -> dict:
    """Test-side TOML read. ``tomllib`` is stdlib on 3.11+; fall back
    to ``tomli`` (dev extra) on 3.10, else parse by hand — tests run
    under whatever Python the dev has.
    """
    text = path.read_text(encoding="utf-8")
    try:
        import tomllib  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover — 3.10 path
        import tomli as tomllib  # type: ignore[no-redef]
    return tomllib.loads(text)


def test_codex_cli_toml_adds_and_preserves_entries(tmp_path: Path) -> None:
    """Seed an existing TOML with another ``[mcp_servers.other]`` and
    a top-level user comment; after install both the sibling section
    and the comment must survive; after uninstall myco is gone but
    the sibling stays.
    """
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "# user comment preserved across re-runs\n"
        "[mcp_servers.other]\n"
        'command = "/usr/bin/other"\n'
        'args = ["--flag"]\n',
        encoding="utf-8",
    )

    _install("codex-cli", tmp_path)
    text = cfg.read_text(encoding="utf-8")
    assert "# user comment preserved across re-runs" in text
    parsed = _read_codex_toml(cfg)
    assert parsed["mcp_servers"]["other"]["command"] == "/usr/bin/other"
    assert parsed["mcp_servers"]["myco"]["command"] == MCP_COMMAND
    assert parsed["mcp_servers"]["myco"]["args"] == MCP_ARGS

    _install("codex-cli", tmp_path, uninstall=True)
    text_after = cfg.read_text(encoding="utf-8")
    assert "# user comment preserved across re-runs" in text_after
    parsed_after = _read_codex_toml(cfg)
    assert "other" in parsed_after["mcp_servers"]
    assert "myco" not in parsed_after.get("mcp_servers", {})


def test_codex_cli_toml_idempotent(tmp_path: Path) -> None:
    """Running the installer twice in a row produces byte-identical
    files — the second run is a no-op.
    """
    _install("codex-cli", tmp_path)
    first = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    _install("codex-cli", tmp_path)
    second = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert first == second


def test_codex_cli_dry_run_previews_without_writing(tmp_path: Path) -> None:
    output = _install("codex-cli", tmp_path, dry_run=True)
    assert "[dry-run]" in output
    assert "[mcp_servers.myco]" in output
    assert not (tmp_path / ".codex" / "config.toml").exists()


def test_codex_cli_rejects_malformed_existing_toml(tmp_path: Path) -> None:
    """If the user's existing config.toml is broken, we refuse rather
    than silently clobber it (only when tomllib is available).
    """
    import myco.install.clients as _clients

    if not _clients._HAVE_TOMLLIB:
        pytest.skip("tomllib not available; validation path inactive")
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("this = is = not valid\n", encoding="utf-8")
    with pytest.raises(MycoInstallError) as exc_info:
        _install("codex-cli", tmp_path)
    assert "not valid TOML" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Goose (YAML with ``extensions.<name>`` nesting — not ``mcpServers``)
# ---------------------------------------------------------------------------


def test_goose_yaml_uses_extensions_key(tmp_path: Path) -> None:
    """Goose's schema is ``extensions:`` at the top level. We must
    NOT write ``mcpServers`` — that would be invisible to Goose.
    """
    import yaml

    _install("goose", tmp_path)
    path = tmp_path / ".config" / "goose" / "config.yaml"
    assert path.exists()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "extensions" in data
    assert "mcpServers" not in data
    myco_entry = data["extensions"]["myco"]
    assert myco_entry["type"] == "stdio"
    assert myco_entry["command"] == MCP_COMMAND
    assert myco_entry["args"] == MCP_ARGS
    assert myco_entry["enabled"] is True


def test_goose_yaml_preserves_other_extensions(tmp_path: Path) -> None:
    """Sibling ``extensions.*`` entries (and unrelated top-level
    keys) must survive both install and uninstall.
    """
    import yaml

    cfg = tmp_path / ".config" / "goose" / "config.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        yaml.safe_dump(
            {
                "provider": "anthropic",
                "extensions": {
                    "developer": {
                        "type": "stdio",
                        "command": "developer",
                        "args": [],
                        "enabled": True,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    _install("goose", tmp_path)
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    assert data["provider"] == "anthropic"
    assert "developer" in data["extensions"]
    assert "myco" in data["extensions"]

    _install("goose", tmp_path, uninstall=True)
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    assert data["provider"] == "anthropic"
    assert "developer" in data["extensions"]
    assert "myco" not in data["extensions"]


def test_goose_yaml_idempotent(tmp_path: Path) -> None:
    _install("goose", tmp_path)
    first = (tmp_path / ".config" / "goose" / "config.yaml").read_text(encoding="utf-8")
    _install("goose", tmp_path)
    second = (tmp_path / ".config" / "goose" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert first == second


# ---------------------------------------------------------------------------
# v0.5.15: cowork alias + detect_installed_hosts + --all-hosts
# ---------------------------------------------------------------------------


def test_cowork_alias_writes_claude_desktop_config(tmp_path: Path) -> None:
    """``cowork`` is an alias for ``claude-desktop`` — same config file
    because Cowork runs inside Claude Desktop.

    Uses ``_appdata`` to compute the expected path so the assertion
    holds on every platform: Windows maps ``%APPDATA%`` to
    ``~/AppData/Roaming``, macOS to ``~/Library/Application Support``,
    Linux to ``$XDG_CONFIG_HOME`` or ``~/.config``.
    """
    from myco.install.clients import _appdata

    dispatch("cowork", dry_run=False, global_=False, uninstall=False, home=tmp_path)
    cfg = _appdata(tmp_path) / "Claude" / "claude_desktop_config.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "myco" in data["mcpServers"]


def test_detect_installed_hosts_all_missing_returns_all_none(tmp_path: Path) -> None:
    """On a fresh home with no host ever run, every signal is ``None``."""
    from myco.install.clients import CLIENTS, detect_installed_hosts

    signals = detect_installed_hosts(home=tmp_path)
    assert set(signals) == set(CLIENTS)
    assert all(v is None for v in signals.values()), signals


def test_detect_installed_hosts_finds_claude_code(tmp_path: Path) -> None:
    """Creating ``~/.claude/`` makes the probe return a Path."""
    from myco.install.clients import detect_installed_hosts

    (tmp_path / ".claude").mkdir()
    signals = detect_installed_hosts(home=tmp_path)
    assert signals["claude-code"] is not None
    # Other hosts still None — single dir doesn't mask everything else.
    assert signals["cursor"] is None
    assert signals["goose"] is None


def test_detect_installed_hosts_finds_multiple(tmp_path: Path) -> None:
    """Probes are independent — multiple dirs detected in parallel."""
    from myco.install.clients import detect_installed_hosts

    (tmp_path / ".claude").mkdir()
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".codex").mkdir()
    signals = detect_installed_hosts(home=tmp_path)
    assert signals["claude-code"] is not None
    assert signals["cursor"] is not None
    assert signals["codex-cli"] is not None
    assert signals["goose"] is None


def test_detect_installed_hosts_cowork_matches_claude_desktop(tmp_path: Path) -> None:
    """Cowork and claude-desktop share a signal (both point at
    ``%APPDATA%/Claude/``). Either detected ⇒ both detected."""
    from myco.install.clients import _appdata, detect_installed_hosts

    (_appdata(tmp_path) / "Claude").mkdir(parents=True)
    signals = detect_installed_hosts(home=tmp_path)
    assert signals["claude-desktop"] is not None
    assert signals["cowork"] is not None
