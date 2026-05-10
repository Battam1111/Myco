"""``myco propagate`` — push integrated/distilled notes to downstream substrate(s).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
§ "Propagation" — the cross-substrate edge that federates basins
of knowledge without merging them.

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
from myco.core.context import MycoContext, Result
from myco.core.errors import ContractError, MycoError, UsageError
from myco.core.io_atomic import atomic_utf8_write, bounded_read_text
from myco.core.version import ContractVersion
from myco.digestion.pipeline import Note, parse_note, render_note

__all__ = ["propagate", "run", "Select"]


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
    note: Note,
    *,
    src_substrate_id: str,
    commit: str | None,
    now_iso: str,
) -> Note:
    new_fm: MutableMapping[str, Any] = dict(note.frontmatter)
    commit_str = commit if commit else "unknown"
    new_fm["source"] = f"{src_substrate_id}@{commit_str}"
    new_fm["ingest_state"] = "raw"
    new_fm["stage"] = "raw"
    new_fm["propagated_at"] = now_iso
    return Note(frontmatter=new_fm, body=note.body)


def _normalize_dst_roots(
    dst_root: Path | None,
    dst_roots: Sequence[Path] | Path | None,
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
            "propagate: pass exactly one of dst_root (legacy) or dst_roots "
            "(N-peer); both were supplied"
        )
    if dst_root is None and dst_roots is None:
        raise UsageError(
            "propagate: pass exactly one of dst_root (legacy) or dst_roots "
            "(N-peer); neither was supplied"
        )
    if dst_root is not None:
        return [dst_root]
    # dst_roots is not None at this point.
    if isinstance(dst_roots, Path):
        # Scalar Path is sugar for a 1-element list.
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
            f"invalid propagate select {select!r}: "
            f"must be one of {sorted(_VALID_SELECT)}"
        )

    raw_peers = _normalize_dst_roots(dst_root, dst_roots)
    # Resolve every peer eagerly so error messages and the payload
    # report stable absolute paths.
    peers: list[Path] = [p.resolve() for p in raw_peers]

    try:
        src_ver = ContractVersion.parse(src_ctx.substrate.canon.contract_version)
    except ValueError as exc:
        raise ContractError(f"unparseable src contract_version: {exc}") from exc

    # Round 1a: validate every peer's canon BEFORE any plan computation.
    # This honours the N-peer transactional contract — a single bad
    # peer aborts before we even read the source notes.
    compat_warnings: list[str] = []
    for peer in peers:
        peer_canon_path = peer / "_canon.yaml"
        if not peer_canon_path.is_file():
            raise ContractError(f"dst is not a Myco substrate (no _canon.yaml): {peer}")
        peer_canon = load_canon(peer_canon_path)
        try:
            peer_ver = ContractVersion.parse(peer_canon.contract_version)
        except ValueError as exc:
            raise ContractError(
                f"unparseable contract_version for peer {peer}: {exc}"
            ) from exc
        if src_ver.major != peer_ver.major:
            raise ContractError(
                f"contract-version major mismatch for peer {peer}: "
                f"src={src_ver} dst={peer_ver}"
            )
        for w in _compat_warnings(src_ver, peer_ver):
            compat_warnings.append(f"{peer}: {w}")

    sources = _iter_sources(src_ctx, select)
    now = now or datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    src_substrate_id = src_ctx.substrate.canon.substrate_id or "unknown"

    # Round 1b: read + stamp source notes ONCE; the rendered text is
    # peer-independent so we don't redo this work per peer.
    stamped_payloads: list[tuple[str, str]] = []  # (dst_name, rendered_text)
    for src_path in sources:
        try:
            text = bounded_read_text(src_path)
        except (OSError, MycoError) as exc:
            raise ContractError(f"failed to read {src_path}: {exc}") from exc
        note = parse_note(text)
        stamped = _stamp_note(
            note,
            src_substrate_id=src_substrate_id,
            commit=commit,
            now_iso=now_iso,
        )
        # v0.5.8 FIX: strip the n_/d_ tier-prefix so the stem written
        # to dst's notes/raw/ matches what digest_one expects.
        dst_name = src_path.name
        if dst_name.startswith("n_") or dst_name.startswith("d_"):
            dst_name = dst_name[2:]
        stamped_payloads.append((dst_name, render_note(stamped)))

    # Round 2: compute per-peer plans and gather collisions. Plans
    # accumulate before any write so that a collision on peer N
    # cannot leave peers 1..N-1 written.
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
                f"propagate collision(s) in dst inbox for peer {peer}: "
                f"{sorted(set(peer_collisions))}; duplicate-by-id is an error"
            )
        per_peer_plan.append((peer, plan))

    # Round 3: writes (or dry-run report). All collision/canon checks
    # have passed at this point.
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
    total_count = sum(len(plan) for _, plan in per_peer_plan)

    return Result(
        exit_code=0,
        payload={
            "select": select,
            "src_substrate_id": src_substrate_id,
            # v0.7.10 N-peer field — the canonical answer.
            "dst_roots": dst_roots_tuple,
            # Backwards-compat scalar — first peer's resolved path.
            "dst_root": dst_roots_tuple[0],
            "count": total_count,
            "propagated": tuple(propagated),
            "compat_warnings": tuple(compat_warnings),
            "dry_run": dry_run,
            "commit": commit if commit else "unknown",
        },
    )


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
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
    if not dst_raw and not dsts_raw:
        raise UsageError("propagate requires a dst path (or dsts list)")

    dst_root: Path | None = None
    dst_roots: list[Path] | None = None
    if dst_raw:
        dst_root = Path(str(dst_raw))
    else:
        # ``dsts`` may be a list/tuple OR a single string — be liberal
        # in what we accept here so the manifest layer can stay simple.
        if isinstance(dsts_raw, (str, bytes)):
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
            f"invalid propagate select {select_raw!r}: "
            f"must be one of {sorted(_VALID_SELECT)}"
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
