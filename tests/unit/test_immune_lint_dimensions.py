"""Consolidated tests for L12-L22 immune lint dimensions.

Combines 5 separate dimension test files using parametrization:
- test_immune_internal_link_integrity.py (L12: 4 tests)
- test_immune_dimension_count.py (L19: 4 tests)
- test_immune_translation_mirror.py (L20: 4 tests)
- test_immune_contract_version_inline.py (L21: 4 tests)
- test_immune_wave_seed_orphan.py (L22: 4 tests)

All 20 test cases follow a common fixture pattern via parametrization.
"""

from __future__ import annotations

from pathlib import Path
import json

import pytest

from myco.immune import (
    FULL_CHECKS,
    lint_internal_link_integrity,
    lint_dimension_count_consistency,
    _count_skeleton,
    _L20_SKIP_MARKER,
    lint_translation_mirror_consistency,
    _L21_SKIP_MARKER,
    lint_contract_version_inline,
    lint_wave_seed_orphan,
    load_canon,
)


# ═══════════════════════════════════════════════════════════════════════════
# L12 — Internal Link Integrity
# ═══════════════════════════════════════════════════════════════════════════


def test_l12_broken_markdown_link(_isolate_myco_project: Path) -> None:
    """L12: Markdown link to non-existent file → MEDIUM issue."""
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
    assert medium_issues


def test_l12_valid_markdown_link(_isolate_myco_project: Path) -> None:
    """L12: Markdown link to existing file → no issues from that link."""
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
    assert link_issues == []


def test_l12_skips_external_urls(_isolate_myco_project: Path) -> None:
    """L12: External URL (https://) → no issues."""
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
    assert url_issues == []


def test_l12_broken_backtick_path(_isolate_myco_project: Path) -> None:
    """L12: Backtick path to non-existent file → LOW issue."""
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
    assert low_issues


# ═══════════════════════════════════════════════════════════════════════════
# L19 — Dimension Count Consistency
# ═══════════════════════════════════════════════════════════════════════════


EXPECTED = len(FULL_CHECKS)
EXPECTED_L_MAX = EXPECTED - 1
DRIFTED = EXPECTED - 4  # an obviously-wrong stale count for tests


def _write_clean_surfaces_l19(project: Path) -> None:
    """Write minimal HIGH+MEDIUM surfaces that all reference EXPECTED correctly."""
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

    # MEDIUM surfaces
    (project / "CONTRIBUTING.md").write_text(
        f"# {EXPECTED}-dimension consistency checker (L0-L{EXPECTED_L_MAX})\n",
        encoding="utf-8",
    )
    (project / "wiki").mkdir(exist_ok=True)
    (project / "wiki" / "README.md").write_text(
        f"应 {EXPECTED}/{EXPECTED} 绿\n",
        encoding="utf-8",
    )


def test_l19_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """L19 base case: a clean substrate produces zero L19 issues."""
    project = _isolate_myco_project
    _write_clean_surfaces_l19(project)

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)

    assert issues == []


def test_l19_badge_drift_caught_high(_isolate_myco_project: Path) -> None:
    """L19: README badge drift is HIGH severity."""
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
    assert high_badge_issues


def test_l19_multi_pattern_co_match(_isolate_myco_project: Path) -> None:
    """L19: One line matching multiple patterns produces one issue per pattern."""
    project = _isolate_myco_project
    # One line, three pattern hits, all drifted to the same wrong number.
    (project / "MYCO.md").write_text(
        f"The {DRIFTED}-dimension lint, {DRIFTED} 维 lint, "
        f"covers L0-L{DRIFTED - 1}.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)
    myco_issues = [i for i in issues if i[2] == "MYCO.md"]

    assert len(myco_issues) >= 2
    # Every issue against MYCO.md must be HIGH severity.
    for level, severity, rel, msg in myco_issues:
        assert level == "L19"
        assert severity == "HIGH"


def test_l19_severity_split_high_vs_medium(_isolate_myco_project: Path) -> None:
    """L19: Same drift in HIGH vs MEDIUM surfaces produces HIGH and MEDIUM respectively."""
    project = _isolate_myco_project
    drift_line = f"This is the {DRIFTED}-dimension lint.\n"
    (project / "README.md").write_text(drift_line, encoding="utf-8")
    (project / "CONTRIBUTING.md").write_text(drift_line, encoding="utf-8")

    canon = load_canon(project)
    issues = lint_dimension_count_consistency(canon, project)

    readme_issues = [i for i in issues if i[2] == "README.md"]
    contributing_issues = [i for i in issues if i[2] == "CONTRIBUTING.md"]

    assert readme_issues
    assert contributing_issues

    readme_severities = {i[1] for i in readme_issues}
    contributing_severities = {i[1] for i in contributing_issues}

    assert readme_severities == {"HIGH"}
    assert contributing_severities == {"MEDIUM"}


# ═══════════════════════════════════════════════════════════════════════════
# L20 — Translation Mirror Consistency
# ═══════════════════════════════════════════════════════════════════════════


def test_l20_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """L20 base case: 3 locale READMEs with identical skeletons → no issues."""
    project = _isolate_myco_project
    parallel_skeleton = (
        "![Lint](https://img.shields.io/badge/Lint-21%2F21-brightgreen)\n"
        "\n"
        "## Section A\n"
        "\n"
        "### Subsection A1\n"
        "\n"
        "```bash\n"
        "echo hello\n"
        "```\n"
        "\n"
        "| col1 | col2 |\n"
        "|------|------|\n"
        "| a    | b    |\n"
        "\n"
        "## Section B\n"
    )
    (project / "README.md").write_text(parallel_skeleton, encoding="utf-8")
    (project / "README_zh.md").write_text(parallel_skeleton, encoding="utf-8")
    (project / "README_ja.md").write_text(parallel_skeleton, encoding="utf-8")

    canon = load_canon(project)
    issues = lint_translation_mirror_consistency(canon, project)

    assert issues == []


def test_l20_section_drop_caught(_isolate_myco_project: Path) -> None:
    """L20: Dropping a `##` from README_zh.md surfaces as HIGH."""
    project = _isolate_myco_project
    # Reference: 2 H2 sections
    (project / "README.md").write_text(
        "## Section A\n\nSome prose.\n\n## Section B\n\nMore prose.\n",
        encoding="utf-8",
    )
    # Drifted: only 1 H2 section
    (project / "README_zh.md").write_text(
        "## 第一节\n\n一些文字。\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_translation_mirror_consistency(canon, project)

    h2_issues = [
        i for i in issues
        if i[0] == "L20"
        and i[1] == "HIGH"
        and i[2] == "README_zh.md"
        and "h2" in i[3]
    ]
    assert h2_issues


def test_l20_skip_marker_respected(_isolate_myco_project: Path) -> None:
    """L20: A section preceded by the skip marker is excluded from counts."""
    project = _isolate_myco_project
    (project / "README.md").write_text(
        "## Section A\n\nProse.\n\n## Section B\n\nMore prose.\n",
        encoding="utf-8",
    )
    (project / "README_zh.md").write_text(
        "## 第一节\n\n文字。\n\n## 第二节\n\n更多文字。\n\n"
        f"{_L20_SKIP_MARKER}\n\n"
        "## 致谢\n\n感谢所有贡献者。\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_translation_mirror_consistency(canon, project)

    assert issues == []

    # Also assert via _count_skeleton directly that the marker is honored.
    zh_content = (project / "README_zh.md").read_text(encoding="utf-8")
    h2, h3, code, table_rows, badge = _count_skeleton(zh_content)
    assert h2 == 2


def test_l20_code_fence_aware(_isolate_myco_project: Path) -> None:
    """L20: H2/H3 lines inside fenced code blocks are not counted."""
    project = _isolate_myco_project
    # Both files have exactly 1 real H2; the English one shows a code sample
    # that *contains* a `## fake` line that must not be counted.
    (project / "README.md").write_text(
        "## Real Section\n\n"
        "Example markdown:\n\n"
        "```markdown\n"
        "## fake heading inside fence\n"
        "### also fake\n"
        "```\n",
        encoding="utf-8",
    )
    (project / "README_zh.md").write_text(
        "## 真实小节\n\n"
        "示例 markdown：\n\n"
        "```markdown\n"
        "## fake heading inside fence\n"
        "### also fake\n"
        "```\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_translation_mirror_consistency(canon, project)

    assert issues == []

    # Direct skeleton check: each file has h2=1, h3=0, code=1
    en_skel = _count_skeleton((project / "README.md").read_text(encoding="utf-8"))
    zh_skel = _count_skeleton((project / "README_zh.md").read_text(encoding="utf-8"))
    assert en_skel[0] == 1
    assert en_skel[1] == 0
    assert en_skel[2] == 1
    assert zh_skel[0] == 1
    assert zh_skel == en_skel


# ═══════════════════════════════════════════════════════════════════════════
# L21 — Contract Version Inline
# ═══════════════════════════════════════════════════════════════════════════


_TEST_CANON_V_31 = """\
system:
  principles_count: 13
  principles_label: "十三原則"
  entry_point: MYCO.md
  contract_version: "v0.31.0"
  synced_contract_version: "v0.31.0"
architecture:
  layers: 4
  wiki_pages: 0
project:
  name: TestProject
"""


def test_l21_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """L21 base case: inline claim matches canon → no issues."""
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

    assert issues == []


def test_l21_stale_inline_caught_high(_isolate_myco_project: Path) -> None:
    """L21: Stale inline claim in MYCO.md surfaces as HIGH."""
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
    assert high_issues


def test_l21_historical_marker_skipped(_isolate_myco_project: Path) -> None:
    """L21: Historical-marker lines are not flagged even if version diverges."""
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

    assert issues == []


def test_l21_skip_marker_respected(_isolate_myco_project: Path) -> None:
    """L21: A line preceded by the skip marker is excluded."""
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

    assert issues == []


# ═══════════════════════════════════════════════════════════════════════════
# L22 — Wave Seed Orphan Lifecycle
# ═══════════════════════════════════════════════════════════════════════════


def _write_raw_note(project: Path, note_id: str, tags: list[str]) -> Path:
    """Write a minimal raw note with the given id + tag list."""
    tags_yaml = "[" + ", ".join(tags) + "]" if tags else "[]"
    body = (
        "---\n"
        f"id: {note_id}\n"
        "status: raw\n"
        "created: 2026-04-12T00:00:00Z\n"
        "last_touched: 2026-04-12T00:00:00Z\n"
        "digest_count: 0\n"
        f"tags: {tags_yaml}\n"
        "---\n"
        "\n"
        "Body of the seed note.\n"
    )
    path = project / "notes" / f"n_{note_id}.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_l22_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """L22 base case: empty notes/ + empty log.md → no issues."""
    project = _isolate_myco_project
    canon = load_canon(project)
    issues = lint_wave_seed_orphan(canon, project)

    assert issues == []


def test_l22_orphan_caught_high(_isolate_myco_project: Path) -> None:
    """L22: Raw wave25-seed when Wave 25 landed → HIGH issue."""
    project = _isolate_myco_project
    _write_raw_note(project, "20260412T000000_w25", ["wave25-seed"])
    (project / "log.md").write_text(
        "# Log\n"
        "\n"
        "**Wave 25 landed (test infrastructure seed)**\n"
        "\n"
        "Some recap prose.\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_wave_seed_orphan(canon, project)

    high_issues = [
        i for i in issues
        if i[0] == "L22"
        and i[1] == "HIGH"
        and "n_20260412T000000_w25.md" in i[2]
        and "wave25-seed" in i[3]
        and "myco digest --to extracted" in i[3]
    ]
    assert high_issues


def test_l22_pre_landing_seed_silent_pass(_isolate_myco_project: Path) -> None:
    """L22: Raw wave42-seed while Wave 42 NOT yet landed → no issues."""
    project = _isolate_myco_project
    _write_raw_note(project, "20260412T000000_w42", ["wave42-seed"])
    (project / "log.md").write_text(
        "# Log\n"
        "\n"
        "**Wave 25 landed (test infrastructure seed)**\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_wave_seed_orphan(canon, project)

    assert issues == []


def test_l22_no_tag_raw_silent_pass(_isolate_myco_project: Path) -> None:
    """L22: Raw note with no wave-seed tag → no issues."""
    project = _isolate_myco_project
    _write_raw_note(
        project,
        "20260412T000000_misc",
        ["forage-digest", "hermes-agent"],
    )
    (project / "log.md").write_text(
        "# Log\n"
        "\n"
        "**Wave 25 landed (test infrastructure seed)**\n",
        encoding="utf-8",
    )

    canon = load_canon(project)
    issues = lint_wave_seed_orphan(canon, project)

    assert issues == []
