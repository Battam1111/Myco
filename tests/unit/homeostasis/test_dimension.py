"""Tests for ``myco.homeostasis.dimension``."""

from __future__ import annotations

from typing import Iterable

import pytest

from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding


def test_cannot_instantiate_abstract() -> None:
    with pytest.raises(TypeError):
        Dimension()  # type: ignore[abstract]


def test_subclass_must_implement_run() -> None:
    class Incomplete(Dimension):
        id = "X"
        category = Category.MECHANICAL
        default_severity = Severity.LOW

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_concrete_subclass_works() -> None:
    class Good(Dimension):
        """Explain text."""

        id = "G1"
        category = Category.SEMANTIC
        default_severity = Severity.MEDIUM

        def run(self, ctx) -> Iterable[Finding]:  # noqa: ARG002
            return ()

    d = Good()
    assert d.id == "G1"
    assert d.category is Category.SEMANTIC
    assert d.explain == "Explain text."
