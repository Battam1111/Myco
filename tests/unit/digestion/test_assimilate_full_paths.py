"""Comprehensive coverage for digestion/assimilate.py."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.digestion.assimilate import _list_raw, _sync_contract_version, reflect, run
from myco.ingestion.eat import append_note


def _seed(root: Path) -> MycoContext:
    body = """\
schema_version: "2"
contract_version: "v0.6.0"
synced_contract_version: "v0.5.0"
identity:
  substrate_id: "test"
  entry_point: "MYCO.md"
system:
  hard_contract:
    rule_count: 7
  write_surface:
    allowed:
      - "_canon.yaml"
      - "notes/**"
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
"""
    (root / "_canon.yaml").write_text(body, encoding="utf-8")
    (root / "MYCO.md").write_text("# x", encoding="utf-8")
    return MycoContext.for_testing(root=root)


def test_list_raw_empty_when_no_raw_dir(tmp_path: Path):
    ctx = _seed(tmp_path)
    assert _list_raw(ctx) == []


def test_list_raw_returns_files(tmp_path: Path):
    ctx = _seed(tmp_path)
    raw = tmp_path / "notes" / "raw"
    raw.mkdir(parents=True)
    (raw / "n1.md").write_text("---\nstage: raw\n---\n# 1\n", encoding="utf-8")
    (raw / "n2.md").write_text("---\nstage: raw\n---\n# 2\n", encoding="utf-8")
    out = _list_raw(ctx)
    assert len(out) == 2


def test_reflect_no_notes_returns_zero_promoted(tmp_path: Path):
    ctx = _seed(tmp_path)
    out = reflect(ctx=ctx)
    assert out["promoted"] == 0
    assert out["errors"] == []


def test_reflect_all_promotes_existing(tmp_path: Path):
    ctx = _seed(tmp_path)
    append_note(ctx=ctx, content="finding 1")
    append_note(ctx=ctx, content="finding 2")
    out = reflect(ctx=ctx)
    assert out["promoted"] == 2
    assert out["errors"] == []


def test_reflect_specific_note_id(tmp_path: Path):
    ctx = _seed(tmp_path)
    rec = append_note(ctx=ctx, content="solo")
    nid = rec.path.stem
    out = reflect(ctx=ctx, note_id=nid)
    assert out["promoted"] == 1


def test_reflect_unknown_note_id_records_error(tmp_path: Path):
    ctx = _seed(tmp_path)
    out = reflect(ctx=ctx, note_id="not-a-real-id")
    assert out["errors"]
    assert out["promoted"] == 0


def test_run_clean_pass_returns_exit_0(tmp_path: Path):
    ctx = _seed(tmp_path)
    append_note(ctx=ctx, content="x")
    res = run({}, ctx=ctx)
    assert res.exit_code == 0


def test_run_no_candidates_exit_0(tmp_path: Path):
    """Empty raw dir → exit 0 (no-op, not error)."""
    ctx = _seed(tmp_path)
    res = run({}, ctx=ctx)
    assert res.exit_code == 0


def test_run_all_failed_exit_1(tmp_path: Path):
    """If all attempts errored → exit 1."""
    ctx = _seed(tmp_path)
    res = run({"note_id": "nonexistent"}, ctx=ctx)
    assert res.exit_code == 1


def test_run_syncs_contract_version_when_drifted(tmp_path: Path):
    """assimilate updates synced_contract_version on clean pass."""
    ctx = _seed(tmp_path)
    res = run({}, ctx=ctx)
    assert res.exit_code == 0
    canon_text = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    assert 'synced_contract_version: "v0.6.0"' in canon_text
    assert res.payload["synced_contract_version_updated"] is True


def test_sync_contract_version_idempotent(tmp_path: Path):
    """When already synced, _sync_contract_version is a no-op."""
    body = """\
schema_version: "2"
contract_version: "v0.6.0"
synced_contract_version: "v0.6.0"
identity:
  substrate_id: "test"
  entry_point: "MYCO.md"
system:
  hard_contract:
    rule_count: 7
  write_surface:
    allowed: ["_canon.yaml"]
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
"""
    (tmp_path / "_canon.yaml").write_text(body, encoding="utf-8")
    (tmp_path / "MYCO.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=tmp_path)
    assert _sync_contract_version(ctx) is False


def test_sync_contract_version_legacy_canon_missing_field(tmp_path: Path):
    """Canon without synced_contract_version → silent no-op."""
    body = """\
schema_version: "2"
contract_version: "v0.6.0"
identity:
  substrate_id: "test"
  entry_point: "MYCO.md"
system:
  hard_contract:
    rule_count: 7
  write_surface:
    allowed: ["_canon.yaml"]
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
"""
    (tmp_path / "_canon.yaml").write_text(body, encoding="utf-8")
    (tmp_path / "MYCO.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=tmp_path)
    assert _sync_contract_version(ctx) is False
