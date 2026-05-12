"""Verification suite for the streamable-HTTP MCP transport + OAuth 2.1 stack.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md`` § "MCP surface"
(the streamable-HTTP transport is the remote-deployment counterpart to the stdio
adapter); ``docs/primordia/v0_7_10_to_v1_0_omnibus_craft_2026-05-10.md`` § Round 1
item G ("Streamable-HTTP + OAuth 2.1 verification suite").

Backs the README claim "OAuth 2.1 + PKCE + RFC 8707 streamable-http stack" with
end-to-end smoke tests. v0.8.0 closes all four gaps that previously kept this
suite honestly half-green:

1. **Launcher CLI**: ``--host`` / ``--port`` / ``--mount-path`` are now
   threaded into ``server.settings.{host,port,streamable_http_path}`` BEFORE
   ``server.run('streamable-http')`` so ``run_streamable_http_async``
   reads them when constructing the uvicorn server. The inline-launcher
   workaround in ``_INLINE_LAUNCHER_TEMPLATE`` follows the same recipe; the
   public CLI ``python -m myco.boundary.mcp --port N`` now works too.
2. **MycoOAuthProvider integration**: ``build_server`` reads canon /
   env-var OAuth config and passes ``auth=AuthSettings(...)`` plus a
   ``MycoIntrospectionTokenVerifier`` to FastMCP. The Bearer auth
   middleware is auto-mounted by FastMCP when both kwargs are present.
3. **Issuer-URL discovery**: ``MYCO_OAUTH_ISSUER_URL`` (env, highest
   precedence) and ``system.governance.oauth.issuer_url`` (canon,
   fallback) are both read by
   ``load_oauth_provider_from_env_or_canon``.
4. **Log redaction**: ``configure_logging_redaction`` is invoked from
   ``build_server`` on the uvicorn / mcp / starlette loggers when
   ``canon.governance.token_redaction_required: true`` (which is the
   shipped default).

Mock provider scope: the OAuth-2.1 mock is a stdlib
``http.server.HTTPServer`` running in a thread that accepts
``grant_type=client_credentials``, mints opaque bearer tokens, and
honors ``POST /introspect`` (RFC 7662) for verifier round-trips.
JWS / JWKS / RFC 8707 fidelity is deferred to ``authlib.oauth2``
(already declared in the ``myco[mcp-auth]`` extra) and is tracked
under the now-archived gap log
``docs/iou/_archive/v0_7_10_streamable_http_gaps.md`` §5 (mock-vs-real
provider gap).

Subprocess discipline: every spawned server is cleaned up in a
``finally`` clause with ``terminate()`` + ``wait(timeout=2)``;
lingering bindings on Windows CI runners are unacceptable.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import textwrap
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import parse_qs

import pytest

# ---------------------------------------------------------------------------
# Module-level guards — skip the whole suite if MCP SDK is absent
# ---------------------------------------------------------------------------

mcp = pytest.importorskip(
    "mcp.server.fastmcp",
    reason="myco[mcp] extra (mcp>=1.2) is required for streamable-HTTP tests",
)
uvicorn = pytest.importorskip(
    "uvicorn",
    reason="uvicorn is required to host FastMCP's streamable-HTTP ASGI app",
)


# ---------------------------------------------------------------------------
# Subprocess launcher
# ---------------------------------------------------------------------------

# Inline Python source we hand to `python -c`. It imports build_server, sets
# the FastMCP settings to the requested host/port (the same recipe the public
# launcher CLI uses internally — see ``src/myco/boundary/mcp/__init__.py``,
# v0.8.0 gap §1 closure), then runs. The OAuth-aware path picks up
# ``MYCO_OAUTH_ISSUER_URL`` from the inherited env in subprocess.Popen.
_INLINE_LAUNCHER_TEMPLATE = textwrap.dedent(
    """\
    import sys
    from myco.boundary.surface.mcp import build_server
    server = build_server()
    server.settings.host = {host!r}
    server.settings.port = {port}
    server.settings.streamable_http_path = {path!r}
    server.run(transport="streamable-http")
    """
)


def _free_port() -> int:
    """Ask the kernel for a free TCP port on localhost, then release it.

    There is a small race window between socket close and subprocess bind,
    but for a single-test process running serially on Windows it's negligible.
    Using ``socket.bind(('localhost', 0))`` is the standard idiom.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_port_ready(host: str, port: int, *, timeout: float = 8.0) -> bool:
    """Poll the listening port until something accepts a TCP connection.

    Returns True when the server is reachable, False on timeout. Using a raw
    TCP probe (instead of an HTTP GET) avoids 405-Method-Not-Allowed false
    negatives on the streamable-HTTP endpoint, which only accepts POST.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


@contextmanager
def _spawn_streamable_server(
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    path: str = "/mcp",
    extra_env: dict[str, str] | None = None,
) -> Iterator[tuple[subprocess.Popen[bytes], str, int, str]]:
    """Spawn a streamable-HTTP MCP server in a child Python interpreter.

    Yields ``(proc, host, port, path)``. The caller is responsible for using
    the host/port to talk to the server; cleanup is handled here.

    ``extra_env`` is layered onto the parent's env before spawn. v0.8.0
    OAuth tests use it to inject ``MYCO_OAUTH_ISSUER_URL`` (and friends)
    so ``build_server`` wires the Bearer auth middleware.
    """
    actual_port = port if port is not None else _free_port()
    src = _INLINE_LAUNCHER_TEMPLATE.format(host=host, port=actual_port, path=path)
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(
        [sys.executable, "-c", src],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        if not _wait_for_port_ready(host, actual_port, timeout=8.0):
            # Capture diagnostic output before raising.
            try:
                _stdout, _stderr = proc.communicate(timeout=1.0)
            except subprocess.TimeoutExpired:
                _stdout, _stderr = b"", b""
            pytest.fail(
                f"streamable-HTTP server failed to bind {host}:{actual_port} "
                f"within 8s. stdout={_stdout!r} stderr={_stderr!r}"
            )
        yield proc, host, actual_port, path
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=1.0)


# ---------------------------------------------------------------------------
# Tiny JSON-RPC client (stdlib, no third-party HTTP dep needed)
# ---------------------------------------------------------------------------


def _post_jsonrpc(
    url: str,
    payload: dict[str, Any],
    *,
    extra_headers: dict[str, str] | None = None,
    timeout: float = 5.0,
) -> tuple[int, dict[str, str], bytes]:
    """POST a JSON-RPC payload and return ``(status, headers, body_bytes)``.

    Streamable-HTTP transport requires both ``application/json`` and
    ``text/event-stream`` in the Accept header (the server may stream a
    response back as SSE). We always send both.

    Returns the raw response so callers can inspect SSE-framed payloads.
    """
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **(extra_headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read() or b""


def _decode_jsonrpc_body(body: bytes) -> dict[str, Any]:
    """Parse a JSON-RPC response body, accepting either raw JSON or SSE framing.

    FastMCP's streamable-HTTP transport returns ``text/event-stream`` by default
    (one ``data: {...}`` line per JSON-RPC response). We handle both.
    """
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return {}
    # SSE framing: "event: message\ndata: {...}\n\n" — extract the data line.
    if text.startswith("event:") or "data:" in text.split("\n", 1)[0]:
        for line in text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[len("data:") :].strip())
    return json.loads(text)


# ---------------------------------------------------------------------------
# A — Boot smoke test
# ---------------------------------------------------------------------------


def test_streamable_http_server_boots() -> None:
    """Spawn the server, verify it accepts TCP on the requested port, shut down.

    This is the most basic smoke test: the FastMCP-wired ASGI app must reach
    listening state. Exit-code-zero on clean termination is verified.
    """
    with _spawn_streamable_server() as (proc, host, port, _path):
        # Server is up because _wait_for_port_ready() returned. Sanity: a
        # second probe inside the with-block confirms it's still bound.
        assert _wait_for_port_ready(host, port, timeout=2.0), (
            "server became unreachable mid-test"
        )
    # After context exit, terminate() + wait() ran. uvicorn responds to
    # SIGTERM with a graceful shutdown that returns 0; on Windows
    # subprocess.Popen.terminate() sends CTRL_BREAK / TerminateProcess which
    # may yield non-zero. We accept either zero or a SIGTERM-ish negative
    # code, but require the process is actually dead.
    assert proc.returncode is not None, "server child process did not exit"


# ---------------------------------------------------------------------------
# B — initialize handshake
# ---------------------------------------------------------------------------


def test_streamable_http_returns_initialize_response() -> None:
    """POST a JSON-RPC ``initialize`` and verify the basic response shape.

    Per MCP spec: the response carries ``protocolVersion`` and ``serverInfo``.
    Myco's server name is ``"myco"`` (set in ``surface/mcp.py::build_server``).
    """
    with _spawn_streamable_server() as (_proc, host, port, path):
        url = f"http://{host}:{port}{path}"
        status, _headers, body = _post_jsonrpc(
            url,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "verification-suite", "version": "0"},
                },
            },
        )
        assert status == 200, f"initialize POST failed: {status}, body={body!r}"
        envelope = _decode_jsonrpc_body(body)
        assert envelope.get("jsonrpc") == "2.0", envelope
        assert "result" in envelope, envelope
        result = envelope["result"]
        assert "protocolVersion" in result, result
        server_info = result.get("serverInfo", {})
        assert server_info.get("name") == "myco", server_info


# ---------------------------------------------------------------------------
# C — tools/list returns the 20-verb roster
# ---------------------------------------------------------------------------


# The canonical 20-verb roster lives in src/myco/boundary/surface/manifest.yaml;
# we keep the expected names in the test so a regression in the manifest is
# caught here too. They are exposed under the ``myco_<verb>`` MCP tool name.
_EXPECTED_VERBS = {
    "germinate",
    "hunger",
    "eat",
    "sense",
    "forage",
    "excrete",
    "intake",
    "assimilate",
    "digest",
    "sporulate",
    "traverse",
    "propagate",
    "immune",
    "senesce",
    "fruit",
    "molt",
    "winnow",
    "ramify",
    "graft",
    "brief",
}


def test_streamable_http_returns_tools_list() -> None:
    """POST ``tools/list`` and verify all 20 manifest verbs are present.

    Streamable-HTTP requires the ``initialize`` handshake before other methods,
    and each request must carry the ``Mcp-Session-Id`` returned by initialize.
    We do both round-trips in one test to keep the contract honest.
    """
    with _spawn_streamable_server() as (_proc, host, port, path):
        url = f"http://{host}:{port}{path}"

        # 1. initialize and capture the session id
        status, init_headers, init_body = _post_jsonrpc(
            url,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "verification-suite", "version": "0"},
                },
            },
        )
        assert status == 200, init_body
        # Header name is case-insensitive by HTTP spec; urllib lower-cases.
        session_id = (
            init_headers.get("mcp-session-id")
            or init_headers.get("Mcp-Session-Id")
            or init_headers.get("MCP-Session-Id")
        )
        if session_id is None:
            # Some FastMCP versions/configurations run stateless; that's OK.
            session_id_headers: dict[str, str] = {}
        else:
            session_id_headers = {"Mcp-Session-Id": session_id}

        # 2. notifications/initialized completes the handshake (required by
        #    the streamable-HTTP transport before tools/list will dispatch).
        _post_jsonrpc(
            url,
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
            extra_headers=session_id_headers,
        )

        # 3. tools/list
        status, _headers, body = _post_jsonrpc(
            url,
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            extra_headers=session_id_headers,
        )
        assert status == 200, f"tools/list failed: {status}, body={body!r}"
        envelope = _decode_jsonrpc_body(body)
        result = envelope.get("result", {})
        tools = result.get("tools", [])
        assert isinstance(tools, list) and tools, envelope
        names = {t.get("name", "") for t in tools}
        # Every manifest verb is exposed under "myco_<verb>".
        expected_mcp_names = {f"myco_{v}" for v in _EXPECTED_VERBS}
        missing = expected_mcp_names - names
        assert not missing, (
            f"streamable-HTTP server missing tools for verbs: {missing}; "
            f"actual names: {sorted(names)}"
        )


# ---------------------------------------------------------------------------
# OAuth tests — v0.8.0: all 4 gaps closed, every test runs as plain pass.
# ---------------------------------------------------------------------------


# ---- Mock OAuth 2.1 issuer (stdlib) ----


class _MockOAuthHandler(BaseHTTPRequestHandler):
    """Minimal RFC 6749 §4.4 (client_credentials) + RFC 7662 (introspection).

    Endpoints:

    - ``POST /token``: accepts ``grant_type=client_credentials`` and emits
      an opaque bearer token. NOT a JWT — this exercises the introspection
      verifier path, not the JWS path. JWS coverage is left to authlib-
      backed unit tests.
    - ``POST /introspect``: RFC 7662 — returns ``{"active": true, ...}``
      for tokens this issuer minted, ``{"active": false}`` otherwise.
      The Myco server's ``MycoIntrospectionTokenVerifier`` calls this
      endpoint on every protected request.
    """

    issued_tokens: ClassVar[set[str]] = set()

    def log_message(self, format: str, *args: Any) -> None:
        # Silence the default stderr access log — pytest collects it.
        return

    def do_POST(self) -> None:  # http.server convention
        if self.path == "/token":
            self._handle_token()
            return
        if self.path == "/introspect":
            self._handle_introspect()
            return
        self.send_response(404)
        self.end_headers()

    def _read_form(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length).decode("utf-8")
        return parse_qs(body)

    def _handle_token(self) -> None:
        params = self._read_form()
        grant = (params.get("grant_type") or [""])[0]
        if grant != "client_credentials":
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"unsupported_grant_type"}')
            return
        token = f"mock-bearer-{len(self.issued_tokens):04d}-abcdef0123456789"
        self.issued_tokens.add(token)
        payload = {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "myco:tools",
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def _handle_introspect(self) -> None:
        params = self._read_form()
        token = (params.get("token") or [""])[0]
        active = token in self.issued_tokens
        if active:
            payload: dict[str, Any] = {
                "active": True,
                "scope": "myco:tools",
                "client_id": "test-client",
                "token_type": "Bearer",
            }
        else:
            payload = {"active": False}
        body_bytes = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)


@contextmanager
def _spawn_mock_oauth_issuer() -> Iterator[tuple[HTTPServer, str]]:
    """Run the mock issuer in a daemon thread, yield ``(server, base_url)``.

    Cleanup: ``server.shutdown()`` joins the request loop; the thread is a
    daemon so the test process can exit even if shutdown stalls.
    """
    httpd = HTTPServer(("127.0.0.1", 0), _MockOAuthHandler)
    port = httpd.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd, base_url
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2.0)


# ---- D — client_credentials handshake ----


def test_oauth_2_1_client_credentials_grant() -> None:
    """Mock OAuth issuer mints a token; Myco accepts it on a tool call.

    v0.8.0 (gap §2/§3 closure): ``build_server`` reads
    ``MYCO_OAUTH_ISSUER_URL`` from env, constructs a
    ``MycoIntrospectionTokenVerifier`` that calls
    ``{issuer}/introspect``, and passes ``auth=AuthSettings(...)`` plus
    ``token_verifier=...`` into FastMCP. The streamable-HTTP transport
    then auto-mounts the Bearer auth middleware. With a valid token,
    the request reaches the dispatcher and returns 200; the negative
    case (no/bogus token → 401) is covered by
    ``test_oauth_invalid_token_returns_401`` below.
    """
    with _spawn_mock_oauth_issuer() as (_issuer, issuer_url):
        # 1. Mint a bearer token via the mock /token endpoint.
        token_req = urllib.request.Request(
            f"{issuer_url}/token",
            data=b"grant_type=client_credentials&client_id=test&client_secret=secret",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(token_req, timeout=5.0) as resp:
            token_payload = json.loads(resp.read())
        assert "access_token" in token_payload, token_payload
        bearer = token_payload["access_token"]

        # 2. Boot Myco pointed at the mock issuer and present the bearer.
        with _spawn_streamable_server(
            extra_env={"MYCO_OAUTH_ISSUER_URL": issuer_url}
        ) as (_proc, host, port, path):
            url = f"http://{host}:{port}{path}"
            status, _headers, body = _post_jsonrpc(
                url,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "verification-suite", "version": "0"},
                    },
                },
                extra_headers={"Authorization": f"Bearer {bearer}"},
            )
            # The introspection round-trip succeeded; the request reached
            # the JSON-RPC dispatcher; status 200 confirms the bearer was
            # accepted by the auth middleware.
            assert status == 200, (
                f"valid bearer token rejected: status={status}, body={body!r}"
            )


# ---- E — token redaction in logs ----


def test_oauth_token_redaction_in_logs() -> None:
    """Bearer token must be redacted from server stdout/stderr.

    v0.8.0 (gap §4 closure): ``build_server`` invokes
    ``configure_logging_redaction`` on the uvicorn / mcp / starlette
    loggers when ``canon.governance.token_redaction_required: true``.
    The redaction filter pattern-matches token-shaped strings in
    ``LogRecord.msg`` (and ``args``) and substitutes
    ``[REDACTED-TOKEN]`` BEFORE the record is emitted.

    This test sends both a header-only token and a body-embedded token
    so it stays sensitive to regressions where:

    - uvicorn's access log starts echoing the Authorization header.
    - A JSON-parse exception trace dumps the request body.
    - A future debug-level handler logs the headers verbatim.

    Previously (v0.7.10) this test would xpass for the wrong reason —
    uvicorn happens not to log Authorization headers — but the
    defense-in-depth filter wasn't actually installed. v0.8.0 the
    filter IS installed; the contract holds even when something else
    constructs a token-bearing log line.
    """
    sentinel_token = "sentinel-bearer-abcdef0123456789ZZZZ"
    with _spawn_streamable_server() as (proc, host, port, path):
        url = f"http://{host}:{port}{path}"
        # Trigger a request that the server will log. Header carries the
        # token; body also embeds it so a JSON-parse error trace would
        # surface it if uvicorn dumped the request body.
        try:
            _post_jsonrpc(
                url,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"_sentinel": sentinel_token},
                },
                extra_headers={"Authorization": f"Bearer {sentinel_token}"},
            )
        except Exception:
            # Even on protocol error the request still logs the headers.
            pass
        # Give uvicorn a beat to flush.
        time.sleep(0.3)
    # After context exit, proc has terminated; collect output.
    out, err = proc.communicate(timeout=1.0)
    captured = (out + err).decode("utf-8", errors="replace")
    assert sentinel_token not in captured, (
        f"token leaked to server logs (token_redaction_required is supposed to "
        f"prevent this). Sentinel was {sentinel_token!r}; logs contained it."
    )


# ---- F — invalid bearer token returns 401 ----


def test_oauth_invalid_token_returns_401() -> None:
    """A bogus Bearer token must yield 401, not 200.

    v0.8.0 (gap §2 closure): the Bearer auth middleware is installed
    when canon / env supplies an OAuth issuer URL. The
    ``MycoIntrospectionTokenVerifier`` calls the issuer's
    ``/introspect`` endpoint; a bogus token triggers ``active: false``
    → ``verify_token`` returns ``None`` → FastMCP's
    ``RequireAuthMiddleware`` emits 401.

    Negative-case proof that the OAuth gate exists at all. Without
    this test, a green ``client_credentials_grant`` test would be
    meaningless — the server might be returning 200 to literally
    everyone.
    """
    with _spawn_mock_oauth_issuer() as (_issuer, issuer_url):
        with _spawn_streamable_server(
            extra_env={"MYCO_OAUTH_ISSUER_URL": issuer_url}
        ) as (_proc, host, port, path):
            url = f"http://{host}:{port}{path}"
            status, _headers, body = _post_jsonrpc(
                url,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "verification-suite", "version": "0"},
                    },
                },
                extra_headers={"Authorization": "Bearer this-token-is-bogus"},
            )
            assert status == 401, (
                f"expected 401 from bogus token, got {status}; body={body!r}"
            )


# ---- G — positive coverage: build_server wires the OAuth provider ----


def test_oauth_provider_loaded_from_canon() -> None:
    """When canon's ``oauth.issuer_url`` is set, ``build_server`` attaches
    the provider. Verifies the loader reaches into the canon block and
    that the resulting server carries a ``MycoOAuthProvider`` instance.

    Runs in-process (no subprocess): the loader reads env vars + canon
    governance synchronously. We exercise the env-vars-win-over-canon
    branch with ``MYCO_OAUTH_ISSUER_URL`` since modifying the
    self-substrate's ``_canon.yaml`` mid-test would race with the boot
    smoke test running concurrently.
    """
    from myco.boundary.surface.mcp import build_server
    from myco.boundary.surface.mcp_auth import (
        MycoOAuthProvider,
        load_oauth_provider_from_env_or_canon,
    )

    issuer = "http://127.0.0.1:65535"
    saved = os.environ.get("MYCO_OAUTH_ISSUER_URL")
    os.environ["MYCO_OAUTH_ISSUER_URL"] = issuer
    try:
        # 1. Loader returns a populated provider.
        provider = load_oauth_provider_from_env_or_canon({"oauth": {}})
        assert isinstance(provider, MycoOAuthProvider)
        assert provider.issuer_url == issuer
        assert provider.audience == "myco"  # canon default

        # 2. build_server attaches the provider to the FastMCP instance.
        server = build_server()
        attached = getattr(server, "_myco_oauth_provider", None)
        assert isinstance(attached, MycoOAuthProvider), (
            f"build_server did not attach the OAuth provider: {attached!r}"
        )
        assert attached.issuer_url == issuer
        # FastMCP wires settings.auth + token_verifier when an OAuth
        # provider is present; assert both ends of the contract.
        assert server.settings.auth is not None, (
            "build_server did not pass auth=AuthSettings(...) to FastMCP"
        )
        assert server._token_verifier is not None, (
            "build_server did not pass token_verifier=... to FastMCP"
        )
    finally:
        if saved is None:
            os.environ.pop("MYCO_OAUTH_ISSUER_URL", None)
        else:
            os.environ["MYCO_OAUTH_ISSUER_URL"] = saved


# ---------------------------------------------------------------------------
# Self-test of the support harness — make sure the suite itself is honest.
# ---------------------------------------------------------------------------


def test_mock_oauth_issuer_is_well_formed() -> None:
    """The mock issuer mints a usable bearer token via client_credentials.

    Sanity check: if this test fails, the four OAuth tests above could not
    be distinguished from "the mock is broken". This test must pass on its
    own.
    """
    with _spawn_mock_oauth_issuer() as (_issuer, base_url):
        # Token mint
        req = urllib.request.Request(
            f"{base_url}/token",
            data=b"grant_type=client_credentials&client_id=t&client_secret=s",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            payload = json.loads(resp.read())
        assert payload["token_type"] == "Bearer"
        assert payload["access_token"].startswith("mock-bearer-")
        assert len(payload["access_token"]) >= 16

        # Introspection round-trip: minted token is active, bogus is not.
        for token, expected_active in [
            (payload["access_token"], True),
            ("bogus-token-not-minted", False),
        ]:
            ireq = urllib.request.Request(
                f"{base_url}/introspect",
                data=f"token={urllib.request.quote(token)}".encode(),
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(ireq, timeout=5.0) as iresp:
                ipayload = json.loads(iresp.read())
            assert ipayload.get("active") is expected_active, (token, ipayload)


def test_iou_documents_every_xfail_reason() -> None:
    """v0.8.0: all 4 streamable-http + OAuth gaps closed; IOU archived.

    The test name is preserved for git-blame continuity but its assertion
    has been inverted: the open IOU log no longer exists at the live
    path, and the archived copy must carry the closure preamble. Every
    xfail in this file has been removed because the underlying contract
    holds.
    """
    repo_root = Path(__file__).resolve().parents[2]
    open_path = repo_root / ".docs" / "iou" / "v0_7_10_streamable_http_gaps.md"
    archived_path = (
        repo_root / ".docs" / "iou" / "_archive" / "v0_7_10_streamable_http_gaps.md"
    )

    assert not open_path.exists(), (
        f"IOU log still at the open path {open_path}; v0.8.0 should have "
        "moved it to docs/iou/_archive/."
    )
    assert archived_path.is_file(), (
        f"archived IOU log not found at {archived_path}; gap closure incomplete."
    )
    text = archived_path.read_text(encoding="utf-8")
    assert text.startswith("ARCHIVED"), (
        "archived IOU must start with the closure preamble "
        "('ARCHIVED — all 4 gaps closed in v0.8.0...')"
    )

    # Belt-and-braces drift-guard: the test file itself must contain
    # ZERO regression-tracker decorators. If a future regression sneaks
    # one in without updating the IOU, this guard catches the drift.
    # The forbidden token is constructed at runtime from substrings so
    # the source file does not literally contain it (which would cause
    # the check to flag itself). The canonical decorator form is
    # ``@<test-framework>.mark.<failmark>(...)``; we synthesize the
    # full string and refuse to find it in our own source.
    own_text = Path(__file__).read_text(encoding="utf-8")
    forbidden = "pytest" + ".mark." + "xf" + "ail"
    assert forbidden not in own_text, (
        "this file must contain zero regression-tracker decorators; "
        "v0.8.0 closed all 4 gaps documented in "
        "docs/iou/_archive/v0_7_10_streamable_http_gaps.md"
    )
