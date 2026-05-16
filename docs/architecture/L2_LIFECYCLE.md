# L2 — Lifecycle Doctrine

> **Status**: DRAFT 2 (2026-05-17, M27 CA5 cleanup). Cross-cut doctrine theme.
> **Scope**: substrate operating regimes and transitions. Cross-cuts L0 I1 / P7 / P8 + L1_GOVERNANCE §3-§4 + L1_CONTINUITY §2-§5 + L1_TROPISM §4.

---

## §1. The state space

Three top-level states (per L0 I1):

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

Sub-states of `alive` (DRAFT 9 SEALED expanded set, per L0 §I1 + L1_GOVERNANCE §3.2):

- **normal** (default steady-state)
- **birth-period** (transitional; first ~N events; CI-elevation in effect)
- **quarantined** (invariant breach; intake closed; awaiting Cultivator clearance)
- **legacy** (Cultivator heartbeat stale past §15.3 threshold; mutations frozen; daily ops continue)
- **orphaned** (legacy_window elapsed without `succession_acceptance_attestation` OR empty `successor_chain` at legacy entry — per L1_GOVERNANCE §3.2)
- **archived** (terminal-non-destroyed via §7.5 bet-retirement; state_dir preserved with anchor-seal — per L0 §7.5.c)
- **saturated** (compression-insufficient OR no pre-attested compression rules — per L0 P11.c; sustained saturation past threshold escalates to P7)

A substrate may be in multiple alive sub-states simultaneously (e.g., legacy AND quarantined).

---

## §2. Genesis (one-time Cultivator-initiated event)

**Mechanism**: L1_GOVERNANCE §4.1. **Trust derivation**: L2_TRUST_MODEL §2.

**Lifecycle-cross-cut content**: genesis sporocarp lands in DAG; substrate enters `alive (birth-period)` sub-state. This is the only transition where a human is operationally load-bearing — every subsequent transition is substrate-initiated or Cultivator-attested-but-substrate-emitted.

---

## §3. Birth period (transitional sub-state of alive)

Birth-period is where seed thresholds + seed gradient-update-rules apply (per L1_TROPISM §4). The substrate has not yet observed enough metabolism to emerge thresholds; everything is hand-coded seeds.

### §3.1 Birth-period CI elevation

All parameter-tuning events are CI-level regardless of steady-state classification (per L1_GOVERNANCE §1.3). The reclassification to daily-autonomous happens at owner-attested birth-period termination.

This is intentionally high-friction: during birth, the substrate is most vulnerable to silent bad-tuning. Owner attention is concentrated here.

### §3.2 Birth-period termination — two coherent paths

Per L1_TROPISM §4 + L1_GOVERNANCE §1.3:

**Path A: convergence-attested**
- ≥N sporocarps fruited (default ~100; L4-tunable)
- ≥M active-operation time (default 6 months; L4-tunable)
- `threshold_emergence_rule` reports convergence per-axis below epsilon

When all three hold, substrate proposes `birth_period_complete_proposal`; owner co-attests; substrate transitions to `alive (steady-state)`. Substrate fruits `maturity_attestation` sporocarp.

**Path B: maximum-duration ceiling**
- L1-tunable max (default 180 active-operation days)
- Reaching max forces forced-graduation OR `self_euthanasia_proposal` (if non-convergent at ceiling)

The two paths are coherent: convergence (A) terminates birth normally; ceiling (B) is a safety valve preventing indefinite birth-period exploitation (per pass-2 mycoparasite-25 attention-exhaustion attack defense).

### §3.3 Birth-period observability

The Living Bets observatory (L0 §7) treats birth-period signals differently:

- Signal #2 (evolution rate) is HIGH during birth (expected — many seed adjustments)
- Signal #3 (read-pattern diversity) is RISING (agent is learning)
- Signal #10 (composite per L2_OBSERVABILITY §2.3) interpretation accounts for birth-period context (variance-weighted regime per §2.3.1 until P14 telos-alignment outcome signal lands)

If birth-period observatory signals are pathological (e.g., zero evolution; flat read-pattern; substrate is "stuck"), L1_GOVERNANCE classifier may auto-elevate or Cultivator intervenes.

---

## §4. Steady state (default alive sub-state)

After birth-period termination, the substrate operates with emergent thresholds. The metabolic cycle runs per L1_CONTINUITY §1.1 (5-step cycle: tier-1 invariants → gradient advance → delta absorb → sporocarp emit → DAG commit → skin breach check → handshake/attestation arrival processed).

Steady-state characteristics:

- Emergent fruiting thresholds replace seed values
- Living Bets observatory signals stabilize (each builds its own historical baseline)
- Living Bets falsifiability trigger arms (90-day rolling-window quorum)
- L0/L1 doctrine evolutions follow standard P3 protocol (CI-attested)

---

## §5. Dormancy (alive ↔ dormant)

**Mechanism**: L1_CONTINUITY §2. **Triggers**, **throttled/paused modes**, **wake protocol**, **dual-clock asymmetry against paused dormancy**, and **dormancy compute-budget host-observability declared asymmetry** all specified there.

**Lifecycle-cross-cut content**:
- The dormancy ↔ alive arc is the dominant non-terminal transition; substrate may enter/exit dormancy many times across its life.
- Wall-clock-vs-cycle-clock asymmetry during paused dormancy is the canonical defense against the substrate extending wall-clock attestation budgets via self-induced pause (cross-cut to L2_TRUST_MODEL §3.4 dual-clock).
- Compute-budget enforcement against the host is a declared asymmetry (per L0 §6 + L2_TRUST_MODEL §6): substrate cannot enforce against its host; Cultivator-side monitoring is the detection path.

---

## §6. Quarantined sub-state of alive

**Mechanism**: L1_CONTINUITY §5 (entry triggers, metabolism while quarantined, exit via Cultivator-attested `quarantine_clearance` CI event — never auto-clears).

**Lifecycle-cross-cut content**: quarantined is the only alive sub-state whose exit requires fresh Cultivator co-attestation. Federation outputs are suspended; substrate cannot infect peers while quarantined.

---

## §7. Legacy / Orphaned / Archived sub-states of alive (Cultivator-unavailability + bet-retirement)

**Full FSM**: L1_GOVERNANCE §3.2 (Cultivation succession FSM, DRAFT 3 vocabulary). **L0 doctrine**: L0 §15 (Cultivator mortality) + §7.5 (bet-retirement terminal).

**Vocabulary used (DRAFT 3 SEALED)**:
- `succession_acceptance_attestation` — chain-head successor signs at anchor surface (NOT "successor_activation" — pre-DRAFT-3 term).
- `legacy_window` (L1-tunable, default 365 days) — window from legacy entry within which chain-head successor MUST present acceptance attestation.
- `orphaned_terminal_window` (L1-tunable, default 730 days) — window from orphaned entry to terminal.
- `cultivation_orphaned_terminal_choice` — genesis-time pre-attested choice in {self_euthanasia | bet_retirement | indefinite_orphan}.

**Lifecycle-cross-cut content**:
- `alive::legacy`, `alive::orphaned`, `alive::archived` are alive sub-states (per L1_GOVERNANCE §3.2 + L0 §7.5.c + §I1 — substrate-ID + DAG preserved; only `destroyed` and final-`archived` seal future operation).
- Compositional states: a substrate may be both legacy/orphaned AND quarantined simultaneously; recovery requires `succession_acceptance_attestation` + `quarantine_clearance`.
- Bet-retirement (L0 §7.5) transitions alive → `alive::archived` (state_dir preserved with anchor-seal; distinct from `destroyed` because state_dir survives for archival access).

---

## §8. Reproduction (P8 — spawning child substrates)

**Mechanism**: L1_GOVERNANCE §4.3 + §16 (generation discipline per F22) + L1_SCHEMA §3.3 (spore-schema construction). **Inter-substrate doctrine**: L2_FEDERATION.

**Lifecycle-cross-cut content**:
- Reproduction modes: federation (semantic transfer), cloning (full copy), cross-pollination (multi-parent — deferred at L1).
- Each child runs its own complete L2_LIFECYCLE from its own genesis; reproduction is recursive (children spawn grandchildren) under generation-limit discipline (per L0 §16 + F22).
- Child-substrate-ID is Cultivator-minted at anchor surface (NOT parent-minted — per F2 + L1_GOVERNANCE §4.1).

---

## §9. Mortality (alive → destroyed; terminal)

**Mechanism**: L0 P7 + L1_GOVERNANCE §4.4 (three destruction modes: intentional-Cultivator, catastrophic-environment, endogenous-pair dual-channel; M23.2 self-euthanasia execution). **Mortality-axis F7 protection**: L1_HARD_RULES F7 (mortality-signal threshold + update-rule + emergence-rule all CI-level; cannot be silently tuned to suppress).

**Lifecycle-cross-cut content**:
- Endogenous-pair dual-channel: substrate channel emits `self_euthanasia_proposal` with `operator_witness` requirement; anchor-surface channel emits `mortality_drill_failure` on two consecutive failed recovery drills (substrate cannot suppress).
- Post-destruction terminal record: `anchor_surface_final_seal` co-signed by Cultivator. Handshake attempts against destroyed substrate-ID return `substrate_destroyed` from anchor surface (substrate process itself is gone).
- The seal affects only this substrate-ID; Cultivator activity at anchor surface continues for OTHER substrates / federated peers.
- **Alternative terminal**: `alive::archived` via §7.5 bet-retirement preserves state_dir under anchor-seal (distinct from `destroyed` — state_dir not erased; substrate-ID does not re-bind to new operator-connections).

---

## §10. Lifecycle observability summary

Each transition fruits a named sporocarp into the causal DAG:
- `genesis_event`
- `birth_period_complete_proposal` / `maturity_attestation` / `birth_period_max_reached`
- `dormancy_enter` / `dormancy_exit`
- `cold_resume_quarantine` / `quarantine_clearance`
- `succession_required` / `succession_acceptance_attestation` (DRAFT 3 vocabulary; legacy entry/exit per L1_GOVERNANCE §3.2)
- `cultivation_recovered` (orphaned → normal exceptional path)
- `reproduction_request` / `genesis_attested` (in parent's DAG)
- `bet_retired_proposal` / `endogenous_mortality_proposal:cultivation_orphaned_terminal` (per L0 §7.5 + §15.5)
- `destruction_attestation` / `mortality_drill_failure` / `self_euthanasia_proposal`
- `anchor_surface_final_seal` (terminal for `destroyed`; also issued for `alive::archived` per L0 §7.5.c)

These sporocarps are the substrate's auditable life-trail. Observers (Cultivator, anchor-surface-side audit tools, future agents at federated children) can reconstruct the complete lifecycle from the DAG.

---

## §11. Open at L2

- **Multi-Cultivator co-genesis**: deferred to L4 (per L1_GOVERNANCE §7).
- **Substrate hibernation versus dormancy**: dormancy is operator-disconnect-driven; hibernation could be Cultivator-commanded long-term dormancy (years). Currently subsumed into "Cultivator-commanded dormancy" CI event. Possibly worth distinct sub-state if hibernation has special observability properties — L4 may surface.
- **Child substrate inheritance of parent's lifecycle history**: explicitly NOT inherited (per L1_SCHEMA §3.2 — child begins own DAG). Whether anchor-surface records the parent-child genealogy independent of DAG is L4 (recommendation: yes, anchor-surface records `(parent_id, child_id, spawn_timestamp)` for Cultivator-side reproduction-tree auditing).
