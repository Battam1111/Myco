"""Regression tests for the v0.6.11+ subagents + slash commands surface.

These tests guard the structural integrity of the markdown files (5
agents + 6 commands at v0.6.14) on the boundary subsystem's 5th + 6th seams.
They do NOT test subagent behavior — behavioral validation is human
integration testing in subsequent agent sessions.

v0.6.11 baseline (5 + 5):
1. All 5 expected subagent files exist at both `.claude/agents/<name>.md`
   (project-level) and `<repo>/agents/<name>.md` (plugin-bundle scope,
   declared in `.claude-plugin/plugin.json::agents`).
2. All 5 expected slash command files exist at both `.claude/commands/`
   and `<repo>/commands/`.
3. Each subagent file's frontmatter parses as valid YAML and has the
   required `name` + `description` keys.
4. Each subagent's `name` frontmatter value matches its filename stem.
5. Each subagent body (after frontmatter) is non-empty and >= 200 chars
   (the "real content vs stub" floor).
6. Each slash command's frontmatter parses with the recommended
   `description` key.
7. The `.claude/<dir>/<name>.md` and `<repo>/<dir>/<name>.md` pairs are
   bytewise identical (the plugin-mirror discipline; see craft Round 2 §T8).

v0.6.14 extension (sixth seam):
8. `myco-evolve` slash command added (commands count: 5 → 6).
9. **Only** primordium has `Task` in its tools allowlist (autonomous mode
   exception; the other 4 subagents continue to forbid sub-agent recursion).
10. **Only** primordium body mentions "Autonomous mode" — prevents the
    autonomous-mode exception from accidentally proliferating.

Doctrine: docs/architecture/L2_DOCTRINE/boundary.md
   § "Subagents and slash commands (v0.6.11+)" (5th seam)
   + § "Sixth seam: GitHub-side critic-fanout + auto-revert (v0.6.14+)"
Crafts: docs/primordia/v0_6_11_subagents_and_commands_craft_2026-04-28.md (5th)
   + docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md (6th)
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

# Both paths must contain identical files.
_AGENT_DIRS = (
    _REPO_ROOT / ".claude" / "agents",
    _REPO_ROOT / "agents",
)
_COMMAND_DIRS = (
    _REPO_ROOT / ".claude" / "commands",
    _REPO_ROOT / "commands",
)


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
@pytest.mark.parametrize("agent_dir", _AGENT_DIRS, ids=["claude", "plugin"])
def test_subagent_file_exists(name: str, agent_dir: Path) -> None:
    """Each of the 5 subagents must exist at both paths."""
    path = agent_dir / f"{name}.md"
    assert path.is_file(), (
        f"v0.6.11 subagent file missing: {path}. "
        f"Per craft v0_6_11_subagents_and_commands_craft, the 5 fungal-named "
        f"subagents must exist at both .claude/agents/ (project-level) and "
        f"<repo>/agents/ (plugin-bundle scope)."
    )


@pytest.mark.parametrize("cmd", _EXPECTED_COMMANDS)
@pytest.mark.parametrize("cmd_dir", _COMMAND_DIRS, ids=["claude", "plugin"])
def test_command_file_exists(cmd: str, cmd_dir: Path) -> None:
    """Each of the 5 slash commands must exist at both paths."""
    path = cmd_dir / f"{cmd}.md"
    assert path.is_file(), (
        f"v0.6.11 slash command file missing: {path}. "
        f"Per craft v0_6_11_subagents_and_commands_craft, the 5 myco-* slash "
        f"commands must exist at both .claude/commands/ (project-level) and "
        f"<repo>/commands/ (plugin-bundle scope)."
    )


@pytest.mark.parametrize("name", _EXPECTED_SUBAGENTS)
def test_subagent_frontmatter_valid(name: str) -> None:
    """Each subagent's frontmatter parses as YAML with required keys."""
    path = _REPO_ROOT / ".claude" / "agents" / f"{name}.md"
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
    path = _REPO_ROOT / ".claude" / "commands" / f"{cmd}.md"
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


@pytest.mark.parametrize("name", _EXPECTED_SUBAGENTS)
def test_subagent_plugin_mirror_byte_identical(name: str) -> None:
    """The .claude/agents/ (project-level) and <repo>/agents/ (plugin-bundle)
    copies must be byte-identical.

    Per craft Round 2 §T8, the duplication is accepted maintenance debt for
    v0.6.11 (build-hook copy deferred to v0.6.12). This test surfaces drift
    immediately when one copy is edited and the other forgotten.
    """
    a = (_REPO_ROOT / ".claude" / "agents" / f"{name}.md").read_bytes()
    b = (_REPO_ROOT / "agents" / f"{name}.md").read_bytes()
    assert a == b, (
        f"Subagent {name}: .claude/agents/ (project-level) and "
        f"<repo>/agents/ (plugin-bundle scope) copies have drifted. "
        f"v0.6.11 requires bytewise-identical mirrors. If you edited one "
        f"path, copy to the other (or wait for v0.6.12's build-hook copy)."
    )


@pytest.mark.parametrize("cmd", _EXPECTED_COMMANDS)
def test_command_plugin_mirror_byte_identical(cmd: str) -> None:
    """The .claude/commands/ (project-level) and <repo>/commands/ (plugin-bundle)
    copies must be byte-identical.
    """
    a = (_REPO_ROOT / ".claude" / "commands" / f"{cmd}.md").read_bytes()
    b = (_REPO_ROOT / "commands" / f"{cmd}.md").read_bytes()
    assert a == b, (
        f"Slash command {cmd}: .claude/commands/ (project-level) and "
        f"<repo>/commands/ (plugin-bundle scope) copies have drifted. "
        f"v0.6.11 requires bytewise-identical mirrors."
    )


def test_subagent_count_matches_craft() -> None:
    """The shipped subagent count matches the craft doc's claim of 5."""
    files = list((_REPO_ROOT / ".claude" / "agents").glob("*.md"))
    assert len(files) == len(_EXPECTED_SUBAGENTS), (
        f"Expected {len(_EXPECTED_SUBAGENTS)} subagent files in .claude/agents/, "
        f"found {len(files)}: {sorted(f.name for f in files)}. "
        f"If a subagent is added or removed, update _EXPECTED_SUBAGENTS in "
        f"this test and the v0.6.11 craft + boundary doctrine accordingly."
    )


def test_command_count_matches_craft() -> None:
    """The shipped slash command count matches the craft doc's claim of 5."""
    files = list((_REPO_ROOT / ".claude" / "commands").glob("*.md"))
    assert len(files) == len(_EXPECTED_COMMANDS), (
        f"Expected {len(_EXPECTED_COMMANDS)} command files in .claude/commands/, "
        f"found {len(files)}: {sorted(f.name for f in files)}. "
        f"If a command is added or removed, update _EXPECTED_COMMANDS in "
        f"this test and the v0.6.11 craft + boundary doctrine accordingly."
    )


def test_plugin_manifest_declares_agents_and_commands() -> None:
    """`.claude-plugin/plugin.json` must declare both surfaces."""
    import json

    manifest = json.loads(
        (_REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    assert "agents" in manifest, (
        ".claude-plugin/plugin.json must declare an `agents` key pointing at "
        "`./agents/` so plugin marketplace installs deliver the subagents."
    )
    assert "commands" in manifest, (
        ".claude-plugin/plugin.json must declare a `commands` key pointing at "
        "`./commands/` so plugin marketplace installs deliver the slash commands."
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
        path = _REPO_ROOT / ".claude" / "agents" / f"{name}.md"
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
        path = _REPO_ROOT / ".claude" / "agents" / f"{name}.md"
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
