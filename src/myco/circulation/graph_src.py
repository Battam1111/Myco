"""Code-graph extension: walk ``src/**/*.py`` as circulation nodes.

Per v0.5.5 MAJOR-F / J, the circulation graph must cover Python source
as well as markdown — otherwise code-to-doctrine traversal is a gap
(the v0.4.1 audit flagged it). This module is the AST-based walker:
every ``*.py`` under the substrate's ``src/`` directory becomes a
graph node, and two edge kinds are emitted:

- ``import`` — for each ``import myco.X`` / ``from myco.X import Y``
  that resolves to a file inside ``src/``, an edge ``src_file →
  target_file``. Stdlib and third-party imports are ignored; relative
  imports are resolved via the importing file's location.
- ``code_doc_ref`` — for each substrate-relative path string that
  appears in a module docstring (e.g. a doctrine link in the
  module-level triple-quoted string), an edge ``src_file`` to
  ``docs_file``. This is what makes "which code module is governed
  by which L2 doctrine" answerable from the graph.

Cheap by construction: uses :func:`ast.parse` on the source text, no
module loading, no import resolution of the wider package. Syntax
errors are swallowed — a broken ``.py`` must not crash graph build.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from pathlib import Path

from myco.core.errors import MycoError
from myco.core.io_atomic import bounded_read_text
from myco.core.skip_dirs import should_skip_dir

__all__ = [
    "walk_src_graph",
    "SrcGraphResult",
]


# v0.8.6 — the previously-private ``_SKIP_DIRS`` clone here has been
# replaced by a delegate to :func:`myco.core.skip_dirs.should_skip_dir`.
# The clone diverged from the canonical set across releases (the
# graph walker was missing `.hg`, `.svn`, `.vscode`, `.idea`,
# `legacy_v0_3`) and the consolidation work originally promised at
# v0.5.8 had never been finished for ``circulation/graph_src.py``.
# By default this module skips test trees, mirroring the historical
# ``"tests"`` ban in the old frozenset — opt back in by passing
# ``include_tests=True`` to :func:`walk_src_graph`.


#: Regex for "looks like a substrate-relative doc path" inside a docstring.
#: Matches ``docs/<something>.md`` at minimum. We deliberately keep this
#: tight: the goal is doctrine/primordia references, not arbitrary
#: path-like substrings. ``./`` and ``../`` prefixes are stripped
#: before resolution.
_DOC_PATH_RE = re.compile(
    r"(?P<path>(?:\.{1,2}/)?(?:docs|notes)/[A-Za-z0-9_./\-]+\.md)"
)


class SrcGraphResult:
    """Plain result container for the src-graph walk.

    Not a frozen dataclass because callers merge these lists into the
    main Graph builder's own mutable state — avoiding a copy on the hot
    path. Fields:

    - ``nodes``: set of substrate-relative POSIX paths for every ``.py``
      scanned (whether or not it had outgoing edges).
    - ``import_edges``: list of ``(src_rel, dst_rel)`` pairs. ``dst_rel``
      is always a substrate-relative path that resolves inside ``src/``.
    - ``doc_edges``: list of ``(src_rel, dst_rel)`` pairs where
      ``dst_rel`` is a ``docs/*.md`` or ``notes/*.md`` path extracted
      from a module docstring. Unresolved (doesn't exist on disk) paths
      are still emitted — the dangling-edge machinery surfaces them.
    """

    __slots__ = ("doc_edges", "import_edges", "nodes")

    def __init__(self) -> None:
        self.nodes: set[str] = set()
        self.import_edges: list[tuple[str, str]] = []
        self.doc_edges: list[tuple[str, str]] = []


def _rel(root: Path, p: Path) -> str:
    return str(p.resolve().relative_to(root.resolve())).replace("\\", "/")


# v0.8.6 — the previously-public ``_iter_py_files`` walker has been
# excreted. It was a duplicate of ``_walk_py`` (split out at v0.5.8 to
# carry a different skip set) and had no in-tree callers. The
# active ``_walk_py`` walker below is the single source of truth.


def _module_to_path(
    module_name: str, src_dir: Path, internal_prefix: str = "myco"
) -> Path | None:
    """Resolve a dotted module name to a file path under ``src_dir``.

    Only resolves imports of the substrate's own ``internal_prefix``
    (default ``myco``) — everything else is stdlib or third-party and
    returns ``None``. Tries ``foo/bar.py`` first, then ``foo/bar/
    __init__.py``. Returns ``None`` if neither exists.
    """
    if not module_name:
        return None
    parts = module_name.split(".")
    if parts[0] != internal_prefix:
        return None
    # Walk ``src_dir/<parts[0]>/.../<parts[-1]>.py``. ``internal_prefix``
    # is itself the top-level directory name under ``src/`` by
    # convention (``src/myco/...``).
    as_file = src_dir.joinpath(*parts).with_suffix(".py")
    if as_file.is_file():
        return as_file
    as_pkg_init = src_dir.joinpath(*parts) / "__init__.py"
    if as_pkg_init.is_file():
        return as_pkg_init
    return None


def _resolve_relative_import(
    importing_file: Path,
    src_dir: Path,
    module: str | None,
    level: int,
    internal_prefix: str = "myco",
) -> Path | None:
    """Resolve a ``from . import x`` / ``from ..y import z`` form.

    ``level`` is the count of leading dots. The importer's package is
    ``importing_file.parent``; ``level=1`` means "that package",
    ``level=2`` means "one up", etc. ``module`` appends a dotted
    suffix (or may be ``None`` for ``from . import x``).

    We translate the relative form to an absolute dotted name under
    ``internal_prefix`` and delegate to :func:`_module_to_path`. If
    the computed base escapes ``src_dir`` (too many dots), return
    ``None``.
    """
    if level <= 0:
        return None
    try:
        importing_rel_parts = (
            importing_file.resolve().relative_to(src_dir.resolve()).parts
        )
    except ValueError:
        return None
    # The package of ``importing_file`` is its parent directory (parts
    # minus the filename). Strip the trailing filename component.
    pkg_parts = list(importing_rel_parts[:-1])
    # Each leading dot past the first pops one package level. ``level=1``
    # means "this package" — nothing popped. ``level=2`` pops one, etc.
    pops = level - 1
    if pops > len(pkg_parts):
        return None
    base_parts = pkg_parts[: len(pkg_parts) - pops] if pops else pkg_parts
    tail_parts = module.split(".") if module else []
    dotted = ".".join(base_parts + tail_parts)
    # ``base_parts`` includes the ``internal_prefix`` root by construction
    # (we took it from ``importing_rel_parts`` which starts at ``myco/``),
    # so _module_to_path will accept it.
    return _module_to_path(dotted, src_dir, internal_prefix=internal_prefix)


def _extract_docstring_doc_refs(
    docstring: str | None,
) -> list[str]:
    """Pull substrate-relative ``docs/*.md`` / ``notes/*.md`` strings.

    Runs the :data:`_DOC_PATH_RE` pattern over the docstring and
    deduplicates in insertion order. Leading ``./`` is stripped;
    ``../`` sequences are left as-is for the resolver in
    :func:`walk_src_graph` to canonicalize.
    """
    if not docstring:
        return []
    seen: list[str] = []
    seen_set: set[str] = set()
    for m in _DOC_PATH_RE.finditer(docstring):
        raw = m.group("path")
        # Normalize leading ``./``; ``../`` is kept so the resolver can
        # decide whether it escapes the substrate (and drop it if so).
        while raw.startswith("./"):
            raw = raw[2:]
        if raw in seen_set:
            continue
        seen_set.add(raw)
        seen.append(raw)
    return seen


def walk_src_graph(
    substrate_root: Path,
    *,
    include_tests: bool = False,
    internal_prefix: str = "myco",
    docs_dir: str = "docs",
    notes_dir: str = "notes",
) -> SrcGraphResult:
    """Walk ``<substrate_root>/src/`` and return nodes + edges.

    No-op (empty result) when the substrate has no ``src/`` directory —
    pure-doctrine substrates never trip the code graph.

    Args:
        substrate_root: the substrate's root path.
        include_tests: if True, ``src/tests/`` style dirs are *not*
            skipped. Default False — tests are excluded from the logical
            graph because their import edges dominate without adding
            signal. (Repository-level ``tests/`` outside ``src/`` is
            always excluded because we only walk ``src/``.)
        internal_prefix: the top-level package name that marks an
            "internal" import (default ``"myco"``). Third-party and
            stdlib imports are dropped.

    The walk is best-effort: a ``.py`` file that fails to parse is
    skipped (node still recorded so ``perfuse`` can see it, but no
    edges extracted).
    """
    result = SrcGraphResult()
    src_dir = (substrate_root / "src").resolve()
    if not src_dir.is_dir():
        return result
    root = substrate_root.resolve()

    # v0.8.6 — delegate to the canonical skip-dir predicate. The walk
    # honors ``include_tests`` (False ⇒ ``tests/`` is pruned via the
    # ``TEST_DIRS`` augmentation in ``core/skip_dirs``). The previous
    # local ``_SKIP_DIRS`` set is gone (drifted from the canonical
    # source and re-introduced quietly-different skip behavior).
    for py in _walk_py(src_dir, include_tests=include_tests):
        rel = _rel(root, py)
        result.nodes.add(rel)
        try:
            source = bounded_read_text(py)
        except (OSError, MycoError):
            continue
        try:
            tree = ast.parse(source, filename=str(py))
        except SyntaxError:
            # Node is recorded but we can't extract edges from a file
            # that doesn't parse. This is intentional: a broken source
            # file should show up in the graph so operators can see it
            # exists, without taking down graph-build.
            continue

        # --- imports ----------------------------------------------------
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _module_to_path(
                        alias.name, src_dir, internal_prefix=internal_prefix
                    )
                    if target is not None:
                        result.import_edges.append((rel, _rel(root, target)))
            elif isinstance(node, ast.ImportFrom):
                # ``node.level`` = 0 means absolute; >=1 means relative.
                if node.level and node.level > 0:
                    base_target = _resolve_relative_import(
                        py,
                        src_dir,
                        node.module,
                        node.level,
                        internal_prefix=internal_prefix,
                    )
                    # ``from . import X`` (node.module=None, level=1) resolves
                    # to the importing file's own package ``__init__.py`` —
                    # which IS the importing file when ``py`` is the package
                    # init. Suppress the self-edge: it's an artifact of
                    # treating ``__init__.py`` as both source and target,
                    # not a real referential cycle. SE3 would otherwise
                    # flag every ``from . import sibling`` as a self-cycle.
                    if base_target is not None and _rel(root, base_target) != rel:
                        result.import_edges.append((rel, _rel(root, base_target)))
                    elif base_target is not None and _rel(root, base_target) == rel:
                        # Treat as None for downstream sub-target dedup.
                        base_target = None
                    # ``from . import sibling`` / ``from .pkg import mod``
                    # — each alias may itself be a submodule. Try each
                    # as a relative import one level deeper (append the
                    # alias to ``node.module``). If it resolves, add an
                    # edge to that specific file as well.
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        combined = (
                            f"{node.module}.{alias.name}" if node.module else alias.name
                        )
                        sub_target = _resolve_relative_import(
                            py,
                            src_dir,
                            combined,
                            node.level,
                            internal_prefix=internal_prefix,
                        )
                        if sub_target is not None and sub_target != base_target:
                            result.import_edges.append((rel, _rel(root, sub_target)))
                    continue
                base = node.module or ""
                # First try the bare ``from pkg.mod import X`` form —
                # the edge is to ``pkg/mod.py`` (or the package init).
                base_target = _module_to_path(
                    base, src_dir, internal_prefix=internal_prefix
                )
                if base_target is not None:
                    result.import_edges.append((rel, _rel(root, base_target)))
                # Also try ``from pkg import submodule`` — each name
                # may itself be a module. We add both edges when the
                # submodule form resolves; this keeps the graph faithful
                # to how Python actually resolves the import.
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    dotted = f"{base}.{alias.name}" if base else alias.name
                    sub_target = _module_to_path(
                        dotted, src_dir, internal_prefix=internal_prefix
                    )
                    if sub_target is not None and sub_target != base_target:
                        result.import_edges.append((rel, _rel(root, sub_target)))

        # --- docstring doc refs ----------------------------------------
        docstring = ast.get_docstring(tree)
        for raw in _extract_docstring_doc_refs(docstring):
            # v0.8.4 root-cleanup: pass canon-configured dirs so the
            # resolver can fall back from "docs/X" to ".docs/X" when
            # Myco-self has relocated the tree.
            resolved = _resolve_doc_ref(
                raw, root, docs_dir=docs_dir, notes_dir=notes_dir
            )
            if resolved is None:
                # Escapes substrate → drop. We don't emit dangling edges
                # from ``..`` that would land outside the tree; keeping
                # the graph rooted to the substrate is the whole point.
                continue
            result.doc_edges.append((rel, resolved))

    return result


def _walk_py(src_dir: Path, *, include_tests: bool = False) -> Iterator[Path]:
    """DFS ``src_dir`` yielding ``*.py`` files, honoring canonical skip-dirs.

    v0.8.6 — uses :func:`myco.core.skip_dirs.should_skip_dir` so the
    set of pruned directories matches every other walker in Myco. The
    previous local skip set drifted from the canonical one (missed
    `.hg`, `.svn`, `.vscode`, `.idea`, `legacy_v0_3`, `.myco/state`).

    v0.5.8 (Lens 13 P1-13-9): symlinks skipped and inode-visited set
    guards cycles. Walks dominated by ``.venv/`` or ``__pycache__/``
    would otherwise blow the node budget on contributor checkouts.
    """
    if not src_dir.is_dir():
        return
    stack: list[Path] = [src_dir]
    visited: set[tuple[int, int]] = set()
    while stack:
        here = stack.pop()
        try:
            entries = list(here.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if should_skip_dir(entry.name, include_tests=include_tests):
                    continue
                try:
                    st = entry.stat()
                    key = (st.st_dev, st.st_ino)
                except OSError:
                    continue
                if key in visited:
                    continue
                visited.add(key)
                stack.append(entry)
            elif entry.is_file() and entry.suffix == ".py":
                yield entry


def _resolve_doc_ref(
    raw: str,
    substrate_root: Path,
    *,
    docs_dir: str = "docs",
    notes_dir: str = "notes",
) -> str | None:
    """Resolve a ``docs/*.md``-style string to a substrate-relative path.

    Returns a POSIX path relative to ``substrate_root`` — or ``None``
    if the path escapes the substrate (e.g. ``../../other/thing.md``).

    v0.8.4 root-cleanup (2026-05-12): when ``raw`` starts with the
    well-known semantic prefixes ``docs/`` / ``notes/`` and that
    literal path doesn't resolve under the substrate root, retry
    against the canon-declared ``docs_dir`` / ``notes_dir`` (Myco-self
    uses ``.docs`` / ``.myco/notes``; downstream substrates keep
    "docs" / "notes"). Existence is verified on the retried path —
    if neither location has the file, return the literal resolution
    so SE1 / dangling-edge bookkeeping continues to fire.
    """
    root_r = substrate_root.resolve()
    try:
        target = (root_r / raw).resolve()
        target.relative_to(root_r)
    except (ValueError, OSError):
        return None
    rel = str(target.relative_to(root_r)).replace("\\", "/")
    if not target.exists():
        for legacy_prefix, override in (
            ("docs/", docs_dir),
            ("notes/", notes_dir),
        ):
            if legacy_prefix == override + "/":
                continue
            if raw.startswith(legacy_prefix) or rel.startswith(legacy_prefix):
                stripped = (
                    raw[len(legacy_prefix) :]
                    if raw.startswith(legacy_prefix)
                    else rel[len(legacy_prefix) :]
                )
                alt = (root_r / override / stripped).resolve()
                try:
                    alt.relative_to(root_r)
                except (ValueError, OSError):
                    continue
                if alt.exists():
                    return str(alt.relative_to(root_r)).replace("\\", "/")
    return rel
