"""Manifest-driven MCP server.

Each manifest verb becomes one FastMCP tool with a JSON-schema input
derived from the verb's ``args`` list. Tool return is a dict with
``exit_code``, ``payload``, and a ``substrate_pulse`` sidecar that
every MCP client — Claude Code, Cursor, Windsurf, Zed, Codex,
Gemini, Continue, Claude Desktop, and any other host — sees on
every tool call.

Why the sidecar: L1 rules R1-R7 are enforced by hooks only inside
Claude Code / Cowork. Everywhere else, the agent is alone with its
training. The pulse is a server-side push that reminds the agent of
the contract and surfaces HIGH substrate signals on EVERY tool
response, so the discipline survives across platforms. The FastMCP
``instructions`` block carries the same information at session
initialization, catching agents that check instructions before any
tool use.

The MCP layer stays a pure adapter: all substantive work runs
through the same dispatcher the CLI uses.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .manifest import CommandSpec, Manifest, dispatch, load_manifest

try:  # pyyaml is a hard dep, but load failures should not break imports
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment,unused-ignore]

__all__ = ["build_server", "build_tool_spec", "build_initialization_instructions"]


_PY_TYPE_MAP = {
    "str": "string",
    "bool": "boolean",
    "int": "integer",
    "path": "string",
    "list[str]": "array",
}


# ---------------------------------------------------------------------------
# Initialization instructions — what the agent sees on `initialize`
# ---------------------------------------------------------------------------

_INSTRUCTIONS_TEMPLATE = """\
Myco — Agent-First symbiotic cognitive substrate.

You have access to {n_verbs} verbs as MCP tools, each one a single
well-defined operation on a Myco substrate (the project directory
with _canon.yaml and MYCO.md at its root).

The Hard Contract (R1-R7, full text at
docs/architecture/L1_CONTRACT/protocol.md) governs every session:

  R1  Boot ritual      — call myco_hunger first in every session.
  R2  Session-end      — call myco_senesce (assimilate + immune --fix)
                          before compaction (PreCompact hook). On abrupt
                          exit with a ~1.5 s kill budget (SessionEnd hook)
                          call myco_senesce with quick=true — assimilate
                          only; immune runs at the next SessionStart.
  R3  Sense before     — call myco_sense before asserting a substrate
      assert              fact. Memory is not a source.
  R4  Eat insights     — capture decisions / frictions via myco_eat the
                          moment they occur.
  R5  Cross-reference  — orphan files are dead knowledge; link on
                          creation.
  R6  Write surface    — write only to paths in
                          _canon.yaml::system.write_surface.allowed.
  R7  Top-down         — L0 > L1 > L2 > L3 > L4. Implementation never
                          overrides contract.

Every tool response also carries a `substrate_pulse` field. Read it
on every call: it surfaces the substrate_id, current contract
version, and any HIGH reflex that is unresolved. If `pulse.rules_hint`
says "hunger not yet called this session", call myco_hunger before
your next substantive action.

Five root principles from L0 (docs/architecture/L0_VISION.md):
Only For Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 / 万物互联.
"""


def build_initialization_instructions(manifest: Manifest | None = None) -> str:
    """Return the initialization-instructions text surfaced at MCP
    ``initialize``. Exposed for tests and for any host that wants to
    inspect the contract without starting the server.
    """
    m = manifest or load_manifest()
    return _INSTRUCTIONS_TEMPLATE.format(n_verbs=len(m.commands))


# ---------------------------------------------------------------------------
# Substrate pulse — sidecar attached to every tool response
# ---------------------------------------------------------------------------


def _load_canon(project_dir: Path | None = None) -> dict[str, Any]:
    """Best-effort canon read. Never raises — the pulse degrades
    gracefully if the substrate is absent or unreadable.
    """
    if yaml is None:
        return {}
    root = project_dir or Path.cwd()
    for candidate in (root, *root.parents):
        canon_path = candidate / "_canon.yaml"
        if canon_path.exists():
            try:
                with open(canon_path, encoding="utf-8") as fh:
                    return yaml.safe_load(fh) or {}
            except Exception:
                return {}
    return {}


def _compute_substrate_pulse(
    verb: str,
    project_dir: Path | None = None,
    hunger_called: bool = False,
) -> dict[str, Any]:
    """Produce the sidecar payload attached to every tool response.

    Kept cheap — reads canon once, does not run hunger, does not
    touch notes/. The goal is a constant-time reminder that R1-R7
    exist and that the agent is inside a Myco substrate, not a
    stateless function call.
    """
    canon = _load_canon(project_dir)
    identity = canon.get("identity", {}) if isinstance(canon, dict) else {}
    rules_hint: str
    if verb == "hunger":
        rules_hint = "Boot ritual in progress."
    elif hunger_called:
        rules_hint = "R3 — call myco_sense before asserting substrate facts."
    else:
        rules_hint = (
            "R1 — call myco_hunger at session start if you have not "
            "already. Your future tool responses will tell you when "
            "it has been called."
        )
    return {
        "substrate_id": identity.get("substrate_id") or "(no substrate detected)",
        "contract_version": canon.get("contract_version") or "(unknown)",
        "hard_contract_ref": "docs/architecture/L1_CONTRACT/protocol.md",
        "rules_hint": rules_hint,
    }


# ---------------------------------------------------------------------------
# Tool-spec derivation
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Dispatch + sidecar wrap
# ---------------------------------------------------------------------------


class _ServerState:
    """Per-process state that outlives individual tool calls. Tracks
    whether ``myco_hunger`` has been invoked so subsequent responses
    can hint at R3 instead of R1.
    """

    def __init__(self) -> None:
        self.hunger_called: bool = False


def _invoke(
    spec: CommandSpec,
    manifest: Manifest,
    args: Mapping[str, Any],
    state: _ServerState,
) -> dict[str, Any]:
    result = dispatch(spec.name, args, manifest=manifest)
    if spec.name == "hunger":
        state.hunger_called = True
    project_dir_arg = args.get("project_dir")
    project_dir = Path(project_dir_arg) if project_dir_arg else None
    pulse = _compute_substrate_pulse(
        verb=spec.name,
        project_dir=project_dir,
        hunger_called=state.hunger_called,
    )
    return {
        "exit_code": result.exit_code,
        "payload": _jsonable(result.payload),
        "substrate_pulse": pulse,
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
    instructions = build_initialization_instructions(m)
    server = FastMCP("myco", instructions=instructions)
    state = _ServerState()
    for spec in m.commands:
        tool = build_tool_spec(spec)

        def _make_handler(spec_local: CommandSpec):
            def _handler(**kwargs: Any) -> dict[str, Any]:
                return _invoke(spec_local, m, kwargs, state)

            _handler.__name__ = spec_local.mcp_tool
            _handler.__doc__ = spec_local.summary
            return _handler

        # Canonical tool registration.
        server.add_tool(
            _make_handler(spec),
            name=tool["name"],
            description=tool["description"],
        )
        # v0.5.3 alias registration: every ``mcp_tool_alias`` exposes
        # the same handler under the legacy MCP tool name so existing
        # MCP clients that cached ``myco_genesis`` / ``myco_craft`` /
        # etc. keep working. Description is prefixed to advertise the
        # deprecation.
        for legacy_name in spec.mcp_tool_aliases:
            server.add_tool(
                _make_handler(spec),
                name=legacy_name,
                description=(
                    f"[deprecated alias for {spec.mcp_tool!r}] {spec.summary}"
                ),
            )
    return server
