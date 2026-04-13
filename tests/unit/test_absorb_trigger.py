"""Unit tests for inlet trigger detection — Wave 49."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def trigger_project(tmp_path):
    """Create a minimal Myco project for inlet trigger testing."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.38.0'\n"
        "  entry_point: MYCO.md\n"
        "  notes_schema:\n"
        "    dir: notes\n"
        "    compression:\n"
        "      ripe_threshold: 5\n"
        "      ripe_age_days: 7\n"
        "  inlet_triggers:\n"
        "    enabled: true\n"
        "    search_miss_threshold: 5\n"
        "    gap_threshold: 3\n"
        "    miss_state_file: '.myco_state/search_misses.yaml'\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    (tmp_path / ".myco_state").mkdir()
    return tmp_path


def test_no_trigger_when_no_misses(trigger_project):
    """Fresh project with no search misses should not fire inlet_ripe."""
    from myco.notes import detect_inlet_trigger

    result = detect_inlet_trigger(trigger_project)
    assert result is None


def test_trigger_on_search_misses(trigger_project):
    """Accumulated search misses above threshold fires inlet_ripe."""
    from myco.notes import detect_inlet_trigger

    miss_path = trigger_project / ".myco_state" / "search_misses.yaml"
    with open(miss_path, "w") as f:
        yaml.dump({"miss_count": 6, "recent_misses": []}, f)

    result = detect_inlet_trigger(trigger_project)
    assert result is not None
    assert "inlet_ripe" in result
    assert "6 search misses" in result


def test_trigger_on_cohort_gap(trigger_project):
    """Cohort gap with enough notes fires inlet_ripe."""
    from myco.notes import detect_inlet_trigger

    notes = trigger_project / "notes"
    for i in range(4):
        (notes / f"n_20260401T00000{i}_000{i}.md").write_text(
            f"---\nid: n_20260401T00000{i}_000{i}\nstatus: raw\n"
            f"source: eat\ntags: [gap-topic]\ncreated: 2026-04-01\n"
            f"last_touched: 2026-04-01\ndigest_count: 0\n"
            f"promote_candidate: false\nexcrete_reason: null\n---\n\nTest.\n"
        )

    result = detect_inlet_trigger(trigger_project)
    assert result is not None
    assert "inlet_ripe" in result
    assert "gap-topic" in result


def test_miss_recording(trigger_project):
    """record_search_miss increments count and stores queries."""
    from myco.notes import record_search_miss

    record_search_miss(trigger_project, "query_alpha")
    record_search_miss(trigger_project, "query_beta")
    record_search_miss(trigger_project, "query_gamma")

    miss_path = trigger_project / ".myco_state" / "search_misses.yaml"
    with open(miss_path, "r") as f:
        data = yaml.safe_load(f)

    assert data["miss_count"] == 3
    assert len(data["recent_misses"]) == 3
    assert data["recent_misses"][0]["query"] == "query_alpha"
