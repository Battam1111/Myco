"""Full coverage tests for ``ingestion.intake`` (v0.6.0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.identity_cluster import MycoContext, MycoError
from myco.ingestion.curate_cluster import (
    intake_directory,
)
from myco.ingestion.curate_cluster import (
    intake_run as run,
)
from myco.ingestion.curate_cluster import (
    intake_run_cli as run_cli,
)


def test_intake_path_not_found(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    with pytest.raises(MycoError, match="not found"):
        intake_directory(ctx, "/nonexistent/path")


def test_intake_path_is_file(tmp_path: Path, genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    f = tmp_path / "file.txt"
    f.write_text("not a dir", encoding="utf-8")
    with pytest.raises(MycoError, match="not a directory"):
        intake_directory(ctx, str(f))


def test_intake_relative_path_resolves_to_substrate(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    sub = genesis_substrate / "input"
    sub.mkdir()
    out = intake_directory(ctx, "input")
    assert out["exit_code"] == 0
    assert out["ingested"] == 0


def test_intake_dry_run_does_not_write(tmp_path: Path, genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "file.txt").write_text("hello", encoding="utf-8")
    out = intake_directory(ctx, str(inp), dry_run=True)
    assert out["dry_run"] is True
    assert out["ingested"] == 1


def test_intake_actually_ingests(tmp_path: Path, genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "a.md").write_text("# a", encoding="utf-8")
    (inp / "b.md").write_text("# b", encoding="utf-8")
    out = intake_directory(ctx, str(inp))
    assert out["ingested"] == 2
    raw_dir = genesis_substrate / "notes" / "raw"
    assert len(list(raw_dir.glob("*.md"))) >= 2


def test_intake_filter_pattern(tmp_path: Path, genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "a.md").write_text("# a", encoding="utf-8")
    (inp / "b.txt").write_text("b body", encoding="utf-8")
    out = intake_directory(ctx, str(inp), filter_pattern=r"\.md$")
    # Only the .md file matches the filter
    assert out["ingested"] == 1


def test_intake_max_count(tmp_path: Path, genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    for i in range(5):
        (inp / f"f{i}.md").write_text(f"# {i}", encoding="utf-8")
    out = intake_directory(ctx, str(inp), max_count=2)
    assert out["ingested"] == 2


def test_intake_bad_filter_pattern_raises(tmp_path: Path, genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "a.md").write_text("# a", encoding="utf-8")
    with pytest.raises(MycoError, match="bad --filter"):
        intake_directory(ctx, str(inp), filter_pattern=r"[invalid")


def test_intake_run_via_dispatcher(tmp_path: Path, genesis_substrate: Path):
    """Standard verb-handler signature: run(args, *, ctx) -> Result."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "x.md").write_text("# x", encoding="utf-8")
    result = run({"path": str(inp)}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["ingested"] == 1


def test_intake_run_missing_path_raises():
    from types import SimpleNamespace

    ctx = SimpleNamespace(substrate=SimpleNamespace(root=Path(".")))
    with pytest.raises(MycoError, match="--path is required"):
        run({}, ctx=ctx)  # type: ignore[arg-type]


def test_intake_run_with_filter_and_max(tmp_path: Path, genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    for i in range(5):
        (inp / f"f{i}.md").write_text(f"# {i}", encoding="utf-8")
    result = run(
        {"path": str(inp), "filter": r"f[0-2]\.md$", "max": 2},
        ctx=ctx,
    )
    assert result.exit_code == 0
    assert result.payload["ingested"] == 2


def test_intake_run_with_string_max(tmp_path: Path, genesis_substrate: Path):
    """Test _as_int_or_none str-coercion path."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "a.md").write_text("# a", encoding="utf-8")
    result = run({"path": str(inp), "max": "1"}, ctx=ctx)
    assert result.exit_code == 0


def test_intake_run_with_invalid_str_max_falls_through(
    tmp_path: Path, genesis_substrate: Path
):
    """Invalid max str → max=None → no cap."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "a.md").write_text("# a", encoding="utf-8")
    result = run({"path": str(inp), "max": "not-a-number"}, ctx=ctx)
    assert result.exit_code == 0


def test_intake_run_cli(tmp_path: Path, genesis_substrate: Path):
    """CLI argparse Namespace adapter."""
    from types import SimpleNamespace

    ctx = MycoContext.for_testing(root=genesis_substrate)
    inp = tmp_path / "inp"
    inp.mkdir()
    (inp / "a.md").write_text("# a", encoding="utf-8")
    args = SimpleNamespace(
        path=str(inp), filter=None, max=None, dry_run=False, strict=False
    )
    result = run_cli(args, ctx)
    assert result.exit_code == 0
