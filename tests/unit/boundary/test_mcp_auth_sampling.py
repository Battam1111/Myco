"""Coverage tests for ``boundary.surface.mcp_auth`` + ``mcp_sampling``."""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace

import pytest

from myco.boundary.surface.mcp_auth import (
    MycoOAuthProvider,
    _clear_token_after_call,
    _redact_in_logs,
    configure_logging_redaction,
    ensure_pkce_method,
    validate_aud_claim,
)
from myco.boundary.surface.mcp_sampling import (
    request_sampling_completion,
    should_advertise_sampling,
)


# ---------- mcp_auth ----------


def test_oauth_provider_dataclass_construction():
    p = MycoOAuthProvider(
        issuer_url="https://issuer.example",
        audience="myco",
        jwks_url="https://issuer.example/jwks",
    )
    assert p.refresh_token_rotation_grace_seconds == 30
    assert p.pkce_required_method == "S256"
    assert p.token_redaction_required is True


def test_redact_in_logs_replaces_bearer():
    msg = "Authorization: Bearer abcdef0123456789ZYXW"
    out = _redact_in_logs(msg)
    assert "REDACTED-TOKEN" in out
    assert "abcdef0123456789" not in out


def test_redact_in_logs_replaces_access_token_kv():
    msg = 'access_token="abcdef0123456789ZYXW"'
    out = _redact_in_logs(msg)
    assert "REDACTED-TOKEN" in out


def test_redact_in_logs_passthrough_when_no_secret():
    out = _redact_in_logs("nothing sensitive here")
    assert out == "nothing sensitive here"


def test_clear_token_after_call_none():
    # Must not raise.
    _clear_token_after_call(None)


def test_clear_token_after_call_dict():
    holder = {
        "access_token": "abc",
        "refresh_token": "def",
        "user_name": "alice",
    }
    _clear_token_after_call(holder)
    assert holder["access_token"] is None
    assert holder["refresh_token"] is None
    # Non-sensitive key untouched.
    assert holder["user_name"] == "alice"


def test_clear_token_after_call_object_attrs():
    holder = SimpleNamespace(access_token="abc", session_id="s1", refresh_token="def")
    _clear_token_after_call(holder)
    assert holder.access_token is None
    assert holder.refresh_token is None
    assert holder.session_id == "s1"


def test_clear_token_after_call_swallows_setattr_failures():
    class Frozen:
        __slots__ = ("access_token",)

        def __init__(self) -> None:
            self.access_token = "abc"

    f = Frozen()
    # No raise even if attribute was read-only — best effort.
    _clear_token_after_call(f)


def test_validate_aud_claim_string_match():
    assert validate_aud_claim({"aud": "myco"}, "myco") is True
    assert validate_aud_claim({"aud": "other"}, "myco") is False


def test_validate_aud_claim_list_match():
    assert validate_aud_claim({"aud": ["a", "myco"]}, "myco") is True
    assert validate_aud_claim({"aud": ["x"]}, "myco") is False


def test_validate_aud_claim_missing_or_wrong_type():
    assert validate_aud_claim({}, "myco") is False
    assert validate_aud_claim({"aud": 42}, "myco") is False


def test_ensure_pkce_method_default_s256():
    assert ensure_pkce_method("S256") is True
    assert ensure_pkce_method("s256") is True
    assert ensure_pkce_method("plain") is False
    assert ensure_pkce_method(None) is False


def test_configure_logging_redaction_attaches_filter():
    logger = logging.getLogger("test-myco-redact")
    before = len(logger.filters)
    configure_logging_redaction(logger)
    assert len(logger.filters) == before + 1
    # The filter should redact when a record passes through.
    rec = logger.makeRecord(
        "test", logging.INFO, "f", 1, "Bearer abcdef0123456789ZZZZ", None, None
    )
    for f in logger.filters:
        f.filter(rec)
    assert "REDACTED-TOKEN" in str(rec.msg)


# ---------- mcp_sampling ----------


def test_should_advertise_sampling_forbidden_returns_false():
    assert should_advertise_sampling({"llm_policy": "forbidden"}) is False


def test_should_advertise_sampling_default_is_forbidden():
    # No llm_policy key → conservative default forbidden.
    assert should_advertise_sampling({}) is False


def test_should_advertise_sampling_opt_in_true():
    assert should_advertise_sampling({"llm_policy": "opt-in"}) is True


def test_should_advertise_sampling_providers_declared_true():
    assert should_advertise_sampling({"llm_policy": "providers-declared"}) is True


def test_request_sampling_forbidden_raises():
    async def _go() -> None:
        await request_sampling_completion(
            mcp_ctx=SimpleNamespace(),
            prompt="hi",
            canon_system={"llm_policy": "forbidden"},
        )

    with pytest.raises(RuntimeError, match="CL1"):
        asyncio.run(_go())


def test_request_sampling_no_session_returns_empty():
    """If mcp_ctx.session is missing (AttributeError), graceful empty."""

    async def _go() -> str:
        return await request_sampling_completion(
            mcp_ctx=SimpleNamespace(),  # no .session
            prompt="hi",
            canon_system={"llm_policy": "opt-in"},
        )

    out = asyncio.run(_go())
    assert out == ""


def test_request_sampling_dict_text_response():
    """Standard MCP response shape: {"content": {"type":"text","text":"..."}}"""

    class FakeSession:
        async def create_message(self, **kwargs):
            return {"content": {"type": "text", "text": "hello world"}}

    async def _go() -> str:
        return await request_sampling_completion(
            mcp_ctx=SimpleNamespace(session=FakeSession()),
            prompt="hi",
            canon_system={"llm_policy": "opt-in"},
        )

    out = asyncio.run(_go())
    assert out == "hello world"


def test_request_sampling_string_content_response():
    """Some hosts return string-form content."""

    class FakeSession:
        async def create_message(self, **kwargs):
            return {"content": "string-form"}

    async def _go() -> str:
        return await request_sampling_completion(
            mcp_ctx=SimpleNamespace(session=FakeSession()),
            prompt="hi",
            canon_system={"llm_policy": "opt-in"},
        )

    out = asyncio.run(_go())
    assert out == "string-form"


def test_request_sampling_exception_returns_empty():
    """Exceptions during create_message → empty fallback."""

    class FakeSession:
        async def create_message(self, **kwargs):
            raise RuntimeError("network fail")

    async def _go() -> str:
        return await request_sampling_completion(
            mcp_ctx=SimpleNamespace(session=FakeSession()),
            prompt="hi",
            canon_system={"llm_policy": "opt-in"},
        )

    out = asyncio.run(_go())
    assert out == ""


def test_request_sampling_unknown_response_shape_returns_empty():
    """Unrecognized result shape → empty string fallback."""

    class FakeSession:
        async def create_message(self, **kwargs):
            return ["unexpected", "shape"]

    async def _go() -> str:
        return await request_sampling_completion(
            mcp_ctx=SimpleNamespace(session=FakeSession()),
            prompt="hi",
            canon_system={"llm_policy": "opt-in"},
        )

    out = asyncio.run(_go())
    assert out == ""
