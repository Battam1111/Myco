---
type: craft
status: ACTIVE
created: 2026-04-15
target_confidence: 0.90
current_confidence: 0.88
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
trigger: "User mandate 2026-04-15: 彻底重构重写、涅槃重生一份 Myco，top-down / 步进式精化，从上到下建立完整映射关系，避免下层不符合上层。"
audit_evidence:
  - code_layer_audit_2026-04-15  # 24,166 LoC; 3 megafunctions; 34 redundancy pairs; 350+ dead LoC
  - substrate_layer_audit_2026-04-15  # 8 identity labels; v0.6.0/v0.45.0/v0.46.0 non-monotonic; 50 ACTIVE crafts; L0-L3 conflated
scope: greenfield_rewrite  # v0.4.0 major; hard break; ASCC migration via script
out_of_scope:
  - specific lint dimension retention list  # deferred to L3 implementation craft
  - error-model migration mechanics         # deferred to implementation sub-craft
  - README translation pipeline decision    # explicit escalation to user
---

# Myco v0.4.0 Greenfield Rewrite — Top-Down Architecture

## §0 Problem Statement

Two parallel Opus sub-agents (≥30 tool uses each) audited the code layer and
the substrate/doctrine layer of Myco v0.3.4. Their combined findings paint a
consistent picture: **Myco has accreted past the maintainer's ability to keep
doctrine in sync with code.** Specifically —

- **Code**: 24,166 LoC across 53 flat files; three megafunctions over 2,000 LoC
  each (`immune.py` 4,400, `mcp_server.py` 3,385, `notes.py` 2,931); three
  redundant project-root discovery paths; three overlapping error models
  (silent-fail / dict-errors / exceptions); ~350 LoC of never-triggered
  speculative infrastructure (`evolve.py`, `redact.py`, `propagate_cmd.py`);
  v0.3.4 bandaids (`_skeleton_downgrade`, `_gitignore_downgrade`) that patch
  leaks in the severity layer without fixing the leak.

- **Doctrine**: eight competing self-descriptions for what Myco *is* (substrate,
  organism, knowledge system, OS, kernel, framework, agent-half, autopoietic
  niche); the L0/L1/L2/L3 layering (vision → contract → subsystem doctrine →
  implementation) exists nowhere as a clean hierarchy — it's conflated across
  `MYCO.md`, `CLAUDE.md`, `docs/vision.md`, `docs/architecture.md`,
  `docs/WORKFLOW.md`, `docs/agent_protocol.md`, and `wiki/`; a non-monotonic
  version sequence (v0.46.0 → v0.6.0 → v0.45.0 in `contract_changelog.md`);
  97 craft docs (50 ACTIVE, 47 archived) = 52% still in deliberation, double
  the sane steady state.

The user's directive is unambiguous: **刮骨疗伤 / 涅槃重生 / top-down / 建立完整
映射 / 下层不得违反上层**. Incremental refactor will not satisfy this — every
accretion wave has failed to retire the previous wave's residue.

This craft designs the replacement. **It does not implement it.** The
implementation is a separate workstream, gated on user approval of this design.

---

## §1 Round 1 — 主张 (Initial Proposal)

### §1.1 Design Principles (L-prime, the principles that govern the layers)

Before naming layers, name the invariants they must satisfy:

| # | Invariant | Why |
|---|-----------|-----|
| P1 | **One identity, one metaphor** | Eight self-descriptions = no identity. Every self-reference uses the same 1-sentence anchor. |
| P2 | **Each layer references only layers above it** | No upward references. L3 cites L2; L2 cites L1; L1 cites L0. Lint enforces mechanically (new L-dim). |
| P3 | **Every L(n+1) entity maps to exactly one L(n) parent** | Module → Subsystem → Contract rule → Identity anchor. Orphans are illegal. |
| P4 | **One canonical implementation per concept** | No three ways to find project root. No three error models. No three link-checkers. |
| P5 | **Speculative infrastructure is deleted** | YAGNI. Re-add when needed, not before. |
| P6 | **Version monotonicity is mechanical** | SemVer is enforced by release tooling, not trust. |
| P7 | **Craft output compresses; craft evidence archives but is never deleted** | Separate the product (doctrine) from the process evidence. |

### §1.2 The Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ L0 VISION — one paragraph, immutable, sealed                    │ 1 file
├─────────────────────────────────────────────────────────────────┤
│ L1 CONTRACT — protocol.md + _canon.yaml + version semantics     │ 2 files
├─────────────────────────────────────────────────────────────────┤
│ L2 DOCTRINE — one doc per subsystem (5 subsystems)              │ 5 files
├─────────────────────────────────────────────────────────────────┤
│ L3 IMPLEMENTATION — code modules, tests, symbiont adapters      │ ~30 files
├─────────────────────────────────────────────────────────────────┤
│ L4 SUBSTRATE — runtime state: notes/, forage/, log.md           │ generated
└─────────────────────────────────────────────────────────────────┘
```

Each layer has **exactly one directory root** and **exactly one entry point**.
The entry point is the only thing a new agent or contributor must read to
understand that layer.

### §1.3 L0 — Vision (identity, metaphor, audience)

**File:** `L0_VISION.md` (root of repo, replaces today's scattered identity prose).

**Content (exactly one paragraph, target 100-150 words):**

> Myco is a symbiotic cognitive substrate for coding agents. An agent brings
> capability; Myco brings continuity — the memory, the health checks, the
> discipline that survives across sessions. The metaphor is fungal: Myco grows
> under the agent's work, metabolizing raw notes into digested knowledge,
> circulating references between modules, maintaining homeostasis via
> self-lint. The agent is the symbiont, not the owner. Humans direct, agents
> execute, Myco remembers. Out of scope: being a chat UI, a model provider,
> a project manager, or a personal note app. Myco is what makes an agent
> *accountable for its own cognition*.

**One metaphor**: mycelium / substrate / fungal (biological).
**One audience**: coding agents working with human directors.
**Banned vocabulary from L0**: "knowledge system", "OS", "kernel", "framework",
"agent's other half", "autopoietic niche". These all appear today and dilute
the anchor.

### §1.4 L1 — Contract (the rules + the numbers + the versioning)

**Files:**
1. `L1_CONTRACT/protocol.md` — replaces `docs/agent_protocol.md`. Seven rules, no more.
2. `L1_CONTRACT/_canon.yaml` — the SSoT for numbers, paths, schemas.
3. `L1_CONTRACT/versioning.md` — SemVer discipline + release ritual.

**The Seven Rules** (consolidated from MYCO.md's 7 + CLAUDE.md's 6; removes the current mismatch):

| # | Rule | Enforced by |
|---|------|-------------|
| R1 | Boot with `myco hunger`; end with `myco reflect` + `myco immune --fix` | Hook + lint |
| R2 | Every substantive decision / friction / insight → `myco eat` immediately | Agent discipline; lint detects silence |
| R3 | Before factual claims about the project, call `myco sense` | Agent discipline |
| R4 | Writes only to paths in `_canon.yaml::write_surface.allowed` | L-dim (mechanical) |
| R5 | Every new file cross-references its neighbors (no orphans) | L-dim (semantic) |
| R6 | Decisions of class `kernel_contract` or `high_risk` go through 3-round craft | L-dim (mechanical) |
| R7 | SemVer is monotonic; release only through the release ritual | CI + L-dim |

**Drop from current contract**: the speculative bullets about cross-project
distillation and "subscription loop" — those are features, not contract rules.
The contract is the minimum invariant set, not the feature wishlist.

**`_canon.yaml` restructure**: every top-level section must have a `purpose:`
field. Sections without purpose are removed or merged. Target: ≤300 lines
(currently 745).

**Versioning**: strict SemVer. The v0.6.0/v0.45.0/v0.46.0 non-monotonicity is
frozen into the legacy-branch archive; v0.4.0 starts a clean sequence.
Pre-release stays v0.x.y until a deliberate 1.0 decision.

### §1.5 L2 — Doctrine (five subsystems, one doc each)

The biological metaphor yields five natural subsystems. Each is a **complete
functional unit** that can be designed, tested, and reasoned about
independently.

| Subsystem | Role | Replaces scattered modules today |
|-----------|------|----------------------------------|
| **Genesis** | Substrate creation + first-contact bootstrap | `inoculate.py`, `autoseed.py`, `germinate.py`, `seed_cmd.py` |
| **Ingestion** | Raw knowledge intake | `notes_cmd.py::run_eat`, `absorb_cmd.py`, `forage.py` + `forage_cmd.py` |
| **Digestion** | raw → refined (status lifecycle, compression) | `notes_cmd.py::run_digest/run_prune`, `condense_cmd.py` |
| **Circulation** | Cross-reference graph + retrieval | `mycelium.py`, `colony.py`, `memory.py`, `memory_cmd.py`, MCP compute functions |
| **Homeostasis** | Health + lint + reflection + version sync | `immune.py`, `pulse_cmd.py`, `reflect`, `metabolism.py`, `reflex.py` |

**Each L2 doc has a fixed structure:**
```
# <Subsystem>
## Purpose (1 sentence)
## Contract invariants (bullet list, each mapping to an L1 rule)
## Surface (CLI commands + MCP tools owned by this subsystem)
## State (data files owned, schemas referenced)
## Interactions (which other subsystems it calls; strict layer direction)
## Doctrine (the shape of the design; WHY this way)
```

**Mapping lock (P3)**: every L3 module declares `subsystem: <one of the five>`
in its module docstring. Lint enforces that every module has exactly one
subsystem tag and that the module lives in the corresponding directory.

### §1.6 L3 — Implementation (≤30 code modules, pluggable where it matters)

**New `src/myco/` layout:**
```
src/myco/
  core/                    # Shared kernel — NO business logic
    __init__.py
    project.py             # ONE project-root discovery function
    config.py              # ONE config loader
    errors.py              # ONE error-model (MycoError + typed subclasses)
    io.py                  # Atomic writes, YAML load, file hygiene
  genesis/
    bootstrap.py           # Merged inoculate + autoseed + germinate
    seed.py                # Merged from seed_cmd.py; split by level if needed
  ingestion/
    eat.py                 # write_note + frontmatter composition
    absorb.py              # external artifact import
    forage.py              # manifest-driven tracking
  digestion/
    lifecycle.py           # status transitions: raw→digesting→integrated/extracted
    compress.py            # forward-compression primitive
    hunger.py              # hunger_report (moved from notes.py)
  circulation/
    mycelium.py            # link graph (unchanged conceptually)
    retrieval.py           # sense + interconnection (extracted from mcp_server)
  homeostasis/
    immune/                # PACKAGE, not a file
      __init__.py          # dimension registry + runner
      mechanical/          # one file per L-dim in this category
      shipped/
      metabolic/
      semantic/
    pulse.py               # health check
    reflect.py             # session reflection
  surface/
    commands.py            # ONE manifest declaring all CLI + MCP commands
    cli.py                 # thin; reads manifest, dispatches
    mcp.py                 # thin; reads manifest, registers tools
    hooks.py               # session hooks
  symbionts/               # largely unchanged; already clean
    __init__.py
    <per-adapter>.py
```

**Module size cap: ≤500 LoC each.** `immune.py` at 4,400 LoC becomes
`homeostasis/immune/` as a package with ~20 small dimension files + a
~200-line runner.

**Command manifest (`surface/commands.py`)**: single source for CLI + MCP.
Each command declared as a dataclass entry: name, subsystem, args, handler,
exposed_on (cli|mcp|both). Eliminates 14 `*_cmd.py` wrapper modules. Solves
the CLI/MCP duplication finding from the audit.

### §1.7 L4 — Substrate (runtime state, generated; unchanged shape, cleaner schema)

Paths unchanged (`notes/`, `forage/`, `log.md`, `.myco_state/`) so migration
is a data-only operation.

Changes:
- **Note frontmatter schema versioned**: add `schema_version: 2` field. Migrations are code (`myco migrate`).
- **Tag vocabulary declared**: `_canon.yaml::tags.vocabulary` lists permitted prefixes (e.g., `system-*`, `friction-*`, `decision-*`). Free-form tags outside vocabulary flagged MEDIUM.
- **Craft doc status machine enforced**: DRAFT → ACTIVE → COMPILED → ARCHIVED. No other values. Lint enforces.
- **Craft compression cadence**: every 14 days OR when `primordia/*ACTIVE*` count exceeds 20, whichever first. Compresses ACTIVE → COMPILED, moves old COMPILED → archive/. Target steady state: ≤15 ACTIVE crafts.

### §1.8 Lint dimension reorganization (≤20 dimensions, category-capped)

**Category caps:**
- `mechanical` ≤ 6 (schema/path/count contracts)
- `shipped` ≤ 5 (user-facing surfaces)
- `metabolic` ≤ 5 (health signals)
- `semantic` ≤ 4 (cross-reference integrity)
- **Total ceiling: 20**

Current 30 dimensions need to drop 10. Specific retention decisions deferred
to the L3 implementation craft (see §2.5 attack response). But three
consolidations are already identified from the audit:

- L1 / L12 / L14 all do "reference → target exists" → **merge into one
  parametric `reference_integrity` dimension**.
- L19 / L21 both do "contract version inline consistency" → merge.
- L28 / L29 both touch version SSoT → merge into one `version_discipline`
  dimension.

That's three merges, saving 5 dimensions. Seven more decisions in the
implementation craft.

**New L-dim (mandatory for this architecture)**:
- `layer_hierarchy` (mechanical) — every doc/module's frontmatter-declared
  layer must match its filesystem path. Enforces P2.

### §1.9 Exit code policy (baked in, not opt-in)

v0.4.0 default for `myco immune`:
```
--exit-on=mechanical:critical,shipped:critical,metabolic:never,semantic:never
```

Legacy `2 if critical else (1 if high else 0)` mode is removed. `--exit-on=legacy`
is NOT a supported value. CI doesn't need `|| echo` workarounds because
metabolic/semantic intentionally never fail CI (they fail reviews).

### §1.10 Translation strategy (escalated decision)

**Explicit escalation to user in Round 3.**

Three options:
- (A) Keep all three READMEs, keep L20 mirror-lint; accept ongoing maintenance burden.
- (B) English canonical only; delete zh/ja; remove L20.
- (C) English canonical + `docs/readme_zh.md` + `docs/readme_ja.md` generated by translation pipeline at release time; L20 removed.

**Recommendation**: (C), but this is user's call (user is also the translator).

### §1.11 Migration for ASCC

Single script `myco migrate --from 0.3 --to 0.4 --project-dir <path>`:
- Rewrites `_canon.yaml` to new schema.
- Adds `schema_version: 2` to all notes.
- Updates `synced_contract_version`.
- Rewrites references to renamed commands (if any).
- Dry-run mode + diff output; destructive only with `--execute`.

---

## §2 Round 1.5 — 自我反驳 · Round 2 修正

Eight attacks on the Round-1 proposal; the survivors shape Round 2.

### §2.1 Attack A1 — "Craft compression loses debate history"

**Attack**: Collapsing 50 ACTIVE craft docs into 5 subsystem doctrine docs
destroys the deliberative evidence. Myco's own W3 principle says *traditional
craft* demands preserving the debate. This proposal contradicts it.

**Response** (holds): Separate the *product* from the *evidence*. The L2
doctrine doc is the *compiled output* of past crafts for that subsystem. The
craft docs themselves move to `docs/primordia/archive/` grouped by subsystem,
and each L2 doctrine doc has a `sourced_from:` frontmatter listing the
compiled crafts. Debate history is preserved; it just stops being in the
working-set navigation path. Compression is a Myco-native idea (W13
Primordia 压缩); applying it to itself is correct.

**Revision (Round 2)**: Add to L2 doctrine template:
```
sourced_from:
  - primordia/archive/ingestion/craft_X.md
  - primordia/archive/ingestion/craft_Y.md
```

### §2.2 Attack A2 — "Single-source CLI/MCP manifest may fight FastMCP"

**Attack**: FastMCP uses decorator-based schema inference. A declarative
manifest may not play nicely; we could end up dual-maintaining anyway.

**Response** (partial concession): Valid risk. Can't be certified without a
spike.

**Revision (Round 2)**: Phase 0 of implementation is a **spike** — build 3
real commands through the manifest + FastMCP adapter. If the spike fails,
fallback to: manifest drives CLI; MCP uses decorators but CI lint checks that
every MCP tool has a manifest entry and vice versa. Either way, the
invariant "one source of truth per command" holds.

### §2.3 Attack A3 — "Genesis as a subsystem is a stretch; it runs once"

**Attack**: Ingestion/Digestion/Circulation/Homeostasis are ongoing
processes. Genesis runs exactly once per substrate lifetime. Lumping it with
the four ongoing subsystems is categorical confusion.

**Response** (reject attack): Genesis runs once per *substrate*, but Myco is
consumed by downstream projects; each downstream runs genesis once. Across
the fleet, genesis is continuously exercised. More importantly, genesis
touches multiple cross-cutting concerns (canon generation, note scaffolding,
symbiont install) that need their own doctrine — they don't fit under any of
the other four. Keeping Genesis separate is correct.

**Revision (Round 2)**: Reinforce in the L2 Genesis doctrine that it's a
first-contact subsystem; lifecycle section makes this explicit.

### §2.4 Attack A4 — "Deleting speculative infra loses optionality"

**Attack**: `evolve.py`, `redact.py`, `propagate_cmd.py` represent partially
designed futures. Delete them and you lose the thinking that went into them.

**Response** (holds): The *thinking* lives in the craft docs that inspired
them — those remain in archive. The *code* is 350 LoC of surface area that
poisons navigation and implies features exist that don't. YAGNI.

**Revision (Round 2)**: none. Deletion stands. If a future wave needs any of
these, the relevant archived craft is the starting point.

### §2.5 Attack A5 — "≤20 lint dimensions is a commitment without a retention list"

**Attack**: A top-down design that says "cap at 20" but defers which 10 to
drop is hand-waving. Either specify the list or admit the cap is aspirational.

**Response** (partial concession): True. The architecture commits to the
category caps as invariants; the specific dimension list is an implementation
decision gated on reading each current dimension's code.

**Revision (Round 2)**: Make the cap **binding per category**:

| Category | Current count | v0.4.0 cap | Known consolidations |
|----------|---------------|------------|----------------------|
| mechanical | ~10 | ≤6 | L19+L21 merge; L28+L29 merge |
| shipped | ~7 | ≤5 | L2+L20 potential merge |
| metabolic | ~7 | ≤5 | L3+L26 potential merge |
| semantic | ~6 | ≤4 | L1+L12+L14 three-way merge |

Specific retention selection deferred to **L3 implementation craft
`lint_consolidation_craft.md`** — a dedicated 3-round decision, not hidden
in implementation work.

### §2.6 Attack A6 — "Error-model migration is the biggest change and the least specified"

**Attack**: Changing from {silent-fail, dict-error, exception} to one model
affects every module. Top-down design should not defer its largest single
refactor.

**Response** (concession on specification, not direction): The *invariant*
(one error model, surface-layer catches) is L1-level and must be in this
craft. The *migration mechanics* (which exceptions exist, how each current
try/except is rewritten) is implementation-level.

**Revision (Round 2)**: Pin the invariant in L1 protocol.md:
- Single base class `MycoError` with typed subclasses (`SchemaError`,
  `ReferenceError`, `WriteSurfaceError`, `VersionError`, etc.).
- Kernel code (L3 below surface/) raises; never catches.
- Surface code (`cli.py`, `mcp.py`, `hooks.py`) catches at the outermost
  boundary; converts to exit codes or JSON.
- No `except Exception: pass`. Lint enforces.

Implementation breakdown is tracked in the rewrite project plan (§4).

### §2.7 Attack A7 — "Doctrine layer enforcement relies on self-declared frontmatter"

**Attack**: L30 `layer_hierarchy` lint trusts frontmatter `layer: L2`. An
agent can lie — place an L3 impl detail in an L2 doc with `layer: L2`.

**Response** (partial holds): Agent can write wrong frontmatter, but the
*combination* of (path, frontmatter, content patterns) is mechanically
checkable:
- `path.startswith("L2_DOCTRINE/")` requires `layer: L2`.
- `layer: L2` requires presence of the fixed L2 doc structure sections.
- Missing "Contract invariants" section in an `layer: L2` doc → LOW.
- Any absolute file path like `src/myco/.../immune.py:...` in an L0/L1/L2
  doc → MEDIUM (implementation detail leaking up). 

The enforcement is layered (not a single check), which is appropriate for
a cross-layer invariant.

**Revision (Round 2)**: Expand L30 from one check to a small family:
`layer_path_match`, `layer_structure_match`, `layer_no_downward_leak`.

### §2.8 Attack A8 — "Public repo breaks in-flight contributors"

**Attack**: Project is public. Hard break on main breaks anyone midway
through a PR or fork.

**Response** (verify, then decide): User confirmed "项目处于公开状态"
implying visibility, not active external contribution. Action for user:
confirm there are no in-flight external PRs before cutover. If there are,
route them through legacy branch.

**Revision (Round 2)**: Cutover sequence:
1. Create `legacy/v0.3` branch, frozen at current `main`.
2. Tag `v0.3.4-final` on that branch.
3. Publicly announce the Greenfield rewrite (README banner).
4. `main` branch gets the rewrite.
5. External contributors can target either branch during a 30-day grace
   period; after that, legacy branch is archived, main is canonical.

---

## §3 Round 2.5 — 再驳 · Round 3 反思

### §3.1 Attack R2.1 — "Still too many top-level packages (8)"

**Attack**: `core/ genesis/ ingestion/ digestion/ circulation/ homeostasis/
surface/ symbionts/` = 8 packages. Current `src/myco/` has a flat structure
with ~53 files. Is 8 packages actually less cognitive load?

**Response**: The current flat 53 is worse because **navigation is
undirected**. 8 packages with ≤6 files each gives a 2-step path: pick
subsystem, pick module. The current flat structure has a 1-step path but
requires reading filename prefixes to guess grouping. 8 packages beat 53
files for navigation clarity — confirmed by the code audit's explicit
recommendation to "extract domain logic from mcp_server into subsystem
modules".

### §3.2 Attack R2.2 — "14-day craft compression cadence is magic"

**Attack**: Why 14 days? Why not 7, or 30?

**Response**: The target is the invariant ("≤20 ACTIVE crafts"); the cadence
is a tuning parameter. Start with 14 days; measure after 2 months; tune.
Specified as a soft config value in `_canon.yaml::craft.compression_cadence_days`,
not a hard-coded constant.

### §3.3 Attack R2.3 — "Does the user actually want 5 subsystems?"

**Attack**: The five (Genesis / Ingestion / Digestion / Circulation /
Homeostasis) came from the biological metaphor. Does that carve the problem
at the right joints, or is it aesthetics?

**Response**: The five correspond to observable categories of existing code:
- Genesis — ~1,500 LoC (inoculate + autoseed + germinate + seed_cmd)
- Ingestion — ~1,400 LoC (eat + absorb + forage)
- Digestion — ~3,700 LoC (notes_cmd digest + condense + hunger report)
- Circulation — ~1,400 LoC (mycelium + colony + memory + MCP compute)
- Homeostasis — ~5,500 LoC (immune + pulse + reflect + metabolism + reflex)

Each group ≥1,000 LoC. No group is so small it should merge; none so large
it must split (Homeostasis is largest but its internal split — immune as a
package, pulse/reflect separate — already addresses that). The joints are at
the right places.

### §3.4 Attack R2.4 — "This craft itself is 5000 words — isn't that more bloat?"

**Attack**: The rewrite's justification: "Myco has accreted too many crafts."
This craft adds one more craft, and a long one.

**Response** (concession + commitment): True. Commitment for Round 3:
- This craft is the **single reference** for the rewrite rationale.
- No additional meta-crafts are authorized during the rewrite.
- Sub-crafts (lint_consolidation, error_model_migration, command_manifest_spike)
  are tightly scoped implementation crafts with short (≤1000 word) targets.
- At v0.4.0 release, this craft is marked `COMPILED → ARCHIVED`; its
  distillation lives in the new `L2_DOCTRINE/` files.

### §3.5 Round 3 — 反思 (Reflection)

**What does the debate reveal about the problem shape?**

**Observation 1 — The accretion was normal; the deferral of compression
wasn't.** Wave 1-62 each added value. What accumulated was the *deferred*
work of retiring what each wave superseded. Greenfield is justified
*specifically because* the maintainer is solo and the deferred pile has
outrun the maintainer's ability to clear it incrementally. A team of 3
engineers could refactor in place; one engineer can't.

**Observation 2 — The single most important output is the layering
invariant (P2).** If "L(n+1) may only reference L(n) or above" is enforced
mechanically from day one, future accretions stay in their layer. The rest
of the design is negotiable; the layering invariant is not.

**Observation 3 — Everything else is negotiable.** Subsystem boundaries,
specific package names, lint dimension merges, cadence numbers — these can
adjust post-cutover without breaking the architecture. User should not
fixate on these in Round 3 review; user *should* fixate on:
- The seven L1 rules (is this the right minimum invariant set?)
- The five L2 subsystem carving (are these the right joints?)
- The three escalated decisions below.

**Observation 4 — Things to escalate to user** (I will not decide these unilaterally):

| Escalation | Options | My recommendation |
|------------|---------|-------------------|
| E1: CLI command renames | Keep iconic names (hunger/eat/digest/immune) vs. rationalize | **Keep iconic** — they're the project's identity |
| E2: Translation strategy | (A) keep 3 READMEs, (B) English only, (C) generate zh/ja | **(C)** — English canonical + generated |
| E3: Subsystem names | Biological (Genesis/Ingestion/...) vs. technical (bootstrap/io/...) | **Biological** — consistent with L0 metaphor |

**Observation 5 — What this craft must NOT become.** It must not expand
into module-level bike-shedding before the architecture is approved. All
L3-level decisions are correctly deferred to implementation crafts. If user
approves this L0-L2, L3 gets written next session with focused scope.

---

## §4 Implementation Plan (post-approval)

**This is a plan summary. Each phase is itself a gated decision.**

### Phase 0 — Spike + legacy freeze (1 session)
- Freeze `legacy/v0.3` branch; tag `v0.3.4-final`.
- Announce rewrite in README banner.
- **Spike**: build 3 commands end-to-end through the proposed manifest →
  CLI + MCP pattern. If spike succeeds, Phase 1 proceeds. If it reveals
  manifest ↔ FastMCP friction, fallback plan from §2.2 activates.

### Phase 1 — L0 + L1 (1 session)
- Write `L0_VISION.md`.
- Write `L1_CONTRACT/protocol.md` (the seven rules).
- Restructure `_canon.yaml` to ≤300 lines with purpose fields.
- Write `L1_CONTRACT/versioning.md`.
- Implementation craft: `error_model_migration_craft.md` (defines the
  `MycoError` hierarchy).

### Phase 2 — L2 doctrine docs (1 session)
- Write five L2 subsystem doctrine docs following the fixed template.
- Each cites its sourced-from archived crafts.
- Lint: L30 `layer_hierarchy` dimension implemented and activated.

### Phase 3 — L3 scaffold (2 sessions)
- Create new `src/myco/` layout (empty packages with __init__.py +
  purpose docstrings).
- Implementation craft: `lint_consolidation_craft.md` decides which 10
  dimensions merge/drop.
- Implementation craft: `command_manifest_craft.md` finalizes the dataclass
  schema for commands.

### Phase 4 — Subsystem migrations (5 sessions, one per subsystem)
- Genesis: move inoculate + autoseed + germinate + seed_cmd into
  `genesis/`; rewrite at ≤500 LoC per file; tests.
- Ingestion: same, for eat + absorb + forage.
- Digestion: same.
- Circulation: extract compute functions from `mcp_server.py` into
  `circulation/`.
- Homeostasis: immune/ package build; 20 dimension files; runner; tests.

### Phase 5 — Surface layer (1 session)
- `surface/commands.py` manifest populated.
- Thin `cli.py` + `mcp.py` wire from manifest.
- Hook scripts rewritten.

### Phase 6 — Substrate migration + ASCC (1 session)
- Notes schema v1 → v2 migration code.
- `myco migrate` command.
- Run against ASCC substrate; verify.
- Tag `v0.4.0`.

**Total**: 11 sessions, ~1-2 weeks elapsed.

**Gates between phases**: each phase ends with a report to user; user can
halt or redirect before next phase starts. No phase starts without explicit
"proceed" from user.

---

## §5 Complete Mapping Matrix (下层 → 上层 锁定)

The core top-down invariant: every L3 module cites an L2 subsystem; every
L2 subsystem cites L1 rules it upholds; every L1 rule cites the L0 identity
anchor it protects. This is the **mapping lock**.

### L1 → L0 (contract rules → identity anchor)

| L1 Rule | Protects L0 identity | Rationale |
|---------|----------------------|-----------|
| R1 boot/end rituals | "continuity across sessions" | No continuity without hand-off rituals |
| R2 eat on decision | "accountable for cognition" | Decisions without trace = no accountability |
| R3 sense before claim | "symbiont, not owner" | Claiming without checking = owner behavior |
| R4 write surface | "substrate shape preserved" | Free-for-all writes = substrate pollution |
| R5 cross-reference | "circulating references" | Orphans break the mycelium metaphor |
| R6 craft gate on kernel | "discipline that survives" | Discipline = not winging kernel changes |
| R7 SemVer monotonicity | "accountable cognition" | Version lies = cognitive dishonesty |

### L2 → L1 (subsystem doctrines → contract rules they implement)

| Subsystem | Implements rules | Owns state |
|-----------|------------------|------------|
| Genesis | R4 (initial write surface), R7 (canon versioning at birth) | `_canon.yaml` initial shape, `.myco_state/autoseeded.txt` |
| Ingestion | R2 (eat), R5 (cross-ref on intake) | `notes/*.md` raw |
| Digestion | R2 (lifecycle transitions are decisions), R5 (compression preserves refs) | `notes/*` status fields, `primordia/archive/` |
| Circulation | R3 (sense is circulation read), R5 (mycelium graph) | `mycelium` graph cache, `.myco_state/boot_brief.md` |
| Homeostasis | R1 (reflect/immune end rituals), R4 (write-surface lint), R6 (craft-gate lint), R7 (version lint) | `log.md`, `.myco_state/` health metrics |

### L3 → L2 (module tags — representative sample)

| Module | Subsystem tag | Justification |
|--------|---------------|---------------|
| `core/project.py` | — (shared kernel) | Used by all; no subsystem |
| `core/errors.py` | — (shared kernel) | Used by all; no subsystem |
| `genesis/bootstrap.py` | Genesis | First-contact substrate creation |
| `ingestion/eat.py` | Ingestion | Raw note intake |
| `ingestion/forage.py` | Ingestion | External artifact tracking |
| `digestion/lifecycle.py` | Digestion | Status transitions |
| `digestion/compress.py` | Digestion | Forward-compression |
| `digestion/hunger.py` | Digestion | Metabolic report (moves from notes.py) |
| `circulation/mycelium.py` | Circulation | Link graph |
| `circulation/retrieval.py` | Circulation | sense + interconnection |
| `homeostasis/immune/<dim>.py` | Homeostasis | Each dimension is a check |
| `homeostasis/pulse.py` | Homeostasis | Health snapshot |
| `homeostasis/reflect.py` | Homeostasis | Session self-assessment |
| `surface/commands.py` | — (surface layer) | Declarative manifest |
| `surface/cli.py` | — (surface layer) | Thin dispatcher |
| `surface/mcp.py` | — (surface layer) | Thin dispatcher |

Full module-to-subsystem map is part of Phase 3's implementation craft.

### L4 → L3 (substrate data → modules that own it)

| Data kind | Path | Owning subsystem | Lint dims that guard it |
|-----------|------|------------------|-------------------------|
| Notes | `notes/*.md` | Ingestion (write) + Digestion (transform) | schema, lifecycle, orphans |
| Canon | `_canon.yaml` | Genesis (init) + Homeostasis (lint) | schema, version, drift |
| Log | `log.md` | Homeostasis | format, append-only |
| Craft docs | `docs/primordia/*.md` | Homeostasis (enforce) | status machine, layer, body |
| Forage | `forage/*` | Ingestion | manifest match, hygiene |
| Boot brief | `.myco_state/boot_brief.md` | Circulation | freshness |

### Lint dimensions → which layer they enforce

| Dimension category | Enforces | Layer protected |
|--------------------|----------|-----------------|
| mechanical | schema/path/count contracts | L1, L4 |
| shipped | user-facing surface consistency | L1, L3 (surface) |
| metabolic | substrate health signals | L4 |
| semantic | cross-reference integrity | L2→L3 mapping, L3→L4 mapping |
| layer_hierarchy (new L30) | no downward references; path matches frontmatter | L0↔L1↔L2↔L3 |

---

## §6 Escalated Decisions (require user before Phase 0 begins)

| # | Decision | My recommendation | User choice needed? |
|---|----------|-------------------|---------------------|
| E1 | Keep iconic CLI command names (hunger/eat/digest/immune/sense/pulse) | Keep | Yes |
| E2 | Translation strategy (A/B/C from §1.10) | C (generated) | Yes |
| E3 | Subsystem names (biological vs. technical) | Biological | Yes |
| E4 | Whether to include the "propagate" future feature anywhere in v0.4.0 | Delete entirely; re-add in v0.5 if needed | Yes |
| E5 | Whether to preserve the Wave numbering system post-rewrite | Drop it; SemVer + dates suffice | Yes |
| E6 | Legacy branch retention period | 30 days grace, then archive | Yes |

---

## §7 Risks + Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Phase 0 spike reveals manifest↔FastMCP friction | MEDIUM | Fallback plan §2.2 activates |
| Implementation effort exceeds 11 sessions | MEDIUM | Phase gates let user halt/resume |
| Lint consolidation loses a load-bearing dimension | HIGH | Dedicated lint_consolidation_craft; each drop justified |
| ASCC migration breaks | HIGH | Dry-run mode mandatory before execute |
| Legacy branch neglected | LOW | 30-day policy documented |
| This craft document becomes accretion bloat | MEDIUM | Marked COMPILED→ARCHIVED at v0.4.0 release |

---

## §8 Approval Request

**User decision required before Phase 0 starts**:

1. **Architecture approval**: Is the L0→L4 layering + five-subsystem carving
   the shape you want? (Yes / No / Revise)
2. **Seven L1 rules**: Is this the right minimum invariant set? (Yes / No /
   Revise)
3. **Escalations E1–E6** (§6): your answer on each.
4. **Phase 0 authorization**: proceed with legacy freeze + spike?

**Nothing is pushed to origin until the rewrite reaches v0.4.0 tag AND you
separately approve the push.**

---

## §9 User Decisions (2026-04-15 — APPROVED)

Yanjun approved the craft and issued the following binding decisions:

### Architecture & Contract
- **L0→L4 architecture**: APPROVED as-is.
- **Seven L1 rules**: APPROVED as-is.

### Escalations
| ID | Question | Decision |
|----|----------|----------|
| E1 | CLI verb names | **Keep biological metaphors** (hunger / eat / sense / reflect / immune / propagate) |
| E2 | Substrate & doc migration | **Fresh re-export** — no in-place translation, no patching; regenerate clean |
| E3 | Subsystem naming | **Keep biological metaphors** (Genesis / Ingestion / Digestion / Circulation / Homeostasis) |
| E4 | `propagate` command | **Rewrite** — but must first redefine semantics, boundary, and interface under the new architecture, THEN implement. No direct port of the old impl. |
| E5 | Wave numbering | **Reset at v0.4.0** — Wave 1 starts fresh |
| E6 | `legacy/v0.3` branch | **Do not keep** as a long-lived branch. Tag `v0.3.4-final` as a history anchor only. |

### Execution constraints
- **No Phase 0 gate, no spike-blocking.** Phase 0 is dissolved; the 3-command manifest spike is integrated into Phase 2/3, not a pre-gate.
- **Proceed directly to full greenfield reconstruction.** Target = `v0.4.0`.
- **Strict top-down.** Lower-layer implementation must always conform to the approved upper layers.
- **Any conflict resolves in favor of the upper layer.** Implementation convenience does not override contract.
- **No reverse-erosion** of L0/L1/L2 for L3 convenience.
- **No push to origin** until v0.4.0 AND separate explicit approval.

### Revised phase plan
1. Record decisions (this §9) — DONE
2. Tag `v0.3.4-final` as history anchor; no `legacy/v0.3` branch retention
3. L0: write `L0_VISION.md`
4. L1: write contract docs + restructure `_canon.yaml`
5. L2: write five subsystem doctrine docs + redefine `propagate`
6. L3: scaffold `src/myco/` 8-package layout + command manifest
7. L3: build core (error model, project discovery, version, manifest→CLI+MCP)
8. L3: migrate subsystems top-down, one at a time
9. L4: fresh substrate re-export + ASCC migration script
10. Tag `v0.4.0` (hold for push approval)

