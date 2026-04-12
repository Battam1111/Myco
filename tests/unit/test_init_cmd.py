"""Unit tests for myco.init_cmd — project initialization (Wave A3)."""

from pathlib import Path
import pytest


def test_init_level0_creates_entry_and_log(tmp_path):
    """init_level_0 creates entry_point and log.md."""
    from myco.init_cmd import init_level_0
    replacements = {
        "PROJECT_NAME": "TestProject",
        "GITHUB_USER": "testuser",
        "CURRENT_PHASE": "Phase 0",
        "DATE": "2026-04-12",
        "ENTRY_POINT": "MYCO.md",
    }
    init_level_0(tmp_path, replacements, "MYCO.md")
    assert (tmp_path / "MYCO.md").exists()
    assert (tmp_path / "log.md").exists()


def test_init_level1_creates_canon_and_dirs(tmp_path):
    """init_level_1 creates _canon.yaml, notes/, wiki/."""
    from myco.init_cmd import init_level_0, init_level_1
    replacements = {
        "PROJECT_NAME": "TestProject",
        "GITHUB_USER": "testuser",
        "CURRENT_PHASE": "Phase 0",
        "DATE": "2026-04-12",
        "ENTRY_POINT": "MYCO.md",
    }
    init_level_0(tmp_path, replacements, "MYCO.md")
    init_level_1(tmp_path, replacements, "MYCO.md")
    assert (tmp_path / "_canon.yaml").exists()
    assert (tmp_path / "notes").is_dir()


def test_run_init_returns_zero(tmp_path):
    """run_init succeeds on fresh directory."""
    import argparse
    from myco.init_cmd import run_init
    target = tmp_path / "newproject"
    target.mkdir()
    args = argparse.Namespace(
        dir=str(target),
        name="Test",
        level=0,
        github_user="testuser",
        entry_point="MYCO.md",
    )
    rc = run_init(args)
    assert rc == 0
