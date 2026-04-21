"""``myco digest <note-id>`` — promote one note by id.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md``
§ "Per-note promotion" (the single-id path; assimilate is the bulk path).

Idempotent on an already-integrated note: if the id resolves to an
existing ``notes/integrated/n_<id>.md``, returns exit 0 with
``status: "already_integrated"``.
"""

from __future__ import annotations

from collections.abc import Mapping

from myco.core.context import MycoContext, Result
from myco.core.errors import UsageError

from .pipeline import promote_to_integrated

__all__ = ["digest_one", "run"]


def _normalize_id(note_id: str) -> str:
    """Strip an optional ``n_`` integrated-prefix so callers can use either form."""
    return note_id[2:] if note_id.startswith("n_") else note_id


def digest_one(
    *,
    ctx: MycoContext,
    note_id: str,
    dry_run: bool = False,
) -> dict[str, object]:
    """Promote a single note by ``note_id`` (filename stem, with or without ``n_``)."""
    stem = _normalize_id(note_id)
    raw_path = ctx.substrate.paths.notes / "raw" / f"{stem}.md"
    integrated_path = ctx.substrate.paths.notes / "integrated" / f"n_{stem}.md"

    if integrated_path.is_file():
        return {
            "status": "already_integrated",
            "path": str(integrated_path),
            "dry_run": dry_run,
            "note_id": stem,
        }

    if not raw_path.is_file():
        raise UsageError(
            f"unknown note id: {note_id} (looked for {raw_path} and {integrated_path})"
        )

    target = promote_to_integrated(ctx=ctx, raw_path=raw_path, dry_run=dry_run)
    return {
        "status": "dry_run" if dry_run else "promoted",
        "path": str(target),
        "dry_run": dry_run,
        "note_id": stem,
    }


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: promote a single raw note by id.

    Idempotent on already-integrated notes (returns ``status:
    "already_integrated"`` without raising). ``dry_run=True``
    previews the target path without moving bytes.
    """
    note_id = str(args.get("note_id") or args.get("note-id") or "")
    if not note_id:
        raise UsageError("digest requires a note-id")
    dry_run = bool(args.get("dry_run", False))
    outcome = digest_one(ctx=ctx, note_id=note_id, dry_run=dry_run)
    return Result(exit_code=0, payload=outcome)
