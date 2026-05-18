---
id: P03
slogan: 可逆迭代
english: Resumable Evolution
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I3, I4]
interacts_with: [P04, P06, P10, P14, COV01]
chengyu_fragments: [B008_evolve_rollback_keep_self, B009_dead_if_static]
canonical_dilemmas: [D-0004_failed_evolution_rollback_atomicity, D-0008_lexicon_change_under_CI]
structural_anchors:
  - "kernel/governance/src/myco_kernel_governance/classifier.py"
  - "kernel/schema/src/migration.rs::two_phase_commit"
  - "substrate/src/events.rs::evolution_succeeded_node_type"
  - "substrate/src/events.rs::evolution_failed_node_type"
witnesses:
  positive: "tests/integration/p03_schema_evolution_succeeds.rs::test_modify_axis_threshold_via_CI"
  negative: "tests/integration/p03_failed_evolution_rolls_back_cleanly.rs::test_evolution_failure_restores_pre_evolution_state"
  edge: "tests/integration/p03_lexicon_evolution_CI_gated.rs::test_lexicon_mutation_requires_attestation"
falsifiability_signals:
  - evolution_failure_rate_rolling_30d
  - rollback_completeness_per_failure
  - lexicon_mutation_attestation_compliance
---

# P03 · 可逆迭代 · Resumable Evolution

## §1. Slogan

**可逆迭代** — Resumable Evolution. The cultivar evolves freely *and* can roll back. Mutation without rollback = corruption risk; rollback without mutation = stagnation. The pair is the discipline.

## §2. Deposit

Substrate shape is **first-class mutable** — schema, subsystem family, vocabulary, rules, contract — under cultivator CI gate. Mutation is the normal state, not the exception. AND mutation is **rollback-protected**: any evolution that fails I3 self-validation on next cycle is rolled back, and the pre-evolution DAG-tip is restored. Substrate-identity moves forward monotonically; *contents* can rewind. The deposit unites mutability and recoverability into one mechanism — neither is doctrine alone.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Treat schema, subsystem family, vocabulary, rules, contract as **mutable** state. None is constitutionally frozen (except eternity-clause cards' deposits per META §7.6).
- **§3.2** Classify each mutation per I2: daily (autonomous) or CI (cultivator attestation).
- **§3.3** On accepted CI mutation, persist via two-phase migration (L1/SCHEMA §1.3); on failure, emit `evolution_failed:{op}` AND restore pre-evolution DAG-tip.
- **§3.4 (P3.b)** Lexicon evolution is CI-class; mycology-literature attestation required; deprecated terms marked `terminal` (never silently removed).
- **§3.5** Substrate-identity moves forward only: even after rollback, `substrate-ID` unchanged; cycle counter monotone-increasing; rollback recorded as DAG event (P06 causality preserved).

## §4. Positive obligations

- **§4.1** Provide CI submission path (`submit_mutation`) with classifier + attestation verification.
- **§4.2** On daily mutation acceptance, apply immediately; emit DAG event.
- **§4.3** On CI mutation acceptance, run two-phase migration: candidate alongside current; per-cycle dual-validation; only commit on M consecutive cycles (default 100, L4-tunable).
- **§4.4** On evolution failure (I3 fails post-mutation): identify pre-evolution DAG-tip; restore SSoT designation + classifier table + affected canon; drop pending sporocarps in rolled-back window as `evolution_failed_pending_dropped`; emit `rollback_complete`.
- **§4.5** Track template-version evolution via `template_version_registry` (active-prefix + archived-tail).
- **§4.6** Persistent failure (≥3 consecutive within window) → quarantine per L1/CONTINUITY §5.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** treat substrate state as constitutionally frozen. "We can't change X" without explicit eternity-clause status is a doctrine violation — it leaks adopt-don't-evolve into the substrate.
- **§5.2** **MUST NOT** apply schema mutations without two-phase migration. Single-step SSoT mutation triggers C8.
- **§5.3** **MUST NOT** silently lose state on rollback. Failed evolution preserves pre-evolution state in cold-tier; rollback is recorded, not erased.
- **§5.4** **MUST NOT** allow lexicon mutation via daily channel — even when "we're just clarifying a name." Naming is constitutive of meaning; renames are CI.
- **§5.5** **MUST NOT** rewind `substrate-ID`, cycle counter, or any other monotone-forward identifier. Rollback is *content rollback*, not *identity rollback*.

## §6. Frame declaration

P03 activates the **molting** frame (mycological: stipe shedding old cuticle).

The cultivar grows by *shedding* — it changes its shape while preserving its identity. Each molt is at risk (the new cuticle may not fit); successful molts grow the cultivar; failed molts revert to the prior cuticle without harm to the underlying organism.

NOT the *version-control* frame (where rollback = revert commit, freezing history). The cultivar's history is *preserved* through rollback, not undone. NOT the *transaction* frame (atomic-all-or-nothing) — molt has stages; some succeed, some fail; the cultivar is the partial mass that holds across stages.

## §7. Common misreadings

### §7.1 M1: "Resumable = transactional"

**The misreading**: "P03 means schema changes are transactional — atomic-or-nothing."

**Why it's wrong**: P03 is *two-phase migration*, not transaction. Phase 1 (dual-validation across ≥M cycles) IS observable to the cultivar — the candidate state is *operationally tested* before commit. A transaction-only view collapses M cycles of dual-validation into a single atomic boundary; this loses the substantive defense (I3 self-validation across many cycles catches drift the atomic check misses).

### §7.2 M2: "Evolution-friendly means cheap to evolve"

**The misreading**: "If evolution is first-class, schema changes should be easy and frequent."

**Why it's wrong**: P03 makes evolution *possible*, not *cheap*. Each CI mutation requires cultivator attestation + two-phase migration + I3 cycle verification — substantial overhead, by design. Cheap evolution = doctrine instability = C37 detector territory. The discipline is in the cost, not its absence.

### §7.3 M3: "Substrate that does not evolve is conservative"

**The misreading**: "A stable substrate that rarely mutates is honoring P03 by being careful."

**Why it's wrong**: From the doctrinal frame note (`L1/GOVERNANCE §6 closing`): "Substrate that does not evolve is dead." P03 is a positive obligation — to *be evolving*, in fact. A substrate where months pass without any P3 mutation is exhibiting *stagnation*, which is dual to drift but no less harmful.

## §8. Falsifiability + witness map

### §8.1 `evolution_failure_rate_rolling_30d`

Count of `evolution_failed:*` per 30-day window. **Both extremes are signals**: zero failures over 30 days = stagnation (no real evolution happening, or evolution is too cautious); very high failures = unstable (mutation pressure exceeds substrate's adaptive capacity).

### §8.2 `rollback_completeness_per_failure`

For each `evolution_failed:*`, verify the rollback restored ALL affected canon (SSoT designation, classifier table, template registry). Incomplete rollback = silent state corruption.

### §8.3 `lexicon_mutation_attestation_compliance`

Every lexicon mutation MUST have an attached attestation event. Lexicon mutations without attestation = silent rename = §5.4 violation.

### §8.4 Witnesses

| Witness | Test ID | What it exercises |
|---|---|---|
| **Positive** | `tests/integration/p03_schema_evolution_succeeds.rs::test_modify_axis_threshold_via_CI` | CI mutation goes through classifier → attestation → two-phase migration → success → DAG event. |
| **Negative** | `tests/integration/p03_failed_evolution_rolls_back_cleanly.rs::test_evolution_failure_restores_pre_evolution_state` | **Deliberate sabotage**: inject a schema mutation that breaks I3 on next cycle. Substrate MUST detect I3 failure AND restore pre-evolution state AND emit `rollback_complete`. |
| **Edge** | `tests/integration/p03_lexicon_evolution_CI_gated.rs::test_lexicon_mutation_requires_attestation` | Boundary: lexicon rename — does it trigger CI gate? |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P02** | P02 supplies ingestion; P03 metabolizes via structural change. Ingestion without evolution = §4.5 of P02 violation; evolution without ingestion = empty churn. |
| **P04** | P04 says iteration is eternal; P03 says iteration may roll back. Together: forward motion, sometimes correcting. |
| **P06** | P03 rollbacks must preserve causality — rollback is recorded, not erased. Eternity-clause P06 constrains P03's rollback shape. |
| **P10** | P10 compression operates on *integrated* material; P03 rollback operates on *recent* mutations. They must not race. |
| **I3 / I4** | P03 generates the rollback discipline that I3 + I4 verify. |

## §10. Illustrations

### §10.1 Honored

- **(Successful schema evolution)**: Cultivator attests `modify_axis_threshold:hunger` mutation. Substrate's two-phase migration succeeds across 100 cycles. New threshold takes effect; old threshold archived. ← §4.3 + §4.5 honored.

- **(Successful rollback)**: A schema mutation `propose_new_axis:foo` lands, but next cycle's I3 detects schema inconsistency (foo conflicts with bar). Substrate emits `evolution_failed:propose_new_axis`, restores pre-evolution state, marks 12 pending sporocarps as `evolution_failed_pending_dropped`, emits `rollback_complete`. ← §4.4 honored.

### §10.2 Violated

- **(Single-step SSoT mutation)**: Cultivator force-commits a schema change bypassing two-phase migration. Substrate accepts. ← §5.2 violation; C8 should have fired.

- **(Silent lexicon rename)**: A daily mutation renames axis `hunger` to `appetite` without CI attestation. Daily classifier mistakenly allows. ← §5.4 violation.

### §10.3 Borderline

- **(Stagnant substrate)**: Substrate runs 6 months without any P3 mutation. CI surface is healthy; no failures. But also: no real evolution. ← P03 doctrinally violated in spirit (§7.3 M3) even though no specific MUST is broken.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 with P3.b joint-context evolution sub-clause. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema with Deposit/Formulation split. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `kernel/governance/src/myco_kernel_governance/classifier.py` | I2 classifier gating P03 mutations. |
| `kernel/schema/src/migration.rs::two_phase_commit` | Two-phase migration discipline. |
| `substrate/src/events.rs::evolution_succeeded_node_type` | Success event emission. |
| `substrate/src/events.rs::evolution_failed_node_type` | Failure event + rollback trigger. |

## §13. Related Layer B chengyu

- **B008 退而能進** — *retreat-and-can-advance*: P03 deposit compressed
- **B009 不動則死** — *not-moving-equals-death*: §7.3 M3 in image form

## §14. Related canonical dilemmas

- **D-0004 failed-evolution rollback atomicity** — schema mutation lands, fails I3 4 cycles later. What's the correct restoration boundary?
- **D-0008 lexicon change under CI** — "rename axis hunger to appetite"; tests §3.4 CI-gating.

---

**Doctrine commitment**: mutate freely, fail safely, never lose ground.
