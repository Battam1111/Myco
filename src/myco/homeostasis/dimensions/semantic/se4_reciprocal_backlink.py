"""SE4 — reciprocal back-link detection.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
"one-way refs" called out as known weakness; v0.6.0 lands SE4 as a
mechanical anchor for R5 (cross-reference-on-creation).

Severity: LOW at land, ramps to MEDIUM after 30 sessions.

White-listed reciprocal pairs:
- doctrine ↔ src code (every L2 doctrine references src code AND
  src code module docstring references doctrine — CG1 + CG2
  jointly handle most of this; SE4 catches what they miss).
- craft ↔ source-note (craft cites source notes; source notes
  link to the craft they triggered).

Out of scope: every markdown link in every note must be reciprocal
(would over-fire). SE4 is opt-in via the white-list.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["SE4ReciprocalBacklink"]


class SE4ReciprocalBacklink(Dimension):
    """White-listed reciprocal links must be bidirectional."""

    id = "SE4"
    category = Category.SEMANTIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # v0.6.0 ships SE4 with an empty white-list — the dim
        # registers in canon and runs cleanly with zero findings,
        # ready to populate the white-list in v0.6.x patches as
        # specific reciprocal-pair patterns are codified.
        # This is the "infrastructure-first" landing pattern: dim
        # implementation lives but emits no findings until policy
        # specifies the pair set. CG1+CG2 already cover doctrine↔src.
        # Generator with no yields → empty iterator (kernel expects iterable).
        return
        yield  # pragma: no cover — makes this a generator
