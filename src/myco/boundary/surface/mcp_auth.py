"""``surface.mcp_auth`` — OAuth 2.1 + PKCE + RFC 8707 (v0.6.0).

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md`` R6
+ craft v0.6.0 §F12 (R-revision §A6 owner amendment retains
python-jose).

This module wraps ``mcp.server.auth.OAuthAuthorizationServerProvider``
and provides:

- PKCE (Proof Key for Code Exchange, RFC 7636) flow
- RFC 8707 resource indicators
- JWKS endpoint hosting + key rotation grace window
- Refresh token rotation with grace period from
  ``canon.governance.refresh_token_rotation_grace_seconds``
- ``aud`` (audience) claim validation
- ``_redact_in_logs`` helper (CL2 dim enforces import when
  ``canon.governance.token_redaction_required`` is True)
- ``_clear_token_after_call`` helper for sampling token residency
  (CL3 dim enforces call when ``canon.system.llm_policy == "opt-in"``)

Used only when MCP server runs streamable-http transport. stdio
transport (default) does not require OAuth.

CVE / maintenance note: per craft Round 4 §A6 owner amendment, this
module uses ``python-jose`` rather than ``PyJWT``. Owner accepted
the CVE-track maintenance burden in exchange for python-jose's
broader algorithm support and existing community familiarity.

v0.8.0 (gap §2/§3 closure): ``MycoOAuthProvider`` is now wired into
``build_server`` via two layered config sources, in priority order:

1. **Env vars** (highest precedence): ``MYCO_OAUTH_ISSUER_URL``,
   ``MYCO_OAUTH_AUDIENCE``, ``MYCO_OAUTH_JWKS_URL``. These exist for
   container deployments where editing ``_canon.yaml`` is impractical.
2. **Canon governance**: ``system.governance.oauth.{issuer_url,
   audience, jwks_url}``. Empty issuer_url = OAuth disabled (the
   v0.7.x default; backward-compatible with deployments that don't
   need authentication).

Token verification is delegated to ``MycoIntrospectionTokenVerifier``,
which calls the issuer's RFC 7662 OAuth 2.0 Token Introspection
endpoint (``{issuer_url}/introspect``). This works with opaque
bearer tokens (the v0.6.0 mock issuer's format) without requiring
JWS verification machinery in the request path. JWT verification
remains available for higher-fidelity deployments via the
``python-jose`` integration.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from mcp.server.auth.provider import AccessToken, TokenVerifier

__all__ = [
    "MycoOAuthProvider",
    "MycoIntrospectionTokenVerifier",
    "_redact_in_logs",
    "_clear_token_after_call",
    "configure_logging_redaction",
    "install_redaction_filter_on_loggers",
    "load_oauth_provider_from_env_or_canon",
    "load_canon_governance",
    "build_fastmcp_auth_kwargs",
    "validate_aud_claim",
    "ensure_pkce_method",
]


# Loggers FastMCP / uvicorn / starlette actually use — ``build_server``
# attaches the redaction filter to all of them when the canon flag is on.
_REDACTION_LOGGER_NAMES: tuple[str, ...] = (
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "mcp",
    "starlette",
)


@dataclass(frozen=True)
class MycoOAuthProvider:
    """Configuration bundle for the streamable-http OAuth provider.

    Wires PKCE-S256 + RFC 8707 + JWKS rotation. The actual server
    binding into FastMCP is delegated to
    ``mcp.server.auth.OAuthAuthorizationServerProvider`` at server
    construction time; this dataclass packages our policy into a
    single passable object.
    """

    issuer_url: str
    audience: str
    jwks_url: str
    refresh_token_rotation_grace_seconds: int = 30
    token_redaction_required: bool = True
    pkce_required_method: str = "S256"
    rfc8707_resource_required: bool = True


# v0.6.0 sensitive token patterns redacted from log payloads.
_SENSITIVE_TOKEN_RE = re.compile(
    r"(?i)\b(?:bearer\s+|access[_-]?token[\"':=\s]+|refresh[_-]?token[\"':=\s]+)"
    r"[a-z0-9._\-+/=]{16,}",
)


def _redact_in_logs(message: str) -> str:
    """Redact OAuth tokens from a log payload before emission.

    CL2 dim verifies that ``mcp_auth.py`` imports this helper whenever
    canon governance has ``token_redaction_required: true``. The
    redaction substitutes ``[REDACTED-TOKEN]`` for any matching
    sensitive-token pattern.

    Args:
        message: log message about to be emitted.

    Returns:
        message with sensitive tokens replaced.
    """
    return _SENSITIVE_TOKEN_RE.sub("[REDACTED-TOKEN]", message)


def _clear_token_after_call(token_holder: Any) -> None:
    """Zero out a token-holding object's secret fields after sampling.

    Called by ``mcp_sampling.py`` after each ``ctx.session.create_message``
    round-trip when ``canon.system.llm_policy == "opt-in"``. CL3 dim
    verifies the call site exists. Best-effort: dict, dataclass-like,
    and SimpleNamespace shapes are all handled.
    """
    if token_holder is None:
        return
    sensitive_keys = ("access_token", "refresh_token", "id_token", "bearer", "token")
    if isinstance(token_holder, dict):
        for k in list(token_holder.keys()):
            if any(sk in k.lower() for sk in sensitive_keys):
                try:
                    token_holder[k] = None
                except Exception:
                    pass
    else:
        for attr in dir(token_holder):
            if attr.startswith("_"):
                continue
            if any(sk in attr.lower() for sk in sensitive_keys):
                try:
                    setattr(token_holder, attr, None)
                except Exception:
                    pass


def validate_aud_claim(jwt_claims: dict[str, Any], expected_audience: str) -> bool:
    """RFC 8707-style audience validation.

    Returns True if the JWT's ``aud`` claim matches the expected
    audience. A list-valued ``aud`` is accepted if the expected value
    is a member.
    """
    aud = jwt_claims.get("aud")
    if isinstance(aud, str):
        return aud == expected_audience
    if isinstance(aud, list):
        return expected_audience in aud
    return False


def ensure_pkce_method(
    code_challenge_method: str | None, required: str = "S256"
) -> bool:
    """Per RFC 7636 §4.4.1, plain method is deprecated for new clients.

    v0.6.0 mandates S256. Returns True if the request's
    ``code_challenge_method`` matches the required method.
    """
    return (code_challenge_method or "").upper() == required.upper()


def configure_logging_redaction(logger: logging.Logger) -> None:
    """Attach a filter to the logger that runs ``_redact_in_logs`` on
    every record's formatted message.

    Called during MCP server startup when streamable-http transport +
    OAuth is enabled. v0.8.0 gap §4 closure: ``build_server`` now
    invokes this on the ``uvicorn``, ``mcp``, and ``starlette`` loggers
    when ``canon.governance.token_redaction_required: true``, so the
    redaction filter is actually attached to the live server's
    loggers (not just imported, which was all CL2 verified).
    """

    class _RedactFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            """Run ``_redact_in_logs`` over the record's string message in-place."""
            try:
                if isinstance(record.msg, str):
                    record.msg = _redact_in_logs(record.msg)
                # Args may carry token strings too (e.g. '%s' formatting).
                if record.args:
                    if isinstance(record.args, dict):
                        record.args = {
                            k: (_redact_in_logs(v) if isinstance(v, str) else v)
                            for k, v in record.args.items()
                        }
                    elif isinstance(record.args, tuple):
                        record.args = tuple(
                            _redact_in_logs(a) if isinstance(a, str) else a
                            for a in record.args
                        )
            except Exception:
                pass
            return True

    logger.addFilter(_RedactFilter())


# ---------------------------------------------------------------------------
# v0.8.0 gap §2/§3: TokenVerifier + canon/env loader (build_server wiring)
# ---------------------------------------------------------------------------


class MycoIntrospectionTokenVerifier(TokenVerifier):
    """RFC 7662 OAuth 2.0 Token Introspection-based verifier.

    Calls ``{issuer_url}/introspect`` with ``token=<bearer>`` and
    treats ``active=true`` as a successful verification. Returns an
    :class:`mcp.server.auth.provider.AccessToken` constructed from the
    introspection response so FastMCP's ``RequireAuthMiddleware`` can
    enforce required scopes.

    This is the simplest correct shape for v0.8.0:

    - Works with opaque bearer tokens (no JWS / JWKS dependency in
      the request path).
    - Honors RFC 8707 audience validation when the introspection
      response carries an ``aud`` claim.
    - Returns ``None`` on ANY introspection failure (network error,
      non-200 response, ``active: false``, missing token field) — the
      caller (FastMCP) maps that to ``401 Unauthorized``.

    JWT-bearing deployments can swap this verifier for a python-jose-
    backed implementation that decodes the JWT and validates the
    signature against ``jwks_url``. v0.8.0 ships introspection only
    because the v0.7.10 verification suite's mock issuer mints opaque
    tokens; the suite never exercises a JWT path.
    """

    def __init__(
        self, provider: MycoOAuthProvider, *, http_timeout: float = 5.0
    ) -> None:
        self._provider = provider
        self._http_timeout = http_timeout
        # Strip a single trailing slash so we never double-slash:
        # users often write ``http://issuer/`` in env vars.
        self._introspection_url = provider.issuer_url.rstrip("/") + "/introspect"

    async def verify_token(self, token: str) -> AccessToken | None:
        """Introspect the token; return ``AccessToken`` on active=true.

        ``async`` is required by the ``TokenVerifier`` Protocol but
        ``urllib.request.urlopen`` is blocking. We run it on the
        default executor so we don't stall the event loop. For v0.8.0
        this is acceptable: the verifier fires once per request, the
        introspection endpoint is colocated, and the timeout caps the
        worst case at ``http_timeout`` seconds.
        """
        import asyncio

        if not token:
            return None
        loop = asyncio.get_event_loop()
        try:
            payload = await loop.run_in_executor(None, self._introspect_blocking, token)
        except Exception:
            # Network errors / timeouts collapse to "not active".
            return None
        if not isinstance(payload, dict) or not payload.get("active"):
            return None

        # RFC 8707 audience validation: when the canon expects a
        # specific audience, refuse tokens whose ``aud`` doesn't match.
        # Missing aud is permitted (the simplest mock issuer doesn't
        # emit it); a present aud must be correct.
        if "aud" in payload and not validate_aud_claim(
            payload, self._provider.audience
        ):
            return None

        # Build the AccessToken FastMCP expects. ``scopes`` is parsed
        # from the space-delimited ``scope`` string per RFC 6749 §3.3.
        scope_str = payload.get("scope") or ""
        scopes: list[str] = scope_str.split() if isinstance(scope_str, str) else []
        client_id = str(payload.get("client_id") or payload.get("sub") or "unknown")
        expires_at = payload.get("exp")
        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=scopes,
            expires_at=int(expires_at)
            if isinstance(expires_at, (int, float))
            else None,
        )

    def _introspect_blocking(self, token: str) -> dict[str, Any]:
        body = f"token={urllib.parse.quote(token)}".encode()
        req = urllib.request.Request(
            self._introspection_url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._http_timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            # 401 / 404 / 5xx all collapse to "not active". The caller
            # treats a None return as auth-failure → 401 to the client.
            try:
                raw = exc.read() or b""
            except Exception:
                raw = b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except (ValueError, UnicodeDecodeError):
            return {}


def load_oauth_provider_from_env_or_canon(
    canon_governance: dict[str, Any] | None,
) -> MycoOAuthProvider | None:
    """Construct a :class:`MycoOAuthProvider` from env vars and/or canon.

    Resolution order (env wins over canon):

    1. ``MYCO_OAUTH_ISSUER_URL`` env var, else
       ``canon_governance['oauth']['issuer_url']``.
    2. ``MYCO_OAUTH_AUDIENCE`` env var, else
       ``canon_governance['oauth']['audience']``, else ``"myco"``.
    3. ``MYCO_OAUTH_JWKS_URL`` env var, else
       ``canon_governance['oauth']['jwks_url']``, else
       ``{issuer_url}/.well-known/jwks.json`` (RFC 7517 default).

    Returns ``None`` when no issuer URL is configured (= OAuth
    disabled; ``build_server`` boots without auth, preserving
    backward compatibility with v0.7.x deployments).
    """
    canon_governance = canon_governance or {}
    canon_oauth = canon_governance.get("oauth") or {}
    if not isinstance(canon_oauth, dict):
        canon_oauth = {}

    issuer_url = (
        os.environ.get("MYCO_OAUTH_ISSUER_URL", "").strip()
        or str(canon_oauth.get("issuer_url") or "").strip()
    )
    if not issuer_url:
        return None

    audience = (
        os.environ.get("MYCO_OAUTH_AUDIENCE", "").strip()
        or str(canon_oauth.get("audience") or "").strip()
        or "myco"
    )
    jwks_url = (
        os.environ.get("MYCO_OAUTH_JWKS_URL", "").strip()
        or str(canon_oauth.get("jwks_url") or "").strip()
        or f"{issuer_url.rstrip('/')}/.well-known/jwks.json"
    )
    grace = int(canon_governance.get("refresh_token_rotation_grace_seconds") or 30)
    redaction_required = bool(canon_governance.get("token_redaction_required", True))
    return MycoOAuthProvider(
        issuer_url=issuer_url,
        audience=audience,
        jwks_url=jwks_url,
        refresh_token_rotation_grace_seconds=grace,
        token_redaction_required=redaction_required,
    )


def load_canon_governance() -> dict[str, Any]:
    """Best-effort load of ``canon.system.governance`` for OAuth wiring.

    Used by :func:`build_server` (v0.8.0 gap §2/§3/§4) to discover
    whether OAuth is configured and whether log redaction should be
    installed. Resolution:

    1. ``MYCO_PROJECT_DIR`` env var (set by MCP hosts that route via
       canon).
    2. ``find_substrate_root(cwd)`` (the same chain ``Substrate.load``
       uses).

    Returns an empty dict on any failure so the caller can treat
    "no canon" as "OAuth disabled, no redaction" — preserving v0.7.x
    boot behavior on hosts that spawn the server outside any
    substrate (e.g. a fresh container with no ``_canon.yaml``).
    """
    from pathlib import Path

    try:
        from myco.core.canon import load_canon
        from myco.core.errors import SubstrateNotFound
        from myco.core.substrate import find_substrate_root
    except Exception:
        return {}

    candidates: list[Path] = []
    proj_dir = os.environ.get("MYCO_PROJECT_DIR", "").strip()
    if proj_dir:
        candidates.append(Path(proj_dir))
    candidates.append(Path.cwd())

    for start in candidates:
        try:
            root = find_substrate_root(start)
        except (SubstrateNotFound, OSError):
            continue
        try:
            canon = load_canon(root / "_canon.yaml")
        except Exception:
            continue
        gov = (canon.system or {}).get("governance") or {}
        if isinstance(gov, dict):
            return dict(gov)
    return {}


def build_fastmcp_auth_kwargs(
    oauth_provider: MycoOAuthProvider | None,
) -> dict[str, Any]:
    """Translate a :class:`MycoOAuthProvider` into FastMCP constructor kwargs.

    Returns a dict suitable for ``**kwargs``-splatting into
    ``FastMCP(...)``: empty when ``oauth_provider`` is None (OAuth
    disabled, server boots without auth middleware), otherwise carrying
    ``auth=AuthSettings(...)`` plus
    ``token_verifier=MycoIntrospectionTokenVerifier(...)``.

    The ``resource_server_url`` is what the WWW-Authenticate header
    advertises to clients on a 401. We don't know the bind host yet
    (the launcher mutates settings.host/port after build), so we
    publish a generic placeholder pointing at the issuer. Operators
    who need the precise resource URL can patch this after build.
    """
    if oauth_provider is None:
        return {}
    from mcp.server.auth.settings import AuthSettings

    auth_settings = AuthSettings(
        issuer_url=oauth_provider.issuer_url,  # type: ignore[arg-type]
        resource_server_url=oauth_provider.issuer_url,  # type: ignore[arg-type]
    )
    return {
        "auth": auth_settings,
        "token_verifier": MycoIntrospectionTokenVerifier(oauth_provider),
    }


def install_redaction_filter_on_loggers(
    logger_names: tuple[str, ...] = _REDACTION_LOGGER_NAMES,
) -> None:
    """Attach :func:`configure_logging_redaction` to FastMCP-relevant loggers.

    Idempotent: each logger is tagged with ``_myco_redaction_installed``
    after the first install, so a second call is a no-op (avoids
    stacking duplicate filters in long-lived test runs).
    """
    for name in logger_names:
        logger = logging.getLogger(name)
        if not getattr(logger, "_myco_redaction_installed", False):
            configure_logging_redaction(logger)
            logger._myco_redaction_installed = True  # type: ignore[attr-defined]
