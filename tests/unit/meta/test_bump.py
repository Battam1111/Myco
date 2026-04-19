"""Tests for ``myco.meta.bump``."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from myco.meta.bump import (
    _VERSION_RE,
    _insert_changelog_entry,
    _patch_canon_field,
    run,
)

from myco.core.canon import load_canon
from myco.core.context import MycoContext
from myco.core.errors import ContractError, UsageError


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _bumpable_canon() -> str:
    return textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0"
        synced_contract_version: "v0.4.0"
        identity:
          substrate_id: "x"
          entry_point: "MYCO.md"
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        """
    )


def _write_substrate(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "_canon.yaml").write_text(_bumpable_canon(), encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "contract_changelog.md").write_text(
        textwrap.dedent(
            """\
            # Contract Changelog

            Append-only record of contract-version bumps.

            Format: one section per `contract_version`, newest first.

            ---

            ## v0.4.0 — 2026-04-15 — Greenfield rewrite

            First entry.
            """
        ),
        encoding="utf-8",
    )
    return root


def test_version_re_accepts_common_shapes() -> None:
    assert _VERSION_RE.match("v0.5.0")
    assert _VERSION_RE.match("0.5.0")
    assert _VERSION_RE.match("v0.5.0-alpha.1")
    assert _VERSION_RE.match("v0.5.0.dev")
    assert not _VERSION_RE.match("garbage")
    assert not _VERSION_RE.match("v0.5")


def test_patch_canon_field_replaces_value() -> None:
    text = 'contract_version: "v0.4.0"\nother: "y"\n'
    out = _patch_canon_field(text, "contract_version", "v0.5.0")
    assert 'contract_version: "v0.5.0"' in out
    assert 'other: "y"' in out


def test_patch_canon_field_missing_raises() -> None:
    with pytest.raises(ContractError, match="could not locate"):
        _patch_canon_field("no such field\n", "contract_version", "v0.5.0")


def test_insert_changelog_entry_prepends_above_newest_heading() -> None:
    existing = textwrap.dedent(
        """\
        # Contract Changelog

        ---

        ## v0.4.0 — 2026-04-15 — Greenfield

        body
        """
    )
    out = _insert_changelog_entry(existing, "## v0.5.0 — 2026-04-17 — New\n\nbody\n")
    assert out.index("## v0.5.0") < out.index("## v0.4.0")


def test_run_dry_run_does_not_write(tmp_path: Path) -> None:
    _write_substrate(tmp_path)
    ctx = _ctx(tmp_path)
    r = run({"contract": "v0.5.0", "dry_run": True}, ctx=ctx)
    assert r.exit_code == 0
    assert r.payload["dry_run"] is True
    assert r.payload["new_version"] == "v0.5.0"
    # Canon was not modified.
    raw = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    assert 'contract_version: "v0.4.0"' in raw


def test_run_updates_canon_and_changelog(tmp_path: Path) -> None:
    _write_substrate(tmp_path)
    ctx = _ctx(tmp_path)
    r = run({"contract": "v0.5.0", "date": "2026-04-17"}, ctx=ctx)
    assert r.exit_code == 0

    # Canon contract + synced both at v0.5.0 now.
    reloaded = load_canon(tmp_path / "_canon.yaml")
    assert reloaded.contract_version == "v0.5.0"
    assert reloaded.synced_contract_version == "v0.5.0"

    # Changelog has the new section above the v0.4.0 one.
    log = (tmp_path / "docs" / "contract_changelog.md").read_text(encoding="utf-8")
    assert "## v0.5.0 — 2026-04-17 — Contract bump" in log
    assert log.index("## v0.5.0") < log.index("## v0.4.0")


def test_run_rejects_bad_version(tmp_path: Path) -> None:
    _write_substrate(tmp_path)
    ctx = _ctx(tmp_path)
    with pytest.raises(UsageError, match="does not match"):
        run({"contract": "garbage"}, ctx=ctx)


def test_run_rejects_same_version(tmp_path: Path) -> None:
    _write_substrate(tmp_path)
    ctx = _ctx(tmp_path)
    with pytest.raises(UsageError, match="already"):
        run({"contract": "v0.4.0"}, ctx=ctx)


def test_run_requires_contract_flag(tmp_path: Path) -> None:
    _write_substrate(tmp_path)
    ctx = _ctx(tmp_path)
    with pytest.raises(UsageError, match="--contract"):
        run({}, ctx=ctx)
