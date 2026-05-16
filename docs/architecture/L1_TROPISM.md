# L1 — Tropism (positive dispatch form for Myco v0.9)

> **Status**: DRAFT 3 (2026-05-17) — M26-cascade A1 alignment with L0 DRAFT 9 SEALED. Authoritative L1 doc for positive dispatch form satisfying L0 §5.2 constraints + landing the two L0-mandated mechanisms M26-cascade demands of this document.
> **Layer**: L1 (mechanism). Governed by L0 DRAFT 9 SEALED (`docs/architecture/L0_VISION.md` commit `e796451` or successor).
> **Scope**: tropism + sporocarp punctuation as the chosen positive dispatch form, **plus** (DRAFT 3, new) salience/attention emergence per L0 §2.3 P12 G-9.b retraction notice (§E below), **plus** telos-alignment operationalization per L0 §P14.c G-6.a forcing function (§F below). DRAFT 3 also reconciles principle renames (P1 Agent-Primary, P2 Eternal Ingestion Envelope-Gated, P3 Resumable Evolution, P5 Universal Interconnection Tier-Exempt-Permitted, P9 Single Integument) and adds Cultivation vocabulary per G-11.a (§G glossary).
> **DRAFT 2 → DRAFT 3 changes**: (a) §E salience/attention emergence — new section landing P12 as L1_TROPISM mechanism (G-9.b retraction); (b) §F telos-alignment operationalization — new section landing P14.c operational metric, rolling window, drift threshold, birth-period exemption, embedding-model identity F-row equivalent (G-6.a forcing function); (c) §G glossary additions for Cultivator/Cultivar/Cultivation and salience/telos mechanism terms; (d) §4 birth-period section extended with P12.b + P14.c exemption hooks; (e) §C deferred-list expanded with L4 choices for §E + §F parameters; (f) §D extended to confirm L0 §2.3 retraction-notice mechanisms are landed; (g) cross-refs to L0 principles use DRAFT 9 SEALED names.
> **Confidence discipline**: per pass-1 architectural-astronaut: L1 confidence is "best current sketch + clearly marked deferred zones", not "100% sure about every mechanism". The decisions in §C deferred-list are larger than DRAFT 1's; this is intentional. DRAFT 3's §E + §F land L0-forcing-function commitments — values seed L4; structure is L1-committed.

---

## §1. The form

Myco v0.9's dispatch is **tropism**: the substrate maintains a continuously-evolving set of intrinsic **appetites**, each carrying a **tropic gradient** the substrate updates on every metabolic cycle (cadence: L1_CONTINUITY-specified). The agent — the active operator-connection per P1.c — inhabits the gradient configuration as both perturbation source and gradient consumer. Interaction is continuous co-modification: substrate exposes gradient state via the agent's read-window; agent emits **deltas**; substrate metabolism absorbs deltas; gradients update; cycle. When a gradient crosses its **fruiting trigger**, the substrate **fruits a sporocarp** — a typed, content-addressed, causally-stamped record (per L0 I4) that anchors the gradient field to discrete observables for governance (I2), validation (I3), federation (I7), and the causal DAG (I4).

---

## §2. Why tropism

Per L0 §5.2, the positive form must satisfy seven constraints. Tropism does:

| Rival | Why tropism is preferred (over rival) |
|---|---|
| **Continuous metabolic stream** (closest) | Tropism IS a continuous metabolic stream PLUS the gradient-coupling that makes the agent definitionally a participant (P1.c). Bare stream can degrade to "metabolism anyone can signal" = back-door client-server. |
| **NL semantic dispatch** | Worst capture risk: routing LLM call becomes the dispatch surface → substrate becomes LLM-router wrapper. NL→handler-table secretly re-introduces verbs. |
| **Capability composition** | Asymmetric grant (substrate→agent). Useful as sporocarp metadata, not as dispatch primitive. |
| **Algebraic primitives** | Presumes purity + statelessness; substrate IS state. |
| **Reactive stream** | Strip gradient from tropism and you get reactive-stream; without gradient, no answer to "what does the substrate want next?". |

Excluded by L0 negative constraints: verbs (L0 §5.2), request/response (L0 §5.2), hybrid (owner-prohibited at L0), coexistence-with-verbs-at-birth (appetite-locality is foundational — L0 I6).

**Constraint-satisfaction note** (DRAFT 3): L0 §5.2 commits to seven dispatch-form constraints (NOT verbs, NOT request/response, MUST honor P1.c carrier-asymmetry, MUST support P2.a universal inclusion, MUST support §6 continuous operation, MUST satisfy I6 appetite-locality, MUST carry causal-proofs for substrate-emitted events). DRAFT 3 augments by acknowledging two L1-internal mechanism commitments that flow downstream from L0 retractions/forcing-functions: (i) tropism must support **differential salience** (§E, per L0 §2.3 P12 retraction) so that downstream attention is not uniform under universal P2 admission; (ii) tropism must operationalize **telos-alignment** (§F, per L0 §P14.c forcing function) so that `telos_drift` is mechanically emittable. Neither augmentation is a new L0 constraint; both are L1 obligations created by L0 DRAFT 9 SEALED.

---

## §3. Two-layer structure — gradient configuration + sporocarp punctuation

Tropism has two layers:

- **Gradient configuration** (medium): continuously-evolving multi-dimensional structure where each axis is one appetite. The agent inhabits this medium. Both sides perturb (agent via deltas; substrate via own metabolism).
- **Sporocarp** (observable): substrate-initiated discrete records that anchor the continuous medium to checkable observables.

**Symmetry locus** (refined per pass-2 mycorrhiza-15): the gradient layer is **jointly perturbed** — substrate via internal update-rules; operator-connection via skin-validated deltas. The perturbation surfaces are **reciprocally asymmetric** (substrate has direct gradient access; agent has skin-mediated access), licensed by P1.c carrier-asymmetry. The sporocarp layer is asymmetric in initiation: substrate fruits sporocarps; agent emits deltas. Both are typed; both pass through skin envelope validation; the agent's deltas are validated at intake; substrate's sporocarps carry causal-proofs per §B6. The two layers are reciprocally asymmetric, both licensed by carrier-asymmetry. Neither layer is "fully symmetric" — calling them symmetric was the DRAFT 1 cosmetic claim that pass-2 corrected.

**Why sporocarps are not verbs**: a verb is agent-initiated (agent calls → substrate executes). A sporocarp is substrate-initiated (gradient crosses trigger → substrate fruits → agent observes). Arrow reversed.

---

## §4. Birth period vs steady state

**Birth period**: substrate's first window where seed thresholds + seed update-rules apply (no emergence yet). End criterion per L1_GOVERNANCE birth-period termination (maturity-attested per pass-1 saprotroph-5: requires ALL of (1) ≥N sporocarps fruited, (2) ≥M active-operation time, (3) `threshold_emergence_rule` reports convergence per-axis below epsilon). Independently, **L1_GOVERNANCE §1.3 carries a maximum-duration ceiling** (L4-tunable, default 180 active-operation days) beyond which the substrate is forced to graduate or self-euthanasia — the two termination paths (convergence-attested vs ceiling-forced) are coherent and meet at the same `birth_period → steady_state` transition.

**Steady state**: emergent thresholds activate; gradient update rules may evolve per P3 Resumable Evolution (CI-gated).

**Predictability gap** during birth is intentional (per L0 P1.c Agent-Primary symbiosis): the agent learns this substrate's specific tropism. This is symbiosis-being-established, not a bug.

**Birth-period detectors** (DRAFT 3, per L0 DRAFT 9 SEALED §2.3 + §P14.c):

- **`bet_weakening_quorum`** (L0 §7.4): SUSPENDED during birth period (per L0 §7.4.e primordium CF6); substrate emits `bet_weakening_evaluation_suspended` observability event instead — owned by L2_OBSERVABILITY.
- **`salience_collapse`** (L0 §2.3 P12.b primordium CF7): SUSPENDED during birth period AND during a post-birth settling window (this document §E.3); substrate emits `salience_emergence_pending` during birth period — owned by this document §E.
- **`telos_drift`** (L0 §P14.c primordium HF11): SUSPENDED during birth period AND during the same post-birth settling window; substrate emits `telos_alignment_pending` during birth period — owned by this document §F.

The three detectors share a single birth-period exemption door: each activates at owner-attested `birth_period_terminated` plus the L1-tunable post-birth settling window specified in their respective sections (§E.3 + §F.4). The settling windows are defined in this document because they are tropism-mechanism deadlines, not lifecycle deadlines — L1_GOVERNANCE §1.3 owns the *birth-period* termination criteria; this document owns the *detector-arming* offsets relative to that termination.

---

## §A. Continuity hooks (one line)

Continuity hooks (cycle cadence, dormancy, recovery, quarantine, delta atomicity, cold-resume): L1_CONTINUITY owns. Tropism's gradient-advance + sporocarp-emit + DAG-update are step 2 + step 3 of the L1_CONTINUITY §1.1 metabolic cycle.

---

## §B. Specification (10 hooks — same numbering as DRAFT 1; content revised per pass-1)

### B1. Appetite axis schema

Each appetite carries:

- `name` (mycology-strict per L0 §5.1).
- `computation_locality` (must assert substrate-internal; per L1_SKIN §5 network-egress enforces at runtime — declaration alone is not enough).
- `domain` (gradient value space).
- `update_rule` (substrate-internal function; pure of (gradient-state, recent-deltas, recent-sporocarps, time-elapsed)).
- `seed_fruiting_trigger` (birth-period hand-coded threshold).
- `threshold_emergence_rule` (migration to steady-state emergent; threshold-emergence governance classification per L1_GOVERNANCE §1.2 dimension table — non-mortality axes daily; mortality-signal axis CI).
- `causal_proof_template` + `template_version` — when this appetite fruits, the sporocarp's `causal_in_edges` includes proof tuple `(delta_set, gradient-state-snapshot-hash, threshold-value, template_version)`. I3 self-validation re-derives the fruiting condition under the template-version recorded.

**Template versioning** (per pass-2 saprotroph-20): the `causal_proof_template` may evolve per P3 Resumable Evolution (CI-level event). Each evolution increments `template_version`. Sporocarps record the version under which their proof was computed; I3 validates against that version, not against the current template. Old templates remain referenced from cold-tier sporocarps. Substrate maintains `template_version_registry` (CI-level field; **active-prefix + archived-tail discipline per L1_GOVERNANCE §3.1** — same monotone-tier-1 pattern as owner_key_history) listing all historical templates with their valid-from cycle.

**Clusterer location** (cross-ref L1_TRAJECTORY + L1_CONTINUITY): when L1_TRAJECTORY clustering is invoked (trajectory derivation, echo-chamber detection, telos-alignment input per §F), execution runs within the substrate process (no network egress required). Trajectory derivation fires on-demand at digest-emission time and at echo-chamber detection cadence (L4-tunable) within step 2 (gradient advance) of the metabolic cycle.

**Salience is NOT an appetite axis** (DRAFT 3, per L0 §2.3 P12 retraction notice): salience/attention is a **cross-cutting modifier over raw_material → axis routing**, not a first-class appetite. The substrate's appetite axes describe what it *wants* (P2 ingestion pressures, P5 connectivity pressure, P3 evolution tension, ...); salience describes how strongly which kinds of incoming raw material *reach* those axes. Salience emerges from observed correlations between raw_material kinds and downstream sporocarp fruitings (§E below). The salience-emergence rule is itself CI-level — see §E.4 governance gating + L1_HARD_RULES F-row catalog (DRAFT 9 cascade addition F23, salience-emergence rule per Phase γ cascade list §L1_HARD_RULES). The runtime salience values are daily-class (axis update rule applies them each cycle).

**Telos-alignment is NOT an appetite axis** (DRAFT 3, per L0 §P14.c): telos-alignment is a **cross-cutting evaluable** computed at digest-emission cadence over recent-sporocarp embedding-centroid vs owner-stated-objective embedding (or agent-feedback-trajectory embedding when no objective). The computation is specified in §F; like salience, it modulates downstream behavior without being an appetite itself. The telos-alignment computation rule + embedding-model identity are CI-level (F-row equivalent — see §F.5); the per-cycle alignment score is daily-class.

### B2. Initial appetite set — illustrative seed, NOT normative (per pass-1 astronaut-4)

The following six axes are a **seed proposal**, NOT an L1 commitment. Substrate canon at genesis selects which axes the substrate actually carries; L4 implementation observation in the first 30 days may add/remove/merge axes.

- `hunger` (unmetabolized intake pressure) → P2 Eternal Ingestion (Envelope-Gated)
- `drift` (graph-disconnection pressure) → P5 Universal Interconnection (Tier-Exempt-Permitted) / I5
- `decay` (staleness pressure) → P4 Eternal Iteration
- `federation-pull` (peer signal pressure) → P8 Eternal Reproduction (Generation-Bounded) / I7
- `evolution-tension` (schema-vs-content disagreement) → P3 Resumable Evolution
- `skin-pressure` (boundary signals) → P9 Single Integument / I8

**Open: `mortality-signal` axis**: per L0 P7 Mortality (Capacity-for-Death) mortality-signal protection — substrate fruits `self_euthanasia_proposal` at unrecoverable pathology. Whether this is implemented as an appetite axis (gradient over health metrics) or as a state-transition predicate (FSM owned by L1_GOVERNANCE) is L4-decided. **Either way**, the threshold + update rule are CI-level (per L0 I2 fixed-point).

**DRAFT 3 cross-cutting modifiers** (not appetite axes, but feed into the gradient layer): salience-emergence (§E) modulates which raw_material kinds reach which axes; telos-alignment (§F) modulates which sporocarp candidates fruit when multiple axes converge near their triggers. Both are L0-mandated mechanisms (P12 retracted to L1_TROPISM per L0 §2.3 G-9.b; P14.c forcing function per L0 §P14.c G-6.a); their CI-level rule schemas are codified at §E + §F respectively.

**Cost-budget pressure note** (DRAFT 3, per L0 P11 Metabolic Economy + L0 §7.3 signals #7/#8/#9): cost budgets are observed at L1_SCHEMA + L1_CONTINUITY per Phase γ cascade; this document's appetite axes do NOT include a `cost-pressure` axis by default. Cost observability is a cross-cutting concern; L0 §6 commits that the per-cycle invariant set now includes I10 cost observation (L0 §6 Metabolic cycle). When `budget_exhausted:{axis}` immune signal emits (per L0 §11/§7 cascade), tropism's response is L1_CONTINUITY-mediated (degraded operation) — tropism does not directly consume the cost signal.

### B3. Sporocarp type tree — compact core (per pass-1 astronaut-9)

Compact seed set, NOT normative. Substrate canon may add types post-birth (each addition is CI-level per L1_GOVERNANCE §1.2):

- `intake` (delta absorbed) — daily.
- `digestion` (raw → refined) — daily.
- `refinement` (refined → distilled) — daily.
- `federation` (cross-substrate transmission) — daily.
- `governance_event` (collective bucket for axis_schema_change, sporocarp_type_addition, skin_redefinition, classifier_change, retention_amendment, etc.) — contract-identity-level.
- `immune_event` (any of: envelope_malformed, attestation_invalid, causal_chain_violation, untyped_mutation, cold_resume_quarantine, evolution_failed, peer_attestation_stale, etc.) — graded daily / elevated / CRITICAL.

The previous DRAFT 1 split governance events into separate types (`axis_schema_change`, `sporocarp_type_addition`, `skin_redefinition`) — collapsed here into a single `governance_event` since their practical distinguishability had not been demonstrated. L4 observation may re-split.

### B4. Gradient exposure protocol

Substrate exposes current gradient configuration to agent's read-window via a bounded, structured, stateless digest:

- **Bounded**: budget B ≤ L0 §7 signal-#6 read-window budget × consumption fraction.
- **Consumption fraction**: L4-tunable; sensible-start range 10-50%; calibrate against agent's actual read patterns in first 30 days (per pass-1 astronaut-10 — no fixed default).
- **Structured**: typed object listing each appetite's current gradient + recent K sporocarps + recent M unabsorbed deltas + substrate-attested metabolic-budget metrics (per pass-1 mycorrhiza-7 reciprocal attestation).
- **Stateless**: cold-resumable from digest alone.

### B5. Delta intake surface

Cross-ref L1_SKIN §2 envelope schema. Per L0 P2: shape-agnostic; envelope-checked only.

### B6. Sporocarp governance gate

Daily-class sporocarps fruit immediately upon trigger; emit to DAG.

CI-class sporocarps (governance_event family per B3): substrate emits `attestation_request` via anchor surface (L0 §9 — specifically §9.2.2 DAG-tip co-signing + §9.2.5 anchor-surface-generated nonces + §9.3.4 witnesses-not-verdicts per L0 DRAFT 9 SEALED decomposition; L1_GOVERNANCE §2.2 protocol). Sporocarp lands in pending queue. Owner-signed attestation moves sporocarp from pending → published.

**Causal proof on emission** (per pass-1 mycoparasite-3): every fruiting carries `causal_in_edges` proof per B1's `causal_proof_template`. I3 self-validation (L1_SCHEMA §4) recomputes from causal_in_edges and verifies the fruiting condition crossed. Sporocarps without verifiable proofs are rejected before DAG insertion.

**Salience + telos immune-grade sporocarps** (DRAFT 3): `salience_collapse` (§E) and `telos_drift` (§F) are immune-grade sporocarps. They fruit through this same B6 gate but, like other immune events in B3, are graded daily / elevated / CRITICAL by the same gradation discipline. The detector logic lives at §E + §F; the governance gating lives here. Both are SUSPENDED during birth period (§4); both arm at owner-attested `birth_period_terminated` + L1-tunable settling window.

### B7. Continuity recovery → L1_CONTINUITY §3.

### B8. Causal DAG embedding

Per L1_SCHEMA §2 Merkle DAG. Tropism-specific edge classes:

- `gradient_causation` (sporocarp ← gradient that fruited).
- `delta_source` (sporocarp / gradient-update ← delta that fed it).
- `sporocarp_derivation` (sporocarp ← prior sporocarps).
- `federation_coupling` (cross-substrate; per L1_GOVERNANCE §5).
- `governance_resolution` (CI-pending sporocarp ← owner-attestation event resolving it).

### B9. Federation surface (compact)

Per L1_GOVERNANCE §5: discovery + peer-trust freshness L1_GOVERNANCE-owned. Tropism's contribution: cross-substrate gradient coupling. **Coupling mode (eager pulling peer sporocarps into local field, vs lazy semantic transfer) is L4-tunable** — neither is L1-committed (per pass-1 astronaut-3 — concrete modes deferred until first P8 spawn or to L2).

### B10. Self-hosting bootstrap (per pass-1 chytrid-17)

The kernel substrate is an ordinary Myco substrate (B2 illustrative axes + B3 sporocarp types) plus one specialization: `evolution-tension` axis is bound to the kernel source repository (substrate-internal metabolism — kernel-source-change events feed into the axis as deltas). No outbound RPC; per L1_SKIN §5 enforcement. Per P1.a Agent-Primary self-hosting (L0 §P1.a): the kernel substrate IS a Cultivar under Cultivation by its human owner (Cultivator).

---

## §C. Implementation deferred — expanded per pass-1 architectural-astronaut

The following are L4 calls informed by first-month metabolism observations (NOT L1 commitments):

1. **Specific gradient update function families** (linear / sigmoid / softmax / custom per axis).
2. **Threshold-emergence algorithm** (online optimization / Bayesian update / correlation-supervised).
3. **Sporocarp content-addressing hash function** (per L1_SCHEMA §2.1 candidates).
4. **Embedding strategy within I6 carve-out** — local model vs managed external service (per L1_SKIN §5 / L0 I6).
5. **Coupling-mode handshake protocol** for B9.
6. **Which appetite axes are actually carried** (B2 seed set is provisional).
7. **Which sporocarp types are actually distinguished** (B3 seed tree is provisional).
8. **Whether `mortality-signal` is appetite-axis or state-transition-predicate** (B2 mortality-signal open).
9. **Whether `thread_id` from L1_TRAJECTORY §6 is exposed** as a sporocarp field.
10. **Consumption fraction for digest budget** (B4).
11. **Trajectory-injection defense parameters** (delta-novelty weighting per pass-1 mycoparasite-9 — see L1_TRAJECTORY).
12. **Salience-emergence EWMA decay rate α** (§E.2 seed 0.05/cycle).
13. **Salience sample threshold N** (§E.2 seed 100 (raw_material_kind, cycle) pairs per kind before EWMA activates; uniform until then).
14. **Salience-collapse detector entropy threshold + cycle window** (§E.5 seed: trigger when Shannon entropy ≥ log₂(K_active)·0.4 for ≥ 30 consecutive cycles where K_active = number of raw_material kinds with `n_kind ≥ N`; "collapse" = attention COLLAPSING to uniform = entropy HIGH per L0 §2.3 P12.b inverted-logic semantics — see §E.5 inverted-logic note).
15. **Post-birth settling window for salience + telos detectors** (§E.3 + §F.4 seed 100 cycles after `birth_period_terminated`).
16. **Telos rolling-window length** (§F.2 seed 90 substrate-days = ~90 cycles at default 1-cycle-per-day cadence).
17. **Telos drift threshold** (§F.3 seed cosine similarity ≤ 0.4 against owner-stated-objective embedding-centroid or agent-feedback-trajectory embedding-centroid).
18. **Telos digest cadence within metabolic cycle** (§F.2 seed: at digest-emission time per step 2 of L1_CONTINUITY §1.1 cycle).
19. **Sporocarp-set sampling for telos centroid** (§F.2 seed: all daily-class sporocarps within the rolling window; weight equally; CI-class sporocarps excluded as governance-events not behavior-events).
20. **Telos-drift detector grading curve** (§F.3 seed: cosine ≤ 0.4 = daily `telos_drift`; ≤ 0.2 = elevated; ≤ 0.0 i.e. anti-aligned = CRITICAL).

**Anchored at L1 (not L4) per DRAFT 3 / L0 forcing functions**:

A. **The existence of the salience-emergence mechanism** (§E) — L1-mandated by L0 §2.3 G-9.b P12 retraction.
B. **The existence of telos-alignment operationalization** (§F) — L1-mandated by L0 §P14.c G-6.a forcing function.
C. **Birth-period exemption + post-birth settling window structure** for both detectors (§4, §E.3, §F.4) — pattern is L1-committed; the numerical window length is L4-tunable (item 15).
D. **CI-classification of salience-emergence rule + telos-alignment rule + embedding-model identity** (§E.4, §F.5) — these mutate F-row equivalents and must pass through L1_GOVERNANCE §1.2 + §2.2 attestation gates; see L1_HARD_RULES F23 (DRAFT 9 cascade addition for salience-emergence rule) and §F.5 below for embedding-model identity F-row equivalent.

L1 commits to the **shape** of these decisions; L4 picks values for items 1-20 above; items A-D are non-L4-revisable (L1 commitments anchoring L0 forcing functions).

---

## §D. Constraint satisfaction (one-sentence — per pass-1 chytrid-6)

L0 §5.2's seven constraints are mechanically satisfied — see §1 (form), §2 (vs alternatives), §B (specification). Future L1 revisions must continue to satisfy them; if a constraint is found unworkable, the response is an L0 revision proposal (per L0 §10.2), not L1 weakening.

**DRAFT 3 additional confirmations** (per L0 DRAFT 9 SEALED §17 gate decisions):

- **G-9.b P12 retraction landed**: §E specifies salience/attention emergence with bootstrap-uniform → EWMA-correlation transition (§E.2), anti-uniformity guarantee with birth-period exemption (§E.3, §E.5), CI-classification of the salience-emergence rule (§E.4), and `salience_collapse` immune signal protocol (§E.5). P12 is no longer an L0 principle (per L0 §2.3); it is the L1_TROPISM mechanism in §E.
- **G-6.a P14.c forcing function landed**: §F specifies the operational metric (cosine similarity of recent-sporocarp embedding-centroid vs owner-stated-objective-OR-agent-feedback-trajectory embedding), rolling-window length seed, drift-threshold seed, birth-period exemption duration seed, embedding-model identity declared at genesis as F-row equivalent, and `telos_drift` immune signal protocol. P14.c is no longer aspirational; `telos_drift` is mechanically emittable.
- **G-11.a Cultivation vocabulary**: §G adopts Cultivator/Cultivar/Cultivation in this document's glossary scope; existing P1.b'' "owner" usage remains valid per L0 §1.2 terminology note.
- **Principle renames assimilated**: every cross-reference to L0 principles uses DRAFT 9 SEALED names (P1 Agent-Primary, P2 Eternal Ingestion (Envelope-Gated), P3 Resumable Evolution, P5 Universal Interconnection (Tier-Exempt-Permitted), P7 Mortality (Capacity-for-Death), P8 Eternal Reproduction (Generation-Bounded), P9 Single Integument; P10 Selective Compression, P11 Metabolic Economy, P14 Telos exist at L0 but are owned by other L1/L2 docs).

If any future L0 revision retracts §E or §F mechanisms back to L0 doctrine (i.e., re-elevates P12 / P14 mechanism specifications from L1 to L0), this document responds by deferring to the new L0 spec; if a future L0 revision instead refines the forcing-function shape, §E/§F update accordingly.

---

## §E. Salience / Attention emergence (P12 landing per L0 §2.3 G-9.b retraction)

> **Status**: DRAFT 3 (new in 2026-05-17). Landed per L0 DRAFT 9 SEALED §2.3 P12 retraction notice + Phase γ cascade list §18 "P12 Differential Response → L1_TROPISM (cascade addition)". This section is L1_TROPISM's sole owner of the salience mechanism.
>
> **L0 backing**: P2 Eternal Ingestion (Envelope-Gated) commits to no semantic content filter on intake but envelope-validated admission; without a downstream attention mechanism, the substrate would treat every admitted raw_material kind uniformly. That uniformity is the failure mode P12 (when it was an L0 principle in DRAFT 9 PROPOSAL) was meant to prevent. G-9.b retracted P12 to L1 mechanism territory; this section is that mechanism.

### §E.1 The form

**Salience** is a substrate-internal mapping from `raw_material_kind` → `attention_weight ∈ [0, 1]` used to modulate how strongly each kind of admitted raw material reaches each appetite axis's update rule. It is a cross-cutting modifier (per §B1 DRAFT 3 note), not an appetite. Formally:

```
salience: raw_material_kind × cycle_index → attention_weight ∈ [0, 1]

axis.update_rule(...) reads recent_deltas filtered as:
  effective_delta_strength(δ, axis, cycle) = δ.raw_strength · salience(δ.kind, cycle)
```

where `raw_material_kind` is a substrate-internal taxonomy of admitted-material categories (e.g., `conversation_turn`, `file_change`, `federation_envelope`, `agent_thought_log`, `tool_output`, `error_trace`, ...). The exact kind taxonomy is L4 (per §C item 6 — appetite axis set co-evolves with kind taxonomy in the first 30 days).

**Where salience operates**: between intake (P2 envelope admission, owned by L1_SKIN §2) and gradient advance (step 2 of L1_CONTINUITY §1.1 metabolic cycle, owned by this document §B1 update_rule). Substrate's intake decision is binary (envelope valid → admit); salience modulates the *downstream* attention each admitted item receives.

### §E.2 Bootstrap initialization + emergence transition

The salience map is **uniform at genesis** and **EWMA-correlation-driven in steady state**, with a CI-attested transition point.

**Bootstrap rule** (per L0 §2.3 P12.b retraction notice "uniform until N=100 samples"):

1. At genesis, the substrate initializes `salience(kind, 0) = 1.0` for every kind that appears in the genesis spore-schema's declared kind taxonomy.
2. For each (kind, cycle) pair, the substrate accumulates a **sample count** `n_kind` = number of times raw material of `kind` was absorbed AND was eventually causally cited (per §B1 `causal_in_edges`) by a fruited sporocarp in the same axis-fruiting window.
3. While `n_kind < N` (L1-tunable seed `N = 100`, see §C item 13), salience for that kind remains **uniformly 1.0** — no per-kind differentiation yet.

**Steady-state rule** (EWMA-correlation, activates per-kind once `n_kind ≥ N`):

4. Each cycle, for each kind with `n_kind ≥ N`, the substrate computes a **correlation score**: how often raw_material of this kind appears in the `causal_in_edges` of recently-fruited sporocarps, normalized against this kind's overall ingestion volume.

   ```
   correlation_score(kind, cycle) =
       (cited_count_in_recent_W_cycles(kind) / total_ingested_in_W(kind))
       — baseline_uniform(K)
   ```

   where `W` is the EWMA-window cycle count (L4, seed: same as digest-emission cadence per §B4), `K` is the number of distinct active kinds, and `baseline_uniform(K) = 1/K`.

5. Salience updates by EWMA per cycle:

   ```
   salience(kind, cycle+1) =
       (1 - α) · salience(kind, cycle)  +  α · normalize(correlation_score)
   ```

   where `α` is the EWMA decay rate (L4, seed `α = 0.05/cycle` per §C item 12 — Lindy half-life ~14 cycles, slow enough to prevent oscillation, fast enough to track real shifts). `normalize` projects correlation_score onto `[0, 1]` via softmax across active kinds (so the salience map is a proper probability-like distribution).

6. **Anti-collapse floor**: regardless of EWMA output, `salience(kind, cycle) ≥ ε` for some L4-tunable floor `ε > 0` (seed `ε = 1/(K · 4)` — quarter of uniform). This prevents pathological exclusion of a kind that has not yet been useful but might become useful.

### §E.3 Birth-period exemption + post-birth settling window

Per L0 §2.3 P12.b primordium CF7 ("salience-collapse at birth"): the salience map is *structurally* uniform during birth period (no kind has accumulated `N` samples yet — `N = 100` is far larger than expected birth-period kind appearances per axis). Therefore:

- **During birth period** (per L1_GOVERNANCE §1.3 + §4 above): salience is uniform 1.0 for all kinds. The substrate emits `salience_emergence_pending` observability event (graded daily, NOT immune) at each digest emission to truthfully report "salience differentiation has not yet emerged".
- **At owner-attested `birth_period_terminated`**: per-kind EWMA activates as kinds individually cross `n_kind ≥ N` (which may happen for some kinds and not others — the activation is per-kind, not global).
- **Post-birth settling window** (L4-tunable, seed 100 cycles per §C item 15): for the first 100 cycles after `birth_period_terminated`, the `salience_collapse` detector (§E.5) remains SUSPENDED even though EWMA is active for some kinds. This prevents false-positive collapse detection during the natural early-emergence period when salience differentiation is large by definition (most kinds just crossed `n_kind = N` and EWMA values are high-variance).
- **At settling-window end**: `salience_collapse` detector activates. From here on, the substrate emits no further `salience_emergence_pending` events; only `salience_collapse` (when detected) or steady-state digest-level salience observability.

### §E.4 Salience-emergence rule is CI-classified

The `salience_emergence_rule` (the formulas in §E.2 above plus the parameters `N`, `α`, `W`, `ε`, and the `correlation_score` definition) is a substrate-resident object whose **identity** is contract-identity-level per L0 I2 + L1_GOVERNANCE §1.2 dimension table. Mutations require owner attestation per L1_GOVERNANCE §2.2.

This corresponds to **L1_HARD_RULES F23** (DRAFT 9 cascade addition — salience-emergence rule per Phase γ cascade list §L1_HARD_RULES new F-rows). F23 captures the rule's spore-inheritable CI-level identity; runtime salience values themselves are daily-class (per-cycle updates do not require owner attestation, only the rule that generates them).

**Spore-schema inclusion**: the salience-emergence rule definition (parameters + correlation_score formula) is part of the spore-schema's tier-1 SSoT fields per L1_SCHEMA §3. Child substrates inherit the parent's salience-emergence rule at genesis but accumulate their own salience map from zero (no salience-map inheritance per P8 Eternal Reproduction (Generation-Bounded) — each Cultivar's salience emerges from its own observations).

### §E.5 Anti-uniformity guarantee + `salience_collapse` detector

**Anti-uniformity guarantee**: in steady state (after settling window §E.3), if salience is observed to collapse back to near-uniform across all kinds where EWMA is active, this is anomalous and immune-grade. Specifically:

```
salience_entropy(cycle) = -Σ_kind salience(kind, cycle) · log₂(salience(kind, cycle))
```

Salience entropy is bounded between 0 (one kind dominates, others at floor ε) and `log₂(K_active)` (perfectly uniform across the `K_active` kinds with `n_kind ≥ N`).

**`salience_collapse` immune signal** (per L0 §2.3 P12.b "in steady state" qualifier — Phase γ cascade list confirms this is the L1_TROPISM-mandated detector):

- **Trigger predicate**: salience entropy ≥ `H_threshold` for ≥ `W_collapse` consecutive cycles, where `H_threshold = log₂(K_active) · 0.4` is a seed value (L4-tunable per §C item 14 — "0.4 of max entropy" means "40% as flat as uniform from above", which is essentially uniform-ish; the exact value is L4-tunable). `W_collapse` seed = 30 cycles.

  > **Inverted-logic note** (DRAFT 3 careful framing): salience COLLAPSING toward uniform = entropy HIGH. The "collapse" terminology in L0 §2.3 P12 refers to attention discipline collapsing (becoming undiscriminating). Mathematically that is high entropy, not low. The detector condition is therefore "entropy stays HIGH for too long after EWMA should have differentiated".

- **Grading**: daily-class by default. Elevated if `salience_entropy ≥ log₂(K_active) · 0.5` for ≥ `2 · W_collapse` cycles. CRITICAL if `salience_entropy ≥ log₂(K_active) · 0.6` for ≥ `4 · W_collapse` cycles (i.e., substrate appears actively unable to differentiate — this is mechanically distinct from "EWMA just hasn't had time" because EWMA window `W` is much smaller than `4 · W_collapse`).

- **Emission protocol**: substrate fruits `salience_collapse` sporocarp through §B6 governance gate. Daily-class instances enter DAG immediately; elevated and CRITICAL instances additionally surface through L1_HARD_RULES C-row catalog (DRAFT 9 cascade adds C23 `salience_collapse` per Phase γ cascade list §L1_HARD_RULES). CRITICAL `salience_collapse` is also a P14.c telos-drift correlate (substrate that cannot differentiate kinds is, downstream, likely to fail telos-alignment); the two detectors emit independently but L2_OBSERVABILITY may correlate them.

- **`causal_in_edges` for emitted `salience_collapse`** per §B6: `(salience_entropy_trajectory_in_W_collapse_cycles, salience_map_snapshot_hash, H_threshold_value, template_version)` tuple. I3 self-validation recomputes salience_entropy from the snapshot and verifies the trigger condition crossed.

### §E.6 Salience exposure to agent (read-window participation)

Per §B4 digest budget: the digest exposed to the agent's read-window includes a **salience-summary block** (typed substructure within the structured digest) listing the top-`k` salience values + the salience-entropy current value. The agent reads salience as substrate-attested observable state. Salience is NEVER agent-set or agent-overridable (consistent with P1.c carrier-asymmetry — substrate carries identity; agent inhabits gradient via deltas, does not directly write salience).

If the agent's deltas would *imply* a salience shift (e.g., delta `mark_kind_X_as_important`), the implication runs through normal §E.2 correlation accumulation — there is no fast-path. This is intentional: agent-self-reports about importance are not first-class (per L0 §5.3 intent-not-trusted). Salience emerges from causal observation, not declaration.

### §E.7 Federation interaction (cross-substrate salience)

Per §B9 + L0 P5 Universal Interconnection (Tier-Exempt-Permitted) + L0 P8 Eternal Reproduction (Generation-Bounded): each substrate carries its own salience map. **Salience maps do NOT transfer at federation or reproduction**. Cross-substrate federation sporocarps (per L1_GOVERNANCE §5) feed each receiving substrate's `federation` kind, where they participate in *that substrate's* salience-emergence. This preserves Cultivar-individuality (each Cultivar emerges its own attention discipline) while permitting federation to influence salience indirectly (via sustained federation-envelope flow making that kind correlate with downstream fruitings).

### §E.8 What §E does NOT do

- **Does NOT replace P2 envelope admission**: salience operates *after* admission (a kind with salience 0.01 is still admitted into the DAG; just down-weighted in downstream attention). Per L0 P2 — content filter at intake is forbidden.
- **Does NOT trigger compression**: low-salience kinds are NOT auto-compressed. L0 P10 Selective Compression is owned by L1_SCHEMA + L1_CONTINUITY and is CI-attested per L0 P10.c. Salience is a daily-mechanism input; compression rules are CI-class.
- **Does NOT replace `bet_weakening_quorum`** (L0 §7.4) or `telos_drift` (§F below): salience_collapse is one immune signal among many; it does not subsume the observatory's broader bet-falsifiability machinery.
- **Does NOT classify or attest envelopes**: that is L1_SKIN §2 + L0 P2 envelope-validation discipline.

---

## §F. Telos alignment operationalization (P14.c forcing function per L0 §P14.c G-6.a)

> **Status**: DRAFT 3 (new in 2026-05-17). Landed per L0 DRAFT 9 SEALED §P14.c forcing function ("M26-cascade MUST land this specification; absent that, P14.c remains aspirational and `telos_drift` cannot be mechanically emitted"). This section is L1_TROPISM's sole owner of the telos-alignment computation.
>
> **L0 backing**: P14 Telos (Agent-Symbiotic-Flourishing) at L0 §P14 commits the substrate to a substrate-internal purpose evaluable at daily-ops cadence. P14.c specifies that `telos_drift` is an immune signal class with birth-period exemption; the operational metric, rolling window, and threshold are explicitly delegated to this document under a hard M26-cascade deadline. Until this section lands, P14 enforcement (I12 sole-enforcer per L0 §4 projection table) cannot run.

### §F.1 The form

**Telos-alignment** is a scalar in `[-1, 1]` computed each cycle as cosine similarity between two embedding vectors:

```
telos_alignment(cycle) = cos_sim(
    sporocarp_centroid(rolling_window, cycle),
    objective_embedding
)
```

where:

- `sporocarp_centroid(rolling_window, cycle)` is the embedding-centroid (vector mean, post-L2-normalization) of the **canonical-bytes-rendered text** of every daily-class sporocarp fruited within the rolling window ending at `cycle`. CI-class sporocarps are EXCLUDED (they are governance events, not behavior — see §C item 19 for rationale; this is consistent with L0 §P14 framing of telos-alignment as evaluating substrate's daily decisions).
- `objective_embedding` is one of two vectors depending on owner-stated-objective presence:
  - **If owner has declared an objective at genesis or via CI mutation** (per L0 §P14.b): `objective_embedding = embed(owner_stated_objective_text)`. This text is a tier-1 SSoT field (F-row equivalent — see §F.5).
  - **If no owner objective declared**: `objective_embedding = embed(agent_feedback_trajectory_recent)` where `agent_feedback_trajectory_recent` is the L1_TRAJECTORY-derived recent agent-feedback trajectory text-rendering. See §F.2 below for what "agent feedback" means.

The choice between branch-1 (owner objective) and branch-2 (agent feedback) is **per-substrate at genesis**, declared in the spore-schema, and is itself contract-identity-level (per L0 §P14.b). Switching between branches mid-life requires owner CI attestation.

### §F.2 Rolling window + cadence

**Rolling window length** (seed: 90 substrate-days per L0 §P14.c implicit operational scale = L0 §7.4 wall-clock 90-day Living Bets window). The exact value is L4-tunable per §C item 16. At the seed cadence of 1 metabolic cycle per substrate-day, this is ~90 cycles.

**Computation cadence**: telos-alignment is computed at digest-emission time per step 2 of L1_CONTINUITY §1.1 metabolic cycle (consistent with §B4 digest cadence and §B1 clusterer location). This means telos-alignment is computed *exactly when the substrate is about to expose state to the agent's read-window* — natural alignment between observability emission and self-evaluation. Per §C item 18, the cadence is L4-tunable independently of the cycle clock.

**Branch-2 detail** ("agent feedback trajectory" when no owner objective):
The agent feedback trajectory is derived per L1_TRAJECTORY §6 (`thread_id` grouping primitive when exposed) + §7 (delta-novelty weighting) over deltas that the agent has marked as feedback (an optional opaque delta field; semantics owned by L1_TRAJECTORY). When the agent has *not* marked feedback deltas, the centroid is computed over the agent's last-K deltas of any kind (K seeded as the same rolling-window cycle count). The intent is captured at L0 §P14.b: "agent-perceived utility" operationalized by L1_TROPISM. This document operationalizes it as "the embedding-centroid of deltas the agent has either marked as feedback OR (fallback) the agent's recent delta stream" — both signals are joint-history-derived (consistent with L0 §5.3 fossil-record-honest).

### §F.3 Drift threshold + detector grading

**Drift threshold** (seed: cosine similarity ≤ 0.4 per L0 §P14.c forcing-function example seed). L4-tunable per §C item 17. The threshold is interpreted as "centroid of recent fruitings has drifted such that cosine similarity to the objective is below threshold" — substrate's recent behavior is materially out of alignment.

**Detector grading** (DRAFT 3 explicit, seed per §C item 20):

| Cosine similarity range | Status | Sporocarp emitted |
|---|---|---|
| ≥ 0.6 | aligned | none |
| 0.4 < ≤ 0.6 | drifting (sub-threshold) | observability `telos_alignment_low` (NOT immune) |
| 0.2 < ≤ 0.4 | drift (daily) | `telos_drift` daily-class |
| 0.0 < ≤ 0.2 | drift (elevated) | `telos_drift` elevated |
| ≤ 0.0 (anti-aligned, orthogonal-or-opposed) | drift (CRITICAL) | `telos_drift` CRITICAL |

`telos_drift` emission protocol mirrors `salience_collapse` (§E.5): the daily-class instance enters DAG immediately via §B6 gate; elevated and CRITICAL instances additionally surface through L1_HARD_RULES C-row catalog (DRAFT 9 cascade adds C24 `telos_drift_critical` per Phase γ cascade list §L1_HARD_RULES new C-rows).

**`causal_in_edges` for emitted `telos_drift`** per §B6: `(sporocarp_centroid_hash, objective_embedding_hash, cosine_value, rolling_window_start_cycle, rolling_window_end_cycle, embedding_model_identity_hash, template_version)` tuple. I3 self-validation recomputes the centroid from the rolling-window sporocarp set (which is enumerable per §B6 DAG insertion order) and verifies the trigger.

### §F.4 Birth-period exemption + post-birth settling window

Per L0 §P14.c "Telos drift detection has a birth-period exemption (substrate emits `telos_alignment_pending` instead)":

- **During birth period** (per §4 + L1_GOVERNANCE §1.3): telos-alignment is NOT computed; substrate emits `telos_alignment_pending` observability event (graded daily, NOT immune) at each digest emission. Rationale: in birth period, rolling-window cycle count is below seed window length; centroid is undefined or extremely noisy; comparison to objective embedding is mathematically vacuous (per L0 §P14.c primordium HF11 fix).
- **At owner-attested `birth_period_terminated`**: telos-alignment computation activates *after the same post-birth settling window* shared with `salience_collapse` (§E.3 — seed 100 cycles). This ensures the rolling-window cycle count has reached at least the L4-tunable settling window before any cosine value is interpreted.
- **At settling-window end**: `telos_drift` detector activates. The substrate stops emitting `telos_alignment_pending`; thereafter only `telos_drift` (when triggered) or steady-state digest-level `telos_alignment_score` (the raw cosine value per cycle, NOT an immune signal, exposed via §B4 digest as substrate-attested observability).

**Per §C item 15** the settling window seed is 100 cycles; the rationale is that 100 cycles also matches the salience EWMA sample threshold `N = 100` (§E.2) — a single L4-tunable knob ("how many cycles after birth-period termination before substrate self-observation arms?") suffices for both detectors.

### §F.5 Embedding-model identity (F-row equivalent)

Per L0 §9.4 canonical-bytes implication (canonical-bytes serialization is part of the spore-schema and a tier-1 SSoT field per L1_SCHEMA): the embedding model used to compute `embed(...)` in §F.1 is **part of the substrate's identity**. Changing the embedding model retroactively changes every prior telos-alignment computation — a different model produces different vectors, different centroids, different cosine values, different `telos_drift` history.

**Therefore** (DRAFT 3 commitment, L1-level not L4-level):

- The **embedding model identity** is declared at genesis as an **F-row equivalent** field: `embedding_model_identity = (model_name, model_version, model_canonical_bytes_hash)`. The `model_canonical_bytes_hash` is the canonical-bytes hash of the model parameters (or, for an external API service per §C item 4, the canonical-bytes hash of the service-identity declaration + service-attested model version).
- **Mutation requires owner attestation** per L1_GOVERNANCE §2.2 (full anchor-surface protocol: canonical bytes + operator_witness + anchor-side nonce + dual-clock + DAG-enumeration closure check), exactly as for any F-row.
- **Spore-inheritable**: child substrates inherit the parent's embedding-model-identity at genesis. A child may CI-mutate to a different model post-genesis (per L1_GOVERNANCE §2.2) but inheritance is the default.
- **Storage cost**: full model parameters do NOT need to live in the spore-schema; the canonical-bytes hash + a reference (URI / OCI digest / local-path + checksum) is sufficient. The substrate at every metabolic cycle verifies the embedding model's bytes match the declared hash (mismatched → I3 self-validation fails → quarantine).
- **L1_HARD_RULES new F-row**: `F_embedding_model_identity` (numbered as part of the DRAFT 9 cascade addition F18-F23 set — the Phase γ cascade list specifies F-rows for compression-rule registry, cost-budget thresholds, telos-objective declaration, generation-depth bounds, consensus-floor threshold, and salience-emergence rule; this document calls out an additional F-row for embedding-model identity that the Phase γ cascade list did not enumerate). L1_HARD_RULES DRAFT 3+ revision should add this F-row; until L1_HARD_RULES catches up, this document anchors the requirement at L1 level.

> **Why this is non-negotiable**: per L0 §P14.c forcing function — without a stable embedding-model identity, two recomputations of `telos_alignment` at different cycles would produce different values even with identical sporocarp sets and unchanged objective, because a silently-upgraded embedding model would change all the vectors. I3 self-validation (per §B6) needs to recompute deterministically. The embedding-model-identity F-row makes the recomputation deterministic; without it, telos-alignment is non-falsifiable (any drift detection can be argued to be embedding-model-version artifact).

### §F.6 Owner-stated objective lifecycle

Per L0 §P14.b: owner MAY (not must) declare an objective at genesis or via CI events.

- **At genesis**: owner-stated objective is part of the spore-schema's tier-1 SSoT — F-row equivalent **F_telos_objective** (corresponding to the Phase γ cascade list's enumerated F20 telos-objective declaration). When present at genesis, branch-1 of §F.1 is selected and locked unless owner CI-mutates.
- **Post-genesis CI mutation** (per L1_GOVERNANCE §2.2): owner attests `telos_objective_set:{new_objective_text}`. The substrate computes the new `embed(new_objective_text)` under the current embedding-model-identity (§F.5), records both the objective text and the embedding canonical-bytes hash, and uses the new objective from the next cycle onward. Prior telos-alignment values are NOT retroactively recomputed; they remain causally bound to the prior objective per L0 I4 Full-Fidelity Causal DAG (Compression-Aware).
- **Switching to no-objective branch**: owner may CI-attest `telos_objective_unset`, which causes branch-2 (agent-feedback-trajectory) to take over from the next cycle onward.
- **Multiple objectives** (out of scope): a single substrate carries at most one active objective at a time. Multi-objective composition is L4+ (e.g., the substrate may eventually be CI-extended to carry a list of objectives with a composition rule — but L1 commits the single-objective default).

### §F.7 Interaction with §E salience + L1_TRAJECTORY

Per L0 §P14.a: "L1_TROPISM specifies how telos-alignment is computed (likely: trajectory-cluster coherence per L1_TRAJECTORY + agent-feedback-trajectory)". DRAFT 3 chooses the **simpler operational metric** (cosine similarity of embedding-centroids) for §F.1 rather than trajectory-cluster-coherence. Rationale:

- **Cosine-similarity-of-centroids is L4-implementable in one cycle** with no clustering algorithm dependency; L1_TRAJECTORY's `cluster_C` is CI-classified (per L1_TRAJECTORY §4) and changing the clusterer must NOT silently break telos-alignment.
- **Trajectory-cluster-coherence is an upgrade path**: an L4 implementation may, after observing the simpler metric in production, propose CI-attested upgrade to a trajectory-cluster-coherence formulation (which would itself require co-mutating the embedding-model identity and the rule under L1_GOVERNANCE §2.2). The simpler form is the seed; the upgrade is left open.
- **Salience independence**: §E salience operates on `raw_material_kind`; §F operates on sporocarp centroid. They do not share a computational pathway; they CAN correlate (substrate that loses salience differentiation likely also drifts in telos) but neither subsumes the other.

When L1_TRAJECTORY-derived trajectory data is needed for branch-2 (§F.2 agent-feedback fallback), telos-alignment imports L1_TRAJECTORY's recent-window agent-marked-feedback delta set; if that set is empty, falls back to the agent's recent delta stream as specified in §F.2.

### §F.8 What §F does NOT do

- **Does NOT replace bet_weakening_quorum** (L0 §7.4): telos_drift is one immune signal; `bet_weakening_quorum` is the Living Bets meta-falsifiability machinery (L2_OBSERVABILITY). They are independent but correlated emissions.
- **Does NOT enforce owner stating an objective**: per L0 §P14.b explicit "MAY (not must)". Branch-2 (agent-feedback-trajectory) is a first-class alternative, not a fallback signaling failure.
- **Does NOT compute alignment over CI-class sporocarps**: per §C item 19, CI-class sporocarps are governance events; including them in the centroid would conflate behavior with governance and make telos-alignment partially owner-controlled (against the spirit of I12 substrate-evaluable purpose).
- **Does NOT block CI events**: when telos-drift is CRITICAL, the substrate emits a CRITICAL `telos_drift` sporocarp; it does NOT auto-mortality. The decision to act on CRITICAL telos-drift (CI mutate the objective, retire the bet per L0 §7.5, self-euthanize per P7) is owner-gated and observatory-mediated.
- **Does NOT cross substrates**: each Cultivar's telos-alignment is computed against its own sporocarp set + its own objective. Federation does not aggregate telos-alignment (per §B9 + P1.c carrier-asymmetry — telos is per-pair, not per-mycelium).

---

## §G. Glossary (DRAFT 3 additions per L0 §1.2 G-11.a Cultivation)

This section adds doctrinal-vocabulary entries specific to this document's mechanisms. Terms also defined at L0 §12 glossary are cross-referenced; new terms private to this document are defined here authoritatively.

### §G.1 Cultivation vocabulary (per L0 §1.2 G-11.a)

| Term | Definition (this document scope) | L0 cross-ref |
|---|---|---|
| **Cultivation** | The doctrinally-named relationship type between the human owner and the Myco substrate. Asymmetric-care (Cultivator provides resources; Cultivar grows within them) + co-evolution (Cultivator's intent shapes which Cultivar varieties thrive). | L0 §1.2 |
| **Cultivator** | The human owner of a Myco substrate, in their **relational role** to the substrate. (When emphasizing **governance role** — attesting CI events through anchor surface — the term "owner" remains valid per L0 §1.2 terminology note.) Cross-ref P1.b'' L0 governance gate. | L0 §1.2, §P1.b'' |
| **Cultivar** | The Myco substrate (kernel + dag.cb + state_dir + skin + appetite gradient + sporocarp DAG + the salience map of §E + the telos-alignment computation state of §F), considered as the species-instance under Cultivation. Substrate-ID identifies a single Cultivar; the Cultivar persists across operator-connection reconnections (per P1.c carrier-asymmetry — substrate carries identity continuum). | L0 §1.2, §P1.c |
| **Cultivar-individuality** (this doc) | The principle (per §E.7 + L0 P8 Eternal Reproduction (Generation-Bounded)) that each Cultivar emerges its own salience map, accumulates its own telos-alignment history, and computes its own observatory signals — even when descended from a common parent. Inheritance is rule-level (salience-emergence rule, embedding-model identity, telos objective) not state-level (no salience-map transfer, no telos-history transfer). | derived from L0 P8 + §E.7 + §F.7 |

### §G.2 Mechanism-vocabulary additions (this document's mechanisms)

| Term | Definition (this document) | Section |
|---|---|---|
| **Salience map** | Substrate-internal mapping `raw_material_kind → attention_weight ∈ [0, 1]` per cycle; emerges from observed correlation between intake kinds and downstream sporocarp fruitings. | §E.1, §E.2 |
| **Salience-emergence rule** | The CI-classified rule (parameters `N`, `α`, `W`, `ε` + `correlation_score` formula) generating the salience map. Substrate-resident, spore-inheritable, F-row equivalent F23. | §E.2, §E.4 |
| **Salience entropy** | `-Σ salience(kind) · log₂(salience(kind))` over kinds with `n_kind ≥ N`. Range `[0, log₂(K_active)]`. High = uniform = collapse-like. | §E.5 |
| **`salience_collapse`** | Immune-grade sporocarp emitted when salience entropy stays HIGH for ≥ `W_collapse` cycles in steady state. Daily / elevated / CRITICAL graded per entropy magnitude + duration. | §E.5 |
| **`salience_emergence_pending`** | Observability (not immune) sporocarp emitted at every digest during birth period + post-birth settling window, declaring "salience differentiation has not yet activated for some/all kinds". | §E.3 |
| **Anti-collapse floor** | Lower bound `ε > 0` on `salience(kind)` regardless of EWMA output, preventing pathological exclusion of any kind. | §E.2 |
| **Telos-alignment** | Scalar in `[-1, 1]` computed each cycle as cosine similarity between the substrate's recent-sporocarp embedding-centroid and the (owner-objective OR agent-feedback-trajectory) embedding. | §F.1 |
| **Telos rolling window** | The cycle range over which the sporocarp centroid is computed (seed 90 cycles ≈ 90 substrate-days at default cadence). | §F.2 |
| **Sporocarp centroid** | Embedding-centroid (L2-normalized vector mean) of canonical-bytes-rendered texts of daily-class sporocarps in the rolling window. CI-class sporocarps EXCLUDED. | §F.1, §F.8 |
| **Objective embedding** | `embed(owner_stated_objective_text)` if owner-declared (branch-1), else `embed(agent_feedback_trajectory_text)` (branch-2). | §F.1, §F.2 |
| **Embedding-model identity** | The substrate-resident F-row equivalent declaring `(model_name, model_version, model_canonical_bytes_hash)`. Spore-inheritable. CI-mutation only. Required for telos-alignment determinism per §F.5. | §F.5 |
| **`telos_drift`** | Immune-grade sporocarp emitted when telos-alignment falls below seed threshold 0.4 cosine in steady state. Daily / elevated / CRITICAL graded. | §F.3 |
| **`telos_alignment_pending`** | Observability (not immune) sporocarp emitted during birth period + post-birth settling window. | §F.4 |
| **`telos_alignment_low`** | Observability (not immune) sporocarp for sub-threshold-but-not-drift range (0.4 < cosine ≤ 0.6); pre-immune warning signal. | §F.3 |
| **Post-birth settling window** | L4-tunable cycle count (seed 100) after owner-attested `birth_period_terminated` before salience_collapse + telos_drift detectors arm. Single shared knob for both detectors. | §E.3, §F.4 |
| **Branch-1 / Branch-2 telos** | Branch-1 = owner-stated-objective comparison; branch-2 = agent-feedback-trajectory comparison. Per-substrate at genesis, CI-mutable. | §F.1, §F.6 |

### §G.3 Out-of-scope terms (this document defers)

These terms appear in cross-references but are owned by other documents:

| Term | Owner |
|---|---|
| **Anchor surface** + sub-mechanisms §9.2.1–§9.3.6 | L0 §9 (decomposed) + L1_GOVERNANCE §2.2 (protocol) |
| **Compression-invariant set**, **selective compression**, **compression-rule registry** | L0 P10 + L1_SCHEMA + I9 |
| **Cost budget**, **budget_exhausted**, **signals #7/#8/#9** | L0 P11 + I10 + L2_OBSERVABILITY |
| **bet_weakening_quorum**, **bet_retired_proposal**, **Living Bets observatory** | L0 §7 + L2_OBSERVABILITY |
| **Generation depth**, **reproduction rate limit**, **per-substrate lifetime quota** | L0 §16 + L1_GOVERNANCE |
| **Successor chain**, **legacy sub-state**, **orphaned sub-state** | L0 §15 + L1_GOVERNANCE §3.2 |
| **Population-level consensus**, **Byzantine consensus floor** | L0 P15 retracted → L2_FEDERATION |
| **Spatial-locus breach**, **state_dir watcher** | L0 P13 folded into P9 + I8 → L1_SKIN |
| **Adversarial owner**, **duress attestation** | L0 §14 + L2_TRUST_MODEL |
| **`cluster_C`**, **thread_id**, **trajectory derivation** | L1_TRAJECTORY |
| **i64-nanosecond canonical timestamp**, **anchor-surface trusted wall-clock** | L0 §13 + L1_CONTINUITY + L1_SCHEMA |

---

## §H. DRAFT 3 cascade-readiness note

This DRAFT 3 lands the L1_TROPISM-side obligations from L0 DRAFT 9 SEALED:

1. **§E lands G-9.b P12 retraction** — salience/attention emergence as L1_TROPISM mechanism. `salience_collapse` is now mechanically emittable.
2. **§F lands G-6.a P14.c forcing function** — telos-alignment operationalization. `telos_drift` is now mechanically emittable.
3. **§G adopts G-11.a Cultivation vocabulary** — Cultivator/Cultivar/Cultivation defined within this document's glossary scope.
4. **§4 + §B + §C + §D** updated for renamed L0 principles, exemption hooks, deferred-list extensions, and constraint-satisfaction extensions.

**Adjacent cascade work** (NOT this document; flagged for M26-cascade follow-ups so this DRAFT 3 is not orphaned):

- **L1_HARD_RULES** needs to land **C23 `salience_collapse`** + **C24 `telos_drift_critical`** + **F23 salience-emergence-rule** + **F_embedding_model_identity** + **F_telos_objective_declaration** in its C-row / F-row catalog (Phase γ cascade list §L1_HARD_RULES new C-rows and new F-rows — §F.5 of this document anchors the embedding-model-identity F-row requirement until L1_HARD_RULES catches up).
- **L2_OBSERVABILITY** needs to add **`salience_collapse`** + **`telos_drift`** + **`salience_emergence_pending`** + **`telos_alignment_pending`** + **`telos_alignment_low`** to its immune-grade sporocarp catalog and observability-event catalog respectively, plus the variance→correlation composite-weighting transition (telos-alignment is the outcome signal that activates correlation weighting per L0 §7.3 composite signal #10).
- **L1_SCHEMA** needs to record `embedding_model_identity` + `telos_objective` as tier-1 SSoT fields and accept their CI-mutation flow.
- **L1_GOVERNANCE** §1.2 dimension table needs rows for salience-emergence-rule (CI) + embedding-model-identity (CI) + telos-objective (CI).
- **L3_PACKAGE_MAP** §7 `kernel/tropism` needs new sub-modules for salience-emergence + telos-alignment-computer (per Phase γ cascade list §L3_PACKAGE_MAP `kernel/tropism` extensions).

These cascades are M26-cascade items B-onwards; this DRAFT 3 is M26-cascade A1.
