"""Tests for ``myco.core.paths``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.io_cluster import SubstratePaths


def test_all_paths_derive_from_root(tmp_path: Path) -> None:
    p = SubstratePaths(root=tmp_path)
    assert p.canon == tmp_path / "_canon.yaml"
    assert p.notes == tmp_path / "notes"
    assert p.docs == tmp_path / "docs"
    assert p.state == tmp_path / ".myco/state"
    assert p.autoseeded_marker == tmp_path / ".myco/state" / "autoseeded.txt"
    assert p.boot_brief == tmp_path / ".myco/state" / "boot_brief.md"
    assert p.graph_cache == tmp_path / ".myco/state" / "graph.json"
    assert p.entry_point == tmp_path / "MYCO.md"


def test_is_frozen(tmp_path: Path) -> None:
    p = SubstratePaths(root=tmp_path)
    with pytest.raises(Exception):
        p.root = Path("/other")  # type: ignore[misc]
