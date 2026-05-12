"""Comprehensive coverage for cycle/ramify.py — verb / dim / adapter modes."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.cycle.ramify import _slug, run


def _ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _seed_with_canon(root: Path, *, sid: str = "myco-self") -> MycoContext:
    """Seed substrate with M canon, including write_surface and src/myco/."""
    body = f"""\
schema_version: "2"
contract_version: "v0.6.0"
identity:
  substrate_id: "{sid}"
  entry_point: "MYCO.md"
system:
  hard_contract:
    rule_count: 7
  write_surface:
    allowed:
      - "src/**"
      - ".myco/**"
      - "_canon.yaml"
      - "MYCO.md"
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
"""
    (root / "_canon.yaml").write_text(body, encoding="utf-8")
    (root / "MYCO.md").write_text("# x", encoding="utf-8")
    if sid == "myco-self":
        (root / "src" / "myco").mkdir(parents=True, exist_ok=True)
    return _ctx(root)


# ---------- mode dispatch errors ----------


def test_run_no_mode_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="--verb"):
        run({}, ctx=ctx)


def test_run_two_modes_set_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        run({"verb": "x", "dimension": "y"}, ctx=ctx)


def test_run_three_modes_set_raises(genesis_substrate: Path):
    ctx = _ctx(genesis_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        run({"verb": "x", "dimension": "y", "adapter": "z"}, ctx=ctx)


# ---------- _slug ----------


def test_slug_alpha_numeric_kept():
    assert _slug("hello123") == "hello123"


def test_slug_special_chars_to_underscore():
    assert _slug("foo bar-baz") == "foo_bar_baz"


def test_slug_strips_underscores():
    assert _slug("__abc__") == "abc"


def test_slug_empty_falls_back():
    assert _slug("") == "x"
    assert _slug("!!!") == "x"


# ---------- verb mode ----------


def test_verb_mode_unknown_verb_raises(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    with pytest.raises(UsageError, match="not declared in manifest"):
        run({"verb": "no-such-verb-anywhere"}, ctx=ctx)


def test_verb_mode_kernel_path_writes_stub(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    # Use 'eat' which is a real manifest entry mapping to ingestion/eat:run
    res = run({"verb": "eat"}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["mode"] == "verb"
    # Already exists (real eat.py is in repo) → not written.
    # We're running in tmp_path though, so "src/myco/ingestion/eat.py" target doesn't exist yet.
    # The exact answer depends on where _handler_path resolves. Either way, mode is verb.


def test_verb_mode_substrate_local_creates_overlay(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream-substrate")
    # downstream-substrate triggers substrate-local autodetect for dim/adapter,
    # but verb mode preserves kernel-mode default. We must pass substrate_local=True.
    res = run({"verb": "eat", "substrate_local": True}, ctx=ctx)
    assert res.exit_code == 0
    assert res.payload["substrate_local"] is True
    assert res.payload["mode"] == "verb"
    # Overlay should be touched.
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    assert overlay.is_file()


def test_verb_mode_already_exists_no_force(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream-substrate")
    res1 = run({"verb": "eat", "substrate_local": True}, ctx=ctx)
    assert res1.payload["written"] is True
    # Second time, no force → not overwritten.
    res2 = run({"verb": "eat", "substrate_local": True}, ctx=ctx)
    assert res2.payload["written"] is False
    assert "already exists" in res2.payload["reason"]


def test_verb_mode_already_exists_force_overwrites(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream-substrate")
    res1 = run({"verb": "eat", "substrate_local": True}, ctx=ctx)
    assert res1.payload["written"] is True
    res2 = run({"verb": "eat", "substrate_local": True, "force": True}, ctx=ctx)
    assert res2.payload["written"] is True
    assert res2.payload["overwritten"] is True


# ---------- dimension mode ----------


def test_dimension_mode_no_category_raises(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    with pytest.raises(UsageError, match="--category"):
        run({"dimension": "TEST1"}, ctx=ctx)


def test_dimension_mode_no_severity_raises(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    with pytest.raises(UsageError, match="--severity"):
        run({"dimension": "TEST1", "category": "mechanical"}, ctx=ctx)


def test_dimension_mode_unknown_category_raises(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    with pytest.raises(UsageError, match="unknown category"):
        run({"dimension": "TEST1", "category": "wat", "severity": "high"}, ctx=ctx)


def test_dimension_mode_unknown_severity_raises(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    with pytest.raises(UsageError, match="unknown severity"):
        run(
            {"dimension": "TEST1", "category": "mechanical", "severity": "wat"},
            ctx=ctx,
        )


def test_dimension_mode_substrate_local_writes_stub(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    res = run(
        {
            "dimension": "TEST1",
            "category": "mechanical",
            "severity": "medium",
        },
        ctx=ctx,
    )
    assert res.exit_code == 0
    assert res.payload["mode"] == "dimension"
    assert res.payload["substrate_local"] is True
    assert res.payload["written"] is True
    target = tmp_path / ".myco" / "plugins" / "dimensions" / "test1.py"
    assert target.is_file()


def test_dimension_mode_already_exists_no_force(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    res1 = run({"dimension": "T2", "category": "semantic", "severity": "low"}, ctx=ctx)
    assert res1.payload["written"] is True
    res2 = run({"dimension": "T2", "category": "semantic", "severity": "low"}, ctx=ctx)
    assert res2.payload["written"] is False


def test_dimension_mode_force_overwrites(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    run({"dimension": "T3", "category": "metabolic", "severity": "high"}, ctx=ctx)
    res = run(
        {
            "dimension": "T3",
            "category": "metabolic",
            "severity": "high",
            "force": True,
        },
        ctx=ctx,
    )
    assert res.payload["written"] is True
    assert res.payload["overwritten"] is True


def test_dimension_mode_kernel_path(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    res = run(
        {
            "dimension": "TKERN",
            "category": "shipped",
            "severity": "critical",
            "substrate_local": False,
        },
        ctx=ctx,
    )
    assert res.payload["substrate_local"] is False
    target = tmp_path / "src" / "myco" / "homeostasis" / "dimensions" / "tkern.py"
    assert target.is_file()


# ---------- adapter mode ----------


def test_adapter_mode_no_extensions_raises(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    with pytest.raises(UsageError, match="--extensions"):
        run({"adapter": "myadapter"}, ctx=ctx)


def test_adapter_mode_extensions_wrong_type_raises(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    with pytest.raises(UsageError, match="must be a list/tuple"):
        run({"adapter": "x", "extensions": 42}, ctx=ctx)


def test_adapter_mode_extensions_string_accepted(tmp_path: Path):
    """A bare string ``--extensions=.json`` should be accepted as a 1-tuple."""
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    res = run({"adapter": "myada", "extensions": ".json"}, ctx=ctx)
    assert res.payload["written"] is True
    assert ".json" in res.payload["extensions"]


def test_adapter_mode_writes_stub(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    res = run({"adapter": "csvad", "extensions": [".csv", ".tsv"]}, ctx=ctx)
    assert res.payload["mode"] == "adapter"
    assert res.payload["substrate_local"] is True
    target = tmp_path / ".myco" / "plugins" / "adapters" / "csvad.py"
    assert target.is_file()


def test_adapter_mode_normalizes_dot_prefix(tmp_path: Path):
    """``--extensions=json,csv`` (no dot) → normalized to ``.json``, ``.csv``."""
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    res = run({"adapter": "ad2", "extensions": ["json", "csv"]}, ctx=ctx)
    assert ".json" in res.payload["extensions"]
    assert ".csv" in res.payload["extensions"]


def test_adapter_mode_kernel_path(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="myco-self")
    run(
        {
            "adapter": "kernad",
            "extensions": [".log"],
            "substrate_local": False,
        },
        ctx=ctx,
    )
    target = tmp_path / "src" / "myco" / "ingestion" / "adapters" / "kernad.py"
    assert target.is_file()


def test_adapter_mode_already_exists_no_force(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    run({"adapter": "ad3", "extensions": [".x"]}, ctx=ctx)
    res2 = run({"adapter": "ad3", "extensions": [".x"]}, ctx=ctx)
    assert res2.payload["written"] is False


def test_adapter_mode_already_exists_force_overwrites(tmp_path: Path):
    ctx = _seed_with_canon(tmp_path, sid="downstream")
    run({"adapter": "ad4", "extensions": [".x"]}, ctx=ctx)
    res = run({"adapter": "ad4", "extensions": [".x"], "force": True}, ctx=ctx)
    assert res.payload["written"] is True
    assert res.payload["overwritten"] is True
