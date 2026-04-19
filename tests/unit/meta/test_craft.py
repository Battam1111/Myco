"""Tests for ``myco.meta.craft``."""

from __future__ import annotations

from pathlib import Path

import pytest
from myco.meta.craft import _slugify, _title_case, run

from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_slugify_happy_paths() -> None:
    assert _slugify("schema forward compat") == "schema_forward_compat"
    assert _slugify("  Greenfield Rewrite  ") == "greenfield_rewrite"
    assert _slugify("v0_5_0 audit") == "v0_5_0_audit"
    assert _slugify("Simple") == "simple"


def test_slugify_rejects_digit_lead() -> None:
    with pytest.raises(UsageError):
        _slugify("123 topic")


def test_slugify_rejects_empty() -> None:
    with pytest.raises(UsageError):
        _slugify("   ")


def test_title_case() -> None:
    assert _title_case("schema_forward_compat") == "Schema Forward Compat"


def test_run_writes_dated_craft_doc(seeded_substrate: Path) -> None:
    ctx = _ctx(seeded_substrate)
    r = run({"topic": "Schema Forward Compat", "date": "2026-04-17"}, ctx=ctx)
    assert r.exit_code == 0
    rel = r.payload["path"]
    assert rel.endswith("schema_forward_compat_craft_2026-04-17.md")
    target = seeded_substrate / rel
    assert target.is_file()
    body = target.read_text(encoding="utf-8")
    # Frontmatter is present and populated
    assert body.startswith("---\n")
    assert "topic: Schema Forward Compat" in body
    assert "slug: schema_forward_compat" in body
    assert "date: 2026-04-17" in body
    assert "kind: design" in body
    # Body has the three rounds as required sections
    assert "## Round 1 — 主张" in body
    assert "## Round 2 — 修正" in body
    assert "## Round 3 — 反思" in body


def test_run_refuses_overwrite(seeded_substrate: Path) -> None:
    ctx = _ctx(seeded_substrate)
    run({"topic": "alpha", "date": "2026-04-17"}, ctx=ctx)
    with pytest.raises(ContractError, match="refusing to overwrite"):
        run({"topic": "alpha", "date": "2026-04-17"}, ctx=ctx)


def test_run_requires_topic(seeded_substrate: Path) -> None:
    ctx = _ctx(seeded_substrate)
    with pytest.raises(UsageError, match="--topic is required"):
        run({}, ctx=ctx)


def test_run_custom_kind(seeded_substrate: Path) -> None:
    ctx = _ctx(seeded_substrate)
    r = run({"topic": "beta", "kind": "audit", "date": "2026-04-17"}, ctx=ctx)
    body = (seeded_substrate / r.payload["path"]).read_text(encoding="utf-8")
    assert "kind: audit" in body
