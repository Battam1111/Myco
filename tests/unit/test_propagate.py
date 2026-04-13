"""Unit tests for myco.propagate_cmd — SSoT value propagation."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CANON_WITH_CLAIM = """\
system:
  principles_count: 13
  principles_label: "十三原則"
  entry_point: MYCO.md
  contract_version: "v0.24.0"
  synced_contract_version: "v0.24.0"
  numeric_claims:
    mcp_tool_count:
      ssot: "count of @mcp.tool in src/myco/mcp_server.py"
      value: 21
      cited_in: ["README.md"]
    lint_dimensions:
      ssot: "len(FULL_CHECKS)"
      value: 25
      cited_in: ["docs/arch.md"]
    test_count:
      ssot: "pytest output"
      value: 300
      cited_in: ["MYCO.md"]
    principles_count:
      ssot: "_canon.yaml"
      value: 13
      cited_in: ["docs/vision.md"]
architecture:
  layers: 4
  wiki_pages: 0
project:
  name: TestProject
"""


def _setup_project(project: Path, canon: str, files: dict[str, str] | None = None):
    """Write _canon.yaml and any extra files into the project fixture."""
    (project / "_canon.yaml").write_text(canon, encoding="utf-8")
    if files:
        for relpath, content in files.items():
            p = project / relpath
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPropagateUpdatesCitedIn:
    """run_propagate rewrites stale values in cited_in files."""

    def test_mcp_tool_count_english(self, tmp_path):
        """Stale '19 tools' in README.md is updated to '21 tools'."""
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM, {
            "README.md": "Myco exposes 19 tools via MCP.\n",
        })

        from myco.propagate_cmd import run_propagate
        args = SimpleNamespace(project_dir=str(project))
        rc = run_propagate(args)

        assert rc == 0
        content = (project / "README.md").read_text(encoding="utf-8")
        assert "21 tools" in content
        assert "19 tools" not in content

    def test_mcp_tool_count_chinese(self, tmp_path):
        """Stale '19 个工具' is updated to '21 个工具'."""
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM, {
            "README.md": "提供 19 个工具。\n",
        })

        from myco.propagate_cmd import run_propagate
        args = SimpleNamespace(project_dir=str(project))
        run_propagate(args)

        content = (project / "README.md").read_text(encoding="utf-8")
        assert "21 个工具" in content

    def test_lint_dimensions(self, tmp_path):
        """Stale '23-dimension' is updated to '25-dimension'."""
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM, {
            "docs/arch.md": "A 23-dimension lint check.\n",
        })

        from myco.propagate_cmd import run_propagate
        args = SimpleNamespace(project_dir=str(project))
        run_propagate(args)

        content = (project / "docs" / "arch.md").read_text(encoding="utf-8")
        assert "25-dimension" in content
        assert "23-dimension" not in content

    def test_test_count(self, tmp_path):
        """Stale '240 tests' is updated to '300 tests'."""
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM, {
            "MYCO.md": "We have 240 tests passing.\n",
        })

        from myco.propagate_cmd import run_propagate
        args = SimpleNamespace(project_dir=str(project))
        run_propagate(args)

        content = (project / "MYCO.md").read_text(encoding="utf-8")
        assert "300 tests" in content
        assert "240 tests" not in content

    def test_principles_count(self, tmp_path):
        """Stale '10 principles' is updated to '13 principles'."""
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM, {
            "docs/vision.md": "The system follows 10 principles (W1-W10).\n",
        })

        from myco.propagate_cmd import run_propagate
        args = SimpleNamespace(project_dir=str(project))
        run_propagate(args)

        content = (project / "docs" / "vision.md").read_text(encoding="utf-8")
        assert "13 principles" in content
        assert "W1-W13" in content

    def test_missing_cited_in_file(self, tmp_path, capsys):
        """Missing cited_in file prints a warning but does not crash."""
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM)
        # Do NOT create README.md — it's cited_in but absent

        from myco.propagate_cmd import run_propagate
        args = SimpleNamespace(project_dir=str(project))
        rc = run_propagate(args)

        assert rc == 0
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestPropagateIdempotent:
    """Running propagate twice produces the same result."""

    def test_double_run_no_change(self, tmp_path):
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM, {
            "README.md": "Myco exposes 19 MCP tools.\n",
            "docs/arch.md": "A 23-dimension lint.\n",
            "MYCO.md": "240 tests.\n",
            "docs/vision.md": "10 principles.\n",
        })

        from myco.propagate_cmd import run_propagate

        # First run
        args = SimpleNamespace(project_dir=str(project))
        run_propagate(args)

        # Capture state after first run
        readme_after_1 = (project / "README.md").read_text(encoding="utf-8")
        arch_after_1 = (project / "docs" / "arch.md").read_text(encoding="utf-8")

        # Second run — should be a no-op
        args2 = SimpleNamespace(project_dir=str(project))
        rc = run_propagate(args2)

        assert rc == 0
        assert (project / "README.md").read_text(encoding="utf-8") == readme_after_1
        assert (project / "docs" / "arch.md").read_text(encoding="utf-8") == arch_after_1

    def test_already_aligned(self, tmp_path, capsys):
        """When values already match, reports 'already aligned'."""
        project = tmp_path / "project"
        _setup_project(project, _CANON_WITH_CLAIM, {
            "README.md": "Myco exposes 21 tools via MCP.\n",
            "docs/arch.md": "A 25-dimension lint check.\n",
            "MYCO.md": "300 tests.\n",
            "docs/vision.md": "13 principles.\n",
        })

        from myco.propagate_cmd import run_propagate
        args = SimpleNamespace(project_dir=str(project))
        rc = run_propagate(args)

        assert rc == 0
        captured = capsys.readouterr()
        assert "already aligned" in captured.out
