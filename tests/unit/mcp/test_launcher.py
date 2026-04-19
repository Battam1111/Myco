"""Smoke tests for the ``myco.mcp`` launcher subpackage.

The launcher's substantive action — booting a stdio MCP transport —
blocks waiting for a client and cannot be unit-tested directly. These
tests instead cover the surface contract:

  * the subpackage imports without the MCP SDK installed
  * ``build_server`` is re-exported (not wrapped) from
    ``myco.surface.mcp`` so library users get the canonical object
  * ``main`` parses ``--help`` and ``--transport`` cleanly
  * an invalid ``--transport`` choice is rejected with exit code 2
"""

from __future__ import annotations

import pytest

import myco.mcp as pkg


def test_subpackage_exposes_build_server() -> None:
    assert callable(pkg.build_server)


def test_subpackage_exposes_main() -> None:
    assert callable(pkg.main)


def test_build_server_is_shared_with_surface_layer() -> None:
    """Re-export must be the same object, not a wrapper."""
    from myco.surface.mcp import build_server as surface_builder

    assert pkg.build_server is surface_builder


def test_help_exits_cleanly() -> None:
    """``python -m myco.mcp --help`` should argparse-exit with code 0."""
    with pytest.raises(SystemExit) as exc_info:
        pkg.main(["--help"])
    assert exc_info.value.code == 0


def test_invalid_transport_is_rejected() -> None:
    """Argparse rejects unknown transport with exit code 2 (its default)."""
    with pytest.raises(SystemExit) as exc_info:
        pkg.main(["--transport", "carrier-pigeon"])
    assert exc_info.value.code == 2


def test_parser_advertises_documented_transports() -> None:
    """Keep the transport surface coherent with :mod:`mcp.server.fastmcp`."""
    parser = pkg._build_parser()
    transport_action = next(a for a in parser._actions if a.dest == "transport")
    assert set(transport_action.choices) == {"stdio", "sse", "streamable-http"}
    assert transport_action.default == "stdio"


def test_main_returns_2_when_mcp_sdk_missing(monkeypatch) -> None:
    """If the MCP SDK is absent, main reports it and exits 2 — never
    crashes with a raw ImportError.
    """

    def _raise(*_, **__):
        raise ImportError("No module named 'mcp.server.fastmcp'")

    monkeypatch.setattr(pkg, "build_server", _raise)
    rc = pkg.main([])
    assert rc == 2
