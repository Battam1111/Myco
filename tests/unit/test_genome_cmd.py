"""Unit tests for myco.genome_cmd — configuration management (Wave A3)."""

import argparse
from pathlib import Path
import pytest


@pytest.fixture
def config_project(tmp_path):
    (tmp_path / "_canon.yaml").write_text(
        "system:\n  contract_version: 'v0.44.0'\n  entry_point: MYCO.md\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    return tmp_path


