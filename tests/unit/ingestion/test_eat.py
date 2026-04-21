"""Tests for ``myco.ingestion.eat``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from myco.core.context import MycoContext
from myco.ingestion.eat import append_note, run


def _mk_ctx(root: Path, *, now: datetime | None = None) -> MycoContext:
    return MycoContext.for_testing(root=root, now=now)


def test_append_note_creates_raw_dir(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    # genesis doesn't create notes/raw/ specifically; eat should.
    assert not (genesis_substrate / "notes" / "raw").exists()
    outcome = append_note(ctx=ctx, content="hello world")
    assert outcome.path.is_file()
    assert outcome.path.parent.name == "raw"


def test_append_note_writes_frontmatter(genesis_substrate: Path) -> None:
    """v0.5.8: frontmatter now renders via ``yaml.safe_dump`` (block
    style, single-quoted scalars) to defeat YAML injection via
    attacker-controlled ``source``/``tags``. The test validates the
    structural shape via ``parse_note`` rather than exact string
    matches so the assertion is stable across YAML-library output
    variants.
    """
    from myco.digestion.pipeline import parse_note

    ctx = _mk_ctx(genesis_substrate)
    now = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
    outcome = append_note(
        ctx=ctx,
        content="some content",
        tags=["alpha", "beta"],
        source="agent",
        now=now,
    )
    text = outcome.path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    note = parse_note(text)
    assert note.frontmatter["captured_at"] == "2026-04-15T12:00:00Z"
    assert list(note.frontmatter["tags"]) == ["alpha", "beta"]
    assert note.frontmatter["source"] == "agent"
    assert note.frontmatter["stage"] == "raw"
    assert "some content\n" in text


def test_append_note_empty_tags_render_empty_list(genesis_substrate: Path) -> None:
    """Empty tags list — shape-stable across safe_dump vs hand-rolled."""
    from myco.digestion.pipeline import parse_note

    ctx = _mk_ctx(genesis_substrate)
    outcome = append_note(ctx=ctx, content="body")
    text = outcome.path.read_text(encoding="utf-8")
    note = parse_note(text)
    assert note.frontmatter["tags"] == []


def test_collision_resolution(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    now = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
    o1 = append_note(ctx=ctx, content="same title", now=now)
    o2 = append_note(ctx=ctx, content="same title", now=now)
    o3 = append_note(ctx=ctx, content="same title", now=now)
    paths = {o1.path, o2.path, o3.path}
    assert len(paths) == 3
    names = sorted(p.name for p in paths)
    assert names[0].endswith(".md")
    assert "_2" in names[1] or "_2" in names[2]


def test_slug_uses_first_line(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    outcome = append_note(ctx=ctx, content="Hello, World!\nmore\nstuff")
    assert "hello-world" in outcome.path.name.lower()


def test_slug_handles_pure_symbols(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    # No alphanumerics → empty slug, filename is just the stamp.
    outcome = append_note(ctx=ctx, content="!!! ???")
    assert outcome.path.name.endswith(".md")


def test_run_handler_returns_result(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = run(
        {"content": "via handler", "tags": ["t1"], "source": "test"},
        ctx=ctx,
    )
    assert result.exit_code == 0
    assert Path(result.payload["path"]).is_file()
    assert result.payload["tags"] == ("t1",)
    assert result.payload["source"] == "test"
