"""Unit tests for ``boundary.surface.mcp_auth`` v0.8.0 helpers.

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md`` R6
+ v0.8.0 multimedia/OAuth wiring craft (gap §2/§3/§4 closure).

These tests pin the v0.8.0 helper contract in
``src/myco/boundary/surface/mcp_auth.py`` that the v0.8.4 CI cov-fail-
under relax was waiting on. They exercise every code path that does
NOT require booting a real FastMCP / uvicorn / streamable-HTTP server:

* :class:`MycoIntrospectionTokenVerifier` — verify_token honors
  ``active=true`` / RFC 8707 audience / opaque-token shapes; the
  blocking introspection round-trip is mocked at ``urllib.request.urlopen``
  so no real network egress occurs.
* :func:`load_oauth_provider_from_env_or_canon` — env vars beat canon
  governance; missing issuer URL collapses to ``None`` (OAuth disabled,
  v0.7.x backward-compat).
* :func:`load_canon_governance` — best-effort; returns empty dict when
  no substrate is reachable from cwd / ``MYCO_PROJECT_DIR``.
* :func:`build_fastmcp_auth_kwargs` — ``None`` provider yields ``{}``
  (server boots without auth); a real provider yields ``auth=`` +
  ``token_verifier=``.
* :func:`install_redaction_filter_on_loggers` — idempotent across
  repeat calls (tagged via ``_myco_redaction_installed`` sentinel).
* :func:`prepare_fastmcp_oauth_prelude` — end-to-end glue that
  ``build_server`` invokes; we patch the underlying loaders so the
  test stays pure-unit.
* :class:`_RedactFilter` — args-dict + args-tuple branches in the
  filter body (the existing test in
  ``tests/unit/boundary/test_mcp_auth_sampling.py`` only covers the
  msg branch).

All tests run on a default Python install with NO network, NO real
FastMCP boot, NO uvicorn. The integration suite at
``tests/integration/test_streamable_http_oauth.py`` covers the
end-to-end OAuth round-trip behind a subprocess-based mock issuer;
this file complements that with cheap unit-grain coverage so v0.9
can revert ``--cov-fail-under=82`` to ``=85``.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import urllib.error
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from myco.boundary.surface.mcp_auth import (
    MycoIntrospectionTokenVerifier,
    MycoOAuthProvider,
    _redact_in_logs,
    build_fastmcp_auth_kwargs,
    configure_logging_redaction,
    install_redaction_filter_on_loggers,
    load_canon_governance,
    load_oauth_provider_from_env_or_canon,
    prepare_fastmcp_oauth_prelude,
)

# ---------------------------------------------------------------------------
# MycoIntrospectionTokenVerifier
# ---------------------------------------------------------------------------


def _make_provider(
    *,
    issuer: str = "https://issuer.example",
    audience: str = "myco",
) -> MycoOAuthProvider:
    """Build a minimal :class:`MycoOAuthProvider` for verifier tests."""
    return MycoOAuthProvider(
        issuer_url=issuer,
        audience=audience,
        jwks_url=f"{issuer}/.well-known/jwks.json",
    )


def _fake_urlopen_response(payload: dict[str, Any] | bytes, *, status: int = 200):
    """Return a context-manager-shaped fake matching ``urllib.request.urlopen``."""
    body = json.dumps(payload).encode("utf-8") if isinstance(payload, dict) else payload

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return body

    return _Resp()


def test_verifier_init_strips_trailing_issuer_slash() -> None:
    """``http://issuer/`` (trailing slash) → introspection URL has no double slash."""
    v = MycoIntrospectionTokenVerifier(_make_provider(issuer="http://issuer.example/"))
    assert v._introspection_url == "http://issuer.example/introspect"


def test_verifier_init_no_trailing_slash() -> None:
    """``http://issuer`` (no trailing slash) → introspection URL is correctly suffixed."""
    v = MycoIntrospectionTokenVerifier(_make_provider(issuer="http://issuer.example"))
    assert v._introspection_url == "http://issuer.example/introspect"


def test_verifier_init_preserves_http_timeout() -> None:
    """Custom ``http_timeout`` is stashed on the verifier for later use."""
    v = MycoIntrospectionTokenVerifier(_make_provider(), http_timeout=12.5)
    assert v._http_timeout == 12.5


def test_verify_token_active_true_returns_access_token() -> None:
    """RFC 7662 ``active: true`` introspection → :class:`AccessToken` object."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    payload = {
        "active": True,
        "client_id": "client-42",
        "scope": "read write",
        "exp": 1234567890,
    }
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(payload),
    ):
        result = asyncio.run(v.verify_token("opaque-bearer-token"))
    assert result is not None
    assert result.client_id == "client-42"
    assert result.scopes == ["read", "write"]
    assert result.expires_at == 1234567890
    assert result.token == "opaque-bearer-token"


def test_verify_token_empty_token_returns_none() -> None:
    """An empty token short-circuits before any HTTP call → ``None``."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    assert asyncio.run(v.verify_token("")) is None


def test_verify_token_active_false_returns_none() -> None:
    """``active: false`` payload → ``None`` (caller maps to 401)."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response({"active": False}),
    ):
        assert asyncio.run(v.verify_token("revoked-token")) is None


def test_verify_token_aud_mismatch_returns_none() -> None:
    """RFC 8707: ``aud`` claim mismatch → ``None`` (introspection rejected)."""
    v = MycoIntrospectionTokenVerifier(_make_provider(audience="myco"))
    payload = {"active": True, "aud": "some-other-audience", "client_id": "c"}
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(payload),
    ):
        assert asyncio.run(v.verify_token("foreign-aud-token")) is None


def test_verify_token_aud_match_passes() -> None:
    """RFC 8707: matching ``aud`` claim → ``AccessToken``."""
    v = MycoIntrospectionTokenVerifier(_make_provider(audience="myco"))
    payload = {
        "active": True,
        "aud": "myco",
        "client_id": "c",
        "scope": "read",
    }
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(payload),
    ):
        result = asyncio.run(v.verify_token("good-aud-token"))
    assert result is not None
    assert result.client_id == "c"


def test_verify_token_missing_aud_permitted() -> None:
    """A response missing ``aud`` is accepted (mock-issuer compatibility)."""
    v = MycoIntrospectionTokenVerifier(_make_provider(audience="myco"))
    payload = {"active": True, "client_id": "c", "scope": ""}
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(payload),
    ):
        result = asyncio.run(v.verify_token("aud-omitted-token"))
    assert result is not None


def test_verify_token_network_error_returns_none() -> None:
    """A urllib network error → ``None`` (caller maps to auth failure)."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        assert asyncio.run(v.verify_token("any-token")) is None


def test_verify_token_non_dict_payload_returns_none() -> None:
    """A response that decodes to a non-dict (e.g. JSON list) → ``None``."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(b'["not", "a", "dict"]'),
    ):
        assert asyncio.run(v.verify_token("any-token")) is None


def test_verify_token_falls_back_to_sub_when_no_client_id() -> None:
    """When ``client_id`` is absent the verifier uses ``sub`` then ``"unknown"``."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    payload = {"active": True, "sub": "user-7", "scope": "x"}
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(payload),
    ):
        result = asyncio.run(v.verify_token("token"))
    assert result is not None
    assert result.client_id == "user-7"


def test_verify_token_unknown_client_id_default() -> None:
    """No ``client_id`` and no ``sub`` → AccessToken.client_id = ``"unknown"``."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    payload = {"active": True, "scope": ""}
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(payload),
    ):
        result = asyncio.run(v.verify_token("token"))
    assert result is not None
    assert result.client_id == "unknown"


def test_introspect_blocking_handles_http_error() -> None:
    """``HTTPError`` is caught and the body is read for diagnostic context."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    err = urllib.error.HTTPError(
        url="http://issuer.example/introspect",
        code=401,
        msg="Unauthorized",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b'{"active": false}'),
    )
    with patch("urllib.request.urlopen", side_effect=err):
        out = v._introspect_blocking("any-token")
    assert out == {"active": False}


def test_introspect_blocking_handles_unreadable_http_error_body() -> None:
    """``HTTPError`` whose ``.read()`` raises → empty dict (graceful)."""
    v = MycoIntrospectionTokenVerifier(_make_provider())

    class _BadErr(urllib.error.HTTPError):
        def read(self):  # type: ignore[override]
            raise OSError("body stream closed")

    err = _BadErr(
        url="http://issuer.example/introspect",
        code=500,
        msg="Server Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=err):
        out = v._introspect_blocking("token")
    assert out == {}


def test_introspect_blocking_invalid_json_returns_empty() -> None:
    """A malformed JSON body → empty dict (caller treats as inactive)."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(b"this is not json"),
    ):
        out = v._introspect_blocking("token")
    assert out == {}


def test_introspect_blocking_empty_body_returns_empty() -> None:
    """An empty body → empty dict (the ``if raw:`` short-circuit)."""
    v = MycoIntrospectionTokenVerifier(_make_provider())
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen_response(b""),
    ):
        out = v._introspect_blocking("token")
    assert out == {}


# ---------------------------------------------------------------------------
# load_oauth_provider_from_env_or_canon
# ---------------------------------------------------------------------------


def test_load_provider_no_issuer_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No env var, no canon issuer URL → ``None`` (OAuth disabled)."""
    monkeypatch.delenv("MYCO_OAUTH_ISSUER_URL", raising=False)
    monkeypatch.delenv("MYCO_OAUTH_AUDIENCE", raising=False)
    monkeypatch.delenv("MYCO_OAUTH_JWKS_URL", raising=False)
    assert load_oauth_provider_from_env_or_canon(None) is None
    assert load_oauth_provider_from_env_or_canon({}) is None
    assert load_oauth_provider_from_env_or_canon({"oauth": {}}) is None


def test_load_provider_canon_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Canon-supplied issuer URL → provider built from canon values only."""
    monkeypatch.delenv("MYCO_OAUTH_ISSUER_URL", raising=False)
    monkeypatch.delenv("MYCO_OAUTH_AUDIENCE", raising=False)
    monkeypatch.delenv("MYCO_OAUTH_JWKS_URL", raising=False)
    provider = load_oauth_provider_from_env_or_canon(
        {
            "oauth": {
                "issuer_url": "https://canon-issuer.example",
                "audience": "canon-audience",
                "jwks_url": "https://canon-issuer.example/jwks",
            },
            "refresh_token_rotation_grace_seconds": 90,
            "token_redaction_required": False,
        }
    )
    assert provider is not None
    assert provider.issuer_url == "https://canon-issuer.example"
    assert provider.audience == "canon-audience"
    assert provider.jwks_url == "https://canon-issuer.example/jwks"
    assert provider.refresh_token_rotation_grace_seconds == 90
    assert provider.token_redaction_required is False


def test_load_provider_env_beats_canon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env vars override canon values per the documented precedence rule.

    This is the v0.8.0 contract: container deployments where editing
    ``_canon.yaml`` is impractical can override every OAuth field via
    env vars. We verify all three: issuer / audience / jwks_url.
    """
    monkeypatch.setenv("MYCO_OAUTH_ISSUER_URL", "https://env-issuer.example")
    monkeypatch.setenv("MYCO_OAUTH_AUDIENCE", "env-audience")
    monkeypatch.setenv("MYCO_OAUTH_JWKS_URL", "https://env-issuer.example/keys")
    provider = load_oauth_provider_from_env_or_canon(
        {
            "oauth": {
                "issuer_url": "https://canon-issuer.example",
                "audience": "canon-audience",
                "jwks_url": "https://canon-issuer.example/jwks",
            }
        }
    )
    assert provider is not None
    assert provider.issuer_url == "https://env-issuer.example"
    assert provider.audience == "env-audience"
    assert provider.jwks_url == "https://env-issuer.example/keys"


def test_load_provider_default_audience_when_neither_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issuer URL given but no audience anywhere → defaults to ``"myco"``."""
    monkeypatch.delenv("MYCO_OAUTH_AUDIENCE", raising=False)
    monkeypatch.setenv("MYCO_OAUTH_ISSUER_URL", "https://issuer.example")
    monkeypatch.delenv("MYCO_OAUTH_JWKS_URL", raising=False)
    provider = load_oauth_provider_from_env_or_canon(None)
    assert provider is not None
    assert provider.audience == "myco"


def test_load_provider_default_jwks_url_derived_from_issuer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No jwks_url anywhere → default to ``{issuer}/.well-known/jwks.json``."""
    monkeypatch.setenv("MYCO_OAUTH_ISSUER_URL", "https://issuer.example/")
    monkeypatch.delenv("MYCO_OAUTH_JWKS_URL", raising=False)
    monkeypatch.delenv("MYCO_OAUTH_AUDIENCE", raising=False)
    provider = load_oauth_provider_from_env_or_canon(None)
    assert provider is not None
    assert provider.jwks_url == "https://issuer.example/.well-known/jwks.json"


def test_load_provider_canon_oauth_not_dict_treated_as_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed canon (``oauth`` not a dict) is normalised to ``{}`` instead
    of raising — defensive for hand-edited canon files.
    """
    monkeypatch.delenv("MYCO_OAUTH_ISSUER_URL", raising=False)
    # ``oauth`` is a string instead of a dict; the loader should treat
    # it as empty and return None (no issuer URL).
    assert load_oauth_provider_from_env_or_canon({"oauth": "not a dict"}) is None


# ---------------------------------------------------------------------------
# load_canon_governance
# ---------------------------------------------------------------------------


def test_load_canon_governance_real_substrate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reading the in-tree ``_canon.yaml`` returns a non-empty governance dict.

    The Myco substrate itself ships ``governance: {...}`` so a self-load
    against ``MYCO_PROJECT_DIR`` exercises the happy path. We don't pin
    specific keys (canon evolves) — just that the call returns a dict.
    """
    monkeypatch.delenv("MYCO_OAUTH_ISSUER_URL", raising=False)
    # The test runner's cwd is the substrate root; both branches of
    # the candidate list (env-then-cwd) hit the same root.
    out = load_canon_governance()
    assert isinstance(out, dict)


def test_load_canon_governance_empty_when_no_substrate(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """An empty / non-substrate cwd → ``{}`` (graceful fall-through).

    We point ``MYCO_PROJECT_DIR`` at a tmp_path that has no
    ``_canon.yaml`` and ``Path.cwd`` at the same dir; both candidates
    fail to find a substrate, so the helper returns ``{}``.
    """
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert load_canon_governance() == {}


def test_load_canon_governance_empty_string_env_skipped(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """``MYCO_PROJECT_DIR=""`` is treated as unset (whitespace-stripped)."""
    monkeypatch.setenv("MYCO_PROJECT_DIR", "   ")
    monkeypatch.chdir(tmp_path)
    out = load_canon_governance()
    assert out == {}


def test_load_canon_governance_handles_import_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the underlying ``myco.core.canon`` import fails the helper
    returns ``{}`` rather than propagating — preserves the
    "boots without canon" v0.7.x guarantee.
    """
    import sys

    # Stash a None sentinel in sys.modules so the dynamic import inside
    # ``load_canon_governance`` raises ImportError on the next call.
    monkeypatch.setitem(sys.modules, "myco.core.canon", None)
    out = load_canon_governance()
    assert out == {}


# ---------------------------------------------------------------------------
# build_fastmcp_auth_kwargs
# ---------------------------------------------------------------------------


def test_build_fastmcp_auth_kwargs_none_provider_returns_empty() -> None:
    """``None`` provider → empty dict (FastMCP boots without auth)."""
    assert build_fastmcp_auth_kwargs(None) == {}


def test_build_fastmcp_auth_kwargs_real_provider() -> None:
    """A real provider → kwargs carrying ``auth=`` + ``token_verifier=``.

    ``mcp.server.auth.settings.AuthSettings`` must accept the issuer URL
    we pass. We exercise the import + construction without needing a
    real FastMCP runtime — just check the dict shape FastMCP's
    ``__init__`` would splat.
    """
    pytest.importorskip(
        "mcp.server.auth.settings",
        reason="myco[mcp] extra (mcp>=1.2) needed for AuthSettings construction",
    )
    provider = _make_provider()
    kwargs = build_fastmcp_auth_kwargs(provider)
    assert "auth" in kwargs
    assert "token_verifier" in kwargs
    assert isinstance(kwargs["token_verifier"], MycoIntrospectionTokenVerifier)


# ---------------------------------------------------------------------------
# install_redaction_filter_on_loggers
# ---------------------------------------------------------------------------


def test_install_redaction_filter_attaches_once() -> None:
    """First install call attaches a filter; second call is a no-op."""
    # Use a fresh logger name unique to this test so prior runs don't
    # leak state across the assertion.
    logger_name = "myco-test-install-once"
    logger = logging.getLogger(logger_name)
    # Reset for hygiene; some prior test runs may share the logger
    # registry across the session.
    for f in list(logger.filters):
        logger.removeFilter(f)
    if hasattr(logger, "_myco_redaction_installed"):
        delattr(logger, "_myco_redaction_installed")

    install_redaction_filter_on_loggers((logger_name,))
    after_first = len(logger.filters)
    install_redaction_filter_on_loggers((logger_name,))
    after_second = len(logger.filters)

    assert after_first == 1
    assert after_second == 1, "second install must be a no-op (idempotency contract)"
    assert getattr(logger, "_myco_redaction_installed", False) is True


def test_install_redaction_filter_default_logger_set_does_not_raise() -> None:
    """The default ``logger_names`` tuple is the FastMCP/uvicorn surface;
    invoking it must not raise (the loggers may or may not exist, but
    ``logging.getLogger`` always returns a usable object).
    """
    # No assertion beyond "doesn't raise" — the side-effect on real
    # loggers is exercised by the dedicated single-logger test above.
    install_redaction_filter_on_loggers()


# ---------------------------------------------------------------------------
# prepare_fastmcp_oauth_prelude
# ---------------------------------------------------------------------------


def test_prepare_prelude_no_oauth_no_redaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No env vars + canon governance with no oauth + redaction off →
    empty kwargs, ``None`` provider, redaction NOT installed.
    """
    monkeypatch.delenv("MYCO_OAUTH_ISSUER_URL", raising=False)
    # Patch the loader so the test isn't sensitive to the in-tree canon.
    with patch(
        "myco.boundary.surface.mcp_auth.load_canon_governance",
        return_value={"token_redaction_required": False},
    ):
        kwargs, provider = prepare_fastmcp_oauth_prelude()
    assert kwargs == {}
    assert provider is None


def test_prepare_prelude_oauth_disabled_redaction_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No oauth issuer + redaction flag on → empty kwargs, ``None`` provider,
    redaction installed (idempotent).
    """
    monkeypatch.delenv("MYCO_OAUTH_ISSUER_URL", raising=False)
    install_called: list[bool] = []

    def _spy_install(*_a, **_kw) -> None:
        install_called.append(True)

    with (
        patch(
            "myco.boundary.surface.mcp_auth.load_canon_governance",
            return_value={"token_redaction_required": True},
        ),
        patch(
            "myco.boundary.surface.mcp_auth.install_redaction_filter_on_loggers",
            new=_spy_install,
        ),
    ):
        kwargs, provider = prepare_fastmcp_oauth_prelude()
    assert kwargs == {}
    assert provider is None
    assert install_called == [True]


def test_prepare_prelude_full_oauth_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env-supplied issuer + redaction on → kwargs populated, provider built,
    redaction install spy fires.

    The mcp.server.auth.settings.AuthSettings import is exercised inside
    build_fastmcp_auth_kwargs; we skip if the extras aren't present.
    """
    pytest.importorskip(
        "mcp.server.auth.settings",
        reason="myco[mcp] extra needed for AuthSettings construction",
    )
    monkeypatch.setenv("MYCO_OAUTH_ISSUER_URL", "https://prelude-issuer.example")
    install_called: list[bool] = []

    def _spy_install(*_a, **_kw) -> None:
        install_called.append(True)

    with (
        patch(
            "myco.boundary.surface.mcp_auth.load_canon_governance",
            return_value={"token_redaction_required": True},
        ),
        patch(
            "myco.boundary.surface.mcp_auth.install_redaction_filter_on_loggers",
            new=_spy_install,
        ),
    ):
        kwargs, provider = prepare_fastmcp_oauth_prelude()
    assert provider is not None
    assert provider.issuer_url == "https://prelude-issuer.example"
    assert "auth" in kwargs
    assert "token_verifier" in kwargs
    assert install_called == [True]


# ---------------------------------------------------------------------------
# _RedactFilter — args dict + tuple branches
# ---------------------------------------------------------------------------


def _attach_redact_filter_to(logger: logging.Logger) -> logging.Filter:
    """Helper: attach the filter and return a handle to it."""
    before = set(map(id, logger.filters))
    configure_logging_redaction(logger)
    new_filters = [f for f in logger.filters if id(f) not in before]
    assert len(new_filters) == 1
    return new_filters[0]


def test_redact_filter_redacts_args_dict() -> None:
    """A LogRecord with dict-shaped ``args`` must redact each string value
    in place — this exercises the ``isinstance(record.args, dict)`` branch
    that the existing test_mcp_auth_sampling.py msg-only test misses.

    Note: Python's ``logger.makeRecord`` unwraps a single-tuple-of-dict
    into a bare dict in record.args automatically (the ``logging.debug
    ("%(k)s", {"k": v})`` convention). We construct the LogRecord
    directly so the filter sees a dict at ``record.args``.
    """
    flt = _attach_redact_filter_to(logging.getLogger("test-redact-args-dict"))
    rec = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="f",
        lineno=1,
        msg="header=%(auth)s value=%(count)d",
        args=None,
        exc_info=None,
    )
    rec.args = {"auth": "Bearer abcdef0123456789ZYXW", "count": 42}
    flt.filter(rec)
    assert isinstance(rec.args, dict)
    assert "REDACTED-TOKEN" in rec.args["auth"]
    # Non-string values pass through untouched.
    assert rec.args["count"] == 42


def test_redact_filter_redacts_args_tuple() -> None:
    """A LogRecord with tuple-shaped ``args`` must redact each string entry
    while leaving non-string entries untouched — the
    ``isinstance(record.args, tuple)`` branch.
    """
    logger = logging.getLogger("test-redact-args-tuple")
    flt = _attach_redact_filter_to(logger)
    rec = logger.makeRecord(
        "test",
        logging.INFO,
        "f",
        1,
        "%s and %d",
        ("Bearer abcdef0123456789ZYXW", 42),
        None,
    )
    flt.filter(rec)
    assert isinstance(rec.args, tuple)
    assert "REDACTED-TOKEN" in rec.args[0]
    assert rec.args[1] == 42


def test_redact_filter_swallows_exceptions_in_filter_body() -> None:
    """The filter body's broad ``try/except`` swallows mutator-raised errors
    so a filter exception never breaks logging emission. We use a record
    whose ``msg`` setter raises (simulating a pathological subclass) and
    confirm ``filter`` still returns ``True``.
    """
    logger = logging.getLogger("test-redact-tolerates-exceptions")
    flt = _attach_redact_filter_to(logger)

    class _BadRec:
        levelno = logging.INFO
        levelname = "INFO"
        # ``filter`` does ``isinstance(record.msg, str)`` first; we put a
        # string there, then sabotage ``record.args`` to a magic that
        # raises on iteration.
        msg = "ok %s"

        @property
        def args(self):
            raise RuntimeError("evil descriptor")

    bad = _BadRec()
    # MUST NOT raise; must still return True per filter contract.
    assert flt.filter(bad) is True  # type: ignore[arg-type]


def test_redact_in_logs_passes_through_non_string_unchanged() -> None:
    """Module-level helper :func:`_redact_in_logs` must accept a string and
    leave non-token text untouched. Edge case: empty string remains empty.
    """
    assert _redact_in_logs("") == ""
    assert _redact_in_logs("plain message") == "plain message"
    # A near-token-shaped match is still redacted (the regex anchors on
    # "bearer " or "access_token=" prefixes and the 16+ char body).
    redacted = _redact_in_logs("Authorization: Bearer xxxxxxxxxxxxxxxxYYY")
    assert "REDACTED-TOKEN" in redacted


# ---------------------------------------------------------------------------
# Cross-helper integration: full prelude + verifier round-trip (still pure-unit)
# ---------------------------------------------------------------------------


def test_prelude_and_verifier_round_trip_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: prelude builds the verifier, verifier introspects a
    mock-active token, returns an AccessToken. No real network, no
    real FastMCP boot.
    """
    pytest.importorskip("mcp.server.auth.settings")
    monkeypatch.setenv("MYCO_OAUTH_ISSUER_URL", "https://e2e-issuer.example")
    with patch(
        "myco.boundary.surface.mcp_auth.load_canon_governance",
        return_value={"token_redaction_required": False},
    ):
        kwargs, provider = prepare_fastmcp_oauth_prelude()
    assert provider is not None
    verifier = kwargs["token_verifier"]
    assert isinstance(verifier, MycoIntrospectionTokenVerifier)

    # Now drive the verifier's blocking-introspection path with a mock
    # urlopen so verify_token's run_in_executor branch returns a result
    # without leaving the test machine.
    payload = {"active": True, "client_id": "round-trip-client", "scope": "read"}
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read = MagicMock(return_value=json.dumps(payload).encode("utf-8"))
    with patch("urllib.request.urlopen", return_value=mock_resp):
        out = verifier._introspect_blocking("token-x")
    assert out == payload
