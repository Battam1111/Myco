"""Cowork-plugin install support — v0.5.20 rewrite.

Governing doctrine:
``docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md`` — per-host
axis of the extensibility model.

**v0.5.19 was wrong.** That release shipped an installer that wrote
plugin metadata directly into Cowork's ``rpm/manifest.json``, under the
belief that was the source of truth. It is not. On every session
start, Claude Desktop's ``[RemotePluginManager]`` syncs the plugin
list from an Anthropic cloud marketplace and **regenerates** ``rpm/``
from that response. Any local edits are clobbered. v0.5.20 retracts
the installer and replaces it with the real mechanism.

**What actually persists a third-party plugin in Cowork.** The
Anthropic cloud exposes a per-account marketplace (one per user,
named "My Uploads"). A plugin lands there when Claude Desktop's
drag-drop UI uploads a ``.plugin`` ZIP via
``POST https://api.anthropic.com/api/organizations/{orgId}/``
``marketplaces/{marketplaceId}/plugins/account-upload``. Once uploaded,
every Cowork session syncs it down automatically — the skill is then
visible to the agent on next boot. There is no other persistent path
short of Anthropic publishing Myco in a first-party marketplace.

**What this module does now.** It helps the user get the right
``.plugin`` bundle onto disk and gives them the exact drag-drop
instructions. Heavy lifting (building the ZIP) lives in
``myco.install.plugin_bundle``. This module glues:

- Template location (``.cowork-plugin/`` in the repo checkout).
- Bundle builder (:func:`myco.install.plugin_bundle.build_plugin_bundle`).
- Diagnostic helpers (:func:`claude_appdata_root`, :func:`discover_rpm_dirs`)
  that let users sanity-check Cowork's install state after upload.
- The ``rpm/plugin_myco/`` cleanup path for machines that ran the
  v0.5.19 installer — removes stale directories so Cowork's next
  cloud-sync doesn't race against stale files.

There is intentionally no "install the plugin via filesystem" function
any more. The `UPLOAD_INSTRUCTIONS` constant is the only outbound
surface for new installs.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .plugin_bundle import (
    PLUGIN_NAME,
    TEMPLATE_DIRNAME,
    build_plugin_bundle,
)

__all__ = [
    "RpmTarget",
    "claude_appdata_root",
    "discover_rpm_dirs",
    "repo_template_root",
    "prepare_plugin_for_upload",
    "cleanup_legacy_rpm_install",
    "UPLOAD_INSTRUCTIONS",
    "PLUGIN_ID",
    "PLUGIN_NAME",
    "TEMPLATE_DIRNAME",
]

#: Stable plugin id v0.5.19's broken installer used in manifest rows.
#: Kept as a constant so :func:`cleanup_legacy_rpm_install` can target
#: the exact rows it wrote without touching anything else.
PLUGIN_ID = "plugin_myco"

#: Human-facing upload instructions shown by every command that
#: prepares a ``.plugin`` file. Keeping the exact wording in one place
#: means the CLI, tests, and docs all display the same steps.
UPLOAD_INSTRUCTIONS = """\
To install Myco into Cowork permanently:

  1. Open Claude Desktop → Settings → Plugins (or Extensions) → Upload.
  2. Select the .plugin file shown above.
  3. Claude Desktop uploads it to your account's Cowork marketplace
     (private to you). A notification confirms the upload succeeded.
  4. Close any open Cowork session and start a new one. The plugin
     syncs down automatically; the ``myco-substrate`` skill activates
     when you mention Myco or open a workspace containing ``_canon.yaml``.

Why drag-drop rather than an automated installer? Cowork plugins
persist only in Anthropic's cloud marketplace. Writing to the local
``rpm/`` directory is futile — the cloud sync overwrites it on every
session start. v0.5.19 learned this the hard way; see the v0.5.20
changelog for the full story.
"""


# ---------------------------------------------------------------------------
# Diagnostic helpers — read-only, harmless to invoke at any time.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RpmTarget:
    """A single Cowork workspace registry Claude Desktop populates.

    Emitted by :func:`discover_rpm_dirs` for diagnostic use — e.g.
    "show me every Cowork workspace on this machine and what plugins
    it thinks are installed." The v0.5.19 installer used to write
    here; v0.5.20 only reads.
    """

    rpm_dir: Path
    manifest_path: Path
    plugin_dir: Path
    owner_uuid: str
    workspace_uuid: str


def claude_appdata_root(env: os._Environ[str] | dict[str, str] | None = None) -> Path:
    """Return the OS-specific Claude Desktop application-data directory.

    * Windows: ``%APPDATA%\\Claude``
    * macOS: ``~/Library/Application Support/Claude``
    * Linux / other POSIX: ``$XDG_CONFIG_HOME/Claude`` if set, else
      ``~/.config/Claude``.

    The resolved path is not guaranteed to exist; callers should treat
    a missing directory as "Cowork has never run on this machine".
    """
    env = env if env is not None else os.environ
    if sys.platform == "win32":
        appdata = env.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(appdata) / "Claude"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude"
    xdg = env.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else (Path.home() / ".config")
    return base / "Claude"


def discover_rpm_dirs(claude_root: Path) -> list[RpmTarget]:
    """Enumerate every per-workspace ``rpm/`` directory under ``claude_root``.

    Glob: ``local-agent-mode-sessions/*/*/rpm``. The two wildcard
    components are the owner-uuid and workspace-uuid Cowork creates
    per account / project. Returns an empty list when the sessions
    root does not exist (fine — the user has never opened a Cowork
    workspace here).

    v0.5.20: used only for diagnostics. The v0.5.19-era ``install``
    / ``uninstall`` functions that wrote to these directories are
    gone; see :func:`cleanup_legacy_rpm_install` for the migration
    helper.
    """
    sessions_root = claude_root / "local-agent-mode-sessions"
    if not sessions_root.is_dir():
        return []
    out: list[RpmTarget] = []
    for owner_dir in sorted(sessions_root.iterdir()):
        if not owner_dir.is_dir():
            continue
        for ws_dir in sorted(owner_dir.iterdir()) if owner_dir.is_dir() else []:
            if not ws_dir.is_dir():
                continue
            rpm_dir = ws_dir / "rpm"
            if not rpm_dir.is_dir():
                continue
            out.append(
                RpmTarget(
                    rpm_dir=rpm_dir,
                    manifest_path=rpm_dir / "manifest.json",
                    plugin_dir=rpm_dir / PLUGIN_ID,
                    owner_uuid=owner_dir.name,
                    workspace_uuid=ws_dir.name,
                )
            )
    return out


def repo_template_root() -> Path:
    """Locate the ``.cowork-plugin/`` directory shipped with the Myco repo."""
    here = Path(__file__).resolve()
    for parent in (here.parents[3], here.parents[2], here.parents[4]):
        candidate = parent / TEMPLATE_DIRNAME
        if candidate.is_dir():
            return candidate
    return here.parents[3] / TEMPLATE_DIRNAME


# ---------------------------------------------------------------------------
# New behavior: produce the .plugin bundle + tell the user what to do.
# ---------------------------------------------------------------------------


def prepare_plugin_for_upload(
    repo_root: Path,
    *,
    version: str,
    dest_dir: Path | None = None,
    stdout: TextIO | None = None,
) -> Path:
    """Build the ``.plugin`` bundle and print drag-drop instructions.

    This is the v0.5.20 replacement for the old
    ``install_cowork_plugin`` function. Returns the absolute path of
    the written bundle. The caller's responsibility ends at "bundle
    exists on disk" — the actual install is a user action in Claude
    Desktop's UI (see :data:`UPLOAD_INSTRUCTIONS`).

    Parameters
    ----------
    repo_root:
        Repo root containing ``.cowork-plugin/``.
    version:
        Advertised in the output filename. Must match the template's
        ``plugin.json::version``; :func:`build_plugin_bundle` enforces
        this.
    dest_dir:
        Where to write. Defaults to ``repo_root/dist`` — same as
        :mod:`scripts.build_plugin`.

    Raises :class:`myco.install.plugin_bundle.PluginBundleError` when
    the template is missing or malformed.
    """
    out = stdout if stdout is not None else sys.stdout
    path = build_plugin_bundle(repo_root, version=version, dest_dir=dest_dir)
    print(f"built {path}", file=out)
    print("", file=out)
    print(UPLOAD_INSTRUCTIONS, file=out)
    return path


# ---------------------------------------------------------------------------
# Migration from v0.5.19 — remove the broken-installer cruft.
# ---------------------------------------------------------------------------


def cleanup_legacy_rpm_install(
    targets: list[RpmTarget],
    *,
    dry_run: bool,
    stdout: TextIO | None = None,
) -> int:
    """Remove v0.5.19's ``plugin_myco/`` dirs + manifest rows.

    v0.5.19's installer wrote ``<rpm>/plugin_myco/`` + a corresponding
    ``rpm/manifest.json::plugins[]`` row. Cowork's cloud-sync clobbers
    those on its own schedule, but we do a direct cleanup so the user
    isn't confused by stale directories during the grace period.

    Returns the count of rpm/ directories that changed. Safe to call
    when no legacy install exists — a no-op.
    """
    out = stdout if stdout is not None else sys.stdout
    if not targets:
        return 0
    changed = 0
    for target in targets:
        verb = "would remove" if dry_run else "removing"
        if target.plugin_dir.exists() or _manifest_has_legacy_row(target.manifest_path):
            print(
                f"  {verb} -> {target.owner_uuid[:8]}.../"
                f"{target.workspace_uuid[:8]}.../rpm/{PLUGIN_ID}/",
                file=out,
            )
        if not dry_run and target.plugin_dir.exists():
            shutil.rmtree(target.plugin_dir)
        if target.manifest_path.exists():
            manifest = _load_manifest(target.manifest_path)
            manifest, mutated = _drop_legacy_row(manifest)
            if mutated and not dry_run:
                _save_manifest(target.manifest_path, manifest)
            if mutated:
                changed += 1
    return changed


# ---------------------------------------------------------------------------
# Private helpers (manifest I/O).
# ---------------------------------------------------------------------------


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"lastUpdated": _ms_now(), "plugins": []}
    raw = path.read_text(encoding="utf-8")
    data: dict[str, object] = json.loads(raw) if raw.strip() else {}
    data.setdefault("lastUpdated", _ms_now())
    if not isinstance(data.get("plugins"), list):
        data["plugins"] = []
    return data


def _save_manifest(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _ms_now() -> int:
    return int(time.time() * 1000)


def _manifest_has_legacy_row(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, list):
        return False
    return any(isinstance(row, dict) and row.get("id") == PLUGIN_ID for row in plugins)


def _drop_legacy_row(manifest: dict[str, object]) -> tuple[dict[str, object], bool]:
    plugins = manifest["plugins"]
    assert isinstance(plugins, list)
    keep = [
        row
        for row in plugins
        if not (isinstance(row, dict) and row.get("id") == PLUGIN_ID)
    ]
    if len(keep) == len(plugins):
        return manifest, False
    manifest["plugins"] = keep
    manifest["lastUpdated"] = _ms_now()
    return manifest, True


# ---------------------------------------------------------------------------
# Backward-compat shims. Call into the new code paths; the old names
# emit a DeprecationWarning so downstream scripts that still use them
# get a loud hint to migrate.
# ---------------------------------------------------------------------------


def install_cowork_plugin(*args: object, **kwargs: object) -> int:
    """Deprecated alias. v0.5.19 wrote to ``rpm/``; that was wrong.

    Raises :class:`RuntimeError` with migration instructions. Not a
    silent warning because a silent no-op here would re-create the
    v0.5.19 failure mode where users thought install had succeeded.
    """
    raise RuntimeError(
        "install_cowork_plugin is removed in v0.5.20 — writing to "
        "rpm/ is futile because Cowork regenerates it from the "
        "Anthropic cloud marketplace on every session start. Use "
        "prepare_plugin_for_upload (or `myco-install cowork-plugin`) "
        "to build a .plugin file and drag it into Claude Desktop."
    )


def uninstall_cowork_plugin(
    targets: list[RpmTarget],
    *,
    dry_run: bool,
    stdout: TextIO | None = None,
) -> int:
    """v0.5.20 alias for :func:`cleanup_legacy_rpm_install`.

    The old function name ``uninstall_cowork_plugin`` used to remove
    an install-via-rpm that v0.5.19 mistakenly performed. v0.5.20
    keeps the name as a thin shim for backward compatibility but
    renames the canonical function to reflect what it actually does
    (migration cleanup, not a real uninstall).
    """
    return cleanup_legacy_rpm_install(targets, dry_run=dry_run, stdout=stdout)
