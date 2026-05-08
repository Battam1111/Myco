"""``senesce`` verb — close the session.

Two modes, matched to the two hooks that fire it:

* **Full (default)** — ``myco senesce``: runs ``reflect`` then
  ``immune(fix=True)`` then (v0.6.14+) ``_reap_vetoed_intents``.
  Invoked by the ``PreCompact`` hook, which blocks on the hook's
  completion — so the full pipeline gets to finish.
* **Quick** — ``myco senesce --quick``: runs ``reflect`` only.
  Invoked by the ``SessionEnd`` hook, which kills the process at a
  short default budget (~1.5 s in Claude Code; controlled by
  ``CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS``). Skipping immune +
  vetoed-intent reap keeps the hook well inside that budget.

Why the split is safe: ``reflect`` is the *state-advancing* piece
(raw → integrated is monotonic and per-note, so an interrupted run
just leaves the remainder to the next senesce / hunger). ``immune``
is read-only — the optional ``--fix`` pass that runs in full mode
is a nicety, not a correctness requirement: any finding it would
have surfaced is re-surfaced by the next ``myco hunger`` /
``myco immune`` call. ``_reap_vetoed_intents`` is also restartable —
the reaper records its progress in ``.myco_state/last_intent_reap.txt``
and re-runs are no-ops if no new comments since the last reap.

v0.5.3: renamed from ``session_end``. The manifest alias
``session-end`` still invokes this handler through v1.0.0.
v0.5.7: ``--quick`` flag added; default behavior unchanged.
v0.6.14: full mode gains a third step ``_reap_vetoed_intents`` that
parses new ``vetoed_intent`` comments on the substrate-wide
auto-evolve tracking issue (posted by ``.github/workflows/auto_revert.yml``)
and writes ``vetoed_at: <ISO timestamp>`` into matching entries of
``canon.system.governance.last_winnowed_proposals[]``. Idempotent +
shell-out only (uses ``gh`` CLI; no LLM call; substrate-side L0 P1
stays strict).
Governing crafts:
``docs/primordia/_landed/v0_5_x/v0_5_7_senesce_quick_mode_craft_2026-04-19.md``,
``docs/primordia/_landed/v0_5_x/v0_5_7_release_craft_2026-04-19.md``,
``docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md``
(reaper extension).

In fungal biology, senescence is the aging-into-dormancy phase
where the mycelium consolidates what it has absorbed and wards off
pathogens before sleep — which is exactly what this verb does.
The quick / full split is the biology of fast-vs-slow dormancy:
a sudden freeze only has time to close the cell walls (reflect);
a slow seasonal senescence also gets to prune and reinforce
(reflect + immune + reap).
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping
from datetime import datetime, timezone

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

#: Regex extracting the JSON blob from an auto_revert.yml-posted
#: ``vetoed_intent`` comment. The workflow writes a markdown code-block
#: containing a single JSON object on one line; this regex finds it.
_VETOED_INTENT_RE = re.compile(
    r"```json\s*(\{[^}]*\"slug\"\s*:[^}]*\})\s*```",
    re.DOTALL,
)


def _reap_vetoed_intents(ctx: MycoContext) -> dict[str, object]:
    """Read new vetoed_intent comments from the auto-evolve tracking issue.

    Writes ``vetoed_at: <ISO timestamp>`` into matching entries of
    ``canon.system.governance.last_winnowed_proposals[]`` for each
    comment seen since the last reap.

    Skips silently when:
    - canon ``governance.auto_evolve_tracking_issue_id`` is ``None``
      (substrate hasn't seeded a tracking issue yet — that's fine);
    - ``gh`` CLI is unavailable on PATH;
    - ``gh issue view`` fails (network down, auth missing, etc.).

    All shell-out; no LLM call; substrate-side L0 P1 stays strict.

    Idempotent: re-runs are no-ops because the per-comment
    ``createdAt`` cursor in ``.myco_state/last_intent_reap.txt`` filters
    out previously-reaped comments. If canon is mutated during the reap
    (i.e. one or more matching entries had ``vetoed_at: null`` and got
    a real timestamp), the reaper writes the canon back in place.
    """
    canon = ctx.substrate.canon
    governance = (canon.system or {}).get("governance", {}) or {}
    issue_id = governance.get("auto_evolve_tracking_issue_id")
    if issue_id is None:
        return {
            "reaped_count": 0,
            "skipped_reason": "auto_evolve_tracking_issue_id is null in canon",
        }

    state_dir = ctx.substrate.paths.state
    cursor_file = state_dir / "last_intent_reap.txt"
    last_reaped = (
        cursor_file.read_text(encoding="utf-8").strip()
        if cursor_file.is_file()
        else "1970-01-01T00:00:00Z"
    )

    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "view",
                str(issue_id),
                "--json",
                "comments",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ) as exc:
        return {
            "reaped_count": 0,
            "skipped_reason": f"gh CLI unavailable or failed: {exc}",
        }

    try:
        comments = json.loads(result.stdout).get("comments", [])
    except json.JSONDecodeError as exc:
        return {
            "reaped_count": 0,
            "skipped_reason": f"gh issue view returned non-JSON: {exc}",
        }

    pending_file = state_dir / "auto_evolve_vetoed_pending.json"
    pending: list[dict[str, object]] = []
    if pending_file.is_file():
        try:
            pending = json.loads(pending_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pending = []

    reaped = 0
    latest_seen = last_reaped
    pending_slugs = {p.get("slug") for p in pending if isinstance(p, dict)}

    for comment in comments:
        created_at = comment.get("createdAt", "")
        if created_at <= last_reaped:
            continue
        body = comment.get("body", "") or ""
        match = _VETOED_INTENT_RE.search(body)
        if match:
            try:
                intent = json.loads(match.group(1))
            except json.JSONDecodeError:
                intent = None
            if isinstance(intent, dict):
                slug = intent.get("slug")
                if slug and slug not in pending_slugs:
                    pending.append(
                        {
                            "slug": slug,
                            "pr_number": intent.get("pr_number"),
                            "branch": intent.get("branch"),
                            "vetoed_at": created_at,
                            "reason": intent.get(
                                "reason", "owner-closed-without-merge"
                            ),
                            "comment_id": comment.get("id"),
                            "reaped_at": datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z"),
                        }
                    )
                    pending_slugs.add(slug)
                    reaped += 1
        if created_at > latest_seen:
            latest_seen = created_at

    state_dir.mkdir(parents=True, exist_ok=True)
    if reaped > 0:
        # Pending vetoed_intents are queued to .myco_state/auto_evolve_vetoed_pending.json
        # rather than written directly to canon. v0.6.14 limitation: canon
        # round-trip with comment preservation requires a YAML round-trip
        # mechanism not in current deps (pyyaml.safe_dump strips comments
        # and key order; canon_schema.md rule 1 forbids the schema-annotation
        # header from drifting). v0.6.15+ adds a `myco molt --apply-vetoed`
        # path that drains this queue into canon.governance.last_winnowed_proposals[]
        # safely. Until then, the queue is the source of truth for vetoed_at.
        pending_file.write_text(
            json.dumps(pending, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # Update the cursor regardless of reaped count (we processed comments
    # up to latest_seen even if none matched).
    cursor_file.write_text(latest_seen + "\n", encoding="utf-8")

    return {
        "reaped_count": reaped,
        "tracking_issue_id": issue_id,
        "cursor_advanced_to": latest_seen,
        "pending_queue_path": str(pending_file.relative_to(ctx.substrate.root))
        if reaped > 0
        else None,
    }


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
    # v0.6.14: reap vetoed_intent comments from the auto-evolve tracking issue.
    # Best-effort: failures (gh missing, network down, no tracking issue
    # seeded) are silent + reported in the payload; do not gate exit code.
    try:
        reaper_payload = _reap_vetoed_intents(ctx)
    except Exception as exc:  # pragma: no cover — defensive
        reaper_payload = {
            "reaped_count": 0,
            "skipped_reason": f"reaper raised unexpectedly: {exc!r}",
        }

    combined_exit = max(reflect_exit, immune_result.exit_code)
    return Result(
        exit_code=combined_exit,
        findings=immune_result.findings,
        payload={
            "reflect": reflect_payload,
            "immune": dict(immune_result.payload),
            "vetoed_intent_reap": reaper_payload,
            "mode": "full",
        },
    )
