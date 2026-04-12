"""Wave 41 seed tests — L22 wave-seed lifecycle (raw orphan detection).

Four focused tests covering the load-bearing paths of L22 (Wave 41, v0.32.0).
Each test guards a specific Wave 41 craft decision so a regression has a
single discoverable scar class. These extend the Wave 25 / Wave 30 / Wave 31 /
Wave 38 / Wave 39 / Wave 40 seed and follow the same scar-class rationale.
Wave 41 closes the seven-step pipeline post-condition gap (anchor #3): a
``wave{N}-seed`` raw note must advance out of raw before its wave's milestone
lands in ``log.md``.

Wave 41 design coverage:

- ``test_l22_clean_substrate_passes`` exercises Wave 41 D1 base case: when
  ``notes/`` and ``log.md`` are both empty (or contain no orphans), L22
  returns an empty issue list. Without this test, L22 could be permanently
  red against its own home repo and the team would learn to ignore it
  (Goodhart class — same failure shape Wave 38/39/40 D1 already guard).

- ``test_l22_orphan_caught_high`` exercises Wave 41 D1 + D4: the principal
  scar class — a raw note tagged ``wave25-seed`` while ``**Wave 25 landed**``
  already appears in ``log.md`` must surface as a HIGH issue against the
  note path with the actionable advance hint (``myco digest --to extracted``).
  This is the exact pattern that justified the entire lint dimension (the
  7 stale wave25-32 seeds discovered in the Wave 41 scout).

- ``test_l22_pre_landing_seed_silent_pass`` exercises Wave 41 §0.2 + the
  in-flight wave clause: a raw seed tagged ``wave42-seed`` while wave 42
  has NOT yet landed in log.md is legitimate in-flight evidence and must
  NOT be flagged. This is the false-positive escape that protects every
  active wave's seed bundle from being marked as a violation while the
  wave is still being crafted.

- ``test_l22_no_tag_raw_silent_pass`` exercises Wave 41 §0.2 + Wave 41 D1
  scoping: a raw note with no ``wave\\d+-seed`` tag is OUT of L22's scope
  (other lint dimensions handle generic raw backlog via hunger thresholds).
  Without this test, L22 could grow into "every raw note is an orphan",
  punishing the substrate's normal raw backlog and conflating with
  ``raw_backlog``/``stale_raw`` hunger signals.
"""

from __future__ import annotations

from pathlib import Path

from myco.lint import (
    lint_wave_seed_orphan,
    load_canon,
)


# Helper: a minimal valid note frontmatter that L22 can parse. The note id
# is derived from the file stem; status + tags are the fields L22 actually
# inspects. Other fields are present so L10 (notes schema) would accept the
# note shape — though L10 is not invoked by these tests.
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_l22_clean_substrate_passes(_isolate_myco_project: Path) -> None:
    """Wave 41 D1 base case: empty notes/ + empty log.md → no issues.

    The conftest fixture provides an empty ``notes/`` and an empty ``log.md``.
    L22 must return an empty issue list. This is the empty-input invariant —
    without it, L22 could be red against its own home repo and the team would
    normalize ignoring it.
    """
    project = _isolate_myco_project
    canon = load_canon(project)
    issues = lint_wave_seed_orphan(canon, project)

    assert issues == [], (
        f"L22 must produce zero issues against a clean substrate (empty "
        f"notes/, empty log.md). Got: {issues}"
    )


def test_l22_orphan_caught_high(_isolate_myco_project: Path) -> None:
    """Wave 41 D1 + D4: raw wave25-seed when Wave 25 landed → HIGH issue.

    Writes a raw note tagged ``wave25-seed`` and a log.md with a
    ``**Wave 25 landed**`` milestone. L22 must surface a HIGH severity issue
    against the note path with the actionable advance hint. This guards the
    exact scar class that justified Wave 41 (7 stale wave25-32 seeds in
    notes/ at scout time).
    """
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
    assert high_issues, (
        f"L22 must surface a raw wave25-seed orphan as a HIGH issue against "
        f"the note path with the advance hint. Got issues: {issues}"
    )


def test_l22_pre_landing_seed_silent_pass(_isolate_myco_project: Path) -> None:
    """Wave 41 §0.2: raw wave42-seed while Wave 42 NOT yet landed → no issues.

    Writes a raw note tagged ``wave42-seed`` and a log.md that only contains
    a Wave 25 milestone (Wave 42 has NOT landed). L22 must NOT flag the wave42
    seed because the wave is still in-flight and the seed is legitimate
    evidence input. This is the false-positive escape that protects active
    wave seed bundles.
    """
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

    assert issues == [], (
        f"L22 must NOT flag a wave42-seed when Wave 42 has not yet landed in "
        f"log.md (in-flight wave clause — Wave 41 §0.2). Got: {issues}"
    )


def test_l22_no_tag_raw_silent_pass(_isolate_myco_project: Path) -> None:
    """Wave 41 D1 scoping: raw note with no wave-seed tag → no issues.

    Writes a raw note with non-wave tags (``forage-digest``, ``hermes-agent``)
    while Wave 25 has landed. L22 must NOT flag this note because it is OUT
    of scope — generic raw backlog is the responsibility of hunger's
    ``raw_backlog`` / ``stale_raw`` signals, not L22. This guards against L22
    growing into "every raw note is an orphan".
    """
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

    assert issues == [], (
        f"L22 must NOT flag a raw note that has no wave-seed tag (out of "
        f"scope per Wave 41 D1 — generic raw backlog is hunger's job). "
        f"Got: {issues}"
    )
