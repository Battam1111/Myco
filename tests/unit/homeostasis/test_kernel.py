"""Tests for ``myco.homeostasis.kernel``."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Iterable

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding
from myco.homeostasis.kernel import run_immune
from myco.homeostasis.registry import DimensionRegistry, default_registry


class _Fires(Dimension):
    """Dimension that always fires a single CRITICAL mechanical finding."""

    id = "F1"
    category = Category.MECHANICAL
    default_severity = Severity.CRITICAL

    def run(self, ctx) -> Iterable[Finding]:  # noqa: ARG002
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message="fires",
        )


class _Quiet(Dimension):
    id = "Q1"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM

    def run(self, ctx) -> Iterable[Finding]:  # noqa: ARG002
        return ()


def _mk_ctx(root: Path) -> MycoContext:
    return MycoContext.for_testing(root=root)


def test_runs_all_by_default(seeded_substrate: Path) -> None:
    reg = DimensionRegistry()
    reg.register(_Fires())
    reg.register(_Quiet())
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, exit_on="critical")
    assert result.exit_code == 2
    assert len(result.findings) == 1
    assert result.findings[0].dimension_id == "F1"


def test_runs_selected_only(seeded_substrate: Path) -> None:
    reg = DimensionRegistry()
    reg.register(_Fires())
    reg.register(_Quiet())
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, selected=["Q1"], exit_on="critical")
    assert result.exit_code == 0
    assert result.findings == ()


def test_unknown_selected_raises_usage_error(seeded_substrate: Path) -> None:
    reg = DimensionRegistry()
    reg.register(_Fires())
    ctx = _mk_ctx(seeded_substrate)
    with pytest.raises(UsageError, match="unknown dimension"):
        run_immune(ctx, reg, selected=["NOPE"])


def test_exit_on_never_suppresses_critical(seeded_substrate: Path) -> None:
    reg = DimensionRegistry()
    reg.register(_Fires())
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, exit_on="never")
    assert result.exit_code == 0
    assert len(result.findings) == 1  # still reported


def test_skeleton_downgrade_applied_before_policy(tmp_path: Path) -> None:
    canon = textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0-alpha.1"
        identity:
          substrate_id: "skel"
          tags: []
          entry_point: "MYCO.md"
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          genesis: {package: "src/myco/genesis/"}
        lint:
          skeleton_downgrade:
            marker: ".myco_state/autoseeded.txt"
            affected_dimensions: ["F1"]
        """
    )
    (tmp_path / "_canon.yaml").write_text(canon, encoding="utf-8")
    (tmp_path / ".myco_state").mkdir()
    (tmp_path / ".myco_state" / "autoseeded.txt").write_text("", encoding="utf-8")

    reg = DimensionRegistry()
    reg.register(_Fires())
    ctx = _mk_ctx(tmp_path)

    # With exit_on="critical": F1's CRITICAL is downgraded to HIGH, which
    # the `critical` threshold does NOT trip → exit 0.
    r = run_immune(ctx, reg, exit_on="critical")
    assert r.exit_code == 0
    assert r.findings[0].severity is Severity.HIGH

    # With exit_on="high": HIGH trips → exit 1.
    r2 = run_immune(ctx, reg, exit_on="high")
    assert r2.exit_code == 1


def test_payload_records_context(seeded_substrate: Path) -> None:
    reg = DimensionRegistry()
    reg.register(_Fires())
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, exit_on="critical", fix=True)
    assert result.payload["dimensions_run"] == ("F1",)
    assert result.payload["exit_on"] == "critical"
    assert result.payload["fix"] is True
    assert result.payload["skeleton_downgrade_applied"] is False


def test_default_registry_runs_end_to_end(seeded_substrate: Path) -> None:
    reg = default_registry()
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, exit_on="critical")
    # The seeded fixture lacks an entry-point file and a write_surface
    # declaration, so M2 (HIGH) and M3 (MEDIUM) fire. Neither trips
    # the `critical` threshold → exit 0.
    assert result.exit_code == 0
    fired = {f.dimension_id for f in result.findings}
    assert "M2" in fired
    assert "M3" in fired
    # With exit_on="high", M2's HIGH trips → exit 1.
    result_high = run_immune(ctx, reg, exit_on="high")
    assert result_high.exit_code == 1
