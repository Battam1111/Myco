"""Regression test for v0.5.4 bug #2 (hunger count_by_kind)."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.ingestion.hunger import compose_hunger_report


def test_hunger_payload_includes_count_by_kind(
    genesis_substrate: Path,
) -> None:
    """The hunger payload's ``local_plugins`` block exposes
    ``count_by_kind`` with entries for every plugin category.
    Before v0.5.4 only a flat ``count`` shipped, contradicting the
    v0.5.3 CHANGELOG promise."""
    ctx = MycoContext.for_testing(root=genesis_substrate)
    report = compose_hunger_report(ctx)
    payload = report.as_dict()

    assert "local_plugins" in payload
    lp = payload["local_plugins"]
    assert "count" in lp
    assert "count_by_kind" in lp
    by_kind = lp["count_by_kind"]
    for key in ("dimension", "adapter", "schema_upgrader", "overlay_verb"):
        assert key in by_kind, f"missing {key!r} in count_by_kind"
        assert isinstance(by_kind[key], int)
    # Total should equal the sum.
    assert lp["count"] == sum(by_kind.values())
    # At least the built-in dimensions register.
    assert by_kind["dimension"] >= 1
