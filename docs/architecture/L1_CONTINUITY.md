# L1 — Continuity (metabolic cycle, dormancy, recovery)

> **Status**: DRAFT 2 (2026-05-13). Authoritative L1 doc for substrate operational continuity. Canonical owner of dormancy mechanism specification.
> **Layer**: L1. Governed by L0.
> **Scope**: metabolic cycle structure + cadence; dormancy transitions + compute budget; cold-resume recovery (with witnesses, not verdicts); host-crash recovery + delta atomicity; quarantine sub-state.

---

## §1. Metabolic cycle

### §1.1 Cycle structure (5 steps)

Each cycle:

1. **Tier-1 invariant checks** (per L1_SCHEMA §4.1).
2. **Gradient configuration advances** (per L1_TROPISM, or equivalent under chosen dispatch).
3. **Deltas absorbed** atomically (per §4 delta atomicity); sporocarps emitted; DAG atomically commits with new tip-hash.
4. **Skin breach check** (I8) over events absorbed this cycle.
5. **Skin handshake / attestation arrival** processed (any new handshake or owner-attestation event).

**Deep cycle** runs at lower cadence (L4-tunable, default 1/100 of metabolic-cycle rate) and additionally executes:

- I5 reachability check.
- Tier-2 sampled validation (if §4.3 tier-3 escalation activates in L4).
- Recovery-drill scheduling.

A cycle is atomic — either all 5 steps complete and DAG-tip advances, or the cycle aborts and substrate state rolls back to the previous cycle's DAG-tip.

### §1.2 Cycle cadence

**Cadence is L4-tunable** within:

- Minimum cycle interval: default 100 ms wall-clock.
- Maximum cycle interval: default 10 s alive; 100 s dormant-throttled.
- **Adaptive cadence** (alive): fire on minimum-interval OR delta arrival OR gradient threshold approach.
- **Dormant cadence**: time-only at the dormant rate.

**Backlog detection**: if a cycle takes longer than the minimum interval, subsequent cycles backlog. Backlog ≥10 emits `cycle_backlog` immune event. Persistent backlog → quarantine.

---

## §2. Dormancy (canonical specification)

### §2.1 State definition

Three top-level states per L0 I1: alive, dormant, destroyed. Sub-states of alive (quarantined, legacy) are defined here (§5) and L1_GOVERNANCE (§3.2 succession).

### §2.2 alive → dormant triggers

- Operator-connection drop (detected at L1_SKIN §4.5).
- Idle timeout: ≥L1-tunable cycles without delta absorption (default 100 cycles).
- Owner-commanded dormancy via CI event (rare; substrate hibernation).
- Operator-requested dormancy: per L1_SKIN §4.5 `handshake_terminate` with `request_dormancy` field; substrate honors the operator's mode preference (paused vs throttled), subject to resource-pressure override.

Transition emits `dormancy_enter` sporocarp; operator-token invalidated.

### §2.3 dormant → alive triggers

- Valid operator handshake (L1_SKIN §4).
- **Owner-attestation arrival** at the anchor-surface inbound channel: substrate wakes to verify + commit pending CI sporocarp. Wakes into `alive-administrative` micro-state — only attestation-resolution events fire until idle-timeout returns substrate to dormant.

Transition emits `dormancy_exit` sporocarp.

### §2.4 Dormant compute budget

Two modes (operator-selectable per L1_SKIN §4.5; substrate default = throttled):

**Throttled mode**:
- Cycle rate at maximum-cycle-interval floor.
- Tier-1 invariant checks every cycle (cheap).
- Gradient configuration continues to evolve (decay-class appetites primarily).
- No fruiting; intake closed; handshake + attestation-channel listening continues.

**Paused mode**:
- All metabolism halted.
- Only handshake + attestation-channel listening continues.

**Dormancy host-observability**: external observables (network, CPU, disk) must remain below L1-tunable ceilings (default <1% of alive averages). **The substrate cannot enforce this against its own host**; the owner must independently monitor. This is an explicit declared asymmetry, not concealed.

**Wall-clock vs cycle-clock during paused** (per pass-2 mycoparasite-23 + rhizomorph-11): attestation-request `expiry_cycles` does NOT advance during paused dormancy. On wake, substrate re-validates attestation freshness against the anchor-surface trusted-timestamp (which IS wall-clock); stale-on-wake → `attestation_expired` immune event. Substrate cannot extend wall-clock budgets by entering paused dormancy.

---

## §3. Cold-resume recovery (canonical owner)

### §3.1 Pre-handshake checks with witnesses

Before accepting an operator handshake on a substrate in dormant or freshly-loaded state, the substrate runs:

1. I1 check: substrate-ID + owner-signature integrity.
2. I3 check: SSoT consistency at tier-1 fields.
3. I4 check: DAG-tip hash + Merkle chain self-consistency.
4. I5 check: reachability over current SSoT-listed tiers (deep-cycle scope).
5. I8 check: skin declaration matches expected canon.

**Witnesses, not verdicts** (per L0 §9.3 + pass-2 mycoparasite-32): check results are emitted as **cryptographic-proof tuples** the owner / anchor-surface verifier can independently re-derive — sampled hashes, Merkle paths, parent hashes, check inputs. The substrate emits the evidence, not the verdict. Cold-resume that emits only verdicts is skin breach.

These witness tuples land in the handshake-response envelope (per L1_SKIN §4.2 step 3 substrate→agent attestation) AND in the anchor-surface inbound channel for owner-side audit.

### §3.2 Quarantine on cold-resume failure

If any check fails:

1. Substrate transitions to `alive but quarantined` (alive sub-state).
2. Handshake completes with `quarantined` marker in response envelope.
3. Intake closed except for owner-attested administration deltas.
4. Substrate fruits `cold_resume_quarantine` sporocarp recording which check(s) failed.

### §3.3 Quarantine clearance

Owner-attested `quarantine_clearance` CI event after owner has examined state. Never auto-clears.

---

## §4. Host-crash recovery + delta atomicity

### §4.1 Delta atomicity

A delta is either fully absorbed (event committed with all causal edges) or not absorbed.

**Atomicity mechanism**:
- Delta absorption writes to WAL first.
- DAG node creation + edge insertion + index update = single transaction.
- Cycle completion bumps DAG-tip atomically.
- On crash: WAL replayed on restart; incomplete cycles detected (WAL entries past DAG-tip) and rolled back.

### §4.2 Crash detection on restart

1. Read WAL.
2. Compare to last persisted DAG-tip.
3. WAL has uncommitted entries past DAG-tip:
   - Replay succeeds → enter cold-resume with `crashed_recovered` marker.
   - Replay fails → enter cold-resume with `crashed_unrecoverable` marker.
4. Each crashed delta's recovery status fruits a `delta_recovery` sporocarp (committed / rolled-back / dead-letter).

### §4.3 Partial-delta handling

- WAL has envelope + payload but no DAG-tip update → roll back; delta dead-lettered; `interrupted_intake` immune event. Operator may re-emit on reconnect.
- WAL has nothing → delta never persisted; nothing to recover.

The substrate does NOT silently complete a partial delta on restart. Recovery is observable.

---

## §5. Quarantine sub-state of alive

### §5.1 Entry triggers

- Cold-resume invariant failure (§3.2).
- CRITICAL skin breach (per L1_SKIN §6).
- Sustained I3 failure (≥L1-tunable consecutive cycles without rollback resolution).
- Owner-commanded quarantine via CI event.

(Note: standalone `evolution_quarantine` sub-state from DRAFT 1 was cut per pass-2 astronaut-7 — repeated P3 evolution failures route through standard quarantine entry above, not a separate state. Repeated-failure observability lives in L1_GOVERNANCE §6 + the observatory rate signals.)

### §5.2 Quarantine-state metabolism

- Cycle continues at alive cadence (substrate observes itself).
- Tier-1 invariants run.
- Intake closed except owner-attested administration.
- Sporocarp fruiting continues for diagnostic / immune.
- Federation outputs suspended.

### §5.3 Quarantine exit

Owner-attested `quarantine_clearance` (§3.3).

### §5.4 Distinction from legacy (L1_GOVERNANCE §3.2 succession)

- **Legacy**: owner unavailable; substrate runs normally except L0/L1 mutations frozen.
- **Quarantined**: substrate is observing an internal pathology; intake closed; federation suspended; L0/L1 mutations also gated.

A substrate may be both legacy AND quarantined; recovery requires owner-equivalent attestation per L1_GOVERNANCE §3.2 + quarantine clearance.

---

## §6. Open at L1, deferred to L4

- Specific cycle minimum/maximum intervals.
- Idle timeout (default 100 cycles).
- Backlog threshold (default 10).
- Dormant compute ceilings (default <1% of alive averages).
- WAL implementation within {filesystem-level, embedded library, custom append log}.
- Deep-cycle cadence (default 1/100 of metabolic-cycle rate).

Shape is committed; values are L4.
