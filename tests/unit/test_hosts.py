"""Tests for myco.hosts — host environment detection and hook checking."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myco.hosts import (
    check_all_hooks,
    detect_active_host,
    effective_hook_level,
)
from myco.hosts import cowork, claude_code, cursor, vscode


class TestDetectActiveHost:
    """Test host detection."""

    def test_detect_cowork_from_env(self, monkeypatch):
        """Detect Cowork from COWORK_SESSION env var."""
        monkeypatch.setenv("COWORK_SESSION", "test-session")
        assert detect_active_host() == "cowork"

    def test_detect_cowork_from_path(self, tmp_path, monkeypatch):
        """Detect Cowork from /sessions/ path prefix."""
        # Mock cwd to return a /sessions/ path
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/sessions/test-session/mnt/Myco")
            assert detect_active_host() == "cowork"

    def test_detect_claude_code(self, tmp_path, monkeypatch):
        """Detect Claude Code from .claude/ directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".claude").mkdir()
        assert detect_active_host() == "claude_code"

    def test_detect_cursor_from_env(self, monkeypatch):
        """Detect Cursor from CURSOR_SESSION env var."""
        monkeypatch.setenv("CURSOR_SESSION", "test")
        assert detect_active_host() == "cursor"

    def test_detect_cursor_from_dir(self, tmp_path, monkeypatch):
        """Detect Cursor from .cursor/ directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".cursor").mkdir()
        assert detect_active_host() == "cursor"

    def test_detect_vscode(self, tmp_path, monkeypatch):
        """Detect VS Code from .vscode/ directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".vscode").mkdir()
        assert detect_active_host() == "vscode"

    def test_detect_none(self, tmp_path, monkeypatch):
        """Return None when no host detected."""
        monkeypatch.chdir(tmp_path)
        assert detect_active_host() is None


class TestEffectiveHookLevel:
    """Test hook degradation ladder."""

    def test_cowork_native(self, tmp_path):
        """Cowork has native hooks."""
        with patch("myco.hosts.detect_active_host", return_value="cowork"):
            level = effective_hook_level(tmp_path)
            assert level == "native"

    def test_claude_code_native(self, tmp_path):
        """Claude Code has native hooks."""
        with patch("myco.hosts.detect_active_host", return_value="claude_code"):
            level = effective_hook_level(tmp_path)
            assert level == "native"

    def test_cursor_native(self, tmp_path):
        """Cursor has native hooks."""
        with patch("myco.hosts.detect_active_host", return_value="cursor"):
            level = effective_hook_level(tmp_path)
            assert level == "native"

    def test_vscode_protocol(self, tmp_path):
        """VS Code degrades to protocol."""
        with patch("myco.hosts.detect_active_host", return_value="vscode"):
            level = effective_hook_level(tmp_path)
            assert level == "protocol"

    def test_unknown_protocol(self, tmp_path):
        """Unknown host degrades to protocol."""
        with patch("myco.hosts.detect_active_host", return_value=None):
            level = effective_hook_level(tmp_path)
            assert level == "protocol"


class TestCoworkAdapter:
    """Test Cowork adapter."""

    def test_detect_cowork(self):
        """Cowork detector."""
        with patch.dict(os.environ, {"COWORK_SESSION": "test"}):
            assert cowork.detect() is True

    def test_check_hooks_ok(self, tmp_path):
        """Check hooks when all is OK."""
        state = tmp_path / ".myco_state"
        state.mkdir()
        boot_brief = state / "boot_brief.md"
        boot_brief.touch()

        result = cowork.check_hooks(tmp_path)
        assert result["host"] == "cowork"
        assert result["session_start"] is True

    def test_check_hooks_missing_myco_state(self, tmp_path):
        """Check hooks when .myco_state missing."""
        result = cowork.check_hooks(tmp_path)
        assert "missing .myco_state" in result["issues"][0]


class TestClaudeCodeAdapter:
    """Test Claude Code adapter."""

    def test_detect_claude_code(self, tmp_path):
        """Claude Code detector."""
        (tmp_path / ".claude").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert claude_code.detect() is True

    def test_check_hooks_missing_settings(self, tmp_path):
        """Check hooks when .claude/settings.json missing."""
        state = tmp_path / ".myco_state"
        state.mkdir()
        # Need to create .claude directory for detection
        claude_dir = Path.cwd() / ".claude"
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)
            tmp_path_cwd = tmp_path / ".claude"
            tmp_path_cwd.mkdir()
            result = claude_code.check_hooks(tmp_path)
            assert any("settings.json" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)


class TestCursorAdapter:
    """Test Cursor adapter."""

    def test_detect_cursor(self):
        """Cursor detector from env."""
        with patch.dict(os.environ, {"CURSOR_SESSION": "test"}):
            assert cursor.detect() is True

    def test_check_hooks_missing_rules(self, tmp_path):
        """Check hooks when .cursor/rules missing."""
        from pathlib import Path
        import os
        state = tmp_path / ".myco_state"
        state.mkdir()
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            cursor_dir = tmp_path / ".cursor"
            cursor_dir.mkdir()
            result = cursor.check_hooks(tmp_path)
            assert any("rules" in issue for issue in result["issues"])
        finally:
            os.chdir(original_cwd)


class TestVSCodeAdapter:
    """Test VS Code adapter."""

    def test_detect_vscode(self, tmp_path):
        """VS Code detector."""
        (tmp_path / ".vscode").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert vscode.detect() is True

    def test_check_hooks_no_native(self, tmp_path):
        """VS Code always degrades to protocol."""
        result = vscode.check_hooks(tmp_path)
        assert result["session_start"] is False
        assert any("protocol" in issue.lower() for issue in result["issues"])


class TestCheckAllHooks:
    """Test aggregate hook checking."""

    def test_check_all_hooks_structure(self, tmp_path):
        """check_all_hooks returns expected structure."""
        state = tmp_path / ".myco_state"
        state.mkdir()
        (state / "boot_brief.md").touch()

        result = check_all_hooks(tmp_path)
        assert "detected_host" in result
        assert "effective_level" in result
        assert "adapters" in result
        assert "summary" in result
        assert "all_ok" in result["summary"]
