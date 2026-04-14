"""Cross-reference graph for a substrate.

Per L2 ``circulation.md`` and the Stage B.6 craft, the graph is built
on demand from three sources:

1. ``_canon.yaml`` — any leaf string under a key ending in ``_ref``.
2. Note frontmatter — ``references:`` lists in ``notes/**/*.md``.
3. Markdown links — ``[text](relative/path)`` in notes, ``docs/``, and
   the entry-point file (fenced code blocks are skipped).

Nodes are substrate-relative path strings (POSIX-style). Edges carry a
``kind`` tag: ``canon_ref``, ``note_ref``, or ``markdown_link``.

The graph is a read-only snapshot — callers rebuild it on demand.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Literal, Mapping

import yaml

from myco.core.context import MycoContext
from myco.digestion.pipeline import parse_note

__all__ = ["Edge", "Graph", "EdgeKind", "build_graph"]


EdgeKind = Literal["canon_ref", "note_ref", "markdown_link"]

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
    if len(lower) >= 2 and lower[1] == ":":
        return True
    return False


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
            sub_path = path + (str(key),)
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


_SKIP = object()  # sentinel: external ref, drop silently


def _resolve(
    root: Path, owner_rel: str, ref: str, *, anchor: str = "file"
) -> str | object | None:
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
    if anchor == "root":
        base = root
    else:
        base = (root / owner_rel).parent
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


# --- builder ---------------------------------------------------------------


def build_graph(ctx: MycoContext) -> Graph:
    """Scan the substrate and return a fresh :class:`Graph` snapshot."""
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
            if resolved is _SKIP:
                continue
            if resolved is None:
                edges.append(Edge(src=canon_rel, dst=ref, kind="canon_ref"))
            else:
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
            if resolved is _SKIP:
                continue
            if resolved is None:
                edges.append(Edge(src=rel, dst=ref, kind="note_ref"))
            else:
                nodes.add(resolved)
                edges.append(Edge(src=rel, dst=resolved, kind="note_ref"))
        # Markdown body links
        try:
            body = parse_note(text).body
        except Exception:
            body = text
        for link in _iter_markdown_links(body):
            resolved = _resolve(root, rel, link)
            if resolved is _SKIP:
                continue
            if resolved is None:
                edges.append(Edge(src=rel, dst=link, kind="markdown_link"))
            else:
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
            if resolved is _SKIP:
                continue
            if resolved is None:
                edges.append(Edge(src=rel, dst=link, kind="markdown_link"))
            else:
                nodes.add(resolved)
                edges.append(Edge(src=rel, dst=resolved, kind="markdown_link"))

    return Graph(nodes=frozenset(nodes), edges=tuple(edges))
