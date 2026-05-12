"""CL-cluster — merged dimensions (CL1, CL2, CL3).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/mechanical/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "CL1SamplingPolicyGate",
    "CL2OAuthTokenResidency",
    "CL3SamplingTokenClear",
]


# =========================================================================
# CL1 — see module docstring + original git history at parent commits
# =========================================================================

_POLICY_GUARD_RE: re.Pattern[str] = re.compile(
    r"llm_policy\s*[!=]=?\s*['\"](forbidden|opt-in|providers-declared)['\"]"
)


class CL1SamplingPolicyGate(Dimension):
    """mcp_sampling.py must check llm_policy before enabling sampling."""

    id = "CL1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        sampling_path = (
            ctx.substrate.root
            / "src"
            / "myco"
            / "boundary"
            / "surface"
            / "mcp_sampling.py"
        )
        if not sampling_path.is_file():
            # Module not yet shipped (v0.6.0 lands it; downstream
            # substrates may not).
            return
        try:
            text = sampling_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        if not _POLICY_GUARD_RE.search(text):
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "mcp_sampling.py does not check canon.system.llm_policy "
                    "before enabling sampling capability (L0 P1 example #2)"
                ),
                path="src/myco/boundary/surface/mcp_sampling.py",
            )


# =========================================================================
# CL2 — see module docstring + original git history at parent commits
# =========================================================================


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
        # v0.8.6 — corrected path: mcp_auth.py moved under boundary/
        # at v0.6.0. Prior path "src/myco/surface/mcp_auth.py" was
        # never updated, so CL2 silently returned (file-not-found)
        # for every release v0.6.0…v0.8.5 — token-redaction
        # enforcement was a permanent no-op until this fix.
        auth_path = (
            ctx.substrate.root / "src" / "myco" / "boundary" / "surface" / "mcp_auth.py"
        )
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
                path="src/myco/boundary/surface/mcp_auth.py",
            )


# =========================================================================
# CL3 — see module docstring + original git history at parent commits
# =========================================================================


class CL3SamplingTokenClear(Dimension):
    """mcp_sampling.py calls _clear_token_after_call when llm_policy=opt-in."""

    id = "CL3"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        system = ctx.substrate.canon.system or {}
        if not isinstance(system, dict):
            return
        if system.get("llm_policy") != "opt-in":
            return
        sampling_path = (
            ctx.substrate.root
            / "src"
            / "myco"
            / "boundary"
            / "surface"
            / "mcp_sampling.py"
        )
        if not sampling_path.is_file():
            return
        try:
            text = sampling_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        if not re.search(r"\b_clear_token_after_call\b", text):
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "llm_policy=opt-in but mcp_sampling.py does not call "
                    "_clear_token_after_call(); MCP token may stay "
                    "resident in substrate memory between calls"
                ),
                path="src/myco/boundary/surface/mcp_sampling.py",
            )
