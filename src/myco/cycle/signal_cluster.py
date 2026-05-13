"""Cluster module — v0.8.8 pass-4 merge of fruit, senesce, brief.

=== fruit ===
craft verb: scaffold a new three-round primordia doc.

MAJOR 9 (v0.5): elevates "craft" from a markdown-social-convention to
a real agent-callable verb. Given a ``--topic <slug>`` (and optional
``--kind`` tag), writes a new file at::

    docs/primordia/<slug>_craft_<YYYY-MM-DD>.md

with the three-round skeleton (claim / self-rebuttal / revision /
counter-rebuttal / reflection) pre-structured. The agent fills in
each section; the immune kernel (a future dimension CR1) verifies
the body shape meets the protocol floor.

Refuses to overwrite an existing file. Emits the final path in the
Result payload so the caller can open it.

Governing manifest: ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``
(governance-verbs section, v0.5 — per v0.5.0 craft §R13, no new L2
surface.md was created; the governance-verbs content lives at L3
alongside the rest of the verb surface). Historical: the v0.4
pre-rewrite ``craft_protocol.md`` was excreted at v0.7.0; the
``v0.3.4-final`` git tag preserves it.

=== senesce ===
``senesce`` verb — close the session.

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
the reaper records its progress in ``.myco/state/last_intent_reap.txt``
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
History: ``docs/contract_changelog.md`` § v0.5.7 (bimodal senesce
quick-mode landing) + § v0.6.14 (cycle-autostart reaper extension);
the v0.6.14 craft remains at
``docs/primordia/_landed/v0_6_x/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md``.

In fungal biology, senescence is the aging-into-dormancy phase
where the mycelium consolidates what it has absorbed and wards off
pathogens before sleep — which is exactly what this verb does.
The quick / full split is the biology of fast-vs-slow dormancy:
a sudden freeze only has time to close the cell walls (reflect);
a slow seasonal senescence also gets to prune and reinforce
(reflect + immune + reap).

=== brief ===
``myco brief`` — the one explicit human-facing verb.

v0.5.5 MAJOR-G. History: ``docs/contract_changelog.md`` § v0.5.5.

L0 principle 1 says humans do not browse Myco: humans speak natural
language, Agents invoke verbs. ``brief`` is the one carved exception
for the "show me what happened" moment — a markdown rollup of the
substrate's current state that a human can skim in 60 seconds. It
does NOT replace any agent-side verb; it summarizes the outputs of
agent-side verbs for a single human reading moment.

Sections (stable order):

1. Identity (substrate_id, contract_version, tags)
2. Hunger (current substrate backlog + reflex signals)
3. Immune (last 10 findings by severity)
4. Notes inventory (raw / integrated / distilled counts)
5. Primordia (most recent 5 craft docs with dates)
6. Local plugins (substrate-local extension inventory)
7. Suggested next (1-3 concrete actions)

Shape is fixed so repeated invocations are comparable; content is
derived from live substrate state (no cache).

No flags besides the global `--project-dir` and `--json`. Markdown is
the only human format; `--json` emits the same structure as a nested
dict for agents that want to pass it through.
"""

from __future__ import annotations

import json
import re
import string
import subprocess
from collections.abc import Mapping
from datetime import date as _date
from datetime import datetime, timezone
from importlib.resources import files as _pkg_files
from pathlib import Path
from typing import Any

from myco.core.identity_cluster import (
    ContractError,
    MycoContext,
    MycoError,
    Result,
    UsageError,
)
from myco.core.io_cluster import atomic_utf8_write, bounded_read_text
from myco.core.trust_cluster import check_write_allowed
from myco.digestion.cluster import reflect
from myco.homeostasis.kernel import run_immune
from myco.homeostasis.primitives_cluster import default_registry

# =========================================================================
# === fruit — formerly fruit.py
# =========================================================================

_SLUG_RE = re.compile("^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def _slugify(raw: str) -> str:
    """Normalize ``raw`` to a craft-slug shape.

    Accepts human-written phrases ("Schema forward-compat") and emits
    ``schema_forward_compat``. Rejects slugs that cannot be made
    conforming (e.g. bare digits, punctuation-only).
    """
    lowered = raw.strip().lower()
    normalized = re.sub("[^a-z0-9]+", "_", lowered).strip("_")
    if not normalized or not normalized[0].isalpha():
        raise UsageError(
            f"craft: topic {raw!r} does not yield a valid slug. Topic must start with a letter and contain letters, digits, spaces, or underscores."
        )
    if not _SLUG_RE.match(normalized):
        raise UsageError(
            f"craft: derived slug {normalized!r} does not match the craft-slug pattern [a-z][a-z0-9_]*."
        )
    return normalized


def _title_case(slug: str) -> str:
    """Turn ``schema_forward_compat`` into ``Schema Forward Compat``."""
    return " ".join(part.capitalize() for part in slug.split("_"))


def _load_template() -> str:
    return (
        _pkg_files("myco.cycle.templates")
        .joinpath("fruit.md.tmpl")
        .read_text(encoding="utf-8")
    )


def fruit_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: scaffold a primordia craft doc.

    Writes ``docs/primordia/<slug>_craft_<date>.md`` with the
    three-round skeleton (claim → rebuttal → revision → counter →
    convergence). Refuses to overwrite; agent fills in each section.
    """
    topic_raw = args.get("topic")
    if not topic_raw:
        raise UsageError("craft: --topic is required")
    slug = _slugify(str(topic_raw))
    kind = str(args.get("kind") or "design").strip() or "design"
    today = str(args.get("date") or _date.today().isoformat())
    primordia_dir = ctx.substrate.paths.docs / "primordia"
    filename = f"{slug}_craft_{today}.md"
    target = primordia_dir / filename
    if target.exists():
        raise ContractError(
            f"craft: refusing to overwrite existing {target}. Either edit it directly or rename it."
        )
    template = string.Template(_load_template())
    body = template.safe_substitute(
        topic=str(topic_raw), slug=slug, kind=kind, date=today, title=_title_case(slug)
    )
    check_write_allowed(ctx, target, verb="fruit")
    primordia_dir.mkdir(parents=True, exist_ok=True)
    atomic_utf8_write(target, body)
    return Result(
        exit_code=0,
        payload={
            "path": str(target.relative_to(ctx.substrate.root)),
            "slug": slug,
            "kind": kind,
            "date": today,
            "rounds": 3,
            "status": "DRAFT",
        },
    )


# =========================================================================
# === senesce — formerly senesce.py
# =========================================================================

_QUICK_SKIP_REASON = "--quick mode: reflect-only for SessionEnd hook timeout budget (~1.5s default). The next PreCompact/SessionStart will pick up any findings immune would have surfaced."

_VETOED_INTENT_RE = re.compile(
    '```json\\s*(\\{[^}]*\\"slug\\"\\s*:[^}]*\\})\\s*```', re.DOTALL
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
    ``createdAt`` cursor in ``.myco/state/last_intent_reap.txt`` filters
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
            ["gh", "issue", "view", str(issue_id), "--json", "comments"],
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
        pending_file.write_text(
            json.dumps(pending, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    cursor_file.write_text(latest_seen + "\n", encoding="utf-8")
    return {
        "reaped_count": reaped,
        "tracking_issue_id": issue_id,
        "cursor_advanced_to": latest_seen,
        "pending_queue_path": str(pending_file.relative_to(ctx.substrate.root))
        if reaped > 0
        else None,
    }


def senesce_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
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
                "immune": {"skipped": True, "reason": _QUICK_SKIP_REASON},
                "mode": "quick",
            },
        )
    immune_result = run_immune(
        ctx, default_registry(), selected=None, exit_on="critical", fix=True
    )
    try:
        reaper_payload = _reap_vetoed_intents(ctx)
    except Exception as exc:
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


# =========================================================================
# === brief — formerly brief.py
# =========================================================================


def _identity_section(ctx: MycoContext) -> dict[str, Any]:
    c = ctx.substrate.canon
    return {
        "substrate_id": c.substrate_id,
        "contract_version": c.contract_version,
        "synced_contract_version": c.synced_contract_version,
        "tags": list(c.tags),
        "entry_point": c.entry_point,
        "root": str(ctx.substrate.root),
    }


def _hunger_section(ctx: MycoContext) -> dict[str, Any]:
    from myco.ingestion.capture_cluster import compose_hunger_report

    report = compose_hunger_report(ctx)
    return report.as_dict()


def _immune_section(ctx: MycoContext) -> dict[str, Any]:
    """Run immune with a permissive exit policy and surface findings.

    Uses ``exit_on="never"`` so running ``brief`` never accidentally
    propagates a CI-gate exit. The finding list is capped at 10 so
    the human summary stays scannable.
    """
    from myco.homeostasis.kernel import run_immune
    from myco.homeostasis.primitives_cluster import default_registry

    try:
        result = run_immune(ctx, default_registry(), exit_on="never", fix=False)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "findings": [],
            "dimensions_run": [],
        }
    findings = []
    for f in result.findings[:10]:
        findings.append(
            {
                "dimension_id": f.dimension_id,
                "severity": f.severity.label(),
                "category": f.category.value,
                "message": f.message,
                "path": f.path,
            }
        )
    return {
        "ok": True,
        "dimensions_run": list(result.payload.get("dimensions_run", ())),
        "finding_count_total": len(result.findings),
        "findings": findings,
    }


def _notes_section(ctx: MycoContext) -> dict[str, Any]:
    root = ctx.substrate.paths.notes
    out = {"raw": 0, "integrated": 0, "distilled": 0}
    if not root.is_dir():
        return out
    for stage in ("raw", "integrated", "distilled"):
        d = root / stage
        if d.is_dir():
            out[stage] = sum(1 for p in d.glob("*.md") if p.is_file())
    return out


def _primordia_section(ctx: MycoContext, *, limit: int = 5) -> list[dict[str, Any]]:
    primordia_dir = ctx.substrate.paths.docs / "primordia"
    if not primordia_dir.is_dir():
        return []
    entries: list[tuple[str, Path]] = []
    for path in primordia_dir.glob("*.md"):
        if path.is_file():
            entries.append((path.name, path))
    entries.sort(key=lambda x: x[0], reverse=True)
    out = []
    for name, path in entries[:limit]:
        try:
            first_heading = ""
            for line in bounded_read_text(path).splitlines():
                if line.startswith("# "):
                    first_heading = line[2:].strip()
                    break
        except (OSError, MycoError):
            first_heading = ""
        out.append(
            {
                "name": name,
                "heading": first_heading,
                "rel": str(path.relative_to(ctx.substrate.root)),
            }
        )
    return out


def _local_plugins_section(ctx: MycoContext) -> dict[str, Any]:
    """Count **substrate-local** plugins only — kernel built-ins do not
    count as "local" even though they live in the same Python registry.

    v0.5.22: delegates to ``graft._collect_plugins`` so the scope
    classification is shared between ``graft``, ``hunger``, and this
    rollup. Pre-v0.5.22 this function (and its ``hunger`` sibling)
    counted every loaded dimension/adapter regardless of source,
    reporting "Local plugins: 32" on a fresh substrate where the
    actually-local count was zero.
    """
    from myco.cycle.canon_cluster import _collect_plugins

    by_kind = {"dimension": 0, "adapter": 0, "schema_upgrader": 0, "overlay_verb": 0}
    errors: list[str] = list(ctx.substrate.local_plugin_errors)
    try:
        for entry in _collect_plugins(ctx):
            if entry.get("scope") != "substrate":
                continue
            kind = entry.get("kind")
            if kind in by_kind:
                by_kind[kind] += 1
    except Exception as exc:
        errors.append(f"local-plugin enumeration failed: {exc}")
    return {"count": sum(by_kind.values()), "count_by_kind": by_kind, "errors": errors}


def _suggest_next(
    immune: dict[str, Any], hunger: dict[str, Any], notes: dict[str, int]
) -> list[str]:
    """Three-or-fewer concrete next actions."""
    suggestions: list[str] = []
    findings = immune.get("findings") or []
    critical = [f for f in findings if f.get("severity") == "critical"]
    high = [f for f in findings if f.get("severity") == "high"]
    if critical:
        suggestions.append(
            f"`myco immune --fix` — {len(critical)} critical finding(s) need attention"
        )
    elif high:
        suggestions.append(
            f"`myco immune --fix` — {len(high)} high-severity finding(s) fixable"
        )
    if notes.get("raw", 0) > 0 and notes.get("integrated", 0) == 0:
        suggestions.append(
            f"`myco assimilate` — {notes['raw']} raw note(s) awaiting promotion"
        )
    elif notes.get("raw", 0) > 10:
        suggestions.append(
            f"`myco assimilate` — {notes['raw']} raw notes (>10 threshold)"
        )
    if hunger.get("contract_drift"):
        suggestions.append(
            "`myco assimilate` — contract drift between canon and synced_contract_version"
        )
    if not suggestions:
        suggestions.append(
            "substrate quiet; no action required (next `myco hunger` will confirm)"
        )
    return suggestions[:3]


def _render_markdown(payload: Mapping[str, Any]) -> str:
    """Stable-order markdown rollup for human reading."""
    ident = payload["identity"]
    imm = payload["immune"]
    notes = payload["notes"]
    plugins = payload["local_plugins"]
    primordia = payload["primordia"]
    hunger = payload["hunger"]
    suggestions = payload["suggested_next"]
    lines: list[str] = []
    lines.append(f"# Myco brief — {ident['substrate_id']}")
    lines.append("")
    lines.append(f"*Generated {payload['generated_at']} at `{ident['root']}`.*")
    lines.append("")
    lines.append("## 1. Identity")
    lines.append("")
    lines.append(f"- **substrate_id**: `{ident['substrate_id']}`")
    lines.append(f"- **contract_version**: `{ident['contract_version']}`")
    if ident.get("synced_contract_version"):
        lines.append(
            f"- **synced_contract_version**: `{ident['synced_contract_version']}`"
        )
    if ident.get("tags"):
        lines.append(f"- **tags**: `{', '.join(ident['tags'])}`")
    lines.append(f"- **entry_point**: `{ident['entry_point']}`")
    lines.append("")
    lines.append("## 2. Hunger")
    lines.append("")
    lines.append(f"- contract_drift: `{hunger.get('contract_drift', False)}`")
    lines.append(f"- raw_backlog: `{hunger.get('raw_backlog', 0)}`")
    if hunger.get("reflex_signals"):
        lines.append(f"- reflex_signals: `{', '.join(hunger['reflex_signals'])}`")
    if hunger.get("advice"):
        for a in hunger["advice"]:
            lines.append(f"- {a}")
    lines.append("")
    lines.append("## 3. Immune")
    lines.append("")
    if imm.get("ok"):
        lines.append(
            f"- {len(imm.get('dimensions_run', []))} dimension(s) run, {imm.get('finding_count_total', 0)} finding(s)"
        )
        if imm.get("findings"):
            lines.append("")
            lines.append("| ID | severity | category | message | path |")
            lines.append("|---|---|---|---|---|")
            for f in imm["findings"]:
                msg = (f.get("message") or "").replace("|", "\\|")
                path = f.get("path") or "-"
                lines.append(
                    f"| {f['dimension_id']} | {f['severity']} | {f['category']} | {msg} | {path} |"
                )
    else:
        lines.append(f"- **immune failed**: {imm.get('error', 'unknown error')}")
    lines.append("")
    lines.append("## 4. Notes")
    lines.append("")
    lines.append(
        f"- raw: `{notes['raw']}` | integrated: `{notes['integrated']}` | distilled: `{notes['distilled']}`"
    )
    lines.append("")
    lines.append("## 5. Recent primordia")
    lines.append("")
    if primordia:
        for p in primordia:
            heading = p.get("heading") or p["name"]
            lines.append(f"- [`{p['name']}`]({p['rel']}) — {heading}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## 6. Local plugins")
    lines.append("")
    lines.append(f"- total: `{plugins['count']}`")
    for kind, n in plugins["count_by_kind"].items():
        lines.append(f"- {kind}: `{n}`")
    if plugins["errors"]:
        lines.append("")
        lines.append("**errors:**")
        for e in plugins["errors"]:
            lines.append(f"- {e}")
    lines.append("")
    lines.append("## 7. Suggested next")
    lines.append("")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")
    return "\n".join(lines)


def brief_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """brief handler. Produces a stable-section markdown rollup
    of the substrate's current state for a single human reading
    moment. L0 principle 1's single carved exception — brief is
    the one verb specifically intended for a human audience."""
    del args
    generated_at = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "identity": _identity_section(ctx),
        "hunger": _hunger_section(ctx),
        "immune": _immune_section(ctx),
        "notes": _notes_section(ctx),
        "primordia": _primordia_section(ctx),
        "local_plugins": _local_plugins_section(ctx),
    }
    payload["suggested_next"] = _suggest_next(
        payload["immune"], payload["hunger"], payload["notes"]
    )
    payload["markdown"] = _render_markdown(payload)
    return Result(exit_code=0, payload=payload)
