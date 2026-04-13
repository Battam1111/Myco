"""Unit tests for myco.colony — Wave 48 semantic cohort intelligence."""

from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture
def cohort_project(tmp_path):
    """Create a minimal Myco project with notes for cohort testing."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.37.0'\n"
        "  entry_point: MYCO.md\n"
        "  notes_schema:\n"
        "    dir: notes\n"
        "    compression:\n"
        "      ripe_threshold: 3\n"
        "      ripe_age_days: 1\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    return tmp_path


def _write_note(notes_dir, note_id, status, tags, created=None):
    """Helper: write a minimal note file."""
    if created is None:
        created = "2026-04-01T00:00:00"
    content = (
        f"---\n"
        f"id: {note_id}\n"
        f"status: {status}\n"
        f"source: eat\n"
        f"tags: [{', '.join(tags)}]\n"
        f"created: {created}\n"
        f"last_touched: {created}\n"
        f"digest_count: 0\n"
        f"promote_candidate: false\n"
        f"excrete_reason: null\n"
        f"---\n\n"
        f"Test note {note_id}.\n"
    )
    (notes_dir / f"{note_id}.md").write_text(content)


def test_tag_cooccurrence_basic(cohort_project):
    """3 notes with overlapping tags produce correct co-occurrence counts."""
    from myco.colony import tag_cooccurrence

    notes = cohort_project / "notes"
    _write_note(notes, "n_20260401T000001_0001", "raw", ["alpha", "beta"])
    _write_note(notes, "n_20260401T000002_0002", "raw", ["alpha", "gamma"])
    _write_note(notes, "n_20260401T000003_0003", "raw", ["beta", "gamma"])

    pairs = tag_cooccurrence(cohort_project)
    pair_dict = {(a, b): c for a, b, c in pairs}

    assert pair_dict[("alpha", "beta")] == 1
    assert pair_dict[("alpha", "gamma")] == 1
    assert pair_dict[("beta", "gamma")] == 1


def test_cooccurrence_empty(cohort_project):
    """No notes produces empty co-occurrence."""
    from myco.colony import tag_cooccurrence

    pairs = tag_cooccurrence(cohort_project)
    assert pairs == []


def test_gap_detection(cohort_project):
    """Raw-only tag detected as gap; tag with integrated notes is not."""
    from myco.colony import gap_detection

    notes = cohort_project / "notes"
    # "untouched" tag — only raw notes
    _write_note(notes, "n_20260401T000001_0001", "raw", ["untouched"])
    _write_note(notes, "n_20260401T000002_0002", "raw", ["untouched"])
    # "processed" tag — has integrated
    _write_note(notes, "n_20260401T000003_0003", "integrated", ["processed"])

    gaps = gap_detection(cohort_project)
    gap_tags = [g["tag"] for g in gaps]

    assert "untouched" in gap_tags
    assert "processed" not in gap_tags


def test_compression_cohort_suggest(cohort_project):
    """Ripe tag cohort produces a compression suggestion."""
    from myco.colony import compression_cohort_suggest

    notes = cohort_project / "notes"
    # 4 raw notes aged > 1 day with same tag (threshold=3, age=1 in fixture)
    for i in range(4):
        _write_note(notes, f"n_20260401T00000{i}_000{i}",
                    "raw", ["ripe-topic"], created="2026-03-01T00:00:00")

    now = datetime(2026, 4, 12, tzinfo=timezone.utc)
    suggestions = compression_cohort_suggest(cohort_project, now=now)

    assert len(suggestions) >= 1
    assert suggestions[0]["tag"] == "ripe-topic"
    assert suggestions[0]["note_count"] == 4


def test_gap_detection_no_gaps(cohort_project):
    """All tags have synthesized output — no gaps."""
    from myco.colony import gap_detection

    notes = cohort_project / "notes"
    _write_note(notes, "n_20260401T000001_0001", "extracted", ["topic-a"])
    _write_note(notes, "n_20260401T000002_0002", "integrated", ["topic-b"])

    gaps = gap_detection(cohort_project)
    assert gaps == []
