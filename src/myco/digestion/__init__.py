"""``myco.digestion`` — 永恒进化 / 永恒迭代.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/digestion.md``.
Craft: ``docs/primordia/stage_b5_digestion_craft_2026-04-15.md``.

Pipeline: ``raw → digesting → integrated → distilled``. Verbs (v0.5.3+
canonical names, with aliases for the v0.5.x names):

- ``assimilate`` (bulk; aliased ``reflect``) — promote all raw notes.
- ``digest <note-id>`` — promote one note, with ``--dry-run``.
- ``sporulate <slug>`` (aliased ``distill``) — author a doctrine
  proposal note under ``notes/distilled/``.

Function names inside are unchanged (``reflect``, ``distill_proposal``)
to avoid per-call-site churn. Only module names and CLI verb names
moved.
"""

from .assimilate import reflect
from .digest import digest_one
from .pipeline import (
    NOTE_STAGES,
    Note,
    parse_note,
    promote_to_integrated,
    render_note,
)
from .sporulate import distill_proposal

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
