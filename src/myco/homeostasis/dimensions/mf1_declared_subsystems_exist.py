"""MF1 — declared subsystems exist on disk.

Every entry in ``_canon.yaml::subsystems`` declares two strings:

- ``doc``  — path to the L2 doctrine file governing this subsystem.
- ``package`` — filesystem path to the implementation directory.

MF1 walks the subsystems mapping and verifies that each ``package``
resolves to an existing directory under the substrate root. A missing
package directory means the canon is lying about what the substrate
contains — either the package was renamed/removed without a contract
bump (drift), or the canon was edited to declare a subsystem that
hasn't been scaffolded yet.

This dimension lands in v0.5 (MAJOR 7) as the first non-test
enforcement of the canon's subsystems block. Before v0.5, the
subsystems block was required to exist but its contents were never
cross-checked against the filesystem; now the canon and the package
layout are kept honest.

Severity: HIGH. Missing a declared subsystem breaks L3 package_map
invariant "every L2 doctrine has a matching code package" (see
``docs/architecture/L3_IMPLEMENTATION/package_map.md``).

No-op for substrates whose ``subsystems`` block does not declare
``package`` fields (e.g. a canon that uses ``subsystems`` purely for
documentation tagging). The absence check is field-scoped.
"""

from __future__ import annotations

from typing import Iterable

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["MF1DeclaredSubsystemsExist"]


class MF1DeclaredSubsystemsExist(Dimension):
    """Every ``subsystems.<name>.package`` path exists under substrate root."""

    id = "MF1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        subsystems = ctx.substrate.canon.subsystems or {}
        for name, spec in subsystems.items():
            if not isinstance(spec, dict):
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"canon.subsystems.{name} must be a mapping, "
                        f"got {type(spec).__name__}"
                    ),
                    path="_canon.yaml",
                )
                continue
            pkg = spec.get("package")
            if pkg is None:
                # Optional field. If absent the canon is using
                # subsystems for pure documentation tagging — no
                # filesystem claim to check.
                continue
            pkg_path = root / str(pkg)
            if not pkg_path.is_dir():
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"canon.subsystems.{name}.package does not "
                        f"resolve to a directory: {pkg}"
                    ),
                    path="_canon.yaml",
                )
