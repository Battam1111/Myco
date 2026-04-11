"""Wave 25 seed tests — ``myco.notes`` core invariants.

Four focused tests covering the most load-bearing paths in the notes
module. These are intentionally minimal — this is the seed of the test
suite, not its final form. Real coverage grows wave by wave as friction
demands (craft §4.3 L2).

Scar-class coverage rationale (craft §3.3 Round 3 evidence):

- ``test_write_note_roundtrip`` guards the frontmatter contract that
  L10 lint depends on. If a future refactor breaks frontmatter shape,
  L10 would eventually catch it at lint time, but this test catches it
  at edit time — pre-image of "two sensors must agree" (Wave 24).
- ``test_parse_serialize_roundtrip`` guards the ``parse_frontmatter``
  ↔ ``serialize_note`` inverse property. If a character-class escape
  ever regresses, round-trip would break silently in the digestive
  loop; this test fails loud instead.
- ``test_write_note_handles_id_collision`` exercises the
  ``while (notes_dir / id_to_filename(nid)).exists(): nid = ...``
  retry path in ``write_note``. Previously live-tested only by the
  extremely rare case of two notes eaten in the same second with the
  same 4-hex suffix; now deterministic.
- ``test_project_root_raises_on_nonexistent`` locks in the Wave 20
  silent-fail fix. The prior bug returned a healthy-looking path for
  directories with no ``_canon.yaml``; regression here would mean
  ``myco hunger`` starts reporting false-healthy again on /tmp runs.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from myco import notes
from myco.notes import MycoProjectNotFound
from myco.notes_cmd import _project_root


def test_write_note_roundtrip(_isolate_myco_project: Path) -> None:
    """``write_note`` creates a file whose frontmatter parses back to
    the required Myco note schema.

    This is the invariant L10 Notes Schema lint depends on. If this
    test fails, every downstream lint dimension that reads
    ``notes/n_*.md`` is also broken.
    """
    project = _isolate_myco_project

    path = notes.write_note(
        project,
        body="hello world",
        tags=["wave25", "seed-test"],
        source="eat",
        title="Seed test title",
    )

    assert path.exists(), "write_note should return an extant path"
    assert path.parent == project / "notes"
    assert path.name.startswith("n_") and path.suffix == ".md"

    meta, body = notes.read_note(path)
    for field in notes.REQUIRED_FIELDS:
        assert field in meta, f"missing required field: {field}"
    assert meta["status"] == "raw"
    assert meta["source"] == "eat"
    assert set(meta["tags"]) == {"wave25", "seed-test"}
    assert meta["digest_count"] == 0
    assert meta["promote_candidate"] is False
    assert meta["excrete_reason"] is None
    assert "# Seed test title" in body
    assert "hello world" in body


def test_parse_serialize_roundtrip(_isolate_myco_project: Path) -> None:
    """``serialize_note`` → ``parse_frontmatter`` round-trips cleanly.

    Guards the inverse property between the two helpers. Any future
    change to frontmatter encoding (key order, unicode handling,
    quoting) that breaks this round-trip would also break the
    digestive loop, because every ``myco digest`` call reads then
    writes a note through these helpers.
    """
    original_meta = {
        "id": "n_20260412T000000_abcd",
        "status": "raw",
        "source": "eat",
        "tags": ["roundtrip", "中文-ok"],
        "created": "2026-04-12T00:00:00",
        "last_touched": "2026-04-12T00:00:00",
        "digest_count": 0,
        "promote_candidate": False,
        "excrete_reason": None,
    }
    original_body = "# Title\n\nBody with 中文 and symbols: * & <>.\n"

    serialized = notes.serialize_note(original_meta, original_body)
    parsed_meta, parsed_body = notes.parse_frontmatter(serialized)

    for key, value in original_meta.items():
        assert parsed_meta[key] == value, f"field {key!r} round-trip broken"
    assert "Body with 中文" in parsed_body
    assert "# Title" in parsed_body


def test_write_note_handles_id_collision(
    _isolate_myco_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``write_note`` retries id generation on filename collision.

    The while-loop in ``write_note`` is there because 4 hex chars ×
    one-second timestamp means the birthday collision probability is
    nonzero under bulk import. This test forces that path
    deterministically: mock ``generate_id`` to return one duplicate
    then a fresh id, and assert both notes land on disk with distinct
    filenames.
    """
    project = _isolate_myco_project

    # First write uses the real generator to plant a note at a known id.
    first_path = notes.write_note(
        project, body="first note", tags=["collision-setup"]
    )
    first_id = notes.filename_to_id(first_path.name)
    assert first_id is not None

    # Now mock generate_id so the next write_note returns first_id on
    # its first call (collision) and a fresh id on the second call
    # (escape). This exercises the retry branch end-to-end.
    collision_ids = iter([first_id, "n_20261231T235959_dead"])
    monkeypatch.setattr(
        notes, "generate_id", lambda now=None: next(collision_ids)
    )

    second_path = notes.write_note(
        project, body="second note", tags=["collision-result"]
    )

    assert second_path.exists()
    assert second_path != first_path
    assert second_path.name == "n_20261231T235959_dead.md"

    # Sanity: first note still exists, not clobbered.
    assert first_path.exists()
    assert "first note" in first_path.read_text(encoding="utf-8")


def test_project_root_raises_on_nonexistent_path(tmp_path: Path) -> None:
    """``_project_root`` raises ``MycoProjectNotFound`` for a directory
    with no ``_canon.yaml`` in its walk-up path.

    This locks in the Wave 20 silent-fail fix. Regression here would
    mean the Wave 20 doctrine ("a sensory system that returns healthy
    when its sensors are disconnected is worse than a crash") has been
    silently abandoned.

    Note: this test deliberately ignores the autouse fixture's chdir
    by supplying an explicit ``--project-dir`` that points outside any
    Myco project root. The tmp_path fixture gives us a guaranteed-
    fresh directory with no ``_canon.yaml`` at or above it.
    """
    orphan = tmp_path / "orphan_no_canon"
    orphan.mkdir()

    args = SimpleNamespace(project_dir=str(orphan))

    with pytest.raises(MycoProjectNotFound) as excinfo:
        _project_root(args)

    msg = str(excinfo.value)
    assert "not a Myco project" in msg
    assert str(orphan) in msg
    assert "MYCO_ALLOW_NO_PROJECT" in msg  # escape hatch documented in error
