"""Tests for ``myco.homeostasis.finding``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.severity import Severity
from myco.homeostasis.finding import Category, Finding


def test_category_values() -> None:
    assert Category.MECHANICAL.value == "mechanical"
    assert Category.SHIPPED.value == "shipped"
    assert Category.METABOLIC.value == "metabolic"
    assert Category.SEMANTIC.value == "semantic"


def test_category_from_name_case_insensitive() -> None:
    assert Category.from_name("MECHANICAL") is Category.MECHANICAL
    assert Category.from_name("Shipped") is Category.SHIPPED


def test_category_from_name_unknown() -> None:
    with pytest.raises(ValueError, match="unknown category"):
        Category.from_name("fatigue")


def test_finding_defaults() -> None:
    f = Finding(
        dimension_id="L0",
        category=Category.MECHANICAL,
        severity=Severity.LOW,
        message="ok",
    )
    assert f.path is None
    assert f.line is None
    assert f.fixable is False


def test_finding_from_path_converts() -> None:
    p = Path("/tmp/x.md")
    f = Finding.from_path(
        dimension_id="L0",
        category=Category.MECHANICAL,
        severity=Severity.HIGH,
        message="bad",
        path=p,
        line=42,
    )
    assert f.path == str(p)
    assert f.line == 42


def test_finding_from_path_none() -> None:
    f = Finding.from_path(
        dimension_id="L0",
        category=Category.MECHANICAL,
        severity=Severity.HIGH,
        message="bad",
    )
    assert f.path is None


def test_finding_is_frozen() -> None:
    f = Finding(
        dimension_id="L0",
        category=Category.MECHANICAL,
        severity=Severity.LOW,
        message="ok",
    )
    with pytest.raises(Exception):
        f.message = "changed"  # type: ignore[misc]
