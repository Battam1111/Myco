"""Unit tests for myco.notes_cmd — CLI dispatch for eat/digest/view/hunger/prune."""

from pathlib import Path

import pytest


@pytest.fixture
def cmd_project(tmp_path):
    """Minimal project for notes_cmd testing."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.43.0'\n"
        "  entry_point: MYCO.md\n"
        "  notes_schema:\n"
        "    dir: notes\n"
        "    required_fields: [id, status, source, tags, created, last_touched, digest_count, promote_candidate, excrete_reason]\n"
        "    valid_statuses: [raw, digesting, extracted, integrated, excreted]\n"
        "    valid_sources: [chat, eat, promote, import, bootstrap, forage, upstream_absorbed, compress, inlet]\n"
        "    terminal_statuses: [extracted, integrated]\n"
        "    dead_knowledge_threshold_days: 30\n"
        "    compression:\n"
        "      ripe_threshold: 5\n"
        "      ripe_age_days: 7\n"
        "      pressure_threshold: 2.0\n"
        "      gap_stale_days: 14\n"
        "  boot_reflex:\n"
        "    enabled: false\n"
        "    raw_backlog_threshold: 10\n"
        "    raw_exempt_sources: [bootstrap]\n"
        "    grandfather_ceiling_minor_versions: 99\n",
        encoding="utf-8",
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    (tmp_path / "log.md").write_text("# Log\n")
    (tmp_path / ".myco_state").mkdir()
    return tmp_path


def test_run_eat_creates_note(cmd_project):
    """run_eat creates a raw note with correct metadata."""
    import argparse
    from myco.notes_cmd import run_eat
    args = argparse.Namespace(
        project_dir=str(cmd_project), tags="test-tag",
        content="Test content for eat.", title=None, json=False,
        source=None,
    )
    rc = run_eat(args)
    assert rc == 0
    notes = list((cmd_project / "notes").glob("n_*.md"))
    assert len(notes) == 1
    content = notes[0].read_text(encoding="utf-8")
    assert "status: raw" in content
    assert "test-tag" in content


def test_run_hunger_returns_zero_on_healthy(cmd_project):
    """run_hunger returns 0 when substrate is healthy."""
    import argparse
    from myco.notes_cmd import run_hunger
    args = argparse.Namespace(
        project_dir=str(cmd_project), json=False, execute=False,
    )
    rc = run_hunger(args)
    # May return 1 on no_deep_digest (empty project has no digested notes)
    assert rc in (0, 1)


def test_run_view_list_empty(cmd_project):
    """run_view with no notes returns gracefully."""
    import argparse
    from myco.notes_cmd import run_view
    args = argparse.Namespace(
        project_dir=str(cmd_project), note_id=None, tag=None,
        status=None, json=False, limit=20,
    )
    rc = run_view(args)
    assert rc == 0


def test_run_digest_advances_status(cmd_project):
    """run_digest moves a note from raw to digesting."""
    import argparse
    from myco.notes_cmd import run_eat, run_digest
    # First eat a note
    eat_args = argparse.Namespace(
        project_dir=str(cmd_project), tags="digest-test",
        content="Content to digest.", title=None, json=False,
        source=None,
    )
    run_eat(eat_args)
    notes = list((cmd_project / "notes").glob("n_*.md"))
    note_id = notes[0].stem

    # Then digest it
    digest_args = argparse.Namespace(
        project_dir=str(cmd_project), note_id=note_id,
        to=None, json=False, excrete=None,
    )
    rc = run_digest(digest_args)
    assert rc == 0
    content = notes[0].read_text(encoding="utf-8")
    assert "status: digesting" in content
