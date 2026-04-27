"""Tests for ``digestion.reassimilate`` (v0.6.0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import MycoError
from myco.digestion.reassimilate import reassimilate_integrated


def test_reassimilate_empty_reason_raises(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    with pytest.raises(MycoError):
        reassimilate_integrated(ctx, "some-id", "")


def test_reassimilate_whitespace_reason_raises(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    with pytest.raises(MycoError):
        reassimilate_integrated(ctx, "some-id", "   ")


def test_reassimilate_not_found_returns_status(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    out = reassimilate_integrated(ctx, "nonexistent-id", "test reason")
    assert out["status"] == "not_found"
    assert out["exit_code"] == 3


def test_reassimilate_round_trip(genesis_substrate: Path):
    """Create an integrated note, reassimilate it back to raw."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    integrated_dir = genesis_substrate / "notes" / "integrated"
    integrated_dir.mkdir(parents=True, exist_ok=True)
    note_id = "20260101T120000Z_test"
    integrated_path = integrated_dir / f"n_{note_id}.md"
    integrated_path.write_text(
        "---\n"
        "stage: integrated\n"
        "captured_at: '2026-01-01T12:00:00Z'\n"
        "---\n"
        "body content\n",
        encoding="utf-8",
    )
    out = reassimilate_integrated(ctx, note_id, "needs re-marination")
    assert out["status"] == "reassimilated"
    assert out["exit_code"] == 0
    # File should now be in raw/
    raw_dir = genesis_substrate / "notes" / "raw"
    assert any(p.name.startswith(note_id) for p in raw_dir.glob("*.md"))


def test_reassimilate_dry_run(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    integrated_dir = genesis_substrate / "notes" / "integrated"
    integrated_dir.mkdir(parents=True, exist_ok=True)
    note_id = "20260101T120000Z_dry"
    integrated_path = integrated_dir / f"n_{note_id}.md"
    integrated_path.write_text("---\nstage: integrated\n---\nbody\n", encoding="utf-8")
    out = reassimilate_integrated(ctx, note_id, "dry test", dry_run=True)
    assert out["status"] == "reassimilated"
    assert out["dry_run"] is True
    assert integrated_path.is_file()  # not actually moved


def test_reassimilate_idempotent_on_re_raw(genesis_substrate: Path):
    """A note already in re_raw stage is no-op."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    integrated_dir = genesis_substrate / "notes" / "integrated"
    integrated_dir.mkdir(parents=True, exist_ok=True)
    note_id = "20260101T120000Z_already_re_raw"
    integrated_path = integrated_dir / f"n_{note_id}.md"
    integrated_path.write_text("---\nstage: re_raw\n---\nbody\n", encoding="utf-8")
    out = reassimilate_integrated(ctx, note_id, "test")
    assert out["status"] == "already_re_raw"
