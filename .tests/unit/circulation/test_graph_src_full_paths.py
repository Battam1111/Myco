"""Comprehensive coverage for circulation/graph_src.py."""

from __future__ import annotations

from pathlib import Path

from myco.circulation.graph_src import (
    SrcGraphResult,
    _extract_docstring_doc_refs,
    _module_to_path,
    _resolve_doc_ref,
    _resolve_relative_import,
    walk_src_graph,
)

# ---------- _module_to_path ----------


def test_module_to_path_empty_returns_none(tmp_path: Path):
    assert _module_to_path("", tmp_path) is None


def test_module_to_path_external_returns_none(tmp_path: Path):
    """Non-myco prefix → None."""
    assert _module_to_path("os.path", tmp_path) is None


def test_module_to_path_resolves_file(tmp_path: Path):
    """Real file under <src>/myco/<...>.py resolves."""
    pkg = tmp_path / "myco" / "core"
    pkg.mkdir(parents=True)
    (pkg / "foo.py").write_text("# x", encoding="utf-8")
    out = _module_to_path("myco.core.foo", tmp_path)
    assert out is not None
    assert out.name == "foo.py"


def test_module_to_path_resolves_package_init(tmp_path: Path):
    """Module path that's a package → resolves to __init__.py."""
    pkg = tmp_path / "myco" / "core"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("# x", encoding="utf-8")
    out = _module_to_path("myco.core", tmp_path)
    assert out is not None
    assert out.name == "__init__.py"


def test_module_to_path_no_match_returns_none(tmp_path: Path):
    """Module under myco that doesn't exist → None."""
    (tmp_path / "myco").mkdir()
    assert _module_to_path("myco.does.not.exist", tmp_path) is None


# ---------- _resolve_relative_import ----------


def test_resolve_relative_level_zero_returns_none(tmp_path: Path):
    out = _resolve_relative_import(tmp_path / "myco" / "x.py", tmp_path, "y", level=0)
    assert out is None


def test_resolve_relative_too_many_pops(tmp_path: Path):
    """level too high → None."""
    pkg = tmp_path / "myco"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "a.py").write_text("", encoding="utf-8")
    out = _resolve_relative_import(pkg / "a.py", tmp_path, "x", level=10)
    assert out is None


def test_resolve_relative_outside_src_returns_none(tmp_path: Path):
    """File outside src_dir → None (ValueError swallowed)."""
    (tmp_path / "myco").mkdir()
    out = _resolve_relative_import(
        tmp_path.parent / "elsewhere.py", tmp_path, "x", level=1
    )
    assert out is None


def test_resolve_relative_resolves_sibling(tmp_path: Path):
    """from . import sibling — resolves to sibling file."""
    pkg = tmp_path / "myco" / "ingestion"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "sibling.py").write_text("", encoding="utf-8")
    importing = pkg / "main.py"
    importing.write_text("from . import sibling", encoding="utf-8")
    out = _resolve_relative_import(importing, tmp_path, "sibling", level=1)
    assert out is not None
    assert out.name == "sibling.py"


# ---------- _extract_docstring_doc_refs ----------


def test_extract_no_docstring_returns_empty():
    assert _extract_docstring_doc_refs(None) == []
    assert _extract_docstring_doc_refs("") == []


def test_extract_finds_docs_path():
    out = _extract_docstring_doc_refs(
        "See docs/architecture/L1_CONTRACT/protocol.md for details."
    )
    assert "docs/architecture/L1_CONTRACT/protocol.md" in out


def test_extract_finds_notes_path():
    out = _extract_docstring_doc_refs("Reference notes/integrated/foo.md")
    assert "notes/integrated/foo.md" in out


def test_extract_strips_leading_dotslash():
    out = _extract_docstring_doc_refs("Path: ./docs/x.md")
    assert "docs/x.md" in out


def test_extract_dedupes_in_insertion_order():
    out = _extract_docstring_doc_refs(
        "First docs/a.md then docs/a.md again then docs/b.md"
    )
    assert out == ["docs/a.md", "docs/b.md"]


def test_extract_ignores_non_md_paths():
    """Without .md extension, regex doesn't match."""
    out = _extract_docstring_doc_refs("File: docs/foo.txt")
    assert out == []


# ---------- _resolve_doc_ref ----------


def test_resolve_doc_ref_inside_substrate(tmp_path: Path):
    """Path inside substrate → relative POSIX path."""
    out = _resolve_doc_ref("docs/x.md", tmp_path)
    assert out == "docs/x.md"


def test_resolve_doc_ref_escapes_substrate_returns_none(tmp_path: Path):
    """../../escape → None (security)."""
    out = _resolve_doc_ref("../../etc/passwd", tmp_path)
    assert out is None


# ---------- walk_src_graph integration ----------


def test_walk_src_graph_no_src_dir(tmp_path: Path):
    """No src/ → empty result."""
    out = walk_src_graph(tmp_path)
    assert isinstance(out, SrcGraphResult)
    assert out.nodes == set()
    assert out.import_edges == []
    assert out.doc_edges == []


def test_walk_src_graph_minimal_substrate(tmp_path: Path):
    """src/myco/x.py → node added."""
    pkg = tmp_path / "src" / "myco"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "x.py").write_text("# x", encoding="utf-8")
    out = walk_src_graph(tmp_path)
    rels = set(out.nodes)
    assert "src/myco/x.py" in rels


def test_walk_src_graph_absolute_import_edge(tmp_path: Path):
    """from myco.core.x import y → import edge."""
    pkg = tmp_path / "src" / "myco"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    core = pkg / "core"
    core.mkdir()
    (core / "__init__.py").write_text("", encoding="utf-8")
    (core / "x.py").write_text("", encoding="utf-8")
    (pkg / "main.py").write_text("from myco.core.x import y", encoding="utf-8")
    out = walk_src_graph(tmp_path)
    edges = {(s, d) for s, d in out.import_edges}
    assert any("main.py" in s and "x.py" in d for s, d in edges)


def test_walk_src_graph_skips_external_imports(tmp_path: Path):
    """import os doesn't generate an edge."""
    pkg = tmp_path / "src" / "myco"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "x.py").write_text("import os", encoding="utf-8")
    out = walk_src_graph(tmp_path)
    assert out.import_edges == []


def test_walk_src_graph_handles_syntax_error(tmp_path: Path):
    """Broken .py file is recorded as node but produces no edges."""
    pkg = tmp_path / "src" / "myco"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "broken.py").write_text("def x(:", encoding="utf-8")
    out = walk_src_graph(tmp_path)
    assert "src/myco/broken.py" in out.nodes


def test_walk_src_graph_extracts_doc_ref_from_docstring(tmp_path: Path):
    """Module docstring containing docs/x.md → doc_edge."""
    pkg = tmp_path / "src" / "myco"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "x.py").write_text(
        '"""\n'
        "Module that references docs/architecture/L1_CONTRACT/protocol.md.\n"
        '"""\n'
        "y = 1\n",
        encoding="utf-8",
    )
    out = walk_src_graph(tmp_path)
    assert any("protocol.md" in d for s, d in out.doc_edges)


def test_walk_src_graph_skips_pycache(tmp_path: Path):
    """__pycache__ ignored."""
    pkg = tmp_path / "src" / "myco"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    pyc = pkg / "__pycache__"
    pyc.mkdir()
    (pyc / "x.cpython-313.pyc").write_text("", encoding="utf-8")
    out = walk_src_graph(tmp_path)
    assert all("__pycache__" not in n for n in out.nodes)


def test_walk_src_graph_relative_import(tmp_path: Path):
    """from . import sibling → import edge."""
    pkg = tmp_path / "src" / "myco" / "ingestion"
    pkg.mkdir(parents=True)
    (tmp_path / "src" / "myco" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "sibling.py").write_text("", encoding="utf-8")
    (pkg / "main.py").write_text("from . import sibling", encoding="utf-8")
    out = walk_src_graph(tmp_path)
    assert any("sibling.py" in d for s, d in out.import_edges)


def test_walk_src_graph_include_tests_flag(tmp_path: Path):
    """include_tests=True allows tests/ subdirs."""
    pkg = tmp_path / "src" / "myco" / "tests"
    pkg.mkdir(parents=True)
    (tmp_path / "src" / "myco" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "test_x.py").write_text("# t", encoding="utf-8")
    out = walk_src_graph(tmp_path, include_tests=True)
    assert any("test_x.py" in n for n in out.nodes)
