"""Unit tests for myco.seed_cmd — project initialization (Wave A3)."""

from pathlib import Path
import pytest


def test_init_level0_creates_entry_and_log(tmp_path):
    """init_level_0 creates entry_point and log.md."""
    from myco.seed_cmd import init_level_0
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
    from myco.seed_cmd import init_level_0, init_level_1
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
    from myco.seed_cmd import run_init
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


# ---------------------------------------------------------------------------
# Pre-commit hook generation
# ---------------------------------------------------------------------------

class TestPreCommitHookGeneration:
    """Tests for _generate_pre_commit_hook."""

    def test_pre_commit_hook_generated(self, tmp_path):
        """After init with .git/ present, pre-commit hook exists and contains 'myco'."""
        from myco.seed_cmd import _generate_pre_commit_hook

        # Simulate a git repo
        (tmp_path / ".git").mkdir()

        result = _generate_pre_commit_hook(tmp_path)

        assert result is True
        hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()
        content = hook_path.read_text(encoding="utf-8")
        assert "myco" in content
        assert "python -m myco lint --quick" in content

    def test_no_hook_without_git(self, tmp_path):
        """No .git/ directory means no hook is generated."""
        from myco.seed_cmd import _generate_pre_commit_hook

        result = _generate_pre_commit_hook(tmp_path)

        assert result is False
        assert not (tmp_path / ".git" / "hooks" / "pre-commit").exists()

    def test_existing_myco_hook_not_overwritten(self, tmp_path):
        """Existing hook that already has 'myco' is left untouched."""
        from myco.seed_cmd import _generate_pre_commit_hook

        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
        original = "#!/bin/bash\n# myco custom hook\necho 'already here'\n"
        hook_path.write_text(original, encoding="utf-8")

        result = _generate_pre_commit_hook(tmp_path)

        assert result is True
        assert hook_path.read_text(encoding="utf-8") == original

    def test_existing_non_myco_hook_appended(self, tmp_path):
        """Existing non-Myco hook gets Myco lint appended."""
        from myco.seed_cmd import _generate_pre_commit_hook

        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
        original = "#!/bin/bash\necho 'other tool'\n"
        hook_path.write_text(original, encoding="utf-8")

        result = _generate_pre_commit_hook(tmp_path)

        assert result is True
        content = hook_path.read_text(encoding="utf-8")
        # Original content preserved
        assert "other tool" in content
        # Myco section appended
        assert "python -m myco lint --quick" in content

    def test_init_level0_generates_hook_when_git_exists(self, tmp_path):
        """init_level_0 generates the pre-commit hook when .git/ is present."""
        from myco.seed_cmd import init_level_0

        # Simulate git repo
        (tmp_path / ".git").mkdir()

        replacements = {
            "PROJECT_NAME": "TestProject",
            "GITHUB_USER": "testuser",
            "CURRENT_PHASE": "Phase 0",
            "DATE": "2026-04-12",
            "ENTRY_POINT": "MYCO.md",
        }
        init_level_0(tmp_path, replacements, "MYCO.md")

        hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()
        assert "myco" in hook_path.read_text(encoding="utf-8")
