"""Unit tests for myco.mycelium_cmd — CLI dispatch for graph verb."""

import argparse
from pathlib import Path

import pytest


@pytest.fixture
def graph_cmd_project(tmp_path):
    (tmp_path / "_canon.yaml").write_text(
        "system:\n  contract_version: 'v0.43.0'\n  entry_point: MYCO.md\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\nSee [doc](docs/a.md).\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n")
    (tmp_path / "notes").mkdir()
    (tmp_path / "log.md").write_text("# Log\n")
    return tmp_path


