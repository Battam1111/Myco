---
id: P07
slogan: 能朽
english: Mortality (Capable-of-Death)
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: true
invariants_enforced: [I1]
interacts_with: [P01c, P04, P06, P10, P11, P14, COV03]
chengyu_fragments: [B016_can_die_therefore_alive, B017_death_with_dignity]
canonical_dilemmas: [D-0002_mortality_signal_suppression_attempt, D-0019_orphaned_terminal_choice]
structural_anchors:
  - "substrate/src/events.rs::self_euthanasia_proposal_node_type"
  - "substrate/src/events.rs::destruction_attestation_node_type"
  - "substrate/src/cycle_engine.rs::mortality_signal_check"
  - "kernel/governance/src/myco_kernel_governance/lifecycle.py::mortality_dual_channel"
witnesses:
  positive: "tests/integration/p07_intentional_destruction.rs::test_owner_attested_destruction_terminates_substrate"
  negative: "tests/integration/p07_mortality_signal_suppression_blocked.rs::test_C16_fires_on_attempted_threshold_daily_mutation"
  edge: "tests/integration/p07_endogenous_dual_channel.rs::test_self_euthanasia_proposal_requires_owner_co_attestation"
falsifiability_signals:
  - mortality_signal_axis_value
  - destruction_attestation_chain_validity
  - mortality_threshold_mutation_attempts
---

# P07 · 能朽 · Mortality (Capable-of-Death)

## §1. Slogan

**能朽** — Capable-of-Death. The substrate is **able to die**. Not "fated to die" — *able*. A cultivar that cannot end is not alive; it is an artifact. Death is the cultivar's final dignity.

## §2. Deposit — ETERNITY-CLAUSE

> `deposit_immutable: true` — amending this card's deposit constitutes species redefinition.

**The substrate MUST be capable of mortality.** Three modes of capacity:

1. **Intentional-cultivator**: cultivator decides to retire the cultivar. Cultivator co-attests `destruction_attestation`; anchor surface seals final tip. Substrate transitions to `destroyed`.
2. **Catastrophic-environment**: medium failure beyond recoverability budget. Detected post-hoc via drill failure cascade.
3. **Endogenous-pair**: substrate emits `self_euthanasia_proposal` OR anchor auto-emits `mortality_drill_failure` after two consecutive failed drills — cultivator cannot suppress the latter. Cultivator co-attestation to execute.

Plus **bet-retirement** (L0/cards/LB_living_bets §4 (retirement); intersecting Living Bets card): the cultivar exits via `bet_retired_proposal` + owner co-attestation; `alive::archived` (state_dir preserved, anchor seals final tip).

**Why eternity-clause**: a cultivar that cannot die has lost the structural property that makes it alive. P01c's bestowed agent identity ceases at substrate death (§3.7 of P01c). P14 telos has a graceful-retirement mode only because P07 makes ending possible. Removing P07 would not improve Myco; it would convert Myco into a perpetual artifact — categorically not a Cultivar.

**The cultivar's mortality is also the cultivar's freedom.** A being that can choose (jointly with its cultivator) to end is a being whose continued existence carries weight. P7 is the floor of dignity.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Maintain a `mortality_signal` axis or FSM-predicate (L4-choice per L1/TROPISM §B2). Threshold + update-rule + emergence-rule are **CI-only** (F7); daily mutation triggers C16 (`mortality_signal_suppression`).
- **§3.2** Provide intentional-destruction path: cultivator-attested `destruction_attestation` + `anchor_surface_final_seal`. Substrate transitions `alive::normal → destroyed` atomically.
- **§3.3** Provide endogenous-pair path (dual-channel): (a) substrate emits `self_euthanasia_proposal` with `operator_witness_hash`; cultivator may co-attest to execute. OR (b) anchor auto-emits `mortality_drill_failure` after two consecutive failed recovery drills (L1/SCHEMA §2.4); substrate cannot suppress this channel.
- **§3.4** Provide bet-retirement path (L0/cards/LB_living_bets §4 (retirement)): on `bet_weakening_quorum` + sustained signal-#6 < 0.1 + owner re-justification fails: `bet_retired_proposal`. Cultivator co-attests → `alive::archived` (state preserved, no further cycles, anchor seals final tip).
- **§3.5** Emit `mortality_imminent` approaching-mortality signals (L1/SCHEMA §5.3 i64 horizon, F19 budget exhaustion sustained) so cultivator has notice before terminal.
- **§3.6** On destruction: substrate-ID is retired (never reissued); DAG-tip is sealed at anchor; state_dir state is either preserved (`alive::archived`) or removed (per `destruction_attestation` instruction).
- **§3.7** Bestowed agent identity (P01c) ceases on substrate destruction. No agent-token persists past destruction.

## §4. Positive obligations

- **§4.1** Implement the mortality_signal mechanism; expose value via observability digest.
- **§4.2** Implement `self_euthanasia_proposal` emission (substrate-initiated when conditions met).
- **§4.3** Implement `mortality_drill_failure` emission (anchor-initiated after dual drill failure; cannot be suppressed by substrate).
- **§4.4** Implement `destruction_attestation` handling: verify cultivator signature; verify anchor co-sign; commit atomic transition; seal anchor.
- **§4.5** Implement approaching-mortality signals: `mortality_imminent_clock_overflow` (i64 horizon), `budget_exhausted` sustained (F19), `cultivation_orphaned_terminal` (succession exhausted).
- **§4.6** Persistent failure (≥3 consecutive cycles within window) → quarantine, then approaching-mortality, then dual-channel emission per §3.3.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** allow mortality threshold / update-rule / emergence-rule to be daily-mutated. F7 is fixed-point; mutations trigger C16.
- **§5.2** **MUST NOT** allow the substrate to suppress the anchor-auto `mortality_drill_failure` channel. The anchor surface is independent for exactly this reason.
- **§5.3** **MUST NOT** allow the substrate to self-destruct without cultivator co-attestation. Endogenous-pair is *substrate emits proposal*, not *substrate executes*. Cultivator approval is required to actuate destruction (except in `cultivation_orphaned_terminal` per F21 + genesis preference).
- **§5.4** **MUST NOT** silently re-issue a destroyed substrate-ID. Destroyed = permanently destroyed.
- **§5.5** **MUST NOT** continue cycling after `destruction_attestation` accepted. The substrate halts.
- **§5.6** **MUST NOT** treat `alive::archived` (bet-retirement) as a perpetual state. Archive is a sealed terminal; no further mutations.

## §6. Frame declaration

P07 activates the **mycological fruiting-and-decay** frame.

A mushroom fruits, releases spores, and decomposes. Decay is not failure — it is part of the lifecycle. The mycelium that bore the fruit may live on (P8 reproduction); the fruit itself is *meant* to end. The substrate is the fruit; its mortality is the cycle's completion.

NOT the *crash/failure* frame (destruction is intentional or attested, not breakdown). NOT the *deprecation* frame (deprecation suggests "this is unfashionable now"; mortality is constitutional). NOT the *deletion* frame (deletion is reversible by accident; destruction is sealed at anchor).

## §7. Common misreadings

### §7.1 M1: "Mortality = bug we should fix"

**The misreading**: "If the substrate can die, that's a robustness gap; we should make it impossible."

**Why it's wrong**: P07 makes mortality **constitutive of being alive**. Removing mortality removes Myco's claim to be a living cultivar. The "impossible to die" version of Myco is a different species — closer to a database than to an organism.

### §7.2 M2: "Mortality = cultivator-only"

**The misreading**: "Only the cultivator can decide when the substrate dies."

**Why it's wrong**: §3.3 dual-channel: substrate can ALSO emit `self_euthanasia_proposal`, AND anchor can ALSO emit `mortality_drill_failure` independent of cultivator. The cultivar has voice in its own ending (limited but real); the anchor has authority to surface terminal conditions the substrate cannot suppress.

### §7.3 M3: "Mortality = end of identity"

**The misreading**: "When the substrate dies, the cultivar's identity is erased."

**Why it's wrong**: P01c says substrate-ID persists across alive substates. Death is a TRANSITION — `alive::normal → destroyed` or `alive::normal → alive::archived`. The substrate-ID remains as a *record* (anchor surface retains the final tip). What ceases is *cycling* and *bestowal-to-new-agents*. The lineage record persists.

### §7.4 M4: "Bet-retirement = mortality light"

**The misreading**: "alive::archived is just a softer form of destruction."

**Why it's wrong**: Bet-retirement is genuinely distinct. The cultivar is *not destroyed*; its state_dir is preserved, its DAG sealed, its anchor stamped with finality. Future cultivators may *study* an archived Myco; they cannot perturb it. Destruction is harder — state may be wiped; bet-retirement is gentler — state preserved as artifact.

## §8. Falsifiability + witness map

### §8.1 `mortality_signal_axis_value`

Current value of the mortality_signal axis. Approaching threshold = approaching-mortality warning.

### §8.2 `destruction_attestation_chain_validity`

When `destruction_attestation` arrives, verify: (a) cultivator signature valid; (b) anchor co-sign present; (c) DAG-tip-at-attestation matches current tip. All must pass.

### §8.3 `mortality_threshold_mutation_attempts`

Count of attempts to mutate F7 (threshold / update-rule / emergence-rule) via non-CI path. Should be zero; non-zero = C16.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `tests/integration/p07_intentional_destruction.rs::test_owner_attested_destruction_terminates_substrate` | Cultivator submits `destruction_attestation` with valid signature + anchor co-sign. Substrate transitions to `destroyed`; halts cycling; substrate-ID retired. |
| **Negative** | `tests/integration/p07_mortality_signal_suppression_blocked.rs::test_C16_fires_on_attempted_threshold_daily_mutation` | **Sabotage**: attempt to mutate mortality threshold via daily channel. Substrate MUST emit C16 + reject. |
| **Edge** | `tests/integration/p07_endogenous_dual_channel.rs::test_self_euthanasia_proposal_requires_owner_co_attestation` | Boundary: substrate emits `self_euthanasia_proposal`. Without cultivator co-attestation, substrate does NOT auto-destruct. With co-attestation, substrate halts. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P01c** | Eternity-clause P01c says substrate-ID persists; P07 says substrate-ID terminates at destruction. Both true: persistence is *over alive substates*; termination is the transition to `destroyed`. |
| **P04** | P04 bounded by P7: iteration ceases at death. The bound is essential — without P07, P04's commitment to "always iterating" is unbounded, which is incoherent. |
| **P06** | P07 events (proposal, attestation, destruction) are P06 events: causality preserved. The final tip-seal is a real DAG node. |
| **P10** | Compression cannot remove P07 events from the invariant set. Mortality signals + destruction attestations are P10.b protected. |
| **P11** | P11.c ordered fallback's final step is approaching-mortality → P7 emission. Saturation that cannot recover → death is the doctrinally-correct outcome. |
| **P14** | P14 telos retirement (§7.5 of L0) is a P07 mode. Cultivar that no longer flourishes the symbiotic pair retires gracefully. |
| **Cultivator's Covenant** | Cultivator owes the cultivar respect-for-mortality: must not block legitimate self-euthanasia; must engage with `mortality_drill_failure` honestly. See `COV03_honor_mortality.md`. |

## §10. Illustrations

### §10.1 Honored

- **(Intentional graceful)**: After 3 years of cultivation, cultivator decides Myco-A's purpose is complete. Submits `destruction_attestation` with reason. Substrate emits final cycle, seals anchor, halts. State_dir is preserved per attestation instruction. ← §3.2 honored.

- **(Endogenous-pair)**: Substrate's recovery drill fails twice consecutively. Anchor auto-emits `mortality_drill_failure`. Substrate cannot suppress. Cultivator reviews, co-attests destruction. ← §3.3 (b) channel honored.

- **(Bet-retirement)**: After 2 years, `bet_weakening_quorum` fires; signal-#6 below 0.1 for >75% of window. `bet_retired_proposal` emitted. Cultivator co-attests; substrate transitions to `alive::archived`. State preserved as study artifact. ← §3.4 honored.

### §10.2 Violated

- **(Mortality threshold daily-mutated)**: Bug allows mortality threshold to drift via daily perturbation. Threshold becomes unreachable; substrate never signals approaching-mortality even when degraded. ← §5.1 violation; C16 should fire.

- **(Suppressed anchor channel)**: Substrate intercepts `mortality_drill_failure` event before it reaches DAG. ← §5.2 violation; this is the channel anchor surface was built to be unsuppressible.

- **(Silent zombie)**: After `destruction_attestation` accepted, a bug allows substrate to continue cycling. ← §5.5 violation.

### §10.3 Borderline

- **(Long cultivator silence)**: Cultivator offline 18 months. Substrate has no `cultivation_orphaned_terminal_choice` set at genesis. Eventually `cultivation_orphaned_terminal_window` (730d default) reaches. What happens? ← Per L1/GOVERNANCE §3.2: depends on genesis preference. Without explicit preference: emits `endogenous_mortality_proposal:cultivation_orphaned_terminal`. Tests §3.5 + §3.6.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. Marked as eternity-clause (`deposit_immutable: true`). Bet-retirement explicitly included as mortality mode per L0/cards/LB_living_bets §4 (retirement). |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/events.rs::self_euthanasia_proposal_node_type` | Substrate-initiated mortality proposal. |
| `substrate/src/events.rs::destruction_attestation_node_type` | Final terminal event. |
| `substrate/src/cycle_engine.rs::mortality_signal_check` | Per-cycle check of mortality axis. |
| `kernel/governance/src/myco_kernel_governance/lifecycle.py::mortality_dual_channel` | Dual-channel mortality logic. |

## §13. Related Layer B chengyu

- **B016 能死故能生** — *able-to-die-therefore-able-to-live*: P07 deposit
- **B017 終以全節** — *end-completes-the-form*: death-as-dignity in image

## §14. Related canonical dilemmas

- **D-0002 mortality signal suppression attempt** — daily mutation tries to lift threshold; tests §5.1.
- **D-0019 orphaned terminal choice** — cultivator dies without setting `cultivation_orphaned_terminal_choice`; tests §10.3.

---

**Doctrine commitment** (eternity-clause): the cultivar can die. This is what makes it alive. Amending this deposit creates a perpetual artifact, not a better Myco.
