> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# `bet_weakening_quorum` — falsifiability trigger algorithm

> Reference algorithm extracted from L0/cards/LB_living_bets.md §3 (falsifiability quorum) to keep active doctrine lean. Authoritative algorithm lives at **L2/OBSERVABILITY §3** (per-cycle detector) + L0/cards/LB_living_bets.md §3 (falsifiability quorum) (commitment); this file is the consolidated specification. Wall-clock window + 90-sample observatory_history cap normative.

---

## §1. Algorithm (informal)

Over a **90-day wall-clock window** (anchor-stamped per L0/cards/P06_eternal_causality.md + L1/CONTINUITY (time semantics)):

1. For each countable signal s ∈ {#1, #2, #3, #4a, #4b, #6}, collect samples at cadence ≥ 1/substrate-day (≥ 90 samples).
2. Compute OLS-regression slope of s over the window — see §1.3 for the **rate transform** applied to the cumulative-monotone signals.
3. Compute Z = |slope / standard-error|. If Z < 1.96 (95% confidence; L1-tunable), signal is **flat** and does NOT count.
4. If Z ≥ 1.96 AND slope sign matches **DOWN** (per direction table at L2/OBSERVABILITY §3.3), signal **counts**.
5. Independently, check: signal #6 < 1 for ≥ 50% of window samples.
6. If (count ≥ 3) AND (#6 < 1 for ≥ 50% of window) → fire `bet_weakening_quorum` (C40 sporocarp).

### §1.3 Rate transform for cumulative-monotone signals (implementation-binding)

Signals #1 (`dag_node_count`), #2 (`evolution_event_count`), and #3
(`distinct_perturbed_axes_count`) are **cumulative-monotone counters** — they
can only ever rise, so the OLS slope of the *level* series is non-negative and
could never trend DOWN, making the quorum unsatisfiable on these three signals
(the structural bug Phase ② fixes). The doctrine intent is that these signals
are conceptually **rates** whose slope CAN go negative when the substrate
*decelerates*. Therefore the OLS slope + Z-test runs on the **per-cycle
first-difference (rate) series** `r[t] = s[t] − s[t−1]` for #1/#2/#3: a
substrate whose ingestion / evolution / axis-growth RATE is declining yields a
negative slope on the rate series → **DOWN**. The level signals that can already
fall (#4b reachable peers, #6 ratio) run OLS on the level series directly.

A healthy substrate stays **flat/up**: steady growth ⇒ constant rate ⇒ slope ≈ 0
⇒ flat (not counted); accelerating growth ⇒ rising rate ⇒ up. Only genuine
deceleration (a falling rate, statistically significant at Z ≥ 1.96) reads DOWN.

Implementation: `substrate/src/observatory.rs::signal_direction_label_ols` +
`::first_difference_series`, wired in `handle_query_substrate_observatory`.

## §2. Signal #5 role

Signal #5 (OLS slope) is the **meta-direction-detector** — its outputs power steps 2-4 above. Signal #5 itself is NOT counted in the quorum (it IS the math).

## §3. Quorum arithmetic

- 6 countable signals (#5 meta; #4 splits into 4a + 4b).
- Threshold: ≥ 3 of 6.
- Until #4a lands: quorum operates over 5 of 6; documented false-negative bias per L2/OBSERVABILITY §3.4.

## §4. Birth-period exemption (per L0/cards/LB_living_bets.md §3 (birth-period exemption))

SUSPENDED during birth period (L1/TROPISM §4 + L1/GOVERNANCE §1.3): #6 structurally < 1, #1 monotone growing from zero, #3 structurally zero — math vacuous. Substrate emits `bet_weakening_evaluation_suspended` instead of `bet_weakening_quorum`.

Implementation (Phase ②): the birth predicate is
`substrate/src/lifecycle.rs::is_in_birth_period_quarantine` (the canonical
L1/TROPISM §4 + L1/GOVERNANCE §1.3 structural birth window), mirroring the telos
birth gate (`apply_p14c_telos_drift` → `telos_alignment_pending`). When in
birth, `handle_query_substrate_observatory` reports `suspended_birth_period:
true`, skips the quorum, and emits `bet_weakening_evaluation_suspended`
(node_type constant `NODE_TYPE_BET_WEAKENING_EVALUATION_SUSPENDED`) — debounced
on the same 100-cycle channel as C40.

## §5. Trend significance gate seeds

- Z = 1.96 (95% confidence). L1-tunable.
- Cadence: 1/substrate-day. L1-tunable.
- Window: 90 wall-clock days. L1-tunable.

## §6. Output sporocarp

On fire: positive `bet_weakening_quorum_quorum:{cycle}` DAG event + C40 immune sporocarp (per L1/HARD_RULES §1.1).

## §7. Cascade

- L0 commitment: §7.4 + §7.5 retirement trigger.
- L1 mechanism site: L1/GOVERNANCE (proposal lifecycle) + L1/HARD_RULES C40.
- L2 detector: L2/OBSERVABILITY §3.
