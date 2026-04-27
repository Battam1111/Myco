"""Myco MCP launcher subpackage.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
§ "MCP surface" — per L0 principle 1, the MCP server is a
first-class Agent interface, not an afterthought. The pulse sidecar
that every tool response carries is defined in
``docs/architecture/L1_CONTRACT/protocol.md`` (R1-R7 reminder shape).

Executable entry point for ``python -m myco.boundary.mcp``. Boots the
manifest-driven Model Context Protocol server returned by
:func:`myco.boundary.surface.mcp.build_server` over whichever transport the
user requests (stdio by default).

Installing the MCP SDK is separate from installing Myco itself; the
MCP adapter is an optional-dependency extra. Users who want to run
the server should install:

    pip install 'myco[mcp]'

Library users embedding the server in their own process can import
``build_server`` directly — no need to go through the ``main`` wrapper::

    from myco.boundary.mcp import build_server
    server = build_server()
    server.run(transport="stdio")
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from myco.boundary.surface.mcp import build_server
from myco.core.io import ensure_utf8_stdio

__all__ = ["build_server", "main"]


_TRANSPORTS = ("stdio", "sse", "streamable-http")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m myco.boundary.mcp",
        description=(
            "Launch the Myco Model Context Protocol server. "
            "Exposes the 20 manifest verbs as MCP tools to any "
            "compatible client (v0.6.0)."
        ),
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=_TRANSPORTS,
        help="Transport mode (default: stdio).",
    )
    # v0.6.0 streamable-http remote deployment knobs.
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address for streamable-http transport (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Listen port for streamable-http transport (default: 0 = kernel-allocated, prevents multi-container collision).",
    )
    parser.add_argument(
        "--mount-path",
        default="/mcp",
        help="HTTP path mount point for streamable-http transport (default: /mcp).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``python -m myco.boundary.mcp``.

    Returns a POSIX-style exit code so callers can chain it. Exits
    non-zero only when the MCP SDK is missing — the server itself
    blocks on its transport and does not return under normal
    operation.

    v0.6.0 adds streamable-http transport with optional OAuth 2.1 +
    PKCE + RFC 8707 (see ``surface/mcp_auth.py``). When transport is
    ``streamable-http``, the server also exposes a ``.well-known/mcp.json``
    Server Card per MCP spec v2.1.
    """
    ensure_utf8_stdio()
    args = _build_parser().parse_args(argv)
    try:
        server = build_server()
    except ImportError as exc:
        sys.stderr.write(
            f"myco.boundary.mcp: MCP SDK is not installed ({exc}).\n"
            "Install it alongside Myco:\n"
            "    pip install 'myco[mcp]'\n"
        )
        return 2

    # v0.6.0: streamable-http transport receives extra config.
    if args.transport == "streamable-http":
        try:
            server.run(
                transport=args.transport,
                host=args.host,
                port=args.port,
                mount_path=args.mount_path,
            )
        except TypeError:
            # FastMCP older signature fallback.
            server.run(transport=args.transport)
    else:
        server.run(transport=args.transport)
    return 0
