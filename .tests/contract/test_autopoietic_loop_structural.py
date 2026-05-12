"""Structural contract tests for v0.6.14 Cycle 自起 fruit—winnow—molt 闭环.

These tests validate the **shape** of the autopoietic-loop surfaces — they
do NOT mock the Task tool or attempt to drive primordium / stipe end-to-end.
Behavioral validation is human integration testing post-merge (the first
real `/myco-evolve` invocation on an existing distilled note).

Per craft v0.6.14 Round 2 R-T6 + R-T16, contract-test scope:

A. **canon governance fields** (11 new at v0.6.14): all present with
   correct types under `_canon.yaml::system.governance`.
B. **L0 vocabulary discipline**: branch prefix is `fruiting/` (real
   fungal taxonomy), NOT `auto-craft/` (English compound).
C. **MP1 dim host-signature**: every craft in `docs/primordia/*.md`
   carries `authored_by:` frontmatter naming a recognized host.
D. **providers/ excretion**: `src/myco/providers/` no longer exists.
E. **llm_policy enum reduced**: 2 values (`forbidden`, `opt-in`),
   `providers-declared` removed.
F. **Sixth seam doctrine**: `boundary.md` has the new section;
   `cycle.md` has "Cycle 自起 fruit—winnow—molt 闭环 (v0.6.14+)".
G. **myco-evolve mirror**: `.claude/commands/myco-evolve.md` and
   `<repo>/commands/myco-evolve.md` byte-identical.
H. **stipe --branch-only mode**: stipe.md body declares the mode.
I. **auto_revert.yml shape**: triggers correctly + posts to issue.
J. **seed script exists + valid Python**: scripts/seed_auto_evolve_tracking_issue.py.

Doctrine: docs/architecture/L2_DOCTRINE/cycle.md §"Cycle 自起 闭环 (v0.6.14+)"
       + docs/architecture/L2_DOCTRINE/boundary.md §"Sixth seam (v0.6.14+)"
Craft:    docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ===== A. canon governance fields =====


@pytest.fixture(scope="module")
def canon_data() -> dict:
    """Parsed _canon.yaml as a dict."""
    text = (_REPO_ROOT / ".myco" / "canon.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


_REQUIRED_AUTO_EVOLVE_FIELDS = {
    "auto_propose_enabled": bool,
    "auto_evolve_min_wall_clock_seconds_between": int,
    "auto_evolve_critic_count": int,
    "auto_evolve_branch_prefix": str,
    "auto_evolve_distilled_hash_cooldown_senesce": int,
    "auto_evolve_force_high_risk": bool,
    "auto_evolve_pr_window_skip": bool,
    "auto_evolve_min_distilled_severity": str,
    # auto_evolve_daily_budget_usd: null OK (float or None)
    "auto_evolve_tracking_issue_id": (int, type(None)),
    # recognized_authoring_hosts: list of strings
    "recognized_authoring_hosts": list,
}


@pytest.mark.parametrize(
    "field,expected_type",
    list(_REQUIRED_AUTO_EVOLVE_FIELDS.items()),
)
def test_canon_governance_field_present_with_type(
    canon_data: dict, field: str, expected_type: object
) -> None:
    """Each v0.6.14 governance field must be present with the right type."""
    governance = canon_data.get("system", {}).get("governance", {})
    assert field in governance, (
        f"v0.6.14 canon field `governance.{field}` missing. "
        f"Required by Cycle 自起 闭环 protocol."
    )
    value = governance[field]
    if isinstance(expected_type, tuple):
        assert isinstance(value, expected_type), (
            f"governance.{field}: expected one of {expected_type}, got {type(value).__name__}"
        )
    else:
        assert isinstance(value, expected_type), (
            f"governance.{field}: expected {expected_type.__name__}, got {type(value).__name__}"
        )


def test_canon_recognized_authoring_hosts_includes_human_and_claude_code(
    canon_data: dict,
) -> None:
    """recognized_authoring_hosts must include at least 'human' + 'claude-code-agent'."""
    hosts = canon_data["system"]["governance"]["recognized_authoring_hosts"]
    assert "human" in hosts, "recognized_authoring_hosts must include 'human'"
    assert "claude-code-agent" in hosts, (
        "recognized_authoring_hosts must include 'claude-code-agent' "
        "(primordium autonomous mode signature)"
    )


def test_canon_auto_evolve_force_high_risk_default_false(canon_data: dict) -> None:
    """v0.6.15+: Agent-First default. force_high_risk must default False.

    v0.6.14 shipped True (owner-First regression: collapsed every auto-craft
    to owner-merge-gate). Owner observation 2026-04-29: "我感觉还是给owner
    太大权限了, Myco明明是Agent-First". v0.6.15 craft Round 1.5 endophyte
    critic confirmed: paranoia_mode is an undeclared 3rd L0 P1 exception;
    the correct fix is flipping defaults, not adding an opt-in flag.

    Risk class WAS derived from craft CONTENT via core.risk_classifier
    (path_allowlist-based superset of v0.6.0 keywords + recursion-cutter)
    at v0.6.15-v0.8.4. The module was excreted at v0.8.5 — production
    code had zero imports of it across 4 minor releases since v0.6.0.
    The Agent-First default behavior still holds (verified below);
    only the unused content-derivation helper went away.
    """
    governance = canon_data["system"]["governance"]
    assert governance["auto_evolve_force_high_risk"] is False, (
        "auto_evolve_force_high_risk MUST default to False at v0.6.15+. "
        "Setting True forces every auto-craft into high-risk class regardless "
        "of content — collapses Agent-First into Owner-First. See craft "
        "v0_6_15_agent_first_default_for_cycle_autostart_loop_craft_2026-04-29."
    )


def test_canon_auto_evolve_pr_window_skip_default_false(canon_data: dict) -> None:
    """v0.6.15+: pr_window_skip must default False. Restores v0.6.0 governance.

    v0.6.14 shipped True (bypassed 7-session-7-day public window auto-LAND);
    v0.6.15 restores window-bounded governance per L0 P1.
    """
    governance = canon_data["system"]["governance"]
    assert governance["auto_evolve_pr_window_skip"] is False, (
        "auto_evolve_pr_window_skip MUST default to False at v0.6.15+. "
        "True bypasses the v0.6.0 7-session-7-day public window, making "
        "PR-merge the sole gate (owner-First). Default False restores the "
        "v0.6.0 governance public window with always-on `vetoed_at` veto."
    )


def test_canon_auto_evolve_critic_count_is_five(canon_data: dict) -> None:
    """v0.6.15+: critic_count must equal 5 (one per L0 principle P1-P5).

    v0.6.14 shipped 3 ad-hoc critics (mycoparasite/saprotroph/mycorrhiza);
    v0.6.15 refactored to 5 (chytrid/rhizomorph/mycoparasite/saprotroph/mycorrhiza)
    with each tied to one L0 principle. Per craft Round 1.5 endophyte T7
    ("derive critics from L0 P1-P5 directly, not from observed-failure patches").
    """
    governance = canon_data["system"]["governance"]
    assert governance["auto_evolve_critic_count"] == 5, (
        f"auto_evolve_critic_count MUST equal 5 at v0.6.15+ "
        f"(one per L0 P1-P5). Got {governance['auto_evolve_critic_count']}."
    )


def test_canon_no_paranoia_mode_field(canon_data: dict) -> None:
    """v0.6.15+: auto_evolve_owner_paranoia_mode field MUST NOT exist.

    Per craft Round 1.5 endophyte T3+T5: paranoia_mode would be an undeclared
    3rd L0 P1 exception (L0 names exactly two carved exceptions: brief +
    agent-calls-LLM). v0.6.15 declines to introduce it.
    """
    governance = canon_data["system"]["governance"]
    assert "auto_evolve_owner_paranoia_mode" not in governance, (
        "auto_evolve_owner_paranoia_mode MUST NOT be in canon. "
        "Per L0 P1 addendum: 'these two exceptions exhaust the list, "
        "not extend it.' A paranoia_mode flag would add a 3rd."
    )


def test_canon_auto_propose_enabled_default_false(canon_data: dict) -> None:
    """Master switch defaults OFF — autopoietic loop is opt-in."""
    governance = canon_data["system"]["governance"]
    assert governance["auto_propose_enabled"] is False, (
        "auto_propose_enabled MUST default False. v0.6.14 ships the "
        "machinery, but enabling it is per-substrate owner choice."
    )


# ===== B. L0 vocabulary discipline =====


def test_branch_prefix_is_fungal_taxonomy(canon_data: dict) -> None:
    """Branch prefix MUST be 'fruiting/' (real fungal taxonomy), not 'auto-craft/'.

    Per L0:185-186 vocabulary discipline + craft Round 2 R-T4. v0.6.0 §A1
    boundary amendment is "single carved exception, not a license"; this
    is the test that closes that policy line on the auto-evolve seam.
    """
    prefix = canon_data["system"]["governance"]["auto_evolve_branch_prefix"]
    assert prefix == "fruiting/", (
        f"auto_evolve_branch_prefix MUST be 'fruiting/' (fungal taxonomy: "
        f"fruiting body in mycology). Got {prefix!r}. Do not use English "
        f"compounds like 'auto-craft/' (L0:185-186 violation per craft "
        f"Round 2 R-T4)."
    )
    # Sanity: not the rejected English compound.
    assert "auto-craft" not in prefix.lower(), (
        f"branch prefix {prefix!r} contains 'auto-craft' — REJECTED at "
        f"craft Round 2 R-T4. Use 'fruiting/' from fungal taxonomy."
    )


# ===== C. MP1 host-signature: every craft has authored_by =====


def test_every_craft_has_authored_by_frontmatter() -> None:
    """v0.6.14 MP1 extension: every craft (type: craft) under docs/primordia/
    must have `authored_by:`.

    Scope: ``type: craft`` files only. Other primordia (handoff notes,
    audits, design-notes, release-notes) are exempt — the host-signature
    requirement is craft-specific because crafts mutate doctrine, while
    non-craft primordia record decisions already made.

    Skips files under docs/primordia/_excreted/ (auto-excreted stale DRAFTs).
    """
    primordia_dir = _REPO_ROOT / ".docs" / "primordia"
    crafts_missing = []
    for craft_path in primordia_dir.glob("*.md"):
        rel = craft_path.relative_to(_REPO_ROOT).as_posix()
        if "_excreted/" in rel:
            continue
        text = craft_path.read_text(encoding="utf-8")
        # Parse frontmatter via simple regex (mirror MP1's parser).
        if not (text.startswith("---\n") or text.startswith("---\r\n")):
            continue  # non-craft — exempt
        match = re.search(r"^---\s*$", text[4:], re.MULTILINE)
        if match is None:
            continue  # malformed — exempt
        fm_text = text[4 : 4 + match.start()]
        # Scope-restrict to type: craft.
        type_match = re.search(
            r"^\s*type\s*:\s*['\"]?([^'\"\n#]+?)['\"]?\s*(?:#.*)?$",
            fm_text,
            re.MULTILINE,
        )
        if type_match is None or type_match.group(1).strip() != "craft":
            continue  # not a craft — exempt
        # This IS a craft; authored_by: is required.
        if not re.search(r"^\s*authored_by\s*:", fm_text, re.MULTILINE):
            crafts_missing.append((rel, "missing authored_by:"))
    assert crafts_missing == [], (
        "v0.6.14 MP1 extension requires every craft (type: craft) under "
        "docs/primordia/ to declare `authored_by: <recognized-host>` in "
        "frontmatter. Crafts missing the field:\n"
        + "\n".join(f"  - {p}: {reason}" for p, reason in crafts_missing)
    )


# ===== D. providers/ excreted =====


def test_providers_directory_excreted() -> None:
    """src/myco/providers/ must NOT exist (v0.6.14 excretion).

    Per craft Round 2 R-T17: directory was reserved at v0.5.6 as escape
    hatch, never populated through 7 minor releases (v0.5.6 → v0.6.13).
    v0.6.14 excretes; future provider coupling requires its own L0 P1
    amendment craft, not a pre-baked sitting-empty escape hatch.
    """
    providers_dir = _REPO_ROOT / "src" / "myco" / "providers"
    assert not providers_dir.exists(), (
        f"src/myco/providers/ exists at {providers_dir}. v0.6.14 excretes "
        f"this directory. If a downstream substrate needs provider coupling, "
        f"file an L0 P1 amendment craft per the new boundary.md 'Future axis' "
        f"historical note."
    )


# ===== E. llm_policy enum reduced to 2 values =====


def test_llm_policy_value_in_v0_6_14_enum() -> None:
    """canon.system.llm_policy must be 'forbidden' or 'opt-in' (NOT 'providers-declared').

    The 'providers-declared' enum value was dropped at v0.6.14 alongside
    the providers/ excretion (craft Round 2 R-T17).
    """
    canon_text = (_REPO_ROOT / ".myco" / "canon.yaml").read_text(encoding="utf-8")
    canon_data = yaml.safe_load(canon_text)
    policy = canon_data["system"]["llm_policy"]
    assert policy in ("forbidden", "opt-in"), (
        f"llm_policy must be 'forbidden' (default) or 'opt-in'. Got {policy!r}. "
        f"'providers-declared' was dropped at v0.6.14 — use 'opt-in' for "
        f"per-call MCP sampling per CL3."
    )


# ===== F. Sixth seam doctrine =====


def test_cycle_md_has_autostart_section() -> None:
    """L2_DOCTRINE/cycle.md must declare the v0.6.14 autostart loop section."""
    text = (
        _REPO_ROOT / ".docs" / "architecture" / "L2_DOCTRINE" / "cycle.md"
    ).read_text(encoding="utf-8")
    assert "Cycle 自起 fruit—winnow—molt 闭环" in text, (
        "cycle.md must declare the v0.6.14 autostart-loop section per craft "
        "scope item 1."
    )
    assert "fruiting/" in text, (
        "cycle.md autostart section must mention the 'fruiting/' branch "
        "prefix (fungal taxonomy)."
    )


def test_boundary_md_has_sixth_seam_section() -> None:
    """L2_DOCTRINE/boundary.md must declare the v0.6.14 sixth seam."""
    text = (
        _REPO_ROOT / ".docs" / "architecture" / "L2_DOCTRINE" / "boundary.md"
    ).read_text(encoding="utf-8")
    assert "Sixth seam" in text or "sixth seam" in text, (
        "boundary.md must declare the v0.6.14 sixth seam section."
    )
    assert "/myco-evolve" in text, (
        "boundary.md sixth-seam section must mention the /myco-evolve slash."
    )
    assert all(
        name in text
        for name in (
            "chytrid",
            "rhizomorph",
            "mycoparasite",
            "saprotroph",
            "mycorrhiza",
        )
    ), (
        "boundary.md sixth-seam section must name all 5 fungal critic roles "
        "(v0.6.15+: chytrid / rhizomorph / mycoparasite / saprotroph / mycorrhiza, "
        "one per L0 P1-P5)."
    )


# ===== G. myco-evolve mirror byte-identical =====


def test_myco_evolve_lives_at_claude_single_source() -> None:
    """`.claude/commands/myco-evolve.md` is the single source of truth.

    v0.8.8 simplification: the pre-v0.8.8 design carried a byte-
    identical mirror at `.plugin/commands/myco-evolve.md`; the
    mirror was retired (plugin.json now references `.claude/commands/`
    directly per the Claude Code docs Quickstart guidance). This
    test verifies the single source of truth file is present + non-
    trivial, and the retired mirror path is absent.
    """
    src = _REPO_ROOT / ".claude" / "commands" / "myco-evolve.md"
    assert src.is_file(), (
        f"v0.6.14 sixth-seam command file missing: {src} "
        f"(single source of truth at v0.8.8+)."
    )
    assert len(src.read_bytes()) >= 200, f"{src} must be non-trivial (≥ 200 bytes)."
    forbidden = _REPO_ROOT / ".plugin" / "commands" / "myco-evolve.md"
    assert not forbidden.exists(), (
        f"Retired mirror path resurrected: {forbidden}. "
        f"v0.8.8 retired `.plugin/commands/`; plugin.json references "
        f"`.claude/commands/` directly."
    )


# ===== H. stipe --branch-only mode =====


def test_stipe_md_declares_branch_only_mode() -> None:
    """stipe.md body must include the v0.6.14 --branch-only mode section."""
    text = (_REPO_ROOT / ".claude" / "agents" / "stipe.md").read_text(encoding="utf-8")
    assert "--branch-only" in text, (
        "stipe.md must declare the v0.6.14 --branch-only mode (used by "
        "/myco-evolve for auto-craft PRs)."
    )
    assert "fruiting/" in text, (
        "stipe.md branch-only section must reference the 'fruiting/' branch prefix."
    )
    assert "gh pr create" in text, (
        "stipe.md branch-only section must describe PR creation via gh CLI."
    )


# ===== I. auto_revert.yml shape =====


def test_auto_revert_workflow_exists_and_triggers_correctly() -> None:
    """`.github/workflows/auto_revert.yml` must trigger on PR closed-without-merge."""
    path = _REPO_ROOT / ".github" / "workflows" / "auto_revert.yml"
    assert path.is_file(), "auto_revert.yml workflow must exist"
    text = path.read_text(encoding="utf-8")
    # Must trigger on pull_request closed.
    assert "pull_request" in text, "auto_revert.yml must listen on pull_request"
    assert "closed" in text, "auto_revert.yml must filter on PR closed"
    # Must check head_ref starts-with fruiting/.
    assert "fruiting/" in text, (
        "auto_revert.yml must filter on head_ref prefix 'fruiting/' (auto-craft branches)"
    )
    # Must check merged == false.
    assert "merged" in text, (
        "auto_revert.yml must check that PR was NOT merged (vetoed only)"
    )
    # Must post issue comment.
    assert "gh issue comment" in text, (
        "auto_revert.yml must post a vetoed_intent comment via gh issue comment"
    )
    # Must delete branch.
    assert "DELETE" in text or "--delete" in text or "git push --delete" in text, (
        "auto_revert.yml must delete the auto-craft branch"
    )


# ===== J. seed script exists + valid python =====


def test_seed_script_exists_and_imports() -> None:
    """`scripts/seed_auto_evolve_tracking_issue.py` must exist and be valid Python."""
    path = _REPO_ROOT / ".scripts" / "seed_auto_evolve_tracking_issue.py"
    assert path.is_file(), "seed_auto_evolve_tracking_issue.py must exist"
    # AST-parse to confirm syntactic validity (don't run it; it would
    # try to call gh CLI and write canon).
    import ast

    text = path.read_text(encoding="utf-8")
    try:
        ast.parse(text)
    except SyntaxError as exc:
        pytest.fail(f"seed_auto_evolve_tracking_issue.py syntax error: {exc}")
    # Must reference auto_evolve_tracking_issue_id.
    assert "auto_evolve_tracking_issue_id" in text, (
        "seed script must reference the canon field it writes to"
    )
    # Must use gh CLI.
    assert "gh" in text and "issue" in text and "create" in text, (
        "seed script must create the issue via gh CLI"
    )
