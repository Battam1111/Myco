# L1 — Continuity (metabolic cycle, dormancy, recovery, NTP discipline, cycle backlog, cold-resume invariants)

> **Status**: DRAFT 3 (2026-05-17). L1 doc for substrate operational continuity. Canonical owner of dormancy, NTP discipline, cycle-backlog signal, cold-resume invariant-set specification.
> **Layer**: L1. Governed by L0 DRAFT 9 SEALED (commit `e796451`). Cultivation vocabulary at L0 §1.2.

---

## §1. Metabolic cycle

### §1.1 Cycle structure (5 steps)

Each cycle:

1. **Tier-1 invariant checks** (L1_SCHEMA §4.1).
2. **Gradient advances** (L1_TROPISM).
3. **Deltas absorbed atomically** (§4); sporocarps emitted; DAG commits new tip-hash.
4. **Skin breach check** (I8) over absorbed events.
5. **Skin handshake / attestation arrival** processed.

**Deep cycle** (L4-tunable, default 1/100 metabolic-cycle rate): I5 reachability; tier-2 sampled validation (if §4.3 tier-3 escalation L4); recovery-drill scheduling.

Atomic — all 5 steps complete + DAG-tip advances, or cycle aborts + state rolls back.

### §1.2 Cycle cadence

L4-tunable:

- **Minimum**: default 100 ms substrate-process wall-clock (NTP-disciplined per §1.5). Per L0 §13.1: wall-clock authoritative for scheduling; **monotonic** for ordering within substrate.
- **Maximum**: default 10s alive; 100s dormant-throttled.
- **Adaptive (alive)**: fire on minimum-interval OR delta arrival OR gradient threshold approach.
- **Dormant**: time-only at dormant rate.

### §1.3 Cycle-backlog mechanism (C36_cycle_backlog, M24-shipped)

Backlog: `cycle_end_wall_clock − cycle_start_wall_clock > cycle_budget_threshold` (L1-tunable, default 5s; distinct from minimum-cycle-interval).

**Counter and emission**:
- `consecutive_backlog_cycles` (resets to 0 on any in-budget cycle).
- Counter ≥ L1-tunable backlog-emission-threshold (default 10) → emits `C36_cycle_backlog` immune sporocarp.
- Witnesses (NOT verdict per L0 §9.3.4): `(cycle_id, observed_cycle_duration_unix_ns, cycle_budget_threshold_unix_ns, consecutive_backlog_count, gradient_axis_pressures_at_emission, anchor_nonce_derived_sample_of_recent_cycle_durations)`.

**Recovery**: continues operating; no automatic clear. Owner sees C36 at next CI co-sign; decides whether to attest re-baseline or leave in flight.

**Escalation to mortality** (per L0 §2.2 P11.c): sustained C36 past L1-tunable saturation-threshold (default 1000 cycles or 24hr continuous) → alive-but-saturated sub-state per L1_GOVERNANCE / P11.c clause 3; further saturation → P7 endogenous-mortality (`self_euthanasia_proposal`).

C36 is signal #7 (compute cost / cycle) per L0 §7.3 + L2_OBSERVABILITY §7; feeds §7.4 falsifiability quorum.

### §1.4 NTP discipline (per L0 §13.2)

Substrate MUST run under **NTP-disciplined host** (or rigorous — chrony, PTP, or anchor-surface-stamped-wall-clock via §9.2.6). Cycle-clock-only operation **doctrinally forbidden** (defeats L0 §13.1 presumption).

**Drift detection**:
1. **Peer-handshake**: at every L1_SKIN + L2_FEDERATION handshake, compares `substrate_issued_at_unix_ns` to `submitted_at_unix_ns` and `peer_issued_at_unix_ns`.
2. **Tolerance**: L1-tunable clock-drift-threshold (seed 5s).
3. **Anchor-clock cross-check**: at every attestation arrival, compares own `substrate_issued_at_unix_ns` against §9.2.6 trusted-wall-clock stamp.
4. **Emission**: deviation > threshold → `clock_drift_suspected` with witnesses `(substrate_clock_unix_ns, peer_or_operator_clock_unix_ns, anchor_clock_unix_ns_when_available, observed_delta_unix_ns, drift_threshold_unix_ns)`.

Anchor-clock is **security-bound**: attestation `expiry_unix_ns` measured against anchor-stamp, not local wall-clock. Substrate cannot extend security-bound expiries via wall-clock lying; anchor-clock authoritative for `attestation_expired`. Wall-clock authority applies ONLY to scheduling.

Adversarial-clock (L2_TRUST_MODEL §14.2): compromised host NTP cannot self-detect — depends on peer-disagreement. Homogeneous compromise structurally undetectable at L1.

### §1.5 Time-source authority hierarchy (L0 §13.1)

| Use-case | Authoritative clock | Cite |
|---|---|---|
| Cycle scheduling (cadence, backlog) | Substrate-process wall-clock (NTP-disciplined) | L0 §13.1 + §1.2 |
| Event ordering within substrate | Substrate-process **monotonic** clock | L0 §13.1 |
| Attestation expiry (security-bound) | Anchor-surface trusted wall-clock (§9.2.6) | L0 §13.1 |
| Owner-attested event timestamp | Anchor-surface trusted wall-clock (§9.2.6) | L0 §9.2.6 |
| Federation peer-attestation freshness | Anchor-surface trusted wall-clock (§9.2.6) | L0 §13.1 + L2_FEDERATION |

**i64 nanoseconds**: per L0 §13.1, substrate MUST NOT use i32 timestamps. Canonical wire + storage = i64 nanoseconds since 1970-01-01T00:00:00Z. L1_SCHEMA §4.1 carries through to canonical-bytes serializer (tier-1 SSoT).

---

## §2. Dormancy

### §2.1 State definition

Three top-level states per L0 I1: alive, dormant, destroyed. Sub-states of alive (quarantined, legacy) at §5 + L1_GOVERNANCE §3.2.

### §2.2 alive → dormant triggers

- Operator-connection drop (L1_SKIN §4.5).
- Idle timeout (default 100 cycles).
- Owner-commanded via CI event (rare; hibernation).
- Operator-requested per L1_SKIN §4.5 `handshake_terminate` with `request_dormancy` (substrate honors mode preference paused/throttled, subject to resource-pressure override).

Emits `dormancy_enter`; operator-token invalidated.

### §2.3 dormant → alive triggers

- Valid operator handshake (L1_SKIN §4).
- **Owner-attestation arrival** at anchor-surface inbound channel: wakes to verify + commit pending CI sporocarp. Wakes into `alive-administrative` micro-state — only attestation-resolution events fire until idle-timeout returns to dormant.

Emits `dormancy_exit`.

### §2.4 Dormant compute budget

Two modes (operator-selectable per L1_SKIN §4.5; default throttled):

**Throttled**: cycle at maximum-interval floor; tier-1 invariants every cycle; gradient continues to evolve (decay-class appetites); no fruiting; intake closed; handshake + attestation-channel listening continues.

**Paused**: all metabolism halted; only handshake + attestation-channel listening continues.

**Host-observability**: external observables (network, CPU, disk) must remain below L1-tunable ceilings (default <1% of alive averages). Substrate cannot enforce against own host; owner monitors independently. Explicit declared asymmetry.

**Wall-clock vs cycle-clock during paused**: attestation `expiry_cycles` does NOT advance during paused dormancy. On wake, substrate re-validates against anchor trusted-timestamp; stale-on-wake → `attestation_expired`. Substrate cannot extend wall-clock budgets via paused.



## §3. Cold-resume recovery (spec for C9_cold_resume_invariant_failure)

### §3.1 Cold-resume invariant set (per L0 I8 §4.3 + L1_HARD_RULES C9)

Before accepting operator handshake on dormant/freshly-loaded substrate:

1. **I1**: substrate-ID + owner-signature integrity + genesis-attestation chain.
2. **I3**: SSoT consistency at tier-1 fields (L1_SCHEMA §4.1).
3. **I4**: DAG-tip hash + Merkle self-consistency + compression-aware retention closure (L1_SCHEMA §2.3).
4. **I5**: reachability over current SSoT-listed active-tier nodes (deep-cycle scope).
5. **I8**: skin declaration matches expected canon.
6. **I9** (DRAFT 9): **compression-invariant set preserved across reboot**. Enumerate P10.b set (substrate-ID + genesis + owner_key_history active+archived + all CI-attested events + mortality signals + federation pin events + most-recent-N-cycles full DAG); canonical-bytes-hash each; hash chain must reproduce pre-reboot chain.
7. **I10** (DRAFT 9): **metabolic-budget state recoverable**. Replay cost-budget counters (signals #7/#8/#9 per L0 §7.3 + §2.2 P11.b); no counter in forbidden state.
8. **I12** (DRAFT 9): **telos-alignment state recoverable when declared**. If owner-stated objective (P14.b), verify objective text + embedding intact.

**Witnesses, not verdicts** (per L0 §9.3.4): emitted as cryptographic-proof tuples the owner / anchor verifier can independently re-derive — sampled leaf hashes, Merkle paths, parent hashes, check inputs. Verdict-only = breach.

**Anchor-nonce-derived sampling** (per L0 §9.3.5): sampling indices for I3/I4/I5/I9 deterministically derived from anchor nonce (`H(anchor_surface_nonce, leaf_count)`); substrate cannot pre-compute. (Anchor-side nonce minting §9.2.5, 0% implemented; until M-anchor-3 lands, honor-system mode.)

Witness tuples land in handshake-response (L1_SKIN §4.2 step 3) AND anchor-surface inbound channel for owner-side audit.

### §3.1.a `cold_resume_invariant_failure` immune signal (C9)

**Trigger**: any I1/I3/I4/I5/I8/I9/I10/I12 check fails.

**Action**:
1. Substrate → `alive but quarantined` (§5).
2. Handshake completes with `quarantined` marker + specific failure-category list (e.g., `I9_compression_invariant_corruption`, `I4_dag_merkle_break`).
3. Intake closed except owner-attested administration.
4. Fruits `cold_resume_invariant_failure` with witnesses identifying failed check(s) AND canonical-bytes-hash inputs of each.

**Owner response**: anchor client re-derives failure witness; confirmed → `quarantine_clearance` attestation after acknowledging which invariant requires repair; if re-derivation FAILS (substrate lying), anchor verifier flags `substrate_witness_forgery` → C17 analog.

### §3.2 Quarantine on cold-resume failure

Any check fails → quarantine per §3.1.a; handshake completes with `quarantined`; intake closed except owner-attested administration; fruits `cold_resume_quarantine` recording failure category list.

### §3.3 Quarantine clearance

Owner-attested `quarantine_clearance` CI event after owner examines state. Never auto-clears.



## §4. Host-crash recovery + delta atomicity (per L0 §6)

### §4.1 Delta atomicity

Delta is either **fully absorbed** (committed with all causal edges + DAG-tip bumped + WAL fsync'd) **or not absorbed**. Per L0 §6, partial absorption forbidden.

**Atomicity**:

1. **WAL-first write**: delta envelope + canonical-bytes payload appended to WAL with `fsync` BEFORE any DAG-tip mutation. WAL record: `(envelope_canonical_bytes, payload_canonical_bytes, claimed_dag_parents, wall_clock_unix_ns_at_wal_append, monotonic_clock_at_wal_append)` per L1_SCHEMA §4.1.
2. **DAG transaction**: node creation + parent-edge insertion + tier-1 SSoT index update = single in-memory transaction; all-or-nothing (mid-transaction failure rolls back).
3. **Cycle completion**: cycle bumps DAG-tip atomically (single canonical-bytes write of new tip hash) AND fsync's persisted DAG file.
4. **Crash recovery**: on restart, WAL replayed; entries past persisted DAG-tip → rolled back.

**Failure modes**:
- WAL fsync'd, DAG-tip not bumped → replay succeeds, event committed (recovered_committed).
- WAL fsync'd, DAG transaction failed mid-way → rolled back (recovered_rolled_back).
- WAL failed before fsync → delta lost; emits `interrupted_intake` at recovery.
- WAL corrupted → cold-resume with `crashed_unrecoverable` → quarantine.

### §4.2 Crash detection on restart

1. Read WAL with canonical-bytes decode (decode failure = `crashed_unrecoverable`).
2. Compare WAL entries to last persisted DAG-tip.
3. WAL has uncommitted entries past DAG-tip:
   - Replay succeeds → cold-resume with `crashed_recovered`.
   - Replay fails (decode error, parent-hash unresolvable, schema mismatch) → `crashed_unrecoverable`.
4. Each crashed delta's recovery status fruits `delta_recovery` `(delta_id, recovery_outcome, wal_offset, canonical_bytes_hash, evidence_inputs)`.

### §4.3 Partial-delta handling + `interrupted_intake`

Three sub-cases by WAL durability: (a) fsync-confirmed but no DAG-tip update → roll back + dead-letter + emit `interrupted_intake` with `(delta_canonical_bytes_hash, wal_offset, last_persisted_dag_tip_hash, monotonic_at_wal_append)`; (b) no fsync barrier → treat as never-persisted + emit `delta_pre_fsync_lost` (operator retryable); (c) WAL empty → nothing to recover, operator timeout governs retry.

Substrate **does NOT silently complete a partial delta on restart**. Recovery is observable per L0 P6 — silent partial-completion is breach (violates I4).



## §5. Quarantine sub-state of alive

### §5.1 Entry triggers

- Cold-resume invariant failure (§3.1.a / C9).
- CRITICAL skin breach (L1_SKIN §6 + L1_HARD_RULES C1/C2/C3/C4/C11).
- Sustained I3 failure (≥L1-tunable consecutive cycles without rollback).
- Owner-commanded via CI event.
- Sustained cycle-backlog past saturation-threshold (§1.3 + C36) — pre-saturation emits C36 only.
- Snapshot integrity violation (L1_SCHEMA §6.3 + C38) — signer-pubkey mismatch OR signature fails → discard snapshot + full DAG replay; replay fails → quarantine.

### §5.2 Quarantine-state metabolism

Cycle continues at alive cadence; tier-1 invariants run; intake closed except owner-attested administration; sporocarp fruiting continues for diagnostic/immune; federation outputs suspended.

### §5.3 Quarantine exit

Owner-attested `quarantine_clearance` (§3.3).

### §5.4 Distinction from legacy (L1_GOVERNANCE §3.2)

- **Legacy**: owner unavailable; substrate runs normally except L0/L1 mutations frozen.
- **Quarantined**: substrate observing internal pathology; intake closed; federation suspended; L0/L1 mutations gated.

May be both; recovery requires owner-equivalent attestation per L1_GOVERNANCE §3.2 + quarantine clearance.

## §7. C-row catalog (L1_CONTINUITY-owned)

Detection sites here; full catalog rows at L1_HARD_RULES §1/§2:

- **C9** `cold_resume_invariant_failure` — §3.1.a
- **C19** `paused_dormancy_unsafe_host` — §2.4 + §3
- **C36** `cycle_backlog` — §1.3 (M24-shipped)
- `interrupted_intake` (sub-grade observability) — §4.3
