"""Tests for the v0.5.20 Cowork-plugin install pathway.

Scope: verify that ``myco-install cowork-plugin`` / the underlying
library produce a valid ``.zip`` bundle (renamed from ``.plugin`` in
the v0.7.4 hotfix per Anthropic GitHub issue #40414) and emit the
right user instructions. We also verify the legacy-cleanup helper
correctly scrubs v0.5.19's rpm/ writes.

What we do NOT test here: the actual drag-drop flow in Claude
Desktop. That is an external UI action; the closest we can do is
verify the ZIP we hand the user passes every structural check
Claude Desktop's upload validator applies (filename extension,
top-level dir containing ``.claude-plugin/plugin.json``, max size,
etc.). Those structural checks live in
``tests/integration/test_plugin_bundle.py``.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Fixtures — a synthetic Cowork appdata tree used by legacy-cleanup tests.
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_cowork(tmp_path: Path) -> Path:
    """Simulate Claude Desktop appdata with two workspaces where
    v0.5.19's installer has written legacy ``plugin_myco/`` cruft.
    The v0.5.20 cleanup helper should remove it without touching
    sibling plugins that came from Cowork's cloud sync.
    """
    root = tmp_path / "Claude"
    sessions = root / "local-agent-mode-sessions"
    for owner, ws in (("owner-a", "ws-1"), ("owner-b", "ws-2")):
        rpm = sessions / owner / ws / "rpm"
        rpm.mkdir(parents=True)
        # Two plugins cowork would cloud-sync + a v0.5.19 stale entry.
        (rpm / "manifest.json").write_text(
            json.dumps(
                {
                    "lastUpdated": 1,
                    "plugins": [
                        {
                            "id": "plugin_01MKcJsEAmPJswuCytbMJYZJ",
                            "name": "productivity",
                            "updatedAt": "2026-01-01T00:00:00Z",
                            "marketplaceId": "marketplace_01QRn9XAjzzeAokB5nPWVMxP",
                            "marketplaceName": "knowledge-work-plugins",
                            "installedBy": "user",
                            "installationPreference": "available",
                        },
                        {
                            "id": "plugin_myco",
                            "name": "myco",
                            "updatedAt": "2026-04-22T00:00:00Z",
                            "marketplaceId": "local",
                            "marketplaceName": "local (myco repo install)",
                            "installedBy": "user",
                            "installationPreference": "available",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        # v0.5.19 wrote this whole directory; v0.5.20 removes it.
        (rpm / "plugin_myco" / ".claude-plugin").mkdir(parents=True)
        (rpm / "plugin_myco" / ".claude-plugin" / "plugin.json").write_text(
            '{"name":"myco","version":"0.5.19"}', encoding="utf-8"
        )
    return root


# ---------------------------------------------------------------------------
# prepare_plugin_for_upload — the main v0.5.20 entry point.
# ---------------------------------------------------------------------------


def test_prepare_plugin_for_upload_writes_bundle(tmp_path: Path) -> None:
    """Happy path: prepare_plugin_for_upload builds a valid .zip
    bundle and prints the upload instructions. No filesystem writes
    to the user's Claude Desktop appdata — that's the whole point of
    the v0.5.20 redesign."""
    import io

    import myco
    from myco.boundary.install.cowork_plugin import prepare_plugin_for_upload

    stdout = io.StringIO()
    path = prepare_plugin_for_upload(
        REPO_ROOT,
        version=myco.__version__,
        dest_dir=tmp_path,
        stdout=stdout,
    )
    assert path.exists()
    assert path.suffix == ".zip"
    assert path.name == f"myco-{myco.__version__}.zip"

    out = stdout.getvalue()
    assert "built" in out
    assert "Claude Desktop" in out
    assert "Plugins" in out or "Extensions" in out
    # The instructions must tell the user what gets uploaded and why,
    # not just "drag this file somewhere".
    assert "cloud" in out.lower() or "marketplace" in out.lower()


def test_prepare_plugin_for_upload_raises_on_missing_template(tmp_path: Path) -> None:
    """If called against a directory with no bundle sources
    (.claude-plugin/plugin.json + .mcp.json + .plugin/skills/
    myco-substrate/SKILL.md per the v0.8.5 source-unification),
    we must raise loudly rather than produce a bogus empty ZIP."""
    from myco.boundary.install.cowork_plugin import prepare_plugin_for_upload
    from myco.boundary.install.install_helpers_cluster import PluginBundleError

    with pytest.raises(PluginBundleError):
        prepare_plugin_for_upload(tmp_path, version="0.0.0", dest_dir=tmp_path)


def test_prepare_plugin_for_upload_raises_on_version_mismatch(tmp_path: Path) -> None:
    """The caller-supplied version must match plugin.json::version.
    Otherwise the filename and the on-disk metadata would drift."""
    from myco.boundary.install.cowork_plugin import prepare_plugin_for_upload
    from myco.boundary.install.install_helpers_cluster import PluginBundleError

    with pytest.raises(PluginBundleError):
        prepare_plugin_for_upload(REPO_ROOT, version="99.99.99", dest_dir=tmp_path)


# ---------------------------------------------------------------------------
# Bundle structural invariants — the Claude Desktop upload validator
# enforces these at the ``/plugins/account-upload`` endpoint. Breaking
# any of them returns `plugin_validation` error (HTTP 400) and the UI
# shows "Only .zip files are accepted." (despite the file picker
# advertising both .zip and .plugin — see Anthropic GitHub issue
# #40414, which the v0.7.4 hotfix routes around by switching the
# artifact extension to .zip).
# ---------------------------------------------------------------------------


def test_bundle_zip_extension_is_accepted_by_drag_drop_validator(
    tmp_path: Path,
) -> None:
    """Claude Desktop's upload handler accepts only ``.zip`` despite
    its file picker advertising both ``.zip`` and ``.plugin``
    (Anthropic GitHub issue #40414). v0.7.4 switched our builder to
    emit ``.zip`` so drag-drop succeeds without forcing the user to
    rename the file."""
    import myco
    from myco.boundary.install.install_helpers_cluster import build_plugin_bundle

    path = build_plugin_bundle(REPO_ROOT, version=myco.__version__, dest_dir=tmp_path)
    assert path.name.endswith(".zip"), (
        f"v0.7.4 regression: bundle must use .zip extension to pass "
        f"Cowork's upload validator (issue #40414). Got: {path.name!r}"
    )


def test_bundle_extension_constant_is_zip() -> None:
    """v0.7.4: the ``BUNDLE_EXTENSION`` constant must be ``.zip``.

    Locking this in a unit test so a well-meaning future refactor that
    flips it back to ``.plugin`` (e.g. "this is more semantically
    accurate") gets caught at test time instead of breaking every
    user's drag-drop install. Anthropic GitHub issue #40414 (open as
    of 2026-05-09) is the canonical reference; remove this lock-in
    only when the issue is closed AND verified against a current
    Claude Desktop build.
    """
    from myco.boundary.install.install_helpers_cluster import BUNDLE_EXTENSION

    assert BUNDLE_EXTENSION == ".zip", (
        f"BUNDLE_EXTENSION regressed to {BUNDLE_EXTENSION!r}. "
        f"Cowork rejects every non-.zip extension; see issue #40414."
    )


def test_bundle_has_single_top_level_dir_with_plugin_json(tmp_path: Path) -> None:
    """The v0.3.3.plugin shape that Cowork accepted had a single
    top-level dir containing ``.claude-plugin/plugin.json``. Verify we
    preserve that exact layout."""
    import myco
    from myco.boundary.install.install_helpers_cluster import (
        PLUGIN_NAME,
        build_plugin_bundle,
    )

    path = build_plugin_bundle(REPO_ROOT, version=myco.__version__, dest_dir=tmp_path)
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    # Single top-level dir name matches PLUGIN_NAME.
    tops = {n.split("/", 1)[0] for n in names}
    assert tops == {PLUGIN_NAME}, tops
    # plugin.json exists at the expected depth.
    assert f"{PLUGIN_NAME}/.claude-plugin/plugin.json" in names


def test_bundle_carries_myco_substrate_skill(tmp_path: Path) -> None:
    """The whole point of the bundle is to deliver the onboarding
    skill to Cowork. If we ever drop it by accident, Cowork uploads
    succeed but nothing changes for the user."""
    import myco
    from myco.boundary.install.install_helpers_cluster import (
        PLUGIN_NAME,
        build_plugin_bundle,
    )

    path = build_plugin_bundle(REPO_ROOT, version=myco.__version__, dest_dir=tmp_path)
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    assert f"{PLUGIN_NAME}/skills/myco-substrate/SKILL.md" in names


def test_bundle_has_mcp_json(tmp_path: Path) -> None:
    """The bundle declares its MCP server spec. Cowork mounts this to
    set up the stdio server the agent talks to — without it, the
    plugin ships a skill that references MCP tools that don't exist."""
    import myco
    from myco.boundary.install.install_helpers_cluster import (
        PLUGIN_NAME,
        build_plugin_bundle,
    )

    path = build_plugin_bundle(REPO_ROOT, version=myco.__version__, dest_dir=tmp_path)
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    assert f"{PLUGIN_NAME}/.mcp.json" in names


def test_bundle_plugin_json_version_matches(tmp_path: Path) -> None:
    """The bundle filename and the embedded plugin.json metadata must
    advertise the same version. Anthropic's upload dedup / increment
    keys off this.

    v0.6.0 path-B exception: ``__version__`` may carry a PEP 440
    ``.postN`` suffix as a PyPI namespace-burn workaround; the plugin
    manifest stays at the bare base. Build the bundle with the base
    version so the filename and metadata stay aligned for the
    Anthropic UI.
    """
    import re

    import myco
    from myco.boundary.install.install_helpers_cluster import (
        PLUGIN_NAME,
        build_plugin_bundle,
    )

    base = re.sub(r"\.(post|dev)\d+$", "", myco.__version__)
    path = build_plugin_bundle(REPO_ROOT, version=base, dest_dir=tmp_path)
    with zipfile.ZipFile(path) as zf:
        meta = json.loads(
            zf.read(f"{PLUGIN_NAME}/.claude-plugin/plugin.json").decode("utf-8")
        )
    assert meta["version"] == base


def test_bundle_overwrite_default(tmp_path: Path) -> None:
    """Re-building with overwrite=True (default) must replace an
    existing output. False must raise FileExistsError."""
    import myco
    from myco.boundary.install.install_helpers_cluster import build_plugin_bundle

    p1 = build_plugin_bundle(REPO_ROOT, version=myco.__version__, dest_dir=tmp_path)
    mtime1 = p1.stat().st_mtime_ns
    # Default overwrite=True → silent replace. We don't assert mtime changes
    # (filesystems have coarse resolution); we just verify no exception.
    build_plugin_bundle(REPO_ROOT, version=myco.__version__, dest_dir=tmp_path)
    with pytest.raises(FileExistsError):
        build_plugin_bundle(
            REPO_ROOT,
            version=myco.__version__,
            dest_dir=tmp_path,
            overwrite=False,
        )
    _ = mtime1  # silence "unused" lint


# ---------------------------------------------------------------------------
# cleanup_legacy_rpm_install — migration helper for machines that
# ran the v0.5.19 rpm/ writer.
# ---------------------------------------------------------------------------


def test_cleanup_legacy_removes_plugin_myco_row_and_dir(fake_cowork: Path) -> None:
    from myco.boundary.install.cowork_plugin import (
        cleanup_legacy_rpm_install,
        discover_rpm_dirs,
    )

    targets = discover_rpm_dirs(fake_cowork)
    assert len(targets) == 2
    changed = cleanup_legacy_rpm_install(targets, dry_run=False)
    assert changed == 2
    for target in targets:
        assert not target.plugin_dir.exists()
        manifest = json.loads(target.manifest_path.read_text(encoding="utf-8"))
        ids = [p["id"] for p in manifest["plugins"]]
        assert "plugin_myco" not in ids
        # Sibling rows from cloud sync must be preserved.
        assert "plugin_01MKcJsEAmPJswuCytbMJYZJ" in ids


def test_cleanup_legacy_dry_run_is_noop(fake_cowork: Path) -> None:
    from myco.boundary.install.cowork_plugin import (
        cleanup_legacy_rpm_install,
        discover_rpm_dirs,
    )

    targets = discover_rpm_dirs(fake_cowork)
    before_exists = [t.plugin_dir.exists() for t in targets]
    cleanup_legacy_rpm_install(targets, dry_run=True)
    after_exists = [t.plugin_dir.exists() for t in targets]
    assert before_exists == after_exists


def test_cleanup_legacy_is_idempotent(fake_cowork: Path) -> None:
    """After the first cleanup, a second call reports 0 changes."""
    from myco.boundary.install.cowork_plugin import (
        cleanup_legacy_rpm_install,
        discover_rpm_dirs,
    )

    targets = discover_rpm_dirs(fake_cowork)
    cleanup_legacy_rpm_install(targets, dry_run=False)
    assert cleanup_legacy_rpm_install(targets, dry_run=False) == 0


def test_cleanup_legacy_noop_when_no_sessions(tmp_path: Path) -> None:
    from myco.boundary.install.cowork_plugin import (
        cleanup_legacy_rpm_install,
        discover_rpm_dirs,
    )

    # Empty Cowork root — no sessions, no cleanup.
    assert (
        cleanup_legacy_rpm_install(
            discover_rpm_dirs(tmp_path / "Claude"), dry_run=False
        )
        == 0
    )


# ---------------------------------------------------------------------------
# The v0.5.19 install function is now a loud error — regression guard
# so nobody accidentally re-introduces the broken rpm/ writer.
# ---------------------------------------------------------------------------


def test_v05_19_install_function_raises_loudly() -> None:
    """A silent no-op here would reproduce the v0.5.19 failure mode
    (user thinks install worked, plugin never appears). The function
    must raise with migration instructions."""
    from myco.boundary.install.cowork_plugin import install_cowork_plugin

    with pytest.raises(RuntimeError) as exc_info:
        install_cowork_plugin()  # type: ignore[call-arg]
    message = str(exc_info.value)
    assert "cowork-plugin" in message.lower()
    assert "futile" in message or "cloud" in message or "drag" in message


# ---------------------------------------------------------------------------
# Diagnostic helpers — still useful post-v0.5.20, read-only.
# ---------------------------------------------------------------------------


def test_discover_rpm_dirs_finds_all_workspaces(fake_cowork: Path) -> None:
    from myco.boundary.install.cowork_plugin import discover_rpm_dirs

    targets = discover_rpm_dirs(fake_cowork)
    assert {f"{t.owner_uuid}/{t.workspace_uuid}" for t in targets} == {
        "owner-a/ws-1",
        "owner-b/ws-2",
    }


def test_discover_rpm_dirs_tolerates_missing_sessions_dir(tmp_path: Path) -> None:
    from myco.boundary.install.cowork_plugin import discover_rpm_dirs

    assert discover_rpm_dirs(tmp_path / "Claude") == []


def test_claude_appdata_root_respects_windows_APPDATA(tmp_path: Path) -> None:
    """On Windows the resolver uses ``%APPDATA%``, not ``$HOME``."""
    import sys

    from myco.boundary.install.cowork_plugin import claude_appdata_root

    if sys.platform != "win32":
        pytest.skip("windows-specific resolution")
    env = {"APPDATA": str(tmp_path / "Roaming")}
    assert claude_appdata_root(env) == tmp_path / "Roaming" / "Claude"


def test_claude_appdata_root_respects_xdg_config_home(tmp_path: Path) -> None:
    """On Linux, ``$XDG_CONFIG_HOME`` (if set) beats ``~/.config``."""
    import sys

    from myco.boundary.install.cowork_plugin import claude_appdata_root

    if sys.platform in ("win32", "darwin"):
        pytest.skip("posix-specific resolution")
    env = {"XDG_CONFIG_HOME": str(tmp_path / "xdg")}
    assert claude_appdata_root(env) == tmp_path / "xdg" / "Claude"


# ---------------------------------------------------------------------------
# CLI integration — make sure ``myco-install cowork-plugin`` wires into
# the v0.5.20 library, not the v0.5.19 rpm/ writer.
# ---------------------------------------------------------------------------


def test_cli_cowork_plugin_builds_bundle(tmp_path: Path, capsys) -> None:
    """The CLI subcommand, with ``--output`` pointed at tmp, must
    produce exactly the same artifact as the library call."""
    import myco
    from myco.boundary.install import main as install_main

    rc = install_main(["cowork-plugin", "--output", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    bundle = tmp_path / f"myco-{myco.__version__}.zip"
    assert bundle.exists()
    assert "built" in out
    assert "Claude Desktop" in out


def test_cli_cowork_plugin_dry_run_writes_nothing(tmp_path: Path, capsys) -> None:
    from myco.boundary.install import main as install_main

    rc = install_main(["cowork-plugin", "--dry-run", "--output", str(tmp_path)])
    assert rc == 0
    assert not list(tmp_path.iterdir()), "dry-run wrote to --output"
    out = capsys.readouterr().out
    assert "[dry-run]" in out
    assert "Claude Desktop" in out


def test_cli_cowork_plugin_cleanup_legacy(fake_cowork: Path, tmp_path: Path) -> None:
    """``--cleanup-legacy`` scrubs v0.5.19's rpm/ writes."""
    from myco.boundary.install import main as install_main

    out_dir = tmp_path / "out"
    rc = install_main(
        [
            "cowork-plugin",
            "--cleanup-legacy",
            "--output",
            str(out_dir),
            "--cowork-root",
            str(fake_cowork),
        ]
    )
    assert rc == 0
    # Bundle was built. v0.7.4 hotfix: extension is now .zip
    # (not .plugin) per Anthropic issue #40414.
    assert any(out_dir.glob("*.zip"))
    # Legacy rpm/plugin_myco/ is gone.
    for owner, ws in (("owner-a", "ws-1"), ("owner-b", "ws-2")):
        assert not (
            fake_cowork
            / "local-agent-mode-sessions"
            / owner
            / ws
            / "rpm"
            / "plugin_myco"
        ).exists()
