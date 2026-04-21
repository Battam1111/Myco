"""Tests for ``CS1ContractVersionSync``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.cs1_contract_version_sync import (
    CS1ContractVersionSync,
)


def test_synced_no_finding(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    # Fresh substrates are synced by germinate.
    assert list(CS1ContractVersionSync().run(ctx)) == []


def test_drift_fires_high(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    # ``Canon`` is a frozen dataclass; bypass via ``object.__setattr__``.
    object.__setattr__(ctx.substrate.canon, "contract_version", "v0.9.9")
    object.__setattr__(ctx.substrate.canon, "synced_contract_version", "v0.5.0")
    findings = list(CS1ContractVersionSync().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH
    assert "v0.9.9" in findings[0].message
    assert "v0.5.0" in findings[0].message
