# L1 — Trajectory (positive intent-derivation mechanism for Myco v0.9)

> **Status**: DRAFT 2. L1 for intent-derivation satisfying L0 §5.3. Governed by L0.

---

## §1. The form — intent as derived view

Intent is **the directed pattern of operations (deltas + sporocarps) the operator-substrate pair has performed together over a recent DAG window, projected onto a current point in time**. Computed, not stored. Schema gains zero new types.

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

`cluster_C` is substrate's currently-designated clustering algorithm. Intent is a function of `(DAG, cluster_C)` jointly.

---

## §2. Why trajectory beats stored alternatives

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported → unverifiable. Mycoparasite: agent writes `intent=X` while pursuing Y. Intent becomes agent-private (violates P1.c). |
| **(c) NL metadata + vector embed** | Still self-reported; per-item joint, not as-symbiosis joint. |
| **(b') Trajectory query** *(chosen)* | No self-report surface; necessarily joint per P1.c; phantom-intents impossible; long-horizon recoverable across reconnections. |

Fourth position (d) thread_id grouping: orthogonal — see §6.

---

## §3. Cold-start

Genesis DAG contains only `genesis_event` + owner birth attestation. Early queries return ∅ or near-empty subgraphs. Correct degenerate behavior: pair has no joint history at t=0; downstream consumers (I3, immune) read appetite gradients via L1_TROPISM, not trajectory; substrate's "expressed direction" cold start is agent's first few deltas (read directly from DAG). Queries return explicit `cold_start_marker`, not error.

---

## §4. Clusterer coupling

Different clustering algorithms produce different trajectories from identical DAG. Therefore:

- `cluster_C` is a **substrate-resident object** with own identity (NOT free parameter).
- **Changing `cluster_C` is CI** (L1_GOVERNANCE §1.2) — retroactively alters past intents.
- I4 full-fidelity: DAG unchanged by clusterer evolution; trajectory *view* changes.

Candidate algorithms (L4 picks): graph community detection (Louvain/Leiden/label-propagation); density clustering (HDBSCAN/OPTICS); hierarchical; hybrid.

**Atomicity**: cluster_C swap is epoch-boundary event (§5); in-flight queries abort with `clusterer_swap_interrupted` (re-issuable) or snapshot-isolate to clusterer active at query start. L4 picks.

---

## §5. Schema-evolution epochs

v0.9 has not survived first schema change yet; multi-epoch translation deferred. L1 commits structural minimum: each CI mutation creates trajectory epoch boundary recorded as `epoch_boundary` sporocarp (L1_TROPISM §B3); queries default to current epoch; cross-epoch queries L1-deferred until first schema mutation surfaces concrete translation requirements.

---

## §6. thread_id — orthogonal grouping primitive

Each delta/sporocarp MAY carry optional opaque `thread_id` — lightweight mechanically-typed agent-declared grouping. Not intent; declarative grouping. Cost: 1 optional field per node. Benefit: cold-start works; clusterer-independent; schema-evolution-resilient. Not teleological: misplacement self-punishing. Relationship: orthogonal — trajectory clusters causally, threads group declaratively; queries MAY use thread_id as clustering hint (esp. cold-start) but trajectory ≠ threads.

**L1 commits**: thread_id OPTIONAL; substrate canon at genesis chooses to expose. If exposed, opaque string scoped per-substrate. L4 picks construction. Recommended default: expose; use as clustering hint.

---

## §7. Trajectory-injection defense

**Attack**: agent floods deltas crafted to make `cluster_C` produce desired trajectory T; downstream trusts; immune-grade drift suppressed.

**Defense**: trajectory derivation includes **delta-novelty weighting** — deltas whose `causal_in_edges` (L1_TROPISM §B6) trace overwhelmingly to recent same-operator deltas (high self-citation, low external-anchor) are down-weighted.

**Detection**: trajectory dominated by self-citation chains beyond L1-tunable threshold (default ≥80% of recent-window node citations within L1-tunable causal-distance of recent self-citations, regardless of operator-session) emits `echo_chamber` immune sporocarp.

Detection is **substrate-keyed** (DAG-structural, not operator-session) — operator-keyed would conflict with I1 prohibition + be bypassable via logout-reconnect-replay. Down-weighting algorithm + threshold L4. Defense structure (novelty score + echo-chamber detection) L1-committed.

---

## §8. Fossil-record vs teleology

Per L0 §5.3: substrate's view of intent is **fossil-record honest**, not teleologically-honest. Substrate sees what pair did; does not believe agent self-reports about aim. Trajectory queries never return "agent's stated goal"; divergence → trajectory wins empirically; trajectory wandering feeds `bet_weakening_quorum`.
