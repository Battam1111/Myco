"""Wave 38 seed tests — L19 lint dimension count consistency.

Four focused tests covering the load-bearing paths of L19. Each test guards a
specific Wave 38 craft decision so a regression has a single discoverable scar
class. These extend the Wave 25 / Wave 30 / Wave 31 seed in
``tests/unit/test_compress.py`` and follow the same scar-class rationale.

Wave 38 design coverage:

- ``test_l19_clean_substrate_passes`` exercises Wave 38 D1 (SSoT principle)
  + D8 base case: when every narrative surface mirrors
  ``len(FULL_CHECKS)``, L19 returns an empty issue list. Without this test,
  L19 could be permanently red against its own home repo and the team would
  learn to ignore it (Goodhart class — same shape as the silent-fail scars
  Wave 20 closed).

- ``test_l19_badge_drift_caught_high`` exercises Wave 38 D6 pattern #1
  (README badge regex) + D4 severity matrix (README is HIGH). The badge
  is the user-facing first-impression surface, so badge drift MUST surface
  as HIGH severity, not MEDIUM. Without this test, badge drift could
  silently demote to a soft warning the user dismisses.

- ``test_l19_multi_pattern_co_match`` exercises Wave 38 D6 + the
  multi-pattern overlap from craft §3 C5: a single line that matches
  multiple regex patterns must produce one issue PER pattern (not be
  collapsed into a single issue), so each scar class is independently
  visible to the human reader. Without this test, dedup logic could
  swallow co-firing patterns and drift could hide behind a single message.

- ``test_l19_severity_split_high_vs_medium`` exercises Wave 38 D4
  (severity matrix): the same drift in a HIGH surface (README.md) vs a
  MEDIUM surface (CONTRIBUTING.md) must produce HIGH and MEDIUM issues
  respectively. Without this test, the severity matrix could degrade
  to all-MEDIUM (or all-HIGH) and lose its triage signal.
"""

from __future__ import annotations

from pathlib import Path

from myco.lint import (
    FULL_CHECKS,
    QUICK_CHECKS,
    lint_dimension_count_consistency,
    load_canon,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Pull the SSoT once at import time so the test assertions read against the
# *current* value of len(FULL_CHECKS), not a hardcoded number that would itself
# need updating in lockstep — which would defeat L19's whole purpose.
EXPECTED = len(FULL_CHECKS)
EXPECTED_L_MAX = EXPECTED - 1
QUICK_L_MAX = len(QUICK_CHECKS) - 1
DRIFTED = EXPECTED - 4  # an obviously-wrong stale count for tests


def _write_clean_surfaces(project: Path) -> None:
    """Write minimal HIGH+MEDIUM surfaces that all reference EXPECTED correctly.

    Used by ``test_l19_clean_substrate_passes`` to prove the base case works
    even when the substrate is fully populated. We write each scanned surface
    with a single canonical reference line so any future pattern addition can
    extend this helper rather than touching every test.
    """
    # HIGH surfaces — the badge regex requires the URL-encoded slash
    (project / "README.md").write_text(
        f"![Lint](https://img.shields.io/badge/Lint-{EXPECTED}%2F{EXPECTED}%20green-brightgreen)\n"
        f"This is the {EXPECTED}-dimension health check L0-L{EXPECTED_L_MAX}.\n",
        encoding="utf-8",
    )
    (project / "README_zh.md").write_text(
        f"![Lint](https://img.shields.io/badge/Lint-{EXPECTED}%2F{EXPECTED}%20绿灯-brightgreen)\n"
        f"{EXPECTED} 维 lint L0-L{EXPECTED_L_MAX} 全绿。\n",
        encoding="utf-8",
    )
    (project / "README_ja.md").write_text(
        f"![Lint](https://img.shields.io/badge/Lint-{EXPECTED}%2F{EXPECTED}%20全緑-brightgreen)\n"
        f"{EXPECTED} 次元の lint L0-L{EXPECTED_L_MAX} 全緑。\n",
        encoding="utf-8",
    )
    (project / "MYCO.md").write_text(
        f"**{EXPECTED} 维 lint (L0-L{EXPECTED_L_MAX})** all green.\n",
        encoding="utf-8",
    )

    # MEDIUM surfaces — only the ones the test substrate expects
    (project / "CONTRIBUTING.md").write_text(
        f"# {EXPECTED}-dimension consistency checker (L0-L{EXPECTED_L_MAX})\n",
        encoding="utf-8",
    )
    (project / "wiki").mkdir(exist_ok=True)
    (project / "wiki" / "README.md").write_text(
        f"应 {EXPECTED}/{EXPECTED} 绿\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_l19_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """Wave 38 D1 + D8 base case: a clean substrate produces zero L19 issues.

    Writes every relevant narrative surface with values that mirror the
    current ``len(FULL_CHECKS)`` SSoT, then runs L19 and asserts no issues.
    This is the empty-input invariant — without it, L19 could be red against
    its own home repo and the team would normalize ignoring it.
    """
    project = _isolate_myco_project
    _write_clean_surfaces(project)

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)

    assert issues == [], (
        f"L19 must produce zero issues against a clean substrate where "
        f"every surface mirrors len(FULL_CHECKS)={EXPECTED}. Got: {issues}"
    )


def test_l19_badge_drift_caught_high(_isolate_myco_project: Path) -> None:
    """Wave 38 D6 pattern #1 + D4 severity matrix: README badge drift is HIGH.

    Writes a README.md with a stale ``Lint-N/N`` badge where N != EXPECTED.
    L19 must surface this as a HIGH issue (not MEDIUM, not absent), because
    the README badge is the user-facing first-impression surface.
    """
    project = _isolate_myco_project
    (project / "README.md").write_text(
        f"![Lint](https://img.shields.io/badge/Lint-{DRIFTED}%2F{DRIFTED}%20green-brightgreen)\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)

    high_badge_issues = [
        i for i in issues
        if i[0] == "L19"
        and i[1] == "HIGH"
        and i[2] == "README.md"
        and "badge" in i[3]
    ]
    assert high_badge_issues, (
        f"L19 must surface README badge drift `Lint-{DRIFTED}/{DRIFTED}` as a "
        f"HIGH severity issue against README.md. Got issues: {issues}"
    )


def test_l19_multi_pattern_co_match(_isolate_myco_project: Path) -> None:
    """Wave 38 D6 + craft §3 C5: a line that matches multiple regex patterns
    produces one issue per pattern (no dedup, each scar visible).

    Writes a single MYCO.md line that simultaneously matches the English
    dimension pattern, the CJK 维 pattern, and the L0-L{N} range pattern,
    all at the same drifted value. L19 must produce 3 issues (one per
    pattern), not 1 collapsed issue. This guards against an over-eager
    dedup helper swallowing co-firing patterns.
    """
    project = _isolate_myco_project
    # One line, three pattern hits, all drifted to the same wrong number.
    # Note: each clause uses a domain keyword required by its pattern.
    (project / "MYCO.md").write_text(
        f"The {DRIFTED}-dimension lint, {DRIFTED} 维 lint, "
        f"covers L0-L{DRIFTED - 1}.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)
    myco_issues = [i for i in issues if i[2] == "MYCO.md"]

    # Three distinct pattern classes should fire on the same line. We assert
    # at least 3 because additional patterns may incidentally co-match (e.g.
    # if pattern 3 catches a 维 token without trailing keyword).
    assert len(myco_issues) >= 3, (
        f"L19 must emit one issue per matching pattern on the same line "
        f"(no collapsing). Expected ≥3 distinct issues against MYCO.md, "
        f"got {len(myco_issues)}: {myco_issues}"
    )
    # Every issue against MYCO.md must be HIGH severity (D4).
    for level, severity, rel, msg in myco_issues:
        assert level == "L19"
        assert severity == "HIGH", (
            f"MYCO.md issues must be HIGH (D4 severity matrix), got {severity}"
        )


def test_l19_severity_split_high_vs_medium(_isolate_myco_project: Path) -> None:
    """Wave 38 D4 severity matrix: identical drift in HIGH vs MEDIUM surfaces
    produces HIGH and MEDIUM severities respectively.

    Writes the same stale dimension claim into README.md (HIGH) and
    CONTRIBUTING.md (MEDIUM). L19 must produce both severities — proving
    that the surface→severity mapping is real and not collapsed to a single
    severity. Without this test, the severity matrix could degrade to
    all-HIGH or all-MEDIUM and lose its triage signal.
    """
    project = _isolate_myco_project
    drift_line = f"This is the {DRIFTED}-dimension lint.\n"
    (project / "README.md").write_text(drift_line, encoding="utf-8")
    (project / "CONTRIBUTING.md").write_text(drift_line, encoding="utf-8")

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)

    readme_issues = [i for i in issues if i[2] == "README.md"]
    contributing_issues = [i for i in issues if i[2] == "CONTRIBUTING.md"]

    assert readme_issues, "L19 must catch drift in README.md"
    assert contributing_issues, "L19 must catch drift in CONTRIBUTING.md"

    readme_severities = {i[1] for i in readme_issues}
    contributing_severities = {i[1] for i in contributing_issues}

    assert readme_severities == {"HIGH"}, (
        f"README.md is a HIGH surface — all its L19 issues must be HIGH. "
        f"Got: {readme_severities}"
    )
    assert contributing_severities == {"MEDIUM"}, (
        f"CONTRIBUTING.md is a MEDIUM surface — all its L19 issues must be "
        f"MEDIUM. Got: {contributing_severities}"
    )
