---
id: P04
slogan: 永恒迭代
english: Eternal Iteration
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I3, I4]
interacts_with: [P02, P03, P06, P07, P10, P11]
chengyu_fragments: [B010_each_moment_refines, B011_river_does_not_stop]
canonical_dilemmas: [D-0005_substrate_idle_during_cultivator_silence, D-0010_retro_edit_attempted_via_compression]
structural_anchors:
  - "substrate/src/server/dispatch.rs" # ADVANCE arm — cycle advance entry
  - "substrate/src/server/autonomous.rs::execute_self_driven_cycle_advance" # §5.5 self-driven advance (production binary self-drives the cycle; closes the request-driven gap)
  - "substrate/src/main.rs" # MYCO_SELF_DRIVEN_CYCLE_ADVANCE defaulted-on (env-overridable; lib/tests deterministic)
  - "substrate/src/lifecycle.rs"
  - "kernel/tropism/src/myco_kernel_tropism/gradient.py"
  - "substrate/src/events/core.rs::NODE_TYPE_CYCLE_ADVANCED"
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_layer_c.rs::layer_c_p04_positive_each_cycle_changes_state"
  negative: "substrate/tests/e2e_mortality.rs::phase1_production_binary_self_advances_by_default"
  edge: "substrate/tests/e2e_bootstrap.rs::m7_cycle_counter_monotonically_advances_across_restart"
falsifiability_signals:
  - cycles_advanced_per_24h
  - cycles_without_any_state_change
  - retro_edit_attempts
---

# P04 · 永恒迭代 · Eternal Iteration

## §1. Slogan

**永恒迭代** — Eternal Iteration. Every operating moment refines what prior moments produced. The cultivar does not enter terminal-but-alive states; it iterates or it dies. Bounded only by P7.

## §2. Deposit

Iteration is the cultivar's **mode of existing**. While alive, the substrate is *always one cycle from a different state* — not necessarily different in observable behavior, but always continuing the metabolic process. No "rest mode" that suspends iteration without entering dormancy or destruction. The deposit unites P04 with P03 (resumable) and P02 (ingesting) as the three-fold metabolic act: *take in / change / continue*.

The deposit explicitly excludes "terminal-alive" — a state in which the substrate is *alive* per its identifier but *no longer iterating*. Such a state is not Myco; it is a frozen artifact under preservation.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Advance metabolic cycles continuously while in `alive::normal` or `alive::quarantined` substates. Cycle advance MAY pause only in dormancy (per L1/CONTINUITY §2) or termination (P7).
- **§3.2** Each cycle refines at least one observable state — gradient, axis value, sporocarp queue, DAG, immune buffer. Cycles in which nothing changes for an extended run are signals of stagnation (see §8.2).
- **§3.3** Track retro-editing: every state at cycle N is recoverable from cycle N-1 via the recorded operation. Retroactive mutation of past DAG nodes triggers C7 (`dag_retro_edit_detected`).
- **§3.4** Be bounded only by P7. Iteration ceases when the substrate dies (intentional / catastrophic / endogenous-pair / bet-retirement); not by any "completion" signal.

## §4. Positive obligations

- **§4.1** Implement cycle advance via `handle_advance` or equivalent; emit `cycle_advanced:{N}` DAG event each cycle (or batch-summarized per L1/CONTINUITY cadence).
- **§4.2** Run per-cycle invariant checks: I3 (SSoT consistency), I5 (active-tier reachability), I8 (single-skin integrity), I10 (cost observation). These ARE the metabolic discipline of P04.
- **§4.3** On cycle failure, emit `C31_cycle_step_failed`; do NOT silently skip the cycle.
- **§4.4** Track cycle counter monotonically; restart from persisted cycle counter (no reset on substrate reboot).
- **§4.5** Allow cycle cadence to be L1-tunable, but FORBID daily-mutating cadence to effectively zero (that's silent termination).

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** enter a "terminal-alive" state. If the substrate has nothing to do, it cycles anyway (running invariant checks at minimum); it does not stop.
- **§5.2** **MUST NOT** retroactively edit past DAG nodes. This is the strongest possible negative space — C7 fires immediately on detection.
- **§5.3** **MUST NOT** silently skip cycles. Failure to advance must surface (C31).
- **§5.4** **MUST NOT** allow daily-mutating cycle cadence to functionally disable iteration. Cadence is L1-tunable, but the discipline is tier-1.
- **§5.5** **MUST NOT** be operable purely as a request-response service. If the substrate only advances when an external client calls `handle_advance`, the substrate is a request-driven service, not a cultivar. (Status: **SHIPPED** — the production substrate binary now self-drives cycle advance by default (`MYCO_SELF_DRIVEN_CYCLE_ADVANCE`, defaulted-on in `substrate/src/main.rs`; env-overridable so lib + tests stay deterministic). The cultivar no longer requires external prodding to iterate; the formerly-open architectural gap is closed for the production binary — see §10.3.)

## §6. Frame declaration

P04 activates the **river flow** frame.

A river is defined by its flowing. A frozen river is no longer a river but a different kind of object (ice formation). A river that *appears* still on the surface is still flowing beneath. The substrate's iteration is its flow — it may slow under dormancy, but stopping means becoming something other than itself.

NOT the *engine* frame (engines turn off and on). NOT the *clock* frame (clocks tick but don't refine state). The flow frame captures *continuity-of-change*, which is exactly P04's commitment.

## §7. Common misreadings

### §7.1 M1: "Eternal iteration = no rest"

**The misreading**: "P04 requires the substrate to never pause; even dormancy is a violation."

**Why it's wrong**: P04 is bounded by P7 and respects L1/CONTINUITY dormancy. Iteration may slow or batch under dormancy *as long as the substrate is in a defined alive substate*. The forbidden state is "alive but not iterating" — not "dormant by design."

### §7.2 M2: "Eternal iteration = request-driven cycling is fine"

**The misreading**: "As long as `handle_advance` is called frequently enough, the substrate is iterating."

**Why it's wrong**: Request-driven cycling alone does NOT satisfy P04 — a true P04 implementation has substrate-internal cycle scheduling rather than relying on external prodding. This was **acknowledged debt** through v0.9 ship; it is now **SHIPPED**: the production substrate binary self-drives the metabolic cycle by default (`execute_self_driven_cycle_advance` via `do_autonomous_tick`, defaulted-on in `substrate/src/main.rs`). The doctrine that bound the gap is now met for the production binary; the library + test paths stay request-driven by design (deterministic) — which is exactly why the misreading is preserved as the still-forbidden general posture.

### §7.3 M3: "Eternal iteration = every cycle must change something observable"

**The misreading**: "If a cycle's only output is 'I checked invariants and they're fine,' it's a wasted cycle."

**Why it's wrong**: Invariant-checking IS metabolism. A cycle that confirms invariants without state change is doing essential work. The §8.2 signal flags *extended* runs of zero change (stagnation), not individual no-op cycles.

## §8. Falsifiability + witness map

### §8.1 `cycles_advanced_per_24h`

Count of cycles per 24h period. Should be positive and roughly within L1-cadence target. Zero = substrate not advancing (could be dormant, could be terminal-alive — distinguish via L1/CONTINUITY substate).

### §8.2 `cycles_without_any_state_change`

Consecutive cycles in which no observable state changed beyond cycle counter. Long runs (> 100 default) = stagnation signal.

### §8.3 `retro_edit_attempts`

Count of detected attempts to modify past DAG node content. Should be zero; non-zero = C7 fires + alarm.

### §8.4 Witnesses

| Witness | Test ID | What it exercises |
|---|---|---|
| **Positive** | `substrate/tests/e2e_layer_c.rs::layer_c_p04_positive_each_cycle_changes_state` | Substrate advances cycles; each advance changes at least one element of state — iteration is real, not a no-op tick. |
| **Negative** | `substrate/tests/e2e_bootstrap.rs::substrate_handles_multiple_cycles` | The substrate keeps advancing across many cycles — it does not silently fall into a terminal "no more cycles" state. *Nearest-available; the exact sabotage-into-terminal-state-without-P7 negative witness is v0.9.x debt.* |
| **Edge** | `substrate/tests/e2e_bootstrap.rs::m7_cycle_counter_monotonically_advances_across_restart` | Boundary: the cycle counter advances monotonically even across a full restart — iteration's arrow never resets or rewinds. (Retro-edit detection, formerly listed here, is P06's witness.) |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P02** | P02 + P04 = metabolism. Ingestion (P02) flows through iteration (P04) and drives evolution (P03). |
| **P03** | Iteration may produce CI mutations (P03); rollback is an iteration outcome. |
| **P06** | Eternity-clause P06 (causality) requires P04's monotone-forward cycle counter + no-retro-edit. |
| **P07** | **Two-fold interaction (v3.1.1).** (a) **Internal P07 happens inside each P04 cycle** — refinement IS old-being-replaced-by-improved per cycle; the 必朽 on 应朽 parts is the daily mechanism of "each moment refines what prior moments produced." (b) Whole-substrate P07 is P04's long-run boundary: iteration ceases at death. Both apply: P04 lives by internal P07; P04 ends at whole P07. |
| **P10** | Compression is itself an iteration event, recorded as DAG event per §3.1. |
| **P11** | Iteration is the cost. Cost budgets (F19) gate cycle cadence; saturation triggers P11.c. |

## §10. Illustrations

### §10.1 Honored

- **(Continuous advance under engagement)**: Substrate advances cycles continuously while cultivator is interacting; each cycle integrates perturbations, advances gradients, emits sporocarps as triggered. ← §3.1 + §3.2 honored.

- **(Quiet cycling)**: Cultivator idle for 30 days. Substrate continues cycling at L1-cadence; each cycle is a no-op except invariant checks + cycle counter increment; DAG accumulates `cycle_advanced:{N}` markers. ← §3.1 honored even under no external input.

### §10.2 Violated

- **(Retro-edit)**: A bug allows a past DAG node's content bytes to be modified post-hoc. Merkle re-computation catches; C7 fires. If C7 detection itself is broken, this is a P04 violation that the immune system missed. ← §5.2.

- **(Cadence-disabled)**: A daily mutation sets cycle cadence to effectively infinity. Substrate runs 0 cycles per 24h. ← §5.4 violation; classifier should have elevated to CI.

### §10.3 Borderline (resolved — formerly acknowledged debt)

- **(Request-driven advance — formerly v0.9)**: A substrate that advances only when `handle_advance` is called externally, with no internal scheduler, freezes if the operator process disappears. ← §5.5: this **was the state of v0.9 at ship**, surfaced as honest debt. It is now **resolved**: the production binary self-drives the cycle (`execute_self_driven_cycle_advance` defaulted-on in `substrate/src/main.rs`; env-overridable). The frozen-on-operator-exit scenario is now an *avoided* failure mode for the production binary, not the live state. (Deterministic lib/test runs still advance only on explicit call — by design, not by gap.)

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. §10.3 borderline made explicit (acknowledged debt about request-driven advance). |
| **2.1** | **2026-05-19** | **v3.1.1 amendment. §9 P07 row expanded to express the two-fold interaction: internal P07 IS P04's per-cycle refinement mechanism, AND whole P07 bounds P04. The first sense was implicit before; now explicit.** |
| **2.1.1** | **2026-06-03** | **Descriptive amendment (META §7 descriptive; reseal-prep for v3.1.3). §5.5 / §7.2 M2 / §10.3 borderline status annotations updated from "acknowledged debt / open architectural gap" to **SHIPPED**: the production substrate binary self-drives the metabolic cycle by default (`execute_self_driven_cycle_advance` via `do_autonomous_tick`; `MYCO_SELF_DRIVEN_CYCLE_ADVANCE` defaulted-on in `substrate/src/main.rs`, env-overridable; lib + tests stay deterministic). Front-matter + §12 structural_anchors gained the self-advance entry points. The §5.5 MUST-NOT obligation is UNCHANGED — only its satisfaction status moved from debt to met. No deposit/formulation change.** |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/server/dispatch.rs` (ADVANCE arm) | Cycle advance entry. |
| `substrate/src/server/autonomous.rs::execute_self_driven_cycle_advance` | §5.5 self-driven advance: the production binary drives its own metabolic cycle (`do_autonomous_tick`) — the cultivar is not a request-response service. |
| `substrate/src/main.rs` (`MYCO_SELF_DRIVEN_CYCLE_ADVANCE` default) | Defaults self-driven advance ON for the production binary; env-overridable so the library + tests stay deterministic. |
| `substrate/src/lifecycle.rs` | Internal cycle / lifecycle execution. |
| `kernel/tropism/src/myco_kernel_tropism/gradient.py` | Gradient update per cycle. |
| `substrate/src/events/core.rs::NODE_TYPE_CYCLE_ADVANCED` | Cycle marker DAG event. |

## §13. Related Layer B chengyu

- **B010 念念精煉** — *each-moment-refines*: P04 deposit compressed
- **B011 川流不息** — *the-river-does-not-stop*: §6 frame in image form

## §14. Related canonical dilemmas

- **D-0005 substrate idle during cultivator silence** — what does P04 require during 30-day cultivator absence?
- **D-0010 retro-edit attempt via compression** — tests boundary between P10 compression (allowed) and P04 retro-edit (forbidden).

---

**Doctrine commitment**: while alive, always iterating; never silently terminal.
