"""Tests for ``myco.ingestion.boot_brief``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import ContractError
from myco.ingestion.boot_brief import (
    BEGIN_MARKER,
    END_MARKER,
    patch_entry_point,
    render_signals_block,
)


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_render_empty_signals() -> None:
    block = render_signals_block({})
    assert block.startswith(BEGIN_MARKER)
    assert block.endswith(END_MARKER)
    assert "- (no signals)" in block


def test_render_with_signals() -> None:
    block = render_signals_block({"backlog": 3, "drift": False})
    assert "- backlog: 3" in block
    assert "- drift: False" in block


def test_first_injection_appends_block(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    entry = genesis_substrate / "MYCO.md"
    before = entry.read_text(encoding="utf-8")
    assert BEGIN_MARKER not in before

    path = patch_entry_point(ctx=ctx, signals={"backlog": 0})
    assert path == entry
    after = entry.read_text(encoding="utf-8")
    assert BEGIN_MARKER in after
    assert END_MARKER in after
    assert "- backlog: 0" in after
    # Original content preserved.
    assert before.strip() in after


def test_reinjection_replaces_block(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    patch_entry_point(ctx=ctx, signals={"backlog": 1})
    first = (genesis_substrate / "MYCO.md").read_text(encoding="utf-8")

    patch_entry_point(ctx=ctx, signals={"backlog": 5})
    second = (genesis_substrate / "MYCO.md").read_text(encoding="utf-8")

    # Only one BEGIN marker after re-injection.
    assert second.count(BEGIN_MARKER) == 1
    assert second.count(END_MARKER) == 1
    assert "- backlog: 5" in second
    assert "- backlog: 1" not in second
    assert len(second) != len(first) or first != second


def test_idempotent_same_input(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    patch_entry_point(ctx=ctx, signals={"k": "v"})
    a = (genesis_substrate / "MYCO.md").read_text(encoding="utf-8")
    patch_entry_point(ctx=ctx, signals={"k": "v"})
    b = (genesis_substrate / "MYCO.md").read_text(encoding="utf-8")
    assert a == b


def test_missing_entry_point_raises(genesis_substrate: Path) -> None:
    (genesis_substrate / "MYCO.md").unlink()
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(ContractError, match="entry-point .* not found"):
        patch_entry_point(ctx=ctx, signals={})


def test_corrupt_double_marker_raises(genesis_substrate: Path) -> None:
    entry = genesis_substrate / "MYCO.md"
    entry.write_text(
        entry.read_text(encoding="utf-8")
        + f"\n{BEGIN_MARKER}\n{END_MARKER}\n{BEGIN_MARKER}\n{END_MARKER}\n",
        encoding="utf-8",
    )
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(ContractError, match="corrupt"):
        patch_entry_point(ctx=ctx, signals={"x": 1})


def test_corrupt_begin_without_end_raises(genesis_substrate: Path) -> None:
    entry = genesis_substrate / "MYCO.md"
    entry.write_text(
        entry.read_text(encoding="utf-8") + f"\n{BEGIN_MARKER}\n",
        encoding="utf-8",
    )
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(ContractError, match="BEGIN without END"):
        patch_entry_point(ctx=ctx, signals={"x": 1})
