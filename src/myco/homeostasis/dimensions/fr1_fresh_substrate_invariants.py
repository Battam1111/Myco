"""FR1 — fresh-substrate directory invariants.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


A healthy substrate has, at minimum:

- ``_canon.yaml`` at the root,
- the file declared in ``canon.identity.entry_point`` (usually ``MYCO.md``),
- ``notes/raw/`` + ``notes/integrated/`` as directories,
- ``docs/`` as a directory.

``myco germinate`` creates all of these on a fresh substrate; FR1
detects the case where a post-germination substrate has lost one
(user deleted it, a rogue write-surface wipe, a botched merge).

Severity: HIGH per missing root-level anchor (``_canon.yaml`` and
the entry point are contract surfaces), MEDIUM for missing
sub-directories (notes/raw/, notes/integrated/, docs/).

Fixable: False. Creating an empty directory is cheap, but
``myco immune --fix`` on FR1 risks papering over a real data loss
(if a user wiped ``notes/integrated/`` by mistake, FR1 recreating
an empty one would suppress the real finding). Repair is operator
work — typically ``mkdir`` or ``git restore``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["FR1FreshSubstrateInvariants"]


class FR1FreshSubstrateInvariants(Dimension):
    """Fresh-substrate directory invariants are satisfied post-germination."""

    id = "FR1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        canon = ctx.substrate.canon

        # 1) _canon.yaml
        canon_path = ctx.substrate.paths.canon
        if not canon_path.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=f"_canon.yaml missing at {root}",
                path="_canon.yaml",
            )

        # 2) entry point
        entry_name = canon.entry_point
        entry_path = root / entry_name
        if not entry_path.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=(
                    f"canon.identity.entry_point {entry_name!r} does "
                    f"not exist at substrate root"
                ),
                path=entry_name,
            )

        # 3) notes/raw, notes/integrated, docs — MEDIUM each
        for rel in ("notes/raw", "notes/integrated", "docs"):
            p = root / rel
            if not p.is_dir():
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=Severity.MEDIUM,
                    message=(
                        f"{rel}/ directory missing — fresh substrates "
                        f"carry this directory; a missing one means "
                        f"either pre-v0.5 substrate layout or a user "
                        f"wipe. Restore (``git restore``) or mkdir."
                    ),
                    path=rel,
                )
