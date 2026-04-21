"""Tests for ``RL1RulesReferenced``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.rl1_rules_referenced import RL1RulesReferenced


def test_all_rules_present_no_finding(seeded_substrate: Path) -> None:
    docs = seeded_substrate / "docs"
    docs.mkdir(exist_ok=True)
    # One file mentions R1-R7 all at once.
    (docs / "protocol.md").write_text(
        "rules: R1, R2, R3, R4, R5, R6, R7\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(RL1RulesReferenced().run(ctx)) == []


def test_missing_rule_fires(seeded_substrate: Path) -> None:
    docs = seeded_substrate / "docs"
    docs.mkdir(exist_ok=True)
    # Only R1-R6 referenced; R7 missing.
    (docs / "protocol.md").write_text(
        "rules: R1, R2, R3, R4, R5, R6\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(RL1RulesReferenced().run(ctx))
    ids = {f.message for f in findings}
    assert any("R7" in m for m in ids)
