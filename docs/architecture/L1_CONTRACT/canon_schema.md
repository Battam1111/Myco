# L1 — `_canon.yaml` Schema

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L1. Subordinate to `L0_VISION.md`, `protocol.md`.
> **Enforces**: write-surface discipline (R6), contract versioning, lint-category map.
> **Budget**: the v0.4.0 canon instance at L4 MUST be **≤ 300 non-comment lines**. If it isn't, something that belongs elsewhere has leaked in.

---

## Purpose

`_canon.yaml` is the **single source of truth** for every number, name,
path, and contract version that L2/L3/L4 cite. It is consumed by the
agent and by tooling on the agent's behalf (L0 principle 1). It is not a
human-readable document.

Per L0 principle 2 (永恒吞噬), the substrate has no project boundary —
`identity.tags` is free-form and non-exclusive. Per L0 principle 3
(永恒进化), the schema itself may evolve; `schema_version` tracks that.

The pre-rewrite canon (745 lines) violated SSoT discipline: it grew into
a general configuration dump with narrative comments, wave logs, and
subsystem-specific state. The v0.4.0 canon is SSoT-only.

## Top-level shape

```yaml
# _canon.yaml — v0.4.0 schema (example shape; values are illustrative)
schema_version: "1"                # bumps on structural schema change
contract_version: "v0.5.7"         # must match L1 protocol.md
synced_contract_version: "v0.5.7"  # updated by `myco assimilate` (v0.5.2 alias: `reflect`)

identity:                          # substrate self-identification
  substrate_id: "<slug>"           # globally unique; e.g. "myco-self", "ascc-research"
  tags: ["<domain>", ...]          # free-form affiliations (project names, domains); NOT boundaries
  entry_point: "MYCO.md"           # agent-entry file (CLAUDE.md in symbiont substrates)
  # NOTE: no "steward" or "owner" field. Governance (craft approval) is
  # external to the substrate and is not modeled here. Humans do not
  # consume this file (L0 principle 1: 人类无感知).

system:
  write_surface:
    allowed:                       # list of glob patterns agents may write
      - "_canon.yaml"
      - "notes/**"
      - "docs/**"
      - "src/**"
      - ".myco/**"                 # substrate-local plugins, if used (v0.5.3+);
                                   # include when the substrate registers
                                   # anything under `.myco/plugins/` or
                                   # `.myco/manifest_overlay.yaml`
      # …project-specific additions
  no_llm_in_substrate: true        # v0.5.6: default true. "Agent calls LLM;
                                   # substrate does not" — mechanically
                                   # enforced by the MP1 dimension (no
                                   # provider-SDK imports from inside
                                   # `src/myco/**`). Opt-out is `false` +
                                   # populating `src/myco/providers/` +
                                   # a contract-bumping molt.
  hard_contract:
    rules_ref: "docs/architecture/L1_CONTRACT/protocol.md"
    rule_count: 7                  # must match R1–R7

versioning:
  package_version_ref: "src/myco/__init__.py"
  pyproject_dynamic: true

lint:
  dimensions:                      # dimension_id → category (v0.5.7 roster, unchanged from v0.5.6)
    M1: mechanical                 # core write-surface / required-field shape
    M2: mechanical                 # fixable — missing entry-point file
    M3: mechanical                 # write-surface violations
    MF1: mechanical                # declared subsystems exist on disk
    MF2: mechanical                # substrate-local plugin health
    MP1: mechanical                # v0.5.6 NEW — "Agent calls LLM; substrate does not"
    SH1: shipped                   # package version sync
    MB1: metabolic                 # fixable — stale assimilation markers
    MB2: metabolic                 # undigested-note backlog pressure
    SE1: semantic                  # orphan / dangling cross-references
    SE2: semantic                  # canon ↔ reality drift (numbers, paths)
  categories:                      # the four fixed categories
    - mechanical
    - shipped
    - metabolic
    - semantic
  exit_policy:
    default: "mechanical:critical,shipped:critical,metabolic:never,semantic:never"
  skeleton_downgrade:
    marker: ".myco_state/autoseeded.txt"
    affected_dimensions: []        # v0.5.7: empty — no dimension is currently
                                   # downgraded in skeleton mode. The field is
                                   # retained so future dimension retirements
                                   # (or new dimensions that earn skeleton
                                   # grace) can be declared here without a
                                   # schema bump.

subsystems:                        # mirrors L2 Doctrine exactly (v0.5.3+ names)
  germination:                     # was "genesis" pre-v0.5.3; doc filename preserved
    doc: "docs/architecture/L2_DOCTRINE/genesis.md"
    package: "src/myco/germination/"
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

4. **Schema-versioned, forward-compatible.** `schema_version` bumps when
   the top-level shape changes. **v0.5+ (MAJOR 8):** an unknown
   `schema_version` triggers a `UserWarning`, not a hard error. The
   kernel reads the canon best-effort (every downstream consumer uses
   `.get(...)` with defaults, so unknown nested fields are tolerated).
   A registered entry in
   `myco.core.canon.schema_upgraders: dict[str, Callable]` transforms
   the observed shape to a known one in-flight; the warning fires only
   when no upgrader is registered. This is what lets "you never migrate
   again" (L0 principle 3) stand as a load-bearing claim rather than
   aspirational prose — an older kernel reading a newer canon still
   works, and a newer kernel reading an older canon chains through
   registered upgraders silently. Pre-v0.5 substrates that relied on
   the old raise-behavior to catch typos should adopt `myco immune` +
   a MF-class dimension for shape validation instead.

   v0.5.5 registered the first demo entry under key `"0"` (a schema
   version that never shipped in real canons) to prove the chain-
   apply path end-to-end. A canon declaring `schema_version: "0"`
   parses silently; the demo upgrader maps it to the current shape.
   Real v1 → v2 upgraders (when schema v2 ships) will register the
   same way — the mechanism is exercised from day one so the first
   real bump does not also have to debug a cold code path.

5. **Alphabetical within sections.** Deterministic ordering for diffs.

## What does NOT go in canon

- Bug backlogs (→ `docs/…`)
- Session logs (→ `log.md`)
- Craft docs (→ `docs/primordia/`)
- Note digests (→ `notes/`)
- Wave narratives (→ `docs/contract_changelog.md`)
- Per-dimension lint rules (→ `src/myco/homeostasis/` code)
- Runtime state (→ `.myco_state/`): including the mycelium graph cache at
  `.myco_state/graph.json` (see L2 `circulation.md`), the skeleton-mode
  marker `.myco_state/autoseeded.txt`, and the boot-brief snapshot
  `.myco_state/boot_brief.md`. These are derivable / reconstructable and
  must stay out of canon so the SSoT boundary remains clean.

If in doubt: canon only contains **things lint checks cite**. Everything
else lives in its natural home and is cross-referenced.

## Migration note

The v0.3.4 canon (745 lines) is not edited. The v0.3.4 canon is preserved
at tag `v0.3.4-final`; v0.4.0+ substrates are authored fresh from this
schema, carrying over only the values that still apply. See
`docs/contract_changelog.md` for the version-bump history.
