"""Wave 40 seed tests — L21 contract version inline consistency.

Four focused tests covering the load-bearing paths of L21 (Wave 40, v0.31.0).
Each test guards a specific Wave 40 craft decision so a regression has a
single discoverable scar class. These extend the Wave 25 / Wave 30 / Wave 31 /
Wave 38 / Wave 39 seed and follow the same scar-class rationale. Wave 40
closes Wave 37 D7 followup #3 — the third + final candidate from the Wave
37 manual sweep — and completes the silent-rot trio with L19 + L20.

Wave 40 design coverage:

- ``test_l21_clean_substrate_passes`` exercises Wave 40 D1 (forward-looking
  pattern + canon SSoT) base case: when an allowlisted file's inline
  ``kernel contract`` claim already matches ``_canon.yaml::system.contract_version``,
  L21 returns an empty issue list. Without this test, L21 could be permanently
  red against its own home repo and the team would learn to ignore it
  (Goodhart class — same failure shape Wave 38 D1 + Wave 39 D1 already guard).

- ``test_l21_stale_inline_caught_high`` exercises Wave 40 D1 + D4: a drifted
  ``kernel contract vX.Y.Z`` claim in MYCO.md (HIGH allowlist) must surface as
  a HIGH severity issue against MYCO.md naming the drifted version. This is
  the principal scar class L21 was built for — the actual MYCO.md:4/22/159
  drift discovered in the Wave 40 scout that justified the entire lint dim.

- ``test_l21_historical_marker_skipped`` exercises Wave 40 D2 §1.2 historical-
  marker filter: a line containing a historical-event verb (e.g. "landed",
  "✅") or a date-in-parens stamp must NOT be flagged even if its version
  number diverges from canon. This is the false-positive escape that
  preserves history-laden phase trackers without forcing operator skip
  markers everywhere.

- ``test_l21_skip_marker_respected`` exercises Wave 40 D5: a line preceded by
  ``<!-- l21-skip -->`` on the previous non-blank line is excluded from
  enforcement. This is the explicit operator escape hatch for intentional
  divergence (e.g. tutorial showing an old version on purpose). Without this
  test, the skip marker could silently degrade and force every legitimately
  divergent claim into a workaround.
"""

from __future__ import annotations

from pathlib import Path

from myco.lint import (
    _L21_SKIP_MARKER,
    lint_contract_version_inline,
    load_canon,
)


# Helper: rewrite the fixture's canon to a known contract version so the
# test assertions can name a specific expected value without coupling to the
# conftest default. The conftest hard-codes v0.24.0 — we override here so
# tests stay readable when conftest's seed value advances.
_TEST_CANON_V_31 = """\
system:
  principles_count: 12
  principles_label: "十二原则"
  entry_point: MYCO.md
  contract_version: "v0.31.0"
  synced_contract_version: "v0.31.0"
architecture:
  layers: 4
  wiki_pages: 0
project:
  name: TestProject
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_l21_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """Wave 40 D1 base case: a MYCO.md whose inline claim matches canon → no issues.

    Writes a minimal MYCO.md whose ``kernel contract`` line already names the
    canonical version, runs L21, asserts empty issue list. This is the
    empty-input invariant — without it, L21 could be red against its own home
    repo and the team would normalize ignoring it.
    """
    project = _isolate_myco_project
    (project / "_canon.yaml").write_text(_TEST_CANON_V_31, encoding="utf-8")
    (project / "MYCO.md").write_text(
        "# Test Project\n"
        "\n"
        "> kernel contract v0.31.0\n"
        "\n"
        "Some prose.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_contract_version_inline(canon, project)

    assert issues == [], (
        f"L21 must produce zero issues against a clean substrate where the "
        f"inline kernel contract claim matches canon. Got: {issues}"
    )


def test_l21_stale_inline_caught_high(_isolate_myco_project: Path) -> None:
    """Wave 40 D1 + D4: stale inline claim in MYCO.md surfaces as HIGH.

    Writes a MYCO.md whose ``kernel contract`` claim is one minor version
    behind canon. L21 must surface this as a HIGH severity issue against
    MYCO.md naming the drifted version. This guards the exact scar class
    that justified Wave 40 (MYCO.md:4/22/159 still claiming v0.28.0 after
    Waves 38+39 manual sweeps).
    """
    project = _isolate_myco_project
    (project / "_canon.yaml").write_text(_TEST_CANON_V_31, encoding="utf-8")
    (project / "MYCO.md").write_text(
        "# Test Project\n"
        "\n"
        "> kernel contract v0.28.0\n"
        "\n"
        "Some prose.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_contract_version_inline(canon, project)

    high_issues = [
        i for i in issues
        if i[0] == "L21"
        and i[1] == "HIGH"
        and i[2] == "MYCO.md"
        and "v0.28.0" in i[3]
    ]
    assert high_issues, (
        f"L21 must surface a stale `kernel contract v0.28.0` in MYCO.md "
        f"(HIGH allowlist) as a HIGH severity issue naming the drifted "
        f"version. Got issues: {issues}"
    )


def test_l21_historical_marker_skipped(_isolate_myco_project: Path) -> None:
    """Wave 40 D2 §1.2: historical-event verbs / dates / arrows are not flagged.

    Writes a MYCO.md whose ``kernel contract`` claim diverges from canon but
    is wrapped in a historical-marker line (one with the verb "landed" + a
    parenthesized date). L21 must NOT flag this line because the §1.2 filter
    treats it as a frozen historical reference. This protects phase trackers
    + log-style narratives from forcing operator skip markers on every
    historical row.
    """
    project = _isolate_myco_project
    (project / "_canon.yaml").write_text(_TEST_CANON_V_31, encoding="utf-8")
    (project / "MYCO.md").write_text(
        "# Test Project\n"
        "\n"
        "Wave 36 landed kernel contract v0.28.0 (2026-04-12).\n"
        "\n"
        "Some prose.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_contract_version_inline(canon, project)

    assert issues == [], (
        f"L21 must respect the §1.2 historical-marker filter — a line "
        f"containing the verb 'landed' + a date-in-parens stamp must NOT be "
        f"flagged even when the version diverges from canon. Got: {issues}"
    )


def test_l21_skip_marker_respected(_isolate_myco_project: Path) -> None:
    """Wave 40 D5: a line preceded by the skip marker is excluded.

    Writes a MYCO.md whose stale ``kernel contract`` line is preceded by
    ``<!-- l21-skip -->`` on the previous non-blank line. L21 must produce
    zero issues for the skipped line — this is the explicit operator escape
    hatch for intentional divergence (e.g. a tutorial showing an old version
    on purpose, or a comparison with an upstream contract). Without this
    test, the skip marker could silently degrade and force every legitimately
    divergent claim into a removal-or-rewrite.
    """
    project = _isolate_myco_project
    (project / "_canon.yaml").write_text(_TEST_CANON_V_31, encoding="utf-8")
    (project / "MYCO.md").write_text(
        "# Test Project\n"
        "\n"
        f"{_L21_SKIP_MARKER}\n"
        "kernel contract v0.5.0\n"
        "\n"
        "Some prose.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_contract_version_inline(canon, project)

    assert issues == [], (
        f"L21 must respect the skip marker — a line preceded by "
        f"`{_L21_SKIP_MARKER}` on the previous non-blank line must be "
        f"excluded from enforcement. Got: {issues}"
    )
