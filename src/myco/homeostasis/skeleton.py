"""Skeleton-mode downgrade.

Per ``docs/architecture/L1_CONTRACT/exit_codes.md``: when the substrate
is an auto-seeded skeleton (canon-declared marker present), selected
lint dimensions have their CRITICAL findings capped at HIGH so that a
first-run hunger call does not block legitimate adoption.

The set of affected dimensions is canon-driven
(``lint.skeleton_downgrade.affected_dimensions``), never hard-coded.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from myco.core.context import MycoContext
from myco.core.severity import Severity

from .finding import Finding

__all__ = ["apply_skeleton_downgrade"]


def apply_skeleton_downgrade(
    findings: Iterable[Finding],
    *,
    ctx: MycoContext,
) -> tuple[Finding, ...]:
    """Cap CRITICAL→HIGH for canon-declared dimensions when skeleton mode is active.

    No-op when the substrate is not in skeleton mode (no
    ``.myco_state/autoseeded.txt`` marker) or when the canon's
    ``lint.skeleton_downgrade.affected_dimensions`` list is empty.
    """
    findings_t = tuple(findings)
    if not ctx.substrate.is_skeleton:
        return findings_t

    lint = ctx.substrate.canon.lint or {}
    sd = lint.get("skeleton_downgrade") or {}
    affected = set(sd.get("affected_dimensions") or ())
    if not affected:
        return findings_t

    out: list[Finding] = []
    for f in findings_t:
        if f.dimension_id in affected and f.severity == Severity.CRITICAL:
            out.append(replace(f, severity=Severity.HIGH))
        else:
            out.append(f)
    return tuple(out)
