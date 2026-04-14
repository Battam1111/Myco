"""Tests for ``myco.core.context``."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path

import pytest

from myco.core.context import MycoContext, Result
from myco.core.substrate import Substrate


def test_for_testing_from_root(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert isinstance(ctx.substrate, Substrate)
    assert ctx.substrate.canon.substrate_id == "test-substrate"


def test_for_testing_with_overrides(seeded_substrate: Path) -> None:
    fixed_now = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
    out, err = io.StringIO(), io.StringIO()
    ctx = MycoContext.for_testing(
        root=seeded_substrate,
        now=fixed_now,
        env={"FOO": "bar"},
        stdout=out,
        stderr=err,
    )
    assert ctx.now == fixed_now
    assert ctx.env == {"FOO": "bar"}
    assert ctx.stdout is out
    assert ctx.stderr is err


def test_for_testing_requires_root_or_substrate() -> None:
    with pytest.raises(ValueError, match="root= or substrate="):
        MycoContext.for_testing()


def test_context_is_frozen(seeded_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=seeded_substrate)
    with pytest.raises(Exception):
        ctx.now = datetime.now(timezone.utc)  # type: ignore[misc]


def test_result_defaults() -> None:
    r = Result()
    assert r.exit_code == 0
    assert r.findings == ()
    assert r.payload == {}


def test_result_is_frozen() -> None:
    r = Result(exit_code=1)
    with pytest.raises(Exception):
        r.exit_code = 2  # type: ignore[misc]
