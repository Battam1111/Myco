> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4), see `docs/architecture/OUTLINE.md` §3 for details.

---

# L2: Observability Doctrine

> **Scope**: canonical for Living Bets signals + falsifiability quorum. Cross-cuts L0/cards/LB_living_bets/§9.4/§14/§15 + L1/HARD_RULES §1 + I3/I5/I9/I10/I12 + L1/SCHEMA §2.4 + L1/CONTINUITY §1.2. All numeric thresholds L1-tunable unless specified.

---

## §1. Why L0-anchored

Substrate is autopoietic (P1.a); no human in maintenance loop. Without observability, "I am healthy" is unfalsifiable. L0/cards/LB_living_bets.md Living Bets makes value falsifiable within agent-intelligence band; observatory measures stakes; trigger fires when bet lost; bet retirement (§7.5) graceful sunset.

---

## §2. The Living Bets observatory (10 signals + anticipated v3.1.1 additions)

10 = **6 base + 3 cost + 1 composite**.

> **v3.1.1 transition note (2026-05-19; status updated 2026-06-02):** P07's amended reading + COV04 v2 + CHAR07 imply additional observability surfaces. **All five are now LIVE** (the OBSERVATORY-gap milestone wired the remaining three; `observatory_format_version` is now **5**):
> - **`internal_mortality_event_density_per_cycle`**, **LIVE** (snapshot field `signal_internal_mortality_event_density`, computed in `prune.rs`; surfaced per-cycle). Count of part-deaths per window; baseline expected > 0 under normal ingestion; sustained zero → `hoarding_indicator` (C54).
> - **`false_positive_prune_rate`**, **LIVE** (= signal #11, computed live in `observatory.rs` via `prune::count_prune_resurrections`). Of parts pruned, count resurrected (re-added with same canonical bytes); too-eager pruning failure mode.
> - **`sycophancy_indicator`**, **LIVE as C71** (`sycophancy_indicator_elevated`, daily NOT immune). The INVERSE of `honest_disagreement_density` (§8.4): sustained ~zero honest disagreement WHILE interaction is non-trivial (raw_material ingestion ≥ floor). Surfaced under the query's `char07_honest_disagreement` map.
> - **`capability_asymmetry_use_pattern`**, **LIVE as cultivator-attested INTAKE** (NOT autonomously observable per CHAR07 §8.2). Cultivator submits via `submit_char07_assessment` → `char07_assessment:capability_asymmetry_pattern` DAG event; query surfaces the latest with `source:"cultivator_attested"`, or `source:"unavailable"` when none exists. The substrate NEVER fabricates this number (CHAR05).
> - **`cultivator_flourishing_correlation`**, **LIVE as cultivator-attested INTAKE with telos-proxy fallback** (§8.1). Cultivator submits via `submit_char07_assessment` → `char07_assessment:flourishing_correlation`; query surfaces the latest with `source:"cultivator_attested"`, falling back to the existing P14.c telos_alignment cosine (`source:"telos_proxy"`) when no attestation exists.
>
> The single genuinely substrate-observable CHAR07 signal, **`honest_disagreement_density`** (§8.4), is a rolling-window count of the substrate's existing "did-not-just-comply" DAG footprints (immune sporocarps against operator/cultivator content: C5/C14/C56/C69, plus `self_euthanasia_proposal:*` and `telos_drift*`). C71/C72/C73 are **daily/informational, NOT critical** (CHAR07 §8.7: developmental character → auto-quarantine would be wrong). These rows are NOT promoted to the binding §1.1/§1.2 catalog.

### §2.1 Six base signals

| # | Signal | DOWN means | Counts |
|---|---|---|---|
| 1 | Persistence budget | not growing | DOWN |
| 2 | Evolution rate | stagnating | DOWN |
| 3 | Read-pattern diversity | not being read | DOWN |
| 4a | Cumulative fork count | peers exiting | DOWN |
| 4b | Reachable federation count | mycelial fragmentation | DOWN |
| 5 | Time trend per signal | n/a | meta (NOT counted) |
| 6 | Read-window-relative ratio | shrinking vs context | DOWN <1.0 |

Quorum operates over {#1, #2, #3, #4b, #6} = 5 countable signals.

> **#4a doctrinal nuance (2026-06-02):** signal #4a (cumulative fork count) now LANDS, it counts `spore_emission:*` (child sprout) events and is surfaced in the observatory query (`signal_4_federation_health.signal_4a_cumulative_fork_count`) + the per-cycle snapshot. But it is **deliberately NOT added to the `bet_weakening_quorum`**, which stays at the 5 signals above. The §2.1 table's "DOWN = peers exiting" reading for #4a is carried by **#4b** (the reachable-peer count, which CAN fall = mycelial fragmentation = against the bet); the cumulative fork count itself is **monotone-healthy**, forks are reproduction/spread and only ever rise, so a rising #4a is never bet-weakening and a "falling" #4a is impossible. Adding a monotone counter to a falsifiability quorum would be a category error.

### §2.2 Three cost signals (P11.b), **LIVE M26.2**

| # | Signal | Unit | Counts | Status |
|---|---|---|---|---|
| 7 | Compute/cycle | wall-clock ns (substrate-process `Instant`) | UP | **L** |
| 8 | Network/cycle | Bytes egressed/cycle (federation wire bytes: 4-byte length prefix + frame body) | UP | **L** |
| 9 | Storage/cycle | Bytes added to `dag.cb`+`snapshot.cb` (file-metadata delta, monotone) | UP | **L** |

L0 P11.c ordered fallback: (1) pre-eligibility (cycle <N, default 1000): refuse new P2 + `budget_exhausted:{axis}` (F19 daily); (2) post-eligibility: trigger P10 + I9 witnesses; (3) compression-insufficient: degraded → `alive::saturated` → P7. **Ordered fallback machinery is now LIVE (OBSERVATORY-gap milestone, 2026-06-02):**
- **Stage 1: P02 refusal**: while `saturation_stage != Normal`, `handle_ingest_raw_material` returns a structured refusal `{refused:true, reason:"budget_exhausted", axis, saturation_stage}` rather than silently absorbing cost; the matching `budget_exhausted:{axis}` event is already in the DAG.
- **Stage 2, compression proposals**: on entering PostEligibility the substrate emits `compression_proposed:{rule_id}` daily events (pre-existing).
- **Stage 3: P7 escalation**: sustained `Saturated` past `sustained_saturation_mortality_cycle_threshold` (in-memory CostBudgets field, seed 1000) emits `self_euthanasia_proposal:metabolic_saturation`, a **PROPOSAL** the existing `accept_self_euthanasia_proposal` path executes on cultivator co-attestation (NOT auto-death; cooldown-reset on return to Normal).

The live saturation state (stage + `post_eligibility_consecutive_cycles` + `saturated_consecutive_cycles` + per-axis exceeded flags) is surfaced in the observatory query under `saturation_status`.

Implementation: `substrate::observatory::CostAccumulator` drains a federation egress counter + reads on-disk file sizes at each `cycle_advanced`; per-cycle values are stored in `ObservatorySnapshot.signal_{7,8,9}_*` and surfaced by `query_substrate_observatory` as `signal_7_compute_per_cycle` / `signal_8_network_per_cycle` / `signal_9_storage_per_cycle` (each carrying `current_cycle_*` + `rolling_mean_*_repr`).

### §2.3 Composite #10, **LIVE M26.2**

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

Canonical: `algorithms/bet_weakening_quorum.md` + L0/cards/LB_living_bets.md §3 (falsifiability quorum). Window wall-clock 90d (substrate-clocked; keyless v3.1.5, no anchor-stamped wall-clock). Trend OLS `|slope/SE| ≥ Z=1.96`. Quorum ≥3 of 6 countable (5 until #4a lands). Spikes DAG-recorded but do not fire. Birth-period suspended. Bet retirement per L0/cards/LB_living_bets.md §4 (retirement).

---

## §4. Per-cycle invariants (immune)

L1/CONTINUITY §1.1 + L1/SCHEMA §4 + L0/cards/P04_eternal_iteration.md §3-§4 + L1/CONTINUITY:

- **§4.1 Per-cycle (tier-1)**: I1 identity (keyless v3.1.5: the prior active-prefix `owner_key_history` surface is removed with the owner key); I3 tier-1 vs SSoT; I4 DAG-tip Merkle; I8 skin breach; I10 cost emission (#7/#8/#9).
- **§4.2 Per-deep-cycle (tier-2; default 1/100)**: I5 reachability; tier-2 sampled validation (L1/SCHEMA §4.3); recovery-drill scheduling; I9 compression-invariant hash (mismatch → C41/C42); I12 telos-alignment in steady state.
- **§4.3 Witnesses-not-verdicts** (keyless v3.1.5; the principle survives the Superseded AS card, see META §7.8 + B048): emit re-derivable proof tuples (sampled leaf hashes, Merkle paths, parent hashes, check inputs). Substrate does NOT emit pass/fail; the **live human-in-the-loop re-derives the verdict at the CI gate**. *(Keyless: the prior anchor-nonce-derived sampling `H(anchor_surface_nonce, leaf_count)` is retired with anchor nonces; sampling indices are now derived from substrate-internal entropy / the DAG-tip hash, the substrate still cannot bias which fields are sampled because the index derivation is fixed + re-derivable by the verifier.)* Extends to I9/I10/I12.

---

## §5. Immune sporocarp catalog

See **L1/HARD_RULES §1**. CRITICAL → auto-quarantine + named immune sporocarp; daily/elevated emit without quarantine. Observatory tracks immune rates in composite #10.

---

## §6. Drill failure-rate baseline

Canonical **L1/SCHEMA §2.4**. Rolling 30-drill window; emergent `drill_failure_rate`; ≥2σ → immune; secular up-trend → `drill_aging_grade`. Two-baseline: **near** (last-10) + **secular** (first-stable drills 6-15; never advances; current/secular ≥ default 3×). Drills emit witnesses; cadence wall-clock days; must include backup-access discipline check.

---

## §7-§8. Cycle + doctrine bursts

§7 cycle (C36): **L1/CONTINUITY §1.2** (cycle ≥5s OR backlog ≥10 → C36; persistent → quarantine). Approaching max-interval → `compute_pressure` feeding #7. Backlog substrate-monotonic; thresholds use the substrate's own clock (keyless v3.1.5: no anchor timestamp).

§8 doctrine (C37): >10 CI events / 24h rolling wall-clock → `doctrine_instability_burst`. Counted (keyless v3.1.5): CI approvals at the live gate; F1 classifier mutations; L0/L1 revision seals (BLAKE3 bundle reseals); F-row mutations. *(The prior "F3 owner-key rotations" + the AS §4 reference are retired with the owner key/anchor surface.)* Rolling >12 months above → `doctrine_drift_grade`.

---

## §9. Telos-drift class (P14.c)

Canonical mechanism: **L1/TROPISM §F**. Observatory surfaces `telos_drift` (steady) / `telos_alignment_pending` (birth-period).

---

## §10. Federation-network observability

Cross-ref **L2/FEDERATION §13** for #4a/#4b + federation-specific signals. Health intra-substrate (own peers); network-level patterns L4-deferred. Per L0/cards/COV06_no_abandonment_succession.md (cultivator mortality): when federation ≥3 peers, P15 consensus-algorithm choice itself observable as P3 evolution event.

---

## §11-§12. Operator + owner observability

§11 operator: gradient digest + per-cycle emission (L1/TROPISM §B4); sporocarp visibility; cold-resume witness (L1/CONTINUITY §3.1). NO direct observatory access; substrate curates. Operator/substrate mismatches surface as DAG events for review at the live CI gate (keyless v3.1.5: the prior anchor distrust-channel is retired).

§12 cultivator-facing surfaces (keyless v3.1.5; was "owner (anchor surface)"): `recovery_drill_result` (§6); succession / quarantine / mortality / final-seal events (L1/GOVERNANCE §4.4 + L0/cards/COV06_no_abandonment_succession.md; final-seal = the BLAKE3 at-rest seal F5); compression witnesses (I9); cost signals #7/#8/#9; telos-alignment + objective embeddings (F20); C40 + bet_retired events. *(Retired with the anchor surface: the owner-signed substrate-ID birth attestation, the DAG-tip co-signing logs, and the aggregate-reattestation diffs. Doctrine-revision visibility is now the BLAKE3-sealed-bundle chain (PROVENANCE §6) + DAG events at the live CI gate.)*

---

## §13-§14. Self-model + falsifiability summary

§13 self-model: observation recursive; recursion terminates outside the substrate, at the live human-in-the-loop (keyless v3.1.5: formerly "at the anchor"). §14 falsifiability summary: v0.9 claim falsifiable via §3 quorum + §5 immune + §6 drill + §8 doctrine-burst + §9 telos-drift + §10 federation + L1/GOVERNANCE §4.4 mortality. Substrate cannot silently die / lie (subject to L0/cards/COV01_fiduciary_duty.md + COV02 (adversarial owner) + L2/TRUST_MODEL).

