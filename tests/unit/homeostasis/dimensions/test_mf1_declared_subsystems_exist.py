"""Tests for ``MF1DeclaredSubsystemsExist``."""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.mf1_declared_subsystems_exist import (
    MF1DeclaredSubsystemsExist,
)


def _ctx_with_canon(tmp_path: Path, canon: str) -> MycoContext:
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    return MycoContext.for_testing(root=tmp_path)


def test_no_op_when_no_package_field(seeded_substrate: Path) -> None:
    """Canon with only ``doc:`` fields — no filesystem claim to check."""
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(MF1DeclaredSubsystemsExist().run(ctx))
    assert findings == []


def test_fires_when_package_missing(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          ghost:
            package: "src/made_up/package/"
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(MF1DeclaredSubsystemsExist().run(ctx))
    assert len(findings) == 1
    assert findings[0].dimension_id == "MF1"
    assert "ghost" in findings[0].message
    assert "src/made_up/package/" in findings[0].message


def test_silent_when_package_exists(tmp_path: Path) -> None:
    (tmp_path / "src" / "real" / "pkg").mkdir(parents=True)
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          real:
            package: "src/real/pkg"
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(MF1DeclaredSubsystemsExist().run(ctx))
    assert findings == []


def test_fires_on_malformed_subsystem_spec(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          weird: "not a mapping"
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(MF1DeclaredSubsystemsExist().run(ctx))
    assert len(findings) == 1
    assert "must be a mapping" in findings[0].message


def test_self_substrate_passes(tmp_path: Path) -> None:
    """Myco's self-canon declares real packages — verify MF1 stays silent
    when the declared paths exist relative to the substrate root."""
    (tmp_path / "src" / "myco" / "genesis").mkdir(parents=True)
    (tmp_path / "src" / "myco" / "ingestion").mkdir(parents=True)
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis:
            package: "src/myco/genesis/"
          ingestion:
            package: "src/myco/ingestion/"
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(MF1DeclaredSubsystemsExist().run(ctx))
    assert findings == []
