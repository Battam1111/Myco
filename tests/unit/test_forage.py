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
