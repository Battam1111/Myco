"""Wave 39 seed tests — L20 translation mirror consistency.

Four focused tests covering the load-bearing paths of L20 (Wave 39, v0.30.0).
Each test guards a specific Wave 39 craft decision so a regression has a
single discoverable scar class. These extend the Wave 25 / Wave 30 / Wave 31 /
Wave 38 seed and follow the same scar-class rationale.

Wave 39 design coverage:

- ``test_l20_clean_substrate_passes`` exercises Wave 39 D1 (5-tuple skeleton
  parity SSoT) base case: when all 3 locale READMEs share the same
  ``(h2, h3, code, table_rows, badge)`` skeleton, L20 returns an empty issue
  list. Without this test, L20 could be permanently red against its own home
  repo and the team would learn to ignore it (Goodhart class — the same
  failure shape Wave 38 D1 already guards against).

- ``test_l20_section_drop_caught`` exercises Wave 39 D1 + D4: dropping a `##`
  section from one locale must surface as a HIGH severity issue against
  the drifted file. This is the principal scar class L20 was built for —
  silent drift between locales where one language readers see a degraded
  substrate while another sees a healthy one.

- ``test_l20_skip_marker_respected`` exercises Wave 39 D5: a section preceded
  by ``<!-- l20-skip -->`` on the previous non-blank line is excluded from
  the skeleton count. This is the escape hatch for intentional locale-specific
  sections (e.g. a Chinese-only "致谢" or Japanese-only "謝辞") that the lint
  rule must NOT flag as drift. Without this test, the skip marker could
  silently degrade and force every locale-specific section into a workaround.

- ``test_l20_code_fence_aware`` exercises Wave 39 D6: H2/H3 lines inside
  fenced code blocks (e.g. inline markdown examples in a bash code block)
  are NOT counted as structural headings. Without this test, the parser
  could regress into a naive prefix scan that conflates documentation
  headings with prose content shown inside code samples.
"""

from __future__ import annotations

from pathlib import Path

from myco.immune import (
    _count_skeleton,
    _L20_SKIP_MARKER,
    lint_translation_mirror_consistency,
    load_canon,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_l20_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """Wave 39 D1 base case: 3 locale READMEs with identical skeletons → no issues.

    Writes minimal but parallel structures into all 3 locale READMEs (same
    h2/h3/code/table_rows/badge counts), runs L20, asserts empty issue list.
    This is the empty-input invariant — without it, L20 could be red against
    its own home repo and the team would normalize ignoring it.
    """
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

    assert issues == [], (
        f"L20 must produce zero issues against a clean substrate where "
        f"all 3 locale READMEs share the same skeleton tuple. Got: {issues}"
    )


def test_l20_section_drop_caught(_isolate_myco_project: Path) -> None:
    """Wave 39 D1 + D4: dropping a `##` from README_zh.md surfaces as HIGH.

    Writes a 2-section README.md and a 1-section README_zh.md (same h3/code/
    table/badge counts but different h2 counts). L20 must surface this as a
    HIGH severity issue against README_zh.md naming the h2 component.
    """
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
    assert h2_issues, (
        f"L20 must surface a section drop in README_zh.md (h2: 2 → 1) as a "
        f"HIGH severity issue naming the h2 component. Got issues: {issues}"
    )


def test_l20_skip_marker_respected(_isolate_myco_project: Path) -> None:
    """Wave 39 D5: a section preceded by the skip marker is excluded from counts.

    Writes a 2-section README.md and a 3-section README_zh.md where the extra
    section is marked with ``<!-- l20-skip -->``. L20 must produce zero issues
    because the skip marker excludes that section from the h2_count, restoring
    parity. Without this test, locale-specific sections (e.g. a Chinese-only
    "致谢") would force operators to either remove them or accept lint red.
    """
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

    assert issues == [], (
        f"L20 must respect the skip marker — the marked '致谢' section must "
        f"NOT count toward h2, restoring parity with README.md. Got: {issues}"
    )

    # Also assert via _count_skeleton directly that the marker is honored.
    zh_content = (project / "README_zh.md").read_text(encoding="utf-8")
    h2, h3, code, table_rows, badge = _count_skeleton(zh_content)
    assert h2 == 2, (
        f"_count_skeleton must return h2=2 (the marked '致谢' is excluded), "
        f"got h2={h2}"
    )


def test_l20_code_fence_aware(_isolate_myco_project: Path) -> None:
    """Wave 39 D6: H2/H3 lines inside fenced code blocks are not counted.

    Writes a README.md and README_zh.md where one file has a code fence
    containing a `## fake heading` line. The parser must NOT count it as a
    real heading; otherwise the two files would appear to have different
    h2_counts and L20 would emit a false positive. This guards the parser
    against the naive `line.startswith("## ")` regression.
    """
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

    assert issues == [], (
        f"L20 must be code-fence aware — `## fake heading` inside a fence "
        f"must not count as h2. Got: {issues}"
    )

    # Direct skeleton check: each file has h2=1, h3=0, code=1
    en_skel = _count_skeleton((project / "README.md").read_text(encoding="utf-8"))
    zh_skel = _count_skeleton((project / "README_zh.md").read_text(encoding="utf-8"))
    assert en_skel[0] == 1, f"English h2 must be 1 (fence content excluded), got {en_skel[0]}"
    assert en_skel[1] == 0, f"English h3 must be 0 (fence content excluded), got {en_skel[1]}"
    assert en_skel[2] == 1, f"English code count must be 1, got {en_skel[2]}"
    assert zh_skel[0] == 1, f"Chinese h2 must be 1 (fence content excluded), got {zh_skel[0]}"
    assert zh_skel == en_skel, (
        f"Both files must compute identical skeletons after fence-aware "
        f"parsing. en={en_skel}, zh={zh_skel}"
    )
