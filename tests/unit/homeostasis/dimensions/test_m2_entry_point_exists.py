"""Tests for ``M2EntryPointExists``."""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.m2_entry_point_exists import M2EntryPointExists
from myco.homeostasis.finding import Category, Finding
from myco.core.severity import Severity


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


# ---------------------------------------------------------------------------
# v0.5.5 MAJOR-A — fixable seam
# ---------------------------------------------------------------------------


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
    from myco.homeostasis.registry import DimensionRegistry

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
