# L2 — Trajectory Doctrine

> **Status**: DRAFT 2 (2026-05-17, M27 CA5 cleanup). Cross-cuts L0 §5.3 + L1_TRAJECTORY + L1_TROPISM §B6 + L1_GOVERNANCE §1.2 / L1_HARD_RULES F17 + L1_SCHEMA §2 + L2_EVOLUTION §5 + L2_OBSERVABILITY §11.

---

## §1. Negative commitment

L0 §5.3: intent NOT first-class; no `intent` node type, no `intent`/`goal` field on operations/sporocarps/raw material. P1.c: agent-self-reported intent structurally not trusted.

---

## §2. Trajectory derivation

Intent is **emergent from the causal DAG** as a **trajectory view** — a query, not a stored type:

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

Function of `(DAG, cluster_C)`. DAG is substrate state (I4); `cluster_C` is substrate-resident with CI fixed-point identity (L1_HARD_RULES F17).

- **Governance cross-cut**: `cluster_C` mutation is CI-level (L1_GOVERNANCE §2.2). Substrate cannot silently change how trajectories are read.
- **Schema cross-cut**: trajectory queries traverse Merkle DAG (L1_SCHEMA §2.1); proof via parent-hashes; closure verified at CI events (§2.2).
- **Evolution cross-cut**: each CI mutation creates trajectory epoch boundary (L2_EVOLUTION §5 + L1_TRAJECTORY §5); queries default within-epoch.

---

## §3. Fossil-record vs teleology

Substrate's view of intent is fossil record of what the pair did, not teleology of what the agent aimed at:

- Trajectory queries never return "the agent's stated goal".
- Stated-goal vs trajectory divergence: trajectory wins.
- Drift contributes to `bet_weakening_quorum` (L2_OBSERVABILITY §3 + L0 §7.4).
- Trajectory surfaced to operator-agent (L1_TROPISM §B4) + Cultivator-side audit (anchor surface logs); pair sees its own fossil record.
- Retro-rewrite impossible: DAG is full-fidelity (I4); queries reproduce identically given `(DAG, cluster_C)`; DAG retro-editing is C7 breach.

---

## §4. Cold-start

L1_TRAJECTORY §3 (returns explicit `cold_start_marker`, not error). Lifecycle alignment: L2_LIFECYCLE §3 birth-period — substrate's "expressed direction" read directly from DAG, bypassing clustering. Downstream consumers do NOT depend on trajectory being non-empty (appetite gradients are primary internal signal).

---

## §5. Clusterer coupling

`cluster_C` is substrate-resident, CI-mutation-governed (L1_GOVERNANCE §1.2 + L1_HARD_RULES F17). I4 unchanged by clusterer evolution; what changes is the view. Swap is epoch-boundary event (L2_EVOLUTION §5); in-flight queries abort with `clusterer_swap_interrupted`. Past trajectories read through their epoch's clusterer (consistency within span). Historical clusterer retention follows L1_GOVERNANCE §3.1 active-prefix + archived-tail if L4 elects retention.

---

## §6. thread_id — orthogonal grouping

L1_TRAJECTORY §6 (optional opaque field per delta/sporocarp; agent-declared; misplacement self-punishing). Schema: L1_SCHEMA §3.1 (sporocarp field on inheritable spore-schema; opaque-string-typed per-substrate). NOT a trust-bearing claim; self-organizing primitive only.

---

## §7. Trajectory injection defense

L1_TRAJECTORY §7 (delta-novelty weighting; deltas whose `causal_in_edges` overwhelmingly trace to recent same-substrate citations down-weighted; breach emits `echo_chamber` immune sporocarp; substrate-keyed not operator-keyed — avoids logout-reconnect-replay bypass + L0 I1 conflict). Substrate-internal defense; agent cannot disable without CI mutation.

---

## §8. Observability surface

L2_OBSERVABILITY §11 — three observation points:
1. **Operator-side** — gradient digest may include current-trajectory subgraph reference (L1_TROPISM §B4).
2. **Substrate-internal** — immune system observes drift; aggregates into observatory signal #3 (read-pattern diversity).
3. **Cultivator-side** — anchor-surface audit replays trajectory query at any historical DAG-tip co-sign point; reproducible given `(DAG, cluster_C_at_timestamp)`.

---

## §9. Federation

L2_FEDERATION + L1_TRAJECTORY §9 (deferred). Federation event content is canonical-bytes serialized (L1_GOVERNANCE §5.3); trajectory itself is NOT a federation payload — derived view that doesn't travel.

**Commitment**: intent does not federate. Each substrate has its own intent (its own trajectory over its own DAG). Federation transfers content, not direction.
