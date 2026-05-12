"""Structural tests for the Cowork plugin .zip bundle Myco ships.

Pre-v0.8.5 these tests examined the standalone `.cowork-plugin/` source
template directory. v0.8.5 excreted that directory and unified the
Cowork-bundle sources with the Claude Code marketplace plugin
(`.claude-plugin/plugin.json` + root `.mcp.json` + `.plugin/skills/
myco-substrate/SKILL.md`). These tests now build the bundle in a
tmp_path and assert structural invariants on the produced .zip itself
— the thing Claude Desktop's upload validator actually parses.

Scope: contract invariants on the .zip artifact Myco ships. Does NOT
exercise the install (see `test_install_cowork_plugin.py` for the
prepare-for-upload flow + AppData rpm cleanup).
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Cowork bundle sources (v0.8.5+): derived from the Claude Code
# marketplace files at build time.
ROOT_PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
ROOT_MCP_CONFIG = REPO_ROOT / ".mcp.json"
ROOT_SKILL_MD = REPO_ROOT / ".plugin" / "skills" / "myco-substrate" / "SKILL.md"


def _load_zip_member(zf: zipfile.ZipFile, member: str) -> bytes:
    return zf.read(member)


def _build_bundle(tmp_path: Path) -> Path:
    import myco
    from myco.boundary.install.install_helpers_cluster import build_plugin_bundle

    return build_plugin_bundle(
        REPO_ROOT,
        version=myco.__version__,
        dest_dir=tmp_path,
    )


def test_bundle_sources_present() -> None:
    """The three v0.8.5+ bundle sources exist at known paths."""
    assert ROOT_PLUGIN_MANIFEST.is_file(), ROOT_PLUGIN_MANIFEST
    assert ROOT_MCP_CONFIG.is_file(), ROOT_MCP_CONFIG
    assert ROOT_SKILL_MD.is_file(), ROOT_SKILL_MD


def test_bundle_zip_top_level_layout(tmp_path: Path) -> None:
    """The .zip must hold a single top-level `myco/` directory with the
    three required entries inside."""
    out = _build_bundle(tmp_path)
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())

    assert "myco/.claude-plugin/plugin.json" in names
    assert "myco/.mcp.json" in names
    assert "myco/skills/myco-substrate/SKILL.md" in names

    top_levels = {n.split("/", 1)[0] for n in names}
    assert top_levels == {"myco"}, top_levels


def test_bundle_plugin_json_has_required_fields(tmp_path: Path) -> None:
    out = _build_bundle(tmp_path)
    with zipfile.ZipFile(out) as zf:
        data = json.loads(_load_zip_member(zf, "myco/.claude-plugin/plugin.json"))

    assert data["name"] == "myco"
    for field in ("version", "description", "author", "homepage", "repository"):
        assert field in data, field


def test_bundle_plugin_json_strips_claude_code_pointer_keys(tmp_path: Path) -> None:
    """The Cowork .zip inlines its skill content (under `myco/skills/`)
    rather than dereferencing pointers — so the .zip's plugin.json must
    NOT carry the Claude Code marketplace pointer keys."""
    out = _build_bundle(tmp_path)
    with zipfile.ZipFile(out) as zf:
        data = json.loads(_load_zip_member(zf, "myco/.claude-plugin/plugin.json"))

    forbidden = {"mcpServers", "hooks", "skills", "agents", "commands"}
    leaked = forbidden & set(data.keys())
    assert not leaked, (
        f"Cowork-flavored plugin.json must strip pointer keys "
        f"{sorted(forbidden)}; found {sorted(leaked)} still present."
    )


def test_bundle_plugin_json_version_matches_package(tmp_path: Path) -> None:
    """Bundle plugin.json version must match the ``myco.__version__`` base
    (PyPI ``.postN`` suffix per v0.6.0 path-B is stripped first)."""
    import re

    import myco

    out = _build_bundle(tmp_path)
    with zipfile.ZipFile(out) as zf:
        data = json.loads(_load_zip_member(zf, "myco/.claude-plugin/plugin.json"))

    base = re.sub(r"\.(post|dev)\d+$", "", myco.__version__)
    assert data["version"] in (myco.__version__, base), (
        f"bundle plugin.json version {data['version']!r} matches "
        f"neither myco.__version__ {myco.__version__!r} nor base {base!r}"
    )


def test_bundle_mcp_config_points_at_myco_mcp_launcher(tmp_path: Path) -> None:
    """The Cowork bundle uses ``python -m myco.boundary.mcp`` (stdio launcher)
    rather than the bare ``mcp-server-myco`` console script."""
    out = _build_bundle(tmp_path)
    with zipfile.ZipFile(out) as zf:
        data = json.loads(_load_zip_member(zf, "myco/.mcp.json"))

    servers = data["mcpServers"]
    assert "myco" in servers, servers
    entry = servers["myco"]
    assert entry["command"] == "python", entry
    assert entry["args"] == ["-m", "myco.boundary.mcp"], entry


def test_bundle_skill_frontmatter_shape(tmp_path: Path) -> None:
    out = _build_bundle(tmp_path)
    with zipfile.ZipFile(out) as zf:
        text = _load_zip_member(zf, "myco/skills/myco-substrate/SKILL.md").decode(
            "utf-8"
        )

    assert text.startswith("---\n"), "frontmatter must open with `---`"
    closing = text.find("\n---\n", 4)
    assert closing > 0, "frontmatter must close with `---`"
    frontmatter = text[4:closing]
    assert "name: myco-substrate" in frontmatter
    assert "description:" in frontmatter


def test_bundle_skill_body_asserts_correct_framing(tmp_path: Path) -> None:
    """The skill body must teach the correct category and list R1-R7."""
    out = _build_bundle(tmp_path)
    with zipfile.ZipFile(out) as zf:
        text = _load_zip_member(zf, "myco/skills/myco-substrate/SKILL.md").decode(
            "utf-8"
        )

    assert "cognitive substrate" in text.lower()
    assert "not" in text and "memory" in text.lower()
    for rule in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        assert rule in text, f"skill body missing contract rule {rule}"
    for verb in (
        "myco_hunger",
        "myco_sense",
        "myco_eat",
        "myco_senesce",
        "myco_immune",
    ):
        assert verb in text, f"skill body missing verb {verb}"
    assert "substrate_pulse" in text
    assert "project_dir_source" in text


def test_build_raises_on_missing_source(tmp_path: Path) -> None:
    """Calling build_plugin_bundle on an empty directory must raise."""
    from myco.boundary.install.install_helpers_cluster import (
        PluginBundleError,
        build_plugin_bundle,
    )

    with pytest.raises(PluginBundleError):
        build_plugin_bundle(tmp_path, version="0.0.0", dest_dir=tmp_path)


def test_build_raises_on_version_mismatch(tmp_path: Path) -> None:
    """Caller-supplied version must match plugin.json::version."""
    from myco.boundary.install.install_helpers_cluster import (
        PluginBundleError,
        build_plugin_bundle,
    )

    with pytest.raises(PluginBundleError):
        build_plugin_bundle(REPO_ROOT, version="99.99.99", dest_dir=tmp_path)
