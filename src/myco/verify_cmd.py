"""
Partition A (Vision Closure, G3) — ``myco verify`` command.

Truth Immune subsystem: verification of freshness claims in notes.

Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md §G3.

Usage:
    myco verify [--mark {still_true|ambiguous|contradicted} <note_id>] [--project-dir .]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta


def _project_root(args: Any) -> Path:
    """Delegates to centralized find_project_root."""
    from myco.project import find_project_root
    return find_project_root(getattr(args, "project_dir", None), strict=False)


def run_verify(args: Any) -> int:
    """Dispatch ``myco verify`` subcommand."""
    from myco.notes import read_note, update_note, list_notes, _now_iso

    root = _project_root(args)
    mark_action = getattr(args, "mark_action", None)
    mark_note_id = getattr(args, "mark_note_id", None)
    json_output = getattr(args, "json", False)

    # If marking a specific note
    if mark_action and mark_note_id:
        if mark_action not in ("still_true", "ambiguous", "contradicted"):
            print(f"Error: invalid action {mark_action!r}", file=sys.stderr)
            return 1

        # Find the note file by id
        notes_dir = root / "notes"
        target_path = None
        for p in notes_dir.glob("n_*.md"):
            try:
                meta, _ = read_note(p)
                if meta.get("id") == mark_note_id:
                    target_path = p
                    break
            except Exception:
                continue

        if not target_path:
            print(f"Note {mark_note_id} not found", file=sys.stderr)
            return 1

        # Update based on action
        try:
            now = datetime.now()
            if mark_action == "still_true":
                update_note(target_path, last_verified=_now_iso(now))
                print(f"Marked {mark_note_id} as still_true")
            elif mark_action == "ambiguous":
                meta, _ = read_note(target_path)
                old_window = meta.get("freshness_window_days", 90)
                new_window = max(1, old_window // 2)
                update_note(
                    target_path,
                    last_verified=_now_iso(now),
                    freshness_window_days=new_window,
                )
                print(
                    f"Marked {mark_note_id} as ambiguous "
                    f"(freshness window halved: {old_window}d → {new_window}d)"
                )
            elif mark_action == "contradicted":
                update_note(
                    target_path,
                    status="quarantine",
                    quarantine_reason=f"contradicted during verify check at {_now_iso(now)}",
                )
                print(f"Marked {mark_note_id} as contradicted (moved to quarantine)")
            return 0
        except Exception as e:
            print(f"Error updating note: {e}", file=sys.stderr)
            return 1

    # Verify stale notes (no mark action)
    notes_dir = root / "notes"
    if not notes_dir.exists():
        print("No notes/ directory found")
        return 0

    stale_notes: list[dict[str, Any]] = []
    now = datetime.now()

    # Thresholds: time_sensitive=90 days, live=7 days, static=never
    thresholds = {"time_sensitive": 90, "live": 7, "static": 999999}

    for p in notes_dir.glob("n_*.md"):
        try:
            meta, _ = read_note(p)
        except Exception:
            continue

        status = meta.get("status")
        if status not in ("extracted", "integrated"):
            continue  # Only check extracted/integrated notes

        freshness = meta.get("freshness", "time_sensitive")
        if freshness == "static":
            continue  # Static notes don't need verification

        last_verified_str = meta.get("last_verified", meta.get("created"))
        try:
            last_verified = datetime.strptime(last_verified_str, "%Y-%m-%dT%H:%M:%S")
        except (ValueError, TypeError):
            last_verified = now

        threshold_days = thresholds.get(freshness, 90)
        age_days = (now - last_verified).days

        if age_days > threshold_days:
            stale_notes.append({
                "id": meta.get("id"),
                "file": p.name,
                "freshness": freshness,
                "last_verified_age_days": age_days,
                "threshold_days": threshold_days,
                "title": meta.get("tags", [None])[0] if meta.get("tags") else "untitled",
            })

    # Sort by staleness
    stale_notes.sort(key=lambda x: -x["last_verified_age_days"])

    # Output
    if json_output:
        print(json.dumps({"stale_count": len(stale_notes), "notes": stale_notes}, indent=2))
    else:
        if stale_notes:
            print(f"Stale notes ({len(stale_notes)}):")
            for note in stale_notes[:20]:  # Show top 20
                print(
                    f"  {note['id']}: {note['freshness']}, "
                    f"{note['last_verified_age_days']}d old "
                    f"(threshold {note['threshold_days']}d)"
                )
            if len(stale_notes) > 20:
                print(f"  ... and {len(stale_notes) - 20} more")
            print(f"\nRun: myco verify --mark still_true|contradicted|ambiguous <note_id>")
        else:
            print("All notes are within freshness windows.")

    return 0
