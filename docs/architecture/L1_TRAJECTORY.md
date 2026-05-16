# L1 — Trajectory (positive intent-derivation mechanism for Myco v0.9)

> L1 for intent-derivation satisfying L0 §5.3.

---

## §1. The form — intent as derived view

Intent IS the directed pattern of operations (deltas + sporocarps) the operator-substrate pair has performed together over a recent DAG window, projected onto a current point in time. Computed, not stored. Schema gains zero new types.

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

`cluster_C` is substrate's currently-designated clustering algorithm. Intent is a function of `(DAG, cluster_C)` jointly.

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

Genesis DAG contains only `genesis_event` + owner birth attestation. Early queries return ∅ or near-empty subgraphs. Substrate's "expressed direction" cold start IS agent's first few deltas (read directly from DAG). Queries MUST return explicit `cold_start_marker`, not error.

---

## §4. Clusterer coupling

- `cluster_C` IS a substrate-resident object with own identity (NOT free parameter).
- Changing `cluster_C` IS CI — retroactively alters past intents.
- I4 full-fidelity: DAG unchanged by clusterer evolution; trajectory *view* changes.
- Candidate algorithms (L4): graph community detection (Louvain/Leiden/label-propagation); density (HDBSCAN/OPTICS); hierarchical; hybrid.
- **Atomicity**: cluster_C swap IS epoch-boundary event (§5); in-flight queries abort with `clusterer_swap_interrupted` or snapshot-isolate to clusterer active at query start.

---

## §5. Schema-evolution epochs

Each CI mutation creates trajectory epoch boundary recorded as `epoch_boundary` sporocarp (L1_TROPISM §B3); queries default to current epoch; cross-epoch queries L1-deferred until first schema mutation surfaces concrete translation requirements.

---

## §6. thread_id — orthogonal grouping primitive

Each delta/sporocarp MAY carry optional opaque `thread_id` — lightweight agent-declared grouping. Cost: 1 optional field per node; benefit: cold-start works, clusterer-independent, schema-evolution-resilient. Queries MAY use thread_id as clustering hint but trajectory ≠ threads. **L1 commits**: thread_id OPTIONAL; substrate canon at genesis chooses to expose; opaque string scoped per-substrate. Recommended default: expose; use as clustering hint.

---

## §7. Trajectory-injection defense

Algorithm: `algorithms/echo_chamber_detection.md`. Defense structure (delta-novelty weighting + `echo_chamber` immune sporocarp + substrate-keyed detection) L1-committed; down-weighting algorithm + threshold L4.

---

## §8. Fossil-record vs teleology

Per L0 §5.3: substrate's view of intent IS fossil-record honest, not teleologically-honest. Trajectory queries never return "agent's stated goal"; divergence → trajectory wins empirically; trajectory wandering feeds `bet_weakening_quorum`.
