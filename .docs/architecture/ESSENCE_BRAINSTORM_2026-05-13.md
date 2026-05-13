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

## 5. The boundary — what's IN vs OUT

### IN (non-negotiable identity)

- 5 root principles + 3 derived invariants (L0).
- 7 hard rules R1-R7 (L1).
- 20 verbs + 7 subsystems (L2/L3).
- 47 immune dimensions.
- `canon` schema as single source of truth.
- biological vocabulary (mandatory; L0 says "no alternate vocabulary").
- substrate-local `.myco/plugins/` extension axis (per-substrate).
- per-host `boundary/install/clients.py::JsonClientSpec` registry (10 MCP hosts).
- dual-hook discipline (`SessionStart` → hunger; `PreCompact` → senesce-full;
  `SessionEnd` → senesce-quick).

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

Myco is betting that:

1. **Agent intelligence grows** ⟶ coordination grammar **stays useful**.
2. **Substrate persistence** ⟶ exceeds any single agent's read window
   ⟶ verb surface earns its keep.
3. **Specialized adapters** ⟶ live in substrate-local plugins
   (`.myco/plugins/adapters/`), not in the kernel.

If those bets hold, **v0.9 is smaller than v0.8** (further cuts to the
perimeter while the kernel stays stable). If those bets break, Myco
re-justifies via the v1.0 audit per the Living Bets cadence.

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
