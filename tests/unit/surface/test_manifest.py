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


# v0.5.13: ``MYCO_PROJECT_DIR`` env var fallback — the middle rung of
# the substrate-resolution chain (explicit arg > env > cwd). Exists so
# MCP hosts that ignore the ``cwd`` field in their mcpServers config
# (Claude Desktop is the known offender; others likely do the same)
# can still pin a substrate through the universally-supported ``env``
# field. Three tests cover the three precedence outcomes.


def test_build_context_uses_myco_project_dir_env(
    genesis_substrate: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When no explicit ``project_dir`` is given, ``MYCO_PROJECT_DIR`` wins
    over ``Path.cwd()`` — the fix for MCP-host-without-cwd scenarios."""
    # cwd is tmp_path (NO substrate). Env points at a real substrate.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(genesis_substrate))
    ctx = build_context()
    assert ctx is not None
    assert ctx.substrate.root == genesis_substrate.resolve()


def test_build_context_explicit_arg_beats_env(
    genesis_substrate: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Explicit ``project_dir`` wins over ``MYCO_PROJECT_DIR``."""
    # Env points at a NON-substrate dir; explicit arg points at a real one.
    # If env took precedence we'd see SubstrateNotFound; we see success.
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(tmp_path))
    ctx = build_context(project_dir=genesis_substrate)
    assert ctx is not None
    assert ctx.substrate.root == genesis_substrate.resolve()


def test_build_context_empty_env_var_falls_through_to_cwd(
    genesis_substrate: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty or whitespace-only ``MYCO_PROJECT_DIR`` is treated as unset —
    falls through to cwd. Guards against shells that set empty strings."""
    monkeypatch.chdir(genesis_substrate)
    monkeypatch.setenv("MYCO_PROJECT_DIR", "   ")  # whitespace only
    # Also clear CLAUDE_PROJECT_DIR so it doesn't leak in and divert us
    # to a substrate we didn't ask for.
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    ctx = build_context()
    assert ctx is not None
    assert ctx.substrate.root == genesis_substrate.resolve()


# v0.5.14: ``CLAUDE_PROJECT_DIR`` is injected by Claude Code in hook
# processes. Honouring it means a shared hook + MCP setup needs zero
# Myco-specific env wiring — reusing Claude Code's own pointer.


def test_build_context_uses_claude_project_dir_env(
    genesis_substrate: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """With MYCO_PROJECT_DIR unset, ``CLAUDE_PROJECT_DIR`` is honoured."""
    monkeypatch.chdir(tmp_path)  # cwd: no substrate
    monkeypatch.delenv("MYCO_PROJECT_DIR", raising=False)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(genesis_substrate))
    ctx = build_context()
    assert ctx is not None
    assert ctx.substrate.root == genesis_substrate.resolve()


def test_build_context_myco_env_wins_over_claude_env(
    genesis_substrate: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When both envs are set, MYCO_PROJECT_DIR wins — the explicit Myco
    pointer must override the Claude-Code-injected one."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(genesis_substrate))
    # CLAUDE_PROJECT_DIR points at a NON-substrate dir; if it won, we'd
    # see SubstrateNotFound.
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    ctx = build_context()
    assert ctx is not None
    assert ctx.substrate.root == genesis_substrate.resolve()


def test_substrate_not_found_message_lists_every_tried_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error message enumerates every detection path that was tried, so
    operators can tell WHICH level of the chain failed (v0.5.14)."""
    from myco.core.errors import SubstrateNotFound

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MYCO_PROJECT_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)

    with pytest.raises(SubstrateNotFound) as exc_info:
        build_context()
    msg = str(exc_info.value)
    # Shows cwd since no env was set.
    assert "cwd" in msg
    # Suggests the three fix paths.
    assert "germinate" in msg
    assert "MYCO_PROJECT_DIR" in msg
    assert "roots/list" in msg


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


# ---------------------------------------------------------------------------
# v0.5.24 regressions
# ---------------------------------------------------------------------------


def test_v0_5_24_no_mcp_tool_aliases() -> None:
    """v0.5.24 dropped the MCP alias surface: every legacy tool name
    (``myco_session_end``, ``myco_reflect``, ``myco_distill``, etc.)
    was a duplicate of its canonical counterpart, and Glama's TDQS
    min-dimension penalty dragged the server score because the
    deprecated aliases inherited weaker descriptions. CLI aliases
    (``aliases:``) remain — they keep the fungal-vocabulary migration
    promise for shell users. Only the MCP-tool aliases
    (``mcp_tool_aliases:``) were removed. This test guards against
    accidental reintroduction.
    """
    m = load_manifest()
    offenders = [c.name for c in m.commands if c.mcp_tool_aliases]
    assert not offenders, (
        "v0.5.24 removed all MCP tool aliases; these commands still "
        f"carry mcp_tool_aliases: {offenders}"
    )


def test_v0_5_24_excrete_is_present() -> None:
    """v0.5.24 added the ``myco_excrete`` ingestion verb for raw-note
    deletion with audit tombstone. Regression guard against accidental
    removal.
    """
    m = load_manifest()
    names = {c.name for c in m.commands}
    assert "excrete" in names, (
        "v0.5.24 requires the 'excrete' verb; manifest has: "
        f"{sorted(names)}"
    )
    excrete = m.by_name("excrete")
    assert excrete.mcp_tool == "myco_excrete"
    assert excrete.subsystem == "ingestion"
    # Contract: note-id + reason are required, dry-run is optional.
    arg_names = {a.name for a in excrete.args}
    assert {"note-id", "reason", "dry-run"} <= arg_names
    required = {a.name for a in excrete.args if a.required}
    assert required == {"note-id", "reason"}


def test_v0_5_24_examples_populated_on_high_value_args() -> None:
    """v0.5.24 threaded manifest ``examples: [...]`` into the MCP JSON
    schema to lift Glama's parameterSemantics dimension. Not every arg
    needs an example (bare bools like ``--dry-run`` are
    self-explanatory), but every ``path`` and every required
    non-bool arg should ship at least one. Regression guard: refuse to
    let a future PR drop all examples off a critical arg without
    noticing.
    """
    m = load_manifest()
    # Sample of args where an example is load-bearing for agent UX.
    must_have_examples = {
        ("germinate", "project-dir"),
        ("germinate", "substrate-id"),
        ("eat", "content"),
        ("eat", "path"),
        ("eat", "url"),
        ("sense", "query"),
        ("excrete", "note-id"),
        ("excrete", "reason"),
        ("assimilate", "note-id"),
        ("digest", "note-id"),
        ("sporulate", "slug"),
        ("propagate", "dst"),
        ("molt", "contract"),
        ("winnow", "proposal"),
        ("fruit", "topic"),
    }
    missing: list[tuple[str, str]] = []
    for cmd_name, arg_name in must_have_examples:
        cmd = m.by_name(cmd_name)
        arg = next((a for a in cmd.args if a.name == arg_name), None)
        if arg is None or not arg.examples:
            missing.append((cmd_name, arg_name))
    assert not missing, (
        "v0.5.24 expects Field(examples=[...]) on these args; missing: "
        f"{missing}"
    )


def test_v0_5_24_mcp_schema_embeds_examples() -> None:
    """Downstream verification: the MCP handler signature wraps arg
    annotations in ``Annotated[T, Field(description=..., examples=...)]``
    so pydantic emits ``examples`` into the JSON schema. Without this
    thread, the manifest ``examples:`` key would be a dead letter.
    """
    import json

    from pydantic import TypeAdapter

    from myco.surface.mcp import _build_handler_signature

    m = load_manifest()
    excrete = m.by_name("excrete")
    sig = _build_handler_signature(excrete)
    note_id_param = sig.parameters["note_id"]
    sch = TypeAdapter(note_id_param.annotation).json_schema()
    assert "examples" in sch, f"no examples in schema: {json.dumps(sch)}"
    assert sch["examples"], "examples list is empty in emitted schema"
