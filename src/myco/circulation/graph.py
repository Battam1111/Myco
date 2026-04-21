"""Cross-reference graph for a substrate.

Per L2 ``circulation.md`` and the Stage B.6 craft, the graph is built
on demand from these sources:

1. ``_canon.yaml`` — any leaf string under a key ending in ``_ref``.
2. Note frontmatter — ``references:`` lists in ``notes/**/*.md``.
3. Markdown links — ``[text](relative/path)`` in notes, ``docs/``, and
   the entry-point file (fenced code blocks are skipped).
4. (v0.5.5 MAJOR-F) Python sources under ``src/**/*.py`` — AST-extracted
   ``import`` edges between internal modules plus ``code_doc_ref``
   edges from module docstrings to doctrine/notes paths. See
   :mod:`myco.circulation.graph_src` for the walker.

Nodes are substrate-relative path strings (POSIX-style). Edges carry a
``kind`` tag — one of :data:`EdgeKind`.

v0.5.5 MAJOR-J added graph persistence: :func:`build_graph` caches its
result to ``.myco_state/graph.json`` and reloads on the next call as
long as the canon + ``src/`` fingerprint matches. Pass
``use_cache=False`` to force a rebuild without touching the cache, or
call :func:`invalidate_graph_cache` to evict. The on-disk shape is
versioned (``schema: "1"``) so future kernels can reject unknown
schemas cleanly.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml

from myco.core.context import MycoContext
from myco.core.io_atomic import atomic_utf8_write
from myco.core.substrate import Substrate
from myco.digestion.pipeline import parse_note

from .graph_src import walk_src_graph

__all__ = [
    "Edge",
    "Graph",
    "EdgeKind",
    "build_graph",
    "persist_graph",
    "load_persisted_graph",
    "invalidate_graph_cache",
    "GRAPH_CACHE_SCHEMA",
]


#: Schema version string for the persisted graph file. Bump when the
#: on-disk shape changes; :func:`load_persisted_graph` returns ``None``
#: when the file's ``schema`` doesn't match this, triggering a rebuild.
GRAPH_CACHE_SCHEMA = "1"


EdgeKind = Literal[
    "canon_ref",
    "note_ref",
    "markdown_link",
    "import",
    "code_doc_ref",
]

_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_FENCE_RE = re.compile(r"^\s*```")


@dataclass(frozen=True)
class Edge:
    """A directed reference edge in the substrate graph."""

    src: str
    dst: str
    kind: EdgeKind


@dataclass(frozen=True)
class Graph:
    """Snapshot of the substrate's reference graph.

    ``nodes`` is the set of known substrate-relative paths (every file
    scanned, whether or not it had outgoing edges). ``edges`` is a
    tuple of :class:`Edge` records.
    """

    nodes: frozenset[str]
    edges: tuple[Edge, ...] = field(default_factory=tuple)

    def outgoing(self, src: str) -> tuple[Edge, ...]:
        return tuple(e for e in self.edges if e.src == src)

    def incoming(self, dst: str) -> tuple[Edge, ...]:
        return tuple(e for e in self.edges if e.dst == dst)


# --- helpers ---------------------------------------------------------------


def _rel(root: Path, p: Path) -> str:
    return str(p.resolve().relative_to(root.resolve())).replace("\\", "/")


def _is_external(ref: str) -> bool:
    lower = ref.lower().strip()
    if not lower:
        return True
    if lower.startswith(("http://", "https://", "mailto:", "#", "/")):
        return True
    # Windows-style absolute
    return bool(len(lower) >= 2 and lower[1] == ":")


def _strip_fragment(ref: str) -> str:
    # Drop any ``#anchor`` or ``?query`` tail before resolving on disk.
    for ch in ("#", "?"):
        i = ref.find(ch)
        if i != -1:
            ref = ref[:i]
    return ref.strip()


def _iter_canon_refs(node: Any, path: tuple[str, ...] = ()) -> Iterator[str]:
    """Yield every scalar found under a key ending in ``_ref``."""
    if isinstance(node, Mapping):
        for key, value in node.items():
            sub_path = (*path, str(key))
            key_is_ref = str(key).endswith("_ref")
            if key_is_ref and isinstance(value, str):
                yield value
            elif key_is_ref and isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, str):
                        yield item
            else:
                yield from _iter_canon_refs(value, sub_path)
    elif isinstance(node, (list, tuple)):
        for item in node:
            yield from _iter_canon_refs(item, path)


def _iter_markdown_links(text: str) -> Iterator[str]:
    """Yield link targets from ``text``, skipping fenced code blocks."""
    in_fence = False
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in _MD_LINK_RE.finditer(line):
            yield m.group(1)


class _SkipType:
    """Sentinel class for external refs that ``_resolve`` intentionally
    drops. Using a dedicated class (instead of ``object()``) lets mypy
    narrow ``result is _SKIP`` statically, so the downstream
    ``Edge(dst=resolved)`` and ``nodes.add(resolved)`` calls don't
    require a cast to ``str``.
    """

    _instance: _SkipType | None = None

    def __new__(cls) -> _SkipType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


_SKIP: _SkipType = _SkipType()  # sentinel: external ref, drop silently


def _resolve(
    root: Path,
    owner_rel: str,
    ref: str,
    *,
    anchor: str = "file",
) -> str | None | _SkipType:
    """Resolve ``ref`` to a substrate-relative path.

    Returns:
        - a substrate-relative path string on success,
        - ``_SKIP`` if ``ref`` is external (URL / anchor / absolute),
        - ``None`` if it's a substrate-relative ref that doesn't resolve
          (escapes substrate, or just points to something missing —
          caller emits a dangling edge).
    """
    ref = _strip_fragment(ref)
    if _is_external(ref):
        return _SKIP
    base = root if anchor == "root" else (root / owner_rel).parent
    try:
        target = (base / ref).resolve()
        target.relative_to(root.resolve())
    except (ValueError, OSError):
        return None
    return str(target.relative_to(root.resolve())).replace("\\", "/")


def _iter_files(base: Path, suffixes: Iterable[str]) -> Iterator[Path]:
    if not base.is_dir():
        return
    for p in base.rglob("*"):
        if p.is_file() and p.suffix in set(suffixes):
            yield p


# --- fingerprint + persistence --------------------------------------------


def _canon_fingerprint(substrate: Substrate) -> str:
    """Hash of canon contents + ``src/`` ``(path, mtime)`` pairs.

    Used as the cache-invalidation key for ``.myco_state/graph.json``:
    two builds on the same substrate with the same canon text and the
    same set of Python sources at the same mtimes share a fingerprint,
    and the second build can short-circuit to a cache read.

    Notes deliberately NOT included: markdown edits under ``notes/`` or
    ``docs/`` do not invalidate the cache. That is the intended
    trade-off — graphs over markdown are cheap to rebuild; the
    expensive work is the AST walk over ``src/``, and that's keyed on
    source changes. Callers who want a guaranteed fresh graph pass
    ``use_cache=False``.
    """
    h = hashlib.sha256()
    canon_path = substrate.paths.canon
    if canon_path.is_file():
        try:
            h.update(canon_path.read_bytes())
        except OSError:
            pass
    # Separator byte so "canon ending in bytes that look like a mtime
    # pair" can't collide with the second section.
    h.update(b"\x00\x00SRC\x00\x00")
    src_dir = substrate.root / "src"
    if src_dir.is_dir():
        entries: list[tuple[str, int]] = []
        # Reuse the same skip-dir logic as the src walker so mtime
        # snapshots of ``.venv/`` or ``__pycache__/`` can't whipsaw the
        # fingerprint. Import locally to avoid a top-level cycle.
        from .graph_src import _SKIP_DIRS

        stack: list[Path] = [src_dir]
        # v0.5.8 (Lens 13 P1-13-9): inode-visited guard + symlink skip
        # so the fingerprint walker cannot hit an infinite loop on a
        # symlinked source tree. Matches ``graph_src._walk_py``.
        visited: set[tuple[int, int]] = set()
        while stack:
            here = stack.pop()
            try:
                children = list(here.iterdir())
            except OSError:
                continue
            for child in children:
                if child.is_symlink():
                    continue
                if child.is_dir():
                    if child.name in _SKIP_DIRS:
                        continue
                    try:
                        st = child.stat()
                        key = (st.st_dev, st.st_ino)
                    except OSError:
                        continue
                    if key in visited:
                        continue
                    visited.add(key)
                    stack.append(child)
                elif child.is_file() and child.suffix == ".py":
                    try:
                        mtime_ns = child.stat().st_mtime_ns
                    except OSError:
                        continue
                    rel = str(
                        child.resolve().relative_to(substrate.root.resolve())
                    ).replace("\\", "/")
                    entries.append((rel, mtime_ns))
        entries.sort()
        for rel, mtime_ns in entries:
            h.update(rel.encode("utf-8"))
            h.update(b"|")
            h.update(str(mtime_ns).encode("ascii"))
            h.update(b"\n")
    return h.hexdigest()


def persist_graph(graph: Graph, path: Path, *, fingerprint: str) -> None:
    """Write ``graph`` to ``path`` as JSON under the v1 schema.

    The enclosing directory is created if missing (``.myco_state/`` is
    allowed not to exist yet on fresh substrates). UTF-8 output with
    ``indent=2`` — small enough to diff comfortably, large enough to
    matter if we forgot to sort.

    Edges are flattened to ``[src, dst, kind]`` triples. Nodes are
    sorted so two runs on the same inputs produce byte-identical
    files (useful for git-scratching the cache even though it lives
    under ``.myco_state/``).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema": GRAPH_CACHE_SCHEMA,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "canon_fingerprint": fingerprint,
        "nodes": sorted(graph.nodes),
        "edges": [[e.src, e.dst, e.kind] for e in graph.edges],
    }
    # v0.5.8 Phase 8-10: the persisted graph cache now goes through the
    # shared atomic chokepoint (temp + fsync + os.replace). A concurrent
    # ``build_graph`` on the same substrate can no longer see a
    # half-written ``graph.json`` — readers observe either the old cache
    # or the new, never a torn JSON mid-write.
    atomic_utf8_write(path, json.dumps(payload, indent=2, ensure_ascii=False))


def load_persisted_graph(path: Path) -> tuple[Graph, str] | None:
    """Load a persisted graph from ``path``.

    Returns ``(graph, fingerprint)`` on success, or ``None`` when:

    - the file does not exist,
    - the file is not valid JSON,
    - the top-level ``schema`` doesn't match :data:`GRAPH_CACHE_SCHEMA`,
    - required keys are missing or malformed.

    Any of these cases fall through to a rebuild in :func:`build_graph`.
    Corrupt caches are never raised — a deleted or damaged cache must
    not brick the caller.
    """
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, Mapping):
        return None
    if raw.get("schema") != GRAPH_CACHE_SCHEMA:
        return None
    nodes_raw = raw.get("nodes")
    edges_raw = raw.get("edges")
    fp = raw.get("canon_fingerprint")
    if not isinstance(nodes_raw, list) or not isinstance(edges_raw, list):
        return None
    if not isinstance(fp, str):
        return None
    try:
        nodes = frozenset(str(n) for n in nodes_raw)
        edges: list[Edge] = []
        for item in edges_raw:
            if not isinstance(item, (list, tuple)) or len(item) != 3:
                return None
            src, dst, kind = item
            edges.append(
                Edge(src=str(src), dst=str(dst), kind=str(kind))  # type: ignore[arg-type]
            )
    except (TypeError, ValueError):
        return None
    return Graph(nodes=nodes, edges=tuple(edges)), fp


def invalidate_graph_cache(substrate: Substrate) -> bool:
    """Delete the substrate's graph cache file if present.

    Returns True if a file was removed, False if there was nothing to
    remove. Swallows filesystem errors (the cache is best-effort; a
    locked or permission-denied cache will simply stay and be
    overwritten on the next ``build_graph`` with ``use_cache=True``).
    """
    path = substrate.paths.graph_cache
    if not path.is_file():
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True


# --- builder ---------------------------------------------------------------


def _build_graph_uncached(ctx: MycoContext) -> Graph:
    """Fresh scan of the substrate. Bypasses all caching.

    This is the inner builder. The public :func:`build_graph` wraps it
    with cache-check logic. The split exists so callers who really need
    an uncached snapshot (e.g. the cache-writer itself) can grab one
    without special-casing.
    """
    root = ctx.substrate.root.resolve()
    edges: list[Edge] = []
    nodes: set[str] = set()

    # --- 1) canon refs ------------------------------------------------------
    canon_rel = "_canon.yaml"
    canon_path = ctx.substrate.paths.canon
    if canon_path.is_file():
        nodes.add(canon_rel)
        try:
            raw = yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            raw = {}
        for ref in _iter_canon_refs(raw):
            resolved = _resolve(root, canon_rel, ref, anchor="root")
            if isinstance(resolved, _SkipType):
                continue
            if resolved is None:
                edges.append(Edge(src=canon_rel, dst=ref, kind="canon_ref"))
            else:
                # v0.5.8 (Lens 16 P0-SE1-perf): only add to ``nodes`` when
                # the resolved target actually exists. This makes
                # ``Graph.nodes`` the single source of truth for
                # "exists on disk", letting SE1 skip per-edge stat(2).
                if (root / resolved).is_file():
                    nodes.add(resolved)
                edges.append(Edge(src=canon_rel, dst=resolved, kind="canon_ref"))

    # --- 2) note frontmatter refs + markdown links in notes ----------------
    notes_dir = ctx.substrate.paths.notes
    for md in _iter_files(notes_dir, {".md"}):
        rel = _rel(root, md)
        nodes.add(rel)
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        # Frontmatter references
        try:
            note = parse_note(text)
            refs = note.references
        except Exception:
            refs = ()
        for ref in refs:
            resolved = _resolve(root, rel, ref, anchor="root")
            if isinstance(resolved, _SkipType):
                continue
            if resolved is None:
                edges.append(Edge(src=rel, dst=ref, kind="note_ref"))
            else:
                if (root / resolved).is_file():
                    nodes.add(resolved)
                edges.append(Edge(src=rel, dst=resolved, kind="note_ref"))
        # Markdown body links
        try:
            body = parse_note(text).body
        except Exception:
            body = text
        for link in _iter_markdown_links(body):
            resolved = _resolve(root, rel, link)
            if isinstance(resolved, _SkipType):
                continue
            if resolved is None:
                edges.append(Edge(src=rel, dst=link, kind="markdown_link"))
            else:
                if (root / resolved).is_file():
                    nodes.add(resolved)
                edges.append(Edge(src=rel, dst=resolved, kind="markdown_link"))

    # --- 3) markdown links in docs/ + entry-point --------------------------
    docs_dir = ctx.substrate.paths.docs
    candidate_files: list[Path] = list(_iter_files(docs_dir, {".md"}))
    entry = ctx.substrate.root / ctx.substrate.canon.entry_point
    if entry.is_file():
        candidate_files.append(entry)

    for f in candidate_files:
        rel = _rel(root, f)
        nodes.add(rel)
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for link in _iter_markdown_links(text):
            resolved = _resolve(root, rel, link)
            if isinstance(resolved, _SkipType):
                continue
            if resolved is None:
                edges.append(Edge(src=rel, dst=link, kind="markdown_link"))
            else:
                if (root / resolved).is_file():
                    nodes.add(resolved)
                edges.append(Edge(src=rel, dst=resolved, kind="markdown_link"))

    # --- 4) src/**/*.py — imports + docstring doc refs --------------------
    # Governed by ``graph_src.walk_src_graph``. No-op for substrates
    # that have no ``src/`` directory.
    src_walk = walk_src_graph(ctx.substrate.root)
    for node in src_walk.nodes:
        nodes.add(node)
    for src_rel, dst_rel in src_walk.import_edges:
        # Import targets come from ``_module_to_path`` which only
        # returns paths for files that exist. Still, guard the
        # nodes.add with an ``is_file`` so the invariant "nodes is
        # the set of existing files" holds even if a caller later
        # supplies a pre-computed walker result from a different
        # tree state.
        if (ctx.substrate.root / dst_rel).is_file():
            nodes.add(dst_rel)
        edges.append(Edge(src=src_rel, dst=dst_rel, kind="import"))
    for src_rel, dst_rel in src_walk.doc_edges:
        # doc edges may point to a file that exists or may be dangling
        # (e.g. a docstring references a doctrine page we haven't
        # written yet). Only add the node when it resolves; otherwise
        # leave the edge but not the node so SE1 can surface the
        # dangling edge in the same way it does for markdown links.
        resolved_path = (ctx.substrate.root / dst_rel).resolve()
        try:
            resolved_path.relative_to(ctx.substrate.root.resolve())
            if resolved_path.is_file():
                nodes.add(dst_rel)
        except (ValueError, OSError):
            pass
        edges.append(Edge(src=src_rel, dst=dst_rel, kind="code_doc_ref"))

    return Graph(nodes=frozenset(nodes), edges=tuple(edges))


def build_graph(ctx: MycoContext, *, use_cache: bool = True) -> Graph:
    """Scan the substrate and return a :class:`Graph` snapshot.

    When ``use_cache`` is True (the default) this consults
    ``.myco_state/graph.json`` first and reuses it when the canon +
    ``src/`` fingerprint still matches. On cache miss (missing file,
    stale fingerprint, corrupt JSON) it falls through to a fresh scan
    and writes the cache back.

    When ``use_cache`` is False, always rebuild. The cache file is
    left untouched — this is the knob tests reach for when they need
    a deterministic fresh build and don't care about write-back.

    The signature is backward-compatible with the pre-v0.5.5
    ``build_graph(ctx)`` call — ``use_cache`` is kwarg-only.
    """
    substrate = ctx.substrate

    if not use_cache:
        return _build_graph_uncached(ctx)

    cache_path = substrate.paths.graph_cache
    current_fp = _canon_fingerprint(substrate)

    loaded = load_persisted_graph(cache_path)
    if loaded is not None:
        graph, cached_fp = loaded
        if cached_fp == current_fp:
            return graph
        # Fingerprint drifted — fall through to rebuild and overwrite.

    graph = _build_graph_uncached(ctx)
    try:
        persist_graph(graph, cache_path, fingerprint=current_fp)
    except OSError:
        # Best-effort persistence: on a read-only filesystem (e.g. a
        # zipped test distribution) the rebuild still yields a correct
        # graph; we just won't have a cache next time.
        pass
    return graph
