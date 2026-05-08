"""Cowork / Claude Desktop plugin bundle builder.

Governing doctrine:
``docs/architecture/L2_DOCTRINE/boundary.md`` — per-host
axis of the extensibility model. This module is the v0.5.20 successor
to ``myco.boundary.install.cowork_plugin``'s now-retracted ``rpm/`` writer.

Why this exists
---------------

Cowork (Claude Desktop's local-agent-mode) loads plugins from an
**Anthropic cloud marketplace**, not the local filesystem. On every
session start, ``[RemotePluginManager]`` syncs the cloud's plugin list
down to ``<APPDATA>/Claude/local-agent-mode-sessions/<owner>/<ws>/rpm/``.
Any local edits to that directory are clobbered on the next restart.

The only path that **persists** a third-party plugin into Cowork is:

1. Build a ``.zip`` bundle (ZIP archive with a single top-level
   directory containing ``.claude-plugin/plugin.json``, ``.mcp.json``,
   ``skills/*/SKILL.md``).
2. User drags the ``.zip`` file into Claude Desktop's plugin upload
   UI. The ``uploadPlugin`` handler in ``app.asar`` rejects every
   extension except ``.zip`` with the error
   ``"Only .zip files are accepted."`` (see Anthropic GitHub issue
   #40414 — open as of 2026-05). In Cowork mode with the
   ``720735283`` feature flag on, Claude Desktop calls
   ``uploadPluginViaRemote`` which POSTs the ZIP to
   ``https://api.anthropic.com/api/organizations/{orgId}/marketplaces/
   {marketplaceId}/plugins/account-upload``.
3. Anthropic's cloud stores the plugin in the user's per-account
   marketplace (``marketplace_01UDYDZqTLSQBkNqpTGCfzNM`` pattern,
   named "My Uploads").
4. Every subsequent Cowork session: ``[RemotePluginManager]`` syncs
   down → writes ``rpm/plugin_<ULID>/`` → agent sees the
   ``myco-substrate`` skill and follows R1-R7 on next boot.

The ``.mcpb`` / ``.dxt`` format is **not** usable for this flow —
those are MCPB extensions (bare MCP servers, no skills, no plugin
semantics) and go into Claude Desktop's ``Claude Extensions`` dir,
not the Cowork plugin registry.

History note: v0.5.20-v0.7.3 emitted ``.plugin`` because the file
picker regex accepts both ``.zip`` and ``.plugin``. The v0.7.4 hotfix
discovered that the upload handler does NOT — only ``.zip`` survives
validation. Switching to ``.zip`` makes drag-drop work without forcing
users to rename. See the v0.7.4 craft for the full discovery trail.

What this module does
---------------------

Given a Myco repo root with ``.cowork-plugin/`` populated, produce
``dist/myco-<version>.zip`` — a ZIP with a single top-level dir
(``myco/``) holding:

    myco/.claude-plugin/plugin.json
    myco/.mcp.json
    myco/skills/myco-substrate/SKILL.md
    myco/README.md

The inner dirname is ``PLUGIN_NAME`` (stable across releases; the
Anthropic cloud keys by ``name`` so this determines whether a
subsequent upload overwrites or creates a new plugin).
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

__all__ = [
    "build_plugin_bundle",
    "PLUGIN_NAME",
    "TEMPLATE_DIRNAME",
    "BUNDLE_EXTENSION",
]

#: Inner top-level dirname inside the ZIP. Anthropic cloud keys by this
#: ``name``; keep stable across releases so re-uploads overwrite rather
#: than spawn duplicates.
PLUGIN_NAME = "myco"

#: Source directory under the repo root.
TEMPLATE_DIRNAME = ".cowork-plugin"

#: Extension Claude Desktop recognises for drag-drop plugin uploads.
#: The Claude Desktop file picker advertises both ``.zip`` and ``.plugin``
#: (regex in ``app.asar`` index.js: ``/\.(zip|plugin)$/i``), but the
#: ``uploadPlugin`` handler that processes the dropped file rejects
#: anything other than ``.zip`` with the error
#: ``"Only .zip files are accepted."``. The UI swallows that message
#: and surfaces the generic "Upload failed. You can try again." or
#: "validation failed" — see the open Anthropic-tracked bug:
#:
#:     https://github.com/anthropics/claude-code/issues/40414
#:     [Bug] Claude Desktop plugin upload rejects `.plugin` files despite
#:           file picker allowing them
#:
#: We pick ``.zip`` so drag-drop works today against the production
#: validator. When #40414 lands, ``.plugin`` would also work — but
#: ``.zip`` is universally accepted (file picker + validator + every
#: archive tool that opens a ZIP), so there's no upside to switching
#: back. v0.7.4 hotfix.
BUNDLE_EXTENSION = ".zip"


class PluginBundleError(Exception):
    """Raised when the bundle cannot be built (missing template, etc.).

    User-recoverable — the message names the missing path / field so
    the operator can fix it and retry.
    """


def build_plugin_bundle(
    repo_root: Path,
    *,
    version: str,
    dest_dir: Path | None = None,
    overwrite: bool = True,
) -> Path:
    """Build a ``.zip`` bundle from the repo's ``.cowork-plugin/``.

    Parameters
    ----------
    repo_root:
        Path to the Myco repo root. Must contain ``.cowork-plugin/``
        with ``plugin.json``, ``.mcp.json``, and at least one skill.
    version:
        Semver string used in the output filename. Usually
        ``myco.__version__``. The ``plugin.json`` inside the bundle
        already carries its own version, bumped in lockstep by
        ``scripts/bump_version.py`` — this parameter only names the
        artifact.
    dest_dir:
        Where to write the ``.zip`` file. Defaults to
        ``repo_root/dist`` (created if missing).
    overwrite:
        If ``True`` (default), an existing output file is replaced.
        ``False`` raises ``FileExistsError`` on collision — useful in
        CI when you want an explicit failure rather than silent
        replacement.

    Returns the absolute path of the produced ``.zip`` file.

    Raises ``PluginBundleError`` when the template is missing or
    malformed (no ``plugin.json``, no skill, etc.).
    """
    template = repo_root / TEMPLATE_DIRNAME
    if not template.is_dir():
        raise PluginBundleError(
            f"template directory not found: {template}. Run this from "
            f"a Myco repo root where '{TEMPLATE_DIRNAME}/' exists."
        )

    # Sanity-check the template has the files Claude Desktop requires.
    # plugin.json is the only file the upload validator actually parses;
    # .mcp.json + skills are Cowork-specific but required for Myco's
    # onboarding contract. We fail loud if any are missing so we never
    # ship an empty or broken bundle.
    required = [
        template / ".claude-plugin" / "plugin.json",
        template / ".mcp.json",
        template / "skills" / "myco-substrate" / "SKILL.md",
    ]
    for path in required:
        if not path.is_file():
            raise PluginBundleError(
                f"required file missing from {TEMPLATE_DIRNAME}/: "
                f"{path.relative_to(template)}"
            )

    # Cross-check plugin.json::version matches the version we're
    # advertising — otherwise the filename and the on-disk metadata
    # drift. scripts/bump_version.py keeps them in lockstep, so this
    # is a belt-and-braces check.
    #
    # v0.6.0 path-B exception: ``__version__`` may carry a PEP 440
    # ``.postN`` suffix to dodge a PyPI namespace burn while every
    # user-facing surface (including plugin.json) stays at the bare
    # base version. Accept the match if plugin.json equals the base
    # of ``version`` (i.e. ``version`` minus ``.postN``).
    import re as _re

    plugin_json_path = template / ".claude-plugin" / "plugin.json"
    plugin_meta = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    plugin_version = plugin_meta.get("version")
    base_version = _re.sub(r"\.(post|dev)\d+$", "", str(version))
    if plugin_version not in (version, base_version):
        raise PluginBundleError(
            f"version mismatch: {TEMPLATE_DIRNAME}/.claude-plugin/plugin.json "
            f"says {plugin_version!r} but builder was asked for "
            f"{version!r} (base {base_version!r}). "
            f"Run scripts/bump_version.py to resync."
        )

    dest_dir = dest_dir if dest_dir is not None else (repo_root / "dist")
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / f"{PLUGIN_NAME}-{version}{BUNDLE_EXTENSION}"

    if out_path.exists():
        if not overwrite:
            raise FileExistsError(f"{out_path} exists; pass overwrite=True to replace")
        out_path.unlink()

    # Build the ZIP in memory first so a mid-write crash can never
    # leave a half-written file on disk. Then atomically rename into
    # place.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in sorted(template.rglob("*")):
            if src.is_dir():
                continue
            rel = src.relative_to(template).as_posix()
            # Single top-level dir under the ZIP root — Claude Desktop's
            # plugin extractor expects <name>/.claude-plugin/plugin.json
            # at this depth (confirmed in myco-v0.3.3.plugin, the last
            # ``.plugin``-extension build before v0.7.4 switched to ``.zip``).
            arcname = f"{PLUGIN_NAME}/{rel}"
            zf.write(src, arcname)

    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(out_path)
    return out_path
