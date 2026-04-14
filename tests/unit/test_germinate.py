"""Tests for myco.germinate auto-setup logic."""

import os
import sys
from pathlib import Path
from unittest import mock

import pytest

from myco.germinate import (
    _get_myco_home,
    is_first_run,
    prompt_auto_detect,
    run_auto_setup,
    mark_first_run_done,
    run_if_first_time,
)


class TestGetMycohome:
    """Test _get_myco_home() for platform differences."""

    def test_windows_appdata(self):
        """Windows: use %APPDATA%/Myco."""
        with mock.patch("sys.platform", "win32"):
            with mock.patch.dict(os.environ, {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"}):
                home = _get_myco_home()
                assert "Myco" in str(home)
                assert "AppData" in str(home) or "Myco" in str(home)

    def test_posix_xdg(self):
        """POSIX with XDG_CONFIG_HOME set."""
        with mock.patch("sys.platform", "linux"):
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/xdg"}, clear=False):
                home = _get_myco_home()
                assert "/tmp/xdg/myco" == str(home)

    def test_posix_fallback(self):
        """POSIX without XDG_CONFIG_HOME."""
        with mock.patch("sys.platform", "darwin"):
            with mock.patch.dict(os.environ, {}, clear=True):
                home = _get_myco_home()
                assert ".config/myco" in str(home)


class TestIsFirstRun:
    """Test first-run detection."""

    def test_first_run_marker_absent(self, tmp_path):
        """Return True when marker is absent."""
        with mock.patch("myco.germinate._get_myco_home", return_value=tmp_path):
            assert is_first_run() is True

    def test_first_run_marker_present(self, tmp_path):
        """Return False when marker exists."""
        marker = tmp_path / ".init-complete"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        with mock.patch("myco.germinate._get_myco_home", return_value=tmp_path):
            assert is_first_run() is False

    def test_first_run_env_var_opt_out(self, tmp_path):
        """Return False when MYCO_NO_AUTOINSTALL=1."""
        with mock.patch.dict(os.environ, {"MYCO_NO_AUTOINSTALL": "1"}):
            assert is_first_run() is False


class TestPromptAutoDetect:
    """Test TTY-aware prompt logic."""

    def test_no_tty_default_yes(self):
        """Non-TTY mode defaults to True (yes)."""
        with mock.patch("sys.stdin.isatty", return_value=False):
            assert prompt_auto_detect() is True

    def test_tty_user_yes(self):
        """TTY mode: user types 'y' or 'yes' or empty."""
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("builtins.input", return_value="y"):
                assert prompt_auto_detect() is True
            with mock.patch("builtins.input", return_value=""):
                assert prompt_auto_detect() is True

    def test_tty_user_no(self):
        """TTY mode: user types 'n' or 'no'."""
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("builtins.input", return_value="n"):
                assert prompt_auto_detect() is False

    def test_tty_eof(self):
        """TTY mode: EOF (user Ctrl-D) returns False."""
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("builtins.input", side_effect=EOFError):
                assert prompt_auto_detect() is False


class TestRunAutoSetup:
    """Test auto-setup dispatch."""

    def test_no_host_detected(self, tmp_path):
        """No host detected → graceful summary."""
        with mock.patch("myco.germinate.detect_active_symbiont", return_value=None):
            result = run_auto_setup(tmp_path)
            assert result["host"] == "unknown"
            assert result["installed"] == "false"

    def test_adapter_installed(self, tmp_path):
        """Adapter detected (unknown registry → graceful)."""
        with mock.patch("myco.germinate.detect_active_symbiont", return_value="unknown_host"):
            result = run_auto_setup(tmp_path)
            assert isinstance(result, dict)
            assert result["host"] == "unknown_host"
            assert result["installed"] == "false"

    def test_exception_handling(self, tmp_path):
        """Exception in auto-setup is caught and logged."""
        with mock.patch("myco.germinate.detect_active_symbiont", side_effect=RuntimeError("test error")):
            result = run_auto_setup(tmp_path)
            assert result["host"] == "error"
            assert result["installed"] == "false"


class TestMarkFirstRunDone:
    """Test marker file creation."""

    def test_mark_creates_file(self, tmp_path):
        """mark_first_run_done() creates .init-complete marker."""
        with mock.patch("myco.germinate._get_myco_home", return_value=tmp_path):
            mark_first_run_done()
            marker = tmp_path / ".init-complete"
            assert marker.exists()


class TestRunIfFirstTime:
    """Test overall auto-setup orchestration."""

    def test_not_first_run(self, tmp_path):
        """If not first run, return None."""
        marker = tmp_path / ".init-complete"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        with mock.patch("myco.germinate._get_myco_home", return_value=tmp_path):
            result = run_if_first_time(tmp_path)
            assert result is None

    def test_first_run_user_declines(self, tmp_path):
        """User declines prompt → return None, no marker."""
        with mock.patch("myco.germinate._get_myco_home", return_value=tmp_path):
            with mock.patch("myco.germinate.is_first_run", return_value=True):
                with mock.patch("myco.germinate.prompt_auto_detect", return_value=False):
                    result = run_if_first_time(tmp_path)
                    assert result is None
                    # Marker should not be created
                    marker = tmp_path / ".init-complete"
                    assert not marker.exists()

    def test_first_run_user_accepts(self, tmp_path):
        """User accepts and setup returns result."""
        with mock.patch("myco.germinate._get_myco_home", return_value=tmp_path):
            with mock.patch("myco.germinate.is_first_run", return_value=True):
                with mock.patch("myco.germinate.prompt_auto_detect", return_value=True):
                    with mock.patch("myco.germinate.detect_active_symbiont", return_value="unknown"):
                        # Unknown host → graceful summary, no crash
                        result = run_if_first_time(tmp_path)
                        assert isinstance(result, dict)
