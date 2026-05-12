"""Tests for ``myco.core.errors``."""

from __future__ import annotations

import pytest

from myco.core.errors import (
    CanonSchemaError,
    ContractError,
    MycoError,
    SubstrateNotFound,
    UsageError,
)


def test_exit_codes_are_all_three_or_greater() -> None:
    for exc_cls in (
        MycoError,
        ContractError,
        CanonSchemaError,
        SubstrateNotFound,
        UsageError,
    ):
        assert exc_cls.exit_code >= 3, exc_cls


def test_inheritance_tree() -> None:
    assert issubclass(ContractError, MycoError)
    assert issubclass(CanonSchemaError, ContractError)
    assert issubclass(SubstrateNotFound, MycoError)
    assert issubclass(UsageError, MycoError)


def test_raise_and_catch_preserves_type() -> None:
    with pytest.raises(ContractError) as exc_info:
        raise CanonSchemaError("bad schema")
    assert isinstance(exc_info.value, CanonSchemaError)
    # v0.5.8: CanonSchemaError exits 5 (canon-specific failure) to
    # let CI scripts distinguish it from generic operational
    # failures without string-matching stderr.
    assert exc_info.value.exit_code == 5


def test_differentiated_exit_codes() -> None:
    """v0.5.8: operational exit codes are now differentiated within
    the ``≥3`` contract band so downstream consumers can handle
    substrate-not-found and canon-schema errors separately from the
    generic bucket.
    """
    assert MycoError.exit_code == 3
    assert ContractError.exit_code == 3
    assert UsageError.exit_code == 3
    assert SubstrateNotFound.exit_code == 4
    assert CanonSchemaError.exit_code == 5


def test_myco_error_catches_everything() -> None:
    for exc_cls in (ContractError, CanonSchemaError, SubstrateNotFound, UsageError):
        with pytest.raises(MycoError):
            raise exc_cls("x")
