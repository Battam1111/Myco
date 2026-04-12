"""Unit tests for myco.graph — Wave 47 link graph infrastructure."""

from pathlib import Path

import pytest


@pytest.fixture
def graph_project(tmp_path):
    """Create a minimal Myco project with interconnected files."""
    # _canon.yaml (required for project detection)
    (tmp_path / "_canon.yaml").write_text(
        "system:\n  contract_version: 'v0.36.0'\n  entry_point: MYCO.md\n"
    )

    # MYCO.md links to doc_a.md and wiki/page.md
    (tmp_path / "MYCO.md").write_text(
        "# Myco\n\nSee [Doc A](docs/doc_a.md) and `wiki/page.md` for details.\n"
    )

    # docs/ directory
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "doc_a.md").write_text(
        "# Doc A\n\nReferences [Doc B](doc_b.md) and `MYCO.md`.\n"
    )
    (tmp_path / "docs" / "doc_b.md").write_text(
        "# Doc B\n\nStandalone document.\n"
    )

    # wiki/ directory
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "page.md").write_text(
        "# Wiki Page\n\nSee [Doc A](../docs/doc_a.md) for more.\n"
    )

    # notes/ directory
    (tmp_path / "notes").mkdir()

    # log.md
    (tmp_path / "log.md").write_text("# Log\n")

    return tmp_path


def test_extract_links_markdown(graph_project):
    """Verify markdown links and backtick paths are extracted."""
    from myco.graph import extract_links

    myco_md = graph_project / "MYCO.md"
    links = extract_links(myco_md, graph_project)
    assert "docs/doc_a.md" in links
    assert "wiki/page.md" in links


def test_build_graph_backlinks(graph_project):
    """A→B→C chain: verify A in B's backlinks, B in C's backlinks."""
    from myco.graph import build_link_graph

    graph = build_link_graph(graph_project)

    # MYCO.md links to docs/doc_a.md
    assert "MYCO.md" in graph["docs/doc_a.md"]["backlinks"]

    # docs/doc_a.md links to docs/doc_b.md
    assert "docs/doc_a.md" in graph["docs/doc_b.md"]["backlinks"]


def test_find_orphans(graph_project):
    """Unlinked file detected as orphan; linked files are not."""
    from myco.graph import build_link_graph, find_orphans

    # Add an orphan file
    (graph_project / "docs" / "orphan.md").write_text("# Orphan\nNo one links here.\n")

    graph = build_link_graph(graph_project)
    orphans = find_orphans(graph)

    assert "docs/orphan.md" in orphans
    # doc_a has backlinks from MYCO.md and wiki/page.md — not an orphan
    assert "docs/doc_a.md" not in orphans


def test_find_clusters(graph_project):
    """Two disconnected file pairs produce 2+ clusters."""
    from myco.graph import build_link_graph, find_clusters

    # Add a disconnected pair
    (graph_project / "docs" / "island_x.md").write_text(
        "# Island X\n\nSee [Island Y](island_y.md).\n"
    )
    (graph_project / "docs" / "island_y.md").write_text(
        "# Island Y\n\nSee [Island X](island_x.md).\n"
    )

    graph = build_link_graph(graph_project)
    clusters = find_clusters(graph)

    # Should have at least 2 clusters: the main cluster and the island pair
    assert len(clusters) >= 2

    # Find the island cluster
    island_cluster = None
    for c in clusters:
        if "docs/island_x.md" in c and "docs/island_y.md" in c:
            island_cluster = c
            break
    assert island_cluster is not None, "Island cluster not found"


def test_graph_stats(graph_project):
    """Stats returns expected structure."""
    from myco.graph import build_link_graph, graph_stats

    graph = build_link_graph(graph_project)
    stats = graph_stats(graph)

    assert stats["total_nodes"] > 0
    assert stats["total_edges"] > 0
    assert "hub" in stats
    assert "authority" in stats
    assert stats["cluster_count"] >= 1
