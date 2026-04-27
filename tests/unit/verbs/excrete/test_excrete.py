"""Tests for ``myco.ingestion.excrete`` (v0.5.24).

The ``excrete`` verb is the inverse of ``eat``: it removes a raw note
from ``notes/raw/`` when the note was captured by accident (typo,
wrong substrate, duplicate). Key invariants exercised here:

- Refuses without ``--note-id`` or without ``--reason``.
- Targets outside ``notes/raw/`` are refused (integrated / distilled
  notes are protected by the ingestion doctrine's append-only rule).
- Dry-run returns the exact move plan but never touches disk.
- Real run moves the note to ``.myco_state/excreted/<stem>.md`` and
  prepends ``excreted_at`` / ``excreted_reason`` / ``excreted_from``
  to the frontmatter.
- Write-surface rejection is surfaced as ``UsageError`` with a hint.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.ingestion.eat import append_note
from myco.ingestion.excrete import _annotate_frontmatter, run


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _seed_raw_note(root: Path) -> Path:
    ctx = _ctx(root)
    outcome = append_note(
        ctx=ctx,
        content="test bait — excretion unit test payload",
        tags=["excrete-test"],
    )
    return outcome.path


def test_excrete_dry_run_returns_plan_without_touching_disk(
    genesis_substrate: Path,
) -> None:
    note = _seed_raw_note(genesis_substrate)
    stem = note.stem
    ctx = _ctx(genesis_substrate)

    r = run(
        {"note_id": stem, "reason": "dry-run audit", "dry_run": True},
        ctx=ctx,
    )

    assert r.exit_code == 0
    assert r.payload["dry_run"] is True
    assert r.payload["note_id"] == stem
    assert r.payload["from_path"] == f"notes/raw/{stem}.md"
    assert r.payload["to_path"] == f".myco_state/excreted/{stem}.md"
    # Disk must be untouched.
    assert note.exists()
    assert not (genesis_substrate / ".myco_state" / "excreted").exists()


def test_excrete_real_run_moves_note_and_annotates_frontmatter(
    genesis_substrate: Path,
) -> None:
    note = _seed_raw_note(genesis_substrate)
    stem = note.stem
    ctx = _ctx(genesis_substrate)

    r = run({"note_id": stem, "reason": "accidental-ingest"}, ctx=ctx)

    assert r.exit_code == 0
    assert r.payload["dry_run"] is False
    # Original gone.
    assert not note.exists()
    # Tombstone present.
    tombstone = genesis_substrate / ".myco_state" / "excreted" / f"{stem}.md"
    assert tombstone.is_file()
    text = tombstone.read_text(encoding="utf-8")
    assert "excreted_at: '" in text
    assert "excreted_reason: 'accidental-ingest'" in text
    assert f"excreted_from: 'notes/raw/{stem}.md'" in text
    # Original body still present.
    assert "test bait" in text


def test_excrete_requires_note_id(genesis_substrate: Path) -> None:
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="note-id is required"):
        run({"reason": "anything"}, ctx=ctx)


def test_excrete_requires_reason(genesis_substrate: Path) -> None:
    note = _seed_raw_note(genesis_substrate)
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="reason is required"):
        run({"note_id": note.stem}, ctx=ctx)


def test_excrete_rejects_whitespace_only_reason(
    genesis_substrate: Path,
) -> None:
    note = _seed_raw_note(genesis_substrate)
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="reason is required"):
        run({"note_id": note.stem, "reason": "   "}, ctx=ctx)


def test_excrete_rejects_missing_note(genesis_substrate: Path) -> None:
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="not found in notes/raw/"):
        run(
            {"note_id": "20260101T000000Z_nonexistent", "reason": "test"},
            ctx=ctx,
        )


def test_excrete_tolerates_stem_with_trailing_md(
    genesis_substrate: Path,
) -> None:
    """Forgiveness: if the agent passes the full filename (incl. ``.md``)
    instead of just the stem, excrete still resolves it rather than
    raising. This mirrors agent behaviour in practice (they often have
    the filename at hand, not the stem)."""
    note = _seed_raw_note(genesis_substrate)
    ctx = _ctx(genesis_substrate)

    r = run(
        {"note_id": f"{note.stem}.md", "reason": "trailing-md stem"},
        ctx=ctx,
    )
    assert r.exit_code == 0
    assert not note.exists()


def test_excrete_writesurface_violation_surfaces_usageerror(
    tmp_path: Path,
) -> None:
    """If write_surface doesn't cover ``.myco_state/**`` the operation
    fails with a UsageError that tells the operator how to fix it (add
    the pattern to _canon.yaml). Fresh v0.5.24 substrates include the
    pattern by default — this path only fires on pre-v0.5.24 canons."""
    # Build a substrate whose write_surface deliberately OMITS
    # .myco_state/** to force the guard.
    (tmp_path / "notes" / "raw").mkdir(parents=True)
    (tmp_path / "_canon.yaml").write_text(
        """\
schema_version: "1"
contract_version: "v0.5.24"
identity:
  substrate_id: "excrete-ws-test"
  tags: []
  entry_point: "MYCO.md"
system:
  write_surface:
    allowed:
      - "_canon.yaml"
      - "MYCO.md"
      - "notes/**"
  hard_contract:
    rule_count: 7
subsystems:
  ingestion: {}
""",
        encoding="utf-8",
    )
    (tmp_path / "MYCO.md").write_text("# test\n", encoding="utf-8")
    # Seed a raw note directly.
    raw = tmp_path / "notes" / "raw" / "20260424T000000Z_bait.md"
    raw.write_text(
        "---\ncaptured_at: '2026-04-24T00:00:00Z'\n"
        "tags: []\nsource: agent\nstage: raw\n---\nbait\n",
        encoding="utf-8",
    )

    ctx = MycoContext.for_testing(root=tmp_path)
    with pytest.raises(UsageError, match="write_surface does not allow"):
        run(
            {"note_id": "20260424T000000Z_bait", "reason": "ws-test"},
            ctx=ctx,
        )


def test_annotate_frontmatter_inserts_before_closing_delimiter() -> None:
    text = (
        "---\n"
        "captured_at: '2026-04-24T00:00:00Z'\n"
        "source: agent\n"
        "tags: []\n"
        "stage: raw\n"
        "---\nBody\n"
    )
    out = _annotate_frontmatter(
        text,
        excreted_at="2026-04-24T12:00:00Z",
        excreted_reason="typo",
        excreted_from="notes/raw/x.md",
    )
    # Original keys preserved.
    assert "captured_at: '2026-04-24T00:00:00Z'" in out
    assert "stage: raw" in out
    # New keys inserted before closing delimiter (not at end of file).
    body_idx = out.index("Body")
    closing_idx = out.rindex("---")
    assert out.index("excreted_at:") < closing_idx < body_idx


def test_annotate_frontmatter_handles_missing_frontmatter() -> None:
    """A note without frontmatter gets a minimal one prepended."""
    out = _annotate_frontmatter(
        "just a body\n",
        excreted_at="2026-04-24T12:00:00Z",
        excreted_reason="typo",
        excreted_from="notes/raw/x.md",
    )
    assert out.startswith("---\n")
    assert "excreted_at: '2026-04-24T12:00:00Z'" in out
    assert "just a body" in out


def test_annotate_frontmatter_escapes_apostrophes_in_reason() -> None:
    """Apostrophes in reason strings must be doubled (YAML single-quote
    scalar escaping) so the frontmatter stays parseable."""
    out = _annotate_frontmatter(
        "---\ntags: []\n---\nbody\n",
        excreted_at="2026-04-24T12:00:00Z",
        excreted_reason="it's a typo",
        excreted_from="notes/raw/x.md",
    )
    assert "excreted_reason: 'it''s a typo'" in out
