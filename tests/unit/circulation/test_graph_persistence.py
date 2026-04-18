"""Tests for graph persistence under ``.myco_state/graph.json``.

Covers the v0.5.5 MAJOR-J cache contract:

- persist + load roundtrip,
- fingerprint drift (canon edit) triggers a rebuild,
- corrupt JSON falls through to a rebuild,
- ``use_cache=False`` always rebuilds without touching the cache.
"""

from __future__ import annotations

import json
from pathlib import Path

from myco.circulation.graph import (
    GRAPH_CACHE_SCHEMA,
    Edge,
    Graph,
    _canon_fingerprint,
    build_graph,
    invalidate_graph_cache,
    load_persisted_graph,
    persist_graph,
)
from myco.core.context import MycoContext


def test_persist_and_load_roundtrip(seeded_substrate: Path) -> None:
    graph = Graph(
        nodes=frozenset({"_canon.yaml", "notes/r.md"}),
        edges=(
            Edge(src="notes/r.md", dst="_canon.yaml", kind="note_ref"),
        ),
    )
    cache = seeded_substrate / ".myco_state" / "graph.json"
    persist_graph(graph, cache, fingerprint="deadbeef")

    assert cache.is_file()
    payload = json.loads(cache.read_text(encoding="utf-8"))
    assert payload["schema"] == GRAPH_CACHE_SCHEMA
    assert payload["canon_fingerprint"] == "deadbeef"
    assert "_canon.yaml" in payload["nodes"]
    assert "notes/r.md" in payload["nodes"]

    loaded = load_persisted_graph(cache)
    assert loaded is not None
    loaded_graph, fp = loaded
    assert fp == "deadbeef"
    assert loaded_graph.nodes == graph.nodes
    # Edge tuple roundtrip — compare set-of-tuples since order-independence
    # matters here (the persister sorts nodes but edge order is preserved).
    assert {(e.src, e.dst, e.kind) for e in loaded_graph.edges} == {
        (e.src, e.dst, e.kind) for e in graph.edges
    }


def test_build_graph_writes_cache_on_first_call(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    cache = seeded_substrate / ".myco_state" / "graph.json"
    assert not cache.exists()
    build_graph(ctx)
    assert cache.is_file()
    payload = json.loads(cache.read_text(encoding="utf-8"))
    assert payload["schema"] == GRAPH_CACHE_SCHEMA


def test_second_call_reuses_cache(seeded_substrate: Path) -> None:
    # After a cache write, a canon-identical second call must use
    # the cache — we prove it by pre-seeding a sentinel cache with
    # extra nodes that the real scan would never produce.
    ctx = MycoContext.for_testing(root=seeded_substrate)
    fp = _canon_fingerprint(ctx.substrate)
    sentinel_graph = Graph(
        nodes=frozenset({"_canon.yaml", "synthetic/sentinel.md"}),
        edges=(),
    )
    persist_graph(
        sentinel_graph,
        seeded_substrate / ".myco_state" / "graph.json",
        fingerprint=fp,
    )

    g = build_graph(ctx)
    # The synthetic node can only have come from the cache.
    assert "synthetic/sentinel.md" in g.nodes


def test_fingerprint_change_invalidates_cache(
    seeded_substrate: Path,
) -> None:
    # First build to populate the cache. Then edit the canon so the
    # fingerprint changes; the next build must rebuild (not serve
    # the stale sentinel).
    ctx = MycoContext.for_testing(root=seeded_substrate)
    build_graph(ctx)

    # Overwrite the cache with a sentinel that only the cache could
    # produce, keyed to the CURRENT fingerprint.
    fp_before = _canon_fingerprint(ctx.substrate)
    cache = seeded_substrate / ".myco_state" / "graph.json"
    persist_graph(
        Graph(
            nodes=frozenset({"synthetic/only.md"}),
            edges=(),
        ),
        cache,
        fingerprint=fp_before,
    )

    # Mutate canon → new fingerprint → cache must be ignored.
    canon_path = seeded_substrate / "_canon.yaml"
    canon_path.write_text(
        canon_path.read_text(encoding="utf-8") + "\nextra: true\n",
        encoding="utf-8",
    )
    # Reload the substrate to pick up the canon change for this ctx.
    ctx2 = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx2)
    # Rebuild ran — the sentinel node is gone, real canon node is back.
    assert "synthetic/only.md" not in g.nodes
    assert "_canon.yaml" in g.nodes
    # And the cache now matches the NEW fingerprint.
    loaded = load_persisted_graph(cache)
    assert loaded is not None
    _, fp_after = loaded
    assert fp_after != fp_before


def test_corrupt_json_triggers_rebuild(seeded_substrate: Path) -> None:
    cache = seeded_substrate / ".myco_state" / "graph.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("not-json{{{", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    # Must not raise.
    g = build_graph(ctx)
    # The rebuild rewrites a valid cache.
    payload = json.loads(cache.read_text(encoding="utf-8"))
    assert payload["schema"] == GRAPH_CACHE_SCHEMA
    # Graph is coherent — canon node at minimum.
    assert "_canon.yaml" in g.nodes


def test_wrong_schema_triggers_rebuild(seeded_substrate: Path) -> None:
    cache = seeded_substrate / ".myco_state" / "graph.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {
                "schema": "999",
                "canon_fingerprint": "x",
                "nodes": ["synthetic.md"],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx)
    # Rebuilt — the synthetic node does not survive.
    assert "synthetic.md" not in g.nodes


def test_use_cache_false_always_rebuilds(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    cache = seeded_substrate / ".myco_state" / "graph.json"

    # Pre-populate a stale cache with a sentinel node matching the
    # current fingerprint.
    fp = _canon_fingerprint(ctx.substrate)
    persist_graph(
        Graph(
            nodes=frozenset({"synthetic/should-not-load.md"}),
            edges=(),
        ),
        cache,
        fingerprint=fp,
    )

    g = build_graph(ctx, use_cache=False)
    # Cache was ignored — real scan produced _canon.yaml, not the sentinel.
    assert "synthetic/should-not-load.md" not in g.nodes
    assert "_canon.yaml" in g.nodes
    # And the cache was not rewritten either (unchanged sentinel).
    loaded = load_persisted_graph(cache)
    assert loaded is not None
    cached_graph, _ = loaded
    assert "synthetic/should-not-load.md" in cached_graph.nodes


def test_invalidate_graph_cache_removes_file(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    build_graph(ctx)
    cache = seeded_substrate / ".myco_state" / "graph.json"
    assert cache.is_file()

    removed = invalidate_graph_cache(ctx.substrate)
    assert removed is True
    assert not cache.exists()

    # Second call returns False (nothing to remove).
    removed_again = invalidate_graph_cache(ctx.substrate)
    assert removed_again is False


def test_load_persisted_graph_returns_none_for_missing(
    tmp_path: Path,
) -> None:
    assert load_persisted_graph(tmp_path / "nope.json") is None


def test_persist_graph_creates_state_dir(tmp_path: Path) -> None:
    # ``.myco_state`` dir may not exist yet on fresh substrates —
    # ``persist_graph`` must create it.
    cache = tmp_path / ".myco_state" / "graph.json"
    assert not cache.parent.exists()
    persist_graph(
        Graph(nodes=frozenset({"_canon.yaml"}), edges=()),
        cache,
        fingerprint="abc",
    )
    assert cache.is_file()


def test_persisted_graph_includes_generated_at(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    build_graph(ctx)
    payload = json.loads(
        (seeded_substrate / ".myco_state" / "graph.json").read_text(
            encoding="utf-8"
        )
    )
    assert "generated_at" in payload
    assert payload["generated_at"].endswith("Z")
