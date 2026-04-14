"""Tests for ``myco.meta``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.ingestion.eat import append_note
from myco.meta import session_end_run


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_session_end_runs_reflect_then_immune(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="some content")
    result = session_end_run({}, ctx=ctx)
    assert result.payload["reflect"]["promoted"] == 1
    assert "immune" in result.payload
    # exit code is the worse of the two; both are <3 (finding-driven).
    assert result.exit_code < 3


def test_session_end_with_empty_substrate(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = session_end_run({}, ctx=ctx)
    assert result.payload["reflect"]["promoted"] == 0
    assert "immune" in result.payload
