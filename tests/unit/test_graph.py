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


# ---- Python file scanning tests (mycelium network) ----


@pytest.fixture
def py_project(tmp_path):
    """Myco project with src/myco/*.py files referencing substrate docs."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n  contract_version: 'v0.36.0'\n  entry_point: MYCO.md\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "log.md").write_text("# Log\n")
    (tmp_path / "notes").mkdir()

    # docs with a real file
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "architecture.md").write_text("# Architecture\n")
    (tmp_path / "docs" / "agent_protocol.md").write_text("# Agent Protocol\n")

    # wiki
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "design-decisions.md").write_text("# Design Decisions\n")

    # src/myco with Python files containing mycelium references
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "myco").mkdir()

    (tmp_path / "src" / "myco" / "lint.py").write_text(
        '# Canon SSoT: _canon.yaml\n'
        '# Architecture: docs/architecture.md\n'
        '# Design decisions: wiki/design-decisions.md\n'
        'def check(): pass\n'
    )

    (tmp_path / "src" / "myco" / "notes.py").write_text(
        '# Contract: docs/agent_protocol.md\n'
        'ENTRY = "MYCO.md"\n'
        'def eat(): pass\n'
    )

    return tmp_path


def test_extract_links_py_comment_refs(py_project):
    """Python comment references to substrate files are extracted."""
    from myco.graph import extract_links_py

    lint_py = py_project / "src" / "myco" / "lint.py"
    links = extract_links_py(lint_py, py_project)

    assert "_canon.yaml" in links
    assert "docs/architecture.md" in links
    assert "wiki/design-decisions.md" in links


def test_extract_links_py_string_refs(py_project):
    """Python string references like MYCO.md are extracted."""
    from myco.graph import extract_links_py

    notes_py = py_project / "src" / "myco" / "notes.py"
    links = extract_links_py(notes_py, py_project)

    assert "docs/agent_protocol.md" in links
    assert "MYCO.md" in links


def test_py_files_in_graph(py_project):
    """Python files appear as nodes in the link graph."""
    from myco.graph import build_link_graph

    graph = build_link_graph(py_project)

    assert "src/myco/lint.py" in graph
    assert "src/myco/notes.py" in graph


def test_py_forward_links(py_project):
    """Python file forward links point to the docs they reference."""
    from myco.graph import build_link_graph

    graph = build_link_graph(py_project)

    lint_fwd = graph["src/myco/lint.py"]["forward"]
    assert "docs/architecture.md" in lint_fwd
    assert "_canon.yaml" in lint_fwd


def test_py_backlinks(py_project):
    """Docs referenced by Python files show those .py files in backlinks."""
    from myco.graph import build_link_graph

    graph = build_link_graph(py_project)

    arch_back = graph["docs/architecture.md"]["backlinks"]
    assert "src/myco/lint.py" in arch_back

    proto_back = graph["docs/agent_protocol.md"]["backlinks"]
    assert "src/myco/notes.py" in proto_back


def test_py_files_not_orphans(py_project):
    """Python files are never reported as orphans (code is infrastructure)."""
    from myco.graph import build_link_graph, find_orphans

    graph = build_link_graph(py_project)
    orphans = find_orphans(graph)

    for o in orphans:
        assert not o.endswith(".py"), f"Python file {o} should not be an orphan"


def test_py_scan_does_not_break_md(py_project):
    """Adding .py scanning does not interfere with existing .md link extraction."""
    from myco.graph import build_link_graph

    # Add a markdown cross-reference
    (py_project / "docs" / "architecture.md").write_text(
        "# Architecture\n\nSee [protocol](agent_protocol.md) for details.\n"
    )

    graph = build_link_graph(py_project)

    # .md -> .md link still works
    assert "docs/agent_protocol.md" in graph["docs/architecture.md"]["forward"]
    # .py -> .md link also works
    assert "docs/architecture.md" in graph["src/myco/lint.py"]["forward"]
