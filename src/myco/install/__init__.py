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
from pathlib import Path
from typing import Sequence

from .clients import CLIENTS, MycoInstallError, dispatch
from .fresh import DEFAULT_REPO, run_fresh

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
        "target", nargs="?", default=None,
        help=(
            "Directory to clone into. Defaults to ~/myco. Must be "
            "empty unless --force is passed."
        ),
    )
    p_fresh.add_argument(
        "--repo", default=DEFAULT_REPO,
        help=f"Upstream clone source. Default: {DEFAULT_REPO}",
    )
    p_fresh.add_argument(
        "--branch", default=None,
        help="Git branch or tag to check out (default: repo default).",
    )
    p_fresh.add_argument(
        "--depth", type=int, default=None,
        help=(
            "Shallow-clone depth. Omit for full history (recommended: "
            "the kernel IS the substrate; history is audit-evidence)."
        ),
    )
    p_fresh.add_argument(
        "--extras", default="mcp",
        help=(
            "Pip extras to install alongside (comma-separated inside "
            "one bracketed group, e.g. 'mcp,adapters'). "
            "Default: mcp."
        ),
    )
    p_fresh.add_argument(
        "--configure", nargs="*", default=(), metavar="CLIENT",
        help=(
            "Also run `myco-install host <client>` for each "
            "named client after the editable install succeeds. "
            f"Accepts: {', '.join(sorted(CLIENTS))}."
        ),
    )
    p_fresh.add_argument(
        "--global", dest="global_", action="store_true",
        help="When used with --configure, target the user-global host config.",
    )
    p_fresh.add_argument(
        "--force", action="store_true",
        help=(
            "Overwrite an existing non-empty target directory. "
            "Destroys whatever is in there; use with care."
        ),
    )
    p_fresh.add_argument(
        "--dry-run", action="store_true",
        help="Print every step without executing anything.",
    )
    p_fresh.add_argument(
        "--yes", action="store_true",
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
        choices=sorted(CLIENTS.keys()),
        help="Host to target.",
    )
    p_host.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be written; make no changes.",
    )
    p_host.add_argument(
        "--global", dest="global_", action="store_true",
        help="Target the user-global config (where the client supports it).",
    )
    p_host.add_argument(
        "--uninstall", action="store_true",
        help="Remove the myco entry instead of adding it.",
    )

    return parser


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
            output = dispatch(
                args.client,
                dry_run=args.dry_run,
                global_=args.global_,
                uninstall=args.uninstall,
            )
            if output:
                print(output)
            return 0
    except MycoInstallError as exc:
        sys.stderr.write(f"myco-install: {exc}\n")
        return 2

    parser.print_help(sys.stderr)
    return 2
