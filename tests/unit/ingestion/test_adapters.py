"""Tests for the ingestion adapter protocol, registry, and built-in adapters.

These tests cover the v0.4.2 BLOCKER fixes: forage must list .py files,
eat must accept --path, adapters must produce valid IngestResults.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from myco.ingestion.adapters import (
    find_adapter,
    handled_extensions,
    all_adapters,
    IngestResult,
)
from myco.ingestion.adapters.text_file import TextFileAdapter
from myco.ingestion.adapters.code_repo import CodeRepoAdapter
from myco.ingestion.adapters.tabular import TabularReader


# ---------------------------------------------------------------------------
# Registry smoke tests
# ---------------------------------------------------------------------------


def test_registry_has_at_least_three_adapters() -> None:
    """text-file, code-repo, and tabular are stdlib-only; always present."""
    names = {a.name for a in all_adapters()}
    assert "text-file" in names
    assert "code-repo" in names
    assert "tabular" in names


def test_handled_extensions_include_py_and_csv() -> None:
    exts = handled_extensions()
    assert ".py" in exts, "text-file adapter must claim .py"
    assert ".csv" in exts, "tabular adapter must claim .csv"
    assert ".md" in exts, "text-file adapter must claim .md"


# ---------------------------------------------------------------------------
# TextFileAdapter
# ---------------------------------------------------------------------------


def test_text_file_handles_py(tmp_path: Path) -> None:
    f = tmp_path / "auth.py"
    f.write_text("def sign_token(): pass\n", encoding="utf-8")
    adapter = TextFileAdapter()
    assert adapter.can_handle(str(f))
    results = adapter.ingest(str(f))
    assert len(results) == 1
    assert "sign_token" in results[0].body
    assert results[0].source == str(f.resolve())
    assert "py" in results[0].tags


def test_text_file_rejects_binary(tmp_path: Path) -> None:
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
    adapter = TextFileAdapter()
    assert not adapter.can_handle(str(f))


def test_text_file_handles_makefile(tmp_path: Path) -> None:
    f = tmp_path / "Makefile"
    f.write_text("all:\n\techo hi\n", encoding="utf-8")
    adapter = TextFileAdapter()
    assert adapter.can_handle(str(f))


# ---------------------------------------------------------------------------
# CodeRepoAdapter
# ---------------------------------------------------------------------------


def test_code_repo_walks_and_produces_per_file_notes(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("# main\n", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("# utils\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Readme\n", encoding="utf-8")

    adapter = CodeRepoAdapter()
    assert adapter.can_handle(str(tmp_path))
    results = adapter.ingest(str(tmp_path))
    assert len(results) >= 3, "should produce notes for main.py, utils.py, README.md"
    names = {r.title for r in results}
    assert "main.py" in names
    assert "utils.py" in names
    assert "README.md" in names


def test_code_repo_skips_pycache(tmp_path: Path) -> None:
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "mod.cpython-313.pyc").write_bytes(b"\x00")
    (tmp_path / "real.py").write_text("x = 1\n", encoding="utf-8")
    results = CodeRepoAdapter().ingest(str(tmp_path))
    paths = [r.title for r in results]
    assert "real.py" in paths
    assert "mod.cpython-313.pyc" not in paths


def test_code_repo_provenance_includes_repo_name(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("# a\n", encoding="utf-8")
    results = CodeRepoAdapter().ingest(str(tmp_path))
    assert results
    assert tmp_path.name in results[0].source


# ---------------------------------------------------------------------------
# TabularReader
# ---------------------------------------------------------------------------


def test_tabular_ingests_csv(tmp_path: Path) -> None:
    f = tmp_path / "data.csv"
    f.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
    adapter = TabularReader()
    assert adapter.can_handle(str(f))
    results = adapter.ingest(str(f))
    assert len(results) == 1
    assert "Columns" in results[0].body
    assert "Alice" in results[0].body
    assert "tabular" in results[0].tags


def test_tabular_ingests_jsonl(tmp_path: Path) -> None:
    f = tmp_path / "events.jsonl"
    f.write_text('{"event":"click"}\n{"event":"scroll"}\n', encoding="utf-8")
    results = TabularReader().ingest(str(f))
    assert len(results) == 1
    assert "Records: 2" in results[0].body


def test_tabular_ingests_json(tmp_path: Path) -> None:
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    results = TabularReader().ingest(str(f))
    assert len(results) == 1
    assert "value" in results[0].body


# ---------------------------------------------------------------------------
# find_adapter dispatch
# ---------------------------------------------------------------------------


def test_find_adapter_for_py_file(tmp_path: Path) -> None:
    f = tmp_path / "mod.py"
    f.write_text("x = 1\n", encoding="utf-8")
    a = find_adapter(str(f))
    assert a is not None
    assert a.name == "text-file"


def test_find_adapter_for_directory(tmp_path: Path) -> None:
    a = find_adapter(str(tmp_path))
    assert a is not None
    assert a.name == "code-repo"


def test_find_adapter_for_csv(tmp_path: Path) -> None:
    f = tmp_path / "data.csv"
    f.write_text("a,b\n1,2\n", encoding="utf-8")
    a = find_adapter(str(f))
    assert a is not None
    assert a.name == "tabular"


def test_find_adapter_returns_none_for_binary(tmp_path: Path) -> None:
    f = tmp_path / "blob.bin"
    f.write_bytes(b"\x00\x01\x02\x03" * 200)
    assert find_adapter(str(f)) is None


# ---------------------------------------------------------------------------
# eat --path integration (via the run handler)
# ---------------------------------------------------------------------------


def test_eat_path_produces_notes(genesis_substrate: Path) -> None:
    from myco.core.context import MycoContext
    from myco.ingestion.eat import run

    ctx = MycoContext.for_testing(root=genesis_substrate)
    fixture = genesis_substrate / "ext"
    fixture.mkdir()
    (fixture / "hello.py").write_text("print('hi')\n", encoding="utf-8")
    (fixture / "world.py").write_text("print('world')\n", encoding="utf-8")

    result = run({"path": str(fixture)}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["adapter"] == "code-repo"
    assert result.payload["notes_created"] >= 2

    # Verify notes actually written
    raw_dir = genesis_substrate / "notes" / "raw"
    notes = list(raw_dir.glob("*.md"))
    assert len(notes) >= 2


def test_eat_content_still_works(genesis_substrate: Path) -> None:
    """Backward compat: --content without --path/--url still writes one note."""
    from myco.core.context import MycoContext
    from myco.ingestion.eat import run

    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = run({"content": "hello world"}, ctx=ctx)
    assert result.exit_code == 0
    assert "path" in result.payload
