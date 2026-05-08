"""MF4 — overlay_verb subsystem validity (v0.6.0 R21 mitigation).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
(craft v0.6.0 §F21). Substrate-local plugin manifest_overlay.yaml
may declare overlay_verb entries; each must reference a subsystem
that exists in canon.subsystems.

Severity: LOW at land, ramps to MEDIUM after 30 sessions.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

import yaml

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MF4OverlaySubsystemValidity"]


class MF4OverlaySubsystemValidity(Dimension):
    """Each overlay_verb's subsystem must exist in canon.subsystems."""

    id = "MF4"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        overlay_path = ctx.substrate.root / ".myco" / "manifest_overlay.yaml"
        if not overlay_path.is_file():
            return
        try:
            data = yaml.safe_load(overlay_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return
        if not isinstance(data, dict):
            return
        commands = data.get("commands") or []
        if not isinstance(commands, list):
            return
        valid_subsystems = set((ctx.substrate.canon.subsystems or {}).keys())
        for cmd in commands:
            if not isinstance(cmd, dict):
                continue
            subsys = cmd.get("subsystem")
            if not subsys:
                continue
            if subsys not in valid_subsystems:
                name = cmd.get("name") or "<unknown>"
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"overlay_verb {name!r} declares subsystem "
                        f"{subsys!r} not in canon.subsystems "
                        f"(known: {sorted(valid_subsystems)})"
                    ),
                    path=".myco/manifest_overlay.yaml",
                )
