# L2 — Trajectory Doctrine

> **Status**: DRAFT 1 (2026-05-13). Cross-cut doctrine theme (6th L2 doc, added in DRAFT 2 round per L2 pass-1 rhizomorph-1 gap finding).
> **Layer**: L2.
> **Scope**: intent derivation as cross-cut. Cross-cuts L0 §5.3 (intent NOT first-class) + L1_TRAJECTORY (the L1 mechanism) + L1_TROPISM §B6 (causal-proof on sporocarps) + L1_GOVERNANCE §1.2 / L1_HARD_RULES F17 (cluster_C as CI-fixed-point) + L1_SCHEMA §2 (DAG storage) + L2_EVOLUTION §5 (epoch boundaries) + L2_OBSERVABILITY §10 (operator view). Answers: how does v0.9 represent, derive, and read agent intent without storing it; what is the cross-doc impact of "intent is fossil-record, not teleology"?

---

## §1. The negative commitment (L0 §5.3)

Intent is **NOT a first-class substrate data type**. The substrate schema declares no `intent` node type, no `intent` field on operations or sporocarps, no `goal` field on raw material. Agent-self-reported intent is structurally not trusted (per P1.c — substrate sees what the pair *does*, not what the agent *claims*).

This is L0-doctrinal. Everything in this L2 doc operates within that commitment.

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

## §3. Fossil-record vs teleology (L1_TRAJECTORY §8 — cross-cut elevated)

The substrate's view of intent is the **fossil record** of what the pair did, not the **teleology** of what the agent aimed at. This is structurally enforced:

- Trajectory queries never return "the agent's stated goal".
- If an agent's stated goal (embedded in delta text content) diverges from the trajectory the substrate reads, **the trajectory wins** — empirically.
- Drift detection (per L2_OBSERVABILITY §3): trajectory showing wandering or inconsistency contributes to the Living Bets `bet_weakening_quorum` trigger.

**Cross-cut to observability**: trajectory is itself an observable. The substrate doesn't merely use trajectory internally — it surfaces trajectory query results to the operator-agent (via L1_TROPISM §B4 gradient digest) and to owner-side audit (via anchor surface logs). The pair sees its own fossil record.

**Cross-cut to trust model**: the agent cannot retroactively rewrite the trajectory by claiming "I meant something else" — the DAG is full-fidelity (I4); trajectory queries reproduce identically given (DAG, cluster_C). Per L1_HARD_RULES C7 (`dag_retro_edit_detected`), DAG retro-editing is breach.

---

## §4. Cold-start (L1_TRAJECTORY §3 — cross-cut elevated)

At substrate genesis the causal DAG has only the `genesis_event` sporocarp + owner birth attestation. Trajectory queries return ∅ or near-empty subgraphs for the first ~N operations. **This is correct degenerate behavior:**

- "The pair has no joint history yet" is TRUE at t=0.
- Downstream consumers do NOT depend on trajectory being non-empty (per L2_OBSERVABILITY §4 — appetite gradients are the primary substrate-internal signal source, not trajectory).
- L1 commits: cold-start returns explicit `cold_start_marker`, not error.

**Cross-cut to lifecycle**: cold-start aligns with L2_LIFECYCLE §3 birth period. During birth, both gradient configuration and trajectory are accumulating. The substrate's "expressed direction" during birth is the agent's first few deltas themselves (read directly from DAG, bypassing clustering step). Trajectory becomes well-defined as DAG accumulates.

---

## §5. Clusterer coupling (L1_TRAJECTORY §4 — cross-cut elevated)

`cluster_C` is a **substrate-resident object** with CI-level mutation governance:

- Different clustering algorithms produce different trajectories from identical DAG histories.
- L1 commits: changing `cluster_C` is contract-identity-level (per L1_GOVERNANCE §1.2 + L1_HARD_RULES F17).
- I4 full-fidelity-recoverability: the DAG is unchanged by clusterer evolution; what changes is the trajectory *view*.

**Cross-cut to evolution**: cluster_C swap is an epoch-boundary event (per L2_EVOLUTION §5). Trajectory queries in flight at swap time are aborted with `clusterer_swap_interrupted` marker; may be re-issued against new clusterer. Past trajectories from a previous epoch are read through that epoch's clusterer, not the current one — epochs preserve clusterer-consistency within their span.

**Cross-cut to versioning** (per L2_EVOLUTION §4): cluster_C is one of the substrate-resident objects under active-prefix + archived-tail discipline if L4 chooses to retain historical clusterers; alternatively, only the current cluster_C is stored, and pre-epoch trajectory queries are explicitly bounded (per L2_EVOLUTION §5 cross-epoch deferral).

---

## §6. thread_id — orthogonal grouping (L1_TRAJECTORY §6 — cross-cut elevated)

Each delta and sporocarp MAY carry an optional opaque `thread_id` field — a lightweight grouping primitive declared by the agent ("this delta belongs to long-running thread T").

- **Not teleological** — agent's thread_id misplacement is self-punishing (loses own grouping); no incentive to lie.
- **Cost**: 1 optional field per node.
- **Benefit**: cold-start works; clusterer-independent (survives cluster_C evolution); schema-evolution-resilient (opaque-typed, not predicate-typed).

L1 commits: thread_id is **OPTIONAL** at substrate level. Substrate canon at genesis chooses whether to expose it.

**Cross-cut to schema**: if exposed, thread_id is a sporocarp field per L1_SCHEMA §3.1 spore-schema (inheritable). Type is opaque string scoped per-substrate.

**Cross-cut to trust model**: thread_id is NOT a trust-bearing claim — it's a declarative grouping the agent CAN lie about, but doing so harms only itself. The trust model does not validate thread_id semantics; it's a self-organizing primitive.

---

## §7. Trajectory injection defense (L1_TRAJECTORY §7 — cross-cut elevated)

The agent is the only delta source. An adversarial agent could flood deltas crafted to make `cluster_C` produce a desired trajectory T (engineered self-citation). The trajectory then "honestly" shows T; downstream consumers trust it; immune-grade drift signal suppressed.

**Defense**: trajectory derivation includes **delta-novelty weighting** — deltas whose `causal_in_edges` (per L1_TROPISM §B6 causal-proof) trace overwhelmingly to recent same-substrate citations are **down-weighted** in clustering.

**Detection**: trajectory dominated by self-citation chains beyond an L1-tunable threshold (default ≥80% recent-window self-citations) emits an `echo_chamber` immune sporocarp.

**Substrate-keyed, not operator-keyed** (per L2 pass-2 mycoparasite-33): the detection is a property of DAG structure, not operator-sessions. Avoids conflict with L0 I1 prohibition on persisting operator-discriminating attributes AND logout-reconnect-replay bypass.

**Cross-cut to trust model**: this is the **trajectory-injection-attack** defense. The attack surface is enumerated in L1_HARD_RULES (implicitly via `echo_chamber` as one of the lesser-than-CRITICAL immune events). The defense is substrate-internal; the agent cannot disable it without CI mutation of the trajectory mechanism.

---

## §8. Trajectory observability surface (cross-cut to L2_OBSERVABILITY)

Trajectory becomes an **observable** at three points:

1. **Operator-side**: gradient digest may include current-trajectory subgraph reference (L1_TROPISM §B4); operator reads the substrate's empirical view of "what we've been doing".
2. **Substrate-internal**: immune system observes trajectory drift (echo-chamber detection; long-horizon convergence patterns); aggregates into observatory signal #3 (read-pattern diversity per L0 §7).
3. **Owner-side**: anchor-surface audit can replay trajectory query at any historical DAG-tip co-sign point (DAG is full-fidelity; trajectory is reproducible given (DAG, cluster_C_at_timestamp)).

**Cross-cut to L2_OBSERVABILITY §10**: this is the operator-side observability surface. The agent's view of the substrate's view of the pair's intent is structurally enforced as "fossil-record" — neither party can lie about it without violating I4 (DAG integrity).

---

## §9. Trajectory through federation (cross-cut to L2_FEDERATION)

Per L1_TRAJECTORY §9 deferred: federation trajectory semantics — child substrate begins its own DAG from genesis; trajectory does NOT transfer; child trajectory derives from its own DAG.

**Cross-cut to federation**: federation event content is canonical-bytes serialized (per L1_GOVERNANCE §5.3). Trajectory from substrate A is NOT a federation event payload — it's a derived view that doesn't travel. What travels are federation sporocarps (typed content); the child's trajectory clusters its own ingested federation sporocarps as part of its own metabolism.

This means: **intent does not federate**. Each substrate has its own intent (its own trajectory over its own DAG). Federation transfers content, not direction.

---

## §10. Open at L2

Inherited from L1_TRAJECTORY §9 deferred items + new L2 cross-cut questions:

- **Trajectory window default**: time-bounded / count-bounded / graph-distance-bounded — L4 picks.
- **Multi-trajectory composition**: single composite vs set of clusters — L2 doctrine could codify; recommendation: set of clusters (per pass-2 mycorrhiza if applicable).
- **Cross-epoch translation table format**: deferred to L4 per L2_EVOLUTION §5.
- **Specific `cluster_C` algorithm**: L4 picks per L1_TRAJECTORY §4 candidate families.
- **Specific `thread_id` construction**: L4 picks per L1_TRAJECTORY §6.
- **Specific delta-novelty algorithm + echo-chamber threshold**: L4 picks per L1_TRAJECTORY §7.
- **Trajectory cache invalidation strategy**: L3 implementation choice.
- **Federation trajectory inheritance** (currently NO per L1): is there any case where partial trajectory should pre-seed a child? Likely NO; preserves P1.c carrier-asymmetry. L4 confirms.

---

## §11. Why trajectory deserves its own L2 doc

Trajectory cross-cuts more L1 docs (5: L1_TRAJECTORY, L1_TROPISM, L1_GOVERNANCE, L1_SCHEMA, L1_HARD_RULES) and more L2 docs (4: TRUST_MODEL, EVOLUTION, FEDERATION, OBSERVABILITY) than any other single concept except trust itself. Without an L2 trajectory doc, the cross-cut perspective is scattered across §5 of L2_EVOLUTION and §10 of L2_OBSERVABILITY without a unifying doctrinal home.

L2_TRAJECTORY closes the L2-layer cross-cut coverage. After this doc, every load-bearing L1 mechanism has a corresponding L2 doctrinal cross-cut: trust (L2_TRUST_MODEL), lifecycle (L2_LIFECYCLE), evolution (L2_EVOLUTION), federation (L2_FEDERATION), observability (L2_OBSERVABILITY), and intent (this doc).
