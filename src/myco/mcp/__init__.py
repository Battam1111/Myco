"""Legacy ``myco.mcp`` import path — back-compat shim (v0.6.13+).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``
§ "Boundary subsystem (v0.6.0+)" + § "Legacy import shims (v0.6.13+)".

Pre-v0.6.0 this module was the canonical MCP launcher. The v0.6.0
Round 5 owner directive landed the Boundary subsystem and physically
relocated every ``myco.{mcp,surface,install,symbionts}`` reference
to ``myco.boundary.<sub>``, deleting the legacy top-level packages.
Three releases (v0.6.10 / v0.6.11 / v0.6.12) shipped without a shim
under the assumption every host config had been migrated.

Reality (surfaced by a v0.6.12 Cowork dashboard report): legacy
``mcp_server_config`` blobs in Claude Desktop / Cowork / Cursor /
JetBrains still spell their command ``python -m myco.mcp``. The
post-v0.6.0 kernel raised ``ModuleNotFoundError: No module named
'myco.mcp'`` on every spawn, killing the MCP child instantly with
"Server disconnected" in the host logs.

This shim restores ``myco.mcp`` as a thin redirect to
``myco.boundary.mcp`` so old configs keep working, and emits a
single-line deprecation warning to stderr so operators see the
canonical replacement and have one upgrade window.

The shim does **not** dilute the boundary subsystem's L0:185-186
vocabulary discipline — internal kernel imports still flow through
``myco.boundary.mcp`` (verified by the ``PA3 / PA4`` lint dimensions
which would fire on any kernel-side legacy reference). The shim
exists exclusively for **external** entry points (host MCP configs +
``python -m`` invocations from user shell scripts). Treat any
internal use as a contract bug.

Scheduled removal: not earlier than v0.7.0 (one MAJOR-class release
window, mirroring the v1.0.0 alias-removal cadence in
``docs/architecture/L2_DOCTRINE/digestion.md`` § "Aliases").
"""

from __future__ import annotations

import sys as _sys
import warnings as _warnings

# Re-export everything from the canonical module.
from myco.boundary.mcp import build_server, main

__all__ = ["build_server", "main"]


def _warn_legacy_path() -> None:
    """Emit a single-line stderr deprecation pointer.

    Stderr (not :mod:`warnings`) because MCP host UIs surface the
    server's stderr verbatim in their "View Logs" panel. A single
    short line is the form most likely to be read; the standard
    Python warning machinery prefixes traceback noise that hides
    the actionable signal.
    """
    _sys.stderr.write(
        "myco.mcp: deprecated import path. Update your MCP host "
        "config to use either ``mcp-server-myco`` (the entry-point "
        "binary, recommended) or ``python -m myco.boundary.mcp`` "
        "(the canonical module). The myco.mcp shim will be removed "
        "no earlier than v0.7.0.\n"
    )
    # Also raise a DeprecationWarning so test harnesses + linters can
    # observe the legacy path through the standard warnings filter.
    _warnings.warn(
        "myco.mcp is a v0.6.13 back-compat shim for myco.boundary.mcp; "
        "update your MCP host config.",
        DeprecationWarning,
        stacklevel=2,
    )


_warn_legacy_path()
