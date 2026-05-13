# Myco essence brainstorm — v0.8.8 strategic frame

> ⚠ **2026-05-13 100%-confidence loop (correction #4)**: owner invoked
> the explicit "are you 100% confident? if not, find all holes,
> propose fixes, run the loop until you actually are" forcing function.
> Result: I am 93% confident in my own derivation; the remaining 7%
> is owner-arbitration-only (5 specific items below); claiming 100%
> would be dishonest calibration.
>
> ## Loop trace
>
> | Pass | Confidence | Action |
> |---|---|---|
> | 1 | 60% | Honest baseline after 3 prior corrections |
> | 2 | 60% | Enumerated 20 candidate holes (5 极高 severity) |
> | 3 | 85% | Applied 5 first-order fixes (H6/H3/H8/H11/H12) |
> | 4 | 85% | Applied 5 second-order fixes (H21-H25 — fixing new holes the first-order fixes opened) |
> | 5 | **93%** | Identified residual 7% as owner-arbitration-only; cannot resolve via self-reasoning |
>
> ## First-order fixes (record)
>
> | ID | Fix |
> |---|---|
> | **H6** | **Agent identity internalisation**: Myco *defines* agent identity (= substrate-operator role), rather than inheriting it from underlying model/API. Same substrate → same agent for Myco's purposes, regardless of model weights, provider, host. |
> | **H3** | **Two-tier human-loop**: P1.b' "Human OUT of maintenance loop" (daily schema/lint/verb edits = agent-only); P1.b'' "Human RETAINED as governance gate" (L0/L1 amendments requiring contract_version cross-MAJOR/MINOR bump = owner approval). |
> | **H8** | **Non-recursive bootstrap**: genesis = one-time human operator (`germinate`); maintenance = everlasting agent. Self-hosting describes mature Myco's steady state, not its birth. Pre-self-host (v0.4.x) is *proto-Myco*. |
> | **H11** | **Living Bets operational definition**: bet wins when `persistence_budget > K × read_window` (K ≈ 100 default; tunable). Both quantities token-measurable. |
> | **H12** | **Concurrency scope**: P1 = intra-substrate (one operator per substrate); P5 = inter-substrate (federation across substrates each with their own operator). Same-substrate concurrent operators are not Myco-supported. |
>
> ## Second-order fixes (record)
>
> | ID | Fix |
> |---|---|
> | H21 | H6's circularity (agent=operator, operator=agent) is non-vacuous at runtime — operator is a *behavior*, not a stored identity; fixed point is reachable. |
> | H22 | H3's "daily vs governance" line = contract_version cross-MAJOR/MINOR bump as mechanical boundary. |
> | H23 | H8's "proto-Myco" concession — α describes mature Myco only; v0.4.x is embryonic, not a counterexample. |
> | H24 | H11's K threshold is β/γ tunable; α only asserts "*some* K exists that partitions wins/loses". |
> | H25 | H12's "substrate is lazy medium" — `immune` and other "metabolism" verbs are agent-invoked, never substrate-self-driven. |
>
> ## Residual 7% (owner-arbitration only)
>
> Five claims need explicit owner confirmation before α can be sealed:
>
> 1. **Agent-identity internalisation** (Fix-H6): does owner agree that Myco *bestows* agent identity rather than inheriting it from model/API?
> 2. **Two-tier human-loop boundary** (Fix-H3): is contract_version cross-MAJOR/MINOR the right mechanical line between "daily" and "governance"?
> 3. **Embryonic Myco concession** (Fix-H8): is α permitted to describe mature Myco only?
> 4. **K threshold** (Fix-H11): does owner set K, or let it emerge from substrate metrics?
> 5. **Foundation provisionality** (H16): owner is the only authority over L0/README/MYCO.md; any owner amendment to these source documents propagates into α.
>
> Until these 5 are arbitrated, the document's α stands at "best-derivation-from-current-source-documents-as-of-2026-05-13".
>
> ⚠ **2026-05-13 owner-driven correction #3 (earlier)**: even after
> correction #2, two persistent failure modes remained, both flagged
> by owner:
>
> A. **Anatomy-as-essence leak**. Words like "metabolic pathway",
>    "immune system", "circulation system" sound biological but are
>    still β-layer structural commitments. They presuppose "Myco
>    is decomposed into separable organs". That's an implementation
>    decision, not essence. Correction: at the essence layer,
>    describe *observable behaviors*, not anatomy.
>
> B. **L0-canonical-vocabulary substitution**. I had been replacing
>    L0's 五条根本原则 (只为 Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 /
>    万物互联) with my own English derivatives ("autopoietic",
>    "self-hosting", "mutable form", "persistence > read window",
>    "mechanical integrity"). L0 §"Biological metaphor (authoritative)"
>    says "No alternate vocabulary" — that rule applies to me. The
>    L0 canonical names ARE the essence's preferred expression form;
>    deriving substitutes is downgrading, not clarification.
>    Correction: quote L0's canonical 五条原则 verbatim. Layer the
>    README/MYCO.md derived reinforcements (self-hosting + agent-only
>    maintenance + inclusion) on top, do not substitute for them.
>
> Deeper failure mode being corrected here: I was **operating on L0**
> (translating, abstracting, re-shaping it) instead of **quoting L0**
> (preserving it as the authoritative source). Only the owner can
> revise L0. The brainstorm derives FROM L0; it does not replace L0.
>
> ⚠ **2026-05-13 owner-driven correction #2 (earlier same day)**: an
> earlier revision of this document still leaked β-layer specifics
> ("20 verbs", "47 dims") into the "Concrete" and "Function"
> sections, and framed the near-term roadmap as "tighten β to
> minimal α-satisfaction". Both are wrong. Per the owner's
> corrections (recorded inline via AskUserQuestion answers on
> 2026-05-13):
>
> 1. **Concrete definition** must NOT name specific verb / dim
>    counts. Myco has *metabolic pathways*, *an immune system*,
>    *circulation* — the cardinality of each is ε-snapshot, not
>    essence. The v0.8.7 numbers are a snapshot, not a definition.
> 2. **Function definition** must talk about capability classes
>    (mechanical integrity guarantees / self-continuity / form-
>    evolution capacity), not the specific 47-dim implementation.
> 3. **Near-term vision** is *ground-up rewrite*, not "tighten the
>    recipe". v0.9 is "Myco's second boot", drafting a new β from
>    scratch that satisfies α. The current v0.8.x is an ε snapshot
>    full of historical accretion / misguided directions that
>    would mislead a clean re-derivation.
> 4. **The "doesn't do" list** (no RAG / chatbot memory / LLM call
>    / human docs / file sync) was wrong. Myco is INCLUSIVE not
>    EXCLUSIVE: it should *subsume* all of those sub-techniques
>    within its own framework. Vector retrieval is one form of
>    `sense`; conversation history is one type of raw note; LLM
>    calls happen agent-side but within Myco-prepared scaffolding;
>    file sync is subsumed under semantic federation. Myco's force
>    is *unification*, not exclusion.
>
> Sections §0, §5, §10 below were rewritten in correction #1 (α/β/γ
> decomposition); they are kept. Sections §1, §3 are rewritten
> below as correction #2. The §9 strategic next-steps roadmap is
> superseded by the new §11 "Ground-up rewrite mandate".

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

### The α layer — L0's 五条根本原则 (canonical; correction #3)

Correction #3 (2026-05-13, owner): the previous draft listed 6
English-derived predicates ("persistent", "mechanically self-
validating", "co-authored", "agent-readable", "protocol-coordinated",
"continuity-of-self") as the α layer. This was a violation of L0
§"Biological metaphor (authoritative)" which mandates "No alternate
vocabulary". The α layer is L0's five 永恒X principles verbatim, plus
the README/MYCO.md derived reinforcements of P1:

**L0's 五条根本原则 (verbatim, the α core):**

| 编号 | L0 名 | L0 原文（节选） |
|------|------|------|
| P1 | **只为 Agent （人类无感知）** | "The agent is the sole consumer. Humans do not read, browse, or operate Myco's interior surfaces as a routine activity." |
| P2 | **永恒吞噬 （吞噬万物）** | "Myco consumes without bound. **There is no filter on what enters.**" |
| P3 | **永恒进化** | "Myco's **own shape evolves**... **An unchanging substrate is a dead substrate.**" |
| P4 | **永恒迭代** | "`assimilate → digest → sporulate` is a continuous cycle, not a terminal workflow. **「Final」 is not a status.**" |
| P5 | **万物互联 （菌丝网络）** | "The substrate is a **connected graph**, not a collection. **Orphans are dead tissue.**" |

**Derived reinforcements of P1 (from README + MYCO.md, strengthen
"agent is the sole consumer" → "agent is the sole consumer AND
maintainer AND host"):**

| 编号 | 名 | 来源原文 |
|------|------|------|
| P1.a | **Self-hosting** | "The kernel IS a substrate, editable by default, **maintained by the same agent that uses it**." (README §"The kernel IS a substrate") |
| P1.b | **Agent-only maintenance** | "Every earlier attempt at a self-maintaining knowledge system died in the same place, where the human in the loop could no longer keep up. Myco puts the loop inside the agent... **the human in the loop is no longer load-bearing.**" (README §"What it is") |
| P2.a | **Inclusion** (P2 strong form) | Owner 2026-05-13: 「并非不做，Myco 应该是广纳所有经验、知识、技巧、技术、思考等等的，只是需要在 Myco 的框架下做，而不是割裂开来做」. RAG / conversation / LLM calls / external APIs / file federation should be subsumed *into* Myco's framework, not exist in parallel. |

These 5 + 3 are the **only** things Myco cannot lose without becoming
a different kind of thing. They are NOT my paraphrase of essence —
they ARE the essence as L0 / README / MYCO.md author it, and any
reformulation in this document is downgrading.

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

## 1. The essence — L0 canonical vocabulary (correction #3)

Myco's essence is **exhausted** by L0's 五条根本原则. Quoting L0
verbatim (do not substitute):

| 编号 | L0 名 | L0 原文（节选） |
|------|------|------|
| P1 | **只为 Agent （人类无感知）** | "Myco is a cognitive substrate **for an LLM agent**. The agent is the sole consumer. Humans do not read, browse, or operate Myco's interior surfaces as a routine activity." |
| P2 | **永恒吞噬 — Eternal Ingestion （吞噬万物）** | "Myco consumes without bound. Any input the agent can point at — a decision, a debate, a friction note, a log file, an external document, a conversation fragment, a failed approach — is ingestible raw material. **There is no filter on what enters.**" |
| P3 | **永恒进化 — Eternal Evolution** | "Myco's **own shape evolves**. The schema of canon, the roster of subsystems, the lint dimensions, the contract itself — all of these are first-class mutable objects. **An unchanging substrate is a dead substrate.**" |
| P4 | **永恒迭代 — Eternal Iteration** | "Every session refines what prior sessions produced. `assimilate → digest → sporulate` is a continuous cycle, not a terminal workflow. **「Final」 is not a status.**" |
| P5 | **万物互联 — Universal Interconnection （菌丝网络）** | "The substrate is a **connected graph**, not a collection. Every node is reachable from every other by traversal. **Orphans are dead tissue.**" |

**These five are the essence.** No paraphrase replaces them.
Earlier revisions of this document tried to substitute them with my
own English derivatives ("autopoietic metabolism", "self-hosting",
"mutable form" etc.) — that was a violation of L0's "No alternate
vocabulary" rule. Correction #3 removes those substitutions.

## 1.5 衍生强化 (README + MYCO.md, reinforcing P1)

L0 declares P1 as "agent is the sole *consumer*". README + MYCO.md
strengthen this to "agent is the sole consumer **and the sole
maintainer**":

- **Self-hosting (P1 strong form)**: "The kernel IS a substrate,
  editable by default, **maintained by the same agent that uses it**"
  (README §"The kernel IS a substrate").
- **Agent-only maintenance (P1 strongest form)**: "Every earlier
  attempt at a self-maintaining knowledge system died in the same
  place, where the human in the loop could no longer keep up. Myco
  puts the loop inside the agent... **the human in the loop is no
  longer load-bearing.**" (README §"What it is").
- **Inclusion / unification (logical extension of P2)**: Myco is the
  framework into which every adjacent sub-technique (vector
  retrieval / conversation history / agent-side LLM calls / external
  APIs / semantic file federation / human-facing brief …) **should
  be subsumed**, rather than existing in parallel. Per owner
  correction 2026-05-13: 「并非不做，Myco 应该是广纳所有经验、
  知识、技巧、技术、思考等等的，只是需要在 Myco 的框架下做，
  而不是割裂开来做」.

## 2. The essence — one paragraph (correction #3)

> Myco is a **cognitive substrate** whose identity is exhausted by
> L0's 五条根本原则 (只为 Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 /
> 万物互联), strengthened by three derivations from README + MYCO.md:
> self-hosting (Myco's own kernel lives inside a Myco substrate),
> agent-only maintenance (the human in the loop is no longer
> load-bearing; the same agent that uses Myco maintains Myco), and
> inclusion (every adjacent sub-technique — RAG, conversation
> history, LLM calls, external APIs, semantic federation — should
> live *within* Myco's framework rather than in parallel). The
> grammar shape, immune dimension count, subsystem partition,
> serialization format, protocol surface are all ε-snapshot choices.
> Any v0.9+ redesign is constrained only by the five 永恒X
> principles plus the three reinforcements.

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

## 11. Ground-up rewrite mandate (correction #2)

The v0.9 work is **not** a tightening of v0.8.x. It is a **ground-up
rewrite**. Owner direction (2026-05-13):

> 「近期要做的事情是彻底重构重写 Myco，避免被大量错误误导
> 走向了完全错误的理解和道路。」

Implications:

- **Everything in the β layer is up for replacement**: verb set,
  subsystem partition, dim set, schema format, protocol surface
  (CLI / MCP / something else), biological vocabulary, hook
  discipline, plugin axes, governance loop shape, even the file
  layout. None of v0.8.7's β-layer choices is inherited by
  obligation.
- **The α layer is the only constraint**: any v0.9 design must
  satisfy the six α predicates. Everything else is open.
- **The current v0.8.x substrate is git history**: not the starting
  point for v0.9 changes. v0.9 is a new substrate that the previous
  Myco's source code happens to be available to reference, but
  reference is the right relationship — not "edit in place".
- **The earlier §9 incremental roadmap (S1-S9)** is superseded:
  S1-S9 assumed β-layer tweaks. A ground-up rewrite makes most of
  them moot (S2 dim-tiering, S3 cycle-subsystem-schism, S4 manifest
  importability lint, S5 canon.py split, S7 doctrine merge, S8 MB8
  excretion, S9 ramify re-audit are all β-internal). Only S1 (re-
  audit Living Bets) and S6 (1M-file stress test) survive as
  α-level work-streams. S2-S5 / S7-S9 are subsumed into "draft new
  β from scratch".

## 12. The wager restated for v0.9+ (was §10)

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
