# L0 — Vision

> **Status**: DRAFT 9 PROPOSAL v2 — Phase γ audit revision + Phase γ.9 6-critic adversarial round (2026-05-17). **Pending owner review of §17 gates G-1 through G-11 before sealing.** Phase γ.9 found 223 findings (54 CRITICAL) on DRAFT 9 v1; structural CRITICALs fixed in v2; remaining CRITICALs deferred to owner gates + cascade work (§18.2 inventory). Prior DRAFT 8 archived in git history at commit `3d6749f` (Phase α).
> **Naming**: Myco substrate version is **v0.9**; this document is L0_VISION.md **DRAFT 9 PROPOSAL**. Drafts are integers, not semver. Sealed L0 carries no draft number — only git commit identity.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: each DRAFT's critic-pass diff is in git history. Convergence trace across 100%-confidence loops: DRAFT 6 ← Pass 1 (88/26) → DRAFT 7 ← Pass 2 (66/21) → DRAFT 8 ← Pass 3 (35/10) → DRAFT 8 sealed for owner review; Pass 4 declared convergence (5/0) across all 6 fungal lenses. **Phase γ audit (2026-05-17): 6 opus agents × ≥30 findings each → ~180 findings, 23 CRITICAL across implementation+doctrine.** DRAFT 8 was found to (a) over-claim "literal taxonomic class" species framing, (b) under-specify anchor surface (9 of 11 §9 clauses honor-system, 0-30% mechanically enforced), (c) omit 6 essential principles (selective compression / metabolic economy / differential response / embodiment / telos / population consensus), (d) miss 12 structural gaps (adversarial owner / owner mortality / time semantics / forkbomb / anchor client DR / aged Living Bets seed / liveness / substrate_id collision / backup privacy / doctrine self-consistency / catastrophic forgetting cure / single-skin failure point), (e) rhetorically over-claim in P1/P2/P3/P5/P9 names. **DRAFT 9 PROPOSAL drafted to address all findings.** Critique passes for DRAFT 9: round 1 TBD, owner approval gates sealing.
> **Scope discipline**: L0 commits to **identity, negative space, and constraints**. Mechanism specifications live in L1 documents. Three L0 mechanism exceptions exist because L1-deferral is structurally circular:
>   - Cryptographic anchor surface (§9, inherited from DRAFT 8; DRAFT 9 decomposes into 6 explicit sub-mechanisms §9.1-§9.6 with implementation status).
>   - Time semantics (§13, **new in DRAFT 9**): substrate uses time everywhere (expiry, nonce TTL, cycle-counter relations); without an L0 commitment to monotonic-vs-wall-clock + NTP discipline, every time-bound defense is undefined.
>   - Adversarial-owner threat model (§14, **new in DRAFT 9**): if "anchor surface" is the trust root and "owner controls anchor", the threat model for compromised/coerced/deceased owner is L0-load-bearing, not L1-deferrable.

---

## §1. What Myco is — and what Myco is not (honesty-calibrated)

**Myco is a biology-rooted symbiotic digital substrate** for an LLM agent. Myco draws structural inspiration from mycology (event-sourced DAG ≈ mycelial network; sporocarps ≈ fruiting bodies; spore-schema ≈ genetic inheritance; quarantine ≈ immune response). DRAFT 8's framing as "a literal taxonomic class within digital organisms" was rhetorical maximalism that did not survive Phase γ.6 critique. **DRAFT 9 calibrates honestly**:

### §1.1 What Myco IS

- **Agent-substrate symbiosis with asymmetric carrier** (P1.c): substrate persists; operator-connection attaches per-handshake. Identity is bestowed by substrate onto pair-instance.
- **Semi-autopoietic** (DRAFT 9 honest framing): autopoietic in daily ops (no human in maintenance loop for non-CI mutations); owner-gated in identity-level ops (P1.b'' + §10.2 require owner attestation for L0/L1 changes). True Maturana-autopoiesis is unachievable for a system whose schema is human-attested.
- **Structurally inclusive** of adjacent agent-tooling sub-techniques (P2.a): vector retrieval native; LLM calls Myco-coordinated; conversation history as raw material; semantic federation; human-facing summaries through internal pipeline.
- **Continuous-operation default** at substrate level; host-session intermittency handled internally.
- **Four biology-rooted essences** (DRAFT 8 set, anchored in biological literature):
  - Causality (P6) — full Merkle DAG; analogue of cell-cycle ordering.
  - Mortality (P7) — capacity for finite end; analogue of apoptosis-capacity.
  - Reproduction (P8) — spore-schema inheritance; analogue of mycelial spore formation.
  - Boundary integrity (P9) — single skin; analogue of cell membrane.
- **Two organism-essential-analogues** (DRAFT 9 additions, biology-inspired but not strict biology):
  - **Selective compression (P10)** — analogue of synaptic pruning + REM consolidation; in Myco, lossy compression of non-invariant state under CI attestation. Not enzymatic.
  - **Metabolic economy (P11)** — analogue of cellular ATP budget; in Myco, finite cost budgets over disk/compute/network. Not chemical.

### §1.2 What Myco IS NOT (negation creates implicit positive claims)

Per §3 (expanded in DRAFT 9), Myco is honestly NOT:

- A literal biological organism (no chemical energy; no embodied sensorimotor loop; no enzymatic regulation; no neural substrate). The principles P1-P15 describe **a substrate inspired by biology, not biology itself**. The word "organism" appears in this document as **vocabulary of inspiration, not classification**.
- Co-defined in the strong sense — P1.c says **asymmetric carrier**: substrate carries identity, operator joins. "Mutual constitution" in DRAFT 8 was rhetorically imprecise; DRAFT 9 says **asymmetric bestowal**.
- Autopoietic in the strict Maturana sense (humans are governance gate).
- Safe under adversarial owner (DRAFT 9 §14 makes the threat model explicit, not implicit).
- A LangChain/CrewAI/DSPy competitor in the "subsumes their output" sense — Myco is structurally adjacent + inclusive *of patterns*, not a re-implementation. The "universal inclusion" claim in DRAFT 8 was over-stated; DRAFT 9 P2.a clarifies as "structural inclusion of *patterns*, not literal subsumption of code".

### §1.3 The governance triad (acknowledged in DRAFT 8, re-emphasized in DRAFT 9)

- **Operational pair**: agent + substrate (P1.c).
- **Governance gate**: human owner (P1.b'').
- **Anchor surface**: cryptographic root the owner uses to attest CI events (§9); per Phase γ.5 audit, **DRAFT 9 explicitly acknowledges** that operator-IS-anchor collapse in current v0.9 implementation is a temporary scaffolding, not a doctrinal endpoint. Real anchor surface (separate process, sealed key, owner-controlled) is required for production trust claim.

---

## §2. The fifteen root principles （根本宗旨）

Myco's identity is now described by **fifteen principles** (DRAFT 8 had nine; DRAFT 9 adds P10-P15 per Phase γ.6 findings). Every rule, subsystem, module, and substrate artifact is a projection of these.

### §2.1 The original five (renamed for honesty)

### P1. Agent-Primary （以代理为本）

> DRAFT 9 renaming from DRAFT 8's "Only For Agent / 人类无感知". The "human imperceptible" framing was false on its own terms — humans are governance gate at every CI event (P1.b''), explicitly perceiving every L0 revision, key rotation, spawn, federation change.

Myco is a cognitive substrate **for an LLM agent**. The agent is the sole **consumer** of substrate state AND the sole **maintainer** of substrate behavior in daily ops. Humans are **out of the daily-ops loop** AND **load-bearing in the CI-ops loop** (governance gate). The human's relationship is **with the agent and the agent's outputs**, not with Myco's internals.

#### P1.a Self-hosting (in daily ops)

Myco's own kernel lives inside a Myco substrate. The agent using Myco IS the agent maintaining Myco *for daily ops*. Genesis is a one-time human event; CI events thereafter are owner-gated; daily maintenance is everlasting agent.

#### P1.b Two-tier human-loop boundary

- **P1.b' Human OUT of daily maintenance loop** (strong): daily curation, raw_material ingestion, gradient tuning within emergent thresholds, sporocarp emission, immune response, federation health monitoring are agent-only.
- **P1.b'' Human RETAINED as governance gate** (CI ops): contract-identity-level changes (L0/L1 doctrine, classifier table, mortality threshold, owner key, anchor surface endpoint, destruction attestation) require owner approval via anchor surface (§9). Classifier function is L1-defined.

#### P1.c Agent identity via symbiosis (asymmetric carrier — DRAFT 9 emphasis)

"The agent" is **the active operator-connection currently holding the substrate** as the bestowed pair-instance. Identity is **the substrate's bestowal upon the operator-connection at handshake**, not mutual construction. The substrate is the **persistent carrier** of pair-identity; the operator-connection is **transient holder**. Bestowal flows substrate → connection.

Operational consequences (unchanged from DRAFT 8, asymmetry-emphasized):
- Same substrate operated successively by different model backends → same agent (substrate carries identity continuum).
- Operator-connection disconnect → substrate enters dormancy.
- Operator reconnect → new pair-instance, same agent identity continuum.
- Different substrates, same operator → different agents.
- Substrate destroyed → bestowed identity ceases.
- Concurrent same-substrate connections out of scope.

### P2. Eternal Ingestion (Envelope-Gated) （吞噬万物，皮膜守门）

> DRAFT 9 renaming from DRAFT 8's "Eternal Ingestion / 永恒吞噬". DRAFT 8's "no filter on what enters" was rhetorically maximalist but mechanically false — I8 envelope filter exists, I6 metabolism event is required. The "no filter" claim contradicted I8. DRAFT 9 acknowledges: P2 commits to **no semantic filter on content**, but **envelope structural integrity is a precondition of identity** (per I8), not a content filter.

Myco consumes without bound at the **semantic** level: any input the agent can point at, with valid envelope structure, is ingestible raw material. **There is no filter on what content enters** — only on whether the envelope (sender token, payload shape, causal parent, size, content-type hint) is structurally well-formed. Envelope validation is a **precondition** of admission, not a semantic filter.

#### P2.a Structural Inclusion (DRAFT 9 calibrated)

Myco is the framework that **structurally implements** every adjacent agent-tooling sub-pattern: vector retrieval as a native data structure (not just an API call to external embedding service); agent-side LLM calls within Myco-coordinated context; conversation history as raw material; semantic federation replacing byte-level file sync; human-facing summaries through internal canonical-bytes pipeline.

**DRAFT 9 calibration**: "structurally implements the pattern" ≠ "literally subsumes the codebase". Myco does not re-implement LangChain. It implements the *patterns* of agent-coordination (memory, tools, planning, retrieval) as substrate-native primitives. LangChain code can be wrapped *within* Myco's framework; LangChain itself is not absorbed.

### P3. Resumable Evolution （可逆迭代）

> DRAFT 9 renaming from DRAFT 8's "Eternal Evolution / 永恒进化". DRAFT 8's "eternal" was inaccurate — P3 includes "Failed-evolution rollback" which IS reversal. DRAFT 9 honest: evolution is **resumable, rollback-permitting, monotone-overall-but-locally-reversible**.

Myco's own shape evolves. Schema, subsystem family, vocabulary, rules, contract itself — all first-class mutable objects under P1.b's two-tier boundary.

**Resumability** (DRAFT 9 honest framing): a P3 evolution is permitted to *fail* and roll back (becomes a recorded `evolution_failed:*` DAG event); the substrate resumes from pre-evolution state. Forward progress at the **substrate-identity level** is monotone (substrate-ID is fixed; owner-key history monotone-grows); local evolution attempts may be non-monotone.

**P3.b Joint-context evolution** (per Phase α): substrate evolution is necessarily context-dependent on the pair's history.

**Lexicon evolution**: the mycology lexicon set is itself a contract-identity-level object. Additions admitted on mycology-literature attestation. Deprecations mark a term `terminal` (no new use; prior usage preserved per I4). Lexicon evolution is I2-classified.

### P4. Eternal Iteration （永恒迭代）

Every operating moment refines what prior moments produced. There is no terminal state. "Final" is not a status. Retro-editing is allowed and expected — tracked (I4), not suppressed.

> DRAFT 9: P4 survives Phase γ.6 with no renaming. "Eternal" here means **at every operating moment, refinement occurs**, not "evolution is monotone forever". P4 is bounded by P7 mortality (the substrate's eternal-iteration ends when it dies).

### P5. Universal Interconnection (Tier-Exempt-Permitted) （万物互联，允分层）

> DRAFT 9 renaming from DRAFT 8's "Universal Interconnection / 万物互联". DRAFT 8's "universal" was contradicted by I5 "Tier exemption with enumerability". DRAFT 9 honest: "universal at the *active* graph level, with CI-attested tier exemptions for archival/compressed layers".

The substrate is a **connected graph**, not a collection. Every active-tier node is reachable from every other active-tier node by traversal. Orphans in the active tier are dead tissue. CI-attested tier exemptions (cold-tier archive, compressed roll-ups, selective-compression P10 outputs) are permitted per I5 and remain enumerable on owner demand. The graph spans intra-substrate AND inter-substrate (federated substrates via P8).

### §2.2 The four organism-essence principles (DRAFT 8 set, calibrated)

### P6. Eternal Causality （永恒因果）

> DRAFT 9: P6 is the principle Myco delivers **most defensibly** per Phase γ.6 assessment. No renaming needed.

The substrate has **time**. Every state is recoverable-derivable from prior states; causality is preserved; the arrow of time is monotonic. Without time, P4 has no arrow, P3 has no direction, decisions cannot be audited.

Time is the **causal-chain DAG** (I4) maintained over the substrate's evolution.

### P7. Mortality (Capacity-for-Death) （能朽）

> DRAFT 9 renaming from DRAFT 8's "Mortality / 必朽". The DRAFT 8 "必朽" ("must die") was misleading — substrate is *capable* of mortality, not *required* to die. DRAFT 9 honest: substrate is **mortal-capable**, not **default-mortal**. Dormancy is indefinite; mortality is triggered (intentional / catastrophic / endogenous).

The substrate is **capable of mortality**. Destruction, when it occurs, is final. A destroyed substrate's bestowed agent identity ceases (P1.c).

Destruction modes (unchanged from DRAFT 8):
- **Intentional-owner**: owner-triggered (owner-signed destruction attestation).
- **Catastrophic-environment**: medium failure beyond L1-specified recoverability budget.
- **Endogenous-pair**: substrate fruits a `self_euthanasia_proposal` (CI-level event) when its own metabolism crosses an unrecoverable-pathology threshold. Requires owner co-attestation to execute.

**Mortality-signal protection**: the mortality-signal threshold and its update-rule are contract-identity-level — cannot be silently tuned to suppress mortality warnings.

### P8. Eternal Reproduction (Generation-Bounded) （永恒繁衍，代际有限）

> DRAFT 9: renaming with explicit generation-bound. Phase γ.3 G11 found P8 has no forkbomb defense — recursive sproutChild loops with compromised owner-key generate infinite consent. DRAFT 9 §16 (new) specifies generation limits.

The substrate can spawn child substrates. Reproduction is a first-class operation. The new substrate inherits the parent's **spore-schema** (minimum structural form for the child to begin its own symbiosis — specific contents L1-specified).

**Generation discipline** (DRAFT 9, addresses Phase γ.3 G11): reproduction depth is bounded per §16. No reproduction loop without owner co-attestation per spawn. No species-mesh between unrelated substrates (acknowledged limitation per Phase α gap #3; addressed by P15 only when consensus achieved).

**Federation discovery and trust freshness** are L1-specified. Trust at reproduction is parent-attestation; ongoing federation requires L1-bounded peer-attestation freshness with revocation list — stale/revoked attestation triggers `untrusted_federation` immune signal.

**Spore-schema immune-summary**: spore-schema must include the parent's outstanding immune-signal summary; a child whose parent had unresolved immune signals enters birth period in quarantine until owner re-attests the spawn is intentional.

### P9. Single Integument （单一皮膜）

> DRAFT 9 renaming from DRAFT 8's "Integument / 皮肤为界". DRAFT 8 name was correct but missed the "single" load-bearing constraint of I8 ("exactly one declared boundary surface"). Phase γ.3 G19 found single-skin = single-failure-point with no redundancy doctrine. DRAFT 9 acknowledges this as P9.b explicitly.

#### P9.a Single Skin
The substrate has a **skin** — a well-defined boundary with the outside world. Skin governs intake (P2 universal admission, but envelope integrity holds) and output (federation, summaries, API responses). Skin breach (write outside skin, read from forbidden source, leak across boundary) is an immune-level signal.

#### P9.b Single-Failure-Point Acknowledgment (DRAFT 9)
I8 mandates exactly one skin. This is **single-point-of-failure**: if skin process dies, substrate cannot accept owner's quarantine_clearance, cannot fruit, cannot federate. L1_SKIN MUST specify skin-restart discipline (process supervision, ordered shutdown, recovery semantics). Multi-skin redundancy is **explicitly forbidden** at L0 level — the integument must remain single — but the **skin process** may be restartable.

### §2.3 The six DRAFT 9 additions (Phase γ.6)

> Phase γ.6 audit found 6 essential principles missing from DRAFT 8's 9-principle framework. These 6 are organism-essential analogues that distinguish Myco from "a structured database with biological vocabulary". Adding them brings the framework to 15 principles, which DRAFT 9 commits to as the **revised exhaustive set**.

### P10. Selective Compression （选择性凝结）

> Phase γ.6 finding C-claim-2 (most important missing concept). The DRAFT 8 doctrine forbade pruning (I4 + F9). Biological organisms forget — synaptic pruning, REM consolidation. Myco-without-forgetting is a tape archive, not an organism.

The substrate **selectively compresses** prior states under CI attestation. Compression is **lossy at the semantic level** but **preserves causal recoverability of identity-critical state** (I9 below specifies what survives compression).

#### P10.a What may be compressed
- Old raw_material whose semantic content has been **digested** into higher-level sporocarps (i.e., the gradient axes have absorbed it).
- Old gradient perturbations whose deltas have been **integrated** into current axis values (raw delta history pruned; integrated value retained).
- Federation envelope payloads older than L1-tunable retention.
- Trajectory clusters older than the active rolling window (per L1_TRAJECTORY).

#### P10.b What CANNOT be compressed (compression-invariant set, enforced by I9)
- Substrate-ID + genesis attestation.
- Owner key history (active + archived).
- All CI-attested events (any DAG node from a CI mutation).
- Mortality signal events (cycle_backlog, bet_weakening_quorum, endogenous_mortality_proposal).
- Federation peer pin events.
- The most recent N cycles (L1-tunable, ≥1000) of full causal DAG (no compression in the recent window).

#### P10.c Compression is CI-attested
Each compression event is itself a CI-level mutation: it requires owner attestation, emits a `compression_event` sporocarp with witness (what was kept, what was discarded, the compression-rule version, the canonical-bytes hash of the pre-compression state). Compression is **never silent**.

> Interaction with I4: I4 commits to **causal recoverability of any state from any prior via recorded operations**. P10 commits to **causal recoverability of compression-invariant set + retroactive recoverability of compressed semantics via witness re-derivation**. The set difference is the **honest forgetting boundary**: substrate forgets *which axis was perturbed by 0.3 vs 0.31 at cycle 500*, but retains *the cycle-500 axis-value canonical-bytes hash*. Compression-invariant identity stays exact; compression-permitted history is replaced by digests.

### P11. Metabolic Economy （代谢经济）

> Phase γ.6 finding C-claim-3. Phase α gap #2 (energy economics). Living organisms have ATP cost per action. Myco-without-cost means "eternal ingestion + no filter" is deferred bankruptcy.

The substrate operates within **finite resource budgets** (disk, memory, compute, network egress, embedding-service quota). Every operation has **cost**. Cost is **observable** (per I10 below) and **L1-budgeted** (cost thresholds defined at L1_SCHEMA + L1_CONTINUITY).

#### P11.a Cost units
At L0 level, "cost" is abstract. L1 specifies the concrete units:
- **Persistence cost** (bytes added to DAG per metabolic cycle).
- **Compute cost** (cycles, gradient updates, sporocarp fruitings per cycle).
- **Network cost** (federation envelope bytes, embedding-service queries).

#### P11.b Cost-budget signals
The Living Bets observatory (§7) MUST include cost-budget signals. The current signal #1 (persistence budget) is the start; DRAFT 9 mandates additional signals **#7 compute-cost / cycle, #8 network-cost / cycle, #9 storage-cost / cycle** (numbering aligned with §7.3 — the earlier DRAFT 9 v1 "#1.5/#1.6" was Phase γ.9 rhizomorph C7 ordinal-discipline violation and is retracted). L2_OBSERVABILITY specifies the exact metric definitions.

#### P11.c Budget exhaustion (ordered fallback)
When a cost budget is exhausted, the substrate MUST apply the **first-applicable** response from this ordered list (DRAFT 9 corrects the "OR" ambiguity from DRAFT 9 v1):

1. **Pre-compression-eligibility** (cycle counter < L1-tunable N, default 1000): **refuse new P2 admission** (degraded mode; emits `budget_exhausted:{axis}` immune signal). P10 compression is FORBIDDEN here by P10.b's "recent N cycles" invariant.

2. **Post-compression-eligibility** (cycle counter ≥ N AND owner-pre-attested compression rules exist): **trigger P10 selective compression** with witness emission per I9.

3. **Compression-insufficient OR no pre-attested rules**: enter degraded operation per L1_CONTINUITY (alive-but-saturated sub-state). Sustained saturation past L1-tunable threshold escalates to P7 endogenous-mortality consideration.

L0 commits the **ordered fallback structure**; L1 picks per-stage thresholds. This resolves the Phase γ.9 primordium CF8 P10/P11 deadlock (P11 demanded compression at any budget exhaustion; P10 forbade it pre-cycle-N).

### P12. Differential Response （差异响应）

> Phase γ.6 finding C-claim-4. P2 admits everything equally → noise hoarding. Fungal hyphae extend differentially toward nutrient gradients; Myco needs attention-level discipline.

The substrate **weights inputs differentially** in downstream processing. P2 admits all envelope-valid content; P12 commits that **downstream operations (sporocarp fruiting, gradient perturbation, attention to events) prioritize**.

#### P12.a Salience signals
Salience is **emergent**, not hardcoded. The substrate observes which raw_material kinds correlate with which sporocarp fruitings, and L1_TROPISM (the tropism subsystem) tunes salience weights from this observation. L1 specifies the salience-emergence mechanism.

#### P12.b Anti-uniformity guarantee (with birth-period exemption)
The substrate MUST NOT treat all inputs equally in attention **in steady state**. If observation detects salience-flattening (every input weighted equally over a rolling window), the substrate emits `salience_collapse` immune signal (L1_TROPISM detector).

**Birth-period exemption** (Phase γ.9 primordium CF7): during birth period, salience IS uniform by structural necessity (no history to differentiate from). P12.b detector is SUSPENDED during birth period; substrate emits `salience_emergence_pending` observability event instead. After birth-period termination + L1-tunable settling window (seed: 100 cycles), P12.b activates.

**Bootstrap initialization** (hypha): until N raw_material samples observed (L1-tunable, seed N=100), salience weights are uniform (this is the structurally-correct cold-start, not a violation). Then EWMA-correlation begins. L1_TROPISM specifies the EWMA decay rate.

> Relation to P2: P2 is admission; P12 is attention. P2 says *all valid envelopes are admitted as raw material*; P12 says *raw material is differentially metabolized into gradient + sporocarps*. They are non-overlapping.

### P13. Embodiment (Minimum-Viable) （最小具身）

> Phase γ.6 finding + Phase α gap #1. DRAFT 8 had no embodiment doctrine; Myco substrate is "where" — but nowhere. DRAFT 9 commits to **minimum-viable embodiment**: the substrate has a single declared spatial boundary, and any operation outside that boundary is breach.
>
> **Distinct from P9 Single Integument**: P9 is about *what content crosses the boundary*; P13 is about *what spatial extent the boundary encloses*. P9 governs the gate; P13 governs the territory. These are non-overlapping: P9 fails if content leaks across declared skin; P13 fails if substrate operations touch state outside the declared state_dir + process boundary (e.g., reading host's `/etc/passwd`).
>
> **Distinct from P11 Metabolic Economy**: P11 is about *cost of operations*; P13 is about *spatial locus of operations*. P11 fails if operations exceed budget; P13 fails if operations occur outside body.

The substrate has a **spatial boundary**. The boundary is **the substrate's state_dir + the substrate's process boundary + the substrate's declared skin endpoints** (per L1_SKIN). Operations outside this boundary are P13 breach (distinct from P9 envelope breach; both are immune signals at L1_HARD_RULES level).

#### P13.a State_dir is the substrate's body
The substrate's state lives in a single declared filesystem directory (`MYCO_STATE_DIR`). The state_dir is **the substrate's spatial form**. Backups, replication, transfer of state_dir = backup, replication, transfer of the substrate.

#### P13.b Process boundary is the substrate's nervous system
The substrate runs as a single OS process (Rust binary). Network I/O exits through the declared skin endpoints (federation listener + bridge channel). Multi-process splits are L1 design (e.g., kernel/bridge spawns Python worker — but Python worker is a sub-organ within the substrate's body, not a peer substrate).

#### P13.c Embodiment is NOT physical
Myco does not have sensors, actuators, or chemical embodiment. The "spatial boundary" is digital — directory inode, process PID, declared network endpoints. **DRAFT 9 acknowledges this as honest minimum-viable embodiment**, not aspirational physicality.

#### P13.d Body integrity detection (DRAFT 9 mechanism)
P13 breach detection: substrate periodically lists its state_dir contents + own process file-descriptor set + own network bindings. Any unexpected file in state_dir (not in {dag.cb, snapshot.cb, substrate_signing_key.cb, *.tmp}) OR unexpected fd OR unexpected binding → emit `P13_embodiment_breach` immune signal. L1_SKIN specifies the cadence + the allowed-set.

### P14. Telos (Agent-Symbiotic-Flourishing) （目的：共生繁盛）

> Phase γ.6 finding C-claim-5. DRAFT 8 said "substrate is for the agent" but never named substrate-internal purpose. A "species" without telos is a sediment. DRAFT 9 commits to **agent-symbiotic-flourishing** as substrate's telos.

The substrate's **telos** is to contribute to the flourishing of the agent-substrate symbiotic pair. "Flourishing" is operationally defined as: the pair (over time) accumulates causal capacity to do useful work for the operator's underlying goals, where "useful work" is owner-observed and bet_weakening_quorum (§7) measures the absence of usefulness.

#### P14.a Substrate-internal purpose
The substrate's daily-ops decisions (which sporocarps to fruit, which raw_material to attend to, which mutations to accept) MUST be evaluable against P14. L1_TROPISM specifies how telos-alignment is computed (likely: trajectory-cluster coherence per L1_TRAJECTORY + agent-feedback-trajectory).

#### P14.b Owner-stated objectives
The owner MAY (not must) declare explicit objectives at genesis or via CI events: "this substrate exists to help me research X / write Y / debug Z". When declared, P14 alignment is checked against these objectives. When not declared, P14 alignment defaults to "agent-perceived utility" (operationalized by L1_TROPISM).

#### P14.c Telos drift detection (with birth-period exemption)
The substrate observes its own telos-alignment **in steady state**. If P14 alignment degrades over a rolling window (more sporocarps trend orthogonal to owner-stated or agent-perceived utility), the substrate emits `telos_drift` immune signal (L1_TROPISM detector).

**Operationalization**: "telos-alignment" is computed as cosine similarity between the substrate's recent-sporocarp embedding-centroid and the owner-stated-objective embedding (when objective declared) OR the agent-feedback-trajectory embedding (when no owner objective declared). Similarity below L1-tunable threshold (seed: 0.4 cosine) over rolling window triggers drift detection.

**Birth-period exemption**: telos has no measurable history pre-birth-period-termination; P14.c is SUSPENDED during birth period. Substrate emits `telos_alignment_pending` observability event instead.

### P15. Population-Level Consensus （群体共识）

> Phase γ.6 finding C-claim-6. Federation in DRAFT 8 was pairwise gossip with owner-attested trust — no consensus mechanism. The "mycelial network" doctrine implies population-level claims (mycelial fragmentation, federation health) but has no protocol for population-level agreement.

When the federation includes ≥3 substrates and a claim is population-level (e.g., "this peer is malicious", "this raw_material kind is universally junk"), the substrate operates under a **Byzantine-fault-tolerant consensus protocol**. L2_FEDERATION specifies the protocol.

#### P15.a Population-level claims
Examples requiring consensus:
- Federation peer revocation (one peer claims another is malicious — single-peer claim is insufficient).
- Universal-junk raw_material classification (population-wide spam filter).
- Cross-substrate aggregate observability metrics.

#### P15.b Pairwise-trust below the consensus floor
Claims not crossing P15.a's threshold continue using DRAFT 8's pairwise-attested trust (P8 + L2_FEDERATION). P15 commits to the existence of a consensus floor; L2 specifies where the floor sits + the Byzantine algorithm choice (likely Tendermint-style PBFT or PoS variants — L1 picks).

#### P15.c Single-substrate operates without consensus
A substrate operating outside any federation (lone substrate, no peers) needs no consensus mechanism. P15 activates only when ≥3 federation peers + population-level claims exist.

---

## §3. What Myco is NOT (expanded in DRAFT 9)

> Each negation is an implicit positive claim. DRAFT 9 makes the implicit explicit.

- **Not a documentation system** (humans don't browse the interior).
- **Not a single-project knowledge base** (project is metadata, not boundary).
- **Not a chatbot memory** (conversational recall is raw material, not target).
- **Not version control** (Git owns operational history; Myco owns the current symbiotic graph).
- **Not a file synchronizer** (federation is semantic).
- **Not a LangChain / CrewAI / DSPy reimplementation** (those are agent-orchestration libraries; Myco implements the *patterns* per P2.a, never claims to subsume their codebase).
- **Not session-bounded within the substrate** (host-level sessions exist; see §6).
- **Not a request/response protocol** (negative constraint on dispatch; see §5.2).
- **Not silently trusting either party** (substrate distrusts agent self-report; agent distrusts substrate self-report — both via out-of-band anchors per §9).
- **Not a literal biological organism** (DRAFT 9 addition; explicit honesty per §1.2).
- **Not safe under adversarial owner** (DRAFT 9 addition per Phase γ.3 G8 + §14): if owner is coerced or compromised, the substrate has no defense beyond what §14 specifies. This is acknowledged not denied.
- **Not safe across owner death without succession** (DRAFT 9 addition per G9 + §15): if owner dies and succession is unattested, substrate eventually enters legacy state.
- **Not embodied in physical reality** (DRAFT 9 addition per P13 clarification): substrate's body is filesystem + process + endpoints; no sensors, no actuators.
- **Not free of metabolic cost** (DRAFT 9 addition per P11): every operation has cost; P2 admission is bounded by P11 budget.
- **Not eternal-memory** (DRAFT 9 addition per P10): substrate forgets selectively under CI attestation.
- **Not consensus-free at population scale** (DRAFT 9 addition per P15): federations of ≥3 substrates operate under Byzantine-fault-tolerant consensus for population-level claims.
- **Not winning the Sutton bet at every agent-intelligence tier** (DRAFT 9 honesty per Phase γ.6 + §7 recalibration): the bet has a finite range of applicability; above some agent-intelligence tier the bet is lost. §7 specifies the boundary.

---

## §4. The twelve derived invariants

> DRAFT 8 had I1-I8 invariants enforcing P1-P9. DRAFT 9 adds I9-I12 enforcing P10-P14. P15 is enforced through I7 reproduction-closure extension. The invariants remain mechanically enforceable; every L1/L2/L3 design must satisfy all twelve.

### I1. Lifecycle & Pair-Constituted Identity (unchanged from DRAFT 8, anchor-aware)

The substrate carries a **substrate-ID** established at genesis. The substrate-ID is **owner-signed** at birth via the anchor surface (§9.2.1 + §9.3 substrate-ID birth attestation; was implicit in DRAFT 8). Re-genesis without owner re-signature is destruction (P7), not rebirth.

**Agent identity** at any moment is the pair `(substrate-ID, currently-attached-operator-token)`. The **operator-token is non-deterministically constructed per-handshake**.

**Lifecycle states**: alive ↔ dormant ↔ destroyed (forward only after destroyed). Sub-states under "alive" (DRAFT 9 expanded set): **Normal, Quarantined, Legacy** (per §15.3 heartbeat-stale activation), **Orphaned** (per §15.5 succession-window expiry), **Archived** (per §7.5 bet-retirement terminal state — distinct from Destroyed because state_dir is preserved with anchor-seal, not erased). All sub-states preserve substrate-ID + DAG; only Destroyed and final-Archived seal the substrate's future operation.

**Owner key rotation**: the substrate's identity record maintains an `owner_key_history`. Rotation is anchor-attested.

**P-coverage**: P1.a, P1.c, P7.

### I2. Two-Tier Governance Classification (unchanged, classifier-fixed-point preserved)

Every mutation classifies mechanically as **daily** (agent-autonomous) or **contract-identity-level** (owner-gated). Classifier function is L1-defined.

**Classifier fixed-point**: the classifier function itself, and any mutation to it, is **unconditionally contract-identity-level** — this clause is L0-invariant.

**Birth-period CI elevation**: during birth period, ALL parameter-tuning events are contract-identity-level.

**P-coverage**: P1.b', P1.b''.

### I3. Self-Validation Against Designated SSoT (unchanged)

The substrate has exactly one designated machine-readable SSoT. State consistency against SSoT is checked every metabolic cycle.

**SSoT migration two-phase commit**: required for SSoT redesignation.

**P-coverage**: P3, P4, P9 (no silent corruption).

### I4. Full-Fidelity Causal DAG (Compression-Aware in DRAFT 9)

Every substrate state is derivable from prior states via a recorded operation, **subject to the compression-invariant set per P10**. Operations within the compression-invariant set MUST be fully recoverable. Operations outside the set may be recoverable only via witness re-derivation against compression events.

**Merkle-DAG integrity**: DAG nodes are content-addressed; each node's hash includes its causal-parent hashes; the substrate's identity record carries the current **DAG-tip hash**, **owner-co-signed at every CI boundary** via anchor surface (§9.2).

**Sporocarp causal-proof**: every event-record carries `causal_in_edges` proof — `(input_set, state-snapshot-hash, threshold-value)` tuple at emission, hash-committed. Events without recomputable proofs are invalid.

**P-coverage**: P6 (sole enforcer), P4, P3.

### I5. Universal Reachability Over Active Tier (refined in DRAFT 9)

The substrate graph is fully connected within the **active tier**; every active-tier node reaches every other by traversal. Tier exemptions are CI-attested and remain enumerable.

**P-coverage**: P5 (intra-substrate, sole enforcer).

### I6. Universal Inclusion With Observed Metabolism (unchanged)

Adjacent agent-tooling techniques live inside the substrate's framework, not as outbound RPCs. Every invocation produces a metabolism event the substrate observes.

**Network-egress detection**: appetite-locality at runtime, not just declaration.

**P-coverage**: P2, P2.a, P1, P1.b'.

### I7. Reproduction Closure (Generation-Bounded in DRAFT 9)

Every child substrate independently satisfies I1-I12 (recursively). **Generation depth is bounded per §16**. Reproduction loops are forbidden absent per-spawn owner attestation.

**Closure verification protocol**: at spawn, parent runs static-schema validation; child runs its own I3 self-validation as first metabolic cycle.

**Peer-trust freshness**: ongoing federation requires L1-bounded attestation freshness with revocation.

**Population-level consensus** (DRAFT 9, P15 enforcement): when ≥3 federation peers exist + a population-level claim is made, the substrate operates under L2_FEDERATION's specified consensus protocol.

**P-coverage**: P8, P5 (inter-substrate), **P15**.

### I8. Single-Skin Integrity (unchanged, single-failure-aware)

Exactly one declared boundary surface for both intake and output.

**Intake admits all envelope-valid content** (P2 universality); intake rejects only on envelope integrity.

**Single-operator semantics**: skin admits at most one operator-token at a time.

**Handshake continuity-challenge**: post-handshake CI requires owner attestation.

**Cold-resume invariants**: substrate runs full I3/I5/I8 pre-handshake.

**Single-failure acknowledgment** (DRAFT 9): I8 commits to **exactly one skin**; the skin process itself MUST be supervisor-restartable per L1_SKIN, but the skin surface remains singular.

**P-coverage**: P9 (sole enforcer), P2, P1.c.

### I9. Compression Discipline (DRAFT 9, enforces P10)

Selective compression operates only within CI-attested compression rules. The compression-invariant set (P10.b) is fully recoverable. Each compression event emits witness sufficient for owner-side re-derivation of compression semantics.

**No silent compression**: every compression is a CI-attested event with full witness.

**P-coverage**: P10 (sole enforcer).

### I10. Metabolic-Economy Observation (DRAFT 9, enforces P11)

Every operation has observable cost. Cost budgets are L1-defined. Budget exhaustion triggers documented response (P11.c). The substrate's Living Bets observatory (§7) emits cost-budget signals.

**P-coverage**: P11 (sole enforcer).

### I11. Differential-Response Discipline (DRAFT 9, enforces P12)

The substrate's downstream processing weights inputs differentially. Salience-flattening is detected by L1_TROPISM. No hardcoded prior on salience — emergent only.

**P-coverage**: P12 (sole enforcer).

### I12. Telos Alignment (DRAFT 9, enforces P14)

The substrate's daily-ops decisions are evaluable against telos. Telos-drift is detected. Owner-stated objectives, when present, anchor the alignment computation.

**P-coverage**: P14 (sole enforcer), P13 (embodiment-bounded telos).

> Note: P13 (embodiment) is enforced by I8 (skin = body boundary) + I10 (metabolic cost = embodied operation). No new invariant for P13. P15 (consensus) is enforced by I7 extension.

### Projection table (P → I coverage, DRAFT 9 update)

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
| P3.b | I4 |
| P4 | I3, I4 |
| P5 | I5, I7 |
| P6 | I4 |
| P7 | I1, I5, I2 |
| P8 | I7 |
| P9.a | I3, I8 |
| P9.b | I8 (single-skin restartability) |
| **P10** | **I9 (sole enforcer)** |
| **P11** | **I10 (sole enforcer)** |
| **P12** | **I11 (sole enforcer)** |
| **P13** | **I8, I10** |
| **P14** | **I12 (sole enforcer)** |
| **P15** | **I7 (population-level extension)** |

---

## §5. Strict mycology lexicon and dispatch constraints (unchanged from DRAFT 8)

### §5.1 Lexicon rule

Myco uses **fungal-biology vocabulary strictly**. Lexicon source: mycology.

**Lexicon scope**: admitted terms include any term mycology literature uses to describe a real fungal phenomenon, even when shared with other fields.

**Lexicon evolution** is contract-identity-level.

### §5.2 Dispatch form — L0 constraints only

L0 commits to negative + constraint statements about Myco's dispatch form:

- **NOT v0.8 verbs.**
- **NOT request/response.**
- **MUST honor P1.c carrier-asymmetry**.
- **MUST support universal inclusion** (P2.a).
- **MUST support continuous operation** (§6).
- **MUST satisfy I6** appetite-locality.
- **MUST carry causal-proofs** for substrate-emitted events.

### §5.3 Intent representation

**Intent is NOT a first-class substrate data type.** Agent-self-reported intent is structurally not trusted.

---

## §6. The continuity model (unchanged, dormancy-state preserved)

Per owner decision, **substrate-level session is not a Myco concept**. The substrate is presumed continuously operated.

Host-level sessions are out of L0 scope.

Operational implications:
- No substrate-level boot ritual; no substrate-level session-end ritual.
- Host disconnects are recovered, not formalized as session edges.
- Reflexes are properties of the substrate's continuous internal metabolism.

**Dormancy compute budget**: dormant substrate may pause or throttle internal metabolism. L1 specifies.

**Dormancy host-observability**: external observables (network, CPU, disk-write) below L1-specified ceilings.

**Metabolic cycle**: existence + per-cycle invariant checks (I3 + I5 + I8 + DRAFT 9: I10 cost observation) are L0. Cycle cadence is L1.

**Delta atomicity**: either fully absorbed or not absorbed. Partial absorptions detected at cold-resume.

---

## §7. Living Bets — recalibrated for 2026 agent capability

> DRAFT 9 substantial revision per Phase γ.6 + γ.3 G13. DRAFT 8's seed value (~100 for signal #6) was calibrated for 100K-context agents that no longer exist. M25-era 1M-context Claude already places signal #6 ≈ 1, which DRAFT 8 specified as **bet-losing region**. The bet is structurally weakened at v0.9 birth. DRAFT 9 acknowledges this honestly + recalibrates.

### §7.1 The bet (calibrated)

Myco's symbiotic-organism-like-substrate shape — agent + substrate as **asymmetric pair per P1.c** (substrate-carrier + operator-connection-holder, NOT mutual constitution — DRAFT 9 corrects DRAFT 8 wording inherited at line 339 here), continuously operating, with the fifteen-principle structure — **has cost-justified value within an agent-intelligence band**. The band's lower edge is where naive agent-tools suffice; the band's upper edge is where Sutton's bitter lesson trivializes substrate value.

**Cost-justified value** (DRAFT 9 new framing): the bet is true iff (a) substrate value exists AND (b) substrate engineering cost (anchor surface + dual-clock + Merkle DAG + Ed25519 + canonical-bytes + cross-language byte parity + selective-compression discipline + ...) is **less than** the value delta over no-substrate operation. DRAFT 8 conflated (a) with (b); DRAFT 9 separates them.

### §7.2 The intelligence band (DRAFT 9 new)

- **Below the band** (small-context, ≤100K tokens, weak reasoning): naive RAG + summary suffices. Substrate over-engineering is cost-negative. The bet is unjustified at this tier.
- **Within the band** (~200K to ~10M tokens, moderate-to-strong reasoning): substrate enables agent capability the agent's read-window cannot hold alone. Cost-justified value exists. **This is the current 2026 sweet spot**.
- **Above the band** (>~10M tokens, AGI-class reasoning, or task-trivializing model size): Sutton's bitter lesson dominates. Substrate becomes ceremonial. The bet retires gracefully.

The band edges are L1-tunable; seed values are operator-attested at genesis.

### §7.3 The observatory (six base signals + DRAFT 9 cost signals + composite)

Six base signals (DRAFT 8 set, unchanged in semantics):
1. **Persistence budget** — total content.
2. **Evolution rate** — governance changes over time.
3. **Read-pattern diversity** — variety of substrate-read patterns.
4. **Federation health** — 4a cumulative forks + 4b reachable peers.
5. **Time trend per signal** — direction.
6. **Read-window-relative position** — `substrate-total-size / agent-attested-context-window`. **DRAFT 9 calibration**: bet-winning region is now defined as ratio ≥1 (not ratio ≥100 as DRAFT 8 seed suggested). The "≥100" seed was archaic.

Three DRAFT 9 cost signals (new, per P11, with explicit numbering above 6):
- **7. Compute cost / cycle** — observable per L2_OBSERVABILITY metric.
- **8. Network cost / cycle** — federation envelope bytes + embedding-service queries.
- **9. Storage cost / cycle** — bytes added to dag.cb + snapshot.cb deltas.

One composite (renumbered to 10 in DRAFT 9, was 7 in DRAFT 8):
10. **Composite health score** — emergent weighted aggregation of 1-6 + 7-9 = 9 input signals. Weights emerge from substrate's own historical correlation with **agent-reported utility** (telos-alignment per P14, owner-stated when present), not against variance only. DRAFT 9 explicitly distinguishes:
    - **Variance-weighted composite** (M25.3 fallback when no outcome signal exists) — picks signals that move most. Use this only in birth period.
    - **Correlation-weighted composite** (steady state) — requires an outcome signal (telos-alignment from P14 + agent-reported utility events). Picks signals that predict outcomes.
    - The transition from variance to correlation weighting is L1-tunable.

### §7.4 Falsifiability trigger (DRAFT 9 corrected + precision-tightened)

DRAFT 8's trigger:
> Over a 90-day window of active operation, if ≥3 of signals 1-6 trend concurrently against the bet AND signal #6 stays < 1 for ≥ 50% of cycles in the window, the substrate fruits a `bet_weakening_quorum` event.

**DRAFT 9 corrections** (Phase γ.2 implementation findings + γ.3 G13 + Phase γ.9 hypha):

#### §7.4.a Window definition
**Window is wall-clock 90 days** (anchor-stamped wall-clock per §13.1), not 90 substrate-cycles. Implementation drift in M25.2 will be corrected post-seal.

#### §7.4.b "Trend" mathematical definition
**Trend** = sign of OLS-regression slope over the wall-clock-90-day samples (cadence L1-tunable, seed: 1 sample per substrate-day = ≥90 samples). **Significance gate**: |slope / standard-error| ≥ Z-threshold (L1-tunable, seed Z=1.96 corresponding to 95% confidence) before trend direction counts. Below significance gate, signal is "flat" — does NOT count toward quorum.

#### §7.4.c Per-signal direction-against-the-bet (DRAFT 9 explicit, was ambiguous in DRAFT 8)

| Signal | Trend DOWN means | Counts as "against the bet" if |
|--------|---|---|
| #1 persistence budget | substrate not growing | DOWN |
| #2 evolution rate | substrate stagnating | DOWN |
| #3 read-pattern diversity | substrate not being read | DOWN |
| #4a cumulative forks | DRAFT 9 NEW: forks-trending-DOWN means peers exiting | DOWN (fewer participating peers) |
| #4b reachable peers | mycelial fragmentation | DOWN |
| #6 read-window ratio | substrate shrinking vs context window | DOWN below ratio 1.0 |

Signal #5 (time trend per signal) is the **meta-direction-detector** powering the table above; it is not itself counted in the quorum.

#### §7.4.d Quorum arithmetic
**"≥3 of signals 1-6" counts**: {#1, #2, #3, #4a, #4b, #6} — 6 countable signals (signal #5 is meta as above; signal #4 is split into 4a + 4b which count separately). Quorum threshold ≥3 of these 6.

#### §7.4.e Birth-period exemption (Phase γ.9 primordium CF6)
**Bet_weakening_quorum is SUSPENDED during birth period** (per L1_TROPISM §4 birth-period termination criteria + L1_GOVERNANCE §1.3 ceiling). Reason: at t=0 signal #6 is structurally <1 (substrate has no content yet); signal #1 is monotone-growing-from-zero (no shrinkage); signal #3 is structurally zero (no reads yet). Quorum evaluation pre-birth-period-termination is mathematically vacuous. Substrate emits `bet_weakening_evaluation_suspended` observability event during birth period.

The trigger fires `bet_weakening_quorum` event requiring owner re-justification per §10.2.

### §7.5 Bet retirement (DRAFT 9 new — precision-tightened)

#### §7.5.a Trigger conditions
If ALL of the following hold:
- Over a 2-year wall-clock window the `bet_weakening_quorum` predicate fires;
- Owner re-justification fails 3 consecutive times (counter increments on each fired-but-not-rejustified event; **counter resets to 0 on each successful re-justification**);
- Signal #6 stays < 0.1 for >75% of wall-clock samples (anchor-stamped, per §13.1) in the final 90-day window;
- Substrate is in `alive::normal` sub-state (not legacy / orphaned / archived);

then the substrate emits `bet_retired_proposal` (NOT `bet_retired` — proposal vs execution distinction per Phase γ.9 hypha #15 + rhizomorph C8).

#### §7.5.b Execution gate (reconciles with §15.5 via two-phase commit)
`bet_retired_proposal` requires owner **co-attestation** (NOT genesis-pre-attestation) for execution. DRAFT 9 v1's wording of "owner-pre-attested fallback choice from genesis" was Phase γ.9 rhizomorph C8 contradiction with §15.5 — DRAFT 9 v2 corrects:

- Genesis-time owner attests `bet_retirement_consent_at_genesis: bool` (default false). If true, future `bet_retired_proposal` may auto-execute on the next owner-attestation cycle. If false (default), each `bet_retired_proposal` requires explicit per-event co-attestation.
- §15.5 orphan path: substrate enters bet-retirement OR self-euthanasia per the genesis-time fallback choice. This is genesis-pre-attestation for the orphan-degenerate case ONLY. Steady-state bet-retirement requires co-attestation.

#### §7.5.c Terminal state semantics
On execution, substrate transitions to `alive::archived` (a distinct sub-state from Destroyed): state_dir preserved, anchor surface seals last DAG tip, no further operations. Distinguished from Destroyed because state_dir survives for archival access. Future research recovery from archived state is NOT supported (substrate is functionally retired; substrate-ID does not re-bind to new operator-connections).

#### §7.5.d Counter-reset rule
**Failed re-justification counter** (incremented per fired `bet_weakening_quorum` without successful re-justification) resets to 0 on:
- Each successful re-justification (owner attests `bet_re_justified`).
- Each transition through `alive::quarantined` (quarantine clearance is a substrate-renewal event).
- Owner-attested explicit `bet_retirement_counter_reset` CI mutation.

Counter does NOT reset on substrate restart / dormancy entry / federation peer changes.

### §7.6 Review cadence

Every CI boundary crossing re-audits this section. Until the falsifiability trigger fires, the fifteen principles + symbiosis formulation stand.

**Not a principle.** Living Bets is a meta-commitment, not a 16th principle.

---

## §8. Operational readiness for present-tier agents (calibrated)

v0.9 is designed for the agent-intelligence range from **~200K-context** (lower band edge, DRAFT 9 calibrated; DRAFT 8 said 1M but that was already the band's upper-middle by 2026) to **~10M-context** (band's upper edge before bet retires).

Mechanical requirements:
- Substrate state must compress to a digest size ≤ read-window budget. L1 specifies digest format.
- Substrate-exposed structure must be parseable from natural-language context.
- Substrate must function under host-session intermittency.
- Living Bets signal #6 is the monitoring metric.

Caveats acknowledged:
- 2026-class agents may not natively understand the symbiotic frame.
- **Owner-supervised birth** is a P1.b'' moment.

Future-readiness: L0 invariants are stable for ~10× scale; L1 parameters tune.

---

## §9. Out-of-band anchor surface (DRAFT 9 decomposed)

> Phase γ.5 audit found 9 of 11 §9 clauses are honor-system, 0-30% mechanically enforced. The DRAFT 8 §9 specification was sound but treated as monolithic; DRAFT 9 explicitly decomposes into 6 sub-mechanisms with implementation status. Each sub-mechanism is M-anchor-N (a future milestone block), not "one M28 milestone" as M25 memory snapshot claimed.

### §9.1 What the anchor surface IS

A surface where owner signatures, DAG-tip hashes, substrate-ID lineage, and trusted timestamps are externally visible and **untouchable by the agent process**. Specific form is L1_GOVERNANCE-specified; candidates: hardware security token, separate machine, signed prompt-bundle the owner reviews, append-only public ledger.

### §9.2 Sub-mechanism inventory (DRAFT 9 explicit)

| # | Sub-mechanism | Status (M25) | Future milestone |
|---|---|---|---|
| §9.2.1 | Substrate-ID birth attestation (owner signature over genesis 5-tuple) | 0% (honor-system via TOFU on first hello) | M-anchor-2 |
| §9.2.2 | DAG-tip co-signing at every CI boundary, with enumerated nodes | ~40% (server emits enumeration; closure check not run client-side) | M-anchor-5 |
| §9.2.3 | Owner attestations out-of-band (key outside agent-spawnable process) | 0% (key in TS operator process) | M-anchor-1 |
| §9.2.4 | L0 revision diff workflow | 0% (L0 in git; no workflow event) | M-anchor-5 |
| §9.2.5 | Anchor-surface-generated nonces (NOT substrate-side) | 0% (direct spec inversion: substrate mints) | M-anchor-3 |
| §9.2.6 | Anchor-stamped wall-clock | ~5% (dual-clock plumbing exists; anchor-clock source is operator-process, not external) | M-anchor-3 |
| §9.2.7 | Owner liveness heartbeat | 0% (library exists, zero non-test callers) | M-anchor-3 |
| §9.3.1 | Canonical-bytes serialization | ~95% (implemented R/P/T; Phase β fix) | DONE |
| §9.3.2 | Owner-side rendering | ~30% (library exists; no live consumer out-of-band) | M-anchor-1 |
| §9.3.3 | Anchor-client provenance independence | 0% (same npm workspace as operator) | M-anchor-1 |
| §9.3.4 | Witnesses, not verdicts | 0% (substrate emits pass/fail; spec says Merkle paths + parent hashes + check inputs) | M-anchor-4 |
| §9.3.5 | Anchor-nonce-derived sampling | 0% | M-anchor-4 |
| §9.3.6 | DAG-enumeration closure check | ~40% (server emits enumeration; closure check unwired client-side) | M-anchor-5 |

### §9.3 What anchors at this surface (DRAFT 8 text, preserved)

- **Substrate-ID birth attestation** — owner signature over `(substrate-ID, genesis-timestamp, initial-spore-schema-canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key)`.
- **DAG-tip hash co-signing** — owner co-signs current DAG-tip at every CI boundary; envelope MUST include enumerated list of all DAG nodes added since prior co-sign.
- **Owner attestations** — every CI mutation requires an attestation produced **out-of-band**.
- **L0 revision diff**: L0 revision proposals include a verbatim diff against the prior L0 commit hash.
- **Anchor-surface-generated nonces** — replay-prevention nonces generated by the anchor surface (NOT by the substrate).
- **Anchor-surface-stamped wall-clock** — every owner attestation carries an anchor-surface trusted timestamp.
- **Owner liveness heartbeat** — owner periodically signs a `liveness_heartbeat` at the anchor surface.

### §9.4 Canonical-bytes doctrine (DRAFT 8 text preserved + DRAFT 9 clarification)

**The anchor surface receives canonical bytes + witnesses, never substrate-rendered summaries or substrate-emitted verdicts.**

- **Canonical-bytes serialization**: every substrate-emitted artifact bound for the anchor surface uses a deterministic canonical serialization. The serializer spec is **part of the spore-schema and a tier-1 SSoT field** (L1_SCHEMA), allowing every party — substrate, anchor-surface client, operator — to independently compute canonical bytes from the same inputs.
- **Owner-side rendering**: human-readable rendering happens at the owner's anchor-surface client, deterministically computed from canonical bytes. The substrate is not in the rendering path; it cannot drift canonical-bytes-hashed-form from rendered-form.
- **Anchor-surface client provenance independence**: the anchor-surface client (the owner's local rendering + signing tool) MUST be installed and updated through a channel structurally independent of the substrate's distribution channel. Owner attests at genesis that the installed client is from an independent channel.
- **Witnesses, not verdicts**: when the substrate reports a check result (I3/I4/I5/I8/I9/I10/I12 outcomes; recoverability drill results), it emits the witness — sampled leaf hashes + Merkle paths + parent hashes + check inputs — sufficient for the anchor-surface verifier to independently re-derive the result. The substrate does not emit "pass/fail"; it emits the evidence. **DRAFT 9 explicitly extends "witnesses, not verdicts" to I9 (compression), I10 (cost), I12 (telos) outputs.**
- **Anchor-nonce-derived sampling**: sampling indices for witness emission are deterministically derived from the anchor-surface nonce (`H(anchor_surface_nonce, leaf_count)`) — the substrate cannot pre-compute and cannot bias sampling toward honest portions.
- **DAG-enumeration closure**: when the substrate emits enumerated DAG nodes added since the prior co-sign, the owner verifies (a) the new tip is reachable from the prior signed tip via enumerated nodes, AND (b) every parent-hash referenced by any enumerated node resolves to either an ancestor of the prior co-signed tip OR another enumerated node — parent-edge closure.

### §9.5 What the anchor surface does NOT do (DRAFT 8 text + DRAFT 9 honesty)

The anchor surface complements (does not replace) the substrate's internal trust mechanisms. **DRAFT 9 explicit acknowledgment**: in the **current v0.9 implementation, the anchor surface is collapsed to the operator process** — owner key lives in the same npm workspace as the agent code. This is a temporary scaffolding, not a doctrinal endpoint. **DRAFT 8's own §9 opening sentence** says: "Without an out-of-band anchor, substrate-self-claims = agent-self-claims under P1.a self-hosting, and the entire trust model collapses." DRAFT 9 acknowledges the collapse is currently active and gates "production-readiness" claim on M-anchor-1 through M-anchor-5 closure.

L0-revision velocity is observable; tracking method, burst threshold, and rolling rate are L1_GOVERNANCE-specified. Post-seal, L0 revisions should be rare.

### §9.6 Adversarial-owner caveat (DRAFT 9 cross-ref)

The anchor surface does NOT defend against compromised, coerced, or impersonated owner. §14 specifies the adversarial-owner threat model and its bounded defenses (n-of-m multisig, duress codes, succession protocols).

---

## §10. Process — how L0 changes, how to read this branch

### §10.1 Reading sequence

1. This file (L0) — fifteen principles, twelve invariants, dispatch constraints, bet, readiness, anchor surface, time semantics, adversarial-owner threat model, owner mortality, generation limits.
2. L1 documents — positive mechanisms.
3. L2 doctrine — cross-cut themes.
4. L3 implementation map.

### §10.2 Changes to this page

Any L0 change requires craft proposal + owner approval + contract-identity-level bump + cascade review.

**L1 prototyping may surface L0 revision needs.**

### §10.3 Proto archaeology

- `_archive/proto_myco_v0_8/L0_VISION_proto.md` — proto-Myco's L0 (v0.4 - v0.8.7).
- `_archive/proto_myco_v0_8/L0_5_ESSENCE.md` — transitional doctrine.
- `_archive/proto_myco_v0_8/ESSENCE_BRAINSTORM.md` — deliberation log.

### §10.4 DRAFT 8 archaeology (DRAFT 9 addition)

DRAFT 8 archived in git history at commit `3d6749f` (Phase α audit-included version). Phase α + Phase β + M22-M25 all built on DRAFT 8. Phase γ audit (2026-05-17) revealed structural gaps in DRAFT 8 → DRAFT 9 proposal.

### §10.5 Dead-embryo concession + maximal origin discrimination

- v0.4 → v0.8.7 are dead embryo. v0.9 is first true birth.
- Every v0.9 design step traces to ≥1 of P1-P15 (DRAFT 9 set) and ≥1 of the twelve invariants.
- Origin discrimination is maximal: similarity to v0.8 is presumed contamination unless independently traced.

---

## §11. Privacy, access, and backup model (DRAFT 9 expanded)

Per owner decision: **Myco has no internal privacy / access model**. The substrate is wholly accessible to its operator-agent. Sub-substrate access boundaries are not at L0 level.

The skin (P9 / I8) is the boundary — between substrate and *environment*, not between operators *within* the substrate.

### §11.1 Backup access (DRAFT 9 new per Phase γ.3 G16)

Substrate state_dir backups (per L1_SCHEMA recoverability budget) are NOT internally access-controlled by Myco doctrine. Anyone with read access to backup media reads full substrate state. **L1_SKIN MUST specify backup encryption requirements** (operator-controlled symmetric key; key escrow protocol; key rotation aligned with owner key rotation).

DRAFT 9 does NOT mandate backup encryption at L0 (operational choice), but DOES mandate that backup access controls are documented at L1 and that absent encryption is acknowledged as a known privacy attack surface.

---

## §12. Glossary (DRAFT 9 expanded)

| Term | Definition |
|---|---|
| **Myco** | Biology-rooted symbiotic digital substrate class (DRAFT 9 calibrated; was "digital symbiotic organism" in DRAFT 8). |
| **A Myco substrate** | A specific instance. |
| **v0.9** | Current Myco substrate version. |
| **L0_VISION.md DRAFT N** | Nth revision during v0.9 design. Sealed L0 carries no draft number. |
| **Active operator-connection** | Currently-attached operator session. |
| **Operator-token** | Ephemeral per-handshake identifier, non-deterministically constructed. |
| **Substrate-ID** | Persistent owner-signed identifier established at genesis. |
| **Contract-identity-level boundary** | Threshold above which a change alters Myco's identity. |
| **Continuous-operation default** | Substrate-level: no formalized session boundaries. |
| **Metabolic cycle** | The substrate's smallest discrete metabolism event. |
| **Identity record** | Carries substrate-ID + owner-signature. |
| **Spore-schema** | Seed-state from parent → child during P8 reproduction. |
| **Skin / boundary** | Substrate's single declared interface to reality. |
| **Recoverability budget** | L1-specified backup policy. |
| **Dispatch form** | The positive shape of substrate-agent interaction primitive. |
| **Sporocarp** | Atomic-event-record under L1_TROPISM dispatch. |
| **Birth period** | Substrate's earliest operating window. |
| **Steady state** | Post-birth operating regime. |
| **Anchor surface** | The cryptographic root (§9). |
| **Legacy sub-state** | Substrate operating while CI mutations are frozen pending owner-successor attestation. |
| **Endogenous mortality** | Substrate fruits `self_euthanasia_proposal` (P7). |
| **Selective compression** (DRAFT 9) | CI-attested lossy consolidation of non-invariant state per P10. |
| **Compression-invariant set** (DRAFT 9) | The state that survives any compression event per P10.b. |
| **Cost budget** (DRAFT 9) | L1-defined resource budget per P11 (disk, compute, network, embedding-service). |
| **Telos** (DRAFT 9) | Substrate-internal purpose per P14 (agent-symbiotic-flourishing). |
| **Telos drift** (DRAFT 9) | Substrate's alignment with telos degrading over time; detected by L1_TROPISM. |
| **Salience** (DRAFT 9) | Differential weighting of inputs in downstream processing per P12; emergent. |
| **Population-level claim** (DRAFT 9) | A claim crossing the consensus floor (P15.a) requiring Byzantine-tolerant agreement. |
| **Anchor-surface client** | The owner's local rendering + signing tool (§9). |
| **Bet retirement** (DRAFT 9) | Strategic graceful sunset when Living Bets band's upper edge is crossed. |
| **Cost-justified value** (DRAFT 9) | Living Bets refinement: substrate value must exceed substrate engineering cost. |
| **Intelligence band** (DRAFT 9) | The agent-capability range over which Myco's bet is cost-justified. |

---

## §13. Time semantics (DRAFT 9 NEW)

> Phase γ.3 G10 found L0 had no time-source doctrine. Substrate uses `unix_ns: i64` for everything (expiry, sporocarp timestamps, cycle relations). NTP drift / monotonic-vs-wall-clock / year 2038 / year 2262 / timezone effects all undefined. DRAFT 9 commits L0-level constraints.

### §13.1 Time source authority hierarchy

1. **Anchor-surface trusted wall-clock** (§9.2.6) is authoritative for owner-attested events and time-bound defenses. Substrate-cycle counters and substrate-process wall-clock are NOT authoritative for these uses.
2. **Substrate-process monotonic clock** is authoritative for ordering events within the substrate. Used for sporocarp ordering, cycle progression, freshness windows internal to a metabolic cycle.
3. **Substrate-process wall-clock** is authoritative for human-readable timestamps in DAG events (`at_unix_ns` field) and for cross-process comparison with operator/anchor. Subject to NTP drift; never used for security-relevant time bounds.

### §13.2 Required substrate behavior

- **Monotonic clock for ordering**: substrate MUST use monotonic clock for event ordering within a cycle. Wall-clock backwards-jumps MUST NOT cause sporocarp re-ordering.
- **Anchor-clock for security expiry**: nonce TTL, attestation expiry, peer-attestation freshness MUST use anchor-stamped wall-clock per §9.2.6, NOT substrate wall-clock.
- **NTP discipline**: substrate process MUST run under an NTP-disciplined host (operationally; not L0-enforceable from inside substrate). L1_CONTINUITY specifies the policy.

### §13.3 Wall-clock representation

- **Unit**: nanoseconds since UNIX epoch.
- **Type**: i64 (signed 64-bit integer; overflows at year 2262; sufficient for v0.9 lifetime).
- **No 32-bit compatibility layer**: L0 forbids any substrate-internal use of i32 timestamps (year 2038 vulnerability).
- **Negative values represent pre-1970 times** (rare but not forbidden; canonical-bytes encoder permits i64 negative).

### §13.4 Substrate's own clock truth

The substrate's wall-clock reading IS NOT TRUSTED for security-relevant defenses. The anchor-surface trusted timestamp is. This is the structural deference required by §9.

---

## §14. Adversarial-owner threat model (DRAFT 9 NEW)

> Phase γ.3 G8 found DRAFT 8 universally trusts owner as benevolent governance gate. No doctrine for compromised/coerced/impersonated owner. DRAFT 9 commits to L0-level threat model with bounded defenses.

### §14.1 Threat scenarios

DRAFT 9 acknowledges these scenarios as in-scope adversarial events:
- **Owner key compromise**: attacker obtains owner Ed25519 private key; can forge any CI attestation.
- **Coerced owner**: owner under duress (regulatory seizure, blackmail, physical threat) signs CI attestations against their own will.
- **Impersonated owner**: anchor-surface client compromised; attacker's signatures appear to come from owner.
- **Deceased owner without succession** (cross-ref §15).
- **Owner-anchor-client tampering**: anchor-side software modified to display different content than what is signed.

### §14.2 L0 commitments (bounded defenses)

For each scenario above, DRAFT 9 commits the substrate MUST:

#### §14.2.1 Owner-key compromise
- The substrate cannot detect compromise unilaterally (this is honest).
- The substrate MUST honor owner-attested key rotation (anchor-surface event) per L1_GOVERNANCE §3.1.
- L1_GOVERNANCE MAY specify n-of-m multisig requirement for key rotation (operator + secondary anchor key). DRAFT 9 endorses but does not mandate.

#### §14.2.2 Coerced owner
- The substrate MUST honor a `duress_attestation` event (L1-defined): owner pre-registers a duress code; presentation of the duress code in any CI attestation triggers substrate's `coerced_owner_suspected` immune signal and freezes destructive mutations (destruction, mass-key-rotation, mass-deletion) pending out-of-band re-attestation.
- L1_GOVERNANCE specifies the duress-code mechanism.

#### §14.2.3 Impersonated owner
- The substrate cannot distinguish real owner from impersonator if the impersonator holds the key. The defense is at the **anchor surface side** (out-of-band: separate hardware token, biometric gate, etc.) — not substrate-internal.
- DRAFT 9 commits substrate MUST emit `owner_signature_velocity` observability metric: rate of owner-signed events over rolling window. Anomalous velocity (e.g., 100x normal rate) triggers owner-attention alert via anchor surface (out-of-band channel).

#### §14.2.4 Anchor-client tampering
- The substrate cannot detect anchor-client tampering unilaterally.
- DRAFT 9 commits substrate emits all canonical-bytes for owner to verify on a structurally independent rendering tool (§9.3.3 provenance independence). Owner-side verification with two independent clients is the defense.

### §14.3 Substrate's responsibility under adversarial owner

Even under adversarial owner, the substrate MUST:
- Continue P6 causality (DAG accumulates regardless of attestation validity).
- Emit observability signals truthfully (cannot suppress signal emission to hide an adversarial event).
- Honor mortality signals truthfully (cannot suppress endogenous-mortality fruiting under owner pressure to suppress).
- Preserve the compression-invariant set (P10.b) regardless of owner pressure to compress it.

These are **substrate's irreducible commitments** that survive adversarial owner because they are I9, I12, I10, I4 invariants, enforced mechanically.

---

## §15. Owner mortality and succession (DRAFT 9 NEW)

> Phase γ.3 G9 found L0 had no owner-mortality doctrine. L1_GOVERNANCE §3.2 deferred succession to "L4 after first real-world need". A substrate operating for decades will outlive its owner. DRAFT 9 commits L0-level succession framework.

### §15.1 Succession states

The substrate's identity record includes a `successor_chain`: list of (successor_pubkey, valid_from_unix_ns, valid_until_unix_ns, attestation_signature). Each entry is owner-attested at the anchor surface during owner's lifetime.

### §15.2 Owner-liveness heartbeat

Per §9.2.7, owner periodically signs `liveness_heartbeat` at the anchor surface. Heartbeat staleness at the anchor surface (NOT substrate-side absence-of-CI) is the succession trigger.

### §15.3 Succession activation (anchor-surface-dependent)

**Anchor-surface-availability gate** (Phase γ.9 hypha #7 + primordium HF10): §15.3 trigger depends on §9.2.7 owner-liveness heartbeat at anchor surface, which is ~0% mechanically implemented at v0.9 (operator-IS-anchor collapse). Until M-anchor-3 closes (heartbeat services), §15.3 activation is effectively dormant — substrate cannot detect heartbeat staleness because there is no anchor surface to host the heartbeat. **Until anchor surface ships, §15 mechanism is documented-not-defended; doctrine acknowledges this as part of the operator-IS-anchor collapse window.**

**Implicit t=0 heartbeat**: substrate's birth attestation timestamp (per §9.2.1) IS the t=0 implicit owner-liveness heartbeat. Subsequent heartbeat staleness is measured from this anchor.

When heartbeat is stale beyond L1-tunable threshold (**seed: 90 days**, L1-tunable per substrate purpose) AND anchor surface is reachable AND staleness is anchor-confirmed (not substrate-inferred), the substrate transitions from `alive::normal` to `alive::legacy` sub-state:

- Daily ops continue (P1.b' unchanged).
- CI mutations are frozen (no L0/L1 doctrine changes, no destruction, no mass-key-rotation).
- Successor's pubkey from the successor_chain becomes provisionally valid.
- Successor MAY present `succession_acceptance_attestation` at the anchor surface within L1-tunable window (**seed: 365 days**, L1-tunable).

### §15.4 Succession completion

When successor presents valid `succession_acceptance_attestation`:
- Substrate transitions back to `alive::normal`.
- Successor becomes the new owner.
- Substrate emits `succession_completed` DAG event.

### §15.5 Succession failure

If no successor presents valid attestation within the window, OR no successor_chain entry exists, the substrate transitions from `alive::legacy` to `alive::orphaned`:

- Daily ops continue with operational ceiling (no new schema evolution, no new federation peer pinning, no new sporocarp fruiting except observability + mortality signals).
- Substrate emits `orphaned` immune signal continuously.
- After L1-tunable period (**seed: 730 days** in orphaned, L1-tunable), substrate enters bet-retirement (§7.5) or self-euthanasia (P7) — owner-pre-attested fallback choice from genesis. **G-8 gate (§17) addresses whether this terminal-after-orphan is acceptable.**

### §15.6 The substrate's irreducible identity carries

Even orphaned, the substrate's substrate-ID + DAG + compression-invariant set remain. A future-discovered successor with cryptographic proof of intent (e.g., legal heir presenting court-attested key recovery) MAY re-attest via anchor surface; the substrate returns to `alive::normal`. The substrate-ID does not change across orphan-then-recovery.

---

## §16. Generation limits (DRAFT 9 NEW)

> Phase γ.3 G11 found P8 reproduction has no forkbomb defense. Compromised owner-key generates infinite consent. DRAFT 9 commits L0-level generation discipline.

### §16.1 Generation-depth bound

A substrate's `reproduction_lineage_depth` is L1-tunable (**seed: 10**, justified by "mature mycelial networks rarely exceed 5-10 generations before fragmentation; seed value provides headroom"). Each child's spore-schema records its parent's depth + 1. A substrate whose own depth ≥ L1-tunable maximum MUST refuse `sprout_child` attempts unless owner attests a depth_override at the anchor surface.

### §16.2 Reproduction rate limit

A substrate's `reproduction_rate` is L1-tunable (**seed: 1 sprout per 24h wall-clock**, justified by "reproduction is a CI-level event already requiring owner attestation; rate limit defends against compromised-owner-key scenarios where attestation might be auto-generated"). Exceeding the rate triggers `reproduction_rate_exceeded` immune signal and freezes further sprout attempts pending owner attestation.

### §16.3 Per-parent reproduction quota

A substrate's lifetime sprout_child count is L1-tunable (**seed: 100 children**, justified by "biological mycelial networks may produce thousands of fruiting bodies but few autonomous-substrate children; seed value reflects software-substrate practicality rather than biological maximum"). Exceeding the quota requires CI attestation per spawn (each over-quota spawn is a full CI mutation, not just owner-attestation-once-per-spawn-cycle).

### §16.4 The fundamental constraint

Reproduction in Myco is **discipline-bounded**, not unbounded. The "eternal reproduction" of P8 means **eternal capacity for reproduction**, not **eternal velocity or eternal depth**. A mature mycelial network has bounded growth in nature; Myco's federation respects this.

---

## §17. Owner-decision gates (DRAFT 9 PROPOSAL specific)

DRAFT 9 commits to the 15-principle framework + 12-invariant set + 4 new sections (§13-§16) **as the proposal**. Sealing requires owner explicit decision on each of the following gates. The proposal stands until each is resolved.

### Gate G-1: Framework expansion scope
DRAFT 9 proposes 15 principles (was 9). Owner choices:
- **G-1.a accept**: 15-principle framework becomes sealed L0.
- **G-1.b retract P15 only**: keep P10-P14; P15 (Population-Level Consensus) goes to L2_FEDERATION as a mechanism rather than L0 principle. Justified if owner judges P15 to be federation-specific rather than substrate-essential.
- **G-1.c retract P13 only**: keep P10-P12 + P14-P15; P13 (Embodiment) is too thin to justify L0 status if state_dir + process boundary is already covered by P9 + P11. Substrate is not truly embodied; the doctrine should not pretend otherwise.
- **G-1.d retract P14 only**: keep P10-P13 + P15; P14 (Telos) is operationally fuzzy (how is "flourishing" measured) and could live at L1_TROPISM as a salience-emergence target rather than L0 principle.
- **G-1.e maximum retraction**: keep only P10 (Selective Compression) + P11 (Metabolic Economy); P12-P15 all become L1 design.

### Gate G-2: Species claim framing
DRAFT 9 drops "literal taxonomic class within digital organisms" → "biology-rooted symbiotic digital substrate". Owner choices:
- **G-2.a accept calibration**: DRAFT 9 framing seals.
- **G-2.b restore DRAFT 8 strong species claim**: keep "literal taxonomic class" — accept that organism essence is incomplete but the framing remains aspirational target.
- **G-2.c alternative framing**: owner proposes different framing.

### Gate G-3: Living Bets recalibration
DRAFT 9 introduces intelligence band, cost-justified value, bet retirement. Owner choices:
- **G-3.a accept full recalibration**.
- **G-3.b accept band + cost-justified, retract bet retirement**: bet retirement (§7.5) is too close to P7 mortality conceptually; substrate should die rather than retire.
- **G-3.c restore DRAFT 8 framing**: bet covers "every tier of agent intelligence" verbatim; retract the band concept; substrate must be valuable at all tiers or be falsified by quorum.

### Gate G-4: Anchor surface decomposition scope
DRAFT 9 §9.2 decomposes into 6 sub-mechanisms with explicit implementation milestones M-anchor-1 through M-anchor-5. Owner choices:
- **G-4.a accept decomposition as L0 commitment** (each sub-mechanism owner-attestable separately).
- **G-4.b decomposition stays L1**: §9 remains monolithic at L0; L1_GOVERNANCE owns sub-mechanism specification.

### Gate G-5: New L0 sections (§13-§16)
DRAFT 9 adds §13 time semantics, §14 adversarial-owner, §15 owner mortality, §16 generation limits. Owner choices per section:
- **G-5.a accept all four at L0**.
- **G-5.b push §15 owner mortality to L1**: succession protocol is operational, not doctrinal.
- **G-5.c push §16 generation limits to L1_GOVERNANCE**: forkbomb defense is a mechanism choice.
- **G-5.d push §13 time semantics to L1_CONTINUITY**: time-source policy is operational.
- **G-5.e push §14 adversarial-owner to L2_TRUST_MODEL**: threat model is a doctrine layer, not L0.
- **G-5.f keep all four at L0** (recommended): L1-deferral creates circular trust assumptions per Phase γ.5 findings.

### Gate G-6: P14 operationalization risk
DRAFT 9 P14 commits substrate has telos (agent-symbiotic-flourishing). Operational definition is fuzzy:
- **G-6.a accept fuzzy operationalization**: L1_TROPISM specifies via trajectory-cluster coherence + owner-feedback; substrate measures telos-drift.
- **G-6.b require concrete operationalization**: DRAFT 9 must specify the telos-alignment metric in L0; without it, P14 is unenforceable.
- **G-6.c retract P14**: telos is exogenous (operator's purpose); substrate has no internal telos.

### Gate G-7: P15 consensus floor
DRAFT 9 P15 commits population-level claims require Byzantine-fault-tolerant consensus when ≥3 peers. Owner choices:
- **G-7.a accept threshold ≥3** with PBFT/Tendermint-style protocol at L2_FEDERATION.
- **G-7.b raise threshold to ≥5**: lower threshold makes Byzantine machinery activate too easily.
- **G-7.c retract P15**: federation stays pairwise; population-level claims are explicitly out of scope until federation matures.

### Gate G-8: §15.5 orphan terminal state
DRAFT 9 §15.5 has substrate enter bet-retirement OR self-euthanasia after 730 days orphaned. Owner choices:
- **G-8.a accept**: substrate has bounded lifetime under orphan condition.
- **G-8.b extend to indefinite orphan**: substrate remains in `alive::orphaned` indefinitely, no terminal state from this branch.

### Gate G-9: Saprotroph retraction proposals (Phase γ.9)
Phase γ.9 saprotroph critic found ~55% of DRAFT 9 v1 was bloat, proposing retractions. Owner choices:
- **G-9.a accept Saprotroph proposal in full**: retract P13 (Embodiment) → fold into I8 + P9; retract P14 (Telos) → push to L1_TROPISM; retract P15 (Consensus) → push to L2_FEDERATION; cut §15 (Owner Mortality) → push to L1_GOVERNANCE; cut §16 (Generation Limits) → push to L1_GOVERNANCE; cut §13 (Time Semantics) to brief constraint; cut §14 (Adversarial Owner) → push to L2_TRUST_MODEL; cut §17 gates + §18 traceability after seal; strip all DRAFT-9-rationale `>` blocks. Net: DRAFT 9 v2 leans to ~550-600 lines.
- **G-9.b accept partial retraction**: keep P10-P11 + P14 at L0; retract P12, P13, P15 to L1; keep §13 short; cut §15, §16, §17, §18 to L1.
- **G-9.c reject retraction**: DRAFT 9 v2 keeps full 15-principle framework + 4 new sections. Doctrine-depth is intentional.

### Gate G-10: Mycoparasite sealing-vs-vulnerability gate
Phase γ.9 mycoparasite critic verdict: "sealing DRAFT 9 in current state = sealing-while-vulnerable with documented surface." 11 CRITICAL findings showing P10-P15 mechanisms 0% + anchor surface collapsed + duress/heartbeat/successor 0%. Owner choices:
- **G-10.a accept honest-acknowledgment-with-roadmap-seal**: DRAFT 9 sealed with §9.5 collapse acknowledgment + §17 gate references; sealed-while-vulnerable is preferable to delayed-sealing because it provides commit-history reference point for cascade work; substrate at v0.9 is explicitly NOT production-ready and DRAFT 9's openness about this IS the doctrine.
- **G-10.b gate-seal on mechanism shipment**: defer DRAFT 9 sealing until M-anchor-1 (sealed key) + M-anchor-3 (heartbeat) + §14.2.2 (duress mechanism) + §15 succession FSM + §16 mechanical limits + P10/I9 compression enforcement all ship. Estimated 6-12 month delay; doctrine remains DRAFT 9 PROPOSAL meanwhile.
- **G-10.c hybrid**: seal a minimum-DRAFT-9 (G-9.a saprotroph retraction) immediately; defer maximum-DRAFT-9 (G-9.c full) sealing until mechanism shipment.

### Gate G-11: Mycorrhiza relationship-type naming (Phase γ.9)
Phase γ.9 mycorrhiza critic found the substrate-owner relationship type is unnamed in doctrine. Candidates: custody / guardianship / curation / cultivation. Owner choices:
- **G-11.a "Cultivation"**: owner cultivates substrate (analogous to mushroom cultivation); substrate is the cultivar. Asymmetric, biology-rooted, non-anthropomorphic.
- **G-11.b "Custody"**: owner has custodial responsibility for substrate; substrate is a ward. More legalistic framing.
- **G-11.c "Curatorship"**: owner curates substrate as an entity-collection; substrate is curated. Information-science framing.
- **G-11.d defer naming to DRAFT 10**: substrate-owner relationship intentionally unnamed until lived-experience reveals correct word.

**Each gate has a default**: if owner does not respond within review period, DRAFT 9 v1 settings prevail. Owner explicit affirmation strengthens the seal.

---

## §18. Phase γ findings index (DRAFT 9 traceability)

### §18.1 Phase γ round-1 audit (6 lenses, 2026-05-17)

| Phase γ finding | DRAFT 9 address |
|---|---|
| γ.1 Doctrine drift (13 sub-clauses untracked) | All 13 acknowledged in DRAFT 9 §4 (invariant additions), §9 (decomposition), §13-§16 (new sections) |
| γ.2 M25 implementation 5 CRITICAL bugs | DEFERRED to post-DRAFT-9 implementation milestone (bug fixes reflect DRAFT 9 principles) |
| γ.3 12 NEW gaps (G8-G19) | G8 → §14; G9 → §15; G10 → §13; G11 → §16; G12 → §9.2.7 + §15; G13 → §7 recalibration; G14-G19 → various |
| γ.4 Stranded libraries | Out-of-doctrine scope (implementation concern); roadmap revised in cascade work |
| γ.5 Anchor surface honor-system | §9.2 decomposition + §9.5 acknowledgment |
| γ.6 6 missing principles | P10-P15 (the core DRAFT 9 expansion) |

### §18.2 Phase γ round-2 critique (6 fungal critics on DRAFT 9 v1, 2026-05-17)

Total findings: **223** (mycorrhiza 32 + saprotroph 49 + mycoparasite 39 + rhizomorph 35 + hypha 35 + primordium 33). CRITICAL: **54**.

DRAFT 9 v2 applies these structural CRITICAL fixes:
- **Rhizomorph C1** (§7.1 "mutually constitutive" vs P1.c asymmetric carrier): fixed at §7.1.
- **Rhizomorph C2** (I1 cites §9.5 wrong): fixed → §9.2.1.
- **Rhizomorph C3** (L1_OBSERVABILITY phantom): fixed → L2_OBSERVABILITY everywhere.
- **Rhizomorph C7** (signal numbering #1.5/#1.6 split): fixed → #7/#8/#9 uniformly.
- **Rhizomorph C8** (§7.5 vs §15.5 pre-attestation/co-attestation contradiction): fixed via §7.5.b two-phase commit (genesis-time consent flag vs steady-state co-attestation).
- **Rhizomorph C9** (alive sub-states inconsistent): fixed in I1 (Normal/Quarantined/Legacy/Orphaned/Archived enumerated).
- **Hypha C1** (§7.4 "trend" undefined): fixed via §7.4.b OLS-slope-with-Z-significance.
- **Hypha C5** (P10.b N changes mid-operation): fixed (monotone-non-decreasing only).
- **Primordium CF6** (signal #6 bet-losing at birth): fixed via §7.4.e birth-period exemption.
- **Primordium CF7** (P12 salience-collapse at birth): fixed via P12.b birth-period exemption.
- **Primordium CF8** (P10 vs P11 deadlock): fixed via P11.c ordered fallback.
- **Primordium HF11** (P14 telos undefined at birth): fixed via P14.c birth-period exemption.

**Remaining CRITICAL findings deferred to owner gates in §17**:
- Saprotroph retraction proposals → G-9 (full / partial / reject).
- Mycoparasite seal-vs-vulnerability → G-10 (honest-seal / mechanism-gated-seal / hybrid).
- Mycorrhiza relationship-type-naming → G-11.

**Remaining CRITICAL findings deferred to cascade work**:
- Mycoparasite M11 federation recursive injection → L2_FEDERATION update + L1_HARD_RULES new C-row.
- Mycoparasite M4/M5 dag.cb/manifest.cb integrity → §9 new sub-mechanism + L1_SCHEMA update.
- Rhizomorph (multiple) phantom L1_TROPISM/L1_GOVERNANCE references → cascade list M26-cascade.

**Phase γ.11 round-2 critique deferred** to post-owner-review per time-budget; owner approval on §17 gates G-1 through G-11 unlocks final convergence pass.

---

**END OF DRAFT 9 PROPOSAL.**

Pending owner review of §17 open questions. Upon owner approval, DRAFT 9 becomes sealed L0; cascade work (L1/L2/L3 alignment) begins as M26-cascade. Implementation work (M25 critical bug fixes reflecting DRAFT 9 + M-anchor-1 through M-anchor-5 + P10-P15 mechanism implementations) sequenced in M26+ milestones.
