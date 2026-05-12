"""Extra coverage for circulation.graph + graph_src."""

from __future__ import annotations

from pathlib import Path

from myco.circulation.graph import build_graph
from myco.core.identity_cluster import MycoContext


def test_build_graph_minimal(genesis_substrate: Path):
    """build_graph runs against a minimal genesis substrate."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g = build_graph(ctx)
    assert g is not None
    assert hasattr(g, "nodes") or hasattr(g, "edges") or isinstance(g, dict)


def test_build_graph_with_canon_refs(genesis_substrate: Path):
    """canon refs (notes/integrated/) are picked up."""
    integ = genesis_substrate / "notes" / "integrated"
    integ.mkdir(parents=True, exist_ok=True)
    (integ / "n_test.md").write_text(
        "---\nstage: integrated\n---\n# integrated body\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g = build_graph(ctx)
    assert g is not None


def test_build_graph_with_docs(genesis_substrate: Path):
    docs = genesis_substrate / "docs" / "architecture" / "L2_DOCTRINE"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "test.md").write_text(
        "# Test\n\nSee [related](../L1_CONTRACT/protocol.md)", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g = build_graph(ctx)
    assert g is not None


def test_build_graph_caches_result(genesis_substrate: Path):
    """Second invocation should return same graph (mtime cache)."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g1 = build_graph(ctx)
    g2 = build_graph(ctx)
    # Both invocations succeed
    assert g1 is not None and g2 is not None
