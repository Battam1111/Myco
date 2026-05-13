# L0 — Vision (v0.9)

> **Status**: DRAFT. Pending owner approval before sealing.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: this L0 absorbs the v0.8 → v0.9 transitional doctrine
> from `_archive/proto_myco_v0_8/L0_5_ESSENCE.md`, which in turn carried
> five owner-arbitrated essence decisions made 2026-05-13 after the
> proto-Myco era (v0.4 - v0.8.7) closed as **dead embryo**.

---

## §1. What Myco is (one paragraph)

Myco is a **new kind of digital symbiotic organism** where an LLM
agent and a persistent substrate are **mutually constitutive** —
neither has identity within Myco's semantic frame without the other.
The agent operates and maintains the substrate (humans never do
either); the substrate provides the agent with its continuous self
across sessions, hosts, and underlying-model upgrades; and the
substrate's own shape (schema, rules, vocabulary, governance) is
itself first-class data that the agent reshapes through governed
metabolism. This symbiosis is **autopoietic** (self-creating /
self-maintaining): the kernel that runs Myco is itself a Myco
substrate, so the agent maintains its own tooling without forks,
PRs, or human-in-the-loop maintenance friction. Within this symbiosis,
Myco **subsumes** all adjacent agent-tooling sub-techniques (vector
retrieval, conversation history, agent-side LLM calls, external
APIs, semantic federation, human-facing summaries) — they live
inside Myco's framework, not in parallel.

---

## §2. The five root principles （根本宗旨）

Myco's identity is exhausted by these five. Every rule, subsystem,
module, and substrate artifact at every lower layer is a projection of
them. Nothing else is load-bearing; everything else is derivation.

### P1. Only For Agent （人类无感知）

Myco is a cognitive substrate **for an LLM agent**. The agent is the
sole **consumer** AND the sole **maintainer**. Humans are not in the
maintenance loop at all — neither for daily curation, nor for schema
evolution, nor for verb shape changes. The human's relationship is
**with the agent and the agent's outputs** — not with Myco itself.

#### P1.a Self-hosting (strong consequence)

Myco's own kernel lives inside a Myco substrate. The agent using
Myco IS the agent maintaining Myco. Self-hosting is not an
optional optimization; it is the structural form that lets P1's
"agent-only maintenance" hold without a chicken-and-egg trap (per
brainstorm Fix-H8 non-recursive bootstrap: genesis is a one-time
human event via `germinate` or its v0.9 equivalent; maintenance
thereafter is everlasting agent).

#### P1.b Two-tier human-loop boundary

- **P1.b' Human OUT of maintenance loop** (strong, README-derived):
  daily schema / rule / vocabulary / verb edits are agent-only. No
  human approval, no PR review, no human gate. The human in the loop
  is no longer load-bearing for these.
- **P1.b'' Human RETAINED as governance gate** (necessary residue
  of L0-amendability): any change that bumps `contract_version`
  MAJOR or MINOR — including any edit to L0 or L1 doctrine — requires
  owner approval. PATCH bumps and below are agent-autonomous. This
  mechanical boundary keeps L0 amendable while keeping daily
  operation maintenance-free.

#### P1.c Agent identity is bestowed by symbiosis

Within Myco's semantic frame, "the agent" is defined as **the
entity currently in symbiotic operation with this substrate**. The
agent has no Myco-bestowed identity independent of the substrate;
the substrate has no Myco-bestowed purpose independent of an agent.
Identity is the property of the **pair**, like lichen (fungus + alga)
or mycorrhiza (fungus + plant root) — neither alone is the symbiotic
organism.

Operational consequences:

- Same substrate operated successively by Claude Opus, then GPT-5,
  then Claude Sonnet → **the same agent** from Myco's perspective.
- Different substrates operated by the same underlying model →
  **different agents** (one per substrate).
- A substrate with no current operator → **dormant** (agent
  identity is recoverable when an operator returns).
- A substrate destroyed → **the agent it hosted ceases to exist as
  a Myco-bestowed identity** (the underlying model continues; the
  symbiotic agent does not).
- Same-substrate concurrent operators are out of scope: P1 is
  intra-substrate (one operator per substrate at a time); multi-
  agent coordination happens via P5 inter-substrate federation, not
  concurrent operation.

### P2. 永恒吞噬 — Eternal Ingestion （吞噬万物）

Myco consumes without bound. Any input the agent can point at — a
decision, a debate, a friction note, a log file, an external
document, a conversation fragment, a failed approach, a vector-
retrieval result, an LLM output, an API response, a human-facing
summary, a screenshot, a media file — is ingestible raw material.
There is **no filter on what enters**.

#### P2.a Inclusion (consequence)

P2 implies Myco is the **superset framework** for every adjacent
agent-tooling sub-technique. Vector retrieval is one form of
substrate query; conversation history is one type of raw material;
agent-side LLM calls happen within Myco-prepared scaffolding;
semantic file federation replaces ad-hoc file sync; human-facing
summaries are one exception (per L0.5-era's `brief`-style carved-out
human-readable exception). All these techniques **live inside
Myco's framework**; Myco does not refuse them and they do not
exist in parallel.

Filtering and shaping are downstream (P3, P4) — never at intake.

### P3. 永恒进化 — Eternal Evolution

Myco's **own shape evolves**. The schema of the substrate's identity
record, the roster of subsystems, the vocabulary of operations,
the rules, the contract itself — all of these are first-class
mutable objects, changed through agent-driven governance under P1.b's
two-tier boundary.

An unchanging substrate is a dead substrate. Schema bumps, rule
revisions, vocabulary refactoring are normal operations, not
exceptional events.

### P4. 永恒迭代 — Eternal Iteration

Every operating session refines what prior sessions produced. There
is no terminal state. A piece of substrate content that is "final"
today is open to re-metabolization tomorrow as context sharpens.

"Final" is not a status. Retro-editing previously-processed material
is allowed and expected — tracked, not suppressed. The metabolic
state of the substrate (raw / partially digested / structurally
absorbed) is the **heartbeat**: a substrate with zero metabolic
activity is either perfect or stagnant; assume stagnant until proven
otherwise.

### P5. 万物互联 — Universal Interconnection （菌丝网络）

The substrate is a **connected graph**, not a collection. Every node
(piece of captured material, structural element, governance record,
external artifact, decision, code module if any) is reachable from
every other by traversal. Orphans are dead tissue.

The graph spans both **intra-substrate** (within one substrate's
interior) and **inter-substrate** (across federated substrates).
Federation is a first-class operation, not an afterthought.

---

## §3. What Myco is not

- **Not a documentation system.** Humans don't browse Myco.
- **Not a single-project knowledge base.** A substrate may hold
  knowledge about any number of projects, domains, topics.
- **Not a chatbot memory.** Conversational recall is incidental;
  durable, structured, self-validating substrate is the target.
- **Not version control.** Git owns history; Myco owns *current
  shape* of the symbiotic graph.
- **Not a file synchronizer.** Inter-substrate federation is
  semantic; bytes are not the unit.
- **Not a framework competing with LangChain / CrewAI / DSPy /
  etc.** Those are agent-orchestration libraries; Myco is the
  cognitive substrate orthogonal to them. Agents using those
  libraries can also use Myco; Myco's framework subsumes their
  output as raw material (per P2.a).
- **Not, at this layer, a specific verb set or rule set or
  subsystem partition.** Those are L1 / L2 / L3 design choices
  constrained by L0 but not encoded by L0.

## §4. The five derived invariants

Every L1/L2/L3 design must enforce all five:

1. **Symbiosis-as-identity.** The substrate frame defines "the
   agent"; the agent definitionally operates the substrate. Neither
   has independent Myco-identity. (Projects: P1.c)
2. **Agent-only maintenance + governance gate.** Daily operation is
   agent-autonomous; L0/L1/MAJOR/MINOR changes need owner approval.
   (Projects: P1.b')
3. **Self-validating substrate under continuous change.** The
   substrate evolves and iterates, but every claim it makes about
   itself is checked against a single source of truth at every lint
   pass. The agent cannot silently corrupt the substrate. (Projects:
   P3, P4)
4. **Top-down subordination, mycelial connectedness.** L0 governs
   L1 governs L2 governs L3 governs L4; simultaneously, every node
   is reachable from every other. Hierarchical rigor + graph
   density are the substrate's skeleton and circulatory system.
   (Projects: P2, P5)
5. **Universal inclusion.** Adjacent agent-tooling sub-techniques
   (RAG / conversation memory / external APIs / LLM calls /
   federation / human-facing summaries) are subsumed within Myco's
   framework, not run in parallel. (Projects: P2.a)

## §5. Biological metaphor (authoritative)

Myco uses biological vocabulary deliberately and consistently. The
metaphor is not decoration — it is the agent's prior over what each
verb / rule / subsystem means when cold-read. The metaphor names
the load-bearing subsystem roles:

| Subsystem family | Biological role |
|---|---|
| **Germination** | Spore → first hyphae; the birth of a new substrate |
| **Ingestion** | Feeding — devour raw inputs without filter (P2) |
| **Digestion** | Metabolism — drive eternal iteration + evolution (P3, P4) |
| **Circulation** | Perfusion, signaling, propagation — maintain the mycelium graph inside and across substrates (P5) |
| **Homeostasis** | Immune + regulation — enforce invariants during continuous change (P1, P3) |
| **Cycle** | Life-cycle composer — governance, session-boundary, schema evolution (P3, P4) |
| **Boundary** | Skin — the outward interface to the agent's runtime + neighbor substrates |

**No alternate vocabulary.** Within v0.9 doctrine and implementation,
verb names, subsystem names, rule names, and module names must come
from the fungal-biology lexicon. This rule is mechanical: an agent
cold-reading the substrate uses the names as a semantic prior.

The **specific verb set / rule set / subsystem partition** that v0.9
ships is an L1/L2/L3 design choice — it is **not encoded at L0**.
v0.9 may choose any number of verbs, any subsystem partition, any
governance rule cardinality, as long as each name comes from the
fungal-biology lexicon and the set together satisfies §4's five
invariants.

---

## §6. Living Bets — the bet Myco is making (v0.9 form)

This is the meta-commitment that authorizes Myco's existence. It is
deliberately falsifiable.

**The bet.** Myco's symbiotic-organism shape — agent + substrate as
mutually constitutive — has value **at every tier of agent
intelligence**, provided the substrate's persistence budget exceeds
any single agent's read window. As LLM models grow, the protocol's
value grows in proportion to substrate persistence.

**The counter-bet.** Sutton's bitter lesson predicts that general-
purpose methods with more compute eventually outperform hand-coded
structure. A strong reading predicts that a sufficiently capable
agent does not need a symbiotic substrate — it just holds everything
in context and acts coherently. If that reading wins, Myco is
scaffolding a smarter agent simply discards.

**The wager.** Symbiotic substrate value survives model growth **in
proportion to the substrate's persistence budget**. A short-lived,
single-session task can be solved by raw context-holding; a multi-
session, multi-host, federated symbiosis cannot, because no single
agent's context covers the full mycelial graph at once.

### The observatory (v0.9 form, per L0.5 Decision 4B)

Living Bets is measured as a **multi-signal observatory**, not a
single-K threshold. The substrate maintains continuous metrics on
multiple independent axes:

- **Persistence budget** (total content in the substrate)
- **Evolution rate** (governance changes over time)
- **Query diversity** (variety of substrate-reads per session)
- **Fork count** (federated substrates spawned)
- **Time trend per signal** (up / flat / down)
- **Read-window-relative position** (substrate-size /
  agent-context-window ratio)
- **Composite health score** (weighted aggregation)

Each signal has its own emergent threshold (not statically
hardcoded — emerges from the substrate's own historical metrics).
Living Bets win/loss is evaluated by **multi-signal posture**, not
single number.

The substrate self-reports through the observatory. When the
observatory shows persistent retreat across multiple signals, that
is the substrate's own admission of bet weakening — a falsifiable
self-audit signal, not a subjective judgment.

### Review cadence

Every MAJOR-release window (whenever the contract crosses a MAJOR
boundary) re-audits this section. The concrete trigger for
fundamental redesign: if observed agent behavior shows that
substrates of arbitrary size are operated without protocol mediation
(i.e. the agent holds everything in context and the verb / governance
surface is no longer exercised), Myco must re-justify its existence
or retire.

Until that trigger fires, the five 永恒X principles + the symbiosis
formulation stand.

**Not a principle.** This Living Bets section is not a sixth
principle. It holds P3 (永恒进化) and P4 (永恒迭代) accountable to
falsifiability, and it tempers P1 (只为 Agent) with an honest
statement of *which* agent-tier the current shape is optimized for.
It is a meta-commitment, not a rule.

---

## §7. Reading sequence for a new agent

1. This file (L0) — five root principles + five invariants + the
   wager.
2. (Future) L1 — the contract / hard rules / canon schema / exit
   codes. Currently undrafted in v0.9.
3. (Future) L2 doctrine — per-subsystem doctrine. Currently
   undrafted.
4. (Future) L3 implementation — how the code is organized. Currently
   undrafted.
5. (Future) L4 substrate — the live instance (this branch's canon-
   equivalent + entry-page-equivalent + notes-equivalent + code).
   Currently undrafted.

The v0.9 substrate is being designed top-down: L0 first (this
document, owner-pending), then L1, then L2, then L3, then code.

## §8. Changes to this page

L0 is the identity layer. Any change requires:

1. A craft-style proposal document in the v0.9 substrate's craft-
   equivalent location, arguing the revision.
2. Explicit owner approval recorded in the proposal.
3. A `contract_version` MAJOR bump (per P1.b'').
4. A cascade review of every lower-layer doc for implicit dependencies.

L0 revision is never implementation-driven and never routine.

## §9. Proto archaeology

For lineage:

- [`_archive/proto_myco_v0_8/L0_VISION_proto.md`](../../_archive/proto_myco_v0_8/L0_VISION_proto.md) —
  the L0 of the proto-Myco era (v0.4 - v0.8.7).
- [`_archive/proto_myco_v0_8/L0_5_ESSENCE.md`](../../_archive/proto_myco_v0_8/L0_5_ESSENCE.md) —
  the v0.8 → v0.9 transitional doctrine layer that carried the 5
  decisions absorbed into this L0.
- [`_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md`](../../_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md) —
  the deliberation log: 4 self-corrections + 100%-confidence loop +
  20 candidate holes + 10 fix-Hs (Fix-H6 agent-identity-internalisation,
  Fix-H3 two-tier human-loop, Fix-H8 non-recursive bootstrap, Fix-H11
  Living Bets observability, Fix-H12 concurrency-scope; second-order
  H21-H25 closing the recursion / governance-boundary / embryonic-
  status / K-authority / lazy-medium gaps).

None of these are authoritative in v0.9. They preserve the lineage
that led to v0.9's shape.

---

## §10. The dead-embryo concession

Decision 3D (owner-arbitrated 2026-05-13, recorded in L0.5): the
v0.4 → v0.8.7 line is **not "previous Myco"** but **proto-Myco /
dead embryo / failed gestation attempts**. v0.9 is **Myco's first
true birth**.

This document is the first artifact of that birth. Every subsequent
v0.9 design step (L1 contract, L2 doctrine, L3 implementation, L4
canon + code) must directly trace its decisions back to one or more
of P1-P5 (with P1.a/b'/b''/c, P2.a) and one or more of the five
invariants in §4. Anything that cannot trace back is rejected as
proto-Myco residue.
