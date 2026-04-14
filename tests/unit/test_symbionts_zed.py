"""Tests for myco.symbionts.zed — Zed MCP adapter."""

import json
import os
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from myco.symbionts import zed


class TestDetectZed:
    """Test Zed environment detection."""

    def test_detect_zed_from_project_dir(self, tmp_path):
        """Detect Zed from .zed/ directory at project root."""
        (tmp_path / ".zed").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert zed.detect() is True

    def test_detect_zed_from_executable(self, tmp_path):
        """Detect Zed if zed executable in PATH."""
        with patch("shutil.which", return_value="/usr/bin/zed"):
            assert zed.detect() is True

    def test_detect_zed_from_global_config(self, tmp_path):
        """Detect Zed if global config directory exists."""
        with patch("shutil.which", return_value=None):
            with patch("myco.symbionts.zed._get_zed_config_path", return_value=tmp_path):
                # Create the config directory
                tmp_path.mkdir(parents=True, exist_ok=True)
                assert zed.detect() is True

    def test_detect_zed_absent(self, tmp_path):
        """Return False when Zed not detected."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with patch("shutil.which", return_value=None):
                with patch("myco.symbionts.zed._get_zed_config_path", return_value=tmp_path / "nonexistent"):
                    assert zed.detect() is False


class TestGetZedConfigPath:
    """Test platform-specific config path resolution."""

    def test_zed_config_path_windows(self):
        """Windows: %APPDATA%/Zed."""
        with patch("platform.system", return_value="Windows"):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\testuser\\AppData\\Roaming"}):
                path = zed._get_zed_config_path()
                assert "Zed" in str(path)
                assert "Roaming" in str(path)

    def test_zed_config_path_linux_xdg(self):
        """Linux with XDG_CONFIG_HOME: $XDG_CONFIG_HOME/zed."""
        with patch("platform.system", return_value="Linux"):
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/home/testuser/.config"}, clear=False):
                path = zed._get_zed_config_path()
                assert "zed" in str(path).lower()

    def test_zed_config_path_linux_default(self):
        """Linux without XDG_CONFIG_HOME: ~/.config/zed."""
        with patch("platform.system", return_value="Linux"):
            with patch.dict(os.environ, {}, clear=True):
                with patch("pathlib.Path.home", return_value=Path("/home/testuser")):
                    path = zed._get_zed_config_path()
                    assert ".config" in str(path)
                    assert "zed" in str(path).lower()


class TestCheckHooksZed:
    """Test Zed MCP context_servers hook checking."""

    def test_check_hooks_mcp_registered(self, tmp_path):
        """Detect registered Myco context server with source: custom."""
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        
        settings = {
            "context_servers": {
                "myco": {
                    "source": "custom",
                    "command": "python",
                    "args": ["-m", "myco.mcp_server"],
                    "env": {"PYTHONUNBUFFERED": "1"}
                }
            }
        }
        (zed_dir / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = zed.check_hooks(tmp_path)
            assert result["host"] == "zed"
            assert result["hook_level"] == "mcp_only"
            assert result["mcp_registered"] is True
            assert result["rules_injected"] is False
            assert result["session_hooks"] is False
            assert len(result["issues"]) == 0
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_missing_source_field(self, tmp_path):
        """Reject context_servers.myco without source: custom."""
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        
        settings = {
            "context_servers": {
                "myco": {
                    "command": "python",
                    "args": ["-m", "myco.mcp_server"]
                }
            }
        }
        (zed_dir / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = zed.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
            assert any("source" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_wrong_source_value(self, tmp_path):
        """Reject context_servers.myco with source != custom."""
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        
        settings = {
            "context_servers": {
                "myco": {
                    "source": "standard",  # Wrong value
                    "command": "python"
                }
            }
        }
        (zed_dir / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = zed.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
            assert any("source != 'custom'" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_settings_missing(self, tmp_path):
        """Flag missing .zed/settings.json."""
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = zed.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
            assert any("settings.json not found" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_malformed_json(self, tmp_path):
        """Handle malformed JSON gracefully."""
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        (zed_dir / "settings.json").write_text("invalid json {", encoding="utf-8")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = zed.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
            assert any("failed to read" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)


class TestInstallHooksZed:
    """Test Zed MCP hook installation."""

    def test_install_hooks_creates_settings(self, tmp_path):
        """install_hooks creates .zed/settings.json with context_servers.myco."""
        result = zed.install_hooks(tmp_path)
        assert result is True
        
        settings_file = tmp_path / ".zed" / "settings.json"
        assert settings_file.exists()
        
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        assert "context_servers" in settings
        assert "myco" in settings["context_servers"]
        
        myco = settings["context_servers"]["myco"]
        assert myco["source"] == "custom"
        assert myco["command"] == "python"
        assert "-m" in myco["args"]
        assert "myco.mcp_server" in myco["args"]

    def test_install_hooks_idempotent(self, tmp_path):
        """install_hooks is idempotent."""
        # First install
        result1 = zed.install_hooks(tmp_path)
        assert result1 is True
        
        settings_file = tmp_path / ".zed" / "settings.json"
        content1 = settings_file.read_text(encoding="utf-8")
        
        # Second install
        result2 = zed.install_hooks(tmp_path)
        assert result2 is True
        
        content2 = settings_file.read_text(encoding="utf-8")
        assert content1 == content2  # Identical, no duplicates

    def test_install_hooks_preserves_other_servers(self, tmp_path):
        """install_hooks preserves other context_servers entries."""
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        
        existing = {
            "context_servers": {
                "other": {
                    "source": "custom",
                    "command": "some-other-command"
                }
            }
        }
        (zed_dir / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
        
        result = zed.install_hooks(tmp_path)
        assert result is True
        
        settings = json.loads((zed_dir / "settings.json").read_text(encoding="utf-8"))
        assert "other" in settings["context_servers"]
        assert settings["context_servers"]["other"]["command"] == "some-other-command"
        assert "myco" in settings["context_servers"]

    def test_install_hooks_requires_source_custom(self, tmp_path):
        """install_hooks includes required source: custom field."""
        zed.install_hooks(tmp_path)
        
        settings_file = tmp_path / ".zed" / "settings.json"
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        
        myco = settings["context_servers"]["myco"]
        assert "source" in myco
        assert myco["source"] == "custom"

    def test_install_hooks_env_var_set(self, tmp_path):
        """install_hooks includes PYTHONUNBUFFERED env var."""
        zed.install_hooks(tmp_path)
        
        settings_file = tmp_path / ".zed" / "settings.json"
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        
        env = settings["context_servers"]["myco"]["env"]
        assert env["PYTHONUNBUFFERED"] == "1"

    def test_install_hooks_creates_directories(self, tmp_path):
        """install_hooks creates nested directories if missing."""
        result = zed.install_hooks(tmp_path)
        assert result is True
        
        assert (tmp_path / ".zed").exists()

    def test_install_hooks_merges_with_existing_settings(self, tmp_path):
        """install_hooks merges myco entry into existing settings."""
        zed_dir = tmp_path / ".zed"
        zed_dir.mkdir()
        
        existing = {
            "other_setting": "value",
            "context_servers": {
                "other": {"source": "custom", "command": "other-cmd"}
            }
        }
        (zed_dir / "settings.json").write_text(json.dumps(existing), encoding="utf-8")
        
        result = zed.install_hooks(tmp_path)
        assert result is True
        
        settings = json.loads((zed_dir / "settings.json").read_text(encoding="utf-8"))
        assert settings["other_setting"] == "value"  # Preserved
        assert "myco" in settings["context_servers"]
        assert "other" in settings["context_servers"]


class TestZedIntegration:
    """Integration tests for Zed adapter."""

    def test_detect_and_check_hooks_flow(self, tmp_path):
        """Complete flow: detect → create → check."""
        # Initially not detected
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with patch("shutil.which", return_value=None):
                with patch("myco.symbionts.zed._get_zed_config_path", return_value=tmp_path / "nonexistent"):
                    assert zed.detect() is False
        
        # Create .zed/
        (tmp_path / ".zed").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert zed.detect() is True
        
        # Check hooks (should fail, not installed yet)
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = zed.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
            
            # Install hooks
            install_result = zed.install_hooks(tmp_path)
            assert install_result is True
            
            # Check hooks again (should pass)
            result = zed.check_hooks(tmp_path)
            assert result["mcp_registered"] is True
            assert len(result["issues"]) == 0
        finally:
            os.chdir(original_cwd)
