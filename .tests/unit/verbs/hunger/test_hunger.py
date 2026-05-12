"""Tests for ``myco.ingestion.hunger``."""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.identity_cluster import MycoContext
from myco.ingestion.capture_cluster import (
    BEGIN_MARKER,
    append_note,
    compose_hunger_report,
)
from myco.ingestion.capture_cluster import hunger_run as run


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
    # v0.5.3 adds the ``local_plugins`` block for substrate-local plugin
    # surface visibility; the pre-v0.5.3 keys remain intact.
    assert {"contract_drift", "raw_backlog", "reflex_signals", "advice"}.issubset(
        d.keys()
    )
    assert "local_plugins" in d
    assert isinstance(d["advice"], list)


# v0.8.5 — lifted from .tests/unit/ingestion/test_hunger_count_by_kind.py
# (deleted as part of the dedup pass) to keep all hunger-related
# coverage in one file per the 1-test-file-per-verb convention.
def test_hunger_payload_includes_count_by_kind(
    genesis_substrate: Path,
) -> None:
    """v0.5.4 bug #2 + v0.5.22 bug #4 regression.

    The hunger payload's ``local_plugins`` block exposes ``count_by_kind``
    with entries for every plugin category. Before v0.5.4 only a flat
    ``count`` shipped, contradicting the v0.5.3 CHANGELOG promise.

    v0.5.22 additionally asserts that a **fresh substrate** with no
    ``.myco/plugins/`` tree reports zeros for every kind — pre-v0.5.22
    this reported 32+ because every kernel built-in was misclassified
    as "local".
    """
    ctx = MycoContext.for_testing(root=genesis_substrate)
    report = compose_hunger_report(ctx)
    payload = report.as_dict()

    assert "local_plugins" in payload
    lp = payload["local_plugins"]
    assert "count" in lp
    assert "count_by_kind" in lp
    by_kind = lp["count_by_kind"]
    for key in ("dimension", "adapter", "schema_upgrader", "overlay_verb"):
        assert key in by_kind, f"missing {key!r} in count_by_kind"
        assert isinstance(by_kind[key], int)
    # Total should equal the sum.
    assert lp["count"] == sum(by_kind.values())
    # v0.5.22 semantics: a fresh substrate has no substrate-local
    # plugins — kernel built-ins don't count. Pre-fix this was 32+.
    assert by_kind["dimension"] == 0
    assert by_kind["adapter"] == 0
    assert by_kind["schema_upgrader"] == 0
    assert by_kind["overlay_verb"] == 0
    assert lp["count"] == 0
