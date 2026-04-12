"""Unit tests for myco.migrate — project migration (Wave A3)."""

import argparse
from pathlib import Path
import pytest


@pytest.fixture
def migrate_project(tmp_path):
    """Create a minimal pre-migration project."""
    (tmp_path / "MYCO.md").write_text("# Old Myco Project\n")
    (tmp_path / "log.md").write_text("# Log\n")
    return tmp_path


def _migrate_args(project_dir):
    return argparse.Namespace(
        project_dir=str(project_dir),
        project_name="MigrateTest",
        github_user="testuser",
        entry_point="MYCO.md",
        level=1,
        dry_run=False,
    )


def test_run_migrate_creates_canon(migrate_project):
    """migrate creates _canon.yaml if missing."""
    from myco.migrate import run_migrate
    rc = run_migrate(_migrate_args(migrate_project))
    assert rc == 0
    assert (migrate_project / "_canon.yaml").exists()


def test_run_migrate_preserves_existing_entry(migrate_project):
    """migrate doesn't overwrite existing MYCO.md."""
    from myco.migrate import run_migrate
    run_migrate(_migrate_args(migrate_project))
    assert (migrate_project / "MYCO.md").exists()


def test_run_migrate_idempotent(migrate_project):
    """Running migrate twice doesn't crash."""
    from myco.migrate import run_migrate
    rc1 = run_migrate(_migrate_args(migrate_project))
    rc2 = run_migrate(_migrate_args(migrate_project))
    assert rc1 == 0
    assert rc2 == 0
