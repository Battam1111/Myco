"""Structural tests for the Myco Claude-Code / Cowork plugin bundle.

Scope: verify that the files shipped at the repo root form a valid
plugin according to the documented format (see
https://code.claude.com/docs/en/plugins-reference). Does not exercise
Claude Code's actual install path — that's integration with an
external runtime. Instead we test the contract: manifests parse,
required fields are present, and paths referenced from the manifest
actually exist.

Failing any of these blocks release: a malformed manifest will fail
silently in Claude Code's marketplace view rather than erroring loudly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".claude-plugin" / "marketplace.json"
MCP_CONFIG = REPO_ROOT / ".mcp.json"
HOOKS_CONFIG = REPO_ROOT / "hooks" / "hooks.json"
SKILLS_DIR = REPO_ROOT / "skills"


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# plugin.json
# ---------------------------------------------------------------------------


def test_plugin_manifest_parses() -> None:
    assert PLUGIN_MANIFEST.exists(), PLUGIN_MANIFEST
    _load(PLUGIN_MANIFEST)


def test_plugin_manifest_has_required_fields() -> None:
    data = _load(PLUGIN_MANIFEST)
    # Required
    assert data["name"] == "myco"
    # Strongly recommended
    for field in ("version", "description", "author", "homepage",
                  "repository", "license", "keywords"):
        assert field in data, field


def test_plugin_manifest_references_existing_paths() -> None:
    data = _load(PLUGIN_MANIFEST)
    for key, target in data.items():
        if not isinstance(target, str) or not target.startswith("./"):
            continue
        resolved = REPO_ROOT / target[2:]
        assert resolved.exists(), (key, target, resolved)


def test_plugin_version_tracks_package_version() -> None:
    """Plugin version should match ``myco.__version__`` so marketplace
    update detection and PyPI release stay aligned.
    """
    import myco
    data = _load(PLUGIN_MANIFEST)
    assert data["version"] == myco.__version__, (
        f"plugin.json version {data['version']!r} does not match "
        f"myco.__version__ {myco.__version__!r}"
    )


# ---------------------------------------------------------------------------
# marketplace.json
# ---------------------------------------------------------------------------


def test_marketplace_manifest_parses() -> None:
    assert MARKETPLACE_MANIFEST.exists()
    _load(MARKETPLACE_MANIFEST)


def test_marketplace_lists_exactly_one_plugin_at_repo_root() -> None:
    data = _load(MARKETPLACE_MANIFEST)
    assert data["name"] == "myco"
    assert isinstance(data.get("plugins"), list) and len(data["plugins"]) == 1
    plugin = data["plugins"][0]
    assert plugin["name"] == "myco"
    assert plugin["source"] == "."


# ---------------------------------------------------------------------------
# .mcp.json
# ---------------------------------------------------------------------------


def test_mcp_config_points_at_myco_mcp_launcher() -> None:
    """The repo-root .mcp.json uses the bare mcp-server-myco console
    script (for Claude Code terminal use where PATH is inherited).
    GUI apps should use myco-install which writes the absolute Python
    path instead.
    """
    data = _load(MCP_CONFIG)
    servers = data["mcpServers"]
    assert "myco" in servers
    entry = servers["myco"]
    assert entry["command"] == "mcp-server-myco", entry
    assert entry["args"] == [], entry


def test_hooks_use_python_m_myco() -> None:
    """Hook commands must invoke ``python -m myco`` rather than the
    bare ``myco`` console script.

    Rationale (v0.4.4 hotfix): the console script lands in a pip
    Scripts directory that may not be on PATH, and any stale
    pre-v0.4 myco on PATH will shadow the current version and fail
    the hook (v0.3 does not understand ``--project-dir``). Using
    ``python -m myco`` dispatches through whichever Python is on
    PATH, which then finds the currently-installed myco package.
    """
    data = _load(HOOKS_CONFIG)
    for event in ("SessionStart", "PreCompact"):
        cmd = data["hooks"][event][0]["hooks"][0]["command"]
        assert cmd.startswith("python -m myco "), (event, cmd)


# ---------------------------------------------------------------------------
# hooks/hooks.json
# ---------------------------------------------------------------------------


def test_hooks_declares_session_boundaries() -> None:
    data = _load(HOOKS_CONFIG)
    hooks = data["hooks"]
    assert "SessionStart" in hooks
    assert "PreCompact" in hooks
    for event in ("SessionStart", "PreCompact"):
        entries = hooks[event]
        assert entries and isinstance(entries, list)
        inner = entries[0]["hooks"]
        assert inner and inner[0]["type"] == "command"


def test_hooks_invoke_myco_verbs() -> None:
    """SessionStart must fire hunger, PreCompact must fire the session-
    close verb — R1 and R2 of the Hard Contract. v0.5.3 renamed
    ``session-end`` → ``senesce``; the PreCompact hook may use either
    the canonical name or the legacy alias (both resolve via the
    manifest's ``aliases`` field)."""
    data = _load(HOOKS_CONFIG)
    ss_cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    pc_cmd = data["hooks"]["PreCompact"][0]["hooks"][0]["command"]
    assert " hunger" in ss_cmd
    assert " senesce" in pc_cmd or " session-end" in pc_cmd


# ---------------------------------------------------------------------------
# skills/*/SKILL.md
# ---------------------------------------------------------------------------


SKILL_FRONTMATTER_REQUIRED = ("name", "description")


@pytest.mark.parametrize("skill_name", ["hunger", "session-end"])
def test_skill_file_exists(skill_name: str) -> None:
    assert (SKILLS_DIR / skill_name / "SKILL.md").exists()


@pytest.mark.parametrize("skill_name", ["hunger", "session-end"])
def test_skill_has_required_frontmatter(skill_name: str) -> None:
    text = (SKILLS_DIR / skill_name / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), "frontmatter must open with `---`"
    closing = text.find("\n---\n", 4)
    assert closing > 0, "frontmatter must close with `---`"
    frontmatter = text[4:closing]
    for key in SKILL_FRONTMATTER_REQUIRED:
        assert f"{key}:" in frontmatter, (skill_name, key)
