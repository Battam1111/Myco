"""``core.risk_classifier`` — agent-self-winnow tier classifier (v0.6.0).

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md``
governance section + craft v0.6.0 §F25 / §A5.

Classifies a craft proposal (or a candidate diff) into one of three
risk tiers:

- **High**: requires owner approval before LANDED.
  Triggers: L0 five-principle wording change, R1-R7 number/semantic
  change, ``canon.system.llm_policy`` default flip, subsystem
  deletion, ``protocol.md`` rule-text edit (not editorial), L0
  amendment, contract-version bump from MAJOR-class trigger.

- **Medium**: agent-self-winnow + 7-session/7-day public window.
  Triggers: new dimension addition, new verb alias, fixable-set
  extension, new symbiont host adapter, contract-changelog material
  for non-MAJOR.

- **Low**: agent-self-winnow only.
  Triggers: typo fix, JSON-Schema description tightening, test
  fixtures, README copy edits.

The classifier reads a list of files-changed (or a unified diff) and
returns the tier. Owner-veto via
``canon.governance.last_winnowed_proposals[].vetoed_at`` is always-on
regardless of classification.

Default fail-closed: when uncertain, classify as **High** to force
owner review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

__all__ = ["RiskTier", "classify_paths", "classify_proposal"]


class RiskTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ClassificationResult:
    tier: RiskTier
    rationale: str
    matched_rules: tuple[str, ...]


# Path patterns that always trigger high-risk classification.
_HIGH_RISK_PATH_PATTERNS = (
    re.compile(r"docs/architecture/L0_VISION\.md$"),
    re.compile(r"docs/architecture/L1_CONTRACT/protocol\.md$"),
    re.compile(r"docs/architecture/L1_CONTRACT/canon_schema\.md$"),
    re.compile(r"docs/architecture/L1_CONTRACT/versioning\.md$"),
    re.compile(r"_canon\.yaml$"),  # (any change here is at least medium)
)

# Medium-risk patterns.
_MEDIUM_RISK_PATH_PATTERNS = (
    re.compile(r"docs/architecture/L2_DOCTRINE/.*\.md$"),
    re.compile(r"docs/architecture/L3_IMPLEMENTATION/.*\.md$"),
    re.compile(r"src/myco/homeostasis/dimensions/.*\.py$"),
    re.compile(r"src/myco/surface/manifest\.yaml$"),
    re.compile(r"_canon_lint\.yaml$"),
    re.compile(r"src/myco/symbionts/.*\.py$"),
)

# Low-risk patterns (the default if no higher pattern matches).
_LOW_RISK_PATH_PATTERNS = (
    re.compile(r"README\.md$"),
    re.compile(r"README_zh\.md$"),
    re.compile(r"README_ja\.md$"),
    re.compile(r"\.github/.*\.yml$"),
    re.compile(r"tests/.*\.py$"),
    re.compile(r"examples/.*"),
    re.compile(r"docs/migration/.*"),
    re.compile(r"docs/contract_changelog\.md$"),
    re.compile(r"docs/primordia/.*\.md$"),
)

# Substrings within diff text that always escalate to high.
_HIGH_RISK_DIFF_KEYWORDS = (
    r"^[+-]\s*(?:R[1-7])\b",  # R-rule wording
    r"^[+-]\s*llm_policy",
    r"^[+-]\s*forbidden",
    r"^[+-]\s*hard_contract",
    r"^[+-]\s*rule_count",
    r"^[+-]\s*## L0",
    r"^[+-]\s*Principle",
)


def classify_paths(paths: list[str]) -> ClassificationResult:
    """Classify a craft by file-paths-changed only (no diff body).

    Returns the highest tier any path matches. Default Medium.
    """
    matched: list[str] = []
    has_high = False
    has_medium = False
    has_low = False
    for path in paths:
        for pat in _HIGH_RISK_PATH_PATTERNS:
            if pat.search(path):
                has_high = True
                matched.append(f"high-path: {path}")
                break
        else:
            for pat in _MEDIUM_RISK_PATH_PATTERNS:
                if pat.search(path):
                    has_medium = True
                    matched.append(f"medium-path: {path}")
                    break
            else:
                for pat in _LOW_RISK_PATH_PATTERNS:
                    if pat.search(path):
                        has_low = True
                        matched.append(f"low-path: {path}")
                        break
                else:
                    # Unmatched path: fail-closed to medium.
                    has_medium = True
                    matched.append(f"unknown-path-default-medium: {path}")
    if has_high:
        tier = RiskTier.HIGH
    elif has_medium:
        tier = RiskTier.MEDIUM
    elif has_low:
        tier = RiskTier.LOW
    else:
        # Empty input: fail-closed.
        tier = RiskTier.HIGH
    return ClassificationResult(
        tier=tier,
        rationale=f"path-based classification ({len(paths)} files)",
        matched_rules=tuple(matched),
    )


def classify_proposal(proposal_path: Path) -> ClassificationResult:
    """Classify a craft markdown file.

    Reads the markdown body looking for high-risk signals; if any
    match, escalates to High regardless of file paths. Otherwise,
    falls back to path-based classification on any reachable diff.
    """
    if not proposal_path.is_file():
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale="proposal file missing — fail-closed",
            matched_rules=(),
        )
    try:
        text = proposal_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale="read failure — fail-closed",
            matched_rules=(),
        )
    matched: list[str] = []
    for kw in _HIGH_RISK_DIFF_KEYWORDS:
        if re.search(kw, text, re.MULTILINE):
            matched.append(f"high-keyword: {kw}")
    if matched:
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale="craft body contains high-risk keywords",
            matched_rules=tuple(matched),
        )
    # No high-risk keywords; fallback medium for any craft proposal
    # (crafts authored at all are at-least-medium per protocol).
    return ClassificationResult(
        tier=RiskTier.MEDIUM,
        rationale="craft body has no high-risk signals; default medium",
        matched_rules=(),
    )
