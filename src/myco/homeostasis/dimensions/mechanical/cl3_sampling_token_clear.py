"""CL3 — sampling token clear-after-call (v0.6.0 R19 mitigation).

Governing doctrine: per craft v0.6.0 §F19, when llm_policy is "opt-in",
mcp_sampling.py MUST call _clear_token_after_call() so MCP token does
not remain in substrate process memory beyond the sampling round-trip.

Severity: LOW at land, ramps to MEDIUM after 30 sessions.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["CL3SamplingTokenClear"]


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
            ctx.substrate.root / "src" / "myco" / "surface" / "mcp_sampling.py"
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
                path="src/myco/surface/mcp_sampling.py",
            )
