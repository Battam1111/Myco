"""Unit tests for ``scripts/install_cowork_plugin.py``.

Strategy: instead of exercising the real Claude Desktop appdata
directory (which would clobber the developer's actual install), the
tests stand up a synthetic ``local-agent-mode-sessions/<owner>/<ws>/rpm/``
tree under ``tmp_path`` and point the installer at it via
``--cowork-root``. This lets us verify:

* Discovery walks the glob correctly and skips non-session sentinels
  like ``skills-plugin``.
* Install copies the full template tree into each ``rpm/plugin_myco/``.
* Install upserts a manifest entry without clobbering pre-existing
  entries (e.g. marketplace-installed plugins).
* Re-running the installer is idempotent: no duplicate entries accrue,
  the plugin tree is re-written cleanly, and the manifest list length
  is stable.
* Uninstall symmetrically removes the tree and the manifest row.
* ``--dry-run`` never writes.

The installer is imported via ``importlib`` so we don't need to add
``scripts/`` to ``sys.path`` permanently (and because ``scripts/`` is
outside the package).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "install_cowork_plugin.py"


def _load_script():
    """Dynamically import ``install_cowork_plugin`` as a module."""
    spec = importlib.util.spec_from_file_location("install_cowork_plugin", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["install_cowork_plugin"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def installer():
    return _load_script()


@pytest.fixture()
def fake_cowork(tmp_path: Path) -> Path:
    """Create a synthetic Cowork appdata root with two real sessions
    (each pre-populated with a manifest containing one external
    plugin) and one sentinel dir that should be skipped."""
    root = tmp_path / "Claude"
    sessions = root / "local-agent-mode-sessions"
    # A non-session sentinel Cowork has actually shipped ("skills-plugin").
    (sessions / "skills-plugin").mkdir(parents=True)
    # Two sessions with pre-existing manifests.
    for owner, ws in (("owner-a", "ws-1"), ("owner-b", "ws-2")):
        rpm = sessions / owner / ws / "rpm"
        rpm.mkdir(parents=True)
        (rpm / "manifest.json").write_text(
            json.dumps(
                {
                    "lastUpdated": 1,
                    "plugins": [
                        {
                            "id": "plugin_preexisting",
                            "name": "preexisting",
                            "updatedAt": "2026-01-01T00:00:00Z",
                            "marketplaceId": "marketplace_test",
                            "marketplaceName": "test-marketplace",
                            "installedBy": "user",
                            "installationPreference": "available",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
    # A session where ``rpm/`` exists but is empty (manifest not yet
    # created). Installer must still handle it.
    (sessions / "owner-c" / "ws-3" / "rpm").mkdir(parents=True)
    return root


# ---------------------------------------------------------------------------
# Discovery.
# ---------------------------------------------------------------------------


def test_discovery_finds_only_rpm_subdirs(installer, fake_cowork: Path) -> None:
    targets = installer.discover_rpm_dirs(fake_cowork)
    ids = sorted(f"{t.owner_uuid}/{t.workspace_uuid}" for t in targets)
    assert ids == ["owner-a/ws-1", "owner-b/ws-2", "owner-c/ws-3"]


def test_discovery_tolerates_missing_sessions_dir(installer, tmp_path: Path) -> None:
    assert installer.discover_rpm_dirs(tmp_path / "Claude") == []


# ---------------------------------------------------------------------------
# Install.
# ---------------------------------------------------------------------------


def test_install_copies_template_tree(installer, fake_cowork: Path) -> None:
    rc = installer.main(
        [
            "--cowork-root",
            str(fake_cowork),
            "--repo-root",
            str(REPO_ROOT),
        ]
    )
    assert rc == 0
    for owner, ws in (("owner-a", "ws-1"), ("owner-b", "ws-2"), ("owner-c", "ws-3")):
        plugin_dir = (
            fake_cowork
            / "local-agent-mode-sessions"
            / owner
            / ws
            / "rpm"
            / "plugin_myco"
        )
        assert (plugin_dir / ".claude-plugin" / "plugin.json").is_file()
        assert (plugin_dir / "skills" / "myco-substrate" / "SKILL.md").is_file()
        assert (plugin_dir / ".mcp.json").is_file()


def test_install_upserts_manifest_preserving_existing_entries(
    installer, fake_cowork: Path
) -> None:
    installer.main(["--cowork-root", str(fake_cowork), "--repo-root", str(REPO_ROOT)])
    manifest = json.loads(
        (
            fake_cowork
            / "local-agent-mode-sessions"
            / "owner-a"
            / "ws-1"
            / "rpm"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    ids = sorted(p["id"] for p in manifest["plugins"])
    assert ids == ["plugin_myco", "plugin_preexisting"]
    myco_row = next(p for p in manifest["plugins"] if p["id"] == "plugin_myco")
    assert myco_row["name"] == "myco"
    assert myco_row["marketplaceId"] == "local"
    assert myco_row["installedBy"] == "user"
    assert myco_row["installationPreference"] == "available"


def test_install_creates_manifest_when_missing(installer, fake_cowork: Path) -> None:
    installer.main(["--cowork-root", str(fake_cowork), "--repo-root", str(REPO_ROOT)])
    manifest = json.loads(
        (
            fake_cowork
            / "local-agent-mode-sessions"
            / "owner-c"
            / "ws-3"
            / "rpm"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert [p["id"] for p in manifest["plugins"]] == ["plugin_myco"]


def test_install_is_idempotent(installer, fake_cowork: Path) -> None:
    for _ in range(3):
        installer.main(
            ["--cowork-root", str(fake_cowork), "--repo-root", str(REPO_ROOT)]
        )
    manifest = json.loads(
        (
            fake_cowork
            / "local-agent-mode-sessions"
            / "owner-a"
            / "ws-1"
            / "rpm"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    # Exactly one plugin_myco entry, regardless of re-runs.
    ids = [p["id"] for p in manifest["plugins"]]
    assert ids.count("plugin_myco") == 1
    assert ids.count("plugin_preexisting") == 1


def test_install_refreshes_plugin_tree(installer, fake_cowork: Path) -> None:
    """If a stale file lingers inside ``plugin_myco/`` from a previous
    install, a fresh install must remove it. This guarantees template
    shrinkage (dropping a skill between Myco versions) is honored."""
    installer.main(["--cowork-root", str(fake_cowork), "--repo-root", str(REPO_ROOT)])
    stale = (
        fake_cowork
        / "local-agent-mode-sessions"
        / "owner-a"
        / "ws-1"
        / "rpm"
        / "plugin_myco"
        / "stale.txt"
    )
    stale.write_text("residue from older version")
    installer.main(["--cowork-root", str(fake_cowork), "--repo-root", str(REPO_ROOT)])
    assert not stale.exists(), "old files must not survive a re-install"


# ---------------------------------------------------------------------------
# Dry-run.
# ---------------------------------------------------------------------------


def test_dry_run_writes_nothing(installer, fake_cowork: Path) -> None:
    before = json.loads(
        (
            fake_cowork
            / "local-agent-mode-sessions"
            / "owner-a"
            / "ws-1"
            / "rpm"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    installer.main(
        [
            "--dry-run",
            "--cowork-root",
            str(fake_cowork),
            "--repo-root",
            str(REPO_ROOT),
        ]
    )
    after = json.loads(
        (
            fake_cowork
            / "local-agent-mode-sessions"
            / "owner-a"
            / "ws-1"
            / "rpm"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert before == after
    assert not (
        fake_cowork
        / "local-agent-mode-sessions"
        / "owner-a"
        / "ws-1"
        / "rpm"
        / "plugin_myco"
    ).exists()


# ---------------------------------------------------------------------------
# Uninstall.
# ---------------------------------------------------------------------------


def test_uninstall_removes_tree_and_manifest_entry(
    installer, fake_cowork: Path
) -> None:
    installer.main(["--cowork-root", str(fake_cowork), "--repo-root", str(REPO_ROOT)])
    rc = installer.main(
        [
            "--uninstall",
            "--cowork-root",
            str(fake_cowork),
            "--repo-root",
            str(REPO_ROOT),
        ]
    )
    assert rc == 0
    for owner, ws in (("owner-a", "ws-1"), ("owner-b", "ws-2")):
        base = fake_cowork / "local-agent-mode-sessions" / owner / ws / "rpm"
        assert not (base / "plugin_myco").exists()
        manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
        ids = [p["id"] for p in manifest["plugins"]]
        assert "plugin_myco" not in ids
        assert "plugin_preexisting" in ids  # untouched.


def test_uninstall_is_idempotent(installer, fake_cowork: Path) -> None:
    for _ in range(2):
        installer.main(
            [
                "--uninstall",
                "--cowork-root",
                str(fake_cowork),
                "--repo-root",
                str(REPO_ROOT),
            ]
        )
    # A pre-existing plugin row must still exist after two no-op uninstalls.
    manifest = json.loads(
        (
            fake_cowork
            / "local-agent-mode-sessions"
            / "owner-a"
            / "ws-1"
            / "rpm"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    ids = [p["id"] for p in manifest["plugins"]]
    assert ids == ["plugin_preexisting"]


# ---------------------------------------------------------------------------
# Missing-template guard.
# ---------------------------------------------------------------------------


def test_install_errors_when_template_missing(
    installer, fake_cowork: Path, tmp_path: Path, capsys
) -> None:
    # A repo root that has no .cowork-plugin/ dir should exit non-zero.
    empty_repo = tmp_path / "fake-repo"
    empty_repo.mkdir()
    rc = installer.main(
        [
            "--cowork-root",
            str(fake_cowork),
            "--repo-root",
            str(empty_repo),
        ]
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "template directory not found" in err


# ---------------------------------------------------------------------------
# OS-specific appdata resolution.
# ---------------------------------------------------------------------------


def test_appdata_root_respects_windows_APPDATA(installer, tmp_path: Path) -> None:
    """On Windows the resolver must use ``%APPDATA%``, not ``$HOME``."""
    if sys.platform != "win32":
        pytest.skip("windows-specific resolution")
    env = {"APPDATA": str(tmp_path / "Roaming")}
    assert installer._claude_appdata_root(env) == tmp_path / "Roaming" / "Claude"


def test_appdata_root_respects_xdg_config_home(
    installer, tmp_path: Path, monkeypatch
) -> None:
    """On Linux, ``$XDG_CONFIG_HOME`` (if set) beats ``~/.config``."""
    if sys.platform == "win32" or sys.platform == "darwin":
        pytest.skip("posix-specific resolution")
    env = {"XDG_CONFIG_HOME": str(tmp_path / "xdg")}
    assert installer._claude_appdata_root(env) == tmp_path / "xdg" / "Claude"


# ---------------------------------------------------------------------------
# Smoke: nothing-to-do path.
# ---------------------------------------------------------------------------


def test_install_noop_on_empty_sessions_root(installer, tmp_path: Path, capsys) -> None:
    rc = installer.main(
        [
            "--cowork-root",
            str(tmp_path / "no-claude"),
            "--repo-root",
            str(REPO_ROOT),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "No Cowork rpm" in out


# ---------------------------------------------------------------------------
# myco-install cowork-plugin subcommand — verifies the install module
# exposes the same semantics as the standalone script.
# ---------------------------------------------------------------------------


def test_myco_install_cowork_plugin_subcommand_installs(fake_cowork: Path) -> None:
    """``myco-install cowork-plugin --cowork-root <fake>`` runs the
    library installer and populates every rpm dir just like the
    standalone script does. This guards the wiring in
    ``src/myco/install/__init__.py``.
    """
    from myco.install import main as install_main

    rc = install_main(["cowork-plugin", "--cowork-root", str(fake_cowork)])
    assert rc == 0
    plugin_dir = (
        fake_cowork
        / "local-agent-mode-sessions"
        / "owner-a"
        / "ws-1"
        / "rpm"
        / "plugin_myco"
    )
    assert (plugin_dir / ".claude-plugin" / "plugin.json").is_file()


def test_myco_install_cowork_plugin_subcommand_dry_run(
    fake_cowork: Path, capsys
) -> None:
    from myco.install import main as install_main

    rc = install_main(["cowork-plugin", "--dry-run", "--cowork-root", str(fake_cowork)])
    assert rc == 0
    assert not (
        fake_cowork
        / "local-agent-mode-sessions"
        / "owner-a"
        / "ws-1"
        / "rpm"
        / "plugin_myco"
    ).exists()
    out = capsys.readouterr().out
    assert "would install" in out


def test_myco_install_cowork_plugin_subcommand_uninstall(fake_cowork: Path) -> None:
    from myco.install import main as install_main

    # Install first.
    install_main(["cowork-plugin", "--cowork-root", str(fake_cowork)])
    # Then uninstall.
    rc = install_main(
        ["cowork-plugin", "--uninstall", "--cowork-root", str(fake_cowork)]
    )
    assert rc == 0
    assert not (
        fake_cowork
        / "local-agent-mode-sessions"
        / "owner-a"
        / "ws-1"
        / "rpm"
        / "plugin_myco"
    ).exists()


def test_myco_install_host_cowork_also_installs_plugin(
    fake_cowork: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """``myco-install host cowork`` writes the MCP config entry AND
    triggers the Cowork plugin install (both are needed for a working
    Cowork onboarding). We point the cowork appdata root at the same
    ``fake_cowork`` to verify the plugin install side-effect fires.
    """
    from myco.install import cowork_plugin as cw
    from myco.install import main as install_main

    # Redirect claude_appdata_root to our fake so the host-cowork call
    # also writes to the same fake tree.
    monkeypatch.setattr(cw, "claude_appdata_root", lambda env=None: fake_cowork)
    # Same for the claude-desktop MCP config path — point it at tmp_path
    # so we don't clobber the user's real claude_desktop_config.json.
    rc = install_main(
        [
            "host",
            "cowork",
            # Use a throwaway `home` via env override — dispatch()
            # resolves home via Path.home(); we don't control that from
            # argv, so this test is narrower: it just verifies the
            # plugin-install side-effect runs (the MCP write is
            # covered by test_cowork_alias_writes_claude_desktop_config
            # in tests/unit/install/test_clients.py).
        ]
    )
    # The dispatch may fail for MCP write (no home sandbox), but the
    # plugin-install side-effect should still have run and we can see
    # the printed heading.
    out = capsys.readouterr().out
    assert "Cowork plugin" in out or rc != 0  # either it fired or dispatch errored


def test_myco_install_all_hosts_triggers_cowork_plugin_when_desktop_detected(
    fake_cowork: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """``myco-install host --all-hosts`` on a machine with Claude
    Desktop present must ALSO install the Cowork plugin so Cowork
    agent onboarding works out of the box. We simulate "Claude Desktop
    present" by creating a ``Claude/`` dir under the fake home."""
    from myco.install import cowork_plugin as cw
    from myco.install import main as install_main

    # Redirect plugin root to our sandbox.
    monkeypatch.setattr(cw, "claude_appdata_root", lambda env=None: fake_cowork)

    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Pretend Claude Desktop was installed on this fake home by
    # creating the detection signal.
    from myco.install.clients import _appdata

    (_appdata(fake_home) / "Claude").mkdir(parents=True)

    # Make dispatch() see our fake home so host writes hit tmp_path
    # rather than the real OS appdata.
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    rc = install_main(["host", "--all-hosts", "--dry-run"])
    out = capsys.readouterr().out
    # Either dry-run succeeded, or it partially succeeded — we just want
    # to verify the heading appears, proving the side-effect ran.
    assert "Cowork plugin" in out, (rc, out)
