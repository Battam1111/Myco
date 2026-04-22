"""Tests for ``myco.surface.mcp``."""

from __future__ import annotations

from pathlib import Path

import pytest

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


# v0.5.14: MCP ``roots/list`` discovery. Pure helpers exercised against
# a fake Context/Session so we don't need a real MCP session.


class _FakeRoot:
    def __init__(self, uri: str) -> None:
        self.uri = uri


class _FakeRootsResult:
    def __init__(self, roots: list[_FakeRoot]) -> None:
        self.roots = roots


class _FakeSession:
    def __init__(self, result_or_exc: object) -> None:
        self._result_or_exc = result_or_exc

    async def list_roots(self) -> object:
        if isinstance(self._result_or_exc, Exception):
            raise self._result_or_exc
        return self._result_or_exc


class _FakeContext:
    def __init__(self, session: _FakeSession | None) -> None:
        self.session = session


def test_uri_to_path_posix() -> None:
    from myco.surface.mcp import _uri_to_path

    p = _uri_to_path("file:///home/user/project")
    assert p is not None
    assert str(p).replace("\\", "/").endswith("home/user/project")


def test_uri_to_path_windows() -> None:
    from myco.surface.mcp import _uri_to_path

    p = _uri_to_path("file:///C:/Users/10350/Desktop/C3")
    assert p is not None
    assert str(p).replace("\\", "/").endswith("C:/Users/10350/Desktop/C3")


def test_uri_to_path_with_percent_encoding() -> None:
    """Spaces in paths arrive percent-encoded; must round-trip."""
    from myco.surface.mcp import _uri_to_path

    p = _uri_to_path("file:///tmp/has%20space/x")
    assert p is not None
    assert "has space" in str(p)


def test_uri_to_path_rejects_non_file_scheme() -> None:
    from myco.surface.mcp import _uri_to_path

    assert _uri_to_path("https://example.com/repo") is None
    assert _uri_to_path("git+ssh://github.com/x/y") is None
    assert _uri_to_path("") is None


def test_has_substrate_at_or_above_finds_canon(tmp_path: Path) -> None:
    from myco.surface.mcp import _has_substrate_at_or_above

    (tmp_path / "_canon.yaml").write_text("schema_version: '1'\n")
    assert _has_substrate_at_or_above(tmp_path) is True
    # One dir deeper also sees it (walk up)
    deep = tmp_path / "subdir"
    deep.mkdir()
    assert _has_substrate_at_or_above(deep) is True


def test_has_substrate_at_or_above_negative(tmp_path: Path) -> None:
    from myco.surface.mcp import _has_substrate_at_or_above

    assert _has_substrate_at_or_above(tmp_path) is False


def _run(coro):  # type: ignore[no-untyped-def]
    """Sync-driver for coroutines. Myco's dev deps don't include
    pytest-asyncio and strict-markers mode is on, so we use plain
    ``asyncio.run`` instead of ``@pytest.mark.asyncio``."""
    import asyncio

    return asyncio.run(coro)


def test_resolve_project_via_roots_happy_path(tmp_path: Path) -> None:
    from myco.surface.mcp import _resolve_project_via_roots

    (tmp_path / "_canon.yaml").write_text("schema_version: '1'\n")
    uri = tmp_path.resolve().as_uri()
    ctx = _FakeContext(_FakeSession(_FakeRootsResult([_FakeRoot(uri)])))
    got = _run(_resolve_project_via_roots(ctx))
    assert got is not None
    assert got.resolve() == tmp_path.resolve()


def test_resolve_project_via_roots_skips_non_substrate_roots(
    tmp_path: Path,
) -> None:
    from myco.surface.mcp import _resolve_project_via_roots

    r1 = tmp_path / "no_subst"
    r2 = tmp_path / "yes_subst"
    r1.mkdir()
    r2.mkdir()
    (r2 / "_canon.yaml").write_text("schema_version: '1'\n")
    roots = [_FakeRoot(r1.as_uri()), _FakeRoot(r2.as_uri())]
    ctx = _FakeContext(_FakeSession(_FakeRootsResult(roots)))
    got = _run(_resolve_project_via_roots(ctx))
    assert got is not None
    assert got.resolve() == r2.resolve()


def test_resolve_project_via_roots_client_doesnt_support() -> None:
    """Client that doesn't implement roots/list → graceful None."""
    from myco.surface.mcp import _resolve_project_via_roots

    ctx = _FakeContext(_FakeSession(RuntimeError("not supported")))
    got = _run(_resolve_project_via_roots(ctx))
    assert got is None


def test_resolve_project_via_roots_empty_roots() -> None:
    """Client responds but has no workspace open → None."""
    from myco.surface.mcp import _resolve_project_via_roots

    ctx = _FakeContext(_FakeSession(_FakeRootsResult([])))
    got = _run(_resolve_project_via_roots(ctx))
    assert got is None


def test_resolve_project_via_roots_no_session() -> None:
    """Missing session attribute → graceful None (no AttributeError)."""
    from myco.surface.mcp import _resolve_project_via_roots

    ctx = _FakeContext(None)
    got = _run(_resolve_project_via_roots(ctx))
    assert got is None


def test_resolve_project_via_roots_skips_non_file_uri(
    tmp_path: Path,
) -> None:
    """A root with https:// URI is ignored; next file:// root tried."""
    from myco.surface.mcp import _resolve_project_via_roots

    (tmp_path / "_canon.yaml").write_text("schema_version: '1'\n")
    roots = [
        _FakeRoot("https://example.com/repo"),
        _FakeRoot(tmp_path.resolve().as_uri()),
    ]
    ctx = _FakeContext(_FakeSession(_FakeRootsResult(roots)))
    got = _run(_resolve_project_via_roots(ctx))
    assert got is not None
    assert got.resolve() == tmp_path.resolve()


# v0.5.16: _detect_workspace_root + auto-germ advice soft response.


def test_detect_workspace_root_returns_first_file_uri_regardless_of_substrate(
    tmp_path: Path,
) -> None:
    """Unlike _resolve_project_via_roots, _detect_workspace_root
    returns the first file:// root even when it has no substrate —
    so v0.5.16 can suggest where to germinate."""
    from myco.surface.mcp import _detect_workspace_root

    # No _canon.yaml anywhere under tmp_path.
    uri = tmp_path.resolve().as_uri()
    ctx = _FakeContext(_FakeSession(_FakeRootsResult([_FakeRoot(uri)])))
    got = _run(_detect_workspace_root(ctx))
    assert got is not None
    assert got.resolve() == tmp_path.resolve()


def test_detect_workspace_root_returns_none_when_client_silent() -> None:
    from myco.surface.mcp import _detect_workspace_root

    ctx = _FakeContext(None)
    got = _run(_detect_workspace_root(ctx))
    assert got is None


def test_auto_germ_advice_response_shape(tmp_path: Path) -> None:
    """The soft-fail response exposes exit_code 4, a germinate hint
    in the pulse, the workspace path in the payload, and the v0.5.18
    transparency fields ``project_dir_source`` + ``resolved_project_dir``."""
    from myco.core.errors import SubstrateNotFound
    from myco.surface.mcp import _auto_germ_advice_response

    resp = _auto_germ_advice_response(
        verb="hunger",
        workspace_root=tmp_path,
        exc=SubstrateNotFound("test"),
        hunger_called=False,
    )
    assert resp["exit_code"] == 4
    assert resp["payload"]["error"] == "SubstrateNotFound"
    assert resp["payload"]["workspace_root"] == str(tmp_path)
    pulse = resp["substrate_pulse"]
    assert "myco_germinate" in pulse["rules_hint"]
    assert str(tmp_path) in pulse["rules_hint"]
    assert "no substrate" in pulse["substrate_id"].lower()
    # v0.5.18: transparency fields tell the operator that roots/list
    # DID work (otherwise we wouldn't be in this branch).
    assert "mcp.roots/list" in pulse["project_dir_source"]
    assert str(tmp_path) in pulse["resolved_project_dir"]


def test_pulse_includes_resolution_source_when_provided(tmp_path: Path) -> None:
    """v0.5.17: pulse surfaces ``project_dir_source`` + ``resolved_project_dir``
    when the caller tells it the source — the transparency aid for
    multi-project debugging."""
    from myco.surface.mcp import _compute_substrate_pulse

    (tmp_path / "_canon.yaml").write_text(
        "schema_version: '1'\n"
        "contract_version: 'v0.5.17'\n"
        "identity: { substrate_id: 'src-test' }\n",
        encoding="utf-8",
    )
    pulse = _compute_substrate_pulse(
        "hunger",
        project_dir=tmp_path,
        project_dir_source="mcp.roots/list",
    )
    assert pulse["project_dir_source"] == "mcp.roots/list"
    assert str(tmp_path) in pulse["resolved_project_dir"]


def test_pulse_omits_resolution_source_when_not_provided() -> None:
    """CLI path leaves the source None; fields stay absent (no lies)."""
    from myco.surface.mcp import _compute_substrate_pulse

    pulse = _compute_substrate_pulse("hunger")
    assert "project_dir_source" not in pulse
    assert "resolved_project_dir" not in pulse


def test_invoke_reports_env_source_when_myco_env_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: with MYCO_PROJECT_DIR set and no roots/list, the
    pulse says the env var was the source."""
    from myco.surface.manifest import load_manifest
    from myco.surface.mcp import _invoke, _ServerState

    (tmp_path / "_canon.yaml").write_text(
        "schema_version: '1'\n"
        "contract_version: 'v0.5.17'\n"
        "identity: { substrate_id: 'env-source' }\n"
        "system: { write_surface: { allowed: ['notes/**'] } }\n"
        "subsystems: { x: {} }\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)

    m = load_manifest()
    spec = m.by_name("sense")
    state = _ServerState()
    result = _run(_invoke(spec, m, {"query": "x"}, state, mcp_ctx=None))

    assert result["substrate_pulse"]["project_dir_source"] == "env.MYCO_PROJECT_DIR"
    assert str(tmp_path) in result["substrate_pulse"]["resolved_project_dir"]


def test_invoke_reports_kwargs_source_when_project_dir_explicit(
    tmp_path: Path,
) -> None:
    """Explicit kwargs.project_dir wins the source attribution too."""
    from myco.surface.manifest import load_manifest
    from myco.surface.mcp import _invoke, _ServerState

    (tmp_path / "_canon.yaml").write_text(
        "schema_version: '1'\n"
        "contract_version: 'v0.5.17'\n"
        "identity: { substrate_id: 'kw-source' }\n"
        "system: { write_surface: { allowed: ['notes/**'] } }\n"
        "subsystems: { x: {} }\n",
        encoding="utf-8",
    )

    m = load_manifest()
    spec = m.by_name("sense")
    state = _ServerState()
    result = _run(
        _invoke(
            spec, m, {"query": "x", "project_dir": str(tmp_path)}, state, mcp_ctx=None
        )
    )

    assert result["substrate_pulse"]["project_dir_source"] == "kwargs.project_dir"


def test_invoke_returns_auto_germ_advice_when_roots_lack_substrate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: ``_invoke`` sees a workspace root via roots/list,
    no _canon.yaml at or above, dispatch would raise SubstrateNotFound
    → we return a soft advice response instead.
    """
    from myco.surface.manifest import load_manifest
    from myco.surface.mcp import _invoke, _ServerState

    # Empty workspace (no substrate).
    empty = tmp_path / "fresh-project"
    empty.mkdir()

    # Prevent build_context's env + cwd fallbacks from finding a
    # different substrate (Myco self-substrate if pytest runs from
    # the Myco repo) and silently masking the SubstrateNotFound we
    # need to trigger.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MYCO_PROJECT_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)

    m = load_manifest()
    sense_spec = m.by_name("sense")
    state = _ServerState()

    ctx = _FakeContext(
        _FakeSession(_FakeRootsResult([_FakeRoot(empty.resolve().as_uri())]))
    )
    result = _run(_invoke(sense_spec, m, {"query": "x"}, state, mcp_ctx=ctx))

    assert result["exit_code"] == 4
    assert result["payload"]["workspace_root"] == str(empty.resolve())
    assert "myco_germinate" in result["substrate_pulse"]["rules_hint"]


# ---------------------------------------------------------------------------
# v0.5.21 regression: FastMCP signature-derivation bug.
#
# v0.5.20 and earlier registered handlers as ``async def _handler(ctx,
# **kwargs)``. FastMCP's JSON-schema derivation (via
# ``mcp.server.fastmcp.utilities.func_metadata``) interpreted
# ``**kwargs: Any`` as a single required dict parameter named
# ``kwargs``. The emitted schema was
# ``{"required": ["kwargs"], "properties": {"kwargs": {...}}}`` —
# agents sending flat args got a pydantic validation error, and
# agents sending nested ``{"kwargs": {"content": "..."}}`` had the
# real args buried in Python's varkw sink. The fix: override
# ``__signature__`` with per-manifest-arg parameters. These tests
# lock the behavior so the bug can never silently return.
# ---------------------------------------------------------------------------


def test_handler_signature_has_manifest_args_not_varkw() -> None:
    """Every verb's registered handler must advertise a real signature
    whose parameters mirror the manifest. FastMCP's schema derivation
    reads ``inspect.signature(fn)`` — if any handler still exposes a
    bare ``**kwargs`` to introspection, the JSON schema collapses to
    ``{"required": ["kwargs"]}`` and flat-args calls break again.
    """
    import inspect

    from myco.surface.mcp import _build_handler_signature

    m = load_manifest()
    for spec in m.commands:
        sig = _build_handler_signature(spec)
        # First param is always ctx (injected by FastMCP).
        param_names = list(sig.parameters.keys())
        assert param_names[0] == "ctx", spec.name
        # Every declared manifest arg appears by its snake_case name.
        manifest_arg_names = {arg.snake for arg in spec.args}
        sig_names = set(param_names[1:])
        missing = manifest_arg_names - sig_names
        assert not missing, (spec.name, missing)
        # No varkw (``**kwargs``) or varargs — those are the bug shapes
        # that caused FastMCP to emit the broken schema.
        for p in sig.parameters.values():
            assert p.kind != inspect.Parameter.VAR_KEYWORD, spec.name
            assert p.kind != inspect.Parameter.VAR_POSITIONAL, spec.name


def test_handler_signature_marks_required_args_without_default() -> None:
    """``required: true`` in the manifest must surface as a parameter
    with no default (Pydantic reads the default-less params as
    ``required`` in the JSON Schema it emits to the client)."""
    import inspect

    from myco.surface.mcp import _build_handler_signature

    m = load_manifest()
    sense = m.by_name("sense")  # query is required
    sig = _build_handler_signature(sense)
    query = sig.parameters["query"]
    assert query.default is inspect.Parameter.empty

    eat = m.by_name("eat")  # none are required
    sig = _build_handler_signature(eat)
    for name in ("content", "path", "url"):
        assert sig.parameters[name].default is None


def test_handler_signature_exposes_project_dir_override() -> None:
    """Every verb (except those that already take project-dir as a
    manifest arg, e.g. germinate) must surface ``project_dir`` as an
    optional parameter so the agent can pin a substrate explicitly.
    The sidecar contract relies on this for multi-project routing."""
    from myco.surface.mcp import _build_handler_signature

    m = load_manifest()
    # hunger, eat, sense, etc. don't declare project-dir in the manifest
    # — _build_handler_signature appends it.
    for verb in ("hunger", "eat", "sense", "forage", "immune"):
        spec = m.by_name(verb)
        sig = _build_handler_signature(spec)
        assert "project_dir" in sig.parameters, verb

    # germinate DOES declare project-dir in the manifest — skip the
    # append so the signature stays unique.
    germinate = m.by_name("germinate")
    sig = _build_handler_signature(germinate)
    project_dir_params = [p for p in sig.parameters if p == "project_dir"]
    assert len(project_dir_params) == 1  # no duplicate


def test_fastmcp_tool_schema_exposes_individual_properties() -> None:
    """End-to-end: after ``build_server`` runs, FastMCP's emitted
    ``inputSchema`` must have ``content``, ``path``, ``url`` as
    individual properties — NOT a single ``kwargs`` property. This
    is the shape the MCP client sees over the wire, so it's what
    actually determines whether the bug is present."""
    import asyncio

    from myco.surface.mcp import build_server

    m = load_manifest()
    server = build_server(m)

    async def _list_tools():
        return await server.list_tools()

    tools = asyncio.run(_list_tools())
    eat = next(t for t in tools if t.name == "myco_eat")
    props = eat.inputSchema["properties"]
    # The bug shape: schema with a single "kwargs" property.
    assert set(props.keys()) != {"kwargs"}
    # The fix shape: individual properties for each manifest arg.
    for prop in ("content", "path", "url", "tags", "source", "project_dir"):
        assert prop in props, prop


def test_fastmcp_call_eat_with_flat_args_succeeds() -> None:
    """The closing regression: calling ``myco_eat`` via FastMCP's
    ``call_tool`` with flat ``{"content": "..."}`` must reach the
    eat handler and return a successful Result (exit_code 0). Pre-
    v0.5.21 this raised a pydantic validation error at the MCP
    boundary OR surfaced the dispatcher's "must pass one of"
    UsageError from eat.py (depending on which shape the agent
    tried to work around the broken schema with).
    """
    import asyncio

    from myco.surface.mcp import build_server

    # Need a real substrate root for eat to write to. Use the repo
    # itself — it has _canon.yaml + the write_surface includes notes/**.
    repo_root = Path(__file__).resolve().parents[3]
    assert (repo_root / "_canon.yaml").is_file()

    m = load_manifest()
    server = build_server(m)

    async def _call():
        return await server.call_tool(
            "myco_eat",
            {
                "content": "v0.5.21 regression-test marker — safe to delete",
                "tags": ["regression-test"],
                "project_dir": str(repo_root),
            },
        )

    result = asyncio.run(_call())
    # FastMCP returns a list[TextContent]; parse the JSON body.
    import json as _json

    payload_text = result[0].text if result else ""
    payload = _json.loads(payload_text)
    assert payload["exit_code"] == 0, payload
    # Handler wrote the note to notes/raw/ — clean it up so the test
    # suite stays hermetic.
    written = Path(payload["payload"]["path"])
    try:
        if written.is_file():
            written.unlink()
    except OSError:
        pass  # best-effort cleanup; not fatal.


def test_fastmcp_call_sense_with_flat_query_arg_succeeds() -> None:
    """Same regression for ``sense``, which has ``query`` as a
    *required* arg. Required-arg verbs exercise a different Pydantic
    code path than optional-arg verbs, so we lock it separately."""
    import asyncio

    from myco.surface.mcp import build_server

    repo_root = Path(__file__).resolve().parents[3]
    m = load_manifest()
    server = build_server(m)

    async def _call():
        return await server.call_tool(
            "myco_sense",
            {"query": "substrate", "project_dir": str(repo_root)},
        )

    result = asyncio.run(_call())
    import json as _json

    payload = _json.loads(result[0].text)
    # exit_code 0 == found matches or no matches (both legal); non-zero
    # would mean the call itself failed. We only care that dispatch
    # reached sense.run rather than tripping the MCP surface.
    assert "exit_code" in payload
    assert "substrate_pulse" in payload


def test_fastmcp_none_values_dont_shadow_manifest_defaults() -> None:
    """The v0.5.21 handler drops ``None`` keys before ``_invoke`` so
    an omitted optional arg (which FastMCP default-binds to ``None``)
    doesn't shadow the manifest's own default-providing logic. Without
    this cleanup, ``tags: None`` would reach ``eat.run`` which calls
    ``isinstance(raw_tags, (list, tuple))`` and silently coerces to
    empty — fine for tags, but breaks for any arg whose manifest
    default is a non-None sentinel."""
    import asyncio

    from myco.surface.mcp import build_server

    repo_root = Path(__file__).resolve().parents[3]
    m = load_manifest()
    server = build_server(m)

    async def _call():
        # Omit tags + source entirely — rely on manifest defaults.
        return await server.call_tool(
            "myco_eat",
            {
                "content": "defaults-check marker",
                "project_dir": str(repo_root),
            },
        )

    import json as _json

    result = asyncio.run(_call())
    payload = _json.loads(result[0].text)
    assert payload["exit_code"] == 0
    # Manifest default for source is "agent"; if None had shadowed it,
    # the handler would have stringified None and written "source: None".
    assert payload["payload"]["source"] == "agent"
    # Clean up.
    try:
        Path(payload["payload"]["path"]).unlink()
    except OSError:
        pass
