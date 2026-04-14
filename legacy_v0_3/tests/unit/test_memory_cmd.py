"""Unit tests for myco.memory_cmd — CLI dispatch for session verb."""

import argparse
from pathlib import Path

import pytest


@pytest.fixture
def session_cmd_project(tmp_path):
    (tmp_path / "_canon.yaml").write_text(
        "system:\n  contract_version: 'v0.43.0'\n  entry_point: MYCO.md\n"
        "  sessions:\n    enabled: true\n    db_path: '.myco_state/sessions.db'\n"
        "    claude_projects_dir: null\n    max_age_days: 90\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / ".myco_state").mkdir()
    # Point to empty dir so no real sessions found
    empty = tmp_path / "empty_sessions"
    empty.mkdir()
    return tmp_path


