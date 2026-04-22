"""``myco-install`` — install + bootstrap CLI.

Two subcommands at v0.5.2:

- ``myco-install fresh [TARGET]`` — **primary install path.**
  Clone Myco's source, ``pip install -e`` it, and optionally
  configure one or more MCP hosts to point at the editable
  install. This is what the L0 doctrine (永恒进化 / 永恒迭代)
  actually requires: the agent must be able to edit the kernel,
  not just import it from a read-only ``site-packages``.

- ``myco-install host <client>`` — configure an existing Myco
  install into one of the ten automated MCP hosts (seven JSON,
  one TOML via block-level surgery, one YAML with ``extensions``
  schema, plus OpenClaw via its own CLI mutator). This was the
  only subcommand in v0.4/v0.5; at v0.5.2 it's renamed to an
  explicit subcommand so ``fresh`` can coexist.

Backward compatibility: legacy ``myco-install <client>`` (where
the first positional is a known client name) auto-routes to
``host <client>`` without breaking existing scripts / docs.

See ``docs/INSTALL.md`` for the full host matrix and
``docs/primordia/v0_5_2_editable_default_craft_2026-04-17.md``
for the design record.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..core.io import ensure_utf8_stdio
from .clients import CLIENTS, MycoInstallError, detect_installed_hosts, dispatch
from .cowork_plugin import (
    UPLOAD_INSTRUCTIONS,
    claude_appdata_root,
    cleanup_legacy_rpm_install,
    discover_rpm_dirs,
    prepare_plugin_for_upload,
    repo_template_root,
)
from .fresh import DEFAULT_REPO, run_fresh
from .plugin_bundle import PluginBundleError

__all__ = ["main", "CLIENTS", "MycoInstallError", "dispatch"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myco-install",
        description=(
            "Bootstrap or configure Myco. `fresh` clones the source "
            "and installs it editable (the L0-compliant primary path). "
            "`host` writes an MCP server entry into one of the "
            "supported host config files."
        ),
        epilog=(
            "Hosts not yet automated (OpenHands, Continue, Warp) are "
            "documented in docs/INSTALL.md with manual per-host snippets."
        ),
    )
    sub = parser.add_subparsers(dest="subcommand", metavar="SUBCOMMAND")

    # -- fresh -----------------------------------------------------
    p_fresh = sub.add_parser(
        "fresh",
        help="Clone Myco source + pip install -e (editable).",
        description=(
            "Clone Myco's source tree to TARGET and install it "
            "editable in the current Python environment. Optionally "
            "configure one or more MCP hosts in the same step. This "
            "is the primary install path per L0 doctrine: the kernel "
            "must be editable by the agent."
        ),
    )
    p_fresh.add_argument(
        "target",
        nargs="?",
        default=None,
        help=(
            "Directory to clone into. Defaults to ~/myco. Must be "
            "empty unless --force is passed."
        ),
    )
    p_fresh.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"Upstream clone source. Default: {DEFAULT_REPO}",
    )
    p_fresh.add_argument(
        "--branch",
        default=None,
        help="Git branch or tag to check out (default: repo default).",
    )
    p_fresh.add_argument(
        "--depth",
        type=int,
        default=None,
        help=(
            "Shallow-clone depth. Omit for full history (recommended: "
            "the kernel IS the substrate; history is audit-evidence)."
        ),
    )
    p_fresh.add_argument(
        "--extras",
        default="mcp",
        help=(
            "Pip extras to install alongside (comma-separated inside "
            "one bracketed group, e.g. 'mcp,adapters'). "
            "Default: mcp."
        ),
    )
    p_fresh.add_argument(
        "--configure",
        nargs="*",
        default=(),
        metavar="CLIENT",
        help=(
            "Also run `myco-install host <client>` for each "
            "named client after the editable install succeeds. "
            f"Accepts: {', '.join(sorted(CLIENTS))}."
        ),
    )
    p_fresh.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="When used with --configure, target the user-global host config.",
    )
    p_fresh.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite an existing non-empty target directory. "
            "Destroys whatever is in there; use with care."
        ),
    )
    p_fresh.add_argument(
        "--dry-run",
        action="store_true",
        help="Print every step without executing anything.",
    )
    p_fresh.add_argument(
        "--yes",
        action="store_true",
        help="Non-interactive (reserved for future prompts).",
    )

    # -- host ------------------------------------------------------
    p_host = sub.add_parser(
        "host",
        help="Write (or remove) an MCP server entry in a host's config.",
        description=(
            "Add the mcp-server-myco entry to the configuration file "
            "of a supported MCP host, writing the correct schema for "
            "that host. Idempotent; preserves any sibling servers."
        ),
    )
    p_host.add_argument(
        "client",
        nargs="?",  # v0.5.15: optional when --all-hosts is given
        choices=sorted(CLIENTS.keys()),
        help="Host to target. Omit when using --all-hosts.",
    )
    p_host.add_argument(
        "--all-hosts",
        dest="all_hosts",
        action="store_true",
        help=(
            "v0.5.15: auto-detect every MCP host installed on this "
            "machine (probing each host's user-level config dir) and "
            "run the install for each one. Idempotent; safe to rerun. "
            "Hosts with no detection signal are skipped with a note."
        ),
    )
    p_host.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written; make no changes.",
    )
    p_host.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="Target the user-global config (where the client supports it).",
    )
    p_host.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the myco entry instead of adding it.",
    )

    # -- cowork-plugin ---------------------------------------------
    p_cw = sub.add_parser(
        "cowork-plugin",
        help=(
            "Build a .plugin bundle for drag-drop upload into Claude "
            "Desktop. v0.5.20: replaces v0.5.19's rpm/ writer (which "
            "didn't persist — Cowork regenerates rpm/ from its cloud "
            "marketplace on every session start)."
        ),
        description=(
            "Cowork (Claude Desktop's local-agent-mode) persists "
            "third-party plugins only via its Anthropic cloud "
            "marketplace. The only way to upload a plugin there is "
            "Claude Desktop's drag-drop UI. This subcommand produces "
            "the .plugin bundle you drag in. Heavy lifting lives in "
            "myco.install.plugin_bundle; the bundle copy of this "
            "command matches what the GitHub Release workflow attaches "
            "to every tag. After drag-drop, restart any open Cowork "
            "session — the plugin syncs down automatically and the "
            "myco-substrate skill activates when you mention Myco or "
            "open a workspace with _canon.yaml."
        ),
    )
    p_cw.add_argument(
        "--output",
        "--out",
        dest="output",
        type=Path,
        default=None,
        help=("Directory to write the .plugin file into (default: <repo-root>/dist)."),
    )
    p_cw.add_argument(
        "--cleanup-legacy",
        action="store_true",
        help=(
            "Also remove any rpm/plugin_myco/ directories + manifest "
            "rows written by the v0.5.19 installer (harmless on "
            "machines that never ran v0.5.19; Cowork cloud-sync would "
            "wipe them anyway, but this makes the state clean "
            "immediately)."
        ),
    )
    p_cw.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing anything.",
    )
    p_cw.add_argument(
        "--cowork-root",
        type=Path,
        default=None,
        help=(
            "Override the Claude Desktop application-data root "
            "(default: OS-specific — auto-detected). Only used when "
            "--cleanup-legacy is passed."
        ),
    )

    return parser


def _read_package_version() -> str:
    """Cheap ``__version__`` extractor that avoids circular imports."""
    # Reach for the installed package via a tiny inline import to
    # avoid circularity during module init (_run_cowork_plugin is
    # only called at runtime, not at import time, so this is safe).
    from .. import __version__ as _v

    return _v


def _run_cowork_plugin(
    *,
    dry_run: bool,
    cleanup_legacy: bool,
    output: Path | None = None,
    cowork_root: Path | None = None,
) -> int:
    """Build the Cowork .plugin bundle + show upload instructions.

    This is the v0.5.20 replacement for v0.5.19's ``rpm/`` writer.
    The library does the work (:func:`myco.install.cowork_plugin.prepare_plugin_for_upload`);
    this function glues it to the CLI flags and optionally runs the
    ``--cleanup-legacy`` migration path.

    Returns 0 on success, 1 when the template is missing or malformed.
    """
    version = _read_package_version()
    repo_root = repo_template_root().parent
    if dry_run:
        bundle = repo_root / "dist" / f"myco-{version}.plugin"
        print(f"[dry-run] would build {bundle}")
        print()
        print(UPLOAD_INSTRUCTIONS)
    else:
        try:
            prepare_plugin_for_upload(repo_root, version=version, dest_dir=output)
        except PluginBundleError as exc:
            sys.stderr.write(f"myco-install cowork-plugin: {exc}\n")
            return 1

    if cleanup_legacy:
        claude_root = cowork_root or claude_appdata_root()
        targets = discover_rpm_dirs(claude_root)
        if targets:
            print()
            print("--- v0.5.19 rpm/ cleanup ---")
            print(f"Scanning Claude Desktop root: {claude_root}")
            changed = cleanup_legacy_rpm_install(targets, dry_run=dry_run)
            verb = "would remove" if dry_run else "removed"
            if changed == 0:
                print(
                    "No v0.5.19-era rpm/plugin_myco/ entries found — nothing to clean."
                )
            else:
                print(f"{verb} v0.5.19 entries from {changed} workspace(s).")
    return 0


def _run_all_hosts(
    *,
    dry_run: bool,
    global_: bool,
    uninstall: bool,
) -> int:
    """Iterate over every :data:`CLIENTS` entry whose
    :func:`detect_installed_hosts` probe returned a truthy signal, and
    run the install (or uninstall) for each one. Used by
    ``myco-install host --all-hosts``.

    Skipped hosts are reported but do not cause failure — false
    negatives are preferred to false positives, and any missed host
    can still be installed by explicit name.

    Returns 0 when every attempted install succeeded; 1 when one or
    more attempts raised :class:`MycoInstallError`. Exit code 1 is a
    soft failure (partial success); exit 2 is reserved for usage
    errors.

    v0.5.15 addition. ``--all-hosts`` forces ``global_=True`` when
    not explicitly set, because the intent is "wire every host on this
    machine to find Myco regardless of cwd" — project-level configs
    in the current cwd are the wrong level for that intent. If the
    operator really wants project-local writes they can still loop
    over hosts by name.
    """
    if not global_:
        global_ = True  # --all-hosts implies --global
    signals = detect_installed_hosts()
    installed: list[tuple[str, str]] = []  # (client, output)
    skipped: list[tuple[str, str]] = []  # (client, reason)
    failed: list[tuple[str, str]] = []  # (client, reason)

    # Dedup the cowork alias: claude-desktop covers it. If both detected,
    # we'd write the same config file twice (idempotent but noisy).
    seen_desktop = False

    for client, signal in signals.items():
        if not signal:
            skipped.append((client, "not detected on this machine"))
            continue
        if client == "cowork" and seen_desktop:
            skipped.append((client, "covered by claude-desktop (same config file)"))
            continue
        try:
            output = dispatch(
                client,
                dry_run=dry_run,
                global_=global_,
                uninstall=uninstall,
            )
        except MycoInstallError as exc:
            failed.append((client, str(exc)))
            continue
        installed.append((client, output or ""))
        if client == "claude-desktop":
            seen_desktop = True

    # Report in three groups, each one line per entry, so machine-
    # parseable consumers can grep/awk.
    verb = "uninstalled" if uninstall else "installed"
    for client, output in installed:
        line = f"[{verb}] {client}"
        if output:
            line += f"  →  {output}"
        print(line)
    for client, reason in skipped:
        print(f"[skipped] {client}  ({reason})")
    for client, reason in failed:
        sys.stderr.write(f"[error] {client}: {reason}\n")

    total_detected = len(installed) + len(failed)
    print()
    print(
        f"{len(installed)}/{total_detected} host(s) {verb}, "
        f"{len(skipped)} skipped, {len(failed)} errored."
    )

    # v0.5.20: when Claude Desktop was touched we ALSO build the Cowork
    # .plugin bundle + print the drag-drop upload instructions, so the
    # user sees exactly what to do next. The plugin install itself is a
    # manual UI step in Claude Desktop — v0.5.19's attempt to automate
    # via rpm/ writes was wrong (cloud sync clobbers them). See
    # src/myco/install/cowork_plugin.py module docstring for the full
    # story. Uninstall flow: we DON'T print upload instructions when
    # uninstall=True — the drag-drop marketplace entry is removed via
    # Claude Desktop's UI, not a CLI pathway.
    desktop_was_touched = any(
        client in ("claude-desktop", "cowork") for client, _ in installed
    )
    if desktop_was_touched and not uninstall:
        print()
        print("--- Cowork plugin (next step: upload via Claude Desktop UI) ---")
        _run_cowork_plugin(dry_run=dry_run, cleanup_legacy=False)

    return 0 if not failed else 1


def _legacy_sniff(argv: Sequence[str]) -> list[str]:
    """Accept the v0.4/v0.5 positional form ``myco-install <client>``
    by inserting ``host`` in front. No-op for any other shape.
    """
    args = list(argv)
    if not args:
        return args
    first = args[0]
    if first in CLIENTS:
        return ["host", *args]
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """``myco-install`` entry point. Returns a POSIX exit code.

    Sniffs a legacy positional ``<client>`` form and rewrites to the
    canonical ``host <client>`` form so pre-v0.5.0 scripts keep
    working, then dispatches through ``argparse``.
    """
    ensure_utf8_stdio()
    raw = list(argv) if argv is not None else sys.argv[1:]
    raw = _legacy_sniff(raw)

    parser = _build_parser()
    args = parser.parse_args(raw)

    if args.subcommand is None:
        parser.print_help(sys.stderr)
        return 2

    try:
        if args.subcommand == "fresh":
            return run_fresh(
                target=Path(args.target) if args.target else None,
                repo=args.repo,
                branch=args.branch,
                depth=args.depth,
                configure=tuple(args.configure),
                global_=args.global_,
                force=args.force,
                dry_run=args.dry_run,
                yes=args.yes,
                extras=args.extras,
            )
        if args.subcommand == "host":
            # v0.5.15: --all-hosts iterates every detected host.
            if args.all_hosts:
                return _run_all_hosts(
                    dry_run=args.dry_run,
                    global_=args.global_,
                    uninstall=args.uninstall,
                )
            if not args.client:
                sys.stderr.write(
                    "myco-install: host subcommand requires either a "
                    "client name or --all-hosts\n"
                )
                return 2
            output = dispatch(
                args.client,
                dry_run=args.dry_run,
                global_=args.global_,
                uninstall=args.uninstall,
            )
            if output:
                print(output)
            # v0.5.20: `myco-install host cowork` also builds the
            # .plugin bundle + prints drag-drop instructions, since
            # Cowork only onboards correctly when both the MCP entry
            # (written by `dispatch` above) AND the `myco-substrate`
            # skill (shipped via the uploaded plugin) are in place.
            # `claude-desktop` does NOT trigger this because non-Cowork
            # Claude Desktop doesn't use the local-agent plugin
            # registry and the MCP entry alone is sufficient.
            # Uninstall path is silent: the plugin is removed via the
            # Claude Desktop UI, not a CLI pathway.
            if args.client == "cowork" and not args.uninstall:
                print()
                print("--- Cowork plugin (next step: upload via Claude Desktop UI) ---")
                _run_cowork_plugin(
                    dry_run=args.dry_run,
                    cleanup_legacy=False,
                )
            return 0
        if args.subcommand == "cowork-plugin":
            return _run_cowork_plugin(
                dry_run=args.dry_run,
                cleanup_legacy=args.cleanup_legacy,
                output=args.output,
                cowork_root=args.cowork_root,
            )
    except MycoInstallError as exc:
        sys.stderr.write(f"myco-install: {exc}\n")
        return 2

    parser.print_help(sys.stderr)
    return 2
