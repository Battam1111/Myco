"""``digestion.reassimilate`` — demote integrated note to raw (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md`` state
machine; v0.6.0 craft §F6 closes the loop allowing today's integrated
to become tomorrow's raw (L0 P4 永恒迭代).

Use case: an integrated note that requires re-marination because the
upstream context shifted (a contract bumped, a related craft landed,
a downstream finding revealed the note's framing was incomplete).
Rather than excrete and lose the audit trail, ``reassimilate`` demotes
the note to ``stage: re_raw`` in ``notes/raw/`` and writes a
``reassimilation_history`` frontmatter entry preserving provenance.

Side effects: moves one file ``notes/integrated/n_<id>.md`` →
``notes/raw/<id>_re<n>.md`` and rewrites frontmatter:

- ``stage`` → ``re_raw``.
- ``reassimilation_history`` (list, append): ``[{from_integrated_at,
  reassimilated_at, reason}]``.

Idempotent: re-running on an already-re-raw note is a no-op.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from typing import Any

from myco.core.context import MycoContext
from myco.core.errors import MycoError
from myco.core.io_atomic import atomic_utf8_write
from myco.core.write_surface import check_write_allowed

from .pipeline import parse_note, render_note

__all__ = ["reassimilate_integrated"]


def reassimilate_integrated(
    ctx: MycoContext,
    note_id: str,
    reason: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Demote an integrated note back to raw with audit trail.

    Args:
        ctx: substrate context.
        note_id: stem of the integrated note (without ``n_`` prefix or
            ``.md`` extension), e.g.
            ``20260420T173825Z_v0-5-8-scope-formation-decision``.
        reason: human/agent-readable reason; recorded in
            ``reassimilation_history``. Empty/whitespace rejected.
        dry_run: if True, compute the move without writing.

    Returns:
        ``{exit_code, status, from_path, to_path, dry_run}`` per the
        v0.6.0 verb-result convention. status one of:
        ``"reassimilated"`` / ``"already_re_raw"`` / ``"not_found"``.

    Raises:
        ``MycoError`` (exit_code 3) on bad note_id or empty reason.
    """
    if not reason or not reason.strip():
        raise MycoError(
            "reassimilate: reason is required (non-empty); "
            "preserves audit trail of why integrated was re-marinated"
        )
    root = ctx.substrate.root
    integrated_path = root / "notes" / "integrated" / f"n_{note_id}.md"
    if not integrated_path.is_file():
        return {
            "exit_code": 3,
            "status": "not_found",
            "from_path": str(integrated_path),
            "to_path": "",
            "dry_run": dry_run,
        }

    text = integrated_path.read_text(encoding="utf-8")
    note = parse_note(text)
    fm = dict(note.frontmatter) if isinstance(note.frontmatter, Mapping) else {}

    # Idempotent guard.
    if fm.get("stage") == "re_raw":
        return {
            "exit_code": 0,
            "status": "already_re_raw",
            "from_path": str(integrated_path),
            "to_path": "",
            "dry_run": dry_run,
        }

    now = ctx.now
    if not isinstance(now, dt.datetime):
        now = dt.datetime.now(tz=dt.timezone.utc)
    history = list(fm.get("reassimilation_history") or [])
    history.append(
        {
            "from_integrated_at": fm.get("captured_at") or fm.get("promoted_at") or "",
            "reassimilated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reason": str(reason).strip(),
        }
    )
    fm["stage"] = "re_raw"
    fm["reassimilation_history"] = history

    # Determine output filename: preserve note_id stem and append _re<n>
    # where n is len(history).
    suffix = f"_re{len(history)}"
    target = root / "notes" / "raw" / f"{note_id}{suffix}.md"
    check_write_allowed(ctx, target, verb="reassimilate")
    if integrated_path != target:
        check_write_allowed(ctx, integrated_path, verb="reassimilate")

    rendered = render_note(note.__class__(frontmatter=fm, body=note.body))
    if dry_run:
        return {
            "exit_code": 0,
            "status": "reassimilated",
            "from_path": str(integrated_path),
            "to_path": str(target),
            "dry_run": True,
        }
    atomic_utf8_write(target, rendered)
    integrated_path.unlink()
    return {
        "exit_code": 0,
        "status": "reassimilated",
        "from_path": str(integrated_path),
        "to_path": str(target),
        "dry_run": False,
    }
