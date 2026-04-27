"""Tests for ``myco.digestion.digest``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.digestion.digest import digest_one, run
from myco.ingestion.eat import append_note


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _eat(ctx: MycoContext, content: str = "n") -> str:
    return append_note(ctx=ctx, content=content).path.stem


def test_digest_promotes_raw_note(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    stem = _eat(ctx, "a note")
    outcome = digest_one(ctx=ctx, note_id=stem)
    assert outcome["status"] == "promoted"
    assert Path(outcome["path"]).is_file()


def test_digest_idempotent_on_integrated(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    stem = _eat(ctx)
    digest_one(ctx=ctx, note_id=stem)
    again = digest_one(ctx=ctx, note_id=stem)
    assert again["status"] == "already_integrated"


def test_digest_accepts_n_prefixed_id(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    stem = _eat(ctx)
    digest_one(ctx=ctx, note_id=stem)
    # Calling with the integrated filename form (n_<stem>) still works.
    again = digest_one(ctx=ctx, note_id=f"n_{stem}")
    assert again["status"] == "already_integrated"


def test_digest_unknown_id_raises(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="unknown note id"):
        digest_one(ctx=ctx, note_id="not_a_real_id")


def test_digest_dry_run(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    stem = _eat(ctx)
    raw_path = genesis_substrate / "notes" / "raw" / f"{stem}.md"
    outcome = digest_one(ctx=ctx, note_id=stem, dry_run=True)
    assert outcome["status"] == "dry_run"
    # File stayed put.
    assert raw_path.is_file()


def test_run_handler(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    stem = _eat(ctx)
    result = run({"note_id": stem}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["status"] == "promoted"


def test_run_missing_id_raises(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="requires a note-id"):
        run({}, ctx=ctx)
