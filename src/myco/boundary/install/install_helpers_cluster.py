"""Cluster module — v0.8.8 max-aggressive merge of plugin_bundle, fresh.

=== plugin_bundle ===
Cowork / Claude Desktop plugin bundle builder.

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

=== fresh ===
``myco-install fresh`` — editable-default bootstrap.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/genesis.md``
§ "Editable-default install" (L0 principle 3 realised: the agent
can mutate the kernel, not just read it).

v0.5.2 (MAJOR 11): the primary install path for anyone running
Myco as the L0 doctrine intends — as a substrate whose kernel the
agent can mutate, not as a frozen library imported from
``site-packages``.

End-to-end flow:

1. Check that ``git`` is on PATH. If not, fail with a clear
   "install git, then re-run" message.
2. Resolve the target directory. Refuse to touch a non-empty
   directory unless ``--force`` is passed.
3. ``git clone <repo> <target>`` (defaults:
   ``https://github.com/Battam1111/Myco.git``). ``--branch <REF>``
   and ``--depth <N>`` pass through.
4. ``<python> -m pip install -e <target>[mcp]`` using the same
   Python interpreter the ``myco-install`` CLI is running under.
   This ensures the editable install lands in the same environment
   the user's ``myco`` / ``mcp-server-myco`` console scripts
   resolve to after bootstrap.
5. Verify by invoking ``<python> -m myco --version``.
6. Optionally run one or more ``myco-install host <client>``
   steps in the same session (``--configure claude-code cursor
   windsurf …``) so the MCP hosts immediately point at the
   editable install.
7. Print a short "what just happened / what next" summary.

``--dry-run`` prints every step without executing anything.
``--yes`` skips any interactive confirmations (currently none, but
reserved for future prompts).

This is a side-effect-heavy command; every step validates before
moving on and aborts loud on any error. No half-states.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path

from .clients import CLIENTS, MycoInstallError, dispatch

# =========================================================================
# === plugin_bundle — formerly plugin_bundle.py
# =========================================================================

PLUGIN_NAME = "myco"

BUNDLE_EXTENSION = ".zip"

_COWORK_STRIPPED_KEYS: frozenset[str] = frozenset(
    {"mcpServers", "hooks", "skills", "agents", "commands"}
)

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
    plugin_meta = json.loads(plugin_json_source.read_text(encoding="utf-8"))
    plugin_version = plugin_meta.get("version")
    base_version = re.sub("\\.(post|dev)\\d+$", "", str(version))
    if plugin_version not in (version, base_version):
        raise PluginBundleError(
            f"version mismatch: .claude-plugin/plugin.json says {plugin_version!r} but builder was asked for {version!r} (base {base_version!r}). Run .scripts/bump_version.py to resync."
        )
    cowork_plugin_meta = {
        k: v for k, v in plugin_meta.items() if k not in _COWORK_STRIPPED_KEYS
    }
    cowork_plugin_json_bytes = (
        json.dumps(cowork_plugin_meta, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    dest_dir = dest_dir if dest_dir is not None else repo_root / ".dist"
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / f"{PLUGIN_NAME}-{version}{BUNDLE_EXTENSION}"
    if out_path.exists():
        if not overwrite:
            raise FileExistsError(f"{out_path} exists; pass overwrite=True to replace")
        out_path.unlink()
    mcp_meta = json.loads(mcp_json_source.read_text(encoding="utf-8"))
    for srv in mcp_meta.get("mcpServers", {}).values():
        if isinstance(srv, dict) and srv.get("command") == "mcp-server-myco":
            srv["command"] = "python"
            srv["args"] = ["-m", "myco.boundary.mcp"]
    cowork_mcp_json_bytes = (
        json.dumps(mcp_meta, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            f"{PLUGIN_NAME}/.claude-plugin/plugin.json", cowork_plugin_json_bytes
        )
        zf.writestr(f"{PLUGIN_NAME}/.mcp.json", cowork_mcp_json_bytes)
        zf.write(skill_source, f"{PLUGIN_NAME}/skills/myco-substrate/SKILL.md")
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(out_path)
    return out_path


# =========================================================================
# === fresh — formerly fresh.py
# =========================================================================

DEFAULT_REPO: str = "https://github.com/Battam1111/Myco.git"


def _default_target() -> Path:
    return Path.home() / "myco"


def _run(
    cmd: Sequence[str], *, cwd: Path | None = None, dry_run: bool, stream: bool = True
) -> subprocess.CompletedProcess[str] | None:
    """Run ``cmd`` with clear logging. In ``dry_run`` mode, print
    the would-run command and return None."""
    rendered = " ".join(str(c) for c in cmd)
    if dry_run:
        prefix = "[dry-run] " + (f"(cd {cwd}) " if cwd else "")
        print(f"{prefix}{rendered}")
        return None
    print(f"$ {rendered}" + (f"  # in {cwd}" if cwd else ""))
    if stream:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        if result.returncode != 0:
            raise MycoInstallError(f"command exited {result.returncode}: {rendered}")
        return None  # stream-mode returns None per type signature
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _require_git(dry_run: bool) -> str:
    git = shutil.which("git")
    if git is None:
        raise MycoInstallError(
            "git is not on PATH. myco-install fresh needs git to clone the source; install it (https://git-scm.com) and re-run. Or skip editable install: see the 'Non-evolving install' section in README."
        )
    return git


def _assert_target_available(target: Path, force: bool, dry_run: bool) -> None:
    if not target.exists():
        return
    if not target.is_dir():
        raise MycoInstallError(
            f"target {target} exists but is not a directory; pick another --target path"
        )
    has_children = any(target.iterdir())
    if has_children and (not force):
        raise MycoInstallError(
            f"target {target} is not empty. Pick a fresh path, or pass --force to overwrite (destroys existing content)."
        )
    if has_children and force and (not dry_run):
        for child in target.iterdir():
            if child.is_dir() and (not child.is_symlink()):
                shutil.rmtree(child)
            else:
                child.unlink()


def _configure_hosts(
    target: Path, clients: Iterable[str], dry_run: bool, global_: bool
) -> list[str]:
    """Run ``myco-install host <client>`` for each requested client
    inside the freshly cloned install. ``dispatch`` lives in the
    same process so no subprocess hop; the `home=Path.home()` +
    `cwd=target` context mirrors how the user will run it later.
    """
    results: list[str] = []
    unknown = [c for c in clients if c not in CLIENTS]
    if unknown:
        raise MycoInstallError(
            f"unknown --configure client(s): {unknown}. Known: {sorted(CLIENTS)}"
        )
    for client in clients:
        if dry_run:
            print(f"[dry-run] would configure host: {client}")
            continue
        out = dispatch(
            client,
            dry_run=False,
            global_=global_,
            uninstall=False,
            home=Path.home(),
            cwd=target,
        )
        print(out)
        results.append(out)
    return results


def run_fresh(
    *,
    target: Path | None,
    repo: str,
    branch: str | None,
    depth: int | None,
    configure: Sequence[str],
    global_: bool,
    force: bool,
    dry_run: bool,
    yes: bool,
    extras: str,
    python: str | None = None,
    git: str | None = None,
) -> int:
    """Execute the editable-default bootstrap. Returns POSIX exit code."""
    del yes
    if configure:
        unknown = [c for c in configure if c not in CLIENTS]
        if unknown:
            raise MycoInstallError(
                f"unknown --configure client(s): {unknown}. Known: {sorted(CLIENTS)}"
            )
    git = git or _require_git(dry_run)
    python_exe = python or sys.executable
    target = (target or _default_target()).resolve()
    _assert_target_available(target, force=force, dry_run=dry_run)
    clone_cmd: list[str] = [git, "clone"]
    if branch:
        clone_cmd += ["--branch", branch]
    if depth is not None:
        clone_cmd += ["--depth", str(int(depth))]
    clone_cmd += [repo, str(target)]
    _run(clone_cmd, dry_run=dry_run)
    pip_target = f"{target}[{extras}]" if extras else str(target)
    pip_cmd: list[str] = [python_exe, "-m", "pip", "install", "-e", pip_target]
    _run(pip_cmd, dry_run=dry_run)
    verify_cmd: list[str] = [python_exe, "-m", "myco", "--help"]
    if dry_run:
        print(f"[dry-run] would verify: {' '.join(verify_cmd)}")
    else:
        result = subprocess.run(
            verify_cmd,
            cwd=target,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise MycoInstallError(
                f"post-install verification failed (exit {result.returncode}):\n{result.stderr.strip()}"
            )
    if configure:
        _configure_hosts(target, configure, dry_run, global_)
    _print_summary(
        target=target,
        repo=repo,
        branch=branch,
        configured=list(configure),
        dry_run=dry_run,
        python_exe=python_exe,
    )
    return 0


def _print_summary(
    *,
    target: Path,
    repo: str,
    branch: str | None,
    configured: list[str],
    dry_run: bool,
    python_exe: str,
) -> None:
    lines: list[str] = []
    if dry_run:
        lines.append("")
        lines.append("[dry-run complete] no filesystem changes made.")
    else:
        lines.append("")
        lines.append(f"Myco installed editable at:  {target}")
        lines.append(
            f"Source (clone origin):       {repo}" + (f" @ {branch}" if branch else "")
        )
        lines.append(f"Python interpreter:          {python_exe}")
        if configured:
            lines.append(f"MCP hosts configured:        {', '.join(configured)}")
        lines.append("")
        lines.append("Next:")
        lines.append(f"  cd {target}")
        lines.append("  myco --help                    # sanity-check the CLI")
        lines.append("  myco germinate --project-dir <your-project> \\")
        lines.append(
            "               --substrate-id <slug>        # bootstrap a downstream substrate"
        )
        lines.append("")
        lines.append("Upgrade your kernel later with:")
        lines.append(f"  cd {target} && git pull")
        lines.append("  myco immune                    # verify no drift after upgrade")
    for line in lines:
        print(line)
