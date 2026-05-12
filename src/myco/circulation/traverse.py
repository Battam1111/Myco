"""``myco perfuse`` — report graph health.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
§ "Traversal" — the report-only read path over the mycelium graph.

At Stage B.6 this is a **report-only** subsystem. L2 doctrine forbids
auto-edit: perfuse surfaces orphans, dangling refs, and human-readable
proposals; humans do the editing. The ``dry_run`` flag is accepted for
CLI parity (future stages may activate a write path) but has no effect
here.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

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


def _in_scope(
    path: str,
    scope: Scope,
    entry_point: str = "MYCO.md",
    canon_rel: str = "_canon.yaml",
    notes_dir: str = "notes",
    docs_dir: str = "docs",
) -> bool:
    # v0.8.4 root-cleanup (2026-05-12): entry_point + canon_rel are
    # the agent entry page + canon path read from substrate (defaults
    # = legacy; Myco-self uses ".myco/MYCO.md" + ".myco/canon.yaml").
    # v0.8.5: notes_dir / docs_dir parameters added so scope filtering
    # follows canon-configured paths.notes / paths.docs (Myco-self
    # uses ".myco/notes" + ".docs"; downstream defaults to "notes" +
    # "docs"). Before this fix the hardcoded `path.startswith("docs/")`
    # check returned False for every Myco-self node (which begin with
    # `.docs/`), silently dropping the entire docs-scope filter.
    if scope == "all":
        return True
    if scope == "canon":
        return path == canon_rel
    if scope == "notes":
        return path.startswith(notes_dir + "/")
    if scope == "docs":
        return path.startswith(docs_dir + "/") or path == entry_point
    return False


def _edge_in_scope(
    edge: Edge,
    scope: Scope,
    entry_point: str = "MYCO.md",
    canon_rel: str = "_canon.yaml",
    notes_dir: str = "notes",
    docs_dir: str = "docs",
) -> bool:
    return _in_scope(edge.src, scope, entry_point, canon_rel, notes_dir, docs_dir)


def _dangling(
    graph: Graph,
    root: Path,
    scope: Scope,
    entry_point: str = "MYCO.md",
    canon_rel: str = "_canon.yaml",
    notes_dir: str = "notes",
    docs_dir: str = "docs",
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    root_r = root.resolve()
    for e in graph.edges:
        if not _edge_in_scope(e, scope, entry_point, canon_rel, notes_dir, docs_dir):
            continue
        # External-ish dst (e.g. URLs) left as raw; check existence only
        # if it resolves to something under root.
        candidate = root_r / e.dst
        if not candidate.exists():
            out.append((e.src, e.dst))
    return out


def _orphans(
    graph: Graph,
    scope: Scope,
    entry_point: str = "MYCO.md",
    canon_rel: str = "_canon.yaml",
    notes_dir: str = "notes",
    docs_dir: str = "docs",
) -> list[str]:
    # A node is an orphan if it is a note/doc with no *incoming* edges.
    # Canon and entry-point are never orphans by definition.
    referenced: set[str] = {e.dst for e in graph.edges}
    orphans: list[str] = []
    for n in graph.nodes:
        if n in (canon_rel, entry_point):
            continue
        if not _in_scope(n, scope, entry_point, canon_rel, notes_dir, docs_dir):
            continue
        # Only treat notes/ and docs/ as orphan candidates (resolved via
        # canon-configured prefixes — see _in_scope for v0.8.5 rationale).
        if not (n.startswith(notes_dir + "/") or n.startswith(docs_dir + "/")):
            continue
        if n not in referenced:
            orphans.append(n)
    return sorted(orphans)


def _proposals(orphans: list[str], dangling: list[tuple[str, str]]) -> list[str]:
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
    dry_run: bool = False,
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
            f"invalid perfuse scope {scope!r}: must be one of {sorted(_VALID_SCOPES)}"
        )

    graph, cached = _build_graph_with_cache_info(ctx)
    # v0.8.4 root-cleanup (2026-05-12): pass canon.entry_point + the
    # resolved canon-relative path so the scope filter + orphan
    # exclusion follow the substrate's declared layout (Myco-self uses
    # .myco/MYCO.md + .myco/canon.yaml; downstream defaults to MYCO.md
    # + _canon.yaml unchanged).
    entry_point = ctx.substrate.canon.entry_point
    canon_rel = ctx.substrate.paths.canon.relative_to(
        ctx.substrate.root.resolve()
    ).as_posix()
    # v0.8.5 — pass canon-configured docs_dir / notes_dir so the scope
    # filters in _in_scope() / _dangling() / _orphans() work on
    # substrates whose docs/notes live under hidden prefixes.
    notes_dir = ctx.substrate.paths.notes_dir
    docs_dir = ctx.substrate.paths.docs_dir
    dangling = _dangling(
        graph,
        ctx.substrate.root,
        scope,
        entry_point,
        canon_rel,
        notes_dir,
        docs_dir,
    )
    orphans = _orphans(
        graph,
        scope,
        entry_point,
        canon_rel,
        notes_dir,
        docs_dir,
    )
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
    """Manifest handler: report mycelium-graph health in ``scope``.

    ``scope`` is one of canon / notes / docs / all. Report-only —
    no writes. See L2 circulation.md for the forbidden-auto-edit
    invariant.
    """
    scope_raw = args.get("scope") or "all"
    scope = str(scope_raw)
    if scope not in _VALID_SCOPES:
        raise UsageError(
            f"invalid perfuse scope {scope!r}: must be one of {sorted(_VALID_SCOPES)}"
        )
    dry_run = bool(args.get("dry_run", False))
    return perfuse(ctx=ctx, scope=scope, dry_run=dry_run)  # type: ignore[arg-type]
