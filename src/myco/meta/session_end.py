"""session-end verb: reflect + immune(fix=True) composer.

Extracted from the v0.4 ``myco/meta.py`` single-file module into its
own submodule at v0.5. Behaviour unchanged; only the module path and
the function name (``session_end_run`` → ``run`` to match the verb-
handler convention).
"""

from __future__ import annotations

from typing import Mapping

from myco.core.context import MycoContext, Result
from myco.digestion.reflect import reflect
from myco.homeostasis.kernel import run_immune
from myco.homeostasis.registry import default_registry

__all__ = ["run"]


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Run reflect + immune(fix=True) and merge results.

    Exit code is the worse (higher) of the two sub-results' exit
    codes. Payload bundles both summaries under ``reflect`` and
    ``immune``.
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

    reflect_exit = (
        1
        if reflect_summary["errors"] and reflect_summary["promoted"] == 0
        else 0
    )
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
