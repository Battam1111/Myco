"""Tests for ``circulation.traverse`` (v0.6.0).

Covers the perfuse → traverse rename + the graph-walk verb.
"""

from __future__ import annotations

from pathlib import Path

from myco.boundary.surface.manifest import dispatch
from myco.core.identity_cluster import MycoContext


def test_traverse_runs_on_genesis_substrate(genesis_substrate: Path):
    """traverse runs end-to-end via the dispatcher."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = dispatch("traverse", {}, ctx=ctx)
    assert result.exit_code < 3
    assert "node_count" in result.payload or "scope" in result.payload


def test_traverse_with_scope_canon(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = dispatch("traverse", {"scope": "canon"}, ctx=ctx)
    assert result.exit_code < 3


def test_traverse_with_scope_notes(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = dispatch("traverse", {"scope": "notes"}, ctx=ctx)
    assert result.exit_code < 3


def test_traverse_with_scope_docs(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = dispatch("traverse", {"scope": "docs"}, ctx=ctx)
    assert result.exit_code < 3


def test_traverse_with_scope_all(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = dispatch("traverse", {"scope": "all"}, ctx=ctx)
    assert result.exit_code < 3
