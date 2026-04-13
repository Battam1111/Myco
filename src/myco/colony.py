"""
Myco Cohort Intelligence — tag-based analysis for compression and gap detection.

Wave 48 (contract v0.37.0): Semantic cohort analysis over the notes/ substrate.
Tag co-occurrence, compression cohort suggestion, and gap detection (tags where
all knowledge is unprocessed). Pure engine — no CLI, no MCP imports.

Authoritative design: plan Waves 47-53 §Wave 48.
"""
# --- Mycelium references ---
# Architecture: docs/architecture.md §Compression pipeline

from __future__ import annotations

import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from myco.notes import list_notes, read_note


def _load_compression_config(root: Path) -> Dict[str, Any]:
    """Load compression thresholds from _canon.yaml."""
    canon_path = root / "_canon.yaml"
    defaults = {"ripe_threshold": 5, "ripe_age_days": 7}
    if not canon_path.exists():
        return defaults
    try:
        with open(canon_path, "r", encoding="utf-8") as f:
            canon = yaml.safe_load(f) or {}
        comp = (canon.get("system", {})
                     .get("notes_schema", {})
                     .get("compression", {}))
        return {
            "ripe_threshold": comp.get("ripe_threshold", defaults["ripe_threshold"]),
            "ripe_age_days": comp.get("ripe_age_days", defaults["ripe_age_days"]),
        }
    except Exception:
        return defaults


def _parse_created_dt(meta: Dict[str, Any]) -> Optional[datetime]:
    """Parse the 'created' field from note metadata."""
    raw = meta.get("created")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw
    raw_str = str(raw).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def tag_cooccurrence(root: Path) -> List[Tuple[str, str, int]]:
    """Compute pairwise tag co-occurrence across all notes.

    Returns list of (tag_a, tag_b, count) sorted by count descending.
    """
    cooccur: Dict[Tuple[str, str], int] = defaultdict(int)
    for path in list_notes(root):
        try:
            meta, _ = read_note(path)
        except Exception:
            continue
        tags = meta.get("tags", [])
        if not isinstance(tags, list) or len(tags) < 2:
            continue
        # Sort for consistent pair ordering
        sorted_tags = sorted(set(str(t) for t in tags))
        for a, b in combinations(sorted_tags, 2):
            cooccur[(a, b)] += 1

    result = [(a, b, count) for (a, b), count in cooccur.items()]
    result.sort(key=lambda x: (-x[2], x[0], x[1]))
    return result


def compression_cohort_suggest(
    root: Path,
    *,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Suggest groups of notes that should be compressed together.

    Algorithm:
    1. Scan all notes, collect tag → list of raw/digesting notes with ages.
    2. For tags with >= ripe_threshold notes, compute a score based on
       note count and age of oldest note.
    3. Return suggestions sorted by score descending.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    config = _load_compression_config(root)
    ripe_threshold = config["ripe_threshold"]
    ripe_age_days = config["ripe_age_days"]

    # Build tag → notes map (only raw/digesting, not already compressed)
    tag_notes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for path in list_notes(root):
        try:
            meta, _ = read_note(path)
        except Exception:
            continue
        status = meta.get("status", "")
        if status not in ("raw", "digesting"):
            continue
        # Skip already-compressed notes (cascade defense)
        if meta.get("compressed_from"):
            continue
        tags = meta.get("tags", [])
        if not isinstance(tags, list):
            continue
        created_dt = _parse_created_dt(meta)
        age_days = (now - created_dt).days if created_dt else 0
        note_info = {
            "id": meta.get("id", path.stem),
            "status": status,
            "age_days": age_days,
            "created": str(meta.get("created", "")),
        }
        for tag in tags:
            tag_notes[str(tag)].append(note_info)

    # Find ripe cohorts
    suggestions = []
    for tag, notes in tag_notes.items():
        if len(notes) < ripe_threshold:
            continue
        oldest_age = max(n["age_days"] for n in notes)
        if oldest_age < ripe_age_days:
            continue
        score = len(notes) * (1 + oldest_age / 7.0)
        suggestions.append({
            "tag": tag,
            "note_count": len(notes),
            "oldest_age_days": oldest_age,
            "cohort_score": round(score, 1),
            "note_ids": [n["id"] for n in sorted(notes, key=lambda x: -x["age_days"])],
        })

    suggestions.sort(key=lambda x: -x["cohort_score"])
    return suggestions


def gap_detection(root: Path) -> List[Dict[str, Any]]:
    """Find tags where ALL notes are raw or digesting (unprocessed domains).

    These represent knowledge the substrate has captured but never
    synthesized — topics with no extracted or integrated output.
    """
    # tag → {raw: count, digesting: count, extracted: count, integrated: count, ...}
    tag_status: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for path in list_notes(root):
        try:
            meta, _ = read_note(path)
        except Exception:
            continue
        status = meta.get("status", "raw")
        tags = meta.get("tags", [])
        if not isinstance(tags, list):
            continue
        for tag in tags:
            tag_status[str(tag)][status] += 1

    gaps = []
    for tag, counts in tag_status.items():
        raw = counts.get("raw", 0)
        digesting = counts.get("digesting", 0)
        extracted = counts.get("extracted", 0)
        integrated = counts.get("integrated", 0)
        total = sum(counts.values())

        # Gap = all notes are raw or digesting (no synthesis output)
        if extracted == 0 and integrated == 0 and (raw + digesting) > 0:
            gaps.append({
                "tag": tag,
                "raw_count": raw,
                "digesting_count": digesting,
                "total": total,
            })

    gaps.sort(key=lambda x: -x["total"])
    return gaps
