"""``myco propagate`` — push integrated/distilled notes to a downstream substrate.

Redefined per §9 E4: propagate publishes notes from ``src_ctx`` into
``dst_root``'s ``notes/raw/`` inbox, stamping source-trace frontmatter
so the downstream substrate can reason about provenance. This is not
file sync and not bidirectional.

Discipline:

- Transactional: collect target paths first, verify none exist, then
  write all. Duplicate-by-id is a ``ContractError``.
- Contract-version check: major mismatch raises ``ContractError``;
  other diffs are reported in ``payload["compat_warnings"]``.
- A single ``now`` is used for all notes in one call, so ``dry_run``
  and the real run produce identical output for the same inputs.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from myco.core.canon import load_canon
from myco.core.context import MycoContext, Result
from myco.core.errors import ContractError, UsageError
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


def propagate(
    *,
    src_ctx: MycoContext,
    dst_root: Path,
    select: Select = "integrated",
    commit: str | None = None,
    dry_run: bool = False,
    now: datetime | None = None,
) -> Result:
    """Publish notes from ``src_ctx`` into ``dst_root``'s inbox.

    Raises:
        UsageError: invalid ``select``.
        ContractError: dst canon missing or major-version mismatch,
            or a collision in the dst inbox.
    """
    if select not in _VALID_SELECT:
        raise UsageError(
            f"invalid propagate select {select!r}: "
            f"must be one of {sorted(_VALID_SELECT)}"
        )

    dst_root = dst_root.resolve()
    dst_canon_path = dst_root / "_canon.yaml"
    if not dst_canon_path.is_file():
        raise ContractError(f"dst is not a Myco substrate (no _canon.yaml): {dst_root}")
    dst_canon = load_canon(dst_canon_path)

    try:
        src_ver = ContractVersion.parse(src_ctx.substrate.canon.contract_version)
        dst_ver = ContractVersion.parse(dst_canon.contract_version)
    except ValueError as exc:
        raise ContractError(f"unparseable contract_version: {exc}") from exc
    if src_ver.major != dst_ver.major:
        raise ContractError(
            f"contract-version major mismatch: src={src_ver} dst={dst_ver}"
        )
    compat_warnings = _compat_warnings(src_ver, dst_ver)

    sources = _iter_sources(src_ctx, select)
    now = now or datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    src_substrate_id = src_ctx.substrate.canon.substrate_id or "unknown"

    inbox = dst_root / "notes" / "raw"

    # Round 1: compute all targets + stamped payloads.
    plan: list[tuple[Path, str]] = []
    collisions: list[str] = []
    for src_path in sources:
        try:
            text = src_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ContractError(f"failed to read {src_path}: {exc}") from exc
        note = parse_note(text)
        stamped = _stamp_note(
            note,
            src_substrate_id=src_substrate_id,
            commit=commit,
            now_iso=now_iso,
        )
        # v0.5.8 FIX: the source is from notes/integrated/n_<stem>.md
        # or notes/distilled/d_<stem>.md; the canonical raw filename
        # (what digest_one looks for) is notes/raw/<stem>.md without
        # the tier-prefix. Before this fix, dst wrote n_<stem>.md and
        # digest_one stripped the prefix then failed to find the file.
        dst_name = src_path.name
        if dst_name.startswith("n_") or dst_name.startswith("d_"):
            dst_name = dst_name[2:]
        target = inbox / dst_name
        if target.exists():
            collisions.append(dst_name)
        plan.append((target, render_note(stamped)))

    if collisions:
        raise ContractError(
            f"propagate collision(s) in dst inbox: {sorted(set(collisions))}; "
            f"duplicate-by-id is an error"
        )

    propagated: list[str] = []
    if not dry_run:
        inbox.mkdir(parents=True, exist_ok=True)
        for target, rendered in plan:
            target.write_text(rendered, encoding="utf-8", newline="\n")
            propagated.append(str(target.relative_to(dst_root)).replace("\\", "/"))
    else:
        propagated = [
            str(target.relative_to(dst_root)).replace("\\", "/") for target, _ in plan
        ]

    return Result(
        exit_code=0,
        payload={
            "select": select,
            "src_substrate_id": src_substrate_id,
            "dst_root": str(dst_root),
            "count": len(plan),
            "propagated": tuple(propagated),
            "compat_warnings": tuple(compat_warnings),
            "dry_run": dry_run,
            "commit": commit if commit else "unknown",
        },
    )


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    dst_raw = args.get("dst")
    if not dst_raw:
        raise UsageError("propagate requires a dst path")
    dst_root = Path(str(dst_raw))
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
        select=select_raw,  # type: ignore[arg-type]
        commit=commit_str,
        dry_run=dry_run,
    )
