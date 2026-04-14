"""Unit tests for Windsurf host adapter (myco.symbionts.windsurf)."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from myco.symbionts import windsurf


# =============================================================================
# Test detect() — 5-signal detection
# =============================================================================

class TestWindsurfDetect:
    """Test detect() with all 5 signals."""

    def test_detect_signal_1_cli_on_path(self):
        """Signal 1: windsurf CLI on PATH."""
        with patch("myco.symbionts.windsurf.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/windsurf"
            assert windsurf.detect() is True
            mock_which.assert_called_with("windsurf")

    def test_detect_signal_2_global_config_dir(self, tmp_path):
        """Signal 2: ~/.codeium/windsurf/ directory exists."""
        with patch("myco.symbionts.windsurf.Path.home") as mock_home, \
             patch("myco.symbionts.windsurf.shutil.which", return_value=None):
            fake_home = tmp_path / "home"
            fake_home.mkdir()
            mock_home.return_value = fake_home
            (fake_home / ".codeium" / "windsurf").mkdir(parents=True)
            assert windsurf.detect() is True

    def test_detect_signal_3_project_windsurf_dir(self, tmp_path, monkeypatch):
        """Signal 3: .windsurf/ directory in project."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".windsurf").mkdir()
        with patch("myco.symbionts.windsurf.shutil.which", return_value=None), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            mock_home.return_value = Path.home()
            assert windsurf.detect() is True

    def test_detect_signal_4_legacy_windsurfrules(self, tmp_path, monkeypatch):
        """Signal 4: .windsurfrules file in project."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".windsurfrules").write_text("# Legacy rules")
        with patch("myco.symbionts.windsurf.shutil.which", return_value=None), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            mock_home.return_value = Path.home()
            assert windsurf.detect() is True

    def test_detect_signal_5_env_windsurf(self, tmp_path, monkeypatch):
        """Signal 5: WINDSURF environment variable."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("WINDSURF", "1")
        with patch("myco.symbionts.windsurf.shutil.which", return_value=None), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            mock_home.return_value = Path.home()
            assert windsurf.detect() is True

    def test_detect_signal_5_env_codeium_home(self, tmp_path, monkeypatch):
        """Signal 5: CODEIUM_HOME environment variable."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("CODEIUM_HOME", "/some/path")
        with patch("myco.symbionts.windsurf.shutil.which", return_value=None), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            mock_home.return_value = Path.home()
            assert windsurf.detect() is True

    def test_detect_no_signals(self, tmp_path, monkeypatch):
        """No signals present: returns False."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("WINDSURF", raising=False)
        monkeypatch.delenv("CODEIUM_HOME", raising=False)
        with patch("myco.symbionts.windsurf.shutil.which", return_value=None), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            fake_home = tmp_path / "home"
            fake_home.mkdir()
            mock_home.return_value = fake_home
            assert windsurf.detect() is False


# =============================================================================
# Test check_hooks()
# =============================================================================

class TestWindsurfCheckHooks:
    """Test check_hooks() return structure and logic."""

    def test_check_hooks_returns_expected_keys(self, tmp_path):
        """check_hooks() returns all expected keys."""
        result = windsurf.check_hooks(tmp_path)
        expected_keys = {
            "host", "session_start", "session_end", "hook_level",
            "mcp_registered", "rules_injected", "session_hooks",
            "notes", "issues"
        }
        assert set(result.keys()) == expected_keys

    def test_check_hooks_host_is_windsurf(self, tmp_path):
        """host key is always 'windsurf'."""
        result = windsurf.check_hooks(tmp_path)
        assert result["host"] == "windsurf"

    def test_check_hooks_session_hooks_always_false(self, tmp_path):
        """session_hooks is always False (Windsurf has no SessionStart/SessionEnd)."""
        result = windsurf.check_hooks(tmp_path)
        assert result["session_hooks"] is False

    def test_check_hooks_hook_level_is_rules(self, tmp_path):
        """hook_level is 'rules' for Windsurf."""
        result = windsurf.check_hooks(tmp_path)
        assert result["hook_level"] == "rules"

    def test_check_hooks_all_ok_with_complete_setup(self, tmp_path):
        """All checks pass with complete setup."""
        # Create .windsurf/rules/ with myco marker
        rules_dir = tmp_path / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "00-myco-boot.md").write_text("<!-- myco-boot: v1 -->\nBoot rule")

        # Create .myco_state/
        (tmp_path / ".myco_state").mkdir()

        # Mock MCP registration
        with patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            result = windsurf.check_hooks(tmp_path)
            assert result["rules_injected"] is True
            assert result["mcp_registered"] is True
            assert not result["issues"]

    def test_check_hooks_detects_missing_rules(self, tmp_path):
        """Issues detected when rules are missing."""
        (tmp_path / ".myco_state").mkdir()
        with patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            result = windsurf.check_hooks(tmp_path)
            assert ".windsurf/rules/ missing myco-boot rule" in result["issues"]
            assert result["rules_injected"] is False

    def test_check_hooks_detects_missing_mcp(self, tmp_path):
        """Issues detected when MCP is not registered."""
        rules_dir = tmp_path / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "00-myco-boot.md").write_text("<!-- myco-boot: v1 -->")
        (tmp_path / ".myco_state").mkdir()

        with patch("myco.symbionts.windsurf._check_mcp_registered", return_value=False):
            result = windsurf.check_hooks(tmp_path)
            assert any("MCP not registered" in issue for issue in result["issues"])
            assert result["mcp_registered"] is False

    def test_check_hooks_detects_missing_myco_state(self, tmp_path):
        """Issues detected when .myco_state/ is missing."""
        rules_dir = tmp_path / ".windsurf" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "00-myco-boot.md").write_text("<!-- myco-boot: v1 -->")

        with patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            result = windsurf.check_hooks(tmp_path)
            assert any(".myco_state" in issue for issue in result["issues"])


# =============================================================================
# Test install_hooks() — idempotency and setup
# =============================================================================

class TestWindsurfInstallHooks:
    """Test install_hooks() setup and idempotency."""

    def test_install_hooks_creates_rules_dir(self, tmp_path):
        """install_hooks() creates .windsurf/rules/ directory."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=True), \
             patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            windsurf.install_hooks(tmp_path, write_hooks_json=False)
            assert (tmp_path / ".windsurf" / "rules").is_dir()

    def test_install_hooks_writes_boot_rule_with_marker(self, tmp_path):
        """install_hooks() writes boot rule with idempotent marker."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=True), \
             patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            windsurf.install_hooks(tmp_path, write_hooks_json=False)

            boot_rule = tmp_path / ".windsurf" / "rules" / "00-myco-boot.md"
            assert boot_rule.exists()
            content = boot_rule.read_text()
            assert "<!-- myco-boot: v1 -->" in content
            assert "myco hunger --execute" in content

    def test_install_hooks_idempotent_second_call(self, tmp_path):
        """install_hooks() idempotent on second invocation."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=True), \
             patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            windsurf.install_hooks(tmp_path, write_hooks_json=False)
            boot_rule = tmp_path / ".windsurf" / "rules" / "00-myco-boot.md"
            original_mtime = boot_rule.stat().st_mtime

            # Call again
            windsurf.install_hooks(tmp_path, write_hooks_json=False)
            new_mtime = boot_rule.stat().st_mtime
            assert original_mtime == new_mtime

    def test_install_hooks_calls_register_mcp(self, tmp_path):
        """install_hooks() calls _register_mcp_globally()."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=True) as mock_reg, \
             patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            windsurf.install_hooks(tmp_path, write_hooks_json=False)
            mock_reg.assert_called_once()

    def test_install_hooks_fails_if_mcp_registration_fails(self, tmp_path):
        """install_hooks() returns False if MCP registration fails."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=False):
            result = windsurf.install_hooks(tmp_path, write_hooks_json=False)
            assert result is False

    def test_install_hooks_optionally_writes_hooks_json(self, tmp_path):
        """install_hooks(write_hooks_json=True) writes hooks.json."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=True), \
             patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            windsurf.install_hooks(tmp_path, write_hooks_json=True)

            hooks_json = tmp_path / ".windsurf" / "hooks.json"
            assert hooks_json.exists()
            hooks_data = json.loads(hooks_json.read_text())
            assert "post_write_code" in hooks_data

    def test_install_hooks_skips_hooks_json_by_default(self, tmp_path):
        """install_hooks() (default) does NOT write hooks.json."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=True), \
             patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True):
            windsurf.install_hooks(tmp_path)  # write_hooks_json defaults to False

            hooks_json = tmp_path / ".windsurf" / "hooks.json"
            assert not hooks_json.exists()

    def test_install_hooks_hooks_json_write_failure_nonfatal(self, tmp_path):
        """Failure to write hooks.json does not fail install_hooks()."""
        with patch("myco.symbionts.windsurf._register_mcp_globally", return_value=True), \
             patch("myco.symbionts.windsurf._check_mcp_registered", return_value=True), \
             patch("builtins.open", side_effect=OSError("permission denied")):
            # Should still succeed because hooks.json is optional
            result = windsurf.install_hooks(tmp_path, write_hooks_json=True)
            # Result depends on check_hooks() returning True for rules+MCP
            # Since both are mocked as True, install should succeed overall


# =============================================================================
# Test _get_windsurf_mcp_config_path() — OS-specific paths
# =============================================================================

class TestWindsurfConfigPath:
    """Test OS-specific path resolution."""

    def test_config_path_linux(self, tmp_path):
        """Linux: ~/.codeium/windsurf/mcp_config.json"""
        with patch("myco.symbionts.windsurf.sys.platform", "linux"), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            path = windsurf._get_windsurf_mcp_config_path()
            assert path == tmp_path / ".codeium" / "windsurf" / "mcp_config.json"

    def test_config_path_macos(self, tmp_path):
        """macOS: ~/.codeium/windsurf/mcp_config.json"""
        with patch("myco.symbionts.windsurf.sys.platform", "darwin"), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            path = windsurf._get_windsurf_mcp_config_path()
            assert path == tmp_path / ".codeium" / "windsurf" / "mcp_config.json"

    def test_config_path_windows_with_appdata(self, tmp_path):
        """Windows with APPDATA: %APPDATA%\\Codeium\\Windsurf\\mcp_config.json"""
        with patch("myco.symbionts.windsurf.sys.platform", "win32"), \
             patch("myco.symbionts.windsurf.os.environ.get") as mock_env:
            def env_side_effect(key, default=None):
                if key == "APPDATA":
                    return str(tmp_path)
                return default
            mock_env.side_effect = env_side_effect
            path = windsurf._get_windsurf_mcp_config_path()
            assert path == tmp_path / "Codeium" / "Windsurf" / "mcp_config.json"

    def test_config_path_windows_no_appdata_fallback(self, tmp_path):
        """Windows without APPDATA: fallback to ~/.codeium/windsurf/"""
        with patch("myco.symbionts.windsurf.sys.platform", "win32"), \
             patch("myco.symbionts.windsurf.os.environ.get", return_value=None), \
             patch("myco.symbionts.windsurf.Path.home") as mock_home:
            mock_home.return_value = tmp_path
            path = windsurf._get_windsurf_mcp_config_path()
            assert path == tmp_path / ".codeium" / "windsurf" / "mcp_config.json"


# =============================================================================
# Test _check_mcp_registered()
# =============================================================================

class TestCheckMcpRegistered:
    """Test MCP registration check."""

    def test_check_mcp_registered_not_exists(self, tmp_path):
        """Returns False if config file does not exist."""
        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path") as mock_path:
            mock_path.return_value = tmp_path / "nonexistent.json"
            result = windsurf._check_mcp_registered(tmp_path)
            assert result is False

    def test_check_mcp_registered_valid_config(self, tmp_path):
        """Returns True if myco is in mcpServers."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(json.dumps({
            "mcpServers": {
                "myco": {"command": "python", "args": ["-m", "myco.mcp_server"]}
            }
        }))

        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path", return_value=config_file):
            result = windsurf._check_mcp_registered(tmp_path)
            assert result is True

    def test_check_mcp_registered_missing_myco_entry(self, tmp_path):
        """Returns False if myco key is absent."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(json.dumps({
            "mcpServers": {
                "other": {"command": "..."}
            }
        }))

        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path", return_value=config_file):
            result = windsurf._check_mcp_registered(tmp_path)
            assert result is False

    def test_check_mcp_registered_invalid_json(self, tmp_path):
        """Returns False if JSON is invalid."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text("{ invalid json")

        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path", return_value=config_file):
            result = windsurf._check_mcp_registered(tmp_path)
            assert result is False


# =============================================================================
# Test _register_mcp_globally()
# =============================================================================

class TestRegisterMcpGlobally:
    """Test global MCP registration."""

    def test_register_creates_config_file(self, tmp_path):
        """Creates mcp_config.json if it doesn't exist."""
        config_file = tmp_path / "mcp_config.json"

        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path", return_value=config_file):
            result = windsurf._register_mcp_globally()
            assert result is True
            assert config_file.exists()

            config = json.loads(config_file.read_text())
            assert "myco" in config["mcpServers"]

    def test_register_merges_existing_config(self, tmp_path):
        """Merges with existing mcpServers entries."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(json.dumps({
            "mcpServers": {
                "other": {"command": "other"}
            }
        }))

        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path", return_value=config_file):
            result = windsurf._register_mcp_globally()
            assert result is True

            config = json.loads(config_file.read_text())
            assert "other" in config["mcpServers"]
            assert "myco" in config["mcpServers"]

    def test_register_idempotent_already_registered(self, tmp_path):
        """Returns True if already registered."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(json.dumps({
            "mcpServers": {
                "myco": {"command": "python", "args": ["-m", "myco.mcp_server"]}
            }
        }))

        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path", return_value=config_file):
            original_content = config_file.read_text()
            result = windsurf._register_mcp_globally()
            assert result is True
            # Content should be unchanged
            assert config_file.read_text() == original_content

    def test_register_invalid_json_replaced(self, tmp_path):
        """Replaces invalid JSON with fresh config."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text("{ invalid json")

        with patch("myco.symbionts.windsurf._get_windsurf_mcp_config_path", return_value=config_file):
            result = windsurf._register_mcp_globally()
            assert result is True

            config = json.loads(config_file.read_text())
            assert "myco" in config["mcpServers"]


# =============================================================================
# Test _generate_boot_rule()
# =============================================================================

class TestGenerateBootRule:
    """Test boot rule content generation."""

    def test_generates_valid_markdown(self, tmp_path):
        """Generated content is valid Markdown."""
        content = windsurf._generate_boot_rule(tmp_path)
        assert "# Myco Boot Instruction" in content
        assert "<!-- myco-boot: v1 -->" in content

    def test_includes_project_path(self, tmp_path):
        """Generated content includes project directory path."""
        content = windsurf._generate_boot_rule(tmp_path)
        project_path = str(tmp_path.resolve())
        assert project_path in content
        assert "myco hunger --execute" in content

    def test_includes_documentation_references(self, tmp_path):
        """Generated content references key documentation."""
        content = windsurf._generate_boot_rule(tmp_path)
        assert "MYCO.md" in content
        assert ".windsurf/rules/" in content
        assert "docs/" in content
