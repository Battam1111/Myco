"""Tests for ``RL1RulesReferenced``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.homeostasis.dimensions.rl1_rules_referenced import RL1RulesReferenced


def _seed_protocol(substrate: Path, body: str) -> None:
    """v0.5.10: RL1 now skips when ``docs/architecture/L1_CONTRACT/protocol.md``
    is absent, so tests must materialize it at the canonical path
    before expecting RL1 to fire."""
    proto_dir = substrate / "docs" / "architecture" / "L1_CONTRACT"
    proto_dir.mkdir(parents=True, exist_ok=True)
    (proto_dir / "protocol.md").write_text(body, encoding="utf-8")


def test_all_rules_present_no_finding(seeded_substrate: Path) -> None:
    _seed_protocol(seeded_substrate, "rules: R1, R2, R3, R4, R5, R6, R7\n")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(RL1RulesReferenced().run(ctx)) == []


def test_missing_rule_fires(seeded_substrate: Path) -> None:
    # Only R1-R6 referenced; R7 missing.
    _seed_protocol(seeded_substrate, "rules: R1, R2, R3, R4, R5, R6\n")
    ctx = MycoContext.for_testing(root=seeded_substrate)
    findings = list(RL1RulesReferenced().run(ctx))
    ids = {f.message for f in findings}
    assert any("R7" in m for m in ids)


def test_skips_silently_when_protocol_absent(seeded_substrate: Path) -> None:
    """v0.5.10: a substrate without ``docs/architecture/L1_CONTRACT/
    protocol.md`` does not ship L1 doctrine — RL1's check doesn't
    apply and it returns no findings. Previously this fired 7 LOW
    findings on every fresh germinate."""
    ctx = MycoContext.for_testing(root=seeded_substrate)
    assert list(RL1RulesReferenced().run(ctx)) == []
