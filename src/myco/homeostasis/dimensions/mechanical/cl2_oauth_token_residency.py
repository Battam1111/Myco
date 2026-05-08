"""CL2 — OAuth token-residency policy enforcement (v0.6.0 R12 mitigation).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
(craft v0.6.0 §F12). When canon governance
``token_redaction_required: true``, mcp_auth.py MUST import the
``_redact_in_logs`` helper. CL2 refuses to start the streamable-http
OAuth-enabled server otherwise.

Severity: LOW at land, ramps to HIGH after 30 sessions.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["CL2OAuthTokenResidency"]


class CL2OAuthTokenResidency(Dimension):
    """mcp_auth.py imports _redact_in_logs when token_redaction_required."""

    id = "CL2"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        gov = (ctx.substrate.canon.system or {}).get("governance") or {}
        if not isinstance(gov, dict):
            return
        if not gov.get("token_redaction_required"):
            return
        auth_path = ctx.substrate.root / "src" / "myco" / "surface" / "mcp_auth.py"
        if not auth_path.is_file():
            # OAuth not yet shipped; CL2 only fires when
            # mcp_auth.py is present (v0.6.0+).
            return
        try:
            text = auth_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        if not re.search(r"\b_redact_in_logs\b", text):
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "canon.governance.token_redaction_required=true but "
                    "mcp_auth.py does not import _redact_in_logs; OAuth "
                    "tokens may leak to logs"
                ),
                path="src/myco/surface/mcp_auth.py",
            )
