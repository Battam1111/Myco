"""Comprehensive coverage for cycle/graft.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.cycle.graft import _collect_plugins, _explain, run


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_run_no_mode_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="exactly one of"):
        run({}, ctx=ctx)


def test_run_two_modes_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        run({"list": True, "validate": True}, ctx=ctx)


def test_run_three_modes_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        run({"list": True, "validate": True, "explain": "X"}, ctx=ctx)


def test_run_list_mode(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    res = run({"list": True}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["mode"] == "list"
    assert res.payload["count"] >= 0
    assert isinstance(res.payload["plugins"], list)


def test_run_validate_mode_clean(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    res = run({"validate": True}, ctx=ctx)
    assert res.payload["mode"] == "validate"
    assert isinstance(res.payload["errors"], list)
    # exit 0 when ok=True
    if res.payload["ok"]:
        assert res.exit_code == 0


def test_run_explain_unknown_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="unknown plugin"):
        run({"explain": "no-such-plugin-anywhere"}, ctx=ctx)


def test_run_explain_existing_dimension(genesis_substrate: Path):
    """Explain a real dimension by name (e.g. M1)."""
    ctx = _ctx(genesis_substrate)
    res = run({"explain": "M1"}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["mode"] == "explain"
    assert res.payload["name"] == "M1"
    assert res.payload["kind"] == "dimension"


def test_collect_plugins_returns_dimensions(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    plugins = _collect_plugins(ctx)
    kinds = {p["kind"] for p in plugins}
    assert "dimension" in kinds


def test_collect_plugins_classifies_kernel_scope(genesis_substrate: Path):
    """Built-in dim like M1 is scope=kernel."""
    ctx = _ctx(genesis_substrate)
    plugins = _collect_plugins(ctx)
    m1_entries = [p for p in plugins if p.get("name") == "M1"]
    assert m1_entries
    assert m1_entries[0]["scope"] == "kernel"


def test_explain_dimension(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    out = _explain(ctx, "M1")
    assert out["name"] == "M1"
    assert out["kind"] == "dimension"


def test_explain_unknown_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="unknown plugin"):
        _explain(ctx, "definitely-not-real")


def test_run_list_substrates_mode(genesis_substrate: Path):
    """list-substrates mode runs without crash."""
    ctx = _ctx(genesis_substrate)
    res = run({"list_substrates": True}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["mode"] == "list-substrates"
    assert "substrates" in res.payload
    assert "count" in res.payload
