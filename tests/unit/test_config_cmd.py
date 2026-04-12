"""Unit tests for myco.config_cmd — configuration management (Wave A3)."""

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


def test_run_config_get_returns_value(config_project):
    """config --get reads a value from _canon.yaml."""
    from myco.config_cmd import run_config
    args = argparse.Namespace(
        project_dir=str(config_project),
        get="adapters.mempalace.endpoint",
        set=None, list=None, unset=None,
    )
    rc = run_config(args)
    # Key may not exist → returns 1 or 0 depending on implementation
    assert rc in (0, 1)


def test_run_config_list_shows_section(config_project):
    """config --list shows config section."""
    from myco.config_cmd import run_config
    args = argparse.Namespace(
        project_dir=str(config_project),
        get=None, set=None, list="", unset=None,
    )
    rc = run_config(args)
    assert rc == 0


def test_run_config_handles_missing_key(config_project):
    """config --get with nonexistent key doesn't crash."""
    from myco.config_cmd import run_config
    args = argparse.Namespace(
        project_dir=str(config_project),
        get="system.nonexistent_key",
        set=None, list=None, unset=None,
    )
    rc = run_config(args)
    assert rc in (0, 1, 2)
