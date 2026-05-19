> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L1 — Continuity (metabolic cycle, dormancy, recovery, NTP discipline, cycle backlog, cold-resume invariants)

> L1 for substrate operational continuity. All numeric thresholds L1-tunable unless specified.

---

## §1. Metabolic cycle

**§1.1 Cycle structure (5 steps)** — Each cycle atomic — all 5 complete + DAG-tip advances, or aborts + state rolls back:

| Step | Action |
|---|---|
| 1 | Tier-1 invariant checks (L1/SCHEMA §4.1) |
| 2 | Gradient advances (L1/TROPISM) |
| 3 | Deltas absorbed atomically (§4); sporocarps emitted; DAG commits new tip |
| 4 | Skin breach check (I8) over absorbed events |
| 5 | Handshake / attestation arrival processed |

**Deep cycle** (L4, default 1/100 rate): I5 reachability; tier-2 sampled validation; recovery-drill scheduling; **prune-scan (NEW v3.1.1 — per P07 §3.1.c)** — sample of substrate state inspected against 应朽 family detection rules (canonical: 过时/错误/冗余/无用; L1-extensible per F24 to 有害/矛盾/僵化/异化/污染/失效/寄生/滞塞/死症/...); matched parts pruned with `internal_mortality_event` tombstone emission per P07 §3.3.

> **v3.1.1 transition note (prune-phase):** the prune-scan step is doctrinally committed (P07 v3.1.1 + COV04 v2 + CHAR03 v2) but implementation is deferred to a v0.9.x milestone alongside Layer C witness corpus and HARD_RULES C54-C56 + F24 wiring. The deep-cycle frequency for prune-scan is L4-tunable (default 1/100 rate ≈ daily at 100ms cycle cadence). Full-cycle prune-scan is L1-tunable (default every 1000 cycles, NEVER disabled per P07 §5.1).

**§1.2 Cycle cadence** — L4-tunable: **Minimum** default 100 ms substrate-process wall-clock (NTP-disciplined per §1.5; wall-clock authoritative for scheduling; monotonic for ordering). **Maximum** default 10s alive; 100s dormant-throttled. **Adaptive (alive)** fires on minimum-interval OR delta arrival OR gradient threshold. **Dormant**: time-only at dormant rate.

**§1.3 Cycle-backlog mechanism (C36_cycle_backlog)** — Algorithm: `algorithms/cycle_backlog.md` (predicate + counter + witnesses + escalation to mortality per P11.c). C36 IS signal #7 per L0/cards/LB_living_bets.md §3 + L2/OBSERVABILITY §7; feeds §7.4 falsifiability quorum.

**§1.4 NTP discipline (per L0/cards/COV01_fiduciary_duty.md + COV02 (adversarial owner))** — Substrate MUST run under NTP-disciplined host (or chrony / PTP / anchor-stamped-wall-clock via §9.2.6). Cycle-clock-only operation FORBIDDEN. Drift detection: peer-handshake `substrate_issued_at_unix_ns` vs `submitted_at_unix_ns` and `peer_issued_at_unix_ns`; tolerance seed 5s; anchor-clock cross-check at every attestation arrival; deviation > threshold → `clock_drift_suspected` with witnesses `(substrate_clock_unix_ns, peer_or_operator_clock_unix_ns, anchor_clock_unix_ns_when_available, observed_delta_unix_ns, drift_threshold_unix_ns)`. Anchor-clock IS security-bound: attestation `expiry_unix_ns` measured against anchor-stamp, not local wall-clock. Adversarial-clock (L2/TRUST_MODEL): homogeneous host compromise structurally undetectable at L1.

**§1.5 Time-source authority hierarchy (L0/cards/P06_eternal_causality.md + L1/CONTINUITY (time semantics))**:

| Use-case | Authoritative clock |
|---|---|
| Cycle scheduling (cadence, backlog) | Substrate-process wall-clock (NTP-disciplined) |
| Event ordering within substrate | Substrate-process monotonic clock |
| Attestation expiry (security-bound) | Anchor-surface trusted wall-clock (§9.2.6) |
| Owner-attested event timestamp | Anchor-surface trusted wall-clock (§9.2.6) |
| Federation peer-attestation freshness | Anchor-surface trusted wall-clock (§9.2.6) |

**i64 nanoseconds** (per L0/cards/P06_eternal_causality.md + L1/CONTINUITY (time semantics)): substrate MUST NOT use i32. Canonical wire + storage = i64 ns since 1970-01-01T00:00:00Z. L1/SCHEMA §4.1 carries through to canonical-bytes serializer (tier-1 SSoT).

---

## §2. Dormancy

**§2.1 State definition**: Three top-level per I1: alive, dormant, destroyed. Alive sub-states (quarantined, legacy) at §5 + L1/GOVERNANCE §3.2.

**§2.2 alive → dormant triggers**: Operator-connection drop (L1/SKIN §4.5); idle timeout (default 100 cycles); owner CI hibernation; operator-requested via `handshake_terminate` with `request_dormancy` (paused/throttled, subject to resource-pressure override). Emits `dormancy_enter`; operator-token invalidated.

**§2.3 dormant → alive triggers**: Valid operator handshake (L1/SKIN §4); owner-attestation arrival at anchor inbound channel — wakes to verify + commit pending CI sporocarp into `alive-administrative` micro-state (only attestation-resolution events fire until idle-timeout). Emits `dormancy_exit`.

**§2.4 Dormant compute budget**: Two modes (operator-selectable; default throttled): **Throttled** cycles at max-interval floor; tier-1 invariants every cycle; decay-class gradient evolves; no fruiting; intake closed; handshake + attestation-channel listening continues. **Paused** halts all metabolism; only handshake + attestation-channel listening continues. Host-observability: external observables MUST remain below default <1% of alive averages. Substrate cannot enforce against own host; owner monitors independently — declared asymmetry. Attestation `expiry_cycles` does NOT advance during paused; on wake substrate re-validates against anchor trusted-timestamp; stale-on-wake → `attestation_expired`.

---

## §3. Cold-resume recovery (spec for C9_cold_resume_invariant_failure)

**§3.1 Cold-resume invariant set** — Before accepting operator handshake on dormant/freshly-loaded substrate, substrate MUST check:

1. **I1** — substrate-ID + owner-signature integrity + genesis-attestation chain.
2. **I3** — SSoT consistency at tier-1 fields (L1/SCHEMA §4.1).
3. **I4** — DAG-tip hash + Merkle self-consistency + compression-aware retention closure.
4. **I5** — reachability over SSoT-listed active-tier nodes (deep-cycle scope).
5. **I8** — skin declaration matches expected canon.
6. **I9** — compression-invariant set preserved (P10.b canonical-bytes-hash chain reproduces pre-reboot).
7. **I10** — metabolic-budget state recoverable (replay signals #7/#8/#9 counters).
8. **I12** — telos-alignment state recoverable when declared (P14.b objective text + embedding intact).

**Witnesses, not verdicts** (L0/cards/AS_anchor_surface.md §3.11): emitted as cryptographic-proof tuples (sampled leaf hashes, Merkle paths, parent hashes, check inputs). Verdict-only IS breach. **Anchor-nonce-derived sampling** (L0/cards/AS_anchor_surface.md §3.12): indices deterministically derived from anchor nonce. Witness tuples land in handshake-response (L1/SKIN §4.2 step 3) AND anchor inbound channel.

**§3.1.a `cold_resume_invariant_failure` immune signal (C9)**: Any I1/I3/I4/I5/I8/I9/I10/I12 fails → substrate `alive but quarantined` (§5); handshake completes with `quarantined` marker + failure-category list; intake closed except owner-attested admin; fruits `cold_resume_invariant_failure` with witnesses. Owner anchor client re-derives; confirmed → `quarantine_clearance`; re-derivation FAILS → anchor flags `substrate_witness_forgery` (C17 analog).

**§3.2 + §3.3 Quarantine + clearance**: Any §3.1 fails → quarantine per §3.1.a. Owner-attested `quarantine_clearance` CI after examining state. Never auto-clears.

---

## §4. Host-crash recovery + delta atomicity (per L0/cards/P04_eternal_iteration.md §3-§4 + L1/CONTINUITY)

Schema: `schemas/wal_record.json` (WAL record + 4-step atomicity protocol + failure modes). Delta is fully absorbed (all causal edges + DAG-tip bumped + WAL fsync'd) or not absorbed. Partial FORBIDDEN.

**Crash detection on restart**: (1) read WAL with canonical-bytes decode (decode failure = `crashed_unrecoverable`); (2) compare WAL entries to last persisted DAG-tip; (3) WAL has uncommitted entries past tip — replay succeeds → `crashed_recovered`; replay fails → `crashed_unrecoverable`; (4) each crashed delta fruits `delta_recovery (delta_id, recovery_outcome, wal_offset, canonical_bytes_hash, evidence_inputs)`.

**Partial-delta handling**: three sub-cases by WAL durability — (a) fsync-confirmed + no DAG-tip update → roll back + dead-letter + `interrupted_intake`; (b) no fsync barrier → never-persisted + `delta_pre_fsync_lost` (retryable); (c) WAL empty → operator timeout governs retry. Substrate MUST NOT silently complete partial delta on restart (P6).

---

## §5. Quarantine sub-state of alive

Entry triggers: cold-resume invariant failure (§3.1.a / C9); CRITICAL skin breach (L1/HARD_RULES C1/C2/C3/C4/C11); sustained I3 failure (≥ threshold consecutive cycles); owner CI command; sustained cycle-backlog past saturation-threshold (§1.3 + C36); snapshot integrity violation (L1/SCHEMA §6.3 + C38) → discard snapshot + full DAG replay; replay fails → quarantine.

Quarantine metabolism: cycle continues at alive cadence; tier-1 invariants run; intake closed except owner admin; sporocarp fruiting continues (diagnostic/immune); federation outputs suspended. Exit: owner-attested `quarantine_clearance`.

Distinction from **legacy** (L1/GOVERNANCE §3.2): legacy = owner unavailable + L0/L1 mutations frozen; quarantined = internal pathology + intake closed + federation suspended + mutations gated. May be both; recovery requires owner-equivalent attestation + quarantine clearance.

## §6. Lifecycle regime cross-cut

> Cross-cuts L0 I1 / P7 / P8 + L1/GOVERNANCE §3-§4 + L1/SKIN §4.5 + L1/TROPISM §4 + L2/TRUST_MODEL §2. Numeric thresholds L1-tunable unless specified. Regime view of states this doc operationalizes.

**§6.1 State space + alive sub-states (L0 I1)** — `genesis → alive ⇄ dormant → destroyed (terminal; anchor final seal)`. `alive` sub-states (compositional): **normal**; **birth-period** (CI-elevation); **quarantined** (§5; intake closed); **legacy** (L1/GOVERNANCE §3.2; heartbeat stale; mutations frozen); **orphaned** (legacy_window elapsed without `succession_acceptance_attestation`); **archived** (terminal-non-destroyed via §6.4 / L0/cards/LB_living_bets.md §4 (retirement); state_dir + anchor-seal preserved); **saturated** (compression-insufficient per P11.c).

**§6.2 Genesis + birth period + steady** — Genesis: L1/GOVERNANCE §4.1 + L2/TRUST_MODEL §2; sporocarp lands → `alive (birth-period)`. Birth period (L1/TROPISM §4 + L1/GOVERNANCE §1.3; all parameter-tuning CI; reclassification at owner-attested termination):
- **Path A (convergence-attested)**: ≥N sporocarps + ≥M active-operation time + per-axis convergence below epsilon → `birth_period_complete_proposal` + owner co-attest → `alive (steady-state)` + `maturity_attestation`.
- **Path B (max-duration ceiling)**: default 180 active-operation days; forces graduation OR `self_euthanasia_proposal` (attention-exhaustion safety valve).
- **Observability**: signal #2 HIGH, #3 RISING, #10 variance-weighted (L2/OBSERVABILITY §2.3) until P14 lands.

Steady state: emergent thresholds replace seeds; 5-step metabolic cycle (§1.1); Living Bets baselines build; falsifiability quorum arms (90-day rolling); L0/L1 evolutions follow P3 CI-attested.

**§6.3 Legacy / orphaned / archived vocabulary** — Per L1/GOVERNANCE §3.2 + L0/cards/COV06_no_abandonment_succession.md (cultivator mortality) (Cultivator mortality) + §7.5 (bet-retirement): `succession_acceptance_attestation`, `legacy_window` (default 365 days), `orphaned_terminal_window` (default 730 days), `cultivation_orphaned_terminal_choice` (genesis pre-attested ∈ {self_euthanasia | bet_retirement | indefinite_orphan}). Sub-states remain alive (substrate-ID + DAG preserved); may overlap quarantined.

**§6.4 Reproduction (P8)** — L1/GOVERNANCE §4.3 + §16 (generation discipline F22) + L1/SCHEMA §3.3; inter-substrate L2/FEDERATION. Modes: federation (semantic), cloning (full copy), cross-pollination (multi-parent, L1-deferred). Each child runs own complete lifecycle from own genesis; recursive under generation-limit. Child-substrate-ID Cultivator-minted at anchor (not parent-minted; F2 + L1/GOVERNANCE §4.1).

**§6.5 Mortality (alive → destroyed; terminal)** — L0 P7 + L1/GOVERNANCE §4.4. Three modes: intentional-Cultivator, catastrophic-environment, endogenous-pair dual-channel. Mortality-axis F7: threshold + update-rule + emergence-rule all CI. Endogenous dual-channel: substrate emits `self_euthanasia_proposal` with `operator_witness`; anchor emits `mortality_drill_failure` on two consecutive failed drills. Terminal record: `anchor_surface_final_seal` Cultivator-co-signed; post-destruction handshakes return `substrate_destroyed`; seal substrate-ID-scoped. Alternative terminal: `alive::archived` via L0/cards/LB_living_bets.md §4 (retirement) / §6.3 preserves state_dir (substrate-ID does not re-bind).

**§6.6 Lifecycle sporocarp index** — Auditable life-trail: `genesis_event`; `birth_period_complete_proposal` / `maturity_attestation` / `birth_period_max_reached`; `dormancy_enter` / `dormancy_exit`; `cold_resume_quarantine` / `quarantine_clearance`; `succession_required` / `succession_acceptance_attestation` / `cultivation_recovered`; `reproduction_request` / `genesis_attested`; `bet_retired_proposal` / `endogenous_mortality_proposal:cultivation_orphaned_terminal`; `destruction_attestation` / `mortality_drill_failure` / `self_euthanasia_proposal`; `anchor_surface_final_seal` (terminal for `destroyed`; also `alive::archived` per L0/cards/LB_living_bets.md §4 (retirement).c).

---

## §7. C-row catalog

Full catalog at L1/HARD_RULES §1/§2; detection sites: **C9** (§3.1.a) / **C19** (§2.4 + §3) / **C36** (§1.3) / `interrupted_intake` sub-grade (§4).
