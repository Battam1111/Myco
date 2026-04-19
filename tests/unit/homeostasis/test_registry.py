"""Tests for ``myco.homeostasis.registry``."""

from __future__ import annotations

import warnings
from collections.abc import Iterable

import pytest

from myco.core.errors import ContractError
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.dimensions import (
    _BUILT_IN,
    discover_dimension_classes,
)
from myco.homeostasis.finding import Category, Finding
from myco.homeostasis.registry import DimensionRegistry, default_registry


class _Dim(Dimension):
    id = "T1"
    category = Category.MECHANICAL
    default_severity = Severity.LOW

    def run(self, ctx) -> Iterable[Finding]:
        return ()


class _Dim2(Dimension):
    id = "T2"
    category = Category.SEMANTIC
    default_severity = Severity.HIGH

    def run(self, ctx) -> Iterable[Finding]:
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


def test_default_registry_includes_every_built_in() -> None:
    """The registry contains every dimension declared in pyproject's
    entry-points table (or in the dev fallback ``_BUILT_IN``). Loosened
    from the v0.4 hardcoded 8-id assertion so third-party plugins can
    freely *add* dimensions without breaking this test; the reverse
    direction (no built-in missing) stays tight."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        reg = default_registry()
    for cls in _BUILT_IN:
        assert reg.has(cls.id), f"built-in dimension {cls.id} missing"
    # L0 smoke dim was removed at Stage B.8.
    assert not reg.has("L0")


def test_discover_dimension_classes_returns_every_built_in() -> None:
    """Whichever path discovery takes (entry-points or fallback), it
    must surface every ``_BUILT_IN`` class."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        discovered = discover_dimension_classes()
    found_ids = {cls.id for cls in discovered}
    for cls in _BUILT_IN:
        assert cls.id in found_ids, f"{cls.id} not discovered"


def test_discover_dimension_classes_fallback_warns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When entry-points returns empty, the fallback path must fire a
    DeprecationWarning so dev-checkout users know to ``pip install -e .``."""
    import myco.homeostasis.dimensions as _dims

    def _empty_entry_points(group: str):
        return ()

    monkeypatch.setattr(_dims, "entry_points", _empty_entry_points)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = _dims.discover_dimension_classes()

    # Fallback must still yield the built-ins (they come from the
    # `_BUILT_IN` tuple when entry-points is empty).
    assert len(result) == len(_dims._BUILT_IN)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
        "expected DeprecationWarning on fallback path"
    )
