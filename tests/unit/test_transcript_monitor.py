"""Tests for myco.transcript_monitor (Wave 58 Wave 3 — passive ingest)."""

import pytest

from myco.bootstrap import first_contact_seed
from myco.transcript_monitor import (
    _classify_chunk,
    ingest_transcript,
    is_disabled,
)


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    proj = tmp_path / "tm"
    proj.mkdir()
    monkeypatch.delenv("MYCO_AGENT", raising=False)
    first_contact_seed(proj, silent=True)
    assert (proj / "_canon.yaml").exists()
    return proj


class TestClassify:
    def test_short_chunk_returns_none(self):
        assert _classify_chunk("hi") is None

    def test_decision_chunk_classified(self):
        c = _classify_chunk(
            "I decided we will use Postgres as the primary database going forward."
        )
        assert c is not None
        assert c["kind"] == "decision"
        assert "decision" in c["tags"]

    def test_preference_chunk_classified(self):
        c = _classify_chunk(
            "From now on, I prefer that all commits go through pre-commit hooks."
        )
        assert c is not None
        assert c["kind"] == "preference"

    def test_root_cause_classified(self):
        c = _classify_chunk(
            "Turns out the bug was caused by a missing newline in the CSV writer."
        )
        assert c is not None
        assert c["kind"] == "root-cause"

    def test_noise_returns_none(self):
        assert _classify_chunk("haha yeah that's funny") is None


class TestIngestTranscript:
    def test_not_myco_project(self, tmp_path):
        r = ingest_transcript(tmp_path, [{"role": "user", "text": "hi there"}])
        assert r["errors"] and "not a Myco" in r["errors"][0]

    def test_disabled_sentinel(self, seeded):
        (seeded / ".myco_state").mkdir(exist_ok=True)
        (seeded / ".myco_state" / "transcript_monitor.off").write_text("1")
        assert is_disabled(seeded)
        r = ingest_transcript(seeded, [
            {"role": "user", "text": "I decided to use Postgres for everything."}
        ])
        assert r["disabled"] is True
        assert r["ate"] == 0

    def test_ingests_decision_chunk(self, seeded):
        r = ingest_transcript(seeded, [
            {"role": "user",
             "text": "I decided we will use Postgres for every new service."}
        ])
        assert r["ate"] == 1
        assert r["classified"] == 1
        assert len(r["new_note_ids"]) == 1

    def test_dedupe_second_run(self, seeded):
        chunks = [{"role": "user",
                   "text": "I decided we will use Postgres for every new service."}]
        r1 = ingest_transcript(seeded, chunks)
        r2 = ingest_transcript(seeded, chunks)
        assert r1["ate"] == 1
        assert r2["ate"] == 0
        assert r2["skipped_duplicate"] == 1

    def test_dry_run_writes_nothing(self, seeded):
        r = ingest_transcript(seeded, [
            {"role": "user",
             "text": "I decided we will use ClickHouse for analytics workloads."}
        ], dry_run=True)
        assert r["ate"] == 1
        # No actual note file created — check notes/ count is zero
        notes_dir = seeded / "notes"
        if notes_dir.exists():
            assert len(list(notes_dir.glob("n_*.md"))) == 0

    def test_max_eat_cap(self, seeded):
        chunks = [
            {"role": "user", "text": f"I decided point {i}: we use variant {i}."}
            for i in range(10)
        ]
        r = ingest_transcript(seeded, chunks, max_eat=3)
        assert r["ate"] == 3
