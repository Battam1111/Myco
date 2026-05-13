# L1 — Tropism (positive dispatch form for Myco v0.9)

> **Status**: DRAFT 2 (2026-05-13). Authoritative L1 doc for positive dispatch form satisfying L0 §5.2 constraints.
> **Layer**: L1 (mechanism). Governed by L0.
> **Scope**: tropism + sporocarp punctuation as the chosen positive dispatch form. DRAFT 2 post pass-1 100%-confidence-loop: cut chytrid bloat, demoted astronaut over-commitments (specific axis lists / clustering algorithms / numerical defaults are now explicitly L4-revisable), added mycoparasite defenses (causal-proofs, network-egress, trajectory-injection guards).
> **Confidence discipline**: per pass-1 architectural-astronaut: L1 confidence is "best current sketch + clearly marked deferred zones", not "100% sure about every mechanism". The decisions in §C deferred-list are larger than DRAFT 1's; this is intentional.

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

---

## §3. Two-layer structure — gradient configuration + sporocarp punctuation

Tropism has two layers:

- **Gradient configuration** (medium): continuously-evolving multi-dimensional structure where each axis is one appetite. The agent inhabits this medium. Both sides perturb (agent via deltas; substrate via own metabolism).
- **Sporocarp** (observable): substrate-initiated discrete records that anchor the continuous medium to checkable observables.

**Symmetry locus** (refined per pass-2 mycorrhiza-15): the gradient layer is **jointly perturbed** — substrate via internal update-rules; operator-connection via skin-validated deltas. The perturbation surfaces are **reciprocally asymmetric** (substrate has direct gradient access; agent has skin-mediated access), licensed by P1.c carrier-asymmetry. The sporocarp layer is asymmetric in initiation: substrate fruits sporocarps; agent emits deltas. Both are typed; both pass through skin envelope validation; the agent's deltas are validated at intake; substrate's sporocarps carry causal-proofs per §B6. The two layers are reciprocally asymmetric, both licensed by carrier-asymmetry. Neither layer is "fully symmetric" — calling them symmetric was the DRAFT 1 cosmetic claim that pass-2 corrected.

**Why sporocarps are not verbs**: a verb is agent-initiated (agent calls → substrate executes). A sporocarp is substrate-initiated (gradient crosses trigger → substrate fruits → agent observes). Arrow reversed.

---

## §4. Birth period vs steady state

**Birth period**: substrate's first window where seed thresholds + seed update-rules apply (no emergence yet). End criterion per L1_GOVERNANCE birth-period termination (maturity-attested per pass-1 saprotroph-5: requires ALL of (1) ≥N sporocarps fruited, (2) ≥M active-operation time, (3) `threshold_emergence_rule` reports convergence per-axis below epsilon).

**Steady state**: emergent thresholds activate; gradient update rules may evolve per P3 (CI-gated).

**Predictability gap** during birth is intentional (per L0 P1.c): the agent learns this substrate's specific tropism. This is symbiosis-being-established, not a bug.

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

**Template versioning** (per pass-2 saprotroph-20): the `causal_proof_template` may evolve per P3 (CI-level event). Each evolution increments `template_version`. Sporocarps record the version under which their proof was computed; I3 validates against that version, not against the current template. Old templates remain referenced from cold-tier sporocarps. Substrate maintains `template_version_registry` (CI-level field) listing all historical templates with their valid-from cycle.

**Clusterer location** (cross-ref L1_TRAJECTORY + L1_CONTINUITY): when L1_TRAJECTORY clustering is invoked (trajectory derivation, echo-chamber detection), execution runs within the substrate process (no network egress required). Trajectory derivation fires on-demand at digest-emission time and at echo-chamber detection cadence (L4-tunable) within step 2 (gradient advance) of the metabolic cycle.

### B2. Initial appetite set — illustrative seed, NOT normative (per pass-1 astronaut-4)

The following six axes are a **seed proposal**, NOT an L1 commitment. Substrate canon at genesis selects which axes the substrate actually carries; L4 implementation observation in the first 30 days may add/remove/merge axes.

- `hunger` (unmetabolized intake pressure) → P2
- `drift` (graph-disconnection pressure) → P5 / I5
- `decay` (staleness pressure) → P4
- `federation-pull` (peer signal pressure) → P8 / I7
- `evolution-tension` (schema-vs-content disagreement) → P3
- `skin-pressure` (boundary signals) → P9 / I8

**Open: `mortality-signal` axis**: per L0 P7 mortality-signal protection — substrate fruits `self_euthanasia_proposal` at unrecoverable pathology. Whether this is implemented as an appetite axis (gradient over health metrics) or as a state-transition predicate (FSM owned by L1_GOVERNANCE) is L4-decided. **Either way**, the threshold + update rule are CI-level (per L0 I2 fixed-point).

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

CI-class sporocarps (governance_event family per B3): substrate emits `attestation_request` via anchor surface (L0 §9 + L1_GOVERNANCE §2.2). Sporocarp lands in pending queue. Owner-signed attestation moves sporocarp from pending → published.

**Causal proof on emission** (per pass-1 mycoparasite-3): every fruiting carries `causal_in_edges` proof per B1's `causal_proof_template`. I3 self-validation (L1_SCHEMA §4) recomputes from causal_in_edges and verifies the fruiting condition crossed. Sporocarps without verifiable proofs are rejected before DAG insertion.

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

The kernel substrate is an ordinary Myco substrate (B2 illustrative axes + B3 sporocarp types) plus one specialization: `evolution-tension` axis is bound to the kernel source repository (substrate-internal metabolism — kernel-source-change events feed into the axis as deltas). No outbound RPC; per L1_SKIN §5 enforcement.

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
9. **Whether `thread_id` from L1_TRAJECTORY §5 is exposed** as a sporocarp field.
10. **Consumption fraction for digest budget** (B4).
11. **Trajectory-injection defense parameters** (delta-novelty weighting per pass-1 mycoparasite-9 — see L1_TRAJECTORY).

L1 commits to the **shape** of these decisions; L4 picks values.

---

## §D. Constraint satisfaction (one-sentence — per pass-1 chytrid-6)

L0 §5.2's seven constraints are mechanically satisfied — see §1 (form), §2 (vs alternatives), §B (specification). Future L1 revisions must continue to satisfy them; if a constraint is found unworkable, the response is an L0 revision proposal (per L0 §10.2), not L1 weakening.
