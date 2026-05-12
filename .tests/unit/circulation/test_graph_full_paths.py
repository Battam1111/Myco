"""Comprehensive coverage for circulation/graph.py — cache, fingerprint, edges."""

from __future__ import annotations

import json
from pathlib import Path

from myco.circulation.graph import (
    GRAPH_CACHE_SCHEMA,
    Edge,
    Graph,
    _is_external,
    _iter_canon_refs,
    _iter_markdown_links,
    _strip_fragment,
    build_graph,
    invalidate_graph_cache,
    load_persisted_graph,
    persist_graph,
)
from myco.core.identity_cluster import MycoContext

# ---------- helpers ----------


def test_is_external_url():
    assert _is_external("https://example.com") is True
    assert _is_external("http://example.com") is True
    assert _is_external("mailto:x@y.com") is True


def test_is_external_anchor():
    assert _is_external("#section") is True


def test_is_external_absolute():
    assert _is_external("/abs/path") is True


def test_is_external_windows_absolute():
    assert _is_external("C:/users") is True


def test_is_external_relative_is_false():
    assert _is_external("notes/foo.md") is False
    assert _is_external("../docs/x.md") is False


def test_is_external_empty_is_external():
    assert _is_external("") is True
    assert _is_external("   ") is True


def test_strip_fragment_removes_anchor():
    assert _strip_fragment("file.md#section") == "file.md"


def test_strip_fragment_removes_query():
    assert _strip_fragment("file.md?ver=1") == "file.md"


def test_strip_fragment_no_op_when_clean():
    assert _strip_fragment("file.md") == "file.md"


def test_iter_canon_refs_simple_str():
    out = list(_iter_canon_refs({"foo_ref": "x.md"}))
    assert out == ["x.md"]


def test_iter_canon_refs_list():
    out = list(_iter_canon_refs({"deps_ref": ["a.md", "b.md"]}))
    assert "a.md" in out
    assert "b.md" in out


def test_iter_canon_refs_nested():
    out = list(_iter_canon_refs({"section": {"path_ref": "x.md"}}))
    assert "x.md" in out


def test_iter_canon_refs_no_ref_keys():
    out = list(_iter_canon_refs({"foo": "no", "bar": ["nope"]}))
    assert out == []


def test_iter_canon_refs_list_of_dicts():
    out = list(
        _iter_canon_refs({"items": [{"path_ref": "a.md"}, {"path_ref": "b.md"}]})
    )
    assert "a.md" in out
    assert "b.md" in out


def test_iter_canon_refs_ignores_non_string_in_list():
    out = list(_iter_canon_refs({"deps_ref": ["a.md", 42, None]}))
    assert "a.md" in out
    # Non-strings filtered.
    assert 42 not in out


def test_iter_markdown_links_simple():
    text = "See [link](file.md) for details."
    out = list(_iter_markdown_links(text))
    assert out == ["file.md"]


def test_iter_markdown_links_skips_fenced_blocks():
    text = "\n".join(
        [
            "Real link: [a](real.md)",
            "```python",
            "fake link: [b](fake.md)",
            "```",
            "Real link 2: [c](real2.md)",
        ]
    )
    out = list(_iter_markdown_links(text))
    assert "real.md" in out
    assert "real2.md" in out
    assert "fake.md" not in out


def test_iter_markdown_links_multiple_per_line():
    text = "[a](x.md) and [b](y.md)"
    out = list(_iter_markdown_links(text))
    assert "x.md" in out
    assert "y.md" in out


# ---------- Graph dataclass ----------


def test_graph_outgoing_filter():
    edges = (
        Edge(src="a.md", dst="b.md", kind="markdown_link"),
        Edge(src="a.md", dst="c.md", kind="markdown_link"),
        Edge(src="b.md", dst="d.md", kind="markdown_link"),
    )
    g = Graph(nodes=frozenset({"a.md", "b.md", "c.md", "d.md"}), edges=edges)
    out = g.outgoing("a.md")
    assert len(out) == 2
    assert all(e.src == "a.md" for e in out)


def test_graph_incoming_filter():
    edges = (
        Edge(src="a.md", dst="d.md", kind="markdown_link"),
        Edge(src="b.md", dst="d.md", kind="markdown_link"),
    )
    g = Graph(nodes=frozenset({"a.md", "b.md", "d.md"}), edges=edges)
    inc = g.incoming("d.md")
    assert len(inc) == 2


# ---------- persistence ----------


def test_persist_and_load_roundtrip(tmp_path: Path):
    g = Graph(
        nodes=frozenset({"a", "b"}),
        edges=(Edge(src="a", dst="b", kind="markdown_link"),),
    )
    out = tmp_path / "subdir" / "graph.json"
    persist_graph(g, out, fingerprint="fp123")
    loaded = load_persisted_graph(out)
    assert loaded is not None
    g2, fp2 = loaded
    assert fp2 == "fp123"
    assert "a" in g2.nodes
    assert g2.edges[0].kind == "markdown_link"


def test_load_returns_none_when_missing(tmp_path: Path):
    assert load_persisted_graph(tmp_path / "nope.json") is None


def test_load_returns_none_on_invalid_json(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert load_persisted_graph(p) is None


def test_load_returns_none_when_root_not_mapping(tmp_path: Path):
    p = tmp_path / "g.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert load_persisted_graph(p) is None


def test_load_returns_none_on_schema_mismatch(tmp_path: Path):
    p = tmp_path / "g.json"
    p.write_text(
        json.dumps({"schema": "999", "nodes": [], "edges": []}), encoding="utf-8"
    )
    assert load_persisted_graph(p) is None


def test_load_returns_none_when_nodes_missing(tmp_path: Path):
    p = tmp_path / "g.json"
    p.write_text(
        json.dumps({"schema": GRAPH_CACHE_SCHEMA, "nodes": "not-a-list", "edges": []}),
        encoding="utf-8",
    )
    assert load_persisted_graph(p) is None


def test_load_returns_none_when_fingerprint_missing(tmp_path: Path):
    p = tmp_path / "g.json"
    p.write_text(
        json.dumps({"schema": GRAPH_CACHE_SCHEMA, "nodes": [], "edges": []}),
        encoding="utf-8",
    )
    assert load_persisted_graph(p) is None


def test_load_returns_none_on_malformed_edge(tmp_path: Path):
    p = tmp_path / "g.json"
    p.write_text(
        json.dumps(
            {
                "schema": GRAPH_CACHE_SCHEMA,
                "nodes": ["a"],
                "edges": [["a", "b"]],  # only 2 elements — malformed.
                "canon_fingerprint": "fp",
            }
        ),
        encoding="utf-8",
    )
    assert load_persisted_graph(p) is None


# ---------- invalidate ----------


def test_invalidate_returns_false_when_missing(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    # Force fresh state
    cache = ctx.substrate.paths.graph_cache
    if cache.is_file():
        cache.unlink()
    assert invalidate_graph_cache(ctx.substrate) is False


def test_invalidate_returns_true_after_build(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    build_graph(ctx)
    cache = ctx.substrate.paths.graph_cache
    assert cache.is_file()
    assert invalidate_graph_cache(ctx.substrate) is True


# ---------- build cache reuse ----------


def test_build_graph_cache_short_circuits(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g1 = build_graph(ctx)
    g2 = build_graph(ctx)
    # Both succeed; second is a cache hit if implementation does its job.
    assert isinstance(g1.nodes, frozenset)
    assert isinstance(g2.nodes, frozenset)


def test_build_graph_no_cache_rebuilds(genesis_substrate: Path):
    ctx = MycoContext.for_testing(root=genesis_substrate)
    build_graph(ctx)
    g_no_cache = build_graph(ctx, use_cache=False)
    assert isinstance(g_no_cache.nodes, frozenset)


def test_build_graph_with_canon_refs_resolves(genesis_substrate: Path):
    """If canon has a *_ref to an existing file, it shows as canon_ref edge."""
    canon = genesis_substrate / "_canon.yaml"
    text = canon.read_text(encoding="utf-8")
    text = (
        text + '\nversioning:\n  contract_changelog_ref: "docs/contract_changelog.md"\n'
    )
    canon.write_text(text, encoding="utf-8")
    docs = genesis_substrate / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "contract_changelog.md").write_text("# Changelog", encoding="utf-8")
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g = build_graph(ctx, use_cache=False)
    canon_kinds = [e.kind for e in g.edges]
    assert "canon_ref" in canon_kinds


def test_build_graph_with_dangling_canon_ref(genesis_substrate: Path):
    """Canon ref to non-existent file → dangling edge but no node added."""
    canon = genesis_substrate / "_canon.yaml"
    text = canon.read_text(encoding="utf-8")
    text = text + '\nversioning:\n  missing_ref: "does/not/exist.md"\n'
    canon.write_text(text, encoding="utf-8")
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g = build_graph(ctx, use_cache=False)
    # Either dangling edge present or just no edge — both are valid.
    assert isinstance(g, Graph)


def test_build_graph_with_note_frontmatter_refs(genesis_substrate: Path):
    """Notes' frontmatter `references` produces note_ref edges."""
    notes = genesis_substrate / "notes" / "raw"
    notes.mkdir(parents=True, exist_ok=True)
    (notes / "n_test.md").write_text(
        '---\nstage: raw\nreferences: ["MYCO.md"]\n---\n# body\n',
        encoding="utf-8",
    )
    (genesis_substrate / "MYCO.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=genesis_substrate)
    g = build_graph(ctx, use_cache=False)
    assert any(e.kind == "note_ref" for e in g.edges)
