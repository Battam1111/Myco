# L1 — Trajectory (positive intent-derivation mechanism for Myco v0.9)

> L1 for intent-derivation satisfying L0 §5.3.
> Cross-cuts L1_TROPISM §B4/§B6 + L1_GOVERNANCE §1.2/§2.2/§3.1/§5.3/§6.3 + L1_HARD_RULES F17 + L1_SCHEMA §2.1/§3.1 + L1_CONTINUITY §6.2 + L2_OBSERVABILITY §3/§11 + L2_FEDERATION.

---

## §1. The form — intent as derived view

Intent IS the directed pattern of operations (deltas + sporocarps) the operator-substrate pair has performed together over a recent DAG window, projected onto a current point in time. Computed, not stored. Schema gains zero new types.

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

`cluster_C` is substrate's currently-designated clustering algorithm. Intent is a function of `(DAG, cluster_C)` jointly. DAG = substrate state (I4); `cluster_C` = CI fixed-point (L1_HARD_RULES F17 + L1_GOVERNANCE §2.2). Queries traverse Merkle DAG (L1_SCHEMA §2.1); closure verified at CI.

---

## §2. Why trajectory beats stored alternatives

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported → unverifiable. Agent writes `intent=X` while pursuing Y. Intent becomes agent-private (violates P1.c). |
| **(c) NL metadata + vector embed** | Still self-reported; per-item joint, not as-symbiosis joint. |
| **(b') Trajectory query** *(chosen)* | No self-report surface; necessarily joint per P1.c; phantom-intents impossible; long-horizon recoverable across reconnections. |

Fourth position (d) thread_id grouping: orthogonal — see §6.

---

## §3. Cold-start

Genesis DAG contains only `genesis_event` + owner birth attestation. Early queries return ∅ or near-empty subgraphs. Substrate's "expressed direction" cold start IS agent's first few deltas (read directly from DAG, bypassing clustering per L1_CONTINUITY §6.2 birth-period). Queries MUST return explicit `cold_start_marker`, not error. Downstream consumers do NOT depend on trajectory being non-empty (appetite gradients are primary internal signal).

---

## §4. Clusterer coupling

- `cluster_C` IS a substrate-resident object with own identity (NOT free parameter).
- Changing `cluster_C` IS CI — retroactively alters past intents.
- I4 full-fidelity: DAG unchanged by clusterer evolution; trajectory *view* changes. Past trajectories read through their epoch's clusterer; historical retention per L1_GOVERNANCE §3.1 active-prefix + archived-tail if L4 elects.
- Candidate algorithms (L4): graph community detection (Louvain/Leiden/label-propagation); density (HDBSCAN/OPTICS); hierarchical; hybrid.
- **Atomicity**: cluster_C swap IS epoch-boundary event (§5); in-flight queries abort with `clusterer_swap_interrupted` or snapshot-isolate to clusterer active at query start.

---

## §5. Schema-evolution epochs

Each CI mutation creates trajectory epoch boundary recorded as `epoch_boundary` sporocarp (L1_TROPISM §B3); queries default to current epoch; cross-epoch queries L1-deferred until first schema mutation surfaces concrete translation requirements.

---

## §6. thread_id — orthogonal grouping primitive

Each delta/sporocarp MAY carry optional opaque `thread_id` — lightweight agent-declared grouping (schema: L1_SCHEMA §3.1 inheritable spore-schema field; opaque-string per-substrate). NOT trust-bearing; self-organizing primitive; misplacement self-punishing. Cost: 1 optional field per node; benefit: cold-start works, clusterer-independent, schema-evolution-resilient. Queries MAY use thread_id as clustering hint but trajectory ≠ threads. **L1 commits**: thread_id OPTIONAL; substrate canon at genesis chooses to expose; opaque string scoped per-substrate. Recommended default: expose; use as clustering hint.

---

## §7. Trajectory-injection defense

Algorithm: `algorithms/echo_chamber_detection.md`. Defense structure (delta-novelty weighting + `echo_chamber` immune sporocarp + substrate-keyed detection) L1-committed; down-weighting algorithm + threshold L4. Deltas whose `causal_in_edges` overwhelmingly trace to recent same-substrate citations down-weighted; substrate-keyed not operator-keyed — avoids logout-reconnect-replay bypass + L0 I1 conflict. Substrate-internal; agent cannot disable without CI mutation.

---

## §8. Fossil-record vs teleology

Per L0 §5.3: substrate's view of intent IS fossil-record honest, not teleologically-honest. Trajectory queries never return "agent's stated goal"; divergence → trajectory wins empirically; trajectory wandering feeds `bet_weakening_quorum` (L2_OBSERVABILITY §3 + L0 §7.4); drift surfaced to operator (§9 + L1_TROPISM §B4) + Cultivator-audit. Retro-rewrite impossible (DAG full-fidelity per I4; queries reproduce identically given `(DAG, cluster_C)`; retro-editing = C7 breach).

---

## §9. Observability + federation (cross-cuts)

**Observability** (L2_OBSERVABILITY §11): (1) *Operator-side* — gradient digest may include current-trajectory subgraph reference (L1_TROPISM §B4); (2) *Substrate-internal* — immune observes drift; aggregates into signal #3; (3) *Cultivator-side* — anchor-audit replays query at any historical DAG-tip co-sign point; reproducible given `(DAG, cluster_C_at_timestamp)`.

**Federation** (L2_FEDERATION; L1 deferral): federation event content canonical-bytes (L1_GOVERNANCE §5.3); trajectory itself NOT a federation payload — derived view that doesn't travel. **Commitment**: intent does not federate; each substrate has its own intent over its own DAG. Federation transfers content, not direction.
