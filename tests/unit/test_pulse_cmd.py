"""
Tests for myco pulse — merged doctor + diagnose health check.

Wave 56 (merged 2026-04-14): Consolidates doctor (hooks) and diagnose (deployment).
"""

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from myco.pulse_cmd import (
    run_pulse,
    check_health,
    _format_report,
    _check_myco_state,
    _check_contract_drift,
    _check_hunger_status,
    _verify_deployment,
)


class TestCheckMycoState:
    """Test .myco_state/ integrity checks."""

    def test_myco_state_missing(self, tmp_path):
        """Missing .myco_state/ returns failure."""
        result = _check_myco_state(tmp_path)
        assert not result["exists"]
        assert "missing .myco_state/ directory" in result["issues"]

    def test_myco_state_exists_no_brief(self, tmp_path):
        """Existing .myco_state/ without boot_brief.md."""
        (tmp_path / ".myco_state").mkdir()
        result = _check_myco_state(tmp_path)
        assert result["exists"]
        assert "missing boot_brief.md" in result["issues"][0]


class TestCheckContractDrift:
    """Test contract version consistency."""

    def test_missing_canon(self, tmp_path):
        """Missing _canon.yaml."""
        result = _check_contract_drift(tmp_path)
        assert "error" in result

    def test_contract_in_sync(self, tmp_path):
        """Synced contract versions."""
        canon_path = tmp_path / "_canon.yaml"
        canon_path.write_text("""
system:
  contract_version: 0.6.0
  synced_contract_version: 0.6.0
""", encoding="utf-8")
        result = _check_contract_drift(tmp_path)
        assert result["synced"]
        assert result["kernel_version"] == "0.6.0"

    def test_contract_drift_detected(self, tmp_path):
        """Drift in contract versions."""
        canon_path = tmp_path / "_canon.yaml"
        canon_path.write_text("""
system:
  contract_version: 0.6.0
  synced_contract_version: 0.5.0
""", encoding="utf-8")
        result = _check_contract_drift(tmp_path)
        assert not result["synced"]
        assert any("drift" in issue for issue in result["issues"])


class TestFormatReport:
    """Test report formatting."""

    def test_json_mode(self):
        """JSON mode returns valid JSON."""
        health = {
            "symbiont": {"detected": "cowork", "hook_level": "native"},
            "hooks": {"summary": {"all_ok": True, "issues": []}},
            "myco_state": {"exists": True, "issues": []},
            "contract": {"synced": True, "kernel_version": "0.6.0"},
            "hunger": {"signal_count": 0, "critical_signals": 0},
            "deployment": {"passed": 5, "total": 5, "issues": []},
        }
        report = _format_report(health, json_mode=True)
        parsed = json.loads(report)
        assert parsed["symbiont"]["detected"] == "cowork"

    def test_human_readable_format(self):
        """Human-readable mode contains expected sections."""
        health = {
            "symbiont": {"detected": "cowork", "hook_level": "native"},
            "hooks": {"summary": {"all_ok": True, "issues": []}},
            "myco_state": {"exists": True, "issues": []},
            "contract": {"synced": True, "kernel_version": "0.6.0"},
            "hunger": {"signal_count": 0, "critical_signals": 0},
            "deployment": {"passed": 5, "total": 5, "issues": []},
        }
        report = _format_report(health, json_mode=False)
        assert "SYMBIONT ENVIRONMENT" in report
        assert "SESSION HOOKS" in report
        assert "DEPLOYMENT VERIFICATION" in report


class TestPulseCommand:
    """Integration tests for myco pulse."""

    def test_run_pulse_json_output(self, tmp_path, monkeypatch):
        """pulse command with --json flag."""
        monkeypatch.chdir(tmp_path)

        # Create minimal Myco structure
        (tmp_path / ".myco_state").mkdir(exist_ok=True)
        (tmp_path / "notes").mkdir(exist_ok=True)
        (tmp_path / "_canon.yaml").write_text("""
system:
  contract_version: 0.6.0
  synced_contract_version: 0.6.0
""", encoding="utf-8")

        # Mock dependencies to prevent subprocess calls
        with mock.patch("myco.project.find_project_root") as mock_find:
            mock_find.return_value = tmp_path

            with mock.patch("myco.symbionts.check_all_hooks") as mock_hooks:
                mock_hooks.return_value = {
                    "summary": {"all_ok": True, "issues": []},
                    "adapters": {},
                }

                with mock.patch("myco.notes.compute_hunger_report") as mock_hunger:
                    mock_hunger.return_value = {
                        "signals": [],
                        "signal_count": 0,
                    }

                    from argparse import Namespace
                    args = Namespace(json=True, project_dir=".")

                    with mock.patch("builtins.print") as mock_print:
                        result = run_pulse(args)
                        # Verify JSON was printed
                        mock_print.assert_called()
                        output = mock_print.call_args[0][0]
                        parsed = json.loads(output)
                        assert "symbiont" in parsed
                        assert "deployment" in parsed
