"""Comprehensive coverage for circulation/traverse.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.circulation.graph import Edge, Graph
from myco.circulation.traverse import (
    _count_src_nodes,
    _dangling,
    _edge_in_scope,
    _in_scope,
    _orphans,
    _proposals,
    perfuse,
    run,
)
from myco.core.context import MycoContext
from myco.core.errors import UsageError


# ---------- _in_scope ----------


def test_in_scope_all():
    assert _in_scope("anything.md", "all") is True


def test_in_scope_canon():
    assert _in_scope("_canon.yaml", "canon") is True
    assert _in_scope("notes/x.md", "canon") is False


def test_in_scope_notes():
    assert _in_scope("notes/integrated/x.md", "notes") is True
    assert _in_scope("docs/x.md", "notes") is False


def test_in_scope_docs():
    assert _in_scope("docs/architecture/x.md", "docs") is True
    assert _in_scope("MYCO.md", "docs") is True
    assert _in_scope("notes/x.md", "docs") is False


def test_in_scope_unknown_returns_false():
    assert _in_scope("anything", "weird-scope") is False  # type: ignore[arg-type]


# ---------- _edge_in_scope ----------


def test_edge_in_scope_filters_on_src():
    e = Edge(src="notes/x.md", dst="docs/y.md", kind="markdown_link")
    assert _edge_in_scope(e, "notes") is True
    assert _edge_in_scope(e, "docs") is False


# ---------- _dangling ----------


def test_dangling_finds_missing_targets(tmp_path: Path):
    g = Graph(
        nodes=frozenset({"notes/x.md"}),
        edges=(Edge(src="notes/x.md", dst="docs/missing.md", kind="markdown_link"),),
    )
    out = _dangling(g, tmp_path, "all")
    assert ("notes/x.md", "docs/missing.md") in out


def test_dangling_skips_existing(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "exists.md").write_text("# x", encoding="utf-8")
    g = Graph(
        nodes=frozenset({"notes/x.md", "docs/exists.md"}),
        edges=(Edge(src="notes/x.md", dst="docs/exists.md", kind="markdown_link"),),
    )
    out = _dangling(g, tmp_path, "all")
    assert ("notes/x.md", "docs/exists.md") not in out


def test_dangling_filters_by_scope(tmp_path: Path):
    g = Graph(
        nodes=frozenset({"notes/x.md", "docs/y.md"}),
        edges=(
            Edge(src="notes/x.md", dst="docs/missing1.md", kind="markdown_link"),
            Edge(src="docs/y.md", dst="docs/missing2.md", kind="markdown_link"),
        ),
    )
    out = _dangling(g, tmp_path, "notes")
    # Only the notes/-srced edge counted.
    assert any(s == "notes/x.md" for s, _d in out)
    assert not any(s == "docs/y.md" for s, _d in out)


# ---------- _orphans ----------


def test_orphans_finds_unreferenced_notes():
    g = Graph(
        nodes=frozenset({"notes/integrated/orphan.md", "_canon.yaml"}),
        edges=(),
    )
    out = _orphans(g, "all")
    assert "notes/integrated/orphan.md" in out


def test_orphans_excludes_canon_and_entry():
    g = Graph(
        nodes=frozenset({"_canon.yaml", "MYCO.md"}),
        edges=(),
    )
    assert _orphans(g, "all") == []


def test_orphans_excludes_referenced():
    g = Graph(
        nodes=frozenset({"notes/x.md"}),
        edges=(Edge(src="_canon.yaml", dst="notes/x.md", kind="canon_ref"),),
    )
    assert "notes/x.md" not in _orphans(g, "all")


def test_orphans_filters_by_scope():
    g = Graph(
        nodes=frozenset({"notes/x.md", "docs/y.md"}),
        edges=(),
    )
    out = _orphans(g, "notes")
    assert "notes/x.md" in out
    assert "docs/y.md" not in out


# ---------- _proposals ----------


def test_proposals_orphan_message():
    out = _proposals(orphans=["notes/x.md"], dangling=[])
    assert any("orphan" in p for p in out)


def test_proposals_dangling_message():
    out = _proposals(orphans=[], dangling=[("a.md", "b.md")])
    assert any("dangling" in p for p in out)


# ---------- _count_src_nodes ----------


def test_count_src_nodes_counts_src_prefix():
    g = Graph(
        nodes=frozenset({"src/myco/x.py", "src/myco/y.py", "notes/z.md"}),
        edges=(),
    )
    assert _count_src_nodes(g) == 2


def test_count_src_nodes_zero():
    g = Graph(nodes=frozenset({"notes/x.md"}), edges=())
    assert _count_src_nodes(g) == 0


# ---------- perfuse ----------


def test_perfuse_invalid_scope_raises(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    with pytest.raises(UsageError, match="invalid perfuse scope"):
        perfuse(ctx=ctx, scope="weird")  # type: ignore[arg-type]


def test_perfuse_smoke(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    res = perfuse(ctx=ctx)
    assert res.exit_code == 0
    assert "scope" in res.payload
    assert "orphans" in res.payload
    assert "dangling" in res.payload
    assert "proposals" in res.payload
    assert "node_count" in res.payload
    assert "edge_count" in res.payload
    assert "src_node_count" in res.payload
    assert "cached" in res.payload


def test_perfuse_each_scope(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    for scope in ("all", "canon", "notes", "docs"):
        res = perfuse(ctx=ctx, scope=scope)  # type: ignore[arg-type]
        assert res.payload["scope"] == scope


# ---------- run ----------


def test_run_default_scope_all(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    res = run({}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["scope"] == "all"


def test_run_invalid_scope_raises(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    with pytest.raises(UsageError, match="invalid perfuse scope"):
        run({"scope": "bogus"}, ctx=ctx)


def test_run_dry_run_accepted(genesis_substrate: Path):
    """dry_run is accepted for parity but has no effect."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    res = run({"dry_run": True}, ctx=ctx)
    assert res.exit_code == 0
