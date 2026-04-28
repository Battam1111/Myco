"""Regression coverage for the ``myco.mcp`` legacy back-compat shim.

Background: at v0.6.0 the boundary subsystem landed and the kernel
relocated ``myco.{mcp,surface,install,symbionts}`` to
``myco.boundary.<sub>``. The legacy top-level ``myco.mcp`` was
deleted (Round 5 owner directive). v0.6.10 / 0.6.11 / 0.6.12 shipped
without a shim.

A v0.6.12 dogfood report showed Cowork's Local-MCP-Server config
still spelling its command ``python -m myco.mcp``; every spawn died
with ``ModuleNotFoundError: No module named 'myco.mcp'``. v0.6.13
restored the path as a thin re-export of ``myco.boundary.mcp`` plus
a stderr deprecation pointer.

These tests pin the shim's contract:

1. ``import myco.mcp`` succeeds without raising.
2. The exported public surface (``build_server``, ``main``) is the
   same object as ``myco.boundary.mcp``'s — no duplicate code path.
3. Importing the shim emits a ``DeprecationWarning`` (so test
   harnesses + lint hooks can observe legacy use through the
   standard warnings filter).
4. Importing the shim writes the operator-facing pointer to
   stderr (so MCP host UIs surface it in their "View Logs" panel).
5. ``python -m myco.mcp --help`` exits 0 (legacy spawn path
   continues to work end-to-end).

Doctrine ref: ``docs/architecture/L2_DOCTRINE/boundary.md``
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import warnings


def _reload_shim() -> object:
    """Drop ``myco.mcp`` from sys.modules and re-import.

    Required because ``conftest.py`` and other tests may have already
    imported the shim during collection, exhausting its one-shot
    deprecation warning. Each test that wants to observe the warning
    must reload the module fresh.
    """
    sys.modules.pop("myco.mcp", None)
    return importlib.import_module("myco.mcp")


def test_shim_imports_without_error() -> None:
    """The legacy ``myco.mcp`` module path resolves."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        shim = _reload_shim()
    assert shim is not None
    assert hasattr(shim, "build_server")
    assert hasattr(shim, "main")


def test_shim_reexports_canonical_symbols() -> None:
    """``myco.mcp.X`` is byte-identical to ``myco.boundary.mcp.X``.

    Catches the regression class where a copy-paste re-export drifts
    from canonical (e.g. someone adds a ``main`` to ``boundary.mcp``
    but forgets to update the shim).
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        shim = _reload_shim()
    from myco.boundary import mcp as canonical

    assert shim.build_server is canonical.build_server
    assert shim.main is canonical.main


def test_shim_emits_deprecation_warning() -> None:
    """Standard-warnings observer sees a ``DeprecationWarning``."""
    sys.modules.pop("myco.mcp", None)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.import_module("myco.mcp")

    legacy_warnings = [
        w for w in captured if issubclass(w.category, DeprecationWarning)
    ]
    assert legacy_warnings, "shim must emit a DeprecationWarning on import"
    msg = str(legacy_warnings[0].message)
    assert "myco.mcp" in msg
    assert "boundary" in msg or "v0.7.0" in msg


def test_shim_writes_stderr_pointer(capfd) -> None:
    """The shim writes the operator-readable line to stderr.

    Stderr (not stdout) so MCP host UIs surface it in "View Logs",
    and not the JSON-RPC stdout channel where it would corrupt
    framing. Stdout must stay clean.
    """
    sys.modules.pop("myco.mcp", None)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        importlib.import_module("myco.mcp")
    captured = capfd.readouterr()
    assert captured.out == ""  # stdout must stay clean (JSON-RPC channel)
    assert "myco.mcp" in captured.err
    assert "deprecated" in captured.err
    assert "mcp-server-myco" in captured.err or "myco.boundary.mcp" in captured.err


def test_shim_help_subprocess_exits_zero() -> None:
    """``python -m myco.mcp --help`` exits 0 end-to-end.

    Smoke test that the legacy spawn path that Claude Desktop /
    Cowork / Cursor configs use continues to boot. Subprocess so we
    test the actual ``python -m`` resolution + ``__main__`` module
    discovery, not just the in-process import graph.
    """
    result = subprocess.run(
        [sys.executable, "-m", "myco.mcp", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"`python -m myco.mcp --help` exited {result.returncode}; "
        f"stderr:\n{result.stderr}"
    )
    # Help text comes from boundary.mcp's argparse parser.
    assert "Myco Model Context Protocol server" in result.stdout
    # Deprecation pointer appears on stderr without contaminating stdout.
    assert "myco.mcp: deprecated" in result.stderr
