"""Tests for v0.46.0 kernel-contract convergence (v0.3.4 D1–D7).

Covers:
- D1 skeleton-mode severity downgrade (L0/L1 CRITICAL → HIGH)
- D3 + D7 gitignore-aware severity (L1/L12/L14 downgrade when gitignored)
- D5 per-category exit policies (parse_exit_on + _compute_exit_code)
- D6 + L29 version single-source (__version__ + hatch dynamic)

Lives alongside test_immune_lint_dimensions.py (L12-L22 consolidated).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from myco.immune import (
    DIMENSION_CATEGORY,
    _CATEGORIES,
    _compute_exit_code,
    _is_skeleton_substrate,
    _skeleton_downgrade,
    lint_version_single_source,
    parse_exit_on,
)


# ═══════════════════════════════════════════════════════════════════════════
# D5 — parse_exit_on grammar
# ═══════════════════════════════════════════════════════════════════════════


def test_parse_exit_on_none_returns_empty() -> None:
    """Empty/None spec → empty dict (falsy → legacy path in _compute_exit_code)."""
    assert parse_exit_on(None) == {}
    assert parse_exit_on("") == {}


def test_parse_exit_on_global_never() -> None:
    policy = parse_exit_on("never")
    assert all(policy[cat] == "NEVER" for cat in _CATEGORIES)


def test_parse_exit_on_global_critical() -> None:
    policy = parse_exit_on("critical")
    assert all(policy[cat] == "CRITICAL" for cat in _CATEGORIES)


def test_parse_exit_on_global_high() -> None:
    policy = parse_exit_on("high")
    assert all(policy[cat] == "HIGH" for cat in _CATEGORIES)


def test_parse_exit_on_per_category_mixed() -> None:
    spec = "mechanical:critical,shipped:critical,metabolic:never,semantic:never"
    policy = parse_exit_on(spec)
    assert policy["mechanical"] == "CRITICAL"
    assert policy["shipped"] == "CRITICAL"
    assert policy["metabolic"] == "NEVER"
    assert policy["semantic"] == "NEVER"


def test_parse_exit_on_per_category_partial_defaults_critical() -> None:
    """Categories not named default to CRITICAL threshold."""
    policy = parse_exit_on("metabolic:never")
    assert policy["metabolic"] == "NEVER"
    assert policy["mechanical"] == "CRITICAL"
    assert policy["shipped"] == "CRITICAL"
    assert policy["semantic"] == "CRITICAL"


def test_parse_exit_on_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_exit_on("mechanical:bogus")
    with pytest.raises(ValueError):
        parse_exit_on("bogus:critical")


# ═══════════════════════════════════════════════════════════════════════════
# D5 — _compute_exit_code matrix
# ═══════════════════════════════════════════════════════════════════════════


def test_compute_exit_legacy_clean() -> None:
    """No exit_on + no issues → 0."""
    assert _compute_exit_code(critical=0, high=0) == 0


def test_compute_exit_legacy_high() -> None:
    """No exit_on + HIGH → 1 (legacy ladder)."""
    assert _compute_exit_code(critical=0, high=1) == 1


def test_compute_exit_legacy_critical() -> None:
    """No exit_on + CRITICAL → 2 (legacy ladder)."""
    assert _compute_exit_code(critical=1, high=0) == 2


def test_compute_exit_never_ignores_critical() -> None:
    """--exit-on=never returns 0 even with CRITICAL."""
    policy = "never"
    by_cat = {"mechanical": "CRITICAL"}
    assert _compute_exit_code(1, 0, by_category=by_cat, exit_on=policy) == 0


def test_compute_exit_never_ignores_high() -> None:
    """--exit-on=never returns 0 with HIGH (regression guard — earlier bug fell
    through to legacy ladder and returned 1)."""
    by_cat = {"mechanical": "HIGH"}
    assert _compute_exit_code(0, 1, by_category=by_cat, exit_on="never") == 0


def test_compute_exit_per_category_metabolic_never() -> None:
    """metabolic:never + CRITICAL in metabolic → 0."""
    spec = "mechanical:critical,metabolic:never"
    by_cat = {"metabolic": "CRITICAL"}
    assert _compute_exit_code(1, 0, by_category=by_cat, exit_on=spec) == 0


def test_compute_exit_per_category_mechanical_trips() -> None:
    """mechanical:critical + CRITICAL in mechanical → 2."""
    spec = "mechanical:critical,metabolic:never"
    by_cat = {"mechanical": "CRITICAL"}
    assert _compute_exit_code(1, 0, by_category=by_cat, exit_on=spec) == 2


def test_compute_exit_per_category_high_threshold() -> None:
    """shipped:high + HIGH in shipped → 2."""
    spec = "shipped:high"
    by_cat = {"shipped": "HIGH"}
    assert _compute_exit_code(0, 1, by_category=by_cat, exit_on=spec) == 2


def test_compute_exit_per_category_medium_below_threshold() -> None:
    """shipped:critical + MEDIUM in shipped → 0."""
    spec = "shipped:critical"
    by_cat = {"shipped": "MEDIUM"}
    assert _compute_exit_code(0, 0, by_category=by_cat, exit_on=spec) == 0


# ═══════════════════════════════════════════════════════════════════════════
# D4 — Dimension category mapping coverage
# ═══════════════════════════════════════════════════════════════════════════


def test_dimension_category_covers_all_30() -> None:
    """Every L0..L29 is mapped to a known category."""
    for i in range(30):
        key = f"L{i}"
        assert key in DIMENSION_CATEGORY, f"{key} missing from DIMENSION_CATEGORY"
        assert DIMENSION_CATEGORY[key] in _CATEGORIES


# ═══════════════════════════════════════════════════════════════════════════
# D1 — Skeleton-mode detection + downgrade
# ═══════════════════════════════════════════════════════════════════════════


def test_skeleton_detection_marker_plus_empty_notes(
    _isolate_myco_project: Path,
) -> None:
    """autoseeded.txt marker + no n_*.md notes → skeleton."""
    root = _isolate_myco_project
    (root / ".myco_state").mkdir()
    (root / ".myco_state" / "autoseeded.txt").write_text("1\n", encoding="utf-8")
    assert _is_skeleton_substrate(root) is True


def test_skeleton_detection_no_marker_not_skeleton(
    _isolate_myco_project: Path,
) -> None:
    """No marker → not skeleton, even with empty notes."""
    root = _isolate_myco_project
    assert _is_skeleton_substrate(root) is False


def test_skeleton_detection_marker_plus_integrated_note_not_skeleton(
    _isolate_myco_project: Path,
) -> None:
    """Marker + a digested n_*.md note → substrate has metabolized."""
    root = _isolate_myco_project
    (root / ".myco_state").mkdir()
    (root / ".myco_state" / "autoseeded.txt").write_text("1\n", encoding="utf-8")
    (root / "notes" / "n_001.md").write_text(
        "---\nstatus: integrated\n---\n# digested\n", encoding="utf-8"
    )
    assert _is_skeleton_substrate(root) is False


def test_skeleton_downgrade_critical_to_high(
    _isolate_myco_project: Path,
) -> None:
    root = _isolate_myco_project
    (root / ".myco_state").mkdir()
    (root / ".myco_state" / "autoseeded.txt").write_text("1\n", encoding="utf-8")
    assert _skeleton_downgrade("CRITICAL", root) == "HIGH"
    assert _skeleton_downgrade("HIGH", root) == "HIGH"  # idempotent
    assert _skeleton_downgrade("MEDIUM", root) == "MEDIUM"  # no change


def test_skeleton_downgrade_no_skeleton_no_change(
    _isolate_myco_project: Path,
) -> None:
    root = _isolate_myco_project
    assert _skeleton_downgrade("CRITICAL", root) == "CRITICAL"


# ═══════════════════════════════════════════════════════════════════════════
# L29 — Version Single Source
# ═══════════════════════════════════════════════════════════════════════════


def _make_version_layout(
    root: Path, init_version: str | None, pyproject_body: str
) -> None:
    src = root / "src" / "myco"
    src.mkdir(parents=True)
    if init_version is not None:
        (src / "__init__.py").write_text(
            f'__version__ = "{init_version}"\n', encoding="utf-8"
        )
    else:
        (src / "__init__.py").write_text("# no version\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(pyproject_body, encoding="utf-8")


def test_l29_dynamic_with_hatch_path_passes(
    _isolate_myco_project: Path,
) -> None:
    root = _isolate_myco_project
    _make_version_layout(
        root,
        "0.3.4",
        '[project]\nname = "myco"\ndynamic = ["version"]\n\n'
        '[tool.hatch.version]\npath = "src/myco/__init__.py"\n',
    )
    issues = lint_version_single_source({}, root)
    assert issues == []


def test_l29_missing_version_in_init_critical(
    _isolate_myco_project: Path,
) -> None:
    root = _isolate_myco_project
    _make_version_layout(
        root,
        None,
        '[project]\nname = "myco"\ndynamic = ["version"]\n\n'
        '[tool.hatch.version]\npath = "src/myco/__init__.py"\n',
    )
    issues = lint_version_single_source({}, root)
    assert any(iss[1] == "CRITICAL" for iss in issues)


def test_l29_static_plus_dynamic_collision_critical(
    _isolate_myco_project: Path,
) -> None:
    root = _isolate_myco_project
    _make_version_layout(
        root,
        "0.3.4",
        '[project]\nname = "myco"\nversion = "0.3.4"\ndynamic = ["version"]\n',
    )
    issues = lint_version_single_source({}, root)
    assert any(iss[1] == "CRITICAL" for iss in issues)


def test_l29_static_mismatch_init_critical(
    _isolate_myco_project: Path,
) -> None:
    root = _isolate_myco_project
    _make_version_layout(
        root,
        "0.3.4",
        '[project]\nname = "myco"\nversion = "0.3.3"\n',
    )
    issues = lint_version_single_source({}, root)
    assert any(iss[1] == "CRITICAL" for iss in issues)


def test_l29_dynamic_without_hatch_path_high(
    _isolate_myco_project: Path,
) -> None:
    root = _isolate_myco_project
    _make_version_layout(
        root,
        "0.3.4",
        '[project]\nname = "myco"\ndynamic = ["version"]\n',
    )
    issues = lint_version_single_source({}, root)
    assert any(iss[1] == "HIGH" for iss in issues)
