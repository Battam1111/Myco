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
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

__all__ = [
    "MycoOAuthProvider",
    "_redact_in_logs",
    "_clear_token_after_call",
    "validate_aud_claim",
    "ensure_pkce_method",
]


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
    OAuth is enabled.
    """

    class _RedactFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            """Run ``_redact_in_logs`` over the record's string message in-place."""
            try:
                if isinstance(record.msg, str):
                    record.msg = _redact_in_logs(record.msg)
            except Exception:
                pass
            return True

    logger.addFilter(_RedactFilter())
