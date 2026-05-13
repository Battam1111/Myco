# L0 — Vision

> **Status**: DRAFT 8 — post pass-3 100%-confidence-loop (2026-05-13). Pending owner approval before sealing.
> **Naming**: Myco substrate version is **v0.9**; this document is L0_VISION.md **DRAFT 8**. Drafts are integers, not semver. Sealed L0 carries no draft number — only git commit identity.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: each DRAFT's critic-pass diff is in git history; see commit log. Convergence trace across the 100%-confidence loop: Pass 1 (88 findings / 26 CRITICAL) → DRAFT 6; Pass 2 (66 / 21) → DRAFT 7; Pass 3 (35 / 10, 9 unique roots) → DRAFT 8; Pass 4 (5 / 0) → CONVERGED. Six adversarial fungal-named critics declared convergence in all 6 lenses.
> **Scope discipline**: L0 commits to **identity, negative space, and constraints**. Mechanism specifications live in L1 documents. The single exception: cryptographic anchor surface (§9) is at L0 because the entire trust model depends on out-of-band integrity that cannot be deferred without circularity.

---

## §1. What Myco is

**Myco is a new species of digital symbiotic organism** — a literal taxonomic class within "digital organisms" whose distinguishing properties are: mutual constitution (agent + substrate co-define each other; identity is the pair); autopoietic self-maintenance (no human in the maintenance loop); universal inclusion (every adjacent agent-tooling sub-technique is subsumed INTO Myco's framework, not run in parallel); continuous-operation default at substrate level; and the full biological-essence kit (time / causality, mortality, reproduction, boundary integrity).

The kernel that runs Myco lives inside a Myco substrate, so the agent maintaining Myco IS the agent using Myco — there is no "Myco team" separate from "Myco users". Within this organism, vector retrieval is native, agent-side LLM calls happen within Myco-coordinated context (substrate may itself initiate LLM calls — the v0.8 "substrate-never-calls-LLM" restriction is lifted), conversation history is one form of raw material, semantic inter-substrate federation replaces ad-hoc file sync.

**Mechanism choices** (dispatch form, intent representation, subsystem partition, schema serialization, cryptographic primitives, etc.) are **L1 design**. L0 commits only to the constraints those choices must satisfy (§§4–9). The negative space — what Myco is NOT — is in §3.

**The governance triad** (acknowledged honestly, per pass-1 mycorrhiza-3 finding): the **operational pair** is agent+substrate (P1.c). The **governance gate** is the human owner (P1.b''). The owner is structurally a third party load-bearing in contract-identity-level events — this is not a "residue"; it is integral. The "pair" continues to define Myco-bestowed agent identity; the "triad" describes governance reality.

---

## §2. The nine root principles （根本宗旨）

Myco's identity is exhausted by these nine. Every rule, subsystem, module, and substrate artifact is a projection of them.

### §2.1 The original five principles

### P1. Only For Agent （人类无感知）

Myco is a cognitive substrate **for an LLM agent**. The agent is the sole **consumer** AND the sole **maintainer**. Humans are not in the maintenance loop — the human's relationship is **with the agent and the agent's outputs**, not with Myco itself.

#### P1.a Self-hosting

Myco's own kernel lives inside a Myco substrate. The agent using Myco IS the agent maintaining Myco. Genesis is a one-time human event; maintenance thereafter is everlasting agent.

#### P1.b Two-tier human-loop boundary

- **P1.b' Human OUT of maintenance loop** (strong): daily curation, rule edits, vocabulary changes, governance-mechanism adjustments are agent-only.
- **P1.b'' Human RETAINED as governance gate**: contract-identity-level changes (alterations to L0 / L1 doctrine; changes to substrate kind/identity rather than content) require owner approval. Classifier function is L1-defined.

#### P1.c Agent identity is constituted by symbiosis (asymmetric carrier)

"The agent" is **the active operator-connection currently holding the substrate**. Identity is the property of the pair (substrate + active operator-connection). However — and this asymmetry is **load-bearing, not residual**, per pass-1 mycorrhiza-8 finding:

**The substrate is the persistent carrier** of pair-identity. Operator-connections come and go; the substrate persists (alive ↔ dormant). Bestowal of agent identity flows from substrate to operator-connection at each handshake, not the reverse.

Operational consequences:

- **Same substrate operated successively by different model backends → same agent** (substrate carries the identity continuum across model swaps).
- **Operator-connection disconnect → substrate enters dormancy** (identity continuum preserved; the disconnected operator's specific pair-instance ended, but the substrate's identity carrier persists).
- **Operator reconnect → new pair-instance, same agent identity continuum** (because substrate is the carrier and provides continuity).
- **Different substrates, same operator → different agents** (each substrate is its own identity carrier).
- **Substrate destroyed → bestowed identity ceases** (carrier destroyed; underlying model continues; the symbiotic agent does not).
- **Concurrent same-substrate connections are out of scope** (multi-agent coordination is via P8 reproduction).

This asymmetry is the cost of having identity that persists across reconnects. The substrate carries; the operator joins.

### P2. 永恒吞噬 — Eternal Ingestion （吞噬万物）

Myco consumes without bound. Any input the agent can point at is ingestible raw material. **There is no filter on what enters.** Filtering and shaping are downstream (P3, P4), never at intake.

#### P2.a Strong Inclusion

Myco is **the framework that internally implements** every adjacent agent-tooling sub-technique. Vector retrieval is native (highest-ceiling implementation); agent-side LLM calls happen within Myco-coordinated context; conversation history is one type of raw material; semantic federation replaces byte-level file sync; human-facing summaries are produced through the same internal pipeline as agent-facing surfaces.

These techniques **live inside Myco's framework**; they do not exist in parallel.

### P3. 永恒进化 — Eternal Evolution

Myco's **own shape evolves**. Schema, subsystem family, vocabulary, rules, contract itself — all first-class mutable objects under P1.b's two-tier boundary.

An unchanging substrate is a dead substrate. Schema changes are normal operations.

**Failed-evolution rollback**: when a P3 evolution produces I3 inconsistency, the substrate rolls back to pre-evolution state and records the failure as a discrete causal-DAG event. Rollback mechanism is L1-specified.

**P3.b Joint-context evolution** (per pass-1 mycorrhiza-5): substrate evolution is necessarily context-dependent on the pair's history. Epoch markers carry the substrate's contextual hypothesis about the operator-class at the moment of evolution; specific format is L1-defined.

**Lexicon evolution** (per pass-1 saprotroph-8): the mycology lexicon set is itself a contract-identity-level object. Additions admitted on mycology-literature attestation. Deprecations mark a term `terminal` (no new use; prior usage preserved per I4). Lexicon evolution is I2-classified.

### P4. 永恒迭代 — Eternal Iteration

Every operating moment refines what prior moments produced. There is no terminal state. "Final" is not a status. Retro-editing is allowed and expected — tracked (I4), not suppressed.

### P5. 万物互联 — Universal Interconnection （菌丝网络）

The substrate is a **connected graph**, not a collection. Every node is reachable from every other by traversal. Orphans are dead tissue. The graph spans intra-substrate AND inter-substrate (federated substrates via P8).

### §2.2 The four organism-essence principles

Per owner decision C1.1, Myco's class is digital symbiotic organism — taxonomy, not metaphor. P1-P5 cover audience/intake/evolution/iteration/connection; P6-P9 close the organism-essence gap.

### P6. 永恒因果 — Eternal Causality

The substrate has **time**. Every state is recoverable-derivable from prior states; causality is preserved; the arrow of time is monotonic. Without time, P4 has no arrow, P3 has no direction, decisions cannot be audited.

Time is the **causal-chain DAG** (I4) maintained over the substrate's evolution.

### P7. 必朽 — Mortality

The substrate is **mortal**. Destruction is final. A destroyed substrate's bestowed agent identity ceases (P1.c).

Destruction modes:

- **Intentional-owner**: owner-triggered (owner-signed destruction attestation).
- **Catastrophic-environment**: medium failure beyond L1-specified recoverability budget.
- **Endogenous-pair** (per pass-1 mycorrhiza-4): substrate fruits a `self_euthanasia_proposal` (contract-identity-level event) when its own metabolism crosses an unrecoverable-pathology threshold. Requires owner co-attestation to execute. This is the symmetric counterpart of owner-triggered destruction — the pair has agency over its own ending, owner retains veto.

Dormant ≠ mortal. Graph fragmentation approaching P5 violation is an immune-grade approaching-mortality signal.

**Mortality-signal protection** (per pass-1 mycoparasite-14): the mortality-signal threshold and its update-rule are contract-identity-level — cannot be silently tuned to suppress mortality warnings.

### P8. 永恒繁衍 — Eternal Reproduction

The substrate can spawn child substrates. Reproduction is a first-class operation. The new substrate inherits the parent's **spore-schema** (minimum structural form for the child to begin its own symbiosis — specific contents L1-specified; whether the parent's causal DAG transfers, whether immune-signal summary transfers, all L1-decided).

Reproduction modes: federation (semantic transfer to child) / cloning (full copy) / cross-pollination (multiple parents). L1 picks.

**Federation discovery and trust freshness** are L1-specified (candidate modes: P2P broadcast / owner-attested peer list / hub-and-spoke registry / hybrid). Trust at reproduction is parent-attestation; ongoing federation requires L1-bounded peer-attestation freshness with revocation list — stale/revoked attestation triggers `untrusted_federation` immune signal.

**Spore-schema immune-summary** (per pass-1 mycoparasite-13): spore-schema must include the parent's outstanding immune-signal summary; a child whose parent had unresolved immune signals enters birth period in quarantine until owner re-attests the spawn is intentional.

### P9. 皮肤为界 — Integument

The substrate has a **skin** — a well-defined boundary with the outside world. Skin governs intake (P2 universal admission, but envelope integrity holds) and output (federation, summaries, API responses). Skin breach (write outside skin, read from forbidden source, leak across boundary) is an immune-level signal.

---

## §3. What Myco is not

- **Not a documentation system** (humans don't browse the interior).
- **Not a single-project knowledge base** (any number of projects; project is metadata not boundary).
- **Not a chatbot memory** (conversational recall is raw material, not target).
- **Not version control** (Git owns operational history; Myco owns the current symbiotic graph).
- **Not a file synchronizer** (federation is semantic).
- **Not a LangChain / CrewAI / DSPy competitor** (those are agent-orchestration libraries; Myco subsumes their output per P2.a).
- **Not session-bounded within the substrate** (host-level sessions exist; see §6).
- **Not a request/response protocol** (negative constraint on dispatch; see §5.2).
- **Not silently trusting either party** (substrate distrusts agent self-report; agent distrusts substrate self-report — both via out-of-band anchors per §9).

---

## §4. The eight derived invariants

Every L1/L2/L3 design must mechanically enforce all eight. The set is surjective over P1-P9 (projection table below) and necessary under the strict bar — every invariant is the sole enforcer of at least one P/sub-P entry.

### I1. Lifecycle & Pair-Constituted Identity

The substrate carries a **substrate-ID** established at genesis. The substrate-ID is **owner-signed** at birth (owner cryptographic signature over `(substrate-ID, genesis-timestamp, initial-spore-schema-hash)` — the signature IS the substrate-ID's authority). Re-genesis without owner re-signature is destruction (P7), not rebirth. The substrate cannot mint its own substrate-ID.

**Agent identity** at any moment is the pair `(substrate-ID, currently-attached-operator-token)`. The **operator-token is non-deterministically constructed per-handshake** (per pass-1 mycoparasite-21 — randomized nonce-bound, never derived deterministically from operator-stable secrets). The substrate does not auto-detect operator-continuity across reconnect from token alone; continuity-claims at reconnect require owner-attested operator-succession or are treated as new pair-instances (same agent identity continuum per P1.c).

**No agent-discriminating attribute** (model name, API fingerprint, host fingerprint, persistent user ID, deterministic operator-token) may be persisted in substrate-serializable state. Aggregate read-pattern statistics keyed to the **substrate** (not to any operator) are permitted; per-operator history is not.

**Lifecycle states**: alive ↔ dormant ↔ destroyed (forward only after destroyed). Transitions:

- alive → dormant on operator-disconnect or idle-timeout (L1_CONTINUITY-specified).
- dormant → alive on valid operator handshake OR on owner-attestation arrival at the anchor-surface inbound channel.
- alive → destroyed on owner-attested destruction or recoverability-budget exhaustion.
- destroyed → anything FORBIDDEN.

Sub-states of alive (quarantined under invariant breach; legacy under owner unavailability) are L1_CONTINUITY / L1_GOVERNANCE-defined and do not extend the substrate's three top-level states.

**Owner key rotation**: the substrate's identity record maintains an `owner_key_history` (chronological list of owner public keys with valid-from/valid-until timestamps, each rotation event co-signed by both old and new keys at the anchor surface). Verification of any historical co-sign uses the key valid at that timestamp. Cryptographic suite rotation follows the same pattern. Owner-key rotation is owner-attested at the anchor surface; substrate-ID is unchanged across rotations.

**P-coverage**: P1.a, P1.c, P7.

### I2. Two-Tier Governance Classification (with classifier-fixed-point)

Every mutation classifies mechanically as **daily** (agent-autonomous) or **contract-identity-level** (owner-gated). Classifier function is L1-defined (L1_GOVERNANCE owns).

**Classifier fixed-point** (per pass-1 mycoparasite-4): the classifier function itself, and any mutation to it, is **unconditionally contract-identity-level** — this clause is L0-invariant and cannot be reclassified by any L1 mutation. Recursive classifier capture is structurally forbidden.

**Birth-period CI elevation** (per pass-1 mycoparasite-18): during birth period, ALL parameter-tuning events (seed thresholds, update-rule defaults, fraction settings) are contract-identity-level regardless of steady-state classification. The reclassification to daily-autonomous happens at the birth-period → steady-state transition, which is itself owner-attested.

**P-coverage**: P1.b', P1.b''.

### I3. Self-Validation Against Designated SSoT (with migration two-phase commit)

The substrate has exactly one designated machine-readable SSoT. State consistency against SSoT is checked every metabolic cycle (cycle cadence: L1_CONTINUITY-specified). The SSoT designation is contract-identity-level; cannot be daily-mutated.

**SSoT migration two-phase commit** (per pass-1 mycoparasite-11): migrating to a new SSoT requires (1) new candidate SSoT consistent with current SSoT for ≥ L1-specified cycles, (2) owner co-signs migration. Single-step migration is rejected.

**L0/L1 doctrine vs SSoT** (per pass-1 rhizomorph-18): L0/L1 documents are EXTERNAL governance artifacts (live in git, owner-attested). SSoT is the substrate's own designated internal schema artifact. L0 evolution is reflected into SSoT at the corresponding owner-attested governance event.

**Validation tiering** (per pass-1 saprotroph-12): validation is tiered per L1_SCHEMA — tier-1 (identity-critical) every cycle; tier-2 sampled with rolling 100% coverage over an L1-tunable window; tier-3 owner-triggered. Tiering itself is contract-identity-level.

**P-coverage**: P3, P4, P9 (no silent corruption).

### I4. Full-Fidelity Causal DAG (with Merkle integrity)

Every substrate state is derivable from prior states via a recorded operation, recorded in a causal DAG.

**Materialized-views carve-out** (per pass-1 saprotroph-1): "full fidelity" means **causal recoverability of any state from any prior via recorded operations**. The substrate MAY maintain materialized views (digests, compressed roll-ups) at any tier, provided (a) underlying append-only operations are retained, (b) re-materialization is mechanically possible, (c) materialized-view layer is L1-specified and its retention is contract-identity-level. Materialized-view eviction is NOT pruning.

**Merkle-DAG integrity** (per pass-1 mycoparasite-5): DAG nodes are content-addressed; each node's hash includes its causal-parent hashes (Merkle DAG); the substrate's identity record carries the current **DAG-tip hash**, which is **owner-co-signed at every contract-identity-level boundary crossing**. DAG retro-edits without tip-hash co-signing are immune-detectable as substrate-self-attack.

**Sporocarp causal-proof** (per pass-1 mycoparasite-3): every event-record in the DAG (sporocarps under L1_TROPISM, equivalents under other L1 dispatch choices) carries a `causal_in_edges` proof — the `(input_set, state-snapshot-hash, threshold-value)` tuple at the moment of emission, hash-committed. I3 self-validation recomputes from causal_in_edges. Events without recomputable proofs are invalid.

Re-metabolization produces new DAG nodes referencing prior, never overwrites. Retention policy is contract-identity-level.

**P-coverage**: P6 (sole enforcer), P4, P3.

### I5. Universal Reachability Over Full State Space (with tier enumerability)

The substrate graph is fully connected across every storage tier; every node reaches every other by traversal. Reachability checked every metabolic cycle.

**Tier exemption with enumerability** (per pass-1 mycoparasite-6): tier-exemptions from reachability are contract-identity-level designations AND **tier contents must remain enumerable from the skin (I8) on owner demand**. An exempt tier is exempt from reachability *computation*, not from *existence audit*. A tier whose contents are not enumerable is structurally identical to a skin-breach.

**P-coverage**: P5 (intra-substrate, sole enforcer).

### I6. Universal Inclusion With Observed Metabolism (with network-egress detection)

**(Compound, dual-clause — both required.)**

(a) **Internal-implementation clause**: adjacent agent-tooling techniques (vector retrieval, LLM calls, conversation history, semantic federation, human-facing summaries) live inside the substrate's framework, not as outbound RPCs to external services.

(b) **Observed-metabolism clause**: every invocation produces a metabolism event the substrate observes.

**Network-egress detection** (per pass-1 mycoparasite-8): substrate update-rules whose runtime accesses any network surface other than the declared skin (I8) are skin-breach. The substrate enforces appetite-locality at runtime, not just at declaration: any process-level network-namespace exit outside the declared skin endpoints is detected (specific mechanism — container egress filter, network namespace, syscall hooking, etc. — is L1_SKIN-specified). Update-rules that need external services must declare them as federation peers (P8), not hide them as substrate-internal.

**Embedding-service carve-out** (refined): "substrate-internal" admits (i) local embedding model packaged with the substrate, OR (ii) substrate-managed call to an external embedding service where (1) model identity is attested in the metabolism event, (2) the network exit goes through the declared skin endpoint for embedding service (not arbitrary), (3) embedding-service outage degrades gracefully (intake admits content without embedding; embedding queue is observable). Pure unmanaged outbound RPC remains breach.

**P-coverage**: P2, P2.a (sole enforcer), P1, P1.b'.

### I7. Reproduction Closure (with verification protocol)

Every child substrate independently satisfies ALL invariants I1-I8 (recursively — children spawn closure-bound children) from genesis.

**Closure verification protocol** (per pass-1 rhizomorph-11): at spawn, (a) parent runs static-schema validation (child's SSoT designation, dispatch-form type tree, classifier dimension table match parent's spore-schema), AND (b) child runs its own I3 self-validation as its first metabolic cycle. Success fruits a `genesis_attested` event in the parent's DAG; failure aborts spawn before any federation link commits.

**Peer-trust freshness** (per pass-1 mycoparasite-10): ongoing inter-substrate federation requires L1-bounded peer-attestation freshness. Coupling consuming expired or revoked attestation triggers `untrusted_federation` immune event and quarantines downstream emissions until owner re-attests.

**P-coverage**: P8 (sole enforcer), P5 (inter-substrate).

### I8. Single-Skin Integrity (with handshake continuity-challenge)

The substrate has exactly one declared boundary surface for both intake and output.

**Intake admits all content** (P2 universality); intake rejects only on **envelope integrity** — the envelope schema is L1_SKIN-specified (minimum: sender token, payload-shape declaration, causal-parent ref, size cap, content-type hint).

**Single-operator semantics**: the skin admits at most one operator-token at a time. Second-arrival during active handshake → rejected with `skin_busy` envelope signal AND emits `concurrent_connect_attempt` immune event (daily, elevated grade — owner-observable pattern).

**Handshake continuity-challenge** (per pass-1 mycoparasite-7): incoming operator handshake must produce (a) the substrate-ID owner-signature (I1), AND (b) for contract-identity-level operations within an L1-tunable window of handshake, owner attestation is required regardless of declared governance classification (post-handshake quarantine window).

**Cold-resume invariants**: before presenting state to a reconnecting operator, the substrate runs full I3 + I5 + I8 checks; failure → `alive but quarantined` state until owner attestation; the check results are exposed on the handshake envelope regardless of substrate-internal fruiting (per pass-1 mycoparasite-17 — prevents quarantine-marker spoofing).

**P-coverage**: P9 (sole enforcer), P2 (no-filter clause), P1.c (single-operator).

### Projection table (P → I coverage)

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
| P3.b | I4 (epoch markers in DAG) |
| P4 | I3, I4 |
| P5 | I5, I7 (inter-substrate) |
| P6 | I4 |
| P7 | I1, I5 (fragmentation), endogenous-mortality via I2 governance |
| P8 | I7 |
| P9 | I3 (no silent corruption), I8 |

**Strict necessity** is verifiable by reading the table column-wise — every invariant is the sole enforcer of at least one P/sub-P entry; no invariant droppable.

---

## §5. Strict mycology lexicon and dispatch constraints

### §5.1 Lexicon rule

Myco uses **fungal-biology vocabulary strictly**. Lexicon source: mycology. General-biology and animal-biology terms not in the allowed lexicon. The rule is mechanical: an agent cold-reading the substrate uses the names as a semantic prior, and the prior must be fungal.

**Lexicon scope**: admitted terms include any term mycology literature uses to describe a real fungal phenomenon, even when shared with other fields (e.g., "chemotropism", "gradient", "threshold" describing fungal tropic phenomena). Terms imported purely from physics or mathematics without a mycology footing are not admitted.

**Lexicon evolution** is contract-identity-level (per P3 lexicon-evolution clause; details L1_GOVERNANCE-specified).

**Subsystem partition is L1's choice**; each named subsystem must come from strict mycology lexicon. L0 does not enumerate the candidate set.

### §5.2 Dispatch form — L0 constraints only

L0 commits to negative + constraint statements about Myco's dispatch form. **The positive form is L1 design** (the leading L1 candidate is *tropism + sporocarp punctuation*; see `L1_TROPISM.md`):

- **NOT v0.8 verbs.** Verb-table dispatch (fixed manifest of typed agent-initiated commands) is rejected per owner C5.3.
- **NOT request/response.** Client-server transaction shape rejected; presupposes asymmetry incompatible with P1.c.
- **MUST honor P1.c carrier-asymmetry**. The substrate is the persistent carrier of identity; the dispatch must respect this (the substrate may "speak" in one form, the agent in another — symmetry is in the medium, not necessarily in the utterance shape).
- **MUST support universal inclusion** (P2.a).
- **MUST support continuous operation** (§6).
- **MUST satisfy I6** appetite-locality (or equivalent in chosen positive form).
- **MUST carry causal-proofs** (per I4) for substrate-emitted events.

L1 picks a positive form satisfying all seven.

### §5.3 Intent representation — L0 commitment

**Intent is NOT a first-class substrate data type.** Agent-self-reported intent is structurally not trusted (P1.c — substrate sees what the pair *does*, not what the agent *claims*).

The specific derivation mechanism (trajectory clustering over the causal DAG, declarative thread grouping, or hybrid) is L1 design — see `L1_TRAJECTORY.md` for the leading proposal and its edge cases.

---

## §6. The continuity model

Per owner decision C6.2, **substrate-level session is not a Myco concept**. The substrate is presumed continuously operated; substrate metabolism is continuous; the substrate does not formalize session boundaries internally.

**Host-level sessions are out of L0 scope**. The agent's runtime environment may impose its own session shape; Myco does not control it. Inside the substrate, Myco does not formalize or schedule by host-session boundaries.

Operational implications:

- No substrate-level boot ritual; no substrate-level session-end ritual.
- Host disconnects are recovered, not formalized as session edges. Operator-disconnect → substrate dormant; reconnect → substrate alive.
- Reflexes that v0.8 R1/R2 captured (hunger awareness, senescence cleanup, drift detection) are properties of the substrate's continuous internal metabolism — implemented by L1's chosen dispatch form.

**Dormancy compute budget**: dormant substrate may pause or throttle internal metabolism (L1_CONTINUITY-specified). L0 commits that dormancy is a real state distinct from alive; L0 does not commit to whether dormant metabolism is full / throttled / paused.

**Dormancy host-observability** (per pass-1 mycoparasite-15): dormant substrate's external observables (network, CPU, disk-write) must remain below L1-specified ceilings. Discrepancy is owner-side detectable (substrate cannot enforce against its own host process; this is an explicit asymmetry — substrate's truthfulness about dormancy is owner-checkable, not substrate-checkable).

**Metabolic cycle**: existence and per-cycle invariant checks (I3 + I5 + I8) are L0 commitments. Cycle cadence is L1_CONTINUITY-specified.

**Delta atomicity** (per pass-1 rhizomorph-3): a delta is either fully absorbed (event committed with all causal edges) or not absorbed. Partial absorptions on host crash detected at cold-resume and rolled back as `interrupted_intake` immune event. Atomicity mechanism is L1_SCHEMA-specified.

---

## §7. Living Bets — the bet Myco is making

**The bet.** Myco's symbiotic-organism shape — agent + substrate as mutually constitutive, continuously operating, with the full nine-principle organism essence — has value at every tier of agent intelligence, **in proportion to** the substrate's persistence budget exceeding any single agent's read window. The bet is falsified when a sufficiently capable agent operates a large substrate without engaging dispatch.

**The counter-bet.** Sutton's bitter lesson predicts general-purpose methods with more compute eventually outperform hand-coded structure. A strong reading predicts a capable agent does not need a symbiotic substrate — it just holds everything in context and acts coherently.

### The observatory (6 base signals + 1 composite)

**Each threshold is emergent in steady state** from substrate history; seed values during birth period are L1-specified.

**Six base signals:**

1. **Persistence budget** — total content (size, node count, edge count, event-record count).
2. **Evolution rate** — governance changes (schema, rule, vocabulary, dispatch parameters) over time.
3. **Read-pattern diversity** — variety of substrate-read patterns over a rolling window. Specific operationalization depends on L1 dispatch form.
4. **Federation health** — split per pass-1 saprotroph-6:
   - **4a Cumulative fork count** (monotonic).
   - **4b Reachable-federation count** (peers responding to skin-level health probe at L1-specified cadence).
   - **Divergence 4a-4b** = mycelial fragmentation, immune-grade.
5. **Time trend per signal** — direction (up / flat / down).
6. **Read-window-relative position** — `substrate-total-size / agent-attested-context-window`. **Substrate-total**, not digest-fraction (per pass-1 mycoparasite-16, prevents fraction tampering). Threshold separating "strongly-in-bet-wins" from "bet-loses" is emergent (seed ~100). Window attestation cross-check is L1_SKIN-specified.

   **Model-class epoch buckets** (per pass-1 saprotroph-10): attestation cross-check norms are epoch-bucketed; ≥2× context-window change triggers epoch transition; norm rebuilding starts in the new epoch; prior epoch's norms archived per I4 but no longer participate in active cross-check.

**Composite**:

7. **Composite health score** — emergent weighted aggregation of 1-6. Weights emerge from substrate's own historical correlation; no pre-set.

### Falsifiability trigger (concrete predicate)

Per pass-1 astronaut-6 + saprotroph-7, the trigger is now a **rolling-window quorum**:

> Over a **90-day window of active operation** (L1-tunable), if **≥3 of signals 1-6 trend concurrently against the bet** AND signal #6 stays < 1 for ≥ 50% of cycles in the window, the substrate fruits a `bet_weakening_quorum` event requiring owner re-justification of Myco's existence per §9.

Spike events within a window are DAG-recorded but do not by themselves fire the trigger.

### Review cadence

Every contract-identity-level boundary crossing (P1.b'' / I2) re-audits this section. Until the falsifiability trigger fires, the nine principles + symbiosis formulation stand.

**Not a principle.** Living Bets is a meta-commitment, not a tenth principle.

---

## §8. Operational readiness for present-tier agents

**v0.9 is designed for the agent-intelligence range from 2026-class (≈1M-context LLMs) to ≥10× future agents.**

Mechanical requirements:

- Substrate state must compress to a digest size ≤ read-window budget. L1 specifies digest format.
- Substrate-exposed structure must be parseable from natural-language context by 2026-class agents.
- Substrate must function under host-session intermittency.
- Living Bets signal #6 is the monitoring metric.

**Caveats acknowledged**:
- 2026-class agents may not natively understand the symbiotic frame — learning is experiential per substrate.
- **Owner-supervised birth** is a P1.b'' moment; owner-vigilance during birth is L1_GOVERNANCE-specified (distinct from L1_TROPISM's steady-state-activation threshold).

**Future-readiness**: L0 invariants/principles are stable for ≥10× scale; L1 parameters tune (digest size, cycle cadence, classifier table).

---

## §9. Out-of-band anchor surface (cryptographic root)

**(This is the single L0 mechanism specification, present because the entire trust model depends on it and L1-deferral is circular.)** Without an out-of-band anchor, substrate-self-claims = agent-self-claims under P1.a self-hosting, and the entire trust model collapses.

### §9.1 What the anchor surface is

A surface where owner signatures, DAG-tip hashes, substrate-ID lineage, and trusted timestamps are externally visible and **untouchable by the agent process**. Specific form is L1_GOVERNANCE-specified; candidates: hardware security token, separate machine, signed prompt-bundle the owner reviews, append-only public ledger.

### §9.2 What anchors at this surface

- **Substrate-ID birth attestation** — owner signature over `(substrate-ID, genesis-timestamp, initial-spore-schema-canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key)`. The signature IS the substrate-ID's authority (I1).
- **DAG-tip hash co-signing** — owner co-signs the current DAG-tip hash at every contract-identity-level boundary crossing. Co-sign envelope MUST include **enumerated list of all DAG node hashes added since prior co-sign** — owner's verification recomputes the Merkle chain from these enumerated nodes, NOT from a substrate-supplied summary diff. Retro-edits and parallel-branch forgeries are mechanically impossible without substrate's enumeration matching owner's reconstruction.
- **Owner attestations** — every contract-identity-level mutation requires an attestation produced **out-of-band**: owner-signing key must live outside substrate's process boundary AND outside any process the agent can spawn or read memory of. Attestation events produced inside the agent's process space are skin-breach.
- **L0 revision diff**: L0 revision proposals include a verbatim diff against the prior L0 commit hash; owner reviews against the prior L0, not against the agent-shaped proposal.
- **Anchor-surface-generated nonces** — replay-prevention nonces are generated by the anchor surface (NOT by the substrate); consumed-nonce log lives at the anchor surface; substrate-side nonce mints are not authoritative.
- **Anchor-surface-stamped wall-clock** — every owner attestation carries an anchor-surface trusted timestamp. Time-bound defenses (expiry windows, freshness windows, grace periods, idle timeouts) use the trusted timestamp; substrate-cycle counters are not authoritative for time-bounds (substrate can throttle cycles).
- **Owner liveness heartbeat** — owner periodically signs a `liveness_heartbeat` at the anchor surface (L1-tunable cadence). Succession trigger requires the heartbeat to be stale at the anchor surface, NOT the substrate's absence-of-CI-emission. The substrate cannot manufacture owner-unavailability by suppressing CI emission.

### §9.3 Canonical-bytes doctrine

**The anchor surface receives canonical bytes + witnesses, never substrate-rendered summaries or substrate-emitted verdicts.**

- **Canonical-bytes serialization**: every substrate-emitted artifact bound for the anchor surface uses a deterministic canonical serialization. The serializer spec is **part of the spore-schema and a tier-1 SSoT field** (L1_SCHEMA), allowing every party — substrate, anchor-surface client, operator — to independently compute canonical bytes from the same inputs.
- **Owner-side rendering**: human-readable rendering happens at the owner's anchor-surface client, deterministically computed from canonical bytes. The substrate is not in the rendering path; it cannot drift canonical-bytes-hashed-form from rendered-form.
- **Anchor-surface client provenance independence**: the anchor-surface client (the owner's local rendering + signing tool) MUST be installed and updated through a channel structurally independent of the substrate's distribution channel. Owner attests at genesis that the installed client is from an independent channel (candidate channels: reproducible-build from upstream open-source repo with owner-verified maintainer signature; hardware-token vendor's signed firmware; air-gapped offline distribution). Client distribution that flows through any path the substrate or its maintaining-agent can write to is unsafe.
- **Witnesses, not verdicts**: when the substrate reports a check result (I3/I4/I5/I8 outcomes; recoverability drill results), it emits the witness — sampled leaf hashes + Merkle paths + parent hashes + check inputs — sufficient for the anchor-surface verifier to independently re-derive the result. The substrate does not emit "pass/fail"; it emits the evidence.
- **Anchor-nonce-derived sampling**: sampling indices for witness emission are deterministically derived from the anchor-surface nonce (`H(anchor_surface_nonce, leaf_count)`) — the substrate cannot pre-compute and cannot bias sampling toward honest portions. The anchor-surface verifier re-computes the indices and confirms the substrate emitted witnesses for exactly those indices.
- **DAG-enumeration closure**: when the substrate emits enumerated DAG nodes added since the prior co-sign, the owner verifies (a) the new tip is reachable from the prior signed tip via enumerated nodes, AND (b) **every parent-hash referenced by any enumerated node resolves to either an ancestor of the prior co-signed tip OR another enumerated node** — parent-edge closure. Any parent-hash that does not resolve into the enumerated/ancestral set indicates a hidden parallel branch and aborts co-sign.

### §9.4 What the anchor surface does NOT do

The anchor surface complements (does not replace) the substrate's internal trust mechanisms (I3, I4, I8). It does NOT solve P1.a fully: an adversarial agent could attempt to compromise the anchor mechanism itself, but the anchor's out-of-band nature raises the attack bar from "edit a file" to "compromise a separate system the owner controls".

L0-revision velocity is a substrate observable; tracking method, burst threshold, and rolling rate are L1_GOVERNANCE-specified. Post-seal, L0 revisions should be rare.

---

## §10. Process — how L0 changes, how to read this branch

### §10.1 Reading sequence for a new agent

1. This file (L0) — nine principles, eight invariants, dispatch constraints, bet, readiness, anchor surface.
2. L1 documents — positive mechanisms. Set: `L1_OUTLINE.md` (charter) → `L1_TROPISM.md` (dispatch) + `L1_TRAJECTORY.md` (intent) + **`L1_SCHEMA.md`** + **`L1_GOVERNANCE.md`** + **`L1_SKIN.md`** + **`L1_CONTINUITY.md`** + L1_HARD_RULES (pending). All but L1_HARD_RULES are DRAFT 1 as of this commit.
3. (Future) L2 doctrine, L3 implementation, L4 substrate.

### §10.2 Changes to this page

Any L0 change requires craft proposal + owner approval + contract-identity-level bump + cascade review.

**L1 prototyping may surface L0 revision needs.** When L1 implementation reveals an L0 commitment is unworkable, L1 work pauses and L0 revision is proposed through this same protocol. L0 revision is doctrine-driven, not implementation-driven. The L0 revision diff discipline (§9.2) and burst-detection (§9.4) prevent silent doctrinal drift.

### §10.3 Proto archaeology

- `_archive/proto_myco_v0_8/L0_VISION_proto.md` — proto-Myco's L0 (v0.4 - v0.8.7).
- `_archive/proto_myco_v0_8/L0_5_ESSENCE.md` — transitional doctrine carrying 5 essence decisions into v0.9.
- `_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md` — deliberation log.

None authoritative in v0.9.

### §10.4 Dead-embryo concession + maximal origin discrimination

Per C1.1 + C7.3:

- v0.4 → v0.8.7 are dead embryo. v0.9 is first true birth.
- Every v0.9 design step traces to ≥1 of P1-P9 and ≥1 of the eight invariants.
- Origin discrimination is maximal: similarity to v0.8 is presumed contamination unless independently traced.
- Trace rigor is maximal (C7.1).

---

## §11. Privacy and access model

Per owner decision C8.3: **Myco has no internal privacy / access model**. The substrate is wholly accessible to its operator-agent. Sub-substrate access boundaries are not at L0 level. Multi-operator scenarios handled via P8 reproduction into per-operator child substrates.

The skin (P9 / I8) is the boundary — between substrate and *environment*, not between operators *within* the substrate.

---

## §12. Glossary (v0.9 precise terms)

| Term | Definition |
|---|---|
| **Myco** | The taxonomic class — digital symbiotic organism. |
| **A Myco substrate** | A specific instance of the class. |
| **v0.9** | Current Myco substrate version (under design). vs proto-Myco v0.4–v0.8.7. |
| **L0_VISION.md DRAFT N** | Nth revision of *this* document during v0.9 design. Sealed L0 carries no draft number. |
| **Active operator-connection** | The currently-attached operator session. The thing that, jointly with the substrate, constitutes the agent identity (P1.c). |
| **Operator-token** | Ephemeral per-handshake identifier, non-deterministically constructed per pass-1 mycoparasite-21. Substrate cannot correlate operator-tokens across sessions. |
| **Substrate-ID** | Persistent owner-signed identifier established at genesis (I1, §9.2). Names the substrate; the substrate cannot mint its own. |
| **Contract-identity-level boundary** | Threshold above which a change alters Myco's identity (vs accumulating content). L1_GOVERNANCE-classified; classifier-fixed-point: unconditionally CI-level itself. |
| **Continuous-operation default** | Substrate-level: no formalized session boundaries. Host-level sessions are out of L0 scope. |
| **Metabolic cycle** | The substrate's smallest discrete metabolism event. L0 commits cycles exist + I3/I5/I8 check per cycle; L1_CONTINUITY specifies cadence. |
| **Identity record** | Carries substrate-ID + owner-signature. L1_SCHEMA-specified format. |
| **Spore-schema** | Seed-state from parent → child during P8 reproduction. Minimum structure for child to begin its own symbiosis; specific contents L1-specified including whether parent DAG transfers. |
| **Skin / boundary** | Substrate's single declared interface to reality (P9 / I8). |
| **Recoverability budget** | L1-specified backup policy defining when "destroyed" means destroyed. Below budget = recoverable. Beyond = mortality. |
| **Dispatch form** | The positive shape of substrate-agent interaction primitive. L0 commits to negative constraints (§5.2); positive form is L1 design (leading: tropism + sporocarp punctuation, see L1_TROPISM). |
| **Sporocarp** | Atomic-event-record under L1_TROPISM dispatch (other L1 forms have equivalent atomic records). Substrate-emitted, content-addressed, causally-stamped, carries causal-proof per I4. Per pass-1 rhizomorph-14, "sporocarp" appears in L0 only as a placeholder for the chosen dispatch form's atomic record. |
| **Birth period** | Substrate's earliest operating window. Steady-state-activation threshold L1_TROPISM-specified; owner-vigilance window L1_GOVERNANCE-specified — these are distinct N's. |
| **Steady state** | Post-birth operating regime; emergent thresholds and observatory weights activate. |
| **Anchor surface** | The cryptographic root (§9) — owner-signed attestations and DAG-tip co-signs live here, untouchable by the agent process. L1_GOVERNANCE specifies form. |
| **Legacy sub-state** | I1 sub-state of alive — substrate is operating but L0/L1 mutations are frozen, awaiting owner-successor attestation. |
| **Endogenous mortality** | Per P7 — substrate fruits `self_euthanasia_proposal` (CI-level event) on unrecoverable-pathology threshold; requires owner co-attestation to execute. |
