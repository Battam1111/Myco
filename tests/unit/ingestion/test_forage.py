"""Tests for ``myco.ingestion.forage``.

v0.4.2 (Stage F.1) replaced the hardcoded extension whitelist with
the adapter registry. Tests now verify that forage includes anything
an adapter claims, reports what it skips, and no longer silently
drops code files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.ingestion.forage import list_candidates, run


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_list_candidates_includes_code_files(tmp_path: Path) -> None:
    """Core v0.4.2 fix: .py must be listed (text-file adapter claims it)."""
    (tmp_path / "a.md").write_text("# x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    (tmp_path / "d.py").write_text("print()", encoding="utf-8")
    items, skipped = list_candidates(target_dir=tmp_path)
    suffixes = {it.suffix for it in items}
    assert ".md" in suffixes
    assert ".txt" in suffixes
    assert ".py" in suffixes, (
        ".py must be listed now that the text-file adapter handles it"
    )


def test_list_candidates_skips_binary_and_reports_count(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# x", encoding="utf-8")
    (tmp_path / "c.bin").write_bytes(b"\x00\x01\x02\x03" * 100)
    items, skipped = list_candidates(target_dir=tmp_path)
    suffixes = {it.suffix for it in items}
    assert ".md" in suffixes
    assert ".bin" not in suffixes
    assert skipped >= 1, "binary files should be counted as skipped"


def test_list_candidates_recurses(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "deep.md").write_text("x", encoding="utf-8")
    items, _skipped = list_candidates(target_dir=tmp_path)
    assert any("deep.md" in it.path for it in items)


def test_list_candidates_reports_adapter_name(tmp_path: Path) -> None:
    (tmp_path / "hello.py").write_text("print('hi')", encoding="utf-8")
    items, _ = list_candidates(target_dir=tmp_path)
    assert items
    assert items[0].adapter == "text-file"


def test_list_candidates_rejects_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(UsageError, match="does not exist"):
        list_candidates(target_dir=tmp_path / "nope")


def test_list_candidates_rejects_file(tmp_path: Path) -> None:
    f = tmp_path / "f.md"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(UsageError, match="not a directory"):
        list_candidates(target_dir=f)


def test_run_default_target_is_substrate_root(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = run({}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["target"] == str(genesis_substrate.resolve())
    # MYCO.md and _canon.yaml should be discoverable.
    paths = [it["path"] for it in result.payload["items"]]
    assert any("MYCO.md" in p for p in paths)
    assert any("_canon.yaml" in p for p in paths)


def test_run_payload_includes_skipped_count(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    result = run({}, ctx=ctx)
    assert "skipped" in result.payload


def test_run_with_explicit_path(tmp_path: Path, genesis_substrate: Path) -> None:
    ext = tmp_path / "external"
    ext.mkdir()
    (ext / "a.md").write_text("x", encoding="utf-8")
    ctx = _mk_ctx(genesis_substrate)
    result = run({"path": str(ext)}, ctx=ctx)
    assert result.payload["target"] == str(ext.resolve())
    assert result.payload["count"] == 1
