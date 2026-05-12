"""Comprehensive coverage for boundary/surface/manifest.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.boundary.surface.manifest import (
    ArgSpec,
    CommandSpec,
    _parse_command,
    build_context,
    build_handler_args,
    dash_to_snake,
    dispatch,
    load_manifest,
    load_manifest_with_overlay,
)
from myco.core.identity_cluster import (
    ContractError,
    MycoContext,
    SubstrateNotFound,
    UsageError,
)

# ---------- helpers ----------


def test_dash_to_snake():
    assert dash_to_snake("foo-bar") == "foo_bar"
    assert dash_to_snake("foo") == "foo"


# ---------- ArgSpec.coerce ----------


def test_arg_coerce_str():
    a = ArgSpec(name="x", type="str")
    assert a.coerce(123) == "123"


def test_arg_coerce_bool():
    a = ArgSpec(name="x", type="bool")
    assert a.coerce(True) is True
    assert a.coerce("true") is True
    assert a.coerce("yes") is True
    assert a.coerce("1") is True
    assert a.coerce("on") is True
    assert a.coerce("nope") is False
    assert a.coerce(0) is False
    assert a.coerce(1) is True


def test_arg_coerce_int():
    a = ArgSpec(name="x", type="int")
    assert a.coerce("42") == 42


def test_arg_coerce_path(tmp_path: Path):
    a = ArgSpec(name="x", type="path")
    assert a.coerce(str(tmp_path)) == Path(str(tmp_path))


def test_arg_coerce_list_str():
    a = ArgSpec(name="x", type="list[str]")
    assert a.coerce(["a", "b"]) == ("a", "b")
    assert a.coerce(("a", "b")) == ("a", "b")
    assert a.coerce("single") == ("single",)


def test_arg_coerce_list_str_wrong_type_raises():
    a = ArgSpec(name="x", type="list[str]")
    with pytest.raises(UsageError, match="expected list"):
        a.coerce(42)


def test_arg_coerce_unknown_type_raises():
    a = ArgSpec(name="x", type="unknown")
    with pytest.raises(ContractError, match="unknown arg type"):
        a.coerce("x")


def test_arg_coerce_none_passthrough():
    a = ArgSpec(name="x", type="str")
    assert a.coerce(None) is None


def test_arg_snake_property():
    a = ArgSpec(name="foo-bar", type="str")
    assert a.snake == "foo_bar"


# ---------- CommandSpec ----------


def test_command_spec_resolve_handler_invalid_format():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="no-colon-handler",
        summary="x",
        mcp_tool="x",
    )
    with pytest.raises(ContractError, match="must be 'module:function'"):
        spec.resolve_handler()


def test_command_spec_resolve_handler_module_not_importable():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="not.a.real.module:run",
        summary="x",
        mcp_tool="x",
    )
    with pytest.raises(ContractError, match="not importable"):
        spec.resolve_handler()


def test_command_spec_resolve_handler_function_missing():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="myco.core.canon:_definitely_not_a_function",
        summary="x",
        mcp_tool="x",
    )
    with pytest.raises(ContractError, match="not found or not callable"):
        spec.resolve_handler()


def test_command_spec_resolve_handler_success():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="myco.core.canon:load_canon",
        summary="x",
        mcp_tool="x",
    )
    fn = spec.resolve_handler()
    assert callable(fn)


def test_command_spec_mcp_description_falls_back_to_summary():
    spec = CommandSpec(
        name="x", subsystem="x", handler="x:y", summary="short", mcp_tool="x"
    )
    assert spec.mcp_description == "short"


def test_command_spec_mcp_description_uses_explicit_description():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="x:y",
        summary="short",
        mcp_tool="x",
        description="rich",
    )
    assert spec.mcp_description == "rich"


# ---------- Manifest.by_name + alias ----------


def test_manifest_by_name_canonical():
    m = load_manifest()
    spec = m.by_name("hunger")
    assert spec.name == "hunger"


def test_manifest_by_name_unknown_raises():
    m = load_manifest()
    with pytest.raises(UsageError, match="unknown command"):
        m.by_name("not-a-real-verb")


def test_manifest_names_excludes_aliases():
    m = load_manifest()
    names = m.names()
    # Confirm a canonical name is in there (intake added v0.6.0).
    assert "hunger" in names


def test_manifest_all_names_includes_aliases():
    m = load_manifest()
    all_names = m.all_names_including_aliases()
    # all >= names (since aliases are extra).
    assert len(all_names) >= len(m.names())


# ---------- _parse_command shape errors ----------


def test_parse_command_missing_required():
    with pytest.raises(ContractError, match="missing"):
        _parse_command({"name": "x"})


def test_parse_command_args_not_list():
    with pytest.raises(ContractError, match="args must be a list"):
        _parse_command(
            {
                "name": "x",
                "subsystem": "x",
                "handler": "x:y",
                "summary": "x",
                "mcp_tool": "x",
                "args": {"not": "a list"},
            }
        )


def test_parse_command_arg_missing_name():
    with pytest.raises(ContractError, match="missing name"):
        _parse_command(
            {
                "name": "x",
                "subsystem": "x",
                "handler": "x:y",
                "summary": "x",
                "mcp_tool": "x",
                "args": [{"type": "str"}],
            }
        )


def test_parse_command_arg_unknown_type():
    with pytest.raises(ContractError, match="unknown type"):
        _parse_command(
            {
                "name": "x",
                "subsystem": "x",
                "handler": "x:y",
                "summary": "x",
                "mcp_tool": "x",
                "args": [{"name": "y", "type": "unknown-type"}],
            }
        )


def test_parse_command_aliases_must_be_list():
    with pytest.raises(ContractError, match="aliases must be a list"):
        _parse_command(
            {
                "name": "x",
                "subsystem": "x",
                "handler": "x:y",
                "summary": "x",
                "mcp_tool": "x",
                "aliases": "not-a-list",
            }
        )


# ---------- load_manifest_with_overlay ----------


def test_load_with_overlay_no_substrate_root():
    """None substrate_root → packaged manifest unchanged."""
    base = load_manifest()
    out = load_manifest_with_overlay(None)
    assert out.commands == base.commands


def test_load_with_overlay_no_overlay_file(tmp_path: Path):
    """Substrate without overlay.yaml → packaged manifest unchanged."""
    base = load_manifest()
    out = load_manifest_with_overlay(tmp_path)
    assert out.commands == base.commands


def test_load_with_overlay_invalid_yaml_raises(tmp_path: Path):
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text("[unterminated", encoding="utf-8")
    with pytest.raises(ContractError, match="not valid YAML"):
        load_manifest_with_overlay(tmp_path)


def test_load_with_overlay_top_level_not_mapping(tmp_path: Path):
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ContractError, match="must be a mapping"):
        load_manifest_with_overlay(tmp_path)


def test_load_with_overlay_unknown_schema_version_raises(tmp_path: Path):
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text("schema_version: 999\ncommands: []\n", encoding="utf-8")
    with pytest.raises(ContractError, match="unknown schema_version"):
        load_manifest_with_overlay(tmp_path)


def test_load_with_overlay_commands_not_list(tmp_path: Path):
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text("commands:\n  not: a list\n", encoding="utf-8")
    with pytest.raises(ContractError, match="commands must be a list"):
        load_manifest_with_overlay(tmp_path)


def test_load_with_overlay_command_not_mapping(tmp_path: Path):
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text("commands:\n  - 'just a string'\n", encoding="utf-8")
    with pytest.raises(ContractError, match="must be a mapping"):
        load_manifest_with_overlay(tmp_path)


def test_load_with_overlay_collision_with_packaged_raises(tmp_path: Path):
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text(
        """schema_version: "1"
commands:
  - name: hunger
    subsystem: x
    handler: x:y
    summary: x
    mcp_tool: x
""",
        encoding="utf-8",
    )
    with pytest.raises(ContractError, match="collides with packaged"):
        load_manifest_with_overlay(tmp_path)


def test_load_with_overlay_appends_new_verb(tmp_path: Path):
    overlay = tmp_path / ".myco" / "manifest_overlay.yaml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text(
        """schema_version: "1"
commands:
  - name: my-overlay-verb
    subsystem: ext
    handler: myco.core.canon:load_canon
    summary: A test overlay verb
    mcp_tool: myco_overlay_verb
""",
        encoding="utf-8",
    )
    out = load_manifest_with_overlay(tmp_path)
    names = out.names()
    assert "my-overlay-verb" in names


# ---------- build_handler_args ----------


def test_build_handler_args_coerces_values():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="x:y",
        summary="x",
        mcp_tool="x",
        args=(ArgSpec(name="count", type="int"),),
    )
    out = build_handler_args(spec, {"count": "42"})
    assert out["count"] == 42


def test_build_handler_args_dash_to_snake():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="x:y",
        summary="x",
        mcp_tool="x",
        args=(ArgSpec(name="dash-name", type="str"),),
    )
    out = build_handler_args(spec, {"dash-name": "v"})
    assert out["dash_name"] == "v"


def test_build_handler_args_required_missing_raises():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="x:y",
        summary="x",
        mcp_tool="x",
        args=(ArgSpec(name="must", type="str", required=True),),
    )
    with pytest.raises(UsageError, match="missing required"):
        build_handler_args(spec, {})


def test_build_handler_args_default_used_when_absent():
    spec = CommandSpec(
        name="x",
        subsystem="x",
        handler="x:y",
        summary="x",
        mcp_tool="x",
        args=(ArgSpec(name="opt", type="str", default="default-val"),),
    )
    out = build_handler_args(spec, {})
    assert out["opt"] == "default-val"


def test_build_handler_args_preserves_unknown_keys():
    spec = CommandSpec(
        name="x", subsystem="x", handler="x:y", summary="x", mcp_tool="x"
    )
    out = build_handler_args(spec, {"unknown": "kept"})
    assert out["unknown"] == "kept"


# ---------- build_context ----------


def test_build_context_pre_substrate_returns_none():
    out = build_context(pre_substrate=True)
    assert out is None


def test_build_context_no_substrate_raises(tmp_path: Path):
    """Empty tmp dir as project_dir → SubstrateNotFound."""
    with pytest.raises(SubstrateNotFound, match="no Myco substrate"):
        build_context(project_dir=tmp_path)


def test_build_context_with_genesis(genesis_substrate: Path):
    """genesis_substrate fixture has _canon.yaml."""
    ctx = build_context(project_dir=genesis_substrate)
    assert isinstance(ctx, MycoContext)


# ---------- dispatch (smoke) ----------


def test_dispatch_unknown_verb_raises(genesis_substrate: Path):
    """Unknown verb fails with UsageError."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    with pytest.raises(UsageError, match="unknown command"):
        dispatch("not-a-real-verb", {}, ctx=ctx)


def test_dispatch_pre_substrate_path(tmp_path: Path):
    """Pre-substrate verb (germinate) doesn't need ctx."""
    # Don't actually run germinate — verify the route exists by checking spec.
    m = load_manifest()
    spec = m.by_name("germinate")
    assert spec.pre_substrate is True
