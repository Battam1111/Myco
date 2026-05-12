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
  `<repo>/plugin/agents/<name>.md` and `<repo>/plugin/commands/<name>.md`.

Both paths follow Myco's existing plugin convention (cf.
`<repo>/plugin/skills/` declared in `plugin.json::skills`). The two copies
are bytewise identical per the regression test in
`tests/unit/boundary/test_subagent_and_command_surface.py`.

> **v0.8.4 root-cleanup (2026-05-12)**: plugin-bundle scope was moved
> from repo-root `<repo>/{agents,commands,hooks,skills}/` to
> `<repo>/plugin/{agents,commands,hooks,skills}/` to declutter the
> root directory. `.claude-plugin/` itself stays at repo root so
> `/plugin marketplace add Battam1111/Myco` discovery + `marketplace.json`
> resolution continue unchanged. `plugin.json`'s relative paths were
> updated from `./agents/` etc to `./plugin/agents/` etc; the path
> resolution rule (relative to plugin root = parent of `.claude-plugin/`
> = `<repo>/`) means Claude Code's loader finds them at the new location
> without changes to the spec.

### Subagent roster (5 fungal-named specialists)

| Name | Fungal idiom | Role |
|------|--------------|------|
| `primordium` | The first compact, undifferentiated mass that emerges when a fruiting body begins to form | Drafts a 3-round craft proposal under `docs/primordia/`. Composes claim → 1.5 self-rebuttal → 2 refinement → 3 decision. Runs `myco winnow` to gate before returning. |
| `hypha` | The exploratory thread of fungus that extends through substrate | Investigates a single `myco_immune` finding by tracing root cause through the codebase. Read-only; produces a minimal-fix description, classifies the cause among 5 categories. |
| `autolysis` | Fungal self-digestion of old tissue | Sweeps stale narrative references (version drift, deleted module paths, deprecated identifiers). Produces a deterministic file:line:replacement patch table; does not apply. |
| `stipe` | The mushroom stem that holds the cap aloft so spores can disperse | Orchestrates the full release pipeline: pre-flight gate quintet, atomic bump, commit, push, ci.yml watch, tag, release.yml watch (PyPI + MCP Registry + GitHub Release + Cowork .zip bundle), post-release verification. |
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
   and `<repo>/plugin/<dir>/<name>.md` (plugin-bundle scope, v0.8.4+;
   was `<repo>/<dir>/<name>.md` v0.6.11-v0.8.3). v0.6.11 accepts the
   duplication as known maintenance debt; `scripts/sync_plugin_mirrors.py`
   keeps them in sync as a pre-bump step. A regression test verifies
   the two paths are bytewise identical.

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

- `.claude/commands/myco-evolve.md` ↔ `<repo>/plugin/commands/myco-evolve.md`
- `.claude/agents/primordium.md` ↔ `<repo>/plugin/agents/primordium.md` (autonomous mode added in both)
- `.claude/agents/stipe.md` ↔ `<repo>/plugin/agents/stipe.md` (--branch-only mode added in both)

`tests/unit/boundary/test_subagent_and_command_surface.py` extends `_EXPECTED_COMMANDS` from 5 to 6 entries; new tests assert (a) only primordium has `Task` in its tools allowlist, (b) only primordium body mentions "Autonomous mode" — these prevent the autonomous-mode exception from accidentally proliferating to other subagents (the original mycorrhiza T1 critique).

### Six surface invariants (extending the 5th seam's 5)

1-5 from v0.6.11 unchanged. New at v0.6.14:

6. **Auto-craft branches use `fruiting/<slug>-<date>` prefix** (real fungal taxonomy; `fruiting body` is the standard mycological term). Branch names must NEVER use English compounds like "auto-craft/" — that violates L0:185-186 vocabulary discipline. Enforced by `canon.governance.auto_evolve_branch_prefix: "fruiting/"` and stipe `--branch-only` validation.

## Legacy import shims (v0.7.3+)

Boundary's outward interface is exposed to **two consumer populations whose upgrade cadence the substrate cannot observe**:

1. **Local MCP host configs** (Claude Desktop / Cursor / Cowork / etc.) — each host's config file (`%APPDATA%/Claude/claude_desktop_config.json`, `~/.cursor/mcp.json`, etc.) hardcodes the launcher command. Once written, the config persists indefinitely until the user manually edits it.
2. **Downstream substrates' import statements** — any project that does `from myco.mcp import build_server` (or similar legacy path) is locked into that import path until a human contributor edits the file.

The substrate **cannot** detect these consumers from inside its own process. A `DeprecationWarning` emitted to stderr at module-import time is read by neither population in practice — host UIs surface stderr in a "View Logs" panel that operators rarely open, and downstream substrates' Python imports typically suppress DeprecationWarnings entirely.

The v0.7.0 incident validated this empirically: deletion of the v0.6.13 `myco.mcp` shim (4 versions of stderr deprecation warnings preceding it) broke the substrate's own owner-Claude-Desktop within 2 hours of release. v0.7.1 restored the shim and named the new discipline below; v0.7.3 codifies it as authoritative L2 doctrine.

### Public-API deletion discipline (v0.7.1-named, v0.7.3-canonized)

A back-compat shim package is **safe to delete** only if it satisfies ONE of the following gates. Both gates must be **mechanically verified**, not prose-asserted:

#### Gate (a) — Internal-only verification

ALL of the following must hold:

- `grep -r "from <legacy_path> import" src/ tests/ scripts/ examples/` returns zero hits.
- No CLI or MCP host entry point (`pyproject.toml::[project.entry-points]`, `.claude-plugin/plugin.json`, `.cowork-plugin/`, `.mcp.json`) declares the path.
- No plugin manifest registers handlers / hooks / skills under the path.
- The path is NOT imported via `python -m <legacy_path>` from any documented runbook or migration guide.

If all four conditions hold, the path is internal-only; deletion is the v0.6.16 sweep style mechanical SE2 fix and ships in any release.

#### Gate (b) — Telemetry verification

For paths that expose an external surface (CLI invocation, plugin manifest, MCP host config), gate (a) cannot rule out external usage. Gate (b) instead requires:

- An MB8-style hit counter writes one JSONL line per actual usage (e.g., `.myco_state/shim_hits.json` for `myco.mcp`).
- The substrate has run for ≥ `governance.shim_sunset_min_zero_cycles` senesce cycles (default 7) AND ≥ `governance.shim_sunset_min_zero_days` wall-clock days (default 7) with **zero hits** on the path.
- The senesce-cycle window straddles at least one realistic usage scenario (e.g., a typical week of MCP host invocations).

When gate (b) is satisfied, the deletion may proceed via standard `fruit → winnow → molt`. The MB8 dim continues to monitor for post-deletion regressions during the next 30-day decay window.

### Relation to ratchet dims (v0.7.2+)

The discipline is mechanically enforced by:

- **MB8** (metabolic, MEDIUM) — counts shim-path hits and reports sunset eligibility.
- **MF5** (mechanical, MEDIUM, v0.7.3 reclassified) — flags MIRROR_DRIFT between project-scope and bundle-scope copies of v0.6.11 plugin files (the discipline applies symmetrically to plugin mirrors: byte-identical pairs are the desired state, divergence is real lint).
- **`scripts/sync_plugin_mirrors.py`** (v0.7.3+) — idempotent sync helper invoked by `bump_version.py` post-bump and `build_plugin.py` pre-build. Project-scope `.claude/<dir>/X.md` is the SSoT.
- **risk_classifier recursion-cutter** (v0.7.2+) — `src/myco/mcp/**` + `.myco_state/shim_hits.json` are HIGH-tier paths; any craft touching them auto-classifies as HIGH-risk owner-gated. Compound multi-cluster `path_allowlist` (touching state + shim + canon simultaneously) is also HIGH per mycoparasite T6.

### What this discipline does NOT cover

- **Doctrinal renames** (e.g., `genesis/` → `germination/` at v0.5.3) use Python re-export shims with their own removal cadence; these are governed by craft + the standard fruit→winnow→molt path.
- **Internal API changes** (functions / classes inside `src/myco/` consumed only by other `src/myco/` modules) — gate (a) handles these mechanically.
- **First-time external API additions** — adding a new public entry point is a v0.6.0-style craft decision, not a deletion.

## Cowork plugin artifact extension (v0.7.4+)

> **Status**: APPROVED (2026-05-09, v0.7.4 hotfix landed).
> **Constraint origin**: external — Anthropic Claude Desktop upload validator.

The Cowork plugin bundle (built by `scripts/build_plugin.py` from `.cowork-plugin/`) MUST be emitted with the **`.zip` extension**, not `.plugin`. This is a v0.7.4 hotfix correcting a v0.5.20–v0.7.3 misreading of Claude Desktop's plugin upload contract.

### What changed

- `BUNDLE_EXTENSION` (in `src/myco/boundary/install/plugin_bundle.py`) is now `".zip"`.
- `dist/myco-<ver>.zip` replaces `dist/myco-<ver>.plugin` as the GitHub Release asset.
- `release.yml` glob is `dist/myco-*.zip` (filters out `myco-<ver>.tar.gz` from `python -m build`; `.whl` filenames don't match).
- `tests/integration/test_install_cowork_plugin.py` carries a regression test asserting `BUNDLE_EXTENSION == ".zip"`.

### Why

Claude Desktop's plugin file picker advertises both `.zip` and `.plugin` (the picker filter regex in `app.asar` is `/\.(zip|plugin)$/i`), so v0.5.20 chose `.plugin` for the semantic clarity of "this is a plugin archive, not arbitrary ZIP." That choice was wrong:

- The **upload handler** (a different code path inside Claude Desktop than the file picker) rejects every extension except `.zip` with the error message `"Only .zip files are accepted."`.
- The UI swallows that specific error and surfaces only the generic `"Upload failed. You can try again."` or, in newer builds, `"validation failed"`.
- Anthropic GitHub issue **#40414** (open as of 2026-05-09, area:cowork, platform:windows, label:bug, label:stale) tracks this picker-vs-validator mismatch. Anthropic has not signaled a fix date.
- A user on macOS hit the same path with the same error in issue **#42651** (closed as duplicate).

`.zip` works against today's validator, will continue to work after #40414 is fixed (the file picker accepts both), and is universally understood by every archive tool. There is no upside to switching back even when #40414 lands.

### Boundary subsystem rule (binding)

> Any future change that flips `BUNDLE_EXTENSION` away from `".zip"` MUST cite the resolved-and-verified state of Anthropic GitHub issue #40414 (i.e., the Anthropic engineer commit that lifted the validator restriction, plus a fresh dogfood run against a current Claude Desktop build). The regression test `tests/integration/test_install_cowork_plugin.py::test_bundle_extension_constant_is_zip` enforces this at gate time.

### Discovery trail (for future archaeology)

The bug was discovered post-v0.7.3-release when the owner's drag-drop install of `myco-0.7.3.plugin` into Cowork failed with `"validation failed"`. Investigation:

1. Inspected the bundle (4 files under `myco/`, byte-identical sha256 to a renamed-`.zip` copy → contents not the issue).
2. Verified plugin.json schema against [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference): `name` is the only required field; `mcpServers` and `skills` are auto-discovered from default locations → manifest contents not the issue.
3. Web-searched the exact symptom; landed on issue #40414 and #42651, which name the validator-vs-picker mismatch as the root cause.
4. Renamed the existing build to `.zip` extension, byte-identical contents → drag-drop succeeded.
5. v0.7.4 hotfix systematized the rename across the build script, CI workflow, tests, and user-facing docs.
