"""Tests for myco.symbionts.codex — Codex CLI host adapter."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myco.symbionts import codex


class TestCodexDetect:
    """Test Codex environment detection."""

    def test_detect_codex_from_home_dir(self, tmp_path, monkeypatch):
        """Detect Codex when ~/.codex/ exists."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        (fake_home / ".codex").mkdir()
        monkeypatch.setenv("HOME", str(fake_home))
        assert codex.detect() is True

    def test_detect_codex_from_codex_home_env(self, tmp_path, monkeypatch):
        """Detect Codex when $CODEX_HOME is set."""
        codex_root = tmp_path / "my_codex"
        codex_root.mkdir()
        (codex_root / ".codex").mkdir()
        monkeypatch.setenv("CODEX_HOME", str(codex_root))
        assert codex.detect() is True

    def test_detect_codex_from_cli_path(self, tmp_path, monkeypatch):
        """Detect Codex when 'codex' is on PATH."""
        # Mock shutil.which to simulate codex CLI
        with patch("myco.symbionts.codex.shutil.which", return_value="/usr/bin/codex"):
            assert codex.detect() is True

    def test_detect_codex_false_when_missing(self, tmp_path, monkeypatch):
        """Return False when Codex is not detected."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))
        monkeypatch.delenv("CODEX_HOME", raising=False)

        with patch("myco.symbionts.codex.shutil.which", return_value=None):
            assert codex.detect() is False


class TestCodexCheckHooks:
    """Test Codex hook detection and status checking."""

    def test_check_hooks_when_codex_missing(self, tmp_path):
        """Check hooks when .codex directory missing."""
        result = codex.check_hooks(tmp_path)
        assert result["host"] == "codex"
        assert result["session_start"] is False
        assert result["session_end"] is False
        assert result["hook_level"] == "none"
        assert any("not found" in issue for issue in result["issues"])

    def test_check_hooks_mcp_only_when_config_exists(self, tmp_path, monkeypatch):
        """Check hooks when MCP is registered but no hooks.json."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        # Create config.toml with MCP server
        config_toml = codex_dir / "config.toml"
        config_toml.write_text(
            '[mcp_servers.myco]\ncommand = "python"\nargs = ["-m", "myco.mcp_server"]\n',
            encoding="utf-8",
        )

        monkeypatch.setenv("HOME", str(fake_home))

        result = codex.check_hooks(tmp_path)
        assert result["hook_level"] == "mcp_only"
        assert result["mcp_registered"] is True
        assert result["session_start"] is True

    def test_check_hooks_native_when_hooks_installed(self, tmp_path, monkeypatch):
        """Check hooks when both MCP and hooks.json are installed (Unix)."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        # Create config.toml with MCP
        config_toml = codex_dir / "config.toml"
        config_toml.write_text(
            '[mcp_servers.myco]\ncommand = "python"\nargs = ["-m", "myco.mcp_server"]\n',
            encoding="utf-8",
        )

        # Create hooks.json with SessionStart hook containing 'myco'
        hooks_json = codex_dir / "hooks.json"
        hooks_json.write_text(
            json.dumps({
                "SessionStart": [{"type": "command", "command": "myco hunger --execute"}]
            }),
            encoding="utf-8",
        )

        monkeypatch.setenv("HOME", str(fake_home))

        with patch("myco.symbionts.codex.platform.system", return_value="Darwin"):
            result = codex.check_hooks(tmp_path)
            assert result["hook_level"] == "native"
            assert result["rules_injected"] is True
            assert result["mcp_registered"] is True
            assert result["session_start"] is True

    def test_check_hooks_windows_mcp_only(self, tmp_path, monkeypatch):
        """On Windows, hooks are unavailable; only MCP works."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        config_toml = codex_dir / "config.toml"
        config_toml.write_text(
            '[mcp_servers.myco]\ncommand = "python"\nargs = ["-m", "myco.mcp_server"]\n',
            encoding="utf-8",
        )

        monkeypatch.setenv("HOME", str(fake_home))

        with patch("myco.symbionts.codex.platform.system", return_value="Windows"):
            result = codex.check_hooks(tmp_path)
            assert result["hook_level"] == "mcp_only"
            assert result["rules_injected"] is False
            assert result["mcp_registered"] is True
            assert "Windows" in result["notes"]

    def test_check_hooks_windows_no_hooks_mention(self, tmp_path, monkeypatch):
        """Windows should never report rules_injected = True."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        monkeypatch.setenv("HOME", str(fake_home))

        with patch("myco.symbionts.codex.platform.system", return_value="Windows"):
            result = codex.check_hooks(tmp_path)
            assert result["rules_injected"] is False

    def test_check_hooks_malformed_config_toml(self, tmp_path, monkeypatch):
        """Handle corrupted config.toml gracefully."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        config_toml = codex_dir / "config.toml"
        config_toml.write_text("invalid toml [[[", encoding="utf-8")

        monkeypatch.setenv("HOME", str(fake_home))

        result = codex.check_hooks(tmp_path)
        assert result["hook_level"] == "none"
        assert result["mcp_registered"] is False

    def test_check_hooks_codex_home_override(self, tmp_path, monkeypatch):
        """Respect CODEX_HOME env var when checking hooks."""
        codex_root = tmp_path / "my_codex"
        codex_root.mkdir()
        codex_dir = codex_root / ".codex"
        codex_dir.mkdir()

        config_toml = codex_dir / "config.toml"
        config_toml.write_text(
            '[mcp_servers.myco]\ncommand = "python"\nargs = ["-m", "myco.mcp_server"]\n',
            encoding="utf-8",
        )

        monkeypatch.setenv("CODEX_HOME", str(codex_root))
        monkeypatch.delenv("HOME", raising=False)

        result = codex.check_hooks(tmp_path)
        assert result["mcp_registered"] is True

    def test_check_hooks_backward_compat_mcp_servers_old_format(self, tmp_path, monkeypatch):
        """Check for legacy [mcp.servers.myco] format (old versions)."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        config_toml = codex_dir / "config.toml"
        # Old format
        config_toml.write_text('[mcp.servers.myco]\ncommand = "python"\n', encoding="utf-8")

        monkeypatch.setenv("HOME", str(fake_home))

        result = codex.check_hooks(tmp_path)
        # Should recognize it as already configured
        assert result["mcp_registered"] is True


class TestCodexInstallHooks:
    """Test Codex hook installation."""

    def test_install_hooks_creates_config_toml(self, tmp_path, monkeypatch):
        """install_hooks creates config.toml with MCP server."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        result = codex.install_hooks(tmp_path)
        assert result is True

        config_toml = fake_home / ".codex" / "config.toml"
        assert config_toml.exists()
        content = config_toml.read_text(encoding="utf-8")
        assert "[mcp_servers.myco]" in content
        assert 'command = "python"' in content

    def test_install_hooks_idempotent_config(self, tmp_path, monkeypatch):
        """install_hooks is idempotent — calling twice doesn't duplicate MCP entry."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        # First call
        codex.install_hooks(tmp_path)
        config_toml = fake_home / ".codex" / "config.toml"
        content1 = config_toml.read_text(encoding="utf-8")

        # Second call
        codex.install_hooks(tmp_path)
        content2 = config_toml.read_text(encoding="utf-8")

        # Should be identical (no duplicates)
        assert content1 == content2
        assert content1.count("[mcp_servers.myco]") == 1

    def test_install_hooks_preserves_existing_config(self, tmp_path, monkeypatch):
        """install_hooks merges with existing config.toml (doesn't overwrite)."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        config_toml = codex_dir / "config.toml"
        original = "[other_section]\nkey = true\n"
        config_toml.write_text(original, encoding="utf-8")

        monkeypatch.setenv("HOME", str(fake_home))

        codex.install_hooks(tmp_path)

        content = config_toml.read_text(encoding="utf-8")
        assert "[other_section]" in content
        assert "[mcp_servers.myco]" in content

    def test_install_hooks_creates_hooks_json_unix(self, tmp_path, monkeypatch):
        """On Unix, install_hooks creates hooks.json with SessionStart."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        with patch("myco.symbionts.codex.platform.system", return_value="Darwin"):
            codex.install_hooks(tmp_path)

        hooks_json = fake_home / ".codex" / "hooks.json"
        assert hooks_json.exists()

        hooks = json.loads(hooks_json.read_text(encoding="utf-8"))
        assert "SessionStart" in hooks
        assert len(hooks["SessionStart"]) > 0
        assert any("myco" in str(h) for h in hooks["SessionStart"])

    def test_install_hooks_idempotent_hooks_json(self, tmp_path, monkeypatch):
        """install_hooks doesn't duplicate SessionStart hooks."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        with patch("myco.symbionts.codex.platform.system", return_value="Darwin"):
            # First call
            codex.install_hooks(tmp_path)
            hooks_json = fake_home / ".codex" / "hooks.json"
            hooks1 = json.loads(hooks_json.read_text(encoding="utf-8"))

            # Second call
            codex.install_hooks(tmp_path)
            hooks2 = json.loads(hooks_json.read_text(encoding="utf-8"))

        # SessionStart should have same number of hooks
        assert len(hooks1["SessionStart"]) == len(hooks2["SessionStart"])

    def test_install_hooks_windows_no_hooks_json(self, tmp_path, monkeypatch):
        """On Windows, install_hooks only creates config.toml, not hooks.json."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        with patch("myco.symbionts.codex.platform.system", return_value="Windows"):
            codex.install_hooks(tmp_path)

        config_toml = fake_home / ".codex" / "config.toml"
        assert config_toml.exists()

        hooks_json = fake_home / ".codex" / "hooks.json"
        assert not hooks_json.exists()

    def test_install_hooks_codex_home_override(self, tmp_path, monkeypatch):
        """install_hooks respects CODEX_HOME env var."""
        codex_root = tmp_path / "my_codex"
        codex_root.mkdir()
        monkeypatch.setenv("CODEX_HOME", str(codex_root))
        monkeypatch.delenv("HOME", raising=False)

        codex.install_hooks(tmp_path)

        config_toml = codex_root / ".codex" / "config.toml"
        assert config_toml.exists()

    def test_install_hooks_merges_with_existing_hooks_json(self, tmp_path, monkeypatch):
        """install_hooks merges with existing hooks.json (doesn't overwrite)."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir()

        # Create hooks.json with different event
        hooks_json = codex_dir / "hooks.json"
        existing_hooks = {"PreToolUse": [{"command": "other"}]}
        hooks_json.write_text(json.dumps(existing_hooks), encoding="utf-8")

        monkeypatch.setenv("HOME", str(fake_home))

        with patch("myco.symbionts.codex.platform.system", return_value="Darwin"):
            codex.install_hooks(tmp_path)

        hooks = json.loads(hooks_json.read_text(encoding="utf-8"))
        assert "PreToolUse" in hooks  # Preserved
        assert "SessionStart" in hooks  # Added

    def test_install_hooks_handles_config_write_error(self, tmp_path, monkeypatch):
        """install_hooks returns False if config.toml write fails."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        codex_dir = fake_home / ".codex"
        # Make config_dir read-only (Unix only)
        codex_dir.mkdir(mode=0o444)

        monkeypatch.setenv("HOME", str(fake_home))

        # On platforms where we can't make read-only, skip
        import stat

        if not (os.stat(codex_dir).st_mode & stat.S_IWUSR):
            # Directory is truly read-only, test should fail as expected
            result = codex.install_hooks(tmp_path)
            assert result is False
        else:
            # Skip test if we can't actually make it read-only
            codex_dir.chmod(0o755)


class TestCodexIntegration:
    """Integration tests combining detect + check_hooks + install_hooks."""

    def test_full_workflow_unix(self, tmp_path, monkeypatch):
        """Full workflow: detect → install → check on Unix."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        # Before install, detect should be False
        assert codex.detect() is False

        # Create config dir
        (fake_home / ".codex").mkdir()

        # Now detect should be True
        assert codex.detect() is True

        # Check hooks (none installed yet)
        with patch("myco.symbionts.codex.platform.system", return_value="Darwin"):
            result = codex.check_hooks(tmp_path)
            assert result["hook_level"] == "none"

            # Install hooks
            installed = codex.install_hooks(tmp_path)
            assert installed is True

            # Check hooks again
            result = codex.check_hooks(tmp_path)
            assert result["hook_level"] == "native"
            assert result["mcp_registered"] is True
            assert result["rules_injected"] is True

    def test_full_workflow_windows(self, tmp_path, monkeypatch):
        """Full workflow on Windows (MCP only, no native hooks)."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        (fake_home / ".codex").mkdir()
        assert codex.detect() is True

        with patch("myco.symbionts.codex.platform.system", return_value="Windows"):
            # Before install
            result = codex.check_hooks(tmp_path)
            assert result["hook_level"] == "none"

            # Install
            installed = codex.install_hooks(tmp_path)
            assert installed is True

            # After install
            result = codex.check_hooks(tmp_path)
            assert result["hook_level"] == "mcp_only"
            assert result["mcp_registered"] is True
            assert result["rules_injected"] is False
