"""Tests for myco.symbionts.continue_ — Continue MCP adapter."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from myco.symbionts import continue_


class TestDetectContinue:
    """Test Continue environment detection."""

    def test_detect_continue_from_dir(self, tmp_path):
        """Detect Continue from .continue/ directory."""
        (tmp_path / ".continue").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert continue_.detect() is True

    def test_detect_continue_absent(self, tmp_path):
        """Return False when .continue/ missing."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert continue_.detect() is False


class TestCheckHooksContinue:
    """Test Continue MCP hook checking."""

    def test_check_hooks_mcp_registered(self, tmp_path):
        """Detect registered Myco MCP server in .continue/mcpServers/."""
        continue_dir = tmp_path / ".continue"
        continue_dir.mkdir()
        mcp_dir = continue_dir / "mcpServers"
        mcp_dir.mkdir()
        
        mcp_config = {
            "mcpServers": {
                "myco": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "myco.mcp_server"],
                    "env": {"PYTHONUNBUFFERED": "1"}
                }
            }
        }
        (mcp_dir / "myco.json").write_text(json.dumps(mcp_config), encoding="utf-8")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = continue_.check_hooks(tmp_path)
            assert result["host"] == "continue"
            assert result["hook_level"] == "mcp_only"
            assert result["mcp_registered"] is True
            assert result["rules_injected"] is False
            assert result["session_hooks"] is False
            assert len(result["issues"]) == 0
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_mcp_missing(self, tmp_path):
        """Flag missing MCP registration."""
        continue_dir = tmp_path / ".continue"
        continue_dir.mkdir()
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = continue_.check_hooks(tmp_path)
            assert result["host"] == "continue"
            assert result["mcp_registered"] is False
            assert any("myco.json" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_malformed_json(self, tmp_path):
        """Handle malformed JSON gracefully."""
        continue_dir = tmp_path / ".continue"
        continue_dir.mkdir()
        mcp_dir = continue_dir / "mcpServers"
        mcp_dir.mkdir()
        (mcp_dir / "myco.json").write_text("invalid json {", encoding="utf-8")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = continue_.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
            assert any("failed to read" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_wrong_server_type(self, tmp_path):
        """Detect incorrect server type."""
        continue_dir = tmp_path / ".continue"
        continue_dir.mkdir()
        mcp_dir = continue_dir / "mcpServers"
        mcp_dir.mkdir()
        
        mcp_config = {
            "mcpServers": {
                "myco": {
                    "type": "http",  # Wrong type
                    "url": "http://localhost:3000"
                }
            }
        }
        (mcp_dir / "myco.json").write_text(json.dumps(mcp_config), encoding="utf-8")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = continue_.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
        finally:
            os.chdir(original_cwd)

    def test_check_hooks_not_in_continue(self, tmp_path):
        """Return not-in-Continue when directory missing."""
        result = continue_.check_hooks(tmp_path)
        assert result["host"] == "continue"
        assert result["mcp_registered"] is False
        assert any("not in Continue environment" in issue for issue in result["issues"])


class TestInstallHooksContinue:
    """Test Continue MCP hook installation."""

    def test_install_hooks_creates_mcp_config(self, tmp_path):
        """install_hooks creates .continue/mcpServers/myco.json."""
        result = continue_.install_hooks(tmp_path)
        assert result is True
        
        mcp_file = tmp_path / ".continue" / "mcpServers" / "myco.json"
        assert mcp_file.exists()
        
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
        assert config["mcpServers"]["myco"]["type"] == "stdio"
        assert config["mcpServers"]["myco"]["command"] == "python"
        assert "-m" in config["mcpServers"]["myco"]["args"]
        assert "myco.mcp_server" in config["mcpServers"]["myco"]["args"]

    def test_install_hooks_idempotent(self, tmp_path):
        """install_hooks is idempotent (succeeds if already installed)."""
        # First install
        result1 = continue_.install_hooks(tmp_path)
        assert result1 is True
        
        mcp_file = tmp_path / ".continue" / "mcpServers" / "myco.json"
        content1 = mcp_file.read_text(encoding="utf-8")
        
        # Second install
        result2 = continue_.install_hooks(tmp_path)
        assert result2 is True
        
        content2 = mcp_file.read_text(encoding="utf-8")
        assert content1 == content2  # No duplicate entries

    def test_install_hooks_preserves_other_servers(self, tmp_path):
        """install_hooks preserves other mcpServers entries."""
        continue_dir = tmp_path / ".continue"
        continue_dir.mkdir()
        mcp_dir = continue_dir / "mcpServers"
        mcp_dir.mkdir()
        
        existing_config = {
            "mcpServers": {
                "other": {
                    "type": "stdio",
                    "command": "some-other-command"
                }
            }
        }
        (mcp_dir / "myco.json").write_text(json.dumps(existing_config), encoding="utf-8")
        
        result = continue_.install_hooks(tmp_path)
        assert result is True
        
        mcp_file = mcp_dir / "myco.json"
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
        
        # Other server should be preserved
        assert "other" in config["mcpServers"]
        assert config["mcpServers"]["other"]["command"] == "some-other-command"
        
        # Myco should be added
        assert "myco" in config["mcpServers"]

    def test_install_hooks_env_var_set(self, tmp_path):
        """install_hooks includes PYTHONUNBUFFERED env var."""
        continue_.install_hooks(tmp_path)
        
        mcp_file = tmp_path / ".continue" / "mcpServers" / "myco.json"
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
        
        env = config["mcpServers"]["myco"]["env"]
        assert env["PYTHONUNBUFFERED"] == "1"

    def test_install_hooks_creates_directories(self, tmp_path):
        """install_hooks creates nested directories if missing."""
        result = continue_.install_hooks(tmp_path)
        assert result is True
        
        assert (tmp_path / ".continue").exists()
        assert (tmp_path / ".continue" / "mcpServers").exists()


class TestContinueIntegration:
    """Integration tests for Continue adapter."""

    def test_detect_and_check_hooks_flow(self, tmp_path):
        """Complete flow: detect → create → check."""
        # Initially not detected
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert continue_.detect() is False
        
        # Create .continue/
        (tmp_path / ".continue").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert continue_.detect() is True
        
        # Check hooks (should fail, not installed yet)
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = continue_.check_hooks(tmp_path)
            assert result["mcp_registered"] is False
            
            # Install hooks
            install_result = continue_.install_hooks(tmp_path)
            assert install_result is True
            
            # Check hooks again (should pass)
            result = continue_.check_hooks(tmp_path)
            assert result["mcp_registered"] is True
            assert len(result["issues"]) == 0
        finally:
            os.chdir(original_cwd)
