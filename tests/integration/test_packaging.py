"""Packaging contract tests.

Pin the externally visible shape of the distribution so packaging
regressions (missing console script, stray ephemeral in sdist, lost
extras target, MCP command drift) fail loudly in CI rather than
silently at user install time.
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
GITIGNORE = REPO_ROOT / ".gitignore"


def _pyproject() -> dict:
    with open(PYPROJECT, "rb") as fh:
        return tomllib.load(fh)


# ---------------------------------------------------------------------------
# Console scripts
# ---------------------------------------------------------------------------


def test_myco_cli_script_declared() -> None:
    scripts = _pyproject()["project"]["scripts"]
    assert scripts.get("myco") == "myco.surface.cli:main"


def test_mcp_server_console_script_declared() -> None:
    """Every .mcp.json in the ecosystem should be able to just say
    `command: "mcp-server-myco"`. That requires this entry point.
    """
    scripts = _pyproject()["project"]["scripts"]
    assert scripts.get("mcp-server-myco") == "myco.mcp:main", scripts


# ---------------------------------------------------------------------------
# Optional-deps
# ---------------------------------------------------------------------------


def test_mcp_extras_pins_mcp_package() -> None:
    extras = _pyproject()["project"]["optional-dependencies"]
    assert "mcp" in extras, extras
    pins = extras["mcp"]
    assert any(re.match(r"^mcp\b", p) for p in pins), pins


def test_dev_extras_has_pytest() -> None:
    extras = _pyproject()["project"]["optional-dependencies"]
    dev = extras.get("dev", [])
    assert any(p.startswith("pytest") for p in dev), dev


# ---------------------------------------------------------------------------
# Sdist hygiene
# ---------------------------------------------------------------------------


def test_sdist_excludes_release_ephemerals() -> None:
    """Ensure the hatch sdist config actively excludes release-scratch
    files. Earlier Stage C cycles let a `.release_notes_*.md` land
    uncommitted but on disk; without this exclude list, a mid-release
    `python -m build` would ship it to PyPI.
    """
    sdist_cfg = _pyproject()["tool"]["hatch"]["build"]["targets"]["sdist"]
    excludes = sdist_cfg["exclude"]
    expected = {
        "/.release_notes_*.md",
        "/upload*.log",
        "/dist",
        "/build",
        "/legacy_v0_3",
    }
    assert expected.issubset(set(excludes)), expected - set(excludes)


def test_gitignore_covers_release_ephemerals() -> None:
    text = GITIGNORE.read_text(encoding="utf-8")
    assert ".release_notes_*.md" in text
    assert "upload*.log" in text
    assert "legacy_v0_3/" in text
