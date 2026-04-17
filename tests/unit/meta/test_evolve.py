"""Tests for ``myco.meta.evolve``."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError
from myco.meta.evolve import run


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _well_formed_body() -> str:
    """A proposal doc that should pass every gate."""
    return textwrap.dedent(
        """\
        ---
        type: proposal
        title: Schema Forward Compat
        date: 2026-04-17
        ---

        # Schema Forward Compat — Craft

        ## Round 1 — 主张

        Myco must treat unknown canon schema versions as warnings, not
        errors, so that "You never migrate again" stands as a load-
        bearing claim. An older kernel reading a newer canon should
        emit a UserWarning and proceed best-effort; a newer kernel
        reading an older canon uses the schema_upgraders chain. This
        is the single code-level change that makes the README claim
        tenable rather than aspirational.

        ## Round 2 — 修正

        The gate flips from `raise CanonSchemaError` to
        `warnings.warn(UserWarning)`; a new `schema_upgraders: dict`
        is registered as the forward-compat hook. The existing
        extras-preservation already handles unknown top-level keys.
        The test asserting `raises` flips to `warns`.

        ## Round 3 — 反思

        Shipping the hook with no concrete v1→v2 upgrader registered
        is deliberate — infrastructure only, no UI debt. When schema
        v2 lands, that release introduces its own upgrader entry.
        """
    )


def _write_proposal(root: Path, body: str, *, name: str = "p.md") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    target = root / name
    target.write_text(body, encoding="utf-8")
    return target


def test_requires_proposal_arg(seeded_substrate: Path) -> None:
    ctx = _ctx(seeded_substrate)
    with pytest.raises(UsageError, match="--proposal"):
        run({}, ctx=ctx)


def test_missing_file_raises(seeded_substrate: Path) -> None:
    ctx = _ctx(seeded_substrate)
    with pytest.raises(UsageError, match="not found"):
        run({"proposal": "nope.md"}, ctx=ctx)


def test_well_formed_proposal_passes(seeded_substrate: Path) -> None:
    path = _write_proposal(seeded_substrate, _well_formed_body())
    ctx = _ctx(seeded_substrate)
    r = run({"proposal": path}, ctx=ctx)
    assert r.exit_code == 0
    assert r.payload["verdict"] == "pass"
    assert r.payload["violations"] == []
    assert r.payload["round_count"] >= 3


def test_missing_frontmatter_type_fails(seeded_substrate: Path) -> None:
    body = _well_formed_body().replace("type: proposal", "type: random")
    path = _write_proposal(seeded_substrate, body)
    ctx = _ctx(seeded_substrate)
    r = run({"proposal": path}, ctx=ctx)
    assert r.exit_code == 1
    gates = {v["gate"] for v in r.payload["violations"]}
    assert "G1_frontmatter_type" in gates


def test_short_body_fails(seeded_substrate: Path) -> None:
    body = textwrap.dedent(
        """\
        ---
        type: proposal
        title: Too short
        ---

        ## Round 1
        tiny

        ## Round 2
        also tiny
        """
    )
    path = _write_proposal(seeded_substrate, body)
    ctx = _ctx(seeded_substrate)
    r = run({"proposal": path}, ctx=ctx)
    assert r.exit_code == 1
    gates = {v["gate"] for v in r.payload["violations"]}
    assert "G3_body_min" in gates


def test_one_round_fails(seeded_substrate: Path) -> None:
    body = textwrap.dedent(
        """\
        ---
        type: proposal
        title: One round only
        ---

        ## Round 1 — Claim

        """
    ) + ("padding line.\n" * 400)
    path = _write_proposal(seeded_substrate, body)
    ctx = _ctx(seeded_substrate)
    r = run({"proposal": path}, ctx=ctx)
    assert r.exit_code == 1
    gates = {v["gate"] for v in r.payload["violations"]}
    assert "G4_round_count" in gates


def test_bad_frontmatter_yaml_raises(seeded_substrate: Path) -> None:
    body = "---\ntype: proposal\n: ungood\n---\n\nbody\n"
    path = _write_proposal(seeded_substrate, body)
    ctx = _ctx(seeded_substrate)
    with pytest.raises(ContractError, match="frontmatter"):
        run({"proposal": path}, ctx=ctx)


def test_accepts_type_craft_alias(seeded_substrate: Path) -> None:
    body = _well_formed_body().replace("type: proposal", "type: craft")
    path = _write_proposal(seeded_substrate, body)
    ctx = _ctx(seeded_substrate)
    r = run({"proposal": path}, ctx=ctx)
    assert r.exit_code == 0
