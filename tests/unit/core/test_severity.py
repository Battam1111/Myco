"""Tests for ``myco.core.severity``."""

from __future__ import annotations

import pytest

from myco.core.severity import Severity, downgrade


def test_values_are_1_to_4() -> None:
    assert int(Severity.LOW) == 1
    assert int(Severity.MEDIUM) == 2
    assert int(Severity.HIGH) == 3
    assert int(Severity.CRITICAL) == 4


def test_ordering_is_strict() -> None:
    assert Severity.LOW < Severity.MEDIUM < Severity.HIGH < Severity.CRITICAL


def test_from_name_is_case_insensitive() -> None:
    assert Severity.from_name("critical") is Severity.CRITICAL
    assert Severity.from_name("HIGH") is Severity.HIGH
    assert Severity.from_name("Medium") is Severity.MEDIUM


def test_from_name_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown severity"):
        Severity.from_name("nope")


def test_label_is_lowercase() -> None:
    assert Severity.CRITICAL.label() == "critical"
    assert Severity.LOW.label() == "low"


def test_downgrade_caps_at_ceiling() -> None:
    assert downgrade(Severity.CRITICAL, ceiling=Severity.HIGH) is Severity.HIGH
    assert downgrade(Severity.HIGH, ceiling=Severity.HIGH) is Severity.HIGH


def test_downgrade_noop_below_ceiling() -> None:
    assert downgrade(Severity.MEDIUM, ceiling=Severity.HIGH) is Severity.MEDIUM
    assert downgrade(Severity.LOW, ceiling=Severity.CRITICAL) is Severity.LOW
