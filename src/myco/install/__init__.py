"""``myco-install`` — one-command MCP install across hosts.

The MCP ecosystem has fragmented on config-file schema despite the
server protocol itself being standardized: ``mcpServers`` is most
common, but VS Code uses ``servers``, Zed uses ``context_servers``,
Goose uses ``extensions``, OpenClaw uses ``mcp.servers`` nested, and
Codex / OpenHands use TOML instead of JSON. A single copy-paste
snippet does not work everywhere.

This subpackage writes the *correct* schema per host, so the user
does not have to know which is which. Both
``python -m myco.install <client>`` and the ``myco-install``
console script dispatch to :func:`main`.

See ``docs/INSTALL.md`` for the full matrix including the clients
this helper does not yet automate.
"""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .clients import CLIENTS, MycoInstallError, dispatch

__all__ = ["main", "CLIENTS", "MycoInstallError", "dispatch"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myco-install",
        description=(
            "Install (or uninstall) the mcp-server-myco MCP server into "
            "a Model Context Protocol host. Writes the correct schema "
            "for that host so you do not have to copy-paste by hand."
        ),
        epilog=(
            "Clients that are not yet automated here — Gemini CLI, "
            "Codex CLI, OpenHands, Continue, Goose, Warp — are "
            "documented with per-host snippets in docs/INSTALL.md."
        ),
    )
    parser.add_argument(
        "client",
        choices=sorted(CLIENTS.keys()),
        help="Host to target.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written; make no changes.",
    )
    parser.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="Target the user-global config (where the client supports it).",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the myco entry instead of adding it.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        output = dispatch(
            args.client,
            dry_run=args.dry_run,
            global_=args.global_,
            uninstall=args.uninstall,
        )
    except MycoInstallError as exc:
        sys.stderr.write(f"myco-install: {exc}\n")
        return 2
    if output:
        print(output)
    return 0
