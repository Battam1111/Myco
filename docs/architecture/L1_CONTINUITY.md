# L1 — Continuity (metabolic cycle, dormancy, recovery, delta atomicity)

> **Status**: DRAFT 1 (2026-05-13). Authoritative L1 doc for substrate operational continuity.
> **Layer**: L1 (mechanism). Governed by L0.
> **Scope**: metabolic cycle cadence; dormancy state transitions + compute budget; cold-resume recovery; host-crash recovery; delta atomicity; quarantine sub-state.
> **Honesty**: pass-1 finding clusters addressed here include rhizomorph-3 (host-crash delta atomicity), rhizomorph-16 (dormancy triggers), saprotroph-3 portions, mycoparasite-15 (dormancy host-observability), mycoparasite-17 (quarantine-marker spoofing).

---

## §1. Metabolic cycle

### §1.1 What a cycle is

The substrate's smallest discrete metabolism event. Each cycle:

1. **Tier-1 invariant checks** run (per L1_SCHEMA §4.1) — I1 identity, I4 DAG-tip integrity.
2. **Gradient configuration advances** (per L1_TROPISM, or equivalent under chosen dispatch).
3. **Tier-2 sample validation** runs (one sample per cycle from rolling window).
4. **Deltas absorbed** (any envelope-accepted intake from the previous wall-clock interval).
5. **Sporocarps emitted** (any gradient that crossed its fruiting trigger).
6. **DAG updated** atomically with the cycle's events.
7. **I5 reachability check** runs.
8. **I8 skin breach check** runs.

A cycle is atomic — either all 8 steps complete and the DAG-tip advances, or the cycle is aborted and substrate state rolls back to the previous cycle's DAG-tip.

### §1.2 Cycle cadence

**Cadence is L4-tunable**, within constraints:

- **Minimum cycle interval** (rate ceiling): L1-tunable, default 100 ms wall-clock. Faster cycles risk operator-perceived load amplification.
- **Maximum cycle interval** (rate floor): L1-tunable, default 10 seconds wall-clock during alive state; 100 seconds during dormant-throttled state. Slower cycles risk I3/I5/I8 detection latency.
- **Adaptive cadence**: in alive state, cycles fire on whichever-first basis — every minimum-interval OR on delta arrival OR on gradient threshold approach. In dormant state, cycles fire on time-only basis at the dormant rate.

**Cadence under load**: if a single cycle takes longer than the minimum interval to complete, subsequent cycles backlog. Backlog of ≥L1-tunable (default 10) emits a `cycle_backlog` immune event. Persistent backlog → quarantine.

---

## §2. Dormancy

### §2.1 State definition (per L0 I1)

Three states: alive, dormant, destroyed. Dormant is a sub-state distinct from "alive but idle" — operator is not currently attached.

### §2.2 alive → dormant transition triggers

- **Operator disconnect** (L1_SKIN §4.5).
- **Idle timeout**: ≥L1-tunable cycles without delta absorption (default 100 cycles). This guards against half-open connections that L1_SKIN failed to detect.
- **Owner-commanded dormancy** via CI event (rare; for substrate hibernation).

Transition emits `dormancy_enter` sporocarp; operator-token (if any) is invalidated.

### §2.3 dormant → alive transition

- **Valid operator handshake** at the intake endpoint (per L1_SKIN §4).

Emits `dormancy_exit` sporocarp.

### §2.4 Dormant compute budget (per pass-1 mycoparasite-15)

Two operating modes:

**Throttled mode** (default):
- Cycle rate at the maximum-cycle-interval floor (100 sec / cycle default).
- Tier-1 invariant checks every cycle (cheap).
- Tier-2 sampling continues but at the same throttled rate.
- Gradient configuration continues to evolve (decay-class appetites mostly).
- No fruiting (sporocarps gated until alive).
- Intake closed at skin; handshake listening continues.

**Paused mode** (opt-in via canon):
- All metabolism halted.
- Only handshake listening continues.

**Dormancy host-observability**: the substrate's external observables (network egress, CPU, disk write rate) MUST remain below L1-tunable ceilings during dormancy. Default proposal: <1% of alive-state averages. **The substrate cannot enforce this against its own host** (per pass-1 mycoparasite-15) — the owner must independently monitor host-process behavior. This is an explicit asymmetry; declared, not concealed.

---

## §3. Cold-resume recovery (operationalizes L1_TROPISM §A3 + L0 I8 quarantine)

### §3.1 Pre-handshake checks

Before accepting an operator handshake on a substrate in dormant or freshly-loaded state:

1. **I1 check**: substrate-ID valid; owner-signature valid; identity record intact.
2. **I3 check**: SSoT consistency at tier-1 fields.
3. **I4 check**: DAG-tip hash valid; Merkle chain self-consistent.
4. **I5 check**: reachability over current SSoT-listed tiers.
5. **I8 check**: skin declaration matches expected canon.

**Each check's result is recorded in the handshake response envelope** (per pass-1 mycoparasite-17 — prevents quarantine-marker spoofing; the owner sees the cold-resume invariant results directly on handshake, not just via internal sporocarps).

### §3.2 Quarantine on cold-resume failure

If ANY pre-handshake check fails:

1. Substrate transitions to **`alive but quarantined`** sub-state (I1 state-space addendum).
2. Handshake completes but with a `quarantined` marker in the response envelope.
3. Intake is closed; only owner-attested administration deltas are accepted (limited to: clearing quarantine after fix; emitting `endogenous_mortality_proposal`; reading state for diagnosis).
4. The substrate fruits a `cold_resume_quarantine` sporocarp recording which check(s) failed.

### §3.3 Quarantine clearance

Quarantine is cleared by an owner-attested `quarantine_clearance` CI event after the owner has examined the substrate state and either:

- Confirmed the failure is benign (e.g., a known schema-migration in progress).
- Issued targeted CI mutations that fix the failure.

The quarantine never auto-clears.

---

## §4. Host-crash recovery (operationalizes pass-1 rhizomorph-3)

### §4.1 Delta atomicity

Per L0 §6 + pass-1 rhizomorph-3: a delta is either fully absorbed (event committed with all causal edges) or not absorbed at all.

**Atomicity mechanism**:

- Delta absorption writes to a WAL (write-ahead log) first.
- DAG node creation + edge insertion + index update happen as a single transaction.
- Cycle completion bumps DAG-tip hash atomically.
- On crash: WAL is replayed on restart; incomplete cycles are detected (WAL entries without corresponding DAG-tip update) and rolled back.

### §4.2 Crash detection on restart

On substrate process restart:

1. Read WAL.
2. Compare to last persisted DAG-tip.
3. If WAL has uncommitted entries past DAG-tip: enter cold-resume with `crashed_unrecoverable` marker if WAL replay fails OR `crashed_recovered` marker if replay succeeds.
4. Each crashed delta's recovery status fruits a `delta_recovery` sporocarp recording outcome (committed / rolled-back / dead-letter).

### §4.3 Partial-delta handling

If a delta absorption was interrupted mid-write:

- **WAL has the envelope + payload but no DAG-tip update** → roll back; delta is dead-lettered; emit `interrupted_intake` immune event. The operator's prior emission is lost; the operator may re-emit when reconnected.
- **WAL has nothing** → delta was never persisted; nothing to recover.

The substrate does NOT silently complete a partial delta on restart. Recovery is observable.

---

## §5. Quarantine sub-state of alive (operationalizes L0 I1)

Per pass-1 + L0 I1: legacy and quarantined are sub-states of alive. This section formalizes quarantined.

### §5.1 Entry triggers

- Cold-resume invariant failure (§3.2).
- CRITICAL-grade skin breach (per L1_SKIN §6).
- Repeated I3 evolution failures past quarantine threshold (per L1_GOVERNANCE §6.3).
- Owner-commanded quarantine via CI event.

### §5.2 Quarantine-state metabolism

- Cycle rate continues at alive cadence (substrate is observing itself; cycles run).
- Tier-1 invariants run.
- Intake at skin is **closed except for owner-attested administration deltas**.
- Fruiting continues for diagnostic / immune sporocarps.
- Federation outputs are suspended (cannot exit while quarantined).

### §5.3 Quarantine exit

- Owner-attested `quarantine_clearance` (per §3.3).

### §5.4 Distinction from legacy

- **Legacy** (per L1_GOVERNANCE §3.4): owner unavailable; substrate runs normally except L0/L1 mutations frozen.
- **Quarantined**: substrate is observing an internal pathology; intake closed; federation suspended; L0/L1 mutations also gated.

A substrate may be both legacy AND quarantined (owner unavailable AND substrate pathological). Recovery requires owner-equivalent attestation (successor activation per L1_GOVERNANCE §3.3 plus quarantine clearance).

---

## §6. Open at L1, deferred to L4

- **Specific cycle minimum/maximum intervals** — defaults proposed; L4 calibrates.
- **Specific idle timeout for dormancy** — default 100 cycles; L4 calibrates.
- **Specific backlog threshold** for `cycle_backlog` — default 10 cycles; L4 calibrates.
- **Specific dormant compute ceilings** (CPU / network / disk fractions of alive average) — default <1%; L4 calibrates.
- **WAL implementation** within {filesystem-level, embedded library, custom append log} — L4 picks.

Shape is committed; values are L4.
