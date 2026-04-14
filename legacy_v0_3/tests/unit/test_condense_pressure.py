"""Unit tests for compression pressure metric — Wave 50."""

from pathlib import Path

import pytest


@pytest.fixture
def pressure_project(tmp_path):
    """Create a minimal Myco project for pressure testing."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.39.0'\n"
        "  entry_point: MYCO.md\n"
        "  notes_schema:\n"
        "    dir: notes\n"
        "    compression:\n"
        "      ripe_threshold: 5\n"
        "      ripe_age_days: 7\n"
        "      pressure_threshold: 2.0\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    return tmp_path


def _write_note(notes_dir, note_id, status):
    """Helper: write a minimal note file."""
    content = (
        f"---\nid: {note_id}\nstatus: {status}\nsource: eat\ntags: [test]\n"
        f"created: 2026-04-01\nlast_touched: 2026-04-01\ndigest_count: 0\n"
        f"promote_candidate: false\nexcrete_reason: null\n---\n\nTest.\n"
    )
    (notes_dir / f"{note_id}.md").write_text(content)


def test_pressure_zero_notes(pressure_project):
    """Empty notes directory gives pressure 0.0."""
    from myco.notes import compute_compression_pressure

    pressure, breakdown = compute_compression_pressure(pressure_project)
    assert pressure == 0.0
    assert breakdown["raw"] == 0


def test_pressure_high(pressure_project):
    """10 raw notes, 0 extracted → pressure = 10.0."""
    from myco.notes import compute_compression_pressure

    notes = pressure_project / "notes"
    for i in range(10):
        _write_note(notes, f"n_20260401T00000{i}_000{i}", "raw")

    pressure, breakdown = compute_compression_pressure(pressure_project)
    assert pressure == 10.0
    assert breakdown["raw"] == 10


def test_pressure_balanced(pressure_project):
    """2 raw, 3 extracted → pressure = 0.67."""
    from myco.notes import compute_compression_pressure

    notes = pressure_project / "notes"
    _write_note(notes, "n_20260401T000001_0001", "raw")
    _write_note(notes, "n_20260401T000002_0002", "raw")
    _write_note(notes, "n_20260401T000003_0003", "extracted")
    _write_note(notes, "n_20260401T000004_0004", "extracted")
    _write_note(notes, "n_20260401T000005_0005", "extracted")

    pressure, breakdown = compute_compression_pressure(pressure_project)
    assert pressure == pytest.approx(0.67, abs=0.01)


def test_pressure_signal_in_hunger(pressure_project):
    """High pressure produces signal in hunger report."""
    from myco.notes import compute_hunger_report

    notes = pressure_project / "notes"
    for i in range(10):
        _write_note(notes, f"n_20260401T00000{i}_000{i}", "raw")

    report = compute_hunger_report(pressure_project)
    has_pressure_signal = any("compression_pressure" in s for s in report.signals)
    assert has_pressure_signal, f"Expected compression_pressure signal, got: {report.signals}"
