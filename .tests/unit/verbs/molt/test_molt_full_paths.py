"""Comprehensive coverage for cycle/molt.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.identity_cluster import ContractError, MycoContext, UsageError
from myco.cycle.canon_cluster import (
    _insert_changelog_entry,
    _patch_canon_field,
    _render_changelog_section,
)
from myco.cycle.canon_cluster import (
    molt_run as run,
)


def _seed(root: Path, *, contract: str = "v0.5.0") -> MycoContext:
    body = f"""\
schema_version: "2"
contract_version: "{contract}"
synced_contract_version: "{contract}"
identity:
  substrate_id: "test"
  entry_point: "MYCO.md"
system:
  hard_contract:
    rule_count: 7
  write_surface:
    allowed:
      - "_canon.yaml"
      - "docs/**"
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
waves:
  current: 0
"""
    (root / "_canon.yaml").write_text(body, encoding="utf-8")
    (root / "MYCO.md").write_text("# x", encoding="utf-8")
    return MycoContext.for_testing(root=root)


def test_run_no_contract_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    with pytest.raises(UsageError, match="--contract"):
        run({}, ctx=ctx)


def test_run_invalid_version_format_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    with pytest.raises(UsageError, match="does not match"):
        run({"contract": "not-a-version"}, ctx=ctx)


def test_run_canon_missing_raises(tmp_path: Path):
    ctx = _seed(tmp_path)
    (tmp_path / "_canon.yaml").unlink()
    with pytest.raises(ContractError, match="canon not found"):
        run({"contract": "v0.6.0"}, ctx=ctx)


def test_run_already_at_version_raises(tmp_path: Path):
    ctx = _seed(tmp_path, contract="v0.5.0")
    with pytest.raises(UsageError, match="already"):
        run({"contract": "v0.5.0"}, ctx=ctx)


def test_run_dry_run_no_writes(tmp_path: Path):
    ctx = _seed(tmp_path)
    canon_text_before = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    res = run({"contract": "v0.6.0", "dry_run": True}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["dry_run"] is True
    assert res.payload["old_version"] == "v0.5.0"
    assert res.payload["new_version"] == "v0.6.0"
    canon_text_after = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    # Dry run: no actual write.
    assert canon_text_before == canon_text_after


def test_run_full_writes_all_files(tmp_path: Path):
    ctx = _seed(tmp_path)
    res = run({"contract": "v0.6.0", "date": "2026-04-28"}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["dry_run"] is False
    assert res.payload["new_version"] == "v0.6.0"
    canon_text = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    assert "v0.6.0" in canon_text
    cl = (tmp_path / "docs" / "contract_changelog.md").read_text(encoding="utf-8")
    assert "v0.6.0" in cl
    assert "v0.5.0" in cl


def test_run_creates_changelog_when_missing(tmp_path: Path):
    ctx = _seed(tmp_path)
    # Ensure changelog doesn't pre-exist.
    cl = tmp_path / "docs" / "contract_changelog.md"
    if cl.exists():
        cl.unlink()
    res = run({"contract": "v0.6.0", "date": "2026-04-28"}, ctx=ctx)
    assert res.exit_code == 0
    assert cl.is_file()


def test_run_increments_waves(tmp_path: Path):
    ctx = _seed(tmp_path)
    res = run({"contract": "v0.6.0"}, ctx=ctx)
    assert res.payload["waves_touched"] is True
    canon_text = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    # waves.current was 0 → should be 1 now.
    assert "current: 1" in canon_text


def test_patch_canon_field_writes_value():
    text = 'contract_version: "v0.5.0"\nfoo: bar\n'
    out = _patch_canon_field(text, "contract_version", "v0.6.0")
    assert 'contract_version: "v0.6.0"' in out


def test_patch_canon_field_field_missing_raises():
    text = "foo: bar\n"
    with pytest.raises(ContractError, match="could not locate"):
        _patch_canon_field(text, "contract_version", "v0.6.0")


def test_render_changelog_section_includes_versions():
    out = _render_changelog_section(
        new_version="v0.6.0", old_version="v0.5.0", today="2026-04-28"
    )
    assert "v0.6.0" in out
    assert "v0.5.0" in out
    assert "2026-04-28" in out


def test_insert_changelog_entry_above_existing():
    text = (
        "# Contract Changelog\n\n"
        "Header text.\n\n"
        "---\n\n"
        "## v0.5.0 - 2026-01-01\n\n"
        "Existing entry.\n"
    )
    new = "## v0.6.0 - 2026-04-28\n\nNew entry.\n"
    out = _insert_changelog_entry(text, new)
    assert "v0.6.0" in out
    # Should appear before v0.5.0
    assert out.index("v0.6.0") < out.index("v0.5.0")


def test_insert_changelog_entry_empty_changelog():
    """When no existing ## v entry — appended after the divider."""
    text = "# Contract Changelog\n\nHeader.\n\n---\n"
    new = "## v0.6.0 - 2026-04-28\n\nFirst entry.\n"
    out = _insert_changelog_entry(text, new)
    assert "v0.6.0" in out


def test_insert_changelog_entry_no_divider():
    """No header divider either — append at end."""
    text = "# Contract Changelog\n"
    new = "## v0.6.0 - 2026-04-28\n\nEntry.\n"
    out = _insert_changelog_entry(text, new)
    assert "v0.6.0" in out


def test_run_synced_field_optional(tmp_path: Path):
    """If canon lacks synced_contract_version, molt skips that step silently."""
    body = """\
schema_version: "2"
contract_version: "v0.5.0"
identity:
  substrate_id: "test"
  entry_point: "MYCO.md"
system:
  hard_contract:
    rule_count: 7
  write_surface:
    allowed: ["_canon.yaml", "docs/**"]
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
"""
    (tmp_path / "_canon.yaml").write_text(body, encoding="utf-8")
    (tmp_path / "MYCO.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=tmp_path)
    res = run({"contract": "v0.6.0"}, ctx=ctx)
    assert res.payload["synced_touched"] is False
