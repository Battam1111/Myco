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


# ---------------------------------------------------------------------------
# Wave 32 — anchor #3 step verbs (evaluate / extract / integrate)
# ---------------------------------------------------------------------------
#
# These verbs are CLI aliases over run_digest, exposing the seven-step
# pipeline as first-class verbs per Wave 26 §2.3 ordering. The tests below
# confirm that each alias produces the same end state as the equivalent
# `myco digest <id> --to <status>` invocation, and that the dispatch
# wiring in cli.py constructs the right namespace for run_digest.

def test_step_verbs_extract_transitions_to_extracted(
    _isolate_myco_project: Path,
) -> None:
    """Wave 32 D2: `myco extract <id>` transitions a note to status='extracted'.

    Constructs a digest-shaped namespace mimicking the cli.py dispatch path
    in `args.command in ("evaluate", "extract", "integrate")`, calls
    run_digest directly, asserts post-state.
    """
    from myco.notes_cmd import run_digest
    project = _isolate_myco_project

    p = notes.write_note(
        project, body="extract me",
        tags=["wave32-extract"], source="eat", status="raw",
    )
    note_id = p.stem

    # Mimic cli.py dispatch: extract → run_digest with to='extracted'
    args = SimpleNamespace(
        note_id=note_id,
        to="extracted",
        excrete=None,
        project_dir=str(project),
    )
    rc = run_digest(args)
    assert rc == 0, "extract dispatch must succeed"

    meta_after, _ = notes.read_note(p)
    assert meta_after["status"] == "extracted", \
        "extract must leave the note in status=extracted"
    assert int(meta_after.get("digest_count") or 0) == 1, \
        "extract must increment digest_count"


def test_step_verbs_integrate_transitions_to_integrated(
    _isolate_myco_project: Path,
) -> None:
    """Wave 32 D2: `myco integrate <id>` transitions a note to status='integrated'.

    Mirrors the extract test for the integrate alias.
    """
    from myco.notes_cmd import run_digest
    project = _isolate_myco_project

    p = notes.write_note(
        project, body="integrate me",
        tags=["wave32-integrate"], source="eat", status="raw",
    )
    note_id = p.stem

    args = SimpleNamespace(
        note_id=note_id,
        to="integrated",
        excrete=None,
        project_dir=str(project),
    )
    rc = run_digest(args)
    assert rc == 0

    meta_after, _ = notes.read_note(p)
    assert meta_after["status"] == "integrated"
    assert int(meta_after.get("digest_count") or 0) == 1


def test_step_verbs_evaluate_transitions_to_digesting(
    _isolate_myco_project: Path, capsys
) -> None:
    """Wave 32 D2: `myco evaluate <id>` (no --to) transitions raw→digesting
    and prints reflection prompts.

    The dispatch passes `to=None`, which run_digest interprets as
    "default mode": transition raw→digesting and surface prompts. This
    test asserts the transition happened and the reflection prompt
    section was emitted to stdout.
    """
    from myco.notes_cmd import run_digest
    project = _isolate_myco_project

    p = notes.write_note(
        project, body="evaluate me",
        tags=["wave32-evaluate"], source="eat", status="raw",
    )
    note_id = p.stem

    args = SimpleNamespace(
        note_id=note_id,
        to=None,  # evaluate dispatches with to=None
        excrete=None,
        project_dir=str(project),
    )
    rc = run_digest(args)
    assert rc == 0

    meta_after, _ = notes.read_note(p)
    assert meta_after["status"] == "digesting", \
        "evaluate (no --to) must transition raw→digesting"

    captured = capsys.readouterr()
    assert "Reflection prompts" in captured.out, \
        "evaluate must print the reflection prompts section"


# ---------------------------------------------------------------------------
# Wave 33 — D-layer auto-excretion (prune)
# ---------------------------------------------------------------------------
#
# Three tests covering the load-bearing paths of `myco prune`:
# 1. dry-run does NOT mutate (the safety default — must hold or the verb is dangerous)
# 2. apply DOES mutate the right notes (the actual feature)
# 3. fresh notes are NOT pruned (the grace period — without this, every fresh note becomes a candidate)

from datetime import datetime, timedelta


def _fabricate_aged_note(
    project: Path,
    *,
    age_days: int,
    status: str = "extracted",
    view_count: int = 0,
) -> Path:
    """Helper: create a note that LOOKS like it was created `age_days`
    days ago. Used to fabricate dead-knowledge candidates without waiting
    real time. We write the note normally then patch its frontmatter
    timestamps directly.
    """
    p = notes.write_note(
        project, body=f"aged note {age_days}d",
        tags=[f"aged-{age_days}d"], source="eat", status="raw",
    )
    aged_iso = (datetime.now() - timedelta(days=age_days)).strftime("%Y-%m-%dT%H:%M:%S")
    meta, body = notes.read_note(p)
    meta["created"] = aged_iso
    meta["last_touched"] = aged_iso
    meta["status"] = status
    meta["view_count"] = view_count
    p.write_text(notes.serialize_note(meta, body), encoding="utf-8")
    return p


def test_prune_dry_run_no_mutation(_isolate_myco_project: Path) -> None:
    """Wave 33 D1: dry-run mode must NOT mutate any note.

    This is the load-bearing safety property. If dry-run mutates, the
    verb is silently destructive even when the user explicitly asked
    for a preview. Without this test the safety default is aspirational.
    """
    project = _isolate_myco_project

    # Fabricate two dead-knowledge notes (35d old, terminal, never viewed)
    p1 = _fabricate_aged_note(project, age_days=35, status="extracted")
    p2 = _fabricate_aged_note(project, age_days=40, status="integrated")

    # Snapshot before
    snapshot = {
        p1.name: (p1.read_text(encoding="utf-8"), p1.stat().st_mtime_ns),
        p2.name: (p2.read_text(encoding="utf-8"), p2.stat().st_mtime_ns),
    }

    results = notes.auto_excrete_dead_knowledge(
        project, threshold_days=30, dry_run=True,
    )

    # 2 candidates found, 0 applied
    assert len(results) == 2, f"expected 2 candidates, got {len(results)}"
    assert all(not r.get("applied") for r in results), \
        "dry-run must not apply any mutation"

    # Files unchanged
    for p in (p1, p2):
        new_text = p.read_text(encoding="utf-8")
        new_mtime = p.stat().st_mtime_ns
        assert new_text == snapshot[p.name][0], \
            f"dry-run mutated {p.name} content"
        assert new_mtime == snapshot[p.name][1], \
            f"dry-run touched {p.name} mtime"


def test_prune_apply_excretes_dead_notes(_isolate_myco_project: Path) -> None:
    """Wave 33 D1: --apply mode actually mutates dead-knowledge candidates.

    The mutation: status → 'excreted', excrete_reason set with the
    criteria values that triggered the prune.
    """
    project = _isolate_myco_project

    p = _fabricate_aged_note(project, age_days=45, status="extracted")
    note_id = p.stem

    results = notes.auto_excrete_dead_knowledge(
        project, threshold_days=30, dry_run=False,
    )

    assert len(results) == 1
    r = results[0]
    assert r.get("applied") is True, "apply must mutate the candidate"
    assert r["id"] == note_id

    meta_after, _ = notes.read_note(p)
    assert meta_after["status"] == "excreted", \
        "apply must transition the note to excreted"
    reason = meta_after.get("excrete_reason") or ""
    assert "auto-prune" in reason, \
        "excrete_reason must be machine-parseable as auto-prune"
    assert "threshold=30d" in reason, \
        "excrete_reason must include the threshold for audit"
    assert "view_count=0" in reason, \
        "excrete_reason must include the view_count for audit"


def test_prune_respects_grace_period(_isolate_myco_project: Path) -> None:
    """Wave 33: notes inside the grace period (younger than threshold)
    are NOT pruned.

    This is the dead_knowledge condition #2 (created < cutoff). Without
    it, fresh notes would be pruned the moment they reach terminal status,
    and the substrate would never accumulate any extracted/integrated
    knowledge.
    """
    project = _isolate_myco_project

    # Fresh note (5 days old, well within grace period)
    p_fresh = _fabricate_aged_note(project, age_days=5, status="integrated")
    # Old note (60 days old, well past grace period)
    p_old = _fabricate_aged_note(project, age_days=60, status="integrated")

    results = notes.auto_excrete_dead_knowledge(
        project, threshold_days=30, dry_run=False,
    )

    # Only the old note should be in the result
    assert len(results) == 1, \
        f"only old note should be pruned, got {len(results)} candidates"
    assert results[0]["id"] == p_old.stem, \
        "the OLD note (60d) should be the only candidate, not the fresh one (5d)"

    # Fresh note still integrated
    fresh_meta, _ = notes.read_note(p_fresh)
    assert fresh_meta["status"] == "integrated", \
        "fresh note must NOT be excreted"

    # Old note now excreted
    old_meta, _ = notes.read_note(p_old)
    assert old_meta["status"] == "excreted", \
        "old note must be excreted"
