# L1 — Continuity (metabolic cycle, dormancy, recovery, NTP discipline, cycle backlog, cold-resume invariants)

> **Status**: DRAFT 3 (2026-05-17). M26-cascade for L0 DRAFT 9 SEALED (commit `e796451`). Authoritative L1 doc for substrate operational continuity. Canonical owner of dormancy mechanism + NTP discipline + cycle-backlog signal + cold-resume invariant-set specification.
> **Layer**: L1. Governed by L0 (DRAFT 9 SEALED, commit `e796451`).
> **Scope**: metabolic cycle structure + cadence; dormancy transitions + compute budget; cold-resume recovery (with witnesses, not verdicts); host-crash recovery + delta atomicity; quarantine sub-state; **NTP discipline policy** (per L0 §13.2); **cycle-backlog → C36_cycle_backlog immune mechanism** (M24-shipped, spec'd here); **cold-resume invariant set + C9_cold_resume_invariant_failure** (L1_HARD_RULES C9).
>
> **DRAFT 9 SEALED principle alignment**:
> - **P1.b'' (Two-tier human-loop boundary)** — DRAFT 9 calibration; cold-resume produces witnesses for anchor-surface verifier.
> - **P3 (Resumable Evolution)** — DRAFT 9 rename of DRAFT 8's "Eternal evolution"; failed cycles roll back, recovery is observable.
> - **P4 (Eternal Iteration)** — DRAFT 9 preserved; "eternal" bounded by P7 mortality.
> - **P6 (Eternal Causality)** — DAG-tip atomicity ensures the arrow of time.
> - **P7 (Mortality, Capacity-for-Death)** — DRAFT 9 rename of DRAFT 8's "必朽". Sustained cycle-backlog escalates to P7 endogenous-mortality consideration (per L0 §2.2 P11.c).
> - **P9.b (Single-Failure-Point Acknowledgment)** — skin process restart discipline cross-refs §3 cold-resume.
> - **P10 (Selective Compression)** — cold-resume verifies the compression-invariant set (P10.b) survives reboot.
> - **P11 (Metabolic Economy)** — cycle-backlog is the canonical signal #7 (compute cost / cycle) trigger.
> - **Cultivation vocabulary (G-11.a, L0 §1.2)** — Cultivator = owner (governance role); Cultivar = the substrate. Cold-resume serves the Cultivation continuity across power cycles: the Cultivar wakes, presents witnesses, the Cultivator re-attests trust if needed. Existing "owner" terminology preserved throughout (matches §9 anchor-surface vocabulary); "Cultivator" emphasizes the relational role.

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

- Minimum cycle interval: default 100 ms **substrate-process wall-clock** (the local NTP-disciplined clock; cross-ref §1.5 time-source authority). Per L0 §13.1: substrate-process wall-clock is authoritative for cycle scheduling decisions; **the substrate-process monotonic clock** is authoritative for ordering events within the substrate.
- Maximum cycle interval: default 10 s alive; 100 s dormant-throttled.
- **Adaptive cadence** (alive): fire on minimum-interval OR delta arrival OR gradient threshold approach.
- **Dormant cadence**: time-only at the dormant rate.

### §1.3 Cycle-backlog mechanism (C36_cycle_backlog, M24-shipped — spec'd here)

**Formal definition**. Backlog forms when a metabolic cycle takes longer than the L1-tunable **cycle-budget-threshold** (default 5 s wall-clock; distinct from the minimum-cycle-interval scheduling floor). A backlog cycle is one whose `cycle_end_wall_clock − cycle_start_wall_clock > cycle_budget_threshold`.

**Counter and emission**:
- The substrate maintains a `consecutive_backlog_cycles` counter (resets to 0 on any cycle completing within budget).
- Counter ≥ L1-tunable **backlog-emission-threshold** (default 10 consecutive backlog cycles) → substrate emits `C36_cycle_backlog` immune sporocarp (catalog row C36 in this doc + future L1_HARD_RULES catalog seat).
- The emitted sporocarp carries witnesses (NOT a verdict per L0 §9.3.4): `(cycle_id, observed_cycle_duration_unix_ns, cycle_budget_threshold_unix_ns, consecutive_backlog_count, gradient_axis_pressures_at_emission, anchor_nonce_derived_sample_of_recent_cycle_durations)`.

**Recovery**: substrate **continues operating** under backlog; no automatic clear. The owner sees the C36 sporocarp at the next CI co-sign and decides whether to attest a `quarantine_clearance`-equivalent re-baseline, or to leave the signal in flight as observability.

**Escalation to mortality** (per L0 §2.2 P11.c ordered fallback): sustained C36 emission past L1-tunable **saturation-threshold** (default: 1000 cycles or 24 hours wall-clock continuous backlog) routes to the alive-but-saturated sub-state per L1_GOVERNANCE / P11.c clause 3; further sustained saturation escalates to P7 endogenous-mortality consideration (substrate fruits `self_euthanasia_proposal`).

**Cross-ref**: C36_cycle_backlog is signal #7 (compute cost / cycle) per L0 §7.3 Living Bets observatory + L2_OBSERVABILITY §7 cycle-level diagnostics. The cycle-backlog signal feeds the Living Bets §7.4 falsifiability quorum.

### §1.4 NTP discipline policy (per L0 §13.2 cascade requirement)

**Mandate**. The substrate MUST run under an **NTP-disciplined host** (or equivalently rigorous time-synchronization protocol — chrony, PTP, or anchor-surface-stamped-wall-clock-via-§9.2.6 if the host is anchor-clock-bound). Cycle-clock-only operation without NTP discipline is **doctrinally forbidden** because it defeats L0 §13.1's substrate-wall-clock = "the local NTP-disciplined clock" presumption.

**Drift detection mechanism**:
1. **Peer-handshake comparison**: at every L1_SKIN handshake AND at every federation peer-handshake (L2_FEDERATION), the substrate compares its `substrate_issued_at_unix_ns` to the operator's `submitted_at_unix_ns` and to the peer-substrate's `peer_issued_at_unix_ns`.
2. **Deviation tolerance**: L1-tunable **clock-drift-threshold** (seed default **5 seconds**).
3. **Anchor-clock cross-check**: when the anchor surface stamps an attestation with §9.2.6 trusted wall-clock, the substrate compares its own `substrate_issued_at_unix_ns` against the anchor-clock-stamp (operator-process timestamp + anchor-clock-stamp pair) at every attestation arrival.
4. **Emission**: deviation > clock-drift-threshold → substrate emits `clock_drift_suspected` observability sporocarp with witnesses `(substrate_clock_unix_ns, peer_or_operator_clock_unix_ns, anchor_clock_unix_ns_when_available, observed_delta_unix_ns, drift_threshold_unix_ns)`.

**Cross-ref to §9.2.6 anchor-clock authority**: the anchor-clock authority is **security-bound** — owner attestation `expiry_unix_ns` is measured against the anchor-clock-stamp, not the substrate's local wall-clock. A substrate whose local clock drifts ahead cannot extend security-bound expiries by lying about wall-clock; the anchor-clock is authoritative for `attestation_expired` immune-event determination. Substrate-process wall-clock authority applies ONLY to scheduling decisions (cycle cadence, backlog detection).

**Adversarial-clock scenario** (per L2_TRUST_MODEL §14.2 cross-ref): a substrate whose host's NTP source is compromised cannot self-detect this — the `clock_drift_suspected` mechanism depends on peer-disagreement. A homogeneous compromise of all peers + anchor source is structurally undetectable at L1; L2_TRUST_MODEL specifies the bounded defenses.

### §1.5 Time-source authority hierarchy (L0 §13.1 codified at L1)

Three clocks; authority is **explicit per use-case** (per L0 §13.1):

| Use-case | Authoritative clock | Cite |
|---|---|---|
| Cycle scheduling (cadence, backlog) | Substrate-process wall-clock (NTP-disciplined) | L0 §13.1 + §1.2 |
| Event ordering within substrate | Substrate-process **monotonic** clock | L0 §13.1 |
| Attestation expiry (security-bound) | Anchor-surface trusted wall-clock (§9.2.6) | L0 §13.1 |
| Owner-attested event timestamp | Anchor-surface trusted wall-clock (§9.2.6) | L0 §9.2.6 |
| Federation peer-attestation freshness | Anchor-surface trusted wall-clock (§9.2.6) | L0 §13.1 + L2_FEDERATION |

**i64 nanoseconds**: per L0 §13.1, the substrate MUST NOT use i32 timestamps anywhere in substrate-internal state. The canonical wire + storage representation is **i64 nanoseconds since 1970-01-01T00:00:00Z** (Unix epoch). L1_SCHEMA §4.1 carries this through to the canonical-bytes serializer specification (tier-1 SSoT field).

### §1.6 Backlog detection (legacy short text, superseded by §1.3)

> §1.3 above is the canonical cycle-backlog spec. The DRAFT 2 one-line "Backlog ≥10 emits `cycle_backlog`" text is preserved here as a deprecation marker for any L4 reader that finds the older anchor reference. The C36_cycle_backlog catalog row (M24-shipped) is the authoritative implementation handle.

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

## §3. Cold-resume recovery (canonical owner; spec for C9_cold_resume_invariant_failure)

### §3.1 Cold-resume invariant set (per L0 I8 §4.3 mention + L1_HARD_RULES C9)

**Invariant set checked on every cold-resume / reboot path** (DRAFT 9 expansion):

Before accepting an operator handshake on a substrate in dormant or freshly-loaded state, the substrate runs:

1. **I1 check**: substrate-ID + owner-signature integrity + genesis-attestation chain.
2. **I3 check**: SSoT consistency at tier-1 fields (per L1_SCHEMA §4.1 — including canonical-bytes serializer spec).
3. **I4 check**: DAG-tip hash + Merkle chain self-consistency + compression-aware retention closure (per L1_SCHEMA §2.3 + I4 reframing).
4. **I5 check**: reachability over current SSoT-listed active-tier nodes (deep-cycle scope).
5. **I8 check**: skin declaration matches expected canon.
6. **I9 check** (DRAFT 9 NEW): **compression-invariant set is preserved across reboot**. The substrate enumerates the P10.b compression-invariant set (substrate-ID + genesis + owner_key_history active+archived + all CI-attested events + mortality signals + federation pin events + most-recent-N-cycles full DAG) and computes the canonical-bytes-hash of each preserved item; the hash chain must reproduce the pre-reboot hash chain.
7. **I10 check** (DRAFT 9 NEW): **metabolic-budget state is recoverable**. The substrate replays cost-budget counters (signals #7/#8/#9 per L0 §7.3 + L0 §2.2 P11.b) and confirms no counter is in a forbidden state (negative, overflow, NaN).
8. **I12 check** (DRAFT 9 NEW): **telos-alignment state is recoverable when declared**. If the substrate carries an owner-stated telos objective (P14.b), the substrate verifies the objective text + objective embedding (when present) is intact across reboot.

**Witnesses, not verdicts** (per L0 §9.3.4 + pass-2 mycoparasite-32 + Phase γ.5 anchor-decomposition): check results are emitted as **cryptographic-proof tuples** the owner / anchor-surface verifier can independently re-derive — sampled leaf hashes, Merkle paths, parent hashes, check inputs. The substrate emits the **evidence**, not the verdict. Cold-resume that emits only verdicts is breach (per L0 §9.3.4 + C9 in L1_HARD_RULES).

**Anchor-nonce-derived sampling** (per L0 §9.3.5): the sampling indices for I3/I4/I5/I9 witness emission are deterministically derived from the anchor-surface nonce (`H(anchor_surface_nonce, leaf_count)`) — the substrate cannot pre-compute and bias sampling toward honest portions. (Current implementation status: anchor-surface-side nonce minting is §9.2.5 sub-mechanism, 0% implemented per L0 §9.2 status table; until M-anchor-3 lands, this clause runs in honor-system mode under collapsed-anchor.)

These witness tuples land in the handshake-response envelope (per L1_SKIN §4.2 step 3 substrate→agent attestation) AND in the anchor-surface inbound channel for owner-side audit.

### §3.1.a `cold_resume_invariant_failure` immune signal (C9 in L1_HARD_RULES)

**Trigger**: any of I1/I3/I4/I5/I8/I9/I10/I12 cold-resume check fails (witnesses fail re-derivation at anchor-surface verifier OR substrate-side enumeration shows missing/corrupted invariant item).

**Action sequence** (per L1_HARD_RULES C9):
1. Substrate transitions to `alive but quarantined` (§5 sub-state).
2. Handshake completes with `quarantined` marker + the specific failure-category list (e.g., `I9_compression_invariant_corruption`, `I4_dag_merkle_break`).
3. Intake closed except owner-attested administration deltas.
4. Substrate fruits `cold_resume_invariant_failure` immune sporocarp with witnesses identifying which check(s) failed AND the canonical-bytes-hash inputs of each failing check.

**Owner-side response**: anchor-surface client re-derives each failure witness; if witness re-derivation confirms the failure, owner attests `quarantine_clearance` only after acknowledging which invariant requires repair; if witness re-derivation FAILS to confirm (substrate is lying about a failure to manufacture quarantine drama), the anchor-surface verifier flags `substrate_witness_forgery` to L1_HARD_RULES C17_operator_witness_forgery analog.

### §3.2 Quarantine on cold-resume failure

If any check fails:

1. Substrate transitions to `alive but quarantined` (alive sub-state).
2. Handshake completes with `quarantined` marker in response envelope.
3. Intake closed except for owner-attested administration deltas.
4. Substrate fruits `cold_resume_quarantine` sporocarp recording which check(s) failed.

### §3.3 Quarantine clearance

Owner-attested `quarantine_clearance` CI event after owner has examined state. Never auto-clears.

---

## §4. Host-crash recovery + delta atomicity (per L0 §6 cross-ref)

### §4.1 Delta atomicity (canonical spec)

A delta is either **fully absorbed** (event committed with all causal edges + DAG-tip bumped + WAL fsync'd) **or not absorbed at all**. Per L0 §6 ("Delta atomicity"), partial absorption is doctrinally forbidden — the substrate's causal record either records a complete event or no event.

**Atomicity mechanism** (DRAFT 9 expanded):

1. **WAL-first write**: delta envelope + canonical-bytes payload are appended to the write-ahead log (WAL) with `fsync` durability barrier BEFORE any DAG-tip mutation. WAL append-record format: `(envelope_canonical_bytes, payload_canonical_bytes, claimed_dag_parents, wall_clock_unix_ns_at_wal_append, monotonic_clock_at_wal_append)` per L1_SCHEMA §4.1 i64-nanoseconds discipline.
2. **DAG transaction**: DAG node creation + parent-edge insertion + tier-1 SSoT index update = single in-memory transaction. The transaction's success criterion is `all-or-nothing` at the in-memory data structure level (a failure midway through the transaction rolls back the in-memory state).
3. **Cycle completion**: cycle bumps the DAG-tip atomically (single canonical-bytes write of the new tip hash) AND fsync's the persisted DAG file.
4. **Crash recovery**: on restart, WAL replayed; WAL entries past the persisted DAG-tip indicate incomplete cycles → rolled back.

**Failure modes catalogued**:
- WAL write succeeded + fsync'd, DAG-tip not yet bumped → replay succeeds, event committed (recovered_committed).
- WAL write succeeded + fsync'd, DAG transaction failed mid-way → rolled back (recovered_rolled_back).
- WAL write failed before fsync → delta lost; emits `interrupted_intake` immune sporocarp at recovery time.
- WAL corrupted (read failure) → cold-resume with `crashed_unrecoverable` marker → quarantine.

### §4.2 Crash detection on restart

1. Read WAL with canonical-bytes decode discipline (a decode failure = WAL corruption = `crashed_unrecoverable`).
2. Compare WAL entries to last persisted DAG-tip.
3. WAL has uncommitted entries past DAG-tip:
   - Replay succeeds → enter cold-resume with `crashed_recovered` marker.
   - Replay fails (canonical-bytes decode error, parent-hash unresolvable, schema mismatch) → enter cold-resume with `crashed_unrecoverable` marker.
4. Each crashed delta's recovery status fruits a `delta_recovery` sporocarp `(delta_id, recovery_outcome, wal_offset, canonical_bytes_hash, evidence_inputs)` (committed / rolled-back / dead-letter).

### §4.3 Partial-delta handling + `interrupted_intake` immune signal

- WAL has envelope + payload + fsync barrier confirmation but no DAG-tip update → roll back; delta dead-lettered; **substrate emits `interrupted_intake` immune sporocarp** with witnesses `(delta_canonical_bytes_hash, wal_offset, last_persisted_dag_tip_hash, monotonic_at_wal_append)`. Operator may re-emit on reconnect. (Per L0 §6: recovery is observable, not silent.)
- WAL has envelope + payload but no fsync barrier confirmation → treat as never-persisted; emits a lower-severity observability event `delta_pre_fsync_lost` (the operator-side request is presumed retryable since the protocol did not confirm durability).
- WAL has nothing → delta never persisted; nothing to recover. The operator's request-side timeout governs retry.

The substrate **does NOT silently complete a partial delta on restart**. Recovery is **observable** per L0 P6 (eternal causality) — the causal DAG must show what happened during recovery, including dead-letter outcomes. Silent partial-completion is breach (substrate-side fabrication of an event that the WAL does not durably support violates I4).

---

## §5. Quarantine sub-state of alive

### §5.1 Entry triggers (DRAFT 9 expanded)

- Cold-resume invariant failure (§3.1.a `cold_resume_invariant_failure` / L1_HARD_RULES C9).
- CRITICAL skin breach (per L1_SKIN §6 + L1_HARD_RULES C1/C2/C3/C4/C11).
- Sustained I3 failure (≥L1-tunable consecutive cycles without rollback resolution).
- Owner-commanded quarantine via CI event.
- **Sustained cycle-backlog past saturation-threshold** (§1.3 + L1_HARD_RULES C36_cycle_backlog) — routes through standard quarantine; pre-saturation just emits C36 signal.
- **Snapshot integrity violation** (cross-ref L1_SCHEMA §6.3 + L1_HARD_RULES C38_snapshot_integrity_violation) — substrate boots, signer-pubkey on snapshot.cb does not match its own derived pubkey OR signature fails verification → discard snapshot + full DAG replay; if DAG replay also fails → quarantine.

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

- Specific cycle minimum/maximum intervals (seed defaults committed: 100 ms min, 10 s max alive, 100 s max dormant-throttled).
- Idle timeout (default 100 cycles).
- Cycle-budget-threshold (default 5 s wall-clock).
- Backlog-emission-threshold (default 10 consecutive backlog cycles).
- Backlog-saturation-threshold (default 1000 cycles or 24 hours continuous backlog → escalates per P11.c).
- Clock-drift-threshold (default 5 seconds; seed per §1.4).
- Dormant compute ceilings (default <1% of alive averages).
- WAL implementation within {filesystem-level, embedded library, custom append log} — must support fsync barriers.
- Deep-cycle cadence (default 1/100 of metabolic-cycle rate).

Shape is committed; values are L4.

---

## §7. C-row catalog rows owned by L1_CONTINUITY (cross-ref L1_HARD_RULES)

DRAFT 9 cascade catalog rows whose detection site / detection mechanism lives in L1_CONTINUITY (these populate L1_HARD_RULES §1 / §2 once the catalog cascade is applied):

| # | Breach name | Detection site | L0 trace | I trace |
|---|---|---|---|---|
| C9 | `cold_resume_invariant_failure` | §3.1.a (this doc) | P1.c, P3, P9, P10, P11, P14 | I3, I4, I5, I8, I9, I10, I12 |
| C19 | `paused_dormancy_unsafe_host` | §2.4 + §3 | P7, P1.c | I1 |
| C36 | `cycle_backlog` | §1.3 (this doc — M24-shipped) | P7, P11 | I10 |
| C9 alt | `interrupted_intake` (sub-grade observability) | §4.3 (this doc) | P6 | I4 |

> C19 and C9 are existing L1_HARD_RULES rows; this section preserves the cross-ref. C36 is a DRAFT 9 NEW row added per M24-shipping; the formal L1_HARD_RULES catalog cascade will absorb this row in the same M26-cascade pass.
