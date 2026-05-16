# L1 — Tropism (positive dispatch form for Myco v0.9)

> **Status**: DRAFT 3 (2026-05-17). L1 doc for positive dispatch form satisfying L0 §5.2 + the two L0-mandated mechanisms (§E salience, §F telos).
> **Layer**: L1. Governed by L0 DRAFT 9 SEALED (`docs/architecture/L0_VISION.md` commit `e796451` or successor). Cultivation vocabulary at L0 §1.2.

---

## §1. The form

Dispatch is **tropism**: substrate maintains intrinsic **appetites**, each with a **tropic gradient** updated each metabolic cycle (cadence: L1_CONTINUITY). Agent (active operator-connection per P1.c) inhabits gradient as perturbation source + consumer. Substrate exposes gradient state via agent's read-window; agent emits **deltas**; substrate absorbs; gradients update. When a gradient crosses its **fruiting trigger**, substrate **fruits a sporocarp** — typed, content-addressed, causally-stamped record (I4) anchoring the gradient field for governance (I2), validation (I3), federation (I7), DAG (I4).

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

- **Gradient configuration** (medium): continuously-evolving multi-dimensional structure; one axis per appetite. Jointly perturbed — reciprocally asymmetric per P1.c.
- **Sporocarp** (observable): substrate-initiated discrete records anchoring medium to checkable observables. Typed; pass skin envelope validation; carry causal-proofs per §B6.

**Why sporocarps ≠ verbs**: verb agent-initiated (agent calls → substrate executes); sporocarp substrate-initiated (gradient crosses trigger → substrate fruits → agent observes). Arrow reversed.

## §4. Birth period vs steady state

**Birth period**: seed thresholds + seed update-rules. End per L1_GOVERNANCE §1.3 (maturity-attested: ≥N sporocarps, ≥M active-operation time, threshold_emergence_rule convergence) OR L1_GOVERNANCE §1.3 maximum-duration ceiling (default 180 active-operation days). Both termination paths meet at same `birth_period → steady_state` transition.

**Steady state**: emergent thresholds activate; gradient update rules may evolve per P3 (CI-gated).

**Birth-period detectors** (per L0 §2.3 + §P14.c) — all three SUSPENDED during birth period AND post-birth settling window (§E.3 + §F.4); arm at owner-attested `birth_period_terminated` + L1-tunable settling window:

- `bet_weakening_quorum` (L0 §7.4): emits `bet_weakening_evaluation_suspended` — L2_OBSERVABILITY.
- `salience_collapse` (P12.b CF7): emits `salience_emergence_pending` — §E.
- `telos_drift` (§P14.c HF11): emits `telos_alignment_pending` — §F.

## §A. Continuity hooks

L1_CONTINUITY owns cycle cadence, dormancy, recovery, quarantine, delta atomicity, cold-resume. Tropism's gradient-advance + sporocarp-emit + DAG-update are step 2 + step 3 of L1_CONTINUITY §1.1.



## §B. Specification

### B1. Appetite axis schema

Each appetite: `name` (mycology-strict per L0 §5.1); `computation_locality` (substrate-internal; L1_SKIN §5 enforces); `domain`; `update_rule` (pure of gradient-state, recent-deltas, recent-sporocarps, time-elapsed); `seed_fruiting_trigger`; `threshold_emergence_rule` (per L1_GOVERNANCE §1.2); `causal_proof_template` + `template_version` (sporocarp `causal_in_edges` includes `(delta_set, gradient-state-snapshot-hash, threshold-value, template_version)`; I3 re-derives under recorded version).

**Template versioning**: `causal_proof_template` evolves per P3 (CI-level). `template_version_registry` (CI-level; active-prefix + archived-tail per L1_GOVERNANCE §3.1).

**Clusterer location** (L1_TRAJECTORY + L1_CONTINUITY): trajectory derivation runs within substrate process (no network egress); fires on-demand at digest-emission time and echo-chamber detection cadence within step 2.

**Salience is NOT an appetite axis** (per L0 §2.3 P12): cross-cutting modifier over `raw_material → axis routing`. Emerges from correlations between raw_material kinds and downstream fruitings (§E). Rule CI-level (L1_HARD_RULES F25); runtime values daily-class.

**Telos-alignment is NOT an appetite axis** (per L0 §P14.c): cross-cutting evaluable at digest-emission over recent-sporocarp embedding-centroid vs owner-stated-objective (or agent-feedback-trajectory) embedding. Rule + embedding-model identity CI-level (§F.5); per-cycle score daily-class.

### B2. Initial appetite set — illustrative seed, NOT normative

Substrate canon at genesis selects axes; L4 may add/remove/merge in first 30 days.

- `hunger` (unmetabolized intake) → P2
- `drift` (graph-disconnection) → P5 / I5
- `decay` (staleness) → P4
- `federation-pull` (peer signal) → P8 / I7
- `evolution-tension` (schema-vs-content disagreement) → P3
- `skin-pressure` (boundary signals) → P9 / I8

**Open: `mortality-signal` axis** (P7): appetite axis or FSM predicate (L1_GOVERNANCE) is L4. Threshold + update rule CI-level (per I2).

**Cross-cutting modifiers**: salience (§E), telos (§F). Cost-budget signals (`budget_exhausted:{axis}`, #7/#8/#9 per L0 §7.3) NOT consumed as tropism axis; degraded-operation L1_CONTINUITY-mediated.

### B3. Sporocarp type tree — seed (NOT normative)

Substrate canon may add types post-birth (each addition CI-level):

- `intake`, `digestion`, `refinement`, `federation` — daily.
- `governance_event` (axis_schema_change, sporocarp_type_addition, skin_redefinition, classifier_change, retention_amendment, etc.) — CI.
- `immune_event` (envelope_malformed, attestation_invalid, causal_chain_violation, untyped_mutation, cold_resume_quarantine, evolution_failed, peer_attestation_stale, etc.) — daily / elevated / CRITICAL.

### B4. Gradient exposure protocol

Bounded, structured, stateless digest to agent's read-window:

- **Bounded**: B ≤ L0 §7 signal-#6 read-window budget × consumption fraction (L4-tunable, 10-50%).
- **Structured**: typed object listing each appetite's gradient + recent K sporocarps + recent M unabsorbed deltas + metabolic-budget metrics.
- **Stateless**: cold-resumable from digest alone.

### B5. Delta intake surface

L1_SKIN §2 envelope schema. Per P2: shape-agnostic; envelope-checked only.

### B6. Sporocarp governance gate

Daily → DAG immediately. CI-class (governance_event family): emits `attestation_request` via anchor surface (L0 §9.2.2 + §9.2.5 + §9.3.4; L1_GOVERNANCE §2.2). Pending → published on owner-signed attestation.

**Causal proof**: every fruiting carries `causal_in_edges` per B1 template. I3 (L1_SCHEMA §4) recomputes; unverifiable rejected before DAG insertion.

**Salience + telos immune sporocarps**: `salience_collapse` (§E) + `telos_drift` (§F) fruit through this gate; detectors at §E/§F. Both SUSPENDED during birth period; arm at `birth_period_terminated` + settling window.

### B7. Continuity recovery → L1_CONTINUITY §3.

### B8. Causal DAG embedding

L1_SCHEMA §2 Merkle DAG. Edge classes: `gradient_causation` (sporocarp ← fruiting gradient); `delta_source` (sporocarp / gradient-update ← delta); `sporocarp_derivation` (sporocarp ← prior sporocarps); `federation_coupling` (per L1_GOVERNANCE §5); `governance_resolution` (CI-pending ← owner-attestation event).

### B9. Federation surface

L1_GOVERNANCE §5: discovery + peer-trust freshness L1_GOVERNANCE-owned. Tropism contribution: cross-substrate gradient coupling. Coupling mode (eager-pull vs lazy-semantic-transfer) L4-tunable.

### B10. Self-hosting bootstrap

Kernel substrate is ordinary substrate (B2 seed + B3 types) with one specialization: `evolution-tension` bound to kernel source repository (kernel-source-change events feed as deltas). No outbound RPC; L1_SKIN §5 enforces. Per P1.a (L0 §P1.a): kernel substrate IS a Cultivar under Cultivation by its human owner (Cultivator).



## §E. Salience / Attention emergence (P12 landing per L0 §2.3 G-9.b)

### §E.1 The form

**Salience**: `raw_material_kind → attention_weight ∈ [0, 1]` modulating how strongly each kind reaches each axis's update rule.

```
salience: raw_material_kind × cycle_index → attention_weight ∈ [0, 1]

axis.update_rule(...) filters recent_deltas as:
  effective_delta_strength(δ, axis, cycle) = δ.raw_strength · salience(δ.kind, cycle)
```

Kind taxonomy (e.g., `conversation_turn`, `file_change`, `federation_envelope`, `agent_thought_log`, `tool_output`, `error_trace`) L4.

Operates between intake (L1_SKIN §2) and gradient advance (step 2 of L1_CONTINUITY §1.1). Intake decision binary; salience modulates downstream attention.

### §E.2 Bootstrap + emergence transition

**Bootstrap** (uniform until N=100 samples per L0 §2.3 P12.b):

1. Genesis: `salience(kind, 0) = 1.0` for every kind in spore-schema taxonomy.
2. Substrate accumulates per-kind `n_kind` = times raw material of `kind` was absorbed AND causally cited (per B1) by a fruited sporocarp in same axis-fruiting window.
3. While `n_kind < N` (seed 100), salience uniformly 1.0.

**Steady-state** (EWMA-correlation per-kind, activates at `n_kind ≥ N`):

4. Per cycle:

   ```
   correlation_score(kind, cycle) =
       (cited_count_in_recent_W_cycles(kind) / total_ingested_in_W(kind))
       — baseline_uniform(K)
   ```

   `W` = EWMA-window; `K` = distinct active kinds; `baseline_uniform(K) = 1/K`.

5. EWMA update:

   ```
   salience(kind, cycle+1) =
       (1 - α) · salience(kind, cycle)  +  α · normalize(correlation_score)
   ```

   Seed α=0.05/cycle. `normalize` = softmax across active kinds.

6. **Anti-collapse floor**: `salience(kind, cycle) ≥ ε > 0` (seed `ε = 1/(K · 4)`).

### §E.3 Birth-period exemption + post-birth settling window

- **Birth period** (per L1_GOVERNANCE §1.3 + §4): salience uniform 1.0; emits `salience_emergence_pending` (daily, NOT immune) at each digest.
- **At `birth_period_terminated`**: per-kind EWMA activates as kinds cross `n_kind ≥ N` (per-kind, not global).
- **Post-birth settling window** (seed 100 cycles): `salience_collapse` detector SUSPENDED.
- **End**: detector activates; no further `salience_emergence_pending`.

### §E.4 Salience-emergence rule is CI-classified

`salience_emergence_rule` (formulas + N, α, W, ε + `correlation_score`) is substrate-resident, CI-level per L0 I2 + L1_GOVERNANCE §1.2. Mutations require owner attestation per L1_GOVERNANCE §2.2. **L1_HARD_RULES F25**.

**Spore-schema**: rule is tier-1 SSoT per L1_SCHEMA §3. Child substrates inherit rule; accumulate salience map from zero (per P8 — each Cultivar's salience emerges from own observations).

### §E.5 Anti-uniformity guarantee + `salience_collapse` detector

`salience_entropy(cycle) = -Σ_kind salience(kind, cycle) · log₂(salience(kind, cycle))`. Range `[0, log₂(K_active)]` over kinds with `n_kind ≥ N`.

**`salience_collapse` immune signal**:

- **Trigger**: entropy ≥ `H_threshold = log₂(K_active) · 0.4` for ≥ `W_collapse` (seed 30) consecutive cycles.

  > **Inverted-logic note**: salience COLLAPSING toward uniform = entropy HIGH. "Collapse" in P12 = attention discipline collapsing (undiscriminating); mathematically high entropy.

- **Grading**: daily default; elevated at ≥ 0.5 for ≥ `2·W_collapse`; CRITICAL at ≥ 0.6 for ≥ `4·W_collapse` (distinct from "EWMA hasn't had time" since W ≪ `4·W_collapse`).
- **Emission**: §B6 gate. Daily → DAG; elevated/CRITICAL also L1_HARD_RULES C23. CRITICAL also §P14.c telos-drift correlate (emitted independently; may be correlated at L2_OBSERVABILITY).
- **`causal_in_edges`**: `(salience_entropy_trajectory_in_W_collapse_cycles, salience_map_snapshot_hash, H_threshold_value, template_version)`.

### §E.6 Salience exposure to agent

§B4 digest includes salience-summary block (top-`k` values + entropy). Substrate-attested; NEVER agent-set or agent-overridable (per P1.c). Agent deltas implying salience shift run through normal §E.2 accumulation; no fast-path (per L0 §5.3).

### §E.7 Federation interaction

Per §B9 + P5 + P8: each substrate carries own salience map. **Maps do NOT transfer at federation or reproduction**. Cross-substrate sporocarps feed receiving substrate's `federation` kind in that substrate's salience-emergence. Preserves Cultivar-individuality.

### §E.8 What §E does NOT do

- Replace P2 envelope admission (operates after admission).
- Trigger compression (L0 P10; CI-attested at L1_SCHEMA + L1_CONTINUITY).
- Replace `bet_weakening_quorum` or `telos_drift`.
- Classify/attest envelopes (L1_SKIN §2 + P2).



## §F. Telos alignment operationalization (P14.c per L0 §P14.c G-6.a)

### §F.1 The form

**Telos-alignment** is scalar `[-1, 1]`:

```
telos_alignment(cycle) = cos_sim(
    sporocarp_centroid(rolling_window, cycle),
    objective_embedding
)
```

- `sporocarp_centroid`: L2-normalized vector mean of canonical-bytes-rendered text of every daily-class sporocarp in rolling window. CI-class EXCLUDED (governance events ≠ behavior; per L0 §P14).
- `objective_embedding`:
  - **Owner objective declared** (L0 §P14.b): `embed(owner_stated_objective_text)`. Tier-1 SSoT (F-row §F.5).
  - **No objective**: `embed(agent_feedback_trajectory_recent)` (L1_TRAJECTORY-derived).

Per-substrate at genesis, CI-level (L0 §P14.b); switching branches requires owner CI attestation.

### §F.2 Rolling window + cadence

**Window**: seed 90 substrate-days = L0 §7.4 Living Bets window. **Cadence**: digest-emission time per L1_CONTINUITY §1.1 step 2.

**Branch-2 detail**: agent feedback trajectory per L1_TRAJECTORY §6 + §7 over deltas marked as feedback. Empty → centroid over agent's last-K deltas (K = rolling-window cycle count). Operationalizes L0 §P14.b "agent-perceived utility" (joint-history-derived per L0 §5.3).

### §F.3 Drift threshold + detector grading

| Cosine | Status | Sporocarp |
|---|---|---|
| ≥ 0.6 | aligned | none |
| 0.4 < ≤ 0.6 | drifting (sub-threshold) | observability `telos_alignment_low` (NOT immune) |
| 0.2 < ≤ 0.4 | drift | `telos_drift` daily |
| 0.0 < ≤ 0.2 | drift | `telos_drift` elevated |
| ≤ 0.0 | drift | `telos_drift` CRITICAL |

Emission mirrors `salience_collapse` (§E.5). Daily → DAG; elevated/CRITICAL also L1_HARD_RULES C24.

**`causal_in_edges`**: `(sporocarp_centroid_hash, objective_embedding_hash, cosine_value, rolling_window_start_cycle, rolling_window_end_cycle, embedding_model_identity_hash, template_version)`. I3 recomputes centroid from window sporocarp set (enumerable per §B6 DAG order).

### §F.4 Birth-period exemption + post-birth settling window

- **Birth period**: NOT computed; emits `telos_alignment_pending` (daily, NOT immune) at each digest.
- **At `birth_period_terminated`**: activates after settling window shared with `salience_collapse` (§E.3 seed 100 cycles).
- **End**: detector activates; emits `telos_drift` (when triggered) or `telos_alignment_score` observability.

Single shared settling-window knob for both detectors.

### §F.5 Embedding-model identity (F-row equivalent)

Per L0 §9.4: embedding model is **part of substrate identity**; changing model retroactively changes every prior telos-alignment.

- **Identity** at genesis: `embedding_model_identity = (model_name, model_version, model_canonical_bytes_hash)`. External API: hash of service-identity declaration + service-attested model version.
- **Mutation** requires owner attestation per L1_GOVERNANCE §2.2 (full anchor protocol).
- **Spore-inheritable**: child inherits at genesis; CI-mutable post-genesis.
- **Storage**: parameters NOT in spore-schema; hash + reference (URI / OCI digest / local-path + checksum) sufficient. Substrate verifies bytes match hash each cycle (mismatch → I3 fail → quarantine).
- **L1_HARD_RULES F-row**: `F_embedding_model_identity` (DRAFT 9 cascade F18-F24).

Without stable identity, telos-alignment is non-falsifiable.

### §F.6 Owner-stated objective lifecycle

Per L0 §P14.b: owner MAY (not must) declare objective at genesis or via CI events.

- **Genesis**: F-row **F_telos_objective** (Phase γ F20). Branch-1 selected, locked unless CI-mutated.
- **CI mutation**: `telos_objective_set:{new_objective_text}`. Substrate computes new `embed(...)` under current embedding-model-identity, records text + hash, uses from next cycle. Prior values NOT retroactively recomputed (per I4).
- **Switch to no-objective**: `telos_objective_unset` → branch-2 from next cycle.
- **Multiple objectives**: out of scope; one active. Multi-objective composition L4+.

### §F.7 Interaction with §E + L1_TRAJECTORY

Per L0 §P14.a: this document chooses **cosine similarity of embedding-centroids** rather than trajectory-cluster-coherence. L4-implementable in one cycle with no clustering dependency; L1_TRAJECTORY's `cluster_C` is CI-classified and must NOT silently break telos-alignment. Trajectory-cluster-coherence is upgrade path (would require co-mutating embedding-model identity + rule).

**Salience independence**: §E on `raw_material_kind`; §F on sporocarp centroid. No shared pathway; correlated but neither subsumes. Branch-2 imports L1_TRAJECTORY's recent-window agent-marked-feedback delta set; empty → falls back to recent delta stream.

### §F.8 What §F does NOT do

- Replace `bet_weakening_quorum` (L0 §7.4).
- Enforce owner stating objective (L0 §P14.b MAY-not-must; branch-2 first-class).
- Compute alignment over CI-class sporocarps (governance events; conflates behavior with governance; against I12).
- Block CI events (CRITICAL `telos_drift` does NOT auto-mortality; owner-gated + observatory-mediated).
- Cross substrates (per §B9 + P1.c; telos is per-pair, not per-mycelium).



## §G. Glossary

L0 §1.2 owns Cultivation / Cultivator / Cultivar. Document-private:

- **Cultivar-individuality** (§E.7 + L0 P8): each Cultivar emerges own salience map + accumulates own telos history; inheritance is rule-level (salience rule, embedding-model identity, telos objective), not state-level.

Mechanism terms inline at §E/§F where defined: salience map / salience-emergence rule (F25) / salience entropy / `salience_collapse` / `salience_emergence_pending` / anti-collapse floor (§E.1-§E.5); telos-alignment / telos rolling window / sporocarp centroid / objective embedding / embedding-model identity (F-row) / `telos_drift` / `telos_alignment_pending` / `telos_alignment_low` / post-birth settling window / branch-1 vs branch-2 (§F.1-§F.6).

Cross-doc terminology at L0 §12; mechanism homes per L0 §4.
