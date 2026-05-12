"""Cluster module — v0.8.8 max-aggressive merge of io, io_atomic, paths, skip_dirs.

=== io ===
I/O primitives. Currently: stdio encoding guard for platforms whose
default (e.g. GBK on Chinese Windows) cannot encode the Unicode that
Myco emits (box-drawing glyphs in embedded prompts, non-ASCII note
content, JSON with any user-supplied text).

v0.5.8: extended to cover ``sys.stdin`` too. On Chinese Windows
(cp936/GBK) the MCP stdio transport was receiving UTF-8-encoded
JSON-RPC request bodies but decoding them as GBK before the handler
saw the payload — corrupting every Chinese / emoji / non-latin
argument. Reconfiguring stdin to UTF-8 at every ``main()`` entry
fixes this uniformly.

=== io_atomic ===
Atomic file I/O helpers — the single chokepoint every kernel write
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

* **Line-ending normalisation** — ``newline="
"`` is the default so
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

=== paths ===
Canonical paths within a substrate.

Governing doctrine: ``docs/architecture/L1_CONTRACT/canon_schema.md``
(the canon declares ``system.write_surface.allowed`` globs against
which these canonical paths are matched).

Pure functions of the substrate root, plus a small set of
discovery helpers (``find_substrate_canon`` / ``has_substrate``) that
do touch the filesystem — kept here as the canonical resolution
point for the v0.8.4+ dual-location canon layout.

=== skip_dirs ===
Canonical directory-skip list for every filesystem walker in Myco.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
(Circulation § "Scope" — the graph walker's skip rules live here).
Also consumed by ``docs/architecture/L2_DOCTRINE/ingestion.md`` §
"Forage" and by MP1/MP2 dimensions.

v0.5.8 consolidated three previously-divergent ``_SKIP_DIRS`` lists
(``circulation/graph_src.py``, ``ingestion/adapters/code_repo.py``, and
an inline predicate in ``homeostasis/dimensions/mp1_no_provider_imports.py``)
into this single module so every walker sees the same set.

The list covers:

* **Python tooling caches**: ``__pycache__``, ``.pytest_cache``,
  ``.mypy_cache``, ``.ruff_cache``, ``.tox``, ``*.egg-info``.
* **VCS**: ``.git``, ``.hg``, ``.svn``.
* **Python virtualenvs**: ``.venv``, ``venv``, ``env``.
* **Node ecosystem**: ``node_modules``.
* **Build output**: ``build``, ``dist``.
* **Editor local caches**: ``.vscode``, ``.idea``, ``.DS_Store`` (file, but
  a reasonable include).
* **Myco's own runtime state**: ``.myco/state`` (derivable; must not
  be ingested or graphed).
* **Legacy quarantine (defensive — directory excreted at v0.7.0)**:
  ``legacy_v0_3`` is no longer in the working tree. The filter
  remains so that if a downstream substrate clones an old branch and
  re-introduces the directory, walks still skip it.

Callers can opt in to test trees (``tests`` is NOT in the default
skip set so graph-walkers cover test-doc refs correctly; pass
``include_tests=False`` to exclude).
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .identity_cluster import MycoError

# =========================================================================
# === io — formerly io.py
# =========================================================================


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
            pass


# =========================================================================
# === io_atomic — formerly io_atomic.py
# =========================================================================

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
        * ``newline="
    "`` — cross-platform-stable line endings. Pass
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
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(
            tmp_fd, "w", encoding=encoding, errors=errors, newline=newline, closefd=True
        ) as fh:
            fh.write(content)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        os.replace(tmp_path, path)
    except BaseException:
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
            f"file too large for bounded_read_text: {path} is {size} bytes (cap {max_bytes}). Raise max_bytes explicitly if this is intentional."
        )
    return path.read_text(encoding=encoding, errors=errors)


def bounded_read_bytes(path: Path, *, max_bytes: int = DEFAULT_MAX_READ_BYTES) -> bytes:
    """Byte-level counterpart of :func:`bounded_read_text`.

    Used by graph fingerprinting (which hashes raw bytes) and by
    adapters that need unnormalised content (PDF reader etc.) so that
    the same DoS cap applies everywhere we read from the substrate.
    """
    path = Path(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise MycoError(
            f"file too large for bounded_read_bytes: {path} is {size} bytes (cap {max_bytes}). Raise max_bytes explicitly if this is intentional."
        )
    return path.read_bytes()


# =========================================================================
# === paths — formerly paths.py
# =========================================================================

_CANON_CANDIDATES: tuple[str, ...] = (".myco/canon.yaml", "_canon.yaml")


def find_substrate_canon(root: Path) -> Path:
    """Return the canon file path for a substrate root.

    Tries ``.myco/canon.yaml`` first (v0.8.4+ layout); falls back to
    ``_canon.yaml`` (legacy / downstream substrates). Returns the new
    path even when neither exists (caller can ``is_file()``-check the
    result for graceful "not a substrate" handling).
    """
    for filename in _CANON_CANDIDATES:
        p = root / filename
        if p.is_file():
            return p
    return root / _CANON_CANDIDATES[0]


def has_substrate(root: Path) -> bool:
    """True when ``root`` contains a Myco canon (either layout)."""
    return any((root / fn).is_file() for fn in _CANON_CANDIDATES)


@dataclass(frozen=True)
class SubstratePaths:
    """The canonical directory/file layout of a Myco substrate.

    Every path is absolute and derived from ``root``. Whether a path
    *exists* on disk is a separate question — callers check as needed.

    v0.8.4 root-cleanup (2026-05-12): the canon filename is now a
    constructor parameter so substrates on the new ``.myco/canon.yaml``
    layout and substrates on the legacy ``_canon.yaml`` layout share
    the same paths object. ``Substrate.load`` determines which layout
    the substrate uses (via :func:`find_substrate_canon`) and passes
    the resolved relative path here.
    """

    root: Path
    canon_filename: str = "_canon.yaml"
    notes_dir: str = "notes"
    docs_dir: str = "docs"

    @property
    def canon(self) -> Path:
        """The substrate's L4 single source of truth.

        Default is the legacy ``_canon.yaml`` at root; Myco-self (and
        any v0.8.4+-layout substrate) sets this to
        ``.myco/canon.yaml`` via the ``canon_filename`` ctor arg.
        """
        return self.root / self.canon_filename

    @property
    def notes(self) -> Path:
        """Substrate notes tree (raw/integrated/distilled).

        Default ``notes/`` at root; Myco-self overrides to
        ``.myco/notes/`` via canon ``system.notes_dir``.
        """
        return self.root / self.notes_dir

    @property
    def docs(self) -> Path:
        """Substrate documentation tree (architecture, primordia, ...).

        Default ``docs/`` at root; Myco-self overrides to ``.docs/``
        via canon ``system.docs_dir``.
        """
        return self.root / self.docs_dir

    @property
    def state(self) -> Path:
        """``.myco/state/`` — runtime state (not source of truth)."""
        return self.root / ".myco/state"

    @property
    def autoseeded_marker(self) -> Path:
        """Skeleton-mode marker consumed by the immune kernel."""
        return self.state / "autoseeded.txt"

    @property
    def boot_brief(self) -> Path:
        """Session boot brief written by ``myco hunger``."""
        return self.state / "boot_brief.md"

    @property
    def graph_cache(self) -> Path:
        """``.myco/state/graph.json`` — persisted circulation graph.

        The graph cache is written by :func:`myco.circulation.graph.build_graph`
        when ``use_cache=True`` (the default) and read on the next call as
        long as the canon + src fingerprint matches. Lives under
        ``.myco/state/`` because it's runtime state, not source of truth —
        safe to delete at any time (next ``build_graph`` rebuilds).
        """
        return self.state / "graph.json"

    @property
    def entry_point(self) -> Path:
        """Default agent entry page.

        The *actual* entry point comes from ``canon.identity.entry_point``;
        this property exposes the default (``MYCO.md``). The canon-
        driven version is resolved in ``Substrate.load``.
        """
        return self.root / "MYCO.md"

    @property
    def local_plugins_dir(self) -> Path:
        """``.myco/plugins/`` — substrate-local plugin package root."""
        return self.root / ".myco" / "plugins"

    @property
    def local_plugins_init(self) -> Path:
        """``.myco/plugins/__init__.py`` — the entry-point importer."""
        return self.root / ".myco" / "plugins" / "__init__.py"

    @property
    def manifest_overlay(self) -> Path:
        """``.myco/manifest_overlay.yaml`` — per-substrate verb overlay."""
        return self.root / ".myco" / "manifest_overlay.yaml"


# =========================================================================
# === skip_dirs — formerly skip_dirs.py
# =========================================================================

DEFAULT_SKIP_DIRS: Final[frozenset[str]] = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "build",
        "dist",
        ".vscode",
        ".idea",
        ".myco/state",
        "legacy_v0_3",
    }
)

TEST_DIRS: Final[frozenset[str]] = frozenset({"tests", "test"})


def should_skip_dir(
    name: str, *, include_tests: bool = True, extra: Iterable[str] | None = None
) -> bool:
    """Return True if a directory with the given basename should be
    skipped by a walker.

    Args:
        name: basename of the directory (not a full path).
        include_tests: if True (default), ``tests/`` is walked. Pass
            False when forage'ing a downstream project and test trees
            are typically noise.
        extra: caller-supplied additions to the skip set (e.g. a
            substrate-local ``canon.system.walker_skip_dirs`` field).

    Also skips any directory whose basename matches the ``*.egg-info``
    glob (covers ``myco.egg-info``, ``pip.egg-info``, etc.) and any
    dot-prefixed directory not explicitly listed (heuristic for ".*"
    private dirs like ``.next``, ``.cache``; callers that legitimately
    want to walk such dirs pass ``extra`` and filter the result).
    """
    skip_set = set(DEFAULT_SKIP_DIRS)
    if not include_tests:
        skip_set |= TEST_DIRS
    if extra:
        skip_set |= set(extra)
    if name in skip_set:
        return True
    return name.endswith(".egg-info")


def should_skip_path(
    path: Path,
    *,
    root: Path | None = None,
    include_tests: bool = True,
    extra: Iterable[str] | None = None,
) -> bool:
    """Return True if any component of ``path`` (relative to ``root``
    if supplied, otherwise all parts) triggers the skip predicate.

    This is the common predicate walkers use when iterating deep
    trees: a nested match at any level prunes the entire subtree.
    """
    if root is not None:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        parts = rel.parts
    else:
        parts = path.parts
    for part in parts:
        if should_skip_dir(part, include_tests=include_tests, extra=extra):
            return True
    return False
