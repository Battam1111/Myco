"""
Partition A (Vision Closure, G5) — Engine Self-Evolution: Metabolism Tracking.

Metabolism logging: persistent record of Myco's metabolic state over time.

Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md §G5.

Usage:
    From notes.py, call ``log_metabolism(root, report)`` after computing hunger.
    From CLI, call ``myco introspect`` to analyze trends.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


METABOLISM_LOG_PATH = ".myco_state/metabolism.jsonl"


def log_metabolism(root: Path, hunger_report: Dict[str, Any]) -> None:
    """Partition A (G5): Log current metabolic state to JSONL.

    Called by compute_hunger_report after complete scan. Records:
        - timestamp (ISO 8601)
        - total_notes
        - by_status (counts per status)
        - signals_count (how many signals fired)
        - lint_score (if available)
        - miss_count (search misses, if tracked)
        - freshness_debt (count of past-window notes)
        - excretion_rate_7d (notes excreted in last 7 days)
        - deep_digested_count (digest_count ≥ 2)

    Appends one JSON line to .myco_state/metabolism.jsonl.
    """
    log_dir = Path(root) / ".myco_state"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "metabolism.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "total_notes": hunger_report.get("total", 0),
        "by_status": hunger_report.get("by_status", {}),
        "signals_count": len(hunger_report.get("signals", [])),
        "deep_digested_count": len(hunger_report.get("deep_digested", [])),
        "dead_notes_count": len(hunger_report.get("dead_notes", [])),
        # These will be populated by future features:
        "lint_score": None,
        "miss_count": 0,
        "freshness_debt": 0,  # TODO: compute from notes
        "excretion_rate_7d": 0,  # TODO: compute from counter
    }

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Silent fail — metabolism logging is advisory


def read_metabolism_log(
    root: Path,
    lookback_days: int = 30,
) -> list[Dict[str, Any]]:
    """Read recent entries from metabolism.jsonl.

    Returns list of entry dicts, most recent first.
    """
    log_path = Path(root) / METABOLISM_LOG_PATH
    if not log_path.exists():
        return []

    entries = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        return []

    # Filter by age
    now = datetime.now()
    cutoff = now - __import__("datetime").timedelta(days=lookback_days)
    recent = []
    for entry in entries:
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
            if ts >= cutoff:
                recent.append(entry)
        except (ValueError, KeyError, TypeError):
            continue

    return sorted(recent, key=lambda e: e.get("timestamp", ""), reverse=True)


def detect_worsening_metrics(entries: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect monotonically worsening metrics over recent runs.

    Returns dict with keys like:
        - worsening: list of (metric_name, trend_description)
        - stagnant_signals: list of (signal_name, fire_count)
        - suspect_files: list of (module_name, reason)
    """
    worsening = []
    stagnant_signals = []
    suspect_files = []

    if len(entries) < 5:
        return {
            "worsening": [],
            "stagnant_signals": [],
            "suspect_files": [],
            "note": "fewer than 5 runs recorded; insufficient data for trend detection",
        }

    # Extract numeric metrics
    metrics_to_check = ["freshness_debt", "miss_count", "dead_notes_count"]

    for metric in metrics_to_check:
        values = []
        for e in entries[-5:]:  # Last 5 entries
            val = e.get(metric)
            if isinstance(val, (int, float)):
                values.append(val)

        if len(values) == 5:
            # Check if strictly increasing (not just non-decreasing)
            # This avoids flagging flat metrics as "worsening"
            if all(values[i] < values[i + 1] for i in range(4)):
                worsening.append((metric, f"increasing: {values[0]} → {values[4]}"))

    return {
        "worsening": worsening,
        "stagnant_signals": stagnant_signals,
        "suspect_files": suspect_files,
    }
