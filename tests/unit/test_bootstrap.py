"""Tests for myco.bootstrap — first-contact auto-seed (Wave 56)."""

from pathlib import Path

import pytest

from myco.bootstrap import (
    _infer_project_name,
    _infer_entry_point,
    is_bootstrapped,
    first_contact_seed,
)


class TestInferProjectName:
    def test_plain_name(self, tmp_path):
        (tmp_path / "my-project").mkdir()
        assert _infer_project_name(tmp_path / "my-project") == "my-project"

    def test_sanitize_special_chars(self, tmp_path):
        weird = tmp_path / "weird name with spaces!@#"
        weird.mkdir()
        name = _infer_project_name(weird)
        assert " " not in name
        assert "!" not in name
        assert name  # non-empty

    def test_fallback_for_empty_name(self):
        # Path("") .name is ""
        assert _infer_project_name(Path("")) == "myco_project"


class TestInferEntryPoint:
    def test_default_is_claude_md(self, monkeypatch):
        monkeypatch.delenv("MYCO_AGENT", raising=False)
        assert _infer_entry_point() == "CLAUDE.md"

    def test_cursor(self, monkeypatch):
        monkeypatch.setenv("MYCO_AGENT", "cursor")
        assert _infer_entry_point() == "MYCO.md"

    def test_gpt(self, monkeypatch):
        monkeypatch.setenv("MYCO_AGENT", "gpt")
        assert _infer_entry_point() == "GPT.md"


class TestIsBootstrapped:
    def test_false_for_empty_dir(self, tmp_path):
        assert is_bootstrapped(tmp_path) is False

    def test_true_when_canon_exists(self, tmp_path):
        (tmp_path / "_canon.yaml").write_text("version: 1\n")
        assert is_bootstrapped(tmp_path) is True

    def test_true_when_sentinel_exists(self, tmp_path):
        (tmp_path / ".myco_state").mkdir()
        (tmp_path / ".myco_state" / "bootstrapped").write_text("x")
        assert is_bootstrapped(tmp_path) is True


class TestFirstContactSeed:
    def test_creates_canon_yaml(self, tmp_path, monkeypatch):
        project = tmp_path / "my-new-project"
        project.mkdir()
        # Avoid unintended agent selection
        monkeypatch.delenv("MYCO_AGENT", raising=False)
        result = first_contact_seed(project, silent=True)
        assert result is not None
        assert (project / "_canon.yaml").exists()
        assert (project / ".myco_state" / "bootstrapped").exists()

    def test_skip_if_already_bootstrapped(self, tmp_path):
        project = tmp_path / "already-set"
        project.mkdir()
        (project / "_canon.yaml").write_text("version: 1\n")
        result = first_contact_seed(project, silent=True)
        assert result is None

    def test_sentinel_prevents_reseed(self, tmp_path):
        project = tmp_path / "sentinel-test"
        project.mkdir()
        (project / ".myco_state").mkdir()
        (project / ".myco_state" / "bootstrapped").write_text("x")
        result = first_contact_seed(project, silent=True)
        assert result is None

    def test_rejects_home_dir(self, monkeypatch):
        # Should not seed the user's home directory
        home = Path.home()
        # Only run if home doesn't already have _canon.yaml
        if (home / "_canon.yaml").exists():
            pytest.skip("home already has _canon.yaml")
        result = first_contact_seed(home, silent=True)
        assert result is None
