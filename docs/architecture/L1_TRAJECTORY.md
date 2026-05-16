# L1 — Trajectory (positive intent-derivation mechanism for Myco v0.9)

> **Status**: DRAFT 2 (2026-05-13). L1 doc for intent-derivation satisfying L0 §5.3.
> **Layer**: L1. Governed by L0.

---

## §1. The form — intent as derived view

Intent is **the directed pattern of operations (deltas + sporocarps) the operator-substrate pair has performed together over a recent window of the causal DAG, projected onto a current point in time**. No stored representation. **Computed**, not stored. Schema gains zero new types.

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

`cluster_C` is the substrate's currently-designated clustering algorithm. Intent is a function of `(DAG, cluster_C)` jointly.

---

## §2. Why trajectory beats stored alternatives

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported → unverifiable. Mycoparasite: agent writes `intent=X` while pursuing Y. Phantom intents accumulate. Intent becomes agent-private (violates P1.c). |
| **(c) NL metadata + vector embed** | Still self-reported; per-item joint, not as-symbiosis joint. |
| **(b') Trajectory query** *(chosen)* | No self-report surface (mycoparasite-resistant); necessarily joint per P1.c; phantom-intents impossible; long-horizon intent recoverable across reconnections. |

A fourth position (**(d) thread_id grouping**): orthogonal — lightweight grouping primitive, not substitute. Compatible with (b'); see §6.

---

## §3. Cold-start

At genesis the DAG contains only `genesis_event` + owner birth attestation. Early trajectory queries return ∅ or near-empty subgraphs. **Correct degenerate behavior:**

- "Pair has no joint history yet" is true at t=0.
- Downstream consumers (I3, immune system) read appetite gradients directly via L1_TROPISM; don't depend on trajectory being non-empty.
- Substrate's "expressed direction" during cold start is agent's first few deltas (read directly from DAG, bypassing clustering).
- As DAG accumulates, trajectory becomes well-defined.

Cold-start trajectory queries return explicit `cold_start_marker`, not error.

---

## §4. Clusterer coupling

Different clustering algorithms produce different trajectories from identical DAG. Therefore:

- `cluster_C` is a **substrate-resident object** with its own identity (NOT free parameter).
- **Changing `cluster_C` is CI-level** (per L1_GOVERNANCE §1.2) — retroactively alters past intents.
- L0 I4 full-fidelity: DAG unchanged by clusterer evolution; trajectory *view* changes.

Candidate algorithm families (L4 picks): graph community detection (Louvain/Leiden/label-propagation); density clustering (HDBSCAN/OPTICS) on causal-distance metric; hierarchical clustering on DAG-induced metric; hybrid.

**Atomicity**: cluster_C swap is an epoch-boundary event (§5); in-flight queries either abort with `clusterer_swap_interrupted` and are re-issuable, or are snapshot-isolated to the active clusterer at query start. L4 picks.

---

## §5. Schema-evolution epochs

v0.9 has not survived first schema change yet; multi-epoch translation deferred. L1 commits to structural minimum:

- Each CI-level mutation creates a trajectory epoch boundary recorded as `epoch_boundary` sporocarp (per L1_TROPISM §B3 governance_event family).
- Trajectory queries default to **within current epoch**.
- **Cross-epoch trajectory queries are L1-deferred** until first schema mutation surfaces concrete translation requirements.

---

## §6. thread_id — orthogonal grouping primitive

Each delta and sporocarp MAY carry optional opaque `thread_id` field — lightweight mechanically-typed grouping declared by agent. Threads are **not intent**; they are declarative grouping.

- **Cost**: 1 optional field per node.
- **Benefit**: cold-start works; clusterer-independent; schema-evolution-resilient (opaque, not predicate-typed).
- **Not teleological**: agent misplacement self-punishing (loses own grouping).
- **Relationship to trajectory**: orthogonal. Trajectory clusters causally; threads group declaratively. Trajectory queries MAY use thread_id as clustering hint (especially cold-start), but trajectory is not defined by threads.

**L1 commits**: thread_id OPTIONAL; substrate canon at genesis chooses to expose. If exposed, type is opaque string scoped per-substrate. L4 picks construction.

**Recommended default**: expose; use as clustering hint when present.

---

## §7. Trajectory-injection defense

**Attack**: agent floods deltas crafted to make `cluster_C` produce desired trajectory T; downstream consumers trust it; immune-grade drift signal suppressed.

**Defense**: trajectory derivation includes **delta-novelty weighting** — deltas whose `causal_in_edges` (per L1_TROPISM §B6) trace overwhelmingly to recent same-operator deltas (high self-citation, low external-anchor) are **down-weighted**.

**Detection**: trajectory dominated by self-citation chains beyond L1-tunable threshold (default ≥80% of recent-window node citations within L1-tunable causal-distance of recent self-citations **regardless of which operator-session emitted them**) emits `echo_chamber` immune sporocarp.

Detection is **substrate-keyed** (DAG-structural property, not operator-session property). Operator-keyed detection would conflict with L0 I1 prohibition on persisting operator-discriminating attributes and would be bypassable via logout-reconnect-replay.

Down-weighting algorithm + threshold tuning are L4. Defense structure (novelty score + echo-chamber detection) is L1-committed.

---

## §8. Fossil-record vs teleology

Per L0 §5.3: substrate's view of intent is **fossil-record honest**, not teleologically-honest. Substrate sees what pair did; does not believe agent self-reports about aim.

Consequences: trajectory queries never return "agent's stated goal"; if agent's stated goal diverges from trajectory, trajectory wins empirically; trajectory wandering/inconsistency feeds L0 §7 bet_weakening_quorum.
