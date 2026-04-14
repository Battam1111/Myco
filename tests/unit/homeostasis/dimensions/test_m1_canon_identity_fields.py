"""Tests for ``M1CanonIdentityFields``."""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.m1_canon_identity_fields import (
    M1CanonIdentityFields,
)


def _ctx_with_canon(tmp_path: Path, canon: str) -> MycoContext:
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    return MycoContext.for_testing(root=tmp_path)


def test_clean_canon_no_findings(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(M1CanonIdentityFields().run(ctx)) == []


def test_missing_substrate_id_fires(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0"
        identity:
          substrate_id: ""
          entry_point: "MYCO.md"
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(M1CanonIdentityFields().run(ctx))
    assert any("substrate_id" in f.message for f in findings)


def test_missing_entry_point_fires(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0"
        identity:
          substrate_id: "x"
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(M1CanonIdentityFields().run(ctx))
    assert any("entry_point" in f.message for f in findings)
