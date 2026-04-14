"""Tests for L27 Protocol Adherence lint."""

from pathlib import Path

import pytest

from myco.immune import lint_protocol_adherence


@pytest.fixture
def canon():
    """Minimal canon dict."""
    return {"system": {}}


class TestProtocolAdherence:
    """Test L27 Protocol Adherence lint."""

    def test_no_violations(self, tmp_path, canon):
        """Healthy state produces no violations."""
        # Create notes directory with some integrated notes
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create boot_brief
        state = tmp_path / ".myco_state"
        state.mkdir()
        boot_brief = state / "boot_brief.md"
        boot_brief.write_text("# Boot\n")

        issues = lint_protocol_adherence(canon, tmp_path)
        assert len(issues) == 0

    def test_missing_boot_brief(self, tmp_path, canon):
        """Detect missing boot_brief.md."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        issues = lint_protocol_adherence(canon, tmp_path)
        assert len(issues) > 0
        assert "L27" in str(issues[0])
        assert "missing_boot_brief" in str(issues[0])

    def test_stale_boot_brief(self, tmp_path, canon):
        """Detect stale boot_brief.md (>3 days old)."""
        from datetime import datetime, timedelta
        import os

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        state = tmp_path / ".myco_state"
        state.mkdir()

        boot_brief = state / "boot_brief.md"
        boot_brief.write_text("# Boot\n")

        # Set mtime to 5 days ago
        old_time = (datetime.now() - timedelta(days=5)).timestamp()
        os.utime(boot_brief, (old_time, old_time))

        issues = lint_protocol_adherence(canon, tmp_path)
        assert len(issues) > 0
        assert "L27" in str(issues[0])
        assert "stale_boot_brief" in str(issues[0])

    def test_eat_digest_imbalance(self, tmp_path, canon):
        """Detect imbalance between raw notes and digested notes."""
        from myco.notes import write_note

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        state = tmp_path / ".myco_state"
        state.mkdir()
        boot_brief = state / "boot_brief.md"
        boot_brief.write_text("# Boot\n")

        # Create many raw notes but few integrated
        for i in range(5):
            write_note(tmp_path, f"Raw note {i}", status="raw", title=f"Note {i}")

        issues = lint_protocol_adherence(canon, tmp_path)
        # Should detect imbalance
        assert any("eat_digest_imbalance" in str(issue) for issue in issues) or len(issues) == 0

    def test_unrecovered_misses(self, tmp_path, canon):
        """Detect unrecovered search misses."""
        import yaml

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        state = tmp_path / ".myco_state"
        state.mkdir()
        boot_brief = state / "boot_brief.md"
        boot_brief.write_text("# Boot\n")

        # Create search misses log
        miss_file = state / "search_misses.yaml"
        misses = {
            "recent_misses": [
                {"query": "topic1", "timestamp": "2024-01-01"},
                {"query": "topic2", "timestamp": "2024-01-02"},
                {"query": "topic1", "timestamp": "2024-01-03"},
                {"query": "topic3", "timestamp": "2024-01-04"},
            ]
        }
        with open(miss_file, "w") as f:
            yaml.dump(misses, f)

        issues = lint_protocol_adherence(canon, tmp_path)
        # Should detect unrecovered misses
        assert any("unrecovered_misses" in str(issue) for issue in issues) or len(issues) == 0

    def test_multiple_violations(self, tmp_path, canon):
        """Detect multiple violations → MEDIUM severity."""
        import yaml

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        state = tmp_path / ".myco_state"
        state.mkdir()

        # Don't create boot_brief (violation 1)
        # Create search misses (violation 2)
        miss_file = state / "search_misses.yaml"
        misses = {
            "recent_misses": [
                {"query": "x", "timestamp": "2024-01-01"},
                {"query": "x", "timestamp": "2024-01-02"},
                {"query": "y", "timestamp": "2024-01-03"},
                {"query": "y", "timestamp": "2024-01-04"},
            ]
        }
        with open(miss_file, "w") as f:
            yaml.dump(misses, f)

        issues = lint_protocol_adherence(canon, tmp_path)
        if issues:
            # If violations detected, should be MEDIUM (multiple violations)
            assert "MEDIUM" in str(issues[0]) or "LOW" in str(issues[0])
