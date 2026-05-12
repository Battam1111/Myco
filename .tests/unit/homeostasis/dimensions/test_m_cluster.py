"""Tests for ``m_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.dimensions.mechanical.m_cluster import (
    M1CanonIdentityFields,
    M2EntryPointExists,
    M3WriteSurfaceDeclared,
    _slugify,
)
from myco.homeostasis.primitives_cluster import Category, Finding

# =========================================================================
# test_m1_canon_identity_fields — see git history for original per-dim file
# =========================================================================


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


# =========================================================================
# test_m1_m3_fix_paths — see git history for original per-dim file
# =========================================================================


def test_slugify_lowercases():
    assert _slugify("My Project") == "my-project"


def test_slugify_strips_dashes():
    assert _slugify("---hello---") == "hello"


def test_slugify_falls_back_to_unnamed():
    assert _slugify("!!!") == "unnamed"


def _seed_canon(tmp_path: Path, *, identity: str, system: str = "") -> Path:
    sys_block = system or "  hard_contract:\n    rule_count: 7\n"
    body = (
        'schema_version: "2"\n'
        'contract_version: "v0.6.0"\n'
        f"identity:\n{identity}"
        f"system:\n{sys_block}"
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


# =========================================================================
# test_m2_entry_point_exists — see git history for original per-dim file
# =========================================================================


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


def test_m2_is_fixable_class_attribute() -> None:
    """Dimension declares itself fixable at the class level."""
    assert M2EntryPointExists.fixable is True


def test_m2_fix_creates_missing_entry_point(seeded_substrate: Path) -> None:
    """Fix writes the minimal skeleton at the canon-declared path."""
    ctx = MycoContext.for_testing(root=seeded_substrate)
    dim = M2EntryPointExists()
    findings = list(dim.run(ctx))
    assert len(findings) == 1

    target = seeded_substrate / ctx.substrate.canon.entry_point
    assert not target.exists()

    outcome = dim.fix(ctx, findings[0])

    assert outcome["applied"] is True
    assert "created" in outcome["detail"].lower()
    assert target.is_file()
    body = target.read_text(encoding="utf-8")
    # The template interpolates substrate_id + an ISO timestamp.
    assert ctx.substrate.canon.substrate_id in body
    assert "Myco substrate" in body
    assert "_canon.yaml" in body
    # Timestamp is UTC, ends in Z.
    assert "Z" in body


def test_m2_fix_is_idempotent(seeded_substrate: Path) -> None:
    """A second --fix pass sees the existing file and is a no-op."""
    ctx = MycoContext.for_testing(root=seeded_substrate)
    dim = M2EntryPointExists()
    finding = next(iter(dim.run(ctx)))

    first = dim.fix(ctx, finding)
    assert first["applied"] is True

    target = seeded_substrate / ctx.substrate.canon.entry_point
    body_before = target.read_text(encoding="utf-8")

    # Re-run run() — file now exists, so no finding. But if someone
    # passed a stale finding in (as the kernel might on back-to-back
    # --fix), fix() must still refuse to clobber.
    second = dim.fix(ctx, finding)
    assert second["applied"] is False
    assert "exists" in second["detail"].lower()

    body_after = target.read_text(encoding="utf-8")
    assert body_before == body_after


def test_m2_fix_refuses_to_overwrite_nonempty(seeded_substrate: Path) -> None:
    """If the entry point somehow exists + is non-empty, fix() is a no-op.

    Covers the race where run() saw a missing file but by the time
    fix() fires something else has populated it. The fix refuses to
    overwrite rather than silently clobbering user content.
    """
    target = seeded_substrate / "MYCO.md"
    target.write_text("hand-authored content\n", encoding="utf-8")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    # Construct a stale finding (as if run() saw the missing file
    # earlier in the same kernel pass).
    stale = Finding(
        dimension_id="M2",
        category=Category.MECHANICAL,
        severity=Severity.HIGH,
        message="stale",
        path="MYCO.md",
    )
    outcome = M2EntryPointExists().fix(ctx, stale)
    assert outcome["applied"] is False
    assert "exists" in outcome["detail"].lower()
    assert target.read_text(encoding="utf-8") == "hand-authored content\n"


def test_m2_fix_refuses_outside_write_surface(tmp_path: Path) -> None:
    """Kernel safety guard skips fix when target is outside write_surface.

    This drives the kernel-level guard (not the dimension itself):
    when ``canon.system.write_surface.allowed`` is declared and does
    NOT include the entry-point path, ``run_immune(fix=True)``
    records an ``error: "outside write surface"`` without calling
    ``fix()``.
    """
    from myco.homeostasis.kernel import run_immune
    from myco.homeostasis.primitives_cluster import DimensionRegistry

    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.5.5"
        identity:
          substrate_id: "locked"
          entry_point: "MYCO.md"
        system:
          write_surface:
            allowed:
              - "docs/**"
          hard_contract: {rule_count: 7}
        subsystems:
          germination: {package: "src/myco/germination/"}
        """
    )
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    ctx = MycoContext.for_testing(root=tmp_path)

    reg = DimensionRegistry()
    reg.register(M2EntryPointExists())
    result = run_immune(ctx, reg, exit_on="never", fix=True)

    fixes = result.payload["fixes"]
    assert len(fixes) == 1
    assert fixes[0]["dimension_id"] == "M2"
    assert fixes[0]["applied"] is False
    assert fixes[0]["error"] == "outside write surface"
    # And the file was definitely not created.
    assert not (tmp_path / "MYCO.md").exists()


# =========================================================================
# test_m3_write_surface_declared — see git history for original per-dim file
# =========================================================================


def _ctx_with_canon(tmp_path: Path, canon: str) -> MycoContext:
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    return MycoContext.for_testing(root=tmp_path)


def test_fires_when_write_surface_absent(tmp_path: Path) -> None:
    # v0.5.8: the shared ``minimal_canon_text`` fixture now declares a
    # write_surface so other write-verb tests work out of the box.
    # This test specifically exercises the "surface absent" path, so
    # we build our own narrow canon without write_surface.
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0"
        identity: {substrate_id: "x", entry_point: "MYCO.md"}
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        """
    )
    ctx = _ctx_with_canon(tmp_path, canon)
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
