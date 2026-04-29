"""CL1 — MCP sampling capability gated on llm_policy.

Governing doctrine: ``docs/architecture/L0_VISION.md`` P1 exception #2
("agent calls the LLM, the substrate does not"); v0.6.0 craft §F19
adds ``canon.system.llm_policy`` enum and CL1 dim.

When ``llm_policy: "forbidden"`` (default), MCP sampling capability
must NOT be advertised by the server — verify by checking the
mcp_sampling.py module is gated behind the enum check.

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

__all__ = ["CL1SamplingPolicyGate"]

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
