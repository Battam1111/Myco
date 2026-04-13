"""Tests for myco lint --fix auto-repair mode.

Covers the four fixable dimensions (L2, L12, L16, L19) plus idempotency.
Each test uses the conftest ``_isolate_myco_project`` fixture for a
clean, tmp_path-backed workspace.

Test coverage:

- ``test_lint_fix_l2_numeric_claim``: stale lint_dimensions count in a
  cited file is corrected to match _canon.yaml SSoT value.

- ``test_lint_fix_l19_dimension_count``: stale dimension count in
  README badge + English prose is corrected to len(FULL_CHECKS).

- ``test_lint_fix_l19_cjk``: CJK dimension claims (维/次元) and
  L-ranges are corrected.

- ``test_lint_fix_l12_broken_markdown_link``: broken markdown link
  syntax is removed, keeping display text.

- ``test_lint_fix_l12_broken_backtick_path``: broken backtick path
  reference backticks are removed.

- ``test_lint_fix_l16_boot_brief_missing``: missing boot brief is
  created when boot_brief.enabled=true in canon.

- ``test_lint_fix_idempotent``: running fix twice on the same stale
  substrate produces the same result (no double-fix corruption).
"""

from __future__ import annotations

import yaml
from pathlib import Path

from myco.immune import (
    FULL_CHECKS,
    QUICK_CHECKS,
    auto_fix_issues,
    collect_all_issues,
    lint_dimension_count_consistency,
    lint_internal_link_integrity,
    lint_numbers,
    load_canon,
    _fix_l2_numeric_claims,
    _fix_l12_broken_links,
    _fix_l16_boot_brief,
    _fix_l19_dimension_count,
)


EXPECTED = len(FULL_CHECKS)
EXPECTED_L_MAX = EXPECTED - 1
DRIFTED = EXPECTED - 4  # obviously-wrong stale count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_canon_with_claims(project: Path, claims: dict = None,
                              boot_brief: bool = False) -> dict:
    """Write a _canon.yaml with numeric_claims and return the parsed canon."""
    canon_data = {
        "system": {
            "principles_count": 13,
            "principles_label": "test",
            "entry_point": "MYCO.md",
            "contract_version": "v0.24.0",
            "synced_contract_version": "v0.24.0",
            "traceability": {
                "numeric_claims": claims or {},
            },
        },
        "architecture": {
            "layers": 4,
            "wiki_pages": 0,
        },
        "project": {
            "name": "TestProject",
        },
    }
    if boot_brief:
        canon_data["system"]["boot_brief"] = {
            "enabled": True,
            "brief_path": ".myco_state/boot_brief.md",
        }
    (project / "_canon.yaml").write_text(
        yaml.dump(canon_data, allow_unicode=True),
        encoding="utf-8",
    )
    return canon_data


# ---------------------------------------------------------------------------
# L2 fix tests
# ---------------------------------------------------------------------------

def test_lint_fix_l2_numeric_claim(_isolate_myco_project: Path) -> None:
    """Stale lint_dimensions count in a cited file is corrected to SSoT."""
    project = _isolate_myco_project

    # Set up canon with lint_dimensions claim
    _write_canon_with_claims(project, {
        "lint_dimensions": {
            "ssot": "len(FULL_CHECKS) in src/myco/lint.py",
            "value": EXPECTED,
            "cited_in": ["MYCO.md"],
        },
    })

    # Write MYCO.md with a stale dimension count
    (project / "MYCO.md").write_text(
        f"# Myco\n\nThis is a {DRIFTED}-dimension lint system, "
        f"covering L0-L{DRIFTED - 1}.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_numbers(canon, project)

    # Should detect the stale value
    l2_issues = [i for i in issues if i[0] == "L2"]
    assert l2_issues, f"L2 must detect stale lint_dimensions. Got: {issues}"

    # Run fix
    fixed = _fix_l2_numeric_claims(project, l2_issues, canon)
    assert fixed > 0, "L2 fix should have modified at least one file"

    # Verify the file now contains the correct value
    content = (project / "MYCO.md").read_text(encoding="utf-8")
    assert f"{EXPECTED}-dimension" in content, (
        f"After L2 fix, MYCO.md should contain '{EXPECTED}-dimension'. "
        f"Got: {content}"
    )
    assert f"L0-L{EXPECTED_L_MAX}" in content, (
        f"After L2 fix, MYCO.md should contain 'L0-L{EXPECTED_L_MAX}'. "
        f"Got: {content}"
    )


# ---------------------------------------------------------------------------
# L19 fix tests
# ---------------------------------------------------------------------------

def test_lint_fix_l19_dimension_count(_isolate_myco_project: Path) -> None:
    """Stale dimension count in README badge + prose is corrected."""
    project = _isolate_myco_project

    # Write README.md with stale badge and dimension count
    (project / "README.md").write_text(
        f"![Lint](https://img.shields.io/badge/Lint-{DRIFTED}%2F{DRIFTED}%20green-brightgreen)\n"
        f"This is the {DRIFTED}-dimension lint.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)
    assert issues, "L19 must detect stale dimension count"

    # Run fix
    fixed = _fix_l19_dimension_count(project, issues, canon)
    assert fixed > 0, "L19 fix should have modified at least one file"

    # Verify
    content = (project / "README.md").read_text(encoding="utf-8")
    assert f"Lint-{EXPECTED}%2F{EXPECTED}" in content, (
        f"Badge should be updated to Lint-{EXPECTED}%2F{EXPECTED}. Got: {content}"
    )
    assert f"{EXPECTED}-dimension" in content, (
        f"Prose should be updated to {EXPECTED}-dimension. Got: {content}"
    )


def test_lint_fix_l19_cjk(_isolate_myco_project: Path) -> None:
    """CJK dimension claims and L-ranges are corrected."""
    project = _isolate_myco_project

    # Write MYCO.md with stale CJK counts
    (project / "MYCO.md").write_text(
        f"**{DRIFTED} \u7ef4 lint (L0-L{DRIFTED - 1})** all green.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)
    assert issues, "L19 must detect stale CJK dimension count"

    fixed = _fix_l19_dimension_count(project, issues, canon)
    assert fixed > 0, "L19 fix should have modified at least one file"

    content = (project / "MYCO.md").read_text(encoding="utf-8")
    assert f"{EXPECTED} \u7ef4" in content, (
        f"CJK count should be updated to {EXPECTED} \u7ef4. Got: {content}"
    )
    assert f"L0-L{EXPECTED_L_MAX}" in content, (
        f"L-range should be updated to L0-L{EXPECTED_L_MAX}. Got: {content}"
    )


# ---------------------------------------------------------------------------
# L12 fix tests
# ---------------------------------------------------------------------------

def test_lint_fix_l12_broken_markdown_link(_isolate_myco_project: Path) -> None:
    """Broken markdown link syntax is removed, keeping display text."""
    project = _isolate_myco_project

    doc = project / "docs" / "example.md"
    doc.write_text(
        "# Example\n\n"
        "See [the guide](nonexistent/path.md) for details.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_internal_link_integrity(canon, project)

    l12_issues = [i for i in issues if i[0] == "L12" and i[1] == "MEDIUM"]
    assert l12_issues, "L12 must detect broken markdown link"

    fixed = _fix_l12_broken_links(project, l12_issues, canon)
    assert fixed > 0, "L12 fix should have modified at least one file"

    content = doc.read_text(encoding="utf-8")
    assert "[the guide](nonexistent/path.md)" not in content, (
        "Broken link syntax should be removed"
    )
    assert "the guide" in content, (
        "Display text should be preserved"
    )


def test_lint_fix_l12_broken_backtick_path(_isolate_myco_project: Path) -> None:
    """Broken backtick path reference backticks are removed."""
    project = _isolate_myco_project

    doc = project / "docs" / "example.md"
    doc.write_text(
        "# Example\n\n"
        "Check `nonexistent/config.yaml` for settings.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_internal_link_integrity(canon, project)

    l12_issues = [i for i in issues if i[0] == "L12" and i[1] == "LOW"]
    assert l12_issues, "L12 must detect broken backtick path"

    fixed = _fix_l12_broken_links(project, l12_issues, canon)
    assert fixed > 0, "L12 fix should have modified at least one file"

    content = doc.read_text(encoding="utf-8")
    assert "`nonexistent/config.yaml`" not in content, (
        "Backtick wrapping should be removed"
    )
    assert "nonexistent/config.yaml" in content, (
        "Path text should be preserved (just without backticks)"
    )


# ---------------------------------------------------------------------------
# L16 fix tests
# ---------------------------------------------------------------------------

def test_lint_fix_l16_boot_brief_missing(_isolate_myco_project: Path) -> None:
    """Missing boot brief is created when enabled in canon."""
    project = _isolate_myco_project

    _write_canon_with_claims(project, boot_brief=True)

    canon = load_canon(project)

    # Simulate the L16 issue (brief is missing)
    brief_path = project / ".myco_state" / "boot_brief.md"
    assert not brief_path.exists(), "Brief should not exist yet"

    issues = [
        ("L16", "MEDIUM", ".myco_state/boot_brief.md",
         "boot brief is missing but boot_brief.enabled=true. "
         "Run `myco hunger` to regenerate.")
    ]

    fixed = _fix_l16_boot_brief(project, issues, canon)
    assert fixed > 0, "L16 fix should have created the brief"
    assert brief_path.exists(), "Boot brief file should now exist"


# ---------------------------------------------------------------------------
# Idempotency test
# ---------------------------------------------------------------------------

def test_lint_fix_idempotent(_isolate_myco_project: Path) -> None:
    """Running fix twice on the same stale substrate produces the same result.

    This guards against double-fix corruption where the second pass
    further mutates already-corrected values.
    """
    project = _isolate_myco_project

    # Write stale README.md
    (project / "README.md").write_text(
        f"![Lint](https://img.shields.io/badge/Lint-{DRIFTED}%2F{DRIFTED}%20green-brightgreen)\n"
        f"This is the {DRIFTED}-dimension lint.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)

    # First fix pass
    issues_1 = lint_dimension_count_consistency(canon, project)
    assert issues_1, "First pass should detect issues"
    _fix_l19_dimension_count(project, issues_1, canon)

    content_after_first = (project / "README.md").read_text(encoding="utf-8")

    # Second fix pass
    issues_2 = lint_dimension_count_consistency(canon, project)
    if issues_2:
        _fix_l19_dimension_count(project, issues_2, canon)

    content_after_second = (project / "README.md").read_text(encoding="utf-8")

    assert content_after_first == content_after_second, (
        "Fix must be idempotent: running twice should produce identical content.\n"
        f"After first:  {content_after_first!r}\n"
        f"After second: {content_after_second!r}"
    )


# ---------------------------------------------------------------------------
# Integration: collect_all_issues + auto_fix_issues end-to-end
# ---------------------------------------------------------------------------

def test_lint_fix_integration_end_to_end(_isolate_myco_project: Path) -> None:
    """End-to-end: detect issues, run auto_fix_issues, verify reduction."""
    project = _isolate_myco_project

    # Write stale README.md with L19-detectable drift
    (project / "README.md").write_text(
        f"![Lint](https://img.shields.io/badge/Lint-{DRIFTED}%2F{DRIFTED}%20green-brightgreen)\n"
        f"This is the {DRIFTED}-dimension lint system.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues_before = collect_all_issues(canon, project)
    l19_before = [i for i in issues_before if i[0] == "L19"]
    assert l19_before, "Should have L19 issues before fix"

    # Run auto_fix_issues
    fixed = auto_fix_issues(project, issues_before, canon)
    assert fixed > 0, "auto_fix_issues should fix at least one file"

    # Re-check: L19 issues should be gone
    issues_after = collect_all_issues(canon, project)
    l19_after = [i for i in issues_after if i[0] == "L19"]
    assert not l19_after, (
        f"L19 issues should be resolved after auto_fix_issues. "
        f"Remaining: {l19_after}"
    )
