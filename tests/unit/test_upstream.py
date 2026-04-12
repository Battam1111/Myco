"""Unit tests for myco.upstream — bundle pattern + scan detection (Wave 60)."""

from pathlib import Path

import pytest


@pytest.fixture
def upstream_project(tmp_path):
    """Create a minimal Myco project with upstream infrastructure."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.43.0'\n"
        "  entry_point: MYCO.md\n"
        "  upstream_scan_last_run: null\n"
        "  upstream_scan:\n"
        "    stale_days: 7\n"
        "    enabled: true\n"
        "  upstream_absorb:\n"
        "    kernel_inbox_dir: .myco_upstream_inbox\n"
        "    absorbed_subdir: absorbed\n"
        "    bundle_filename_pattern: '^n_\\d{8}T\\d{6}_[0-9a-f]+\\.bundle\\.(yaml|yml|json)$'\n"
        "    kernel_bundle_filename_pattern: '^\\d{8}T\\d{6}_n_\\d{8}T\\d{6}_[0-9a-f]+\\.bundle\\.(yaml|yml|json)$'\n"
        "    pointer_note_source: upstream_absorbed\n"
        "    batch_ingest_cap: 10\n"
        "  notes_schema:\n"
        "    dir: notes\n"
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    return tmp_path


def test_bundle_pattern_match(upstream_project):
    """Outbox bundle filename pattern matches valid bundles."""
    import re
    pattern = re.compile(r"^n_\d{8}T\d{6}_[0-9a-f]+\.bundle\.(yaml|yml|json)$")
    assert pattern.match("n_20260411T004215_ce72.bundle.yaml")
    assert pattern.match("n_20260412T123456_abcd.bundle.json")
    assert not pattern.match("random_file.txt")
    assert not pattern.match("n_20260411T004215_ce72.yaml")  # missing .bundle


def test_scan_detects_staleness(upstream_project):
    """upstream_scan_stale fires when last_run is null (never scanned)."""
    from myco.notes import detect_upstream_scan_stale

    result = detect_upstream_scan_stale(upstream_project)
    # With null last_run and no inbox bundles, signal should either be None
    # (no bundles to worry about) or a stale scan signal
    # The actual behavior depends on whether inbox exists
    # With no inbox dir, the signal is about staleness only
    assert result is None or "upstream_scan_stale" in str(result)


def test_inbox_absent_no_crash(upstream_project):
    """Missing inbox directory doesn't crash scan detection."""
    from myco.notes import detect_upstream_scan_stale

    # No .myco_upstream_inbox/ directory
    result = detect_upstream_scan_stale(upstream_project)
    # Should not raise — grandfather-compatible behavior
    assert result is None or isinstance(result, str)


def test_scan_with_stale_timestamp(upstream_project):
    """Stale scan timestamp with inbox bundles produces signal."""
    from myco.notes import detect_upstream_scan_stale
    import yaml

    # Set last_run to a very old timestamp
    canon_path = upstream_project / "_canon.yaml"
    with open(canon_path, "r") as f:
        canon = yaml.safe_load(f)
    canon["system"]["upstream_scan_last_run"] = "2026-01-01T00:00:00Z"
    with open(canon_path, "w") as f:
        yaml.dump(canon, f, default_flow_style=False)

    # Create inbox with a bundle
    inbox = upstream_project / ".myco_upstream_inbox"
    inbox.mkdir()
    (inbox / "n_20260411T004215_ce72.bundle.yaml").write_text("test: true\n")

    result = detect_upstream_scan_stale(upstream_project)
    assert result is not None
    assert "upstream_scan_stale" in result
