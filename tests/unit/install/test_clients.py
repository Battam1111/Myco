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
    CLIENTS,
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
        dispatch("does-not-exist",
                 dry_run=False, global_=False, uninstall=False,
                 home=tmp_path, cwd=tmp_path)
    assert "unknown client" in str(exc_info.value).lower()


@pytest.mark.parametrize("client", [
    "claude-code", "claude-desktop", "cursor",
    "windsurf", "zed", "vscode",
])
def test_install_creates_or_updates_file_for_json_clients(
    client: str, tmp_path: Path
) -> None:
    """Every JSON-schema client should produce a JSON file containing
    the myco command. Shape varies (key name, entry fields) but the
    command string is invariant.
    """
    _install(client, tmp_path)
    # Walk tmp to find the produced JSON file
    produced = list(tmp_path.rglob("*.json"))
    assert produced, f"{client} did not create any JSON file under {tmp_path}"
    text = produced[0].read_text(encoding="utf-8")
    assert MCP_COMMAND in text, (client, produced[0], text)


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
    cfg.write_text(json.dumps({
        "mcpServers": {
            "other-server": {"command": "other", "args": ["--flag"]},
        },
    }), encoding="utf-8")

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
    cfg.write_text(json.dumps({
        "mcpServers": {
            "other-server": {"command": "other", "args": []},
            "myco": {"command": MCP_COMMAND, "args": []},
        },
    }), encoding="utf-8")

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
        args=[], returncode=0, stdout="ok\n", stderr="",
    )
    with patch("myco.install.clients.shutil.which", return_value="/fake/openclaw"), \
         patch("myco.install.clients.subprocess.run", return_value=fake_result) as runner:
        _install("openclaw", tmp_path)
    assert runner.called
    called_cmd = runner.call_args[0][0]
    assert called_cmd[:4] == ["openclaw", "mcp", "set", "myco"]
    payload = json.loads(called_cmd[4])
    assert payload["command"] == MCP_COMMAND
