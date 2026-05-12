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

v0.8.5 source-of-truth consolidation
------------------------------------

Pre-v0.8.5: the bundle was built from ``.cowork-plugin/`` — a
standalone template directory parallel to the Claude Code marketplace
sources (``.plugin/`` + ``.claude-plugin/`` + repo-root ``.mcp.json``).
The two trees carried duplicated metadata (plugin.json, .mcp.json) and
the cowork-plugin tree had no skills beyond ``myco-substrate``.

v0.8.5 deletes ``.cowork-plugin/`` and derives the Cowork bundle from
the same sources as the Claude Code marketplace plugin:

- ``.claude-plugin/plugin.json`` — full plugin metadata (the Cowork
  bundle gets a STRIPPED form with the Claude-Code-only pointer keys
  ``mcpServers`` / ``hooks`` / ``skills`` / ``agents`` / ``commands``
  removed, because the Cowork zip inlines those contents rather than
  dereferences pointers).
- Repo-root ``.mcp.json`` — the MCP server declaration (used by both
  Claude Code marketplace AND Cowork drag-drop).
- ``.plugin/skills/myco-substrate/SKILL.md`` — the Cowork-onboarding
  skill, now co-located with the other Claude Code marketplace skills
  (``hunger/`` and ``session-end/``). The ``myco-substrate`` skill is
  also useful in Claude Code marketplace contexts, so collocating
  improves discoverability for those agents.

The Cowork bundle stays single-skill (``myco-substrate`` only) because
Cowork's runtime only honors skills (no hooks, no slash commands,
no sub-agents per Cowork architecture); shipping the other two
``.plugin/skills/`` would inflate the bundle with skills Cowork would
discard at load time.

What this module does
---------------------

Produces ``.dist/myco-<version>.zip`` — a ZIP with a single top-level
dir (``myco/``) holding:

    myco/.claude-plugin/plugin.json   # derived from root plugin.json
    myco/.mcp.json                    # copy of root .mcp.json
    myco/skills/myco-substrate/SKILL.md  # copy of .plugin/skills/myco-substrate/SKILL.md

The inner dirname is ``PLUGIN_NAME`` (stable across releases; the
Anthropic cloud keys by ``name`` so this determines whether a
subsequent upload overwrites or creates a new plugin).
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

__all__ = [
    "build_plugin_bundle",
    "PLUGIN_NAME",
    "BUNDLE_EXTENSION",
]

#: Inner top-level dirname inside the ZIP. Anthropic cloud keys by this
#: ``name``; keep stable across releases so re-uploads overwrite rather
#: than spawn duplicates.
PLUGIN_NAME = "myco"

#: Extension Claude Desktop recognises for drag-drop plugin uploads.
#: The Claude Desktop file picker advertises both ``.zip`` and ``.plugin``
#: (regex in ``app.asar`` index.js: ``/\.(zip|plugin)$/i``), but the
#: ``uploadPlugin`` handler that processes the dropped file rejects
#: anything other than ``.zip`` with the error
#: ``"Only .zip files are accepted."``. v0.7.4 hotfix locked in ``.zip``.
BUNDLE_EXTENSION = ".zip"

#: Sub-keys of the Claude Code marketplace plugin.json that the Cowork
#: bundle does NOT inline (Cowork bundles inline-include the contents
#: rather than dereference pointers). Strip these before writing the
#: Cowork-flavored plugin.json into the .zip.
_COWORK_STRIPPED_KEYS: frozenset[str] = frozenset(
    {"mcpServers", "hooks", "skills", "agents", "commands"}
)

#: The single skill the Cowork bundle ships (out of the .plugin/skills/
#: set which the Claude Code marketplace bundles all of). The Cowork
#: runtime only honors skills, so this is the Cowork-onboarding payload.
_COWORK_SKILL_RELPATH: tuple[str, ...] = ("skills", "myco-substrate", "SKILL.md")


class PluginBundleError(Exception):
    """Raised when the bundle cannot be built (missing source file, etc.).

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
    """Build a ``.zip`` bundle from the repo's ``.plugin/`` + ``.claude-plugin/``
    + root ``.mcp.json``.

    Parameters
    ----------
    repo_root:
        Path to the Myco repo root. Must contain
        ``.claude-plugin/plugin.json`` (the source-of-truth plugin
        metadata; Cowork-stripped form is written to the bundle),
        ``.mcp.json`` (root MCP server declaration), and
        ``.plugin/skills/myco-substrate/SKILL.md`` (the Cowork-
        onboarding skill body).
    version:
        Semver string used in the output filename. Usually
        ``myco.__version__``. The plugin.json that lives inside the
        repo already carries its own version, bumped in lockstep by
        ``.scripts/bump_version.py`` — this parameter only names the
        artifact and is cross-checked against plugin.json::version.
    dest_dir:
        Where to write the ``.zip`` file. Defaults to ``repo_root/.dist``
        (created if missing; the hidden directory was introduced in
        the v0.8.4 root-cleanup pass).
    overwrite:
        If ``True`` (default), an existing output file is replaced.
        ``False`` raises ``FileExistsError`` on collision.

    Returns the absolute path of the produced ``.zip`` file.

    Raises ``PluginBundleError`` when any source file is missing or
    malformed.
    """
    plugin_json_source = repo_root / ".claude-plugin" / "plugin.json"
    mcp_json_source = repo_root / ".mcp.json"
    skill_source = repo_root / Path(".plugin").joinpath(*_COWORK_SKILL_RELPATH)

    for path in (plugin_json_source, mcp_json_source, skill_source):
        if not path.is_file():
            raise PluginBundleError(
                f"required Cowork bundle source missing: {path.relative_to(repo_root)}"
            )

    # Cross-check plugin.json::version matches the version we're
    # advertising. The bump-version script keeps them in lockstep; this
    # is belt-and-braces.
    plugin_meta = json.loads(plugin_json_source.read_text(encoding="utf-8"))
    plugin_version = plugin_meta.get("version")
    base_version = re.sub(r"\.(post|dev)\d+$", "", str(version))
    if plugin_version not in (version, base_version):
        raise PluginBundleError(
            f"version mismatch: .claude-plugin/plugin.json says "
            f"{plugin_version!r} but builder was asked for "
            f"{version!r} (base {base_version!r}). "
            f"Run .scripts/bump_version.py to resync."
        )

    # Strip Claude-Code-only pointer keys for the Cowork inline form.
    cowork_plugin_meta = {
        k: v for k, v in plugin_meta.items() if k not in _COWORK_STRIPPED_KEYS
    }
    cowork_plugin_json_bytes = (
        json.dumps(cowork_plugin_meta, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    # v0.8.4 root-cleanup (2026-05-12): default dest dir hidden under
    # .dist/ to declutter the repo root.
    dest_dir = dest_dir if dest_dir is not None else (repo_root / ".dist")
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / f"{PLUGIN_NAME}-{version}{BUNDLE_EXTENSION}"

    if out_path.exists():
        if not overwrite:
            raise FileExistsError(f"{out_path} exists; pass overwrite=True to replace")
        out_path.unlink()

    # MCP server declaration: the root .mcp.json uses the
    # `mcp-server-myco` console-script form (works fine in CLI / Claude
    # Code marketplace contexts where the venv's Scripts/ is on PATH).
    # The Cowork bundle needs the `python -m myco.boundary.mcp` launcher
    # form because Claude Desktop spawns MCP servers from a GUI process
    # without the venv-Scripts dir necessarily on PATH. Swap at bundle
    # build time so both contexts work from a single SoT .mcp.json.
    mcp_meta = json.loads(mcp_json_source.read_text(encoding="utf-8"))
    for srv in mcp_meta.get("mcpServers", {}).values():
        if isinstance(srv, dict) and srv.get("command") == "mcp-server-myco":
            srv["command"] = "python"
            srv["args"] = ["-m", "myco.boundary.mcp"]
    cowork_mcp_json_bytes = (
        json.dumps(mcp_meta, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    # Build the ZIP in memory first so a mid-write crash can never
    # leave a half-written file on disk. Atomically rename into place.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Inline-stripped plugin.json — written under .claude-plugin/
        # inside the bundle dir (Claude Desktop's plugin extractor
        # expects <name>/.claude-plugin/plugin.json at this depth).
        zf.writestr(
            f"{PLUGIN_NAME}/.claude-plugin/plugin.json",
            cowork_plugin_json_bytes,
        )
        # MCP server declaration (Cowork-rewritten copy of root .mcp.json).
        zf.writestr(f"{PLUGIN_NAME}/.mcp.json", cowork_mcp_json_bytes)
        # Cowork-onboarding skill.
        zf.write(
            skill_source,
            f"{PLUGIN_NAME}/skills/myco-substrate/SKILL.md",
        )

    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(out_path)
    return out_path
