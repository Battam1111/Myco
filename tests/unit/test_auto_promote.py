"""Tests for colony.auto_promote_cross_project (Wave 58 Wave 3)."""

import pytest

from myco.inoculate import first_contact_seed
from myco.colony import auto_promote_cross_project
from myco.notes import write_note


@pytest.fixture
def global_myco(tmp_path, monkeypatch):
    """Build a fake `~/Myco` root with two projects sharing a tag."""
    monkeypatch.delenv("MYCO_AGENT", raising=False)
    gm = tmp_path / "global_myco"
    gm.mkdir()

    # project A
    a = gm / "proj_a"
    a.mkdir()
    first_contact_seed(a, silent=True)
    write_note(a, "A stuff about rag", tags=["rag"], title="A rag")
    write_note(a, "more A rag content", tags=["rag"], title="A rag 2")

    # project B
    b = gm / "proj_b"
    b.mkdir()
    first_contact_seed(b, silent=True)
    write_note(b, "B stuff about rag", tags=["rag"], title="B rag")

    return gm, a, b


class TestAutoPromote:
    def test_promote_writes_page(self, global_myco):
        gm, a, _ = global_myco
        out = auto_promote_cross_project(a, global_myco_root=gm,
                                         min_cluster_size=2, min_total_notes=2)
        slugs = [p["slug"] for p in out["promoted"]]
        assert "rag" in slugs
        target = a / "wiki" / "cross_project" / "rag.md"
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert "proj_a" in text
        assert "proj_b" in text

    def test_dry_run_writes_nothing(self, global_myco):
        gm, a, _ = global_myco
        out = auto_promote_cross_project(a, global_myco_root=gm,
                                         min_cluster_size=2, min_total_notes=2,
                                         dry_run=True)
        slugs = [p["slug"] for p in out["promoted"]]
        assert "rag" in slugs
        assert not (a / "wiki" / "cross_project" / "rag.md").exists()

    def test_min_total_notes_filter(self, global_myco):
        gm, a, _ = global_myco
        out = auto_promote_cross_project(a, global_myco_root=gm,
                                         min_cluster_size=2,
                                         min_total_notes=100)
        # Nothing should promote since total < 100
        assert out["promoted"] == []

    def test_idempotent_rewrite(self, global_myco):
        gm, a, _ = global_myco
        out1 = auto_promote_cross_project(a, global_myco_root=gm,
                                          min_cluster_size=2, min_total_notes=2)
        out2 = auto_promote_cross_project(a, global_myco_root=gm,
                                          min_cluster_size=2, min_total_notes=2)
        # Second run should see no change (fingerprint match)
        skipped = [s["slug"] for s in out2["skipped"]]
        assert "rag" in skipped or out2["promoted"] == []
