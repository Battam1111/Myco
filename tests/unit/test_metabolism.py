"""
Partition A (Vision Closure, G5) — Engine Self-Evolution Metabolism Test Suite.

Tests for metabolism logging and trend detection.

Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md §G5.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from myco.metabolism import log_metabolism, read_metabolism_log, detect_worsening_metrics


def test_log_metabolism_creates_file(_isolate_myco_project: Path) -> None:
    """log_metabolism creates .myco_state/metabolism.jsonl."""
    root = _isolate_myco_project

    # Create a fake hunger report
    report = {
        "total": 10,
        "by_status": {"raw": 5, "integrated": 5},
        "signals": ["raw_backlog"],
        "deep_digested": [],
        "dead_notes": [],
    }

    log_metabolism(root, report)

    log_path = root / ".myco_state" / "metabolism.jsonl"
    assert log_path.exists()

    # Read and verify
    with open(log_path) as f:
        line = f.readline()
        entry = json.loads(line)

    assert entry["total_notes"] == 10
    assert entry["by_status"]["raw"] == 5
    assert "timestamp" in entry


def test_log_metabolism_appends(_isolate_myco_project: Path) -> None:
    """log_metabolism appends lines (idempotent multiple calls)."""
    root = _isolate_myco_project

    report1 = {"total": 5, "by_status": {"raw": 5}, "signals": [], "deep_digested": [], "dead_notes": []}
    report2 = {"total": 6, "by_status": {"raw": 6}, "signals": [], "deep_digested": [], "dead_notes": []}

    log_metabolism(root, report1)
    log_metabolism(root, report2)

    log_path = root / ".myco_state" / "metabolism.jsonl"
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")

    assert len(lines) == 2
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])

    assert entry1["total_notes"] == 5
    assert entry2["total_notes"] == 6


def test_read_metabolism_log(_isolate_myco_project: Path) -> None:
    """read_metabolism_log reads entries from JSONL."""
    root = _isolate_myco_project

    # Manually create entries
    log_path = root / ".myco_state" / "metabolism.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    entries_data = [
        {
            "timestamp": (now - timedelta(days=5)).isoformat(),
            "total_notes": 10,
            "by_status": {"raw": 5},
        },
        {
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "total_notes": 8,
            "by_status": {"raw": 3},
        },
    ]

    with open(log_path, "w") as f:
        for data in entries_data:
            f.write(json.dumps(data) + "\n")

    # Read back
    entries = read_metabolism_log(root, lookback_days=30)

    assert len(entries) == 2
    # Should be reverse chronological (most recent first)
    assert entries[0]["total_notes"] == 8
    assert entries[1]["total_notes"] == 10


def test_read_metabolism_log_age_filter(_isolate_myco_project: Path) -> None:
    """read_metabolism_log filters by age."""
    root = _isolate_myco_project

    log_path = root / ".myco_state" / "metabolism.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    old_entry = {
        "timestamp": (now - timedelta(days=40)).isoformat(),  # Outside lookback
        "total_notes": 100,
    }
    recent_entry = {
        "timestamp": (now - timedelta(days=1)).isoformat(),
        "total_notes": 50,
    }

    with open(log_path, "w") as f:
        f.write(json.dumps(old_entry) + "\n")
        f.write(json.dumps(recent_entry) + "\n")

    # Read with 30-day lookback
    entries = read_metabolism_log(root, lookback_days=30)

    # Should only get the recent one
    assert len(entries) == 1
    assert entries[0]["total_notes"] == 50


def test_detect_worsening_metrics_insufficient_data() -> None:
    """detect_worsening_metrics returns empty with < 5 entries."""
    entries = [
        {"freshness_debt": 1},
        {"freshness_debt": 2},
        {"freshness_debt": 3},
    ]

    result = detect_worsening_metrics(entries)

    assert result["worsening"] == []
    assert "insufficient data" in result.get("note", "")


def test_detect_worsening_metrics_increasing_debt() -> None:
    """detect_worsening_metrics detects monotonic increase."""
    entries = [
        {"freshness_debt": 0, "timestamp": "2026-04-10"},
        {"freshness_debt": 1, "timestamp": "2026-04-11"},
        {"freshness_debt": 2, "timestamp": "2026-04-12"},
        {"freshness_debt": 3, "timestamp": "2026-04-13"},
        {"freshness_debt": 4, "timestamp": "2026-04-14"},
    ]

    result = detect_worsening_metrics(entries)

    worsening = result.get("worsening", [])
    found_debt = False
    for metric, descr in worsening:
        if metric == "freshness_debt":
            found_debt = True
            assert "increasing" in descr

    assert found_debt, "Should detect increasing freshness_debt"


def test_detect_worsening_metrics_stable() -> None:
    """detect_worsening_metrics doesn't flag stable metrics."""
    entries = [
        {"freshness_debt": 5, "miss_count": 0},
        {"freshness_debt": 5, "miss_count": 0},
        {"freshness_debt": 5, "miss_count": 0},
        {"freshness_debt": 5, "miss_count": 0},
        {"freshness_debt": 5, "miss_count": 0},
    ]

    result = detect_worsening_metrics(entries)

    assert result["worsening"] == []
