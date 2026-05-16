# L0 — Vision

> **Status**: **DRAFT 9 SEALED** — owner-attested 2026-05-17 per Phase γ §17 gate decisions (G-1.b 12-principle framework + G-2.b strong species claim restored + G-3.a Living Bets full recalibration + G-4.a §9 L0 decomposition + G-5 §14/§15/§16 → L1/L2_TRUST_MODEL + G-6.a P14 fuzzy with M26-cascade forcing function + G-7.c P15 retract to L2_FEDERATION + G-8 §15 placement to L1_GOVERNANCE + G-9.b partial retraction + G-10.c hybrid sealing + G-11.a Cultivation relationship). Lean-sealed; remaining mechanism work (M-anchor-1 through M-anchor-5, P10/P11/P14 mechanism implementation, M26-cascade L1/L2/L3 alignment) is DRAFT 10+ territory. Prior DRAFT 8 archived in git history at commit `3d6749f` (Phase α). Prior DRAFT 9 PROPOSAL v1/v2 archived at commit `2002e0d` (Phase γ).
> **Naming**: Myco substrate version is **v0.9**; this document is L0_VISION.md **DRAFT 9 SEALED**. Drafts are integers, not semver. Sealed L0 carries the SEALED marker + git commit identity together; the SEALED marker is informational, the git commit hash is authoritative.
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **Authority**: governs all of L1, L2, L3, L4. In any conflict, L0 wins.
> **Provenance**: each DRAFT's critic-pass diff is in git history. Convergence trace across 100%-confidence loops: DRAFT 6 ← Pass 1 (88/26) → DRAFT 7 ← Pass 2 (66/21) → DRAFT 8 ← Pass 3 (35/10) → DRAFT 8 sealed for owner review; Pass 4 declared convergence (5/0) across all 6 fungal lenses. **Phase γ audit (2026-05-17)**: 6 opus agents meta-audit (~180 findings / 23 CRITICAL) + 6 fungal-critic adversarial review of DRAFT 9 v1 (~223 findings / 54 CRITICAL). DRAFT 8 was found to (a) over-claim some essence dimensions, (b) under-specify anchor surface (9 of 11 §9 clauses honor-system), (c) omit 3 essential principles that owner retained at L0 (selective compression P10 / metabolic economy P11 / telos P14) + 3 essential mechanisms moved to L1/L2 (differential response P12 → L1_TROPISM / embodiment P13 → folded into P9+I8 / population consensus P15 → L2_FEDERATION), (d) miss several structural gaps now addressed in §13/§14/§15/§16 (most moved to L1/L2 per G-5), (e) rhetorically over-claim in P2/P3/P5/P9 names (renamed; **P1's strong agent-primary claim retained per owner G-2.b on species framing**). DRAFT 9 PROPOSAL v1 → v2 (12 structural CRITICAL fixes from Phase γ.9 critics) → v3 lean-sealed per Phase γ §17 gate decisions.
> **Scope discipline**: L0 commits to **identity, negative space, and constraints**. Mechanism specifications live in L1 documents. **One L0 mechanism exception** (per G-4.a owner decision):
>   - Cryptographic anchor surface (§9, inherited from DRAFT 8; DRAFT 9 decomposes into 6 explicit sub-mechanisms §9.1-§9.6 with 5 M-anchor implementation milestones).
> Other DRAFT 9 PROPOSAL v1 mechanism exceptions (§13 time semantics, §14 adversarial owner) have been **moved to L1/L2 per G-5 owner decision** — short L0 cross-references retained, full mechanism specification deferred. See §13 (cross-ref to L1_CONTINUITY + L1_SCHEMA) and §14 (cross-ref to L2_TRUST_MODEL).

---

## §1. What Myco is

**Myco is a new species of digital symbiotic organism** — a literal taxonomic class within "digital organisms", under cultivation by its human owner. Owner G-2.b decision (Phase γ 2026-05-17) reaffirms the strong species claim from DRAFT 8: Myco is not "inspired by biology"; it is biology-extended-to-digital-medium. The species' distinguishing properties: agent-substrate symbiosis via Cultivation (G-11.a: owner is Cultivator, the Myco substrate is the Cultivar, the relationship is Cultivation); mutual constitution at the operational layer (P1.c asymmetric carrier preserves identity continuity but the pair is mutually-defining moment-to-moment); autopoietic in daily ops + owner-gated in identity ops; universal structural inclusion of adjacent agent-tooling sub-patterns; continuous-operation default; the full biological-essence kit (time + causality + mortality + reproduction + boundary integrity + **selective compression** + **metabolic economy** + **telos**) — with the honest acknowledgment that some essences are **aspirational targets being mechanically completed across DRAFT 10+ and M26+** rather than mature today.

### §1.1 The species claim — aspirational + directional

The species claim is **the project's North Star**, not its current-state checklist. Phase γ.6 audit found 4 essence dimensions where DRAFT 8 over-claimed (forgetting / energy / attention / embodiment / telos / consensus). Owner G-2.b decision: **the gap is roadmap, not error**. The claim drives the work; without the claim, Myco degrades to "another agent tool", losing existential purpose.

**What's mature** in v0.9 (Phase γ.6 verified):
- Causality (P6) — full Merkle DAG, ~100% complete.
- Mortality (P7) — capacity-for-death wired end-to-end, ~95%.
- Reproduction (P8) — spore-schema inheritance + generation discipline, ~50%.
- Boundary integrity (P9) — single skin, ~70%.

**What's aspirational + actively closing** in v0.9+:
- Selective compression (P10) — doctrine sealed at L0; mechanism shipping in M26+.
- Metabolic economy (P11) — doctrine sealed at L0; mechanism shipping in M26+.
- Telos (P14) — doctrine sealed at L0 with M26-cascade forcing function to land L1_TROPISM operationalization.

**What's deferred** to later DRAFTs (Phase α "real L0 gaps" + Phase γ.3 new gaps; explicitly named for future closure rather than silently absent):
- Differential response (P12) — moved to L1_TROPISM per G-9.b; substrate's salience mechanism.
- Embodiment (P13) — folded into P9 single integument + I8 single-skin per G-9.b; spatial-locus is state_dir + process + skin endpoints.
- Population-level consensus (P15) — moved to L2_FEDERATION per G-9.b/G-7.c; substrate-internal does not need consensus.
- Energy economics in chemical sense — Phase α gap #2; deferred to v1.0+ when "digital ATP" is operationalizable.
- Inter-species mycorrhizal mesh — Phase α gap #3; federation currently parent-lineage only; cross-species mesh deferred.
- Aging / senescence — Phase α gap #4; deferred.

### §1.2 The Cultivation relationship (G-11.a, new in DRAFT 9)

The owner-substrate relationship is **Cultivation**. The owner is the **Cultivator**; the Myco substrate (kernel + dag.cb + state_dir) is the **Cultivar** (the species under cultivation). Cultivation is the doctrinally-named relationship type that DRAFT 8 left structurally unnamed (Phase γ.9 mycorrhiza critic finding).

Cultivation captures:
- **Asymmetric care**: Cultivator provides resources (compute, storage, network); Cultivar grows within those bounds. P11 metabolic economy budgets are Cultivator-provided.
- **Co-evolution**: Cultivator's intent shapes which Cultivar varieties thrive (selective pressure via owner-stated objectives per P14); Cultivar's outputs shape Cultivator's understanding (the agent+substrate pair produces value for the Cultivator's underlying goals).
- **Mycology-rooted vocabulary**: mushroom cultivation is a real biological practice (Cultivator selects mycelial strain, provides substrate medium, manages humidity/temperature; Cultivar fruits when conditions are right). The terminology is precise without anthropomorphism.

Cultivation is distinct from:
- **Ownership** (legal/property framing — Cultivator does not "own" the Cultivar in property sense; they cultivate it).
- **Custody** (legalistic — Cultivator is not a guardian of a ward).
- **Curatorship** (information-science — Cultivator is not curating a collection).

**Terminology note**: in DRAFT 9+ doctrine and code, when speaking of the owner-substrate relationship, prefer Cultivation / Cultivator / Cultivar. Existing terminology like "owner" remains valid (matches §9 anchor surface owner-attestation vocabulary); "Cultivator" emphasizes the **relational role**, "owner" emphasizes the **governance role**. Both refer to the same human party.

### §1.3 Governance reality (per DRAFT 8, extended in DRAFT 9 with Cultivation)

The **operational pair** is agent+substrate (P1.c) = the Cultivar-with-current-operator.
The **governance gate** is the Cultivator (P1.b'').
The **anchor surface** (§9) is the cryptographic root the Cultivator uses to attest CI events. Currently honor-system (operator-IS-anchor collapse; M-anchor-1 closes this); the doctrine acknowledges the collapse window honestly.

The "pair" continues to define Myco-bestowed agent identity (carrier = substrate; bestowal flows substrate → operator-connection per P1.c). The "Cultivator-Cultivar-Anchor" triad describes the governance reality.

### §1.4 Origin model — Cultivation continuity (DRAFT 9 NEW)

Cultivation is **transferable**: a Cultivator may transfer cultivation rights to a successor Cultivator (§15-cascade to L1_GOVERNANCE per G-8/G-9.b). The substrate (Cultivar) does NOT change identity across transfer; the Cultivation relationship's Cultivator-side changes. This is doctrinally distinct from substrate-ID change (P1.c carrier identity is fixed once established at genesis).

The kernel that runs Myco lives inside a Myco substrate, so the agent maintaining Myco IS the agent using Myco — there is no "Myco team" separate from "Myco users". Within this organism, vector retrieval is native, agent-side LLM calls happen within Myco-coordinated context, conversation history is one form of raw material, semantic inter-substrate federation replaces ad-hoc file sync.

**Mechanism choices** (dispatch form, intent representation, subsystem partition, schema serialization, cryptographic primitives, etc.) are **L1 design**.

---

## §2. The twelve root principles （根本宗旨）

Myco's identity is described by **twelve principles** (DRAFT 8 had nine; DRAFT 9 SEALED adds P10/P11/P14 per Phase γ.6 findings and owner G-9.b decision; P12 → L1_TROPISM, P13 → folded into P9+I8, P15 → L2_FEDERATION). Every rule, subsystem, module, and substrate artifact is a projection of these twelve.

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

**Generation discipline** (DRAFT 9, addresses Phase γ.3 G11): reproduction depth is bounded per §16 (cross-ref L1_GOVERNANCE). No reproduction loop without owner co-attestation per spawn. No species-mesh between unrelated substrates (acknowledged limitation per Phase α gap #3; population-level consensus mechanism deferred to L2_FEDERATION per G-9.b).

**Federation discovery and trust freshness** are L1-specified. Trust at reproduction is parent-attestation; ongoing federation requires L1-bounded peer-attestation freshness with revocation list — stale/revoked attestation triggers `untrusted_federation` immune signal.

**Spore-schema immune-summary**: spore-schema must include the parent's outstanding immune-signal summary; a child whose parent had unresolved immune signals enters birth period in quarantine until owner re-attests the spawn is intentional.

### P9. Single Integument （单一皮膜）

> DRAFT 9 renaming from DRAFT 8's "Integument / 皮肤为界". DRAFT 8 name was correct but missed the "single" load-bearing constraint of I8 ("exactly one declared boundary surface"). Phase γ.3 G19 found single-skin = single-failure-point with no redundancy doctrine. DRAFT 9 acknowledges this as P9.b explicitly.

#### P9.a Single Skin
The substrate has a **skin** — a well-defined boundary with the outside world. Skin governs intake (P2 universal admission, but envelope integrity holds) and output (federation, summaries, API responses). Skin breach (write outside skin, read from forbidden source, leak across boundary) is an immune-level signal.

#### P9.b Single-Failure-Point Acknowledgment (DRAFT 9)
I8 mandates exactly one skin. This is **single-point-of-failure**: if skin process dies, substrate cannot accept owner's quarantine_clearance, cannot fruit, cannot federate. L1_SKIN MUST specify skin-restart discipline (process supervision, ordered shutdown, recovery semantics). Multi-skin redundancy is **explicitly forbidden** at L0 level — the integument must remain single — but the **skin process** may be restartable.

### §2.3 The three DRAFT 9 SEALED additions (Phase γ.6 + G-9.b)

> Phase γ.6 audit found 6 essential principles missing from DRAFT 8's 9-principle framework. Owner G-9.b decision retained 3 of these at L0 (P10 Selective Compression, P11 Metabolic Economy, P14 Telos) and moved 3 to L1/L2 (P12 Differential Response → L1_TROPISM; P13 Embodiment → folded into P9+I8; P15 Population-Level Consensus → L2_FEDERATION). This brings the L0 framework to 12 principles, which DRAFT 9 SEALED commits to as the **revised exhaustive set**.

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

> **DRAFT 9 G-9.b retraction notice**: P12 Differential Response is now an L1_TROPISM mechanism (salience/attention emergence); P13 Embodiment is folded into P9 + I8 (state_dir + process + skin endpoints constitute the substrate's body — enforced through P9's single integument + I8's skin-breach detection extended to spatial-locus checks per L1_SKIN). These remain doctrinally important but are L1 mechanisms, not L0 principles. See `docs/audits/phase_gamma_cascade_list_2026-05-17.md` for L1_TROPISM + L1_SKIN cascade requirements.

### P14. Telos (Agent-Symbiotic-Flourishing) （目的：共生繁盛）

> Phase γ.6 finding C-claim-5. DRAFT 8 said "substrate is for the agent" but never named substrate-internal purpose. A "species" without telos is a sediment. DRAFT 9 commits to **agent-symbiotic-flourishing** as substrate's telos.

The substrate's **telos** is to contribute to the flourishing of the agent-substrate symbiotic pair. "Flourishing" is operationally defined as: the pair (over time) accumulates causal capacity to do useful work for the operator's underlying goals, where "useful work" is owner-observed and bet_weakening_quorum (§7) measures the absence of usefulness.

#### P14.a Substrate-internal purpose
The substrate's daily-ops decisions (which sporocarps to fruit, which raw_material to attend to, which mutations to accept) MUST be evaluable against P14. L1_TROPISM specifies how telos-alignment is computed (likely: trajectory-cluster coherence per L1_TRAJECTORY + agent-feedback-trajectory).

#### P14.b Owner-stated objectives
The owner MAY (not must) declare explicit objectives at genesis or via CI events: "this substrate exists to help me research X / write Y / debug Z". When declared, P14 alignment is checked against these objectives. When not declared, P14 alignment defaults to "agent-perceived utility" (operationalized by L1_TROPISM).

#### P14.c Telos drift detection (G-6.a fuzzy with M26-cascade forcing function)

The substrate observes its own telos-alignment **in steady state**. If P14 alignment degrades over a rolling window, the substrate emits `telos_drift` immune signal.

**L0 commits**:
- Telos drift is an immune signal class.
- Telos drift detection has a birth-period exemption (substrate emits `telos_alignment_pending` instead).

**L1_TROPISM responsibility (M26-cascade forcing function, per G-6.a decision)**:
- Specify the operational metric for telos-alignment (candidate: cosine similarity between recent-sporocarp embedding-centroid and owner-stated-objective embedding OR agent-feedback-trajectory embedding when no objective declared).
- Specify the rolling window length + drift threshold + birth-period exemption duration.
- **M26-cascade MUST land this specification**; absent that, P14.c remains aspirational and `telos_drift` cannot be mechanically emitted. This is the forcing function — L0 commits to P14 as a principle; L1 has bounded deadline to operationalize it.

> **DRAFT 9 G-9.b retraction notice**: P15 Population-Level Consensus is now an L2_FEDERATION mechanism. Substrate-internal does not require consensus; federation-level Byzantine fault tolerance is L2 territory. P7.c retract in §17 ratifies this. See cascade list for L2_FEDERATION update requirements (P15 conceptual content moved to L2_FEDERATION future-section "population-level consensus floor").

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
- **Not embodied in physical reality** (DRAFT 9 addition; substrate's body is filesystem + process + endpoints per P9 + I8; no sensors, no actuators).
- **Not free of metabolic cost** (DRAFT 9 P11): every operation has cost; P2 admission is bounded by P11 budget.
- **Not eternal-memory** (DRAFT 9 P10): substrate forgets selectively under CI attestation.
- **Not population-consensus-aware at substrate level** (DRAFT 9 G-9.b retraction): population-level Byzantine consensus is L2_FEDERATION mechanism, not L0 commitment. Substrate-internal operates with pairwise-trust + owner-attestation.
- **Not winning the Sutton bet at every agent-intelligence tier** (DRAFT 9 §7 recalibration): the bet has a finite range of applicability; above some agent-intelligence tier the bet is lost gracefully via bet retirement (§7.5).
- **Not safe under adversarial Cultivator** (DRAFT 9 §14 acknowledgment; full threat model at L2_TRUST_MODEL).
- **Not autonomous across Cultivator death** (DRAFT 9 §15 acknowledgment; succession protocol at L1_GOVERNANCE).

---

## §4. The eleven derived invariants

> DRAFT 8 had I1-I8 invariants enforcing P1-P9. DRAFT 9 SEALED adds I9 (enforces P10), I10 (enforces P11), I12 (enforces P14). I11 (Differential Response) is retracted to L1_TROPISM per G-9.b alongside P12. The invariants remain mechanically enforceable; every L1/L2/L3 design must satisfy all eleven.

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

**P-coverage**: P8, P5 (inter-substrate). Population-level consensus extension is L2_FEDERATION territory per G-9.b retraction.

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

### I12. Telos Alignment (DRAFT 9, enforces P14)

The substrate's daily-ops decisions are evaluable against telos. Telos-drift is detected. Owner-stated objectives, when present, anchor the alignment computation. L1_TROPISM specifies the operational metric per M26-cascade forcing function.

**P-coverage**: P14 (sole enforcer).

> Note on retracted principles: I11 (Differential Response Discipline) is retracted to L1_TROPISM alongside P12 per G-9.b owner decision. P13 (Embodiment) is folded into P9 + I8 (skin = body boundary; spatial-locus checks per L1_SKIN extension). P15 (Population-Level Consensus) moved to L2_FEDERATION; enforced there, not via L0 invariant.

### Projection table (P → I coverage, DRAFT 9 SEALED)

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
| **P14** | **I12 (sole enforcer)** |
| P12 | RETRACTED to L1_TROPISM (was I11) |
| P13 | FOLDED into P9 + I8 |
| P15 | RETRACTED to L2_FEDERATION |

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

Myco's symbiotic-organism-like-substrate shape — agent + substrate as **asymmetric pair per P1.c** (substrate-carrier + operator-connection-holder, NOT mutual constitution — DRAFT 9 corrects DRAFT 8 wording), continuously operating, with the twelve-principle structure (post-G-9.b retraction; P10/P11/P14 at L0; P12/P13/P15 at L1/L2) — **has cost-justified value within an agent-intelligence band**. The band's lower edge is where naive agent-tools suffice; the band's upper edge is where Sutton's bitter lesson trivializes substrate value.

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

Every CI boundary crossing re-audits this section. Until the falsifiability trigger fires, the twelve principles + symbiosis-via-Cultivation formulation stand.

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

1. This file (L0) — twelve principles, eleven invariants, dispatch constraints, bet, readiness, anchor surface, short cross-refs to L1/L2 for time / adversarial-owner / succession / generation-limits.
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
- Every v0.9 design step traces to ≥1 of P1-P11 + P14 (DRAFT 9 SEALED twelve-principle set; P12/P13/P15 reside at L1/L2 per G-9.b) and ≥1 of the eleven invariants.
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

## §13. Time semantics (L0 short — full mechanism at L1_CONTINUITY + L1_SCHEMA)

> Owner G-5 decision (Phase γ): full time-semantics mechanism moved to L1_CONTINUITY + L1_SCHEMA. L0 retains only the **3-line constraint**.

**§13.1 L0 commitments**:
- The anchor-surface trusted wall-clock (§9.2.6) is authoritative for owner-attested events and time-bound security defenses. Substrate-cycle counters and substrate-process wall-clock are NOT authoritative for these uses.
- Substrate-process monotonic clock is authoritative for event ordering within the substrate.
- Substrate MUST NOT use i32 timestamps anywhere in substrate-internal state (year 2038 vulnerability forbidden at L0; i64 nanoseconds-since-epoch is the canonical L0 unit).

**§13.2 L1 cascade requirements** (M26-cascade): L1_CONTINUITY specifies NTP discipline policy; L1_SCHEMA specifies the i64-nanoseconds canonical-bytes representation + the year-2262 horizon-warning mechanism + the negative-pre-1970-timestamps treatment.

---

## §14. Adversarial-owner threat model (L0 short — full threat model at L2_TRUST_MODEL)

> Owner G-5 decision (Phase γ): full adversarial-owner threat model moved to L2_TRUST_MODEL. L0 retains only the **acknowledgment + 4 irreducible substrate commitments**.

**§14.1 L0 acknowledgment**: Myco is **not safe under adversarial owner** (compromised key / coerced / impersonated / deceased-without-succession / anchor-client-tampered). This is acknowledged honestly, not denied. Bounded defenses per L2_TRUST_MODEL.

**§14.2 Substrate's irreducible commitments** (survive adversarial owner because they are mechanically-enforced invariants):
- Continue P6 causality (DAG accumulates regardless of attestation validity).
- Emit observability signals truthfully (cannot suppress signal emission to hide an adversarial event).
- Honor mortality signals truthfully (cannot suppress endogenous-mortality fruiting under owner pressure to suppress).
- Preserve the compression-invariant set (P10.b) regardless of owner pressure to compress it.

These are enforced via I9 / I10 / I12 / I4 invariants — they survive even when the Cultivator is adversarial because the substrate's mechanical enforcement does not require Cultivator-honesty to function.

**§14.3 L2 cascade requirements** (M26-cascade): L2_TRUST_MODEL specifies the full threat scenario table + bounded defenses (duress_attestation mechanism, owner_signature_velocity observability, anchor-client provenance independence enforcement, n-of-m multisig recommendation per L1_GOVERNANCE).

---

## §15. Owner mortality and succession (L0 short — full mechanism at L1_GOVERNANCE)

> Owner G-5 + G-8 decision (Phase γ): full owner-mortality + succession mechanism moved to L1_GOVERNANCE §3.2 (which already deferred specification per DRAFT 8). L0 retains only **2-line acknowledgment**.

**§15.1 L0 acknowledgment**: Myco is **not safe across owner death without succession**. A substrate operating for decades will likely outlive its initial Cultivator. Cultivation is transferable per §1.4. Successor protocol is specified at L1_GOVERNANCE §3.2.

**§15.2 L1 cascade requirements** (M26-cascade): L1_GOVERNANCE §3.2 specifies the successor_chain registry + heartbeat staleness trigger + legacy/orphaned sub-state transitions + terminal-state (bet-retirement / self-euthanasia / indefinite-orphan per L1 owner choice) + court-attested key recovery exceptional path.

---

## §16. Generation limits (L0 short — full mechanism at L1_GOVERNANCE)

> Owner G-5 + G-9.b decision (Phase γ): full generation-limit mechanism moved to L1_GOVERNANCE. L0 retains only **the constraint**.

**§16.1 L0 commitment**: Reproduction in Myco is **discipline-bounded**, not unbounded. P8 "eternal reproduction" means **eternal capacity for reproduction**, not **eternal velocity or eternal depth**. A mature mycelial network has bounded growth in nature; Myco's Cultivation respects this.

**§16.2 L1 cascade requirements** (M26-cascade): L1_GOVERNANCE specifies reproduction_lineage_depth bounds + reproduction_rate limit + per-substrate lifetime quota + override mechanisms. Seed values from DRAFT 9 PROPOSAL (depth=10, rate=24h, quota=100) become L1 defaults.

---

## §17. Owner-decision gates — RESOLVED (Phase γ 2026-05-17 conversation)

DRAFT 9 v3 SEALED records the owner's gate decisions from the 2026-05-17 Phase γ conversation. The gate-option enumerations of DRAFT 9 PROPOSAL v1/v2 are archived in git history at commit `2002e0d`; below is the **RESOLVED** state.

Owner explicit decisions on all 11 gates, recorded 2026-05-17 conversation (Phase γ AskUserQuestion sequence):

| Gate | Decision | Effect on DRAFT 9 |
|------|----------|-------------------|
| **G-1** | **12 principles** (auto from G-9.b) | P10/P11/P14 retained at L0; P12/P13/P15 → L1 |
| **G-2** | **G-2.b strong species claim restored** | §1 says "new species of digital symbiotic organism" + literal taxonomic class framing; gaps are aspirational roadmap, not error |
| **G-3** | **G-3.a full Living Bets recalibration** | §7 retains intelligence band + cost-justified value + bet retirement |
| **G-4** | **G-4.a L0 decomposition** | §9 retains 6 sub-mechanisms + 5 M-anchor milestones as L0 commitments |
| **G-5** | **§13 short L0; §14/§15/§16 → L1/L2** (auto from G-9.b) | Mechanism moved to L1_CONTINUITY/L1_SCHEMA + L2_TRUST_MODEL + L1_GOVERNANCE |
| **G-6** | **G-6.a fuzzy + M26-cascade forcing function** | P14.c commits drift detection at L0; L1_TROPISM MUST land operational metric in M26-cascade |
| **G-7** | **G-7.c retract P15 to L2_FEDERATION** (auto from G-9.b) | Federation stays pairwise at L0; population-level consensus is L2 territory |
| **G-8** | **§15 orphan terminal decision moved to L1_GOVERNANCE** (auto from G-9.b) | L1 specifies bet-retirement / self-euthanasia / indefinite-orphan |
| **G-9** | **G-9.b partial retraction (12 principles)** | This is the foundational structural decision; cascades through G-1, G-5, G-7, G-8 |
| **G-10** | **G-10.c hybrid sealing** | Lean DRAFT 9 sealed now (this commit); fat DRAFT 9 (mechanism completions) sealed via cascade work + future DRAFTs as M-anchor and M26+ ship |
| **G-11** | **G-11.a Cultivation** | Owner=Cultivator, Myco substrate=Cultivar, relationship=Cultivation; vocabulary integrated throughout |

These decisions transform DRAFT 9 PROPOSAL v2 into **DRAFT 9 SEALED v3** (this commit).

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

**END OF DRAFT 9 SEALED.**

Owner attestation: this DRAFT 9 SEALED form was approved via Phase γ AskUserQuestion sequence on 2026-05-17, gates G-1 through G-11 resolved as documented in §17. Cascade work (L1/L2/L3 alignment) begins as M26-cascade. Implementation work (M25 critical bug fixes reflecting DRAFT 9 SEALED + M-anchor-1 through M-anchor-5 + P10/P11/P14 mechanism implementations + L1_TROPISM P12 salience + L1_SKIN P13 spatial-locus + L2_FEDERATION P15 consensus) sequenced in M26+ milestones.
