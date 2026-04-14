"""Tests for the smoke dimension ``L0KernelAlive``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.l0_kernel_alive import L0KernelAlive
from myco.homeostasis.finding import Category


def test_smoke_emits_one_low_finding(seeded_substrate: Path) -> None:
    dim = L0KernelAlive()
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(dim.run(ctx))
    assert len(findings) == 1
    f = findings[0]
    assert f.dimension_id == "L0"
    assert f.category is Category.MECHANICAL
    assert f.severity is Severity.LOW


def test_smoke_has_explain() -> None:
    assert L0KernelAlive().explain  # truthy, non-empty
