"""Comprehensive coverage for digestion/sporulate.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError
from myco.digestion.sporulate import (
    _integrated_notes,
    _summary_line,
    distill_proposal,
    run,
)


def _seed(root: Path) -> MycoContext:
    body = """\
schema_version: "2"
contract_version: "v0.6.0"
identity:
  substrate_id: "test"
  entry_point: "MYCO.md"
system:
  hard_contract:
    rule_count: 7
  write_surface:
    allowed:
      - "_canon.yaml"
      - "notes/**"
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
"""
    (root / "_canon.yaml").write_text(body, encoding="utf-8")
    (root / "MYCO.md").write_text("# x", encoding="utf-8")
    return MycoContext.for_testing(root=root)


def _seed_integrated_notes(ctx: MycoContext, n: int = 2) -> list[Path]:
    integrated = ctx.substrate.paths.notes / "integrated"
    integrated.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        p = integrated / f"n_2026042{i}T000000Z_test{i}.md"
        p.write_text(
            f'---\nstage: integrated\ntags: ["theme1"]\n'
            f'created_at: "2026-04-2{i + 5}T00:00:00Z"\n---\n# Title {i}\nFinding {i} body.\n',
            encoding="utf-8",
        )
        paths.append(p)
    return paths


def test_integrated_notes_empty_when_no_dir(tmp_path: Path):
    ctx = _seed(tmp_path)
    assert _integrated_notes(ctx) == []


def test_integrated_notes_returns_files(tmp_path: Path):
    ctx = _seed(tmp_path)
    _seed_integrated_notes(ctx, n=3)
    assert len(_integrated_notes(ctx)) == 3


def test_summary_line_reads_first_body_line(tmp_path: Path):
    ctx = _seed(tmp_path)
    paths = _seed_integrated_notes(ctx, n=1)
    out = _summary_line(paths[0])
    assert "Title" in out or "Finding" in out


def test_summary_line_handles_missing_file(tmp_path: Path):
    out = _summary_line(tmp_path / "nope.md")
    assert "nope" in out


def test_distill_proposal_invalid_slug_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    with pytest.raises(UsageError, match="invalid distill slug"):
        distill_proposal(ctx=ctx, slug="UPPERCASE")


def test_distill_proposal_no_sources_uses_all(tmp_path: Path):
    ctx = _seed(tmp_path)
    _seed_integrated_notes(ctx, n=2)
    out = distill_proposal(ctx=ctx, slug="myproposal")
    assert out.is_file()
    assert "d_myproposal.md" in out.name
    body = out.read_text(encoding="utf-8")
    # Should reference both integrated notes.
    assert "Finding 0" in body or "Title 0" in body


def test_distill_proposal_explicit_sources(tmp_path: Path):
    ctx = _seed(tmp_path)
    paths = _seed_integrated_notes(ctx, n=2)
    rel = [str(p.relative_to(tmp_path)) for p in paths]
    out = distill_proposal(ctx=ctx, slug="explicit", sources=rel)
    assert out.is_file()


def test_distill_proposal_missing_source_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    with pytest.raises(ContractError, match="missing"):
        distill_proposal(
            ctx=ctx, slug="bad", sources=["notes/integrated/no_such_file.md"]
        )


def test_distill_proposal_source_escapes_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    with pytest.raises(ContractError, match="escapes substrate"):
        distill_proposal(ctx=ctx, slug="esc", sources=["../etc/passwd"])


def test_distill_proposal_already_exists_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    _seed_integrated_notes(ctx, n=1)
    distill_proposal(ctx=ctx, slug="dup")
    with pytest.raises(ContractError, match="already exists"):
        distill_proposal(ctx=ctx, slug="dup")


def test_run_no_slug_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    with pytest.raises(UsageError, match="requires a slug"):
        run({}, ctx=ctx)


def test_run_with_slug_writes_proposal(tmp_path: Path):
    ctx = _seed(tmp_path)
    _seed_integrated_notes(ctx, n=1)
    res = run({"slug": "myproposal"}, ctx=ctx)
    assert res.exit_code == 0
    assert "d_myproposal.md" in res.payload["path"]


def test_run_invalid_sources_type_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    with pytest.raises(UsageError, match="must be a list"):
        run({"slug": "x", "sources": "not-a-list"}, ctx=ctx)


def test_run_empty_sources_list_uses_all(tmp_path: Path):
    """Empty list → fall back to all integrated notes (per code comment)."""
    ctx = _seed(tmp_path)
    _seed_integrated_notes(ctx, n=2)
    res = run({"slug": "fallback", "sources": []}, ctx=ctx)
    assert res.exit_code == 0
