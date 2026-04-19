"""``senesce`` verb — close the session.

Two modes, matched to the two hooks that fire it:

* **Full (default)** — ``myco senesce``: runs ``reflect`` then
  ``immune(fix=True)``. Invoked by the ``PreCompact`` hook, which
  blocks on the hook's completion — so the full pipeline (reflect
  ~ms, immune ~seconds) gets to finish.
* **Quick** — ``myco senesce --quick``: runs ``reflect`` only.
  Invoked by the ``SessionEnd`` hook, which kills the process at a
  short default budget (~1.5 s in Claude Code; controlled by
  ``CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS``). Skipping immune
  keeps the hook well inside that budget.

Why the split is safe: ``reflect`` is the *state-advancing* piece
(raw → integrated is monotonic and per-note, so an interrupted run
just leaves the remainder to the next senesce / hunger). ``immune``
is read-only — the optional ``--fix`` pass that runs in full mode
is a nicety, not a correctness requirement: any finding it would
have surfaced is re-surfaced by the next ``myco hunger`` /
``myco immune`` call.

v0.5.3: renamed from ``session_end``. The manifest alias
``session-end`` still invokes this handler through v1.0.0.
v0.5.7: ``--quick`` flag added; default behavior unchanged.
Governing crafts:
``docs/primordia/v0_5_7_senesce_quick_mode_craft_2026-04-19.md``
(the quick-mode design) and
``docs/primordia/v0_5_7_release_craft_2026-04-19.md``
(the v0.5.7 release-closure audit).

In fungal biology, senescence is the aging-into-dormancy phase
where the mycelium consolidates what it has absorbed and wards off
pathogens before sleep — which is exactly what this verb does.
The quick / full split is the biology of fast-vs-slow dormancy:
a sudden freeze only has time to close the cell walls (reflect);
a slow seasonal senescence also gets to prune and reinforce
(reflect + immune).
"""

from __future__ import annotations

from collections.abc import Mapping

from myco.core.context import MycoContext, Result
from myco.digestion.assimilate import reflect
from myco.homeostasis.kernel import run_immune
from myco.homeostasis.registry import default_registry

__all__ = ["run"]


#: Reason string surfaced in the payload when immune is skipped.
#: Kept as a module-level constant so tests can assert on it and
#: downstream tooling can grep for it without string drift.
_QUICK_SKIP_REASON = (
    "--quick mode: reflect-only for SessionEnd hook timeout budget "
    "(~1.5s default). The next PreCompact/SessionStart will pick up "
    "any findings immune would have surfaced."
)


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Run reflect (+ immune --fix unless ``--quick``) and merge results.

    Args (all optional):
        quick: ``bool``. If true, skip the immune pass. Default false.

    Exit code is the worse (higher) of the two sub-results' exit
    codes in full mode; just the reflect exit code in quick mode.
    Payload always bundles both summaries under ``reflect`` and
    ``immune`` keys — in quick mode the ``immune`` value is
    ``{"skipped": True, "reason": <str>}`` so downstream consumers
    that read ``payload["immune"]["..."]`` don't KeyError.
    """
    # Accept ``quick`` via either snake_case (dispatcher path) or a
    # direct-dict call (older tests that pass ``{}``). ``build_handler_args``
    # always normalizes to snake so both forms land on the same key.
    quick = bool(args.get("quick", False)) if isinstance(args, Mapping) else False

    reflect_summary = reflect(ctx=ctx)
    reflect_exit = (
        1 if reflect_summary["errors"] and reflect_summary["promoted"] == 0 else 0
    )
    reflect_payload = {
        "promoted": reflect_summary["promoted"],
        "errors": reflect_summary["errors"],
        "outcomes": reflect_summary["outcomes"],
    }

    if quick:
        return Result(
            exit_code=reflect_exit,
            findings=(),
            payload={
                "reflect": reflect_payload,
                "immune": {
                    "skipped": True,
                    "reason": _QUICK_SKIP_REASON,
                },
                "mode": "quick",
            },
        )

    immune_result = run_immune(
        ctx,
        default_registry(),
        selected=None,
        exit_on="critical",
        fix=True,
    )
    combined_exit = max(reflect_exit, immune_result.exit_code)
    return Result(
        exit_code=combined_exit,
        findings=immune_result.findings,
        payload={
            "reflect": reflect_payload,
            "immune": dict(immune_result.payload),
            "mode": "full",
        },
    )
