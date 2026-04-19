"""Tests for ``myco.digestion.distill``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError
from myco.digestion.distill import distill_proposal, run
from myco.digestion.pipeline import parse_note
from myco.digestion.reflect import reflect
from myco.ingestion.eat import append_note


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _seed_integrated(genesis_substrate: Path, n: int = 2) -> list[str]:
    ctx = _mk_ctx(genesis_substrate)
    stems: list[str] = []
    for i in range(n):
        stems.append(append_note(ctx=ctx, content=f"finding {i}").path.stem)
    reflect(ctx=ctx)
    return stems


def test_distill_creates_proposal(genesis_substrate: Path) -> None:
    _seed_integrated(genesis_substrate, n=2)
    ctx = _mk_ctx(genesis_substrate)
    target = distill_proposal(ctx=ctx, slug="shaping-bottleneck")
    assert target.is_file()
    assert target.name == "d_shaping-bottleneck.md"
    note = parse_note(target.read_text(encoding="utf-8"))
    assert note.stage == "distilled"
    assert note.frontmatter["proposed_doctrine"] == "shaping-bottleneck"
    assert len(note.frontmatter["sources"]) == 2


def test_distill_rejects_invalid_slug(genesis_substrate: Path) -> None:
    _seed_integrated(genesis_substrate, n=1)
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="invalid distill slug"):
        distill_proposal(ctx=ctx, slug="Has Spaces")


def test_distill_refuses_existing(genesis_substrate: Path) -> None:
    _seed_integrated(genesis_substrate, n=1)
    ctx = _mk_ctx(genesis_substrate)
    distill_proposal(ctx=ctx, slug="foo")
    with pytest.raises(ContractError, match="already exists"):
        distill_proposal(ctx=ctx, slug="foo")


def test_distill_refuses_when_no_integrated(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(ContractError, match="no integrated"):
        distill_proposal(ctx=ctx, slug="empty")


def test_distill_with_explicit_sources(genesis_substrate: Path) -> None:
    _seed_integrated(genesis_substrate, n=2)
    ctx = _mk_ctx(genesis_substrate)
    # Pick one integrated file explicitly.
    integrated = sorted((genesis_substrate / "notes" / "integrated").glob("n_*.md"))
    rel = str(integrated[0].relative_to(genesis_substrate)).replace("\\", "/")
    target = distill_proposal(ctx=ctx, slug="explicit", sources=[rel])
    note = parse_note(target.read_text(encoding="utf-8"))
    assert note.frontmatter["sources"] == [rel]


def test_distill_explicit_source_missing_raises(
    genesis_substrate: Path,
) -> None:
    _seed_integrated(genesis_substrate, n=1)
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(ContractError, match="missing"):
        distill_proposal(ctx=ctx, slug="miss", sources=["notes/nope.md"])


def test_distill_rejects_escaping_source(genesis_substrate: Path) -> None:
    _seed_integrated(genesis_substrate, n=1)
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(ContractError, match="escapes substrate"):
        distill_proposal(ctx=ctx, slug="esc", sources=["../outside.md"])


def test_run_handler(genesis_substrate: Path) -> None:
    _seed_integrated(genesis_substrate, n=1)
    ctx = _mk_ctx(genesis_substrate)
    result = run({"slug": "handler-slug"}, ctx=ctx)
    assert result.exit_code == 0
    assert Path(result.payload["path"]).is_file()


def test_run_missing_slug(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="requires a slug"):
        run({}, ctx=ctx)
