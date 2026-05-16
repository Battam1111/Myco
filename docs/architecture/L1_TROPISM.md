# L1 — Tropism (positive dispatch form for Myco v0.9)

> **Status**: DRAFT 3. L1 for positive dispatch satisfying L0 §5.2 + two L0-mandated mechanisms (§E salience, §F telos). Governed by L0. Cultivation vocabulary at L0 §1.2.

---

## §1. The form

Dispatch is **tropism**: substrate maintains intrinsic **appetites**, each with a **tropic gradient** updated each metabolic cycle (cadence: L1_CONTINUITY). Agent (active operator-connection per P1.c) inhabits gradient as perturbation source + consumer. Substrate exposes gradient state via agent's read-window; agent emits **deltas**; substrate absorbs; gradients update. Gradient crossing **fruiting trigger** → substrate **fruits a sporocarp** (typed, content-addressed, causally-stamped record per I4) anchoring gradient field for I2 / I3 / I7 / I4.

## §2. Why tropism (vs L0 §5.2 rivals)

| Rival | Why tropism preferred |
|---|---|
| Continuous metabolic stream | Tropism IS that PLUS gradient-coupling making agent definitionally a participant (P1.c). Bare stream → back-door client-server. |
| NL semantic dispatch | LLM-call becomes dispatch surface → LLM-router wrapper. NL→handler-table secretly re-introduces verbs. |
| Capability composition | Asymmetric grant. Useful as sporocarp metadata, not dispatch primitive. |
| Algebraic primitives | Presumes purity + statelessness; substrate IS state. |
| Reactive stream | Strip gradient → no answer to "what does substrate want next?". |

Excluded by L0 §5.2: verbs, request/response, hybrid, coexistence-with-verbs-at-birth (I6). Two L1 mechanisms flow from L0: (i) **differential salience** (§E, per P12 retraction); (ii) **telos-alignment operationalization** (§F, per §P14.c).

## §3. Two-layer structure

- **Gradient configuration** (medium): continuously-evolving multi-dimensional; one axis per appetite. Jointly perturbed — reciprocally asymmetric per P1.c.
- **Sporocarp** (observable): substrate-initiated discrete records anchoring medium to checkable observables. Typed; pass skin envelope; carry causal-proofs per §B6.

**Sporocarps ≠ verbs**: verb agent-initiated; sporocarp substrate-initiated (gradient crosses trigger → substrate fruits → agent observes). Arrow reversed.

## §4. Birth period vs steady state

**Birth period**: seed thresholds + seed update-rules. End per L1_GOVERNANCE §1.3 (maturity-attested OR 180-day ceiling). Both paths meet at same `birth_period → steady_state` transition.

**Steady state**: emergent thresholds activate; gradient rules may evolve per P3 (CI-gated).

**Birth-period detectors** — all SUSPENDED during birth + post-birth settling window (§E.3 + §F.4); arm at owner-attested `birth_period_terminated` + L1-tunable settling:

- `bet_weakening_quorum` (L0 §7.4): emits `bet_weakening_evaluation_suspended`.
- `salience_collapse` (P12.b): emits `salience_emergence_pending` — §E.
- `telos_drift` (§P14.c): emits `telos_alignment_pending` — §F.

## §A. Continuity hooks

L1_CONTINUITY owns cycle cadence, dormancy, recovery, quarantine, delta atomicity, cold-resume. Tropism's gradient-advance + sporocarp-emit + DAG-update are steps 2-3 of L1_CONTINUITY §1.1.



## §B. Specification

### B1. Appetite axis schema

Each appetite: `name` (L0 §5.1); `computation_locality` (substrate-internal); `domain`; `update_rule` (pure of gradient-state, recent-deltas, recent-sporocarps, time); `seed_fruiting_trigger`; `threshold_emergence_rule` (L1_GOVERNANCE §1.2); `causal_proof_template` + `template_version` (sporocarp `causal_in_edges` includes `(delta_set, gradient-snapshot-hash, threshold-value, template_version)`; I3 re-derives).

**Template versioning**: evolves per P3 (CI); `template_version_registry` active-prefix + archived-tail per L1_GOVERNANCE §3.1. **Clusterer location**: trajectory derivation runs in-substrate (no network egress); fires at digest-emission + echo-chamber cadence. **Salience NOT an appetite axis** (P12): cross-cutting modifier over `raw_material → axis routing`; rule CI (F25), runtime daily. **Telos-alignment NOT an appetite axis** (P14.c): cross-cutting at digest-emission; rule + embedding-model identity CI (§F.5), per-cycle daily.

### B2. Initial appetite set — illustrative seed, NOT normative

Substrate canon selects axes at genesis; L4 may mutate first 30 days.

- `hunger` (unmetabolized intake) → P2
- `drift` (graph-disconnection) → P5 / I5
- `decay` (staleness) → P4
- `federation-pull` → P8 / I7
- `evolution-tension` → P3
- `skin-pressure` → P9 / I8

**Open: `mortality-signal` axis** (P7): axis-vs-FSM-predicate L4-choose. Threshold + rule CI. **Cross-cutting modifiers**: salience (§E), telos (§F). Cost-budget signals (#7/#8/#9) NOT consumed as tropism axis; degraded-op L1_CONTINUITY-mediated.

### B3. Sporocarp type tree — seed (NOT normative)

Substrate canon may add types post-birth (CI): `intake` / `digestion` / `refinement` / `federation` (daily); `governance_event` (axis_schema_change, type_addition, classifier_change, etc. — CI); `immune_event` (envelope_malformed, attestation_invalid, etc. — daily/elevated/CRITICAL).

### B4. Gradient exposure protocol

Bounded, structured, stateless digest to agent's read-window: **Bounded** B ≤ L0 §7 signal-#6 × consumption fraction (L4 10-50%); **Structured** typed object listing each appetite's gradient + recent K sporocarps + recent M unabsorbed deltas + metabolic-budget metrics; **Stateless** cold-resumable from digest alone.

### B5. Delta intake surface

L1_SKIN §2 envelope schema. Per P2: shape-agnostic; envelope-checked only.

### B6. Sporocarp governance gate

Daily → DAG immediately. CI-class: emits `attestation_request` via anchor (L0 §9.2.2 + §9.2.5; L1_GOVERNANCE §2.2); pending → published on owner attestation. **Causal proof**: every fruiting carries `causal_in_edges` per B1 template; I3 recomputes; unverifiable rejected pre-DAG. **Salience + telos immune sporocarps** (`salience_collapse` §E, `telos_drift` §F) fruit through this gate; both SUSPENDED in birth; arm at `birth_period_terminated` + settling window.

### B7-B10

- **B7** Continuity recovery → L1_CONTINUITY §3.
- **B8** Causal DAG (L1_SCHEMA §2). Edge classes: `gradient_causation`, `delta_source`, `sporocarp_derivation`, `federation_coupling`, `governance_resolution`.
- **B9** Federation surface (L1_GOVERNANCE §5): discovery + peer-trust freshness L1_GOVERNANCE-owned; tropism contributes cross-substrate gradient coupling. Coupling mode L4.
- **B10** Self-hosting bootstrap: kernel substrate is ordinary substrate (B2 + B3) with one specialization — `evolution-tension` bound to kernel source repo; no outbound RPC. Kernel substrate IS a Cultivar under Cultivation by its human owner.



## §E. Salience / Attention emergence (P12 landing per L0 §2.3 G-9.b)

### §E.1 The form

**Salience**: `raw_material_kind → attention_weight ∈ [0, 1]` modulating each kind's reach into axis update rules.

```
salience: raw_material_kind × cycle_index → attention_weight ∈ [0, 1]

axis.update_rule(...) filters recent_deltas as:
  effective_delta_strength(δ, axis, cycle) = δ.raw_strength · salience(δ.kind, cycle)
```

Kind taxonomy (`conversation_turn`, `file_change`, `federation_envelope`, etc.) L4. Operates between intake (L1_SKIN §2) and gradient advance (step 2 of L1_CONTINUITY §1.1) — intake decision binary; salience modulates downstream.

### §E.2 Bootstrap + emergence transition

**Bootstrap** (uniform until N=100 samples):
1. Genesis: `salience(kind, 0) = 1.0` for every kind in spore-schema taxonomy.
2. `n_kind` = times raw material of `kind` was absorbed AND causally cited by a fruited sporocarp in same axis-fruiting window.
3. While `n_kind < N` (seed 100), salience uniformly 1.0.

**Steady-state** (EWMA per-kind, activates at `n_kind ≥ N`):

4. ```
   correlation_score(kind, cycle) =
       (cited_count_in_recent_W_cycles(kind) / total_ingested_in_W(kind))
       — baseline_uniform(K)
   ```
   `W` = EWMA window; `K` = distinct active kinds; `baseline_uniform(K) = 1/K`.

5. ```
   salience(kind, cycle+1) =
       (1 - α) · salience(kind, cycle)  +  α · normalize(correlation_score)
   ```
   Seed α=0.05/cycle. `normalize` = softmax across active kinds.

6. **Anti-collapse floor**: `salience(kind, cycle) ≥ ε > 0` (seed `ε = 1/(K · 4)`).

### §E.3 Birth-period exemption + post-birth settling

Birth period: salience uniform 1.0; emits `salience_emergence_pending` (daily, NOT immune). At `birth_period_terminated`: EWMA activates per-kind as kinds cross `n_kind ≥ N`. Post-birth settling window (seed 100 cycles): `salience_collapse` detector SUSPENDED. End: detector activates.

### §E.4 Salience-emergence rule is CI-classified

`salience_emergence_rule` (formulas + N, α, W, ε) is substrate-resident CI per I2 + L1_GOVERNANCE §1.2. Mutations require owner attestation per L1_GOVERNANCE §2.2. **L1_HARD_RULES F25**. Spore-schema: tier-1 SSoT (L1_SCHEMA §3); child substrates inherit rule + accumulate salience from zero (P8 — each Cultivar's salience emerges from own observations).

### §E.5 Anti-uniformity guarantee + `salience_collapse` detector

`salience_entropy(cycle) = -Σ_kind salience(kind, cycle) · log₂(salience(kind, cycle))` over kinds with `n_kind ≥ N`.

**`salience_collapse` immune signal**:

| Condition | Grade |
|---|---|
| entropy ≥ `H_threshold = log₂(K_active) · 0.4` for ≥ `W_collapse` (seed 30) | daily |
| entropy ≥ 0.5 for ≥ `2·W_collapse` | elevated |
| entropy ≥ 0.6 for ≥ `4·W_collapse` | CRITICAL (L1_HARD_RULES C23) |

> **Inverted-logic note**: salience COLLAPSING toward uniform = entropy HIGH. "Collapse" = attention discipline collapsing (undiscriminating); mathematically high entropy.

- **Emission**: §B6 gate. CRITICAL is §P14.c telos-drift correlate (emitted independently; correlated at L2_OBSERVABILITY).
- **`causal_in_edges`**: `(salience_entropy_trajectory_in_W_collapse_cycles, salience_map_snapshot_hash, H_threshold_value, template_version)`.

### §E.6 Salience exposure to agent

§B4 digest includes salience-summary block (top-`k` + entropy). Substrate-attested; NEVER agent-set/overridable (P1.c). Agent deltas implying shift run through §E.2; no fast-path.

### §E.7 Federation interaction

Per §B9 + P5 + P8: each substrate carries own salience map; maps do NOT transfer at federation or reproduction. Cross-substrate sporocarps feed receiving substrate's `federation` kind. Preserves Cultivar-individuality.

### §E.8 What §E does NOT do

Replace P2 envelope admission (operates after); trigger compression (L0 P10; CI at L1_SCHEMA + L1_CONTINUITY); replace `bet_weakening_quorum` or `telos_drift`; classify/attest envelopes.



## §F. Telos alignment operationalization (P14.c per L0 §P14.c G-6.a)

### §F.1 The form

**Telos-alignment** scalar `[-1, 1]`:

```
telos_alignment(cycle) = cos_sim(
    sporocarp_centroid(rolling_window, cycle),
    objective_embedding
)
```

- `sporocarp_centroid`: L2-normalized vector mean of canonical-bytes-rendered text of every daily-class sporocarp in rolling window. CI-class EXCLUDED (governance events ≠ behavior).
- `objective_embedding`:
  - **Owner objective declared** (P14.b): `embed(owner_stated_objective_text)`. Tier-1 SSoT (F-row §F.5).
  - **No objective**: `embed(agent_feedback_trajectory_recent)` (L1_TRAJECTORY-derived).

Per-substrate at genesis, CI; switching branches requires owner CI attestation.

### §F.2 Rolling window + cadence

Window: seed 90 substrate-days (= L0 §7.4 Living Bets window). Cadence: digest-emission per L1_CONTINUITY §1.1 step 2. Branch-2: agent feedback trajectory per L1_TRAJECTORY §6+§7 over feedback-marked deltas; empty → centroid over agent's last-K deltas (K = window cycle count). Operationalizes "agent-perceived utility" joint-history-derived per L0 §5.3.

### §F.3 Drift threshold + detector grading

| Cosine | Status | Sporocarp |
|---|---|---|
| ≥ 0.6 | aligned | none |
| 0.4 < ≤ 0.6 | drifting | `telos_alignment_low` (observability) |
| 0.2 < ≤ 0.4 | drift | `telos_drift` daily |
| 0.0 < ≤ 0.2 | drift | `telos_drift` elevated |
| ≤ 0.0 | drift | `telos_drift` CRITICAL (C24) |

Emission mirrors §E.5. `causal_in_edges`: `(sporocarp_centroid_hash, objective_embedding_hash, cosine_value, rolling_window_start_cycle, rolling_window_end_cycle, embedding_model_identity_hash, template_version)`. I3 recomputes centroid from window sporocarp set.

### §F.4 Birth-period exemption + post-birth settling

Birth period: NOT computed; emits `telos_alignment_pending` (daily, NOT immune). At `birth_period_terminated`: activates after settling window shared with `salience_collapse` (§E.3 seed 100 cycles). End: detector activates. Single shared settling-window knob.

### §F.5 Embedding-model identity (F-row equivalent)

Embedding model is part of substrate identity (L0 §9.4); changing model retroactively changes every prior telos-alignment. **Identity at genesis**: `embedding_model_identity = (model_name, model_version, model_canonical_bytes_hash)`; external API: hash of service-identity + service-attested version. **Mutation**: owner attestation per L1_GOVERNANCE §2.2. **Spore-inheritable**: child inherits; CI-mutable post-genesis. **Storage**: parameters NOT in spore-schema; hash + reference (URI / OCI digest / local-path+checksum). Substrate verifies bytes match hash each cycle (mismatch → I3 fail → quarantine). F-row: `F_embedding_model_identity`. Without stable identity, telos-alignment is non-falsifiable.

### §F.6 Owner-stated objective lifecycle

Owner MAY (not must) declare at genesis or via CI (P14.b). **Genesis F-row F20**: branch-1 locked unless CI-mutated. **CI mutation** (`telos_objective_set:{new_text}`): substrate computes `embed(...)` under current embedding-model-identity, records text+hash, uses from next cycle; prior values NOT retroactively recomputed (I4). **Switch to no-objective**: `telos_objective_unset` → branch-2 from next cycle. **Multiple objectives**: out of scope; one active. Multi-objective L4+.

### §F.7 Interaction with §E + L1_TRAJECTORY

Per P14.a: chooses cosine-similarity-of-embedding-centroids over trajectory-cluster-coherence — L4-implementable in one cycle, no clustering dependency; cluster_C is CI and must NOT silently break telos-alignment. **Salience independence**: §E on `raw_material_kind`; §F on sporocarp centroid. No shared pathway; correlated but neither subsumes. Branch-2 imports L1_TRAJECTORY recent-window feedback-marked deltas; empty → falls back to recent delta stream.

### §F.8 What §F does NOT do

Replace `bet_weakening_quorum` (L0 §7.4); enforce owner stating objective (P14.b MAY-not-must); compute over CI-class sporocarps (conflates behavior with governance); block CI events (CRITICAL telos_drift owner-gated + observatory-mediated; not auto-mortality); cross substrates (per-pair, not per-mycelium).



## §G. Glossary

Cultivation / Cultivator / Cultivar owned by L0 §1.2. Document-private:

- **Cultivar-individuality** (§E.7 + P8): each Cultivar emerges own salience map + accumulates own telos history; inheritance is rule-level (salience rule, embedding-model identity, telos objective), not state-level.

Mechanism terms inline at §E/§F where defined. Cross-doc terminology at L0 §12.
