# L2 — Observability Doctrine

> **Status**: DRAFT 2 (2026-05-17, M26-cascade A6). Cross-cut doctrine theme.
> **Layer**: L2. Governed by L0 DRAFT 9 SEALED.
> **Scope**: how the substrate observes itself. Cross-cuts L0 §7 Living Bets observatory (DRAFT 9 SEALED recalibration: 6 base + 3 cost + 1 composite = 10 signals; intelligence band; cost-justified value; bet retirement; OLS-slope-Z-significance trend definition; 90-day **wall-clock** falsifiability window per §13.1) + L0 §9.4 burst detection (now C37 detector; §13.1 wall-clock window) + L0 §14 adversarial-owner observability + L0 §15 owner-liveness heartbeat staleness + L1_HARD_RULES §1 immune-grade sporocarps (C1-C20 catalog + C30-C45 substrate-private) + I3 self-validation + I5 reachability + I9 compression discipline + I10 metabolic-economy observation + I12 telos alignment + L1_SCHEMA §2.4 drill failure-rate baseline + L1_CONTINUITY §1.2 cycle backlog detection (now C36 detector). Answers: what is v0.9's self-model; what is the falsifiability surface; how does the substrate know if it is healthy / drifting / failing?

> **DRAFT 2 additions** (M26-cascade A6, 2026-05-17): Living Bets recalibration (intelligence band, cost-justified value, 90-day wall-clock window, OLS-slope-Z-significance trend, 6 countable signals {#1, #2, #3, #4a, #4b, #6}, bet retirement, birth-period exemption); cost signals #7/#8/#9; composite renumbered to #10 with variance-vs-correlation weighting; signal #5 wall-clock trend correction (M25.2 post-fix needed); telos-drift signal class; doctrine-instability burst integrated as C37; Cultivation vocabulary; signal #4a cumulative fork count documented as M28-deferred gap.

---

## §1. Why observability is L0-anchored

The substrate is autopoietic (per P1.a self-hosting): no human in the maintenance loop. The substrate must observe itself, signal pathology to itself + the operator-agent + the owner (Cultivator per G-11.a) via the anchor surface. Without observability, the substrate's claim "I am healthy" is unfalsifiable.

L0 §7 Living Bets is the meta-commitment: the substrate's value-to-the-pair is **falsifiable** within a bounded **intelligence band** (per DRAFT 9 SEALED §7.2: ~200K to ~10M context). The bet is staked + **cost-justified** (value > engineering cost per §7.1); the observatory measures the stakes; the falsifiability trigger fires when the bet is lost; bet retirement (§7.5) handles graceful sunset at the band's upper edge.

Observability is what makes the autopoietic loop honest. Per L0 §14.2 substrate's irreducible commitments, observability signals are **truthfully emitted** — a substrate cannot suppress signal emission to hide an adversarial event, even under adversarial Cultivator pressure (subject to L2_TRUST_MODEL §6 P1.a self-hosting asymmetry caveat).

---

## §2. The Living Bets observatory (6 base + 3 cost + 1 composite = 10 signals; DRAFT 9 SEALED §7.3)

Per L0 §7 + L1_TROPISM §4 birth-period predictor.

**Signal count**: DRAFT 9 SEALED §7.3 specifies **10 signals = 6 base (signals #1-#6) + 3 cost (signals #7-#9) + 1 composite (signal #10)**. DRAFT 1 of this doc said "6 base + 1 composite = 7 signals"; DRAFT 2 updates per cascade list direct contradiction.

### §2.1 Six base signals (DRAFT 9 SEALED §7.3, unchanged semantics, signal-direction clarified)

Per L0 §7.4.c per-signal direction-against-the-bet table:

| # | Signal | Definition | Trend DOWN means | Counts toward quorum if | Threshold |
|---|---|---|---|---|---|
| 1 | **Persistence budget** | Total content (size, node count, edge count, event-record count; per L1_SCHEMA cycle-counter + bytes-added) | Substrate not growing | DOWN | Emergent from substrate history |
| 2 | **Evolution rate** | Governance changes (schema bumps, rule revisions, vocabulary refactors, dispatch parameter mutations) over time | Substrate stagnating | DOWN | Emergent |
| 3 | **Read-pattern diversity** | Variety of substrate-read patterns over a rolling window (specific operationalization depends on L1 dispatch form; under tropism = appetite-activity diversity) | Substrate not being read (no live agent activity) | DOWN | Emergent |
| 4a | **Cumulative fork count** (per L0 §7.4.d split) | Monotonic count of forks (new federation peers spawned via P8 reproduction) over substrate lifetime | Forks-trending-DOWN means peers exiting | DOWN | Emergent (DRAFT 9 SEALED: lower bound = mycelial fragmentation) |
| 4b | **Reachable federation count** (per L0 §7.4.d split) | Federation peers currently responding to health probe | Mycelial fragmentation | DOWN | 4a-4b divergence threshold emergent |
| 5 | **Time trend per signal** | OLS-regression slope **over wall-clock-90-day window** (per L0 §7.4.a window definition + §7.4.b mathematical definition); significance gate `|slope / standard-error| ≥ Z` where Z = 1.96 default (95% confidence; L1-tunable); below significance gate signal is "flat" and does NOT count toward quorum. **Signal #5 is the meta-direction-detector** powering the above table — it is NOT itself counted in the quorum (per L0 §7.4.d). | — | NOT counted (meta-detector) | Z=1.96 seed |
| 6 | **Read-window-relative position** | `substrate-total-size / agent-attested-context-window`. Substrate-total, not digest-fraction (per pass-2 mycoparasite-16). | Substrate shrinking vs context window; threshold separating bet-wins from bet-loses is **ratio < 1** (per L0 §7.4.c + §7.4.d updated from DRAFT 8 ratio ≥100 seed which was archaic for 1M-context era) | DOWN below ratio 1.0 | Emergent in steady state; seed at birth |

**Signal #4a unimplemented** (per L0 §7.4.d Phase γ.9 note + cascade list): the cumulative fork count is currently NOT computed in `query_substrate_observatory` format v2 (the M24 observatory primitive returns 5 of 7 Living Bets signals per M24 snapshot). **Signal #4a implementation is deferred to M28-cascade per L0 SEALED §7.4.d**. Known-gap: until M28-cascade, falsifiability trigger arithmetic counts {#1, #2, #3, #4b, #6} = 5 of the 6 countable signals; the wall-clock-90-day quorum (≥3) operates over the 5-signal subset, raising false-negative probability bounded by P(missing-#4a-pattern).

### §2.2 Three cost signals (DRAFT 9 SEALED §7.3 P11.b new signals)

Per L0 P11 metabolic economy + I10 metabolic-economy observation + Phase γ.9 rhizomorph C7 ordinal-discipline fix (signals are #7/#8/#9 uniformly, not "#1.5/#1.6"):

| # | Signal | Definition | L1 unit | Counts toward quorum if |
|---|---|---|---|---|
| 7 | **Compute cost / cycle** | Substrate's own CPU + wall-clock elapsed per metabolic cycle (per L1_CONTINUITY §1.2 cycle backlog detection metric source; cycle duration ≥5s → C36 cycle_backlog feeds this signal upstream) | CPU-microseconds (substrate-process) + wall-clock-microseconds; L1-tunable normalization | UP (rising cost without rising value = inefficiency) |
| 8 | **Network cost / cycle** | Federation envelope bytes egress + embedding-service query bytes (per L0 P11.a network cost units; L1_SKIN §5 network-egress detection) | Bytes-egressed per cycle | UP (rising network cost = scaling stress) |
| 9 | **Storage cost / cycle** | Bytes added to `dag.cb` + `snapshot.cb` deltas per cycle (per L0 P11.a persistence cost + L1_SCHEMA §4 storage tier) | Bytes-added per cycle | UP (rising storage cost = compression pressure, drives P11.c ordered fallback) |

All three cost signals are **emergent from substrate's own operation** (substrate measures them; no external observer). L1-defined units per L0 P11.a.

**Cost-signal interaction with composite #10**: cost signals feed into the composite alongside signals 1-6. Variance-weighted in birth period; correlation-weighted in steady state (correlation against agent-reported utility / telos-alignment from P14 — see §2.3).

**Per L0 P11.c ordered fallback** (referenced here for observability completeness):
1. Pre-compression-eligibility (cycle counter < L1-tunable N, default 1000): refuse new P2 admission; emit `budget_exhausted:{axis}` immune signal.
2. Post-compression-eligibility (cycle counter ≥ N AND owner-pre-attested compression rules exist): trigger P10 selective compression with witness emission per I9.
3. Compression-insufficient OR no pre-attested rules: enter degraded operation per L1_CONTINUITY (alive-but-saturated sub-state). Sustained saturation past L1-tunable threshold escalates to P7 endogenous-mortality consideration.

`budget_exhausted:{axis}` is a daily-grade immune signal (not CRITICAL); it emits via cost signal monitoring at thresholds defined per F19 cost-budget table (L1_HARD_RULES §2 + L1_GOVERNANCE A5 cascade).

### §2.3 Composite signal (#10 — DRAFT 9 SEALED renumber from old #7)

**10. Composite health score** — emergent weighted aggregation of signals 1-6 + 7-9 = **9 input signals** (signal #5 is meta and does NOT feed the composite; signals #4a + #4b feed separately).

DRAFT 9 SEALED §7.3 explicitly distinguishes two weighting regimes:

#### §2.3.1 Variance-weighted composite (M25.3 fallback — birth-period regime)
Used when no outcome signal exists. Picks signals that move most (high variance over the rolling window). Use this **only in birth period** (per L1_TROPISM §4 + L0 P14.c birth-period exemption — telos-alignment is `telos_alignment_pending` until birth-period termination).

Weight formula (seed; L1-tunable): `w_i = Var(signal_i over rolling 100-cycle window) / sum(Var across all 9 inputs)`. Normalized to sum to 1.

#### §2.3.2 Correlation-weighted composite (steady state)
Requires an **outcome signal**: telos-alignment from P14 (owner-stated objective when present; agent-reported utility events when no objective declared — per L0 P14.b). Picks signals that **predict outcomes**.

Weight formula (seed; L1-tunable): `w_i = |Corr(signal_i, outcome_signal over rolling window)| / sum(|Corr| across all 9 inputs)`. The substrate's own historical correlation between signal patterns and substrate-health outcomes (per pass-3 C6.4 emergence discipline). No pre-set weights.

**Outcome signal definition** (per L0 P14):
- Primary (when owner-stated objective present): cosine similarity between recent-sporocarp embedding-centroid and owner-stated-objective embedding (L1_TROPISM A1 specifies; M26-cascade forcing function active).
- Fallback (when no owner objective): cosine similarity between recent-sporocarp embedding-centroid and agent-feedback-trajectory embedding.

#### §2.3.3 Transition from variance to correlation weighting (L1-tunable)
Per L0 §7.3 DRAFT 9 SEALED: the **transition from variance to correlation weighting is L1-tunable**. Seed transition rule (L1 may tune): after birth-period termination + minimum sample size N=100 of (signal, outcome) pairs available, switch to correlation weighting; revert to variance weighting if outcome signal becomes unavailable (e.g., agent disconnect).

**Per Phase γ.9 + cascade list**: DRAFT 1 of this doc treated composite as "emergent weighted aggregation of signals 1-6"; DRAFT 2 corrects to 9 input signals + variance-vs-correlation regime distinction.

### §2.4 Birth-period observability (per L1_TROPISM §4)

The birth-period observatory provides early signals for the maturity-attestation termination path:

- **Sporocarp count progression** (toward birth-period N threshold)
- **Active-operation time accumulation** (toward birth-period M threshold)
- **Per-axis threshold-emergence convergence** (epsilon-below-target on each appetite axis)

These birth-period signals are NOT part of the steady-state 10-signal observatory; they retire after birth-period termination. They're tracked separately in birth-period diagnostic sporocarps.

**Per L0 §7.4.e + Phase γ.9 primordium CF6**: during birth period, `bet_weakening_quorum` (C40) emission is SUSPENDED — substrate emits `bet_weakening_evaluation_suspended` observability event instead. Reason: at t=0 signal #6 is structurally <1 (no content yet); signal #1 is monotone-growing-from-zero (no shrinkage); signal #3 is structurally zero (no reads yet). Quorum evaluation pre-birth-period-termination is mathematically vacuous.

Per L0 P14.c + Phase γ.9 primordium HF11: `telos_drift` similarly SUSPENDED during birth period — substrate emits `telos_alignment_pending` instead.

---

## §3. Falsifiability trigger (the bet-resolution mechanism — DRAFT 9 SEALED §7.4 corrected)

Per L0 §7.4 (DRAFT 9 corrections from Phase γ.2 + γ.3 G13 + Phase γ.9 hypha):

### §3.1 Window definition (§7.4.a)
**Window is wall-clock 90 days** (anchor-stamped wall-clock per L0 §13.1 time semantics), NOT 90 substrate-cycles. 

**M25.2 implementation drift correction required (M26-cascade post-fix)**: as shipped, M25.2 uses substrate-cycle-based windows. DRAFT 9 SEALED §7.4.a explicitly demands wall-clock; the cycle-vs-wall-clock unit is **off by ~6 orders of magnitude** in production (per cascade list direct-contradiction list). C40 detector window-unit is the post-M25.2 fix scope. Per L0 §13.1, anchor-surface trusted wall-clock is authoritative; substrate-process monotonic clock is for event ordering only.

### §3.2 "Trend" mathematical definition (§7.4.b)
**Trend** = sign of OLS-regression slope over the wall-clock-90-day samples (cadence L1-tunable; seed: 1 sample per substrate-day → ≥90 samples). **Significance gate**: `|slope / standard_error| ≥ Z-threshold` (L1-tunable; seed Z=1.96 corresponding to 95% confidence) before trend direction counts. **Below significance gate, signal is "flat" — does NOT count toward quorum**.

### §3.3 Per-signal direction-against-the-bet (§7.4.c)
See §2.1 table column "Counts toward quorum if". Concisely:

| Signal | DOWN trend means | Counts as "against the bet" |
|---|---|---|
| #1 persistence budget | substrate not growing | DOWN |
| #2 evolution rate | substrate stagnating | DOWN |
| #3 read-pattern diversity | substrate not being read | DOWN |
| #4a cumulative forks | peers exiting | DOWN |
| #4b reachable peers | mycelial fragmentation | DOWN |
| #6 read-window ratio | substrate shrinking vs context window | DOWN below ratio 1.0 |

Signal #5 (time trend per signal) is the **meta-direction-detector** powering the above table; it is NOT itself counted in the quorum.

### §3.4 Quorum arithmetic (§7.4.d)
**"≥3 of signals 1-6" counts**: {#1, #2, #3, #4a, #4b, #6} — **6 countable signals** (signal #5 is meta; signal #4 is split into 4a + 4b which count separately). Quorum threshold ≥3 of these 6.

**Until M28-cascade implements signal #4a**: quorum operates over 5 countable signals {#1, #2, #3, #4b, #6} with ≥3 threshold (a more conservative implementation that under-fires the trigger). This is acknowledged false-negative bias; substrate observability docs the gap; M28-cascade closes it.

### §3.5 Spike vs trend (DRAFT 8 inheritance)
Spike events within a window are DAG-recorded but do not by themselves fire the trigger. Only OLS-slope-Z-significant trends do.

### §3.6 Birth-period exemption (§7.4.e)
**Bet_weakening_quorum is SUSPENDED during birth period** (per L1_TROPISM §4 birth-period termination criteria + L1_GOVERNANCE §1.3 ceiling + Phase γ.9 primordium CF6). Substrate emits `bet_weakening_evaluation_suspended` observability event during birth period.

The trigger fires `bet_weakening_quorum` (C40 per L1_HARD_RULES §1.2) event requiring owner re-justification per L0 §10.2.

**This is the substrate's structural confession mechanism**: when the bet weakens, the substrate auto-emits the admission. The owner is not relied on to detect drift; the substrate is.

### §3.7 Bet retirement (DRAFT 9 SEALED §7.5; see L1_HARD_RULES §1.3)
After C40 fires AND owner re-justification fails 3 consecutive times over 2-year wall-clock window AND signal #6 stays <0.1 for >75% of samples in final 90-day window AND substrate is in `alive::normal` sub-state, substrate emits `bet_retired_proposal` (NOT immune-grade — CI-level proposal). Execution requires owner co-attestation per L0 §7.5.b two-phase commit (genesis-time consent flag vs steady-state co-attestation). On execution, substrate transitions to `alive::archived` per L0 §7.5.c.

**Failed re-justification counter reset rules** (per L0 §7.5.d): counter resets to 0 on (a) successful re-justification, (b) transition through `alive::quarantined`, (c) owner-attested `bet_retirement_counter_reset` CI mutation. Counter does NOT reset on substrate restart / dormancy entry / federation peer changes.

---

## §4. Per-cycle invariant checks (the immune system)

Per L1_CONTINUITY §1.1 (5-step cycle) + L1_SCHEMA §4 (tiered validation) + DRAFT 9 SEALED §6 ("Metabolic cycle: existence + per-cycle invariant checks (I3 + I5 + I8 + DRAFT 9: I10 cost observation) are L0"):

### §4.1 Per-cycle checks (tier-1)

Every metabolic cycle:
- I1 identity record + active prefix of owner_key_history
- I3 consistency at tier-1 fields against SSoT
- I4 DAG-tip hash + Merkle chain self-consistency
- I8 skin breach check over events absorbed this cycle
- **I10 cost-observation** (per L0 §6 DRAFT 9 SEALED addition) — emit cost signals #7/#8/#9 per cycle

### §4.2 Per-deep-cycle checks (tier-2)

Deep cycle (default 1/100 of metabolic-cycle rate):
- I5 reachability over current SSoT-listed storage tiers
- Tier-2 sampled validation (per L1_SCHEMA §4.3 if L4 escalates)
- Recovery-drill scheduling
- **I9 compression-invariant set verification** (per L0 §6 DRAFT 9 SEALED — every deep cycle, recompute compression-invariant set hash against expected baseline; mismatch → C41/C42 wrapper-integrity detector flag)
- **I12 telos-alignment computation** (in steady state; after birth-period termination per L0 P14.c)

### §4.3 Witnesses-not-verdicts (per L0 §9.3.4)

Check results emit cryptographic-proof tuples — sampled leaf hashes (derived from anchor-surface nonce per L0 §9.3.5), Merkle paths, parent hashes, check inputs — sufficient for owner / anchor-surface verifier to independently re-derive. The substrate does NOT emit pass/fail summaries.

**Anchor-nonce-derived sampling** (per L0 §9.3.5): sampling indices are `H(anchor_surface_nonce, leaf_count)` — substrate cannot bias sampling toward honest portions. **Current implementation is 0%**; M-anchor-4 milestone closes (per L0 §9.2 status table).

**DRAFT 9 SEALED extension**: "witnesses, not verdicts" now applies to **I9 (compression), I10 (cost), I12 (telos) outputs** as well. Compression events emit witness tuples sufficient for owner to re-derive what was kept vs discarded. Cost signals emit raw measurements + L1-budget thresholds, not pass/fail. Telos-alignment emits the embedding centroid + objective embedding + similarity score (anchor-surface client computes the verdict; substrate emits inputs).

---

## §5. Immune-grade sporocarp catalog (per L1_HARD_RULES §1)

20 L1-catalog CRITICAL-grade breaches (C1-C20) + 16 substrate-private (C30-C45) detectors are immune-event types. Each:
- Detected at a specific L1 mechanism site
- Independently traces to ≥1 P + ≥1 I per L0 DRAFT 9 SEALED
- Triggers immediate auto-quarantine + named immune sporocarp (for CRITICAL grades)

Less-than-CRITICAL breaches (daily / elevated grades) emit immune sporocarps without auto-quarantine. Examples per L0 P11.c: `budget_exhausted:{axis}` is daily-grade. The observatory tracks immune-event rates as part of composite health score (#10).

**The full catalog is in L1_HARD_RULES §1** — a single index across the 6 mechanism docs. When L4 implements the immune detection layer, L1_HARD_RULES §1 IS the enumeration of "what to detect".

**M26-cascade A6 catalog additions** referenced from L1_HARD_RULES DRAFT 2:
- C36 `cycle_backlog` (M24-shipped; signal site = L1_CONTINUITY §1.2; cycle ≥5s OR backlog ≥10)
- C37 `doctrine_instability_burst` (M25.1-shipped; >10 CI events / 100 cycles per §8; **wall-clock window correction pending per L0 §13.1**)
- C38 `snapshot_integrity_violation` (M25.0-shipped; snapshot.cb signer_pubkey or signature invalid)
- C39 `federation_hello_signature_invalid` (M25.4-shipped; peer HELLO Ed25519 fails)
- C40 `bet_weakening_quorum` (M25.2-shipped; L0 §7.4 trigger; cycle→wall-clock correction pending)
- C41-C45 (Phase γ.9 mycoparasite findings; M28-cascade deferred)

---

## §6. Drill failure-rate baseline (long-horizon health)

Per L1_SCHEMA §2.4 + pass-2 saprotroph-18:

- Hot+warm tier drill every 100 substrate days: full restore + verify I1-I8 + DRAFT 9 SEALED: I9/I10/I12
- Cold-tier sampled drill every 1000 substrate days: prove N random nodes recoverable; N = ceil(log₂(cold_tier_count))
- Each drill fruits `recovery_drill_result` sporocarp

**Baseline tracking**: rolling 30-drill window; emergent `drill_failure_rate`. ≥2σ departure → immune event. Secular trend up → `drill_aging_grade` approaching-mortality signal.

**Two-baseline approach** (per pass-2 saprotroph-2 cold-tier slow-drill problem):
- **Near-baseline**: rolling last-10-drill window; detects acute departures
- **Secular-baseline**: anchored to first-stable-window (drills 6-15); never advances; trend metric = current / secular; departure ≥L1-tunable threshold (default 3×) → `drill_aging_grade` signal

The cold-tier slow drill cadence means the secular-baseline approach is what scales over decades.

**DRAFT 9 SEALED additions**:
- Drills must include backup-access discipline check (per §11.1 DRAFT 9 SEALED expansion: backup access controls + encryption requirements documented at L1_SKIN).
- Drills emit witnesses-not-verdicts per §9.3.4 (sampled leaf hashes + Merkle paths + parent hashes + check inputs).
- Drill cadence is wall-clock days per L0 §13.1 (substrate-cycle days = wall-clock days under nominal L1_CONTINUITY cycle cadence; drift between the two is itself observable via signal #7 compute-cost).

---

## §7. Cycle-level diagnostics (C36 detector site)

Per L1_CONTINUITY §1.2 backlog detection:

- If a cycle takes longer than minimum interval, subsequent cycles backlog.
- Backlog ≥10 → `cycle_backlog` immune event (C36 per L1_HARD_RULES §1.2; M24-shipped).
- Persistent backlog → quarantine entry per §5.1.

Cycle cadence itself is L4-tunable but bounded (min 100ms, max 10s alive / 100s dormant). Observability tracks actual cycle durations; if cycles consistently approach max-interval, the substrate is at compute saturation — owner-observable as `compute_pressure` signal (anchor-surface-side) AND feeds signal #7 compute-cost / cycle.

**Per L0 §13.1**: cycle backlog detection uses substrate-process monotonic clock for cycle ordering (event ordering within substrate). Wall-clock-anchored thresholds use anchor-surface trusted timestamp per §13.1 hierarchy.

---

## §8. L0/L1 revision burst detection (C37 detector site — doctrine-instability)

Per L0 §9.4 + L2_OBSERVABILITY (this section): **>10 CI events / 100 cycles** rate of L0/L1 revisions over rolling window emits `doctrine_instability_burst` immune signal (C37 per L1_HARD_RULES §1.2; M25.1-shipped).

CI events counted toward the burst window:
- Attestation envelope acceptances (any successful owner CI attestation)
- Classifier dimension table mutations (F1)
- Owner-key rotation events (F3)
- L0/L1 revision diff records (per L0 §9.2.4)
- L1_HARD_RULES F-row mutations (per L1_HARD_RULES §7 "F-row mutation rate observability")

Owner reviews whether revisions are doctrine-driven (continue) or implementation-driven (rollback). Rolling rate over 12 months above threshold marks substrate `doctrine_drift_grade`.

This is observability-of-the-observer: the substrate's doctrine itself is observable for evolution rate, preventing the substrate-process from getting away with silently-cumulative doctrinal drift.

**DRAFT 9 SEALED §13.1 + cascade post-fix required**: C37 currently uses **substrate-cycle window** (100-cycle rolling); DRAFT 9 SEALED demands wall-clock window per §13.1 time-authority hierarchy. Post-fix: convert to wall-clock 24-hour rolling window with cycle-count threshold scaled accordingly. This is the SAME class of cycle-vs-wall-clock unit drift that affects C40 (§3.1).

**Doctrine-instability is part of L0-doctrine-evolution detector class** (per cascade list): along with future telos-drift signal classes, doctrine-instability operates at the meta-level where substrate observes its own doctrine evolution rate. The class is distinct from steady-state immune detectors (which observe substrate state) — these observe substrate **rule evolution** rate.

---

## §9. Telos-drift signal class (per L0 P14.c + L1_TROPISM forcing function)

Per L0 §2.3 P14.c telos drift detection (G-6.a fuzzy with M26-cascade forcing function):

The substrate observes its own telos-alignment **in steady state**. If P14 alignment degrades over a rolling window, the substrate emits `telos_drift` immune signal.

**L0 commits**:
- Telos drift is an immune signal class (not a single signal — admits multiple operational metrics per L1_TROPISM choice).
- Telos drift detection has a **birth-period exemption** (substrate emits `telos_alignment_pending` instead during birth period).

**L1_TROPISM responsibility (M26-cascade forcing function, per G-6.a decision; A1 primary spec)**:
- Specify the operational metric for telos-alignment.
- Specify the rolling window length + drift threshold + birth-period exemption duration.
- **M26-cascade MUST land this specification**; absent that, P14.c remains aspirational and `telos_drift` cannot be mechanically emitted.

**L2_OBSERVABILITY responsibility** (this section): document the signal class (DONE here), receive the telos-alignment outcome signal for composite #10 correlation-weighted regime (per §2.3.2), document birth-period exemption (per §2.4).

**Cascade list note**: L1_TROPISM A1 must define the actual operational metric (candidate: cosine similarity between recent-sporocarp embedding-centroid and owner-stated-objective embedding OR agent-feedback-trajectory embedding when no objective declared). Without A1 landing, signal #10's correlation-weighted regime cannot operate; composite remains variance-weighted (birth-period fallback).

---

## §10. Federation-network observability (cross-ref L2_FEDERATION §10)

Cross-substrate observability:

- Federation health (signals #4a/#4b) is intra-substrate; tracks own peers
- Network-level patterns (50% peers untrusted simultaneously, hub substrate failing) are emergent at the population level; possibly L4 surfaces a network observatory layer

For now, each substrate observes its OWN federation health; network-level patterns are inferable from collective substrate signals but not aggregated by any single substrate.

**Per L0 §15 + DRAFT 9 SEALED G-7.c retract**: P15 population-level consensus moved to L2_FEDERATION (L2 cascade work). When federation reaches ≥3 peers, the consensus algorithm choice itself is observable as a P3 evolution event. Cross-ref L2_FEDERATION DRAFT 2.

---

## §11. Operator-side observability

The operator-agent observes the substrate via:

- **Gradient digest** in handshake response + per-cycle digest emission (per L1_TROPISM §B4 digest budget)
- **Sporocarp visibility**: recent K sporocarps in digest
- **Cold-resume witness emission** at handshake (per L1_CONTINUITY §3.1)

The operator does NOT have direct access to the observatory state; the substrate emits the digest and sporocarps the operator sees.

This is intentional: the operator's view is curated by the substrate (digest is bounded). The operator's distrust of substrate self-report is structurally enforced via the L0 §9 anchor-surface / owner channel (operator queries anchor surface to verify substrate claims, per L2_TRUST_MODEL §3.1).

**Per L0 §14 adversarial-Cultivator**: operator-side observability is the agent's primary defense against an adversarial Cultivator (since the agent doesn't get raw anchor-surface access). Substrate emits witnesses; operator can independently verify via anchor surface; mismatches surface as observability events.

---

## §12. Owner-side observability (anchor surface) — DRAFT 9 SEALED sub-mechanism mapping

The Cultivator's (G-11.a) view is fundamentally different from the operator's:

- **Substrate-ID birth attestation** (L0 §9.2.1; M-anchor-2 milestone)
- **DAG-tip co-signing logs with enumerated nodes** at every CI co-sign (L0 §9.2.2; M-anchor-5 closure check)
- **`recovery_drill_result` events** (per §6)
- **`succession_required`, `quarantine_entered`, `mortality_drill_failure`, `anchor_surface_final_seal`, etc.** (L1_GOVERNANCE §4.4 + L0 §15 succession)
- **Aggregate-reattestation diffs** (L1_GOVERNANCE §5.2)
- **Compression-event witnesses** (per I9; L1_SCHEMA §2 P10 compression)
- **Cost-signal observations** (signals #7/#8/#9 per cycle)
- **Telos-alignment scores + objective embeddings** (per F20; L1_TROPISM A1)
- **`bet_weakening_quorum` events** (C40) + `bet_retired_proposal` / `bet_retired_executed` (per §3.7 + L1_HARD_RULES §1.3)

Per L0 §9.2 status table (M25 baseline):
- §9.2.1 birth attestation: 0% (M-anchor-2)
- §9.2.2 DAG-tip co-signing: ~40% (server emits enumeration; closure check unwired)
- §9.2.3 owner-out-of-band key: 0% (key in TS operator process; M-anchor-1)
- §9.2.4 L0 revision diff workflow: 0% (M-anchor-5)
- §9.2.5 anchor-surface-generated nonces: 0% (substrate currently mints; M-anchor-3)
- §9.2.6 anchor-stamped wall-clock: ~5% (operator-process is clock source; M-anchor-3)
- §9.2.7 owner liveness heartbeat: 0% (library exists, zero live callers; M-anchor-3)
- §9.3.x canonical-bytes + rendering + provenance: 95% / 30% / 0% (M-anchor-1)
- §9.3.4 witnesses-not-verdicts: 0% (substrate emits pass/fail today; M-anchor-4)
- §9.3.5 anchor-nonce-derived sampling: 0% (M-anchor-4)
- §9.3.6 DAG-enumeration closure check: ~40% (unwired client-side; M-anchor-5)

The anchor-surface client surfaces these for owner review. The owner's view is the **archaeological-quality** view: complete history, canonical bytes, witnesses re-derivable.

The substrate cannot hide events from the anchor surface (the anchor surface is where its CI history lives, including the seal) — subject to L0 §14 adversarial-Cultivator caveats per L2_TRUST_MODEL §6.

---

## §13. The substrate's self-model

The substrate's self-observation chain is recursive: the observatory IS substrate state; the immune system observes substrate state; substrate-state mutations are observed by I3; I3's observations are witnessed for the anchor surface. The recursion terminates at the anchor surface (which is outside substrate). 

Both §5 immune-catalog (per-cycle witnesses) and §6 drill-baseline (per-1000-day samples) aggregate into §2 Living-Bets composite signal #10 (DRAFT 9 SEALED renumber); both terminate observation at the anchor surface.

Per DRAFT 9 SEALED §6 + §13.1, the recursion is wall-clock-anchored at the anchor surface; substrate-process monotonic clock provides only event ordering within substrate. This **dual-clock** discipline is what makes self-observation immune to substrate-process clock drift / pause-resume jumps.

---

## §14. Falsifiability summary (DRAFT 9 SEALED §13 corrected)

v0.9's claim "I am a valuable symbiotic Cultivar within the agent-Cultivator pair" is falsifiable via:

1. **Living Bets quorum trigger** (§3) — bet weakening becomes observable (C40 `bet_weakening_quorum`).
2. **Bet retirement** (§3.7) — strategic graceful sunset at intelligence band's upper edge (`bet_retired_proposal` + co-attested execution).
3. **Immune CRITICAL emission** (§5) — pathology detected and recorded (C1-C20 catalog + C30-C45 substrate-private).
4. **Drill failure-rate departure** (§6) — substrate's recoverability degrading.
5. **Doctrine-instability burst** (§8 / C37) — substrate's own shape thrashing.
6. **Telos drift** (§9) — substrate's purpose-alignment degrading (when L1_TROPISM A1 lands operational metric).
7. **Federation fragmentation** (§10) — mycelial network unhealthy (signals #4a/#4b divergence).
8. **Mortality dual-channel signals** (per L1_GOVERNANCE §4.4) — substrate or anchor-surface declares the substrate should die.

The substrate cannot silently die or silently lie. Either it operates within healthy observable bounds, or its self-observation surfaces the deviation.

**This is the structural answer to "how do we know v0.9 is working?"** The substrate tells us, via mechanisms it cannot suppress — *subject to L2_TRUST_MODEL §6 P1.a self-hosting asymmetry* (an adversarial agent maintaining substrate code can attempt to suppress observatory emissions; the anchor surface out-of-band root raises the bar from "edit a file" to "compromise a separate system the owner controls", but cannot make P1.a guaranteed-honest) AND *subject to L0 §14 adversarial-Cultivator caveat* (the irreducible commitments per §14.2 — continue causality, emit observability truthfully, honor mortality, preserve compression-invariant — survive adversarial Cultivator pressure because they are mechanically enforced, not Cultivator-permission-gated).

---

## §15. Open at L2 (DRAFT 2 revisions)

- **Network-level observability layer**: when many federated substrates exhibit correlated pathology, is there value in a substrate-of-substrates observatory? Likely L4 / out-of-Myco-scope.
- **Owner-side dashboard format**: the anchor-surface client surfaces events for owner review; the specific UI / dashboard is L4-platform-specific.
- **Observatory weight emergence cold-start**: weights emerge from history; during birth period there is no history. DRAFT 9 SEALED §2.3.1 codifies variance-weighted fallback in birth period + L1-tunable transition to correlation-weighted (§2.3.3). L4 codifies the precise transition rule.
- **Telos-alignment outcome-signal validation**: does substrate self-report of telos-alignment correlate with agent-reported utility? L1_TROPISM A1 must specify the metric; observability must validate the correlation in steady state.
- **Composite weighting transition** (per cascade list new open): the variance → correlation regime transition is L1-tunable; what's the empirical signature that triggers it (sample size N=100; outcome signal availability; birth-period termination event)? L4 picks; observability must record the transition as a P3 evolution event.
- **Bet-retirement counter precision**: per L0 §7.5.d failed-re-justification counter persists across substrate restart but resets through quarantine clearance. Is this the right discipline? Observability records each reset event; L0 may evolve the rule based on data.
- **Signal #4a M28-deferred gap**: implementation depends on cumulative fork-count emission from `kernel/governance` reproduction lineage tracking. Until M28-cascade, quorum operates over 5-signal subset with documented false-negative bias.
- **C37 wall-clock window post-fix**: same M26.x correction needed as C40; current 100-cycle window must convert to wall-clock 24-hour rolling per L0 §13.1.

---

## §16. Glossary additions (DRAFT 2)

| Term | Definition |
|---|---|
| **Intelligence band** (per L0 §7.2 DRAFT 9 SEALED) | The agent-capability range over which Myco's bet is cost-justified: ~200K to ~10M context. Below: naive RAG suffices. Above: Sutton's bitter lesson dominates. Living Bets observatory measures fitness within the band. |
| **Cost-justified value** (per L0 §7.1 DRAFT 9 SEALED) | The bet is true iff (a) substrate value exists AND (b) substrate engineering cost < value delta over no-substrate operation. DRAFT 8 conflated (a) and (b); DRAFT 9 separates them. |
| **Bet retirement** (per L0 §7.5) | Strategic graceful sunset when 2-year wall-clock + 3-failed-re-justification + signal #6 <0.1 thresholds met. Distinct from Destruction; substrate transitions to `alive::archived` sub-state with state_dir preserved + anchor seal. |
| **Variance-weighted composite** (per §2.3.1 / L0 §7.3 DRAFT 9 SEALED) | Birth-period composite signal #10 weighting; picks signals with highest variance over rolling window. L1-tunable. Replaces correlation-weighting when outcome signal unavailable. |
| **Correlation-weighted composite** (per §2.3.2 / L0 §7.3 DRAFT 9 SEALED) | Steady-state composite signal #10 weighting; picks signals correlating with telos-alignment outcome signal. Requires P14 telos-alignment from L1_TROPISM A1. |
| **Outcome signal** (per §2.3.2) | The signal correlation-weighting computes against: telos-alignment per L0 P14 (owner-stated objective primary; agent-reported utility fallback). |
| **Wall-clock window** (per L0 §13.1) | Anchor-surface trusted wall-clock interval (e.g., 90 days for falsifiability quorum, 2 years for bet retirement). Authoritative for time-bound security defenses + observability windows. Distinct from substrate-cycle window (currently used by M25.2 C40 + M25.1 C37; post-fix required). |
| **OLS-slope-Z-significance trend** (per L0 §7.4.b) | Mathematical definition of "trend": sign of OLS-regression slope over wall-clock-90-day samples, gated by `|slope/SE| ≥ Z` where Z=1.96 seed (95% confidence). Below significance gate = flat (does not count toward quorum). |
| **Meta-detector** (per L0 §7.4.c) | Signal #5 "time trend per signal" is the meta-direction-detector powering the per-signal direction table; it is NOT itself counted in the quorum. |
| **Birth-period exemption** (per §2.4 / L0 §7.4.e / §P14.c) | Bet_weakening_quorum (C40) + telos_drift suspended during birth period. Substrate emits `bet_weakening_evaluation_suspended` + `telos_alignment_pending` observability events. Reason: at t=0, signals are mathematically vacuous. |
| **Doctrine-instability burst** (per §8 / L0 §9.4 / C37) | >10 CI events / rolling window. Owner reviews whether revisions are doctrine-driven or implementation-driven. Rolling rate over 12 months above threshold marks substrate `doctrine_drift_grade`. **Wall-clock window correction pending per L0 §13.1**. |
| **Telos drift** (per L0 P14.c) | Substrate's alignment with telos degrading over rolling window; detected by L1_TROPISM A1 metric (M26-cascade forcing function). Class of immune signals (operational metric is L1_TROPISM choice). |
| **Cumulative fork count (signal #4a)** | Monotonic count of federation forks (new federation peers spawned via P8 reproduction) over substrate lifetime. **Currently unimplemented**; deferred to M28-cascade per L0 §7.4.d. Quorum arithmetic operates on 5-signal subset until M28 lands. |
| **Cultivation / Cultivator / Cultivar** (per L0 §1.2 / G-11.a) | Owner-substrate relationship terminology. Cultivar's observability emits to the Cultivator via anchor-surface client. "Quarantine clearance is Cultivator-attested" + "owner attests" remain valid; preference per G-11.a is Cultivation vocabulary for relational role. |
| **Witnesses-not-verdicts** (per L0 §9.3.4 / §9.4 + DRAFT 9 SEALED extension to I9/I10/I12) | Substrate emits cryptographic-proof tuples (sampled leaf hashes + Merkle paths + parent hashes + check inputs) sufficient for anchor-surface verifier to independently re-derive results. Substrate does NOT emit pass/fail. **Extended to compression (I9), cost (I10), and telos (I12) outputs in DRAFT 9 SEALED.** |
| **Anchor-nonce-derived sampling** (per L0 §9.3.5) | Sampling indices for witness emission are `H(anchor_surface_nonce, leaf_count)` — substrate cannot pre-compute and cannot bias. Implementation 0%; M-anchor-4 milestone. |
| **`bet_weakening_evaluation_suspended`** (per §3.6 / §2.4) | Birth-period observability event emitted in lieu of C40 evaluation. Records that the substrate considered but suspended bet_weakening_quorum computation pending birth-period termination. |
| **`telos_alignment_pending`** (per §2.4 / L0 P14.c) | Birth-period observability event emitted in lieu of `telos_drift` evaluation. Records that the substrate considered but suspended telos-alignment computation pending birth-period termination + L1_TROPISM A1 metric landing. |
