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
    in the pulse, and the workspace path in the payload."""
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
