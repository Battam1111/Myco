"""Tests for ``myco.homeostasis.skeleton``."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.finding import Category, Finding
from myco.homeostasis.skeleton import apply_skeleton_downgrade


@pytest.fixture
def canon_with_downgrade() -> str:
    return textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0-alpha.1"
        identity:
          substrate_id: "test"
          tags: []
          entry_point: "MYCO.md"
        system:
          hard_contract:
            rule_count: 7
        subsystems:
          genesis:
            package: "src/myco/genesis/"
        lint:
          skeleton_downgrade:
            marker: ".myco_state/autoseeded.txt"
            affected_dimensions: ["L0", "L1"]
        """
    )


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def _mk_finding(dim: str, sev: Severity) -> Finding:
    return Finding(
        dimension_id=dim,
        category=Category.MECHANICAL,
        severity=sev,
        message="x",
    )


def test_noop_when_not_skeleton(seeded_substrate: Path) -> None:
    ctx = _mk_ctx(seeded_substrate)
    fs = [_mk_finding("L0", Severity.CRITICAL)]
    out = apply_skeleton_downgrade(fs, ctx=ctx)
    assert out[0].severity is Severity.CRITICAL


def test_downgrades_affected_when_skeleton(
    tmp_path: Path, canon_with_downgrade: str
) -> None:
    (tmp_path / "_canon.yaml").write_text(canon_with_downgrade, encoding="utf-8")
    (tmp_path / ".myco_state").mkdir()
    (tmp_path / ".myco_state" / "autoseeded.txt").write_text("", encoding="utf-8")
    ctx = _mk_ctx(tmp_path)
    fs = [
        _mk_finding("L0", Severity.CRITICAL),
        _mk_finding("L1", Severity.HIGH),       # not CRITICAL, unchanged
        _mk_finding("L2", Severity.CRITICAL),  # not affected, unchanged
    ]
    out = apply_skeleton_downgrade(fs, ctx=ctx)
    assert out[0].severity is Severity.HIGH
    assert out[1].severity is Severity.HIGH
    assert out[2].severity is Severity.CRITICAL


def test_missing_affected_list_is_noop(seeded_substrate: Path) -> None:
    # seeded_substrate canon has no lint.skeleton_downgrade section.
    (seeded_substrate / ".myco_state").mkdir()
    (seeded_substrate / ".myco_state" / "autoseeded.txt").write_text(
        "", encoding="utf-8"
    )
    ctx = _mk_ctx(seeded_substrate)
    fs = [_mk_finding("L0", Severity.CRITICAL)]
    out = apply_skeleton_downgrade(fs, ctx=ctx)
    assert out[0].severity is Severity.CRITICAL
