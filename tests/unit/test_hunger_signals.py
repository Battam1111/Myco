"""Unit tests for hunger signal pipeline — covering Wave 46-59 additions."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def signal_project(tmp_path):
    """Create a project for testing hunger signals."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.43.0'\n"
        "  entry_point: MYCO.md\n"
        "  notes_schema:\n"
        "    dir: notes\n"
        "    terminal_statuses: [extracted, integrated]\n"
        "    dead_knowledge_threshold_days: 30\n"
        "    compression:\n"
        "      ripe_threshold: 5\n"
        "      ripe_age_days: 7\n"
        "      pressure_threshold: 2.0\n"
        "      gap_stale_days: 14\n"
        "  boot_reflex:\n"
        "    enabled: true\n"
        "    severity: HIGH\n"
        "    raw_backlog_threshold: 10\n"
        "    reflex_prefix: '[REFLEX HIGH]'\n"
        "    raw_exempt_sources: [bootstrap]\n"
        "    grandfather_ceiling_minor_versions: 5\n"
        "  inlet_triggers:\n"
        "    enabled: true\n"
        "    search_miss_threshold: 5\n"
        "    gap_threshold: 3\n"
        "    miss_state_file: '.myco_state/search_misses.yaml'\n",
        encoding="utf-8",
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    (tmp_path / ".myco_state").mkdir()
    (tmp_path / "log.md").write_text("# Log\n")
    return tmp_path


def _write_note(notes_dir, note_id, status, tags=None, created="2026-04-01"):
    content = (
        f"---\nid: {note_id}\nstatus: {status}\nsource: eat\n"
        f"tags: [{', '.join(tags or ['test'])}]\ncreated: {created}\n"
        f"last_touched: {created}\ndigest_count: 0\n"
        f"promote_candidate: false\nexcrete_reason: null\n---\n\nTest.\n"
    )
    (notes_dir / f"{note_id}.md").write_text(content)


def test_hunger_no_crash_on_empty_project(signal_project):
    """Empty project produces a hunger report without crashing."""
    from myco.notes import compute_hunger_report
    report = compute_hunger_report(signal_project)
    assert report.total == 0
    assert isinstance(report.signals, list)
    assert isinstance(report.actions, list)


def test_hunger_raw_backlog_signal(signal_project):
    """Exceeding raw backlog threshold produces REFLEX HIGH signal."""
    from myco.notes import compute_hunger_report
    notes = signal_project / "notes"
    for i in range(12):  # > threshold of 10
        _write_note(notes, f"n_20260401T00000{i:01d}_000{i:01d}", "raw",
                    created="2026-04-01")
    report = compute_hunger_report(signal_project)
    has_backlog = any("raw_backlog" in s for s in report.signals)
    assert has_backlog


def test_hunger_graph_orphans_signal(signal_project):
    """Graph orphans signal fires when orphan count > 10."""
    from myco.notes import compute_hunger_report
    # Create 15 unlinked doc files
    docs_dir = signal_project / "docs"
    docs_dir.mkdir()
    for i in range(15):
        (docs_dir / f"orphan_{i}.md").write_text(f"# Orphan {i}\n")
    report = compute_hunger_report(signal_project)
    has_orphan = any("graph_orphans" in s for s in report.signals)
    assert has_orphan


def test_hunger_cohort_staleness_signal(signal_project):
    """Cohort staleness fires for tags with only raw notes."""
    from myco.notes import compute_hunger_report
    notes = signal_project / "notes"
    for i in range(4):
        _write_note(notes, f"n_20260401T00000{i}_000{i}", "raw",
                    tags=["stale-topic"], created="2026-03-01")
    report = compute_hunger_report(signal_project)
    has_staleness = any("cohort_staleness" in s for s in report.signals)
    assert has_staleness
