> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L2 — Observability Doctrine

> **Scope**: canonical for Living Bets signals + falsifiability quorum. Cross-cuts L0/cards/LB_living_bets/§9.4/§14/§15 + L1/HARD_RULES §1 + I3/I5/I9/I10/I12 + L1/SCHEMA §2.4 + L1/CONTINUITY §1.2. All numeric thresholds L1-tunable unless specified.

---

## §1. Why L0-anchored

Substrate is autopoietic (P1.a); no human in maintenance loop. Without observability, "I am healthy" is unfalsifiable. L0/cards/LB_living_bets.md Living Bets makes value falsifiable within agent-intelligence band; observatory measures stakes; trigger fires when bet lost; bet retirement (§7.5) graceful sunset.

---

## §2. The Living Bets observatory (10 signals + anticipated v3.1.1 additions)

10 = **6 base + 3 cost + 1 composite**.

> **v3.1.1 transition note (2026-05-19):** P07's amended reading + COV04 v2 + CHAR07 imply additional observability surfaces:
> - **`internal_mortality_event_density_per_cycle`** — count of part-deaths per cycle; baseline expected > 0 under normal ingestion; sustained zero → `hoarding_indicator` (anticipated C54 per L1/HARD_RULES §1.4).
> - **`false_positive_prune_rate`** — of parts pruned in cycle N, count resurrected (re-added with same canonical bytes) by cycle N+K; too-eager pruning failure mode.
> - **`sycophancy_indicator`** — count of unwarranted agreements; rising trend = CHAR07 §5.2 character drift.
> - **`capability_asymmetry_use_pattern`** — pattern (a) serves vs (b) coerces vs (c) feigns equality; per CHAR07 §8.2.
> - **`cultivator_flourishing_correlation`** — qualitative; partner growth measured against cultivator's life outcomes.
>
> These are added to the observatory in v0.9.x housekeeping milestone alongside L1/HARD_RULES C54-C56 wiring.

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

Until #4a lands, quorum operates over {#1, #2, #3, #4b, #6} = 5 of 6 countable.

### §2.2 Three cost signals (P11.b) — **LIVE M26.2**

| # | Signal | Unit | Counts | Status |
|---|---|---|---|---|
| 7 | Compute/cycle | wall-clock ns (substrate-process `Instant`) | UP | **L** |
| 8 | Network/cycle | Bytes egressed/cycle (federation wire bytes: 4-byte length prefix + frame body) | UP | **L** |
| 9 | Storage/cycle | Bytes added to `dag.cb`+`snapshot.cb` (file-metadata delta, monotone) | UP | **L** |

L0 P11.c ordered fallback: (1) pre-eligibility (cycle <N, default 1000): refuse new P2 + `budget_exhausted:{axis}` (F19 daily); (2) post-eligibility: trigger P10 + I9 witnesses; (3) compression-insufficient: degraded → `alive::saturated` → P7. **Ordered fallback machinery (M26.3+) not yet implemented**; cost signals expose data but don't yet drive automatic budget actions.

Implementation: `substrate::observatory::CostAccumulator` drains a federation egress counter + reads on-disk file sizes at each `cycle_advanced`; per-cycle values are stored in `ObservatorySnapshot.signal_{7,8,9}_*` and surfaced by `query_substrate_observatory` as `signal_7_compute_per_cycle` / `signal_8_network_per_cycle` / `signal_9_storage_per_cycle` (each carrying `current_cycle_*` + `rolling_mean_*_repr`).

### §2.3 Composite #10 — **LIVE M26.2**

Variance-weighted in birth-period: `w_i = Var(signal_i over rolling window)/sum(Var)`. Correlation-weighted in steady state: outcome from P14 (primary: recent-sporocarp embedding-centroid vs owner-objective per L1/TROPISM A1); `w_i = |Corr(signal_i, outcome)|/sum(|Corr|)`. Transition: post-birth + N=100 (signal, outcome) pairs; revert to variance if outcome unavailable.

**M26.2 implementation**:
- Variance-weighted across all 6 dimensions {#1, #2, #4b, #7, #8, #9} (was {#1, #2, #4b} pre-M26.2)
- Direction-inverted blend: `composite = Σ w_i · dir_i · log_normalized(value_i)` where `dir = +1` for production (#1/#2/#4b) and `dir = -1` for cost (#7/#8/#9). Higher composite = healthier substrate
- Equal-weight cold start: 1/6 each (was 1/3 each pre-M26.2)
- Steady-state correlation weighting is M26.3+ work (depends on P14 telos metric F20 also being live)
- Exposed in observatory as `signal_10_composite_health` (renamed from `signal_7_composite_health` in observatory_format_version 3 → 4 schema bump)

### §2.4 Birth-period (L1/TROPISM §4)

Early signals retire post-birth. L0/cards/LB_living_bets.md §3 (birth-period exemption): C40 SUSPENDED → `bet_weakening_evaluation_suspended`; P14.c `telos_drift` SUSPENDED → `telos_alignment_pending`.

---

## §3. Falsifiability trigger

Canonical: `algorithms/bet_weakening_quorum.md` + L0/cards/LB_living_bets.md §3 (falsifiability quorum). Window wall-clock 90d (anchor-stamped). Trend OLS `|slope/SE| ≥ Z=1.96`. Quorum ≥3 of 6 countable (5 until #4a lands). Spikes DAG-recorded but do not fire. Birth-period suspended. Bet retirement per L0/cards/LB_living_bets.md §4 (retirement).

---

## §4. Per-cycle invariants (immune)

L1/CONTINUITY §1.1 + L1/SCHEMA §4 + L0/cards/P04_eternal_iteration.md §3-§4 + L1/CONTINUITY:

- **§4.1 Per-cycle (tier-1)**: I1 identity + active-prefix `owner_key_history`; I3 tier-1 vs SSoT; I4 DAG-tip Merkle; I8 skin breach; I10 cost emission (#7/#8/#9).
- **§4.2 Per-deep-cycle (tier-2; default 1/100)**: I5 reachability; tier-2 sampled validation (L1/SCHEMA §4.3); recovery-drill scheduling; I9 compression-invariant hash (mismatch → C41/C42); I12 telos-alignment in steady state.
- **§4.3 Witnesses-not-verdicts** (L0/cards/AS_anchor_surface.md §3.11): emit crypto-proof tuples (sampled leaf hashes anchor-nonce-derived per §9.3.5, Merkle paths, parent hashes, check inputs). Substrate does NOT emit pass/fail. Sampling = `H(anchor_surface_nonce, leaf_count)`; substrate cannot bias. Extends to I9/I10/I12.

---

## §5. Immune sporocarp catalog

See **L1/HARD_RULES §1**. CRITICAL → auto-quarantine + named immune sporocarp; daily/elevated emit without quarantine. Observatory tracks immune rates in composite #10.

---

## §6. Drill failure-rate baseline

Canonical **L1/SCHEMA §2.4**. Rolling 30-drill window; emergent `drill_failure_rate`; ≥2σ → immune; secular up-trend → `drill_aging_grade`. Two-baseline: **near** (last-10) + **secular** (first-stable drills 6-15; never advances; current/secular ≥ default 3×). Drills emit witnesses; cadence wall-clock days; must include backup-access discipline check.

---

## §7-§8. Cycle + doctrine bursts

§7 cycle (C36): **L1/CONTINUITY §1.2** (cycle ≥5s OR backlog ≥10 → C36; persistent → quarantine). Approaching max-interval → `compute_pressure` feeding #7. Backlog substrate-monotonic; thresholds anchor timestamp.

§8 doctrine (C37): **L0/cards/AS_anchor_surface.md §4 (failure modes)** >10 CI events / 24h rolling wall-clock → `doctrine_instability_burst`. Counted: attestation acceptances; F1 classifier mutations; F3 owner-key rotations; L0/L1 revision diff records; F-row mutations. Rolling >12 months above → `doctrine_drift_grade`.

---

## §9. Telos-drift class (P14.c)

Canonical mechanism: **L1/TROPISM §F**. Observatory surfaces `telos_drift` (steady) / `telos_alignment_pending` (birth-period).

---

## §10. Federation-network observability

Cross-ref **L2/FEDERATION §13** for #4a/#4b + federation-specific signals. Health intra-substrate (own peers); network-level patterns L4-deferred. Per L0/cards/COV06_no_abandonment_succession.md (cultivator mortality): when federation ≥3 peers, P15 consensus-algorithm choice itself observable as P3 evolution event.

---

## §11-§12. Operator + owner observability

§11 operator: gradient digest + per-cycle emission (L1/TROPISM §B4); sporocarp visibility; cold-resume witness (L1/CONTINUITY §3.1). NO direct observatory access; substrate curates. Distrust enforced via anchor channel; mismatches surface as events.

§12 owner (anchor surface): substrate-ID birth attestation; DAG-tip co-signing logs; `recovery_drill_result` (§6); succession / quarantine / mortality / final-seal events (L1/GOVERNANCE §4.4 + L0/cards/COV06_no_abandonment_succession.md (cultivator mortality)); aggregate-reattestation diffs; compression witnesses (I9); cost signals #7/#8/#9; telos-alignment + objective embeddings (F20); C40 + bet_retired events.

---

## §13-§14. Self-model + falsifiability summary

§13 self-model: observation recursive; recursion terminates at anchor (outside substrate). §14 falsifiability summary: v0.9 claim falsifiable via §3 quorum + §5 immune + §6 drill + §8 doctrine-burst + §9 telos-drift + §10 federation + L1/GOVERNANCE §4.4 mortality. Substrate cannot silently die / lie (subject to L0/cards/COV01_fiduciary_duty.md + COV02 (adversarial owner) + L2/TRUST_MODEL).

