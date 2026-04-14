# L1 — `_canon.yaml` Schema

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L1. Subordinate to `L0_VISION.md`, `protocol.md`.
> **Enforces**: write-surface discipline (R6), contract versioning, lint-category map.
> **Budget**: the v0.4.0 canon instance at L4 MUST be **≤ 300 non-comment lines**. If it isn't, something that belongs elsewhere has leaked in.

---

## Purpose

`_canon.yaml` is the **single source of truth** for every number, name,
path, and contract version that L2/L3/L4 cite. When a wiki page says
"test_count: 600", the 600 comes from canon, not from the wiki. When the
immune kernel computes exit codes, category mappings come from canon, not
from a hard-coded table.

The pre-rewrite canon (745 lines) violated this: it grew into a general
configuration dump with narrative comments, wave logs, and
subsystem-specific state. The v0.4.0 canon is SSoT-only.

## Top-level shape

```yaml
# _canon.yaml — v0.4.0 schema
schema_version: "1"                # bumps on structural schema change
contract_version: "v0.4.0"         # must match L1 protocol.md
synced_contract_version: "v0.4.0"  # updated by `myco reflect`

identity:                          # who this substrate belongs to
  project: "<name>"                # e.g. "myco", "ascc"
  steward: "<human name>"
  entry_point: "MYCO.md"           # or "CLAUDE.md" for downstream projects

system:
  write_surface:
    allowed:                       # list of glob patterns agents may write
      - "_canon.yaml"
      - "notes/**"
      - "docs/**"
      - "src/**"
      # …project-specific additions
  hard_contract:
    rules_ref: "docs/architecture/L1_CONTRACT/protocol.md"
    rule_count: 7                  # must match R1–R7

versioning:
  package_version_ref: "src/myco/__init__.py"
  pyproject_dynamic: true

lint:
  dimensions:                      # dimension_id → category
    L0: mechanical
    L1: mechanical
    # …
  categories:                      # the four fixed categories
    - mechanical
    - shipped
    - metabolic
    - semantic
  exit_policy:
    default: "mechanical:critical,shipped:critical,metabolic:never,semantic:never"
  skeleton_downgrade:
    marker: ".myco_state/autoseeded.txt"
    affected_dimensions: [L0, L1]

subsystems:                        # mirrors L2 Doctrine exactly
  genesis:
    doc: "docs/architecture/L2_DOCTRINE/genesis.md"
    package: "src/myco/genesis/"
  ingestion:
    doc: "docs/architecture/L2_DOCTRINE/ingestion.md"
    package: "src/myco/ingestion/"
  digestion:
    doc: "docs/architecture/L2_DOCTRINE/digestion.md"
    package: "src/myco/digestion/"
  circulation:
    doc: "docs/architecture/L2_DOCTRINE/circulation.md"
    package: "src/myco/circulation/"
  homeostasis:
    doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"
    package: "src/myco/homeostasis/"

commands:                          # manifest reference
  manifest_ref: "docs/architecture/L3_IMPLEMENTATION/command_manifest.md"

metrics:                           # SSoT numbers other files cite
  test_count: <int>                # updated on test-suite change
  # ↳ fix-ups: lint dim L2 ("stale numbers") checks every .md against these

waves:                             # history of contract-level changes
  current: 1                       # resets to 1 at v0.4.0 (per §9 E5)
  log_ref: "docs/contract_changelog.md"
```

## Rules

1. **No narrative comments.** Cross-references live in dedicated fields
   (`…_ref`), not YAML comments. Comments are reserved for schema
   annotations only.

2. **No subsystem state.** Runtime state (`.myco_state/*`), cached briefs,
   and hunger snapshots live under `.myco_state/`, never in canon.

3. **No duplication.** If a value exists in canon, it does not exist
   anywhere else. Other files either reference canon or are validated
   against canon.

4. **Schema-versioned.** `schema_version` bumps when the top-level shape
   changes. The immune system refuses to read an unknown `schema_version`.

5. **Alphabetical within sections.** Deterministic ordering for diffs.

## What does NOT go in canon

- Bug backlogs (→ `docs/…`)
- Session logs (→ `log.md`)
- Craft docs (→ `docs/primordia/`)
- Note digests (→ `notes/`)
- Wave narratives (→ `docs/contract_changelog.md`)
- Per-dimension lint rules (→ `src/myco/homeostasis/` code)

If in doubt: canon only contains **things lint checks cite**. Everything
else lives in its natural home and is cross-referenced.

## Migration note

The v0.3.4 canon (745 lines) will not be edited. At L4 re-export, a fresh
canon is authored from this schema, carrying over only the values that
still apply. See `docs/architecture/L4_SUBSTRATE/export_plan.md` (to be
authored at Phase 9).
