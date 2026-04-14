"""
Partition A (Vision Closure, G6) — Cross-project Conduction Test Suite.

Tests for project tagging and cross-project clustering.

Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md §G6.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myco import notes
from myco.notes import write_note, read_note, infer_project_name
from myco.colony import cross_project_cluster


def test_infer_project_name_from_dir(_isolate_myco_project: Path) -> None:
    """Project name is inferred from directory."""
    root = _isolate_myco_project

    project_name = infer_project_name(root)

    # Should be the directory name
    assert project_name == root.name


def test_project_tag_on_write(_isolate_myco_project: Path) -> None:
    """Notes written get auto-tagged with project name."""
    root = _isolate_myco_project

    path = write_note(root, body="test", tags=["test"])
    meta, _ = read_note(path)

    # Should have a project field
    assert "project" in meta
    assert meta["project"] == root.name


def test_project_tag_explicit(_isolate_myco_project: Path) -> None:
    """Project tag can be explicitly provided."""
    root = _isolate_myco_project

    path = write_note(root, body="test", tags=["test"], project="custom_project")
    meta, _ = read_note(path)

    assert meta["project"] == "custom_project"


def test_cross_project_cluster_empty() -> None:
    """Cross-project clustering on empty dir returns empty clusters."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = cross_project_cluster(Path(tmpdir))

    assert result["clusters"] == []


def test_cross_project_cluster_single_project(tmp_path: Path) -> None:
    """Single project doesn't produce cross-project clusters (min 2 projects needed)."""
    project_a = tmp_path / "project_a"
    project_a.mkdir()

    # Create a Myco project with notes
    notes_dir = project_a / "notes"
    notes_dir.mkdir(parents=True)

    # Create a note manually (simplified for test)
    note_path = notes_dir / "n_20260414T000000_aaaa.md"
    note_path.write_text(
        """---
id: n_20260414T000000_aaaa
status: integrated
source: eat
tags: [vision, test]
created: 2026-04-14T00:00:00
last_touched: 2026-04-14T00:00:00
digest_count: 0
promote_candidate: false
excrete_reason: null
project: project_a
---
Test content
""",
        encoding="utf-8",
    )

    result = cross_project_cluster(tmp_path, min_cluster_size=2)

    # Should have no clusters (only 1 project)
    assert result["clusters"] == []


def test_cross_project_cluster_multi_project(tmp_path: Path) -> None:
    """Multiple projects with shared tags produce clusters."""
    project_a = tmp_path / "project_a"
    project_b = tmp_path / "project_b"
    project_a.mkdir()
    project_b.mkdir()

    # Create notes in project A
    notes_a = project_a / "notes"
    notes_a.mkdir()
    note_a = notes_a / "n_20260414T000000_aaaa.md"
    note_a.write_text(
        """---
id: n_20260414T000000_aaaa
status: integrated
source: eat
tags: [shared_topic, ai]
created: 2026-04-14T00:00:00
last_touched: 2026-04-14T00:00:00
digest_count: 1
promote_candidate: false
excrete_reason: null
project: project_a
---
Project A content about shared topic
""",
        encoding="utf-8",
    )

    # Create notes in project B
    notes_b = project_b / "notes"
    notes_b.mkdir()
    note_b = notes_b / "n_20260414T000001_bbbb.md"
    note_b.write_text(
        """---
id: n_20260414T000001_bbbb
status: integrated
source: eat
tags: [shared_topic, research]
created: 2026-04-14T00:00:01
last_touched: 2026-04-14T00:00:01
digest_count: 1
promote_candidate: false
excrete_reason: null
project: project_b
---
Project B content about shared topic
""",
        encoding="utf-8",
    )

    result = cross_project_cluster(tmp_path, min_cluster_size=1)

    # Should find a cluster for shared_topic
    clusters = result.get("clusters", [])
    found_cluster = None
    for cluster in clusters:
        if cluster["topic_slug"] == "shared_topic":
            found_cluster = cluster
            break

    assert found_cluster is not None, "Should find shared_topic cluster"
    assert len(found_cluster["contributing_projects"]) == 2
    assert "project_a" in found_cluster["contributing_projects"]
    assert "project_b" in found_cluster["contributing_projects"]
    assert found_cluster["total_notes"] == 2
