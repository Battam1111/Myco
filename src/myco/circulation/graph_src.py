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

__all__ = [
    "walk_src_graph",
    "SrcGraphResult",
]


#: Directory names we always skip when walking ``src/``. Build artifacts,
#: virtualenvs, and caches are never part of the logical graph. ``tests``
#: is skipped by default because unit-test imports dominate the edge
#: budget without adding signal; toggle via ``include_tests=True`` if a
#: caller ever needs them.
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".tox",
        "node_modules",
        ".git",
        "tests",
    }
)


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


def _iter_py_files(src_dir: Path) -> Iterator[Path]:
    """Walk ``src_dir`` yielding ``*.py`` files, pruning skip-dirs.

    ``Path.rglob`` does not let us prune mid-walk, so we roll a manual
    DFS that honors :data:`_SKIP_DIRS`. This matters because a ``.venv/``
    left inside a contributor's substrate can add tens of thousands of
    files and blow up graph-build time.
    """
    if not src_dir.is_dir():
        return
    stack: list[Path] = [src_dir]
    while stack:
        here = stack.pop()
        try:
            entries = list(here.iterdir())
        except OSError:
            # Unreadable directory — skip silently rather than crash
            # graph-build on a permissions issue.
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name in _SKIP_DIRS:
                    continue
                stack.append(entry)
            elif entry.is_file() and entry.suffix == ".py":
                yield entry


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

    # Honor ``include_tests`` by optionally removing the ``tests`` ban
    # from the skip set for this walk. We build the effective set
    # locally so ``_SKIP_DIRS`` stays frozen at module level.
    effective_skip = _SKIP_DIRS - {"tests"} if include_tests else _SKIP_DIRS

    for py in _walk_py(src_dir, effective_skip):
        rel = _rel(root, py)
        result.nodes.add(rel)
        try:
            source = py.read_text(encoding="utf-8")
        except OSError:
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
                    if base_target is not None:
                        result.import_edges.append((rel, _rel(root, base_target)))
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
            resolved = _resolve_doc_ref(raw, root)
            if resolved is None:
                # Escapes substrate → drop. We don't emit dangling edges
                # from ``..`` that would land outside the tree; keeping
                # the graph rooted to the substrate is the whole point.
                continue
            result.doc_edges.append((rel, resolved))

    return result


def _walk_py(src_dir: Path, effective_skip: frozenset[str]) -> Iterator[Path]:
    """DFS ``src_dir`` yielding ``*.py`` files, honoring ``effective_skip``.

    Split out from :func:`_iter_py_files` so ``walk_src_graph`` can
    toggle the ``tests`` exclusion at call time without mutating the
    module-level frozenset.
    """
    if not src_dir.is_dir():
        return
    stack: list[Path] = [src_dir]
    while stack:
        here = stack.pop()
        try:
            entries = list(here.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name in effective_skip:
                    continue
                stack.append(entry)
            elif entry.is_file() and entry.suffix == ".py":
                yield entry


def _resolve_doc_ref(raw: str, substrate_root: Path) -> str | None:
    """Resolve a ``docs/*.md``-style string to a substrate-relative path.

    Returns a POSIX path relative to ``substrate_root`` — or ``None``
    if the path escapes the substrate (e.g. ``../../other/thing.md``).
    Doesn't check for file existence here: unresolved edges flow
    through the same dangling-ref channel as markdown links do.
    """
    root_r = substrate_root.resolve()
    try:
        target = (root_r / raw).resolve()
        target.relative_to(root_r)
    except (ValueError, OSError):
        return None
    return str(target.relative_to(root_r)).replace("\\", "/")
