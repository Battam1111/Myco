# `bet_weakening_quorum` — falsifiability trigger algorithm (extracted from L0_VISION.md §7.4)

> **Status**: REFERENCE ALGORITHM. Extracted from L0_VISION.md DRAFT 9 SEALED §7.4 to keep active doctrine lean. Authoritative algorithm lives at **L2_OBSERVABILITY §3** (per-cycle detector) + L0 §7.4 (commitment); this file is the consolidated specification.
> **Source**: L0_VISION.md DRAFT 9 SEALED commit `e796451`; M25.2 wall-clock-window correction pending (cycle→wall-clock; observatory_history capped at 90).

---

## §1. Algorithm (informal)

Over a **90-day wall-clock window** (anchor-stamped per L0 §13.1):

1. For each countable signal s ∈ {#1, #2, #3, #4a, #4b, #6}, collect samples at cadence ≥ 1/substrate-day (≥ 90 samples).
2. Compute OLS-regression slope of s over the window.
3. Compute Z = |slope / standard-error|. If Z < 1.96 (95% confidence; L1-tunable), signal is **flat** and does NOT count.
4. If Z ≥ 1.96 AND slope sign matches **DOWN** (per direction table at L2_OBSERVABILITY §3.3), signal **counts**.
5. Independently, check: signal #6 < 1 for ≥ 50% of window samples.
6. If (count ≥ 3) AND (#6 < 1 for ≥ 50% of window) → fire `bet_weakening_quorum` (C40 sporocarp).

## §2. Signal #5 role

Signal #5 (OLS slope) is the **meta-direction-detector** — its outputs power steps 2-4 above. Signal #5 itself is NOT counted in the quorum (it IS the math).

## §3. Quorum arithmetic

- 6 countable signals (#5 meta; #4 splits into 4a + 4b).
- Threshold: ≥ 3 of 6.
- Until #4a implemented (M28-cascade deferred): quorum operates over 5 of 6; documented false-negative bias per L2_OBSERVABILITY §3.4.

## §4. Birth-period exemption (per L0 §7.4.e)

SUSPENDED during birth period (L1_TROPISM §4 + L1_GOVERNANCE §1.3): #6 structurally < 1, #1 monotone growing from zero, #3 structurally zero — math vacuous. Substrate emits `bet_weakening_evaluation_suspended` instead of `bet_weakening_quorum`.

## §5. Trend significance gate seeds

- Z = 1.96 (95% confidence). L1-tunable.
- Cadence: 1/substrate-day. L1-tunable.
- Window: 90 wall-clock days. L1-tunable.

## §6. Output sporocarp

On fire: positive `bet_weakening_quorum_quorum:{cycle}` DAG event + C40 immune sporocarp (per L1_HARD_RULES §1.1).

## §7. Cascade

- L0 commitment: §7.4 + §7.5 retirement trigger.
- L1 mechanism site: L1_GOVERNANCE (proposal lifecycle) + L1_HARD_RULES C40.
- L2 detector: L2_OBSERVABILITY §3.
- M25.2 implementation status: ships wall-clock window + observatory_history cap = 90 samples + Z-test.
