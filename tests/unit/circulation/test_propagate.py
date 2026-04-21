"""Tests for ``myco.circulation.propagate``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.circulation.propagate import propagate, run
from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError
from myco.digestion.distill import distill_proposal
from myco.digestion.pipeline import parse_note
from myco.digestion.reflect import reflect
from myco.genesis import bootstrap
from myco.ingestion.eat import append_note


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _seed_src(root: Path, n: int = 2) -> MycoContext:
    ctx = _mk_ctx(root)
    for i in range(n):
        append_note(ctx=ctx, content=f"finding {i}")
    reflect(ctx=ctx)
    return ctx


@pytest.fixture
def dst_substrate(tmp_path: Path) -> Path:
    """A second substrate produced via genesis, to serve as propagate target."""
    dst = tmp_path / "downstream"
    dst.mkdir()
    bootstrap(project_dir=dst, substrate_id="downstream")
    return dst


def test_propagate_integrated_round_trip(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    """v0.5.8 P0 fix: propagate now writes notes/raw/<stem>.md (without
    the ``n_``/``d_`` tier-prefix) so ``digest_one`` can locate the
    file at ``notes/raw/<stem>.md`` after it strips the prefix from
    the note-id. Previously propagate preserved ``n_<stem>.md`` and
    every downstream assimilate failed with UsageError."""
    src_ctx = _seed_src(genesis_substrate, n=2)
    result = propagate(src_ctx=src_ctx, dst_root=dst_substrate, commit="abc1234")
    assert result.exit_code == 0
    assert result.payload["count"] == 2
    inbox = dst_substrate / "notes" / "raw"
    # v0.5.8: stem-only names (prefix stripped) in raw/.
    files = list(inbox.glob("*.md"))
    assert len(files) == 2
    # No n_ prefix at the destination.
    assert not any(f.name.startswith("n_") for f in files)
    # Source-trace frontmatter is stamped.
    note = parse_note(files[0].read_text(encoding="utf-8"))
    assert note.frontmatter["source"].startswith("test-substrate@abc1234")
    assert note.frontmatter["ingest_state"] == "raw"
    assert note.frontmatter["stage"] == "raw"


def test_propagate_unknown_commit_when_none(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    src_ctx = _seed_src(genesis_substrate, n=1)
    result = propagate(src_ctx=src_ctx, dst_root=dst_substrate)
    inbox = dst_substrate / "notes" / "raw"
    # v0.5.8: no n_ prefix at destination.
    candidates = list(inbox.glob("*.md"))
    assert len(candidates) == 1
    note = parse_note(candidates[0].read_text(encoding="utf-8"))
    assert note.frontmatter["source"].endswith("@unknown")
    assert result.payload["commit"] == "unknown"


def test_propagate_dry_run_writes_nothing(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    src_ctx = _seed_src(genesis_substrate, n=1)
    result = propagate(src_ctx=src_ctx, dst_root=dst_substrate, dry_run=True)
    assert result.payload["dry_run"] is True
    inbox = dst_substrate / "notes" / "raw"
    # v0.5.8: prefix stripped in destination raw/.
    assert not list(inbox.glob("*.md"))


def test_propagate_rejects_collision(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    src_ctx = _seed_src(genesis_substrate, n=1)
    propagate(src_ctx=src_ctx, dst_root=dst_substrate)
    # Second run with same source should collide.
    with pytest.raises(ContractError, match="collision"):
        propagate(src_ctx=src_ctx, dst_root=dst_substrate)


def test_propagate_select_both_includes_distilled(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    """v0.5.8: ``d_`` prefix stripped at destination, so the
    distilled source ``distilled/d_doctrine.md`` lands at
    ``notes/raw/doctrine.md``."""
    src_ctx = _seed_src(genesis_substrate, n=2)
    distill_proposal(ctx=src_ctx, slug="doctrine")
    result = propagate(src_ctx=src_ctx, dst_root=dst_substrate, select="both")
    assert result.payload["count"] == 3  # 2 integrated + 1 distilled
    inbox = dst_substrate / "notes" / "raw"
    assert (inbox / "doctrine.md").is_file()


def test_propagate_select_distilled_only(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    src_ctx = _seed_src(genesis_substrate, n=1)
    distill_proposal(ctx=src_ctx, slug="only")
    result = propagate(src_ctx=src_ctx, dst_root=dst_substrate, select="distilled")
    assert result.payload["count"] == 1
    inbox = dst_substrate / "notes" / "raw"
    # v0.5.8: d_ prefix stripped.
    assert (inbox / "only.md").is_file()
    # Integrated prefix would also be stripped, but select=distilled.
    # This double-check keeps the test semantic.
    assert not list(inbox.glob("n_*.md"))
    assert not list(inbox.glob("d_*.md"))


def test_propagate_rejects_bad_select(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    src_ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="invalid propagate select"):
        propagate(
            src_ctx=src_ctx,
            dst_root=dst_substrate,
            select="bogus",  # type: ignore[arg-type]
        )


def test_propagate_rejects_non_substrate_dst(
    genesis_substrate: Path, tmp_path: Path
) -> None:
    src_ctx = _mk_ctx(genesis_substrate)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ContractError, match="not a Myco substrate"):
        propagate(src_ctx=src_ctx, dst_root=empty)


def test_propagate_rejects_major_version_mismatch(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    # Forcibly rewrite dst canon to a different major version. v0.5.8:
    # germinate stamps the live kernel version, so we rewrite to
    # anything with a distinct major.
    import re as _re

    dst_canon = dst_substrate / "_canon.yaml"
    text = dst_canon.read_text(encoding="utf-8")
    text = _re.sub(
        r'contract_version:\s*"[^"]+"',
        'contract_version: "v1.0.0-alpha.1"',
        text,
        count=1,
    )
    text = _re.sub(
        r'synced_contract_version:\s*"[^"]+"',
        'synced_contract_version: "v1.0.0-alpha.1"',
        text,
        count=1,
    )
    dst_canon.write_text(text, encoding="utf-8")
    src_ctx = _seed_src(genesis_substrate, n=1)
    with pytest.raises(ContractError, match="major mismatch"):
        propagate(src_ctx=src_ctx, dst_root=dst_substrate)


def test_propagate_minor_mismatch_warns(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    """v0.5.8: force src+dst to have same major but distinct minor so
    the compat-warning fires regardless of which kernel version
    germinated the fixtures."""
    import re as _re

    dst_canon = dst_substrate / "_canon.yaml"
    text = dst_canon.read_text(encoding="utf-8")
    # Rewrite dst canon to a deliberately-different minor within the
    # same major as whatever the live kernel stamps.
    from myco import __version__ as _myco_version

    parts = _myco_version.split(".")
    major = parts[0]
    bumped_minor = str(int(parts[1]) + 7)  # guarantee a delta
    target_ver = f"v{major}.{bumped_minor}.0"
    text = _re.sub(
        r'contract_version:\s*"[^"]+"',
        f'contract_version: "{target_ver}"',
        text,
        count=1,
    )
    text = _re.sub(
        r'synced_contract_version:\s*"[^"]+"',
        f'synced_contract_version: "{target_ver}"',
        text,
        count=1,
    )
    dst_canon.write_text(text, encoding="utf-8")
    src_ctx = _seed_src(genesis_substrate, n=1)
    result = propagate(src_ctx=src_ctx, dst_root=dst_substrate)
    assert any("minor version mismatch" in w for w in result.payload["compat_warnings"])


def test_propagate_dry_run_and_real_match(
    genesis_substrate: Path, dst_substrate: Path
) -> None:
    from datetime import datetime, timezone

    src_ctx = _seed_src(genesis_substrate, n=2)
    fixed = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
    dry = propagate(src_ctx=src_ctx, dst_root=dst_substrate, dry_run=True, now=fixed)
    real = propagate(src_ctx=src_ctx, dst_root=dst_substrate, dry_run=False, now=fixed)
    assert dry.payload["propagated"] == real.payload["propagated"]


def test_run_handler(genesis_substrate: Path, dst_substrate: Path) -> None:
    src_ctx = _seed_src(genesis_substrate, n=1)
    result = run({"dst": str(dst_substrate), "commit": "xyz"}, ctx=src_ctx)
    assert result.exit_code == 0
    assert result.payload["count"] == 1


def test_run_missing_dst_raises(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="requires a dst"):
        run({}, ctx=ctx)


def test_run_rejects_bad_select(genesis_substrate: Path, dst_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="invalid propagate select"):
        run({"dst": str(dst_substrate), "select": "nope"}, ctx=ctx)
