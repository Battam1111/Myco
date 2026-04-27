"""Coverage tests for M1 / M3 fix paths."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.mechanical.m1_canon_identity_fields import (
    M1CanonIdentityFields,
    _slugify,
)
from myco.homeostasis.dimensions.mechanical.m3_write_surface_declared import (
    M3WriteSurfaceDeclared,
)
from myco.homeostasis.finding import Category, Finding


# ---------- M1 ----------


def test_slugify_lowercases():
    assert _slugify("My Project") == "my-project"


def test_slugify_strips_dashes():
    assert _slugify("---hello---") == "hello"


def test_slugify_falls_back_to_unnamed():
    assert _slugify("!!!") == "unnamed"


def _seed_canon(tmp_path: Path, *, identity: str, system: str = "") -> Path:
    body = (
        'schema_version: "2"\n'
        'contract_version: "v0.6.0"\n'
        f"identity:\n{identity}"
        f"system:\n{system or '  hard_contract:\n    rule_count: 7\n'}"
        "  write_surface:\n    allowed: ['_canon.yaml']\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n"
    )
    path = tmp_path / "_canon.yaml"
    path.write_text(body, encoding="utf-8")
    (tmp_path / "MYCO.md").write_text("# x", encoding="utf-8")
    return path


def test_m1_no_finding_when_identity_complete(tmp_path: Path):
    _seed_canon(
        tmp_path,
        identity='  substrate_id: "x"\n  entry_point: "MYCO.md"\n',
    )
    ctx = MycoContext.for_testing(root=tmp_path)
    findings = list(M1CanonIdentityFields().run(ctx))
    assert findings == []


def test_m1_emits_when_substrate_id_missing(tmp_path: Path):
    _seed_canon(tmp_path, identity='  entry_point: "MYCO.md"\n  substrate_id: ""\n')
    ctx = MycoContext.for_testing(root=tmp_path)
    findings = list(M1CanonIdentityFields().run(ctx))
    assert any("substrate_id" in f.message for f in findings)


def test_m1_emits_when_entry_point_missing(tmp_path: Path):
    _seed_canon(tmp_path, identity='  substrate_id: "x"\n  entry_point: ""\n')
    ctx = MycoContext.for_testing(root=tmp_path)
    findings = list(M1CanonIdentityFields().run(ctx))
    assert any("entry_point" in f.message for f in findings)


def test_m1_fix_when_canon_missing(tmp_path: Path):
    _seed_canon(
        tmp_path,
        identity='  substrate_id: "x"\n  entry_point: "MYCO.md"\n',
    )
    ctx = MycoContext.for_testing(root=tmp_path)
    # Now delete the canon
    (tmp_path / "_canon.yaml").unlink()
    finding = Finding(
        dimension_id="M1",
        category=Category.MECHANICAL,
        severity=ctx.substrate.canon.lint.get("default_severity", "HIGH"),  # type: ignore[arg-type]
        message="x",
        path="_canon.yaml",
    )
    out = M1CanonIdentityFields().fix(ctx, finding)
    assert out["applied"] is False
    assert "missing" in out["detail"]


def test_m1_fix_idempotent_when_already_set(tmp_path: Path):
    _seed_canon(
        tmp_path,
        identity='  substrate_id: "filled"\n  entry_point: "MYCO.md"\n',
    )
    ctx = MycoContext.for_testing(root=tmp_path)
    finding = Finding(
        dimension_id="M1",
        category=Category.MECHANICAL,
        severity="HIGH",  # type: ignore[arg-type]
        message="x",
        path="_canon.yaml",
    )
    out = M1CanonIdentityFields().fix(ctx, finding)
    assert out["applied"] is False
    # Either "already satisfied" or "manual edit required" — both are no-ops.
    assert any(s in out["detail"] for s in ("already satisfied", "manual edit"))


# ---------- M3 ----------


def test_m3_emits_when_write_surface_missing(tmp_path: Path):
    body = (
        'schema_version: "2"\n'
        'contract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "MYCO.md"\n'
        "system:\n  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n"
    )
    (tmp_path / "_canon.yaml").write_text(body, encoding="utf-8")
    (tmp_path / "MYCO.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=tmp_path)
    findings = list(M3WriteSurfaceDeclared().run(ctx))
    assert any("write_surface" in f.message for f in findings)


def test_m3_emits_when_allowed_empty(tmp_path: Path):
    body = (
        'schema_version: "2"\n'
        'contract_version: "v0.6.0"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "MYCO.md"\n'
        "system:\n  hard_contract:\n    rule_count: 7\n"
        "  write_surface:\n    allowed: []\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n"
    )
    (tmp_path / "_canon.yaml").write_text(body, encoding="utf-8")
    (tmp_path / "MYCO.md").write_text("# x", encoding="utf-8")
    ctx = MycoContext.for_testing(root=tmp_path)
    findings = list(M3WriteSurfaceDeclared().run(ctx))
    assert any("empty" in f.message or "list" in f.message for f in findings)


def test_m3_fix_returns_advisory(tmp_path: Path):
    _seed_canon(
        tmp_path,
        identity='  substrate_id: "x"\n  entry_point: "MYCO.md"\n',
    )
    ctx = MycoContext.for_testing(root=tmp_path)
    out = M3WriteSurfaceDeclared().fix(
        ctx,
        Finding(
            dimension_id="M3",
            category=Category.MECHANICAL,
            severity="MEDIUM",  # type: ignore[arg-type]
            message="x",
            path="_canon.yaml",
        ),
    )
    assert out["applied"] is False
    assert "advisory" in out["detail"]
