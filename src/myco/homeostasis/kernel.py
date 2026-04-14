"""Immune-kernel orchestrator.

One entry point — :func:`run_immune` — that a future ``myco immune``
handler (Stage B.7) invokes with a single call.

Design choices (per Stage B.2 craft Round 2.5):

- Per-dimension exceptions propagate. A crashing dimension is a bug,
  not a finding. B.8 may opt-in to exception handling if a need
  emerges.
- ``fix=True`` is plumbed through but does nothing at Stage B.2. The
  first fixable dimension lands in B.8.
- Unknown selected dimension ids surface as :class:`UsageError` with a
  clean message (exit 3).
"""

from __future__ import annotations

from typing import Sequence

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

from .exit_policy import parse_exit_policy
from .finding import Finding
from .registry import DimensionRegistry
from .skeleton import apply_skeleton_downgrade

__all__ = ["run_immune"]


def run_immune(
    ctx: MycoContext,
    registry: DimensionRegistry,
    *,
    selected: Sequence[str] | None = None,
    exit_on: str = "critical",
    fix: bool = False,
) -> Result:
    """Run the immune kernel over ``ctx.substrate``.

    ``selected`` — if given, run only these dimension ids.
    ``exit_on`` — ``--exit-on`` spec string.
    ``fix``     — plumbed but no-op at Stage B.2.
    """
    if selected is not None:
        dims = []
        for dim_id in selected:
            if not registry.has(dim_id):
                raise UsageError(f"unknown dimension: {dim_id!r}")
            dims.append(registry.get(dim_id))
    else:
        dims = list(registry.all())

    findings: list[Finding] = []
    for dim in dims:
        findings.extend(dim.run(ctx))

    findings_t = apply_skeleton_downgrade(findings, ctx=ctx)

    policy = parse_exit_policy(exit_on)
    exit_code = policy.compute(findings_t)

    return Result(
        exit_code=exit_code,
        findings=findings_t,
        payload={
            "dimensions_run": tuple(d.id for d in dims),
            "skeleton_downgrade_applied": ctx.substrate.is_skeleton,
            "exit_on": exit_on,
            "fix": fix,  # echo back; no effect at B.2
        },
    )
