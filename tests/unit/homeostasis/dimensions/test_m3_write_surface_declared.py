"""Tests for ``M3WriteSurfaceDeclared``."""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.m3_write_surface_declared import (
    M3WriteSurfaceDeclared,
)


def _ctx_with_canon(tmp_path: Path, canon: str) -> MycoContext:
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    return MycoContext.for_testing(root=tmp_path)


def test_fires_when_write_surface_absent(seeded_substrate: Path) -> None:
    # The minimal fixture omits write_surface.
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(M3WriteSurfaceDeclared().run(ctx))
    assert len(findings) == 1


def test_fires_when_allowed_empty(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          write_surface:
            allowed: []
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(M3WriteSurfaceDeclared().run(ctx))
    assert any("empty" in f.message for f in findings)


def test_silent_with_declared_surface(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    assert list(M3WriteSurfaceDeclared().run(ctx)) == []
