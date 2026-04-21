"""Tests for ``FR1FreshSubstrateInvariants``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.fr1_fresh_substrate_invariants import (
    FR1FreshSubstrateInvariants,
)


def test_fresh_substrate_clean(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    assert list(FR1FreshSubstrateInvariants().run(ctx)) == []


def test_missing_entry_point_fires_high(genesis_substrate: Path) -> None:
    (genesis_substrate / "MYCO.md").unlink()
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(FR1FreshSubstrateInvariants().run(ctx))
    assert any(f.severity is Severity.HIGH for f in findings)
    assert any("entry_point" in f.message for f in findings)


def test_missing_notes_raw_fires_medium(genesis_substrate: Path) -> None:
    import shutil

    shutil.rmtree(genesis_substrate / "notes" / "raw", ignore_errors=True)
    ctx = MycoContext.for_testing(root=genesis_substrate)
    findings = list(FR1FreshSubstrateInvariants().run(ctx))
    assert any(
        f.severity is Severity.MEDIUM and "notes/raw" in f.message for f in findings
    )
