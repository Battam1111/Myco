# L1 — Tropism (positive dispatch form for Myco v0.9)

> L1 for positive dispatch satisfying L0 §5.2 + two L0-mandated mechanisms (§E salience, §F telos). All numeric thresholds L1-tunable unless specified.

---

## §1. The form

Dispatch IS **tropism**: substrate maintains intrinsic **appetites**, each with a **tropic gradient** updated each metabolic cycle. Agent (per P1.c) inhabits gradient as perturbation source + consumer. Substrate exposes gradient state via agent's read-window; agent emits **deltas**; substrate absorbs; gradients update. Gradient crossing **fruiting trigger** → substrate **fruits a sporocarp** (typed, content-addressed, causally-stamped per I4) anchoring gradient field for I2 / I3 / I7 / I4.

## §2. Why tropism (vs L0 §5.2 rivals)

| Rival | Why tropism preferred |
|---|---|
| Continuous metabolic stream | Tropism IS that PLUS gradient-coupling making agent definitionally a participant (P1.c). Bare stream → back-door client-server. |
| NL semantic dispatch | LLM-call becomes dispatch surface → LLM-router wrapper. |
| Capability composition | Asymmetric grant. Useful as sporocarp metadata, not dispatch primitive. |
| Algebraic primitives | Presumes purity + statelessness; substrate IS state. |
| Reactive stream | Strip gradient → no answer to "what does substrate want next?". |

Excluded by L0 §5.2: verbs, request/response, hybrid, coexistence-with-verbs-at-birth (I6). Two L1 mechanisms flow from L0: (i) **differential salience** (§E, per P12 retraction); (ii) **telos-alignment** (§F, per §P14.c).

## §3. Two-layer structure

- **Gradient configuration**: continuously-evolving multi-dimensional; one axis per appetite. Reciprocally asymmetric per P1.c.
- **Sporocarp**: substrate-initiated discrete records anchoring medium to checkable observables. Typed; pass skin envelope; carry causal-proofs per §B6.

**Sporocarps ≠ verbs**: verb agent-initiated; sporocarp substrate-initiated. Arrow reversed.

## §4. Birth period vs steady state

- **Birth period**: seed thresholds + seed update-rules. End per L1_GOVERNANCE §1.3 (maturity-attested OR 180-day ceiling).
- **Steady state**: emergent thresholds activate; gradient rules MAY evolve per P3 (CI-gated).
- **Birth-period detectors SUSPENDED** during birth + post-birth settling window; arm at owner-attested `birth_period_terminated` + settling: `bet_weakening_quorum` (L0 §7.4) emits `bet_weakening_evaluation_suspended`; `salience_collapse` (P12.b) emits `salience_emergence_pending`; `telos_drift` (§P14.c) emits `telos_alignment_pending`.

## §A. Continuity hooks

L1_CONTINUITY owns cycle cadence, dormancy, recovery, quarantine, delta atomicity, cold-resume. Tropism's gradient-advance + sporocarp-emit + DAG-update are steps 2-3 of L1_CONTINUITY §1.1.

## §B. Specification

**B1. Appetite axis schema** — Each appetite carries `name` (L0 §5.1); `computation_locality` (substrate-internal); `domain`; `update_rule` (pure of gradient-state, recent-deltas, recent-sporocarps, time); `seed_fruiting_trigger`; `threshold_emergence_rule` (L1_GOVERNANCE §1.2); `causal_proof_template` + `template_version` — sporocarp `causal_in_edges` includes `(delta_set, gradient-snapshot-hash, threshold-value, template_version)`. Template versioning evolves per P3 (CI); `template_version_registry` active-prefix + archived-tail per L1_GOVERNANCE §3.1. Trajectory derivation runs in-substrate (no network egress). **Salience NOT an appetite axis** (P12): cross-cutting modifier over `raw_material → axis routing`; rule CI (F25), runtime daily. **Telos-alignment NOT an appetite axis** (P14.c): cross-cutting at digest-emission; rule + embedding-model identity CI (§F), per-cycle daily.

**B2. Initial appetite set** — Illustrative seed, NOT normative. Substrate canon selects at genesis; L4 MAY mutate first 30 days: `hunger` (unmetabolized intake) → P2; `drift` (graph-disconnection) → P5 / I5; `decay` (staleness) → P4; `federation-pull` → P8 / I7; `evolution-tension` → P3; `skin-pressure` → P9 / I8. **Open**: `mortality-signal` axis-vs-FSM-predicate L4-choose. Cost-budget signals (#7/#8/#9) NOT consumed as tropism axis.

**B3. Sporocarp type tree (seed)** — `intake` / `digestion` / `refinement` / `federation` (daily); `governance_event` (axis_schema_change, type_addition, classifier_change — CI); `immune_event` (envelope_malformed, attestation_invalid — daily/elevated/CRITICAL).

**B4. Gradient exposure protocol** — Bounded, structured, stateless digest to agent's read-window: **Bounded** B ≤ L0 §7 signal-#6 × consumption fraction (L4 10-50%); **Structured** typed object listing each appetite's gradient + recent K sporocarps + recent M unabsorbed deltas + metabolic-budget metrics; **Stateless** cold-resumable from digest alone.

**B5. Delta intake surface** — L1_SKIN §2 envelope schema. Per P2: shape-agnostic; envelope-checked only.

**B6. Sporocarp governance gate** — Daily class → DAG immediately. CI-class emits `attestation_request` via anchor; pending → published on owner attestation. Every fruiting carries `causal_in_edges` per B1; I3 recomputes; unverifiable rejected pre-DAG. Salience + telos immune sporocarps (`salience_collapse` §E, `telos_drift` §F) fruit through this gate; both SUSPENDED in birth.

**B7-B10**:
- **B7** Continuity recovery → L1_CONTINUITY §3. **B8** Causal DAG → L1_SCHEMA §2; edge classes: `gradient_causation`, `delta_source`, `sporocarp_derivation`, `federation_coupling`, `governance_resolution`. **B9** Federation surface → L1_GOVERNANCE §5; tropism contributes cross-substrate gradient coupling (mode L4).
- **B10** Self-hosting bootstrap: kernel substrate IS ordinary substrate with one specialization — `evolution-tension` bound to kernel source repo; no outbound RPC. Kernel substrate IS a Cultivar under Cultivation by its human owner.

## §E. Salience / Attention emergence (P12 landing)

**§E.1 The form**: **Salience**: `raw_material_kind → attention_weight ∈ [0, 1]` modulating each kind's reach into axis update rules. Algorithm: `algorithms/ewma_salience.md` (bootstrap until N=100 samples → EWMA per-kind; decay seed 0.05/cycle; anti-collapse floor; entropy-based `salience_collapse` grading). Kind taxonomy (`conversation_turn`, `file_change`, `federation_envelope`, etc.) L4. Operates between intake (L1_SKIN §2) and gradient advance — intake decision binary; salience modulates downstream.

**§E.2 Birth-period + post-birth settling**: Birth: salience uniform 1.0; emits `salience_emergence_pending` (daily, NOT immune). At `birth_period_terminated`: EWMA activates per-kind as kinds cross `n_kind ≥ N`. Post-birth settling window (seed 100 cycles): `salience_collapse` SUSPENDED.

**§E.3 CI classification + scope**: `salience_emergence_rule` (formulas + N, α, W, ε) IS substrate-resident CI per I2 + L1_GOVERNANCE §1.2; mutations require owner attestation. **L1_HARD_RULES F25**. Spore-schema tier-1; child substrates inherit rule + accumulate salience from zero (P8).

**§E.4 Agent exposure + federation + scope**: §B4 digest includes salience-summary block (top-`k` + entropy). Substrate-attested; NEVER agent-set/overridable (P1.c). Each substrate carries own salience map; maps do NOT transfer at federation or reproduction; cross-substrate sporocarps feed receiving substrate's `federation` kind. **§E does NOT**: replace P2 envelope admission; trigger compression (L0 P10); replace `bet_weakening_quorum` or `telos_drift`; classify/attest envelopes.

## §F. Telos alignment operationalization (P14.c)

**§F.1 The form**: **Telos-alignment** scalar `[-1, 1]`. Algorithm: `algorithms/telos_drift.md` (cosine of sporocarp centroid vs objective embedding; 5-grade threshold table from aligned ≥0.6 to CRITICAL ≤0.0 / C24; causal_in_edges; embedding-model identity F-row). Per-substrate at genesis, CI; switching branches requires owner CI attestation. Branch selection: owner objective declared (P14.b) → `embed(owner_stated_objective_text)`; no objective → `embed(agent_feedback_trajectory_recent)` (L1_TRAJECTORY-derived).

**§F.2 Window + cadence**: Window seed 90 substrate-days (= L0 §7.4 Living Bets window). Cadence: digest-emission per L1_CONTINUITY §1.1 step 2.

**§F.3 Birth-period + post-birth settling**: Birth: NOT computed; emits `telos_alignment_pending` (daily, NOT immune). At `birth_period_terminated`: activates after settling window shared with `salience_collapse` (§E.2 seed 100 cycles). Single shared knob.

**§F.4 Owner-stated objective lifecycle**: Owner MAY (not must) declare at genesis or via CI (P14.b). Genesis F-row F20: branch-1 locked unless CI-mutated. CI mutation `telos_objective_set:{new_text}`: substrate computes `embed(...)` under current embedding-model-identity, records text+hash, uses from next cycle; prior values NOT retroactively recomputed (I4). `telos_objective_unset` → branch-2 from next cycle. Multi-objective L4+.

**§F.5 Interaction + scope**: Per P14.a: cosine-similarity chosen over trajectory-cluster-coherence — L4-implementable in one cycle, no clustering dependency; cluster_C is CI and MUST NOT silently break telos-alignment. **§F does NOT**: replace `bet_weakening_quorum`; enforce owner stating objective (P14.b MAY-not-must); compute over CI-class sporocarps; block CI events (CRITICAL telos_drift owner-gated, not auto-mortality); cross substrates (per-pair).

## §G. Doc-private terms

- **Cultivar-individuality** (§E.4 + P8): each Cultivar emerges own salience map + accumulates own telos history; inheritance is rule-level (salience rule, embedding-model identity, telos objective), not state-level.
