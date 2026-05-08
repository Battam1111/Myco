"""MB7 — MCP resource_watch quota pressure (v0.6.0 R11 mitigation).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
(craft v0.6.0 §F11). Multi-tenant streamable-http deployments can
exhaust inotify/fd watch handles. ``canon.system.resource_watch.
max_per_substrate`` caps watches; MB7 emits when ≥80% of quota is
consumed for a sustained period.

Severity: LOW at land, ramps to MEDIUM after 30 sessions.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MB7ResourceWatchQuota"]


class MB7ResourceWatchQuota(Dimension):
    """resource_watch quota pressure (≥80% consumed)."""

    id = "MB7"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        rwatch = (ctx.substrate.canon.system or {}).get("resource_watch") or {}
        if not isinstance(rwatch, dict):
            return
        max_watches = int(rwatch.get("max_per_substrate", 100))
        # Read current watch count from metric file written by
        # mcp_resources subscription manager (v0.6.0+).
        metric_path = ctx.substrate.root / ".myco_state" / "resource_watch_count.json"
        if not metric_path.is_file():
            return
        try:
            data = json.loads(metric_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        active = int(data.get("active", 0))
        if max_watches > 0 and active / max_watches >= 0.80:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"resource_watch quota pressure: {active}/{max_watches} "
                    f"({100 * active / max_watches:.0f}%) consumed; "
                    f"increase canon.system.resource_watch.max_per_substrate "
                    f"or unsubscribe stale watches"
                ),
                path="_canon.yaml",
            )
