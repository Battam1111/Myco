#!/usr/bin/env python3
"""
Myco Notes CLI — the four-command digestive set.

Wires `myco eat | digest | view | hunger` into the shared notes engine
(src/myco/notes.py). Designed for both human invocation and MCP-agent
dogfooding.

Philosophy:
    * `eat`     — permissive capture. No questions asked. Minimum friction.
    * `digest`  — reflective transition. Outputs prompts, not answers.
    * `view`    — read-only lens on the substrate.
    * `hunger`  — metabolic dashboard that *signals*, never *nags*.

Keep the output human-readable but structured. Agents parse the printed
ids and paths; humans read the headlines.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from myco.notes import (
    VALID_STATUSES,
    VALID_SOURCES,
    MycoProjectNotFound,
    auto_excrete_dead_knowledge,
    compute_hunger_report,
    id_to_filename,
    list_notes,
    read_note,
    record_view,
    update_note,
    write_note,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project_root(args) -> Path:
    """Wave A1: delegates to centralized find_project_root."""
    from myco.project import find_project_root
    return find_project_root(getattr(args, "project_dir", None))


def _guard_project(func):
    """Decorator: catch MycoProjectNotFound from run_* verbs and
    exit 2 with a stderr message. Wave 20 strict-mode wrapper.
    """
    def _wrapped(args):
        try:
            return func(args)
        except MycoProjectNotFound as e:
            print(f"myco {func.__name__.removeprefix('run_')}: {e}",
                  file=sys.stderr)
            return 2
    _wrapped.__name__ = func.__name__
    _wrapped.__doc__ = func.__doc__
    return _wrapped


def _read_body_from_args(args) -> str:
    """Resolve body content from --content / --file / stdin."""
    if getattr(args, "content", None):
        return args.content
    if getattr(args, "file", None):
        p = Path(args.file).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"--file not found: {p}")
        return p.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data.strip():
            return data
    raise ValueError(
        "No content provided. Use --content '...', --file path, or pipe via stdin."
    )


def _print_header(title: str) -> None:
    print(f"\n🍄 {title}\n" + "─" * (len(title) + 3))


# ---------------------------------------------------------------------------
# eat  — permissive capture
# ---------------------------------------------------------------------------

@_guard_project
def run_eat(args) -> int:
    """`myco eat` — ingest a chunk of content as a raw note.

    Zero-friction by design: no interactive prompts, no confirmation. If
    the content is malformed, that's fine — the digestive tract can handle
    garbage-in at this stage.
    """
    root = _project_root(args)
    try:
        body = _read_body_from_args(args)
    except (FileNotFoundError, ValueError) as e:
        print(f"eat: {e}", file=sys.stderr)
        return 2

    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    source = args.source or "eat"
    title = args.title

    path = write_note(
        root, body,
        tags=tags,
        source=source,
        status="raw",
        title=title,
    )
    rel = path.relative_to(root)
    note_id = path.stem

    if args.json:
        print(json.dumps({
            "status": "ok",
            "id": note_id,
            "file": str(rel),
            "tags": tags,
            "source": source,
        }, ensure_ascii=False))
    else:
        _print_header(f"Eaten: {note_id}")
        print(f"  file:   {rel}")
        print(f"  status: raw")
        print(f"  source: {source}")
        if tags:
            print(f"  tags:   {', '.join(tags)}")
        print(f"\n  Next: `myco digest {note_id}` when ready to process.")
    return 0


# ---------------------------------------------------------------------------
# correct  — self-correction shortcut (Wave 19, contract v0.18.0)
# ---------------------------------------------------------------------------

@_guard_project
def run_correct(args) -> int:
    """`myco correct` — Hard Contract rule #3 ergonomic shortcut (Wave 19).

    Thin wrapper over `run_eat` that force-merges the mandatory tag pair
    `friction-phase2, on-self-correction` required whenever the agent
    utters a self-correction ("what I said earlier about X is wrong").
    Additional user tags are appended in order, deduplicated exactly.

    Motivation: H-3 from panorama audit `n_20260411T231220_3fb8`. The
    previous friction was remembering both the rule and the exact tag
    incantation under cognitive load; a one-verb shortcut drops that
    barrier to zero. Full detection still requires Phase 2 chat-stream
    NLP — kernel code can only make compliance cheap, not automatic.

    Canon source of truth for the mandatory tag set:
        system.self_correction.mandatory_tags
    """
    user_tags = [t.strip() for t in (getattr(args, "tags", "") or "").split(",") if t.strip()]
    required = ["friction-phase2", "on-self-correction"]
    merged = required + [t for t in user_tags if t not in required]
    args.tags = ",".join(merged)
    if not getattr(args, "source", None):
        args.source = "eat"
    return run_eat(args)


# ---------------------------------------------------------------------------
# digest  — reflective transition
# ---------------------------------------------------------------------------

_DIGEST_PROMPTS = [
    "What is the single most compressible claim in this note?",
    "Is there an existing wiki page or MYCO.md section this belongs to?",
    "If this were lost tomorrow, what would break?",
    "What should the new status be: extracted / integrated / excreted?",
]


@_guard_project
def run_digest(args) -> int:
    """`myco digest` — move a note along the lifecycle.

    Modes:
        myco digest                     # pick oldest raw note, print prompts
        myco digest <id>                # target specific note
        myco digest <id> --to extracted # apply a transition
        myco digest <id> --excrete "why"# shortcut to excreted
    """
    root = _project_root(args)

    # Resolve target note
    target: Optional[Path] = None
    if args.note_id:
        nid = args.note_id
        if not nid.startswith("n_"):
            nid = "n_" + nid
        candidate = root / "notes" / id_to_filename(nid)
        if not candidate.exists():
            print(f"digest: note not found: {nid}", file=sys.stderr)
            return 2
        target = candidate
    else:
        raw_notes = list_notes(root, status="raw")
        if not raw_notes:
            print("digest: nothing to digest — no raw notes in queue.")
            return 0
        target = raw_notes[0]

    meta, body = read_note(target)

    # Excrete shortcut
    if args.excrete:
        update_note(
            target,
            status="excreted",
            excrete_reason=args.excrete,
            _increment_digest=True,
        )
        print(f"🍄 Excreted {target.stem}: {args.excrete}")
        return 0

    # Explicit transition
    if args.to:
        if args.to not in VALID_STATUSES:
            print(
                f"digest: invalid --to {args.to!r}; expected one of "
                f"{list(VALID_STATUSES)}",
                file=sys.stderr,
            )
            return 2
        update_note(target, status=args.to, _increment_digest=True)
        print(f"🍄 {target.stem}: {meta.get('status', 'raw')} → {args.to}")
        return 0

    # Default: transition to 'digesting' and print prompts
    if meta.get("status") == "raw":
        update_note(target, status="digesting", _increment_digest=True)
        current_status = "digesting"
    else:
        update_note(target, _increment_digest=True)
        current_status = meta.get("status", "raw")

    _print_header(f"Digesting: {target.stem}")
    print(f"  status: {meta.get('status')} → {current_status}")
    print(f"  tags:   {', '.join(meta.get('tags') or []) or '(none)'}")
    print(f"  digest_count: {int(meta.get('digest_count') or 0) + 1}")
    print(f"\n  Body preview:")
    for line in body.splitlines()[:12]:
        print(f"    │ {line}")
    if len(body.splitlines()) > 12:
        print(f"    │ … ({len(body.splitlines()) - 12} more lines)")
    print("\n  Reflection prompts:")
    for i, q in enumerate(_DIGEST_PROMPTS, 1):
        print(f"    {i}. {q}")
    print(
        "\n  Next: answer above, then `myco digest "
        f"{target.stem} --to extracted|integrated|excreted`."
    )
    return 0


# ---------------------------------------------------------------------------
# view  — read-only lens
# ---------------------------------------------------------------------------

@_guard_project
def run_view(args) -> int:
    """`myco view` — read-only lens on the substrate.

    Modes (dispatch order):
        myco view <id>              single note body (positional, legacy)
        myco view --next-raw        body of oldest raw note (digest-queue head)
        myco view --tag T           table of notes whose tags contain T
        myco view [--status S]      table of notes (optionally status-filtered)

    `--next-raw` and `--tag` were added in Wave 21 (v0.20.0) to give
    the verb agent-facing value (closes NH-7). The positional-id mode
    and the default list mode are unchanged.
    """
    root = _project_root(args)

    # Wave 21 --next-raw mode: show the body of the oldest raw note.
    if getattr(args, "next_raw", False):
        raws = list_notes(root, status="raw")
        if not raws:
            _print_header("Next raw note")
            print("  (no raw notes; raw backlog is empty)")
            return 0
        # list_notes returns sorted by filename which encodes timestamp,
        # so the first entry is the oldest.
        path = raws[0]
        try:
            meta, body = read_note(path)
        except Exception as e:
            print(f"view --next-raw: {e}", file=sys.stderr)
            return 2
        _print_header(f"Next raw note: {meta.get('id')}")
        for k in ("status", "source", "tags", "created", "last_touched",
                  "digest_count"):
            print(f"  {k}: {meta.get(k)}")
        print("\n" + body.rstrip())
        print(f"\n  Next: `myco digest {meta.get('id')}` to process.")
        try:
            record_view(path)
        except Exception:
            pass
        return 0

    # Wave 21 --tag mode: filter by frontmatter tag, table output.
    if getattr(args, "tag", None):
        tag = args.tag
        paths = list_notes(root, status=args.status)
        matched = []
        for p in paths:
            try:
                meta, _ = read_note(p)
            except Exception:
                continue
            if tag in (meta.get("tags") or []):
                matched.append((p, meta))
        # Sort by last_touched desc. Coerce to str because YAML can
        # deserialize ISO-8601 dates as datetime objects, which don't
        # compare against plain strings → TypeError.
        def _sort_key(item):
            _, m = item
            v = m.get("last_touched") or m.get("created") or ""
            return str(v)
        matched.sort(key=_sort_key, reverse=True)
        matched = matched[: (args.limit or 50)]
        if args.json:
            out = []
            for p, m in matched:
                out.append({
                    "id": m.get("id"),
                    "file": str(p.relative_to(root)),
                    "status": m.get("status"),
                    "tags": m.get("tags") or [],
                    "digest_count": m.get("digest_count"),
                    "last_touched": m.get("last_touched"),
                })
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        _print_header(f"notes tagged '{tag}' (showing {len(matched)})")
        if not matched:
            print("  (no matches)")
            return 0
        for p, meta in matched:
            try:
                _, body = read_note(p)
            except Exception:
                continue
            title = ""
            for line in body.splitlines():
                if line.strip().startswith("#"):
                    title = line.strip().lstrip("#").strip()
                    break
            if not title:
                title = (body.strip().splitlines() or [""])[0][:60]
            tag_str = ",".join(meta.get("tags") or [])
            print(
                f"  [{meta.get('status','?'):<10}] {meta.get('id','?')}  "
                f"d={meta.get('digest_count',0)}  {tag_str:<30}  {title[:50]}"
            )
        return 0

    # Single-note mode
    if args.note_id:
        nid = args.note_id
        if not nid.startswith("n_"):
            nid = "n_" + nid
        path = root / "notes" / id_to_filename(nid)
        if not path.exists():
            print(f"view: note not found: {nid}", file=sys.stderr)
            return 2
        meta, body = read_note(path)
        _print_header(f"Note: {nid}")
        display_keys = ["status", "source", "tags", "created", "last_touched",
                        "digest_count", "promote_candidate", "excrete_reason"]
        # Surface optional v0.4.0 fields if present (view_count / last_viewed_at)
        for opt in ("view_count", "last_viewed_at"):
            if opt in meta:
                display_keys.append(opt)
        for k in display_keys:
            print(f"  {k}: {meta.get(k)}")
        print("\n" + body.rstrip())
        # Record the read (D-layer dead-knowledge detection input).
        # Deliberate: does NOT bump last_touched — read/write are separated.
        try:
            record_view(path)
        except Exception:
            # Non-fatal: view is read-only semantics from the user's POV.
            pass
        return 0

    # List mode
    status_filter = args.status
    if status_filter and status_filter not in VALID_STATUSES:
        print(
            f"view: invalid --status {status_filter!r}; expected one of "
            f"{list(VALID_STATUSES)}",
            file=sys.stderr,
        )
        return 2

    paths = list_notes(root, status=status_filter)
    limit = args.limit or 50
    paths = paths[-limit:]  # most recent N

    if args.json:
        out = []
        for p in paths:
            try:
                meta, _ = read_note(p)
            except Exception:
                continue
            out.append({
                "id": meta.get("id"),
                "file": str(p.relative_to(root)),
                "status": meta.get("status"),
                "tags": meta.get("tags") or [],
                "digest_count": meta.get("digest_count"),
                "last_touched": meta.get("last_touched"),
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    header = f"notes/ (filter: {status_filter or 'all'}, showing {len(paths)})"
    _print_header(header)
    if not paths:
        print("  (empty)")
        return 0
    for p in paths:
        try:
            meta, body = read_note(p)
        except Exception:
            continue
        title = ""
        for line in body.splitlines():
            if line.strip().startswith("#"):
                title = line.strip().lstrip("#").strip()
                break
        if not title:
            title = (body.strip().splitlines() or [""])[0][:60]
        tag_str = ",".join(meta.get("tags") or [])
        print(
            f"  [{meta.get('status','?'):<10}] {meta.get('id','?')}  "
            f"d={meta.get('digest_count',0)}  {tag_str:<20}  {title[:60]}"
        )
    return 0


# ---------------------------------------------------------------------------
# hunger  — metabolic dashboard
# ---------------------------------------------------------------------------

@_guard_project
def run_hunger(args) -> int:
    """`myco hunger` — show metabolic state + actionable signals."""
    root = _project_root(args)
    report = compute_hunger_report(root)

    # Wave 17 (contract v0.16.0) — Boot Brief Injector.
    # Side effects: persist boot brief + patch entry-point signals
    # block. Both are best-effort, never block hunger output.
    # See docs/primordia/boot_brief_injector_craft_2026-04-11.md.
    try:
        from myco.notes import write_boot_brief, render_entry_point_signals_block
        write_boot_brief(root, report)
        render_entry_point_signals_block(root, report)
    except Exception as _e:
        # Defensive: any failure in brief writers must not break hunger
        print(f"[WARN] boot brief writers: {_e}", file=sys.stderr)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0

    _print_header(f"Hunger report  ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"  total notes: {report.total}")
    print("  by_status:")
    for s in VALID_STATUSES:
        print(f"    {s:<11} {report.by_status.get(s, 0)}")
    print(f"  deep-digested (digest_count≥2): {len(report.deep_digested)}")
    print(f"  excreted-with-reason:            {report.excreted_with_reason}")
    print(f"  promote_candidates:              {len(report.promote_candidates)}")
    # D-layer dead-knowledge section (contract v0.4.0 seed).
    if getattr(report, "dead_notes", None):
        print(
            f"\n  💀 dead knowledge  "
            f"(terminal status, untouched & unread ≥ {report.dead_threshold_days}d, "
            f"view_count < 2):"
        )
        for d in report.dead_notes[:10]:
            print(
                f"    • {d.get('id','?')}  "
                f"status={d.get('status','?')}  "
                f"last_touched={d.get('last_touched','?')}  "
                f"views={d.get('view_count',0)}"
            )
        if len(report.dead_notes) > 10:
            print(f"    … ({len(report.dead_notes) - 10} more)")
    print("\n  Signals:")
    for s in report.signals:
        print(f"    • {s}")
    # Wave 54 (v0.41.0): --execute auto-runs ALL recommended actions.
    # Agent-first design: closes the signals→execution gap. The agent
    # calls `myco hunger --execute` and the substrate self-heals.
    if getattr(args, "execute", False) and report.actions:
        print(f"\n  ⚡ Auto-executing {len(report.actions)} action(s):")
        import subprocess
        for action in report.actions:
            verb = action.get("verb", "")
            action_args = action.get("args", {})
            reason = action.get("reason", "")
            # Build CLI command
            cmd_parts = [sys.executable, "-c",
                         "from myco.cli import main; main()", "--"]
            if verb == "digest":
                note_id = action_args.get("note_id")
                if note_id:
                    cmd_parts += ["digest", note_id, "--project-dir", str(root)]
                else:
                    # Bulk digest: skip — too complex for auto-execute
                    print(f"    ⏭ skip bulk digest (requires manual note selection)")
                    continue
            elif verb == "compress":
                tag = action_args.get("tag")
                cohort = action_args.get("cohort")
                if cohort == "auto":
                    cmd_parts += ["compress", "--cohort", "auto",
                                  "--rationale", f"auto: {reason}",
                                  "--project-dir", str(root)]
                elif tag:
                    cmd_parts += ["compress", "--tag", tag,
                                  "--rationale", f"auto: {reason}",
                                  "--project-dir", str(root)]
                else:
                    print(f"    ⏭ skip compress (no tag or cohort)")
                    continue
            elif verb == "prune":
                cmd_parts += ["prune", "--apply", "--project-dir", str(root)]
            elif verb == "inlet":
                # Inlet requires content — advisory only in auto mode
                print(f"    📋 inlet recommended: {reason}")
                continue
            else:
                print(f"    ⏭ skip unknown verb: {verb}")
                continue

            print(f"    → {verb}: {reason[:80]}...")
            try:
                result = subprocess.run(cmd_parts, capture_output=True,
                                        text=True, timeout=120)
                if result.returncode == 0:
                    print(f"      ✅ success")
                else:
                    stderr = (result.stderr or "").strip()[:120]
                    print(f"      ❌ exit {result.returncode}: {stderr}")
            except Exception as e:
                print(f"      ❌ error: {e}")
        print()

    # Non-zero exit if the substrate is in a concerning state.
    concerning = any(
        sig.startswith(
            ("raw_backlog", "stale_raw", "no_deep_digest",
             "no_excretion", "dead_knowledge")
        )
        for sig in report.signals
    )
    return 1 if concerning else 0


# ---------------------------------------------------------------------------
# Wave 33 — prune (D-layer auto-excretion)
# ---------------------------------------------------------------------------

@_guard_project
def run_prune(args) -> int:
    """`myco prune` — D-layer auto-excretion of dead-knowledge notes.

    Wave 33: closes the D-layer hunger-signal loop. Without this verb,
    `dead_knowledge` was a signal that the user had to manually act on
    by running `myco digest <id> --excrete "..."` for each candidate.
    With this verb, the substrate self-prunes when invoked.

    SAFETY: defaults to `--dry-run` (the SAFE mode). Requires explicit
    `--apply` flag to actually mutate. This is the inverse of the
    `myco compress --dry-run` opt-in: dry-run is the default for
    destructive operations, opt-in for additive ones. The asymmetry
    is intentional — see Wave 33 craft §1.4.

    Exit codes:
        0 — success (or empty cohort, which is also success)
        2 — usage error
        5 — io error (cannot read project)
    """
    from myco.notes import auto_excrete_dead_knowledge

    root = _project_root(args)
    threshold_days = getattr(args, "threshold_days", None)
    apply_mode = bool(getattr(args, "apply", False))
    json_out = bool(getattr(args, "json", False))

    results = auto_excrete_dead_knowledge(
        root,
        threshold_days=threshold_days,
        dry_run=not apply_mode,
    )

    if json_out:
        print(json.dumps({
            "mode": "apply" if apply_mode else "dry_run",
            "threshold_days": threshold_days,
            "candidate_count": len(results),
            "applied_count": sum(1 for r in results if r.get("applied")),
            "results": results,
        }, ensure_ascii=False, indent=2))
        return 0

    mode_label = "APPLY (writes)" if apply_mode else "DRY RUN (no writes)"
    _print_header(f"Prune dead knowledge — {mode_label}")
    if not results:
        print("  No dead-knowledge candidates found. Substrate is clean.")
        if not apply_mode:
            print("\n  (Run again with --apply to actually excrete.)")
        return 0

    print(f"  Found {len(results)} dead-knowledge candidate(s):\n")
    for r in results:
        marker = "✓ excreted" if r.get("applied") else "→ would excrete"
        if r.get("error"):
            marker = f"✗ FAILED ({r.get('error')})"
        print(f"  {marker}  {r.get('id', '?')}")
        print(f"      prior_status: {r.get('prior_status', '?')}")
        print(f"      reason:       {r.get('excrete_reason', '?')}")

    applied = sum(1 for r in results if r.get("applied"))
    failed = sum(1 for r in results if r.get("error"))
    print(f"\n  Total: {len(results)} candidates, "
          f"{applied} excreted, {failed} failed")
    if not apply_mode:
        print(
            f"\n  This was a DRY RUN. Re-run with `myco prune --apply` "
            f"to actually excrete these notes."
        )
    return 0
