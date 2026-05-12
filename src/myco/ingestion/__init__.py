"""``myco.ingestion`` — 永恒吞噬 (eternal ingestion).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``.
History: see ``docs/contract_changelog.md`` § v0.4.0 + § v0.5.x.

Four commands, one entry-point patcher:

- ``eat``: append a raw note to ``notes/raw/``.
- ``hunger``: compose the substrate hunger report.
- ``sense``: read-only lookup across canon / notes / docs.
- ``forage``: inspect an external directory for ingestible material.
- ``boot_brief``: maintain a marker-delimited signals block in the
  entry-point file (internal — used by ``hunger --execute``).
"""

from .capture_cluster import (
    BEGIN_MARKER,
    END_MARKER,
    EatOutcome,
    HungerReport,
    append_note,
    compose_hunger_report,
    patch_entry_point,
    render_signals_block,
)
from .curate_cluster import ForageItem, SenseHit, list_candidates, search_substrate

__all__ = [
    # eat
    "EatOutcome",
    "append_note",
    # hunger
    "HungerReport",
    "compose_hunger_report",
    # sense
    "SenseHit",
    "search_substrate",
    # forage
    "ForageItem",
    "list_candidates",
    # boot_brief
    "BEGIN_MARKER",
    "END_MARKER",
    "patch_entry_point",
    "render_signals_block",
]
