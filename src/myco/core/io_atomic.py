"""Atomic file I/O helpers — the single chokepoint every kernel write
routes through.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
(Homeostasis § "Safe-fix discipline" — rule 3 "Non-destructive"
depends on atomic replace semantics to hold). Companion helper to
:mod:`myco.core.write_surface`, which adds the R6 surface check on
top of every write.

v0.5.8 introduced this module to absorb a cluster of concurrency,
cross-platform, and sanitization findings surfaced by Iteration 1-4
audits:

* **Atomic semantics** — write-to-temp then ``os.replace`` so a
  concurrent reader never sees a torn file. On NTFS and POSIX alike
  the replace is the atomic commit point. Resolves race-condition
  findings in ``molt``, ``persist_graph``, ``boot_brief`` marker
  writes, and the ``promote_to_integrated`` two-step.

* **Line-ending normalisation** — ``newline="\n"`` is the default so
  files written on Windows don't silently acquire CRLF. This keeps
  byte-level fingerprints stable across platforms. Callers that
  genuinely want platform-native endings pass ``newline=None``.

* **UTF-8 always** — every text write is ``encoding="utf-8"``; the
  helper rejects any byte-level caller that tries to route a bytes
  payload through the text API, eliminating the "forgot encoding="
  foot-gun.

* **Bounded reads** — ``bounded_read_text`` caps a read at
  ``max_bytes`` (default 10 MB), raising ``MycoError`` on oversized
  inputs rather than OOM-ing on a pathological canon or raw note.

The helpers are pure and free of canon / substrate knowledge; they
compose into ``core.write_surface.guarded_write`` which adds the
write-surface policy check on top.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Final

from .errors import MycoError

__all__ = [
    "DEFAULT_MAX_READ_BYTES",
    "atomic_utf8_write",
    "bounded_read_text",
    "bounded_read_bytes",
]


#: 10 MB cap for substrate file reads. Large enough for any realistic
#: canon, note, or doctrine page; small enough that a malicious 5 GB
#: file cannot OOM the kernel.
DEFAULT_MAX_READ_BYTES: Final[int] = 10 * 1024 * 1024


def atomic_utf8_write(
    path: Path,
    content: str,
    *,
    newline: str | None = "\n",
    encoding: str = "utf-8",
    errors: str = "strict",
    make_parents: bool = True,
) -> None:
    """Atomically write ``content`` to ``path``.

    Writes to a temp file in the same directory as ``path`` then
    ``os.replace``s into place. The replace is atomic on both NTFS
    (same-volume rename) and POSIX. A concurrent reader therefore sees
    either the old content or the new, never a torn mid-write state.

    Defaults:
    * ``newline="\n"`` — cross-platform-stable line endings. Pass
      ``newline=None`` for Python's universal-newline translation (CRLF
      on Windows) only when the file MUST use platform-native endings.
    * ``encoding="utf-8"`` — never Windows ``cp936`` / POSIX ``ascii``.
    * ``make_parents=True`` — create parent dirs if missing.

    Raises:
        OSError: any filesystem-level failure during the write or
            replace. The temp file is cleaned up on error when
            feasible.
        TypeError: if ``content`` is not ``str``. Route bytes via a
            separate helper when a binary variant is needed.
    """
    if not isinstance(content, str):
        raise TypeError(
            f"atomic_utf8_write expects str content; got {type(content).__name__}"
        )

    path = Path(path)
    if make_parents:
        path.parent.mkdir(parents=True, exist_ok=True)

    # tempfile.mkstemp honours dir= so the temp file lives on the same
    # filesystem as the target — required for os.replace to be atomic
    # on Windows. suffix matches the target so tooling that peeks at
    # temp files can identify them.
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_path_str)

    try:
        # Wrap the fd in a text-mode file so we get the encoding +
        # newline handling Python's open() does. Closefd=True lets the
        # context manager close tmp_fd.
        with os.fdopen(
            tmp_fd,
            "w",
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=True,
        ) as fh:
            fh.write(content)
            fh.flush()
            # fsync is best-effort: guarantees the kernel has flushed
            # buffers before we rename. Some filesystems (tmpfs) don't
            # support fsync on the fd; ignore that case.
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        # Atomic rename. os.replace overwrites target on both POSIX
        # and Windows (Python 3.3+).
        os.replace(tmp_path, path)
    except BaseException:
        # Clean up temp file on any failure including KeyboardInterrupt
        # so we never leak a ".<name>.*.tmp" on disk.
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def bounded_read_text(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_READ_BYTES,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> str:
    """Read ``path`` as UTF-8 text, refusing anything larger than
    ``max_bytes``.

    Protects against DoS-by-huge-file (a 5 GB ``_canon.yaml`` or a
    malicious ingested note). Raises ``MycoError`` when the file
    exceeds ``max_bytes`` rather than letting Python try to materialise
    it in memory.
    """
    path = Path(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise MycoError(
            f"file too large for bounded_read_text: {path} is "
            f"{size} bytes (cap {max_bytes}). Raise max_bytes "
            f"explicitly if this is intentional."
        )
    return path.read_text(encoding=encoding, errors=errors)


def bounded_read_bytes(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_READ_BYTES,
) -> bytes:
    """Byte-level counterpart of :func:`bounded_read_text`.

    Used by graph fingerprinting (which hashes raw bytes) and by
    adapters that need unnormalised content (PDF reader etc.) so that
    the same DoS cap applies everywhere we read from the substrate.
    """
    path = Path(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise MycoError(
            f"file too large for bounded_read_bytes: {path} is "
            f"{size} bytes (cap {max_bytes}). Raise max_bytes "
            f"explicitly if this is intentional."
        )
    return path.read_bytes()
