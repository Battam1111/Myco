"""PA2 — no megafile in src/myco/ exceeds the LoC cap.

Governing doctrine: ``docs/architecture/L3_IMPLEMENTATION/package_map.md``
invariant 5 ("no megafile >800 LoC"). v0.6.0 mechanical anchor for that
invariant per craft ``v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md`` §F5.

Severity: LOW at land, ramps to MEDIUM after 30 sessions of green
observation per ``_canon.yaml::lint.severity_promotion``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["PA2MegafileLocCap"]

_LOC_CAP: int = 800


class PA2MegafileLocCap(Dimension):
    """No `.py` file in `src/myco/` may exceed the LoC cap (default 800)."""

    id = "PA2"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        src_root = ctx.substrate.root / "src" / "myco"
        if not src_root.is_dir():
            return
        for path in src_root.rglob("*.py"):
            if any(should_skip_dir(p.name) for p in path.parents):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            if len(lines) > _LOC_CAP:
                rel = path.relative_to(ctx.substrate.root).as_posix()
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"megafile: {len(lines)} LoC > {_LOC_CAP} cap "
                        f"(invariant 5 in package_map.md)"
                    ),
                    path=rel,
                )
