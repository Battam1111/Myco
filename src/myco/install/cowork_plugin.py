"""Cowork-plugin installer — library side of ``scripts/install_cowork_plugin.py``.

Governing doctrine:
``docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md`` — per-host
axis of the extensibility model. Cowork is registered in the host
matrix (``docs/INSTALL.md``) alongside the other ten automated hosts,
but its install format diverges enough to live in its own module
rather than being folded into :mod:`myco.install.clients`.

Cowork (Claude Desktop's local-agent-mode) loads plugins from a
per-workspace registry at
``<CLAUDE_APPDATA>/local-agent-mode-sessions/<owner>/<workspace>/rpm/``.
Marketplace installs populate that directory automatically. We don't
have a Cowork marketplace for Myco yet, so this module is the
equivalent: it copies the repo's ``.cowork-plugin/`` template into
every ``rpm/`` directory it can find and upserts a row in each
``rpm/manifest.json``.

The logic lives here rather than only in ``scripts/install_cowork_plugin.py``
so that:

- ``myco-install host --all-hosts`` can call it as a natural
  continuation of host-config writing (when Claude Desktop is
  detected, we also want the Cowork plugin tree populated).
- ``myco-install cowork-plugin`` provides a first-class subcommand
  for users who only want the plugin installed without re-touching
  MCP host configs.
- It has proper test coverage via ``tests/integration/test_install_cowork_plugin.py``.

The standalone script at ``scripts/install_cowork_plugin.py`` becomes
a thin shim that calls into this module, so users who clone the repo
and want a one-liner (``python scripts/install_cowork_plugin.py``)
still work without needing ``pip install -e .`` first.

Install path per OS:

    Windows:  %APPDATA%\\Claude\\local-agent-mode-sessions\\...
    macOS:    ~/Library/Application Support/Claude/local-agent-mode-sessions/...
    Linux:    ~/.config/Claude/local-agent-mode-sessions/...
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

__all__ = [
    "RpmTarget",
    "claude_appdata_root",
    "discover_rpm_dirs",
    "install_cowork_plugin",
    "uninstall_cowork_plugin",
    "repo_template_root",
    "PLUGIN_ID",
    "PLUGIN_NAME",
    "TEMPLATE_DIRNAME",
]

# ---------------------------------------------------------------------------
# Constants.
# ---------------------------------------------------------------------------

#: Directory in this repo holding the template tree copied to each rpm dir.
TEMPLATE_DIRNAME = ".cowork-plugin"

#: Stable plugin id used in each rpm/manifest.json entry. Keeping it stable
#: makes the upsert idempotent: re-running the installer updates the existing
#: row rather than creating duplicates. Marketplace-installed plugins use
#: ULID ids (``plugin_<ULID>``); we use ``plugin_myco`` to make the local-
#: install origin obvious on inspection.
PLUGIN_ID = "plugin_myco"

#: Human-visible plugin name surfaced in Cowork UI.
PLUGIN_NAME = "myco"

#: Marker shown in rpm/manifest.json so it is obvious these entries did not
#: come from a real Cowork marketplace.
LOCAL_MARKETPLACE_ID = "local"
LOCAL_MARKETPLACE_NAME = "local (myco repo install)"


# ---------------------------------------------------------------------------
# Types.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RpmTarget:
    """A single Cowork workspace registry we can install into.

    Attributes
    ----------
    rpm_dir:
        The ``<owner>/<workspace>/rpm/`` directory.
    manifest_path:
        ``rpm_dir / "manifest.json"``.
    plugin_dir:
        Where the Myco plugin tree will live: ``rpm_dir / PLUGIN_ID``.
    owner_uuid, workspace_uuid:
        Parsed from the path, for human-readable status output.
    """

    rpm_dir: Path
    manifest_path: Path
    plugin_dir: Path
    owner_uuid: str
    workspace_uuid: str


# ---------------------------------------------------------------------------
# Discovery.
# ---------------------------------------------------------------------------


def claude_appdata_root(env: os._Environ[str] | dict[str, str] | None = None) -> Path:
    """Return the OS-specific Claude Desktop application-data directory.

    Resolution order per platform:

    * Windows: ``%APPDATA%\\Claude`` (typically ``C:\\Users\\<user>\\AppData\\Roaming\\Claude``).
    * macOS: ``~/Library/Application Support/Claude``.
    * Linux / other POSIX: ``$XDG_CONFIG_HOME/Claude`` if set, else ``~/.config/Claude``.

    The resolved path is *not* guaranteed to exist — callers should treat a
    missing directory as "Cowork has never run on this machine" rather than
    an error.
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

    We look for the glob ``local-agent-mode-sessions/*/*/rpm``. The two
    wildcard components correspond to the owner-uuid and workspace-uuid that
    Cowork creates per account / project.

    Returns an empty list — not an error — when the sessions dir does not
    exist yet (i.e. the user has never opened a Cowork workspace on this
    machine). Callers should treat zero targets as "nothing to do" and
    exit cleanly.
    """
    sessions_root = claude_root / "local-agent-mode-sessions"
    if not sessions_root.is_dir():
        return []
    out: list[RpmTarget] = []
    for owner_dir in sorted(sessions_root.iterdir()):
        if not owner_dir.is_dir():
            continue
        # Skip non-session bookkeeping dirs like ``skills-plugin``. Session
        # dirs are UUID-shaped, but we accept anything whose child has an
        # ``rpm/`` subdir — more tolerant than a UUID regex if Cowork
        # introduces new sentinel dirs later.
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
    """Locate the ``.cowork-plugin/`` directory shipped with the Myco repo.

    In development (``pip install -e .``) this resolves to the repo root;
    in a wheel install it resolves to wherever setuptools placed the
    package data. We walk up from this file's location until we find a
    directory named :data:`TEMPLATE_DIRNAME` — the repo layout (package
    at ``src/myco/`` with template at repo root) gives us a stable
    ``parents[3]`` anchor, but we defensively walk up in case the
    package is bundled differently.
    """
    here = Path(__file__).resolve()
    for parent in (here.parents[3], here.parents[2], here.parents[4]):
        candidate = parent / TEMPLATE_DIRNAME
        if candidate.is_dir():
            return candidate
    # Last-resort: return the expected v0.5.19 path even if missing, so
    # the caller's "template not found" error message names the file we
    # actually looked for.
    return here.parents[3] / TEMPLATE_DIRNAME


# ---------------------------------------------------------------------------
# Manifest I/O.
# ---------------------------------------------------------------------------


def _load_manifest(path: Path) -> dict[str, object]:
    """Read a Cowork ``rpm/manifest.json`` or return an empty skeleton.

    Tolerant of missing keys — Cowork has produced manifests with and
    without ``lastUpdated`` in the wild — but the returned dict always
    has ``plugins: list`` so callers can mutate in place.
    """
    if not path.is_file():
        return {"lastUpdated": _ms_now(), "plugins": []}
    raw = path.read_text(encoding="utf-8")
    data: dict[str, object] = json.loads(raw) if raw.strip() else {}
    data.setdefault("lastUpdated", _ms_now())
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        data["plugins"] = []
    return data


def _save_manifest(path: Path, data: dict[str, object]) -> None:
    """Atomically write a Cowork ``rpm/manifest.json``.

    Uses the temp-file + replace idiom so a crash mid-write cannot
    leave a half-written manifest that Cowork would refuse to parse.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _ms_now() -> int:
    """Milliseconds since epoch — matches the format Cowork itself writes."""
    return int(time.time() * 1000)


def _iso_now() -> str:
    """Current UTC time as ISO-8601 with a ``Z`` suffix (Cowork's format)."""
    return (
        datetime.now(tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _register_in_manifest(
    manifest: dict[str, object],
) -> tuple[dict[str, object], bool]:
    """Upsert the Myco entry in a manifest. Returns (manifest, changed)."""
    plugins = manifest["plugins"]
    assert isinstance(plugins, list)
    now = _iso_now()
    for row in plugins:
        if isinstance(row, dict) and row.get("id") == PLUGIN_ID:
            # Already registered. Touch updatedAt but leave everything else
            # alone — the user may have flipped ``installationPreference``
            # to ``disabled`` from the Cowork UI and we shouldn't override
            # that choice on every re-run.
            if row.get("updatedAt") == now:
                return manifest, False
            row["updatedAt"] = now
            manifest["lastUpdated"] = _ms_now()
            return manifest, True
    plugins.append(
        {
            "id": PLUGIN_ID,
            "name": PLUGIN_NAME,
            "updatedAt": now,
            "marketplaceId": LOCAL_MARKETPLACE_ID,
            "marketplaceName": LOCAL_MARKETPLACE_NAME,
            "installedBy": "user",
            "installationPreference": "available",
        }
    )
    manifest["lastUpdated"] = _ms_now()
    return manifest, True


def _remove_from_manifest(
    manifest: dict[str, object],
) -> tuple[dict[str, object], bool]:
    """Drop the Myco entry from a manifest. Returns (manifest, changed)."""
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
# Plugin tree copy.
# ---------------------------------------------------------------------------


def _copy_plugin_tree(template: Path, dst: Path, *, dry_run: bool) -> None:
    """Replace ``dst`` with a fresh copy of ``template``.

    We unconditionally wipe the destination so stale skill files from an
    earlier Myco version cannot linger when the template shrinks. ``dst``
    is only ever ``<rpm>/plugin_myco/``, owned entirely by this installer —
    no risk of clobbering the user's own files.
    """
    if dry_run:
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(template, dst)


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------


def install_cowork_plugin(
    template_root: Path,
    targets: list[RpmTarget],
    *,
    dry_run: bool,
    stdout: TextIO | None = None,
) -> int:
    """Copy the template into every rpm dir and upsert the manifest entry.

    Returns the number of manifests that changed, or ``-1`` when the
    template root is missing (fatal: the caller wrote or referenced the
    wrong repo layout). A return of zero means "no targets found" (benign
    — the user simply has no Cowork sessions on this machine).
    """
    out = stdout if stdout is not None else sys.stdout
    if not template_root.is_dir():
        print(
            f"error: template directory not found: {template_root}\n"
            "Run this installer from a Myco repo checkout, or pass "
            "--repo-root if the template lives elsewhere.",
            file=sys.stderr,
        )
        return -1
    if not targets:
        print(
            "No Cowork rpm/ directories found on this machine. Either "
            "Cowork has never run here, or it stores its sessions in a "
            "non-default location. Nothing to do.",
            file=out,
        )
        return 0
    changed = 0
    for target in targets:
        action = "would install" if dry_run else "installing"
        print(
            f"  {action} -> {target.owner_uuid[:8]}.../{target.workspace_uuid[:8]}.../rpm/{PLUGIN_ID}/",
            file=out,
        )
        _copy_plugin_tree(template_root, target.plugin_dir, dry_run=dry_run)
        manifest = _load_manifest(target.manifest_path)
        manifest, mutated = _register_in_manifest(manifest)
        if mutated and not dry_run:
            _save_manifest(target.manifest_path, manifest)
        if mutated:
            changed += 1
    verb = "would change" if dry_run else "changed"
    print(f"Done: {verb} {changed} of {len(targets)} manifest(s).", file=out)
    return changed


def uninstall_cowork_plugin(
    targets: list[RpmTarget],
    *,
    dry_run: bool,
    stdout: TextIO | None = None,
) -> int:
    """Remove the Myco plugin tree + manifest entry from every rpm dir.

    Returns the number of manifests that changed. Idempotent: calling
    uninstall on a machine where Myco was never installed is a no-op
    that prints a friendly "nothing to do" line.
    """
    out = stdout if stdout is not None else sys.stdout
    if not targets:
        print("No Cowork rpm/ directories found. Nothing to uninstall.", file=out)
        return 0
    changed = 0
    for target in targets:
        action = "would remove" if dry_run else "removing"
        print(
            f"  {action} -> {target.owner_uuid[:8]}.../{target.workspace_uuid[:8]}.../rpm/{PLUGIN_ID}/",
            file=out,
        )
        if not dry_run and target.plugin_dir.exists():
            shutil.rmtree(target.plugin_dir)
        if target.manifest_path.exists():
            manifest = _load_manifest(target.manifest_path)
            manifest, mutated = _remove_from_manifest(manifest)
            if mutated and not dry_run:
                _save_manifest(target.manifest_path, manifest)
            if mutated:
                changed += 1
    verb = "would change" if dry_run else "changed"
    print(f"Done: {verb} {changed} of {len(targets)} manifest(s).", file=out)
    return changed
