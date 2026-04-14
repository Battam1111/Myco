"""Tests for ``myco.circulation.graph``."""

from __future__ import annotations

from pathlib import Path

from myco.circulation.graph import build_graph
from myco.core.context import MycoContext
from myco.ingestion.eat import append_note


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_graph_empty_substrate_has_canon_node(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    g = build_graph(ctx)
    assert "_canon.yaml" in g.nodes


def test_graph_picks_up_note_frontmatter_refs(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "ref.md").write_text(
        '---\nstage: raw\nreferences: ["_canon.yaml"]\n---\nbody\n',
        encoding="utf-8",
    )
    g = build_graph(ctx)
    refs = [e for e in g.edges if e.kind == "note_ref"]
    assert any(e.dst == "_canon.yaml" for e in refs)


def test_graph_markdown_links_in_notes(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "linky.md").write_text(
        "---\nstage: raw\n---\nsee [canon](../../_canon.yaml) for details\n",
        encoding="utf-8",
    )
    g = build_graph(ctx)
    md_edges = [e for e in g.edges if e.kind == "markdown_link"]
    assert any(e.dst == "_canon.yaml" for e in md_edges)


def test_graph_skips_links_in_fenced_blocks(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "fenced.md").write_text(
        "---\nstage: raw\n---\n"
        "real: [x](../../_canon.yaml)\n"
        "```\n[fake](../../BOGUS.md)\n```\n",
        encoding="utf-8",
    )
    g = build_graph(ctx)
    md_edges = [e for e in g.edges if e.kind == "markdown_link"]
    dsts = {e.dst for e in md_edges}
    assert "_canon.yaml" in dsts
    assert "BOGUS.md" not in dsts


def test_graph_skips_external_urls(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "external.md").write_text(
        "---\nstage: raw\n---\n[x](https://example.com) and [y](#anchor)\n",
        encoding="utf-8",
    )
    g = build_graph(ctx)
    # No markdown-link edges should be emitted for these.
    md_edges = [
        e
        for e in g.edges
        if e.kind == "markdown_link" and e.src.endswith("external.md")
    ]
    assert md_edges == []


def test_graph_canon_ref_scan(genesis_substrate: Path) -> None:
    # Inject a ``*_ref`` field into canon and rebuild.
    canon = genesis_substrate / "_canon.yaml"
    text = canon.read_text(encoding="utf-8")
    text += "\nextras_ref: MYCO.md\n"
    canon.write_text(text, encoding="utf-8")
    ctx = _mk_ctx(genesis_substrate)
    g = build_graph(ctx)
    canon_edges = [e for e in g.edges if e.kind == "canon_ref"]
    assert any(e.dst == "MYCO.md" for e in canon_edges)


def test_graph_outgoing_incoming(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "a.md").write_text(
        '---\nstage: raw\nreferences: ["_canon.yaml"]\n---\nbody\n',
        encoding="utf-8",
    )
    g = build_graph(ctx)
    outs = g.outgoing("notes/raw/a.md")
    assert any(e.dst == "_canon.yaml" for e in outs)
    ins = g.incoming("_canon.yaml")
    assert any(e.src == "notes/raw/a.md" for e in ins)


def test_graph_records_unresolved_as_dangling_edge(
    genesis_substrate: Path,
) -> None:
    ctx = _mk_ctx(genesis_substrate)
    raw = genesis_substrate / "notes" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "bad.md").write_text(
        "---\nstage: raw\n---\nsee [missing](./nowhere.md)\n",
        encoding="utf-8",
    )
    g = build_graph(ctx)
    md_edges = [
        e
        for e in g.edges
        if e.kind == "markdown_link" and e.src.endswith("bad.md")
    ]
    # Edge is still recorded (dst is relative path that won't exist);
    # perfuse will flag it as dangling.
    assert md_edges


def test_graph_handles_integrated_notes(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="hello")
    g = build_graph(ctx)
    note_nodes = [n for n in g.nodes if n.startswith("notes/raw/")]
    assert note_nodes
