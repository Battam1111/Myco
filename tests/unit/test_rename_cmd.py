"""Unit tests for myco.rename_cmd -- syntax-aware module renaming."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from myco.rename_cmd import build_plan, execute_plan, RenamePlan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_CANON = """\
system:
  principles_count: 13
  principles_label: "十三原則"
  entry_point: MYCO.md
  contract_version: "v0.24.0"
  synced_contract_version: "v0.24.0"
architecture:
  layers: 4
  wiki_pages: 0
project:
  name: TestProject
"""


@pytest.fixture
def rename_project(tmp_path):
    """Create a fresh project directory for rename tests.

    Uses a 'rename_ws' subdirectory to avoid colliding with the autouse
    ``_isolate_myco_project`` fixture (which creates ``tmp_path/project``).
    """
    project = tmp_path / "rename_ws"
    project.mkdir()
    (project / "_canon.yaml").write_text(_CANON, encoding="utf-8")
    (project / "notes").mkdir()
    (project / "docs").mkdir()
    (project / "docs" / "primordia").mkdir()
    (project / "log.md").write_text("", encoding="utf-8")
    # Create src/myco/ structure
    src_myco = project / "src" / "myco"
    src_myco.mkdir(parents=True, exist_ok=True)
    (src_myco / "__init__.py").write_text("", encoding="utf-8")
    # Create tests/unit/ structure
    test_dir = project / "tests" / "unit"
    test_dir.mkdir(parents=True, exist_ok=True)
    return project


def _add_files(project: Path, files: dict[str, str]):
    """Write extra files into the project."""
    for relpath, content in files.items():
        p = project / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRenameDryRun:
    """Verify dry-run mode shows planned changes without executing them."""

    def test_dry_run_shows_file_moves(self, rename_project):
        """Dry-run should list file moves for existing module files."""
        _add_files(rename_project, {
            "src/myco/alpha.py": "# alpha module\n",
            "src/myco/alpha_cmd.py": "# alpha command\n",
            "tests/unit/test_alpha.py": "# test alpha\n",
            "tests/unit/test_alpha_integration.py": "# test alpha integration\n",
        })

        plan = build_plan("alpha", "beta", str(rename_project))

        assert not plan.errors
        git_mv_actions = [a for a in plan.actions if a.kind == "git_mv"]

        # Should plan to move the core module, cmd file, and both test files
        sources = {a.source for a in git_mv_actions}
        targets = {a.target for a in git_mv_actions}

        assert "src/myco/alpha.py" in sources
        assert "src/myco/beta.py" in targets
        assert "src/myco/alpha_cmd.py" in sources
        assert "src/myco/beta_cmd.py" in targets
        assert "tests/unit/test_alpha.py" in sources
        assert "tests/unit/test_beta.py" in targets
        assert "tests/unit/test_alpha_integration.py" in sources
        assert "tests/unit/test_beta_integration.py" in targets

    def test_dry_run_no_execution(self, rename_project):
        """Files should remain untouched after building a plan (no execute)."""
        _add_files(rename_project, {
            "src/myco/alpha.py": "# alpha module\n",
        })

        plan = build_plan("alpha", "beta", str(rename_project))

        # Plan exists but file is still at old location
        assert (rename_project / "src" / "myco" / "alpha.py").is_file()
        assert not (rename_project / "src" / "myco" / "beta.py").exists()

    def test_dry_run_detects_import_replacements(self, rename_project):
        """Dry-run should detect Python import patterns to replace."""
        _add_files(rename_project, {
            "src/myco/cli.py": (
                'from myco.alpha import run_alpha\n'
                'from myco.alpha_cmd import something\n'
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))

        replace_actions = [a for a in plan.actions if a.kind == "replace"]
        # Should detect import patterns
        import_actions = [
            a for a in replace_actions
            if "Python import" in a.pattern
        ]
        assert len(import_actions) > 0

    def test_dry_run_detects_mcp_tool_name(self, rename_project):
        """Dry-run should detect MCP tool name patterns."""
        _add_files(rename_project, {
            "src/myco/mcp_server.py": (
                '@mcp.tool()\n'
                'def myco_alpha(project_dir: str = ".") -> str:\n'
                '    """Run alpha check."""\n'
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))

        replace_actions = [a for a in plan.actions if a.kind == "replace"]
        mcp_actions = [
            a for a in replace_actions
            if "MCP tool name" in a.pattern
        ]
        assert len(mcp_actions) > 0

    def test_summary_output(self, rename_project):
        """Summary should be human-readable and include all sections."""
        _add_files(rename_project, {
            "src/myco/alpha.py": "# module\n",
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        summary = plan.summary()

        assert "alpha" in summary
        assert "beta" in summary
        assert "git mv" in summary.lower() or "File moves" in summary


class TestRenameUpdatesImports:
    """Verify that executing a rename correctly updates import statements."""

    def test_renames_module_file(self, rename_project):
        """Execute should physically move the module file."""
        _add_files(rename_project, {
            "src/myco/alpha.py": "# alpha module\ndef run_alpha(): pass\n",
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        messages = execute_plan(plan)

        # File should be moved
        assert not (rename_project / "src" / "myco" / "alpha.py").exists()
        assert (rename_project / "src" / "myco" / "beta.py").is_file()

    def test_updates_python_imports(self, rename_project):
        """Execute should rewrite 'from myco.alpha' to 'from myco.beta'."""
        _add_files(rename_project, {
            "src/myco/alpha.py": "# alpha module\ndef hello(): pass\n",
            "src/myco/other.py": (
                "from myco.alpha import hello\n"
                "import myco.alpha\n"
                "\n"
                "def do_thing():\n"
                "    return myco.alpha.hello()\n"
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        execute_plan(plan)

        # Read the other.py content -- imports should be updated
        other_content = (rename_project / "src" / "myco" / "other.py").read_text(encoding="utf-8")
        assert "from myco.beta import hello" in other_content
        assert "import myco.beta" in other_content
        # Old imports should be gone
        assert "from myco.alpha" not in other_content
        assert "import myco.alpha" not in other_content

    def test_updates_mock_patch_strings(self, rename_project):
        """Execute should rewrite 'myco.alpha' string refs (mock patches)."""
        _add_files(rename_project, {
            "src/myco/alpha.py": "# alpha\n",
            "tests/unit/test_alpha.py": (
                "import pytest\n"
                'from unittest.mock import patch\n'
                '\n'
                'def test_something():\n'
                '    with patch("myco.alpha.run_alpha") as mock:\n'
                '        pass\n'
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        execute_plan(plan)

        # Test file should have been moved AND content updated
        new_test = rename_project / "tests" / "unit" / "test_beta.py"
        assert new_test.is_file()
        content = new_test.read_text(encoding="utf-8")
        assert '"myco.beta.run_beta"' in content
        assert '"myco.alpha' not in content

    def test_updates_mcp_tool_names(self, rename_project):
        """Execute should rewrite myco_alpha -> myco_beta in MCP server."""
        _add_files(rename_project, {
            "src/myco/mcp_server.py": (
                'def myco_alpha(project_dir: str = ".") -> str:\n'
                '    """Run the myco_alpha check."""\n'
                '    pass\n'
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        execute_plan(plan)

        content = (rename_project / "src" / "myco" / "mcp_server.py").read_text(encoding="utf-8")
        assert "myco_beta" in content
        assert "myco_alpha" not in content

    def test_updates_doc_references(self, rename_project):
        """Execute should rewrite 'myco alpha' and 'myco_alpha' in .md files."""
        _add_files(rename_project, {
            "README.md": (
                "# My Project\n"
                "\n"
                "Run `myco alpha --quick` to check health.\n"
                "The myco_alpha tool is also available via MCP.\n"
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        execute_plan(plan)

        content = (rename_project / "README.md").read_text(encoding="utf-8")
        assert "myco beta" in content
        assert "myco_beta" in content
        assert "myco alpha" not in content
        assert "myco_alpha" not in content

    def test_no_false_positives_bare_name(self, rename_project):
        """Bare 'alpha' without myco prefix should NOT be replaced."""
        _add_files(rename_project, {
            "src/myco/unrelated.py": (
                "alpha_value = 42\n"
                "# This alpha is not a myco module\n"
                "def alpha(): pass\n"
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        execute_plan(plan)

        content = (rename_project / "src" / "myco" / "unrelated.py").read_text(encoding="utf-8")
        # Bare 'alpha' references should be untouched
        assert "alpha_value = 42" in content
        assert "def alpha(): pass" in content

    def test_updates_cli_subparser(self, rename_project):
        """Execute should rewrite subparser name in cli.py."""
        _add_files(rename_project, {
            "src/myco/cli.py": (
                'alpha_parser = subparsers.add_parser(\n'
                '    "alpha",\n'
                '    help="Run alpha",\n'
                ')\n'
                'if args.command == "alpha":\n'
                '    from myco.alpha import run_alpha\n'
                '    sys.exit(run_alpha(args))\n'
            ),
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        execute_plan(plan)

        content = (rename_project / "src" / "myco" / "cli.py").read_text(encoding="utf-8")
        assert '"beta"' in content
        assert "from myco.beta import run_beta" in content
        # Old references gone
        assert '"alpha"' not in content
        assert "from myco.alpha" not in content


class TestRenameEdgeCases:
    """Edge cases and error handling."""

    def test_same_name_errors(self, rename_project):
        """Renaming to the same name should produce an error."""
        plan = build_plan("alpha", "alpha", str(rename_project))
        assert len(plan.errors) > 0
        assert "identical" in plan.errors[0].lower()

    def test_invalid_identifier_errors(self, rename_project):
        """Non-identifier names should produce an error."""
        plan = build_plan("123bad", "good", str(rename_project))
        assert len(plan.errors) > 0

    def test_no_matching_files(self, rename_project):
        """Renaming a non-existent module should produce an empty plan (no error)."""
        plan = build_plan("nonexistent", "newname", str(rename_project))
        # No errors -- just nothing to do
        assert len(plan.errors) == 0
        # May have zero actions (no files found, no references)
        # This is valid: the rename is a no-op

    def test_cmd_file_only(self, rename_project):
        """When only _cmd.py exists (no core .py), should still rename it."""
        _add_files(rename_project, {
            "src/myco/alpha_cmd.py": "# command module\n",
        })

        plan = build_plan("alpha", "beta", str(rename_project))
        git_mv_actions = [a for a in plan.actions if a.kind == "git_mv"]

        sources = {a.source for a in git_mv_actions}
        assert "src/myco/alpha_cmd.py" in sources

    def test_canon_yaml_updated(self, rename_project):
        """References in _canon.yaml should be updated."""
        canon_with_ref = _CANON + (
            "  tools:\n"
            "    - myco_alpha\n"
        )
        (rename_project / "_canon.yaml").write_text(canon_with_ref, encoding="utf-8")

        plan = build_plan("alpha", "beta", str(rename_project))
        execute_plan(plan)

        content = (rename_project / "_canon.yaml").read_text(encoding="utf-8")
        assert "myco_beta" in content
        assert "myco_alpha" not in content
