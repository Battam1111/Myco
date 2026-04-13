"""Tests for L12 Internal Link Integrity lint dimension.

Four focused tests covering the load-bearing paths of L12:

- ``test_l12_broken_markdown_link``: a markdown link to a non-existent file
  must surface as a MEDIUM issue. This is the primary scar class — clickable
  links that 404 are the most user-visible broken reference.

- ``test_l12_valid_markdown_link``: a markdown link to an existing file must
  produce zero issues. Without this test, L12 could false-positive on every
  internal link and the team would learn to ignore it.

- ``test_l12_skips_external_urls``: external URLs (https://) must NOT be
  flagged. L12 only checks internal (relative) links — external link
  validation is out of scope (network-dependent, flaky).

- ``test_l12_broken_backtick_path``: a backtick path reference to a
  non-existent file must surface as a LOW issue. Backtick paths are
  informational (not clickable), so they get lower severity than markdown
  links.
"""

from __future__ import annotations

from pathlib import Path

from myco.lint import (
    lint_internal_link_integrity,
    load_canon,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_l12_broken_markdown_link(_isolate_myco_project: Path) -> None:
    """Markdown link to non-existent file -> MEDIUM issue."""
    project = _isolate_myco_project

    doc = project / "docs" / "example.md"
    doc.write_text(
        "# Example\n"
        "\n"
        "See [the guide](nonexistent.md) for details.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_internal_link_integrity(canon, project)

    medium_issues = [
        i for i in issues
        if i[0] == "L12"
        and i[1] == "MEDIUM"
        and "nonexistent.md" in i[3]
    ]
    assert medium_issues, (
        f"L12 must surface a broken markdown link as a MEDIUM issue. "
        f"Got issues: {issues}"
    )


def test_l12_valid_markdown_link(_isolate_myco_project: Path) -> None:
    """Markdown link to existing file -> no issues from that link."""
    project = _isolate_myco_project

    # Create target file so the link is valid.
    target = project / "docs" / "guide.md"
    target.write_text("# Guide\n\nContent here.\n", encoding="utf-8")

    doc = project / "docs" / "example.md"
    doc.write_text(
        "# Example\n"
        "\n"
        "See [the guide](guide.md) for details.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_internal_link_integrity(canon, project)

    # Filter to only L12 issues from docs/example.md referencing guide.md.
    link_issues = [
        i for i in issues
        if i[0] == "L12"
        and "guide.md" in i[3]
    ]
    assert link_issues == [], (
        f"L12 must NOT flag a valid markdown link to an existing file. "
        f"Got issues: {link_issues}"
    )


def test_l12_skips_external_urls(_isolate_myco_project: Path) -> None:
    """External URL (https://) -> no issues."""
    project = _isolate_myco_project

    doc = project / "docs" / "example.md"
    doc.write_text(
        "# Example\n"
        "\n"
        "See [example](https://example.com) for details.\n"
        "Also [docs](http://docs.example.com/guide).\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_internal_link_integrity(canon, project)

    url_issues = [
        i for i in issues
        if i[0] == "L12"
        and ("example.com" in i[3] or "docs.example.com" in i[3])
    ]
    assert url_issues == [], (
        f"L12 must NOT flag external URLs. Got issues: {url_issues}"
    )


def test_l12_broken_backtick_path(_isolate_myco_project: Path) -> None:
    """Backtick path to non-existent file -> LOW issue."""
    project = _isolate_myco_project

    doc = project / "docs" / "example.md"
    doc.write_text(
        "# Example\n"
        "\n"
        "The module lives at `nonexistent/file.py` in the source tree.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_internal_link_integrity(canon, project)

    low_issues = [
        i for i in issues
        if i[0] == "L12"
        and i[1] == "LOW"
        and "nonexistent/file.py" in i[3]
    ]
    assert low_issues, (
        f"L12 must surface a broken backtick path reference as a LOW issue. "
        f"Got issues: {issues}"
    )
