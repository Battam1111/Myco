"""Tests for ``sh_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.identity_cluster import MycoContext
from myco.homeostasis.dimensions.shipped.sh_cluster import (
    SH1PackageVersionRef,
)

# =========================================================================
# test_sh1_package_version_ref — see git history for original per-dim file
# =========================================================================


def _ctx_with_canon(tmp_path: Path, canon: str) -> MycoContext:
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    return MycoContext.for_testing(root=tmp_path)


def test_silent_when_versioning_absent(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(SH1PackageVersionRef().run(ctx)) == []


def test_fires_when_declared_ref_missing(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        versioning:
          package_version_ref: "src/missing/__init__.py"
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
    findings = list(SH1PackageVersionRef().run(ctx))
    assert len(findings) == 1
    assert "src/missing/__init__.py" in findings[0].message


def test_silent_when_declared_ref_exists(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        versioning:
          package_version_ref: "pkg.py"
        """
    )
    (tmp_path / "pkg.py").write_text("__version__ = '0.0'\n", encoding="utf-8")
    ctx = _ctx_with_canon(tmp_path, canon)
    assert list(SH1PackageVersionRef().run(ctx)) == []
