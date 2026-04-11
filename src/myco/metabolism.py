"""Myco metabolism engine — biomimetic alias for myco.notes.

**Wave 29 (Biomimetic Nomenclature rewrite, phase 1 — additive)**: this module
exposes the substrate's digestive/metabolic functions under the biomimetic name
`metabolism`, re-exporting everything from the underlying `notes` module
without moving any implementation yet.

Why the indirection instead of moving the code outright: Wave 29's Phase A
inventory (`docs/primordia/biomimetic_execution_craft_2026-04-12.md §1`) found
~60-90 file edits would be required for a full atomic rename in one wave, and
single-response context budget under marathon discipline cannot safely
complete that without risk of leaving the substrate in a broken intermediate
state. The additive alias approach lets every intermediate state stay
lint-green because the old `from myco.notes import X` import path continues
to work unchanged while the new `from myco.metabolism import X` import path
becomes the canonical forward-looking name.

Wave 29b (or later) may physically move the implementation into this file
once all current callers have migrated. Until then, `from myco.metabolism
import X` and `from myco.notes import X` are semantically identical — both
resolve to the same function objects, same classes, same module state.

**Design rationale**: `docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md`
(Wave 28 design craft, kernel_contract, 0.90)

**Execution pivot**: `docs/primordia/biomimetic_execution_craft_2026-04-12.md`
§2.2 Defense of Attack N — the rename is physically coupled but additively
introducible, and additive introduction is the safer marathon shape.

**Named exports**: all public classes, constants, and functions from
`myco.notes`. The `_private` names stay private in both modules.
"""

from __future__ import annotations

# Biomimetic re-export of the metabolism engine's full public API.
# Every name listed here is a name that agents, tests, and future
# waves may reference as `from myco.metabolism import <name>`.
from myco.notes import (  # noqa: F401 — re-export
    # Exception taxonomy (will grow in future error-taxonomy wave C3)
    MycoProjectNotFound,

    # Schema constants
    DEFAULT_DEAD_THRESHOLD_DAYS,
    NOTES_DIRNAME,
    NOTE_FILENAME_RE,

    # ID + filename helpers
    generate_id,
    id_to_filename,
    filename_to_id,

    # Frontmatter parse/serialize
    parse_frontmatter,
    serialize_note,
    validate_frontmatter,

    # Note filesystem operations (the core digestive verbs)
    ensure_notes_dir,
    write_note,
    read_note,
    update_note,
    record_view,
    list_notes,

    # Reporting + signal detection (the hunger surface)
    HungerReport,
    DEFAULT_STRUCTURAL_LIMITS,
    detect_structural_bloat,
    detect_craft_reflex_missing,
    detect_contract_drift,
    detect_session_end_drift,
    detect_upstream_scan_stale,
    write_boot_brief,
    render_entry_point_signals_block,
    compute_hunger_report,
)

__all__ = [
    "MycoProjectNotFound",
    "DEFAULT_DEAD_THRESHOLD_DAYS",
    "NOTES_DIRNAME",
    "NOTE_FILENAME_RE",
    "generate_id",
    "id_to_filename",
    "filename_to_id",
    "parse_frontmatter",
    "serialize_note",
    "validate_frontmatter",
    "ensure_notes_dir",
    "write_note",
    "read_note",
    "update_note",
    "record_view",
    "list_notes",
    "HungerReport",
    "DEFAULT_STRUCTURAL_LIMITS",
    "detect_structural_bloat",
    "detect_craft_reflex_missing",
    "detect_contract_drift",
    "detect_session_end_drift",
    "detect_upstream_scan_stale",
    "write_boot_brief",
    "render_entry_point_signals_block",
    "compute_hunger_report",
]
