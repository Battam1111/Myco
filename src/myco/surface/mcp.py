"""Manifest-driven MCP server.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
§ "MCP surface" (the MCP server is a first-class Agent-facing
circulation path; the pulse sidecar is the R1-R7 reminder shape).

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

import inspect
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..core.errors import SubstrateNotFound
from .manifest import CommandSpec, Manifest, dispatch, load_manifest

try:  # pyyaml is a hard dep, but load failures should not break imports
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment,unused-ignore]

# v0.5.14: FastMCP detects Context parameters via ``typing.get_type_hints``
# which resolves string annotations against module globals. Context must
# therefore live at module level. The MCP SDK is an optional extra (see
# ``pip install 'myco[mcp]'``), so fall back to a harmless stub when it
# isn't installed — in that case ``build_server`` fails on its own
# FastMCP import anyway, so the stub never feeds a real server.
try:
    from mcp.server.fastmcp import Context as _MCPContext
except Exception:  # pragma: no cover - MCP SDK not installed

    class _MCPContext:  # type: ignore[no-redef]
        """Runtime stub for the MCP ``Context`` type when the SDK is absent."""

        session: Any = None


__all__ = ["build_server", "build_tool_spec", "build_initialization_instructions"]


_PY_TYPE_MAP = {
    "str": "string",
    "bool": "boolean",
    "int": "integer",
    "path": "string",
    "list[str]": "array",
}

# v0.5.21 Python type mapping — used when building ``inspect.Signature``
# for FastMCP handlers. FastMCP inspects the handler's signature to
# derive the tool's JSON inputSchema. We map manifest types to the
# closest Python types so Pydantic (which FastMCP uses internally)
# generates useful JSON Schema properties + a proper validator.
#
# Paths arrive from MCP clients as JSON strings; the manifest's
# ``path`` type is coerced to ``Path`` by ``arg.coerce`` downstream in
# ``build_handler_args`` — the signature only needs ``str`` so MCP
# accepts the wire format. Boolean, integer, and string pass through.
_PY_RUNTIME_TYPE_MAP: dict[str, type] = {
    "str": str,
    "bool": bool,
    "int": int,
    "path": str,
    "list[str]": list,
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

**Multi-project hint (v0.5.17).** When you know which project folder
the user is working on, pass `project_dir="<absolute path>"` in every
tool call's kwargs. Hosts that don't implement the MCP `roots/list`
capability (Claude Desktop / Cowork, at time of writing) rely on this
to route to the right substrate; otherwise Myco falls through to env
vars and finally cwd, which may not match the user's workspace. The
`pulse.project_dir_source` field on every response tells you which
level of the resolution chain was used — if it says anything other
than `kwargs.project_dir` and the user is in a specific folder, pass
it explicitly next call.

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


#: Process-local cache: ``{canon_path_str: (mtime_ns, parsed_dict)}``.
#:
#: v0.5.8 (Lens 11 P1-PERF-mcp): every MCP tool response carries a
#: ``substrate_pulse`` sidecar, which means ``_load_canon`` fires on
#: every call. Re-parsing YAML is ~300 µs, which adds up on a
#: workflow that fires 500+ tool calls per session. The cache is
#: keyed on canon ``mtime_ns`` so any edit — from ``molt``, from
#: ``germinate``, from a human — invalidates automatically.
_CANON_CACHE: dict[str, tuple[int, dict[str, Any]]] = {}


def _load_canon(project_dir: Path | None = None) -> dict[str, Any]:
    """Best-effort canon read. Never raises — the pulse degrades
    gracefully if the substrate is absent or unreadable.

    v0.5.8: mtime-keyed cache. Repeated calls with an unchanged
    canon return the cached parse in O(1) after the first call.
    """
    if yaml is None:
        return {}
    root = project_dir or Path.cwd()
    for candidate in (root, *root.parents):
        canon_path = candidate / "_canon.yaml"
        if not canon_path.exists():
            continue
        try:
            mtime_ns = canon_path.stat().st_mtime_ns
        except OSError:
            return {}
        key = str(canon_path.resolve()).replace("\\", "/")
        cached = _CANON_CACHE.get(key)
        if cached is not None and cached[0] == mtime_ns:
            return cached[1]
        try:
            with open(canon_path, encoding="utf-8") as fh:
                parsed = yaml.safe_load(fh) or {}
        except Exception:
            return {}
        if not isinstance(parsed, dict):
            parsed = {}
        _CANON_CACHE[key] = (mtime_ns, parsed)
        return parsed
    return {}


def _compute_substrate_pulse(
    verb: str,
    project_dir: Path | None = None,
    hunger_called: bool = False,
    project_dir_source: str | None = None,
) -> dict[str, Any]:
    """Produce the sidecar payload attached to every tool response.

    Kept cheap — reads canon once, does not run hunger, does not
    touch notes/. The goal is a constant-time reminder that R1-R7
    exist and that the agent is inside a Myco substrate, not a
    stateless function call.

    v0.5.17: ``project_dir_source`` + ``resolved_project_dir`` are
    included in the returned dict when the caller knows them, so the
    agent can see at a glance WHICH level of the substrate-resolution
    chain answered (explicit arg / MCP roots / env var / cwd). This
    is the canonical debugging aid for the "I'm in folder X but Myco
    thinks I'm in Y" class of mystery — the pulse now says where
    Myco got its answer. Harmless when ``project_dir_source`` is
    ``None`` — the fields stay absent rather than lying.
    """
    from myco.core.trust import safe_frontmatter_field

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
    # v0.5.8 Phase 8-10: the pulse crosses the trust boundary into
    # agent prompt context on every MCP tool response, so any
    # substrate-derived scalar (substrate_id, contract_version)
    # passes through ``safe_frontmatter_field`` first — strips ANSI
    # escapes, newlines, and other prompt-injection vectors that a
    # hostile canon could plant.
    raw_substrate_id = identity.get("substrate_id") or "(no substrate detected)"
    raw_contract_version = canon.get("contract_version") or "(unknown)"
    pulse: dict[str, Any] = {
        "substrate_id": safe_frontmatter_field(str(raw_substrate_id), max_len=128),
        "contract_version": safe_frontmatter_field(
            str(raw_contract_version), max_len=64
        ),
        "hard_contract_ref": "docs/architecture/L1_CONTRACT/protocol.md",
        "rules_hint": rules_hint,
    }
    # v0.5.17: resolution transparency. Included only when we know
    # how project_dir was resolved (MCP path; CLI path leaves it None).
    if project_dir_source is not None:
        pulse["project_dir_source"] = safe_frontmatter_field(
            project_dir_source, max_len=64
        )
        pulse["resolved_project_dir"] = safe_frontmatter_field(
            str(project_dir) if project_dir else "(none — build_context picked cwd)",
            max_len=512,
        )
    return pulse


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


def _build_handler_signature(spec: CommandSpec) -> inspect.Signature:
    """Build the ``inspect.Signature`` FastMCP will introspect.

    **Why this exists (v0.5.21 hotfix).** FastMCP derives the tool's
    JSON input schema from the Python signature of the registered
    handler via :mod:`mcp.server.fastmcp.utilities.func_metadata`. The
    pre-v0.5.21 handler was declared as ``async def _handler(ctx,
    **kwargs)``. FastMCP / Pydantic interpret ``**kwargs: Any`` not as
    a varkw sink but as **a single required parameter named
    ``kwargs``** — so the emitted schema was
    ``{"required": ["kwargs"], "properties": {"kwargs": {...}}}``.
    Every MCP client saw ``myco_eat(kwargs: dict)`` instead of
    ``myco_eat(content: str?, path: str?, url: str?, ...)``. Agents
    sending flat args ``{"content": "..."}`` got a pydantic validation
    error; agents sending nested ``{"kwargs": {"content": "..."}}``
    had the ``content`` key buried inside Python's varkw sink as
    ``kwargs = {"kwargs": {"content": "..."}}``, which then surfaced
    as the dispatcher's "missing --content | --path | --url" error
    because ``build_handler_args`` only looks at the top level.

    The fix: generate a real ``inspect.Signature`` whose parameters
    match the manifest. FastMCP sees a named parameter for every
    manifest arg, the JSON schema reflects the actual verb surface,
    and varkw stops swallowing keys. The actual function body keeps
    its ``**kwargs`` varkw so Python runtime binding still works.

    We ALSO expose ``project_dir`` as a first-class optional
    parameter because :func:`_invoke`'s resolution chain treats it
    specially (level-1 override of the substrate routing — see
    ``docs/architecture/L1_CONTRACT/protocol.md`` multi-project
    pattern). Without this, agents that want to pin a non-default
    substrate can't discover the override through the tool schema.
    """
    params: list[inspect.Parameter] = [
        inspect.Parameter(
            "ctx",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=_MCPContext,
        ),
    ]
    for arg in spec.args:
        runtime_type = _PY_RUNTIME_TYPE_MAP[arg.type]
        # Optional params get ``X | None`` annotation and a default of
        # ``None`` (unless the manifest specifies one). Required params
        # get no default — Pydantic surfaces them in ``required`` in
        # the emitted JSON schema.
        if arg.required:
            annotation: Any = runtime_type
            default: Any = inspect.Parameter.empty
        else:
            annotation = runtime_type | None
            default = arg.default if arg.default is not None else None
        params.append(
            inspect.Parameter(
                arg.snake,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=annotation,
            )
        )
    # project_dir: user-facing multi-project override. Always optional;
    # _invoke pops it before dispatch so it never confuses manifest
    # handlers that don't declare it. Skip when the manifest already
    # declares it as an arg (e.g. ``germinate`` takes ``project-dir``
    # as a required positional) — duplicating would raise ValueError
    # in ``inspect.Signature.__init__``.
    already_has_project_dir = any(p.name == "project_dir" for p in params)
    if not already_has_project_dir:
        params.append(
            inspect.Parameter(
                "project_dir",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation=str | None,
            )
        )
    return inspect.Signature(params)


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


async def _invoke(
    spec: CommandSpec,
    manifest: Manifest,
    args: Mapping[str, Any],
    state: _ServerState,
    mcp_ctx: Any = None,
) -> dict[str, Any]:
    """Invoke a manifest verb from the MCP surface.

    v0.5.14 resolution chain for project_dir (highest first):

    1. ``kwargs.project_dir`` explicit argument — extracted here and
       passed as a first-class dispatch parameter so it reaches the
       handler + ``build_context``. (In v0.5.12 it was silently dropped
       by ``build_handler_args`` which filters to per-verb spec args.)
    2. **MCP ``roots/list`` from client** — async query. The MCP
       protocol defines this capability for exactly this case: host
       tells server which folder(s) the user has open. If the client
       supports it and at least one root has a substrate at or above
       it, we use that.
    3. ``MYCO_PROJECT_DIR`` env var — handled by ``build_context``.
    4. ``Path.cwd()`` — handled by ``build_context``.

    Any of 1/2 succeeding short-circuits the chain. 3/4 are
    fallbacks when neither an explicit arg nor a responsive client
    yields anything.

    v0.5.16: when the client returned a workspace root but that root
    has no substrate, Myco returns a soft response (exit_code 0) with
    a ``substrate_pulse.rules_hint`` that tells the agent to call
    ``myco_germinate --project-dir=<workspace_root>``. This fixes the
    "user opens a fresh project and Myco yells at them" class of UX
    regression. The agent relays the suggestion; the user approves;
    germinate runs. Never auto-germinates — that would be surprising.
    """
    args_in = dict(args)  # mutable copy; we may pop/overwrite project_dir

    # v0.5.17: centralise the full resolution chain here (was split
    # between _invoke and build_context). Track the source so the
    # pulse can tell the agent which level answered — the canonical
    # debugging aid for "why did Myco pick substrate X when I'm in
    # folder Y?" mysteries.
    source: str  # one of: kwargs.project_dir, mcp.roots/list,
    #   env.MYCO_PROJECT_DIR, env.CLAUDE_PROJECT_DIR, Path.cwd()
    project_dir: Path | None = None

    # Level 1: explicit kwargs.project_dir (fix for a latent bug —
    # previously this key survived only long enough to compute the
    # pulse sidecar; it never reached dispatch or build_context).
    project_dir_str = args_in.pop("project_dir", None)
    if project_dir_str:
        project_dir = Path(str(project_dir_str)).expanduser()
        source = "kwargs.project_dir"

    # Level 2: MCP roots/list — query the client for workspace roots.
    # v0.5.16: also capture the first raw root (regardless of whether
    # it has a substrate) so we can suggest germinating there if
    # dispatch falls through to SubstrateNotFound.
    workspace_root: Path | None = None
    if project_dir is None and mcp_ctx is not None:
        discovered = await _resolve_project_via_roots(mcp_ctx)
        if discovered is not None:
            project_dir = discovered
            source = "mcp.roots/list"
        else:
            workspace_root = await _detect_workspace_root(mcp_ctx)

    # Level 3/4: env vars. Walk MYCO_PROJECT_DIR then CLAUDE_PROJECT_DIR
    # (mirrors build_context's chain — inlined here so we can report
    # the exact source back to the agent via the pulse).
    if project_dir is None:
        for env_var in ("MYCO_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
            env_val = os.environ.get(env_var, "").strip()
            if env_val:
                project_dir = Path(env_val).expanduser()
                source = f"env.{env_var}"
                break

    # Level 5: cwd. Record as the source even though build_context
    # would have reached this anyway — makes the report complete.
    if project_dir is None:
        source = "Path.cwd()"

    try:
        result = dispatch(
            spec.name,
            args_in,
            manifest=manifest,
            project_dir=project_dir,
        )
    except SubstrateNotFound as exc:
        # v0.5.16: if we know a workspace root but it has no substrate,
        # return a soft auto-germ advice instead of erroring. Agent
        # sees a normal tool response with a clear germinate hint in
        # the pulse rules_hint; user gets asked before anything is
        # written to disk.
        if workspace_root is not None and not spec.pre_substrate:
            return _auto_germ_advice_response(
                verb=spec.name,
                workspace_root=workspace_root,
                exc=exc,
                hunger_called=state.hunger_called,
            )
        raise

    # If level 5 (cwd) was the answer, fill in the resolved path now
    # that dispatch has happened. (build_context's resolve -> substrate
    # root might differ slightly from cwd if it walked up — we report
    # the dispatch-requested value.)
    pulse_project_dir = project_dir if project_dir is not None else Path.cwd()

    if spec.name == "hunger":
        state.hunger_called = True
    pulse = _compute_substrate_pulse(
        verb=spec.name,
        project_dir=pulse_project_dir,
        hunger_called=state.hunger_called,
        project_dir_source=source,
    )
    return {
        "exit_code": result.exit_code,
        "payload": _jsonable(result.payload),
        "substrate_pulse": pulse,
    }


async def _resolve_project_via_roots(ctx: Any) -> Path | None:
    """Ask the MCP client for its workspace roots via ``roots/list``.

    Returns the first root whose path has a Myco substrate (a
    ``_canon.yaml`` at it or any ancestor). Returns ``None`` when:

    - the client doesn't support ``roots/list`` (raises / no capability)
    - the client returns an empty roots list
    - no root's URI is a ``file://`` URI
    - no root has a substrate anywhere along its ancestry

    This is the core ``一劳永逸`` fix for MCP hosts that don't set a
    useful cwd on MCP-server subprocesses (Claude Desktop, Cowork,
    Cursor, Zed, …). Every spec-compliant MCP client exposes
    workspace roots via this protocol method; Myco uses that
    standard channel rather than each host's bespoke config field.
    """
    try:
        session = getattr(ctx, "session", None)
        if session is None or not hasattr(session, "list_roots"):
            return None
        result = await session.list_roots()
    except Exception:
        # Client doesn't support `roots/list`, network error,
        # unsupported MCP version, any other reason — fall through.
        return None
    roots = getattr(result, "roots", None) or []
    for root in roots:
        uri = getattr(root, "uri", None)
        if not uri:
            continue
        candidate = _uri_to_path(str(uri))
        if candidate is None:
            continue
        if _has_substrate_at_or_above(candidate):
            return candidate
    return None


async def _detect_workspace_root(ctx: Any) -> Path | None:
    """Return the first ``file://`` workspace root the client exposes,
    **regardless of whether it has a substrate**.

    Paired with :func:`_resolve_project_via_roots` as the "did the
    client at least tell us something about the workspace?" probe.
    If ``_resolve_project_via_roots`` returned ``None`` (no root had
    a substrate), we still want to know where the user's workspace
    IS so we can suggest germinating a substrate there.

    v0.5.16 addition.
    """
    try:
        session = getattr(ctx, "session", None)
        if session is None or not hasattr(session, "list_roots"):
            return None
        result = await session.list_roots()
    except Exception:
        return None
    roots = getattr(result, "roots", None) or []
    for root in roots:
        uri = getattr(root, "uri", None)
        if not uri:
            continue
        candidate = _uri_to_path(str(uri))
        if candidate is not None:
            return candidate
    return None


def _auto_germ_advice_response(
    *,
    verb: str,
    workspace_root: Path,
    exc: SubstrateNotFound,
    hunger_called: bool,
) -> dict[str, Any]:
    """Return a soft-fail MCP tool response when the workspace has no
    substrate yet. The agent sees a normal-shaped response whose pulse
    tells it to call ``myco_germinate`` with the workspace root.

    Why soft-fail: raising ``SubstrateNotFound`` here would surface
    as a transport-level error on the MCP client, blocking the agent
    from relaying the suggestion to the user. A dict response with
    advice in the pulse gets the agent to say "this folder doesn't
    have a Myco substrate yet — want me to germinate one?" which is
    the UX we want.

    ``exit_code`` is set to 4 (``SubstrateNotFound``'s canonical exit
    code per the v0.5.8 contract) so anything that checks exit codes
    still differentiates "no substrate" from other error classes.
    The agent reads the pulse advice.

    v0.5.16 initial shape. v0.5.18 bugfix: also include the
    ``project_dir_source`` + ``resolved_project_dir`` transparency
    fields that v0.5.17 added to the normal dispatch path — reaching
    this function PROVES ``_detect_workspace_root`` got a workspace
    back from the client, which is itself the most useful debugging
    signal (confirms roots/list works even though _resolve_... came
    up empty because the root had no substrate).
    """
    from myco.core.trust import safe_frontmatter_field

    suggested = (
        f"no substrate at {workspace_root}. Call "
        f"myco_germinate(project_dir={str(workspace_root)!r}, "
        "substrate_id=<slug>) to bootstrap one."
    )
    return {
        "exit_code": 4,
        "payload": {
            "error": "SubstrateNotFound",
            "detail": str(exc),
            "workspace_root": str(workspace_root),
            "advice": suggested,
        },
        "substrate_pulse": {
            "substrate_id": "(no substrate — workspace detected)",
            "contract_version": "(unknown)",
            "hard_contract_ref": "docs/architecture/L1_CONTRACT/protocol.md",
            "rules_hint": suggested,
            # v0.5.18: transparency — reaching this path means
            # _detect_workspace_root returned a file:// root from the
            # client. So roots/list IS working; it just returned a
            # folder without a substrate.
            "project_dir_source": "mcp.roots/list (root has no substrate)",
            "resolved_project_dir": safe_frontmatter_field(
                str(workspace_root), max_len=512
            ),
        },
    }


def _uri_to_path(uri: str) -> Path | None:
    """Parse a ``file://`` URI to a local ``Path``.

    Handles POSIX (``file:///home/user/x``) and Windows
    (``file:///C:/Users/x`` or ``file://C:/Users/x``) URIs, plus
    percent-encoded spaces / non-ASCII characters. Returns ``None``
    for non-file schemes (``https://``, ``git+ssh://``, etc).
    """
    import urllib.parse
    import urllib.request

    try:
        parsed = urllib.parse.urlparse(uri)
    except Exception:
        return None
    if parsed.scheme != "file":
        return None
    try:
        return Path(urllib.request.url2pathname(parsed.path))
    except Exception:
        return None


def _has_substrate_at_or_above(path: Path) -> bool:
    """True when ``path`` or any ancestor contains a ``_canon.yaml``."""
    try:
        p = path.resolve()
    except OSError:
        return False
    for candidate in [p, *p.parents]:
        if (candidate / "_canon.yaml").is_file():
            return True
    return False


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
            async def _handler(ctx: _MCPContext, **kwargs: Any) -> dict[str, Any]:
                # ``ctx`` is FastMCP's Context object, injected because of
                # the ``_MCPContext`` type annotation. ``_invoke`` queries
                # it for ``roots/list`` when no explicit project_dir is
                # given, giving the substrate discovery chain a way to
                # find the user's workspace on MCP hosts that spawn the
                # server with cwd = system dir.
                #
                # v0.5.21: explicit-param binding puts each declared arg
                # into ``kwargs`` by name (thanks to ``__signature__``
                # override below). Drop keys whose value is ``None`` so
                # optional-with-default-None args don't shadow the
                # manifest's own defaulting logic — ``build_handler_args``
                # re-applies defaults for omitted keys.
                clean = {k: v for k, v in kwargs.items() if v is not None}
                return await _invoke(spec_local, m, clean, state, mcp_ctx=ctx)

            _handler.__name__ = spec_local.mcp_tool
            _handler.__doc__ = spec_local.summary
            # v0.5.21 hotfix: override the Python signature so FastMCP's
            # schema derivation sees each manifest arg as an individual
            # JSON property rather than collapsing ``**kwargs`` into a
            # single required ``{"kwargs": dict}`` property. See
            # :func:`_build_handler_signature` for the full rationale.
            _handler.__signature__ = _build_handler_signature(spec_local)  # type: ignore[attr-defined]
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
