# L2 — Observability Doctrine

> **Status**: DRAFT 2 (2026-05-17, M26-cascade A6). Canonical for Living Bets signals + falsifiability quorum.
> **Scope**: L0 §7/§9.4/§14/§15 + L1_HARD_RULES §1 + I3/I5/I9/I10/I12 + L1_SCHEMA §2.4 + L1_CONTINUITY §1.2.

---

## §1. Why observability is L0-anchored

Substrate is autopoietic (P1.a); no human in maintenance loop. Without observability, "I am healthy" is unfalsifiable. L0 §7 Living Bets: substrate value-to-pair is **falsifiable** within bounded intelligence band (~200K to ~10M context); bet cost-justified (value > engineering cost); observatory measures stakes; trigger fires when bet lost; bet retirement (§7.5) handles graceful sunset. Per L0 §14.2 irreducible commitments: signals **truthfully emitted** — substrate cannot suppress emission to hide adversarial events (subject to L2_TRUST_MODEL §6 P1.a caveat).

---

## §2. The Living Bets observatory (10 signals; L0 §7.3)

Per L0 §7 + L1_TROPISM §4 birth-period predictor. **10 signals = 6 base + 3 cost + 1 composite**.

### §2.1 Six base signals (L0 §7.3; §7.4.c per-signal direction)

| # | Signal | Definition | Trend DOWN means | Counts toward quorum if | Threshold |
|---|---|---|---|---|---|
| 1 | **Persistence budget** | Total content (size, node count, edge count, event-record count; per L1_SCHEMA cycle-counter + bytes-added) | Substrate not growing | DOWN | Emergent from substrate history |
| 2 | **Evolution rate** | Governance changes (schema bumps, rule revisions, vocabulary refactors, dispatch parameter mutations) over time | Substrate stagnating | DOWN | Emergent |
| 3 | **Read-pattern diversity** | Variety of substrate-read patterns over a rolling window (specific operationalization depends on L1 dispatch form; under tropism = appetite-activity diversity) | Substrate not being read (no live agent activity) | DOWN | Emergent |
| 4a | **Cumulative fork count** (per L0 §7.4.d split) | Monotonic count of forks (new federation peers spawned via P8 reproduction) over substrate lifetime | Forks-trending-DOWN means peers exiting | DOWN | Emergent (DRAFT 9 SEALED: lower bound = mycelial fragmentation) |
| 4b | **Reachable federation count** (per L0 §7.4.d split) | Federation peers currently responding to health probe | Mycelial fragmentation | DOWN | 4a-4b divergence threshold emergent |
| 5 | **Time trend per signal** | OLS-regression slope **over wall-clock-90-day window** (per L0 §7.4.a window definition + §7.4.b mathematical definition); significance gate `|slope / standard-error| ≥ Z` where Z = 1.96 default (95% confidence; L1-tunable); below significance gate signal is "flat" and does NOT count toward quorum. **Signal #5 is the meta-direction-detector** powering the above table — it is NOT itself counted in the quorum (per L0 §7.4.d). | — | NOT counted (meta-detector) | Z=1.96 seed |
| 6 | **Read-window-relative position** | `substrate-total-size / agent-attested-context-window` (substrate-total, not digest-fraction). | Substrate shrinking vs context window; threshold separating bet-wins from bet-loses is **ratio < 1** (per L0 §7.4.c + §7.4.d) | DOWN below ratio 1.0 | Emergent in steady state; seed at birth |

**Signal #4a unimplemented** (L0 §7.4.d, M28-cascade deferred): not in `query_substrate_observatory` format v2 (M24 returns 5 of 7 Living Bets). Until M28: quorum operates over {#1, #2, #3, #4b, #6} = 5 of 6 countable signals; false-negative bounded by P(missing-#4a-pattern).

### §2.2 Three cost signals (L0 §7.3 P11.b)

Per L0 P11 + I10 observation:

| # | Signal | Definition | L1 unit | Counts toward quorum if |
|---|---|---|---|---|
| 7 | **Compute cost / cycle** | Substrate's own CPU + wall-clock elapsed per metabolic cycle (per L1_CONTINUITY §1.2 cycle backlog detection metric source; cycle duration ≥5s → C36 cycle_backlog feeds this signal upstream) | CPU-microseconds (substrate-process) + wall-clock-microseconds; L1-tunable normalization | UP (rising cost without rising value = inefficiency) |
| 8 | **Network cost / cycle** | Federation envelope bytes egress + embedding-service query bytes (per L0 P11.a network cost units; L1_SKIN §5 network-egress detection) | Bytes-egressed per cycle | UP (rising network cost = scaling stress) |
| 9 | **Storage cost / cycle** | Bytes added to `dag.cb` + `snapshot.cb` deltas per cycle (per L0 P11.a persistence cost + L1_SCHEMA §4 storage tier) | Bytes-added per cycle | UP (rising storage cost = compression pressure, drives P11.c ordered fallback) |

All three cost signals are emergent from substrate's own operation; L1-defined units per L0 P11.a. Feed composite #10 alongside signals 1-6 (variance-weighted in birth period; correlation-weighted in steady state).

**Per L0 P11.c ordered fallback**: (1) Pre-compression-eligibility (cycle < N, default 1000): refuse new P2; emit `budget_exhausted:{axis}` (daily, F19). (2) Post-eligibility (cycle ≥ N + owner-pre-attested rules): trigger P10 with I9 witness emission. (3) Compression-insufficient or no rules: degraded operation per L1_CONTINUITY (alive-but-saturated); sustained → P7 consideration.

### §2.3 Composite signal #10 (L0 §7.3)

Emergent weighted aggregation of 9 inputs (signals 1-6 + 7-9; #5 meta + #4a/#4b feed separately).

- **§2.3.1 Variance-weighted (birth-period)**: no outcome signal (per L1_TROPISM §4 + L0 P14.c: `telos_alignment_pending` until birth-period termination). Seed: `w_i = Var(signal_i over rolling 100-cycle) / sum(Var across 9)`; normalized.
- **§2.3.2 Correlation-weighted (steady state)**: outcome from P14 (primary: cosine similarity recent-sporocarp embedding-centroid vs owner-objective per L1_TROPISM A1; fallback: vs agent-feedback-trajectory). Seed: `w_i = |Corr(signal_i, outcome)| / sum(|Corr|)`.
- **§2.3.3 Transition**: L1-tunable; seed = post-birth-period + N=100 (signal, outcome) pairs → switch to correlation; revert to variance if outcome unavailable.

### §2.4 Birth-period observability (per L1_TROPISM §4)

Early signals for maturity-attestation termination (sporocarp count, active-operation time, per-axis threshold-emergence convergence). NOT part of steady-state 10-signal observatory; retires post-birth-period. Per L0 §7.4.e: C40 SUSPENDED (signals mathematically vacuous: #6<1, #1 monotone-growing, #3 zero) → emit `bet_weakening_evaluation_suspended`. Per P14.c: `telos_drift` similarly SUSPENDED → emit `telos_alignment_pending`.

---

## §3. Falsifiability trigger (per L0 §7.4)

- **§3.1 Window** (§7.4.a): wall-clock 90 days (anchor-stamped per L0 §13.1), NOT 90 substrate-cycles. M25.2 correction pending: as shipped uses cycle-based; cycle-vs-wall-clock off by ~6 orders of magnitude in production. C40 detector window-unit is post-M25.2 fix scope.
- **§3.2 Trend** (§7.4.b): sign of OLS-slope over wall-clock-90-day samples (cadence L1-tunable; seed 1/substrate-day → ≥90 samples). Significance gate `|slope/SE| ≥ Z` (seed Z=1.96, 95% confidence); below = flat (NOT counted).
- **§3.3 Per-signal direction-against-bet** (§7.4.c):

  | Signal | DOWN means | Counts |
  |---|---|---|
  | #1 persistence budget | not growing | DOWN |
  | #2 evolution rate | stagnating | DOWN |
  | #3 read-pattern diversity | not being read | DOWN |
  | #4a cumulative forks | peers exiting | DOWN |
  | #4b reachable peers | mycelial fragmentation | DOWN |
  | #6 read-window ratio | substrate shrinking vs context | DOWN <1.0 |

  Signal #5 meta-direction-detector; NOT counted.
- **§3.4 Quorum** (§7.4.d): ≥3 of 6 countable signals {#1, #2, #3, #4a, #4b, #6}. Until M28 implements #4a: quorum over 5 {#1, #2, #3, #4b, #6} with ≥3 threshold (conservative; documented false-negative bias).
- **§3.5 Spike vs trend**: spikes DAG-recorded but do not fire; only OLS-slope-Z-significant trends do.
- **§3.6 Birth-period exemption** (§7.4.e): C40 SUSPENDED in birth period (L1_TROPISM §4 + L1_GOVERNANCE §1.3); emit `bet_weakening_evaluation_suspended`. Trigger fires `bet_weakening_quorum` (C40) requiring owner re-justification per L0 §10.2 — substrate's structural confession mechanism.
- **§3.7 Bet retirement** (L0 §7.5; L1_HARD_RULES §1.3): C40 fires AND re-justification fails 3 consecutive times over 2-year wall-clock window AND signal #6 stays <0.1 for >75% of final-90-day samples AND substrate `alive::normal` → emit `bet_retired_proposal` (CI proposal); execution requires owner co-attestation (§7.5.b); on execution → `alive::archived` (§7.5.c). Counter resets (§7.5.d): on (a) successful re-justification, (b) `alive::quarantined` transit, (c) owner-attested `bet_retirement_counter_reset` CI. Does NOT reset on restart / dormancy / federation peer changes.

---

## §4. Per-cycle invariant checks (the immune system)

Tiered validation per L1_CONTINUITY §1.1 + L1_SCHEMA §4 + L0 §6 (I3/I5/I8/I10 L0-mandated).

- **§4.1 Per-cycle (tier-1)**: I1 identity record + active prefix of owner_key_history; I3 tier-1 vs SSoT; I4 DAG-tip hash + Merkle; I8 skin breach; I10 cost-observation (emit signals #7/#8/#9).
- **§4.2 Per-deep-cycle (tier-2; default 1/100)**: I5 reachability over SSoT tiers; tier-2 sampled validation (L1_SCHEMA §4.3); recovery-drill scheduling; I9 compression-invariant hash vs baseline (mismatch → C41/C42); I12 telos-alignment in steady state.
- **§4.3 Witnesses-not-verdicts** (L0 §9.3.4): emit cryptographic-proof tuples — sampled leaf hashes (anchor-nonce-derived per §9.3.5), Merkle paths, parent hashes, check inputs — sufficient for verifier to re-derive. Substrate does NOT emit pass/fail summaries. Sampling indices = `H(anchor_surface_nonce, leaf_count)`; substrate cannot bias. Implementation 0%; M-anchor-4 closes. Extension: applies to I9 (compression: kept-vs-discarded witnesses), I10 (cost: raw measurements + L1 thresholds), I12 (telos: embedding centroid + objective embedding + similarity score, anchor-client computes verdict).

---

## §5. Immune-grade sporocarp catalog (per L1_HARD_RULES §1)

20 L1-catalog CRITICAL (C1-C20) + 16 substrate-private (C30-C45). Each detected at L1 site; traces to ≥1 P + ≥1 I; CRITICAL → auto-quarantine + named immune sporocarp. Daily/elevated grades emit without quarantine (e.g., `budget_exhausted:{axis}`). Observatory tracks immune rates in composite #10. Full catalog at L1_HARD_RULES §1. M26-cascade A6 additions: C36 `cycle_backlog`, C37 `doctrine_instability_burst` (wall-clock correction pending), C38 `snapshot_integrity_violation`, C39 `federation_hello_signature_invalid`, C40 `bet_weakening_quorum` (cycle→wall-clock correction pending), C41-C45 mycoparasite findings (M28-cascade deferred).

---

## §6. Drill failure-rate baseline

Canonical at L1_SCHEMA §2.4 (cadences, sampled cold-tier verification, `recovery_drill_result` emission). Observability: rolling 30-drill window; emergent `drill_failure_rate`; ≥2σ departure → immune; secular up-trend → `drill_aging_grade` approaching-mortality.

Two-baseline: **near** (last-10 rolling; acute departures); **secular** (anchored to first-stable drills 6-15; never advances; current/secular ≥L1-tunable threshold default 3× → `drill_aging_grade`). Cold-tier slow cadence → secular scales over decades. Drills emit witnesses-not-verdicts; cadence wall-clock days per L0 §13.1; must include backup-access discipline check per L1_SKIN §11.1.

---

## §7. Cycle-level diagnostics (C36 site)

Canonical at **L1_CONTINUITY §1.2** (cycle ≥5s OR backlog ≥10 → C36; persistent → quarantine; cadence bounds). Observability: cycles approaching max-interval → `compute_pressure` + feeds signal #7. Backlog uses substrate-monotonic clock per L0 §13.1; wall-clock thresholds use anchor timestamp.

---

## §8. L0/L1 revision burst (C37 — doctrine-instability)

Per L0 §9.4: >10 CI events / 100 cycles rolling → `doctrine_instability_burst` (C37; M25.1-shipped). Counted events: attestation acceptances; F1 classifier mutations; F3 owner-key rotations; L0/L1 revision diff records (§9.2.4); L1_HARD_RULES F-row mutations. Rolling rate over 12 months above threshold → `doctrine_drift_grade`. Observability-of-the-observer; prevents silently-cumulative drift. Wall-clock post-fix pending per L0 §13.1: currently 100-cycle; DRAFT 9 SEALED demands wall-clock 24-hour rolling.

---

## §9. Telos-drift signal class (per L0 P14.c)

Substrate observes own telos-alignment in steady state; degradation → `telos_drift` immune class (metrics per L1_TROPISM A1). Birth-period exemption → `telos_alignment_pending`. **L1_TROPISM A1 forcing function (G-6.a)**: specify operational metric + window length + drift threshold + birth-period exemption. Without A1, P14.c remains aspirational; `telos_drift` cannot be mechanically emitted; composite #10 stays variance-weighted. Candidate metric: cosine similarity recent-sporocarp embedding-centroid vs owner-objective (or agent-feedback-trajectory). L2_OBSERVABILITY receives outcome signal for composite #10 correlation regime (§2.3.2); documents birth-period exemption (§2.4).

---

## §10. Federation-network observability (cross-ref L2_FEDERATION §13)

Federation health (signals #4a/#4b) is intra-substrate; tracks own peers. Network-level patterns (50% peers untrusted simultaneously, hub failing) are population-level emergent; possibly L4 surfaces network observatory. Per L0 §15 + G-7.c: P15 population consensus moved to L2_FEDERATION; when federation reaches ≥3 peers, consensus algorithm choice itself is observable as P3 evolution event.

---

## §11. Operator-side observability

Operator-agent observes substrate via: gradient digest in handshake + per-cycle digest emission (L1_TROPISM §B4); sporocarp visibility (recent K in digest); cold-resume witness emission (L1_CONTINUITY §3.1). Operator has NO direct observatory access; substrate curates digest (bounded). Distrust structurally enforced via L0 §9 anchor channel (operator queries anchor to verify substrate claims, per L2_TRUST_MODEL §3.1). Per L0 §14: operator-side observability is agent's primary adversarial-Cultivator defense; substrate emits witnesses; operator independently verifies; mismatches surface as observability events.

---

## §12. Owner-side observability (anchor surface)

Cultivator's view (G-11.a) covers: substrate-ID birth attestation (L0 §9.2.1; M-anchor-2); DAG-tip co-signing logs with enumerated nodes (L0 §9.2.2; M-anchor-5); `recovery_drill_result` (§6); `succession_required`/`quarantine_entered`/`mortality_drill_failure`/`anchor_surface_final_seal` (L1_GOVERNANCE §4.4 + L0 §15); aggregate-reattestation diffs (L1_GOVERNANCE §5.2); compression witnesses (I9; L1_SCHEMA §2 P10); cost signals #7/#8/#9 per cycle; telos-alignment + objective embeddings (F20; L1_TROPISM A1); `bet_weakening_quorum` (C40) + `bet_retired_proposal`/`bet_retired_executed` (§3.7).

Per-sub-mechanism status + M-anchor-N at L0 §9.2 status table (canonical). Owner view is archaeological-quality: complete history, canonical bytes, re-derivable witnesses. Substrate cannot hide events from anchor — subject to L0 §14 per L2_TRUST_MODEL §6.

---

## §13. The substrate's self-model

Self-observation recursive: observatory IS substrate state; immune observes state; mutations observed by I3; observations witnessed for anchor. Recursion terminates at anchor (outside substrate). §5 immune-catalog + §6 drill-baseline aggregate into §2 composite #10; both terminate at anchor. Per L0 §6 + §13.1: recursion wall-clock-anchored; substrate-process monotonic clock provides only event ordering. Dual-clock makes self-observation immune to substrate clock drift / pause-resume jumps.

---

## §14. Falsifiability summary

v0.9's claim "I am a valuable symbiotic Cultivar within the agent-Cultivator pair" is falsifiable via: (1) Living Bets quorum trigger §3 — C40; (2) bet retirement §3.7; (3) immune CRITICAL emission §5 — C1-C20 + C30-C45; (4) drill failure-rate departure §6; (5) doctrine-instability burst §8/C37; (6) telos drift §9 (when L1_TROPISM A1 lands); (7) federation fragmentation §10 (signals #4a/#4b); (8) mortality dual-channel (L1_GOVERNANCE §4.4). Substrate cannot silently die or silently lie — subject to L2_TRUST_MODEL §6 P1.a caveat AND L0 §14 adversarial-Cultivator caveat (§14.2 irreducible commitments survive because mechanically enforced).

---

## §15. Glossary

| Term | Definition |
|---|---|
| Intelligence band | Agent-capability range where Myco's bet is cost-justified (~200K to ~10M context). Below: RAG suffices. Above: bitter lesson dominates. |
| Cost-justified value | (a) substrate value exists AND (b) engineering cost < value delta over no-substrate. |
| Bet retirement | Graceful sunset when 2-year wall-clock + 3-failed-re-justification + signal #6 <0.1 met. Distinct from Destruction; → `alive::archived`. |
| Variance/Correlation-weighted composite | §2.3.1 (birth-period; high-variance signals) / §2.3.2 (steady; signals correlating with telos outcome). |
| Outcome signal | Telos-alignment per P14 (owner-objective primary; agent-utility fallback). |
| Wall-clock window | Anchor-trusted interval (90d quorum, 2y retirement). Authoritative for time-bound defenses. Distinct from substrate-cycle window (M25.2 C40 + M25.1 C37; post-fix pending). |
| OLS-slope-Z-significance trend | Sign of OLS slope over wall-clock-90-day samples, `|slope/SE| ≥ Z=1.96`. Below = flat. |
| Meta-detector | Signal #5 powers direction table; NOT counted in quorum. |
| Birth-period exemption | C40 + telos_drift suspended; emit `bet_weakening_evaluation_suspended` + `telos_alignment_pending`. Reason: t=0 signals mathematically vacuous. |
| Doctrine-instability burst | >10 CI events / rolling window; →`doctrine_drift_grade` if sustained. Wall-clock correction pending. |
| Telos drift | P14.c alignment degradation; L1_TROPISM A1 metric (M26-cascade forcing function). |
| Cumulative fork count (#4a) | Monotonic federation-fork count. Unimplemented; M28-cascade deferred. |
| Cultivation / Cultivator / Cultivar | See L0 §12. |
| Witnesses-not-verdicts | Crypto-proof tuples (leaf hashes + Merkle paths + parent hashes + check inputs); anchor-verifier re-derives. DRAFT 9 SEALED extends to I9/I10/I12. |
| Anchor-nonce-derived sampling | Indices = `H(anchor_surface_nonce, leaf_count)`; substrate cannot bias. Implementation 0%; M-anchor-4. |
