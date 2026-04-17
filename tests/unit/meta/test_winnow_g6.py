"""Regression test for v0.5.4 observation #4 (winnow G6 gate)."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.cycle.winnow import run as winnow_run
from myco.cycle.fruit import run as fruit_run


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_g6_rejects_unfilled_fruit_skeleton(
    genesis_substrate: Path,
) -> None:
    """A freshly-fruited craft skeleton (all TBD placeholders) should
    trip the G6_template_boilerplate gate so ``myco winnow`` does not
    falsely greenlight an unfilled template. Before v0.5.4 the
    skeleton passed every shape gate by construction."""
    ctx = _ctx(genesis_substrate)
    fruited = fruit_run(
        {"topic": "dogfood g6 test", "kind": "audit", "date": "2026-04-17"},
        ctx=ctx,
    )
    path = genesis_substrate / fruited.payload["path"]

    r = winnow_run({"proposal": path}, ctx=ctx)
    gates = {v["gate"] for v in r.payload["violations"]}
    assert "G6_template_boilerplate" in gates, (
        f"freshly-fruited skeleton should trip G6; "
        f"got violations={r.payload['violations']}"
    )
    assert r.payload["verdict"] == "fail"
    assert r.exit_code == 1


def test_g6_passes_filled_craft(
    genesis_substrate: Path,
) -> None:
    """A craft with real content (no dominant boilerplate markers)
    passes G6. This test writes a minimal but non-template body."""
    craft_path = genesis_substrate / "docs" / "primordia" / "real_craft_2026-04-17.md"
    craft_path.parent.mkdir(parents=True, exist_ok=True)
    # Build a body that has >30% non-boilerplate content so G6 passes.
    real_body = """---
type: craft
title: Real craft for G6 test
date: 2026-04-17
---

# Real Craft

Real content: the agent actually thought about this problem and
wrote something substantive instead of leaving the template
placeholders in. The body is deliberately long enough to clear
G3 and G5 while keeping boilerplate lines below the G6 threshold.

## Round 1 — claim

The claim is that v0.5.4 fixes the winnow gate coverage hole. The
shape-only validation does its shape job, but a new G6 gate watches
for bodies that are mostly template-boilerplate markers so an
agent that ran fruit then immediately winnow without doing the
craft work actually gets told to go finish.

## Round 2 — revision

After review we revise: G6 triggers on greater than 70 percent
boilerplate lines, which means a normal three-round craft that
sprinkles a few TBD markers across deliverable lists still passes.
The gate is a signal not a sledgehammer.

## Round 3 — reflection

This closes the hole the dogfood session surfaced. Shipping v0.5.4
with the gate live, the regression test pinning the behavior, and
the contract_changelog entry noting that winnow now rejects
templates in their skeleton state. Agents that want a verdict on
their craft work now actually get one.
"""
    craft_path.write_text(real_body, encoding="utf-8")

    ctx = _ctx(genesis_substrate)
    r = winnow_run({"proposal": craft_path}, ctx=ctx)
    assert r.exit_code == 0, r.payload
    assert r.payload["verdict"] == "pass"
    gates = {v["gate"] for v in r.payload["violations"]}
    assert "G6_template_boilerplate" not in gates
