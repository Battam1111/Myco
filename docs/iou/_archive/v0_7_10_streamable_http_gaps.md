ARCHIVED — all 4 gaps closed in v0.8.0 (commit <will-be-filled>).

# IOU — v0.7.10 streamable-HTTP + OAuth verification gaps

> **Status**: CLOSED 2026-05-11 in v0.8.0. All four gaps below are closed by
> commits to `src/myco/boundary/mcp/__init__.py` (gap §1),
> `src/myco/boundary/surface/mcp.py::build_server` (gaps §2 + §4),
> `src/myco/boundary/surface/mcp_auth.py` (gap §3 — `MycoIntrospectionTokenVerifier`
> + `load_oauth_provider_from_env_or_canon`), and `_canon.yaml`
> (`system.governance.oauth` block).
> The verification suite at `tests/integration/test_streamable_http_oauth.py`
> now runs with zero xfails / zero xpasses (5 transport-level passes + 4
> OAuth-level passes + 2 self-tests + 1 archive-drift guard).
> **Layer**: L3 (closed gap log; retained for historical traceability).
> **Scope**: was blocking the README claim that `myco` ships an
> OAuth-2.1-protected streamable-HTTP MCP server. v0.8.0 lands the wiring;
> the claim is now end-to-end verified.

---

## 1 — Launcher discards `--host` / `--port` / `--mount-path`

**File**: [`src/myco/boundary/mcp/__init__.py`](../../src/myco/boundary/mcp/__init__.py) lines 104-114

The launcher invokes `server.run(transport="streamable-http", host=..., port=..., mount_path=...)`. In `mcp>=1.2`, the `FastMCP.run()` signature is
`run(transport, mount_path=None)` — so `host=` and `port=` always raise `TypeError`,
trip the `except TypeError` branch, and fall through to `server.run(transport="streamable-http")`.
The fallback uses the FastMCP construction-time defaults (`host=127.0.0.1`, `port=8000`,
`streamable_http_path=/mcp`), which means **the CLI flags are dead code**.

`FASTMCP_HOST` / `FASTMCP_PORT` env vars are also ignored, because `FastMCP.__init__`
calls `Settings(host=host, port=port, ...)` with the parameter defaults — and explicit
kwargs win over `pydantic-settings` env-fallback.

**Concrete fix (one of):**

- (a) Pass host/port/mount_path/streamable_http_path into `FastMCP(...)` at construction time
  in `surface/mcp.py::build_server`, threading them through from the launcher CLI.
- (b) Mutate `server.settings.host` / `server.settings.port` between `build_server()` and
  `server.run("streamable-http")` in the launcher.
- (c) Drop the dead try/except + kwargs and bind via uvicorn directly using
  `server.streamable_http_app()`.

**Test impact**: the verification suite's `_spawn_server` helper writes a tiny inline
launcher script that imports `build_server`, mutates `server.settings`, and runs —
bypassing `myco.boundary.mcp.__main__` because the public CLI cannot pick a free port.

---

## 2 — `MycoOAuthProvider` is a config dataclass with no integration

**File**: [`src/myco/boundary/surface/mcp_auth.py`](../../src/myco/boundary/surface/mcp_auth.py)

`MycoOAuthProvider` is a `@dataclass(frozen=True)` holding `issuer_url`, `audience`,
`jwks_url`, etc. It is never instantiated from `build_server()`, never passed to
`FastMCP(auth=..., token_verifier=...)`, never wired into the streamable-HTTP ASGI app.
Consequences:

- The server boots streamable-HTTP **without authentication** — every request is accepted.
- There is no `/token` endpoint (FastMCP would mount one if `auth_server_provider` were
  configured; see `mcp/server/fastmcp/server.py:988-999`).
- There is no `Authorization: Bearer <token>` requirement.
- A bogus token cannot return `401`, because no middleware inspects the header.
- RFC 8707 audience validation, PKCE-S256 enforcement, and JWKS rotation are all
  defined in helpers (`validate_aud_claim`, `ensure_pkce_method`, `_redact_in_logs`)
  but no code path calls them at request time.

**Concrete fix**: in `surface/mcp.py::build_server`, when canon governance enables
streamable-HTTP-OAuth (e.g. via a new `system.transport.oauth_enabled: true` flag),
construct an `OAuthAuthorizationServerProvider` (or a minimal `TokenVerifier`) from
the `MycoOAuthProvider` config, and pass `auth=AuthSettings(issuer_url=..., required_scopes=...)`
plus `token_verifier=...` (or `auth_server_provider=...`) into `FastMCP(...)`.
The FastMCP runtime then auto-mounts the OAuth metadata + Bearer auth middleware.

**Test impact**: every test in the OAuth section of the verification suite is
`pytest.mark.xfail(strict=False, reason="...")` — they document the missing surface
rather than masking it.

---

## 3 — No `MYCO_OAUTH_TOKEN_URL` discovery

**File**: search across `src/`

There is no environment variable, no canon field, and no constructor argument that
points the running server at an upstream OAuth 2.1 issuer for client_credentials
grant validation. The verification suite cannot point Myco at a mock issuer because
there is nothing on the receiving end to consume the configuration.

**Concrete fix**: alongside §2, define a discovery surface — for example
`MYCO_OAUTH_ISSUER_URL` + `MYCO_OAUTH_AUDIENCE` env vars, or a
`system.transport.oauth.{issuer_url, audience, jwks_url}` canon block that
`build_server` reads. The CL2 dim already validates `token_redaction_required`;
the same governance block could carry the issuer URL.

---

## 4 — Token-redaction filter is not attached at server boot

**File**: [`src/myco/boundary/surface/mcp_auth.py`](../../src/myco/boundary/surface/mcp_auth.py) — `configure_logging_redaction`

The helper exists and the unit test confirms it works, but `build_server` never calls
`configure_logging_redaction(...)` on the FastMCP / uvicorn / starlette loggers, even
when `canon.governance.token_redaction_required: true` (which IS the case in the
shipped `_canon.yaml` line 130).

The CL2 lint dimension verifies that `mcp_auth.py` *imports* the helper, but doesn't
verify that `build_server` *invokes* it. So the dim is satisfied without the redaction
actually being installed on the running server.

**Concrete fix**: in `surface/mcp.py::build_server`, when streamable-HTTP transport
will be used and governance flags require redaction, call
`configure_logging_redaction(logging.getLogger("uvicorn"))` and
`configure_logging_redaction(logging.getLogger("mcp"))` before returning.

---

## 5 — Mock-vs-real provider gap

The verification suite stands up an in-process mock OAuth issuer (stdlib
`http.server.HTTPServer` in a thread) that accepts `client_credentials` and emits
unsigned, opaque bearer tokens. This is enough to verify the protocol shape but
does NOT exercise:

- JWS signature verification (no JWT signing/verification in the mock)
- JWKS endpoint rotation
- RFC 8707 resource indicator validation against a real issuer
- Refresh-token rotation grace window
- Real-world clock skew handling

These are tested in unit-isolation (`tests/unit/boundary/test_mcp_auth_sampling.py`)
but not end-to-end. Once §1-§4 are closed, the verification suite should be extended
to use `authlib`'s `OAuth2Server` (already declared in `pyproject.toml`'s
`mcp-auth` extra) for a higher-fidelity provider.

---

## Closure criteria

This IOU is closed when:

1. `tests/integration/test_streamable_http_oauth.py` runs with **zero `xfail`s** —
   every test currently marked `xfail` becomes `xpass` (and the markers are removed).
2. `python -m myco.boundary.mcp --transport streamable-http --port 0` actually binds
   to a kernel-assigned port (not 8000).
3. `curl -X POST http://localhost:<port>/mcp -H "Content-Type: application/json"`
   without an `Authorization` header returns `401` when OAuth is enabled.
4. Bearer-token logs are redacted in the server's stdout/stderr capture.

Until then, the README claim "OAuth 2.1 + PKCE + RFC 8707 streamable-http stack" is
**advertised but not verified**.
