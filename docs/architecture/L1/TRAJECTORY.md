> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4); see `docs/architecture/OUTLINE.md` §3 for details.

---

# L1: Trajectory (positive intent-derivation mechanism for Myco v0.9)

> L1 for intent-derivation satisfying L0/cards/P01c_asymmetric_carrier.md §5.3.
> Cross-cuts L1/TROPISM §B4/§B6 + L1/GOVERNANCE §1.2/§2.2/§3.1/§5.3/§6.3 + L1/HARD_RULES F17 + L1/SCHEMA §2.1/§3.1 + L1/CONTINUITY §6.2 + L2/OBSERVABILITY §3/§11 + L2/FEDERATION.

---

## §1. The form: intent as derived view

Intent IS the directed pattern of operations (deltas + sporocarps) the operator-substrate pair has performed together over a recent DAG window, projected onto a current point in time. Computed, not stored. Schema gains zero new types.

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

`cluster_C` is substrate's currently-designated clustering algorithm. Intent is a function of `(DAG, cluster_C)` jointly. DAG = substrate state (I4); `cluster_C` = CI fixed-point (L1/HARD_RULES F17 + L1/GOVERNANCE §2.2). Queries traverse Merkle DAG (L1/SCHEMA §2.1); closure verified at CI.

---

## §2. Why trajectory beats stored alternatives

| Position | Why rejected |
|---|---|
| **(a) First-class Intent record** | Self-reported → unverifiable. Agent writes `intent=X` while pursuing Y. Intent becomes agent-private (violates P1.c). |
| **(c) NL metadata + vector embed** | Still self-reported; per-item joint, not as-symbiosis joint. |
| **(b') Trajectory query** *(chosen)* | No self-report surface; necessarily joint per P1.c; phantom-intents impossible; long-horizon recoverable across reconnections. |

Fourth position (d) thread_id grouping: orthogonal (see §6).

---

## §3. Cold-start

Genesis DAG contains only `genesis_event` (keyless v3.1.5: the prior owner-signed birth attestation is retired with the anchor surface; substrate-ID is self-derived per L1/GOVERNANCE §4.1, F2). Early queries return ∅ or near-empty subgraphs. Substrate's "expressed direction" cold start IS agent's first few deltas (read directly from DAG, bypassing clustering per L1/CONTINUITY §6.2 birth-period). Queries MUST return explicit `cold_start_marker`, not error. Downstream consumers do NOT depend on trajectory being non-empty (appetite gradients are primary internal signal).

---

## §4. Clusterer coupling

- `cluster_C` IS a substrate-resident object with own identity (NOT free parameter).
- Changing `cluster_C` IS CI: retroactively alters past intents.
- I4 full-fidelity: DAG unchanged by clusterer evolution; trajectory *view* changes. Past trajectories read through their epoch's clusterer; historical retention per L1/GOVERNANCE §3.1 active-prefix + archived-tail if L4 elects.
- Candidate algorithms (L4): graph community detection (Louvain/Leiden/label-propagation); density (HDBSCAN/OPTICS); hierarchical; hybrid.
- **Atomicity**: cluster_C swap IS epoch-boundary event (§5); in-flight queries abort with `clusterer_swap_interrupted` or snapshot-isolate to clusterer active at query start.

---

## §5. Schema-evolution epochs

Each CI mutation creates trajectory epoch boundary recorded as `epoch_boundary` sporocarp (L1/TROPISM §B3); queries default to current epoch; cross-epoch queries L1-deferred until first schema mutation surfaces concrete translation requirements.

---

## §6. thread_id: orthogonal grouping primitive

Each delta/sporocarp MAY carry optional opaque `thread_id`: lightweight agent-declared grouping (schema: L1/SCHEMA §3.1 inheritable spore-schema field; opaque-string per-substrate). NOT trust-bearing; self-organizing primitive; misplacement self-punishing. Cost: 1 optional field per node; benefit: cold-start works, clusterer-independent, schema-evolution-resilient. Queries MAY use thread_id as clustering hint but trajectory ≠ threads. **L1 commits**: thread_id OPTIONAL; substrate canon at genesis chooses to expose; opaque string scoped per-substrate. Recommended default: expose; use as clustering hint.

---

## §7. Trajectory-injection defense

Algorithm: `algorithms/echo_chamber_detection.md`. Defense structure (delta-novelty weighting + `echo_chamber` immune sporocarp + substrate-keyed detection) L1-committed; down-weighting algorithm + threshold L4. Deltas whose `causal_in_edges` overwhelmingly trace to recent same-substrate citations down-weighted; substrate-keyed not operator-keyed, which avoids logout-reconnect-replay bypass + L0 I1 conflict. Substrate-internal; agent cannot disable without CI mutation.

---

## §8. Fossil-record vs teleology

Per L0/cards/P01c_asymmetric_carrier.md §5.3: substrate's view of intent IS fossil-record honest, not teleologically-honest. Trajectory queries never return "agent's stated goal"; divergence → trajectory wins empirically; trajectory wandering feeds `bet_weakening_quorum` (L2/OBSERVABILITY §3 + L0/cards/LB_living_bets.md §3 (falsifiability quorum)); drift surfaced to operator (§9 + L1/TROPISM §B4) + Cultivator-audit. Retro-rewrite impossible (DAG full-fidelity per I4; queries reproduce identically given `(DAG, cluster_C)`; retro-editing = C7 breach).

---

## §9. Observability + federation (cross-cuts)

**Observability** (L2/OBSERVABILITY §11): (1) *Operator-side*: gradient digest may include current-trajectory subgraph reference (L1/TROPISM §B4); (2) *Substrate-internal*: immune observes drift; aggregates into signal #3; (3) *Cultivator-side*: the cultivator replays the query at any historical DAG-tip at the live CI gate (keyless v3.1.5: was an anchor-audit at a DAG-tip co-sign point); reproducible given `(DAG, cluster_C_at_timestamp)`.

**Federation** (L2/FEDERATION; L1 deferral): federation event content canonical-bytes (L1/GOVERNANCE §5.3); trajectory itself NOT a federation payload: a derived view that doesn't travel. **Commitment**: intent does not federate; each substrate has its own intent over its own DAG. Federation transfers content, not direction.
