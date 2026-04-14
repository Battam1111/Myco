"""Unit tests for myco.forage — forage backlog detection (Wave 60)."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def forage_project(tmp_path):
    """Create a minimal Myco project with forage infrastructure."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.43.0'\n"
        "  entry_point: MYCO.md\n"
        "  forage_schema:\n"
        "    dir: forage\n"
        "    index_file: forage/_index.yaml\n"
        "    forage_backlog_threshold: 3\n"
        "    stale_raw_days: 14\n"
        "    total_budget_bytes: 209715200\n"
        "    hard_budget_bytes: 1073741824\n"
        "    license_recheck_days: 90\n"
        "    valid_statuses: [raw, digesting, digested, absorbed, discarded, quarantined]\n"
        "    valid_source_types: [paper, repo, article, other]\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "forage").mkdir()
    return tmp_path


def _write_manifest(forage_dir, items):
    """Write a forage manifest with given items."""
    manifest = {"schema_version": 1, "items": items}
    index_path = forage_dir / "_index.yaml"
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False)


def test_detect_forage_backlog_empty(forage_project):
    """Empty manifest produces no backlog signal."""
    from myco.forage import detect_forage_backlog

    _write_manifest(forage_project / "forage", [])
    result = detect_forage_backlog(forage_project)
    assert result is None


def test_detect_forage_backlog_fires(forage_project):
    """Enough raw items trigger the backlog signal."""
    from myco.forage import detect_forage_backlog

    items = [
        {"id": f"f_2026040{i}T000000_000{i}", "source_url": f"https://example.com/{i}",
         "source_type": "paper", "local_path": f"forage/papers/p{i}.pdf",
         "acquired_at": "2026-03-01T00:00:00", "status": "raw",
         "license": "unknown", "size_bytes": 1000}
        for i in range(4)  # 4 >= threshold of 3
    ]
    _write_manifest(forage_project / "forage", items)
    result = detect_forage_backlog(forage_project)
    assert result is not None
    assert "forage_backlog" in result


def test_forage_budget_within_limit(forage_project):
    """Items within budget don't trigger budget signal."""
    from myco.forage import detect_forage_backlog

    items = [
        {"id": "f_20260401T000000_0001", "source_url": "https://example.com/1",
         "source_type": "paper", "local_path": "forage/papers/p1.pdf",
         "acquired_at": "2026-04-12T00:00:00", "status": "digested",
         "license": "MIT", "size_bytes": 1000}
    ]
    _write_manifest(forage_project / "forage", items)
    result = detect_forage_backlog(forage_project)
    assert result is None


def test_forage_status_validation(forage_project):
    """Non-raw items don't count toward raw backlog."""
    from myco.forage import detect_forage_backlog

    items = [
        {"id": f"f_2026040{i}T000000_000{i}", "source_url": f"https://example.com/{i}",
         "source_type": "paper", "local_path": f"forage/papers/p{i}.pdf",
         "acquired_at": "2026-04-12T00:00:00", "status": "digested",
         "license": "MIT", "size_bytes": 1000}
        for i in range(5)  # 5 items but all digested — no backlog
    ]
    _write_manifest(forage_project / "forage", items)
    result = detect_forage_backlog(forage_project)
    assert result is None


# ── L14 digest_target backlink tests ──


def test_l14_broken_digest_target(forage_project):
    """digest_target pointing to a nonexistent note emits MEDIUM issue."""
    from myco.immune import lint_forage_hygiene

    canon = yaml.safe_load(
        (forage_project / "_canon.yaml").read_text(encoding="utf-8")
    )
    # notes/ dir exists but is empty — no note files
    (forage_project / "notes").mkdir(exist_ok=True)

    items = [
        {"id": "f_20260412T000000_ab01",
         "source_url": "https://example.com/paper",
         "source_type": "paper",
         "acquired_at": "2026-04-12T00:00:00",
         "status": "digested",
         "license": "MIT",
         "size_bytes": 500,
         "digest_target": ["n_20260411T194951_9e91"]}
    ]
    _write_manifest(forage_project / "forage", items)

    issues = lint_forage_hygiene(canon, forage_project)
    l14_medium = [i for i in issues if i[0] == "L14" and i[1] == "MEDIUM"
                  and "digest_target" in i[3] and "broken backlink" in i[3]]
    assert len(l14_medium) >= 1, f"Expected broken-backlink issue, got: {issues}"


def test_l14_valid_digest_target(forage_project):
    """digest_target pointing to an existing note emits no issue."""
    from myco.immune import lint_forage_hygiene

    canon = yaml.safe_load(
        (forage_project / "_canon.yaml").read_text(encoding="utf-8")
    )
    notes_dir = forage_project / "notes"
    notes_dir.mkdir(exist_ok=True)
    # Create the note file that digest_target references
    (notes_dir / "n_20260411T194951_9e91.md").write_text(
        "---\nstatus: extracted\n---\n# Test note\n"
    )

    items = [
        {"id": "f_20260412T000000_ab01",
         "source_url": "https://example.com/paper",
         "source_type": "paper",
         "acquired_at": "2026-04-12T00:00:00",
         "status": "digested",
         "license": "MIT",
         "size_bytes": 500,
         "digest_target": ["n_20260411T194951_9e91"]}
    ]
    _write_manifest(forage_project / "forage", items)

    issues = lint_forage_hygiene(canon, forage_project)
    backlink_issues = [i for i in issues if i[0] == "L14"
                       and "digest_target" in i[3]
                       and "broken backlink" in i[3]]
    assert len(backlink_issues) == 0, (
        f"Expected no broken-backlink issues, got: {backlink_issues}"
    )


# ── Wave 61: Mycelium Wrapping tests ──


@pytest.fixture
def forage_project_threshold_1(tmp_path):
    """Project with forage_backlog_threshold=1 for mycelium wrapping."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.43.0'\n"
        "  entry_point: MYCO.md\n"
        "  forage_schema:\n"
        "    dir: forage\n"
        "    index_file: forage/_index.yaml\n"
        "    forage_backlog_threshold: 1\n"
        "    stale_raw_days: 14\n"
        "    total_budget_bytes: 209715200\n"
        "    hard_budget_bytes: 1073741824\n"
        "    license_recheck_days: 90\n"
        "    valid_statuses: [raw, digesting, digested, absorbed, discarded, quarantined]\n"
        "    valid_source_types: [paper, repo, article, other]\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "forage").mkdir()
    (tmp_path / "notes").mkdir()
    return tmp_path


def test_forage_backlog_threshold_1(forage_project_threshold_1):
    """With threshold=1, a single raw item triggers the backlog signal."""
    from myco.forage import detect_forage_backlog

    items = [
        {"id": "f_20260413T000000_0001",
         "source_url": "https://example.com/paper1",
         "source_type": "paper",
         "local_path": "forage/papers/p1.pdf",
         "acquired_at": "2026-04-13T00:00:00",
         "status": "raw",
         "license": "MIT",
         "size_bytes": 1000}
    ]
    _write_manifest(forage_project_threshold_1 / "forage", items)
    result = detect_forage_backlog(forage_project_threshold_1)
    assert result is not None
    assert "forage_backlog" in result
    assert "1 raw items" in result or "1 raw item" in result


def test_digest_adds_forage_source(forage_project_threshold_1):
    """When digest is called with digest_target, referenced notes get forage_source."""
    from myco.forage import add_item, update_item_status
    from myco.notes import write_note, read_note

    root = forage_project_threshold_1

    # Create a note that will be the digest target.
    note_path = write_note(
        root, body="Extracted insight from paper.",
        tags=["forage-test"], source="forage",
    )
    meta, _ = read_note(note_path)
    note_id = meta["id"]

    # forage_source should NOT be present yet.
    assert "forage_source" not in meta

    # Add a forage item.
    item = add_item(
        root,
        source_url="https://example.com/paper1",
        source_type="paper",
        local_path="forage/papers/p1.pdf",
        license="MIT",
        why="Testing mycelium wrapping",
    )
    forage_id = item["id"]

    # Transition to "digested" with the note as digest_target.
    update_item_status(root, forage_id, "digested", digest_target=[note_id])

    # Re-read the note — forage_source should now be injected.
    meta2, _ = read_note(note_path)
    assert meta2.get("forage_source") == forage_id


def test_digest_preserves_existing_forage_source(forage_project_threshold_1):
    """Digest does not overwrite an existing forage_source on a note."""
    from myco.forage import add_item, update_item_status
    from myco.notes import write_note, read_note

    root = forage_project_threshold_1

    # Create a note WITH forage_source already set.
    note_path = write_note(
        root, body="Pre-linked note.",
        tags=["forage-test"], source="forage",
        forage_source="f_20260413T000000_original",
    )
    meta, _ = read_note(note_path)
    note_id = meta["id"]
    assert meta["forage_source"] == "f_20260413T000000_original"

    # Add a different forage item and digest targeting this note.
    item = add_item(
        root,
        source_url="https://example.com/paper2",
        source_type="paper",
        local_path="forage/papers/p2.pdf",
        license="MIT",
        why="Should not overwrite",
    )
    update_item_status(root, item["id"], "digested", digest_target=[note_id])

    # forage_source should remain the original value.
    meta2, _ = read_note(note_path)
    assert meta2["forage_source"] == "f_20260413T000000_original"
