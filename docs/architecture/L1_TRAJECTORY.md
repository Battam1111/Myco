# L1 — Trajectory (positive intent-derivation mechanism for Myco v0.9)

> **Status**: DRAFT 2 (2026-05-13). Authoritative L1 doc for intent-derivation satisfying L0 §5.3.
> **Layer**: L1. Governed by L0.
> **Scope**: trajectory derivation over the causal DAG as the positive intent mechanism. DRAFT 2 post pass-1 100%-confidence-loop: cut bloat, demoted epoch machinery to deferred (astronaut-2), cut Leiden algorithm naming (astronaut-5), added trajectory-injection defense (mycoparasite-9), kept the four edge-case codifications (cold-start, clusterer coupling, schema epochs, thread_id).
> **Confidence discipline**: per L1 norm — best current sketch + clearly-deferred zones.

---

## §1. The form — intent as derived view

Intent in a Myco v0.9 substrate is **the directed pattern of operations (deltas + sporocarps) the operator-substrate pair has performed together over a recent window of the causal DAG, projected onto a current point in time**. It has no stored representation. It is **computed**, not stored. Schema gains zero new types from intent existing.

Operationally:

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

where `cluster_C` is the substrate's currently-designated clustering algorithm. Intent is a function of `(DAG, cluster_C)` jointly.

---

## §2. Why trajectory beats stored alternatives

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported → unverifiable. Mycoparasite attack: agent writes `intent=X` while pursuing Y; downstream consumers trust the lie. Phantom intents accumulate over time. Intent becomes agent-private, violating P1.c joint-state. |
| **(c) NL metadata + vector embed** | Still self-reported (partial improvement); adds embedding cost per ingestion; per-item joint, not as-symbiosis joint. |
| **(b') Trajectory query** *(chosen)* | No self-report surface (mycoparasite-resistant); intent is necessarily joint (per P1.c — the pair's joint history IS the trajectory); phantom-intents impossible (no records to leave behind); long-horizon intent recoverable by DAG traversal across operator-reconnections. |

A fourth position (**(d) thread_id grouping**): orthogonal to intent. Lightweight grouping primitive, not a substitute for intent. Compatible with (b'); see §5.

---

## §3. Cold-start

At substrate genesis the causal DAG contains only the `genesis_event` sporocarp + the owner birth attestation. For early operations, trajectory queries return ∅ or near-empty subgraphs. **This is the correct degenerate behavior:**

- "The pair has no joint history yet" is a true statement at t=0.
- Downstream consumers (I3 self-validation, immune system) read appetite gradients directly via the L1_TROPISM dispatch surface; they do NOT depend on trajectory being non-empty.
- Substrate's "expressed direction" during cold start is the agent's first few deltas themselves (read directly from the DAG, bypassing clustering).
- As DAG accumulates, trajectory becomes well-defined.

L1 commits: cold-start trajectory queries return an explicit `cold_start_marker`, not an error. The substrate's empty trajectory is part of the substrate's honest state.

---

## §4. Clusterer coupling

Different clustering algorithms produce different trajectories from identical DAG histories. Therefore:

- The clustering algorithm `cluster_C` is a **substrate-resident object** with its own identity (NOT a free parameter, NOT implicit in runtime).
- **Changing `cluster_C` is contract-identity-level** (per L1_GOVERNANCE §1.2) — retroactively alters how past intents are read.
- L0 I4 full-fidelity-recoverability: the DAG is unchanged by clusterer evolution; what changes is the trajectory *view*.

**Candidate algorithm families** (per pass-1 astronaut-5, no L1 preference; L4 picks):

- Graph community detection (Louvain / Leiden / label-propagation).
- Density clustering (HDBSCAN / OPTICS) on causal-distance metric.
- Hierarchical clustering on a DAG-induced metric.
- Hybrid combinations.

Algorithm choice is L4. L1 commits that the choice exists and is CI-protected.

**Atomicity** (per pass-1 rhizomorph-10): cluster_C swap is an epoch-boundary event (§5); trajectory queries in flight at swap time are aborted with a `clusterer_swap_interrupted` marker and may be re-issued against the new clusterer. Alternatively: queries are snapshot-isolated to the clusterer active at query start. L4 picks.

---

## §5. Schema-evolution epochs (per pass-1 astronaut-2 — significantly trimmed)

DRAFT 1 specified detailed epoch machinery (predicate-translation tables, adjacent-epoch composition, senescence horizons). DRAFT 2 acknowledges: **v0.9 has not survived its first schema change yet**. Specifying multi-epoch translation infrastructure before observing the first concrete cross-epoch read is architectural-astronaut territory.

L1 commits to the structural minimum:

- Each contract-identity-level mutation creates a trajectory epoch boundary, recorded as an `epoch_boundary` sporocarp (per L1_TROPISM §B3 governance_event family).
- Trajectory queries default to **within current epoch**.
- **Cross-epoch trajectory queries are L1-deferred until the substrate's first schema mutation surfaces concrete translation requirements**. L4 codifies after observed need.

This is intentional: writing predicate-translation infrastructure now would mean writing it twice — once speculatively, once for real.

---

## §6. thread_id — orthogonal grouping primitive (per pass-1 mycoparasite-21, retained)

Each delta and sporocarp MAY carry an optional opaque `thread_id` field — a lightweight, mechanically-typed grouping primitive declared by the agent ("this delta belongs to long-running thread T"). Threads are **not intent**; they are *declarative grouping*.

- **Cost**: 1 optional field per node.
- **Benefit**: cold-start works (`thread_id` set on first relevant operation); clusterer-independent; schema-evolution-resilient (opaque-typed, not predicate-typed).
- **Not teleological**: agent's thread_id misplacement is self-punishing (loses own grouping); no incentive to lie.
- **Relationship to trajectory**: orthogonal. Trajectory clusters causally; threads group declaratively. Trajectory queries MAY use thread_id as a clustering hint (especially during cold-start), but trajectory is not defined by threads.

**L1 commits**: thread_id is **OPTIONAL** — substrate canon at genesis chooses whether to expose it. If exposed, type is opaque string scoped per-substrate. L4 picks specific construction.

**Recommended default**: expose thread_id; use as clustering hint when present.

---

## §7. Trajectory-injection defense (per pass-1 mycoparasite-9 — NEW in DRAFT 2)

**Attack**: the agent (the only delta source) floods deltas crafted to make `cluster_C` produce a desired trajectory T. Trajectory "honestly" shows T; downstream consumers trust it; immune-grade drift signal suppressed.

**Defense**: trajectory derivation includes **delta-novelty weighting** — deltas whose `causal_in_edges` (per L1_TROPISM §B6 causal-proof) trace overwhelmingly to recent same-operator deltas (high self-citation, low external-anchor) are **down-weighted** in clustering.

**Detection of pathological self-citation**: trajectory dominated by self-citation chains beyond an L1-tunable threshold (default: ≥80% of recent-window node citations are self-loops within an operator-session) emits an `echo_chamber` immune sporocarp.

**Implementation**: down-weighting algorithm + threshold tuning are L4. The structure of the defense (novelty score per delta + echo-chamber detection) is L1-committed.

---

## §8. Fossil-record vs teleology

Per L0 §5.3 commitment: the substrate's view of intent is **fossil-record honest**, not teleologically-honest. The substrate sees what the pair did; it does not believe agent self-reports about what the agent aimed at.

Consequences:

- Trajectory queries never return "the agent's stated goal".
- If an agent's stated goal (in delta text content) diverges from the trajectory the substrate reads, the trajectory wins — empirically.
- Drift detection (L0 §7 falsifiability trigger): trajectory showing wandering / inconsistency in conjunction with other observatory signals contributes to the bet_weakening_quorum.

---

## §9. L2 / L3 questions deferred

- **Trajectory window default** (time-bounded / count-bounded / graph-distance-bounded — L4 picks; default likely all three exposed as parameters).
- **Multi-trajectory composition** (single composite vs set of clusters — L2 doctrine).
- **Trajectory cache invalidation strategy** (L3 implementation).
- **Federation trajectory semantics** — per L0 P8: child substrate begins its own DAG from genesis; trajectory does NOT transfer; child trajectory derives from its own DAG (L2 doctrine codifies).
- **Cross-epoch translation table format** — deferred per §5 until concrete need surfaces.
- **Specific `cluster_C` algorithm** — L4 picks per §4.
- **Specific `thread_id` construction** — L4 picks per §6.
- **Specific delta-novelty algorithm + echo-chamber threshold** — L4 picks per §7.

L1 commits to the shape; L4 picks values.
