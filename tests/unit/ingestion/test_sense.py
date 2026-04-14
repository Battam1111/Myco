"""Tests for ``myco.ingestion.sense``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.ingestion.eat import append_note
from myco.ingestion.sense import MAX_HITS, run, search_substrate


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_search_finds_canon_hit(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    hits = search_substrate(ctx=ctx, query="substrate_id")
    assert any("_canon.yaml" in h.path for h in hits)


def test_search_finds_note_content(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="a memorable phrase about ferns")
    hits = search_substrate(ctx=ctx, query="ferns")
    assert any("ferns" in h.snippet.lower() for h in hits)
    assert any("notes/raw/" in h.path for h in hits)


def test_scope_canon_restricts_search(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="only-in-notes-marker")
    canon_hits = search_substrate(
        ctx=ctx, query="only-in-notes-marker", scope="canon"
    )
    assert canon_hits == ()
    all_hits = search_substrate(
        ctx=ctx, query="only-in-notes-marker", scope="all"
    )
    assert len(all_hits) >= 1


def test_empty_query_raises(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="non-empty"):
        search_substrate(ctx=ctx, query="   ")


def test_unknown_scope_raises(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="unknown sense scope"):
        search_substrate(ctx=ctx, query="x", scope="bogus")  # type: ignore[arg-type]


def test_hit_cap_enforced(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    # Seed many notes with a common word.
    for i in range(80):
        append_note(ctx=ctx, content=f"note {i} common-marker payload")
    hits = search_substrate(ctx=ctx, query="common-marker")
    assert len(hits) <= MAX_HITS


def test_run_handler(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = run({"query": "substrate_id", "scope": "all"}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["query"] == "substrate_id"
    assert len(result.payload["hits"]) >= 1


def test_case_insensitive(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="UPPERCASE_MARKER token")
    hits = search_substrate(ctx=ctx, query="uppercase_marker")
    assert len(hits) >= 1
