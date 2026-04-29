# L2 — Boundary Doctrine

> **Status**: APPROVED (2026-04-28, v0.6.0 craft Round 4 owner amendment §A1; Round 5 physical merger LANDED).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/protocol.md`.
> **Maps to**: `src/myco/boundary/` (v0.6.0 7th canonical subsystem; **full physical layout** with surface/install/mcp/host_integration as proper subpackages).

---

## What this subsystem does

Boundary is the substrate's **outward interface layer**. Where the 6
fungal-bionic subsystems handle internal metabolism (germinate, ingest,
digest, circulate, regulate, transition), boundary handles
externalization — every surface where the agent or a host or an
installer touches the substrate from outside.

Boundary unifies four cross-cutting adapter packages that v0.5.x
treated as ad-hoc layers (v0.6.0 Round 5 — full physical merger):

- `boundary.surface` (`src/myco/boundary/surface/`): CLI + MCP server +
  manifest dispatcher. Translates verbs into CLI subcommands and MCP
  tool registrations.
- `boundary.install` (`src/myco/boundary/install/`): host config writers
  (myco-install host claude-code / cursor / cowork / etc). Writes
  basic mcpServers JSON to user-home config files.
- `boundary.mcp` (`src/myco/boundary/mcp/`): MCP server launcher, entry
  point for `mcp-server-myco` console script.
- `boundary.host_integration` (`src/myco/boundary/host_integration/`):
  per-host deep adapters writing native rule files / skills / commands /
  recipes. v0.6.0 ships 14 host adapters covering Claude Code, Cursor,
  Cowork, VS Code, Continue, Cline, JetBrains, Zed, Goose, Windsurf,
  Codex CLI, Gemini CLI, OpenClaw, Claude Desktop.

The legacy top-level packages `myco.surface` / `myco.install` /
`myco.mcp` / `myco.symbionts` are **REMOVED at v0.6.0**. All 80+
project-internal imports rewritten to canonical `myco.boundary.<sub>`
form via `scripts/myco_migrate.py`.

## Why this is a subsystem (not a meta-package)

v0.5.x treated `surface/` and `install/` as "cross-cutting adapter
packages, not subsystems". v0.6.0 owner amendment promotes them to a
single canonical subsystem `boundary` because:

1. **R7 enforceability**: cross-cutting status placed surface/install/
   mcp/symbionts outside `canon.subsystems`, hence outside MF1 (declared
   subsystems exist) / CG1 (doctrine has src reference) / CG2 (src
   subpackage links to doctrine) coverage. Promoting to subsystem brings
   them under the same machine-readable contract as the other 6.

2. **L0 P5 万物互联**: the substrate-as-graph has these packages
   present in every traversal. Treating them as "edge cases of the
   diagram" was a doctrine-implementation drift. Boundary makes the
   outward layer a first-class node.

3. **Dual-layer versioning**: per craft §F23, contract-frozen vs
   ecosystem-thawed split aligns with internal-metabolism vs
   outward-boundary distinction. Boundary IS the ecosystem-thawed
   surface in many respects (host adapters change with host releases;
   MCP transport evolves with spec); promoting it makes the layer
   visible in canon.

## L0 vocabulary amendment

`L0_VISION.md:185-186` says "No alternate vocabulary" — every
subsystem name must come from the fungal-bionic taxonomy. Boundary
narrowly extends this:

- The 6 internal subsystems remain strictly fungal-bionic
  (Germination / Ingestion / Digestion / Circulation / Homeostasis /
  Cycle).
- The 7th (Boundary) admits the most narrowly-applicable English
  word for "outward interface" because no fungal-bionic term maps
  cleanly. The amendment is recorded in
  `v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md`
  Round 4 §A1 with explicit owner approval.

Future contract-bumps must respect this scoping — the amendment is a
single carved exception, not a license to coin further alternate
vocabulary.

## Cross-subsystem contract

- **Reads from**: every subsystem (the surface adapter loads manifest
  from cycle, dispatches to ingestion/digestion/circulation/homeostasis;
  install reads canon to write per-host configs).
- **Writes to**: paths outside substrate root for install/host_integration
  (governed by host config discipline, not R6); paths inside substrate
  root only via verb dispatch (surface) or MCP tool invocation (mcp).
- **Emits**: nothing directly — boundary is a translation layer, not
  a content producer.

## Core invariants

1. **Boundary surfaces are R6-aware.** Every write within substrate
   root passes through `core.write_surface.check_write_allowed`.
   Writes outside substrate root (host config, user home) are
   excluded from R6 by definition — they are the host's own discipline,
   not the substrate's.

2. **Boundary surfaces are derivation-only.** No verb logic lives
   here. CLI argparse handlers, MCP tool registrations, install
   writers, and host adapters all delegate to subsystem code. PA3
   (mechanical, surface pure-adapter) guards.

3. **Boundary subpackage independence.** `boundary.surface`,
   `boundary.install`, `boundary.mcp`, `boundary.host_integration`
   may import from each other and from core/, but not from any
   subsystem's internal modules beyond their public ``run`` /
   ``run_cli`` entry points.

4. **Host-side write transparency.** Every artifact written by
   `boundary.host_integration.<host>.install_deep` carries a
   `# myco-symbiont-sig: <substrate_id>:<myco_version>` header. MF3
   dim verifies presence on every immune pass.

## v0.6.0 physical layout

The 7th-subsystem promotion landed as **full physical merger** at
v0.6.0 Round 5 per owner directive ("不许有任何一丝一毫偷懒"):

```
src/myco/boundary/
├── __init__.py              # imports the four subpackages locally
├── surface/                 # CLI + MCP server + manifest dispatcher
│   ├── cli.py
│   ├── manifest.yaml
│   ├── manifest.py
│   ├── mcp.py
│   ├── mcp_resources.py
│   ├── mcp_prompts.py
│   ├── mcp_sampling.py
│   ├── mcp_auth.py
│   └── capability.py
├── install/                 # myco-install host writers
│   ├── clients.py
│   ├── cowork_plugin.py
│   ├── plugin_bundle.py
│   └── fresh.py
├── mcp/                     # MCP launcher (`python -m myco.boundary.mcp`)
│   └── __init__.py
└── host_integration/        # 14 host adapters (formerly `myco.symbionts`)
    ├── _protocol.py
    ├── claude_code.py
    ├── cursor.py
    ├── cowork.py
    ├── vscode.py
    ├── continue_dev.py
    ├── cline.py
    ├── jetbrains.py
    ├── zed.py
    ├── goose.py
    ├── windsurf.py
    ├── codex_cli.py
    ├── gemini_cli.py
    ├── openclaw.py
    └── claude_desktop.py
```

201 import-path rewrites across 60 files (src + tests + docs +
configs) converted every `myco.surface.X` / `myco.install.X` /
`myco.mcp.X` / `myco.symbionts.X` reference to its `myco.boundary.X`
canonical form. pyproject.toml entry-points updated:

- `myco = "myco.boundary.surface.cli:main"`
- `mcp-server-myco = "myco.boundary.mcp:main"`
- `myco-install = "myco.boundary.install:main"`

## Migration notes

- v0.5.x → v0.6.0: legacy top-level imports (`from myco.surface import X`,
  `from myco.symbionts import X`, etc.) **break** — run
  `scripts/myco_migrate.py <path>` to rewrite user scripts to the
  canonical `myco.boundary.<sub>` form.
- v0.6.0 → v0.6.x: ecosystem-thawed patches may add new
  `boundary.host_integration/<host>.py` modules but the four
  subpackage layout is contract-frozen.

## What boundary does NOT do

- **Does not** generate verbs (those live in subsystems + cycle).
- **Does not** validate substrate invariants (homeostasis does).
- **Does not** propagate to downstream substrates (circulation does).
- **Does not** write LLM-imports to substrate (P1 forbidden; MP1/MP2/
  MP3 dims guard).

## Subagents and slash commands (v0.6.11+)

Boundary's outward interface gained a fifth seam at v0.6.11: **fungal-named
Claude Code subagents and slash commands** that formalize specialist roles
and user-trigger workflows that were previously done as ad-hoc agent
sessions. Two parallel paths host them:

- **Project-level** (auto-discovered by Claude Code when a developer opens
  the Myco-self repository): `.claude/agents/<name>.md` and
  `.claude/commands/<name>.md`.
- **Plugin-bundle scope** (declared in `.claude-plugin/plugin.json` so that
  `/plugin install myco@myco` delivers them to user installations):
  `<repo>/agents/<name>.md` and `<repo>/commands/<name>.md`.

Both paths follow Myco's existing plugin convention (cf. `<repo>/skills/`
declared in `plugin.json::skills`). The two copies are bytewise identical
per the regression test in
`tests/unit/boundary/test_subagent_and_command_surface.py`.

### Subagent roster (5 fungal-named specialists)

| Name | Fungal idiom | Role |
|------|--------------|------|
| `primordium` | The first compact, undifferentiated mass that emerges when a fruiting body begins to form | Drafts a 3-round craft proposal under `docs/primordia/`. Composes claim → 1.5 self-rebuttal → 2 refinement → 3 decision. Runs `myco winnow` to gate before returning. |
| `hypha` | The exploratory thread of fungus that extends through substrate | Investigates a single `myco_immune` finding by tracing root cause through the codebase. Read-only; produces a minimal-fix description, classifies the cause among 5 categories. |
| `autolysis` | Fungal self-digestion of old tissue | Sweeps stale narrative references (version drift, deleted module paths, deprecated identifiers). Produces a deterministic file:line:replacement patch table; does not apply. |
| `stipe` | The mushroom stem that holds the cap aloft so spores can disperse | Orchestrates the full release pipeline: pre-flight gate quintet, atomic bump, commit, push, ci.yml watch, tag, release.yml watch (PyPI + MCP Registry + GitHub Release + Cowork .plugin), post-release verification. |
| `anamorph` | The asexual transformative life-cycle form | Drafts canon schema migrations (named partial upgraders + tests + schema delta + migration guide). Stops before flipping `_canon.yaml::schema_version`. |

### Slash command roster (5 `myco-` triggers)

| Slash | Subagent | Argument |
|-------|----------|----------|
| `/myco-primordium <topic>` | primordium | topic phrase |
| `/myco-hypha [pattern]` | hypha | optional dim ID or path pattern |
| `/myco-autolyze [category]` | autolysis | optional category filter |
| `/myco-disperse <version>` | stipe | clean PEP 440 version string |
| `/myco-anamorph <new-schema-version> <governing-craft-path>` | anamorph | schema-version int + craft path |

### Surface invariants

1. **Subagents are atoms; verbs are the composition primitive.** Subagents
   cannot recurse (Claude Code spec) — they invoke each other via Bash
   calls to Myco's verb manifest, never via the Agent tool. The 20-verb
   manifest is the single composition primitive across both substrate
   subsystems and boundary subagents.

2. **R-rule awareness baked into each subagent body.** State-mutating
   subagents (`primordium`, `stipe`, `anamorph`) call `myco hunger`
   first per R1. Read-mostly subagents (`hypha`, `autolysis`) skip
   the boot ritual but still honor R3 (sense before assert) and R6
   (write surface).

3. **Plugin-mirror discipline.** The 10 markdown files (5 agents +
   5 commands) live at both `.claude/<dir>/<name>.md` (project-level)
   and `<repo>/<dir>/<name>.md` (plugin-bundle scope). v0.6.11 accepts
   the duplication as known maintenance debt; v0.6.12 may add a
   build-hook copy in `scripts/build_plugin.py`. A regression test
   verifies the two paths are bytewise identical.

4. **Naming complies with L0:185-186.** All five subagent names come
   from fungal taxonomy. The boundary subsystem amendment from v0.6.0
   §A1 (which permits "boundary" as a non-fungal English-coined name)
   is NOT invoked here; subagent names stay strictly fungal.

5. **Downstream substrates extend at project level.** A downstream
   substrate may add or override subagents via its own
   `.claude/agents/<name>.md`. Per Claude Code precedence, project-level
   agents override plugin agents. Myco-self ships these 5 as defaults;
   downstream may keep, override, or supplement.

### Future axis

`myco ramify --agent <name>` and `myco ramify --command <name>` flag
extensions are deferred to a subsequent release. v0.6.11 only ships the
surface; downstream substrates that want to scaffold subagents currently
copy from `.claude/agents/` manually or write from scratch following the
boundary doctrine pattern documented above.

> **Historical note (v0.6.14)**: `src/myco/providers/` was reserved at
> v0.5.6 as a named, path-scoped escape hatch from MP1's
> no-provider-SDK enforcement. Through 7 minor releases (v0.5.6 →
> v0.6.13) it remained empty by design. v0.6.14 excretes the directory:
> with `llm_policy: forbidden` as the default and v0.6.14 mechanizing
> the autopoietic loop entirely in the Agent layer (Sixth seam below),
> the kernel-side escape hatch is unused infrastructure. Future provider
> coupling, if ever needed, requires its own L0 P1 amendment craft and
> a fresh contract-bumping `molt`, **not** a pre-baked escape hatch
> sitting empty for years. The `llm_policy` enum drops
> `providers-declared` accordingly; remaining values are `forbidden`
> (default) and `opt-in` (per-call MCP sampling, tokens cleared per CL3).

## Sixth seam: GitHub-side critic-fanout + auto-revert (v0.6.14+)

Boundary's outward interface gained a **sixth seam** at v0.6.14:
**autopoietic kernel-evolution loop** that mechanizes the bridge from
metabolic flow (`eat → assimilate → sporulate`) to morphogenetic flow
(`fruit → winnow → molt`). The seam adds a new slash command, extends
two existing subagents, adds a GitHub Actions workflow, and lifts MP1's
mechanical guard — but **substrate kernel binary stays L0 P1 strict**
(zero new lines of LLM dispatch).

> **Governing craft**: `docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md`.
> **Cross-ref**: `L2_DOCTRINE/cycle.md` § "Cycle 自起 fruit—winnow—molt 闭环 (v0.6.14+)" carries the full chain semantics; this section documents the boundary-side surfaces only.

### Surface delta vs the 5th seam

| Element | 5th seam (v0.6.11) | 6th seam (v0.6.14) |
|---------|---------------------|---------------------|
| Subagent count | 5 (primordium / hypha / autolysis / stipe / anamorph) | 5 (unchanged) |
| Slash command count | 5 | **6** (new: `/myco-evolve <distilled-slug>`) |
| Subagent extension | (none) | primordium gains autonomous mode + Task tool; stipe gains `--branch-only` mode |
| GitHub-side surface | (none beyond plugin-bundle declaration) | `.github/workflows/auto_revert.yml` (new) |
| MP1 dim role | scans `src/myco/**` for provider SDK imports | additionally requires `authored_by:` frontmatter on every `docs/primordia/*.md` craft |
| Tracking issue | (none) | one substrate-wide GitHub issue tagged `auto-evolve-tracker` for `vetoed_intent` comment thread |

### Five fungal critic roles (sub-agent fanout protocol, v0.6.15+, derived from L0 P1-P5)

primordium's autonomous mode spawns **5 parallel** `general-purpose` sub-agents via the Task tool, each with a fungal role-prompt mapped to one L0 principle and a **disjoint visibility scope**. The 5-critic / one-per-principle shape was derived from the v0.6.15 craft Round 1.5 endophyte critic's T7 finding: "critic shape must be derived from L0 P1-P5 directly, not from observed-failure patches." Future critic additions require naming an L0 principle (or revising L0).

| Role | L0 Principle | Fungal idiom | Visibility scope | Bias |
|------|--------------|--------------|------------------|------|
| **chytrid** (壶菌) | P1 — Only For Agent | The most ancient fungal lineage; lives independently in water/soil without plant or animal host | L0_VISION.md only | does the proposal pull humans into the substrate's loop? introduce routine consumption? add owner role outside L0's "L0/L1/L2 craft-doc approver" definition? |
| **rhizomorph** (根状菌索) | P2 — Eternal Ingestion | Cord-like aggregations of hyphae that actively reach distant nutrient sources | ingestion subsystem code + adapters + L0 P2 doctrine | does the proposal restrict raw absorption? add intake-time filtering? violate "no out-of-scope rejection at ingest"? |
| **mycoparasite** (寄生菌) | P3 — Eternal Evolution | A fungus that infects + kills another organism; transformative replacement | draft only (no doctrine, no src/) | break paths, invalid premises, prompt-injection, feedback loops, single-point-of-failure |
| **saprotroph** (腐生菌) | P4 — Eternal Iteration | A fungus that decomposes dead organic matter into substrate; iteratively recycles | L0/L1/L2 + canon + previous crafts (no draft, no src/) | doctrine drift, vocabulary violations, governance contradictions, dead code, retrospective integration |
| **mycorrhiza** (菌根) | P5 — Universal Interconnection | Symbiotic root-fungus association; builds the largest underground graphs in nature | src/ + tests/ + .github/ + .claude/ + scripts/ (no draft, no doctrine) | impl traction, API boundaries, mock infra, byte-identity tests, graph connectedness |

All five names are established fungal-ecology terms (Chytridiomycota / rhizomorph aggregations / mycoparasitism / saprotrophic nutrition / mycorrhizal symbiosis); L0:185-186 vocabulary discipline strict.

Critic outputs are **veto votes**: any HIGH-severity tension from any critic forces primordium to abort to DRAFT status. primordium does NOT adjudicate; it surfaces all HIGHs and stops.

> **Migration note**: v0.6.14 shipped 3 ad-hoc critics (mycoparasite/saprotroph/mycorrhiza). v0.6.15 transitionally used 4 critics (added `endophyte` for L0 P1 conformance). The 5-critic L0-mapped shape going forward is the doctrinal answer; endophyte's role is now performed by **chytrid** (P1) — better fungal taxonomy match for "primal fungal-ness, no host dependency."

### Auto-revert workflow design

`.github/workflows/auto_revert.yml` triggers on `pull_request.closed && !merged && head_ref starts-with fruiting/`. Actions:

1. `git push --delete origin ${{ github.head_ref }}` — removes the auto-craft branch.
2. `gh issue comment <auto-evolve-tracker-id> --body "<vetoed_intent JSON blob>"` — records the veto for later canon write.

The next `myco senesce` invocation (in any session) parses new comments since `.myco_state/last_intent_reap.txt` and writes `vetoed_at: <ISO timestamp>` into matching entries of `canon.governance.last_winnowed_proposals[]`. Idempotent. The indirection (issue comment + senesce reaper) avoids the GitHub Actions concurrency hazard of writing `_canon.yaml` directly while a parallel push to main is in flight.

### Plugin-mirror discipline (extends 5th seam invariant 3)

The 6th seam's new files follow the same byte-identical mirror rule:

- `.claude/commands/myco-evolve.md` ↔ `<repo>/commands/myco-evolve.md`
- `.claude/agents/primordium.md` ↔ `<repo>/agents/primordium.md` (autonomous mode added in both)
- `.claude/agents/stipe.md` ↔ `<repo>/agents/stipe.md` (--branch-only mode added in both)

`tests/unit/boundary/test_subagent_and_command_surface.py` extends `_EXPECTED_COMMANDS` from 5 to 6 entries; new tests assert (a) only primordium has `Task` in its tools allowlist, (b) only primordium body mentions "Autonomous mode" — these prevent the autonomous-mode exception from accidentally proliferating to other subagents (the original mycorrhiza T1 critique).

### Six surface invariants (extending the 5th seam's 5)

1-5 from v0.6.11 unchanged. New at v0.6.14:

6. **Auto-craft branches use `fruiting/<slug>-<date>` prefix** (real fungal taxonomy; `fruiting body` is the standard mycological term). Branch names must NEVER use English compounds like "auto-craft/" — that violates L0:185-186 vocabulary discipline. Enforced by `canon.governance.auto_evolve_branch_prefix: "fruiting/"` and stipe `--branch-only` validation.
