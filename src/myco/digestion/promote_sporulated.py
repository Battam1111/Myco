"""``digestion.promote_sporulated`` — distilled → sporulated (v0.6.0).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md``
state machine completion; v0.6.0 craft §F6 closes the loop by
promoting a distilled note to ``stage: sporulated`` once a craft
under ``docs/primordia/`` consumes it.

Detection rule (heuristic but precise):

    A distilled note ``notes/distilled/d_<slug>.md`` is considered
    "consumed" if a craft file ``docs/primordia/<slug>_*_<date>.md``
    exists whose body references the distilled note's path or whose
    frontmatter ``slug`` matches the distilled slug.

When promotion fires, the distilled note's frontmatter is rewritten:

- ``stage`` → ``sporulated``.
- ``propagated_doctrine`` → relative path to the consuming craft.
- ``promoted_at`` → UTC timestamp.

MB4 dim verifies the integrity of this state.

Idempotent: re-running on already-sporulated notes is no-op.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from myco.core.context import MycoContext
from myco.core.io_atomic import atomic_utf8_write
from myco.core.write_surface import check_write_allowed

from .pipeline import parse_note, render_note

__all__ = ["promote_consumed_distilled"]


def promote_consumed_distilled(
    ctx: MycoContext,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Walk distilled/ + primordia/, promote consumed distilled notes.

    Returns:
        ``{exit_code, promoted: [{slug, distilled_path, craft_path}],
        already_sporulated, dry_run}``.
    """
    root = ctx.substrate.root
    distilled_root = root / "notes" / "distilled"
    primordia_root = root / "docs" / "primordia"
    promoted: list[dict[str, str]] = []
    already_sporulated = 0

    if not distilled_root.is_dir() or not primordia_root.is_dir():
        return {
            "exit_code": 0,
            "promoted": [],
            "already_sporulated": 0,
            "dry_run": dry_run,
        }

    crafts = list(primordia_root.glob("*_craft_*.md"))

    for distilled_path in distilled_root.glob("d_*.md"):
        if "_excreted" in distilled_path.parts:
            continue
        slug = distilled_path.stem.removeprefix("d_")
        try:
            text = distilled_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        note = parse_note(text)
        fm = dict(note.frontmatter) if isinstance(note.frontmatter, Mapping) else {}
        if fm.get("stage") == "sporulated":
            already_sporulated += 1
            continue

        # Find a craft that mentions the slug in its filename or body.
        consuming_craft: Path | None = None
        for craft_path in crafts:
            if slug in craft_path.stem:
                consuming_craft = craft_path
                break
            try:
                ctext = craft_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            rel_distilled = distilled_path.relative_to(root).as_posix()
            if rel_distilled in ctext or distilled_path.name in ctext:
                consuming_craft = craft_path
                break
        if consuming_craft is None:
            continue

        # Promote.
        now = ctx.now
        if not isinstance(now, dt.datetime):
            now = dt.datetime.now(tz=dt.timezone.utc)
        fm["stage"] = "sporulated"
        fm["propagated_doctrine"] = consuming_craft.relative_to(root).as_posix()
        fm["promoted_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        check_write_allowed(ctx, distilled_path, verb="promote_sporulated")
        if not dry_run:
            rendered = render_note(note.__class__(frontmatter=fm, body=note.body))
            atomic_utf8_write(distilled_path, rendered)
        promoted.append(
            {
                "slug": slug,
                "distilled_path": distilled_path.relative_to(root).as_posix(),
                "craft_path": consuming_craft.relative_to(root).as_posix(),
            }
        )

    return {
        "exit_code": 0,
        "promoted": promoted,
        "already_sporulated": already_sporulated,
        "dry_run": dry_run,
    }
