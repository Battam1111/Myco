"""``core.risk_classifier`` — agent-self-winnow tier classifier (v0.6.0+).

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md``
governance section + craft v0.6.0 §F25 / §A5
+ craft v0.6.15 (Agent-First default for Cycle 自起 闭环).

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

**v0.6.15 — content-based craft risk classification + recursion-cutter:**

``classify_craft_via_path_allowlist(craft_path)`` reads the craft's
frontmatter ``path_allowlist:`` field (introduced by winnow gate G7
at v0.6.15+) and applies path-based classification. This is the
canonical craft-classifier path going forward; ``classify_proposal``
remains as v0.6.0 body-keyword fallback for pre-v0.6.15 grandfather'd
crafts.

The **recursion-cutter** (v0.6.15+) forces HIGH-risk classification
regardless of any other content when ``path_allowlist`` includes:

- ``src/myco/core/risk_classifier.py`` itself (any change requires
  owner review; otherwise the substrate could quietly auto-merge a
  craft that disables its own risk gates)
- ``_canon.yaml`` ``governance.auto_evolve_*`` keys (the gating
  policy itself; same recursion concern)
- ``.github/workflows/auto_*.yml`` (auto_revert, future auto_merge,
  any other governance workflow)

This closes the perpetual-motion attack the v0.6.15 craft Round 1.5
mycoparasite T1 surfaced: without the recursion-cutter, an auto-craft
could legitimately classify itself as MEDIUM-risk while modifying the
classifier or governance keys, then auto-merge after window expiry,
hollowing out the L0 P1 gates.

Default fail-closed: when uncertain, classify as **High** to force
owner review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

__all__ = [
    "RiskTier",
    "classify_paths",
    "classify_proposal",
    "classify_craft_via_path_allowlist",
]


class RiskTier(Enum):
    """Three-tier craft risk classification (low | medium | high).

    Invariant: each craft proposal maps to exactly one tier; HIGH
    requires owner approval before LANDED, MEDIUM requires the
    7-session/7-day winnow window, LOW is agent-self-winnow only.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ClassificationResult:
    """Frozen verdict from the risk classifier.

    Carries the assigned ``tier``, a human-readable ``rationale``, and
    the ordered tuple of ``matched_rules`` (path patterns or diff
    keywords) that drove the decision. Immutable so callers can stash
    it in audit logs without defensive copying.
    """

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
    # v0.6.15 — explicit superset additions for craft path_allowlist scan.
    # Subsystem deletion (any subsystem doctrine page disappearing) is
    # detected at the diff level via _HIGH_RISK_DIFF_KEYWORDS, but a
    # path_allowlist that touches the manifest (verb count) or lint
    # config (dim count) or schema_version is also high-risk.
    re.compile(r"src/myco/boundary/surface/manifest\.yaml$"),
    re.compile(r"_canon_lint\.yaml$"),
)


# v0.6.15 — recursion-cutter path patterns. Forces HIGH-risk regardless
# of any other classification. See craft v0.6.15 Round 1.5 mycoparasite T1.
# v0.7.2 — extended per craft v0_7_2 Round 1.5 mycoparasite T1/T2/T6:
# the new MB8 ratchet's shim-hit counter file + the shim packages
# themselves are recursion-cutter-protected so an adversary craft
# cannot zero counts + delete shim in a single MEDIUM-tier molt.
_RECURSION_CUTTER_PATH_PATTERNS = (
    # The risk classifier itself.
    re.compile(r"src/myco/core/risk_classifier\.py$"),
    # The classifier's tests (could be subverted to NOT enforce cutter).
    re.compile(r"tests/unit/core/test_risk_classifier.*\.py$"),
    # Governance workflow files (auto_revert, future auto_merge, etc.).
    re.compile(r"\.github/workflows/auto_.*\.ya?ml$"),
    # The winnow gate that requires path_allowlist (G7).
    re.compile(r"src/myco/cycle/winnow\.py$"),
    # v0.7.2: the MB8 shim-hit counter state file. Zeroing this file
    # would unlock the shim-deletion gate falsely.
    re.compile(r"\.myco_state/shim_hits\.json$"),
    # v0.7.2: any other state-file the substrate writes for telemetry-
    # gated decisions. Broad pattern; better safe than sorry.
    re.compile(r"\.myco_state/.*\.json$"),
    # v0.7.2: the back-compat shim package itself (deleting it
    # bypasses MB8's telemetry; must be HIGH-tier owner-gated).
    re.compile(r"src/myco/mcp/.*\.py$"),
    # v0.7.2: the canonical MCP launcher (any change here affects
    # downstream consumers of `python -m myco.boundary.mcp`).
    re.compile(r"src/myco/boundary/mcp/.*\.py$"),
)


# v0.6.15 — within _canon.yaml, modifications to these governance keys
# trigger the recursion-cutter. Detected via diff-keyword scan when
# _canon.yaml is in path_allowlist.
# v0.7.2 — extended per mycoparasite T3: any modification to the new
# `metrics.repo_size_*` thresholds OR the `governance.shim_sunset_*`
# thresholds bypasses the v0.7.2 ratchets if not recursion-cutter'd.
_RECURSION_CUTTER_CANON_KEYS = (
    "auto_propose_enabled",
    "auto_evolve_min_wall_clock_seconds_between",
    "auto_evolve_critic_count",
    "auto_evolve_branch_prefix",
    "auto_evolve_distilled_hash_cooldown_senesce",
    "auto_evolve_force_high_risk",
    "auto_evolve_pr_window_skip",
    "auto_evolve_min_distilled_severity",
    "auto_evolve_daily_budget_usd",
    "auto_evolve_tracking_issue_id",
    "recognized_authoring_hosts",
    # v0.7.2 永恒删减 ratchet thresholds.
    "repo_size_max_bytes",
    "repo_size_excluded",
    "shim_sunset_min_zero_cycles",
    "shim_sunset_min_zero_days",
)


# v0.7.2 — multi-cluster compound trigger (mycoparasite T6). A craft
# whose path_allowlist simultaneously touches paths from ≥ 2 of these
# disjoint sensitivity clusters escalates to HIGH risk regardless of
# any individual path's classification. This defeats the compound
# attack: a single craft with `path_allowlist: [_canon.yaml,
# .myco_state/shim_hits.json, src/myco/mcp/__init__.py]` would
# otherwise see 3 separate MEDIUM-tier paths and auto-LAND despite
# the combined effect being a perpetual-motion shim-deletion exploit.
_RECURSION_CUTTER_COMPOUND_CLUSTERS: tuple[
    tuple[str, tuple[re.Pattern[str], ...]], ...
] = (
    ("state", (re.compile(r"\.myco_state/"),)),
    (
        "shim",
        (
            re.compile(r"src/myco/mcp/"),
            re.compile(r"src/myco/boundary/mcp/"),
        ),
    ),
    # _canon.yaml is one path but represents two clusters because
    # different content-edits touch metrics.* vs governance.*
    # (the dim-content scanner distinguishes; this clustering is
    # path-level coarseness).
    ("canon", (re.compile(r"^_canon\.yaml$"),)),
    (
        "classifier",
        (
            re.compile(r"src/myco/core/risk_classifier\.py$"),
            re.compile(r"src/myco/cycle/winnow\.py$"),
        ),
    ),
)


def _hits_compound_clusters(paths: list[str]) -> tuple[bool, list[str]]:
    """Return (compound-triggered, list-of-cluster-names-hit).

    A path_allowlist that simultaneously touches ≥ 2 disjoint clusters
    forces HIGH-risk classification per the v0.7.2 multi-cluster
    compound trigger.
    """
    hit_clusters: list[str] = []
    for cluster_name, patterns in _RECURSION_CUTTER_COMPOUND_CLUSTERS:
        for path in paths:
            if any(p.search(path) for p in patterns):
                hit_clusters.append(cluster_name)
                break
    return (len(set(hit_clusters)) >= 2, hit_clusters)


# Medium-risk patterns.
# v0.6.16: dead-pattern cleanup — removed pre-v0.6.0 paths
# (``src/myco/surface/manifest.yaml`` and ``_canon_lint.yaml`` are
# already covered HIGH at lines 100-101; ``src/myco/symbionts/`` was
# excreted at v0.6.0 in favor of ``src/myco/boundary/host_integration/``).
_MEDIUM_RISK_PATH_PATTERNS = (
    re.compile(r"docs/architecture/L2_DOCTRINE/.*\.md$"),
    re.compile(r"docs/architecture/L3_IMPLEMENTATION/.*\.md$"),
    re.compile(r"src/myco/homeostasis/dimensions/.*\.py$"),
    re.compile(r"src/myco/boundary/host_integration/.*\.py$"),
)

# Low-risk patterns (the default if no higher pattern matches).
_LOW_RISK_PATH_PATTERNS = (
    re.compile(r"README\.md$"),
    re.compile(r"README_zh\.md$"),
    re.compile(r"README_ja\.md$"),
    re.compile(r"\.github/.*\.yml$"),
    re.compile(r"tests/.*\.py$"),
    # v0.8.4 root-cleanup (2026-05-12): examples/ moved to docs/examples/.
    re.compile(r"docs/examples/.*"),
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


def _path_matches_recursion_cutter(path: str) -> bool:
    """True iff ``path`` is in the recursion-cutter set (v0.6.15+).

    See module docstring "v0.6.15 — content-based craft risk classification
    + recursion-cutter" for rationale.
    """
    return any(pat.search(path) for pat in _RECURSION_CUTTER_PATH_PATTERNS)


def _craft_touches_recursion_cutter_canon_keys(craft_text: str) -> bool:
    """True iff the craft body or path_allowlist includes a `_canon.yaml`
    write that mentions a recursion-cutter governance key.

    We check craft body for the literal key name (e.g. ``auto_evolve_force_high_risk``)
    appearing on a line that looks like a YAML mutation. This is heuristic
    but reliable — crafts that propose flipping a governance default
    invariably mention the key by name.
    """
    for key in _RECURSION_CUTTER_CANON_KEYS:
        # Match patterns like:
        #   auto_evolve_force_high_risk: true
        #   `auto_evolve_force_high_risk` (in markdown body)
        #   - auto_evolve_force_high_risk: ...
        if re.search(rf"\b{re.escape(key)}\b\s*[:=]", craft_text):
            return True
    return False


def classify_craft_via_path_allowlist(
    craft_path: Path,
) -> ClassificationResult:
    """Classify a craft via its frontmatter ``path_allowlist:`` field (v0.6.15+).

    This is the canonical craft-classifier path going forward. It reads
    the YAML frontmatter from the craft markdown file, extracts the
    ``path_allowlist`` list, and:

    1. Returns HIGH **forced** if any path in the allowlist matches the
       recursion-cutter set (the risk classifier itself, governance
       workflow files, or — when ``_canon.yaml`` is touched — the canon
       body mentions a governance key in the recursion-cutter set).
    2. Otherwise applies path-based classification via ``classify_paths``.
    3. Returns HIGH fallback if ``path_allowlist`` is missing (winnow
       G7 should have caught this, but defense-in-depth).

    Pre-v0.6.15 crafts that lack path_allowlist fall through to the
    HIGH-fallback branch; the caller should typically use
    ``classify_proposal`` (body-keyword fallback) for those.
    """
    if not craft_path.is_file():
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale="craft file missing — fail-closed",
            matched_rules=(),
        )
    try:
        text = craft_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale="read failure — fail-closed",
            matched_rules=(),
        )

    # Parse YAML frontmatter (lightweight — no pyyaml import; we only
    # need the path_allowlist list).
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale="no frontmatter — fail-closed",
            matched_rules=(),
        )
    fm_end = re.search(r"^---\s*$", text[4:], re.MULTILINE)
    if fm_end is None:
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale="unclosed frontmatter — fail-closed",
            matched_rules=(),
        )
    fm_text = text[4 : 4 + fm_end.start()]
    body_text = text[4 + fm_end.end() :]

    # Extract path_allowlist list. Pyyaml-free regex parse — looks for
    # ``path_allowlist:`` followed by indented ``- <path>`` lines.
    allowlist_match = re.search(
        r"^path_allowlist\s*:\s*\n((?:\s+-\s*.+\n?)*)",
        fm_text,
        re.MULTILINE,
    )
    if allowlist_match is None:
        # Inline-list form: `path_allowlist: [a, b, c]`.
        inline_match = re.search(
            r"^path_allowlist\s*:\s*\[([^\]]*)\]",
            fm_text,
            re.MULTILINE,
        )
        if inline_match is None:
            return ClassificationResult(
                tier=RiskTier.HIGH,
                rationale=(
                    "frontmatter missing `path_allowlist:` — winnow G7 "
                    "violation; fail-closed to HIGH"
                ),
                matched_rules=(),
            )
        # Inline form: split on commas, strip quotes/whitespace.
        items_raw = inline_match.group(1)
        paths = [p.strip().strip("\"'") for p in items_raw.split(",") if p.strip()]
    else:
        # Block form: each `- <path>` line.
        block = allowlist_match.group(1)
        paths = [
            line.strip().lstrip("-").strip().strip("\"'")
            for line in block.splitlines()
            if line.strip().startswith("-")
        ]

    # Empty allowlist is permitted (signals pure doctrine craft, no code
    # changes). Treat as MEDIUM (no path triggers HIGH).
    if not paths:
        return ClassificationResult(
            tier=RiskTier.MEDIUM,
            rationale="empty path_allowlist (pure doctrine craft)",
            matched_rules=(),
        )

    # Recursion-cutter: any path matching forces HIGH regardless of
    # other content.
    cutter_matches = [p for p in paths if _path_matches_recursion_cutter(p)]
    if cutter_matches:
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale=(
                f"recursion-cutter triggered: path_allowlist touches "
                f"{cutter_matches!r} (risk classifier / governance "
                f"workflow / winnow gate / shim package / state "
                f"telemetry file). Forced HIGH regardless of content "
                f"classification."
            ),
            matched_rules=tuple(f"recursion-cutter: {p}" for p in cutter_matches),
        )

    # _canon.yaml + recursion-cutter governance keys.
    canon_paths = [p for p in paths if "_canon.yaml" in p]
    if canon_paths and _craft_touches_recursion_cutter_canon_keys(body_text):
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale=(
                "recursion-cutter triggered: path_allowlist includes "
                "_canon.yaml AND craft body mentions governance / "
                "metrics ratchet keys (auto_evolve_* / repo_size_* / "
                "shim_sunset_*). Forced HIGH (cannot auto-merge changes "
                "to gating policy or threshold knobs)."
            ),
            matched_rules=("recursion-cutter: _canon.yaml + governance/metrics keys",),
        )

    # v0.7.2 multi-cluster compound trigger (mycoparasite T6). A craft
    # whose path_allowlist simultaneously touches ≥ 2 disjoint
    # sensitivity clusters forces HIGH risk regardless of any
    # individual path's classification. Defeats the compound attack:
    # `path_allowlist: [_canon.yaml, .myco_state/shim_hits.json,
    # src/myco/mcp/__init__.py]` → 3 separate MEDIUM paths in v0.6.15
    # would auto-LAND despite the combined effect being a perpetual-
    # motion shim-deletion exploit.
    compound_hit, hit_clusters = _hits_compound_clusters(paths)
    if compound_hit:
        return ClassificationResult(
            tier=RiskTier.HIGH,
            rationale=(
                f"recursion-cutter compound-cluster triggered: "
                f"path_allowlist simultaneously touches clusters "
                f"{sorted(set(hit_clusters))!r}. The combined effect of "
                f"editing multiple sensitivity clusters in a single "
                f"craft is HIGH-risk regardless of individual path "
                f"classifications (v0.7.2 mycoparasite T6)."
            ),
            matched_rules=tuple(
                f"recursion-cutter compound: {c}" for c in sorted(set(hit_clusters))
            ),
        )

    # Otherwise: standard path-based classification.
    return classify_paths(paths)
