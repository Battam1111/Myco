"""M1 — canon identity fields present and non-empty.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``.

Checks that ``_canon.yaml::identity`` carries a non-empty
``substrate_id`` and ``entry_point``. The canon parser (Stage B.1)
requires ``identity`` to be present and non-empty as a mapping, but
does not force any particular key inside it. This dimension closes
that gap.

Severity: HIGH (a substrate that can't name itself or point at its
entry page is not usable by the agent surface).

v0.6.0 (§F18 craft): **fixable**. ``myco immune --fix`` derives
``substrate_id`` from the substrate root directory name and stamps
``entry_point`` to ``"MYCO.md"`` when missing. Idempotent narrow
write to ``_canon.yaml`` only.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.io_atomic import atomic_utf8_write
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["M1CanonIdentityFields"]


def _slugify(value: str) -> str:
    """Lowercase + non-alphanum to dash; trim dashes."""
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return s or "unnamed"


class M1CanonIdentityFields(Dimension):
    """``identity.substrate_id`` and ``identity.entry_point`` non-empty."""

    id = "M1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        identity = ctx.substrate.canon.identity
        for key in ("substrate_id", "entry_point"):
            val = identity.get(key)
            if val is None or str(val).strip() == "":
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=f"canon.identity.{key} is missing or empty",
                    path="_canon.yaml",
                )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Stamp missing identity fields with sane defaults.

        Narrow line-level patch (M2-style template):
        - substrate_id: derive slug from substrate root name.
        - entry_point: 'MYCO.md'.

        Idempotent: if both keys are already non-empty, no-op.
        """
        canon_path = ctx.substrate.root / "_canon.yaml"
        if not canon_path.is_file():
            return {"applied": False, "detail": "canon file missing"}
        text = canon_path.read_text(encoding="utf-8")
        identity = ctx.substrate.canon.identity
        sub_id = identity.get("substrate_id") or _slugify(ctx.substrate.root.name)
        entry = identity.get("entry_point") or "MYCO.md"
        applied = False
        # Insert/replace lines under identity: section.
        lines = text.splitlines(keepends=True)
        in_identity = False
        seen_sub_id = False
        for i, line in enumerate(lines):
            stripped = line.rstrip("\n")
            if re.match(r"^identity:\s*$", stripped):
                in_identity = True
                continue
            if in_identity:
                if re.match(r"^[a-zA-Z]", stripped):  # next top-level
                    in_identity = False
                    continue
                if re.match(r"^\s+substrate_id:", stripped):
                    seen_sub_id = True
                    if "substrate_id" not in identity or not identity.get(
                        "substrate_id"
                    ):
                        lines[i] = f'  substrate_id: "{sub_id}"\n'
                        applied = True
                if re.match(r"^\s+entry_point:", stripped) and (
                    "entry_point" not in identity or not identity.get("entry_point")
                ):
                    lines[i] = f'  entry_point: "{entry}"\n'
                    applied = True
        if not seen_sub_id:
            return {
                "applied": False,
                "detail": "identity stanza missing keys; manual edit required",
            }
        if not applied:
            return {"applied": False, "detail": "M1 already satisfied"}
        atomic_utf8_write(canon_path, "".join(lines))
        return {
            "applied": True,
            "detail": f"stamped substrate_id={sub_id!r} / entry_point={entry!r}",
        }
