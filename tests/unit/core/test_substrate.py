"""Tests for ``myco.core.substrate``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.errors import CanonSchemaError, SubstrateNotFound
from myco.core.substrate import Substrate, find_substrate_root


def test_find_walks_up_to_hit(seeded_substrate: Path) -> None:
    child = seeded_substrate / "a" / "b"
    child.mkdir(parents=True)
    assert find_substrate_root(child) == seeded_substrate.resolve()


def test_find_direct_hit(seeded_substrate: Path) -> None:
    assert find_substrate_root(seeded_substrate) == seeded_substrate.resolve()


def test_find_miss_raises(tmp_path: Path) -> None:
    # tmp_path has no _canon.yaml and walk-up eventually terminates.
    # Use a child to guarantee we traverse at least one parent.
    child = tmp_path / "nope"
    child.mkdir()
    with pytest.raises(SubstrateNotFound):
        find_substrate_root(child)


def test_find_innermost_wins(seeded_substrate: Path, minimal_canon_text: str) -> None:
    inner = seeded_substrate / "inner"
    inner.mkdir()
    (inner / "_canon.yaml").write_text(
        minimal_canon_text.replace("test-substrate", "inner-substrate"),
        encoding="utf-8",
    )
    root = find_substrate_root(inner)
    assert root == inner.resolve()


def test_find_corrupt_canon_propagates(tmp_path: Path) -> None:
    (tmp_path / "_canon.yaml").write_text("- bad\n", encoding="utf-8")
    with pytest.raises(CanonSchemaError):
        find_substrate_root(tmp_path)


def test_substrate_load(seeded_substrate: Path) -> None:
    s = Substrate.load(seeded_substrate)
    assert s.root == seeded_substrate.resolve()
    assert s.canon.substrate_id == "test-substrate"
    assert s.paths.notes == s.root / "notes"


def test_substrate_load_missing_canon(tmp_path: Path) -> None:
    with pytest.raises(CanonSchemaError, match="not found"):
        Substrate.load(tmp_path)


def test_substrate_discover(seeded_substrate: Path) -> None:
    child = seeded_substrate / "x" / "y"
    child.mkdir(parents=True)
    s = Substrate.discover(child)
    assert s.root == seeded_substrate.resolve()


def test_is_skeleton_false_by_default(seeded_substrate: Path) -> None:
    s = Substrate.load(seeded_substrate)
    assert s.is_skeleton is False


def test_is_skeleton_true_when_marker_present(seeded_substrate: Path) -> None:
    (seeded_substrate / ".myco_state").mkdir()
    (seeded_substrate / ".myco_state" / "autoseeded.txt").write_text("", encoding="utf-8")
    s = Substrate.load(seeded_substrate)
    assert s.is_skeleton is True
