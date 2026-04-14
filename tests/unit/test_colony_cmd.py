"""Unit tests for myco.colony_cmd — CLI dispatch for cohort verb."""

import argparse
from pathlib import Path

import pytest


@pytest.fixture
def cohort_cmd_project(tmp_path):
    (tmp_path / "_canon.yaml").write_text(
        "system:\n  contract_version: 'v0.43.0'\n  entry_point: MYCO.md\n"
        "  notes_schema:\n    dir: notes\n    compression:\n"
        "      ripe_threshold: 3\n      ripe_age_days: 1\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    return tmp_path


