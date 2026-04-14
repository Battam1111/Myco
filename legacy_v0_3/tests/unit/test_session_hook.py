"""Tests for myco.session_hook — zero-touch close-out ritual (Wave 56)."""

from pathlib import Path

import pytest

from myco.inoculate import first_contact_seed
from myco.session_hook import run_session_end, _refresh_boot_brief


@pytest.fixture
def seeded_project(tmp_path, monkeypatch):
    """A freshly-seeded Myco project via first_contact_seed."""
    proj = tmp_path / "seeded"
    proj.mkdir()
    monkeypatch.delenv("MYCO_AGENT", raising=False)
    first_contact_seed(proj, silent=True)
    assert (proj / "_canon.yaml").exists(), "bootstrap must succeed"
    return proj


class TestRunSessionEnd:
    def test_not_myco_project(self, tmp_path):
        result = run_session_end(tmp_path)
        assert result["ok"] is False
        assert "not a Myco project" in result["errors"][0]

    def test_refresh_brief_only(self, seeded_project):
        result = run_session_end(seeded_project, summary=None, prune=False)
        assert result["ok"] is True
        assert result["brief_refreshed"] is True
        assert (seeded_project / ".myco_state" / "boot_brief.md").exists()

    def test_eat_summary(self, seeded_project):
        result = run_session_end(
            seeded_project,
            summary="Completed Wave 1 of zero-touch automation.",
            prune=False,
            refresh_brief=False,
        )
        assert result["ok"] is True
        assert result["ate"] is not None
        # The eaten note should exist
        note_path = seeded_project / result["ate"]
        assert note_path.exists()
        assert "Wave 1" in note_path.read_text(encoding="utf-8")

    def test_prune_zero_candidates(self, seeded_project):
        # Fresh project: no notes → prune=0
        result = run_session_end(seeded_project, prune=True, refresh_brief=False)
        assert result["ok"] is True
        assert result["pruned"] == 0

    def test_all_steps(self, seeded_project):
        result = run_session_end(
            seeded_project,
            summary="Session summary.",
            prune=True,
            refresh_brief=True,
        )
        assert result["ok"] is True
        assert result["ate"] is not None
        assert result["brief_refreshed"] is True


class TestRefreshBootBrief:
    def test_creates_brief(self, seeded_project):
        _refresh_boot_brief(seeded_project)
        brief = seeded_project / ".myco_state" / "boot_brief.md"
        assert brief.exists()
        content = brief.read_text(encoding="utf-8")
        assert "Boot Brief" in content
        assert "Next-action hint" in content
