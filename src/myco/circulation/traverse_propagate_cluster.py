"""Cluster module — v0.8.8 max-aggressive merge of traverse, propagate.

=== traverse ===
``myco perfuse`` — report graph health.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
§ "Traversal" — the report-only read path over the mycelium graph.

At Stage B.6 this is a **report-only** subsystem. L2 doctrine forbids
auto-edit: perfuse surfaces orphans, dangling refs, and human-readable
proposals; humans do the editing. The ``dry_run`` flag is accepted for
CLI parity (future stages may activate a write path) but has no effect
here.

=== propagate ===
``myco propagate`` — push integrated/distilled notes to downstream substrate(s).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
§ "Propagation" — the cross-substrate edge that federates basins
of knowledge without merging them. The federation discipline that
governs cross-substrate publication (peer-list, transactional
fan-out, contract-version compat) is codified at
``docs/architecture/L2_DOCTRINE/release_discipline.md`` § "Rule 5"
(v0.7.10 omnibus).

Redefined per §9 E4: propagate publishes notes from ``src_ctx`` into
each ``dst_root``'s ``notes/raw/`` inbox, stamping source-trace
frontmatter so the downstream substrate(s) can reason about
provenance. This is not file sync and not bidirectional.

v0.7.10: extended from single-peer to **N-peer fan-out** to honour the
L0 P5 mycelium-graph promise (which spans federated substrates plural,
not a 1:1 edge). Callers pass either ``dst_root`` (the legacy scalar,
sugar for a 1-element list) OR ``dst_roots`` (an explicit list of peer
roots). The single-peer call shape continues to work unchanged.

Discipline:

- Transactional across **all peers**: collect every peer's target
  paths first, verify every peer's canon + every peer's inbox is
  collision-free, then write to every peer's inbox. A single failure
  on any peer aborts the whole batch — no partial writes anywhere.
- Contract-version check per peer: a major mismatch on any peer
  raises ``ContractError`` (with the offending peer path) before
  any writes; minor/patch/tag diffs accumulate into
  ``payload["compat_warnings"]``.
- A single ``now`` is used for all notes across all peers in one
  call, so ``dry_run`` and the real run produce identical output for
  the same inputs.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from myco.core.canon import load_canon
from myco.core.identity_cluster import (
    ContractError,
    ContractVersion,
    MycoContext,
    MycoError,
    Result,
    UsageError,
)
from myco.core.io_cluster import atomic_utf8_write, bounded_read_text
from myco.digestion.cluster import Note, parse_note, render_note

from .graph import (
    Edge,
    Graph,
    _build_graph_uncached,
    _canon_fingerprint,
    load_persisted_graph,
    persist_graph,
)

# =========================================================================
# === traverse — formerly traverse.py
# =========================================================================

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
    referenced: set[str] = {e.dst for e in graph.edges}
    orphans: list[str] = []
    for n in graph.nodes:
        if n in (canon_rel, entry_point):
            continue
        if not _in_scope(n, scope, entry_point, canon_rel, notes_dir, docs_dir):
            continue
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
            return (graph, True)
    graph = _build_graph_uncached(ctx)
    try:
        persist_graph(graph, cache_path, fingerprint=current_fp)
    except OSError:
        pass
    return (graph, False)


def _count_src_nodes(graph: Graph) -> int:
    """Count graph nodes whose path starts with ``src/``.

    This is the coverage signal for the v0.5.5 MAJOR-F rollout: a
    substrate whose ``perfuse`` report has ``src_node_count == 0`` is
    either a pure-doctrine substrate (by design) or a code substrate
    where the src walker didn't engage (bug). The single number is
    cheap to compute and diff across runs.
    """
    return sum(1 for n in graph.nodes if n.startswith("src/"))


def perfuse(*, ctx: MycoContext, scope: Scope = "all", dry_run: bool = False) -> Result:
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
    entry_point = ctx.substrate.canon.entry_point
    canon_rel = ctx.substrate.paths.canon.relative_to(
        ctx.substrate.root.resolve()
    ).as_posix()
    notes_dir = ctx.substrate.paths.notes_dir
    docs_dir = ctx.substrate.paths.docs_dir
    dangling = _dangling(
        graph, ctx.substrate.root, scope, entry_point, canon_rel, notes_dir, docs_dir
    )
    orphans = _orphans(graph, scope, entry_point, canon_rel, notes_dir, docs_dir)
    proposals = _proposals(orphans, dangling)
    return Result(
        exit_code=0,
        payload={
            "scope": scope,
            "orphans": tuple(orphans),
            "dangling": tuple(((s, d) for s, d in dangling)),
            "proposals": tuple(proposals),
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "src_node_count": _count_src_nodes(graph),
            "cached": cached,
        },
    )


def traverse_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
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


# =========================================================================
# === propagate — formerly propagate.py
# =========================================================================

Select = Literal["integrated", "distilled", "both"]

_VALID_SELECT: frozenset[str] = frozenset({"integrated", "distilled", "both"})


def _iter_sources(ctx: MycoContext, select: Select) -> list[Path]:
    notes_dir = ctx.substrate.paths.notes
    out: list[Path] = []
    if select in ("integrated", "both"):
        d = notes_dir / "integrated"
        if d.is_dir():
            out.extend(sorted(p for p in d.glob("n_*.md") if p.is_file()))
    if select in ("distilled", "both"):
        d = notes_dir / "distilled"
        if d.is_dir():
            out.extend(sorted(p for p in d.glob("d_*.md") if p.is_file()))
    return out


def _compat_warnings(src: ContractVersion, dst: ContractVersion) -> list[str]:
    warnings: list[str] = []
    if src.minor != dst.minor:
        warnings.append(f"minor version mismatch: src={src} dst={dst}")
    elif src.patch != dst.patch:
        warnings.append(f"patch version mismatch: src={src} dst={dst}")
    elif (src._has_final, src._tag) != (dst._has_final, dst._tag):
        warnings.append(f"pre-release tag mismatch: src={src} dst={dst}")
    return warnings


def _stamp_note(
    note: Note, *, src_substrate_id: str, commit: str | None, now_iso: str
) -> Note:
    new_fm: MutableMapping[str, Any] = dict(note.frontmatter)
    commit_str = commit if commit else "unknown"
    new_fm["source"] = f"{src_substrate_id}@{commit_str}"
    new_fm["ingest_state"] = "raw"
    new_fm["stage"] = "raw"
    new_fm["propagated_at"] = now_iso
    return Note(frontmatter=new_fm, body=note.body)


def _normalize_dst_roots(
    dst_root: Path | None, dst_roots: Sequence[Path] | Path | None
) -> list[Path]:
    """Resolve the (legacy ``dst_root`` | new ``dst_roots``) duality
    into a single canonical list of peer roots.

    Exactly one of the two must be supplied. ``dst_roots`` accepts
    either a list of paths (the canonical N-peer shape) or a bare
    ``Path`` (sugar treated as ``[Path]``). The legacy ``dst_root``
    keyword remains a scalar ``Path`` for backwards compatibility
    with v0.5.x-v0.7.5 callers and the existing test suite.

    Raises:
        UsageError: both or neither were supplied; or ``dst_roots``
            was provided as an empty sequence.
    """
    if dst_root is not None and dst_roots is not None:
        raise UsageError(
            "propagate: pass exactly one of dst_root (legacy) or dst_roots (N-peer); both were supplied"
        )
    if dst_root is None and dst_roots is None:
        raise UsageError(
            "propagate: pass exactly one of dst_root (legacy) or dst_roots (N-peer); neither was supplied"
        )
    if dst_root is not None:
        return [dst_root]
    if isinstance(dst_roots, Path):
        return [dst_roots]
    roots = list(dst_roots) if dst_roots is not None else []
    if not roots:
        raise UsageError(
            "propagate: dst_roots must be a non-empty sequence of peer paths"
        )
    return roots


def propagate(
    *,
    src_ctx: MycoContext,
    dst_root: Path | None = None,
    dst_roots: Sequence[Path] | Path | None = None,
    select: Select = "integrated",
    commit: str | None = None,
    dry_run: bool = False,
    now: datetime | None = None,
) -> Result:
    """Publish notes from ``src_ctx`` into one or more downstream peers' inboxes.

    Exactly one of ``dst_root`` (legacy single-peer scalar) or
    ``dst_roots`` (the v0.7.10 N-peer shape; accepts a list of paths
    or — as sugar — a bare ``Path``) must be supplied. Single-peer
    callers should keep using ``dst_root=`` unchanged; N-peer callers
    should pass ``dst_roots=[peer_a, peer_b, peer_c]``.

    The fan-out is **transactional across all peers**:

    1. Every peer's ``_canon.yaml`` is loaded and contract-MAJOR
       checked first. A single missing canon or major mismatch on
       any peer raises ``ContractError`` before any plan is computed.
    2. The same source-note set is then planned (read + stamped)
       into every peer's ``notes/raw/`` inbox. A collision check is
       performed per peer; a collision on any peer raises
       ``ContractError`` (citing the peer path) before any writes.
    3. Only when all peers pass do the writes proceed. They are
       atomic per file but not cross-process atomic: a system crash
       mid-fan-out can leave some peers written and others not.
       Re-running propagate is safe — already-written peers will
       collide and the verb will refuse to overwrite.

    Returns a ``Result`` whose payload contains:

    - ``dst_roots`` — tuple of resolved POSIX-style peer paths
      (always present; is ``(<single-peer>,)`` when called via the
      legacy ``dst_root=`` shape).
    - ``dst_root`` — the FIRST peer's resolved path (kept as a
      backwards-compatibility convenience for callers that read the
      pre-v0.7.10 scalar field).
    - ``propagated`` — tuple of POSIX-style relative paths, one per
      (peer, source-note) write, in peer-then-source order. Each
      entry is rooted on its peer (``notes/raw/<stem>.md``); for
      multi-peer calls the same stem appears once per peer.
    - ``count`` — total writes across all peers (==
      ``len(propagated)``); for a single-peer call this matches the
      pre-v0.7.10 semantics (number of source notes).
    - ``compat_warnings`` — flattened tuple of non-major
      mismatches across all peers, each prefixed with the peer's
      path so multi-peer warnings remain distinguishable.

    Raises:
        UsageError: invalid ``select``, or both/neither of
            ``dst_root`` / ``dst_roots`` supplied.
        ContractError: any peer's canon missing, any peer's
            major-version mismatch, any peer's inbox collision, or
            an unreadable source note.
    """
    if select not in _VALID_SELECT:
        raise UsageError(
            f"invalid propagate select {select!r}: must be one of {sorted(_VALID_SELECT)}"
        )
    raw_peers = _normalize_dst_roots(dst_root, dst_roots)
    peers: list[Path] = [p.resolve() for p in raw_peers]
    try:
        src_ver = ContractVersion.parse(src_ctx.substrate.canon.contract_version)
    except ValueError as exc:
        raise ContractError(f"unparseable src contract_version: {exc}") from exc
    compat_warnings: list[str] = []
    from myco.core.io_cluster import find_substrate_canon, has_substrate

    for peer in peers:
        if not has_substrate(peer):
            raise ContractError(
                f"dst is not a Myco substrate (no .myco/canon.yaml or _canon.yaml): {peer}"
            )
        peer_canon_path = find_substrate_canon(peer)
        peer_canon = load_canon(peer_canon_path)
        try:
            peer_ver = ContractVersion.parse(peer_canon.contract_version)
        except ValueError as exc:
            raise ContractError(
                f"unparseable contract_version for peer {peer}: {exc}"
            ) from exc
        if src_ver.major != peer_ver.major:
            raise ContractError(
                f"contract-version major mismatch for peer {peer}: src={src_ver} dst={peer_ver}"
            )
        for w in _compat_warnings(src_ver, peer_ver):
            compat_warnings.append(f"{peer}: {w}")
    sources = _iter_sources(src_ctx, select)
    now = now or datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    src_substrate_id = src_ctx.substrate.canon.substrate_id or "unknown"
    stamped_payloads: list[tuple[str, str]] = []
    for src_path in sources:
        try:
            text = bounded_read_text(src_path)
        except (OSError, MycoError) as exc:
            raise ContractError(f"failed to read {src_path}: {exc}") from exc
        note = parse_note(text)
        stamped = _stamp_note(
            note, src_substrate_id=src_substrate_id, commit=commit, now_iso=now_iso
        )
        dst_name = src_path.name
        if dst_name.startswith("n_") or dst_name.startswith("d_"):
            dst_name = dst_name[2:]
        stamped_payloads.append((dst_name, render_note(stamped)))
    per_peer_plan: list[tuple[Path, list[tuple[Path, str]]]] = []
    for peer in peers:
        inbox = peer / "notes" / "raw"
        plan: list[tuple[Path, str]] = []
        peer_collisions: list[str] = []
        for dst_name, rendered in stamped_payloads:
            target = inbox / dst_name
            if target.exists():
                peer_collisions.append(dst_name)
            plan.append((target, rendered))
        if peer_collisions:
            raise ContractError(
                f"propagate collision(s) in dst inbox for peer {peer}: {sorted(set(peer_collisions))}; duplicate-by-id is an error"
            )
        per_peer_plan.append((peer, plan))
    propagated: list[str] = []
    if not dry_run:
        for peer, plan in per_peer_plan:
            inbox = peer / "notes" / "raw"
            inbox.mkdir(parents=True, exist_ok=True)
            for target, rendered in plan:
                atomic_utf8_write(target, rendered)
                propagated.append(str(target.relative_to(peer)).replace("\\", "/"))
    else:
        for peer, plan in per_peer_plan:
            for target, _ in plan:
                propagated.append(str(target.relative_to(peer)).replace("\\", "/"))
    dst_roots_tuple: tuple[str, ...] = tuple(str(p) for p in peers)
    total_count = sum((len(plan) for _, plan in per_peer_plan))
    return Result(
        exit_code=0,
        payload={
            "select": select,
            "src_substrate_id": src_substrate_id,
            "dst_roots": dst_roots_tuple,
            "dst_root": dst_roots_tuple[0],
            "count": total_count,
            "propagated": tuple(propagated),
            "compat_warnings": tuple(compat_warnings),
            "dry_run": dry_run,
            "commit": commit if commit else "unknown",
        },
    )


def propagate_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: propagate notes to one or more downstream substrates.

    Dispatches on ``args["dst"]`` (legacy single peer) OR ``args["dsts"]``
    (v0.7.10 N-peer; a list of paths). Exactly one must be provided.
    Other args: ``args["select"]`` (integrated / distilled / both),
    ``args["commit"]``, ``args["dry_run"]``. Writes are transactional
    across all peers: collect → verify-all → write-all or raise.
    """
    dst_raw = args.get("dst")
    dsts_raw = args.get("dsts")
    if dst_raw and dsts_raw:
        raise UsageError("propagate: pass exactly one of dst (single) or dsts (N-peer)")
    if not dst_raw and (not dsts_raw):
        raise UsageError("propagate requires a dst path (or dsts list)")
    dst_root: Path | None = None
    dst_roots: list[Path] | None = None
    if dst_raw:
        dst_root = Path(str(dst_raw))
    elif isinstance(dsts_raw, (str, bytes)):
        dst_roots = [Path(str(dsts_raw))]
    elif isinstance(dsts_raw, Sequence):
        dst_roots = [Path(str(p)) for p in dsts_raw]
    else:
        raise UsageError(
            f"propagate: dsts must be a list of paths, got {type(dsts_raw).__name__}"
        )
    select_raw = str(args.get("select") or "integrated")
    if select_raw not in _VALID_SELECT:
        raise UsageError(
            f"invalid propagate select {select_raw!r}: must be one of {sorted(_VALID_SELECT)}"
        )
    commit = args.get("commit")
    commit_str = str(commit) if commit else None
    dry_run = bool(args.get("dry_run", False))
    return propagate(
        src_ctx=ctx,
        dst_root=dst_root,
        dst_roots=dst_roots,
        select=select_raw,  # type: ignore[arg-type]
        commit=commit_str,
        dry_run=dry_run,
    )
