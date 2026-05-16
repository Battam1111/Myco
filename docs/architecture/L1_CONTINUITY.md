# L1 — Continuity (metabolic cycle, dormancy, recovery, NTP discipline, cycle backlog, cold-resume invariants)

> **Status**: DRAFT 3. L1 for substrate operational continuity — dormancy, NTP discipline, cycle-backlog signal, cold-resume invariant set. Governed by L0. Cultivation vocabulary at L0 §1.2.

---

## §1. Metabolic cycle

### §1.1 Cycle structure (5 steps)

Each cycle: (1) tier-1 invariant checks (L1_SCHEMA §4.1); (2) gradient advances (L1_TROPISM); (3) deltas absorbed atomically (§4), sporocarps emitted, DAG commits new tip; (4) skin breach check (I8) over absorbed events; (5) handshake / attestation arrival processed.

**Deep cycle** (L4, default 1/100 rate): I5 reachability; tier-2 sampled validation; recovery-drill scheduling.

Atomic — all 5 complete + DAG-tip advances, or cycle aborts + state rolls back.

### §1.2 Cycle cadence

L4-tunable: **Minimum** default 100 ms substrate-process wall-clock (NTP-disciplined per §1.5; wall-clock authoritative for scheduling; monotonic for ordering). **Maximum** default 10s alive; 100s dormant-throttled. **Adaptive (alive)** fires on minimum-interval OR delta arrival OR gradient threshold. **Dormant**: time-only at dormant rate.

### §1.3 Cycle-backlog mechanism (C36_cycle_backlog)

Backlog: `cycle_end_wall_clock − cycle_start_wall_clock > cycle_budget_threshold` (L1-tunable, default 5s).

**Counter and emission**: `consecutive_backlog_cycles` (resets to 0 on any in-budget cycle); counter ≥ L1-tunable (default 10) → `C36_cycle_backlog` immune. Witnesses (L0 §9.3.4): `(cycle_id, observed_cycle_duration_unix_ns, cycle_budget_threshold_unix_ns, consecutive_backlog_count, gradient_axis_pressures_at_emission, anchor_nonce_derived_sample_of_recent_cycle_durations)`.

**Recovery**: continues operating; no auto-clear. Owner sees C36 at next CI co-sign; chooses re-baseline attestation or leave in flight.

**Escalation to mortality** (P11.c): sustained C36 past L1-tunable saturation-threshold (default 1000 cycles or 24hr continuous) → alive-but-saturated sub-state; further saturation → P7 (`self_euthanasia_proposal`).

C36 is signal #7 per L0 §7.3 + L2_OBSERVABILITY §7; feeds §7.4 falsifiability quorum.

### §1.4 NTP discipline (per L0 §13.2)

Substrate MUST run under NTP-disciplined host (or chrony / PTP / anchor-stamped-wall-clock via §9.2.6). Cycle-clock-only operation doctrinally forbidden (defeats L0 §13.1 presumption).

**Drift detection**: (1) peer-handshake — at every L1_SKIN + L2_FEDERATION handshake, compares `substrate_issued_at_unix_ns` to `submitted_at_unix_ns` and `peer_issued_at_unix_ns`; (2) tolerance L1-tunable clock-drift-threshold (seed 5s); (3) anchor-clock cross-check at every attestation arrival; (4) deviation > threshold → `clock_drift_suspected` with witnesses `(substrate_clock_unix_ns, peer_or_operator_clock_unix_ns, anchor_clock_unix_ns_when_available, observed_delta_unix_ns, drift_threshold_unix_ns)`.

Anchor-clock is security-bound: attestation `expiry_unix_ns` measured against anchor-stamp, not local wall-clock — substrate cannot extend security-bound expiries via wall-clock lying. Wall-clock authority applies ONLY to scheduling. Adversarial-clock (L2_TRUST_MODEL §14.2): compromised host NTP cannot self-detect; homogeneous compromise structurally undetectable at L1.

### §1.5 Time-source authority hierarchy (L0 §13.1)

| Use-case | Authoritative clock |
|---|---|
| Cycle scheduling (cadence, backlog) | Substrate-process wall-clock (NTP-disciplined) |
| Event ordering within substrate | Substrate-process monotonic clock |
| Attestation expiry (security-bound) | Anchor-surface trusted wall-clock (§9.2.6) |
| Owner-attested event timestamp | Anchor-surface trusted wall-clock (§9.2.6) |
| Federation peer-attestation freshness | Anchor-surface trusted wall-clock (§9.2.6) |

**i64 nanoseconds** (per L0 §13.1): substrate MUST NOT use i32 timestamps. Canonical wire + storage = i64 ns since 1970-01-01T00:00:00Z. L1_SCHEMA §4.1 carries through to canonical-bytes serializer (tier-1 SSoT).

---

## §2. Dormancy

### §2.1 State definition

Three top-level per I1: alive, dormant, destroyed. Alive sub-states (quarantined, legacy) at §5 + L1_GOVERNANCE §3.2.

### §2.2 alive → dormant triggers

Operator-connection drop (L1_SKIN §4.5); idle timeout (default 100 cycles); owner CI hibernation; operator-requested via `handshake_terminate` with `request_dormancy` (substrate honors paused/throttled, subject to resource-pressure override). Emits `dormancy_enter`; operator-token invalidated.

### §2.3 dormant → alive triggers

Valid operator handshake (L1_SKIN §4); owner-attestation arrival at anchor inbound channel — wakes to verify + commit pending CI sporocarp into `alive-administrative` micro-state (only attestation-resolution events fire until idle-timeout returns to dormant). Emits `dormancy_exit`.

### §2.4 Dormant compute budget

Two modes (operator-selectable; default throttled): **Throttled** — cycle at max-interval floor; tier-1 invariants every cycle; decay-class gradient evolves; no fruiting; intake closed; handshake + attestation-channel listening continues. **Paused** — all metabolism halted; only handshake + attestation-channel listening continues.

**Host-observability**: external observables (network, CPU, disk) must remain below L1-tunable ceilings (default <1% of alive averages). Substrate cannot enforce against own host; owner monitors independently. Declared asymmetry.

**Wall-clock vs cycle-clock during paused**: attestation `expiry_cycles` does NOT advance during paused. On wake, substrate re-validates against anchor trusted-timestamp; stale-on-wake → `attestation_expired`. Substrate cannot extend wall-clock budgets via paused.



## §3. Cold-resume recovery (spec for C9_cold_resume_invariant_failure)

### §3.1 Cold-resume invariant set

Before accepting operator handshake on dormant/freshly-loaded substrate:

1. **I1** — substrate-ID + owner-signature integrity + genesis-attestation chain.
2. **I3** — SSoT consistency at tier-1 fields (L1_SCHEMA §4.1).
3. **I4** — DAG-tip hash + Merkle self-consistency + compression-aware retention closure (L1_SCHEMA §2.3).
4. **I5** — reachability over SSoT-listed active-tier nodes (deep-cycle scope).
5. **I8** — skin declaration matches expected canon.
6. **I9** — compression-invariant set preserved across reboot. Enumerate P10.b set (substrate-ID + genesis + owner_key_history active+archived + all CI-attested events + mortality signals + federation pin events + most-recent-N cycles full DAG); canonical-bytes-hash each; hash chain must reproduce pre-reboot chain.
7. **I10** — metabolic-budget state recoverable. Replay cost-budget counters (signals #7/#8/#9); no counter in forbidden state.
8. **I12** — telos-alignment state recoverable when declared. If owner-stated objective (P14.b), verify objective text + embedding intact.

**Witnesses, not verdicts** (L0 §9.3.4): emitted as cryptographic-proof tuples owner / anchor can independently re-derive (sampled leaf hashes, Merkle paths, parent hashes, check inputs). Verdict-only = breach.

**Anchor-nonce-derived sampling** (L0 §9.3.5): sampling indices for I3/I4/I5/I9 deterministically derived from anchor nonce; substrate cannot pre-compute.

Witness tuples land in handshake-response (L1_SKIN §4.2 step 3) AND anchor inbound channel for owner-side audit.

### §3.1.a `cold_resume_invariant_failure` immune signal (C9)

**Trigger**: any I1/I3/I4/I5/I8/I9/I10/I12 check fails. **Action**: (1) substrate → `alive but quarantined` (§5); (2) handshake completes with `quarantined` marker + failure-category list; (3) intake closed except owner-attested admin; (4) fruits `cold_resume_invariant_failure` with witnesses identifying failed check(s) AND canonical-bytes-hash inputs.

**Owner response**: anchor client re-derives failure witness; confirmed → `quarantine_clearance` after acknowledging which invariant requires repair; re-derivation FAILS (substrate lying) → anchor flags `substrate_witness_forgery` (C17 analog).

### §3.2 Quarantine on cold-resume failure

Any check fails → quarantine per §3.1.a; `quarantined` handshake completion; intake closed except owner admin; fruits `cold_resume_quarantine` recording failure list.

### §3.3 Quarantine clearance

Owner-attested `quarantine_clearance` CI after owner examines state. Never auto-clears.



## §4. Host-crash recovery + delta atomicity (per L0 §6)

### §4.1 Delta atomicity

Delta is fully absorbed (all causal edges + DAG-tip bumped + WAL fsync'd) or not absorbed. Partial absorption forbidden.

**Atomicity**: (1) WAL-first write — delta envelope + canonical-bytes payload appended to WAL with `fsync` BEFORE any DAG mutation; record: `(envelope_canonical_bytes, payload_canonical_bytes, claimed_dag_parents, wall_clock_unix_ns_at_wal_append, monotonic_clock_at_wal_append)`; (2) DAG transaction — node creation + parent-edge insertion + tier-1 SSoT update = single in-memory transaction; all-or-nothing; (3) cycle completion bumps DAG-tip atomically (single canonical-bytes write) AND fsyncs persisted DAG; (4) crash recovery — WAL replayed; entries past persisted DAG-tip rolled back.

**Failure modes**: WAL fsync'd + DAG-tip not bumped → replay succeeds (recovered_committed); WAL fsync'd + DAG mid-way failure → rolled back; WAL failed pre-fsync → delta lost + `interrupted_intake`; WAL corrupted → `crashed_unrecoverable` → quarantine.

### §4.2 Crash detection on restart

(1) Read WAL with canonical-bytes decode (decode failure = `crashed_unrecoverable`); (2) compare WAL entries to last persisted DAG-tip; (3) WAL has uncommitted entries past tip: replay succeeds → `crashed_recovered`; replay fails (decode error / parent-hash unresolvable / schema mismatch) → `crashed_unrecoverable`; (4) each crashed delta fruits `delta_recovery (delta_id, recovery_outcome, wal_offset, canonical_bytes_hash, evidence_inputs)`.

### §4.3 Partial-delta handling + `interrupted_intake`

Three sub-cases by WAL durability: (a) fsync-confirmed but no DAG-tip update → roll back + dead-letter + `interrupted_intake (delta_canonical_bytes_hash, wal_offset, last_persisted_dag_tip_hash, monotonic_at_wal_append)`; (b) no fsync barrier → treat as never-persisted + `delta_pre_fsync_lost` (retryable); (c) WAL empty → operator timeout governs retry.

Substrate does NOT silently complete partial delta on restart. Recovery observable per P6 — silent completion violates I4.



## §5. Quarantine sub-state of alive

### §5.1 Entry triggers

Cold-resume invariant failure (§3.1.a / C9); CRITICAL skin breach (L1_HARD_RULES C1/C2/C3/C4/C11); sustained I3 failure (≥L1-tunable consecutive cycles without rollback); owner CI command; sustained cycle-backlog past saturation-threshold (§1.3 + C36); snapshot integrity violation (L1_SCHEMA §6.3 + C38) → discard snapshot + full DAG replay; replay fails → quarantine.

### §5.2 Quarantine-state metabolism

Cycle continues at alive cadence; tier-1 invariants run; intake closed except owner admin; sporocarp fruiting continues (diagnostic/immune); federation outputs suspended.

### §5.3 Quarantine exit

Owner-attested `quarantine_clearance` (§3.3).

### §5.4 Distinction from legacy (L1_GOVERNANCE §3.2)

**Legacy**: owner unavailable; substrate runs normally except L0/L1 mutations frozen. **Quarantined**: substrate observing internal pathology; intake closed; federation suspended; L0/L1 mutations gated. May be both; recovery requires owner-equivalent attestation per L1_GOVERNANCE §3.2 + quarantine clearance.

## §7. C-row catalog (L1_CONTINUITY-owned)

Full catalog at L1_HARD_RULES §1/§2; detection sites:

- **C9** `cold_resume_invariant_failure` — §3.1.a
- **C19** `paused_dormancy_unsafe_host` — §2.4 + §3
- **C36** `cycle_backlog` — §1.3
- `interrupted_intake` (sub-grade observability) — §4.3
