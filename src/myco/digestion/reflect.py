"""``myco reflect`` — bulk-promote raw notes.

With ``--all`` (the default for the command), every file under
``notes/raw/*.md`` is promoted. With ``--note <id>`` only one note is
promoted. A missing ``notes/raw/`` directory yields zero promotions.

Each promotion that raises a recoverable error (bad frontmatter,
unresolved reference, existing integrated target) is recorded in the
``errors`` list of the payload; the reflect call itself still returns
exit 0 unless *every* candidate errored, in which case the caller gets
``exit_code = 1`` so CI gates notice. This matches the L1 "high"
exit semantics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from myco.core.context import MycoContext, Result
from myco.core.errors import MycoError

from .digest import digest_one

__all__ = ["reflect", "run"]


def _list_raw(ctx: MycoContext) -> list[Path]:
    raw = ctx.substrate.paths.notes / "raw"
    if not raw.is_dir():
        return []
    return sorted(p for p in raw.glob("*.md") if p.is_file())


def reflect(*, ctx: MycoContext, note_id: str | None = None) -> dict[str, object]:
    """Promote raw notes.

    When ``note_id`` is ``None``, all raw notes are considered.
    Otherwise only the specified id. Errors are collected per-note;
    the overall call succeeds unless every candidate errors.
    """
    if note_id is not None:
        outcomes: list[dict[str, object]] = []
        errors: list[dict[str, str]] = []
        try:
            outcomes.append(digest_one(ctx=ctx, note_id=note_id))
        except MycoError as exc:
            errors.append({"note_id": note_id, "error": str(exc)})
        return {
            "promoted": sum(1 for o in outcomes if o.get("status") == "promoted"),
            "already_integrated": sum(
                1 for o in outcomes if o.get("status") == "already_integrated"
            ),
            "errors": errors,
            "outcomes": outcomes,
        }

    raw_paths = _list_raw(ctx)
    outcomes_all: list[dict[str, object]] = []
    errors_all: list[dict[str, str]] = []
    for path in raw_paths:
        stem = path.stem
        try:
            outcomes_all.append(digest_one(ctx=ctx, note_id=stem))
        except MycoError as exc:
            errors_all.append({"note_id": stem, "error": str(exc)})

    return {
        "promoted": sum(1 for o in outcomes_all if o.get("status") == "promoted"),
        "already_integrated": sum(
            1 for o in outcomes_all if o.get("status") == "already_integrated"
        ),
        "errors": errors_all,
        "outcomes": outcomes_all,
    }


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    note_id = args.get("note_id") or args.get("note")
    note_id_str = str(note_id) if note_id else None
    summary = reflect(ctx=ctx, note_id=note_id_str)

    # Exit 1 only when we tried and *every* candidate errored.
    total = len(summary["outcomes"]) + len(summary["errors"])  # type: ignore[arg-type]
    exit_code = 1 if (total > 0 and not summary["outcomes"]) else 0
    return Result(exit_code=exit_code, payload=summary)
