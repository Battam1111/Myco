"""I/O primitives. Currently: stdio encoding guard for platforms whose
default (e.g. GBK on Chinese Windows) cannot encode the Unicode that
Myco emits (box-drawing glyphs in embedded prompts, non-ASCII note
content, JSON with any user-supplied text).

v0.5.8: extended to cover ``sys.stdin`` too. On Chinese Windows
(cp936/GBK) the MCP stdio transport was receiving UTF-8-encoded
JSON-RPC request bodies but decoding them as GBK before the handler
saw the payload — corrupting every Chinese / emoji / non-latin
argument. Reconfiguring stdin to UTF-8 at every ``main()`` entry
fixes this uniformly.
"""

from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    """Reconfigure sys.stdin/stdout/stderr to UTF-8 if they aren't already.

    Idempotent, safe on all Python 3.10+ runtimes. A no-op on streams
    that don't support reconfigure (e.g. when stdout is a pipe captured
    by a subprocess that already forced its own encoding, or when stdin
    is a non-TTY). Any Myco CLI / MCP ``main()`` should call this as
    its first line.

    The ``errors="replace"`` policy intentionally swallows single-byte
    decode failures rather than raising — a malformed input at the
    transport edge should produce a visible replacement character, not
    a crash. Code that needs strict decoding should do so explicitly
    at its own boundary.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # Stream already closed, detached, or not reconfigurable.
            pass
