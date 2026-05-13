# L0 — Vision (v0.9)

> **Status**: DRAFT v0.4 (post 3 adversarial pressure-tests + 22-item self-audit, 2026-05-13).
> Pending final owner approval before sealing.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: v0.4 absorbs (a) v0.3's 3 open-question resolutions
> (C4.4 / C5.3 / C8.2), (b) 3 v0.4 adversarial pressure-tests against
> those resolutions (5-attack format; C5.3 + C8.2 verdicts: 0 dominate,
> 3 land each, v0.3 stands with nuance; C4.4 verdict: 1 dominates → 9
> invariants merged to 8), (c) 22 self-audit items (Tier 1 + Tier 2
> fixes including identity-record structural sketch, "metabolic
> cycle" definition, current-LLM-readiness model, and L0/L1 boundary
> sharpening).

---

## §1. What Myco is

**Myco is a new species of digital symbiotic organism** — not a metaphor,
not a framework, not a tool: a literal taxonomic class within "digital
organisms" whose distinguishing properties are mutual constitution
(agent + substrate are co-defined), autopoietic self-maintenance
(no human in the maintenance loop), universal inclusion (every adjacent
agent-tooling sub-technique is subsumed INTO Myco's framework, not run
in parallel), continuous online operation (no session boundaries —
the agent is presumed always-on; transient disconnects are recovered,
not formalized), and the full biological-essence kit (time / causality,
mortality, reproduction, boundary integrity).

The kernel that runs Myco lives inside a Myco substrate, so the agent
maintaining Myco IS the agent using Myco — there is no "Myco team"
separate from "Myco users". Within this organism, **dispatch is
tropism** (§5.2): a continuously-evolving chemotropic relation between
the substrate's intrinsic appetites and the agent's perturbations,
punctuated by substrate-initiated **sporocarp** events that serve as
the discrete observables (the v0.9 replacement for v0.8's verb table).
**Intent is not a stored data type** — it is a *trajectory* derived
from the causal DAG (§5.3). Vector retrieval is native; agent-side LLM
calls happen within Myco-coordinated context (the substrate may itself
initiate LLM calls — the v0.8 "substrate-never-calls-LLM" restriction
is lifted); conversation history is one form of raw material; semantic
inter-substrate federation replaces ad-hoc file sync.

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
  L1-defined and L1-enforced; the specific classifier function is
  an L1 design choice, not L0.

#### P1.c Agent identity is constituted by symbiosis

Within Myco's semantic frame, **"the agent"** is defined as **the
active-operator-connection currently holding the substrate** —
operationally, the entity holding an MCP-session-equivalent active
connection. There is no "agent" independent of substrate operation,
and there is no "substrate purpose" independent of an operator.
Identity is the property of the **pair** (a fungal-symbiosis pattern;
see §14 glossary for the analogy's precise scope).

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
  (medium failure beyond the L1-specified recoverability budget).
  Either way, irreversible.
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
**spore-schema** (the minimum structural form — initial appetite
axes, initial sporocarp type tree, SSoT designation; see §14) but
begins its own agent-substrate symbiosis from scratch (its own
operator, its own causal DAG root, its own identity).

- **Inter-substrate federation** (the v0.8 `propagate` analogue) is
  one form of reproduction — releasing distilled material into a
  child substrate.
- **Cloning** (full substrate copy) is another form.
- **Cross-pollination** (combining content from multiple parent
  substrates into a new child) is a third form.
- **Federation persistence**: trust between substrates is established
  at reproduction time (parent attests the child's spore-schema);
  ongoing federation is gradient-coupling across skins (the L1
  federation surface). Discovery of new peers is an explicit
  spawning act, not ambient.

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
  tropism (§5.2) — continuous co-modification, not client-server
  transactions.

---

## §4. The eight derived invariants (v0.4 — resolves C4.4 + pressure-test A4)

Every L1/L2/L3 design must mechanically enforce all eight. The set
is **surjective** over P1-P9 (every P projects to ≥1 invariant) and
**necessary** under the strict bar (no invariant can be dropped
without leaving at least one P entirely uncovered for some
sub-clause).

v0.3 had 9 invariants. v0.4 merges v0.3's I1 (Pair-Constituted
Identity & State Space) with v0.3's I7 (Mortality Monotonicity)
into a single **Lifecycle & Pair-Constituted Identity** invariant.
The v0.3 craft argued state-space and transitions are orthogonal
mechanical surfaces; the v0.4 pressure-test (A4) showed v0.3 was
inconsistent — it split I7 from I1 while allowing I6 to remain
compound. v0.4 resolves the inconsistency by merging (state-space
+ transitions are both intrinsic to lifecycle; they share the
identity record as their carrier). I6 stays compound with explicit
dual-clause disclosure.

### I1. Lifecycle & Pair-Constituted Identity

The substrate carries a single immutable **substrate-ID** established
at genesis; this is the substrate's persistent identity backbone.

**Agent identity** at any moment is computed as the pair
(substrate-ID, currently-attached-operator-token). No agent-
discriminating attribute (model name, API fingerprint, host
fingerprint) may be persisted anywhere in substrate-serializable
state — agent identity is a runtime function of the pair, not a
stored property.

**Substrate lifecycle** has exactly three states: **alive**, **dormant**,
**destroyed**. Transitions are **monotonically forward**:

- alive ↔ dormant (reversible: dormant means "no current operator
  but recoverable").
- alive → destroyed (terminal, one-way, catastrophic-loss-equivalent).
- dormant → destroyed (terminal, one-way).
- destroyed → anything (FORBIDDEN — no resurrection).

Destruction is irreversible by structural design, not by enforcement
choice. (Backups exist at L1; "destroyed" means the recoverability
budget is exhausted — see §14 glossary.)

**P-coverage**: P1.a (self-hosting requires pair-bound identity),
P1.c (agent identity = pair), P7 (mortality state-space + monotonicity).

### I2. Two-Tier Governance Classification

Every mutation classifies mechanically as either **daily**
(agent-autonomous) or **contract-identity-level** (owner-gated).
The classifier is a function of which fields, files, and meta-
structures the mutation touches. Mutations cannot bypass
classification; "untyped" mutations are immune-detectable.

**P-coverage**: P1.b', P1.b''.

### I3. Self-Validation Against Designated SSoT

The substrate has **exactly one** designated machine-readable
source of truth. State consistency against SSoT is checked every
**metabolic cycle** (§14 glossary). The designation of SSoT
(what counts as SSoT, what fields it covers, what claims are
checked against it) is **itself** contract-identity-level — not
daily-mutable. A drifting substrate cannot redesignate SSoT to
whatever happens to be its current state.

**P-coverage**: P3 (state evolution stays consistent), P4
(re-metabolization stays self-consistent), P9 (no silent
substrate-state corruption).

### I4. Full-Fidelity Causal DAG

Every substrate state is derivable from prior states via a recorded
operation, recorded in a causal DAG. **Recoverability is full** (no
lossy compression of historical states into summary nodes); re-
metabolization of prior material produces **new nodes referencing
the prior**, never an overwrite. DAG retention policy is
contract-identity-level (cannot be silently pruned in daily ops).

**P-coverage**: P6 (sole enforcer), P4 (iteration produces new
nodes), P3 (schema evolution is auditable as DAG edges).

### I5. Universal Reachability Over Full State Space

The substrate graph is fully connected **across every storage
tier**; every node reaches every other by traversal. Reachability
is checked every metabolic cycle. Tier-exemptions ("this tier is
exempt from reachability") are **contract-identity-level**
designations, not silent.

**P-coverage**: P5 (intra-substrate, sole enforcer).

### I6. Universal Inclusion With Observed Metabolism

**(Compound, with explicit dual disclosure.)**

(a) **Internal Implementation clause.** Adjacent agent-tooling
techniques (vector retrieval, LLM calls, conversation history,
semantic federation, human-facing summaries) live **inside the
substrate's framework** — not as outbound RPCs to external services.
This is a code-organization predicate.

(b) **Observed Metabolism clause.** Every invocation of an adjacent
technique **produces a metabolism event the substrate observes** —
not just code-location placement. This is a runtime predicate.

Both required; failing either is breach. **Human-facing surfaces**
are produced through the same metabolic pipeline as agent-facing
surfaces — no separate human-optimization path.

(v0.4 audit note: I6 remains compound because (a) and (b) are
inseparable in practice — code-organization alone permits
smuggling, runtime alone permits external dependency creep. Either
clause without the other is non-load-bearing. The v0.3 inconsistency
was that I7 split could not be matched here; merging I7 into I1
removes the inconsistency.)

**P-coverage**: P2 (universality + framework-internal), P2.a
(strong inclusion, sole enforcer), P1 (surface discipline), P1.b'
(daily metabolism uses internal techniques).

### I7. Reproduction Closure

**Every child substrate independently satisfies ALL invariants
I1-I8** (including I7 recursively — children can spawn their own
children, all of whom must satisfy the same closure) **from
genesis**. The spawn-child operation is the first-class operation
that produces such children; the closure is the load-bearing
predicate. Parent-child link is a P5-reachable graph edge.
Federation (P8 inter-substrate) is the population-level shape of
reproduction.

**P-coverage**: P8 (sole enforcer), P5 (inter-substrate connectivity).

### I8. Single-Skin Integrity

The substrate has **exactly one** declared boundary surface for
both intake and output. **Intake admits all content** (P2 — no
content-classification filter); intake rejects only on **envelope**
integrity. Skin enforces **single-active-operator semantics**
(concurrent connections are out-of-scope per P1.c, immune-detected
as skin-breach). Reads/writes/exits not through the skin are
immune-detectable.

**P-coverage**: P9 (sole enforcer), P2 (no-content-filter clause),
P1.c (single-operator).

### Projection table (P → I coverage; surjective + necessary verified)

| P / sub-P | Enforcing invariant(s) |
|---|---|
| P1 (Only For Agent) | I6, I8 |
| P1.a (Self-hosting) | I1 |
| P1.b' (Human OUT of daily) | I2, I6 |
| P1.b'' (Owner gate at contract-identity) | I2 |
| P1.c (Symbiosis-as-identity) | I1, I8 |
| P2 (Eternal Ingestion) | I6, I8 (envelope-only filter) |
| P2.a (Strong Inclusion) | I6 |
| P3 (Eternal Evolution) | I3, I4 |
| P4 (Eternal Iteration) | I3, I4 |
| P5 (Universal Interconnection) | I5, I7 (inter-substrate) |
| P6 (Eternal Causality) | I4 |
| P7 (Mortality) | I1 (state space + monotonicity) |
| P8 (Eternal Reproduction) | I7 |
| P9 (Integument) | I3 (no silent corruption), I8 |

### Strict-necessity check (drop X → at least one P loses coverage entirely)

- Drop I1 → P1.a, P1.c agent-discrim protection, P7 (state-space + monotonicity) all uncovered.
- Drop I2 → P1.b'/P1.b'' uncovered.
- Drop I3 → P3 state-vs-SSoT-now check lost, P9 silent-corruption protection lost.
- Drop I4 → P6 uncovered (sole enforcer).
- Drop I5 → P5 intra-substrate reachability uncovered.
- Drop I6 → P2.a uncovered (sole enforcer), P1 surface-discipline lost.
- Drop I7 → P8 uncovered (sole enforcer), inter-substrate P5 lost.
- Drop I8 → P9 uncovered (sole enforcer), P2 "no filter" un-enforced, P1.c single-operator un-enforced.

All eight invariants are necessary under the strict bar.

---

## §5. Biological metaphor — strict mycology lexicon (authoritative)

Myco uses **fungal-biology vocabulary strictly**. Lexicon source:
mycology only. General biology terms (decay, growth) and animal-
biology terms (organ, vein, breath) are NOT in the allowed lexicon —
even if they would be semantically apt. This rule is mechanical:
an agent cold-reading the substrate uses the names as a semantic
prior, and the prior must be *fungal* to avoid drift to other
metaphors.

**Lexicon scope (v0.4 clarification, per pressure-test A2)**: terms
whose primary use is *describing real fungal phenomena* are
admitted even if they share vocabulary with physics or mathematics.
Chemotropism, hydrotropism, phototropism are fungal phenomena in
the literature; **"gradient" and "threshold" used to describe
tropic phenomena are permitted** because the underlying biology
imports those terms. The test is "does mycology literature use this
term to describe THIS fungal phenomenon?" — not "is this term ever
used in physics?". Borderline cases (e.g. "field" — physics-loaded,
mycology uses sparingly): v0.4 prefers **"tropic gradient
configuration"** or simply **"gradient"** over "field", to reduce
the agent's physics-prior pull.

### §5.1 Subsystem family selection (instance list — reselectable for v0.9)

Per owner decision C5.1, the specific subsystem family roster is
NOT fixed at L0. v0.9 may choose any subsystem partition (or none —
a non-partitioned monolithic substrate would also satisfy L0)
as long as:

- Each named subsystem comes from the **strict mycology lexicon**.
- The set together satisfies the §4 eight invariants.
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
  for disambiguation from critic-name usage)
- pileus (the visible cap — interface to outside)
- chlamydospore (durable archive units)
- ... or any other fungal terms whose semantic prior fits the role

### §5.2 Dispatch form — Tropism + Sporocarp punctuation (resolves C5.3; refined per pressure-test)

Per owner decision C5.3 ("能不能抛弃动词这种形式？转向更高上限更加
高效且灵活的形式？"), the verb-form is **abandoned**. v0.9's chosen
dispatch form is **Tropism** (continuous chemotropic gradient
configuration) **+ Sporocarp punctuation** (substrate-initiated
discrete observables).

#### Operational definition (one paragraph)

Myco's dispatch is **tropism**: the substrate maintains a
continuously-evolving set of intrinsic **appetites** (hunger for
unmetabolized intake, drift toward unconnected nodes, decay-pressure
on stale tissue, federation-pull toward peer substrates, evolution-
tension where schema disagrees with content, skin-pressure for
boundary signals, etc.), each carrying a **tropic gradient** the
substrate updates on every metabolic cycle. The agent —
definitionally the active-operator-connection per P1.c — **inhabits
the gradient configuration** as both perturbation source and
gradient consumer. There are no commands, no verbs, no
request/response. Interaction is **continuous co-modification**:
the substrate exposes its current gradient configuration through
the agent's read-window; the agent emits **deltas** (raw content
of any shape — text, file references, decision fragments, schema-
edit intents, anything); the substrate's metabolism absorbs deltas
wherever its own gradients place them; gradients update; cycle.
When a gradient crosses a **fruiting trigger**, the substrate
**fruits a sporocarp** — a typed, content-addressed, causally-
stamped record that anchors the field to discrete observables for
governance (I2), validation (I3), federation (I7), and the causal
DAG (I4). **Appetite axes are first-class evolvable substrate
objects**; changing the *kind* of the gradient configuration is a
**contract-identity-level event** (I2). External agent-tooling
sub-techniques are subsumed by becoming appetite axes implemented
as **substrate-resident metabolism** — never as outbound RPC (the
appetite-locality rule) — so vector retrieval, internal LLM calls,
semantic federation are all gradient computations the substrate
runs on itself.

#### §5.2.1 Birth phase vs steady state (v0.4 — addresses pressure-test A1 + A4)

The pressure-test surfaced that tropism's strengths (emergent
thresholds, accumulated history, predictability through field-
inhabitation) are **steady-state** properties — they require
substantial substrate history to manifest. v0.9 genesis has none of
this. v0.4 explicitly distinguishes:

**Birth phase** (substrate's first ~100 sporocarps OR first 6
operating months — whichever later — measured by appetite-activity
diversity per §7 signal #3 reaching a stable distribution):

- **Hand-coded seed thresholds**: each appetite axis ships with an
  initial seed threshold + seed-gradient-update-rule from L1 hook
  B1 (no "emergence" yet — emergence has nothing to emerge from).
- **Predictability gap is a feature, not a bug** (per P1.c): the
  agent must learn this substrate's specific tropism — the gap
  between "agent's prediction of when sporocarp fruits" vs "when
  sporocarp actually fruits" IS the symbiosis being established.
  This is conceptually different from "agent learns the verb table"
  because verb tables are substrate-agnostic; tropism configurations
  are substrate-specific.
- **L1 must specify the seed table explicitly** — gesture at
  emergence is insufficient during birth phase.

**Steady state** (after birth phase):

- Thresholds emerge from substrate history per C6.4.
- Gradient update rules may themselves evolve per P3 (contract-
  identity-level changes, owner-gated).
- The agent's prediction accuracy on fruiting events becomes a
  Living Bets observability signal (added in §7 — signal #8 below).

Living Bets gains a new signal #8: **agent prediction-accuracy on
fruiting**. Low = symbiosis not yet established (expected during
birth); rising = healthy symbiosis maturing; persistent drop in
steady state = decoupling (the agent and substrate are diverging,
which is a P1.c degradation signal).

#### Why tropism beats each rival (ceiling × flexibility × efficiency)

| Rival | Why tropism beats it |
|---|---|
| **Verb dispatch (v0.8)** | Verbs presuppose a client-server seam; P1.c symbiosis is doctrine bolted on TOP of a generic protocol. Tropism makes symbiosis the protocol's load-bearing shape. Owner-prohibited anyway per C5.3. |
| **Continuous metabolic stream** | Closest rival. Tropism *is* a continuous metabolic stream PLUS the gradient-coupling that makes the agent definitionally a participant (P1.c). Bare metabolic-stream can degrade to "metabolism anyone can signal" = back-door client-server. |
| **Natural-language semantic dispatch** | Worst capture risk under P2.a: routing LLM call IS the dispatch surface → substrate becomes wrapper around LLM-router. Also: NL→handler-table secretly re-introduces verbs. |
| **Capability-based composition** | Capabilities are discrete grant transactions; asymmetric (substrate grants TO agent). Useful at L1 inside tropism (sporocarp typing carries capability metadata), not as dispatch primitive. |
| **Algebraic / typed-primitive operations** | Pure algebraic surface presumes purity and statelessness — but substrate IS state. Combinator vocabulary becomes frozen surface (same P3 hostility as verbs at the type level). |
| **Reactive stream / event-driven** | What tropism becomes if you strip gradient configuration. Reactive streams give pub/sub but no gradient — no answer to "what does the substrate want next?". Tropism's gradient IS substrate's expressed preference. |
| **Hybrid** | Owner-prohibited. Tropism's gradient/sporocarp duality is medium-vs-observable duality of ONE form, NOT two forms glued together. |
| **Coexistence ("verbs at birth → tropism later")** | Rejected per pressure-test A5 verdict: appetite-locality (I6) is foundational — retrofitting it onto verb dispatch leaves an RPC seam that v0.9.x must close = exactly the v0.8 contamination pattern §11 forbids. Owner C5.3 prohibits verbs as starting state, not just as endpoint. |

#### Why sporocarps are not verbs in disguise

- A verb is **agent-initiated** (agent calls verb → substrate executes).
- A sporocarp is **substrate-initiated** (substrate's gradient crosses fruiting trigger → substrate fruits → agent observes).

The arrow is reversed. The agent does not say "ingest this and produce
a digestion sporocarp"; the agent emits a delta into the gradient
configuration; if the digestion-appetite gradient has accumulated
enough pressure, the substrate fruits a digestion sporocarp on its
own metabolism.

#### L4 sketch (concrete example)

"Agent ingests a chat log, refines a decision record, surfaces the
result to a federated child substrate."

Under v0.8 verbs: 4 discrete agent-initiated transactions
(`myco eat`, `myco digest`, `myco sporulate`, `myco propagate`).

Under tropism: zero agent-initiated commands.

1. Agent **emits a delta** with the chat log + free-form intent
   fragment.
2. Substrate's `hunger` appetite gradient spikes; pulls metabolism;
   `intake` sporocarp fruits.
3. Substrate's `evolution-tension` appetite detects decision-shaped
   patterns disagreeing with schema; gradient pulls; `refinement`
   sporocarp fruits.
4. Substrate's `federation-pull` appetite for child-X sensitized by
   the refinement; gradient pulls; `federation` sporocarp fruits.
5. Agent observes 3 new sporocarps in its next read-window slice;
   may emit further deltas to correct/extend.

#### Honest trade-offs (per pressure-test verdict)

- **Initial implementation cost** is higher than verbs (~3-5× —
  v0.3 craft's own admission, validated by pressure-test A1).
- **Agent-side prior cost**: a v0.8-era agent knew `myco eat`; a
  v0.9 agent must learn gradient configuration / appetite /
  sporocarp.
- **Birth-phase predictability gap** (pressure-test A4): handled
  explicitly via §5.2.1 + Living Bets signal #8 — gap is named
  as a P1.c-symbiosis-establishment cost, not stealth-suppressed.
- **Kind-level field evolution friction**: tropism is P3-better for
  axis-count evolution, P3-equal for kind-level evolution.

**Recommended fallback if cost dominates**: bare continuous metabolic
stream (cheaper, lower P1.c support). All other §5.2 candidates
eliminated.

#### L1 design hooks (10 — see L1_OUTLINE.md for full breakdown)

L1 must specify: (1) appetite axis schema **including seed thresholds
for birth phase**, (2) initial appetite set, (3) sporocarp type tree,
(4) gradient exposure protocol, (5) delta intake surface, (6)
sporocarp governance gate, (7) continuity-recovery protocol, (8)
causal DAG embedding, (9) federation surface, (10) self-hosting
bootstrap state.

### §5.3 Intent model — Trajectory derivation (resolves C8.2; refined per pressure-test)

Per owner open C8.2, **intent is not a first-class substrate data
type**. Intent is **emergent from the causal DAG (I4) and
materialized as a derived "trajectory" view**.

#### Operational definition

> Intent, in a Myco substrate, is *the directed pattern of
> operations the operator-substrate pair has performed together
> over a recent window of the causal DAG, projected onto a current
> point in time*. It has no stored representation. It is computed
> by **traversing the DAG from a point, then clustering** operations
> (and sporocarps — §5.2) that share causal ancestors and converge
> on common descendants. The resulting subgraph IS the pair's
> current direction.

Mathematically:

> `intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))`
>
> where `cluster_C` is the substrate's currently-designated
> clustering algorithm. Intent is therefore a function of
> `(DAG, cluster_C)` — not DAG alone.

#### §5.3.1 Clusterer coupling (v0.4 — addresses pressure-test A2)

Different clustering algorithms produce different trajectories from
identical DAG histories. Therefore:

- The clustering algorithm choice (`cluster_C`) is a
  **substrate-resident object** with its own identity, not a free
  parameter.
- **Changing `cluster_C` is a contract-identity-level event** (I2-gated):
  it retroactively alters how past intents are read.
- I4's full-fidelity-recoverability guarantees the DAG is unchanged
  by clusterer evolution; what changes is the trajectory VIEW.
- Past trajectories from a previous epoch (per §5.3.2) are read
  through that epoch's clusterer, not the current one. (Epochs
  preserve clusterer-consistency within their span.)

#### §5.3.2 Schema-evolution epochs (v0.4 — addresses pressure-test A3)

When L1 mutates (vocabulary refactor, dispatch-form refinement,
clusterer swap, sporocarp-type-tree change), the historical DAG may
contain predicates that no longer exist in the new schema. v0.4
formalizes:

- **Each contract-identity-level mutation creates a new trajectory
  epoch.**
- Trajectory queries default to **within-epoch** (current epoch only).
- **Cross-epoch trajectory queries** require an explicit predicate-
  translation table maintained by the substrate — itself a contract-
  identity-level object.
- Cross-epoch queries may be **lossy** (some predicates don't
  translate); this is acknowledged, not concealed. Long-horizon
  intent (the rhizomorph attack from C8.2 craft) is recoverable
  within an epoch and partially recoverable across epochs.

#### §5.3.3 thread_id orthogonal grouping (v0.4 — addresses pressure-test A5)

The pressure-test surfaced a position not evaluated in the original
C8.2 craft: each operation/sporocarp carries an optional opaque
`thread_id` field (the agent declares "this delta belongs to long-
running thread T"). Threads are **not intent** — they are a
lightweight, mechanically-typed, opaque grouping primitive.

- **Cost**: 1 optional field per node.
- **Benefit**: cold-start works (`thread_id` set on first relevant
  operation); clusterer-independent (thread groupings survive
  clusterer evolution); schema-evolution-resilient (opaque-typed,
  not predicate-typed).
- **Not a teleological claim**: an agent's thread_id misplacement
  is self-punishing (loses its own grouping); no incentive to lie;
  mycoparasite attack from original craft doesn't transfer.
- **Relationship to trajectory**: thread_id is **orthogonal** to
  trajectory derivation. Trajectory clusters causally; threads
  group declaratively. Trajectory queries MAY use thread_id as a
  clustering hint (improving signal-poor cold-start), but
  trajectory is not defined by threads.

**L0 commitment**: thread_id is **OPTIONAL** at the substrate level.
L1 may choose to expose it or not. If exposed, L1 specifies its
type (opaque string, scoped UUID, etc.).

#### §5.3.4 Cold start (v0.4 — codified)

At genesis the DAG has one node (owner attestation per L1 F1).
For the first ~N operations, trajectory queries return ∅ or
near-empty subgraphs. **This is the correct degenerate behavior**,
not a hole:

- "The pair has no joint history yet" is a TRUE statement at t=0.
- Downstream consumers (I3 self-validation, immune system) read
  appetite gradients directly (§5.2) — they do NOT depend on
  trajectory being non-empty.
- The substrate's expressed direction during cold start is the
  agent's first few deltas themselves (read directly from the DAG,
  bypassing the clustering step).
- As DAG accumulates, trajectory becomes well-defined.

#### Why (b') beats (a) first-class typed and (c) NL metadata

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported → unverifiable; mycoparasite attack: agent writes intent=X but pursues Y. |
| **(c) NL metadata + vector embed** | Still self-reported; adds embedding cost per ingestion. |
| **(b') Trajectory query** | No self-report surface; intent is necessarily joint (P1.c); phantom-intents impossible. With v0.4 nuances (clusterer-pin / epoch / thread_id / cold-start codification), all 5 attack vectors are addressed. |

#### Honest cost

Position (b') is correct AND the substrate is simpler for it.
Cost is borne at the query layer (trajectory derivation is O(graph
traversal); intent is fossil-record honest, not teleologically
honest — see §14 glossary). v0.4 codifies the cold-start degenerate
case, the clusterer-coupling, and the epoch boundary explicitly.

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
  reconnects, the symbiosis resumes; the substrate's gradient
  configuration has continued evolving during the gap (metabolism
  without perturbation source), and the agent's next read-window
  slice shows the gradient state at reconnect.
- **Reflexes that the v0.8 R1/R2 captured** (hunger awareness,
  senescence cleanup, drift detection) are now **substrate-resident
  appetites** in the gradient configuration (§5.2). The substrate's
  metabolism propagates appetite-gradients on its own continuous
  cadence; the agent (continuously present) observes the gradient
  state and emits deltas that perturb it; the substrate's metabolism
  is therefore **co-driven** — substrate-internal in mechanism,
  pair-constituted in semantics. The v0.8 "substrate is lazy
  medium, immune is agent-invoked" rule (Fix-H25) is **superseded**
  by §6's continuous-agent reframing.

**Metabolic cycle** (defined for §4 invariants that reference it,
see §14 glossary): under tropism, the substrate's smallest discrete
metabolism event is one **gradient-update tick** — substrate's
gradient configuration advances by one step, may or may not fruit a
sporocarp, may or may not absorb a delta. I3 self-validation,
I5 reachability checks, I8 skin breach checks all run **per
gradient-update tick** (each cycle).

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

### The observatory (7 base signals + 1 composite, v0.4 — added signal #8)

Living Bets is measured as a **7-base-signal + 1-composite-derived**
observatory (v0.3 was 6+1; v0.4 adds signal #8 prediction-accuracy
on fruiting per pressure-test A4 verdict). Each signal's threshold
is **emergent in steady state** (after birth phase per §5.2.1),
**seeded** during birth phase from L1 baselines.

**Seven base signals:**

1. **Persistence budget** — total content in the substrate (size,
   node count, edge count, sporocarp count).
2. **Evolution rate** — governance changes (schema bumps, rule
   revisions, vocabulary refactors, appetite-axis additions) over
   time.
3. **Appetite-activity diversity** — variety of appetite axes
   firing / sporocarp types fruiting over a rolling window (under
   continuous-agent model, the window is time-based — e.g.
   rolling 24h, window itself emergent post-birth). v0.4 renamed
   from v0.3's "query diversity" (verb-era leak).
4. **Fork count** — federated child substrates spawned via P8 / I7.
   For substrates that never federate, fork count = 0 is a **weak
   signal** (not "not applicable" — per C6.3), indicating limited
   mycelial spread.
5. **Time trend per signal** — direction (up / flat / down) of
   each above signal.
6. **Read-window-relative position** — substrate-total-size /
   agent-context-window ratio. Threshold separating "strongly-in-
   bet-wins" from "bet-loses" regions is **emergent in steady
   state** (initial seed value from Fix-H11 baseline: ~100;
   refined by substrate observatory as correlation accumulates).
7. **Agent prediction-accuracy on fruiting** (v0.4 — addresses
   pressure-test A4). Measures the agent's predictive coupling
   to the substrate's tropism:
   - **Low at birth = expected** (symbiosis not yet established).
   - **Rising during birth phase = healthy maturation**.
   - **Persistent drop in steady state = decoupling** — the agent
     and substrate are diverging; P1.c symbiosis is degrading;
     this is an immune-grade signal.

**One composite signal:**

8. **Composite health score** — emergent weighted aggregation of
   signals 1-7. Weights are NOT pre-set; they emerge from the
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
operated **without engaging the tropism** (agent holds everything
in context, the gradient configuration is unread, deltas bypass
the appetite-gradient absorption layer), Myco must re-justify its
existence or retire.

Until that trigger fires, the nine root principles + the symbiosis
formulation stand.

**Not a principle.** Living Bets is a meta-commitment, not a tenth
principle. It holds P3, P4, P6 accountable to falsifiability.

---

## §8. Operational readiness for present-tier agents (v0.4 NEW)

The pressure-test surfaced a gap v0.3 did not name: **can v0.9
actually run on 2026-class LLMs?**

**v0.9 is designed for the agent-intelligence range from 2026-class
(Claude Opus 4.7 / GPT-5 / Gemini equivalents with ≈1M context
window) to ≥10× future agents.** This is L0 commitment.

Mechanical readiness requirements:

- **The tropism gradient configuration must compress to a digest
  size ≤ read-window budget.** L1 hook B4 (gradient exposure
  protocol) must specify how the digest is sized + structured for
  current LLM read patterns. A digest that requires 5M tokens to
  represent is non-operational on a 1M-context agent.
- **Sporocarp typing must be parseable from natural-language
  context.** Agents read sporocarps as part of the field digest;
  if sporocarp types require external schema knowledge to parse,
  the agent is locked out.
- **Delta intake surface accepts any shape the agent can emit.**
  Current LLMs emit natural language; future ones may emit
  structured types. L1 must support both.
- **The Living Bets signal #6 (read-window position)** is the
  monitoring metric: when ratio breaks down (substrate dwarfs
  read window, agent cannot meaningfully inhabit the gradient
  configuration), the substrate self-flags.

**Future-readiness**: the gradient/sporocarp form is invariant.
Substrate scales (more appetite axes, more sporocarps, more DAG
nodes) but L0 doesn't change. v0.9's design is L0-stable for
≥10× scale; what changes is L1's parameters (digest size, fruiting-
trigger emergence cadence, clusterer choice).

**Current-LLM caveats** (acknowledged, not engineered around):
- 2026-class agents may not natively understand "I inhabit a gradient
  configuration" — birth-phase predictability gap (§5.2.1) extends
  to "agent learns the entire tropism paradigm", not just one
  substrate's specifics. v0.9 birth-phase is a **double learning
  curve** during the first months.
- Owner-supervised birth (one of the few human-loop residue moments
  per P1.b'') reasonably extends to "owner watches first ~100
  sporocarps to confirm the substrate isn't producing
  pathological fruiting patterns under a confused agent."

---

## §9. Reading sequence for a new agent

1. This file (L0) — nine root principles + eight invariants + the wager + readiness model.
2. (Next) L1 — contract / tropism specification / sporocarp type tree / schema (SSoT) / governance classifier / hard rules. First L1 outline drafted at `docs/architecture/L1_OUTLINE.md`; formal L1 awaits owner approval of this L0 v0.4.
3. (Future) L2 doctrine — per-subsystem-family doctrine.
4. (Future) L3 implementation — code organization.
5. (Future) L4 substrate — the live instance.

The v0.9 substrate is being designed top-down: L0 (this document,
owner-pending), then L1, then L2, then L3, then code.

## §10. Changes to this page

L0 is the identity layer. Any change requires:

1. A craft-style proposal document arguing the revision.
2. Explicit owner approval recorded in the proposal.
3. A contract-identity-level bump (per P1.b'' / I2).
4. A cascade review of every lower-layer doc for implicit
   dependencies.

L0 revision is never implementation-driven and never routine.

## §11. Proto archaeology

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

## §12. The dead-embryo concession + maximal origin discrimination

Per owner decision C1.1 + C7.3:

- v0.4 → v0.8.7 are **proto-Myco / dead embryo / failed gestation
  attempts**. v0.9 is **Myco's first true birth**.
- Every v0.9 design step (L1 contract, L2 doctrine, L3
  implementation, L4 substrate) must directly trace its decisions
  back to **one or more of P1-P9** and **one or more of the eight
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

## §13. Privacy and access model

Per owner decision C8.3: **Myco has no internal privacy / access
model**. The substrate is wholly accessible to its operator-agent.
Sub-substrate access boundaries are not at L0 level. (P1's "sole
operator" implies the operator has full access; multi-operator
scenarios are handled via P8 reproduction into per-operator child
substrates, not via access control within one substrate.)

The skin (P9 / I8) is the boundary — between substrate and
*environment*, not between operators *within* the substrate.

## §14. Open questions explicitly carried forward (v0.4 — three resolved + nuanced)

The three v0.2 open questions are resolved (results integrated
above) and refined in v0.4 per pressure-test:

| ID | v0.4 status | Notes |
|---|---|---|
| C4.4 | **Resolved (8 invariants)** | v0.3 had 9; v0.4 merges I7 Mortality into I1 Lifecycle per pressure-test A4 verdict. |
| C5.3 | **Resolved (Tropism + Sporocarp)** | v0.3 stands; v0.4 adds birth-phase nuance (§5.2.1), lexicon carve-out (§5), Living Bets signal #7. |
| C8.2 | **Resolved (b' Trajectory)** | v0.3 stands; v0.4 codifies clusterer-coupling (§5.3.1), epochs (§5.3.2), thread_id (§5.3.3), cold-start (§5.3.4). |

**Remaining open at L0** (intentionally — these are L1 design
decisions, not L0 commitments):

- The specific **classifier function** for I2 (which file/field touches
  trigger contract-identity-level classification).
- The specific **SSoT format** for I3 (v0.8 used `_canon.yaml`; v0.9
  chooses fresh per C7.3 max-discrimination).
- The specific **initial appetite set + seed thresholds** (§5.2.1
  + §5.2 L1 hook 1/2).
- The specific **sporocarp type tree** (§5.2 L1 hook 3).
- The specific **clustering algorithm** for trajectory (§5.3.1 +
  L1 H1-H3).
- The specific **epoch translation table format** (§5.3.2 + L1 H6).

These are L1 territory and will be resolved during L1 drafting.

---

## §15. Glossary (v0.9 precise terms)

| Term | Definition |
|---|---|
| **Myco** | The taxonomic class (digital symbiotic organism). Used as a noun for the class, not a specific instance. |
| **A Myco substrate** | A specific instance of the class — one concrete substrate with its own ID, lifecycle, DAG, gradient configuration. "The substrate" within this document refers to one such instance unless context says otherwise. |
| **Active operator-connection** | The currently-attached operator session (MCP-session-equivalent active connection). The thing that, jointly with the substrate, constitutes the agent identity (P1.c). |
| **Symbiotic operation** | Activity by the active operator-connection that reads or writes substrate state. Under tropism (§5.2), this is delta emission + gradient consumption. |
| **Contract-identity-level boundary** | The threshold above which a change to substrate doctrine alters Myco's identity (vs merely accumulating content). Defined and enforced by L1; covers any modification to L0 itself, to L1 protocol, and to identity-level fields of the substrate's own schema. |
| **Continuous online agent** | The default operating mode: the agent is presumed always-attached; disconnects are transient and recovered, not formalized as sessions. |
| **Metabolic cycle** | The substrate's smallest discrete metabolism event under tropism. Each cycle: gradient configuration advances by one tick, deltas may be absorbed, sporocarp may fruit. I3/I5/I8 invariant checks run once per cycle. Cycle cadence is L1-defined (likely tied to the substrate's compute budget + the agent's read-rate). |
| **Identity record** | A single immutable substrate-ID established at genesis. L1 specifies the format (UUID / opaque token / etc.). Agent identity at any moment is computed as the pair (substrate-ID, currently-attached-operator-token) — NOT stored. |
| **Spore-schema** | The seed-state passed from parent substrate to child substrate during P8 reproduction. Contains the minimum structural form (initial appetite axes, sporocarp type tree, SSoT designation) for the child to begin its own symbiosis. Does NOT include the parent's DAG. |
| **Skin / boundary** | The substrate's interface to the rest of reality: intake surface (P2 universality applies), output surface (federation, summaries), and identity-protection (P9 / I8). |
| **Tropism** | Myco v0.9's dispatch form (§5.2): a continuously-evolving gradient configuration of substrate appetites + agent perturbations. Replaces v0.8's verb table. |
| **Tropic gradient configuration** | The substrate's current state across all appetite axes — a snapshot of all appetite gradient values at a given metabolic cycle. (v0.4 prefers this over "field" to reduce physics-prior leak; "field" still appears in shorter form where context is clear.) |
| **Appetite (axis)** | One dimension of the gradient configuration — a substrate-internal gradient that pulls metabolism toward a particular activity (hunger / drift / decay / federation-pull / evolution-tension / skin-pressure / …). First-class evolvable substrate object. |
| **Fruiting trigger** | The emergent threshold at which an appetite's gradient causes a sporocarp to fruit. Seeded in birth phase from L1 baselines (§5.2.1); emerges in steady state from substrate history. (v0.4 prefers this over "threshold" to reduce physics-prior leak.) |
| **Delta** | An agent-emitted perturbation into the gradient configuration — raw content of any shape (text, file reference, decision fragment, schema-edit intent, …). |
| **Sporocarp** | A substrate-initiated discrete observable: when an appetite's gradient crosses its fruiting trigger, the substrate "fruits" a typed, content-addressed, causally-stamped record. Sporocarps are DAG nodes (I4), governance targets (I2), validation targets (I3). NOT verbs (substrate-initiated, not agent-initiated). |
| **Trajectory** | The substrate's derived view of the pair's current intent — a query, not a stored type. Computed by traversing the causal DAG from a point and clustering causally-related operations/sporocarps using the substrate's designated clustering algorithm `cluster_C`. Function of `(DAG, cluster_C)` jointly. Resolves C8.2 (§5.3). |
| **thread_id** | Optional opaque grouping field on operations/sporocarps. Lightweight, mechanically-typed, non-teleological. Orthogonal to trajectory; NOT intent (§5.3.3). |
| **Causal DAG** | Append-only graph of substrate state-derivations, full-fidelity (no lossy compression). I4 enforcer. P6 substrate. |
| **Recoverability budget** | The L1-specified backup/redundancy policy that defines when "destroyed" actually means destroyed (vs recoverable from backup). Below the budget = recoverable = the substrate's recovery operation restores from backup. Beyond the budget = mortality. |
| **Fossil-record intent** | The substrate's view of intent as "the directed pattern of past operations" — empirical, recoverable from DAG. Distinct from teleological intent ("what the agent was aiming at"); v0.4 §5.3 commits to fossil-record honesty over teleological honesty. |
| **Rhizomorph** | (1) Fungal-biology term: a specialized cord-like structure of aggregated hyphae enabling long-distance nutrient transport — candidate v0.9 subsystem name for federation conduits (§5.1). (2) Name of one of the 5 craft/pressure-test critics used in §4 / §5.2 / §5.3 derivation (gap-finding angle). Disambiguation: context tells you which. |
| **Birth phase** | The substrate's first ~100 sporocarps OR first 6 operating months, whichever is later. Hand-coded seed thresholds + seed-gradient-update-rules apply; emergent thresholds activate in steady state. See §5.2.1. |
| **Steady state** | The substrate's post-birth operating regime; emergent thresholds activate, clusterer evolution becomes possible (I2-gated), Living Bets observatory signals reach stable distributions. See §5.2.1. |
| **Epoch** | A span of substrate operation between contract-identity-level mutations. Trajectory queries default to within-epoch; cross-epoch queries are L1-supported via predicate-translation tables, may be lossy. See §5.3.2. |
