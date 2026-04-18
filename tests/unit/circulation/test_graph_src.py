"""Tests for ``myco.circulation.graph_src`` (v0.5.5 MAJOR-F).

Covers the AST-based src walker:

- code nodes appear for every ``.py`` under ``src/``,
- ``from myco.X import Y`` and ``import myco.X`` produce import edges
  that resolve to the right file under ``src/``,
- module-docstring doc references produce ``code_doc_ref`` edges,
- stdlib + third-party imports do not produce edges,
- a syntax-broken ``.py`` never crashes the walk.

We use ``seeded_substrate`` plus a handcrafted ``src/myco/...`` tree
per test. ``build_graph(ctx, use_cache=False)`` keeps each test
independent of the persisted cache.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.circulation.graph import Edge, build_graph
from myco.circulation.graph_src import walk_src_graph
from myco.core.context import MycoContext


def _seed_src(root: Path, relpath: str, body: str) -> Path:
    """Write ``body`` to ``root/src/<relpath>`` and return the path."""
    target = root / "src" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(body), encoding="utf-8")
    return target


def test_graph_covers_py_files(seeded_substrate: Path) -> None:
    # Two internal modules, one imports the other — both should be
    # nodes, and the import edge should land.
    _seed_src(
        seeded_substrate,
        "myco/foo.py",
        '''
        """foo module."""
        VALUE = 1
        ''',
    )
    _seed_src(
        seeded_substrate,
        "myco/bar.py",
        '''
        """bar module."""
        from myco.foo import VALUE
        ''',
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx, use_cache=False)
    assert "src/myco/foo.py" in g.nodes
    assert "src/myco/bar.py" in g.nodes
    import_edges = [e for e in g.edges if e.kind == "import"]
    assert any(
        e.src == "src/myco/bar.py" and e.dst == "src/myco/foo.py"
        for e in import_edges
    )


def test_graph_resolves_from_import(seeded_substrate: Path) -> None:
    # ``from myco.core import canon`` should resolve to a file path
    # pointing at ``src/myco/core/canon.py``.
    _seed_src(
        seeded_substrate,
        "myco/core/canon.py",
        '''
        """canon module."""
        VALUE = 1
        ''',
    )
    _seed_src(
        seeded_substrate,
        "myco/core/__init__.py",
        '''
        """core package."""
        ''',
    )
    _seed_src(
        seeded_substrate,
        "myco/caller.py",
        '''
        """caller."""
        from myco.core import canon
        ''',
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx, use_cache=False)
    import_edges = [e for e in g.edges if e.kind == "import"]
    # Expect an edge to the canon submodule file specifically.
    assert any(
        e.src == "src/myco/caller.py" and e.dst == "src/myco/core/canon.py"
        for e in import_edges
    )


def test_graph_docstring_doc_reference(seeded_substrate: Path) -> None:
    # A module docstring that mentions ``docs/foo.md`` produces a
    # ``code_doc_ref`` edge. Whether the target file exists is
    # orthogonal — we still emit the edge so SE1 can surface
    # dangling doctrine references.
    _seed_src(
        seeded_substrate,
        "myco/handler.py",
        '''
        """Handler module.

        Governing doctrine: ``docs/architecture/L2_DOCTRINE/genesis.md``.
        """
        ''',
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx, use_cache=False)
    doc_edges = [e for e in g.edges if e.kind == "code_doc_ref"]
    assert any(
        e.src == "src/myco/handler.py"
        and e.dst == "docs/architecture/L2_DOCTRINE/genesis.md"
        for e in doc_edges
    )


def test_graph_skips_stdlib_imports(seeded_substrate: Path) -> None:
    # Imports of ``sys`` / ``pathlib`` / third-party should never
    # create edges; only internal ``myco.*`` imports count.
    _seed_src(
        seeded_substrate,
        "myco/standalone.py",
        '''
        """standalone module, no internal deps."""
        import sys
        import pathlib
        from collections import OrderedDict
        import yaml
        ''',
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx, use_cache=False)
    # No import edges should originate from this file.
    outgoing_imports = [
        e
        for e in g.edges
        if e.kind == "import" and e.src == "src/myco/standalone.py"
    ]
    assert outgoing_imports == []
    # But the node itself must still be present.
    assert "src/myco/standalone.py" in g.nodes


def test_graph_handles_syntax_error_gracefully(seeded_substrate: Path) -> None:
    # A syntax-broken Python file must not crash graph build; the
    # node is still recorded (operators can see the file exists)
    # and other edges continue to land.
    _seed_src(
        seeded_substrate,
        "myco/good.py",
        '''
        """a good module."""
        x = 1
        ''',
    )
    # Intentionally invalid syntax.
    _seed_src(
        seeded_substrate,
        "myco/broken.py",
        '''
        def (:
            broken
        ''',
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    # Must not raise.
    g = build_graph(ctx, use_cache=False)
    # Both nodes present.
    assert "src/myco/good.py" in g.nodes
    assert "src/myco/broken.py" in g.nodes
    # Broken file has no outgoing import edges (couldn't parse).
    broken_outs = [
        e
        for e in g.edges
        if e.kind == "import" and e.src == "src/myco/broken.py"
    ]
    assert broken_outs == []


def test_walk_src_graph_no_op_without_src_dir(seeded_substrate: Path) -> None:
    # Pure-doctrine substrate with no ``src/`` — walker returns empty.
    result = walk_src_graph(seeded_substrate)
    assert result.nodes == set()
    assert result.import_edges == []
    assert result.doc_edges == []


def test_walk_src_graph_skips_pycache(seeded_substrate: Path) -> None:
    # ``__pycache__`` contents must never become graph nodes.
    _seed_src(
        seeded_substrate,
        "myco/real.py",
        '''
        """real."""
        ''',
    )
    cache_dir = seeded_substrate / "src" / "myco" / "__pycache__"
    cache_dir.mkdir(parents=True, exist_ok=True)
    # ``.py`` under __pycache__ is very unusual but exercises the
    # skip-dir filter regardless of extension matching.
    (cache_dir / "real.cpython-313.py").write_text(
        "# synthetic", encoding="utf-8"
    )
    result = walk_src_graph(seeded_substrate)
    assert any(n == "src/myco/real.py" for n in result.nodes)
    assert not any("__pycache__" in n for n in result.nodes)


def test_import_edge_for_bare_import_statement(seeded_substrate: Path) -> None:
    # ``import myco.pkg.mod`` (no ``from``) also produces an edge.
    _seed_src(
        seeded_substrate,
        "myco/pkg/__init__.py",
        '''
        """pkg."""
        ''',
    )
    _seed_src(
        seeded_substrate,
        "myco/pkg/mod.py",
        '''
        """mod."""
        X = 1
        ''',
    )
    _seed_src(
        seeded_substrate,
        "myco/top.py",
        '''
        """top."""
        import myco.pkg.mod
        ''',
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx, use_cache=False)
    assert any(
        e.kind == "import"
        and e.src == "src/myco/top.py"
        and e.dst == "src/myco/pkg/mod.py"
        for e in g.edges
    )


def test_relative_import_resolves_to_sibling(seeded_substrate: Path) -> None:
    # ``from . import sibling`` inside ``myco/pkg/caller.py`` must
    # resolve to ``src/myco/pkg/sibling.py``.
    _seed_src(
        seeded_substrate,
        "myco/pkg/__init__.py",
        '''
        """pkg."""
        ''',
    )
    _seed_src(
        seeded_substrate,
        "myco/pkg/sibling.py",
        '''
        """sibling."""
        X = 1
        ''',
    )
    _seed_src(
        seeded_substrate,
        "myco/pkg/caller.py",
        '''
        """caller."""
        from . import sibling
        ''',
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    g = build_graph(ctx, use_cache=False)
    assert any(
        e.kind == "import"
        and e.src == "src/myco/pkg/caller.py"
        and e.dst == "src/myco/pkg/sibling.py"
        for e in g.edges
    )
