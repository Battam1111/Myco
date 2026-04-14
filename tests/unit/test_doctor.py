"""Tests for myco.doctor_cmd — system health checks."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myco.doctor_cmd import (
    _check_contract_drift,
    _check_hunger_status,
    _check_myco_state,
    check_health,
    _format_report,
)


@pytest.fixture
def healthy_project(tmp_path):
    """Create a minimally healthy Myco project."""
    myco_state = tmp_path / ".myco_state"
    myco_state.mkdir()

    # Create boot_brief.md
    boot_brief = myco_state / "boot_brief.md"
    boot_brief.write_text("# Boot Brief\n")

    # Create minimal _canon.yaml
    canon = tmp_path / "_canon.yaml"
    canon.write_text("""
system:
  contract_version: "v0.45.0"
  synced_contract_version: "v0.45.0"
""")

    # Create notes directory
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()

    return tmp_path


class TestCheckMycoState:
    """Test .myco_state checks."""

    def test_myco_state_missing(self, tmp_path):
        """Detect missing .myco_state."""
        result = _check_myco_state(tmp_path)
        assert result["exists"] is False
        assert any("missing" in issue for issue in result["issues"])

    def test_myco_state_exists(self, healthy_project):
        """Detect healthy .myco_state."""
        result = _check_myco_state(healthy_project)
        assert result["exists"] is True
        # Should not report issues if boot_brief is fresh

    def test_boot_brief_missing(self, tmp_path):
        """Detect missing boot_brief.md."""
        myco_state = tmp_path / ".myco_state"
        myco_state.mkdir()
        result = _check_myco_state(tmp_path)
        assert any("boot_brief" in issue for issue in result["issues"])

    def test_boot_brief_age(self, tmp_path):
        """Detect stale boot_brief.md."""
        from datetime import datetime, timedelta

        myco_state = tmp_path / ".myco_state"
        myco_state.mkdir()
        boot_brief = myco_state / "boot_brief.md"
        boot_brief.write_text("# Boot\n")

        # Set mtime to 48 hours ago
        old_time = (datetime.now() - timedelta(days=2)).timestamp()
        import os
        os.utime(boot_brief, (old_time, old_time))

        result = _check_myco_state(tmp_path)
        assert any("old" in issue.lower() for issue in result["issues"])


class TestCheckContractDrift:
    """Test contract version drift detection."""

    def test_no_canon(self, tmp_path):
        """Detect missing _canon.yaml."""
        result = _check_contract_drift(tmp_path)
        assert "error" in result

    def test_synced(self, healthy_project):
        """Detect synced contract versions."""
        result = _check_contract_drift(healthy_project)
        assert result["synced"] is True
        assert result["issues"] == []

    def test_drift(self, tmp_path):
        """Detect contract drift."""
        canon = tmp_path / "_canon.yaml"
        canon.write_text("""
system:
  contract_version: "v0.45.0"
  synced_contract_version: "v0.44.0"
""")
        result = _check_contract_drift(tmp_path)
        assert result["synced"] is False
        assert any("drift" in issue.lower() for issue in result["issues"])


class TestCheckHungerStatus:
    """Test hunger status checks."""

    def test_hunger_status_no_notes(self, tmp_path):
        """Handle case with no notes."""
        notes = tmp_path / "notes"
        notes.mkdir()
        canon = tmp_path / "_canon.yaml"
        canon.write_text("system:\n  principles_count: 13\n")

        result = _check_hunger_status(tmp_path)
        assert "signal_count" in result


class TestCheckHealth:
    """Test aggregated health check."""

    def test_check_health_structure(self, healthy_project):
        """check_health returns expected structure."""
        health = check_health(healthy_project)
        assert "host" in health
        assert "hooks" in health
        assert "myco_state" in health
        assert "contract" in health
        assert "hunger" in health

    def test_check_health_unhealthy(self, tmp_path):
        """check_health detects unhealthy state."""
        health = check_health(tmp_path)
        assert "hooks" in health
        assert "myco_state" in health


class TestFormatReport:
    """Test report formatting."""

    def test_format_report_json(self, healthy_project):
        """Format report as JSON."""
        health = check_health(healthy_project)
        report = _format_report(health, json_mode=True)
        import json
        parsed = json.loads(report)  # Should not raise
        assert isinstance(parsed, dict)

    def test_format_report_text(self, healthy_project):
        """Format report as text."""
        health = check_health(healthy_project)
        report = _format_report(health, json_mode=False)
        assert "HOST ENVIRONMENT" in report
        assert "SESSION HOOKS" in report
        assert ".MYCO_STATE INTEGRITY" in report
        assert "CONTRACT VERSION" in report
