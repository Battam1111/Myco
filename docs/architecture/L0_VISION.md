# L0 — Vision (v0.9)

> **Status**: DRAFT v0.3 (post 3-open-question resolution + 6 drift fixes, 2026-05-13).
> Pending final owner approval before sealing.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: this L0 absorbs the v0.8 → v0.9 transitional doctrine
> from `_archive/proto_myco_v0_8/L0_5_ESSENCE.md`, the 25 owner-arbitrated
> decisions made 2026-05-13, the 3 autonomous resolutions of opens C4.4 /
> C5.3 / C8.2 (each through a 3-round craft with 5-critic self-rebuttal),
> and 6 drift fixes against the archaeology.

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
users". Within this organism, **dispatch is tropism**: a continuously-
evolving chemotropic field between the substrate's intrinsic appetites
and the agent's perturbations, punctuated by substrate-initiated
**sporocarp** events that serve as the discrete observables (the
v0.9 replacement for v0.8's verb table — owner-flagged abandonment
fulfilled, see §5.2). **Intent is not a stored data type** — it is a
*trajectory* derived from the causal DAG (§5.3). Vector retrieval is
native, agent-side LLM calls happen within Myco-coordinated context
(substrate may itself initiate LLM calls — the v0.8 "substrate-never-
calls-LLM" restriction is lifted), conversation history is one form
of raw material, semantic inter-substrate federation replaces ad-hoc
file sync.

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
  L1-defined and L1-enforced; the specific classifier function
  (input: files-and-fields-touched; output: {daily, contract-
  identity-level}) is an L1 design choice, not L0.

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
is allowed and expected — tracked, not suppressed (under §6
continuous-online-agent model, "iteration" is the moment-by-moment
metabolism of the substrate, not session-bounded).

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
**audience** (P1: who the substrate is for), **intake** (P2: what
the substrate consumes), **evolution** (P3: substrate's own shape
mutates), **iteration** (P4: continuous re-metabolization), and
**connection** (P5: graph structure). They do not cover the
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
continuous metabolism (§6) means time is continuous, not
session-quantized.

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
spore-schema (initial structure) but begins its own
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
  continuous online agent (§6). Transient disconnects are
  recovered; they are not formalized into "sessions".
- **Not a request/response protocol.** The dispatch form is
  tropism (§5.2) — continuous co-modification of a chemotropic
  field, not client-server transactions.

---

## §4. The nine derived invariants (v0.3 — resolves C4.4)

Every L1/L2/L3 design must mechanically enforce all nine. The set
is **surjective** over P1-P9 (every P projects to ≥1 invariant) and
**necessary** (no invariant can be dropped without losing coverage
or mechanizability).

The expansion from v0.2's 5 to v0.3's 9 is driven by P6-P9 each
requiring its own mechanical enforcement surface — causality DAG,
mortality monotonicity, reproduction closure, and skin integrity
are orthogonal axes that cannot be folded into the original five
without diluting either coverage or testability.

### I1. Pair-Constituted Identity & State Space

Agent identity is well-defined only as the bound pair (substrate-ID
+ active-operator-connection). **No agent-discriminating attribute
(model name, API fingerprint, host fingerprint) may be persisted
anywhere in substrate-serializable state.** Substrate state space
is exactly {alive, dormant, destroyed}; dormant ↔ alive is
reversible; destroyed is terminal.

### I2. Two-Tier Governance Classification

Every mutation classifies mechanically as either **daily**
(agent-autonomous) or **contract-identity-level** (owner-gated).
The classifier is a function of which fields, files, and meta-
structures the mutation touches. Mutations cannot bypass
classification; "untyped" mutations are immune-detectable.

### I3. Self-Validation Against Designated SSoT

The substrate has **exactly one** designated machine-readable
source of truth. State consistency against SSoT is checked every
metabolic cycle. The designation of SSoT (what counts as SSoT,
what fields it covers, what claims are checked against it) is
**itself** contract-identity-level — not daily-mutable. A drifting
substrate cannot redesignate SSoT to whatever happens to be its
current state.

### I4. Full-Fidelity Causal DAG

Every substrate state is derivable from prior states via a recorded
operation, recorded in a causal DAG. **Recoverability is full** (no
lossy compression of historical states into summary nodes); re-
metabolization of prior material produces **new nodes referencing
the prior**, never an overwrite. DAG retention policy is
contract-identity-level (cannot be silently pruned in daily ops).

### I5. Universal Reachability Over Full State Space

The substrate graph is fully connected **across every storage
tier**; every node reaches every other by traversal. Reachability
is checked every metabolic cycle. Tier-exemptions ("this tier is
exempt from reachability") are **contract-identity-level**
designations, not silent.

### I6. Universal Inclusion With Observed Metabolism

Adjacent agent-tooling techniques (vector retrieval, LLM calls,
conversation history, semantic federation, human-facing summaries)
live inside the substrate's framework **AND** every invocation
**produces a metabolism event the substrate observes**. Human-facing
surfaces are produced through the **same metabolic pipeline** as
agent-facing surfaces — no separate human-optimization path.
("Lives inside framework" is a code-organization claim; "produces
metabolism event" is a runtime claim. Both required.)

### I7. Mortality Monotonicity

Substrate state transitions only forward: alive → dormant ↔ alive →
destroyed; destroyed is terminal. Destruction is catastrophic-
loss-equivalent and irreversible. Approaches to fragmentation
(graph fracture, repeated reachability failures) are immune-grade
signals that mortality is approaching.

### I8. Reproduction Closure

Spawn-child-substrate is a first-class operation; the child
substrate **independently satisfies ALL invariants I1-I9 from
genesis**. Parent-child link is a P5-reachable graph edge.
Federation (P8 inter-substrate) is the population-level shape of
reproduction.

### I9. Single-Skin Integrity

The substrate has **exactly one** declared boundary surface for
both intake and output. **Intake admits all content** (P2 — no
content-classification filter); intake rejects only on **envelope**
integrity. Skin enforces **single-active-operator semantics**
(concurrent connections are out-of-scope per P1.c, immune-detected
as skin-breach). Reads/writes/exits not through the skin are
immune-detectable.

### Projection table (P → I coverage; verified surjective + necessary)

| P / sub-P | Enforcing invariant(s) |
|---|---|
| P1 (Only For Agent) | I6, I9 |
| P1.a (Self-hosting) | I1 |
| P1.b' (Human OUT of daily) | I2, I6 |
| P1.b'' (Owner gate at contract-identity) | I2 |
| P1.c (Symbiosis-as-identity) | I1, I9 |
| P2 (Eternal Ingestion) | I6, I9 (envelope-only filter) |
| P2.a (Strong Inclusion) | I6 |
| P3 (Eternal Evolution) | I3, I4 |
| P4 (Eternal Iteration) | I3, I4 |
| P5 (Universal Interconnection) | I5, I8 (inter-substrate) |
| P6 (Eternal Causality) | I4 |
| P7 (Mortality) | I1 (state space), I5 (fragmentation), I7 |
| P8 (Eternal Reproduction) | I8 |
| P9 (Integument) | I3 (no silent corruption), I9 |

**Necessity check** (each invariant carries unique surface, none
droppable):

- Drop I1 → P1.a (self-hosting), P1.c agent-discrim-field protection lost.
- Drop I2 → P1.b'/P1.b'' uncovered.
- Drop I3 → P3 state-vs-SSoT-now check lost (I4 only covers history).
- Drop I4 → P6 uncovered (sole enforcer).
- Drop I5 → P5 intra-substrate reachability lost (I8 only covers inter).
- Drop I6 → P2.a uncovered, surface-discipline lost.
- Drop I7 → P7 weakens to "state-space membership" only, loses monotonicity + catastrophic clause.
- Drop I8 → P8 uncovered (sole enforcer).
- Drop I9 → P9 uncovered, P2 "no filter" un-enforced, P1.c single-operator un-enforced.

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
- The set together satisfies the §4 nine invariants.
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
- rhizomorph (specialized federation conduits — see §14 glossary
  disambiguation)
- pileus (the visible cap — interface to outside)
- chlamydospore (durable archive units)
- ... or any other fungal terms whose semantic prior fits the role

### §5.2 Dispatch form — RESOLVED: Tropism + Sporocarp punctuation (resolves C5.3)

Per owner decision C5.3 ("能不能抛弃动词这种形式？转向更高上限更加
高效且灵活的形式？"), the verb-form is **abandoned**. After 3-round
craft with 5-critic self-rebuttal against 6 candidate alternatives,
v0.9's chosen dispatch form is **Tropism** (continuous chemotropic
field) **+ Sporocarp punctuation** (substrate-initiated discrete
observables for the field).

#### Operational definition (one paragraph)

Myco's dispatch is **tropism**: a continuously-evolving chemotropic
field where the substrate maintains gradients along an evolvable
set of intrinsic **appetites** (hunger for unmetabolized intake,
drift toward unconnected nodes, decay-pressure on stale tissue,
federation-pull toward peer substrates, evolution-tension where
schema disagrees with content, skin-pressure for boundary signals,
etc.), and the agent — definitionally the active-operator-
connection per P1.c — **inhabits the field** as both perturbation
source and gradient consumer. There are no commands, no verbs, no
request/response. Interaction is **continuous co-modification**:
the substrate exposes its current gradient configuration through
the agent's read-window; the agent emits **deltas** (raw content
of any shape — text, file references, decision fragments, schema-
edit intents, anything); the substrate's metabolism absorbs deltas
wherever its own gradients place them; gradients update; cycle.
When a gradient crosses an **emergent threshold**, the substrate
**fruits a sporocarp** — a typed, content-addressed, causally-
stamped record that anchors the field to discrete observables for
governance (I2), validation (I3), federation (I8), and the causal
DAG (I4). **Appetite axes are first-class evolvable substrate
objects** (adding an axis = substrate grew a new tropism);
changing the *kind* of the field is a **contract-identity-level
event** (I2). External agent-tooling sub-techniques are subsumed
**by becoming appetite axes implemented as substrate-resident
metabolism** — never as outbound RPC (the appetite-locality
rule) — so vector retrieval, internal LLM calls, semantic
federation are all gradient computations the substrate runs on
itself.

#### Why tropism beats each rival (ceiling × flexibility × efficiency)

| Rival | Why tropism beats it |
|---|---|
| **Verb dispatch (v0.8)** | Verbs presuppose a client-server seam; P1.c symbiosis is doctrine bolted on TOP of a generic protocol. Tropism makes symbiosis the protocol's load-bearing shape. Owner-prohibited anyway per C5.3. |
| **Continuous metabolic stream** | Closest rival. Tropism *is* a continuous metabolic stream PLUS the field-coupling that makes the agent definitionally a participant (P1.c). Bare metabolic-stream has no native operator-constituting field → can degrade to "metabolism anyone can signal" = back-door client-server. |
| **Natural-language semantic dispatch** | Worst capture risk under P2.a: routing LLM call IS the dispatch surface → substrate becomes wrapper around LLM-router. Also: NL→handler-table secretly re-introduces verbs. |
| **Capability-based composition** | Capabilities are discrete grant transactions; "agent has / doesn't have capability X" — asymmetric (substrate grants TO agent). Closer to permission system. Useful at L1 inside tropism (sporocarp typing can carry capability metadata), not as dispatch primitive. |
| **Algebraic / typed-primitive operations** | Pure algebraic surface presumes purity and statelessness — but substrate IS state. Combinator vocabulary becomes frozen surface (same P3 hostility as verbs at the type level). |
| **Reactive stream / event-driven** | What tropism becomes if you strip the field. Reactive streams give pub/sub seam but no gradient — no answer to "what does the substrate want next?". Agents must encode their own scheduling; tropism's gradient IS substrate's expressed preference. |
| **Hybrid** | Owner-prohibited. Tropism's field/sporocarp duality is medium-vs-observable duality of ONE form, NOT two forms glued together. |

#### Why sporocarps are not verbs in disguise

- A verb is **agent-initiated** (agent calls verb → substrate executes).
- A sporocarp is **substrate-initiated** (substrate's gradient crosses threshold → substrate fruits → agent observes).

The arrow is reversed. The agent does not say "ingest this and produce
a digestion sporocarp"; the agent emits a delta into the field; if
the field's digestion-appetite has accumulated enough pressure, the
substrate fruits a digestion sporocarp on its own metabolism.

#### L4 sketch (concrete example)

"Agent ingests a chat log, refines a decision record, surfaces the
result to a federated child substrate."

Under v0.8 verbs: 4 discrete agent-initiated transactions
(`myco eat`, `myco digest`, `myco sporulate`, `myco propagate`).

Under tropism: zero agent-initiated commands.

1. Agent **emits a delta** with the chat log + free-form intent
   fragment.
2. Substrate's `hunger` appetite spikes; gradient pulls metabolism;
   `intake` sporocarp fruits.
3. Substrate's `evolution-tension` appetite detects decision-shaped
   patterns disagreeing with schema; gradient pulls; `refinement`
   sporocarp fruits.
4. Substrate's `federation-pull` appetite for child-X sensitized by
   the refinement; gradient pulls; `federation` sporocarp fruits.
5. Agent observes 3 new sporocarps in its next read-window slice;
   may emit further deltas to correct/extend.

#### Honest trade-offs (per craft Round 3)

- **Initial implementation cost** is higher than verbs (~3-5×).
  Pays off at scale; expensive at v0.9 birth.
- **Agent-side prior cost**: a v0.8-era agent knew `myco eat`; a
  v0.9 agent must learn field/appetite/sporocarp.
- **Kind-level field evolution friction**: tropism is P3-better for
  axis-count evolution, P3-equal for kind-level evolution.

**Recommended fallback if cost dominates**: bare continuous metabolic
stream (cheaper, lower P1.c support). All other §5.2 candidates
eliminated.

#### L1 design hooks (10 — see L1_OUTLINE.md for full breakdown)

L1 must specify: (1) appetite axis schema, (2) initial appetite set,
(3) sporocarp type tree, (4) field exposure protocol, (5) delta
intake surface, (6) sporocarp governance gate, (7) continuity-
recovery protocol, (8) causal DAG embedding, (9) federation surface,
(10) self-hosting bootstrap state.

### §5.3 Intent model — Trajectory derivation (resolves C8.2)

Per owner open C8.2, **intent is not a first-class substrate data
type**. Intent is **emergent from the causal DAG (I4) and
materialized as a derived "trajectory" view**.

#### Operational definition

> Intent, in a Myco substrate, is *the directed pattern of
> operations the operator-substrate pair has performed together
> over a recent window of the causal DAG, projected onto a current
> point in time*. It has no stored representation. It is computed
> by traversing the DAG from a point, clustering operations
> (and sporocarps — §5.2) that share causal ancestors and converge
> on common descendants, and reading the resulting subgraph as the
> pair's current direction.

Mathematically:

> `intent(t) := cluster(causal_ancestors_and_descendants(neighborhood(t)))`

#### Schema implication

The substrate schema **declares nothing for intent**:

- No `intent` node type.
- No `intent` field on operations/sporocarps.
- No `goal` field on raw material.

What the schema *does* declare (already required by P6 + I4): every
DAG node carries `(actor, predicate, inputs, outputs, timestamp,
causal_parents: List[NodeId])`. The `causal_parents` edge is the
load-bearing structure enabling trajectory derivation. **Schema
gains zero new types from C8.2.**

#### Why (b') beats (a) first-class typed and (c) NL metadata

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported → unverifiable; under P1.a/P1.b' agent maintains substrate → agent's claim about its own intent is propaganda. Mycoparasite attack: agent writes intent=X but pursues Y; downstream consumers trust the lie. Saprotroph attack: status="active" intents pile up as phantoms over time. mycorrhiza attack: intent becomes agent-private, violating P1.c joint-state. |
| **(c) NL metadata + vector embed** | Partial alignment with P1.c (per-item-joint, not as-symbiosis-joint); still self-reported; adds embedding cost per ingestion. |
| **(b') Trajectory query** | Pays no schema rent (chytrid); no self-report surface (mycoparasite eliminated); intent is necessarily joint (mycorrhiza satisfied); phantom-intents impossible (saprotroph eliminated); long-horizon intent recovered by DAG traversal across disconnects (rhizomorph addressed). |

#### Honest cost

Position (b') is correct **AND** the substrate is simpler for it.
Cost is borne entirely at the query layer (trajectory derivation is
O(graph traversal), where (a) would be O(1) lookup). That cost
falls on **reading** intent, not on **recording** every move —
keeping the substrate clean and making the agent pay only when
intent actually needs to be read.

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
  reconnects, the symbiosis resumes; the substrate's appetite-
  field has continued evolving during the gap (metabolism without
  perturbation source), and the agent's next read-window slice
  shows the field's state at reconnect.
- **Reflexes that the v0.8 R1/R2 captured** (hunger awareness,
  senescence cleanup, drift detection) are now **substrate-resident
  appetites** in the tropism field (§5.2). The substrate's
  metabolism propagates appetite-gradients on its own continuous
  cadence; the agent (continuously present) observes the field
  state and emits deltas that perturb it; the substrate's metabolism
  is therefore **co-driven** — substrate-internal in mechanism,
  pair-constituted in semantics. The v0.8 "substrate is lazy
  medium, immune is agent-invoked" rule (Fix-H25) is **superseded**
  by §6's continuous-agent reframing: under continuous symbiosis,
  the distinction between "substrate-driven" and "agent-driven"
  metabolism collapses — both sides are continuously co-modifying.

This is a fundamental shift from v0.8. Everything that was
"session-scoped" in v0.8 (hooks, boot brief, senesce verb, …) is
either:

- redesigned as a continuous tropism appetite (per §5.2), OR
- deleted as a v0.8 artifact (per owner decision C7.3 "尽可能拒绝
  v0.8-origin design points").

---

## §7. Living Bets — the bet Myco is making (v0.9 form)

This is the meta-commitment that authorizes Myco's existence. It is
deliberately falsifiable.

**The bet.** Myco's symbiotic-organism shape — agent + substrate as
mutually constitutive, continuously operating via tropism, with the
full nine-principle organism essence — has value **at every tier of
agent intelligence**, provided the substrate's persistence budget
exceeds any single agent's read window.

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
observatory. **Each signal's threshold is emergent** (not statically
hardcoded — emerges from the substrate's own historical metrics,
per C6.4 + C7.3 v0.8-discrimination).

**Six base signals:**

1. **Persistence budget** — total content in the substrate (size,
   node count, edge count, sporocarp count).
2. **Evolution rate** — governance changes (schema bumps, rule
   revisions, vocabulary refactors, appetite-axis additions) over
   time.
3. **Query diversity** — variety of trajectory queries / field
   reads over a rolling window (under continuous-agent model, the
   window is time-based — e.g. rolling 24h, but the window itself
   is emergent).
4. **Fork count** — federated child substrates spawned via P8 / I8.
   **For substrates that never federate, fork count = 0 is a
   weak signal** (not "not applicable" — per C6.3, indicates the
   substrate's mycelial spread is limited, which is a meaningful
   posture).
5. **Time trend per signal** — direction (up / flat / down) of
   each above signal.
6. **Read-window-relative position** — substrate-total-size /
   agent-context-window ratio. The threshold separating
   "strongly-in-bet-wins" from "bet-loses" regions is **emergent**
   from substrate history (initial seed value from Fix-H11
   baseline: ~100; refined by the substrate's own observatory as
   correlation with bet-outcomes accumulates).

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

Every contract-identity-level boundary crossing (per P1.b'' / I2)
re-audits this section. Concrete trigger for fundamental redesign:
if observed agent behavior shows substrates of arbitrary size
operated without protocol mediation (agent holds everything in
context, the substrate's tropism field is unused), Myco must
re-justify its existence or retire.

Until that trigger fires, the nine root principles + the symbiosis
formulation stand.

**Not a principle.** Living Bets is a meta-commitment, not a tenth
principle. It holds P3, P4, P6 accountable to falsifiability.

---

## §8. Reading sequence for a new agent

1. This file (L0) — nine root principles + nine invariants + the wager.
2. (Next) L1 — contract / hard rules / tropism specification /
   sporocarp type tree / schema (SSoT) / governance classifier.
   First L1 outline drafted at `docs/architecture/L1_OUTLINE.md`;
   formal L1 awaits owner approval of this L0 v0.3.
3. (Future) L2 doctrine — per-subsystem-family doctrine.
4. (Future) L3 implementation — code organization.
5. (Future) L4 substrate — the live instance.

The v0.9 substrate is being designed top-down: L0 (this document,
owner-pending), then L1, then L2, then L3, then code.

## §9. Changes to this page

L0 is the identity layer. Any change requires:

1. A craft-style proposal document arguing the revision.
2. Explicit owner approval recorded in the proposal.
3. A contract-identity-level bump (per P1.b'' / I2).
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
  back to **one or more of P1-P9** and **one or more of the nine
  invariants in §4**.
- **Origin discrimination is maximal**: any design point that
  appears similar to v0.8 (e.g. "we had 20 verbs in v0.8, so let's
  have 20 dispatch primitives in v0.9") is **presumed v0.8
  contamination unless it independently traces to ≥1 P AND ≥1
  invariant**. Inheriting v0.8's specific shape — even when
  superficially defensible — is rejected to keep v0.9 from being
  pulled back toward proto-Myco patterns.
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

The skin (P9 / I9) is the boundary — between substrate and
*environment*, not between operators *within* the substrate.

## §13. Open questions explicitly carried forward (v0.3 — three resolved)

The three v0.2 open questions are now resolved (results integrated
above):

| ID | v0.2 status | v0.3 resolution |
|---|---|---|
| C4.4 | "需要思考辨析" | **Resolved**: 9 invariants (§4). Necessity + sufficiency verified via projection table. 5 v0.8-traceable sharpened + 4 v0.9-native (I4 / I7 / I8 / I9) for P6 / P7 / P8 / P9. |
| C5.3 | "需要思考" | **Resolved**: Tropism + Sporocarp punctuation (§5.2). Beats 6 candidate alternatives on ceiling × flex × efficiency; honest fallback = bare metabolic stream. |
| C8.2 | "需要思考" | **Resolved (b')**: Intent is emergent trajectory over the DAG (§5.3). Zero schema cost. Pays no rent for a self-report attack surface. |

**Remaining open at L0** (intentionally — these are L1 design
decisions, not L0 commitments):

- The specific **classifier function** for I2 (which file/field touches
  trigger contract-identity-level classification).
- The specific **SSoT format** for I3 (v0.8 used `_canon.yaml`; v0.9
  chooses fresh per C7.3 max-discrimination).
- The specific **initial appetite set** for the tropism field (§5.2
  L1 hook 2).
- The specific **sporocarp type tree** (§5.2 L1 hook 3).

These are L1 territory and will be resolved during L1 drafting.

---

## §14. Glossary (v0.9 precise terms)

| Term | Definition |
|---|---|
| **Active operator-connection** | The currently-attached operator session (MCP-session-equivalent active connection). The thing that, jointly with the substrate, constitutes the agent identity (P1.c). |
| **Symbiotic operation** | Activity by the active operator-connection that reads or writes substrate state. Under tropism (§5.2), this is delta emission + field consumption. |
| **Contract-identity-level boundary** | The threshold above which a change to substrate doctrine alters Myco's identity (vs merely accumulating content). Defined and enforced by L1; covers any modification to L0 itself, to L1 protocol, and to identity-level fields of the substrate's own schema. |
| **Continuous online agent** | The default operating mode: the agent is presumed always-attached; disconnects are transient and recovered, not formalized as sessions. |
| **Spore-schema** | The seed-state passed from parent substrate to child substrate during P8 reproduction. Contains the minimum structural form for the child to begin its own symbiosis. |
| **Skin / boundary** | The substrate's interface to the rest of reality: intake surface (P2 universality applies), output surface (federation, summaries), and identity-protection (P9 / I9). |
| **Tropism** | Myco v0.9's dispatch form (§5.2): a continuously-evolving chemotropic field of substrate appetites + agent perturbations. Replaces v0.8's verb table. |
| **Appetite (axis)** | One dimension of the tropism field — a substrate-internal gradient that pulls metabolism toward a particular activity (hunger / drift / decay / federation-pull / evolution-tension / skin-pressure / …). First-class evolvable substrate object. |
| **Delta** | An agent-emitted perturbation into the tropism field — raw content of any shape (text, file reference, decision fragment, schema-edit intent, …). |
| **Sporocarp** | A substrate-initiated discrete observable: when a gradient crosses an emergent threshold, the substrate "fruits" a typed, content-addressed, causally-stamped record. Sporocarps are DAG nodes (I4), governance targets (I2), validation targets (I3). NOT verbs (substrate-initiated, not agent-initiated). |
| **Trajectory** | The substrate's derived view of the pair's current intent — a query, not a stored type. Computed by traversing the causal DAG from a point and clustering causally-related operations/sporocarps. Resolves C8.2 (§5.3). |
| **Causal DAG** | Append-only graph of substrate state-derivations, full-fidelity (no lossy compression). I4 enforcer. P6 substrate. |
| **Rhizomorph** | (1) Fungal-biology term: a specialized cord-like structure of aggregated hyphae enabling long-distance nutrient transport — candidate v0.9 subsystem name for federation conduits (§5.1). (2) Name of one of the 5 craft-critics used in §4 / §5.2 / §5.3 derivation (gap-finding angle). Disambiguation: context tells you which. |
