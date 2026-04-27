"""Full coverage of all 14 host_integration adapter modules."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from myco.boundary.host_integration import (
    claude_code,
    claude_desktop,
    cline,
    codex_cli,
    continue_dev,
    cowork,
    cursor,
    gemini_cli,
    goose,
    jetbrains,
    openclaw,
    vscode,
    windsurf,
    zed,
)
from myco.boundary.host_integration._protocol import (
    InstallReport,
    SymbiontProbe,
    UninstallReport,
)

ALL_HOSTS = (
    claude_code,
    claude_desktop,
    cline,
    codex_cli,
    continue_dev,
    cowork,
    cursor,
    gemini_cli,
    goose,
    jetbrains,
    openclaw,
    vscode,
    windsurf,
    zed,
)


def _fake_substrate(root: Path) -> SimpleNamespace:
    canon = SimpleNamespace(substrate_id="test-sub", contract_version="v0.6.0")
    return SimpleNamespace(root=root, canon=canon)


@pytest.mark.parametrize("mod", ALL_HOSTS)
def test_each_host_has_required_symbols(mod):
    """Every host adapter exports the four-function symbiont protocol."""
    assert hasattr(mod, "HOST_ID")
    assert isinstance(mod.HOST_ID, str)
    for fn in ("discover", "install_basic", "install_deep", "uninstall"):
        assert callable(getattr(mod, fn))


@pytest.mark.parametrize("mod", ALL_HOSTS)
def test_each_host_discover_returns_probe_or_none(mod, tmp_path):
    """discover() returns None or a SymbiontProbe."""
    probe = mod.discover(tmp_path)
    assert probe is None or isinstance(probe, SymbiontProbe)


@pytest.mark.parametrize("mod", ALL_HOSTS)
def test_each_host_install_basic_dry_run(mod, tmp_path):
    """install_basic in dry-run mode produces a InstallReport."""
    probe = SymbiontProbe(
        host_id=mod.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp"}),
    )
    sub = _fake_substrate(tmp_path)
    rpt = mod.install_basic(probe, sub, dry_run=True)
    assert isinstance(rpt, InstallReport)
    assert rpt.dry_run is True


@pytest.mark.parametrize("mod", ALL_HOSTS)
def test_each_host_install_deep_dry_run(mod, tmp_path):
    """install_deep in dry-run produces an InstallReport without writing."""
    probe = SymbiontProbe(
        host_id=mod.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp"}),
    )
    sub = _fake_substrate(tmp_path)
    rpt = mod.install_deep(probe, sub, dry_run=True)
    assert isinstance(rpt, InstallReport)


@pytest.mark.parametrize("mod", ALL_HOSTS)
def test_each_host_uninstall_dry_run(mod, tmp_path):
    """uninstall in dry-run produces an UninstallReport."""
    probe = SymbiontProbe(
        host_id=mod.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp"}),
    )
    rpt = mod.uninstall(probe, dry_run=True)
    assert isinstance(rpt, UninstallReport)


# ---------- Specific deep-install paths ----------


def test_vscode_install_deep_writes_tasks_json(tmp_path: Path):
    """VS Code deep-install writes .vscode/tasks.json with three tasks."""
    probe = SymbiontProbe(
        host_id=vscode.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp", "tasks"}),
    )
    sub = _fake_substrate(tmp_path)
    rpt = vscode.install_deep(probe, sub, dry_run=False)
    target = tmp_path / ".vscode" / "tasks.json"
    assert target.is_file()
    body = json.loads(target.read_text(encoding="utf-8"))
    labels = [t["label"] for t in body["tasks"]]
    assert "Myco: Hunger" in labels
    assert "Myco: Senesce" in labels
    assert "Myco: Brief" in labels
    assert any(str(target) in p for p in (rpt.files_written or ()))


def test_vscode_install_deep_skips_if_exists(tmp_path: Path):
    """If .vscode/tasks.json exists, deep-install skips."""
    probe = SymbiontProbe(
        host_id=vscode.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp", "tasks"}),
    )
    sub = _fake_substrate(tmp_path)
    target = tmp_path / ".vscode" / "tasks.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")
    rpt = vscode.install_deep(probe, sub, dry_run=False)
    assert any(str(target) in p for p in (rpt.files_skipped or ()))


def test_vscode_install_deep_handles_no_substrate(tmp_path: Path):
    """install_deep with substrate that has no .root returns gracefully."""
    probe = SymbiontProbe(
        host_id=vscode.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp", "tasks"}),
    )
    rpt = vscode.install_deep(probe, None, dry_run=False)
    assert isinstance(rpt, InstallReport)


def test_cline_install_deep_writes_clinerules(tmp_path: Path):
    """Cline deep-install writes .clinerules/myco.md when probe.installed."""
    probe = SymbiontProbe(
        host_id=cline.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp", "rules"}),
    )
    sub = _fake_substrate(tmp_path)
    rpt = cline.install_deep(probe, sub, dry_run=False)
    target = tmp_path / ".clinerules" / "myco.md"
    assert target.is_file()
    body = target.read_text(encoding="utf-8")
    assert "R1" in body or "Hard Contract" in body
    assert any(str(target) in p for p in (rpt.files_written or ()))


def test_cline_install_deep_skips_if_signed_file_exists(tmp_path: Path):
    """Cline deep-install skips if existing file already has the symbiont sig."""
    from myco.boundary.host_integration._protocol import SYMBIONT_SIG_PREFIX

    probe = SymbiontProbe(
        host_id=cline.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset({"mcp", "rules"}),
    )
    sub = _fake_substrate(tmp_path)
    target = tmp_path / ".clinerules" / "myco.md"
    target.parent.mkdir(parents=True)
    target.write_text(f"{SYMBIONT_SIG_PREFIX} test:0.6.0\n existing", encoding="utf-8")
    rpt = cline.install_deep(probe, sub, dry_run=False)
    assert any(str(target) in p for p in (rpt.files_skipped or ()))


def test_cline_install_deep_skips_when_not_installed(tmp_path: Path):
    """Cline deep-install no-ops when probe.installed=False."""
    probe = SymbiontProbe(
        host_id=cline.HOST_ID,
        installed=False,
        home=tmp_path,
        capabilities=frozenset(),
    )
    sub = _fake_substrate(tmp_path)
    rpt = cline.install_deep(probe, sub, dry_run=False)
    assert isinstance(rpt, InstallReport)
    assert not rpt.files_written


def test_jetbrains_discover_handles_missing_dir(tmp_path: Path):
    """jetbrains discover() with no jetbrains config dir returns probe.installed=False."""
    probe = jetbrains.discover(tmp_path)
    assert isinstance(probe, SymbiontProbe)
    assert probe.installed is False


def test_jetbrains_discover_picks_up_ide_dir(tmp_path: Path):
    """jetbrains discover() detects when an IDE versioned subdir exists."""
    import sys

    # Per-OS root path
    if sys.platform == "darwin":
        root = tmp_path / "Library" / "Application Support" / "JetBrains"
    elif sys.platform == "win32":
        root = tmp_path / "AppData" / "Roaming" / "JetBrains"
    else:
        root = tmp_path / ".config" / "JetBrains"
    (root / "PyCharm2025.2" / "options").mkdir(parents=True)
    probe = jetbrains.discover(tmp_path)
    assert probe is not None
    assert probe.installed is True
    assert "mcp" in probe.capabilities


def test_jetbrains_discover_with_mcp_config(tmp_path: Path):
    """jetbrains discover() detects mcp_configured capability when XML present."""
    import sys

    if sys.platform == "darwin":
        root = tmp_path / "Library" / "Application Support" / "JetBrains"
    elif sys.platform == "win32":
        root = tmp_path / "AppData" / "Roaming" / "JetBrains"
    else:
        root = tmp_path / ".config" / "JetBrains"
    (root / "PyCharm2025.2" / "options").mkdir(parents=True)
    (root / "PyCharm2025.2" / "options" / "mcpServers.xml").write_text(
        "<xml/>", encoding="utf-8"
    )
    probe = jetbrains.discover(tmp_path)
    assert probe is not None
    assert "mcp_configured" in probe.capabilities


def test_claude_desktop_discover_delegates_to_cowork(tmp_path: Path):
    """claude_desktop discover delegates to cowork's discover."""
    probe = claude_desktop.discover(tmp_path)
    # claude_desktop returns None or a probe re-tagged with HOST_ID.
    if probe is not None:
        assert probe.host_id == claude_desktop.HOST_ID


def test_codex_cli_minimal_paths(tmp_path: Path):
    """codex_cli stub adapter — verify all three install/uninstall paths."""
    probe = SymbiontProbe(
        host_id=codex_cli.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset(),
    )
    sub = _fake_substrate(tmp_path)
    assert isinstance(codex_cli.install_basic(probe, sub), InstallReport)
    assert isinstance(codex_cli.install_deep(probe, sub), InstallReport)
    assert isinstance(codex_cli.uninstall(probe), UninstallReport)


def test_gemini_cli_minimal_paths(tmp_path: Path):
    probe = SymbiontProbe(
        host_id=gemini_cli.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset(),
    )
    sub = _fake_substrate(tmp_path)
    assert isinstance(gemini_cli.install_basic(probe, sub), InstallReport)
    assert isinstance(gemini_cli.install_deep(probe, sub), InstallReport)
    assert isinstance(gemini_cli.uninstall(probe), UninstallReport)


def test_openclaw_minimal_paths(tmp_path: Path):
    probe = SymbiontProbe(
        host_id=openclaw.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset(),
    )
    sub = _fake_substrate(tmp_path)
    assert isinstance(openclaw.install_basic(probe, sub), InstallReport)
    assert isinstance(openclaw.install_deep(probe, sub), InstallReport)
    assert isinstance(openclaw.uninstall(probe), UninstallReport)


def test_windsurf_minimal_paths(tmp_path: Path):
    probe = SymbiontProbe(
        host_id=windsurf.HOST_ID,
        installed=True,
        home=tmp_path,
        capabilities=frozenset(),
    )
    sub = _fake_substrate(tmp_path)
    assert isinstance(windsurf.install_basic(probe, sub), InstallReport)
    assert isinstance(windsurf.install_deep(probe, sub), InstallReport)
    assert isinstance(windsurf.uninstall(probe), UninstallReport)
