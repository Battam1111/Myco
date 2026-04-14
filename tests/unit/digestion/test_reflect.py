"""Tests for ``myco.digestion.reflect``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.digestion.reflect import reflect, run
from myco.ingestion.eat import append_note


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_reflect_on_empty_substrate(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    summary = reflect(ctx=ctx)
    assert summary["promoted"] == 0
    assert summary["errors"] == []
    assert summary["outcomes"] == []


def test_reflect_promotes_all(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="one")
    append_note(ctx=ctx, content="two")
    append_note(ctx=ctx, content="three")
    summary = reflect(ctx=ctx)
    assert summary["promoted"] == 3
    integrated = list((genesis_substrate / "notes" / "integrated").glob("*.md"))
    assert len(integrated) == 3
    raw = list((genesis_substrate / "notes" / "raw").glob("*.md"))
    assert raw == []


def test_reflect_records_errors_and_continues(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "good.md").write_text(
        "---\nstage: raw\n---\nbody\n", encoding="utf-8"
    )
    (raw / "bad.md").write_text(
        "---\nstage: raw\nreferences: [\"notes/missing.md\"]\n---\nbody\n",
        encoding="utf-8",
    )
    summary = reflect(ctx=ctx)
    assert summary["promoted"] == 1
    assert len(summary["errors"]) == 1
    assert summary["errors"][0]["note_id"] == "bad"


def test_reflect_single_note(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    a = append_note(ctx=ctx, content="a")
    append_note(ctx=ctx, content="b")
    summary = reflect(ctx=ctx, note_id=a.path.stem)
    assert summary["promoted"] == 1
    assert (genesis_substrate / "notes" / "raw" / "b.md").exists() or len(
        list((genesis_substrate / "notes" / "raw").glob("*.md"))
    ) == 1


def test_run_exit_code_all_errored(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "bad.md").write_text(
        "---\nstage: raw\nreferences: [\"notes/missing.md\"]\n---\nbody\n",
        encoding="utf-8",
    )
    result = run({}, ctx=ctx)
    assert result.exit_code == 1  # every candidate errored
    assert result.payload["promoted"] == 0


def test_run_exit_code_clean(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="x")
    result = run({}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["promoted"] == 1
