"""Legacy ``myco.mcp`` import path — back-compat shim (v0.6.13+).

Re-exports :mod:`myco.boundary.mcp` so pre-v0.6.0 host configs
(`python -m myco.mcp`) keep booting, and emits a single-line
stderr deprecation pointer + a standard ``DeprecationWarning`` so
operators see the canonical replacement.

Doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``
§ "Legacy import shims (v0.6.13+)".

Removal gate: MB8 dim's sunset criterion (≥ 7 senesce cycles
**and** ≥ 7 days with zero hits in ``.myco/state/shim_hits.json``)
or the v1.0.0 stable freeze, whichever comes first. v0.7.0 tried
to delete this shim and broke the substrate's own Claude Desktop
config within 2 hours; the v0.7.1 amendment instituted the
telemetry-gated discipline that v0.7.2 mechanized via MB8.
"""

from __future__ import annotations

import sys as _sys
import warnings as _warnings

from myco.boundary.mcp import build_server, main

__all__ = ["build_server", "main"]


def _warn_legacy_path() -> None:
    """Stderr-pointer (MCP host UIs surface stderr verbatim) +
    ``DeprecationWarning`` (test harness + lint observability)."""
    _sys.stderr.write(
        "myco.mcp: deprecated import path (v0.6.13+). Update host "
        "config to ``mcp-server-myco`` (entry-point binary) or "
        "``python -m myco.boundary.mcp`` (canonical module). "
        "Removal gated on MB8 sunset (zero hits ≥ 7 sessions / 7 days) "
        "or v1.0.0 stable freeze.\n"
    )
    _warnings.warn(
        "myco.mcp is a v0.6.13 back-compat shim for myco.boundary.mcp; "
        "update your MCP host config.",
        DeprecationWarning,
        stacklevel=2,
    )


_warn_legacy_path()
