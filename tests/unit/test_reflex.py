"""Tests for myco.reflex — inter-tool reflex chains (Wave 57 Wave 2)."""

import pytest

from myco.bootstrap import first_contact_seed
from myco.notes import write_note
from myco.reflex import (
    apply_supersede,
    detect_supersede_candidates,
    hunger_to_scent,
    verify_to_scent,
)


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    proj = tmp_path / "ref"
    proj.mkdir()
    monkeypatch.delenv("MYCO_AGENT", raising=False)
    first_contact_seed(proj, silent=True)
    assert (proj / "_canon.yaml").exists()
    return proj


class TestSupersedeDetect:
    def test_no_candidates_when_empty(self, seeded):
        # Create a single note; no older note to supersede.
        p = write_note(seeded, "Fresh content about Rust borrow checker.",
                       tags=["rust"], title="Rust borrow checker notes")
        r = detect_supersede_candidates(seeded, p.stem)
        assert r["supersedes"] == []

    def test_similar_title_detected(self, seeded):
        # Old note
        old = write_note(
            seeded,
            "Notes on the Python asyncio event loop and its quirks.",
            tags=["python"],
            title="Asyncio event loop primer",
        )
        new = write_note(
            seeded,
            "Notes on the Python asyncio event loop and its quirks revisited.",
            tags=["python"],
            title="Asyncio event loop primer",
        )
        r = detect_supersede_candidates(seeded, new.stem)
        ids = [c["note_id"] for c in r["supersedes"]]
        # At least one candidate, and it includes the older note
        assert old.stem in ids


class TestApplySupersede:
    def test_round_trip(self, seeded):
        old = write_note(seeded, "Original.", title="X")
        new = write_note(seeded, "Refreshed.", title="X v2")
        r = apply_supersede(seeded, new.stem, [old.stem])
        assert old.stem in r["applied"]
        # Check frontmatter updated
        from myco.notes import read_note
        meta_old, _ = read_note(old)
        meta_new, _ = read_note(new)
        assert meta_old.get("superseded_by") == new.stem
        assert new.stem not in (meta_new.get("supersedes") or [])  # self NOT in list
        assert old.stem in (meta_new.get("supersedes") or [])


class TestVerifyToScent:
    def test_still_true_no_reflex(self, seeded):
        p = write_note(seeded, "claim about latest numpy", tags=["numpy"])
        r = verify_to_scent(seeded, p.stem, "ok")
        assert r["triggered"] is False

    def test_contradicted_triggers_scent(self, seeded):
        p = write_note(seeded, "claim about langchain", tags=["langchain"])
        r = verify_to_scent(seeded, p.stem, "contradicted")
        assert r["triggered"] is True
        assert r["topic"] == "langchain"
        assert "myco_scent" in r["suggested_call"]


class TestHungerToScent:
    def test_dict_input_passes(self, seeded):
        hr = {"actions": [
            {"verb": "scent", "args": {"topic": "rag"}, "reason": "gap"},
            {"verb": "digest", "args": {"note_id": "abc"}, "reason": "raw"},
        ]}
        r = hunger_to_scent(seeded, hr)
        topics = [s["topic"] for s in r["scents"]]
        assert "rag" in topics
        # digest action shouldn't create a scent
        assert "abc" not in topics

    def test_empty_actions(self, seeded):
        r = hunger_to_scent(seeded, {"actions": []})
        assert r["scents"] == []
