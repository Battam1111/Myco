"""Tests for ``LB1LivingBetsOverdue``.

Covers the matrix declared in
``src/myco/homeostasis/dimensions/semantic/lb1_living_bets_overdue.py``:

- Fresh substrates pre-v0.7 → silent.
- Substrate at v0.7.x with a v0.7.x audit → silent.
- Substrate at v0.7.x with no audit and no primordia/ → LOW.
- Substrate at v0.8.0 with a v0.7.x audit only → LOW (1 MAJOR overdue,
  0 minor accrued past the bump).
- Severity ramp at 5 minor → MEDIUM, at 10 minor → HIGH.
- Most-recent audit picked when multiple MAJORs exist.
- ``_landed/`` archive subtree still recognized.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.semantic.lb1_living_bets_overdue import (
    LB1LivingBetsOverdue,
)


def _write_canon(sub: Path, contract_version: str) -> None:
    """Write a minimal valid _canon.yaml at the given contract_version."""
    canon = textwrap.dedent(
        f"""\
        schema_version: "1"
        contract_version: "{contract_version}"
        identity:
          substrate_id: "test-substrate"
          entry_point: "MYCO.md"
        system:
          write_surface:
            allowed:
              - "_canon.yaml"
              - "docs/**"
          hard_contract:
            rule_count: 7
        subsystems:
          genesis:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        """
    )
    (sub / "_canon.yaml").write_text(canon, encoding="utf-8")
    (sub / "MYCO.md").write_text("# entry\n", encoding="utf-8")


def _write_audit(
    sub: Path,
    *,
    version_token: str,
    archived: bool = False,
    suffix: str = "2026-05-10",
) -> Path:
    """Place a Living Bets audit doc under docs/primordia/ (or its
    ``_landed/v0_X_x/`` archive when ``archived`` is True).

    ``version_token`` is the ``vN_M_P`` filename prefix; the resulting
    file matches the LB1 detection regex
    (``v.*_living_bets_audit_*.md``).
    """
    if archived:
        # Park the audit under the era-bucketed archive that v0.5.x
        # already uses (`_landed/v0_5_x/`, `_landed/v0_6_x/`, ...).
        # Parse the major.minor from the version_token.
        parts = version_token.lstrip("v").split("_")
        bucket = f"v{parts[0]}_{parts[1]}_x"
        target_dir = sub / "docs" / "primordia" / "_landed" / bucket
    else:
        target_dir = sub / "docs" / "primordia"
    target_dir.mkdir(parents=True, exist_ok=True)
    audit_path = target_dir / f"{version_token}_living_bets_audit_{suffix}.md"
    audit_path.write_text(
        f"# {version_token} Living Bets Re-Audit\n\nbody\n",
        encoding="utf-8",
    )
    return audit_path


# ===== silence cases =====


def test_lb1_silent_on_fresh_substrate_pre_v0_7(tmp_path: Path) -> None:
    """v0.6.0 substrate with no audit doc anywhere → 0 findings.

    The Living Bets concept landed at v0.5.6 and the v0.6.0 audit was
    implicit inside the unified-evolution craft, so a fresh v0.6.x
    substrate without a standalone audit file should not be punished.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.6.0")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


def test_lb1_silent_when_audit_matches_current_major(tmp_path: Path) -> None:
    """v0.7.5 substrate + v0_7_5_living_bets_audit_*.md → 0 findings."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


# ===== firing cases =====


def test_lb1_fires_low_on_v0_7_with_no_audit(tmp_path: Path) -> None:
    """v0.7.5 substrate + no docs/primordia/ at all → 1 LOW finding."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    # NB: no docs/primordia/ written.
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.dimension_id == "LB1"
    assert finding.category.value == "semantic"
    assert finding.severity is Severity.LOW
    assert "missing" in finding.message.lower()


def test_lb1_fires_low_on_v0_8_with_v0_7_audit_only(tmp_path: Path) -> None:
    """v0.8.0 substrate with only v0_7_*_living_bets_audit_*.md → 1 LOW.

    1 MAJOR overdue, < 2 minor accrued past the v0.7→v0.8 bump.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.8.0")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.dimension_id == "LB1"
    assert finding.severity is Severity.LOW
    assert "v0.7" in finding.message
    assert "v0.8" in finding.message


def test_lb1_ramps_to_medium_after_5_minor(tmp_path: Path) -> None:
    """v0.8.5 substrate with v0.7 audit → MEDIUM (5 minor past the bump)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.8.5")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.MEDIUM


def test_lb1_ramps_to_high_after_10_minor(tmp_path: Path) -> None:
    """v0.8.10 substrate with v0.7 audit → HIGH (10 minor past the bump)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.8.10")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH


def test_lb1_picks_most_recent_audit(tmp_path: Path) -> None:
    """Multiple audits: v0_6_0_*, v0_7_0_*, v0_7_5_* present at v0.7.5
    substrate → silent (the v0_7_5 audit is most recent and matches MAJOR)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    _write_audit(sub, version_token="v0_6_0")
    _write_audit(sub, version_token="v0_7_0")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


def test_lb1_handles_landed_archive(tmp_path: Path) -> None:
    """An audit doc moved to docs/primordia/_landed/v0_7_x/... is still
    recognized as the most-recent audit for that MAJOR."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    audit_path = _write_audit(sub, version_token="v0_7_5", archived=True)
    # Sanity: confirm the archive parking actually happened.
    assert "_landed" in audit_path.as_posix()
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


# ===== bonus parity tests =====


def test_lb1_ignores_unrelated_primordia_files(tmp_path: Path) -> None:
    """Only ``*living_bets_audit*.md`` filenames count; an unrelated
    craft of the same MAJOR does NOT satisfy the cadence."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    primordia = sub / "docs" / "primordia"
    primordia.mkdir(parents=True)
    # An ordinary craft, not an audit.
    (primordia / "v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md").write_text(
        "# omnibus craft\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.LOW


def test_lb1_silent_when_audit_is_forward_looking(tmp_path: Path) -> None:
    """A v1_0_*_living_bets_audit_*.md craft on a v0.7.x substrate is
    treated as forward-thinking; LB1 stays silent rather than punishing
    the substrate for having too much L0 hygiene."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    _write_audit(sub, version_token="v1_0_0")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []
