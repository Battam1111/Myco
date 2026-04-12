"""Myco immune system — biomimetic alias for myco.lint.

**Wave 29 (Biomimetic Nomenclature rewrite, phase 1 — additive)**: this module
exposes the substrate's 23-dimension immune system (formerly "lint") under
the biomimetic name `immune`, re-exporting everything from the underlying
`lint` module without moving any implementation yet.

**Why "immune" not "lint"**: the 23 dimensions L0–L22 perform immune-system
functions on the substrate:
- **L0** genome self-check (canon schema validity)
- **L1** reference integrity (foreign-token detection)
- **L2** number consistency (internal coherence)
- **L3** stale pattern scan (senescence detection)
- **L4** orphan detection (unlinked organelle removal signal)
- **L5** log coverage (trail completeness)
- **L6** date consistency (temporal invariants)
- **L7** hyphae format (formerly "wiki format" — structured knowledge strand integrity)
- **L8** .original sync (compression audit trail)
- **L9** vision anchor (identity drift detection — anti-cancer)
- **L10** metabolism schema (formerly "notes schema" — digestive contract)
- **L11** write surface (membrane permeability)
- **L12** upstream dotfile hygiene (foreign-contact surface hygiene)
- **L13** craft protocol schema (reproductive organ integrity)
- **L14** forage hygiene (food safety)
- **L15** craft reflex (self-healing reflex arc)
- **L16** boot brief freshness (sensory input integrity)
- **L17** contract drift (cross-instance immune memory)
- **L18** compression integrity (.original / extracted note hash audit — Wave 30, v0.26.0)
- **L19** lint dimension count consistency (downstream-cache drift — Wave 38, v0.29.0)
- **L20** translation mirror consistency (locale README skeleton parity — Wave 39, v0.30.0)
- **L21** contract version inline consistency (forward-looking inline contract version SSoT — Wave 40, v0.31.0)
- **L22** wave-seed lifecycle (raw wave-seed orphan detection — seven-step pipeline post-condition, Wave 41, v0.32.0)

"Lint" is the generic software-engineering term that reads as "static analysis
tool". "Immune" is what the code actually does in the fungal-organism frame.

**Wave 29 strategy**: additive re-export (same as `myco.metabolism` / `myco.notes`).
Every intermediate state stays lint-green because `from myco.lint import X`
still works. Later waves may physically move implementation here and retire
the `myco.lint` path.

**Design rationale**: `docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md`

**Execution pivot**: `docs/primordia/biomimetic_execution_craft_2026-04-12.md`
"""

from __future__ import annotations

# Biomimetic re-export of the immune system's full public surface.
from myco.lint import (  # noqa: F401 — re-export
    # Color helpers (terminal output)
    C,
    red,
    green,
    yellow,
    cyan,
    bold,

    # Canon / reference helpers
    load_canon,
    get_entry_point,
    read_file,
    find_files,

    # 23 immune dimensions L0–L22
    lint_canon_schema,        # L0 — will become "lint_genome_schema" in a later wave
    lint_references,          # L1
    lint_numbers,             # L2
    lint_stale_patterns,      # L3
    lint_orphans,             # L4
    lint_log,                 # L5
    lint_dates,               # L6
    lint_wiki_format,         # L7 — will become "lint_hyphae_format" in a later wave
    lint_vision_anchors,      # L9
    lint_notes_schema,        # L10 — will become "lint_metabolism_schema" in a later wave
    lint_original_sync,       # L8 (order in lint.py differs)
    lint_write_surface,       # L11
    lint_dotfile_hygiene,     # L12
    lint_craft_protocol,      # L13
    lint_forage_hygiene,      # L14
    lint_craft_reflex,        # L15
    lint_boot_brief_freshness,  # L16
    lint_contract_drift,      # L17
    lint_compression_integrity,  # L18 — Wave 30 (v0.26.0)
    lint_dimension_count_consistency,  # L19 — Wave 38 (v0.29.0)
    lint_translation_mirror_consistency,  # L20 — Wave 39 (v0.30.0)
    lint_contract_version_inline,  # L21 — Wave 40 (v0.31.0)
    lint_wave_seed_orphan,    # L22 — Wave 41 (v0.32.0)

    # Entry points
    main,
    run_lint,
)

__all__ = [
    "C",
    "red",
    "green",
    "yellow",
    "cyan",
    "bold",
    "load_canon",
    "get_entry_point",
    "read_file",
    "find_files",
    "lint_canon_schema",
    "lint_references",
    "lint_numbers",
    "lint_stale_patterns",
    "lint_orphans",
    "lint_log",
    "lint_dates",
    "lint_wiki_format",
    "lint_vision_anchors",
    "lint_notes_schema",
    "lint_original_sync",
    "lint_write_surface",
    "lint_dotfile_hygiene",
    "lint_craft_protocol",
    "lint_forage_hygiene",
    "lint_craft_reflex",
    "lint_boot_brief_freshness",
    "lint_contract_drift",
    "lint_compression_integrity",
    "lint_dimension_count_consistency",
    "lint_translation_mirror_consistency",
    "lint_contract_version_inline",
    "lint_wave_seed_orphan",
    "main",
    "run_lint",
]
