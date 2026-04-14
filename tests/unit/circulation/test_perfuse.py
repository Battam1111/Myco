"""Tests for ``myco.circulation.perfuse``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.circulation.perfuse import perfuse, run
from myco.core.context import MycoContext
from myco.core.errors import UsageError


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_perfuse_empty_substrate_clean(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = perfuse(ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["scope"] == "all"
    assert result.payload["node_count"] >= 1


def test_perfuse_detects_dangling_markdown_link(
    genesis_substrate: Path,
) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "bad.md").write_text(
        "---\nstage: raw\n---\nsee [x](./nowhere.md)\n",
        encoding="utf-8",
    )
    result = perfuse(ctx=ctx)
    dangling = result.payload["dangling"]
    assert any("nowhere.md" in d[1] for d in dangling)
    assert any("dangling" in p for p in result.payload["proposals"])


def test_perfuse_detects_orphan_note(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "lonely.md").write_text(
        "---\nstage: raw\n---\nnobody links to me\n",
        encoding="utf-8",
    )
    result = perfuse(ctx=ctx)
    orphans = result.payload["orphans"]
    assert any("lonely.md" in o for o in orphans)


def test_perfuse_scope_canon_only(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "a.md").write_text(
        "---\nstage: raw\n---\nsee [x](./nope.md)\n",
        encoding="utf-8",
    )
    # With scope=canon, a dangling edge originating from notes/ should
    # NOT appear in the report.
    result = perfuse(ctx=ctx, scope="canon")
    for src, _ in result.payload["dangling"]:
        assert src == "_canon.yaml"


def test_perfuse_rejects_bad_scope(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="invalid perfuse scope"):
        perfuse(ctx=ctx, scope="garbage")  # type: ignore[arg-type]


def test_run_handler(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = run({"scope": "all"}, ctx=ctx)
    assert result.exit_code == 0
    assert "orphans" in result.payload
    assert "dangling" in result.payload


def test_run_accepts_dry_run_arg(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    # dry_run is ignored at B.6 but must not error.
    result = run({"scope": "all", "dry_run": True}, ctx=ctx)
    assert result.exit_code == 0


def test_run_rejects_bad_scope(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="invalid perfuse scope"):
        run({"scope": "bogus"}, ctx=ctx)
