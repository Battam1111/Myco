"""Regression tests for the v0.6.11+ subagents + slash commands surface.

These tests guard the structural integrity of the markdown files (5
agents + 6 commands at v0.6.14+) on the boundary subsystem's 5th + 6th seams.
They do NOT test subagent behavior — behavioral validation is human
integration testing in subsequent agent sessions.

v0.6.11 baseline (5 + 5) → v0.6.14 extension (sixth-seam command: 5 + 6).

v0.8.8 simplification — `.claude/{agents,commands}/` is now the **single
source of truth**. The pre-v0.8.8 design carried byte-identical mirror
copies at `.plugin/{agents,commands}/` to satisfy what the v0.7.3 craft
believed was a Claude Code spec requirement; re-reading the official
docs (https://code.claude.com/docs/en/plugins § "Convert existing
configurations to plugins") showed the docs explicitly recommend
single-source-of-truth: "After migrating, you can remove the original
files from `.claude/` to avoid duplicates. The plugin version will
take precedence when loaded." v0.8.8 inverted that recommendation —
keep `.claude/`, drop the mirror — and redirected
`plugin.json::"agents"|"commands"` straight at `./.claude/<dir>/`.

Tests now check:

1. All 5 subagents exist at `.claude/agents/<name>.md`.
2. All 6 slash commands exist at `.claude/commands/<name>.md`.
3. Each subagent's frontmatter parses as YAML and has required keys.
4. Each subagent's `name` frontmatter value matches its filename stem.
5. Each body is ≥ 200 chars (the "real content vs stub" floor).
6. Each slash command's frontmatter parses with `description`.
7. `plugin.json::"agents"|"commands"` references the `.claude/`
   single source of truth (no `.plugin/` mirror is permitted).

v0.6.14 invariants preserved:

8. **Only** primordium has `Task` in its tools allowlist.
9. **Only** primordium body mentions "Autonomous mode".

Doctrine: docs/architecture/L2_DOCTRINE/boundary.md
   § "Subagents and slash commands (v0.6.11+)" (5th seam)
   + § "Sixth seam: GitHub-side critic-fanout + auto-revert (v0.6.14+)"
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Repo root resolved via __file__ since tests run from various cwds.
_REPO_ROOT = Path(__file__).resolve().parents[3]

_EXPECTED_SUBAGENTS = (
    "primordium",
    "hypha",
    "autolysis",
    "stipe",
    "anamorph",
)

_EXPECTED_COMMANDS = (
    "myco-primordium",
    "myco-hypha",
    "myco-autolyze",
    "myco-disperse",
    "myco-anamorph",
    # v0.6.14 — sixth seam: orchestrates Cycle 自起 fruit—winnow—molt 闭环.
    "myco-evolve",
)

# v0.8.8 — single source of truth at .claude/. The .plugin/{agents,
# commands}/ mirror directories were retired; plugin.json references
# .claude/ directly.
_AGENT_DIR = _REPO_ROOT / ".claude" / "agents"
_COMMAND_DIR = _REPO_ROOT / ".claude" / "commands"


def _split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Parse a markdown file's YAML frontmatter + return (meta, body).

    Frontmatter is a `---`-delimited YAML block at the top of the file.
    Returns (empty-dict, full-text) if no frontmatter present.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_text = text[4:end]
    body = text[end + 5 :]
    meta = yaml.safe_load(fm_text) or {}
    return meta, body


@pytest.mark.parametrize("name", _EXPECTED_SUBAGENTS)
def test_subagent_file_exists(name: str) -> None:
    """Each of the 5 subagents must exist at .claude/agents/."""
    path = _AGENT_DIR / f"{name}.md"
    assert path.is_file(), (
        f"v0.6.11 subagent file missing: {path}. The 5 fungal-named "
        f"subagents live at .claude/agents/ (single source of truth at "
        f"v0.8.8+; plugin.json references this path directly)."
    )


@pytest.mark.parametrize("cmd", _EXPECTED_COMMANDS)
def test_command_file_exists(cmd: str) -> None:
    """Each of the 6 slash commands must exist at .claude/commands/."""
    path = _COMMAND_DIR / f"{cmd}.md"
    assert path.is_file(), (
        f"v0.6.11+ slash command file missing: {path}. The 6 myco-* "
        f"slash commands live at .claude/commands/ (single source of "
        f"truth at v0.8.8+)."
    )


@pytest.mark.parametrize("name", _EXPECTED_SUBAGENTS)
def test_subagent_frontmatter_valid(name: str) -> None:
    """Each subagent's frontmatter parses as YAML with required keys."""
    path = _AGENT_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(text)
    assert isinstance(meta, dict) and meta, (
        f"Subagent {name}: frontmatter missing or unparseable."
    )
    # Required per Claude Code spec: name + description.
    assert "name" in meta, f"Subagent {name}: frontmatter missing `name` key."
    assert "description" in meta, (
        f"Subagent {name}: frontmatter missing `description` key."
    )
    # Name field must match filename stem (Claude Code spec).
    assert meta["name"] == name, (
        f"Subagent {name}: frontmatter `name: {meta['name']!r}` "
        f"does not match filename stem {name!r}."
    )
    # Body floor: 200 chars rules out stub files.
    assert len(body.strip()) >= 200, (
        f"Subagent {name}: body is too short ({len(body.strip())} chars). "
        f"Per craft Round 2 §T7, the 200-char floor signals real content."
    )


@pytest.mark.parametrize("cmd", _EXPECTED_COMMANDS)
def test_command_frontmatter_valid(cmd: str) -> None:
    """Each slash command's frontmatter parses with `description` key."""
    path = _COMMAND_DIR / f"{cmd}.md"
    text = path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(text)
    assert isinstance(meta, dict) and meta, (
        f"Slash command {cmd}: frontmatter missing or unparseable."
    )
    # Recommended per Claude Code spec: description.
    assert "description" in meta, (
        f"Slash command {cmd}: frontmatter missing `description` key."
    )
    # Body floor.
    assert len(body.strip()) >= 200, (
        f"Slash command {cmd}: body is too short ({len(body.strip())} chars). "
        f"Per craft Round 2 §T7, the 200-char floor signals real content."
    )


def test_subagent_count_matches_craft() -> None:
    """The shipped subagent count matches the craft doc's claim of 5."""
    files = list(_AGENT_DIR.glob("*.md"))
    assert len(files) == len(_EXPECTED_SUBAGENTS), (
        f"Expected {len(_EXPECTED_SUBAGENTS)} subagent files in .claude/agents/, "
        f"found {len(files)}: {sorted(f.name for f in files)}. "
        f"If a subagent is added or removed, update _EXPECTED_SUBAGENTS in "
        f"this test and the v0.6.11 craft + boundary doctrine accordingly."
    )


def test_command_count_matches_craft() -> None:
    """The shipped slash command count matches the craft doc's claim of 6."""
    files = list(_COMMAND_DIR.glob("*.md"))
    assert len(files) == len(_EXPECTED_COMMANDS), (
        f"Expected {len(_EXPECTED_COMMANDS)} command files in .claude/commands/, "
        f"found {len(files)}: {sorted(f.name for f in files)}. "
        f"If a command is added or removed, update _EXPECTED_COMMANDS in "
        f"this test and the v0.6.11 craft + boundary doctrine accordingly."
    )


def test_plugin_manifest_points_at_claude_single_source() -> None:
    """v0.8.8 — `plugin.json::"agents"|"commands"` MUST point at `.claude/`.

    The pre-v0.8.8 design referenced `./.plugin/agents/` etc., a
    byte-identical mirror of `.claude/`. v0.8.8 retired that mirror
    after the Claude Code docs Quickstart guidance ("remove the
    original files from `.claude/` to avoid duplicates") refuted the
    v0.7.3 craft's "dual sources required" inference. This test pins
    the new single-source-of-truth shape so a future regression
    cannot silently reintroduce the mirror.
    """
    import json

    manifest = json.loads(
        (_REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    assert manifest.get("agents") == "./.claude/agents/", (
        'plugin.json::"agents" MUST point at `./.claude/agents/` '
        "(v0.8.8 single source of truth, replacing the retired "
        "`./.plugin/agents/` mirror)."
    )
    assert manifest.get("commands") == "./.claude/commands/", (
        'plugin.json::"commands" MUST point at `./.claude/commands/` '
        "(v0.8.8 single source of truth, replacing the retired "
        "`./.plugin/commands/` mirror)."
    )


def test_no_plugin_mirror_directories() -> None:
    """v0.8.8 — `.plugin/{agents,commands}/` MUST NOT exist.

    These were byte-identical mirrors of `.claude/{agents,commands}/`
    in the pre-v0.8.8 design. MF5 dim catches accidental
    resurrection (single file under the retired path), but this
    test catches the directory-level resurrection up front.
    """
    forbidden = (
        _REPO_ROOT / ".plugin" / "agents",
        _REPO_ROOT / ".plugin" / "commands",
    )
    for d in forbidden:
        assert not d.exists(), (
            f"Retired mirror path resurrected: {d}. The v0.8.8 single-"
            f"source-of-truth doctrine forbids `.plugin/{{agents,commands}}/`. "
            f"Move content to `.claude/{{agents,commands}}/` and remove."
        )


# ----- v0.6.14 sixth-seam invariants -----


def test_only_primordium_has_task_in_tools() -> None:
    """v0.6.14 invariant: ONLY primordium has `Task` in its tools allowlist.

    The other 4 subagents (hypha / autolysis / stipe / anamorph) continue
    to forbid sub-agent recursion. primordium's autonomous-mode exception
    is single-purpose and must not proliferate. Per cycle.md § "Cycle 自起
    闭环 (v0.6.14+)" + craft v0_6_14_*.

    If a subagent legitimately needs Task (extremely unlikely), update the
    craft + this test together — but think hard first about whether you're
    re-creating the recursion explosion the v0.6.11 craft Round 2 §T1 closed.
    """
    for name in _EXPECTED_SUBAGENTS:
        path = _AGENT_DIR / f"{name}.md"
        text = path.read_text(encoding="utf-8")
        meta, _body = _split_frontmatter(text)
        tools_field = meta.get("tools", "")
        # tools is a comma-separated string in the existing format.
        tool_list = (
            [t.strip() for t in tools_field.split(",")]
            if isinstance(tools_field, str)
            else list(tools_field)
        )
        if name == "primordium":
            assert "Task" in tool_list, (
                f"primordium MUST have `Task` in tools (autonomous mode "
                f"requires it for Round 1.5 critic fanout). Found: {tool_list}"
            )
        else:
            assert "Task" not in tool_list, (
                f"Subagent {name} has `Task` in tools — but only primordium "
                f"is permitted Task per v0.6.14 boundary doctrine "
                f"(autonomous-mode exception is single-purpose). Found: {tool_list}"
            )


def test_only_primordium_mentions_autonomous_mode() -> None:
    """v0.6.14 invariant: ONLY primordium body mentions 'Autonomous mode'.

    Prevents the autonomous-mode exception from accidentally proliferating
    via copy-paste. If a future subagent gains an analogous mode, it should
    pick a different name (and a different craft) so the surface remains
    clearly bounded.
    """
    for name in _EXPECTED_SUBAGENTS:
        path = _AGENT_DIR / f"{name}.md"
        text = path.read_text(encoding="utf-8")
        _meta, body = _split_frontmatter(text)
        has_autonomous = "Autonomous mode" in body or "autonomous mode" in body
        if name == "primordium":
            assert has_autonomous, (
                "primordium body MUST contain 'Autonomous mode' section "
                "(v0.6.14 critic-fanout protocol)."
            )
        else:
            assert not has_autonomous, (
                f"Subagent {name} body mentions 'Autonomous mode' — but only "
                f"primordium is permitted that mode per v0.6.14 boundary "
                f"doctrine. Did you copy-paste from primordium?"
            )
