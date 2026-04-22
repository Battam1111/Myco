"""Structural tests for the Cowork plugin template shipped at repo root.

The `.cowork-plugin/` tree is the source-of-truth template that
`scripts/install_cowork_plugin.py` copies into every
`<appdata>/Claude/local-agent-mode-sessions/<owner>/<workspace>/rpm/`
directory. A malformed template silently installs a broken plugin that
Cowork would fail to load — these tests catch that before release.

Scope: contract invariants on files shipped with the repo. Does NOT
exercise the installer (see `test_install_cowork_plugin.py` for that).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COWORK_ROOT = REPO_ROOT / ".cowork-plugin"
COWORK_PLUGIN_MANIFEST = COWORK_ROOT / ".claude-plugin" / "plugin.json"
COWORK_MCP_CONFIG = COWORK_ROOT / ".mcp.json"
COWORK_SKILLS_DIR = COWORK_ROOT / "skills"
COWORK_SKILL_MD = COWORK_SKILLS_DIR / "myco-substrate" / "SKILL.md"


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Template presence.
# ---------------------------------------------------------------------------


def test_cowork_plugin_directory_exists() -> None:
    assert COWORK_ROOT.is_dir(), COWORK_ROOT
    assert (COWORK_ROOT / "README.md").is_file()


# ---------------------------------------------------------------------------
# plugin.json
# ---------------------------------------------------------------------------


def test_cowork_plugin_manifest_parses() -> None:
    assert COWORK_PLUGIN_MANIFEST.is_file(), COWORK_PLUGIN_MANIFEST
    _load(COWORK_PLUGIN_MANIFEST)


def test_cowork_plugin_manifest_has_required_fields() -> None:
    data = _load(COWORK_PLUGIN_MANIFEST)
    assert data["name"] == "myco"
    for field in ("version", "description", "author", "homepage", "repository"):
        assert field in data, field


def test_cowork_plugin_version_tracks_package_version() -> None:
    """Cowork plugin version must match ``myco.__version__`` so the
    Cowork UI shows the same release number as PyPI and the Claude
    Code plugin bundle at the repo root.
    """
    import myco

    data = _load(COWORK_PLUGIN_MANIFEST)
    assert data["version"] == myco.__version__, (
        f".cowork-plugin/.claude-plugin/plugin.json version {data['version']!r} "
        f"does not match myco.__version__ {myco.__version__!r}"
    )


# ---------------------------------------------------------------------------
# .mcp.json
# ---------------------------------------------------------------------------


def test_cowork_mcp_config_points_at_myco_mcp_launcher() -> None:
    """The Cowork bundle uses ``python -m myco.mcp`` (stdio launcher)
    rather than the bare ``mcp-server-myco`` console script: Claude
    Desktop / Cowork spawns MCP servers from a GUI context where a
    user-site Scripts dir may not be on PATH.
    """
    data = _load(COWORK_MCP_CONFIG)
    servers = data["mcpServers"]
    assert "myco" in servers, servers
    entry = servers["myco"]
    assert entry["command"] == "python", entry
    assert entry["args"] == ["-m", "myco.mcp"], entry


# ---------------------------------------------------------------------------
# skills/myco-substrate/SKILL.md
# ---------------------------------------------------------------------------


def test_cowork_skill_file_exists() -> None:
    assert COWORK_SKILL_MD.is_file(), COWORK_SKILL_MD


def test_cowork_skill_frontmatter_shape() -> None:
    text = COWORK_SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "frontmatter must open with `---`"
    closing = text.find("\n---\n", 4)
    assert closing > 0, "frontmatter must close with `---`"
    frontmatter = text[4:closing]
    assert "name: myco-substrate" in frontmatter
    assert "description:" in frontmatter


def test_cowork_skill_body_asserts_correct_framing() -> None:
    """The skill body is the agent's first contact with Myco. It must
    teach the correct category (cognitive substrate, not memory tool)
    and list the R1-R7 contract rules — any regression here would ship
    a mis-framed onboarding to every Cowork user.
    """
    text = COWORK_SKILL_MD.read_text(encoding="utf-8")
    # Core framing
    assert "cognitive substrate" in text.lower()
    assert "not" in text and "memory" in text.lower()
    # Contract rules
    for rule in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        assert rule in text, f"skill body missing contract rule {rule}"
    # Verbs — sample the five subsystems
    for verb in (
        "myco_hunger",
        "myco_sense",
        "myco_eat",
        "myco_senesce",
        "myco_immune",
    ):
        assert verb in text, f"skill body missing verb {verb}"
    # The pulse-reading contract that makes multi-project routing work.
    assert "substrate_pulse" in text
    assert "project_dir_source" in text
