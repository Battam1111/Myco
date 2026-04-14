"""Tests for ``myco.homeostasis.registry``."""

from __future__ import annotations

from typing import Iterable

import pytest

from myco.core.errors import ContractError
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding
from myco.homeostasis.registry import DimensionRegistry, default_registry


class _Dim(Dimension):
    id = "T1"
    category = Category.MECHANICAL
    default_severity = Severity.LOW

    def run(self, ctx) -> Iterable[Finding]:  # noqa: ARG002
        return ()


class _Dim2(Dimension):
    id = "T2"
    category = Category.SEMANTIC
    default_severity = Severity.HIGH

    def run(self, ctx) -> Iterable[Finding]:  # noqa: ARG002
        return ()


def test_register_get() -> None:
    reg = DimensionRegistry()
    d = _Dim()
    reg.register(d)
    assert reg.get("T1") is d
    assert reg.has("T1")
    assert not reg.has("T2")
    assert len(reg) == 1


def test_duplicate_registration_raises() -> None:
    reg = DimensionRegistry()
    reg.register(_Dim())
    with pytest.raises(ContractError, match="duplicate"):
        reg.register(_Dim())


def test_register_rejects_non_dimension() -> None:
    reg = DimensionRegistry()
    with pytest.raises(TypeError):
        reg.register(object())  # type: ignore[arg-type]


def test_all_sorted_by_id() -> None:
    reg = DimensionRegistry()
    reg.register(_Dim2())
    reg.register(_Dim())
    ids = [d.id for d in reg.all()]
    assert ids == ["T1", "T2"]


def test_default_registry_includes_smoke_dim() -> None:
    reg = default_registry()
    assert reg.has("L0")
