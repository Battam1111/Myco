"""Cross-cutting meta-verbs that compose multiple subsystems.

Currently holds ``session_end_run`` — the handler for ``myco
session-end``, which orchestrates ``reflect`` followed by ``immune
--fix``. Kept outside ``surface/`` so that package stays pure
adaptation per L3 package_map invariant 4.
"""

from __future__ import annotations

from typing import Mapping

from myco.core.context import MycoContext, Result
from myco.digestion.reflect import reflect
from myco.homeostasis.kernel import run_immune
from myco.homeostasis.registry import default_registry

__all__ = ["session_end_run"]


def session_end_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Run reflect + immune(fix=True) and merge results.

    Exit code is the worse (higher) of the two sub-results' exit codes.
    Payload bundles both summaries under ``reflect`` and ``immune``.
    """
    del args  # no args at B.7

    reflect_summary = reflect(ctx=ctx)
    immune_result = run_immune(
        ctx,
        default_registry(),
        selected=None,
        exit_on="critical",
        fix=True,
    )

    reflect_exit = 1 if reflect_summary["errors"] and reflect_summary["promoted"] == 0 else 0
    combined_exit = max(reflect_exit, immune_result.exit_code)

    return Result(
        exit_code=combined_exit,
        findings=immune_result.findings,
        payload={
            "reflect": {
                "promoted": reflect_summary["promoted"],
                "errors": reflect_summary["errors"],
                "outcomes": reflect_summary["outcomes"],
            },
            "immune": dict(immune_result.payload),
        },
    )
