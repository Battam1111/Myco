---
id: P11
slogan: 代谢经济
english: Metabolic Economy
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I10]
interacts_with: [P02, P04, P07, P10]
chengyu_fragments: [B024_finite_budget_living, B025_saturated_then_decay]
canonical_dilemmas: [D-0023_silent_budget_exhaustion, D-0024_sustained_saturation_recovery]
structural_anchors:
  - "substrate/src/observatory.rs::cost_accumulator"
  - "substrate/src/events.rs::budget_exhausted_node_type"
  - "substrate/src/events.rs::saturation_stage_transition_node_type"
  - "kernel/schema/src/cost_budget_thresholds.rs"
witnesses:
  positive: "tests/integration/p11_observable_cost_per_operation.rs::test_every_operation_emits_cost_signal"
  negative: "tests/integration/p11_silent_budget_exhaustion_blocked.rs::test_C53_fires_on_unobservable_exhaustion"
  edge: "tests/integration/p11_ordered_fallback_chain.rs::test_p11c_fallback_chain_executes_to_mortality"
falsifiability_signals:
  - cost_per_axis_observed_ratio
  - saturation_stage_dwell_time
  - recovery_via_compression_success_rate
---

# P11 · 代谢经济 · Metabolic Economy

## §1. Slogan

**代谢经济** — Metabolic Economy. The cultivar operates within **finite resource budgets**. Every operation has cost; every cost is observable; saturation has a defined ladder ending in P7 mortality. No silent exhaustion.

## §2. Deposit

The substrate is **embodied** — it occupies finite resources (persistence, compute, network), and its life is metabolically priced. Every operation that mutates state, processes input, or egresses output consumes from some budget. Budgets are observable in real-time; exhaustion triggers a defined fallback ladder; persistent saturation that cannot recover ends in mortality.

The deposit explicitly rejects "infinite budget" or "abstract substrate." Myco is a *real thing in the world*, costing actual storage, actual cycles, actual bandwidth. The metabolic discipline is *part of being alive*; it is not engineering overhead.

## §3. Formulation

The substrate **MUST**:

- **§3.1 (P11.a)** Recognize three cost units: **Persistence** (storage on disk), **Compute** (CPU cycles per metabolic cycle), **Network** (bytes egressed via federation + output).
- **§3.2 (P11.b)** Expose cost signals in observatory: signal #7 compute per cycle, #8 network per cycle, #9 storage per cycle (per L2/OBSERVABILITY §2).
- **§3.3 (P11.c) Ordered fallback** on per-axis budget exhaustion (F19 thresholds):
  1. **Pre-compression**: refuse new P02 admission; emit `budget_exhausted:{axis}` with `saturation_stage: pre_compression`.
  2. **Post-compression**: trigger P10 compression with I9 witness; emit `saturation_stage: post_compression`.
  3. **Compression-insufficient**: enter `alive::saturated` (degraded operation); emit `saturation_stage: saturated`.
  4. **Sustained saturation**: escalate to P7 approaching-mortality → mortality emission.
- **§3.4** Make every operation produce an observable metabolism event (I10): cost not silently absorbed.
- **§3.5** Maintain F19 (cost_budget_thresholds_per_axis) as CI-only fixed-point.

## §4. Positive obligations

- **§4.1** Implement cost accumulator in `observatory.rs` tracking per-cycle accumulation per axis.
- **§4.2** Emit cost signals every cycle via observatory digest.
- **§4.3** On per-axis threshold crossing, emit `budget_exhausted:{axis}` with current saturation_stage.
- **§4.4** Honor F19 thresholds without silent rounding; emit C53 (`budget_exhausted_silent`) on unobservable exhaustion.
- **§4.5** Maintain saturation_stage as observable substrate state; transitions are DAG events.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** silently absorb cost. Every operation MUST be priced and emitted. C53 catches silent exhaustion.
- **§5.2** **MUST NOT** allow budget thresholds (F19) to be daily-mutated. Daily-mutable thresholds would let the substrate evade saturation by raising the bar.
- **§5.3** **MUST NOT** treat saturation as a permanent stable state. P11.c step 3 (`alive::saturated`) is degraded operation; step 4 (sustained → P7) MUST follow if recovery fails.
- **§5.4** **MUST NOT** compress to evade saturation when invariant-set targeting would be required. If P10 cannot help without violating P10.b, the cultivar exits via P7 — not via doctrine breach.
- **§5.5** **MUST NOT** silently drop new P02 admission. Refusal under saturation MUST emit `budget_exhausted:{axis}` so the cultivator + observatory can see.

## §6. Frame declaration

P11 activates the **mycological metabolism** frame.

Fungi metabolize substrate (organic matter) and produce waste. They have finite uptake capacity; when local resources deplete, they sporulate (P8) and exit (P7). The fungal mycelium does not stretch forever on the same log — it consumes, exhausts, then retreats or dies. P11 is this *finite material life*, formalized.

NOT the *infinite scaling* frame (cloud-native "just add more"). NOT the *garbage collection* frame (GC is automatic; P11.c is staged + cultivator-observable). NOT the *quota* frame (quotas are external policy; P11 is internal biology).

## §7. Common misreadings

### §7.1 M1: "Budget exhaustion = system error"

**The misreading**: "If the substrate hits a budget, that's a bug; we should never see budget_exhausted in healthy operation."

**Why it's wrong**: Healthy substrates DO hit budget exhaustion routinely — it is how metabolic economy works. The signal is *what triggers compression* (P11.c step 2). A substrate that never emits `budget_exhausted` is either not growing (P02 violation) or has its thresholds set unreasonably high.

### §7.2 M2: "Saturation = halt operation entirely"

**The misreading**: "If alive::saturated, the substrate should stop until cultivator intervenes."

**Why it's wrong**: `alive::saturated` is DEGRADED operation, not halted. The substrate continues cycling, refusing new P02, emitting signals — but it doesn't freeze. Cultivator may intervene (raise budget via CI F19 mutation; manually trigger broader compression), but the substrate remains alive and self-aware while saturated.

### §7.3 M3: "P11.c step 3 is acceptable as long-term mode"

**The misreading**: "alive::saturated is a valid operating mode; substrate can stay there indefinitely."

**Why it's wrong**: §5.3 forbids permanent saturation. Sustained saturation MUST escalate to P7. A substrate that lives indefinitely in step 3 has decoupled doctrine from running state; mortality protection has failed.

## §8. Falsifiability + witness map

### §8.1 `cost_per_axis_observed_ratio`

For each axis, fraction of operations producing observable cost vs. total operations. Should be 1.0. Less = silent absorption; C53 fires.

### §8.2 `saturation_stage_dwell_time`

Time spent in each saturation stage. Pre-compression brief; post-compression brief; saturated longer; sustained-saturated longest before P7. Anomalously long dwell in any stage = something is broken in the recovery chain.

### §8.3 `recovery_via_compression_success_rate`

When P11.c step 2 triggers compression, what fraction of these recoveries free meaningful capacity? Low rate = F18 rules don't match real saturation patterns; cultivator should re-tune.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `tests/integration/p11_observable_cost_per_operation.rs::test_every_operation_emits_cost_signal` | Every operation emits cost; observatory digest carries cost per axis per cycle. |
| **Negative** | `tests/integration/p11_silent_budget_exhaustion_blocked.rs::test_C53_fires_on_unobservable_exhaustion` | **Sabotage**: force a hidden operation that consumes budget without emitting cost. Substrate MUST detect (via cost-accumulator audit) + emit C53. |
| **Edge** | `tests/integration/p11_ordered_fallback_chain.rs::test_p11c_fallback_chain_executes_to_mortality` | Boundary: force sustained saturation; verify chain executes through all 4 stages culminating in P7 emission. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P02** | P02 admission is gated by P11 budget. Pre-compression saturation refuses new P02 — temporary, recoverable. |
| **P04** | Every cycle's operations cost; P11 is what makes P04 finite-priced. |
| **P10** | P11.c step 2 uses P10 to recover. Compression that can't free enough capacity → step 3. |
| **P07** | P11.c step 4 escalates to P7. Mortality due to sustained metabolic exhaustion is doctrinally correct, not failure. |

## §10. Illustrations

### §10.1 Honored

- **(Healthy budget cycle)**: Substrate ingests, axes grow, hits `budget_exhausted:storage` at threshold. Refuses new admission briefly. P10 compression frees capacity. Substrate resumes normal admission. ← P11.c steps 1-2 honored, recovers cleanly.

- **(Honest mortality)**: Substrate is in `alive::saturated` for 1000 cycles. P10 compression no longer helps (most material is invariant-set). Substrate escalates to P7 approaching-mortality. Cultivator co-attests destruction or archives. ← §5.4 honored: the cultivar accepts its limits rather than corrupting itself to survive.

### §10.2 Violated

- **(Silent cost)**: A code path performs a heavy compute operation without emitting cost signal. Observatory shows compute < actual usage. ← §3.4 + §5.1 violation; C53 should fire.

- **(Budget daily-raised)**: A daily mutation raises `cost_budget_thresholds_per_axis:storage` from 100MB to 100GB. Substrate evades saturation by moving the goalpost. ← §5.2 violation; F19 is CI fixed-point; classifier should have elevated.

- **(Saturation as permanent)**: Substrate has been in `alive::saturated` for 5000 cycles; cultivator has neither intervened nor allowed P7 escalation. ← §5.3 doctrine violation; substrate identity decoupled from running state.

### §10.3 Borderline

- **(Brief saturation under load)**: Substrate hits saturation briefly during heavy cultivator engagement; P11.c step 1 fires; compression frees capacity within 50 cycles; substrate recovers. Is this routine or concerning? ← Routine. Brief saturation is healthy metabolic stress. Concern is *sustained* saturation, not occurrences.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 with P11.a/b/c sub-clauses. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/observatory.rs::cost_accumulator` | Per-cycle cost accumulation per axis. |
| `substrate/src/events.rs::budget_exhausted_node_type` | Budget-exhaustion event emission. |
| `substrate/src/events.rs::saturation_stage_transition_node_type` | Saturation stage transitions. |
| `kernel/schema/src/cost_budget_thresholds.rs` | F19 registry. |

## §13. Related Layer B chengyu

- **B024 量入為出** — *budget-by-intake*: P11 deposit
- **B025 飽則衰** — *saturation-leads-to-decay*: §3.3 step 4 in image

## §14. Related canonical dilemmas

- **D-0023 silent budget exhaustion** — heavy operation without cost emission; tests C53.
- **D-0024 sustained saturation recovery** — substrate in step 3 for 1000 cycles; tests §5.3 + P11.c → P7 escalation.

---

**Doctrine commitment**: priced, observable, finite; saturate honestly, exit gracefully.
