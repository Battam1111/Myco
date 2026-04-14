"""Tests for myco.symbionts.cline — Cline host adapter for rules-based boot."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myco.symbionts import cline


class TestDetectCline:
    """Test Cline environment detection."""

    def test_detect_clinerules_dir(self, tmp_path):
        """Detect Cline from .clinerules/ directory."""
        (tmp_path / ".clinerules").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert cline.detect() is True

    def test_detect_clinerules_file(self, tmp_path):
        """Detect Cline from .clinerules file."""
        (tmp_path / ".clinerules").touch()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert cline.detect() is True

    def test_detect_roo_code(self, tmp_path):
        """Detect Roo Code variant with .roo/rules/."""
        (tmp_path / ".roo" / "rules").mkdir(parents=True)
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            assert cline.detect() is True

    def test_detect_vscode_with_cline_settings(self, tmp_path):
        """Detect Cline from .vscode/ + Cline global settings present."""
        (tmp_path / ".vscode").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = True
                mock_path.return_value = mock_path_obj
                assert cline.detect() is True

    def test_detect_negative_no_markers(self, tmp_path):
        """Return False when no Cline markers present."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = False
                mock_path.return_value = mock_path_obj
                assert cline.detect() is False


class TestClineSettingsPath:
    """Test OS-specific Cline settings path resolution."""

    def test_windows_path(self):
        """Windows path uses APPDATA environment variable."""
        with patch("sys.platform", "win32"):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"}):
                path = cline._cline_settings_path()
                assert "saoudrizwan.claude-dev" in str(path)
                assert "cline_mcp_settings.json" in str(path)

    def test_windows_path_fallback(self):
        """Windows path falls back to home/AppData when APPDATA not set."""
        with patch("sys.platform", "win32"):
            with patch.dict(os.environ, {}, clear=True):
                with patch("pathlib.Path.home", return_value=Path("C:\\Users\\test")):
                    path = cline._cline_settings_path()
                    assert "AppData" in str(path)
                    assert "Roaming" in str(path)

    def test_macos_path(self):
        """macOS path uses ~/Library/Application Support."""
        with patch("sys.platform", "darwin"):
            with patch("pathlib.Path.home", return_value=Path("/Users/test")):
                path = cline._cline_settings_path()
                assert "Library" in str(path)
                assert "Application Support" in str(path)
                assert "cline_mcp_settings.json" in str(path)

    def test_linux_path(self):
        """Linux path uses ~/.config."""
        with patch("sys.platform", "linux"):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                path = cline._cline_settings_path()
                assert ".config" in str(path)
                assert "cline_mcp_settings.json" in str(path)


class TestCheckHooks:
    """Test Cline hook verification."""

    def test_check_hooks_rules_injected(self, tmp_path):
        """Detect rules_injected when .clinerules/00-myco-boot.md with marker exists."""
        state = tmp_path / ".myco_state"
        state.mkdir()

        clinerules = tmp_path / ".clinerules"
        clinerules.mkdir()
        boot_rule = clinerules / "00-myco-boot.md"
        boot_rule.write_text("<!-- myco-boot: v1 -->\n# Boot rules", encoding="utf-8")

        result = cline.check_hooks(tmp_path)
        assert result["host"] == "cline"
        assert result["rules_injected"] is True
        assert result["session_start"] is True
        assert result["hook_level"] == "rules"

    def test_check_hooks_mcp_registered(self, tmp_path):
        """Detect mcp_registered when myco in cline_mcp_settings.json."""
        state = tmp_path / ".myco_state"
        state.mkdir()

        clinerules = tmp_path / ".clinerules"
        clinerules.mkdir()

        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            settings_file = tmp_path / "cline_mcp_settings.json"
            settings_file.write_text(
                json.dumps({"mcpServers": {"myco": {"command": "python"}}}),
                encoding="utf-8",
            )
            mock_path.return_value = settings_file

            result = cline.check_hooks(tmp_path)
            assert result["mcp_registered"] is True
            assert "mcp_only" in result["hook_level"] or result["session_start"] is False

    def test_check_hooks_rules_prioritized_over_mcp(self, tmp_path):
        """Rules-injected takes priority over MCP-only."""
        state = tmp_path / ".myco_state"
        state.mkdir()

        clinerules = tmp_path / ".clinerules"
        clinerules.mkdir()
        boot_rule = clinerules / "00-myco-boot.md"
        boot_rule.write_text("<!-- myco-boot: v1 -->\n# Boot", encoding="utf-8")

        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            settings_file = tmp_path / "cline_mcp_settings.json"
            settings_file.write_text(
                json.dumps({"mcpServers": {"myco": {"command": "python"}}}),
                encoding="utf-8",
            )
            mock_path.return_value = settings_file

            result = cline.check_hooks(tmp_path)
            assert result["rules_injected"] is True
            assert result["mcp_registered"] is True
            assert result["hook_level"] == "rules"
            assert result["session_start"] is True

    def test_check_hooks_missing_clinerules(self, tmp_path):
        """Report issue when .clinerules/ missing."""
        state = tmp_path / ".myco_state"
        state.mkdir()

        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            mock_path_obj = MagicMock()
            mock_path_obj.exists.return_value = False
            mock_path.return_value = mock_path_obj

            result = cline.check_hooks(tmp_path)
            assert any(".clinerules" in issue for issue in result["issues"])

    def test_check_hooks_missing_myco_state(self, tmp_path):
        """Report issue when .myco_state/ missing (bootstrap not run)."""
        clinerules = tmp_path / ".clinerules"
        clinerules.mkdir()
        boot_rule = clinerules / "00-myco-boot.md"
        boot_rule.write_text("<!-- myco-boot: v1 -->\n# Boot", encoding="utf-8")

        result = cline.check_hooks(tmp_path)
        assert any(".myco_state" in issue for issue in result["issues"])

    def test_check_hooks_invalid_mcp_json(self, tmp_path):
        """Handle gracefully when cline_mcp_settings.json is invalid JSON."""
        state = tmp_path / ".myco_state"
        state.mkdir()

        clinerules = tmp_path / ".clinerules"
        clinerules.mkdir()

        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            settings_file = tmp_path / "cline_mcp_settings.json"
            settings_file.write_text("{ INVALID JSON", encoding="utf-8")
            mock_path.return_value = settings_file

            result = cline.check_hooks(tmp_path)
            # Should report parse error but not crash
            assert any("parse" in issue.lower() for issue in result["issues"])


class TestInstallHooks:
    """Test Cline hook installation."""

    def test_install_hooks_creates_boot_rule(self, tmp_path):
        """install_hooks creates .clinerules/00-myco-boot.md with marker."""
        result = cline.install_hooks(tmp_path)
        assert result is True

        boot_rule = tmp_path / ".clinerules" / "00-myco-boot.md"
        assert boot_rule.exists()

        content = boot_rule.read_text(encoding="utf-8")
        assert "<!-- myco-boot: v1 -->" in content
        assert "Myco" in content

    def test_install_hooks_registers_mcp(self, tmp_path):
        """install_hooks merges myco into global cline_mcp_settings.json."""
        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            settings_file = tmp_path / "cline_mcp_settings.json"
            mock_path.return_value = settings_file

            result = cline.install_hooks(tmp_path)
            assert result is True

            assert settings_file.exists()
            settings = json.loads(settings_file.read_text(encoding="utf-8"))
            assert "myco" in settings.get("mcpServers", {})

    def test_install_hooks_idempotent(self, tmp_path):
        """install_hooks is idempotent — multiple calls produce same result."""
        # First call
        cline.install_hooks(tmp_path)
        boot_rule_1 = (tmp_path / ".clinerules" / "00-myco-boot.md").read_text(encoding="utf-8")

        # Second call
        cline.install_hooks(tmp_path)
        boot_rule_2 = (tmp_path / ".clinerules" / "00-myco-boot.md").read_text(encoding="utf-8")

        assert boot_rule_1 == boot_rule_2

    def test_install_hooks_preserves_existing_mcp_entries(self, tmp_path):
        """install_hooks merges into existing mcpServers without overwriting."""
        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            settings_file = tmp_path / "cline_mcp_settings.json"
            settings_file.write_text(
                json.dumps({
                    "mcpServers": {
                        "other_tool": {"command": "other"}
                    }
                }),
                encoding="utf-8",
            )
            mock_path.return_value = settings_file

            cline.install_hooks(tmp_path)

            settings = json.loads(settings_file.read_text(encoding="utf-8"))
            assert "myco" in settings["mcpServers"]
            assert "other_tool" in settings["mcpServers"]

    def test_install_hooks_roo_code_support(self, tmp_path):
        """install_hooks also writes .roo/rules/00-myco-boot.md if .roo/rules exists."""
        # Create Roo Code structure
        (tmp_path / ".roo" / "rules").mkdir(parents=True)

        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            mock_path.return_value = tmp_path / "cline_mcp_settings.json"

            result = cline.install_hooks(tmp_path)
            assert result is True

            # Check both locations
            assert (tmp_path / ".clinerules" / "00-myco-boot.md").exists()
            assert (tmp_path / ".roo" / "rules" / "00-myco-boot.md").exists()

            # Both should have the marker
            roo_content = (tmp_path / ".roo" / "rules" / "00-myco-boot.md").read_text(encoding="utf-8")
            assert "<!-- myco-boot: v1 -->" in roo_content

    def test_install_hooks_marker_stable(self, tmp_path):
        """Marker in boot rule is stable and idempotent across versions."""
        # Install once
        cline.install_hooks(tmp_path)
        boot_rule_path = tmp_path / ".clinerules" / "00-myco-boot.md"
        content_v1 = boot_rule_path.read_text(encoding="utf-8")

        # Verify marker is present
        assert content_v1.count("<!-- myco-boot: v1 -->") == 1

        # Install again — should produce identical content
        cline.install_hooks(tmp_path)
        content_v2 = boot_rule_path.read_text(encoding="utf-8")

        # Content should be identical
        assert content_v1 == content_v2
        assert content_v2.count("<!-- myco-boot: v1 -->") == 1


class TestDeepMerge:
    """Test JSON deep merge utility."""

    def test_deep_merge_simple(self):
        """Merge simple dicts."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = cline._deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self):
        """Merge nested dicts recursively."""
        base = {"x": {"y": 1, "z": 2}}
        override = {"x": {"z": 3, "w": 4}}
        result = cline._deep_merge(base, override)
        assert result == {"x": {"y": 1, "z": 3, "w": 4}}

    def test_deep_merge_preserves_base(self):
        """Merge does not mutate base dict."""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        result = cline._deep_merge(base, override)
        assert base == {"a": {"b": 1}}  # unchanged
        assert result == {"a": {"b": 1, "c": 2}}


class TestJsonMergeWrite:
    """Test JSON file merge-write utility."""

    def test_json_merge_write_creates_new(self, tmp_path):
        """Creates new file when it doesn't exist."""
        target = tmp_path / "test.json"
        payload = {"key": "value"}
        result = cline._json_merge_write(target, payload)

        assert result == "created"
        assert json.loads(target.read_text(encoding="utf-8")) == payload

    def test_json_merge_write_merges_existing(self, tmp_path):
        """Merges into existing file."""
        target = tmp_path / "test.json"
        target.write_text(json.dumps({"a": 1, "b": 2}), encoding="utf-8")

        patch = {"b": 3, "c": 4}
        result = cline._json_merge_write(target, patch)

        assert result == "merged"
        assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1, "b": 3, "c": 4}

    def test_json_merge_write_creates_parent_dirs(self, tmp_path):
        """Creates parent directories if needed."""
        target = tmp_path / "a" / "b" / "c" / "test.json"
        payload = {"x": 1}
        result = cline._json_merge_write(target, payload)

        assert result == "created"
        assert target.exists()

    def test_json_merge_write_invalid_json_overwrites(self, tmp_path):
        """Overwrites file if existing JSON is invalid."""
        target = tmp_path / "test.json"
        target.write_text("INVALID {", encoding="utf-8")

        payload = {"new": "content"}
        result = cline._json_merge_write(target, payload)

        assert result == "created — old file was invalid"
        assert json.loads(target.read_text(encoding="utf-8")) == payload


class TestIntegration:
    """Integration tests combining detect, check_hooks, install_hooks."""

    def test_full_workflow_from_detect_to_check(self, tmp_path):
        """Full workflow: detect -> install -> check."""
        # Start: no markers
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
                mock_path.return_value = tmp_path / "cline_mcp_settings.json"
                assert cline.detect() is False

        # Create .clinerules to enable detection
        (tmp_path / ".clinerules").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
                mock_path.return_value = tmp_path / "cline_mcp_settings.json"
                assert cline.detect() is True

        # Install hooks
        (tmp_path / ".myco_state").mkdir()
        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            mock_path.return_value = tmp_path / "cline_mcp_settings.json"
            assert cline.install_hooks(tmp_path) is True

        # Verify via check_hooks
        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            mock_path.return_value = tmp_path / "cline_mcp_settings.json"
            check = cline.check_hooks(tmp_path)
            assert check["rules_injected"] is True
            assert check["mcp_registered"] is True
            assert check["session_start"] is True
            assert check["hook_level"] == "rules"


class TestRegressionPrevention:
    """Tests to prevent regressions in core functionality."""

    def test_marker_never_duplicated(self, tmp_path):
        """Ensure marker appears exactly once after multiple install attempts."""
        boot_rule_path = tmp_path / ".clinerules"
        boot_rule_path.mkdir()

        # Simulate multiple install attempts (idempotent)
        for i in range(3):
            cline.install_hooks(tmp_path)
            content = (boot_rule_path / "00-myco-boot.md").read_text(encoding="utf-8")
            marker_count = content.count("<!-- myco-boot: v1 -->")
            assert marker_count == 1, f"After attempt {i+1}: marker duplicated: found {marker_count} times"

    def test_mcp_registration_resilient(self, tmp_path):
        """MCP registration survives partial failures."""
        with patch("myco.symbionts.cline._cline_settings_path") as mock_path:
            settings_file = tmp_path / "test_settings.json"
            mock_path.return_value = settings_file

            # Install with non-existent parent
            cline.install_hooks(tmp_path)

            # Should create parent directories
            assert settings_file.exists()
