"""``myco perfuse`` — report graph health.

At Stage B.6 this is a **report-only** subsystem. L2 doctrine forbids
auto-edit: perfuse surfaces orphans, dangling refs, and human-readable
proposals; humans do the editing. The ``dry_run`` flag is accepted for
CLI parity (future stages may activate a write path) but has no effect
here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Mapping

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

from .graph import (
    Edge,
    Graph,
    _build_graph_uncached,
    _canon_fingerprint,
    load_persisted_graph,
    persist_graph,
)

__all__ = ["perfuse", "run", "Scope"]


Scope = Literal["canon", "notes", "docs", "all"]
_VALID_SCOPES: frozenset[str] = frozenset({"canon", "notes", "docs", "all"})


def _in_scope(path: str, scope: Scope) -> bool:
    if scope == "all":
        return True
    if scope == "canon":
        return path == "_canon.yaml"
    if scope == "notes":
        return path.startswith("notes/")
    if scope == "docs":
        return path.startswith("docs/") or path == "MYCO.md"
    return False


def _edge_in_scope(edge: Edge, scope: Scope) -> bool:
    return _in_scope(edge.src, scope)


def _dangling(graph: Graph, root: Path, scope: Scope) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    root_r = root.resolve()
    for e in graph.edges:
        if not _edge_in_scope(e, scope):
            continue
        # External-ish dst (e.g. URLs) left as raw; check existence only
        # if it resolves to something under root.
        candidate = root_r / e.dst
        if not candidate.exists():
            out.append((e.src, e.dst))
    return out


def _orphans(graph: Graph, scope: Scope) -> list[str]:
    # A node is an orphan if it is a note/doc with no *incoming* edges.
    # Canon and entry-point are never orphans by definition.
    referenced: set[str] = {e.dst for e in graph.edges}
    orphans: list[str] = []
    for n in graph.nodes:
        if n == "_canon.yaml" or n == "MYCO.md":
            continue
        if not _in_scope(n, scope):
            continue
        # Only treat notes/ and docs/ as orphan candidates.
        if not (n.startswith("notes/") or n.startswith("docs/")):
            continue
        if n not in referenced:
            orphans.append(n)
    return sorted(orphans)


def _proposals(
    orphans: list[str], dangling: list[tuple[str, str]]
) -> list[str]:
    props: list[str] = []
    for o in orphans:
        props.append(f"orphan: consider linking {o} from canon or an index doc")
    for src, dst in dangling:
        props.append(f"dangling: {src} references missing {dst}")
    return props


def _build_graph_with_cache_info(ctx: MycoContext) -> tuple[Graph, bool]:
    """Build the graph and report whether the cache hit.

    Returns ``(graph, cached)``. Cache hits skip the scan + write-back
    entirely; misses run the full scan and persist. This mirrors the
    logic inside :func:`build_graph` but exposes the hit/miss signal
    that :func:`perfuse` wants to surface to callers (v0.5.5 MAJOR-J).
    """
    substrate = ctx.substrate
    cache_path = substrate.paths.graph_cache
    current_fp = _canon_fingerprint(substrate)
    loaded = load_persisted_graph(cache_path)
    if loaded is not None:
        graph, cached_fp = loaded
        if cached_fp == current_fp:
            return graph, True
    graph = _build_graph_uncached(ctx)
    try:
        persist_graph(graph, cache_path, fingerprint=current_fp)
    except OSError:
        pass
    return graph, False


def _count_src_nodes(graph: Graph) -> int:
    """Count graph nodes whose path starts with ``src/``.

    This is the coverage signal for the v0.5.5 MAJOR-F rollout: a
    substrate whose ``perfuse`` report has ``src_node_count == 0`` is
    either a pure-doctrine substrate (by design) or a code substrate
    where the src walker didn't engage (bug). The single number is
    cheap to compute and diff across runs.
    """
    return sum(1 for n in graph.nodes if n.startswith("src/"))


def perfuse(
    *,
    ctx: MycoContext,
    scope: Scope = "all",
    dry_run: bool = False,  # noqa: ARG001 — accepted for CLI parity
) -> Result:
    """Scan the substrate and return a health report.

    Payload shape::

        {
            "scope": <scope>,
            "orphans": list[str],
            "dangling": list[[src, dst]],
            "proposals": list[str],
            "node_count": int,
            "edge_count": int,
            "src_node_count": int,   # v0.5.5: nodes under src/
            "cached": bool,          # v0.5.5: graph came from persisted cache
        }
    """
    if scope not in _VALID_SCOPES:
        raise UsageError(
            f"invalid perfuse scope {scope!r}: "
            f"must be one of {sorted(_VALID_SCOPES)}"
        )

    graph, cached = _build_graph_with_cache_info(ctx)
    dangling = _dangling(graph, ctx.substrate.root, scope)
    orphans = _orphans(graph, scope)
    proposals = _proposals(orphans, dangling)

    return Result(
        exit_code=0,
        payload={
            "scope": scope,
            "orphans": tuple(orphans),
            "dangling": tuple((s, d) for s, d in dangling),
            "proposals": tuple(proposals),
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "src_node_count": _count_src_nodes(graph),
            "cached": cached,
        },
    )


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    scope_raw = args.get("scope") or "all"
    scope = str(scope_raw)
    if scope not in _VALID_SCOPES:
        raise UsageError(
            f"invalid perfuse scope {scope!r}: "
            f"must be one of {sorted(_VALID_SCOPES)}"
        )
    dry_run = bool(args.get("dry_run", False))
    return perfuse(ctx=ctx, scope=scope, dry_run=dry_run)  # type: ignore[arg-type]
