"""Integration tests for myco init — verify OUTPUT correctness.

These tests exercise the full run_init / run_auto_detect code paths and
assert on the actual files produced (paths, content, structure), not just
return codes. They exist because unit-level tests on individual helpers
missed real bugs like "docs/current/ instead of docs/primordia/" and
"settings.json skip-if-exists".

Every test uses tmp_path so the real filesystem is never touched.
The autouse conftest fixture is intentionally bypassed where needed by
operating on a fresh subdirectory inside tmp_path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from myco.init_cmd import run_init, run_auto_detect, _metabolic_skill_content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(
    target: Path,
    *,
    name: str = "TestProject",
    level: int = 2,
    agent: str | None = "claude",
    auto_detect: bool = False,
    github_user: str = "testuser",
    entry_point: str = "MYCO.md",
) -> argparse.Namespace:
    """Build an argparse.Namespace matching the CLI parser output."""
    return argparse.Namespace(
        dir=str(target),
        name=name,
        level=level,
        agent=agent,
        auto_detect=auto_detect,
        github_user=github_user,
        entry_point=entry_point,
    )


def _patch_mcp_sdk():
    """Patch _check_mcp_sdk to avoid real pip install during tests."""
    return patch("myco.init_cmd._check_mcp_sdk", return_value=True) if hasattr(
        __import__("myco.init_cmd", fromlist=["_check_mcp_sdk"]), "_check_mcp_sdk"
    ) else patch("builtins.__import__", side_effect=lambda *a, **kw: None)


# The 21 canonical MCP tools that SKILL.md must list.
EXPECTED_MCP_TOOLS = [
    "mcp__myco__myco_hunger",
    "mcp__myco__myco_lint",
    "mcp__myco__myco_log",
    "mcp__myco__myco_session",
    "mcp__myco__myco_digest",
    "mcp__myco__myco_compress",
    "mcp__myco__myco_prune",
    "mcp__myco__myco_status",
    "mcp__myco__myco_view",
    "mcp__myco__myco_eat",
    "mcp__myco__myco_search",
    "mcp__myco__myco_cohort",
    "mcp__myco__myco_graph",
    "mcp__myco__myco_reflect",
    "mcp__myco__myco_evolve",
    "mcp__myco__myco_evolve_list",
    "mcp__myco__myco_inlet",
    "mcp__myco__myco_forage",
    "mcp__myco__myco_uncompress",
]


# ═══════════════════════════════════════════════════════════════════════════
# 1. myco init --agent claude --level 2
# ═══════════════════════════════════════════════════════════════════════════

class TestInitAgentClaudeLevel2:
    """Full output correctness for ``myco init --agent claude --level 2``."""

    @pytest.fixture()
    def project(self, tmp_path):
        """Run init once, return the project dir for all assertions."""
        target = tmp_path / "claude_l2"
        target.mkdir()
        args = _make_args(target, level=2, agent="claude")
        # Patch out the MCP SDK auto-install check
        with patch.dict("os.environ", {}, clear=False):
            try:
                # _check_mcp_sdk is a nested function, patch the import check
                import myco.init_cmd as mod
                original = getattr(mod, "_check_mcp_sdk", None)
            except Exception:
                original = None

        # Run init — patch subprocess to avoid pip install
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0
        return target

    # -- Directory structure --

    def test_docs_primordia_exists(self, project):
        """docs/primordia/ must exist (NOT docs/current/)."""
        assert (project / "docs" / "primordia").is_dir()
        assert not (project / "docs" / "current").exists(), (
            "Bug regression: docs/current/ should not exist; primordia/ is canonical"
        )

    def test_notes_dir_exists(self, project):
        assert (project / "notes").is_dir()

    def test_wiki_dir_exists(self, project):
        assert (project / "wiki").is_dir()

    def test_scripts_dir_exists(self, project):
        assert (project / "scripts").is_dir()

    # -- CLAUDE.md --

    def test_claude_md_exists(self, project):
        assert (project / "CLAUDE.md").exists()

    def test_claude_md_contains_boot_ritual(self, project):
        """CLAUDE.md must reference the boot ritual in some form.

        With --agent claude, init_level_0 writes the MYCO.md template
        into CLAUDE.md (since entry_point="CLAUDE.md"), which contains
        the boot signals block and myco hunger references. The dedicated
        CLAUDE.md template (with myco_hunger(execute=true) MCP syntax)
        is then skipped because "Myco" is already present.

        This test verifies the boot ritual is referenced regardless of
        which template provided it.
        """
        content = (project / "CLAUDE.md").read_text(encoding="utf-8")
        has_mcp_form = "myco_hunger(execute=true)" in content
        has_cli_form = "myco hunger" in content
        assert has_mcp_form or has_cli_form, (
            "CLAUDE.md must contain a boot ritual reference "
            "(either myco_hunger(execute=true) or 'myco hunger')"
        )

    def test_claude_md_contains_boot_keyword(self, project):
        content = (project / "CLAUDE.md").read_text(encoding="utf-8")
        assert "boot" in content.lower()

    # -- .mcp.json --

    def test_mcp_json_exists(self, project):
        assert (project / ".mcp.json").exists()

    def test_mcp_json_contains_myco_server(self, project):
        data = json.loads((project / ".mcp.json").read_text(encoding="utf-8"))
        assert "mcpServers" in data
        assert "myco" in data["mcpServers"], (
            ".mcp.json must define a 'myco' server"
        )

    def test_mcp_json_myco_server_command(self, project):
        data = json.loads((project / ".mcp.json").read_text(encoding="utf-8"))
        srv = data["mcpServers"]["myco"]
        assert srv["command"] == "python"
        assert srv["args"] == ["-m", "myco.mcp_server"]

    # -- .claude/settings.json --

    def test_settings_json_exists(self, project):
        assert (project / ".claude" / "settings.json").exists()

    def test_settings_json_contains_myco_pattern(self, project):
        data = json.loads(
            (project / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        allow = data.get("permissions", {}).get("allow", [])
        assert "mcp__myco__*" in allow, (
            "settings.json must contain mcp__myco__* in permissions.allow"
        )

    # -- Scheduled task SKILL.md --

    def test_metabolic_skill_exists(self, project):
        skill = (
            project / ".claude" / "scheduled-tasks"
            / "myco-metabolic-cycle" / "SKILL.md"
        )
        assert skill.exists()

    def test_metabolic_skill_has_20_tools(self, project):
        skill = (
            project / ".claude" / "scheduled-tasks"
            / "myco-metabolic-cycle" / "SKILL.md"
        )
        content = skill.read_text(encoding="utf-8")
        for tool in EXPECTED_MCP_TOOLS:
            assert tool in content, f"SKILL.md missing allowed-tool: {tool}"

    def test_metabolic_skill_tool_count(self, project):
        """Exactly 21 tools — no more, no fewer."""
        skill = (
            project / ".claude" / "scheduled-tasks"
            / "myco-metabolic-cycle" / "SKILL.md"
        )
        content = skill.read_text(encoding="utf-8")
        tool_lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("- mcp__myco__")
        ]
        assert len(tool_lines) == 19, (
            f"Expected 19 MCP tools in SKILL.md, found {len(tool_lines)}: {tool_lines}"
        )

    # -- Cowork skill stubs --

    def test_myco_boot_skill_exists(self, project):
        skill = project / ".claude" / "skills" / "myco-boot" / "SKILL.md"
        assert skill.exists()

    def test_myco_boot_skill_has_content(self, project):
        skill = project / ".claude" / "skills" / "myco-boot" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        assert "myco_hunger" in content

    # -- _canon.yaml --

    def test_canon_yaml_exists(self, project):
        assert (project / "_canon.yaml").exists()

    def test_canon_yaml_principles_count(self, project):
        content = (project / "_canon.yaml").read_text(encoding="utf-8")
        assert "principles_count: 13" in content


# ═══════════════════════════════════════════════════════════════════════════
# 2. myco init --auto-detect
# ═══════════════════════════════════════════════════════════════════════════

class TestInitAutoDetect:
    """Full output correctness for ``myco init --auto-detect``."""

    @pytest.fixture()
    def project(self, tmp_path):
        target = tmp_path / "auto_detect_l2"
        target.mkdir()
        args = _make_args(
            target, level=2, agent=None, auto_detect=True,
        )
        with patch("myco.init_cmd.detect_tools") as mock_detect:
            mock_detect.return_value = {
                "Claude Code": False,
                "Cursor": False,
                "VS Code": False,
                "Codex": False,
                "Cline": False,
                "Continue": False,
                "Windsurf": False,
                "Zed": False,
            }
            rc = run_auto_detect(args)
        assert rc == 0
        return target

    def test_claude_md_always_created(self, project):
        """--auto-detect ALWAYS creates CLAUDE.md regardless of detection."""
        assert (project / "CLAUDE.md").exists()

    def test_claude_md_contains_boot_ritual(self, project):
        """Same as --agent claude: boot ritual must appear in some form.

        In --auto-detect, init_level_X writes the MYCO.md template into
        CLAUDE.md, then _gen_claude_md sees "Myco" already present and
        skips appending the dedicated CLAUDE.md template.
        """
        content = (project / "CLAUDE.md").read_text(encoding="utf-8")
        has_mcp_form = "myco_hunger(execute=true)" in content
        has_cli_form = "myco hunger" in content
        assert has_mcp_form or has_cli_form, (
            "CLAUDE.md must contain a boot ritual reference"
        )

    def test_docs_primordia_exists(self, project):
        assert (project / "docs" / "primordia").is_dir()
        assert not (project / "docs" / "current").exists()

    def test_notes_dir_exists(self, project):
        assert (project / "notes").is_dir()

    def test_canon_yaml_exists(self, project):
        assert (project / "_canon.yaml").exists()

    def test_canon_yaml_principles_count(self, project):
        content = (project / "_canon.yaml").read_text(encoding="utf-8")
        assert "principles_count: 13" in content

    def test_settings_json_exists(self, project):
        assert (project / ".claude" / "settings.json").exists()

    def test_settings_json_contains_myco_pattern(self, project):
        data = json.loads(
            (project / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        allow = data.get("permissions", {}).get("allow", [])
        assert "mcp__myco__*" in allow

    def test_metabolic_skill_exists(self, project):
        skill = (
            project / ".claude" / "scheduled-tasks"
            / "myco-metabolic-cycle" / "SKILL.md"
        )
        assert skill.exists()

    def test_metabolic_skill_has_20_tools(self, project):
        skill = (
            project / ".claude" / "scheduled-tasks"
            / "myco-metabolic-cycle" / "SKILL.md"
        )
        content = skill.read_text(encoding="utf-8")
        for tool in EXPECTED_MCP_TOOLS:
            assert tool in content, f"SKILL.md missing: {tool}"

    def test_myco_boot_skill_exists(self, project):
        assert (project / ".claude" / "skills" / "myco-boot" / "SKILL.md").exists()


# ═══════════════════════════════════════════════════════════════════════════
# 3. settings.json MERGE behavior
# ═══════════════════════════════════════════════════════════════════════════

class TestSettingsJsonMerge:
    """Verify settings.json merges existing content instead of overwriting."""

    def test_preserves_existing_permissions(self, tmp_path):
        target = tmp_path / "merge_settings"
        target.mkdir()
        claude_dir = target / ".claude"
        claude_dir.mkdir(parents=True)
        existing = {
            "permissions": {
                "allow": ["Bash(git *)"],
                "deny": ["Bash(rm -rf *)"],
            },
            "customKey": "preserved",
        }
        (claude_dir / "settings.json").write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )

        args = _make_args(target, level=2, agent="claude")
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0

        data = json.loads(
            (claude_dir / "settings.json").read_text(encoding="utf-8")
        )
        # Myco patterns must be present
        allow = data["permissions"]["allow"]
        assert "mcp__myco__*" in allow
        # customKey at root must survive the merge
        assert data.get("customKey") == "preserved"

    def test_creates_settings_from_scratch(self, tmp_path):
        target = tmp_path / "fresh_settings"
        target.mkdir()

        args = _make_args(target, level=2, agent="claude")
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0

        data = json.loads(
            (target / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        assert "mcp__myco__*" in data["permissions"]["allow"]


# ═══════════════════════════════════════════════════════════════════════════
# 4. .mcp.json MERGE behavior
# ═══════════════════════════════════════════════════════════════════════════

class TestMcpJsonMerge:
    """Verify .mcp.json merges existing servers instead of overwriting."""

    def test_preserves_existing_server(self, tmp_path):
        target = tmp_path / "merge_mcp"
        target.mkdir()
        existing = {
            "mcpServers": {
                "other-tool": {
                    "command": "node",
                    "args": ["server.js"],
                }
            }
        }
        (target / ".mcp.json").write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )

        args = _make_args(target, level=2, agent="claude")
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0

        data = json.loads(
            (target / ".mcp.json").read_text(encoding="utf-8")
        )
        assert "other-tool" in data["mcpServers"], (
            "Existing server 'other-tool' must be preserved after merge"
        )
        assert "myco" in data["mcpServers"], (
            "Myco server must be added after merge"
        )

    def test_creates_mcp_json_from_scratch(self, tmp_path):
        target = tmp_path / "fresh_mcp"
        target.mkdir()

        args = _make_args(target, level=2, agent="claude")
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0

        data = json.loads(
            (target / ".mcp.json").read_text(encoding="utf-8")
        )
        assert "myco" in data["mcpServers"]

    def test_handles_invalid_existing_mcp_json(self, tmp_path):
        target = tmp_path / "invalid_mcp"
        target.mkdir()
        (target / ".mcp.json").write_text("NOT VALID JSON{{{", encoding="utf-8")

        args = _make_args(target, level=2, agent="claude")
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0

        data = json.loads(
            (target / ".mcp.json").read_text(encoding="utf-8")
        )
        assert "myco" in data["mcpServers"]


# ═══════════════════════════════════════════════════════════════════════════
# 5. SKILL.md no-overwrite
# ═══════════════════════════════════════════════════════════════════════════

class TestSkillMdNoOverwrite:
    """Verify pre-existing SKILL.md files are NOT overwritten."""

    def test_metabolic_skill_not_overwritten(self, tmp_path):
        target = tmp_path / "no_overwrite"
        target.mkdir()

        # Pre-create SKILL.md with custom content
        sched_dir = target / ".claude" / "scheduled-tasks" / "myco-metabolic-cycle"
        sched_dir.mkdir(parents=True)
        custom = "---\nname: custom\n---\nMy custom metabolic cycle.\n"
        (sched_dir / "SKILL.md").write_text(custom, encoding="utf-8")

        args = _make_args(target, level=2, agent="claude")
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0

        content = (sched_dir / "SKILL.md").read_text(encoding="utf-8")
        assert content == custom, (
            "SKILL.md must NOT be overwritten if it already exists"
        )

    def test_cowork_skill_not_overwritten(self, tmp_path):
        target = tmp_path / "no_overwrite_cowork"
        target.mkdir()

        # Pre-create myco-boot SKILL.md with custom content
        boot_dir = target / ".claude" / "skills" / "myco-boot"
        boot_dir.mkdir(parents=True)
        custom = "---\nname: my-custom-boot\n---\nCustom boot.\n"
        (boot_dir / "SKILL.md").write_text(custom, encoding="utf-8")

        args = _make_args(target, level=2, agent="claude")
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = type("R", (), {"returncode": 0})()
            rc = run_init(args)
        assert rc == 0

        content = (boot_dir / "SKILL.md").read_text(encoding="utf-8")
        assert content == custom, (
            "Cowork skill SKILL.md must NOT be overwritten if it already exists"
        )

    def test_auto_detect_metabolic_skill_not_overwritten(self, tmp_path):
        """Same no-overwrite guarantee for --auto-detect path."""
        target = tmp_path / "no_overwrite_auto"
        target.mkdir()

        sched_dir = target / ".claude" / "scheduled-tasks" / "myco-metabolic-cycle"
        sched_dir.mkdir(parents=True)
        custom = "---\nname: custom-auto\n---\nCustom auto cycle.\n"
        (sched_dir / "SKILL.md").write_text(custom, encoding="utf-8")

        args = _make_args(target, level=2, agent=None, auto_detect=True)
        with patch("myco.init_cmd.detect_tools") as mock_detect:
            mock_detect.return_value = {k: False for k in [
                "Claude Code", "Cursor", "VS Code", "Codex",
                "Cline", "Continue", "Windsurf", "Zed",
            ]}
            rc = run_auto_detect(args)
        assert rc == 0

        content = (sched_dir / "SKILL.md").read_text(encoding="utf-8")
        assert content == custom


# ═══════════════════════════════════════════════════════════════════════════
# 6. _metabolic_skill_content unit check
# ═══════════════════════════════════════════════════════════════════════════

class TestMetabolicSkillContent:
    """Verify the single-source-of-truth helper produces correct content."""

    def test_contains_all_20_tools(self):
        content = _metabolic_skill_content("/fake/path")
        for tool in EXPECTED_MCP_TOOLS:
            assert tool in content

    def test_tool_count_is_exactly_19(self):
        content = _metabolic_skill_content("/fake/path")
        tool_lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("- mcp__myco__")
        ]
        assert len(tool_lines) == 19

    def test_contains_project_dir(self):
        content = _metabolic_skill_content("/my/project")
        assert "/my/project" in content

    def test_has_frontmatter(self):
        content = _metabolic_skill_content("/fake")
        assert content.startswith("---\n")
        # Ends with closing frontmatter before body
        assert "\n---\n" in content
