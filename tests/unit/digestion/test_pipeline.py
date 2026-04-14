"""Tests for ``myco.digestion.pipeline``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError
from myco.digestion.pipeline import (
    Note,
    parse_note,
    promote_to_integrated,
    render_note,
)
from myco.ingestion.eat import append_note


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


# --- parse / render --------------------------------------------------------


def test_parse_note_roundtrip(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    outcome = append_note(ctx=ctx, content="hello\nworld", tags=["t1"])
    text = outcome.path.read_text(encoding="utf-8")
    note = parse_note(text)
    assert note.stage == "raw"
    assert note.frontmatter["tags"] == ["t1"]
    assert "hello" in note.body


def test_parse_without_frontmatter() -> None:
    note = parse_note("just a body\n")
    assert note.stage == "raw"
    assert note.body == "just a body\n"


def test_parse_missing_closing_fence_raises() -> None:
    with pytest.raises(ContractError, match="closing"):
        parse_note("---\nfoo: bar\n(never closed)")


def test_parse_non_mapping_frontmatter_raises() -> None:
    with pytest.raises(ContractError, match="mapping"):
        parse_note("---\n- just\n- a list\n---\nbody\n")


def test_render_preserves_fields() -> None:
    n = Note(
        frontmatter={"stage": "integrated", "tags": ["a", "b"]},
        body="body line",
    )
    out = render_note(n)
    back = parse_note(out)
    assert back.stage == "integrated"
    assert back.frontmatter["tags"] == ["a", "b"]
    assert "body line" in back.body


# --- promote --------------------------------------------------------------


def test_promote_moves_file_and_updates_stage(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    outcome = append_note(ctx=ctx, content="about ferns")
    raw_path = outcome.path

    target = promote_to_integrated(ctx=ctx, raw_path=raw_path)

    assert not raw_path.exists()
    assert target.is_file()
    assert target.parent.name == "integrated"
    assert target.name.startswith("n_")

    promoted = parse_note(target.read_text(encoding="utf-8"))
    assert promoted.stage == "integrated"
    assert "integrated_at" in promoted.frontmatter


def test_promote_dry_run_does_not_move(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    outcome = append_note(ctx=ctx, content="dry test")
    raw_path = outcome.path
    target = promote_to_integrated(ctx=ctx, raw_path=raw_path, dry_run=True)
    assert raw_path.exists()
    assert not target.exists()
    # Target path still has the expected shape.
    assert target.parent.name == "integrated"


def test_promote_rejects_outside_raw(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    bad = genesis_substrate / "rogue.md"
    bad.write_text("---\nstage: raw\n---\nbody\n", encoding="utf-8")
    with pytest.raises(UsageError, match="not under notes/raw"):
        promote_to_integrated(ctx=ctx, raw_path=bad)


def test_promote_missing_file_raises(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="not found"):
        promote_to_integrated(
            ctx=ctx, raw_path=genesis_substrate / "notes" / "raw" / "nope.md"
        )


def test_promote_rejects_missing_reference(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw_dir = genesis_substrate / "notes" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    bad = raw_dir / "ref.md"
    bad.write_text(
        "---\nstage: raw\nreferences: [\"notes/missing.md\"]\n---\nbody\n",
        encoding="utf-8",
    )
    with pytest.raises(ContractError, match="does not exist"):
        promote_to_integrated(ctx=ctx, raw_path=bad)


def test_promote_accepts_existing_reference(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw_dir = genesis_substrate / "notes" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    bad = raw_dir / "ref.md"
    bad.write_text(
        "---\nstage: raw\nreferences: [\"_canon.yaml\"]\n---\nbody\n",
        encoding="utf-8",
    )
    target = promote_to_integrated(ctx=ctx, raw_path=bad)
    assert target.is_file()


def test_promote_ignores_url_references(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw_dir = genesis_substrate / "notes" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    bad = raw_dir / "urlref.md"
    bad.write_text(
        "---\nstage: raw\nreferences: [\"https://example.com\"]\n---\nbody\n",
        encoding="utf-8",
    )
    # Should succeed: URLs are not substrate paths.
    target = promote_to_integrated(ctx=ctx, raw_path=bad)
    assert target.is_file()


def test_promote_rejects_reference_escaping_substrate(
    genesis_substrate: Path,
) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw_dir = genesis_substrate / "notes" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    bad = raw_dir / "escape.md"
    bad.write_text(
        "---\nstage: raw\nreferences: [\"../escape.md\"]\n---\nbody\n",
        encoding="utf-8",
    )
    with pytest.raises(ContractError, match="escapes substrate"):
        promote_to_integrated(ctx=ctx, raw_path=bad)
