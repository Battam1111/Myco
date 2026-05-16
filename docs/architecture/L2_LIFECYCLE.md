# L2 — Lifecycle Doctrine

> **Status**: DRAFT 3 (2026-05-17, M27 R5 cleanup). Cross-cuts L0 I1 / P7 / P8 + L1_GOVERNANCE §3-§4 + L1_CONTINUITY §2-§5 + L1_TROPISM §4.

---

## §1. State space (L0 I1)

```
   genesis ──▶ alive ◀──▶ dormant ──▶ destroyed (terminal; anchor final seal)
```

`alive` sub-states (compositional): **normal**; **birth-period** (CI-elevation); **quarantined** (intake closed; awaits clearance); **legacy** (heartbeat stale past §15.3; mutations frozen); **orphaned** (legacy_window elapsed without `succession_acceptance_attestation`); **archived** (terminal-non-destroyed via §7.5; state_dir preserved + anchor-seal); **saturated** (compression-insufficient per P11.c).

---

## §2-§4. Genesis + birth + steady

§2 genesis: L1_GOVERNANCE §4.1 + L2_TRUST_MODEL §2; sporocarp lands in DAG → `alive (birth-period)`; only operationally human-load-bearing transition.

§3 birth period (L1_TROPISM §4 + L1_GOVERNANCE §1.3; all parameter-tuning CI; reclassification at owner-attested termination):
- **Path A (convergence-attested)**: ≥N sporocarps + ≥M active-operation time + per-axis convergence below epsilon → `birth_period_complete_proposal` + owner co-attest → `alive (steady-state)` + `maturity_attestation`.
- **Path B (max-duration ceiling)**: L1-tunable max (default 180 active-operation days); forces graduation OR `self_euthanasia_proposal` (attention-exhaustion safety valve).
- **Observability**: #2 HIGH, #3 RISING, #10 variance-weighted (L2_OBSERVABILITY §2.3) until P14 lands.

§4 steady state: emergent thresholds replace seeds; 5-step metabolic cycle (L1_CONTINUITY §1.1); Living Bets baselines build; falsifiability quorum arms (90-day rolling); L0/L1 evolutions follow P3 CI-attested.

---

## §5-§7. Dormancy + quarantine + legacy-FSM

§5 dormancy: L1_CONTINUITY §2 (triggers, throttled/paused, wake, dual-clock asymmetry, compute-budget asymmetry). Wall-clock-vs-cycle-clock asymmetry during paused dormancy is canonical defense vs self-induced-pause wall-clock-budget-extension. Compute-budget enforcement vs host is declared asymmetry; Cultivator-side monitoring is detection path.

§6 quarantined: L1_CONTINUITY §5 (entry, metabolism-while-quarantined, exit via Cultivator-attested `quarantine_clearance` — never auto-clears). Only alive sub-state requiring fresh co-attestation for exit. Federation outputs suspended.

§7 legacy/orphaned/archived: L1_GOVERNANCE §3.2; L0 §15 (Cultivator mortality) + §7.5 (bet-retirement). Vocabulary: `succession_acceptance_attestation`, `legacy_window` (default 365 days), `orphaned_terminal_window` (default 730 days), `cultivation_orphaned_terminal_choice` (genesis pre-attested ∈ {self_euthanasia | bet_retirement | indefinite_orphan}). Sub-states remain alive (substrate-ID + DAG preserved); may overlap quarantined. Bet-retirement → `alive::archived` (state_dir preserved with anchor-seal; distinct from `destroyed`).

---

## §8. Reproduction (P8)

L1_GOVERNANCE §4.3 + §16 (generation discipline F22) + L1_SCHEMA §3.3; inter-substrate L2_FEDERATION. Modes: federation (semantic), cloning (full copy), cross-pollination (multi-parent, L1-deferred). Each child runs own complete lifecycle from own genesis; recursive under generation-limit. Child-substrate-ID Cultivator-minted at anchor (not parent-minted; F2 + L1_GOVERNANCE §4.1).

---

## §9. Mortality (alive → destroyed; terminal)

L0 P7 + L1_GOVERNANCE §4.4 (three modes: intentional-Cultivator, catastrophic-environment, endogenous-pair dual-channel; M23.2 self-euthanasia). Mortality-axis F7: threshold + update-rule + emergence-rule all CI.

- **Endogenous dual-channel**: substrate emits `self_euthanasia_proposal` with `operator_witness`; anchor emits `mortality_drill_failure` on two consecutive failed drills.
- **Terminal record**: `anchor_surface_final_seal` Cultivator-co-signed; post-destruction handshakes return `substrate_destroyed`; seal substrate-ID-scoped.
- **Alternative terminal**: `alive::archived` via §7.5 preserves state_dir (substrate-ID does not re-bind).

---

## §10. Lifecycle sporocarp index

Substrate's auditable life-trail: `genesis_event`; `birth_period_complete_proposal` / `maturity_attestation` / `birth_period_max_reached`; `dormancy_enter` / `dormancy_exit`; `cold_resume_quarantine` / `quarantine_clearance`; `succession_required` / `succession_acceptance_attestation` / `cultivation_recovered`; `reproduction_request` / `genesis_attested`; `bet_retired_proposal` / `endogenous_mortality_proposal:cultivation_orphaned_terminal`; `destruction_attestation` / `mortality_drill_failure` / `self_euthanasia_proposal`; `anchor_surface_final_seal` (terminal for `destroyed`; also `alive::archived` per L0 §7.5.c).
