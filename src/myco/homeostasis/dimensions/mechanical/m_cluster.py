"""M-cluster — canon-identity invariants (M1 + M2 + M3).

v0.8.8 merged: this file consolidates the 3 single-class M-prefix
dimension files that previously lived as
``m1_canon_identity_fields.py``, ``m2_entry_point_exists.py``, and
``m3_write_surface_declared.py``. The class names and behaviour are
byte-equivalent — only the file location changed. Per the
"L3 organization choice, not contract" reading of L1 protocol.md
"L3 changes within an existing L2 doctrine are ordinary code
changes and do not require a contract bump".

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration". Original per-dim files preserved in git
history at parent commits.

- **M1** (HIGH, fixable): canon ``identity.substrate_id`` and
  ``identity.entry_point`` non-empty.
- **M2** (HIGH, fixable): the canon-declared entry-point file
  exists on disk.
- **M3** (MEDIUM, fixable=advisory): ``system.write_surface.allowed``
  is a non-empty list.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import timezone
from string import Template
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.io_atomic import atomic_utf8_write
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = [
    "M1CanonIdentityFields",
    "M2EntryPointExists",
    "M3WriteSurfaceDeclared",
]


# =========================================================================
# M1 — canon identity fields present and non-empty
# =========================================================================


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
        # v0.8.6 — canon may live at `.myco/canon.yaml` (Myco-self
        # post-v0.8.4) or default `_canon.yaml` (downstream). The
        # finding's `path` field tracks the live location so agents
        # can navigate to the actual source of truth.
        canon_rel = ctx.substrate.paths.canon.relative_to(
            ctx.substrate.root.resolve()
        ).as_posix()
        for key in ("substrate_id", "entry_point"):
            val = identity.get(key)
            if val is None or str(val).strip() == "":
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=f"canon.identity.{key} is missing or empty",
                    path=canon_rel,
                )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Stamp missing identity fields with sane defaults.

        Narrow line-level patch (M2-style template):
        - substrate_id: derive slug from substrate root name.
        - entry_point: 'MYCO.md'.

        Idempotent: if both keys are already non-empty, no-op.

        v0.8.6 — writes to the canon-configured path (Myco-self
        `.myco/canon.yaml`, downstream `_canon.yaml`) via
        `ctx.substrate.paths.canon`, not the legacy hardcoded
        `root / "_canon.yaml"` (which would silently miss on any
        substrate that relocates its canon under a hidden prefix).
        """
        canon_path = ctx.substrate.paths.canon
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


# =========================================================================
# M2 — the canon-declared entry-point file exists on disk
# =========================================================================


_ENTRY_POINT_TEMPLATE = Template(
    "# $substrate_id — Myco substrate\n"
    "\n"
    "This is the agent entry point for the `$substrate_id` substrate.\n"
    "See `_canon.yaml` for contract, `docs/architecture/` for doctrine,\n"
    "`docs/primordia/` for craft history.\n"
    "\n"
    "Generated by `myco immune --fix` on $generated_at.\n"
)


class M2EntryPointExists(Dimension):
    """Canon entry-point file must exist under the substrate root."""

    id = "M2"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH

    #: v0.5.5 — M2 autonomously creates the missing entry-point file
    #: from a minimal skeleton template. See :meth:`fix`.
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        entry = ctx.substrate.canon.entry_point  # defaults to "MYCO.md"
        if not entry:
            return
        path = ctx.substrate.root / entry
        if not path.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"entry point {entry!r} declared in canon "
                    f"but no file found at that path"
                ),
                path=entry,
            )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Create the missing entry-point file from a skeleton template.

        Idempotent + narrow contract (v0.5.5):

        - If the target file already exists and is non-empty, the fix
          is a silent no-op (``applied=False``, descriptive detail).
        - Creates parent directories if they don't exist (the entry
          point usually sits at substrate root, but a canon that
          points it at a subdirectory is legal).
        - Writes atomically via a single ``write_text`` — the file is
          too small to need temp-file-plus-rename semantics.
        - Never touches anything else.

        The write-surface guard in
        :func:`myco.homeostasis.kernel._apply_fix` has already run by
        the time we get here, so the target is known-safe.
        """
        entry = ctx.substrate.canon.entry_point
        if not entry:
            return {
                "applied": False,
                "detail": "canon declares no entry_point; nothing to fix",
            }

        target = ctx.substrate.root / entry
        if target.is_file() and target.stat().st_size > 0:
            # Idempotent: a second --fix pass sees the file we wrote
            # last time (or one the user populated themselves) and
            # refuses to overwrite it.
            return {
                "applied": False,
                "detail": f"entry point {entry!r} already exists; not overwriting",
            }

        substrate_id = ctx.substrate.canon.substrate_id or "unnamed"
        generated_at = ctx.now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = _ENTRY_POINT_TEMPLATE.substitute(
            substrate_id=substrate_id,
            generated_at=generated_at,
        )

        atomic_utf8_write(target, body)
        return {
            "applied": True,
            "detail": f"created entry point {entry!r} ({len(body)} bytes)",
        }


# =========================================================================
# M3 — system.write_surface.allowed is a non-empty list
# =========================================================================


class M3WriteSurfaceDeclared(Dimension):
    """``system.write_surface.allowed`` must be a non-empty list."""

    id = "M3"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = True

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """v0.6.0 §F18 narrow fix: detect missing write_surface but defer
        write to operator; canon-shape-edits are too high-stakes for
        autofix to silently rewrite (per safety four-rule §homeostasis.md
        narrow). The fix surfaces a structured advisory.
        """
        return {
            "applied": False,
            "detail": (
                "M3 fixable=True at v0.6.0 is advisory: write_surface is "
                "high-stakes; manual edit required. See canon_schema.md "
                "for the canonical default list."
            ),
        }

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        system = ctx.substrate.canon.system or {}
        ws = system.get("write_surface")
        if not isinstance(ws, dict):
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message="canon.system.write_surface is missing or not a mapping",
                path="_canon.yaml",
            )
            return
        allowed = ws.get("allowed")
        if not isinstance(allowed, list) or len(allowed) == 0:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "canon.system.write_surface.allowed is empty or not a list; "
                    "declare at least one permitted path pattern"
                ),
                path="_canon.yaml",
            )
