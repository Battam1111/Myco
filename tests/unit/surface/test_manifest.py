"""Tests for ``myco.surface.manifest``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError
from myco.surface.manifest import (
    ArgSpec,
    CommandSpec,
    build_context,
    build_handler_args,
    dash_to_snake,
    dispatch,
    load_manifest,
)


def test_dash_to_snake() -> None:
    assert dash_to_snake("project-dir") == "project_dir"
    assert dash_to_snake("abc") == "abc"


def test_load_manifest_has_every_v0_5_verb() -> None:
    """v0.5 expanded from 12 verbs (v0.4) to 16 — added governance
    verbs (craft/bump/evolve) plus scaffold. v0.5.3 renamed 9 verbs
    to fungal-bionic canonical names but kept every old name as an
    alias so this still resolves. Kept as an at-least-these set so a
    future minor release adding a new verb does not force a test
    edit (the inverse direction, "every handler resolves", is covered
    by :func:`test_every_handler_resolves` below)."""
    m = load_manifest()
    assert m.schema_version == "1"
    # Every v0.5 invokable name (canonical + alias) — v0.5.3 aliases
    # the pre-rename names; ``all_names_including_aliases`` surfaces
    # both axes of the compatibility surface.
    all_names = set(m.all_names_including_aliases())
    must_have = {
        # v0.4 set (now aliases post-v0.5.3 rename).
        "genesis",
        "hunger",
        "eat",
        "sense",
        "forage",
        "reflect",
        "digest",
        "distill",
        "perfuse",
        "propagate",
        "immune",
        "session-end",
        # v0.5 governance + scaffold (aliases post-v0.5.3 rename).
        "craft",
        "bump",
        "evolve",
        "scaffold",
    }
    missing = must_have - all_names
    assert not missing, f"manifest missing verbs: {sorted(missing)}"


def test_every_handler_resolves() -> None:
    m = load_manifest()
    for spec in m.commands:
        handler = spec.resolve_handler()
        assert callable(handler)


def test_genesis_is_pre_substrate() -> None:
    m = load_manifest()
    g = m.by_name("genesis")
    assert g.pre_substrate is True


def test_by_name_unknown_raises() -> None:
    m = load_manifest()
    with pytest.raises(UsageError, match="unknown command"):
        m.by_name("not-a-verb")


def test_arg_coercion_str() -> None:
    a = ArgSpec(name="x", type="str")
    assert a.coerce("hello") == "hello"
    assert a.coerce(7) == "7"
    assert a.coerce(None) is None


def test_arg_coercion_bool() -> None:
    a = ArgSpec(name="x", type="bool")
    assert a.coerce(True) is True
    assert a.coerce("yes") is True
    assert a.coerce("no") is False
    assert a.coerce(1) is True


def test_arg_coercion_bool_string_literals() -> None:
    """v0.5.7 test-coverage closure: the str→bool path accepts the full
    four-way vocabulary (`1 / true / yes / on` → True) and rejects
    everything else (→ False). Previously only ``"yes"``/``"no"`` were
    covered, so a downstream substrate writing ``--quick=true`` via a
    manifest overlay would have been rejected silently on first test.
    """
    a = ArgSpec(name="x", type="bool")
    # The four affirmative literals that ``ArgSpec.coerce`` knows.
    for truthy in ("1", "true", "yes", "on", "TRUE", "YES", "On"):
        assert a.coerce(truthy) is True, f"truthy literal {truthy!r}"
    # Everything else — empty, "0", "false", whitespace, garbage.
    for falsy in ("0", "false", "no", "off", "", " ", "garbage", "None"):
        assert a.coerce(falsy) is False, f"falsy literal {falsy!r}"


def test_arg_coercion_bool_none_returns_none() -> None:
    """``None`` passes through as ``None`` (not coerced to False),
    preserving the "unset vs explicitly false" distinction the
    dispatcher relies on.
    """
    a = ArgSpec(name="x", type="bool")
    assert a.coerce(None) is None


def test_arg_coercion_path() -> None:
    a = ArgSpec(name="x", type="path")
    assert a.coerce("/tmp") == Path("/tmp")


def test_arg_coercion_list() -> None:
    a = ArgSpec(name="x", type="list[str]")
    assert a.coerce(["a", "b"]) == ("a", "b")
    assert a.coerce("only") == ("only",)
    with pytest.raises(UsageError):
        a.coerce(42)


def test_build_handler_args_defaults_and_required() -> None:
    spec = CommandSpec(
        name="x",
        subsystem="s",
        handler="m:f",
        summary="",
        mcp_tool="tx",
        args=(
            ArgSpec(name="a", type="str", required=True),
            ArgSpec(name="b", type="bool", default=False),
        ),
    )
    out = build_handler_args(spec, {"a": "hello"})
    assert out["a"] == "hello"
    assert out["b"] is False
    with pytest.raises(UsageError, match="missing required"):
        build_handler_args(spec, {})


def test_build_context_pre_substrate_returns_none() -> None:
    assert build_context(pre_substrate=True) is None


def test_build_context_raises_when_no_substrate(tmp_path: Path) -> None:
    # v0.5.10: ``SubstrateNotFound`` (exit 4) not ``UsageError`` (exit 3),
    # preserving the v0.5.8 exit-code differentiation that the earlier
    # UsageError-wrap silently broke.
    from myco.core.errors import SubstrateNotFound

    with pytest.raises(SubstrateNotFound, match="no Myco substrate") as exc_info:
        build_context(project_dir=tmp_path)
    assert exc_info.value.exit_code == 4


def test_build_context_happy_path(genesis_substrate: Path) -> None:
    ctx = build_context(project_dir=genesis_substrate)
    assert ctx is not None
    assert ctx.substrate.root == genesis_substrate.resolve()


def test_dispatch_runs_handler(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = dispatch("eat", {"content": "hi"}, ctx=ctx)
    assert isinstance(result, Result)
    assert result.exit_code == 0


def test_dispatch_pre_substrate_genesis(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    target.mkdir()
    result = dispatch(
        "genesis",
        {"project-dir": str(target), "substrate-id": "brandnew"},
    )
    assert result.exit_code == 0
    assert (target / "_canon.yaml").is_file()


def test_dispatch_unknown_verb() -> None:
    with pytest.raises(UsageError, match="unknown command"):
        dispatch("not-a-verb", {})
