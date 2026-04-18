"""I/O primitives. Currently: stdio encoding guard for platforms whose
default (e.g. GBK on Chinese Windows) cannot encode the Unicode that
Myco emits (box-drawing glyphs in embedded prompts, non-ASCII note
content, JSON with any user-supplied text).
"""
from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    """Reconfigure sys.stdout/sys.stderr to UTF-8 if they aren't already.

    Idempotent, safe on all Python 3.10+ runtimes. A no-op on streams
    that don't support reconfigure (e.g. when stdout is a pipe captured
    by a subprocess that already forced its own encoding). Any Myco CLI
    `main()` should call this as its first line.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # Stream already closed, detached, or not reconfigurable.
            pass
