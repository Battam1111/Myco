# L1 — Trajectory (the positive intent derivation form for Myco v0.9)

> **Status**: DRAFT 1 (2026-05-13). Authoritative L1 document for the positive intent-derivation mechanism satisfying L0 §5.3's commitment.
> **Layer**: L1 (mechanism). Governed by L0; in conflict with L0, L0 wins.
> **Scope**: L0 §5.3 commits to "intent is NOT a first-class substrate data type". This L1 doc commits to the positive mechanism — *trajectory derivation over the causal DAG* — by which intent-shaped queries are answered without a stored intent type.
> **Relationship to L0**: L0 commits to the negative claim. This L1 doc commits to the positive mechanism.
> **Provenance**: this content was previously stuffed into L0 DRAFTs 3-4 as §5.3 inner specification. DRAFT 5 of L0 moved it here per structural-rework authorization.

---

## §1. The form — intent as derived view

Intent in a Myco v0.9 substrate is **the directed pattern of operations the operator-substrate pair has performed together over a recent window of the causal DAG, projected onto a current point in time**. It has no stored representation. It is computed by traversing the DAG from a point, clustering operations and sporocarps that share causal ancestors and converge on common descendants. The resulting subgraph IS the pair's current direction.

Mathematically:

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))

where cluster_C is the substrate's currently-designated clustering algorithm.
```

Intent is therefore a function of `(DAG, cluster_C)` jointly — not DAG alone. The choice of clustering algorithm is a substrate property, not a free parameter.

---

## §2. Why (b') trajectory beats the alternatives

L0 §5.3 considered three positions on intent:

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported by the agent → unverifiable; under P1.a/P1.b' the agent maintains the substrate, so its claim about its own intent is propaganda. Mycoparasite attack: agent writes `intent=X` but pursues Y; downstream consumers trust the lie. Saprotroph attack: `status=active` intents pile up as phantoms over time. Mycorrhiza attack: intent becomes agent-private, violating P1.c joint-state. |
| **(c) NL metadata + vector embed on raw material** | Still self-reported (partial improvement); adds embedding cost per ingestion; mycorrhiza partial alignment (per-item joint, not as-symbiosis joint). |
| **(b') Trajectory query** *(chosen)* | No self-report surface (mycoparasite-resistant); intent is necessarily joint (P1.c satisfied — the trajectory IS operations the pair performed together); phantom-intents impossible (no records to leave behind); long-horizon intent recoverable by DAG traversal across operator-connection disconnects. |

A fourth position not in the original L0 §5.3 craft:

| **(d) thread_id grouping** | Orthogonal to intent — useful as a structural grouping primitive (see §5 below), not as a substitute for intent. Lightweight, opaque, self-punishing-if-misused. Compatible with (b'); the substrate may carry both. |

Trajectory derivation + optional thread_id grouping is the chosen L1 form.

---

## §3. Clusterer coupling

Different clustering algorithms produce different trajectories from identical DAG histories. Therefore:

- The clustering algorithm choice `cluster_C` is a **substrate-resident object** with its own identity (not a free parameter, not implicit in the runtime).
- **Changing `cluster_C` is a contract-identity-level event** (I2-gated) — it retroactively alters how past intents are read.
- L0 I4 full-fidelity-recoverability guarantees the DAG is unchanged by clusterer evolution; what changes is the trajectory *view*.
- Past trajectories from a previous epoch (§4 below) are read through that epoch's clusterer, not the current one. Epochs preserve clusterer-consistency within their span.

**Candidate clustering algorithms** (L1 chooses one or composes; lower L2/L3 implements):

- Graph-based community detection (Louvain, Leiden, label propagation).
- Density-based clustering (HDBSCAN, OPTICS) on causal-distance metric.
- Hierarchical clustering on a custom DAG-induced metric.
- Hybrid: graph-clustering for short-horizon + density-clustering for long-horizon trajectories.

L1 leading proposal: **Leiden community detection on the DAG's bidirectional causal neighborhood**, with hierarchical refinement for trajectory zoom-in/zoom-out.

---

## §4. Schema-evolution epochs

When L1 mutates (vocabulary refactor, dispatch-form refinement, clusterer swap, sporocarp-type-tree change), the historical DAG may contain predicates that no longer exist in the new schema. L1 formalizes:

- **Each contract-identity-level mutation creates a new trajectory epoch.**
- Trajectory queries default to **within-epoch** (current epoch only).
- **Cross-epoch trajectory queries** require an explicit predicate-translation table maintained by the substrate — itself a contract-identity-level object. Format L1-specified per substrate canon.
- Cross-epoch queries may be **lossy** (some predicates don't translate); this is acknowledged, not concealed. Long-horizon intent is recoverable within an epoch and partially recoverable across epochs.

Epoch markers are sporocarps of type `epoch_boundary` (contract-identity-level per L1_TROPISM.md §B3).

---

## §5. thread_id orthogonal grouping (optional)

Each delta and sporocarp may carry an optional opaque `thread_id` field — a lightweight, mechanically-typed grouping primitive. The agent declares "this delta belongs to long-running thread T". Threads are **not intent**; they are *declarative grouping*.

- **Cost**: 1 optional field per node.
- **Benefit**: cold-start works (thread_id set on first relevant operation); clusterer-independent (thread groupings survive `cluster_C` evolution); schema-evolution-resilient (opaque-typed, not predicate-typed).
- **Not a teleological claim**: an agent's thread_id misplacement is self-punishing (it loses its own grouping); no incentive to lie; mycoparasite attack from (a) doesn't transfer to (d).
- **Relationship to trajectory**: orthogonal. Trajectory clusters causally; threads group declaratively. Trajectory queries MAY use thread_id as a clustering hint (improving signal-poor cold-start), but trajectory is not defined by threads.

**L1 commits to**: thread_id is **OPTIONAL** at the substrate level. Substrate canon chooses whether to expose it. If exposed, L1 specifies the type (opaque string scoped per-substrate; UUID-like).

L1 leading proposal: **expose thread_id by default**; treat as a hint for trajectory clustering when present.

---

## §6. Cold-start behavior

At substrate genesis the causal DAG has one node (owner attestation per substrate-genesis sporocarp). For the first ~N substrate events, trajectory queries return ∅ or near-empty subgraphs. **This is the correct degenerate behavior**, not a hole:

- "The pair has no joint history yet" is a TRUE statement at t=0.
- Downstream consumers (L0 I3 self-validation, immune system) read appetite gradients directly via the dispatch surface (L1_TROPISM.md), not the trajectory view; they do NOT depend on trajectory being non-empty.
- The substrate's "expressed direction" during cold start is the agent's first few deltas themselves (read directly from the DAG, bypassing the clustering step).
- As DAG accumulates, trajectory becomes well-defined.

L1 commits: **trajectory queries during cold start return an explicit `cold_start` marker**, not an error. The substrate's empty trajectory is part of the substrate's honest state.

---

## §7. The honest cost

Position (b') trajectory derivation is correct AND the substrate is simpler for it — schema gains nothing. Cost is borne entirely at the query layer:

- Trajectory derivation is O(graph traversal + clustering), which depending on `cluster_C` is anywhere from O(n log n) to O(n²).
- A first-class typed intent (position (a)) would be O(1) lookup but creates an unverifiable self-report attack surface; trajectory's O(traversal) is the price of mycoparasite-resistance.
- Cost falls on **reading** intent, not on **recording** every move. Substrate stays clean; agent pays only when intent actually needs to be read.

**Practical mitigation** (L2/L3 territory):

- Trajectory views are cacheable per `(epoch, query-position, window-size)` — invalidated on new sporocarps within the window.
- Cold-start mode skips clustering entirely (returns DAG slice directly).

---

## §8. Intent is fossil-record, not teleology

L0 §5.3 commits to a structural property: the substrate's view of intent is the **fossil record** of what the pair did, not the **teleology** of what the agent aimed at. The substrate does not believe agent self-reports about goals; it sees only what was done. This is doctrinal (P1.c — there is no "agent purpose independent of operator", i.e., no teleology that exists outside what the pair actually did).

L1 reinforces this:

- Trajectory queries never return "the agent's stated goal". They return the directed pattern of operations.
- If an agent's stated goal (e.g., embedded in a delta's text content) diverges from the trajectory the substrate reads, the trajectory wins — empirically.
- Drift detection (per L0 §7 Living Bets falsifiability) is: trajectory shows wandering / inconsistency → immune-grade signal.

---

## §9. L2 / L3 design questions surfaced

These are deferred from L1 to lower layers:

- **Trajectory window defaults** — time-bounded (last 24h) vs operation-count-bounded (last N) vs graph-distance-bounded (k-hop from current frontier). L2 doctrine picks the default; substrate canon overrides.
- **Multi-trajectory composition** — if the pair has multiple parallel directions, return one composite cluster vs a set of clusters. L2 doctrine picks; substrate canon may override.
- **Cross-epoch translation-table format** — JSON / YAML / SQLite / custom. L3 choice.
- **Trajectory cache invalidation strategy** — L3 implementation choice.
- **Federation semantics for trajectory** — does a federated child substrate inherit the parent's trajectory? Per L0 P8 spore-schema definition, **no** (child begins its own DAG from genesis; trajectory derives from there). L2 doctrine codifies this.

L1 commits to *that* these decisions need to be made; L2/L3 commit to *which* decisions.
