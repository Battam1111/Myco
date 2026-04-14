"""Manifest-driven MCP server.

Each manifest verb becomes one FastMCP tool with a JSON-schema input
derived from the verb's ``args`` list. Tool return is a dict with
``exit_code`` and ``payload``.

The MCP layer is a pure adapter — all work happens inside the same
dispatcher the CLI uses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .manifest import CommandSpec, Manifest, dispatch, load_manifest

__all__ = ["build_server", "build_tool_spec"]


_PY_TYPE_MAP = {
    "str": "string",
    "bool": "boolean",
    "int": "integer",
    "path": "string",
    "list[str]": "array",
}


def build_tool_spec(spec: CommandSpec) -> dict[str, Any]:
    """Return a FastMCP-compatible tool description for ``spec``.

    Not coupled to the MCP SDK: returns a plain dict, so tests can
    inspect without importing MCP transport code.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []
    for arg in spec.args:
        json_type = _PY_TYPE_MAP[arg.type]
        prop: dict[str, Any] = {"type": json_type, "description": arg.help}
        if arg.type == "list[str]":
            prop["items"] = {"type": "string"}
        properties[arg.snake] = prop
        if arg.required:
            required.append(arg.snake)
    return {
        "name": spec.mcp_tool,
        "description": spec.summary,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def _invoke(spec: CommandSpec, manifest: Manifest, args: Mapping[str, Any]) -> dict[str, Any]:
    result = dispatch(
        spec.name,
        args,
        manifest=manifest,
    )
    return {
        "exit_code": result.exit_code,
        "payload": _jsonable(result.payload),
    }


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def build_server(manifest: Manifest | None = None):  # pragma: no cover - integration
    """Construct a FastMCP server with one tool per manifest verb.

    Import of :mod:`mcp.server.fastmcp` is deferred to call-time so the
    rest of the package remains importable without the MCP SDK.
    """
    from mcp.server.fastmcp import FastMCP

    m = manifest or load_manifest()
    server = FastMCP("myco")
    for spec in m.commands:
        tool = build_tool_spec(spec)

        def _make_handler(spec_local: CommandSpec):
            def _handler(**kwargs: Any) -> dict[str, Any]:
                return _invoke(spec_local, m, kwargs)

            _handler.__name__ = spec_local.mcp_tool
            _handler.__doc__ = spec_local.summary
            return _handler

        server.add_tool(
            _make_handler(spec),
            name=tool["name"],
            description=tool["description"],
        )
    return server
