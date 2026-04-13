"""Unit tests for myco.diagnose_cmd — deployment health check.

Tests the 5 automation/deployment completeness checks added to verify:
  5a. Scheduled task (myco-metabolic-cycle)
  5b. Settings permissions (mcp__myco__* in allow list)
  5c. Cowork skills (myco-boot)
  5d. CLAUDE.md / MYCO.md boot ritual (myco_hunger)
  5e. docs/primordia/ craft directory
"""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_verify_args(project_dir: str) -> argparse.Namespace:
    return argparse.Namespace(project_dir=project_dir)


# ---------------------------------------------------------------------------
# Helpers: scaffold a minimal project that passes the original 8 checks as
# far as substrate structure goes (to avoid noise in failure output).
# ---------------------------------------------------------------------------

def _scaffold_project(root: Path) -> None:
    """Create the bare minimum for the first 3 substrate structure checks."""
    (root / "_canon.yaml").write_text(
        "system:\n  contract_version: 'v0.43.0'\n", encoding="utf-8"
    )
    (root / "notes").mkdir(exist_ok=True)
    (root / "MYCO.md").write_text("# Test\n", encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)


# ===========================================================================
# 5a. Scheduled task
# ===========================================================================

class TestScheduledTask:
    def test_pass_when_skill_exists(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        fake_home_claude = tmp_path / "fake_home" / ".claude"
        sched = fake_home_claude / "scheduled-tasks" / "myco-metabolic-cycle"
        sched.mkdir(parents=True)
        (sched / "SKILL.md").write_text("# metabolic cycle\n", encoding="utf-8")

        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home_claude
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Scheduled task: myco-metabolic-cycle" in out
        assert "Scheduled task missing" not in out

    def test_fail_when_skill_missing(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        fake_home_claude = tmp_path / "fake_home" / ".claude"
        fake_home_claude.mkdir(parents=True)

        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home_claude
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Scheduled task missing" in out


# ===========================================================================
# 5b. Settings permissions
# ===========================================================================

class TestSettingsPermissions:
    def test_pass_when_allow_list_has_myco(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        settings = {
            "permissions": {
                "allow": ["mcp__myco__*"]
            }
        }
        (claude_dir / "settings.json").write_text(
            json.dumps(settings), encoding="utf-8"
        )
        # Ensure user-level doesn't interfere
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "mcp__myco__* in allow list" in out

    def test_pass_with_settings_local(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        settings = {
            "permissions": {
                "allow": ["mcp__myco__myco_hunger", "mcp__myco__myco_eat"]
            }
        }
        (claude_dir / "settings.local.json").write_text(
            json.dumps(settings), encoding="utf-8"
        )
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "mcp__myco__* in allow list" in out

    def test_fail_when_no_myco_in_allow(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        settings = {
            "permissions": {
                "allow": ["Bash(ls)"]
            }
        }
        (claude_dir / "settings.json").write_text(
            json.dumps(settings), encoding="utf-8"
        )
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "not in allow list" in out

    def test_fail_when_no_settings(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "not in allow list" in out


# ===========================================================================
# 5c. Cowork skills
# ===========================================================================

class TestCoworkSkills:
    def test_pass_when_boot_skill_exists(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / "myco-boot"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# boot\n", encoding="utf-8")

        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Cowork skill: myco-boot" in out
        assert "Cowork skill missing" not in out

    def test_fail_when_boot_skill_missing(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Cowork skill missing" in out


# ===========================================================================
# 5d. Boot ritual (myco_hunger in entry point)
# ===========================================================================

class TestBootRitual:
    def test_pass_when_entry_has_myco_hunger(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        (tmp_path / "MYCO.md").write_text(
            "# Project\n> Boot: Call `myco_hunger(execute=true)` first.\n",
            encoding="utf-8",
        )
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Boot ritual: MYCO.md contains myco_hunger" in out

    def test_fail_when_entry_missing_myco_hunger(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        # MYCO.md exists but has no myco_hunger
        (tmp_path / "MYCO.md").write_text("# Project\nNo boot info.\n", encoding="utf-8")
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "missing myco_hunger" in out

    def test_checks_claude_md_too(self, tmp_path, monkeypatch, capsys):
        """CLAUDE.md is checked before MYCO.md per candidate order."""
        _scaffold_project(tmp_path)
        # Remove MYCO.md, add CLAUDE.md with boot ritual
        (tmp_path / "MYCO.md").unlink()
        (tmp_path / "CLAUDE.md").write_text(
            "# X\n> `myco_hunger(execute=true)` as FIRST action.\n",
            encoding="utf-8",
        )
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Boot ritual: CLAUDE.md contains myco_hunger" in out


# ===========================================================================
# 5e. docs/primordia/ craft directory
# ===========================================================================

class TestCraftDirectory:
    def test_pass_when_primordia_exists(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        primordia = tmp_path / "docs" / "primordia"
        primordia.mkdir(parents=True, exist_ok=True)
        (primordia / "foo_craft_2026-04-10.md").write_text("# craft\n", encoding="utf-8")

        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Craft directory: docs/primordia/ (1 craft files)" in out

    def test_fail_when_primordia_missing(self, tmp_path, monkeypatch, capsys):
        _scaffold_project(tmp_path)
        # Remove docs/primordia if scaffold created it
        primordia = tmp_path / "docs" / "primordia"
        if primordia.exists():
            primordia.rmdir()

        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "Craft directory missing" in out


# ===========================================================================
# Total check count
# ===========================================================================

class TestTotalCount:
    def test_total_is_14(self, tmp_path, monkeypatch, capsys):
        """Verify total checks is now 13 (8 original + 5 new)."""
        _scaffold_project(tmp_path)
        fake_home = tmp_path / "fake_home" / ".claude"
        fake_home.mkdir(parents=True)
        monkeypatch.setattr(
            "myco.diagnose_cmd._user_claude_dir", lambda: fake_home
        )

        from myco.diagnose_cmd import run_verify
        run_verify(_make_verify_args(str(tmp_path)))
        out = capsys.readouterr().out
        # The summary line shows "X/14 passed"
        assert "/14 passed" in out or "/14 CHECKS PASSED" in out
