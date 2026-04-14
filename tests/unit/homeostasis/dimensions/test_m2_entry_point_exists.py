"""Tests for ``M2EntryPointExists``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.m2_entry_point_exists import M2EntryPointExists


def test_fires_when_entry_file_missing(seeded_substrate: Path) -> None:
    # The minimal fixture's canon declares entry_point: MYCO.md but
    # the file isn't written; M2 should fire.
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(M2EntryPointExists().run(ctx))
    assert len(findings) == 1
    assert "MYCO.md" in findings[0].message


def test_silent_when_entry_file_present(seeded_substrate: Path) -> None:
    (seeded_substrate / "MYCO.md").write_text("# entry\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(M2EntryPointExists().run(ctx)) == []


def test_genesis_substrate_clean(genesis_substrate: Path) -> None:
    # Genesis bootstraps an entry-point file; M2 must be silent.
    ctx = MycoContext.for_testing(root=genesis_substrate)
    assert list(M2EntryPointExists().run(ctx)) == []
