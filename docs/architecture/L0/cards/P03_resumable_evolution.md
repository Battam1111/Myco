---
id: P03
slogan: 可逆迭代
english: Resumable Evolution
category: Postulate
layer: Cultivar essence
status: Active
version: 3
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-19"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I3, I4]
interacts_with: [P02, P04, P06, P07, P10, P14, COV01]
chengyu_fragments: [B008_evolve_rollback_keep_self, B009_dead_if_static]
canonical_dilemmas: [D-0004_failed_evolution_rollback_atomicity, D-0008_lexicon_change_under_CI]
structural_anchors:
  - "kernel/governance/src/myco_kernel_governance/classifier.py"
  - "kernel/governance/src/myco_kernel_governance/schema_evolution.py::apply_schema_diff"
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
- **§3.3** On accepted CI mutation, persist via **snapshot-rollback semantics**: the substrate snapshots the pre-mutation gradient state, applies the diff atomically, validates I3 invariants; on I3 inconsistency or apply-time exception, restores the snapshot and emits `evolution_failed:{op}`. On success, emits `evolution_succeeded:{op}`. The pre-evolution DAG-tip is always recoverable from the causal chain (P06). **Multi-cycle two-phase migration** (candidate-alongside-current across M cycles with per-cycle dual-validation) is doctrine-described as an L4 enhancement target in §10.4 acknowledged debt — current shipping behavior is **single-cycle apply-with-rollback**, which honors the deposit (mutable schema + recoverable identity) but not the §4.3-claimed M-cycle window.
- **§3.4 (P3.b)** Lexicon evolution is CI-class; mycology-literature attestation required; deprecated terms marked `terminal` (never silently removed).
- **§3.5** Substrate-identity moves forward only: even after rollback, `substrate-ID` unchanged; cycle counter monotone-increasing; rollback recorded as DAG event (P06 causality preserved).

## §4. Positive obligations

- **§4.1** Provide CI submission path (`submit_mutation`) with classifier + attestation verification.
- **§4.2** On daily mutation acceptance, apply immediately; emit DAG event.
- **§4.3** On CI mutation acceptance, run **single-cycle snapshot-rollback** apply: snapshot gradient state → apply diff → validate I3 → on success commit, on failure restore. Two-phase migration with M-cycle dual-validation is the L4 target (see §10.4); current behavior delivers the deposit (mutable + recoverable) at the cost of one cycle of dual-validation rather than M.
- **§4.4** On evolution failure (I3 fails post-mutation): identify pre-evolution DAG-tip; restore SSoT designation + classifier table + affected canon; drop pending sporocarps in rolled-back window as `evolution_failed_pending_dropped`; emit `rollback_complete`.
- **§4.5** Track template-version evolution via `template_version_registry` (active-prefix + archived-tail).
- **§4.6** Persistent failure (≥3 consecutive within window) → quarantine per L1/CONTINUITY §5.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** treat substrate state as constitutionally frozen. "We can't change X" without explicit eternity-clause status is a doctrine violation — it leaks adopt-don't-evolve into the substrate.
- **§5.2** **MUST NOT** apply schema mutations OUTSIDE the snapshot-rollback envelope. Direct SSoT mutation that skips the classifier + attestation + snapshot path triggers C8. (When §10.4's M-cycle migration ships, this clause re-tightens to require the M-cycle window; current shipping requirement is the snapshot-rollback envelope.)
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

**Why it's wrong**: P03's spirit is **dual-validation across time** — the candidate state must survive operational testing, not just a one-shot atomic commit. The current shipping implementation (single-cycle snapshot-rollback) approximates this with a one-cycle window: snapshot → apply → I3 validate → commit-or-restore. The L4 enhancement target (§10.4) extends this to M-cycle dual-validation where the candidate runs alongside the current state across many cycles, accumulating evidence before commit. Both forms reject the pure-transaction reading: in P03, the test of a mutation is its **continued operational success**, not just its successful application.

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
| **P07** | **P03 evolution requires P07's permission to delete.** Old forms must die for new forms to take their place — evolution **IS** old-being-replaced-by-new. Without P07's 必朽 discipline on 应朽 parts, P03 cannot occur: accumulated past blocks future possibilities. P07 is structurally upstream of P03's mechanism. |
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

### §10.4 Acknowledged debt — multi-cycle two-phase migration

**Current shipping** (v3.1.1, post-Sprint 6.D 2026-05-19):
single-cycle snapshot-rollback. `kernel/governance/.../schema_evolution.py::apply_schema_diff`
snapshots the gradient state, applies the diff, validates I3, and on
failure restores the snapshot atomically. This delivers P03's **deposit**
(mutable schema + recoverable identity + DAG-recorded failure) within one
metabolic cycle.

**Target enhancement** (L4/M-future, estimated 16-24h):
multi-cycle two-phase migration. The candidate state runs alongside the
current state for M consecutive cycles (default 100, L4-tunable); both
states process the same inputs; per-cycle dual-validation compares
outputs; commit happens only on M consecutive matches. The substantive
defense gain: I3 drift that takes >1 cycle to surface (e.g., interaction
with other axes manifesting after several cycles of operation) is caught
in dual-validation rather than after commit.

**Migration path**: requires
  1. `kernel/schema/src/migration.rs` (currently absent) introducing
     `two_phase_commit` types: `CandidateState`, `DualValidationCycle`,
     `CommitDecision`.
  2. Substrate-side bookkeeping for "active gradient" + "candidate
     gradient" + cycle-counter for M-window tracking.
  3. Classifier `cost_budget_set` / `add_axis_to_gradient` mutations
     extended to enter migration mode rather than apply directly.
  4. Operator-visible "migration_pending" surface so cultivator can
     observe / abort in-flight migrations.
  5. New C-row detector (C64 anticipated): migration window exceeded
     without commit (signals candidate diverging permanently).

This debt is **descriptive** — the current implementation does not
violate the deposit (which is `first-class mutable + rollback-protected`),
it implements a smaller-window approximation. Implementing §10.4 would
strengthen the dual-validation defense without changing the deposit's
shape.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 with P3.b joint-context evolution sub-clause. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema with Deposit/Formulation split. |
| 2.1 | 2026-05-19 | v3.1.1 amendment. Added P02 + P07 to interacts_with + §9 interaction row for P07 (evolution requires permission to delete; P07 upstream of P03 mechanism). No deposit change. |
| **3** | **2026-05-19** (Sprint 6.D) | **Descriptive amendment: §3.3 + §4.3 + §5.2 + §7.1 reframed from "two-phase migration with M-cycle dual-validation" to actual shipping behavior (single-cycle snapshot-rollback). Two-phase migration named explicitly as L4 enhancement target in new §10.4 acknowledged debt section with full migration path. Phantom structural anchor `kernel/schema/src/migration.rs::two_phase_commit` replaced by actual `kernel/governance/.../schema_evolution.py::apply_schema_diff`. Deposit (§2) UNCHANGED — `first-class mutable + rollback-protected` is honored by both the current snapshot-rollback and the planned M-cycle migration. Sprint 5.B identified the drift; Sprint 6.D resolves it by aligning doctrine with shipped code while naming the gap that future cultivator work can close.** |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `kernel/governance/src/myco_kernel_governance/classifier.py` | I2 classifier gating P03 mutations. |
| `kernel/governance/src/myco_kernel_governance/schema_evolution.py::apply_schema_diff` | Snapshot-rollback semantics (single-cycle apply-with-restore). Sprint 6.D pinned this as the shipping mechanism; replaces the prior phantom anchor `kernel/schema/src/migration.rs::two_phase_commit` which was doctrine-aspirational but never landed. The M-cycle two-phase migration is §10.4 acknowledged debt. |
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
