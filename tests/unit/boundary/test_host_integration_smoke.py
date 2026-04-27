"""Smoke tests for all 14 host_integration adapters.

Each adapter implements the Symbiont protocol with four functions:
discover / install_basic / install_deep / uninstall. These tests
exercise each adapter's public surface against tmp_path so the
host-side write paths (when applicable) land in a sandbox.

Coverage focus: every public function in every adapter is invoked at
least once with both a discovered=True path and a discovered=False
path (where applicable). Idempotency (running install_deep twice) is
also exercised.
"""

from __future__ import annotations

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


def _fake_substrate(root: Path):
    """Minimal substrate-shaped object for adapters' install_deep."""
    return SimpleNamespace(
        root=root,
        canon=SimpleNamespace(substrate_id="test-substrate"),
    )


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """A throwaway $HOME for each test."""
    h = tmp_path / "home"
    h.mkdir()
    return h


# ---------------------------------------------------------------------------
# claude_code: introspection-only adapter
# ---------------------------------------------------------------------------


def test_claude_code_discover_no_claude_dir(home: Path):
    probe = claude_code.discover(home)
    assert probe is not None
    assert probe.host_id == "claude-code"
    assert probe.installed is False


def test_claude_code_discover_with_claude_dir(home: Path):
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    probe = claude_code.discover(home)
    assert probe.installed is True
    assert "settings" in probe.capabilities


def test_claude_code_install_basic_install_deep_uninstall(home: Path):
    sub = _fake_substrate(home)
    probe = claude_code.discover(home)
    rep = claude_code.install_basic(probe, sub, dry_run=True)
    assert rep.host_id == "claude-code"
    rep2 = claude_code.install_deep(probe, sub, dry_run=True)
    assert rep2.host_id == "claude-code"
    rep3 = claude_code.uninstall(probe, dry_run=True)
    assert rep3.host_id == "claude-code"


# ---------------------------------------------------------------------------
# cursor: writes ~/.cursor/rules/myco.mdc
# ---------------------------------------------------------------------------


def test_cursor_discover_no_dir(home: Path):
    probe = cursor.discover(home)
    assert probe.host_id == "cursor"


def test_cursor_install_deep_writes_rule_file(home: Path):
    (home / ".cursor").mkdir()
    sub = _fake_substrate(home)
    probe = cursor.discover(home)
    assert probe.installed is True
    rep = cursor.install_deep(probe, sub)
    assert any("myco.mdc" in f for f in rep.files_written)
    target = home / ".cursor" / "rules" / "myco.mdc"
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert "myco-symbiont-sig" in text


def test_cursor_install_deep_idempotent_dry_run(home: Path):
    (home / ".cursor").mkdir()
    sub = _fake_substrate(home)
    probe = cursor.discover(home)
    rep = cursor.install_deep(probe, sub, dry_run=True)
    assert rep.dry_run is True


def test_cursor_install_deep_skip_when_signed(home: Path):
    (home / ".cursor").mkdir()
    sub = _fake_substrate(home)
    probe = cursor.discover(home)
    cursor.install_deep(probe, sub)
    # Second call should skip.
    rep2 = cursor.install_deep(probe, sub)
    assert rep2.files_skipped or rep2.files_written == ()


def test_cursor_uninstall_removes_file(home: Path):
    (home / ".cursor").mkdir()
    sub = _fake_substrate(home)
    probe = cursor.discover(home)
    cursor.install_deep(probe, sub)
    rep = cursor.uninstall(probe)
    assert rep.files_removed
    rep_again = cursor.uninstall(probe)
    assert rep_again.files_not_found


def test_cursor_install_basic_no_op(home: Path):
    sub = _fake_substrate(home)
    probe = cursor.discover(home)
    rep = cursor.install_basic(probe, sub, dry_run=True)
    assert rep.host_id == "cursor"


def test_cursor_install_deep_not_installed(home: Path):
    sub = _fake_substrate(home)
    probe = cursor.discover(home)  # no .cursor/ → not installed
    rep = cursor.install_deep(probe, sub)
    assert rep.host_id == "cursor"


def test_cursor_uninstall_dry_run(home: Path):
    (home / ".cursor").mkdir()
    sub = _fake_substrate(home)
    probe = cursor.discover(home)
    cursor.install_deep(probe, sub)
    rep = cursor.uninstall(probe, dry_run=True)
    assert rep.dry_run is True


# ---------------------------------------------------------------------------
# continue_dev: writes ~/.continue/rules/myco.md
# ---------------------------------------------------------------------------


def test_continue_dev_discover_no_dir(home: Path):
    probe = continue_dev.discover(home)
    assert probe.host_id == "continue-dev"


def test_continue_dev_install_deep_writes_rule(home: Path):
    (home / ".continue").mkdir()
    sub = _fake_substrate(home)
    probe = continue_dev.discover(home)
    assert probe.installed is True
    rep = continue_dev.install_deep(probe, sub)
    assert any("myco.md" in f for f in rep.files_written)


def test_continue_dev_install_basic_install_deep_uninstall(home: Path):
    (home / ".continue").mkdir()
    sub = _fake_substrate(home)
    probe = continue_dev.discover(home)
    continue_dev.install_basic(probe, sub, dry_run=True)
    continue_dev.install_deep(probe, sub, dry_run=True)
    continue_dev.install_deep(probe, sub)  # actual write
    continue_dev.install_deep(probe, sub)  # idempotent skip
    continue_dev.uninstall(probe, dry_run=True)
    continue_dev.uninstall(probe)


# ---------------------------------------------------------------------------
# cline: writes substrate-local .clinerules/myco.md
# ---------------------------------------------------------------------------


def test_cline_discover_no_signal(home: Path):
    probe = cline.discover(home)
    assert probe is not None
    assert probe.host_id == "cline"


def test_cline_with_vscode_extensions(home: Path):
    (home / ".vscode" / "extensions").mkdir(parents=True)
    probe = cline.discover(home)
    assert probe.installed is True


def test_cline_install_deep_writes(home: Path, tmp_path: Path):
    (home / ".vscode" / "extensions").mkdir(parents=True)
    sub_root = tmp_path / "substrate"
    sub_root.mkdir()
    sub = SimpleNamespace(
        root=sub_root, canon=SimpleNamespace(substrate_id="test-sub")
    )
    probe = cline.discover(home)
    rep = cline.install_deep(probe, sub)
    assert rep.host_id == "cline"
    rep2 = cline.install_deep(probe, sub)
    rep3 = cline.install_basic(probe, sub, dry_run=True)
    assert rep3.host_id == "cline"
    cline.uninstall(probe, dry_run=True)


# ---------------------------------------------------------------------------
# zed: writes ~/.config/zed/commands/myco.toml
# ---------------------------------------------------------------------------


def test_zed_discover_no_dir(home: Path):
    probe = zed.discover(home)
    assert probe.host_id == "zed"


def test_zed_install_deep_writes_commands(home: Path):
    (home / ".config" / "zed").mkdir(parents=True)
    sub = _fake_substrate(home)
    probe = zed.discover(home)
    assert probe.installed is True
    rep = zed.install_deep(probe, sub)
    assert any("myco.toml" in f for f in rep.files_written)
    target = home / ".config" / "zed" / "commands" / "myco.toml"
    assert target.is_file()


def test_zed_full_lifecycle(home: Path):
    (home / ".config" / "zed").mkdir(parents=True)
    sub = _fake_substrate(home)
    probe = zed.discover(home)
    zed.install_basic(probe, sub, dry_run=True)
    zed.install_deep(probe, sub, dry_run=True)
    zed.install_deep(probe, sub)
    zed.install_deep(probe, sub)  # idempotent
    zed.uninstall(probe, dry_run=True)
    zed.uninstall(probe)
    zed.uninstall(probe)  # already-removed


# ---------------------------------------------------------------------------
# goose: writes ~/.config/goose/recipes/myco-bootstrap.yaml
# ---------------------------------------------------------------------------


def test_goose_discover_no_dir(home: Path):
    probe = goose.discover(home)
    assert probe.host_id == "goose"


def test_goose_install_deep_writes_recipe(home: Path):
    (home / ".config" / "goose").mkdir(parents=True)
    sub = _fake_substrate(home)
    probe = goose.discover(home)
    rep = goose.install_deep(probe, sub)
    assert rep.host_id == "goose"
    target = home / ".config" / "goose" / "recipes" / "myco-bootstrap.yaml"
    assert target.is_file()


def test_goose_full_lifecycle(home: Path):
    (home / ".config" / "goose").mkdir(parents=True)
    sub = _fake_substrate(home)
    probe = goose.discover(home)
    goose.install_basic(probe, sub, dry_run=True)
    goose.install_deep(probe, sub, dry_run=True)
    goose.install_deep(probe, sub)
    goose.install_deep(probe, sub)
    goose.uninstall(probe, dry_run=True)
    goose.uninstall(probe)
    goose.uninstall(probe)


# ---------------------------------------------------------------------------
# vscode: writes .vscode/tasks.json (substrate-local)
# ---------------------------------------------------------------------------


def test_vscode_discover_always_plausible(home: Path):
    probe = vscode.discover(home)
    assert probe.host_id == "vscode"
    assert probe.installed is True


def test_vscode_install_deep_writes_tasks(tmp_path: Path):
    sub_root = tmp_path / "substrate"
    sub_root.mkdir()
    sub = SimpleNamespace(root=sub_root)
    probe = vscode.discover(tmp_path)
    rep = vscode.install_deep(probe, sub)
    assert rep.host_id == "vscode"
    target = sub_root / ".vscode" / "tasks.json"
    assert target.is_file()


def test_vscode_install_deep_skip_if_exists(tmp_path: Path):
    sub_root = tmp_path / "substrate"
    sub_root.mkdir()
    (sub_root / ".vscode").mkdir()
    (sub_root / ".vscode" / "tasks.json").write_text("{}", encoding="utf-8")
    sub = SimpleNamespace(root=sub_root)
    probe = vscode.discover(tmp_path)
    rep = vscode.install_deep(probe, sub)
    assert rep.files_skipped


def test_vscode_full_lifecycle(tmp_path: Path):
    sub_root = tmp_path / "substrate"
    sub_root.mkdir()
    sub = SimpleNamespace(root=sub_root)
    probe = vscode.discover(tmp_path)
    vscode.install_basic(probe, sub, dry_run=True)
    vscode.install_deep(probe, sub, dry_run=True)
    vscode.uninstall(probe, dry_run=True)
    vscode.uninstall(probe)


# ---------------------------------------------------------------------------
# cowork: claude desktop variant
# ---------------------------------------------------------------------------


def test_cowork_discover_no_config(home: Path):
    probe = cowork.discover(home)
    assert probe.host_id == "cowork"
    assert probe.installed is False


def test_cowork_full_lifecycle(home: Path):
    sub = _fake_substrate(home)
    probe = cowork.discover(home)
    cowork.install_basic(probe, sub, dry_run=True)
    cowork.install_deep(probe, sub, dry_run=True)
    cowork.uninstall(probe, dry_run=True)


# ---------------------------------------------------------------------------
# claude_desktop: shares Cowork detection
# ---------------------------------------------------------------------------


def test_claude_desktop_discover_no_config(home: Path):
    probe = claude_desktop.discover(home)
    assert probe is None or probe.host_id == "claude-desktop"


def test_claude_desktop_full_lifecycle(home: Path):
    sub = _fake_substrate(home)
    # Even if discover returns None, exercise the install/uninstall paths.
    from myco.boundary.host_integration._protocol import SymbiontProbe

    fake_probe = SymbiontProbe(host_id="claude-desktop", installed=True, home=home)
    claude_desktop.install_basic(fake_probe, sub, dry_run=True)
    claude_desktop.install_deep(fake_probe, sub, dry_run=True)
    claude_desktop.uninstall(fake_probe, dry_run=True)


# ---------------------------------------------------------------------------
# jetbrains: detection-only adapter
# ---------------------------------------------------------------------------


def test_jetbrains_discover_no_dir(home: Path):
    probe = jetbrains.discover(home)
    assert probe.host_id == "jetbrains"


def test_jetbrains_with_ide_dir(home: Path, monkeypatch: pytest.MonkeyPatch):
    """Simulate a JetBrains IDE config directory."""
    import sys

    # Force per-OS root resolution to predictable Linux path
    monkeypatch.setattr(sys, "platform", "linux")
    jb_root = home / ".config" / "JetBrains" / "PyCharm2025.2"
    jb_root.mkdir(parents=True)
    (jb_root / "options").mkdir()
    (jb_root / "options" / "mcpServers.xml").write_text("<x/>", encoding="utf-8")
    probe = jetbrains.discover(home)
    assert probe.installed is True


def test_jetbrains_full_lifecycle(home: Path):
    sub = _fake_substrate(home)
    probe = jetbrains.discover(home)
    jetbrains.install_basic(probe, sub, dry_run=True)
    jetbrains.install_deep(probe, sub, dry_run=True)
    jetbrains.uninstall(probe, dry_run=True)


# ---------------------------------------------------------------------------
# windsurf / codex_cli / gemini_cli / openclaw — detection-only stubs
# ---------------------------------------------------------------------------


def test_windsurf_discover(home: Path):
    probe = windsurf.discover(home)
    assert probe.host_id == "windsurf"
    sub = _fake_substrate(home)
    windsurf.install_basic(probe, sub, dry_run=True)
    windsurf.install_deep(probe, sub, dry_run=True)
    windsurf.uninstall(probe, dry_run=True)


def test_codex_cli_discover(home: Path):
    (home / ".codex").mkdir()
    (home / ".codex" / "config.toml").write_text("", encoding="utf-8")
    probe = codex_cli.discover(home)
    assert probe.installed is True
    sub = _fake_substrate(home)
    codex_cli.install_basic(probe, sub, dry_run=True)
    codex_cli.install_deep(probe, sub, dry_run=True)
    codex_cli.uninstall(probe, dry_run=True)


def test_gemini_cli_discover(home: Path):
    cfg = home / ".config" / "gemini-cli" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("{}", encoding="utf-8")
    probe = gemini_cli.discover(home)
    assert probe.installed is True
    sub = _fake_substrate(home)
    gemini_cli.install_basic(probe, sub, dry_run=True)
    gemini_cli.install_deep(probe, sub, dry_run=True)
    gemini_cli.uninstall(probe, dry_run=True)


def test_openclaw_discover(home: Path):
    probe = openclaw.discover(home)
    assert probe.host_id == "openclaw"
    sub = _fake_substrate(home)
    openclaw.install_basic(probe, sub, dry_run=True)
    openclaw.install_deep(probe, sub, dry_run=True)
    openclaw.uninstall(probe, dry_run=True)
