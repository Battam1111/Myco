# L1 — `_canon.yaml` Schema

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9; v0.6.0 schema v2 amendment LANDED 2026-04-28 per `docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md`).
> **Layer**: L1. Subordinate to `L0_VISION.md`, `protocol.md`.
> **Enforces**: write-surface discipline (R6), contract versioning, lint-category map.
> **Budget**: the v0.4.0 canon instance at L4 MUST be **≤ 300 non-comment lines**. If it isn't, something that belongs elsewhere has leaked in. v0.6.0 raises the budget to **≤ 400 non-comment lines** to accommodate schema v2 additions (resource_redaction, resource_watch, governance, severity_promotion, thresholds, abstract_parent_allowlist, federation_peers, expanded lint.dimensions). Future v2.1 will extract `lint.dimensions` to sibling `_canon_lint.yaml`, returning the main canon to ≤ 300 LoC.

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
# canon (v0.8.4+: .myco/canon.yaml | legacy: _canon.yaml at root)
# Schema started at v0.4.0; values below are illustrative current-state.
schema_version: "3"                # v0.7.5+ — bumps on structural schema change
contract_version: "v0.8.5"         # must match L1 protocol.md
synced_contract_version: "v0.8.5"  # updated by `myco assimilate`

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
  # v0.6.0+ owner amendment §A4: full lint dim roster lives in sibling
  # canon_lint.yaml. core.canon.load_canon merges the dimensions_ref
  # payload into the canon's lint section transparently. Single SSoT.
  # The v0.6.0 release expanded the roster to 46 dims; v0.7.2 added
  # SE5+MB8+PA6 (49); v0.7.5 added LB1+CG1+CG2 (52); v0.8.0 added LB2 (53);
  # v0.8.5 retired MF3 (host_integration excretion) and MB7 (mcp_resources
  # excretion); v0.8.6 retired SE4 + RL2 + RL3 (never-fire dead-letter
  # dims) — live roster: **47 dims** at v0.8.6.
  dimensions_ref: "_canon_lint.yaml"
  # Representative slice of the v0.8.6 roster (full table at
  # canon_lint.yaml; `myco immune --list` prints the live IDs):
  #   M1/M2/M3/MF1+MF2+MF4+MF5/MP1-MP3 (mechanical kernel/plugin/purity)
  #   DC1-DC5/CS1/FR1/PA1-PA6/CG1-CG2/DI1-DI2/AD1/SC1/CL1-CL3 (mechanical hygiene)
  #   SH1/SH2 (shipped: package + provenance)
  #   MB1-MB4/MB6/MB8 (metabolic: backlog pressure + shim-hit telemetry)
  #   SE1-SE3/SE5/RL1/LB1-LB2 (semantic: cross-ref, version-anchor freshness,
  #     Living Bets cadence + two-regime axis)
  categories:                      # the four fixed categories
    - mechanical
    - shipped
    - metabolic
    - semantic
  exit_policy:
    default: "mechanical:critical,shipped:critical,metabolic:never,semantic:never"
  skeleton_downgrade:
    marker: ".myco_state/autoseeded.txt"
    affected_dimensions: []        # v0.6.15: empty — no dimension is currently
                                   # downgraded in skeleton mode. The field is
                                   # retained so future dimension retirements
                                   # (or new dimensions that earn skeleton
                                   # grace) can be declared here without a
                                   # schema bump.

subsystems:                        # mirrors L2 Doctrine exactly (7 subsystems at v0.6.0+)
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
  cycle:                           # 6th subsystem since v0.6.0 (was cross-cutting at v0.5.3)
    doc: "docs/architecture/L2_DOCTRINE/cycle.md"
    package: "src/myco/cycle/"
  boundary:                        # 7th subsystem since v0.6.0 (unified outward-interface layer)
    doc: "docs/architecture/L2_DOCTRINE/boundary.md"
    package: "src/myco/boundary/"

commands:                          # manifest reference (v0.6.0 path)
  manifest_ref: "src/myco/boundary/surface/manifest.yaml"

metrics:                           # SSoT numbers other files cite
  test_count: <int>                # updated on test-suite change
  # ↳ fix-ups: lint dim L2 ("stale numbers") checks every .md against these

waves:                             # history of contract-level changes
  current: 1                       # resets to 1 at v0.4.0 (per §9 E5)
  log_ref: "docs/contract_changelog.md"
```

## v0.6.0+ schema v2 additions

Schema v2 (LANDED at v0.6.0 per the unified evolution craft) added the
following fields. The minimal example above stays focused on the v0.4.0
core shape; the additions below extend `system.*` and `lint.*` and
**SHOULD be present in canons that opt into the v0.6.0+ governance,
resource-redaction, and resource-watch surfaces**. Their absence is
tolerated by the schema-upgrader chain — older canons read fine.

### `system.llm_policy` (v0.5.6 → enum-narrowed at v0.6.14)

```yaml
system:
  llm_policy: "forbidden"          # v0.6.14: 2-value enum (was 3 at v0.6.0).
                                   # "forbidden" (default; Myco strict P1 — no LLM in substrate process)
                                   # "opt-in"   (per-call sampling allowed; tokens cleared after each call)
                                   # MP1/MP2/MP3 + CL1/CL2/CL3 dims cooperate to enforce.
                                   # Per craft v0.6.14: "providers-declared" dropped because
                                   # src/myco/providers/ was excreted (never populated through
                                   # 7 minor releases v0.5.6 → v0.6.13).
```

### `system.resource_redaction` (v0.6.0)

```yaml
system:
  resource_redaction:
    paths:
      protected:                   # paths agents see only with `canon:read` scope
        - "identity.federation_peers"
        - "identity.tags"
        - "system.governance"
      private: []                  # paths gated behind `canon:full` only
    scopes:
      public: ["contract_version", "schema_version", "subsystems", "lint.categories"]
      protected: ["identity.substrate_id", "system.write_surface", "lint.dimensions"]
```

### `system.resource_watch` (v0.6.0)

```yaml
system:
  resource_watch:
    max_per_substrate: 100         # inotify max_user_watches budget per substrate
    eviction: "lru"
    fallback_to_etag_polling: true # ETag-based long-poll when quota saturates.
                                   # (The v0.6.0 MB7 dim that previously
                                   # emitted at ≥80% consumption was excreted
                                   # at v0.8.5 with the mcp_resources stub
                                   # that was never wired into build_server.
                                   # Re-mechanise in v0.9 if the resource-
                                   # watch subscription manager actually ships.)
```

### `system.governance` (v0.6.0 + v0.6.14 + v0.6.15)

The governance section gates risk-tiered craft proposals through
`agent-self-winnow + 7-session/7-day public window + always-on
vetoed_at`. Per L0 P1 (Only For Agent), defaults are Agent-First:
medium-risk auto-crafts auto-LAND after window expiry; only HIGH-risk
crafts force owner-merge gates.

```yaml
system:
  governance:
    # v0.6.0 originals (window definitions + token rotation)
    public_window_min_senesce_count: 7        # int — min senesce count before auto-LAND
    public_window_min_wall_clock_days: 7      # int — wall-clock days; whichever is hit first
    refresh_token_rotation_grace_seconds: 30  # int — OAuth refresh grace
    last_winnowed_proposals: []               # array of objects (see schema below)
    token_redaction_required: true            # bool — when true, mcp_auth.py must import
                                              # _redact_in_logs helper. CL2 dim refuses
                                              # streamable-http server boot otherwise.

    # v0.6.14 Cycle 自起 fruit—winnow—molt 闭环 governance fields
    auto_propose_enabled: false               # bool — master switch (default false per substrate)
    auto_evolve_min_wall_clock_seconds_between: 600  # int — rate limit between auto-evolve runs;
                                              # persisted in .myco_state/last_auto_evolve.txt
    auto_evolve_critic_count: 5               # int — fungal critics primordium spawns; v0.6.15
                                              # changed from 3 (v0.6.14) → 5 (one per L0 P1-P5)
    auto_evolve_branch_prefix: "fruiting/"    # str — fungal taxonomy per L0:185-186
    auto_evolve_distilled_hash_cooldown_senesce: 7  # int — same-distilled-hash cooldown
    auto_evolve_min_distilled_severity: medium  # enum — low/medium/high/critical
    auto_evolve_daily_budget_usd: null        # int|null — daily USD-equivalent cap; null = unbounded
    auto_evolve_tracking_issue_id: null       # int|null — GitHub issue ID for vetoed_intent comments
    recognized_authoring_hosts:               # array[str] — MP1 host-signature allowlist
      - "claude-code-agent"
      - "cursor-agent"
      - "claude-desktop-agent"
      - "cowork-agent"
      - "human"

    # v0.6.15 Agent-First default flips (corrected v0.6.14 owner-First regression)
    auto_evolve_force_high_risk: false        # bool — false at v0.6.15 (was true at v0.6.14).
                                              # When false, risk class is derived from craft
                                              # CONTENT (winnow G7 path_allowlist + keyword
                                              # heuristics; the v0.6.0 core.risk_classifier
                                              # helper that did this work was excreted at v0.8.5
                                              # as never-wired-into-winnow.G7-production-path).
    auto_evolve_pr_window_skip: false         # bool — false at v0.6.15 (was true at v0.6.14).
                                              # When false, medium-risk auto-crafts honor the
                                              # v0.6.0 governance public window.

# Object shape for last_winnowed_proposals[] entries:
#   - craft_path:    str  # absolute path to docs/primordia/<slug>.md
#     risk_tier:     enum # "low" | "medium" | "high"
#     winnowed_at:   str  # ISO 8601 UTC timestamp
#     senesce_count: int  # senesce count at winnow time (for window check)
#     pr_url:        str  # GitHub PR URL (or null pre-PR)
#     vetoed_at:     str|null  # ISO 8601 UTC; owner sets to abort. Always-on.
#     landed_at:     str|null  # ISO 8601 UTC; senesce reaper writes when window expires
```

Schema-version bump justification: the governance section's array shape
(`last_winnowed_proposals: list[object]`) was the load-bearing change
that tipped v0.6.0 from schema v1 → schema v2. The object schema above
must be honored by any kernel reading the canon; the schema-upgrader
chain (`myco.core.canon.schema_upgraders["1"]`) handles the v1 → v2
transition for older substrates.

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

The pre-rewrite v0.3.4 canon (745 lines) is not edited. The legacy v0.3.4
canon is preserved at tag `v0.3.4-final`; v0.4.0+ substrates are
authored fresh from this schema, carrying over only the values that
still apply. See
`docs/contract_changelog.md` for the version-bump history.
