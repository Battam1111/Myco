"""Unit tests for myco.project — centralized project root resolution (Wave A1)."""

import os
from pathlib import Path

import pytest


def test_find_project_root_walks_up(tmp_path):
    """find_project_root walks up from subdir to find _canon.yaml."""
    from myco.project import find_project_root

    (tmp_path / "_canon.yaml").write_text("system:\n  contract_version: 'v0.43.0'\n")
    subdir = tmp_path / "src" / "myco"
    subdir.mkdir(parents=True)

    result = find_project_root(subdir)
    assert result == tmp_path


def test_find_project_root_strict_raises(tmp_path):
    """strict=True raises MycoProjectNotFound when no _canon.yaml."""
    from myco.project import MycoProjectNotFound, find_project_root

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(MycoProjectNotFound):
        find_project_root(empty_dir, strict=True)


def test_find_project_root_non_strict_returns_hint(tmp_path):
    """strict=False returns best-guess path when no _canon.yaml."""
    from myco.project import find_project_root

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = find_project_root(empty_dir, strict=False)
    assert result == empty_dir


def test_find_project_root_env_escape_hatch(tmp_path, monkeypatch):
    """MYCO_ALLOW_NO_PROJECT=1 overrides strict mode."""
    from myco.project import find_project_root

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    monkeypatch.setenv("MYCO_ALLOW_NO_PROJECT", "1")
    result = find_project_root(empty_dir, strict=True)
    assert result == empty_dir


def test_find_project_root_none_hint_uses_cwd():
    """hint=None resolves from cwd."""
    from myco.project import find_project_root

    # This test runs from the Myco project root which has _canon.yaml
    result = find_project_root(None)
    assert (result / "_canon.yaml").exists()
