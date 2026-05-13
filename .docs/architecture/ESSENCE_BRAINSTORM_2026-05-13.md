# Myco essence brainstorm — v0.8.8 strategic frame

> **Date**: 2026-05-13.
> **Status**: strategic note authored after v0.8.8 max-aggressive cleanup
> (commits `6e8bfa0` → `640949f`, 8 pass total). Captures the substrate's
> **distilled identity** and **kernel boundary** for the v0.9+ roadmap.
> Read alongside [`L0_VISION.md`](./L0_VISION.md) and
> [`L1_CONTRACT/protocol.md`](./L1_CONTRACT/protocol.md).
> **Scope**: NOT a contract change — this is a reflection document.
> Any L0/L1 amendment derived from this brainstorm must go through the
> standard `fruit → winnow → molt` cycle.
>
> **2026-05-13 owner correction recorded inline**: §5 originally listed
> "5 root principles + 3 invariants + 7 rules + 20 verbs + 7 subsystems
> + 47 dims + biological vocabulary + plugin axes + dual hook" as
> "non-negotiable identity". That was a category error — those are the
> **v0.8.7 current recipe (Beta)**, not the **essence (Alpha)**. Every
> item in that list has been mutated at least once between v0.4 and
> v0.8.7 (rule count, verb count, subsystem count, dim count, schema
> version, hook count all moved). The corrected three-layer
> decomposition lives at §0 (added below) and §5 (rewritten). The
> previous "IN list" frame would have made fundamental reconstruction
> ("彻底重构") impossible because it locked the recipe instead of the
> essence.

---

## 0. The three-layer decomposition (2026-05-13 correction)

Earlier drafts of this document conflated three distinct strata. To
make fundamental reconstruction tractable, separate them explicitly:

| Layer | Content | Reconstruction latitude |
|---|---|---|
| **α (Essence)** | The 6 atomic predicates below. The irreducible "what Myco is". | **Zero**. Removing any one turns Myco into a different kind of artifact (wiki / chatbot memory / RAG / notebook / fixed-schema database). |
| **β (Current recipe)** | 5 principles, 3 invariants, 7 rules, 20 verbs, 7 subsystems, 47 dims, biological vocabulary, canon-as-YAML, MCP+CLI surfaces, dual-hook discipline, plugin axes. | **Complete**. Any β item can be replaced with a different design that still satisfies α. None is "non-negotiable identity"; all have mutated at least once between v0.4 and v0.8.7. |
| **γ (Current implementation)** | 64 .py source files, the specific dependency graph, the specific test suite, the specific manifest.yaml, the cluster-merge file layout. | **Always**. γ moves whenever the recipe moves, and even when it doesn't (e.g. v0.8.8 cluster merges kept β stable but rewrote γ). |

### The α layer (6 atomic predicates — non-negotiable)

| # | Predicate | Why it's irreducible (the negative counterexample) |
|---|---|---|
| α1 | **Persistent** — the substrate survives the agent's read window. | If you drop persistence you have chatbot memory, not Myco. |
| α2 | **Mechanically self-validating** — the substrate enforces its own integrity invariants; the agent CANNOT silently corrupt it. | If you drop self-validation you have a wiki / shared notebook. |
| α3 | **Co-authored** — both the agent and the substrate's own machinery shape the substrate; the substrate's shape (schema) is itself first-class data. | If you drop co-authorship you have a fixed-schema database. |
| α4 | **Agent-readable** — the substrate is accessible to LLM agents through some protocol. | If you drop agent-readability you have an artifact for humans (documentation system). |
| α5 | **Protocol-coordinated** — there exists a shared grammar (whatever form) between the agent and the substrate. | If you drop the shared grammar you have a bag of files with no API. |
| α6 | **Continuity-of-self** — across sessions / hosts / agent instances, the substrate restores a "self" to the agent. | If you drop continuity you have per-session RAG, not a substrate. |

These 6 are the **only** things Myco cannot lose without becoming a
different kind of thing. The 5 root principles in L0 are a particular
projection of α onto a particular vocabulary; α is what survives if L0
itself were rewritten.

### The β layer (current recipe — completely re-architectable)

Every item below is a β-layer design choice. **None of them are
non-negotiable.** Each could be replaced with a different design that
still satisfies α:

| β choice | Why it's β, not α | Reconstruction-space example |
|---|---|---|
| 5 root principles (L0) | Particular projection of α onto a vocabulary; L0 itself is owner-mutable. | Could be 3 principles, 8 principles, or zero principles + direct α statement. |
| 3 derived invariants | Derived from the 5 principles. | Falls out of whatever principle set replaces L0. |
| 7 hard rules R1-R7 (L1) | L1 itself says "Adding an eighth rule requires a craft + bump + approval". Rule count has been disputed historically (MYCO.md=7 vs CLAUDE.md=6 before alignment). | Could be 3 rules, 12 rules, or a totally different rule grammar (e.g. capability-based). |
| 20 verbs | History: 6 → 11 → 17 → 19 → 20. | Could be 5 verbs (CRUD-shaped), 50 verbs (fine-grained), or even 0 verbs (raw graph operations exposed). |
| 7 subsystems | History: 5 (v0.4) → 6 (cycle, v0.5.3) → 7 (boundary, v0.6.0). | Could be 3 mega-subsystems, 15 micro-subsystems, or no subsystem partition at all. |
| 47 immune dimensions | History: 11 → 25 → 30+ → 51 → 47. | Could be replaced entirely by a type system, property-based tests, or a runtime contract DSL. |
| canon schema | History: v1 → v2 → v3 → v4 (every anamorph bump). | Could be JSON Schema, protobuf, SQLite metadata table, or in-memory dataclass. |
| biological vocabulary | L0 locks it but L0 itself is owner-mutable. | Could be military terms, mathematical terms, geological terms, or arbitrary symbols. The metaphor is the *agent's prior*, not the substrate's identity. |
| canon-as-YAML | One serialization choice. | Could be TOML, JSON, sqlite, in-memory dataclass with file mirror. |
| MCP + CLI surfaces | Two protocol implementations. | Could be REST, GraphQL, gRPC, direct function calls, or shared-memory IPC. |
| dual-hook discipline | History: single hook (pre-v0.5.7) → dual hook → potentially tri-hook. | Could be polling-based, signal-driven, daemon-based, or hook-less with explicit verb calls. |
| `.myco/plugins/` + JsonClientSpec axes | Two extension axes (per-substrate + per-host). | Could be one axis (per-tenant), three axes (per-substrate + per-host + per-team), or a single capability registry. |

### Why this matters for "彻底重构"

A reconstruction that preserves α and rewrites β is still Myco — just a
different recipe. A reconstruction that preserves β but breaks α is no
longer Myco — same recipe, different essence. The earlier "IN list"
locked β as identity, which would have made true reconstruction
impossible (every β change would have read as a Myco-killing breach).
By relocating identity to α, the design space for v0.9+ opens up: the
question becomes "what β satisfies α best given today's constraints?"
not "how do we minimally tweak the v0.8.7 β?".

---

## 1. The essence — one sentence

> **Myco is a verb-grammar contract for agent ↔ persistent-substrate
> coordination, where both the substrate's shape (`canon`) and the
> agent's behaviors (`R1-R7`) are first-class mutable objects under
> continuous, lint-gated evolution.**

## 2. The essence — one paragraph

Myco bets that LLM agents operating across sessions, hosts, and federated
substrates need a **shared coordination grammar** with the substrate they
work on — the way `cp`/`mv`/`grep` outlive any single editor's UX because
the filesystem outlives any editor's process. The bet is bounded by L0's
Living Bets appendix: it **wins** when the substrate's persistence budget
exceeds any single agent's read window; it **loses** on ephemeral single-
session work where raw context-holding suffices. The grammar is 20
fungal-named verbs. The substrate's identity is `_canon.yaml` (single
source of truth). The agent's discipline is 7 hard rules (R1-R7). The
substrate's self-validation is 47 immune dimensions across 4 categories.
The whole thing is for the agent; humans enter only through one carved
exception (`myco brief`) and as governance approvers for `fruit`/`molt`
craft cycles.

## 3. What Myco is NOT (the negative space)

The five-line "Not" list from L0 is load-bearing — it defines Myco by
exclusion. Mapping each "not" to a misread the user has not yet made:

| Mis-frame | The reality |
|---|---|
| RAG / vector memory | Structured graph with explicit edges; R5 cross-reference is mandatory at creation. Embeddings are not Myco's job. |
| Documentation tool | Agent-only consumption (P1). Humans browse incidentally; the design target is the agent. |
| Single-project KB | General-purpose substrate. Project affiliation is a tag on nodes, not a boundary on the substrate. |
| Chatbot memory | Durable, self-validating, lint-checked. Conversational recall is incidental. |
| Version control | Git owns history; Myco owns *current shape*. |
| File synchronizer | Even `propagate` is semantic (integrated notes), not bytes. |
| LLM wrapper | The substrate **never** calls the LLM; the agent does. MP1 mechanically enforces. |
| Static config | Canon is a mutable contract; `molt` is a normal operation. |

## 4. The kernel — what could not be cut without breaking the contract

### Tier 0 — Absolute kernel (5 modules, ~2700 LOC)

These are the modules without which there is no Myco — only a directory
of files. Every other module depends transitively on this set; nothing
in Tier 0 depends on anything outside Tier 0.

| Module | Role | LOC |
|---|---|---|
| `core/canon.py` | Load / validate / upgrade `_canon.yaml` (the SSoT). | 787 |
| `core/substrate_cluster.py` | `Substrate.load` + write-surface paths + plugin loader. | 521 |
| `core/identity_cluster.py` | `MycoContext` + error hierarchy + `Severity` enum + version primitives. | 347 |
| `core/trust_cluster.py` | `check_write_allowed` — the R6 enforcement seam. | 387 |
| `boundary/surface/manifest.py` | 20-verb dispatch grammar (SSoT for CLI + MCP). | 624 |

### Tier 1 — The 5 root principles realised (the 7 subsystems)

Each subsystem projects ≥1 L0 principle into runtime code. Removing a
subsystem removes the principle it implements:

| Subsystem | Implements | Core file(s) |
|---|---|---|
| **germination** | P3 (永恒进化, starting state) | `germination/germinate.py` |
| **ingestion** | P2 (永恒吞噬) + R1 + R3 + R4 | `ingestion/{capture,curate}_cluster.py` |
| **digestion** | P3 + P4 (evolution + iteration) | `digestion/cluster.py` |
| **circulation** | P5 (万物互联) | `circulation/{graph,graph_src,traverse_propagate_cluster}.py` |
| **homeostasis** | Invariant 2 (self-validating substrate) | `homeostasis/kernel.py` + 14 dim cluster files |
| **cycle** | P3 + P4 governance | `cycle/{canon,signal}_cluster.py` + `cycle/{winnow,ramify}.py` |
| **boundary** | Invariant 1 (agent-only consumption surface) | `boundary/surface/{cli,mcp,manifest}.py` + `boundary/install/*` |

### Tier 2 — The 20 verbs (the coordination grammar)

Grouped by their R-rule and L0-principle linkage (verbs in **bold** carry
direct hard-contract weight):

| Verb | R-rule | Principle | Subsystem |
|---|---|---|---|
| germinate | bootstrap | P3 | germination |
| **hunger** | **R1** (mandatory boot) | P2 reflex | ingestion |
| **eat** | **R4** (capture-now) | P2 | ingestion |
| **sense** | **R3** (sense before assert) | P1 | ingestion |
| forage | recon for eat | P2 | ingestion |
| excrete | inverse of eat | P2 | ingestion |
| intake | bulk forage+eat | P2 | ingestion |
| assimilate | raw → integrated (bulk) | P4 | digestion |
| digest | raw → integrated (single) | P4 | digestion |
| sporulate | integrated → distilled proposal | P3 | digestion |
| traverse | mycelium graph walk | P5 | circulation |
| propagate | federate to peer substrate | P5 | circulation |
| immune | R5 + R6 + R7 + invariant 2 lint | inv 2 | homeostasis |
| **senesce** | **R2** (session-end ritual) | P4 | cycle |
| fruit | author craft proposal | P3 | cycle |
| molt | bump `contract_version` | P3 | cycle |
| winnow | validate craft shape | P3 | cycle |
| ramify | scaffold new code | P3 | cycle |
| graft | introspect local plugins | P5 | cycle |
| **brief** | **human-facing exception** | P1 carved | cycle |

Five verbs carry hard-contract weight; the other 15 implement principles
2-5 mechanically.

## 5. The boundary — α (non-negotiable) vs β (currently shipped recipe) vs γ (current implementation) vs OUT (already cut)

**Earlier framing**: this section originally listed β items as
"non-negotiable identity". That was the category error owner flagged
on 2026-05-13. Corrected below: only α is non-negotiable; β is
re-architectable; γ is implementation; OUT is the v0.8.8 excretion
roster.

### α — non-negotiable (rewriting any of these makes the artifact
no-longer-Myco)

The 6 atomic predicates from §0:
α1 persistent, α2 mechanically self-validating, α3 co-authored,
α4 agent-readable, α5 protocol-coordinated, α6 continuity-of-self.

### β — currently shipped recipe (re-architectable in v0.9+)

These satisfy α today but are not the only β that could satisfy α.
A v1.0 reconstruction may replace any subset:

- L0: 5 root principles + 3 derived invariants + biological metaphor +
  Living Bets appendix.
- L1: 7 hard rules R1-R7 + canon schema + exit codes.
- L2: 7 subsystems (germination, ingestion, digestion, circulation,
  homeostasis, cycle, boundary).
- L3: 20 verbs + 47 immune dimensions.
- canon-as-YAML at `_canon.yaml` (or `.myco/canon.yaml`).
- MCP stdio + streamable-HTTP transports + CLI argparse surface.
- Dual hook discipline (SessionStart=hunger, PreCompact=senesce-full,
  SessionEnd=senesce-quick).
- Two extension axes: `.myco/plugins/` + `JsonClientSpec`.

### γ — current implementation (always negotiable)

- 64 .py source files at v0.8.8 (down from 137 at v0.8.7 ship).
- The specific cluster-merge file layout.
- The specific dependency graph (PA4 core-no-subsystem-deps, etc.).
- 1268 tests + 47 dim entry-points + manifest.yaml dispatch table.

### OUT — v0.8.8 excretions (will not return)

- Specialized adapters (PDF / HTML / URL / audio / image_ocr / video /
  sqlite / git_history / email / chat_log). Re-addable via
  `.myco/plugins/adapters/`.
- Framework demos (agno / crewai / dspy / langgraph / smolagents /
  microsoft-agent / praisonai / claude-sdk).
- v0.6.13 `src/myco/mcp/` back-compat shim.
- `.docs/primordia/` archive.
- Per-boundary migration guides (collapsed to `HISTORY.md`).
- Benchmark gates.
- `[adapters]` / `[examples]` / `[multimedia]` optional extras.

### OUT (v0.8.8 excretions — will not return)

- Specialized adapters (PDF / HTML / URL / audio / image_ocr / video /
  sqlite / git_history / email / chat_log). These were I/O glue, not core
  logic. Re-addable via `.myco/plugins/adapters/`.
- Framework demos (agno / crewai / dspy / langgraph / smolagents /
  microsoft-agent / praisonai / claude-sdk). Marketing, not substrate code.
- v0.6.13 `src/myco/mcp/` back-compat shim. Sunset moved up from v1.0.0.
- `.docs/primordia/` archive. Git history preserves it.
- v0.5.24→v0.6.0, v0.7.4→v0.7.5, v0.7.x→v0.8.0 per-boundary migration
  guides. Collapsed to a single `migration/HISTORY.md`.
- Benchmark gates (`.tests/benchmark/`). Never ran in CI.
- `[adapters]` / `[examples]` / `[multimedia]` optional extras. Their
  target modules are gone.

### EDGE (kept after deliberate review)

- `boundary/install/` (10-MCP-host installer, ~1700 LOC). Not pure
  "core logic", but the substrate's reach into the agent's runtime.
  Kept.
- `cycle/ramify.py` (724 LOC, scaffolder). The most cuttable kernel-tier
  verb; a sufficiently smart agent writes new code directly. Kept for
  v0.8.x; flagged for re-audit at v0.9.
- `boundary/install/cowork_plugin.py` (Cowork plugin packaging).
  Tangential to core, but currently in the release flow. Kept.

## 6. Coupling diagram — how the pieces hang together

```
            ┌──────────────────────────────┐
            │  L0 VISION  (5 principles)   │  ← Owner-only mutation.
            └──────────────┬───────────────┘
                           │ governs
            ┌──────────────┴───────────────┐
            │  L1 CONTRACT (R1-R7 +        │  ← Versioned. molt-gated.
            │  canon schema + exit codes)  │
            └──────────────┬───────────────┘
                           │ realised by
   ┌───────────────────────┴───────────────────────────┐
   │             7-subsystem L2 doctrine               │
   └───────────────────────┬───────────────────────────┘
                           │ implemented at
       ┌───────────────────┴────────────────────┐
       │  CORE  (canon + substrate + identity   │  ← Tier-0 kernel.
       │         + io + trust)                  │     PA4 lint forbids
       └───────────────────┬────────────────────┘     core → subsystem
                           │ depended on by             dependency.
       ┌───────────────────┴────────────────────────────┐
       │  germination  ingestion  digestion             │
       │  circulation  homeostasis  cycle               │
       └───────────────────┬────────────────────────────┘
                           │ exposed through
                ┌──────────┴───────────┐
                │  BOUNDARY            │
                │   surface/cli.py     │ ← 20-verb argparse
                │   surface/mcp.py     │ ← 20-verb MCP tools
                │   surface/manifest   │ ← SSoT dispatch table
                │   install/clients.py │ ← 10-MCP-host writers
                └──────────┬───────────┘
                           │ talks to
                ┌──────────┴────────────┐
                │  LLM AGENT (the only  │  ← The sole consumer (P1).
                │  consumer per P1)     │
                └───────────────────────┘
```

**Critical invariant** (PA4 lint, mechanical): nothing in `core/`
imports from `germination/`, `ingestion/`, `digestion/`, `circulation/`,
`homeostasis/`, `cycle/`, or `boundary/`. The kernel is sealed at the
bottom — adding a subsystem dep to core is a contract-breaking change.

## 7. Critical realizations (the non-obvious truths)

### Realization 1 — The substrate is the database; Myco is the schema + grammar
Without `_canon.yaml`, there is no substrate — just a directory. Without
the 20 verbs, there is no API — just files. The two together form an
abstract machine the agent operates on.

### Realization 2 — Homeostasis is the kernel security model
The 47 lint dimensions aren't quality-of-life features. They are how the
substrate enforces R5/R6/R7 against itself at runtime. Removing immune
turns Myco from "self-validating substrate" into "directory of YAML
files".

### Realization 3 — The verbs are coordination protocol, not user interface
L0's Living Bets appendix is explicit: **verbs are not UI; they are a
grammar an Agent coordinates with**. The analogy is not "Myco is the
agent's IDE"; it is "Myco is the agent's filesystem". `cp` survives
modern IDEs because the filesystem outlives any IDE process. By the
same logic, `myco hunger` survives smarter agents because the substrate
outlives any agent's read window.

### Realization 4 — The biological metaphor is load-bearing, not decorative
L0 says: "Commands, subsystem names, and directory names at every layer
must match this taxonomy exactly. No alternate vocabulary." This is
mechanical: an agent reading the substrate cold derives intent from the
names. `hunger` → sensing-before-asserting reflex (R3). `senesce` →
session-end ritual (R2). The metaphor is the agent's prior over what
each verb does.

### Realization 5 — Living Bets is the meta-commitment
"The verbs survive in proportion to the substrate's persistence
budget." When that proportionality breaks down, Myco self-terminates
or redesigns. This is unique among "agent memory" systems — most
just assert their utility forever.

### Realization 6 — The kernel is small AND the perimeter is large
- Tier-0 kernel: ~2700 LOC across 5 files.
- Total substrate (post-v0.8.8): 19915 LOC across 64 files.
- Ratio: **13.6% is irreducible kernel; 86.4% is implementation of
  doctrine over it**.

This is the right shape. The kernel says little; the implementation says
everything.

## 8. Tension map — where the design has unresolved tensions

### Tension A — "Only For Agent" vs `boundary/install/`
Per P1, humans don't browse Myco. But `boundary/install` is a CLI the
**human** runs to set up `_canon.yaml` integration with Claude Desktop /
Cursor / etc. Resolution: install is a one-shot governance event
(similar to `myco brief`), not routine consumption. Accepted.

### Tension B — `cycle` has 7 verbs, more than most subsystems
Germination/Circulation/Homeostasis each have 1-2 verbs; Cycle has 7
(senesce + fruit + molt + winnow + ramify + graft + brief). Cycle is
juggling four distinct concerns: session lifecycle (senesce), schema
evolution (fruit / molt / winnow), code scaffolding (ramify), plugin
introspection (graft), human rollup (brief). **Possible resolution at
v0.9**: split into `cycle` (lifecycle) + `governance` (schema/plugin)
subsystems. This is an L0 amendment (adds an 8th subsystem) → not
trivial.

### Tension C — The 47-dim count is from accretion
- v0.5: 11 dims.
- v0.6.0: +21 → 25 dims (the unified-evolution craft).
- v0.7.x: +5 (CG1, CG2, LB1, LB2, SE5).
- v0.8.x: −5 retired (MF3, MB7, SE4, RL2, RL3).
- net: 47.

Many dims are L3-organization checks (DC1-5 docstrings, PA2 megafile,
PA6 repo bloat). Only ~15 enforce R1-R7 directly. **Possible
resolution**: classify dims into "contract-enforcing" (HIGH default)
vs "code-hygiene" (LOW default, opt-in CRITICAL via canon) tiers.

### Tension D — `core/canon.py` is at the PA2 cap edge
787 LOC out of 800. If schema v5 lands, canon.py grows past 800.
Split is mechanical but doctrinally interesting (canon is the SSoT —
splitting means choosing a sub-axis: load vs validate vs upgrade).

### Tension E — `manifest.yaml` is the dispatcher SSoT but lives outside the lint surface
1494 lines of yaml manifest. If a verb is added there and not
implemented in code, the failure mode is `ImportError` at first
invocation, not lint-fail. **Possible resolution**: a new dim that
walks `manifest.yaml::commands[].handler` and asserts each
`module:function` is importable. Cheap (~50 LOC).

### Tension F — MB8 (shim_hits telemetry) is now dead
v0.8.8 pass-5 deleted `src/myco/mcp/` shim. MB8's sole purpose was
counting shim invocations to time its sunset. With the shim gone,
the dim reads a stale `.myco/state/shim_hits.json` forever.
Excrete at v0.9.

## 9. Strategic next steps — proposed v0.9 / v1.0 work

Ordered by leverage (highest first):

### S1 — Re-audit Living Bets (commitment from v0.8.0 amendment)
L0 says "Every MAJOR release re-audits this appendix." v0.9 is the next
MAJOR. The audit question: across the 8 contract bumps from v0.6.0 →
v0.8.7, did verb usage track multi-session work as the bet predicted?
Concrete deliverable: a primordia draft classifying the last 100
sessions on the regime axis (multi-session-federated vs
ephemeral-single-session) and reporting verb-usage correlation.

### S2 — Dim roster tiering (Tension C resolution)
Reclassify the 47 dims into three buckets:
- **Contract dims (~15)** — enforce R1-R7 directly. Default HIGH/CRITICAL.
- **Hygiene dims (~25)** — L3 code-organization checks. Default LOW,
  opt-in CRITICAL via canon.
- **Metabolic dims (~7)** — substrate health (MB*). Already LOW/MEDIUM.

This gives external substrate operators a clean "what does Myco
strictly require" answer.

### S3 — Subsystem schism: `cycle` → `cycle` + `governance` (Tension B)
If the v0.9 audit shows cycle is overloaded, propose an L0 amendment
adding `governance` as an 8th subsystem. Move (fruit, molt, winnow,
graft, brief) → governance; keep (senesce, ramify) → cycle. The new
7→8 subsystem count is a contract change; needs craft + owner approval.

### S4 — Manifest.yaml lint (Tension E resolution)
Add a dim that walks `manifest.yaml::commands[].handler` and asserts
each `module:function` is importable. ~50 LOC, prevents the
ImportError-at-first-invocation failure mode.

### S5 — `canon.py` split (Tension D, conditional)
At schema v5, if and only if canon.py crosses 800 LOC. Sub-axes for the
split: `canon_load.py` (read + upgrade) + `canon_validate.py` (schema
enforcement) + `canon_write.py` (molt-driven mutation).

### S6 — Living Bets v0.9 falsifiability trigger
L0 says: "if a future Agent can maintain a 1M-file substrate without
structured verbs, Myco must re-justify or redesign". Build a stress-test
substrate (1M synthetic notes) and observe whether agent coordination
degrades without verb support. This is the falsifiable experiment that
either renews or retires Myco's wager.

### S7 — Doctrine consolidation pass
Current L2 has 9 docs (boundary, circulation, cycle, digestion,
extensibility, genesis, homeostasis, ingestion, release_discipline).
Several overlap. Propose merge to 5-6 (e.g., `genesis` →
`germination`; `release_discipline` → `boundary`; `extensibility`
section folded into respective subsystem docs).

### S8 — Excretion of MB8 + the shim_hits machinery (Tension F)
With `src/myco/mcp/` shim deleted in pass-5, MB8's sole purpose (shim-
invocation telemetry) is dead. Excrete MB8 + the
`.myco/state/shim_hits.json` reader.

### S9 — Ramify re-audit (Edge-case from §5)
`cycle/ramify.py` is 724 LOC — the largest cycle file. Question: does
a sufficiently smart agent need a scaffolder verb at all, or can it
write new code directly with `eat`/`write`/`molt`? If the v0.9 audit
shows ramify is rarely used in multi-session federated work, excrete
it (saves ~700 LOC + simplifies the verb count to 19).

## 10. The wager restated for v0.9+

Two wagers, separated by layer:

### α-layer wager (load-bearing — if this loses, Myco self-terminates)

Across the next 3-5 years of LLM evolution, agent intelligence grows
**but** the agent's read window remains finite, **and** substrates
exceeding that window remain valuable. Within that window:

- α1 (persistent), α2 (self-validating), α3 (co-authored), α4
  (agent-readable), α5 (protocol-coordinated), α6 (continuity-of-self)
  remain meaningful predicates.

If a future Agent can hold a 1M-file substrate entirely in context
without protocol mediation, α5 collapses (the agent IS the protocol)
and α2/α3 weaken (the agent can self-validate without external
machinery). At that point Myco's α justification needs re-derivation
or the project retires per L0 Living Bets cadence.

### β-layer wager (re-architectable — failing this triggers a v1.0 redesign, not a project end)

The **current** β (5 principles, 7 rules, 20 verbs, 7 subsystems, 47
dims, biological vocabulary, MCP+CLI surfaces) is the right recipe
**for today's agent capability**. Specifically:

- 20 verbs are a sweet spot at current Agent reading speed:
  small enough to fit in a single boot-brief glance, large enough
  to express the full state-machine of substrate ops.
- 47 dims at current accretion is over-tuned; v0.9 likely cuts.
- Biological vocabulary gives a useful prior; an alternative
  prior (mathematical / military / spatial) might give a better
  prior for some Agent classes.
- canon-as-YAML is the lowest-friction serialization given that
  every Agent today treats YAML as legible structured text.

If usage data from v0.9 audit (S1 — Living Bets re-audit) suggests
β over- or under-fits, β is fully replaceable without breaking α.
v1.0 may ship a completely different β.

### What this license to redesign enables

The "彻底重构" the owner is preparing for is NOT a contract amendment
inside the v0.8.7 β. It is a license to **draft a new β from scratch**
that:

- preserves all of α
- chooses its own verb count, vocabulary, dim count, schema format,
  protocol surface, hook discipline, extension axes
- inherits no β-layer item from v0.8.7 by obligation

The brainstorm at §0 §5 §10 sets up that latitude.

## 11. Cross-references (R5 satisfied)

- [`L0_VISION.md`](./L0_VISION.md) — source of truth on the five
  principles, three invariants, biological metaphor, and Living Bets.
- [`L1_CONTRACT/protocol.md`](./L1_CONTRACT/protocol.md) — R1-R7.
- [`L1_CONTRACT/canon_schema.md`](./L1_CONTRACT/canon_schema.md) — the
  schema this brainstorm calls "the SSoT".
- [`L3_IMPLEMENTATION/package_map.md`](./L3_IMPLEMENTATION/package_map.md)
  — the file-layout map this brainstorm references.
- [`../migration/HISTORY.md`](../migration/HISTORY.md) — boundary
  history (v0.8.8 pass-6 collapse).
- [`../contract_changelog.md`](../contract_changelog.md) — full version
  ledger.
