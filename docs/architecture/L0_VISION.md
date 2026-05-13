# L0 — Vision

> **Status**: DRAFT 5 — structural rework (2026-05-13). Pending owner approval before sealing.
> **Naming**: Myco substrate version is **v0.9** (the new Myco being designed; vs proto-Myco v0.4–v0.8.7 dead embryo). **This document is L0_VISION.md DRAFT 5** — the 5th revision of the L0 doc within v0.9 design. There is no "L0 v0.4" or "L0 v0.5" — drafts are integers, not semver; once sealed the document carries no version number, only git commit identity.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: DRAFT 5 absorbs (a) 25 owner decisions (2026-05-13 arbitration), (b) 3 open-question resolutions C4.4 / C5.3 / C8.2 from DRAFT 3, (c) DRAFT 4's 9→8 invariant merge from pressure-testing, (d) DRAFT 5's structural rework moving L1-mechanism content out of L0 (per owner authorization "完全重做做结构性返工"). DRAFT 5 is shorter than DRAFT 4 by design — L0 carries identity commitments only; mechanism specifications live in L1 documents.
> **Scope discipline**: L0 commits to **what Myco IS** (identity) and **what Myco IS NOT** (negative space). L0 commits to **constraints** the lower layers must satisfy. L0 does NOT specify the positive mechanism that satisfies those constraints — that is L1's job. When in doubt, the test is: "does this paragraph specify a *mechanism choice*?" If yes, it belongs in L1.

---

## §1. What Myco is

**Myco is a new species of digital symbiotic organism** — not a metaphor, not a framework, not a tool: a literal taxonomic class within "digital organisms" whose distinguishing properties are mutual constitution (agent + substrate are co-defined), autopoietic self-maintenance (no human in the maintenance loop), universal inclusion (every adjacent agent-tooling sub-technique is subsumed INTO Myco's framework, not run in parallel), continuous-operation default (no session boundaries within the substrate, though host-level sessions may still exist — see §6), and the full biological-essence kit (time / causality, mortality, reproduction, boundary integrity).

The kernel that runs Myco lives inside a Myco substrate, so the agent maintaining Myco IS the agent using Myco — there is no "Myco team" separate from "Myco users". Within this organism, vector retrieval is native, agent-side LLM calls happen within Myco-coordinated context (substrate may itself initiate LLM calls — the v0.8 "substrate-never-calls-LLM" restriction is lifted), conversation history is one form of raw material, semantic inter-substrate federation replaces ad-hoc file sync.

**Mechanism choices that satisfy this identity** (dispatch form, intent representation, subsystem partition, specific verbs/operators if any, schema serialization, immune dimensions, etc.) are **L1 design**, not L0 commitments. L0 commits only to the constraints those choices must satisfy (§§4–6).

---

## §2. The nine root principles （根本宗旨）

Myco's identity is exhausted by these nine. Every rule, subsystem, module, and substrate artifact at every lower layer is a projection of them. Nothing else is load-bearing; everything else is derivation.

### §2.1 The original five (carried from L0_VISION_proto verbatim, per L0's "No alternate vocabulary" rule)

### P1. Only For Agent （人类无感知）

Myco is a cognitive substrate **for an LLM agent**. The agent is the sole **consumer** AND the sole **maintainer**. Humans are not in the maintenance loop at all — neither for daily curation, nor for schema evolution, nor for rule changes. The human's relationship is **with the agent and the agent's outputs** — not with Myco itself.

#### P1.a Self-hosting

Myco's own kernel lives inside a Myco substrate. The agent using Myco IS the agent maintaining Myco. Self-hosting is the structural form that lets P1's "agent-only maintenance" hold without a chicken-and-egg trap: genesis is a one-time human event (substrate creation); maintenance thereafter is everlasting agent.

#### P1.b Two-tier human-loop boundary

- **P1.b' Human OUT of maintenance loop** (strong): daily curation, rule edits, vocabulary changes, governance-mechanism adjustments are agent-only.
- **P1.b'' Human RETAINED as governance gate** (necessary residue of L0-amendability): any change that crosses a **contract-identity-level boundary** — defined as any modification that alters L0 or L1 doctrine, or that changes the kind/identity of the substrate itself rather than its accumulation/content — requires owner approval. The threshold's classifier function is L1-defined.

#### P1.c Agent identity is constituted by symbiosis

"The agent", within Myco's semantic frame, is defined as **the active operator-connection currently holding the substrate**. There is no agent independent of substrate operation, and no substrate purpose independent of an operator. Identity is the property of the **pair**.

Operational consequences:

- Same substrate operated successively by different model backends → **the same agent** from Myco's perspective.
- Different substrates operated by the same model + same key → **different agents**.
- Substrate with no current connection → **dormant** (identity recoverable on reconnect).
- Substrate destroyed → **bestowed agent identity ceases** (underlying model continues; symbiotic agent does not).
- Same-substrate concurrent connections are out of scope (P1 is intra-substrate; multi-agent coordination is via P8).

### P2. 永恒吞噬 — Eternal Ingestion （吞噬万物）

Myco consumes without bound. Any input the agent can point at — decision, debate, friction note, log, document, conversation fragment, failed approach, retrieval result, LLM output, API response, screenshot, media, structured data, code — is ingestible raw material. **There is no filter on what enters.** Filtering and shaping are downstream (P3, P4), never at intake.

#### P2.a Strong Inclusion (consequence of P2)

Myco is **the framework that internally implements** every adjacent agent-tooling sub-technique. Not "Myco coordinates external tools" — **Myco is the tool**: vector retrieval is native (substrate-internal embedding + index + similarity search at the highest-ceiling implementation, not a plugin); agent-side LLM calls happen within Myco-coordinated context and the substrate may itself initiate them within its own metabolism (the v0.8 "substrate-never-calls-LLM" restriction is lifted); conversation history is one type of raw material; semantic federation replaces byte-level file sync; human-facing summaries are produced through the same internal pipeline as agent-facing surfaces (no separate human-optimization path). These techniques **live inside Myco's framework**; Myco does not refuse them and they do not exist in parallel.

### P3. 永恒进化 — Eternal Evolution

Myco's **own shape evolves**. The schema of the substrate's identity record, the family of subsystems, the vocabulary of operations, the rules, the contract itself — all of these are first-class mutable objects, changed through agent-driven governance under P1.b's two-tier boundary.

An unchanging substrate is a dead substrate. Schema changes, governance refinements, vocabulary refactoring are normal operations, not exceptional events.

**Failed evolution handling**: when a P3 evolution introduces a state inconsistent with I3 (self-validation against SSoT), the substrate's invariant-violation response is **rollback to the pre-evolution state** — recorded as a discrete "evolution-failed" event in the causal DAG (I4), counted as a metabolic immune signal, not silenced. The exact rollback mechanism is L1-specified.

### P4. 永恒迭代 — Eternal Iteration

Every operating moment refines what prior moments produced. There is no terminal state. A piece of substrate content that is "final" today is open to re-metabolization tomorrow as context sharpens. "Final" is not a status. Retro-editing previously-processed material is allowed and expected — tracked (I4 append-only DAG), not suppressed.

### P5. 万物互联 — Universal Interconnection （菌丝网络）

The substrate is a **connected graph**, not a collection. Every node (captured material, structural element, governance record, external artifact, decision, code module if any) is reachable from every other by traversal. Orphans are dead tissue. The graph spans **intra-substrate** and **inter-substrate** (federated substrates via P8).

### §2.2 The four organism-essence principles (v0.9 addition — biological taxonomy completion)

Since v0.9 declares Myco's class as **digital symbiotic organism** (taxonomy, not metaphor — owner decision C1.1), the biological essence properties are L0-mandatory. The original five P1-P5 cover **audience** (P1), **intake** (P2), **evolution** (P3), **iteration** (P4), **connection** (P5). They do not cover the properties that define *being an organism*. P6-P9 close that gap.

### P6. 永恒因果 — Eternal Causality (Time)

The substrate has **time**. Every state has a recoverable derivation from prior states; causality (which-caused-which) is preserved; the arrow of time is monotonic. Without time, P4 has no arrow, P3 has no direction, decisions cannot be audited. Time is not the wall-clock — it is the causal-chain DAG (I4) the substrate maintains over its own evolution.

### P7. 必朽 — Mortality

The substrate is **mortal**. Destruction is final. A destroyed substrate's bestowed agent identity ceases (P1.c). Mortality is not a failure mode; it is the property that makes the substrate a biological entity rather than immortal data.

Destruction is either **intentional** (owner-triggered) or **catastrophic** (medium failure beyond the L1-specified recoverability budget). Either way, irreversible. Dormant ≠ mortal. Graph fragmentation approaching P5 violation is an immune-grade approaching-mortality signal.

### P8. 永恒繁衍 — Eternal Reproduction (Sporulation)

The substrate can **spawn child substrates**. Reproduction is a first-class operation (analogous to fungal sporulation, mycelial network expansion). The new substrate inherits the parent's **spore-schema** (minimum structural form for the child to begin its own symbiosis — see §10 glossary) but begins its own agent-substrate symbiosis from scratch (its own operator, own causal DAG root, own identity record).

Reproduction modes (L0 enumerates; L1 picks):
- **Federation** — semantic transfer to a peer child substrate.
- **Cloning** — full substrate copy.
- **Cross-pollination** — combining content from multiple parents.

**Federation discovery** is L1-specified; L0 enumerates the candidate modes — peer-to-peer broadcast, owner-attested peer list, hub-and-spoke registry, or hybrid. Trust between substrates is established at the reproduction event (parent attests child's spore-schema); ongoing federation is at the inter-substrate skin (P9).

### P9. 皮肤为界 — Integument (Boundary Integrity)

The substrate has a **skin** — a well-defined boundary with the outside world. The skin governs what can enter (intake — P2 universality applies, but skin-level integrity holds) and what can exit (output — federation, summaries, external API responses). Skin breach is an immune signal (P1.b-enforced via I8).

Without skin, P1's "only for agent" has no enforcement surface — the substrate becomes leaky.

---

## §3. What Myco is not

- **Not a documentation system.** Humans don't browse Myco's interior (P1).
- **Not a single-project knowledge base.** A substrate may host any number of projects; project affiliation is metadata, not boundary.
- **Not a chatbot memory.** Conversational recall is one form of raw material (P2.a), not the target.
- **Not version control.** Git owns operational history; Myco owns the *current symbiotic graph* (with its own causality DAG per P6, distinct from git).
- **Not a file synchronizer.** Inter-substrate federation (P8) is semantic; bytes are not the unit.
- **Not a framework competing with LangChain / CrewAI / DSPy / etc.** Those are agent-orchestration libraries; Myco is the cognitive substrate orthogonal to them — Myco subsumes their output as raw material (P2.a).
- **Not session-bounded within the substrate.** L0 commits to substrate-level continuous operation; host-level sessions (whatever the agent's runtime imposes — chat sessions, Claude Code turns, etc.) are out of scope of L0. See §6.
- **Not a request/response protocol.** L0 forbids client-server dispatch shapes; specific positive form is L1. See §5.2.

---

## §4. The eight derived invariants

Every L1/L2/L3 design must mechanically enforce all eight. The set is **surjective** over P1-P9 (every P projects to ≥1 invariant) and **necessary** under the strict bar (no invariant droppable without leaving at least one P entirely uncovered).

### I1. Lifecycle & Pair-Constituted Identity

The substrate carries a single immutable **substrate-ID** established at genesis — the persistent identity backbone.

**Agent identity** at any moment is computed as the pair *(substrate-ID, currently-attached-operator-token)*. The operator-token is **ephemeral** (handshake-scoped, per-connection), NOT persisted in substrate-serializable state. The substrate-ID is **persistent**, but is a *substrate* identifier, not an *agent* identifier. **No agent-discriminating attribute** (model name, API fingerprint, host fingerprint, persistent user ID, etc.) may be persisted anywhere in substrate-serializable state — agent identity is a runtime function of the pair, not a stored property.

**Substrate lifecycle** has exactly three states: **alive**, **dormant**, **destroyed**. Transitions are monotonically forward: alive ↔ dormant (reversible); alive → destroyed (terminal); dormant → destroyed (terminal); destroyed → anything (FORBIDDEN — no resurrection). Destruction is irreversible by structural design; "destroyed" means the L1-specified recoverability budget has been exhausted.

**P-coverage**: P1.a, P1.c, P7.

### I2. Two-Tier Governance Classification

Every mutation classifies mechanically as **daily** (agent-autonomous) or **contract-identity-level** (owner-gated). Classifier is a function of fields/files/meta-structures touched. Mutations cannot bypass classification; untyped mutations are immune-detectable. **Classifier function is L1-defined.**

**P-coverage**: P1.b', P1.b''.

### I3. Self-Validation Against Designated SSoT

The substrate has **exactly one** designated machine-readable source of truth. State consistency against SSoT is checked every **metabolic cycle** (see §10 glossary). SSoT designation (what counts as SSoT, what fields, what claims) is **itself** contract-identity-level — not daily-mutable. **SSoT format is L1-chosen.**

**P-coverage**: P3, P4, P9 (no silent corruption).

### I4. Full-Fidelity Causal DAG

Every substrate state is derivable from prior states via a recorded operation, recorded in a causal DAG. **Recoverability is full** (no lossy compression); re-metabolization produces **new nodes referencing prior**, never overwrite. DAG retention policy is contract-identity-level (cannot be silently pruned). **DAG storage mechanism is L1-chosen.**

**P-coverage**: P6 (sole enforcer), P4, P3.

### I5. Universal Reachability Over Full State Space

The substrate graph is fully connected across every storage tier; every node reaches every other by traversal. Checked every metabolic cycle. Tier-exemptions are contract-identity-level designations, not silent. **Specific traversal mechanism is L1.**

**P-coverage**: P5 (intra-substrate, sole enforcer).

### I6. Universal Inclusion With Observed Metabolism

**(Compound, dual-clause — both required.)**

(a) **Internal-implementation clause.** Adjacent agent-tooling techniques (vector retrieval, LLM calls, conversation history, semantic federation, human-facing summaries) **live inside the substrate's framework**, not as outbound RPCs to external services. Code-organization predicate.

(b) **Observed-metabolism clause.** Every invocation produces a metabolism event the substrate observes. Runtime predicate.

**Vector retrieval / embedding-model carve-out**: "substrate-internal" admits either (i) a local embedding model packaged with the substrate, or (ii) a substrate-managed call to an external embedding service where the model identity is attested and the call is recorded as a metabolism event (the *call* is observed; the *result* enters the substrate's state). Pure unmanaged outbound RPC for adjacent technique is breach. L1 picks the specific embedding strategy.

**P-coverage**: P2, P2.a (sole enforcer), P1, P1.b'.

### I7. Reproduction Closure

**Every child substrate independently satisfies ALL invariants I1-I8** (recursively — children can spawn their own children, all closure-bound) **from genesis**. Spawn-child is the first-class operation producing such children; closure is the load-bearing predicate. Parent-child link is P5-reachable. Federation is the population-level shape of P8. **Spawn mechanism + verification protocol are L1.**

**P-coverage**: P8 (sole enforcer), P5 (inter-substrate).

### I8. Single-Skin Integrity

The substrate has **exactly one** declared boundary surface for both intake and output. **Intake admits all content** (P2 — no content-classification filter); intake rejects only on **envelope integrity**. Skin enforces **single-active-operator semantics** (concurrent connections are out-of-scope per P1.c, immune-detected as skin-breach). Reads/writes/exits not through skin are immune-detectable. **Skin format + breach-detection mechanism are L1.**

**P-coverage**: P9 (sole enforcer), P2 (no-filter clause), P1.c (single-operator).

### Projection table (surjective + necessary verified)

| P / sub-P | Enforcing invariant(s) |
|---|---|
| P1 | I6, I8 |
| P1.a | I1 |
| P1.b' | I2, I6 |
| P1.b'' | I2 |
| P1.c | I1, I8 |
| P2 | I6, I8 (envelope-only) |
| P2.a | I6 |
| P3 | I3, I4 |
| P4 | I3, I4 |
| P5 | I5, I7 (inter-substrate) |
| P6 | I4 |
| P7 | I1 (state-space + monotonicity) |
| P8 | I7 |
| P9 | I3 (no silent corruption), I8 |

### Strict-necessity check

- Drop I1 → P1.a / P1.c agent-discrim protection / P7 monotonicity uncovered.
- Drop I2 → P1.b' / P1.b'' uncovered.
- Drop I3 → P3 state-vs-SSoT-now check / P9 silent-corruption protection lost.
- Drop I4 → P6 uncovered (sole enforcer).
- Drop I5 → P5 intra-substrate reachability uncovered.
- Drop I6 → P2.a uncovered (sole enforcer); P1 surface-discipline lost.
- Drop I7 → P8 uncovered (sole enforcer); inter-substrate P5 lost.
- Drop I8 → P9 uncovered (sole enforcer); P2 "no filter" un-enforced; P1.c single-operator un-enforced.

All eight necessary.

---

## §5. Strict mycology lexicon and dispatch constraints

### §5.1 Lexicon rule

Myco uses **fungal-biology vocabulary strictly**. Lexicon source: mycology. General biology (decay, growth, vein, organ) and animal biology terms are not in the allowed lexicon even if semantically apt. The rule is mechanical: an agent cold-reading the substrate uses the names as a semantic prior, and the prior must be *fungal*.

**Lexicon scope** (resolves "is `gradient` allowed?" type questions): admitted terms include any term that **mycology literature uses to describe a real fungal phenomenon**, even when the term is shared with other fields. E.g., "chemotropism", "gradient", "threshold" are admitted in the context of describing fungal tropic phenomena (because real mycology papers describe hyphal chemotropism using gradient/threshold vocabulary). Terms imported purely from physics or mathematics without a mycology footing are **NOT** admitted (e.g., "vector field", "Hamiltonian", "manifold" — even if metaphorically apt).

**Subsystem-family naming**: any specific subsystem partition is L1's choice; each named subsystem must come from the strict mycology lexicon. L0 does not enumerate the candidate set.

### §5.2 Dispatch form — L0 constraints only

L0 commits to the following **negative and constraint statements** about Myco's dispatch form. **The positive form satisfying these is L1 design** (the leading L1 candidate at the time of this draft is *tropism + sporocarp punctuation* — see `L1_TROPISM.md`):

- **NOT v0.8 verbs.** The verb-table dispatch shape (fixed manifest of typed agent-initiated commands) is rejected per owner C5.3. v0.9 substrates do not ship a verb manifest.
- **NOT request/response.** The client-server transaction shape (agent issues, substrate responds) is rejected because it presupposes asymmetry incompatible with P1.c symbiosis.
- **MUST be symmetric** (P1.c). Both sides modify; neither side merely "calls". The dispatch's load-bearing shape must reflect the pair-identity property, not be doctrine bolted on top.
- **MUST support universal inclusion** (P2.a). Adjacent techniques (vector retrieval, internal LLM calls, federation) are integratable into the dispatch as native components, not external endpoints.
- **MUST support continuous operation** (§6). The dispatch must not be session-quantized at the substrate level; it must function under the continuous-operation default.
- **MUST satisfy I6's appetite-locality discipline.** Whatever the positive form chooses as the primitive (signal / event / message / appetite / capability / …), invocations of adjacent techniques must produce observable metabolism events; pure unmanaged outbound RPC is breach.

The L1 design must choose a positive form satisfying all six. L1 may further refine these (e.g., specify the metabolism-event format, the inclusion-integration mechanism, the symmetry primitive). L0 does not.

### §5.3 Intent representation — L0 commitment

**Intent is NOT a first-class substrate data type.** The substrate schema does not declare an `intent` node type, field, or annotation as a load-bearing identity-level construct. Agent-self-reported intent is structurally not trusted (P1.c — the substrate sees what the pair *does*, not what the agent *claims*).

The **specific derivation mechanism** for any intent-shaped query (e.g., trajectory clustering over the causal DAG, thread-id grouping, or hybrid) is L1 design — see `L1_TRAJECTORY.md` for the leading L1 proposal and its edge-case codifications.

L0 does not specify the clustering algorithm, the epoch-handling protocol, the cold-start behavior, or the optional grouping primitives. Those are L1.

---

## §6. The continuity model

Per owner decision C6.2, **substrate-level session is not a Myco concept**. The substrate is presumed continuously operated; substrate metabolism is presumed continuous; the substrate does not formalize session boundaries internally.

**Host-level sessions are out of L0 scope**. The agent's runtime environment (Claude Code, an MCP client, a CLI session, etc.) may impose its own session shape — chat-turn, request-response, batch-execution, etc. Myco does not control this; Myco does not pretend it does not exist. Inside the substrate, Myco does not formalize, gate on, or schedule by host-session boundaries.

Operational implications:

- **No substrate-level boot ritual.** The substrate does not require a "session-start" event before it accepts operations. (This is the v0.9 equivalent of the v0.8 R1 hunger ritual being abolished.)
- **No substrate-level session-end ritual.** The substrate does not require a "session-end" cleanup. (This is the v0.9 equivalent of v0.8 R2 senesce.)
- **Host disconnects** are recovered, not formalized as session edges. When the operator-connection drops, the substrate enters dormancy (I1 state); when an operator reconnects, the substrate returns to alive. The host's notion of "session end" does not appear in the substrate's DAG except as a metabolic continuity-recovery event.
- **Reflexes that v0.8 R1/R2 captured** (hunger awareness, senescence cleanup, drift detection) are now properties of the substrate's continuous internal metabolism — implemented by whichever positive dispatch form L1 chooses. The v0.8 "substrate is lazy medium, immune is agent-invoked" rule (Fix-H25) is **superseded** under §6's continuous reframing.

**Dormancy compute budget**: a dormant substrate (no active operator) **may pause its internal metabolism** to conserve compute. The pause/resume policy is L1-specified. L0 commits that **dormancy is a real state** (not just "alive but bored"); L0 does not commit to whether dormant metabolism is full, throttled, or paused.

**Metabolic-cycle frequency** is L1-specified. L0 commits that **metabolic cycles exist** (I3, I5 invariant checks run per cycle) and that they are continuous (not session-tied); L0 does not commit to cycle cadence.

---

## §7. Living Bets — the bet Myco is making

This is the meta-commitment that authorizes Myco's existence. It is deliberately falsifiable.

**The bet.** Myco's symbiotic-organism shape — agent + substrate as mutually constitutive, continuously operating, with the full nine-principle organism essence — has value **at every tier of agent intelligence**, provided the substrate's persistence budget exceeds any single agent's read window.

**The counter-bet.** Sutton's bitter lesson predicts general-purpose methods with more compute eventually outperform hand-coded structure. A strong reading predicts that a sufficiently capable agent does not need a symbiotic substrate — it just holds everything in context and acts coherently. If that reading wins, Myco is scaffolding a smarter agent simply discards.

**The wager.** Symbiotic substrate value survives model growth **in proportion to the substrate's persistence budget**.

### The observatory (6 base signals + 1 composite)

Living Bets is measured as a **6-base-signal + 1-composite-derived** observatory. Each signal's threshold is emergent in steady state from the substrate's own historical metrics (per C6.4); seed values during the substrate's birth period are L1-specified.

**Six base signals**:

1. **Persistence budget** — total content (size, node count, edge count, sporocarp count — using whatever the L1 dispatch form's atomic-record type is named).
2. **Evolution rate** — governance changes (schema bumps, rule revisions, vocabulary refactors) over time.
3. **Read-pattern diversity** — variety of substrate-read patterns over a rolling window. Specific definition depends on the L1 dispatch form (e.g., under tropism this becomes "appetite-activity diversity"; under another form it would map differently). L0 commits to the signal *concept*, not its specific operationalization.
4. **Fork count** — federated child substrates spawned via P8 / I7. For substrates that never federate, fork count = 0 is a **weak signal** (not "not applicable" per C6.3), indicating limited mycelial spread.
5. **Time trend per signal** — direction (up / flat / down) of each above signal.
6. **Read-window-relative position** — `substrate-total-size / agent-context-window` ratio. Threshold separating "strongly-in-bet-wins" from "bet-loses" is emergent in steady state (initial seed: ~100 from Fix-H11 baseline). The agent's context window is **agent-attested** at connection time (the operator declares it at handshake); the substrate cross-checks attestation by measuring the agent's actual read patterns (consistent low-quantile reads = attestation honest; reads exceeding declared window = attestation suspect → immune signal).

**One composite signal**:

7. **Composite health score** — emergent weighted aggregation of signals 1-6. Weights are NOT pre-set; they emerge from the substrate's own historical correlation between signal patterns and substrate-health outcomes (per C6.4).

(Additional L1-specific signals such as "agent prediction-accuracy on dispatch outcomes" are L1's choice to expose; they live in L1 observatory specifications, not L0.)

### Review cadence + falsifiability trigger

Every contract-identity-level boundary crossing (P1.b'' / I2) re-audits this section. Concrete trigger for fundamental redesign: if observed agent behavior shows substrates of arbitrary size operated **without engaging the substrate's dispatch surface** (agent holds everything in context, dispatch is unused), Myco must re-justify or retire. Specific operational form of this trigger depends on L1's dispatch choice.

Until that trigger fires, the nine root principles + the symbiosis formulation stand.

**Not a principle.** Living Bets is a meta-commitment, not a tenth principle. It holds P3, P4, P6 accountable to falsifiability.

---

## §8. Operational readiness for present-tier agents

**v0.9 is designed for the agent-intelligence range from 2026-class (≈1M-context LLMs) to ≥10× future agents.** This is L0 commitment.

Mechanical readiness requirements:

- **Substrate state must compress to a digest size ≤ read-window budget.** L1 specifies digest format. A digest requiring 5M tokens to represent on a 1M-context agent is non-operational.
- **Substrate-exposed structure must be parseable from natural-language context** by 2026-class agents — no required external schema documentation for the agent to operate.
- **Substrate must function under host-session intermittency** (per §6). The agent's actual operation pattern is intermittent (chat turns, rate limits, cost gates) even though L0 §6 declares the substrate-level continuity model; L1 reconciles by implementing host-session boundaries as continuity-recovery events.
- **Living Bets signal #6** is the monitoring metric — when ratio breaks down, substrate self-flags.

**Future-readiness**: the L0 invariants and principles are L0-stable for ≥10× scale; what changes is L1 parameters (digest size, metabolic cycle cadence, classifier table, etc.).

**Caveats acknowledged, not engineered around**:
- 2026-class agents may not natively understand v0.9's symbiotic frame — the agent learns through experience with the specific substrate (P1.c is an experiential property, not a doctrinal one).
- Owner-supervised birth (a P1.b'' moment) reasonably extends to "owner watches first ~N substrate events to confirm the substrate isn't producing pathological metabolism under a confused agent". Value of N is L1-specified.

---

## §9. Process — how L0 changes, how to read this branch

### §9.1 Reading sequence for a new agent

1. This file (L0) — nine root principles + eight invariants + dispatch constraints + bet + readiness.
2. L1 documents — positive mechanisms satisfying L0 constraints. The L1 set begins with `L1_OUTLINE.md` (charter), and the first L1 design documents are `L1_TROPISM.md` (dispatch positive form) and `L1_TRAJECTORY.md` (intent derivation positive form).
3. (Future) L2 doctrine — per-subsystem-family doctrine.
4. (Future) L3 implementation map — code organization.
5. (Future) L4 substrate — the live instance + code.

The v0.9 substrate is being designed top-down: L0 first (this document, owner-pending), then L1 documents, then L2 / L3 / L4.

### §9.2 Changes to this page

L0 is the identity layer. Any change requires:

1. A craft-style proposal arguing the revision.
2. Explicit owner approval recorded.
3. A contract-identity-level bump (P1.b'' / I2).
4. A cascade review of every lower-layer doc for implicit dependencies.

**L1 prototyping may surface L0 revision needs.** When L1 implementation reveals that an L0 commitment is unworkable or inconsistent, L1 work pauses and an L0 revision is proposed through this same protocol. L0 is identity, not infallibility — but the bar for revision is high.

L0 revision is never implementation-driven (no "we made it work this way in code, change L0 to match"). L0 revision is doctrine-driven (an argued case that the current L0 is wrong on principle).

### §9.3 Proto archaeology

For lineage:
- `_archive/proto_myco_v0_8/L0_VISION_proto.md` — proto-Myco's L0 (v0.4 - v0.8.7).
- `_archive/proto_myco_v0_8/L0_5_ESSENCE.md` — transitional doctrine that carried the 5 essence decisions into v0.9.
- `_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md` — deliberation log (4 self-corrections + 100%-confidence loop + 20 candidate holes + 10 fix-Hs).

None are authoritative in v0.9. They preserve the lineage.

### §9.4 Dead-embryo concession + maximal origin discrimination

Per owner decisions C1.1 + C7.3:

- v0.4 → v0.8.7 are **proto-Myco / dead embryo / failed gestation attempts**. v0.9 is **Myco's first true birth**.
- Every v0.9 design step must trace its decisions to **≥1 of P1-P9** and **≥1 of the eight invariants**.
- **Origin discrimination is maximal**: any design point that appears similar to v0.8 is **presumed v0.8 contamination unless it independently traces to ≥1 P AND ≥1 invariant**. Inheriting v0.8's specific shape — even when superficially defensible — is rejected.
- Trace rigor is maximal (C7.1): every L1/L2/L3 doc and every code-organization choice must enumerate which P and which invariant it projects.

---

## §10. Glossary (v0.9 precise terms)

| Term | Definition |
|---|---|
| **Myco** | The taxonomic class — digital symbiotic organism. Used as a noun for the class. |
| **A Myco substrate** | A specific instance of the class. "The substrate" within this document refers to one such instance unless context says otherwise. |
| **v0.9** | The current Myco substrate version (under design). vs proto-Myco v0.4–v0.8.7 (dead embryo). |
| **L0_VISION.md DRAFT N** | The Nth revision of *this* document during v0.9 design. Pre-seal; sealed L0 carries no revision number. |
| **Active operator-connection** | The currently-attached operator session (MCP-session-equivalent active connection). The thing that, jointly with the substrate, constitutes the agent identity (P1.c). |
| **Operator-token** | The ephemeral, per-connection handshake identifier the substrate uses at runtime to know which operator is currently attached. Not persisted. Distinct from agent-discriminating attributes (which are forbidden in persisted state per I1). |
| **Substrate-ID** | The persistent, immutable identifier established at substrate genesis. Names the substrate, not the agent. Permitted in persisted state. |
| **Contract-identity-level boundary** | The threshold above which a change alters Myco's identity (vs accumulating content). Defined and enforced by L1 (I2 classifier). Covers L0 modification, L1 protocol modification, identity-level schema fields. |
| **Continuous-operation default** | The substrate's mode: substrate does not formalize session boundaries internally. Host-level sessions are out of substrate scope (handled as continuity-recovery events per §6). |
| **Metabolic cycle** | The substrate's smallest discrete metabolism event. L0 commits that cycles exist + I3/I5/I8 invariants check each cycle; L1 specifies cadence and what each cycle does mechanically. |
| **Spore-schema** | The seed-state passed from parent substrate to child substrate during P8 reproduction. Contains the minimum structural form for the child to begin its own symbiosis (initial appetite axes or equivalent L1-dispatch-form structures, sporocarp-equivalent type tree, SSoT designation). Does NOT include the parent's causal DAG. |
| **Skin / boundary** | The substrate's single declared interface to the rest of reality (intake + output). P9 / I8. |
| **Recoverability budget** | The L1-specified backup/redundancy policy defining when "destroyed" actually means destroyed (vs recoverable from backup). Below budget = recoverable. Beyond budget = mortality. |
| **Adjacent technique** | Any agent-tooling sub-technique (vector retrieval, LLM call, conversation history, semantic federation, human-facing summary, etc.) that adjacent ecosystems (LangChain, CrewAI, DSPy, etc.) implement standalone. Per P2.a / I6, Myco absorbs these inside its framework rather than depending on them externally. |
| **Dispatch form** | The positive shape of the substrate-agent interaction primitive. L0 commits to negative constraints (§5.2); the specific positive form is L1 design. |
| **Rollback (P3 failed evolution)** | Substrate state restoration to the pre-evolution snapshot when a P3 schema/rule evolution leaves the substrate in an I3-inconsistent state. Recorded as a discrete event in the causal DAG. |
| **Birth period** | The substrate's earliest operating window (~first N substrate events, with N L1-specified). Hand-coded seeds for emergent thresholds apply; emergent thresholds activate in steady state. |
| **Steady state** | Post-birth-period operating regime; emergent thresholds and observatory weights activate. |
