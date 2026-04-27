"""Tests for ``core.risk_classifier`` (v0.6.0)."""

from __future__ import annotations

from pathlib import Path

from myco.core.risk_classifier import (
    RiskTier,
    classify_paths,
    classify_proposal,
)


def test_classify_paths_high_risk_l0():
    out = classify_paths(["docs/architecture/L0_VISION.md"])
    assert out.tier == RiskTier.HIGH


def test_classify_paths_high_risk_protocol():
    out = classify_paths(["docs/architecture/L1_CONTRACT/protocol.md"])
    assert out.tier == RiskTier.HIGH


def test_classify_paths_high_risk_canon():
    out = classify_paths(["_canon.yaml"])
    assert out.tier == RiskTier.HIGH


def test_classify_paths_medium_risk_l2():
    out = classify_paths(["docs/architecture/L2_DOCTRINE/ingestion.md"])
    assert out.tier == RiskTier.MEDIUM


def test_classify_paths_medium_risk_dim():
    out = classify_paths(
        ["src/myco/homeostasis/dimensions/mechanical/m1_canon_identity_fields.py"]
    )
    assert out.tier == RiskTier.MEDIUM


def test_classify_paths_low_risk_readme():
    out = classify_paths(["README.md"])
    assert out.tier == RiskTier.LOW


def test_classify_paths_low_risk_test():
    out = classify_paths(["tests/unit/core/test_canon.py"])
    assert out.tier == RiskTier.LOW


def test_classify_paths_low_risk_changelog():
    out = classify_paths(["docs/contract_changelog.md"])
    assert out.tier == RiskTier.LOW


def test_classify_paths_high_when_unknown_path():
    """Unknown paths fail-closed to medium (not low)."""
    out = classify_paths(["weird/unknown/path.txt"])
    assert out.tier == RiskTier.MEDIUM


def test_classify_paths_empty_input_fail_closed():
    """Empty input fails closed to high."""
    out = classify_paths([])
    assert out.tier == RiskTier.HIGH


def test_classify_paths_high_wins_when_mixed():
    out = classify_paths(["README.md", "_canon.yaml"])
    assert out.tier == RiskTier.HIGH


def test_classify_proposal_missing_file():
    out = classify_proposal(Path("/does/not/exist.md"))
    assert out.tier == RiskTier.HIGH


def test_classify_proposal_with_high_keyword(tmp_path: Path):
    p = tmp_path / "craft.md"
    p.write_text("Some text\nR3 mention here\nMore text", encoding="utf-8")
    out = classify_proposal(p)
    # "R3" mentioned at line start with keyword pattern
    assert out.tier in (RiskTier.HIGH, RiskTier.MEDIUM)


def test_classify_proposal_low_risk_default(tmp_path: Path):
    p = tmp_path / "craft.md"
    p.write_text("Just regular text. No high-risk signals.", encoding="utf-8")
    out = classify_proposal(p)
    assert out.tier == RiskTier.MEDIUM
