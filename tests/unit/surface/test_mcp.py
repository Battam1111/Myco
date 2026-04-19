"""Tests for ``myco.surface.mcp``."""

from __future__ import annotations

from myco.surface.manifest import load_manifest
from myco.surface.mcp import build_tool_spec


def test_every_verb_has_tool_spec() -> None:
    m = load_manifest()
    for spec in m.commands:
        tool = build_tool_spec(spec)
        assert tool["name"] == spec.mcp_tool
        assert tool["description"] == spec.summary
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema


def test_list_arg_has_items_schema() -> None:
    m = load_manifest()
    eat = m.by_name("eat")
    tool = build_tool_spec(eat)
    assert tool["inputSchema"]["properties"]["tags"]["type"] == "array"
    assert tool["inputSchema"]["properties"]["tags"]["items"] == {"type": "string"}


def test_eat_has_content_path_and_url_properties() -> None:
    """v0.4.2: content is no longer required (path/url are alternatives)."""
    m = load_manifest()
    eat = m.by_name("eat")
    tool = build_tool_spec(eat)
    props = tool["inputSchema"]["properties"]
    assert "content" in props
    assert "path" in props
    assert "url" in props


def test_bool_and_path_types_map_correctly() -> None:
    m = load_manifest()
    genesis = m.by_name("genesis")
    tool = build_tool_spec(genesis)
    props = tool["inputSchema"]["properties"]
    assert props["project_dir"]["type"] == "string"  # path → string
    assert props["dry_run"]["type"] == "boolean"


def test_build_server_imports() -> None:
    # Just verify the function is callable; actual server transport
    # isn't exercised here.
    from myco.surface import mcp as mcp_mod

    assert callable(mcp_mod.build_server)
