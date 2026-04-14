"""``myco.digestion`` — 永恒进化 / 永恒迭代.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md``.
Craft: ``docs/primordia/stage_b5_digestion_craft_2026-04-15.md``.

Pipeline: ``raw → digesting → integrated → distilled``. Verbs:

- ``reflect`` (bulk) — promote all raw notes.
- ``digest <note-id>`` — promote one note, with ``--dry-run``.
- ``distill <slug>`` — author a doctrine proposal note under
  ``notes/distilled/``.
"""

from .digest import digest_one
from .distill import distill_proposal
from .pipeline import (
    NOTE_STAGES,
    Note,
    parse_note,
    promote_to_integrated,
    render_note,
)
from .reflect import reflect

__all__ = [
    "NOTE_STAGES",
    "Note",
    "digest_one",
    "distill_proposal",
    "parse_note",
    "promote_to_integrated",
    "reflect",
    "render_note",
]
