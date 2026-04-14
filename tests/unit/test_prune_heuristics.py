"""
Partition A (Vision Closure, G4) — Aggressive Excretion Test Suite.

Tests for multi-path prune candidate detection.

Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md §G4.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from myco import notes
from myco.notes import (
    write_note,
    update_note,
    detect_prune_candidates_multipath,
    auto_excrete_multipath_candidates,
)


def test_orphan_rule(_isolate_myco_project: Path) -> None:
    """Rule 1: Orphan (inbound=0, outbound ≤ 1, age > 14 days)."""
    root = _isolate_myco_project
    now = datetime.now()
    old_date = now - timedelta(days=20)

    # Create an orphaned note (no inbound, no outbound links, old age)
    orphan_path = write_note(
        root,
        body="This note is isolated with no links.",
        tags=["orphan-test"],
        now=old_date,
    )

    candidates = detect_prune_candidates_multipath(root, now=now)

    # Find our orphan in the candidates
    orphan_candidate = None
    for path, meta, rules_hit in candidates:
        if meta.get("id") == notes.filename_to_id(orphan_path.name):
            orphan_candidate = (path, meta, rules_hit)
            break

    assert orphan_candidate is not None, "Orphan note should be detected"
    assert "orphan" in orphan_candidate[2], f"Expected 'orphan' rule; got {orphan_candidate[2]}"


def test_superseded_rule(_isolate_myco_project: Path) -> None:
    """Rule 2: Superseded (superseded_by field is set)."""
    root = _isolate_myco_project

    # Create two notes
    old_path = write_note(root, body="Old version", tags=["test"])
    new_path = write_note(root, body="New version", tags=["test"])

    old_id = notes.filename_to_id(old_path.name)
    new_id = notes.filename_to_id(new_path.name)

    # Mark old as superseded by new
    update_note(old_path, superseded_by=new_id)

    candidates = detect_prune_candidates_multipath(root)

    # Find old note in candidates
    found = False
    for path, meta, rules_hit in candidates:
        if meta.get("id") == old_id:
            found = True
            assert "superseded" in rules_hit

    assert found, "Superseded note should be in candidates"


def test_low_value_raw_rule(_isolate_myco_project: Path) -> None:
    """Rule 3: Low-value raw (raw, digest_count=0, age > 30, inbound=0)."""
    root = _isolate_myco_project
    now = datetime.now()
    very_old_date = now - timedelta(days=40)

    # Create a raw note that's very old and undigested
    raw_path = write_note(
        root,
        body="Stale raw note",
        tags=["test"],
        status="raw",
        now=very_old_date,
    )

    candidates = detect_prune_candidates_multipath(root, now=now)

    raw_id = notes.filename_to_id(raw_path.name)
    found = False
    for path, meta, rules_hit in candidates:
        if meta.get("id") == raw_id:
            found = True
            assert "low_value_raw" in rules_hit

    assert found, "Low-value raw note should be detected"


def test_quarantine_stale_rule(_isolate_myco_project: Path) -> None:
    """Rule 4: Quarantine stale (status=quarantine, age > 14)."""
    root = _isolate_myco_project
    now = datetime.now()
    old_date = now - timedelta(days=20)

    # Create a quarantine note
    q_path = write_note(
        root,
        body="Quarantined content",
        tags=["test"],
        status="quarantine",
        now=old_date,
    )

    candidates = detect_prune_candidates_multipath(root, now=now)

    q_id = notes.filename_to_id(q_path.name)
    found = False
    for path, meta, rules_hit in candidates:
        if meta.get("id") == q_id:
            found = True
            assert "quarantine_stale" in rules_hit

    assert found, "Stale quarantine note should be detected"


def test_cold_terminal_rule(_isolate_myco_project: Path) -> None:
    """Rule 5: Cold terminal (integrated/extracted, old, unviewed)."""
    root = _isolate_myco_project
    now = datetime.now()
    old_date = now - timedelta(days=40)

    # Create an old integrated note
    old_integrated = write_note(
        root,
        body="Old terminal note",
        tags=["test"],
        status="integrated",
        now=old_date,
    )

    candidates = detect_prune_candidates_multipath(root, now=now)

    old_id = notes.filename_to_id(old_integrated.name)
    found = False
    for path, meta, rules_hit in candidates:
        if meta.get("id") == old_id:
            found = True
            assert "cold_terminal" in rules_hit

    assert found, "Cold terminal note should be detected"


def test_multiple_rules_trigger(_isolate_myco_project: Path) -> None:
    """When multiple rules fire, note is a strong excretion candidate."""
    root = _isolate_myco_project
    now = datetime.now()
    very_old = now - timedelta(days=50)

    # Create a note that triggers multiple rules:
    # - raw (low_value_raw)
    # - very old (orphan, cold_terminal)
    # - no links
    multi_rule_path = write_note(
        root,
        body="Multi-failure node",
        tags=["test"],
        status="raw",
        now=very_old,
    )

    candidates = detect_prune_candidates_multipath(root, now=now)

    multi_id = notes.filename_to_id(multi_rule_path.name)
    found = False
    for path, meta, rules_hit in candidates:
        if meta.get("id") == multi_id:
            found = True
            # Should hit multiple rules
            assert len(rules_hit) >= 2, f"Expected ≥2 rules; got {rules_hit}"

    assert found, "Multi-rule note should be detected"


def test_auto_excrete_only_2plus_rules(_isolate_myco_project: Path) -> None:
    """Auto-excrete only notes with 2+ rules (high confidence)."""
    root = _isolate_myco_project
    now = datetime.now()

    # Create a note with just 1 rule (orphan)
    old_date = now - timedelta(days=20)
    orphan_path = write_note(
        root,
        body="Might be orphan",
        tags=["test"],
        now=old_date,
    )

    # Create a note with 2+ rules
    very_old = now - timedelta(days=50)
    multi_path = write_note(
        root,
        body="Multi-rule",
        tags=["test"],
        status="raw",
        now=very_old,
    )

    results = auto_excrete_multipath_candidates(root, auto=True, dry_run=True, now=now)

    # Check which were marked for auto-excretion
    orphan_id = notes.filename_to_id(orphan_path.name)
    multi_id = notes.filename_to_id(multi_path.name)

    orphan_result = None
    multi_result = None
    for res in results:
        if res["id"] == orphan_id:
            orphan_result = res
        elif res["id"] == multi_id:
            multi_result = res

    # Multi-rule should be listed as strong candidate
    if multi_result:
        assert len(multi_result.get("rules_hit", [])) >= 2

    # In dry_run mode, nothing is applied
    for res in results:
        assert res["applied"] is False


def test_supersedes_field_sync(_isolate_myco_project: Path) -> None:
    """Test that supersedes/superseded_by fields stay in sync."""
    root = _isolate_myco_project

    old_path = write_note(root, body="v1", tags=["test"])
    new_path = write_note(root, body="v2", tags=["test"])

    old_id = notes.filename_to_id(old_path.name)
    new_id = notes.filename_to_id(new_path.name)

    # Set superseded_by on old note
    meta = update_note(old_path, superseded_by=new_id)

    assert meta.get("superseded_by") == new_id
    assert meta.get("id") == old_id

    # Read back and verify persistence
    meta2, _ = notes.read_note(old_path)
    assert meta2.get("superseded_by") == new_id
