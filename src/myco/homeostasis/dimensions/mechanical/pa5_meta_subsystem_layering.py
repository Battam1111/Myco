"""PA5 — meta-subsystem layering: subsystems may not import meta packages.

Governing doctrine: ``docs/architecture/L3_IMPLEMENTATION/package_map.md``
v0.6.0 invariant 7-8 (added with cycle promoted to subsystem; meta
packages remain cross-cutting adapters at surface/install/mcp).

Severity: LOW at land, ramps to MEDIUM after 30 sessions.

Subsystems (germination/ingestion/digestion/circulation/homeostasis)
must not import surface/, install/, or mcp/. Cycle is itself a
subsystem since v0.6.0 but is excepted because it legitimately
authors transitions across all other subsystems.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["PA5MetaSubsystemLayering"]

_FORBIDDEN_META: tuple[str, ...] = (
    "myco.boundary.surface",
    "myco.boundary.install",
    "myco.boundary.mcp",
    "myco.boundary",
)

#: Per-subsystem allowlist of cross-layer imports legitimized by doctrine.
#: ``manifest`` is the canonical contract surface (SSoT for verb declarations
#: and overlay merging) — subsystems read it as data, not as a meta-adapter,
#: so the import does not violate the layering invariant per L2 doctrine
#: ``boundary.md`` § "Manifest as contract surface" (v0.6.0 craft §F19).
#: Without this allowlist, PA5 would flag legitimate manifest reads in
#: ``ingestion/hunger`` (local plugins summary) and ``homeostasis/MF2``
#: (overlay-verb subsystem validity check).
_ALLOWED_META_IMPORTS: frozenset[str] = frozenset(
    {
        "myco.boundary.surface.manifest",
    }
)

_SUBSYSTEM_ROOTS: tuple[str, ...] = (
    "germination",
    "ingestion",
    "digestion",
    "circulation",
    "homeostasis",
    # cycle is excepted: it composes transitions across subsystems.
)


class PA5MetaSubsystemLayering(Dimension):
    """Subsystems may not depend on meta-subsystem (surface/install/mcp/symbionts)."""

    id = "PA5"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        for subsys in _SUBSYSTEM_ROOTS:
            sub_root = ctx.substrate.root / "src" / "myco" / subsys
            if not sub_root.is_dir():
                continue
            for path in sub_root.rglob("*.py"):
                rel = path.relative_to(ctx.substrate.root).as_posix()
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, SyntaxError):
                    continue
                for node in ast.walk(tree):
                    module: str | None = None
                    if isinstance(node, ast.ImportFrom):
                        module = node.module
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            module = alias.name
                            break
                    if not module:
                        continue
                    # v0.6.0: doctrine-allowlisted meta imports (manifest as
                    # contract surface) are exempt — see _ALLOWED_META_IMPORTS.
                    if module in _ALLOWED_META_IMPORTS:
                        continue
                    if any(module.startswith(p) for p in _FORBIDDEN_META):
                        yield Finding(
                            dimension_id=self.id,
                            category=self.category,
                            severity=self.default_severity,
                            message=(
                                f"subsystem {subsys!r} imports meta-subsystem "
                                f"package {module!r}; meta packages are "
                                f"cross-cutting adapters and must not be "
                                f"depended upon by subsystems"
                            ),
                            path=rel,
                        )
