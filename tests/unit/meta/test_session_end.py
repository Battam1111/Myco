"""Tests for ``myco.meta.session_end``.

Replaces the old ``tests/unit/test_meta.py`` — the handler moved from
``myco.meta:session_end_run`` to ``myco.meta.session_end:run`` in the
v0.5 package migration. Backward-compat re-export still works (tested
separately below).
"""

from __future__ import annotations

from pathlib import Path

from myco.meta.session_end import run as session_end_run

from myco.core.context import MycoContext
from myco.ingestion.eat import append_note


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_session_end_runs_reflect_then_immune(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="some content")
    result = session_end_run({}, ctx=ctx)
    assert result.payload["reflect"]["promoted"] == 1
    assert "immune" in result.payload
    assert result.exit_code < 3


def test_session_end_with_empty_substrate(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = session_end_run({}, ctx=ctx)
    assert result.payload["reflect"]["promoted"] == 0
    assert "immune" in result.payload


def test_backward_compat_reexport_still_imports() -> None:
    """``from myco.meta import session_end_run`` must still work at v0.5
    (pre-v0.5 code that pulled the function from the top-level
    ``myco.meta`` module continues to import without edit)."""
    from myco.meta import session_end_run as alias

    assert alias is session_end_run
