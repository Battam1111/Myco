"""Tests for myco.symbionts.common — shared utilities for all host adapters."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from myco.symbionts import common


class TestUserConfigDir:
    """Test user_config_dir per platform."""

    def test_linux_xdg_config_home(self, monkeypatch, tmp_path):
        """Linux: respect XDG_CONFIG_HOME if set."""
        xdg = tmp_path / "xdg_config"
        xdg.mkdir()
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
        monkeypatch.setattr("sys.platform", "linux")

        result = common.user_config_dir("myapp")
        assert result == xdg / "myapp"

    def test_linux_default_config(self, monkeypatch, tmp_path):
        """Linux: default to ~/.config if XDG_CONFIG_HOME not set."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setattr("sys.platform", "linux")

        result = common.user_config_dir("myapp")
        assert result == Path.home() / ".config" / "myapp"

    def test_windows_appdata(self, monkeypatch, tmp_path):
        """Windows: use %APPDATA% if set."""
        appdata = tmp_path / "appdata"
        appdata.mkdir()
        monkeypatch.setenv("APPDATA", str(appdata))
        monkeypatch.setattr("sys.platform", "win32")

        result = common.user_config_dir("myapp")
        assert result == appdata / "myapp"

    def test_windows_fallback(self, monkeypatch):
        """Windows: fallback to %USERPROFILE%/AppData/Roaming if APPDATA missing."""
        monkeypatch.delenv("APPDATA", raising=False)
        monkeypatch.setattr("sys.platform", "win32")

        result = common.user_config_dir("myapp")
        assert "AppData" in str(result) and "Roaming" in str(result)

    def test_macos_app_support(self, monkeypatch):
        """macOS: use ~/Library/Application Support."""
        monkeypatch.setattr("sys.platform", "darwin")

        result = common.user_config_dir("myapp")
        assert result == Path.home() / "Library" / "Application Support" / "myapp"


class TestUserDataDir:
    """Test user_data_dir per platform."""

    def test_linux_xdg_data_home(self, monkeypatch, tmp_path):
        """Linux: respect XDG_DATA_HOME if set."""
        xdg = tmp_path / "xdg_data"
        xdg.mkdir()
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg))
        monkeypatch.setattr("sys.platform", "linux")

        result = common.user_data_dir("myapp")
        assert result == xdg / "myapp"

    def test_linux_default_data(self, monkeypatch):
        """Linux: default to ~/.local/share."""
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setattr("sys.platform", "linux")

        result = common.user_data_dir("myapp")
        assert result == Path.home() / ".local" / "share" / "myapp"

    def test_windows_localappdata(self, monkeypatch, tmp_path):
        """Windows: use %LOCALAPPDATA%."""
        localappdata = tmp_path / "localappdata"
        localappdata.mkdir()
        monkeypatch.setenv("LOCALAPPDATA", str(localappdata))
        monkeypatch.setattr("sys.platform", "win32")

        result = common.user_data_dir("myapp")
        assert result == localappdata / "myapp"

    def test_macos_app_support(self, monkeypatch):
        """macOS: use ~/Library/Application Support."""
        monkeypatch.setattr("sys.platform", "darwin")

        result = common.user_data_dir("myapp")
        assert result == Path.home() / "Library" / "Application Support" / "myapp"


class TestVscodeGlobalStorageDir:
    """Test vscode_global_storage_dir per platform."""

    def test_linux(self, monkeypatch):
        """Linux: ~/.config/Code/User/globalStorage."""
        monkeypatch.setattr("sys.platform", "linux")

        result = common.vscode_global_storage_dir()
        assert result == Path.home() / ".config" / "Code" / "User" / "globalStorage"

    def test_windows(self, monkeypatch, tmp_path):
        """Windows: %APPDATA%/Code/User/globalStorage."""
        appdata = tmp_path / "appdata"
        appdata.mkdir()
        monkeypatch.setenv("APPDATA", str(appdata))
        monkeypatch.setattr("sys.platform", "win32")

        result = common.vscode_global_storage_dir()
        assert result == appdata / "Code" / "User" / "globalStorage"

    def test_macos(self, monkeypatch):
        """macOS: ~/Library/Application Support/Code/User/globalStorage."""
        monkeypatch.setattr("sys.platform", "darwin")

        result = common.vscode_global_storage_dir()
        assert result == Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage"


class TestSafeReadJson:
    """Test safe_read_json."""

    def test_missing_file(self, tmp_path):
        """Missing file returns {}."""
        path = tmp_path / "missing.json"
        assert common.safe_read_json(path) == {}

    def test_valid_json(self, tmp_path):
        """Valid JSON is parsed and returned."""
        path = tmp_path / "config.json"
        data = {"key": "value", "nested": {"key2": "value2"}}
        path.write_text(json.dumps(data), encoding="utf-8")

        result = common.safe_read_json(path)
        assert result == data

    def test_invalid_json(self, tmp_path):
        """Invalid JSON returns {}."""
        path = tmp_path / "invalid.json"
        path.write_text("{ invalid json", encoding="utf-8")

        assert common.safe_read_json(path) == {}

    def test_unicode_error(self, tmp_path):
        """Unreadable file returns {}."""
        path = tmp_path / "unreadable.json"
        path.write_bytes(b"\xff\xfe")

        assert common.safe_read_json(path) == {}


class TestSafeReadToml:
    """Test safe_read_toml."""

    def test_missing_file(self, tmp_path):
        """Missing file returns {}."""
        path = tmp_path / "missing.toml"
        assert common.safe_read_toml(path) == {}

    def test_unreadable_file(self, tmp_path):
        """Unreadable file returns {}."""
        path = tmp_path / "unreadable.toml"
        path.write_bytes(b"\xff\xfe")

        assert common.safe_read_toml(path) == {}


class TestDeepMerge:
    """Test _deep_merge helper."""

    def test_simple_merge(self):
        """Merge two flat dicts."""
        base = {"a": 1}
        override = {"b": 2}
        result = common._deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_deep_merge_dicts(self):
        """Recursively merge nested dicts."""
        base = {"mcpServers": {"other": {"command": "python"}}}
        override = {"mcpServers": {"myco": {"command": "python3"}}}
        result = common._deep_merge(base, override)
        assert result == {
            "mcpServers": {
                "other": {"command": "python"},
                "myco": {"command": "python3"}
            }
        }

    def test_override_non_dict_with_dict(self):
        """Override scalar with dict."""
        base = {"key": "value"}
        override = {"key": {"nested": "value"}}
        result = common._deep_merge(base, override)
        assert result == {"key": {"nested": "value"}}

    def test_override_dict_with_scalar(self):
        """Override dict with scalar."""
        base = {"key": {"nested": "value"}}
        override = {"key": "scalar"}
        result = common._deep_merge(base, override)
        assert result == {"key": "scalar"}


class TestJsonMergeWrite:
    """Test json_merge_write."""

    def test_create_new_file(self, tmp_path):
        """Create new JSON file if missing."""
        path = tmp_path / "new.json"
        patch = {"key": "value"}

        changed = common.json_merge_write(path, patch)
        assert changed is True
        assert json.loads(path.read_text(encoding="utf-8")) == patch

    def test_merge_preserves_unrelated_keys(self, tmp_path):
        """Merge preserves unrelated top-level keys."""
        path = tmp_path / "config.json"
        existing = {"other": "value", "mcpServers": {"other_server": {}}}
        path.write_text(json.dumps(existing), encoding="utf-8")

        patch = {"mcpServers": {"myco": {"command": "python"}}}
        changed = common.json_merge_write(path, patch)

        assert changed is True
        result = json.loads(path.read_text(encoding="utf-8"))
        assert result["other"] == "value"
        assert result["mcpServers"]["other_server"] == {}
        assert result["mcpServers"]["myco"]["command"] == "python"

    def test_deep_merge(self, tmp_path):
        """Deep-merge nested dictionaries."""
        path = tmp_path / "config.json"
        existing = {"a": {"b": {"c": 1}}}
        path.write_text(json.dumps(existing), encoding="utf-8")

        patch = {"a": {"b": {"d": 2}}}
        changed = common.json_merge_write(path, patch)

        assert changed is True
        result = json.loads(path.read_text(encoding="utf-8"))
        assert result == {"a": {"b": {"c": 1, "d": 2}}}

    def test_no_change_returns_false(self, tmp_path):
        """Return False if content unchanged."""
        path = tmp_path / "config.json"
        data = {"key": "value"}
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        changed = common.json_merge_write(path, {"key": "value"})
        assert changed is False

    def test_invalid_json_replaced(self, tmp_path):
        """Invalid JSON is replaced, returning True."""
        path = tmp_path / "broken.json"
        path.write_text("{ invalid", encoding="utf-8")

        patch = {"valid": "json"}
        changed = common.json_merge_write(path, patch)

        assert changed is True
        assert json.loads(path.read_text(encoding="utf-8")) == patch

    def test_creates_parent_directories(self, tmp_path):
        """Create parent directories if missing."""
        path = tmp_path / "a" / "b" / "c" / "config.json"

        changed = common.json_merge_write(path, {"key": "value"})
        assert changed is True
        assert path.exists()


class TestEnsureMarkerBlock:
    """Test ensure_marker_block."""

    def test_create_new_file(self, tmp_path):
        """Create file with marker block if missing."""
        path = tmp_path / "README.md"
        content = "# My Config"

        changed = common.ensure_marker_block(path, "boot", content)
        assert changed is True
        assert "<!-- myco-boot: v1 -->" in path.read_text(encoding="utf-8")
        assert content in path.read_text(encoding="utf-8")

    def test_insert_marker_block(self, tmp_path):
        """Insert marker block into existing file."""
        path = tmp_path / "README.md"
        existing = "# Original Content\n"
        path.write_text(existing, encoding="utf-8")

        content = "# Auto-generated Section"
        changed = common.ensure_marker_block(path, "boot", content)

        assert changed is True
        result = path.read_text(encoding="utf-8")
        assert "# Original Content" in result
        assert "<!-- myco-boot: v1 -->" in result
        assert content in result

    def test_update_existing_marker_block(self, tmp_path):
        """Update existing marker block."""
        path = tmp_path / "README.md"
        old_content = "# Old Section"
        existing = f"# Intro\n<!-- myco-boot: v1 -->\n{old_content}\n<!-- /myco-boot -->\n# Outro\n"
        path.write_text(existing, encoding="utf-8")

        new_content = "# New Section"
        changed = common.ensure_marker_block(path, "boot", new_content)

        assert changed is True
        result = path.read_text(encoding="utf-8")
        assert "# Intro" in result
        assert "# Outro" in result
        assert new_content in result
        assert old_content not in result

    def test_no_change_returns_false(self, tmp_path):
        """Return False if marker block already contains exact content."""
        path = tmp_path / "README.md"
        content = "# Section"
        block = f"<!-- myco-boot: v1 -->\n{content}\n<!-- /myco-boot -->"
        path.write_text(block + "\n", encoding="utf-8")

        changed = common.ensure_marker_block(path, "boot", content)
        assert changed is False

    def test_multiple_markers(self, tmp_path):
        """Handle file with multiple marker blocks."""
        path = tmp_path / "README.md"
        path.write_text(
            "<!-- myco-boot: v1 -->\nold boot\n<!-- /myco-boot -->\n"
            "<!-- myco-config: v1 -->\nconfig\n<!-- /myco-config -->\n",
            encoding="utf-8"
        )

        changed = common.ensure_marker_block(path, "boot", "new boot")
        assert changed is True

        result = path.read_text(encoding="utf-8")
        assert "new boot" in result
        assert "config" in result


class TestTomlMergeWrite:
    """Test toml_merge_write."""

    def test_create_new_file(self, tmp_path):
        """Create new TOML file with section."""
        path = tmp_path / "config.toml"
        entries = {"command": "python", "args": ["-m", "myco"]}

        changed = common.toml_merge_write(path, "mcp_servers.myco", entries)
        assert changed is True

        content = path.read_text(encoding="utf-8")
        assert "[mcp_servers.myco]" in content
        assert 'command = "python"' in content

    def test_skip_existing_section(self, tmp_path):
        """Skip if section already exists (idempotency)."""
        path = tmp_path / "config.toml"
        existing = "[mcp_servers.myco]\ncommand = 'python'\n"
        path.write_text(existing, encoding="utf-8")

        entries = {"command": "python3"}
        changed = common.toml_merge_write(path, "mcp_servers.myco", entries)

        assert changed is False

    def test_append_to_existing_file(self, tmp_path):
        """Append section to existing file without the section."""
        path = tmp_path / "config.toml"
        existing = "[other_section]\nkey = 'value'\n"
        path.write_text(existing, encoding="utf-8")

        entries = {"command": "python"}
        changed = common.toml_merge_write(path, "mcp_servers.myco", entries)

        assert changed is True
        content = path.read_text(encoding="utf-8")
        assert "[other_section]" in content
        assert "[mcp_servers.myco]" in content

    def test_format_string_values(self, tmp_path):
        """Format string values correctly."""
        path = tmp_path / "config.toml"
        entries = {"command": "python", "option": "value"}

        changed = common.toml_merge_write(path, "section", entries)
        assert changed is True

        content = path.read_text(encoding="utf-8")
        assert 'command = "python"' in content
        assert 'option = "value"' in content

    def test_format_list_values(self, tmp_path):
        """Format list values as TOML arrays."""
        path = tmp_path / "config.toml"
        entries = {"args": ["python", "-m", "myco"]}

        changed = common.toml_merge_write(path, "section", entries)
        assert changed is True

        content = path.read_text(encoding="utf-8")
        assert 'args = ["python", "-m", "myco"]' in content

    def test_creates_parent_directories(self, tmp_path):
        """Create parent directories if missing."""
        path = tmp_path / "a" / "b" / "config.toml"
        entries = {"key": "value"}

        changed = common.toml_merge_write(path, "section", entries)
        assert changed is True
        assert path.exists()


class TestHookLevelConstants:
    """Test hook level constants."""

    def test_hook_level_constants(self):
        """Constants are defined and correct."""
        assert common.HOOK_LEVEL_NATIVE == "native"
        assert common.HOOK_LEVEL_RULES == "rules"
        assert common.HOOK_LEVEL_MCP_ONLY == "mcp_only"
        assert common.HOOK_LEVEL_PROTOCOL == "protocol"


class TestIntegration:
    """Integration tests across multiple utilities."""

    def test_json_merge_then_read(self, tmp_path):
        """Write JSON via merge, then read via safe_read."""
        path = tmp_path / "config.json"
        patch1 = {"servers": {"server1": {"port": 8080}}}
        patch2 = {"servers": {"server2": {"port": 9090}}}

        common.json_merge_write(path, patch1)
        common.json_merge_write(path, patch2)

        result = common.safe_read_json(path)
        assert result["servers"]["server1"]["port"] == 8080
        assert result["servers"]["server2"]["port"] == 9090

    def test_marker_blocks_with_json(self, tmp_path):
        """Use marker blocks for documentation alongside JSON config."""
        doc = tmp_path / "README.md"
        config = tmp_path / "config.json"

        # Marker block in documentation
        common.ensure_marker_block(doc, "config", "Configuration guide here")

        # JSON configuration
        common.json_merge_write(config, {"enabled": True})

        doc_content = doc.read_text(encoding="utf-8")
        config_content = common.safe_read_json(config)

        assert "Configuration guide here" in doc_content
        assert config_content["enabled"] is True
