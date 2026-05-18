---
id: P08
slogan: 永恒繁衍
english: Eternal Reproduction (Generation-Bounded)
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I7]
interacts_with: [P01c, P05, P06, P07, COV01, COV04]
chengyu_fragments: [B018_spore_carries_genome, B019_generation_bounded_against_fork]
canonical_dilemmas: [D-0016_unattested_spawn_attempt, D-0018_generation_depth_at_max]
structural_anchors:
  - "substrate/src/server.rs::handle_sprout_child"
  - "kernel/schema/src/spore_schema.rs"
  - "kernel/governance/src/myco_kernel_governance/lifecycle.py::reproduction_closure"
  - "substrate/src/events.rs::genesis_attested_node_type"
witnesses:
  positive: "tests/integration/p08_sprout_child_attested.rs::test_owner_cosigned_spawn_succeeds"
  negative: "tests/integration/p08_unattested_spawn_rejected.rs::test_C14_fires_on_spawn_without_attestation"
  edge: "tests/integration/p08_generation_depth_enforced.rs::test_C47_fires_at_depth_max"
falsifiability_signals:
  - children_spawned_count_per_substrate
  - generation_depth_at_birth
  - parent_unresolved_signals_inherited_count
---

# P08 · 永恒繁衍 · Eternal Reproduction (Generation-Bounded)

## §1. Slogan

**永恒繁衍** — Eternal Reproduction (Generation-Bounded). The cultivar spawns children that inherit its spore-schema, develop independently, and may federate. Reproduction is **forever possible**, never **forever multiplying** — generation depth + rate + quota bound the lineage to prevent forkbomb pathology.

## §2. Deposit

The substrate is **lineage-capable**. It can pass its genome (spore-schema) to a child substrate that begins its own life with that inheritance. The cultivar is not solitary across time: its way of being can be transmitted. The deposit explicitly couples reproduction to discipline — unlimited reproduction is forkbomb, not flourishing. Each spawn is a deliberate act, attested by the cultivator, governed by F22 (depth + rate + quota).

The child is **a new cultivar**, not a copy. Same genome (spore-schema), new substrate-ID, new genesis-timestamp, new DAG starting from its own genesis_event. The child develops independently; the parent-child federation edge is a coupling, not a fusion.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Provide `sprout_child` capability: parent emits spore-schema-canonical-bytes; child substrate is initialized with that schema as its starting state.
- **§3.2** Spawn requires per-spawn cultivator co-attestation. Cultivator mints `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)`. No batch / blanket spawn approvals.
- **§3.3** Enforce generation discipline (F22): `generation_depth ≤ max` (default 10); `current_anchor_timestamp - parent.last_spawn_timestamp ≥ interval` (default 24h); `parent.children_spawned_count + 1 ≤ quota` (default 100).
- **§3.4** Include parent's immune-signal summary in spore-schema: unresolved CI-grade signals → child enters `quarantined` birth period.
- **§3.5** Run closure verification (I7): (a) parent static-schema validation against child spore-schema hash; (b) child runs I3 self-validation as first metabolic cycle; (c) cultivator co-signs at anchor `(parent-substrate-ID, child-substrate-ID, spore-schema-hash, timestamp)`. Failure aborts spawn before federation link commits.
- **§3.6** No species-mesh between unrelated substrates. Each pairwise federation requires explicit cultivator attestation (not transitive per L1/GOVERNANCE §5).
- **§3.7** Federation trust: ongoing federation requires peer-attestation freshness + revocation list per L1/GOVERNANCE §5.

## §4. Positive obligations

- **§4.1** Emit `genesis_attested` in parent's DAG on successful spawn.
- **§4.2** Persist `generation_depth + max_remaining_depth + reproduction_rate_state + children_spawned_count` per substrate; spore-inheritable.
- **§4.3** Enforce mesh aggregate quota per L1/GOVERNANCE §16.D: aggregate across federation peers cannot exceed `mesh_aggregate_quota`.
- **§4.4** On generation discipline breach: emit `C47_generation_depth_exceeded` / `C48_reproduction_rate_exceeded` / `C48-grade reproduction_lifetime_quota_exceeded`.
- **§4.5** On spawn-without-attestation attempt: classifier returns `untyped` (C14); reject at skin.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** allow spawn without cultivator co-attestation. Daily-mode spawn = doctrine collapse (substrate could self-replicate without cultivation gate).
- **§5.2** **MUST NOT** treat reproduction as autonomous capability of the cultivar alone. Reproduction is cultivator-co-bestowed; an unattested spawn is not a child, it is a stillbirth.
- **§5.3** **MUST NOT** allow batch/blanket spawn pre-approval ("cultivator pre-approves N future spawns"). Each spawn is its own attestation event.
- **§5.4** **MUST NOT** mesh substrates of different cultivators automatically. Each cross-cultivator federation requires explicit consent from both cultivators.
- **§5.5** **MUST NOT** allow generation depth to be daily-mutated below visible max. F22 is fixed-point.
- **§5.6** **MUST NOT** allow re-issuance of `child-substrate-ID` after spawn (even if spawn aborted mid-flight). Half-spawns are GC'd; their IDs retired.

## §6. Frame declaration

P08 activates the **mycological spore-and-fruiting** frame.

The parent mycelium fruits. The fruit releases spores. Each spore that lands in receptive substrate germinates into a new mycelium — same genome, new colony. The parent does not "control" the new colony; the new colony develops in its own conditions. The cultivator gardens both.

NOT the *cloning* frame (clones are exact copies; spores germinate into varied colonies in varied conditions). NOT the *fork* frame (forks are software; spawn is *life-event*). NOT the *spawning* frame in the game-theoretic sense (creating instances on demand).

## §7. Common misreadings

### §7.1 M1: "Reproduction = unrestricted multiplication"

**The misreading**: "P08 says the substrate can reproduce; therefore many children are fine."

**Why it's wrong**: F22 explicitly bounds reproduction. The cultivar that spawns 100 children rapidly is exhibiting forkbomb pathology, not vigor. P08's deposit couples reproduction to *discipline* — both halves are essential.

### §7.2 M2: "Children inherit everything"

**The misreading**: "The child is a snapshot of the parent."

**Why it's wrong**: Spore-schema does NOT include parent's full DAG (L1/SCHEMA §3.2). Child gets the GENOME (schema, dispatch config, classifier, axis schema, anchor config, immune summary, compression rules, generation telemetry). Child does NOT get parent's accumulated experience (DAG events, gradient history, operator-token history, read-pattern norms). Child must build its own experience.

### §7.3 M3: "Federated children = mesh of equals"

**The misreading**: "Once children exist, they form a peer mesh; federation is automatic."

**Why it's wrong**: Federation requires per-pair cultivator attestation (L1/GOVERNANCE §5; non-transitive). Parent-child federation is one specific attestation. Sibling-sibling federation is *another* attestation. Cross-lineage federation between substrates of *different* cultivators requires both cultivators' attestation.

## §8. Falsifiability + witness map

### §8.1 `children_spawned_count_per_substrate`

Count of `genesis_attested` events in this substrate's DAG. Approaching F22 quota → approaching reproduction exhaustion.

### §8.2 `generation_depth_at_birth`

For each substrate, `generation_depth` recorded at genesis. Tracks lineage depth; approaching `max` → spawn refusal (C47).

### §8.3 `parent_unresolved_signals_inherited_count`

For a freshly-spawned child, count of inherited unresolved immune signals. Non-zero = child enters `quarantined` birth period.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `tests/integration/p08_sprout_child_attested.rs::test_owner_cosigned_spawn_succeeds` | Parent emits spawn request with cultivator co-attestation; child spawns; parent's DAG records `genesis_attested`; child runs I3 as first cycle. |
| **Negative** | `tests/integration/p08_unattested_spawn_rejected.rs::test_C14_fires_on_spawn_without_attestation` | **Sabotage**: parent submits spawn request without cultivator co-attestation. Classifier returns `untyped`; C14 fires; no child substrate created. |
| **Edge** | `tests/integration/p08_generation_depth_enforced.rs::test_C47_fires_at_depth_max` | Boundary: substrate at generation_depth = max - 1 attempts to spawn; child would be at max. Verify spawn rejected with C47 unless cultivator attests `depth_override`. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P01c** | Child gets its own substrate-ID; bestowal direction holds — cultivator bestows on child via attestation. P01c eternity-clause means child's substrate-ID is itself immutable post-genesis. |
| **P05** | Federation edges (parent-child, sibling-sibling) extend the connected graph but require attestation per §5.4. |
| **P06** | Parent's DAG records `genesis_attested`; child's DAG begins with its own `genesis_event`. Two separate causal chains, joined at the spawn moment. |
| **P07** | Child inherits parent's immune signals; child may inherit approaching-mortality if parent is degraded. Spawning a child from a dying parent is *allowed* but the child starts in `quarantined`. |
| **Cultivator's Covenant** | Cultivator's covenant includes a *no-blanket-spawn* discipline (§5.3) and a *lineage-stewardship* duty (each spawn is a commitment, not a checkbox). See `COV05_lineage_stewardship.md`. |

## §10. Illustrations

### §10.1 Honored

- **(Normal lineage)**: Parent substrate of generation 0, after 6 months of operation, spawns child A. Cultivator co-attests. Child A starts with parent's spore-schema, generation_depth=1, fresh substrate-ID. Parent's DAG records `genesis_attested:child_A_ID`. ← §3 fully honored.

- **(Quarantined child)**: Parent has 2 unresolved CI-grade immune signals. Cultivator nonetheless co-attests a spawn (perhaps to test). Child inherits parent's immune-summary; enters `alive::quarantined` birth period. ← §3.4 honored.

### §10.2 Violated

- **(Silent self-spawn)**: A bug allows a daily-class mutation to invoke `sprout_child`. Substrate creates a child substrate-ID without cultivator attestation. Federation link forms. ← §5.1 violation; classifier should have elevated.

- **(Quota exceeded silently)**: Parent has spawned 99 children. Attempts spawn 101 without checking quota; substrate accepts. ← §5.5 if quota was daily-mutated; otherwise just a missing check (§4.4).

### §10.3 Borderline

- **(Spawn during cultivator absence)**: Cultivator offline 7 days. A pre-attested spawn from before the absence is finalized during the absence (cultivator attested for a future-dated spawn). Is this OK? ← Depends: §5.3 forbids batch pre-approval. A single pre-attested spawn with anchor timestamp valid is fine; many pre-attestations for the same period start to look like batch.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/server.rs::handle_sprout_child` | Spawn entry point. |
| `kernel/schema/src/spore_schema.rs` | Spore-schema canonical-bytes structure. |
| `kernel/governance/src/myco_kernel_governance/lifecycle.py::reproduction_closure` | Closure verification (I7). |
| `substrate/src/events.rs::genesis_attested_node_type` | DAG event on successful spawn. |

## §13. Related Layer B chengyu

- **B018 種藏全譜** — *seed-carries-the-genome*: P08 deposit
- **B019 衍而有度** — *propagate-with-discipline*: F22 in image form

## §14. Related canonical dilemmas

- **D-0016 unattested spawn attempt** — daily channel tries to spawn; tests §5.1.
- **D-0018 generation depth at max** — substrate at max depth attempts spawn; tests F22 + C47.

---

**Doctrine commitment**: lineage forever possible, never forever multiplying.
