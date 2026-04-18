"""Myco MCP launcher subpackage.

Executable entry point for ``python -m myco.mcp``. Boots the
manifest-driven Model Context Protocol server returned by
:func:`myco.surface.mcp.build_server` over whichever transport the
user requests (stdio by default).

Installing the MCP SDK is separate from installing Myco itself; the
MCP adapter is an optional-dependency extra. Users who want to run
the server should install:

    pip install 'myco[mcp]'

Library users embedding the server in their own process can import
``build_server`` directly — no need to go through the ``main`` wrapper::

    from myco.mcp import build_server
    server = build_server()
    server.run(transport="stdio")
"""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

from myco.core.io import ensure_utf8_stdio
from myco.surface.mcp import build_server

__all__ = ["build_server", "main"]


_TRANSPORTS = ("stdio", "sse", "streamable-http")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m myco.mcp",
        description=(
            "Launch the Myco Model Context Protocol server. "
            "Exposes the 12 manifest verbs as MCP tools to any "
            "compatible client."
        ),
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=_TRANSPORTS,
        help="Transport mode (default: stdio).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``python -m myco.mcp``.

    Returns a POSIX-style exit code so callers can chain it. Exits
    non-zero only when the MCP SDK is missing — the server itself
    blocks on its transport and does not return under normal
    operation.
    """
    ensure_utf8_stdio()
    args = _build_parser().parse_args(argv)
    try:
        server = build_server()
    except ImportError as exc:
        sys.stderr.write(
            f"myco.mcp: MCP SDK is not installed ({exc}).\n"
            "Install it alongside Myco:\n"
            "    pip install 'myco[mcp]'\n"
        )
        return 2
    server.run(transport=args.transport)
    return 0
