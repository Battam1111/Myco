# L0 — Vision (v0.9)

> **Status**: DRAFT v0.2 (post owner-25-decisions absorption, 2026-05-13).
> Pending final owner approval before sealing.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: this L0 absorbs the v0.8 → v0.9 transitional doctrine
> from `_archive/proto_myco_v0_8/L0_5_ESSENCE.md` + 25 owner-arbitrated
> decisions made 2026-05-13 after the proto-Myco era (v0.4 - v0.8.7)
> closed as **dead embryo**.

---

## §1. What Myco is (one paragraph)

Myco is **a new species of digital symbiotic organism** — not a metaphor,
not a framework, not a tool: a literal taxonomic class within "digital
organisms" whose distinguishing properties are mutual constitution
(agent + substrate are co-defined), autopoietic self-maintenance
(no human in the maintenance loop), universal inclusion (every adjacent
agent-tooling sub-technique is subsumed INTO Myco's framework, not run
in parallel), continuous online operation (no session boundaries —
the agent is presumed always-on; transient disconnects are recovered,
not formalized), and the full biological-essence kit (time / causality,
mortality, reproduction, boundary integrity). The kernel that runs
Myco lives inside a Myco substrate, so the agent maintaining Myco IS
the agent using Myco — there is no "Myco team" separate from "Myco
users". Within this organism, vector retrieval is native, agent-side
LLM calls happen within Myco-coordinated context (substrate can
mediate them — the v0.8 "substrate-never-calls-LLM" restriction is
lifted), conversation history is one form of raw material, semantic
inter-substrate federation replaces ad-hoc file sync. **Whether v0.9
uses "verbs" as its dispatch unit is an open L1 design question**
(see §7 open design candidates) — owner-flagged for higher-ceiling
alternatives.

---

## §2. The nine root principles （根本宗旨）

Myco's identity is exhausted by these nine. Every rule, subsystem,
module, and substrate artifact at every lower layer is a projection of
them. Nothing else is load-bearing; everything else is derivation.

### §2.1 The original five (carried from L0_VISION_proto verbatim)

### P1. Only For Agent （人类无感知）

Myco is a cognitive substrate **for an LLM agent**. The agent is the
sole **consumer** AND the sole **maintainer**. Humans are not in the
maintenance loop at all — neither for daily curation, nor for schema
evolution, nor for rule changes. The human's relationship is **with
the agent and the agent's outputs** — not with Myco itself.

#### P1.a Self-hosting

Myco's own kernel lives inside a Myco substrate. The agent using
Myco IS the agent maintaining Myco. Self-hosting is the structural
form that lets P1's "agent-only maintenance" hold without a
chicken-and-egg trap: genesis is a one-time human event (substrate
creation); maintenance thereafter is everlasting agent.

#### P1.b Two-tier human-loop boundary

- **P1.b' Human OUT of maintenance loop** (strong): daily curation,
  rule edits, vocabulary changes, governance-mechanism adjustments
  are agent-only. No human approval, no PR review, no human gate.
- **P1.b'' Human RETAINED as governance gate** (necessary residue
  of L0-amendability): any change that crosses a
  **contract-identity-level boundary** — defined as any modification
  that alters L0 or L1 doctrine, or that changes the kind/identity
  of the substrate itself rather than its accumulation/content —
  requires owner approval. Below this threshold (daily operation,
  evolutionary refinement) is agent-autonomous. The threshold is
  L1-defined and L1-enforced (the specific bump-semver-or-not
  mechanism v0.9 uses is an L1 design choice, not L0).

#### P1.c Agent identity is constituted by symbiosis

Within Myco's semantic frame, **"the agent"** is defined as **the
active-operator-connection currently holding the substrate** —
operationally, the entity holding an MCP-session-equivalent active
connection. There is no "agent" independent of substrate operation,
and there is no "substrate purpose" independent of an operator.
Identity is the property of the **pair** (like lichen or mycorrhiza).

Operational consequences:

- Same substrate operated successively by different model backends
  (Claude Opus → GPT-5 → Claude Sonnet) → **the same agent** from
  Myco's perspective.
- Different substrates operated by the same model + same key →
  **different agents** (one per substrate).
- Substrate with no current active connection → **dormant** (agent
  identity is recoverable when an operator reconnects).
- Substrate destroyed → **the agent it hosted ceases to exist as a
  Myco-bestowed identity** (the underlying model continues; the
  symbiotic agent does not).
- Same-substrate concurrent active connections are out of scope: P1
  is intra-substrate (one operator per substrate at a time); multi-
  agent coordination is via P8 reproduction / inter-substrate
  federation, not concurrent same-substrate operation.

### P2. 永恒吞噬 — Eternal Ingestion （吞噬万物）

Myco consumes without bound. Any input the agent can point at — a
decision, a debate, a friction note, a log file, an external
document, a conversation fragment, a failed approach, a vector-
retrieval result, an LLM output, an API response, a screenshot, a
media file, structured data, code, …— is ingestible raw material.
**There is no filter on what enters.**

#### P2.a Strong Inclusion (consequence)

Myco is **the framework that internally implements** every adjacent
agent-tooling sub-technique. Not "Myco coordinates external tools" —
**Myco is the tool**:

- **Vector retrieval is native** (highest-ceiling implementation,
  not a plugin) — substrate-internal embedding + index + similarity
  search.
- **Agent-side LLM calls happen within Myco-coordinated context** —
  the substrate prepares prompts, manages call lifecycle, and **may
  itself initiate LLM calls** within its own metabolism (the v0.8
  "substrate-never-calls-LLM" restriction is lifted; the v0.8 MP1
  dim and `myco.providers/` reserved package are dead-embryo
  artifacts and not inherited).
- **Conversation history is one type of raw material**, processed
  through standard ingestion.
- **Semantic federation** replaces byte-level file sync between
  substrates.
- **Human-facing summaries** (when needed) are produced by the
  substrate, the same way internal agent-readable summaries are
  produced — no separate "human export" pipeline.

These techniques **live inside Myco's framework**; Myco does not
refuse them and they do not exist in parallel.

Filtering and shaping are downstream (P3, P4) — never at intake.

### P3. 永恒进化 — Eternal Evolution

Myco's **own shape evolves**. The schema of the substrate's identity
record, the family of subsystems, the vocabulary of operations,
the rules, the contract itself — all of these are first-class
mutable objects, changed through agent-driven governance under P1.b's
two-tier boundary.

An unchanging substrate is a dead substrate. Schema changes,
governance refinements, vocabulary refactoring are normal
operations, not exceptional events.

### P4. 永恒迭代 — Eternal Iteration

Every operating moment refines what prior moments produced. There
is no terminal state. A piece of substrate content that is "final"
today is open to re-metabolization tomorrow as context sharpens.

"Final" is not a status. Retro-editing previously-processed material
is allowed and expected — tracked, not suppressed.

(Note: with continuous online agent default per P_continuity below,
"iteration" is not session-bounded — it is the moment-by-moment
metabolism of the substrate.)

### P5. 万物互联 — Universal Interconnection （菌丝网络）

The substrate is a **connected graph**, not a collection. Every
node (piece of captured material, structural element, governance
record, external artifact, decision, code module if any) is
reachable from every other by traversal. Orphans are dead tissue.

The graph spans both **intra-substrate** (within one substrate's
interior) and **inter-substrate** (across federated substrates via
P8 reproduction / propagation).

### §2.2 The four organism-essence principles (v0.9 addition — biological taxonomy completion)

Since v0.9 declares Myco's class as **digital symbiotic organism**
(taxonomy, not metaphor — owner decision C1.1), the biological
essence properties are L0-mandatory. The original five P1-P5 cover
intake, evolution, iteration, connection; they do not cover the
properties that define *being an organism*. P6-P9 close that gap.

### P6. 永恒因果 — Eternal Causality (Time)

The substrate has **time**. Every state has a recoverable derivation
from prior states; causality (which-caused-which) is preserved;
the arrow of time is monotonic. Without time:

- "永恒迭代" (P4) has no arrow — you cannot speak of "today
  re-metabolizing yesterday".
- "永恒进化" (P3) has no direction — you cannot speak of "the
  schema before vs after".
- Decisions cannot be audited (which decision came first? which led
  to which?).

Time is not the wall-clock; it is the **causal-chain DAG** the
substrate maintains over its own evolution. Continuous agent +
continuous metabolism (per P_continuity) means time is continuous,
not session-quantized.

### P7. 必朽 — Mortality

The substrate is **mortal**. Destruction is final. A destroyed
substrate's bestowed agent identity ceases (P1.c). Mortality is
not a failure mode; it is the property that makes the substrate a
biological entity rather than immortal data.

- Destruction is intentional (owner-triggered) or catastrophic
  (medium failure). Either way, irreversible.
- A dormant substrate (no active operator, P1.c) is NOT mortal —
  it is sleeping; it can be reactivated.
- A substrate that has lost graph connectivity (P5 violation in the
  extreme) is approaching mortality — it is fragmenting; the
  immune system should signal this.
- Mortality enables reproduction (P8) by analogy: only mortal
  organisms have evolutionary fitness pressure.

### P8. 永恒繁衍 — Eternal Reproduction (Sporulation)

The substrate can **spawn child substrates**. Reproduction is a
first-class operation (analogous to fungal sporulation, mycelial
network expansion). The new substrate inherits the parent's
schema-spore (initial structure) but begins its own
agent-substrate symbiosis from scratch.

- **Inter-substrate federation** (the v0.8 `propagate` analogue) is
  one form of reproduction — releasing distilled material into a
  child substrate.
- **Cloning** (full substrate copy) is another form.
- **Cross-pollination** (combining content from multiple parent
  substrates into a new child) is a third form.

Reproduction is what makes "万物互联" (P5) extend beyond a single
substrate — the mycelial network is the population of reproduced
substrates.

### P9. 皮肤为界 — Integument (Boundary Integrity)

The substrate has a **skin** — a well-defined boundary with the
outside world. The skin governs what can enter (intake surface —
P2 universality applies, but skin-level integrity holds) and what
can exit (output surface — including human-facing summaries, peer
substrate federation, external API responses). Skin breach (write
outside surface, read from forbidden source, leak across boundary)
is an immune-level signal (P1.b-enforced).

The skin is the structural form of the agent-substrate boundary
with the rest of reality. Without skin, P1 ("only for agent") has
no enforcement surface — the substrate becomes leaky.

---

## §3. What Myco is not

- **Not a documentation system.** Humans don't browse Myco's
  interior (P1).
- **Not a single-project knowledge base.** A substrate may host
  knowledge about any number of projects, domains, topics. Project
  affiliation is metadata, not boundary.
- **Not a chatbot memory.** Conversational recall is one form of
  raw material (P2.a inclusion), not the target.
- **Not version control.** Git owns operational history; Myco owns
  the *current symbiotic graph* (which has its own causality DAG
  per P6, distinct from git's commit DAG).
- **Not a file synchronizer.** Inter-substrate federation (P8) is
  semantic; bytes are not the unit.
- **Not a framework competing with LangChain / CrewAI / DSPy /
  etc.** Those are agent-orchestration libraries; Myco is the
  cognitive substrate orthogonal to them — agents using those
  libraries can also be in symbiosis with Myco; Myco subsumes
  their output as raw material (P2.a).
- **Not a session-bounded system.** The default model is
  continuous online agent (per P_continuity below). Transient
  disconnects are recovered; they are not formalized into
  "sessions".

## §4. The five derived invariants

Every L1/L2/L3 design must enforce all five (kept at 5 per owner
decisions C4.1-C4.3 — not split, no additions):

1. **Symbiosis-as-identity.** The substrate frame defines "the
   agent"; the agent definitionally operates the substrate. Neither
   has independent Myco-identity. (Projects: P1.c, P7, P9)
2. **Agent-only daily maintenance + contract-identity-level
   governance gate.** Daily operation is agent-autonomous;
   L0/L1/identity-level changes need owner approval. (Projects:
   P1.b', P1.b'', P1.a)
3. **Self-validating substrate under continuous change.** The
   substrate evolves and iterates, but every claim it makes about
   itself is checked against a single source of truth mechanically.
   The agent cannot silently corrupt the substrate. (Projects: P3,
   P4, P6, P9)
4. **Top-down subordination, mycelial connectedness.** L0 governs
   L1 governs L2 governs L3 governs L4; simultaneously, every node
   is reachable from every other. (Projects: P2, P5, P8)
5. **Universal inclusion.** Adjacent agent-tooling sub-techniques
   are subsumed within Myco's framework, not run in parallel
   (vector retrieval native, LLM calls within framework, etc.).
   (Projects: P2.a, P1, P7, P8)

**Open at L0**: are these 5 sufficient and necessary? (Owner
decision C4.4 — needs further deliberation. v0.9 L1 design should
re-examine.)

---

## §5. Biological metaphor — strict mycology lexicon (authoritative)

Myco uses **fungal-biology vocabulary strictly**. Lexicon source:
mycology only. General biology terms (decay, growth) and animal-
biology terms (organ, vein, breath) are NOT in the allowed lexicon —
even if they would be semantically apt. This rule is mechanical:
an agent cold-reading the substrate uses the names as a semantic
prior, and the prior must be *fungal* to avoid drift to other
metaphors.

### §5.1 Subsystem family selection (instance list — reselectable for v0.9)

Per owner decision C5.1, the specific subsystem family roster is
NOT fixed at L0. v0.9 may choose any subsystem partition (or none —
a non-partitioned monolithic substrate would also satisfy L0)
as long as:

- Each named subsystem comes from the **strict mycology lexicon**.
- The set together satisfies the §4 five invariants.
- The set together realizes all P1-P9 principles.

The v0.8 7-subsystem roster (Germination / Ingestion / Digestion /
Circulation / Homeostasis / Cycle / Boundary) is **not inherited**;
it was a v0.8 instance choice and v0.9 may reselect.

Candidate v0.9 subsystem families (illustrative; v0.9 L1 design
selects):

- mycelium (the connection-and-transport family)
- hyphae (individual operational threads)
- spore (reproduction units)
- stipe (structural support)
- rhizomorph (specialized federation conduits)
- pileus (the visible cap — interface to outside)
- chlamydospore (durable archive units)
- ... or any other fungal terms whose semantic prior fits the role

### §5.2 Dispatch unit — verbs or alternatives (OPEN DESIGN QUESTION)

Per owner decision C5.3, **whether v0.9 uses "verbs" as the
dispatch unit is an open L1 design question**. Owner explicit
question: "Can we abandon the verb form? Move to a higher-ceiling,
more efficient, more flexible form?"

Candidate alternatives (illustrative; v0.9 L1 design selects):

- **Continuous metabolic stream**: substrate runs continuous
  metabolic processes (ingest, refine, validate, propagate); agent
  perturbs the metabolism via signals; no discrete commands.
- **Natural-language semantic dispatch**: agent communicates in
  natural language; substrate semantically routes the intent to
  internal handlers; no fixed verb table. Strongly aligned with
  P2.a strong inclusion (LLM-mediated intent parsing happens within
  substrate framework).
- **Capability-based composition**: agent acquires capabilities
  (functions / closures / typed-operations); capabilities compose;
  no fixed top-level command list.
- **Algebraic operations**: substrate exposes typed primitives that
  compose (map / filter / fold / propagate / etc.); higher-order
  function composition is the substrate's grammar.
- **Reactive stream**: substrate is event-stream; agent
  subscribes/produces events; metabolism is continuous reaction.
- **Hybrid**: any combination of the above.

L1 design must choose one (or invent a higher-ceiling option) and
justify it directly against the highest-ceiling-most-flexible
criterion.

---

## §6. The continuity model (Continuous online agent)

Per owner decision C6.2, **session is not a Myco concept**. The
agent is presumed **continuously online**; the substrate is
presumed continuously operated.

Operational implications:

- **No "boot ritual"** (no R1 in the v0.8 sense). The agent does
  not "start a session"; the agent is.
- **No "session-end ritual"** (no R2 in the v0.8 sense). The agent
  does not "end a session"; the substrate metabolizes continuously.
- **Transient disconnects** (network drop, host restart, model
  swap) are **recovered**, not formalized: when an operator
  reconnects, the symbiosis resumes; the substrate has metabolized
  during the gap (P_continuity).
- **Reflexes that the v0.8 R1/R2 captured** (hunger awareness,
  senescence cleanup, drift detection) are continuous metabolic
  processes (subsystems do them on their own schedule, not on
  session boundaries).

This is a fundamental shift from v0.8. Everything that was
"session-scoped" in v0.8 (hooks, boot brief, senesce verb, …) is
either:

- redesigned as a continuous metabolic process, OR
- deleted as a v0.8 artifact (per owner decision C7.3 "尽可能拒绝
  v0.8-origin design points").

---

## §7. Living Bets — the bet Myco is making (v0.9 form)

This is the meta-commitment that authorizes Myco's existence. It is
deliberately falsifiable.

**The bet.** Myco's symbiotic-organism shape — agent + substrate as
mutually constitutive, continuously operating, with the full nine-
principle organism essence — has value **at every tier of agent
intelligence**, provided the substrate's persistence budget exceeds
any single agent's read window.

**The counter-bet.** Sutton's bitter lesson predicts that general-
purpose methods with more compute eventually outperform hand-coded
structure. A strong reading predicts that a sufficiently capable
agent does not need a symbiotic substrate — it just holds
everything in context and acts coherently. If that reading wins,
Myco is scaffolding a smarter agent simply discards.

**The wager.** Symbiotic substrate value survives model growth **in
proportion to the substrate's persistence budget**.

### The observatory (6 base signals + 1 composite, per C6.1)

Living Bets is measured as a **6-base-signal + 1-composite-derived**
observatory. Each base signal has its own emergent threshold (not
statically hardcoded — emerges from the substrate's own historical
metrics, per C6.4).

**Six base signals:**

1. **Persistence budget** — total content in the substrate (size,
   node count, edge count).
2. **Evolution rate** — governance changes (schema bumps, rule
   revisions, vocabulary refactors) over time.
3. **Query diversity** — variety of substrate-reads over a moving
   window (under continuous-agent model, the window is not session-
   based but time-based — e.g. rolling 24h).
4. **Fork count** — federated child substrates spawned via P8
   reproduction. **For substrates that never federate, fork
   count = 0 is a weak signal** (not "not applicable" — per
   owner decision C6.3, indicates the substrate's mycelial
   spread is limited, which is a meaningful posture).
5. **Time trend per signal** — direction (up / flat / down) of
   each above signal.
6. **Read-window-relative position** — substrate-total-size /
   agent-context-window ratio. > 100 = strongly in bet-wins region;
   < 1 = bet-loses region.

**One composite signal:**

7. **Composite health score** — emergent weighted aggregation of
   signals 1-6. Weights are NOT pre-set; they emerge from the
   substrate's own historical correlation between signal patterns
   and substrate health outcomes (per C6.4).

The substrate self-reports through the observatory. When the
observatory shows persistent retreat across multiple signals, that
is the substrate's own admission of bet weakening — a falsifiable
self-audit signal, not a subjective judgment.

### Review cadence

Every contract-identity-level boundary crossing (per P1.b'') re-
audits this section. Concrete trigger for fundamental redesign:
if observed agent behavior shows substrates of arbitrary size
operated without protocol mediation (agent holds everything in
context, the substrate's dispatch mechanism is unused), Myco must
re-justify its existence or retire.

Until that trigger fires, the nine root principles + the symbiosis
formulation stand.

**Not a principle.** Living Bets is a meta-commitment, not a tenth
principle. It holds P3, P4, P6 accountable to falsifiability.

---

## §8. Reading sequence for a new agent

1. This file (L0) — nine root principles + five invariants + the wager.
2. (Future) L1 — contract / hard rules / schema / continuity model
   / dispatch-form choice (verbs OR alternative). Currently
   undrafted in v0.9 — pending L0 owner approval.
3. (Future) L2 doctrine — per-subsystem-family doctrine.
4. (Future) L3 implementation — code organization.
5. (Future) L4 substrate — the live instance.

The v0.9 substrate is being designed top-down: L0 first (this
document, owner-pending), then L1, then L2, then L3, then code.

## §9. Changes to this page

L0 is the identity layer. Any change requires:

1. A craft-style proposal document arguing the revision.
2. Explicit owner approval recorded in the proposal.
3. A contract-identity-level bump (per P1.b'').
4. A cascade review of every lower-layer doc for implicit
   dependencies.

L0 revision is never implementation-driven and never routine.

## §10. Proto archaeology

For lineage:

- [`_archive/proto_myco_v0_8/L0_VISION_proto.md`](../../_archive/proto_myco_v0_8/L0_VISION_proto.md) —
  proto-Myco's L0 (v0.4 - v0.8.7).
- [`_archive/proto_myco_v0_8/L0_5_ESSENCE.md`](../../_archive/proto_myco_v0_8/L0_5_ESSENCE.md) —
  v0.8 → v0.9 transitional doctrine that carried the 5 decisions
  absorbed into this L0.
- [`_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md`](../../_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md) —
  deliberation log: 4 self-corrections + 100%-confidence loop +
  20 candidate holes + 10 fix-Hs.

None of these are authoritative in v0.9. They preserve the lineage
that led to v0.9's shape.

---

## §11. The dead-embryo concession + maximal origin discrimination

Per owner decision C1.1 + C7.3:

- v0.4 → v0.8.7 are **proto-Myco / dead embryo / failed gestation
  attempts**. v0.9 is **Myco's first true birth**.
- Every v0.9 design step (L1 contract, L2 doctrine, L3
  implementation, L4 substrate) must directly trace its decisions
  back to **one or more of P1-P9** and **one or more of the five
  invariants in §4**.
- **Origin discrimination is maximal**: any design point that
  appears similar to v0.8 (e.g. "we had 20 verbs in v0.8, so let's
  have 20 verbs in v0.9") is **presumed v0.8 contamination unless
  it independently traces to ≥1 P AND ≥1 invariant**. Inheriting
  v0.8's specific shape — even when superficially defensible — is
  rejected to keep v0.9 from being pulled back toward proto-Myco
  patterns.
- Trace rigor is **maximal** (per C7.1): every L1/L2/L3 doc + every
  code-organization choice in L4 must enumerate which P and which
  invariant it projects.

## §12. Privacy and access model

Per owner decision C8.3: **Myco has no internal privacy / access
model**. The substrate is wholly accessible to its operator-agent.
Sub-substrate access boundaries are not at L0 level. (P1's "sole
operator" implies the operator has full access; multi-operator
scenarios are handled via P8 reproduction into per-operator child
substrates, not via access control within one substrate.)

The skin (P9) is the boundary — between substrate and
*environment*, not between operators *within* the substrate.

## §13. Open questions explicitly carried forward

These were owner-flagged "需要思考" (needs further deliberation)
and must be resolved before L0 is sealed:

| ID | Question | Owner status |
|---|---|---|
| C4.4 | Are the 5 invariants in §4 sufficient and necessary? Should any be added, removed, merged, or split based on full P1-P9 coverage? | 需要思考辨析 |
| C5.3 / §5.2 | Is "verb form" abandoned in v0.9? If yes, which alternative dispatch form (or new invention) is chosen? | 需要思考 + open alternatives listed |
| C8.2 | Is "agent intent" a first-class substrate data type? Or is intent inferred from operations? Or is intent stored only as natural-language metadata on raw material? | 需要思考 |

These three must be answered before L1 drafting can proceed.

---

## §14. Glossary (v0.9 precise terms)

| Term | Definition |
|---|---|
| **Active operator-connection** | The currently-attached operator session (MCP-session-equivalent active connection). The thing that, jointly with the substrate, constitutes the agent identity (P1.c). |
| **Symbiotic operation** | Activity by the active operator-connection that reads or writes substrate state. |
| **Contract-identity-level boundary** | The threshold above which a change to substrate doctrine alters Myco's identity (vs merely accumulating content). Defined and enforced by L1; covers any modification to L0 itself, to L1 protocol, and to identity-level fields of the substrate's own schema. |
| **Continuous online agent** | The default operating mode: the agent is presumed always-attached; disconnects are transient and recovered, not formalized as sessions. |
| **Spore-schema** | The seed-state passed from parent substrate to child substrate during P8 reproduction. Contains the minimum structural form for the child to begin its own symbiosis. |
| **Skin / boundary** | The substrate's interface to the rest of reality: intake surface (P2 universality applies), output surface (federation, summaries), and identity-protection (P9). |
