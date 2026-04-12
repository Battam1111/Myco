"""Unit tests for myco.sessions — Wave 52 session memory."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def session_project(tmp_path):
    """Create a minimal Myco project with mock session data."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.40.0'\n"
        "  entry_point: MYCO.md\n"
        "  sessions:\n"
        "    enabled: true\n"
        "    db_path: '.myco_state/sessions.db'\n"
        "    claude_projects_dir: null\n"
        "    max_age_days: 90\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / ".myco_state").mkdir()

    # Create mock session directory structure
    session_dir = tmp_path / ".claude" / "projects" / "test-project"
    session_dir.mkdir(parents=True)

    # Write a mock .jsonl session file
    session_file = session_dir / "test-session.jsonl"
    turns = [
        {"role": "user", "content": "How does compression work in Myco?", "timestamp": "2026-04-12T10:00:00Z"},
        {"role": "assistant", "content": "Compression in Myco uses the myco compress command to synthesize multiple raw notes into a single extracted note.", "timestamp": "2026-04-12T10:00:05Z"},
        {"role": "user", "content": "What about the forage system?", "timestamp": "2026-04-12T10:01:00Z"},
        {"role": "assistant", "content": "The forage substrate handles external reference material. Use myco forage add to acquire items.", "timestamp": "2026-04-12T10:01:05Z"},
    ]
    with open(session_file, "w") as f:
        for turn in turns:
            f.write(json.dumps(turn) + "\n")

    return tmp_path


def test_index_empty(tmp_path):
    """No session files found produces empty stats."""
    from myco.sessions import index_sessions

    # Point to a non-existent dir so no real sessions are found
    empty_sessions = tmp_path / "empty_sessions"
    empty_sessions.mkdir()
    (tmp_path / "_canon.yaml").write_text(
        f"system:\n  sessions:\n    enabled: true\n    db_path: '.myco_state/sessions.db'\n"
        f"    claude_projects_dir: '{str(empty_sessions)}'\n"
    )
    (tmp_path / ".myco_state").mkdir()

    stats = index_sessions(tmp_path)
    assert stats["indexed_files"] == 0
    assert stats["indexed_turns"] == 0


def test_index_and_search_roundtrip(session_project):
    """Index mock sessions, search for known term, verify match."""
    from myco.sessions import index_sessions, search_sessions

    db_path = session_project / ".myco_state" / "sessions.db"
    stats = index_sessions(session_project, db_path=db_path)
    assert stats["indexed_files"] >= 1
    assert stats["indexed_turns"] >= 2

    results = search_sessions(session_project, "compression", db_path=db_path)
    assert len(results) >= 1
    assert any("compress" in r["snippet"].lower() for r in results)


def test_prune_removes_old(session_project):
    """Index then prune with max_age_days=0 removes all."""
    from myco.sessions import index_sessions, prune_sessions

    db_path = session_project / ".myco_state" / "sessions.db"
    index_sessions(session_project, db_path=db_path)

    stats = prune_sessions(session_project, max_age_days=0, db_path=db_path)
    assert stats["removed_turns"] > 0
    assert stats["remaining_turns"] == 0


def test_search_no_results(session_project):
    """Search for absent term returns empty."""
    from myco.sessions import index_sessions, search_sessions

    db_path = session_project / ".myco_state" / "sessions.db"
    index_sessions(session_project, db_path=db_path)

    results = search_sessions(session_project, "xyznonexistent123", db_path=db_path)
    assert results == []
