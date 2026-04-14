"""Tests for ``myco.ingestion.hunger``."""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.ingestion.boot_brief import BEGIN_MARKER
from myco.ingestion.eat import append_note
from myco.ingestion.hunger import compose_hunger_report, run


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_quiet_substrate_reports_no_action(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    report = compose_hunger_report(ctx)
    assert report.contract_drift is False
    assert report.raw_backlog == 0
    assert report.reflex_signals == ()
    assert any("quiet" in a for a in report.advice)


def test_raw_backlog_counts_eaten_notes(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="n1")
    append_note(ctx=ctx, content="n2")
    append_note(ctx=ctx, content="n3")
    report = compose_hunger_report(ctx)
    assert report.raw_backlog == 3
    assert any("backlog=3" in a for a in report.advice)


def test_contract_drift_detected(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0-alpha.1"
        synced_contract_version: "v0.4.0-alpha.0"
        identity:
          substrate_id: "drift-test"
          tags: []
          entry_point: "MYCO.md"
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        """
    )
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    (tmp_path / "notes").mkdir()
    (tmp_path / "docs").mkdir()
    ctx = _mk_ctx(tmp_path)
    report = compose_hunger_report(ctx)
    assert report.contract_drift is True
    assert any("contract drifted" in a for a in report.advice)


def test_execute_patches_entry_point(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    append_note(ctx=ctx, content="x")
    result = run({"execute": True}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["execute"] is True
    entry_text = (genesis_substrate / "MYCO.md").read_text(encoding="utf-8")
    assert BEGIN_MARKER in entry_text
    assert "raw_backlog" in entry_text


def test_no_execute_leaves_entry_point_unpatched(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    before = (genesis_substrate / "MYCO.md").read_text(encoding="utf-8")
    result = run({"execute": False}, ctx=ctx)
    assert result.payload["entry_point_patched"] is None
    after = (genesis_substrate / "MYCO.md").read_text(encoding="utf-8")
    assert before == after


def test_report_as_dict_serializable(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    report = compose_hunger_report(ctx)
    d = report.as_dict()
    assert set(d.keys()) == {"contract_drift", "raw_backlog", "reflex_signals", "advice"}
    assert isinstance(d["advice"], list)
