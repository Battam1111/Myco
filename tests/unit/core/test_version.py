"""Tests for ``myco.core.version``."""

from __future__ import annotations

import pytest

from myco.core.version import ContractVersion, PackageVersion


def test_package_parse_final() -> None:
    v = PackageVersion.parse("0.4.0")
    assert v.major == 0 and v.minor == 4 and v.patch == 0


def test_package_parse_dev_no_number() -> None:
    v = PackageVersion.parse("0.4.0.dev")
    assert v.major == 0 and v.minor == 4


def test_package_parse_dev_numbered() -> None:
    v = PackageVersion.parse("0.4.0.dev7")
    assert v.major == 0 and v.minor == 4 and v.patch == 0


def test_package_ordering_dev_before_final() -> None:
    assert PackageVersion.parse("0.4.0.dev") < PackageVersion.parse("0.4.0")
    assert PackageVersion.parse("0.4.0.dev0") < PackageVersion.parse("0.4.0")
    assert PackageVersion.parse("0.4.0") < PackageVersion.parse("0.4.1")
    assert PackageVersion.parse("0.3.9") < PackageVersion.parse("0.4.0.dev")


def test_package_ordering_within_dev_track() -> None:
    assert PackageVersion.parse("0.4.0.dev") < PackageVersion.parse("0.4.0.dev0")
    assert PackageVersion.parse("0.4.0.dev0") < PackageVersion.parse("0.4.0.dev1")


def test_package_parse_invalid() -> None:
    with pytest.raises(ValueError):
        PackageVersion.parse("0.4")
    with pytest.raises(ValueError):
        PackageVersion.parse("0.4.0-beta")
    with pytest.raises(ValueError):
        PackageVersion.parse("v0.4.0")


def test_contract_parse_with_and_without_v() -> None:
    a = ContractVersion.parse("v0.4.0")
    b = ContractVersion.parse("0.4.0")
    assert (a.major, a.minor, a.patch) == (b.major, b.minor, b.patch)


def test_contract_parse_pre_release_tag() -> None:
    v = ContractVersion.parse("v0.4.0-alpha.1")
    assert (v.major, v.minor, v.patch) == (0, 4, 0)


def test_contract_ordering_tag_before_final() -> None:
    assert ContractVersion.parse("v0.4.0-alpha.1") < ContractVersion.parse("v0.4.0")
    assert ContractVersion.parse("v0.4.0-alpha.1") < ContractVersion.parse(
        "v0.4.0-alpha.2"
    )
    assert ContractVersion.parse("v0.4.0-alpha.2") < ContractVersion.parse(
        "v0.4.0-beta.1"
    )
    assert ContractVersion.parse("v0.4.0") < ContractVersion.parse("v0.4.1")


def test_contract_parse_invalid() -> None:
    with pytest.raises(ValueError):
        ContractVersion.parse("0.4")
    with pytest.raises(ValueError):
        ContractVersion.parse("foo")
