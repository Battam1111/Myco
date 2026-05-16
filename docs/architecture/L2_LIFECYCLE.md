# L2 — Lifecycle Doctrine

> **Status**: DRAFT 2 (2026-05-17, M27 CA5 cleanup). Cross-cuts L0 I1 / P7 / P8 + L1_GOVERNANCE §3-§4 + L1_CONTINUITY §2-§5 + L1_TROPISM §4.

---

## §1. State space

Three top-level states (L0 I1):

```
              ┌──────────┐         ┌──────────┐
   genesis ───▶│  alive   │ ◀────▶  │ dormant  │
              └────┬─────┘         └────┬─────┘
                   │                    │
                   └──────┬─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  destroyed   │ (terminal; anchor-surface final seal)
                   └──────────────┘
```

Sub-states of `alive` (DRAFT 9 SEALED, per L0 §I1 + L1_GOVERNANCE §3.2):

- **normal** — default steady-state
- **birth-period** — first ~N events; CI-elevation in effect
- **quarantined** — invariant breach; intake closed; awaits Cultivator clearance
- **legacy** — Cultivator heartbeat stale past §15.3 threshold; mutations frozen; daily ops continue
- **orphaned** — legacy_window elapsed without `succession_acceptance_attestation` OR empty `successor_chain` (L1_GOVERNANCE §3.2)
- **archived** — terminal-non-destroyed via §7.5 bet-retirement; state_dir preserved with anchor-seal (L0 §7.5.c)
- **saturated** — compression-insufficient OR no pre-attested compression rules (L0 P11.c); sustained → P7

Sub-states compose (e.g., legacy AND quarantined).

---

## §2. Genesis

L1_GOVERNANCE §4.1; trust derivation L2_TRUST_MODEL §2. Genesis sporocarp lands in DAG; substrate enters `alive (birth-period)`. The only operationally human-load-bearing transition.

---

## §3. Birth period

Seed thresholds + seed gradient-update-rules apply (L1_TROPISM §4). All parameter-tuning elevates to CI regardless of steady-state classification (L1_GOVERNANCE §1.3). Reclassification to daily-autonomous occurs at owner-attested birth-period termination.

**Termination paths** (L1_TROPISM §4 + L1_GOVERNANCE §1.3):

- **Path A (convergence-attested)** — ≥N sporocarps fruited + ≥M active-operation time + `threshold_emergence_rule` reports per-axis convergence below epsilon → `birth_period_complete_proposal` + owner co-attest → `alive (steady-state)` + `maturity_attestation` sporocarp.
- **Path B (max-duration ceiling)** — L1-tunable max (default 180 active-operation days); reaching forces forced-graduation OR `self_euthanasia_proposal`. Safety valve vs attention-exhaustion attack.

**Observability**: signals #2 HIGH, #3 RISING, #10 variance-weighted (L2_OBSERVABILITY §2.3.1) until P14 lands. Pathological birth signals → classifier auto-elevate or Cultivator intervene.

---

## §4. Steady state

Emergent thresholds replace seeds. 5-step metabolic cycle runs (L1_CONTINUITY §1.1). Living Bets observatory signals build historical baselines; falsifiability trigger arms (90-day rolling quorum). L0/L1 evolutions follow P3 protocol (CI-attested).

---

## §5. Dormancy (alive ↔ dormant)

L1_CONTINUITY §2 specifies triggers, throttled/paused modes, wake protocol, dual-clock asymmetry, and compute-budget host-observability asymmetry. Dominant non-terminal transition; substrate may cycle many times across life. Wall-clock-vs-cycle-clock asymmetry during paused dormancy is canonical defense vs self-induced-pause wall-clock-budget-extension (L2_TRUST_MODEL §3.4). Compute-budget enforcement vs host is declared asymmetry (L0 §6 + L2_TRUST_MODEL §6); Cultivator-side monitoring is the detection path.

---

## §6. Quarantined

L1_CONTINUITY §5 (entry triggers, metabolism while quarantined, exit via Cultivator-attested `quarantine_clearance` — never auto-clears). Only alive sub-state whose exit requires fresh Cultivator co-attestation. Federation outputs suspended.

---

## §7. Legacy / Orphaned / Archived

Full FSM: L1_GOVERNANCE §3.2; L0 §15 (Cultivator mortality) + §7.5 (bet-retirement).

**Vocabulary (DRAFT 3 SEALED)**: `succession_acceptance_attestation` (chain-head successor signs at anchor surface); `legacy_window` (L1-tunable, default 365 days from legacy entry); `orphaned_terminal_window` (L1-tunable, default 730 days); `cultivation_orphaned_terminal_choice` (genesis-time pre-attested ∈ {self_euthanasia | bet_retirement | indefinite_orphan}).

`alive::legacy`, `alive::orphaned`, `alive::archived` remain alive sub-states (substrate-ID + DAG preserved; only `destroyed` and final-`archived` seal future operation). Compositional (may overlap with quarantined). Bet-retirement transitions alive → `alive::archived` (state_dir preserved with anchor-seal; distinct from `destroyed` — state_dir survives).

---

## §8. Reproduction (P8)

L1_GOVERNANCE §4.3 + §16 (generation discipline per F22) + L1_SCHEMA §3.3 (spore construction). Inter-substrate doctrine: L2_FEDERATION.

- Modes: federation (semantic), cloning (full copy), cross-pollination (multi-parent, L1-deferred).
- Each child runs its own complete L2_LIFECYCLE from its own genesis; recursive under generation-limit discipline (L0 §16 + F22).
- Child-substrate-ID is Cultivator-minted at anchor surface (not parent-minted; F2 + L1_GOVERNANCE §4.1).

---

## §9. Mortality (alive → destroyed; terminal)

L0 P7 + L1_GOVERNANCE §4.4 (three destruction modes: intentional-Cultivator, catastrophic-environment, endogenous-pair dual-channel; M23.2 self-euthanasia). Mortality-axis F7: threshold + update-rule + emergence-rule all CI-level.

- **Endogenous dual-channel**: substrate emits `self_euthanasia_proposal` with `operator_witness`; anchor-surface emits `mortality_drill_failure` on two consecutive failed recovery drills.
- **Terminal record**: `anchor_surface_final_seal` Cultivator-co-signed; post-destruction handshakes return `substrate_destroyed`; seal scoped to this substrate-ID only.
- **Alternative terminal**: `alive::archived` via §7.5 bet-retirement preserves state_dir (not erased; substrate-ID does not re-bind).

---

## §10. Lifecycle sporocarp index

Each transition fruits a named sporocarp (substrate's auditable life-trail):
- `genesis_event`; `birth_period_complete_proposal` / `maturity_attestation` / `birth_period_max_reached`
- `dormancy_enter` / `dormancy_exit`; `cold_resume_quarantine` / `quarantine_clearance`
- `succession_required` / `succession_acceptance_attestation` (DRAFT 3); `cultivation_recovered`
- `reproduction_request` / `genesis_attested` (in parent's DAG)
- `bet_retired_proposal` / `endogenous_mortality_proposal:cultivation_orphaned_terminal` (L0 §7.5 + §15.5)
- `destruction_attestation` / `mortality_drill_failure` / `self_euthanasia_proposal`
- `anchor_surface_final_seal` (terminal for `destroyed`; also for `alive::archived` per L0 §7.5.c)
