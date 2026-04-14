"""
Partition A (Vision Closure, G3) — Truth Immune Freshness Test Suite.

Tests for note freshness tracking and verification windows.

Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md §G3.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from myco import notes
from myco.notes import write_note, update_note, read_note, VALID_STATUSES


def test_freshness_field_defaults(_isolate_myco_project: Path) -> None:
    """Newly written notes default to time_sensitive freshness."""
    root = _isolate_myco_project

    path = write_note(root, body="test content", tags=["test"])
    meta, _ = read_note(path)

    assert meta.get("freshness") == "time_sensitive"
    assert meta.get("last_verified") == meta.get("created")


def test_freshness_static_notes(_isolate_myco_project: Path) -> None:
    """Static freshness notes don't need re-verification."""
    root = _isolate_myco_project

    path = write_note(root, body="theorem", tags=["math"])
    update_note(path, freshness="static")

    meta, _ = read_note(path)
    assert meta.get("freshness") == "static"

    # A static note from 1000 days ago should not be marked stale
    # (this would be tested by the verify command, but we test the field here)


def test_quarantine_status_is_valid(_isolate_myco_project: Path) -> None:
    """Quarantine is a valid status."""
    root = _isolate_myco_project

    path = write_note(root, body="test", tags=["test"], status="raw")
    update_note(path, status="quarantine")

    meta, _ = read_note(path)
    assert meta.get("status") == "quarantine"


def test_quarantine_reason_required(_isolate_myco_project: Path) -> None:
    """When transitioning to quarantine, should set quarantine_reason."""
    root = _isolate_myco_project

    path = write_note(root, body="test", tags=["test"])
    reason = "contradicted at 2026-04-14"
    update_note(path, status="quarantine", quarantine_reason=reason)

    meta, _ = read_note(path)
    assert meta.get("quarantine_reason") == reason


def test_last_verified_tracking(_isolate_myco_project: Path) -> None:
    """last_verified is updated when note is verified."""
    root = _isolate_myco_project

    path = write_note(root, body="test", tags=["test"])
    original_verified = notes._now_iso()

    # Simulate a verification update
    new_verified = notes._now_iso(datetime.now() + timedelta(hours=1))
    update_note(path, last_verified=new_verified)

    meta, _ = read_note(path)
    assert meta.get("last_verified") == new_verified


def test_freshness_levels(_isolate_myco_project: Path) -> None:
    """Test the three freshness levels."""
    root = _isolate_myco_project

    levels = ["static", "time_sensitive", "live"]
    paths = {}

    for level in levels:
        path = write_note(
            root,
            body=f"{level} content",
            tags=["test"],
        )
        update_note(path, freshness=level)
        paths[level] = path

    for level in levels:
        meta, _ = read_note(paths[level])
        assert meta.get("freshness") == level
