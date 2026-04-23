"""Tests for ``myco.cycle.graft`` — substrate-local plugin introspection.

Graft has three mutually-exclusive modes (``--list`` / ``--validate`` /
``--explain <name>``). This file covers:

* mode-dispatch semantics (usage errors on no-mode / multi-mode),
* the ``--list`` payload shape (every built-in dimension + every
  built-in adapter shows up with kind/name/source),
* the ``--validate`` pass on a clean substrate (no errors, returns
  zero),
* the ``--explain`` pass for known and unknown plugin names.

Coverage gap closed at v0.5.7 — graft had 0% test coverage before.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.cycle.graft import run as graft_run


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


# ---------------------------------------------------------------------------
# Mode dispatch — usage errors
# ---------------------------------------------------------------------------


def test_no_mode_raises_usage_error(genesis_substrate: Path) -> None:
    """Passing no flag is a usage error — must specify one of the
    three modes explicitly."""
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="specify exactly one"):
        graft_run({}, ctx=ctx)


def test_two_modes_at_once_raises(genesis_substrate: Path) -> None:
    """The three modes are mutually exclusive."""
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        graft_run({"list": True, "validate": True}, ctx=ctx)


def test_list_and_explain_at_once_raises(genesis_substrate: Path) -> None:
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        graft_run({"list": True, "explain": "M1"}, ctx=ctx)


# ---------------------------------------------------------------------------
# --list mode
# ---------------------------------------------------------------------------


def test_list_mode_enumerates_dimensions(genesis_substrate: Path) -> None:
    """--list returns every built-in dimension (M1, M2, ..., MP1, SE1,
    SE2 — 11 dimensions at v0.5.7) under kind=dimension."""
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list": True}, ctx=ctx)
    assert result.exit_code == 0
    plugins = result.payload["plugins"]
    dim_names = {p["name"] for p in plugins if p["kind"] == "dimension"}
    # A few representative dimensions that must be present.
    assert {"M1", "MP1", "SE1", "MB1"} <= dim_names


def test_list_mode_enumerates_adapters(genesis_substrate: Path) -> None:
    """--list returns built-in adapters under kind=adapter."""
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list": True}, ctx=ctx)
    kinds = {p["kind"] for p in result.payload["plugins"]}
    # Adapter kind present means the ingestion module loaded.
    assert "adapter" in kinds


def test_list_mode_every_plugin_has_shape(genesis_substrate: Path) -> None:
    """Every plugin entry has keys: kind, name, source, scope."""
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list": True}, ctx=ctx)
    for entry in result.payload["plugins"]:
        # v0.5.22: ``scope`` is now part of the shape so downstream
        # callers (hunger, brief) can filter kernel vs substrate.
        assert set(entry.keys()) >= {"kind", "name", "source", "scope"}
        assert entry["kind"] in {
            "dimension",
            "adapter",
            "schema_upgrader",
            "overlay_verb",
        }
        assert entry["scope"] in {"kernel", "substrate"}


# ---------------------------------------------------------------------------
# v0.5.22 — scope classification (the bug #4 fix).
# ---------------------------------------------------------------------------


def test_list_on_fresh_substrate_classifies_everything_as_kernel(
    genesis_substrate: Path,
) -> None:
    """A fresh substrate has no ``.myco/plugins/``. Every loaded
    dimension/adapter/schema_upgrader lives in the installed myco
    package (kernel), so ``scope`` must be ``"kernel"`` for all.
    Pre-v0.5.22 hunger/brief counted these as "local plugins" — the
    absence of a single ``substrate``-scoped entry is what makes the
    count correctly zero."""
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list": True}, ctx=ctx)
    substrate_scoped = [
        e for e in result.payload["plugins"] if e["scope"] == "substrate"
    ]
    assert substrate_scoped == [], substrate_scoped


def test_scope_classification_maps_kernel_path_correctly(
    genesis_substrate: Path,
) -> None:
    """Unit check on the ``_classify_scope`` inner closure via its
    observable effect: given a fresh substrate, every registered
    dimension's ``source`` path is under site-packages / the installed
    myco package, never under ``<root>/.myco/plugins/``. The classifier
    must therefore label all of them ``"kernel"``.

    (A full round-trip test that creates a local dimension + verifies
    the ``"substrate"`` label is in ``tests/integration/`` — it needs
    a real ``ramify``/reload cycle that unit tests can't cleanly
    stage without cross-process plugin-module caching quirks.)
    """
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list": True}, ctx=ctx)
    plugins = result.payload["plugins"]
    assert len(plugins) > 0  # at least the kernel 32-ish are present
    for entry in plugins:
        # Fresh substrate has no .myco/plugins/; every entry's source
        # must live elsewhere and thus classify as kernel.
        if entry["source"] == "<unknown>":
            assert entry["scope"] == "kernel"
        else:
            src = entry["source"].replace("\\", "/")
            assert ".myco/plugins/" not in src, (entry["name"], src)
            assert entry["scope"] == "kernel", (entry["name"], src)


# ---------------------------------------------------------------------------
# --validate mode
# ---------------------------------------------------------------------------


def test_validate_clean_substrate_returns_zero(genesis_substrate: Path) -> None:
    """On a fresh substrate with no .myco/plugins/, --validate exits 0
    with an empty errors list."""
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"validate": True}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["errors"] == []


def test_validate_reports_errors_key_in_payload(genesis_substrate: Path) -> None:
    """Payload always has an ``errors`` list (possibly empty)."""
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"validate": True}, ctx=ctx)
    assert "errors" in result.payload
    assert isinstance(result.payload["errors"], list)


# ---------------------------------------------------------------------------
# --explain mode
# ---------------------------------------------------------------------------


def test_explain_known_dimension_returns_details(genesis_substrate: Path) -> None:
    """--explain M1 → a payload describing the M1 dimension.

    Payload shape is ``{mode: "explain", name, kind, source, docstring}``
    with the explanation fields spread at top level (not nested under
    an ``explanation`` key).
    """
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"explain": "M1"}, ctx=ctx)
    assert result.exit_code == 0
    payload = result.payload
    assert payload["mode"] == "explain"
    assert payload["name"] == "M1"
    assert payload["kind"] == "dimension"
    assert payload["source"] != ""
    # M1 has a non-empty class docstring.
    assert payload["docstring"]


def test_explain_unknown_name_raises(genesis_substrate: Path) -> None:
    """--explain <missing> is a usage error pointing at --list."""
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="unknown plugin name"):
        graft_run({"explain": "NONEXISTENT_DIM"}, ctx=ctx)


# ---------------------------------------------------------------------------
# Result payload integration
# ---------------------------------------------------------------------------


def test_list_result_has_count_field(genesis_substrate: Path) -> None:
    """--list exposes a ``count`` for cheap summaries."""
    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list": True}, ctx=ctx)
    assert "count" in result.payload
    assert result.payload["count"] == len(result.payload["plugins"])
    # Sanity: at least the 11 built-in dimensions plus some adapters.
    assert result.payload["count"] >= 11


# ---------------------------------------------------------------------------
# v0.5.16: --list-substrates (cross-project registry enumeration)
# ---------------------------------------------------------------------------


def test_list_substrates_returns_empty_when_registry_missing(
    tmp_path: Path,
    genesis_substrate: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no ``~/.myco/substrates.yaml`` yet, --list-substrates
    returns an empty list and count 0 — not an error."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list_substrates": True}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["mode"] == "list-substrates"
    assert result.payload["count"] == 0
    assert result.payload["substrates"] == []


def test_list_substrates_returns_registered_entries(
    tmp_path: Path,
    genesis_substrate: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pre-register two substrates; --list-substrates enumerates them."""
    from myco.core.registry import register_substrate

    # Session fixture disables registry writes; re-enable for this test.
    monkeypatch.delenv("MYCO_REGISTRY_DISABLED", raising=False)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    sub_a = tmp_path / "subA"
    sub_b = tmp_path / "subB"
    sub_a.mkdir()
    (sub_a / "_canon.yaml").write_text("x")
    sub_b.mkdir()  # no canon → stale
    register_substrate("alpha", sub_a, home=fake_home)
    register_substrate("beta", sub_b, home=fake_home)

    ctx = _mk_ctx(genesis_substrate)
    result = graft_run({"list_substrates": True}, ctx=ctx)
    assert result.exit_code == 0
    assert result.payload["count"] == 2
    assert result.payload["live_count"] == 1
    assert result.payload["stale_count"] == 1
    ids = {s["substrate_id"] for s in result.payload["substrates"]}
    assert ids == {"alpha", "beta"}


def test_list_substrates_is_mutually_exclusive_with_other_modes(
    genesis_substrate: Path,
) -> None:
    """Passing both --list and --list-substrates must raise UsageError."""
    ctx = _mk_ctx(genesis_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        graft_run({"list": True, "list_substrates": True}, ctx=ctx)
