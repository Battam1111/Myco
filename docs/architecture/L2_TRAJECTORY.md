# L2 — Trajectory Doctrine

> **Status**: DRAFT 2 (2026-05-17, M27 CA5 cleanup). Cross-cut doctrine theme.
> **Scope**: intent derivation as cross-cut. Cross-cuts L0 §5.3 + L1_TRAJECTORY + L1_TROPISM §B6 + L1_GOVERNANCE §1.2 / L1_HARD_RULES F17 + L1_SCHEMA §2 + L2_EVOLUTION §5 + L2_OBSERVABILITY §11.

---

## §1. The negative commitment

**Source**: L0 §5.3 (intent NOT first-class; no `intent` node type, no `intent`/`goal` field on operations / sporocarps / raw material). Per P1.c, agent-self-reported intent is structurally not trusted. Everything in this L2 doc operates within that commitment.

---

## §2. The positive form: trajectory derivation

Per L1_TRAJECTORY: intent is **emergent from the causal DAG**, materialized as a **trajectory view** — a query, not a stored type.

```
intent(t) := cluster_C(causal_ancestors_and_descendants(neighborhood(t)))
```

Trajectory is a function of `(DAG, cluster_C)` jointly. The DAG is substrate state (I4); `cluster_C` is a substrate-resident object with its own identity (per L1_HARD_RULES F17 — CI fixed-point).

**Cross-cut to governance**: `cluster_C` mutation is CI-level (rotation requires owner attestation via L1_GOVERNANCE §2.2 attestation protocol). The substrate cannot silently change how trajectories are read.

**Cross-cut to schema**: trajectory queries traverse the Merkle DAG (per L1_SCHEMA §2.1); proof of causal-ancestry uses parent-hashes; closure verification at CI events (per L1_SCHEMA §2.2) verifies the DAG that trajectory queries operate over.

**Cross-cut to evolution**: each contract-identity-level mutation creates a trajectory epoch boundary (per L2_EVOLUTION §5 + L1_TRAJECTORY §5). Trajectory queries default to within-epoch.

---

## §3. Fossil-record vs teleology (cross-cut elevated from L1_TRAJECTORY §8)

The substrate's view of intent is the **fossil record** of what the pair did, not the **teleology** of what the agent aimed at:

- Trajectory queries never return "the agent's stated goal".
- If an agent's stated goal (in delta text) diverges from the trajectory the substrate reads, **the trajectory wins**.
- Drift detection: trajectory wandering contributes to the Living Bets `bet_weakening_quorum` trigger (cross-ref L2_OBSERVABILITY §3 + L0 §7.4).

**Cross-cut to observability + trust model**: trajectory is an observable surfaced to the operator-agent (L1_TROPISM §B4) + Cultivator-side audit (anchor surface logs). The pair sees its own fossil record. The agent cannot retroactively rewrite trajectory: DAG is full-fidelity (I4); trajectory queries reproduce identically given `(DAG, cluster_C)`. DAG retro-editing is breach (L1_HARD_RULES C7).

---

## §4. Cold-start (cross-cut elevated from L1_TRAJECTORY §3)

**Mechanism**: L1_TRAJECTORY §3 (cold-start returns explicit `cold_start_marker`, not error). **Lifecycle alignment**: L2_LIFECYCLE §3 birth-period (during birth, both gradient configuration and trajectory are accumulating; substrate's "expressed direction" is read directly from DAG, bypassing clustering).

**Cross-cut commitment**: downstream consumers do NOT depend on trajectory being non-empty (appetite gradients are the primary substrate-internal signal source, not trajectory).

---

## §5. Clusterer coupling (cross-cut elevated from L1_TRAJECTORY §4)

`cluster_C` is a substrate-resident object with CI-level mutation governance (per L1_GOVERNANCE §1.2 + L1_HARD_RULES F17). I4 unchanged by clusterer evolution; what changes is the trajectory *view*.

**Cross-cut to evolution**: `cluster_C` swap is an epoch-boundary event (L2_EVOLUTION §5). Trajectory queries in flight at swap abort with `clusterer_swap_interrupted` marker. Past trajectories from a previous epoch are read through that epoch's clusterer, preserving clusterer-consistency within span. Historical clusterer retention follows L1_GOVERNANCE §3.1 active-prefix + archived-tail discipline if L4 elects retention.

---

## §6. thread_id — orthogonal grouping (cross-cut elevated)

**Mechanism**: L1_TRAJECTORY §6 (optional opaque field per delta/sporocarp; agent-declared; misplacement is self-punishing — no incentive to lie). **Schema integration**: L1_SCHEMA §3.1 (if exposed, thread_id is a sporocarp field on inheritable spore-schema; opaque-string-typed per-substrate).

**Cross-cut to trust model**: thread_id is NOT a trust-bearing claim; trust model does not validate thread_id semantics; it's a self-organizing primitive.

---

## §7. Trajectory injection defense (cross-cut elevated)

**Mechanism**: L1_TRAJECTORY §7 (delta-novelty weighting; deltas whose `causal_in_edges` overwhelmingly trace to recent same-substrate citations are down-weighted; threshold breach emits `echo_chamber` immune sporocarp; substrate-keyed not operator-keyed — avoids logout-reconnect-replay bypass + L0 I1 conflict).

**Cross-cut to trust model**: trajectory-injection is the named attack surface. Defense is substrate-internal; agent cannot disable without CI mutation of the trajectory mechanism.

---

## §8. Trajectory observability surface

**Three observation points** (full spec L2_OBSERVABILITY §11):
1. **Operator-side**: gradient digest may include current-trajectory subgraph reference (L1_TROPISM §B4).
2. **Substrate-internal**: immune system observes trajectory drift; aggregates into observatory signal #3 (read-pattern diversity).
3. **Cultivator-side**: anchor-surface audit replays trajectory query at any historical DAG-tip co-sign point; trajectory is reproducible given `(DAG, cluster_C_at_timestamp)`.

---

## §9. Trajectory through federation

**Cross-ref**: L2_FEDERATION + L1_TRAJECTORY §9 (deferred). Federation event content is canonical-bytes serialized (L1_GOVERNANCE §5.3); trajectory itself is NOT a federation event payload — it's a derived view that doesn't travel.

**Commitment**: **intent does not federate**. Each substrate has its own intent (its own trajectory over its own DAG). Federation transfers content, not direction.

---

## §10. Open at L2

Inherited from L1_TRAJECTORY §9 deferred items + new L2 cross-cut questions:

- **Trajectory window default**: time-bounded / count-bounded / graph-distance-bounded — L4 picks.
- **Multi-trajectory composition**: single composite vs set of clusters; recommendation: set of clusters.
- **Cross-epoch translation table format**: deferred to L4 per L2_EVOLUTION §5.
- **Specific `cluster_C` algorithm**: L4 picks per L1_TRAJECTORY §4 candidate families.
- **Specific `thread_id` construction**: L4 picks per L1_TRAJECTORY §6.
- **Specific delta-novelty algorithm + echo-chamber threshold**: L4 picks per L1_TRAJECTORY §7.
- **Trajectory cache invalidation strategy**: L3 implementation choice.
- **Federation trajectory inheritance** (currently NO per L1): is there any case where partial trajectory should pre-seed a child? Likely NO; preserves P1.c carrier-asymmetry. L4 confirms.

