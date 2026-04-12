"""Unit tests for myco init --auto-detect (auto-detection and MCP config generation)."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from myco.init_cmd import (
    detect_tools,
    run_auto_detect,
    _gen_claude_code,
    _gen_cursor,
    _gen_vscode,
    _gen_codex,
    _gen_cline,
    _gen_continue,
    _gen_zed,
    _gen_claude_md,
    _json_merge_write,
    _toml_merge_write,
)


# ---------------------------------------------------------------------------
# detect_tools
# ---------------------------------------------------------------------------

class TestDetectTools:
    """Tests for detect_tools()."""

    def test_detects_claude_on_path(self, tmp_path):
        with patch("myco.init_cmd.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/claude" if cmd == "claude" else None
            result = detect_tools(tmp_path)
        assert result["Claude Code"] is True

    def test_detects_cursor_dir(self, tmp_path):
        (tmp_path / ".cursor").mkdir()
        with patch("myco.init_cmd.shutil.which", return_value=None):
            result = detect_tools(tmp_path)
        assert result["Cursor"] is True

    def test_detects_cursor_on_path(self, tmp_path):
        with patch("myco.init_cmd.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/cursor" if cmd == "cursor" else None
            result = detect_tools(tmp_path)
        assert result["Cursor"] is True

    def test_detects_vscode_dir(self, tmp_path):
        (tmp_path / ".vscode").mkdir()
        with patch("myco.init_cmd.shutil.which", return_value=None):
            result = detect_tools(tmp_path)
        assert result["VS Code"] is True

    def test_detects_vscode_on_path(self, tmp_path):
        with patch("myco.init_cmd.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/code" if cmd == "code" else None
            result = detect_tools(tmp_path)
        assert result["VS Code"] is True

    def test_detects_codex_dir(self, tmp_path):
        codex_dir = Path.home() / ".codex"
        if codex_dir.is_dir():
            # Already exists on this system
            with patch("myco.init_cmd.shutil.which", return_value=None):
                result = detect_tools(tmp_path)
            assert result["Codex"] is True
        else:
            # Mock the home directory check
            with patch("myco.init_cmd.shutil.which", return_value=None), \
                 patch("myco.init_cmd.Path.home") as mock_home:
                fake_home = tmp_path / "fakehome"
                fake_home.mkdir()
                (fake_home / ".codex").mkdir()
                mock_home.return_value = fake_home
                result = detect_tools(tmp_path)
            assert result["Codex"] is True

    def test_detects_cline_settings(self, tmp_path):
        (tmp_path / "cline_mcp_settings.json").write_text("{}", encoding="utf-8")
        with patch("myco.init_cmd.shutil.which", return_value=None):
            result = detect_tools(tmp_path)
        assert result["Cline"] is True

    def test_detects_continue_dir(self, tmp_path):
        (tmp_path / ".continue").mkdir()
        with patch("myco.init_cmd.shutil.which", return_value=None):
            result = detect_tools(tmp_path)
        assert result["Continue"] is True

    def test_detects_zed_on_path(self, tmp_path):
        with patch("myco.init_cmd.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/zed" if cmd == "zed" else None
            result = detect_tools(tmp_path)
        assert result["Zed"] is True

    def test_nothing_detected(self, tmp_path):
        with patch("myco.init_cmd.shutil.which", return_value=None), \
             patch("myco.init_cmd.Path.home") as mock_home:
            fake_home = tmp_path / "fakehome"
            fake_home.mkdir()
            mock_home.return_value = fake_home
            result = detect_tools(tmp_path)
        assert not any(result.values())


# ---------------------------------------------------------------------------
# JSON merge helper
# ---------------------------------------------------------------------------

class TestJsonMergeWrite:
    """Tests for _json_merge_write()."""

    def test_creates_new_file(self, tmp_path):
        path = tmp_path / "test.json"
        status = _json_merge_write(path, {"key": "val"})
        assert status == "created"
        assert json.loads(path.read_text(encoding="utf-8")) == {"key": "val"}

    def test_merges_existing(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"existing": True, "mcpServers": {"other": {}}}) + "\n",
                        encoding="utf-8")
        status = _json_merge_write(path, {"mcpServers": {"myco": {"cmd": "py"}}})
        assert status == "merged"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "other" in data["mcpServers"]
        assert "myco" in data["mcpServers"]

    def test_handles_invalid_json(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text("not-valid-json", encoding="utf-8")
        status = _json_merge_write(path, {"key": "val"})
        assert status == "created \u2014 old file was invalid"
        assert json.loads(path.read_text(encoding="utf-8")) == {"key": "val"}

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "test.json"
        status = _json_merge_write(path, {"a": 1})
        assert status == "created"
        assert path.exists()


# ---------------------------------------------------------------------------
# TOML merge helper
# ---------------------------------------------------------------------------

class TestTomlMergeWrite:
    """Tests for _toml_merge_write()."""

    def test_creates_new_toml(self, tmp_path):
        path = tmp_path / "config.toml"
        block = '[mcp.servers.myco]\ncommand = "python"'
        status = _toml_merge_write(path, block)
        assert status == "created"
        assert "[mcp.servers.myco]" in path.read_text(encoding="utf-8")

    def test_merges_into_existing_toml(self, tmp_path):
        path = tmp_path / "config.toml"
        path.write_text('[other]\nkey = "value"', encoding="utf-8")
        block = '[mcp.servers.myco]\ncommand = "python"'
        status = _toml_merge_write(path, block)
        assert status == "merged"
        content = path.read_text(encoding="utf-8")
        assert "[other]" in content
        assert "[mcp.servers.myco]" in content

    def test_skips_if_already_present(self, tmp_path):
        path = tmp_path / "config.toml"
        path.write_text('[mcp.servers.myco]\ncommand = "python"', encoding="utf-8")
        block = '[mcp.servers.myco]\ncommand = "python"'
        status = _toml_merge_write(path, block)
        assert status == "already configured \u2014 skipped"

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "config.toml"
        block = '[mcp.servers.myco]\ncommand = "python"'
        status = _toml_merge_write(path, block)
        assert status == "created"
        assert path.exists()


# ---------------------------------------------------------------------------
# Per-tool generators
# ---------------------------------------------------------------------------

class TestGenClaudeCode:
    """Tests for _gen_claude_code()."""

    def test_creates_mcp_json(self, tmp_path):
        status = _gen_claude_code(tmp_path)
        assert status == "created"
        data = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
        assert "myco" in data["mcpServers"]
        assert data["mcpServers"]["myco"]["command"] == "python"

    def test_merges_existing_mcp_json(self, tmp_path):
        (tmp_path / ".mcp.json").write_text(
            json.dumps({"mcpServers": {"other": {"command": "node"}}}),
            encoding="utf-8")
        status = _gen_claude_code(tmp_path)
        assert status == "merged"
        data = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
        assert "other" in data["mcpServers"]
        assert "myco" in data["mcpServers"]


class TestGenCursor:
    """Tests for _gen_cursor()."""

    def test_creates_cursor_mcp_json(self, tmp_path):
        status = _gen_cursor(tmp_path)
        assert status == "created"
        data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
        assert "myco" in data["mcpServers"]

    def test_merges_existing(self, tmp_path):
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()
        (cursor_dir / "mcp.json").write_text(
            json.dumps({"mcpServers": {"existing": {}}}), encoding="utf-8")
        status = _gen_cursor(tmp_path)
        assert status == "merged"
        data = json.loads((cursor_dir / "mcp.json").read_text(encoding="utf-8"))
        assert "existing" in data["mcpServers"]
        assert "myco" in data["mcpServers"]


class TestGenVSCode:
    """Tests for _gen_vscode()."""

    def test_creates_vscode_settings(self, tmp_path):
        status = _gen_vscode(tmp_path)
        assert status == "created"
        data = json.loads((tmp_path / ".vscode" / "settings.json").read_text(encoding="utf-8"))
        assert "myco" in data["mcp"]["servers"]

    def test_merges_existing_settings(self, tmp_path):
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "settings.json").write_text(
            json.dumps({"editor.fontSize": 14, "mcp": {"servers": {"other": {}}}}),
            encoding="utf-8")
        status = _gen_vscode(tmp_path)
        assert status == "merged"
        data = json.loads((vscode_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["editor.fontSize"] == 14
        assert "other" in data["mcp"]["servers"]
        assert "myco" in data["mcp"]["servers"]


class TestGenCodex:
    """Tests for _gen_codex()."""

    def test_creates_codex_config(self, tmp_path):
        with patch("myco.init_cmd.Path.home", return_value=tmp_path):
            status = _gen_codex(tmp_path)
        assert status == "created"
        content = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
        assert "[mcp.servers.myco]" in content
        assert 'command = "python"' in content


class TestGenCline:
    """Tests for _gen_cline()."""

    def test_creates_cline_settings(self, tmp_path):
        status = _gen_cline(tmp_path)
        assert status == "created"
        data = json.loads((tmp_path / "cline_mcp_settings.json").read_text(encoding="utf-8"))
        assert "myco" in data["mcpServers"]

    def test_merges_existing(self, tmp_path):
        (tmp_path / "cline_mcp_settings.json").write_text(
            json.dumps({"mcpServers": {"existing": {}}}), encoding="utf-8")
        status = _gen_cline(tmp_path)
        assert status == "merged"
        data = json.loads((tmp_path / "cline_mcp_settings.json").read_text(encoding="utf-8"))
        assert "existing" in data["mcpServers"]
        assert "myco" in data["mcpServers"]


class TestGenContinue:
    """Tests for _gen_continue()."""

    def test_creates_continue_config(self, tmp_path):
        status = _gen_continue(tmp_path)
        assert status == "created"
        data = json.loads(
            (tmp_path / ".continue" / "mcpServers" / "myco.json").read_text(encoding="utf-8"))
        assert data["command"] == "python"
        assert data["args"] == ["-m", "myco.mcp_server"]


class TestGenZed:
    """Tests for _gen_zed()."""

    def test_creates_zed_settings(self, tmp_path):
        status = _gen_zed(tmp_path)
        assert status == "created"
        data = json.loads((tmp_path / ".zed" / "settings.json").read_text(encoding="utf-8"))
        assert "myco" in data["context_servers"]
        assert data["context_servers"]["myco"]["source"] == "custom"

    def test_merges_existing(self, tmp_path):
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        (zed_dir / "settings.json").write_text(
            json.dumps({"context_servers": {"other": {}}, "theme": "dark"}),
            encoding="utf-8")
        status = _gen_zed(tmp_path)
        assert status == "merged"
        data = json.loads((zed_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["theme"] == "dark"
        assert "other" in data["context_servers"]
        assert "myco" in data["context_servers"]


class TestGenClaudeMd:
    """Tests for _gen_claude_md()."""

    def test_creates_new_claude_md(self, tmp_path):
        replacements = {
            "PROJECT_NAME": "Test",
            "DATE": "2026-04-12",
            "CURRENT_PHASE": "Phase 0",
            "PROJECT_DESCRIPTION": "test",
            "PROJECT_SUMMARY": "test",
            "GITHUB_USER": "testuser",
            "ENTRY_POINT": "CLAUDE.md",
        }
        status = _gen_claude_md(tmp_path, replacements)
        assert status == "created"
        assert (tmp_path / "CLAUDE.md").exists()
        content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Myco" in content

    def test_appends_to_existing_without_myco(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# My Project\nSome content.", encoding="utf-8")
        replacements = {
            "PROJECT_NAME": "Test",
            "DATE": "2026-04-12",
            "CURRENT_PHASE": "Phase 0",
            "PROJECT_DESCRIPTION": "test",
            "PROJECT_SUMMARY": "test",
            "GITHUB_USER": "testuser",
            "ENTRY_POINT": "CLAUDE.md",
        }
        status = _gen_claude_md(tmp_path, replacements)
        assert status == "Myco section appended"
        content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "My Project" in content
        assert "Myco" in content

    def test_skips_if_myco_already_present(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# Myco Project\nAlready here.", encoding="utf-8")
        replacements = {
            "PROJECT_NAME": "Test",
            "DATE": "2026-04-12",
            "CURRENT_PHASE": "Phase 0",
            "PROJECT_DESCRIPTION": "test",
            "PROJECT_SUMMARY": "test",
            "GITHUB_USER": "testuser",
            "ENTRY_POINT": "CLAUDE.md",
        }
        status = _gen_claude_md(tmp_path, replacements)
        assert status == "already contains Myco config \u2014 skipped"


# ---------------------------------------------------------------------------
# Integration: run_auto_detect
# ---------------------------------------------------------------------------

class TestRunAutoDetect:
    """Integration tests for run_auto_detect()."""

    def test_returns_zero(self, tmp_path):
        target = tmp_path / "newproject"
        target.mkdir()
        args = argparse.Namespace(
            dir=str(target),
            name="TestAuto",
            level=0,
            github_user="testuser",
            entry_point="MYCO.md",
            auto_detect=True,
            agent=None,
        )
        # Mock all tools as not detected to avoid filesystem side effects
        with patch("myco.init_cmd.detect_tools") as mock_detect, \
             patch("myco.init_cmd.shutil.which", return_value=None):
            mock_detect.return_value = {
                "Claude Code": False,
                "Cursor": False,
                "VS Code": False,
                "Codex": False,
                "Cline": False,
                "Continue": False,
                "Zed": False,
            }
            rc = run_auto_detect(args)
        assert rc == 0
        # CLAUDE.md should always be generated
        assert (target / "CLAUDE.md").exists()

    def test_generates_configs_for_detected_tools(self, tmp_path):
        target = tmp_path / "autodetect_project"
        target.mkdir()
        args = argparse.Namespace(
            dir=str(target),
            name="TestAuto",
            level=0,
            github_user="testuser",
            entry_point="MYCO.md",
            auto_detect=True,
            agent=None,
        )
        with patch("myco.init_cmd.detect_tools") as mock_detect:
            mock_detect.return_value = {
                "Claude Code": True,
                "Cursor": True,
                "VS Code": False,
                "Codex": False,
                "Cline": False,
                "Continue": False,
                "Zed": False,
            }
            rc = run_auto_detect(args)
        assert rc == 0
        assert (target / ".mcp.json").exists()
        assert (target / ".cursor" / "mcp.json").exists()
        # VS Code not detected, so no .vscode/settings.json
        assert not (target / ".vscode" / "settings.json").exists()

    def test_run_init_dispatches_to_auto_detect(self, tmp_path):
        """run_init delegates to run_auto_detect when --auto-detect is set."""
        from myco.init_cmd import run_init
        target = tmp_path / "dispatch_test"
        target.mkdir()
        args = argparse.Namespace(
            dir=str(target),
            name="TestDispatch",
            level=0,
            github_user="testuser",
            entry_point="MYCO.md",
            auto_detect=True,
            agent=None,
        )
        with patch("myco.init_cmd.detect_tools") as mock_detect:
            mock_detect.return_value = {
                "Claude Code": False,
                "Cursor": False,
                "VS Code": False,
                "Codex": False,
                "Cline": False,
                "Continue": False,
                "Zed": False,
            }
            rc = run_init(args)
        assert rc == 0
        assert (target / "CLAUDE.md").exists()

    def test_all_tools_detected_generates_all_configs(self, tmp_path):
        """When all tools are detected, all configs are generated."""
        target = tmp_path / "alltools"
        target.mkdir()
        args = argparse.Namespace(
            dir=str(target),
            name="TestAll",
            level=1,
            github_user="testuser",
            entry_point="MYCO.md",
            auto_detect=True,
            agent=None,
        )
        with patch("myco.init_cmd.detect_tools") as mock_detect, \
             patch("myco.init_cmd.Path.home", return_value=tmp_path):
            mock_detect.return_value = {
                "Claude Code": True,
                "Cursor": True,
                "VS Code": True,
                "Codex": True,
                "Cline": True,
                "Continue": True,
                "Zed": True,
            }
            rc = run_auto_detect(args)
        assert rc == 0
        # Verify all config files exist
        assert (target / ".mcp.json").exists()
        assert (target / ".cursor" / "mcp.json").exists()
        assert (target / ".vscode" / "settings.json").exists()
        assert (tmp_path / ".codex" / "config.toml").exists()
        assert (target / "cline_mcp_settings.json").exists()
        assert (target / ".continue" / "mcpServers" / "myco.json").exists()
        assert (target / ".zed" / "settings.json").exists()
        assert (target / "CLAUDE.md").exists()
