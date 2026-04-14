"""Tests for ``myco.homeostasis.exit_policy``."""

from __future__ import annotations

import pytest

from myco.core.errors import ContractError
from myco.core.severity import Severity
from myco.homeostasis.exit_policy import ExitPolicy, Threshold, parse_exit_policy
from myco.homeostasis.finding import Category, Finding


# --- parsing ---------------------------------------------------------------


def test_parse_global_critical() -> None:
    p = parse_exit_policy("critical")
    assert all(t is Threshold.CRITICAL for t in p.thresholds.values())


def test_parse_global_high() -> None:
    p = parse_exit_policy("high")
    assert all(t is Threshold.HIGH for t in p.thresholds.values())


def test_parse_global_never() -> None:
    p = parse_exit_policy("never")
    assert all(t is Threshold.NEVER for t in p.thresholds.values())


def test_parse_per_cat_list_defaults_unnamed_to_critical() -> None:
    p = parse_exit_policy("mechanical:never,semantic:high")
    assert p.thresholds[Category.MECHANICAL] is Threshold.NEVER
    assert p.thresholds[Category.SEMANTIC] is Threshold.HIGH
    assert p.thresholds[Category.SHIPPED] is Threshold.CRITICAL
    assert p.thresholds[Category.METABOLIC] is Threshold.CRITICAL


def test_parse_canonical_ci_gate() -> None:
    p = parse_exit_policy(
        "mechanical:critical,shipped:critical,metabolic:never,semantic:never"
    )
    assert p.thresholds[Category.MECHANICAL] is Threshold.CRITICAL
    assert p.thresholds[Category.METABOLIC] is Threshold.NEVER


def test_parse_empty_raises() -> None:
    with pytest.raises(ContractError, match="empty"):
        parse_exit_policy("")


def test_parse_unknown_global_raises() -> None:
    with pytest.raises(ContractError, match="unknown global"):
        parse_exit_policy("foobar")


def test_parse_unknown_category_raises() -> None:
    with pytest.raises(ContractError, match="unknown category"):
        parse_exit_policy("bogus:critical")


def test_parse_unknown_threshold_raises() -> None:
    with pytest.raises(ContractError, match="unknown threshold"):
        parse_exit_policy("mechanical:fatal")


def test_parse_duplicate_category_raises() -> None:
    with pytest.raises(ContractError, match="specified twice"):
        parse_exit_policy("mechanical:critical,mechanical:never")


def test_parse_per_cat_missing_colon_raises() -> None:
    # A list-form spec must have a colon in every piece. Supplying a
    # bare keyword inside a per-cat list is ambiguous and rejected.
    with pytest.raises(ContractError, match="must contain"):
        parse_exit_policy("mechanical:critical,high")


# --- compute ---------------------------------------------------------------


def _mk_finding(cat: Category, sev: Severity) -> Finding:
    return Finding(
        dimension_id="X",
        category=cat,
        severity=sev,
        message="x",
    )


def test_compute_clean_returns_zero() -> None:
    p = parse_exit_policy("critical")
    assert p.compute([]) == 0


def test_compute_critical_in_cat_critical_returns_two() -> None:
    p = parse_exit_policy("critical")
    assert p.compute([_mk_finding(Category.MECHANICAL, Severity.CRITICAL)]) == 2


def test_compute_high_in_cat_critical_returns_zero() -> None:
    # threshold `critical` means only CRITICAL trips.
    p = parse_exit_policy("critical")
    assert p.compute([_mk_finding(Category.MECHANICAL, Severity.HIGH)]) == 0


def test_compute_high_in_cat_high_returns_one() -> None:
    p = parse_exit_policy("high")
    assert p.compute([_mk_finding(Category.MECHANICAL, Severity.HIGH)]) == 1


def test_compute_critical_in_cat_high_returns_two() -> None:
    p = parse_exit_policy("high")
    assert p.compute([_mk_finding(Category.MECHANICAL, Severity.CRITICAL)]) == 2


def test_compute_never_suppresses_everything() -> None:
    p = parse_exit_policy("never")
    assert (
        p.compute([_mk_finding(Category.MECHANICAL, Severity.CRITICAL)])
        == 0
    )


def test_compute_worst_wins() -> None:
    p = parse_exit_policy("high")
    findings = [
        _mk_finding(Category.MECHANICAL, Severity.HIGH),
        _mk_finding(Category.SEMANTIC, Severity.CRITICAL),
    ]
    assert p.compute(findings) == 2


def test_compute_per_cat_isolation() -> None:
    # metabolic:never, mechanical:critical
    p = parse_exit_policy("mechanical:critical,metabolic:never")
    findings = [
        _mk_finding(Category.METABOLIC, Severity.CRITICAL),  # suppressed
        _mk_finding(Category.MECHANICAL, Severity.CRITICAL),  # counts → 2
    ]
    assert p.compute(findings) == 2

    findings2 = [
        _mk_finding(Category.METABOLIC, Severity.CRITICAL),  # suppressed
    ]
    assert p.compute(findings2) == 0


def test_compute_medium_never_trips() -> None:
    p = parse_exit_policy("high")
    assert (
        p.compute([_mk_finding(Category.MECHANICAL, Severity.MEDIUM)])
        == 0
    )
