# L2 — Lifecycle Doctrine

> **Status**: DRAFT 1 (2026-05-13). Cross-cut doctrine theme.
> **Layer**: L2.
> **Scope**: substrate operating regimes and transitions. Cross-cuts L0 I1 lifecycle states / P7 mortality / P8 reproduction + L1_GOVERNANCE §4 lifecycle + L1_CONTINUITY §2-5 dormancy/quarantine + L1_TROPISM §4 birth period. Answers: what are v0.9's operating regimes, what triggers each transition, how does the substrate move through its life?

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

Plus sub-states of `alive`:

- **steady-state** (default)
- **birth-period** (transitional; first ~N events; CI-elevation in effect)
- **quarantined** (invariant breach; intake closed; awaiting owner clearance)
- **legacy** (owner unavailable past grace; mutations frozen; daily ops continue)

A substrate may be in multiple alive sub-states simultaneously (e.g., legacy AND quarantined).

---

## §2. Genesis (one-time owner-initiated event)

Genesis is the only routine human-initiated event in the lifecycle. Detailed in L1_GOVERNANCE §4.1; the trust-model implications are in L2_TRUST_MODEL §2.

Detailed protocol in L1_GOVERNANCE §4.1 + trust derivation in L2_TRUST_MODEL §2. **The lifecycle-cross-cut content**: genesis sporocarp lands in DAG; substrate enters `alive (birth-period)` sub-state. This is the only transition where a human is operationally load-bearing — every subsequent transition is substrate-initiated or owner-attested-but-substrate-emitted.

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
- Signal #7 (composite health) interpretation accounts for birth-period context

If birth-period observatory signals are pathological (e.g., zero evolution; flat read-pattern; substrate is "stuck"), L1_GOVERNANCE classifier may auto-elevate or owner intervenes.

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

### §5.1 Triggers (alive → dormant)

Per L1_CONTINUITY §2.2 + L1_GOVERNANCE §4.2:

- Operator-connection drop (detected at skin)
- Idle timeout (default 100 cycles without delta absorption)
- Owner-commanded dormancy (CI event; rare; for substrate hibernation)
- Operator-requested dormancy via `handshake_terminate` with `request_dormancy: paused | throttled` field

Transition fruits `dormancy_enter` sporocarp; operator-token invalidated.

### §5.2 Dormancy modes

**Throttled mode** (default):
- Cycle rate at maximum-cycle-interval floor (default 100 s / cycle)
- Tier-1 invariant checks every cycle
- Gradient configuration continues to evolve (decay-class appetites)
- No fruiting; intake closed at skin; handshake + attestation-channel listening continues

**Paused mode** (operator-requestable; opt-in via canon):
- All metabolism halted
- Only handshake + attestation-channel listening continues

**Wall-clock-vs-cycle-clock asymmetry during paused** (cross-cut to L2_TRUST_MODEL): attestation-request `expiry_cycles` does NOT advance during paused dormancy, but anchor-surface trusted wall-clock CONTINUES. On wake, substrate re-validates attestation freshness against anchor-surface wall-clock; stale-on-wake → `attestation_expired` immune event. Substrate cannot extend wall-clock budgets by entering paused dormancy. This is the dual-clock defense (per L1_CONTINUITY §2.4 + L1_GOVERNANCE §2.3) propagating to lifecycle.

### §5.3 Triggers (dormant → alive)

- Valid operator handshake (per L1_SKIN §4)
- Owner-attestation arrival at anchor-surface inbound channel (substrate wakes into `alive-administrative` micro-state to process pending CI sporocarps)

Transition fruits `dormancy_exit`.

### §5.4 Dormancy compute budget + host-observability

Substrate's external observables (network egress, CPU, disk write rate) MUST remain below L1-tunable ceilings during dormancy (default <1% of alive averages). **The substrate cannot enforce this against its own host**; owner-side monitoring is the detection path. Declared asymmetry (per L0 §6 + L2_TRUST_MODEL §6).

---

## §6. Quarantined sub-state of alive

### §6.1 Entry triggers (per L1_CONTINUITY §5.1)

- Cold-resume invariant failure (§3.2 of L1_CONTINUITY)
- CRITICAL skin breach (per L1_SKIN §6 — see L1_HARD_RULES §1 for the full C1-C20 enumeration)
- Sustained I3 failure (≥L1-tunable consecutive cycles without rollback resolution)
- Owner-commanded quarantine via CI event

### §6.2 Quarantine-state metabolism

- Cycle continues at alive cadence (substrate is observing itself)
- Tier-1 invariants run
- Intake closed except owner-attested administration deltas
- Diagnostic + immune sporocarp fruiting continues
- Federation outputs suspended (cannot exit while quarantined)

### §6.3 Quarantine exit

Owner-attested `quarantine_clearance` CI event after owner has examined state and either:
- Confirmed failure is benign (e.g., known schema-migration in progress)
- Issued targeted CI mutations that fix the failure

Quarantine never auto-clears.

---

## §7. Legacy sub-state of alive (owner-unavailability)

### §7.1 Entry trigger (per L1_GOVERNANCE §3.2)

Owner liveness heartbeat goes stale at anchor surface (≥L1-tunable window without owner heartbeat AND substrate has at least one pending CI event).

`succession_required` immune event fires; substrate enters `succession_grace_period`.

### §7.2 Succession resolution

**During grace period**:
- Pre-attested successors may activate by signing `successor_activation` (anchor-surface-verified; substrate cannot use cached successor list — must consult anchor surface freshly).
- If owner liveness heartbeat resumes during grace, succession is canceled.

**Grace period elapsed without activation**: substrate transitions to `legacy` (alive but L0/L1 mutations frozen until ANY valid successor activation arrives, however late).

### §7.3 Legacy-state metabolism

- Daily operations continue normally
- CI events queue as pending (not rejected)
- New CI events cannot succeed (no owner to attest)
- Substrate is "alive without governance" — usable, not evolvable

### §7.4 Legacy exit

A successor activation arrives (potentially years later). Pending CI events from legacy period are evaluated by new owner; rejection rate is itself an immune-relevant statistic.

### §7.5 Legacy + quarantined compositional state

A substrate may be both legacy AND quarantined (owner unavailable AND pathology detected). Recovery requires successor activation + quarantine clearance.

---

## §8. Reproduction (P8 — spawning child substrates)

Per L1_GOVERNANCE §4.3 + L1_SCHEMA §3.3.

### §8.1 Reproduction modes

- **Federation**: semantic transfer to a child substrate
- **Cloning**: full substrate copy
- **Cross-pollination**: combining content from multiple parent substrates

### §8.2 Spawn protocol

1. Parent fruits `reproduction_request` CI-level sporocarp.
2. Owner co-attests (per L1_GOVERNANCE §2.2 attestation envelope).
3. Owner mints `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)`. Parent cannot mint.
4. Owner signs child's birth attestation at anchor surface.
5. Parent runs static-schema validation: child's spore-schema matches parent's current spore-schema-hash.
6. Child runs own I3 self-validation as first metabolic cycle.
7. If parent had unresolved CI-grade immune sporocarps: child enters `quarantined` birth-period until owner re-attests spawn was intentional.
8. Success: `genesis_attested` sporocarp in parent's DAG (federation_coupling edge to child-substrate-ID).

### §8.3 Child substrate's own lifecycle

Each child runs its own complete lifecycle from genesis through this same L2_LIFECYCLE doctrine. Reproduction is recursive: children spawn grandchildren.

See L2_FEDERATION for the inter-substrate population-level doctrine.

---

## §9. Mortality (alive → destroyed; terminal)

Per L0 P7 + L1_GOVERNANCE §4.4.

### §9.1 Three destruction modes

**Intentional-owner**:
- Owner emits CI-level `destruction_attestation` sporocarp.
- Substrate transitions alive → destroyed.
- **Final action**: substrate emits `anchor_surface_final_seal` co-signed by owner at anchor surface. Terminal record: "this substrate-ID is destroyed at timestamp T".

**Catastrophic-environment**:
- Medium failure beyond L1_SCHEMA recoverability budget.
- Detected post-hoc via recovery-drill failure (anchor-surface-side auto-emit).
- Identity continuum ceases retroactively to the moment catastrophe became unrecoverable.

**Endogenous-pair** (dual-channel):
- **Substrate channel**: substrate fruits `self_euthanasia_proposal` when its own metabolism crosses unrecoverable-pathology threshold. Active operator MUST produce `operator_witness` before proposal transmits to anchor surface; if no operator connected, substrate enters `pre-mortal-pending` and waits.
- **Anchor-surface channel**: two consecutive failed recovery drills → anchor-side `mortality_drill_failure` auto-emit (substrate cannot suppress).
- Either channel can trigger; owner co-attestation required to execute.

### §9.2 Mortality-signal protection

Mortality-signal threshold + update-rule + emergence-rule for mortality axis are all CI-level (per L1_GOVERNANCE §1.2 dimension table + L1_HARD_RULES F7). Cannot be silently tuned to suppress mortality warnings.

### §9.3 Post-destruction

After `anchor_surface_final_seal`:
- Substrate-ID is permanently destroyed.
- Substrate process terminates (gone).
- Handshake attempts against the destroyed substrate-ID return `substrate_destroyed` from the anchor surface (not from the substrate process — which no longer exists).
- Owner activity at the anchor surface continues for OTHER substrates / federated peers; the seal does NOT affect them.

---

## §10. Lifecycle observability summary

Each transition fruits a named sporocarp into the causal DAG:
- `genesis_event`
- `birth_period_complete_proposal` / `maturity_attestation` / `birth_period_max_reached`
- `dormancy_enter` / `dormancy_exit`
- `cold_resume_quarantine` / `quarantine_clearance`
- `succession_required` / `successor_activation` (legacy entry/exit)
- `reproduction_request` / `genesis_attested` (in parent's DAG)
- `destruction_attestation` / `mortality_drill_failure` / `self_euthanasia_proposal`
- `anchor_surface_final_seal` (terminal)

These sporocarps are the substrate's auditable life-trail. Observers (owner, anchor-surface-side audit tools, future agents at federated children) can reconstruct the complete lifecycle from the DAG.

---

## §11. Open at L2

- **Multi-owner co-genesis**: deferred to L4 (per L1_GOVERNANCE §7).
- **Substrate hibernation versus dormancy**: dormancy is operator-disconnect-driven; hibernation could be owner-commanded long-term dormancy (years). Currently subsumed into "owner-commanded dormancy" CI event. Possibly worth distinct sub-state if hibernation has special observability properties — L4 may surface.
- **Child substrate inheritance of parent's lifecycle history**: explicitly NOT inherited (per L1_SCHEMA §3.2 — child begins own DAG). Whether anchor-surface records the parent-child genealogy independent of DAG is L4 (recommendation: yes, anchor-surface records `(parent_id, child_id, spawn_timestamp)` for owner-side reproduction-tree auditing).
