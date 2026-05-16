# L2 — Observability Doctrine

> **Status**: DRAFT 3 (2026-05-17, M27 R5 cleanup). Canonical for Living Bets signals + falsifiability quorum.
> **Scope**: L0 §7/§9.4/§14/§15 + L1_HARD_RULES §1 + I3/I5/I9/I10/I12 + L1_SCHEMA §2.4 + L1_CONTINUITY §1.2.

---

## §1. Why L0-anchored

Substrate is autopoietic (P1.a); no human in maintenance loop. Without observability, "I am healthy" is unfalsifiable. L0 §7 Living Bets makes value falsifiable within agent-intelligence band; observatory measures stakes; trigger fires when bet lost; bet retirement (§7.5) graceful sunset.

---

## §2. The Living Bets observatory (10 signals)

10 = **6 base + 3 cost + 1 composite**.

### §2.1 Six base signals

| # | Signal | DOWN means | Counts |
|---|---|---|---|
| 1 | Persistence budget | not growing | DOWN |
| 2 | Evolution rate | stagnating | DOWN |
| 3 | Read-pattern diversity | not being read | DOWN |
| 4a | Cumulative fork count | peers exiting | DOWN |
| 4b | Reachable federation count | mycelial fragmentation | DOWN |
| 5 | Time trend per signal | — | meta (NOT counted) |
| 6 | Read-window-relative ratio | shrinking vs context | DOWN <1.0 |

**Signal #4a unimplemented** (M28-deferred): until M28 quorum operates over {#1, #2, #3, #4b, #6} = 5 of 6 countable.

### §2.2 Three cost signals (P11.b)

| # | Signal | Unit | Counts |
|---|---|---|---|
| 7 | Compute/cycle | CPU+wall-clock μs (L1-tunable) | UP |
| 8 | Network/cycle | Bytes egressed/cycle | UP |
| 9 | Storage/cycle | Bytes added to `dag.cb`+`snapshot.cb` | UP |

L0 P11.c ordered fallback: (1) pre-eligibility (cycle <N, default 1000): refuse new P2 + `budget_exhausted:{axis}` (F19 daily); (2) post-eligibility: trigger P10 + I9 witnesses; (3) compression-insufficient: degraded → `alive::saturated` → P7.

### §2.3 Composite #10

Variance-weighted in birth-period: `w_i = Var(signal_i over 100-cycle)/sum(Var)`. Correlation-weighted in steady state: outcome from P14 (primary: recent-sporocarp embedding-centroid vs owner-objective per L1_TROPISM A1); `w_i = |Corr(signal_i, outcome)|/sum(|Corr|)`. Transition: post-birth + N=100 (signal, outcome) pairs; revert to variance if outcome unavailable.

### §2.4 Birth-period (L1_TROPISM §4)

Early signals retire post-birth. L0 §7.4.e: C40 SUSPENDED → `bet_weakening_evaluation_suspended`; P14.c `telos_drift` SUSPENDED → `telos_alignment_pending`.

---

## §3. Falsifiability trigger

Canonical algorithm: `algorithms/bet_weakening_quorum.md` + L0 §7.4. Window wall-clock 90d (anchor-stamped). Trend OLS `|slope/SE| ≥ Z=1.96`. Quorum ≥3 of 6 countable (until M28: ≥3 of 5). Spikes DAG-recorded but do not fire. Birth-period suspended.

**Bet retirement** (L0 §7.5): C40 fires AND re-justification fails 3× over 2-year wall-clock AND #6 <0.1 for >75% of final-90-day samples AND `alive::normal` → `bet_retired_proposal`; owner co-attestation → `alive::archived`. Counter reset on successful re-justification / `alive::quarantined` / owner-attested `bet_retirement_counter_reset`.

---

## §4. Per-cycle invariants (immune)

L1_CONTINUITY §1.1 + L1_SCHEMA §4 + L0 §6:

- **§4.1 Per-cycle (tier-1)**: I1 identity + active-prefix `owner_key_history`; I3 tier-1 vs SSoT; I4 DAG-tip Merkle; I8 skin breach; I10 cost emission (#7/#8/#9).
- **§4.2 Per-deep-cycle (tier-2; default 1/100)**: I5 reachability; tier-2 sampled validation (L1_SCHEMA §4.3); recovery-drill scheduling; I9 compression-invariant hash (mismatch → C41/C42); I12 telos-alignment in steady state.
- **§4.3 Witnesses-not-verdicts** (L0 §9.3.4): emit crypto-proof tuples (sampled leaf hashes anchor-nonce-derived per §9.3.5, Merkle paths, parent hashes, check inputs). Substrate does NOT emit pass/fail. Sampling = `H(anchor_surface_nonce, leaf_count)`; substrate cannot bias. Implementation 0%; M-anchor-4 closes. Extends to I9 (kept-vs-discarded), I10 (raw measurements + thresholds), I12 (embedding centroid + objective + similarity).

---

## §5. Immune sporocarp catalog

20 L1-catalog CRITICAL (C1-C20) + 16 substrate-private (C30-C45); see **L1_HARD_RULES §1**. Each L1-site detected; traces to ≥1 P + ≥1 I; CRITICAL → auto-quarantine + named immune. Daily/elevated emit without quarantine. Observatory tracks immune rates in composite #10. M26-cascade A6: C36 cycle_backlog, C37 doctrine_instability_burst, C38 snapshot_integrity_violation, C39 federation_hello_signature_invalid, C40 bet_weakening_quorum, C41-C45 mycoparasite (M28-deferred). Wall-clock corrections on C37/C40 pending.

---

## §6. Drill failure-rate baseline

Canonical **L1_SCHEMA §2.4**. Rolling 30-drill window; emergent `drill_failure_rate`; ≥2σ → immune; secular up-trend → `drill_aging_grade`. Two-baseline: **near** (last-10) + **secular** (first-stable drills 6-15; never advances; current/secular ≥ default 3×). Drills emit witnesses; cadence wall-clock days; must include backup-access discipline check.

---

## §7-§8. Cycle + doctrine bursts

§7 cycle (C36): **L1_CONTINUITY §1.2** (cycle ≥5s OR backlog ≥10 → C36; persistent → quarantine). Approaching max-interval → `compute_pressure` feeding #7. Backlog substrate-monotonic; thresholds anchor timestamp.

§8 doctrine (C37): **L0 §9.4** >10 CI events / 100 cycles rolling → `doctrine_instability_burst` (C37; M25.1). Counted: attestation acceptances; F1 classifier mutations; F3 owner-key rotations; L0/L1 revision diff records; L1_HARD_RULES F-row mutations. Rolling >12 months above → `doctrine_drift_grade`. Wall-clock fix pending: currently 100-cycle; DRAFT 9 demands 24-hour rolling.

---

## §9. Telos-drift class (P14.c)

Substrate observes own telos-alignment in steady state; degradation → `telos_drift` (metrics per **L1_TROPISM A1**). Birth-period → `telos_alignment_pending`. **A1 forcing function**: specify metric + window + threshold + birth-period exemption. Without A1, P14.c aspirational; composite stays variance-weighted. Candidate: cosine similarity recent-sporocarp embedding-centroid vs owner-objective.

---

## §10. Federation-network observability

Cross-ref **L2_FEDERATION §13** for #4a/#4b + federation-specific signals. Health intra-substrate (own peers); network-level patterns L4-deferred. Per L0 §15: when federation ≥3 peers, P15 consensus-algorithm choice itself observable as P3 evolution event.

---

## §11-§12. Operator + owner observability

§11 operator: gradient digest + per-cycle emission (L1_TROPISM §B4); sporocarp visibility; cold-resume witness (L1_CONTINUITY §3.1). NO direct observatory access; substrate curates. Distrust enforced via anchor channel; mismatches surface as events.

§12 owner (anchor surface): substrate-ID birth attestation (M-anchor-2); DAG-tip co-signing logs (M-anchor-5); `recovery_drill_result` (§6); succession / quarantine / mortality / final-seal events (L1_GOVERNANCE §4.4 + L0 §15); aggregate-reattestation diffs; compression witnesses (I9); cost signals #7/#8/#9; telos-alignment + objective embeddings (F20); C40 + bet_retired events. Per-sub-mechanism status at L0 §9.2.

---

## §13-§14. Self-model + falsifiability summary

§13 self-model: observation recursive; recursion terminates at anchor (outside substrate). Dual-clock makes self-observation immune to clock drift / pause-resume.

§14 falsifiability summary: v0.9 claim is falsifiable via (1) Living Bets quorum (§3 C40); (2) bet retirement (§3); (3) immune CRITICAL (§5); (4) drill failure-rate (§6); (5) doctrine-instability burst (§8/C37); (6) telos drift (§9); (7) federation fragmentation (§10); (8) mortality dual-channel (L1_GOVERNANCE §4.4). Substrate cannot silently die or silently lie (subject to L2_TRUST_MODEL §6 + L0 §14).

---

## §15. Glossary

See L0 §12. Document-specific terms defined inline at §2/§3/§4/§8/§9.
