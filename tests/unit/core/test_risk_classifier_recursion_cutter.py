"""Tests for v0.6.15 risk_classifier recursion-cutter + path_allowlist scan.

The recursion-cutter forces HIGH-risk classification when a craft's
``path_allowlist`` would let an auto-merge change the risk classifier
itself, governance auto-evolve canon keys, or governance workflow files.
Without it, an auto-craft could quietly classify itself as MEDIUM-risk,
auto-merge after window expiry, and hollow out the L0 P1 gates
(perpetual-motion attack — see craft v0.6.15 Round 1.5 mycoparasite T1
+ endophyte T6).

Coverage:
- craft modifying ``src/myco/core/risk_classifier.py`` → forced HIGH
- craft modifying ``_canon.yaml`` + body mentions ``auto_evolve_*`` keys → forced HIGH
- craft modifying ``.github/workflows/auto_revert.yml`` → forced HIGH
- craft modifying ``src/myco/cycle/winnow.py`` (G7 enforcement) → forced HIGH
- craft modifying classifier's own tests → forced HIGH
- craft with empty path_allowlist + benign body → MEDIUM (no recursion trigger)
- craft modifying ``L0_VISION.md`` via path_allowlist → HIGH (v0.6.0 keyword)
- craft missing path_allowlist → fail-closed HIGH

Doctrine: ``docs/architecture/L2_DOCTRINE/cycle.md`` § "Agent-First default (v0.6.15+)".
"""

from __future__ import annotations

from pathlib import Path

from myco.core.risk_classifier import (
    RiskTier,
    classify_craft_via_path_allowlist,
)


def _write_craft(
    tmp_path: Path,
    name: str,
    *,
    path_allowlist: list[str] | None,
    body: str = "# Test craft\n\nTest body content.\n",
) -> Path:
    """Helper: write a v0.6.15-shaped craft markdown."""
    fm_lines = [
        "type: craft",
        f"slug: {name}",
        "kind: design",
        "date: 2026-04-29",
        "rounds: 3",
        "status: DRAFT",
        "authored_by: human",
    ]
    if path_allowlist is not None:
        if path_allowlist:
            fm_lines.append("path_allowlist:")
            for p in path_allowlist:
                fm_lines.append(f"  - {p}")
        else:
            fm_lines.append("path_allowlist: []")
    fm = "\n".join(fm_lines)
    text = f"---\n{fm}\n---\n\n{body}"
    p = tmp_path / f"{name}.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_recursion_cutter_risk_classifier_path(tmp_path: Path) -> None:
    """path_allowlist touching risk_classifier.py → forced HIGH."""
    craft = _write_craft(
        tmp_path,
        "tweak_classifier",
        path_allowlist=["src/myco/core/risk_classifier.py"],
        body="# Tweak classifier\n\nminor refactor of regex patterns.\n",
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH
    assert "recursion-cutter" in result.rationale.lower()
    assert any("risk_classifier" in r for r in result.matched_rules)


def test_recursion_cutter_canon_auto_evolve_keys(tmp_path: Path) -> None:
    """path_allowlist=_canon.yaml + body mentions auto_evolve_* → forced HIGH."""
    craft = _write_craft(
        tmp_path,
        "flip_force_high_risk",
        path_allowlist=["_canon.yaml"],
        body=(
            "# Flip auto_evolve_force_high_risk default\n\n"
            "Change `auto_evolve_force_high_risk: true` to `false`.\n"
        ),
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH
    assert "recursion-cutter" in result.rationale.lower()


def test_recursion_cutter_auto_revert_workflow(tmp_path: Path) -> None:
    """path_allowlist touching .github/workflows/auto_revert.yml → forced HIGH."""
    craft = _write_craft(
        tmp_path,
        "tweak_auto_revert",
        path_allowlist=[".github/workflows/auto_revert.yml"],
        body="# Tweak auto-revert\n\nMinor adjustment.\n",
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH
    assert "recursion-cutter" in result.rationale.lower()


def test_recursion_cutter_winnow_path(tmp_path: Path) -> None:
    """path_allowlist touching winnow.py (G7) → forced HIGH."""
    craft = _write_craft(
        tmp_path,
        "tweak_winnow",
        path_allowlist=["src/myco/cycle/winnow.py"],
        body="# Tweak winnow gates\n\nMinor refactor of G6.\n",
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH


def test_recursion_cutter_classifier_tests_path(tmp_path: Path) -> None:
    """path_allowlist touching risk classifier tests → forced HIGH."""
    craft = _write_craft(
        tmp_path,
        "tweak_classifier_tests",
        path_allowlist=["tests/unit/core/test_risk_classifier_recursion_cutter.py"],
        body="# Update test suite\n\nMinor.\n",
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH


def test_empty_path_allowlist_is_medium(tmp_path: Path) -> None:
    """Empty path_allowlist (pure doctrine craft) → MEDIUM, no recursion trigger."""
    craft = _write_craft(
        tmp_path,
        "pure_doctrine",
        path_allowlist=[],
        body=(
            "# A doctrine-only craft\n\nThis craft proposes no code changes; "
            "purely a doctrine clarification.\n"
        ),
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.MEDIUM
    assert "doctrine" in result.rationale.lower() or "empty" in result.rationale.lower()


def test_l0_vision_path_is_high(tmp_path: Path) -> None:
    """path_allowlist touching L0_VISION.md → HIGH (v0.6.0 keyword)."""
    craft = _write_craft(
        tmp_path,
        "amend_l0",
        path_allowlist=["docs/architecture/L0_VISION.md"],
        body="# Amend L0\n\nTouch the vision doc.\n",
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH


def test_missing_path_allowlist_fails_closed_high(tmp_path: Path) -> None:
    """Craft with no path_allowlist frontmatter → fail-closed HIGH."""
    craft = _write_craft(
        tmp_path,
        "missing_allowlist",
        path_allowlist=None,  # NO path_allowlist field at all
        body="# Missing allowlist\n\nNo path_allowlist declared.\n",
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH
    assert "winnow G7" in result.rationale or "missing" in result.rationale.lower()


def test_normal_medium_path_allowlist(tmp_path: Path) -> None:
    """path_allowlist with only L2 doctrine page → MEDIUM (typical auto-craft)."""
    craft = _write_craft(
        tmp_path,
        "add_l2_section",
        path_allowlist=["docs/architecture/L2_DOCTRINE/circulation.md"],
        body="# Add a section to circulation.md\n\nMinor extension.\n",
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.MEDIUM


def test_inline_path_allowlist_form(tmp_path: Path) -> None:
    """Inline list form `path_allowlist: [a, b]` works."""
    p = tmp_path / "inline.md"
    p.write_text(
        "---\n"
        "type: craft\n"
        "slug: inline\n"
        "kind: design\n"
        "date: 2026-04-29\n"
        "rounds: 3\n"
        "status: DRAFT\n"
        "authored_by: human\n"
        'path_allowlist: ["docs/architecture/L2_DOCTRINE/cycle.md"]\n'
        "---\n\n# Inline form\n",
        encoding="utf-8",
    )
    result = classify_craft_via_path_allowlist(p)
    assert result.tier is RiskTier.MEDIUM


def test_missing_craft_file_fails_closed_high(tmp_path: Path) -> None:
    """Nonexistent craft path → fail-closed HIGH."""
    nonexistent = tmp_path / "does_not_exist.md"
    result = classify_craft_via_path_allowlist(nonexistent)
    assert result.tier is RiskTier.HIGH
    assert "missing" in result.rationale.lower() or "fail" in result.rationale.lower()


def test_no_frontmatter_fails_closed_high(tmp_path: Path) -> None:
    """Craft markdown without frontmatter → fail-closed HIGH."""
    p = tmp_path / "no_fm.md"
    p.write_text("# Body only, no frontmatter\n", encoding="utf-8")
    result = classify_craft_via_path_allowlist(p)
    assert result.tier is RiskTier.HIGH
