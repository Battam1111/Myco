# L2 — Trajectory Doctrine

> **Status**: DRAFT 3 (2026-05-17, M27 R5 cleanup). Cross-cuts L0 §5.3 + L1_TRAJECTORY + L1_TROPISM §B6 + L1_GOVERNANCE §1.2 / L1_HARD_RULES F17 + L1_SCHEMA §2 + L2_EVOLUTION §5 + L2_OBSERVABILITY §11.

---

## §1. Negative commitment

L0 §5.3: intent NOT first-class; no `intent` node type; no `intent`/`goal` field on operations/sporocarps/raw material. P1.c: agent-self-reported intent structurally not trusted.

---

## §2. Trajectory derivation

Intent is emergent from causal DAG as trajectory view — query, not stored type:

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

Function of `(DAG, cluster_C)`. DAG = substrate state (I4); `cluster_C` substrate-resident with CI fixed-point identity (L1_HARD_RULES F17). Governance: `cluster_C` mutation CI-level (L1_GOVERNANCE §2.2). Schema: queries traverse Merkle DAG (L1_SCHEMA §2.1); proof via parent-hashes; closure verified at CI. Evolution: each CI mutation creates trajectory epoch boundary (L2_EVOLUTION §5 + L1_TRAJECTORY §5); queries default within-epoch.

---

## §3-§5. Fossil + cold-start + clusterer

§3 fossil-record: substrate's intent view is what the pair *did*, not what agent *aimed at*. Queries never return "agent's stated goal"; stated-goal vs trajectory divergence → trajectory wins. Drift contributes to `bet_weakening_quorum` (L2_OBSERVABILITY §3 + L0 §7.4); surfaced to operator (L1_TROPISM §B4) + Cultivator-audit. Retro-rewrite impossible (DAG full-fidelity per I4; queries reproduce identically given `(DAG, cluster_C)`; retro-editing = C7 breach).

§4 cold-start: L1_TRAJECTORY §3 (explicit `cold_start_marker`, not error). L2_LIFECYCLE §3 birth-period: "expressed direction" read directly from DAG, bypassing clustering. Downstream consumers do NOT depend on trajectory being non-empty (appetite gradients are primary internal signal).

§5 clusterer coupling: `cluster_C` substrate-resident; CI-mutation-governed. I4 unchanged by clusterer evolution; what changes is the view. Swap is epoch-boundary (L2_EVOLUTION §5); in-flight queries abort with `clusterer_swap_interrupted`. Past trajectories read through their epoch's clusterer. Historical retention per L1_GOVERNANCE §3.1 active-prefix + archived-tail if L4 elects.

---

## §6-§7. thread_id + injection defense

§6 thread_id: L1_TRAJECTORY §6 (optional opaque per delta/sporocarp; agent-declared; misplacement self-punishing). Schema: L1_SCHEMA §3.1 (inheritable spore-schema field; opaque-string per-substrate). NOT trust-bearing; self-organizing primitive.

§7 injection defense: L1_TRAJECTORY §7 (delta-novelty weighting; deltas whose `causal_in_edges` overwhelmingly trace to recent same-substrate citations down-weighted; breach emits `echo_chamber` immune; substrate-keyed not operator-keyed — avoids logout-reconnect-replay bypass + L0 I1 conflict). Substrate-internal; agent cannot disable without CI mutation.

---

## §8-§9. Observability + federation

§8 observability (L2_OBSERVABILITY §11): (1) **Operator-side** — gradient digest may include current-trajectory subgraph reference (L1_TROPISM §B4); (2) **Substrate-internal** — immune observes drift; aggregates into signal #3; (3) **Cultivator-side** — anchor-audit replays query at any historical DAG-tip co-sign point; reproducible given `(DAG, cluster_C_at_timestamp)`.

§9 federation (L2_FEDERATION + L1_TRAJECTORY §9 deferred): federation event content canonical-bytes (L1_GOVERNANCE §5.3); trajectory itself NOT a federation payload — derived view that doesn't travel. **Commitment**: intent does not federate; each substrate has its own intent over its own DAG. Federation transfers content, not direction.
