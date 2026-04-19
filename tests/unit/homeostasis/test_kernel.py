"""Tests for ``myco.homeostasis.kernel``."""

from __future__ import annotations

import textwrap
from collections.abc import Iterable
from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.errors import UsageError
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding
from myco.homeostasis.kernel import (
    run_cli,
    run_explain,
    run_immune,
    run_list,
)
from myco.homeostasis.registry import DimensionRegistry, default_registry


class _Fires(Dimension):
    """Dimension that always fires a single CRITICAL mechanical finding."""

    id = "F1"
    category = Category.MECHANICAL
    default_severity = Severity.CRITICAL

    def run(self, ctx) -> Iterable[Finding]:
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

    def run(self, ctx) -> Iterable[Finding]:
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


def test_run_list_enumerates_without_running(seeded_substrate: Path) -> None:
    """``--list`` returns the dimension catalog, runs no dimensions."""
    reg = DimensionRegistry()
    reg.register(_Fires())
    reg.register(_Quiet())
    r = run_list(reg)
    assert r.exit_code == 0
    assert r.payload["mode"] == "list"
    assert r.payload["count"] == 2
    ids = {d["id"] for d in r.payload["dimensions"]}
    assert ids == {"F1", "Q1"}
    # Entry shape
    f1 = next(d for d in r.payload["dimensions"] if d["id"] == "F1")
    assert f1["category"] == "mechanical"
    assert f1["default_severity"] == "critical"


def test_run_explain_returns_prose(seeded_substrate: Path) -> None:
    reg = DimensionRegistry()
    reg.register(_Fires())
    r = run_explain(reg, "F1")
    assert r.exit_code == 0
    assert r.payload["mode"] == "explain"
    assert r.payload["id"] == "F1"
    assert r.payload["category"] == "mechanical"
    assert r.payload["default_severity"] == "critical"
    assert "always fires" in r.payload["explain"].lower()


def test_run_explain_unknown_dim_raises(seeded_substrate: Path) -> None:
    reg = DimensionRegistry()
    reg.register(_Fires())
    with pytest.raises(UsageError, match="unknown dimension"):
        run_explain(reg, "NOPE")


def test_run_cli_dispatches_list(seeded_substrate: Path) -> None:
    ctx = _mk_ctx(seeded_substrate)
    r = run_cli({"list": True}, ctx=ctx)
    assert r.payload["mode"] == "list"
    assert r.payload["count"] >= 1


def test_run_cli_dispatches_explain(seeded_substrate: Path) -> None:
    ctx = _mk_ctx(seeded_substrate)
    r = run_cli({"explain": "M1"}, ctx=ctx)
    assert r.payload["mode"] == "explain"
    assert r.payload["id"] == "M1"


def test_run_cli_list_and_explain_are_mutex(seeded_substrate: Path) -> None:
    ctx = _mk_ctx(seeded_substrate)
    with pytest.raises(UsageError, match="mutually exclusive"):
        run_cli({"list": True, "explain": "M1"}, ctx=ctx)


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


# ---------------------------------------------------------------------------
# v0.5.5 MAJOR-A — kernel-level fix dispatch
# ---------------------------------------------------------------------------


class _FixableProbe(Dimension):
    """Test dimension that always fires and records every fix() call."""

    id = "FIXPROBE"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable = True

    def __init__(self) -> None:
        self.calls: list[tuple[object, Finding]] = []
        self.return_applied = True

    def run(self, ctx) -> Iterable[Finding]:
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message="probe fires",
            path="probe.md",
        )

    def fix(self, ctx, finding):  # type: ignore[override]
        self.calls.append((ctx, finding))
        return {
            "applied": self.return_applied,
            "detail": "probe-fixed",
            "probe_path": finding.path,
        }


def test_fix_results_appear_in_payload(seeded_substrate: Path) -> None:
    """With fix=True, payload["fixes"] is always present."""
    reg = DimensionRegistry()
    reg.register(_Fires())  # non-fixable; produces one finding
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, exit_on="never", fix=True)
    assert "fixes" in result.payload
    # _Fires is not fixable, so the list is empty.
    assert result.payload["fixes"] == []

    # Without fix=True, the "fixes" key is absent entirely (no need
    # to confuse consumers with an empty list they never asked for).
    result2 = run_immune(ctx, reg, exit_on="never", fix=False)
    assert "fixes" not in result2.payload


def test_run_immune_with_fix_invokes_fixable_dimensions(
    seeded_substrate: Path,
) -> None:
    """fix=True dispatches to dim.fix(); non-fixable dims stay untouched."""
    reg = DimensionRegistry()
    probe = _FixableProbe()
    non_fixable = _Fires()
    reg.register(probe)
    reg.register(non_fixable)
    ctx = _mk_ctx(seeded_substrate)

    # fix=False → probe is never called.
    run_immune(ctx, reg, exit_on="never", fix=False)
    assert probe.calls == []

    # fix=True → probe called exactly once, and the payload has both
    # findings but only one fix entry (for the fixable dim).
    result = run_immune(ctx, reg, exit_on="never", fix=True)
    assert len(probe.calls) == 1
    assert len(result.payload["fixes"]) == 1
    entry = result.payload["fixes"][0]
    assert entry["dimension_id"] == "FIXPROBE"
    assert entry["applied"] is True
    assert entry["detail"] == "probe-fixed"
    # Structured extras from the fix() return flow through.
    assert entry["probe_path"] == "probe.md"
    assert entry["path"] == "probe.md"


def test_run_immune_without_fix_does_not_invoke_fixable_dim(
    seeded_substrate: Path,
) -> None:
    """fix=False must NOT call dim.fix() even on fixable dimensions."""
    reg = DimensionRegistry()
    probe = _FixableProbe()
    reg.register(probe)
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, exit_on="never", fix=False)
    assert probe.calls == []
    # And the payload has no fixes key.
    assert "fixes" not in result.payload
    # But the finding was still emitted.
    assert len(result.findings) == 1


def test_run_immune_fix_captures_raised_exceptions(
    seeded_substrate: Path,
) -> None:
    """A fix() that raises records an error entry; kernel does not crash."""

    class _Explodes(Dimension):
        """Fixable dimension whose fix() always raises."""

        id = "BOOM"
        category = Category.MECHANICAL
        default_severity = Severity.HIGH
        fixable = True

        def run(self, ctx) -> Iterable[Finding]:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message="x",
                path="anywhere.md",
            )

        def fix(self, ctx, finding):  # type: ignore[override]
            raise RuntimeError("kaboom")

    reg = DimensionRegistry()
    reg.register(_Explodes())
    ctx = _mk_ctx(seeded_substrate)
    result = run_immune(ctx, reg, exit_on="never", fix=True)
    assert len(result.payload["fixes"]) == 1
    entry = result.payload["fixes"][0]
    assert entry["dimension_id"] == "BOOM"
    assert entry["applied"] is False
    assert "RuntimeError" in entry["error"]
    assert "kaboom" in entry["error"]
