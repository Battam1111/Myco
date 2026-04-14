"""
Myco Session-End Hook — Zero-touch close-out ritual.

Wave 56 (vision_closure_craft_2026-04-14.md Wave 1):
  When a session ends, automate:
    1. Auto-eat the session summary (if provided) as a raw note
    2. Prune --auto: excrete obvious dead-knowledge notes
    3. Refresh .myco_state/boot_brief.md so next session opens hot

Wave 57 (2026-04-14 Wave 2):
  Session-end brief is now ACTIONABLE — populated by
  session_hook._build_actionable_brief() which emits concrete
  `claude_hint`-style tool calls, not just signal descriptions.

Callable two ways:
  - Explicit MCP tool: myco_session_end(summary=..., project_dir=...)
  - Host adapter hook: hosts/{cowork,claude_code}.py can invoke on exit
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def run_session_end(
    root: Path,
    *,
    summary: Optional[str] = None,
    prune: bool = True,
    refresh_brief: bool = True,
) -> dict:
    """Execute session-end ritual. Never raises; returns a status dict."""
    root = Path(root).resolve()
    result = {
        "ok": True,
        "ate": None,
        "pruned": 0,
        "brief_refreshed": False,
        "errors": [],
    }

    if not (root / "_canon.yaml").exists():
        result["ok"] = False
        result["errors"].append("not a Myco project")
        return result

    # 1. Auto-eat summary
    if summary and summary.strip():
        try:
            from myco.notes import write_note
            path = write_note(
                root,
                summary,
                tags=["session-end", "auto"],
                source="chat",
                status="raw",
                title=f"Session summary {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            )
            result["ate"] = str(path.relative_to(root))
        except Exception as e:
            result["errors"].append(f"eat: {e}")

    # 2. Auto-prune (conservative: auto=True only excretes 2+-rule matches)
    if prune:
        try:
            from myco.notes import auto_excrete_multipath_candidates
            pruned = auto_excrete_multipath_candidates(
                root, auto=True, dry_run=False,
            )
            if pruned:
                result["pruned"] = sum(1 for p in pruned if p.get("applied"))
        except Exception as e:
            result["errors"].append(f"prune: {e}")

    # 3. Refresh boot brief
    if refresh_brief:
        try:
            _refresh_boot_brief(root)
            result["brief_refreshed"] = True
        except Exception as e:
            result["errors"].append(f"brief: {e}")

    # 4. Log metabolism tick (best-effort — signature matches compute_hunger output)
    try:
        from myco.metabolism import log_metabolism
        log_metabolism(root, {
            "event": "session_end",
            "total": 0,
            "by_status": {},
            "signals": [],
            "deep_digested": [],
            "dead_notes": [],
            "ate": bool(result["ate"]),
            "pruned": result["pruned"],
        })
    except Exception:
        pass  # metabolism module may not be present on old installs

    return result


def _refresh_boot_brief(root: Path) -> None:
    """Regenerate .myco_state/boot_brief.md as an ACTIONABLE brief.

    Wave 57: every signal is paired with a concrete tool call so the next
    session's Agent can execute without protocol reasoning.
    """
    brief_dir = root / ".myco_state"
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief = brief_dir / "boot_brief.md"

    brief.write_text(build_actionable_brief(root), encoding="utf-8")


def build_actionable_brief(root: Path) -> str:
    """Produce the actionable boot brief markdown.

    Format (Wave 57):
        # Boot Brief — <ts>
        ## ACTION_REQUIRED
        - [ ] <reason> → call: <tool>(<args>)
        ## ADVISORY
        - <signal>
    """
    root = Path(root)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    actions: list[tuple[str, str]] = []  # (reason, suggested_call)
    advisory: list[str] = []

    # --- Signals from substrate scan ---
    notes_dir = root / "notes"
    raw_ids: list[str] = []
    quarantined_ids: list[str] = []
    if notes_dir.is_dir():
        for f in sorted(notes_dir.glob("n_*.md")):
            head = f.read_text(encoding="utf-8", errors="replace")[:500]
            if "status: raw" in head:
                raw_ids.append(f.stem)
            if "quarantined: true" in head or "status: quarantined" in head:
                quarantined_ids.append(f.stem)

    if len(raw_ids) >= 3:
        ids_preview = ", ".join(raw_ids[:3]) + (" …" if len(raw_ids) > 3 else "")
        actions.append((
            f"{len(raw_ids)} raw notes pending digestion ({ids_preview})",
            f"myco_digest(note_id='{raw_ids[0]}', to_status='extracted')",
        ))
    elif raw_ids:
        advisory.append(f"{len(raw_ids)} raw note(s) pending — low pressure, handle when convenient.")

    if quarantined_ids:
        actions.append((
            f"{len(quarantined_ids)} quarantined note(s) awaiting re-verification",
            f"myco_verify(note_id='{quarantined_ids[0]}')",
        ))

    # --- Hunger signals from notes.compute_hunger_report ---
    # Wave 46 introduced HungerReport.actions — structured verb+args records.
    # We surface them directly; they are already agent-actionable.
    try:
        from myco.notes import compute_hunger_report
        report = compute_hunger_report(root)
        for act in (getattr(report, "actions", None) or [])[:8]:
            verb = act.get("verb", "")
            args = act.get("args", {}) or {}
            reason = act.get("reason", "hunger signal")
            # Map verbs to MCP tool calls.
            if verb == "digest":
                nid = args.get("note_id", "auto")
                actions.append((reason, f"myco_digest(note_id='{nid}', to_status='extracted')"))
            elif verb == "scent":
                topic = args.get("topic", "unknown")
                actions.append((reason, f"myco_scent(topic='{topic}')"))
            elif verb == "verify":
                nid = args.get("note_id", "auto")
                actions.append((reason, f"myco_verify(note_id='{nid}')"))
            elif verb == "condense":
                cluster = args.get("cluster_id", "auto")
                actions.append((reason, f"myco_condense(cluster_id='{cluster}')"))
            elif verb == "prune":
                actions.append((reason, "myco_prune(auto=True)"))
            elif verb == "eat":
                actions.append((reason, "myco_eat(content='...', source='chat')"))
            else:
                advisory.append(f"{reason} (verb={verb})")
        # Also surface top 2 string signals as advisory if no actions.
        for s in (getattr(report, "signals", None) or [])[:2]:
            if not any(s in r for r, _ in actions):
                advisory.append(s)
    except Exception:
        pass  # best-effort — never block session-end on brief generation

    # --- Canon / bootstrap state ---
    if not (root / "_canon.yaml").exists():
        actions.append((
            "No _canon.yaml — project not yet seeded",
            "myco_seed(project_dir='.', auto_detect=True)",
        ))

    # --- Compose markdown ---
    lines = [
        f"# Boot Brief — {now}",
        "",
        "Auto-generated by `session_hook.run_session_end`.",
        "Follow ACTION_REQUIRED items top-to-bottom; they are safe to execute in order.",
        "",
    ]
    if actions:
        lines.append("## ACTION_REQUIRED")
        lines.append("")
        for reason, call in actions:
            lines.append(f"- [ ] {reason}")
            lines.append(f"      → call: `{call}`")
        lines.append("")
    else:
        lines.append("## ACTION_REQUIRED")
        lines.append("")
        lines.append("- (none — substrate is in a healthy steady state)")
        lines.append("")

    if advisory:
        lines.append("## ADVISORY")
        lines.append("")
        for a in advisory:
            lines.append(f"- {a}")
        lines.append("")

    lines.append("## Next-action hint")
    lines.append("")
    if actions:
        lines.append(f"Execute the first ACTION_REQUIRED: `{actions[0][1]}`")
    else:
        lines.append("Call `myco_hunger(execute=true)` to confirm steady-state.")
    lines.append("")

    return "\n".join(lines)
