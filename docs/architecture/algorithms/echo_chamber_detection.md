# Echo-Chamber Detection (Trajectory-Injection Defense)

> Extracted from L1_TRAJECTORY §9. Normative spec lives at L1_TRAJECTORY §9.

## Attack

Agent floods deltas crafted to make `cluster_C` produce desired trajectory T; downstream trusts; immune-grade drift suppressed.

## Defense — delta-novelty weighting

Trajectory derivation down-weights deltas whose `causal_in_edges` (L1_TROPISM §B6) trace overwhelmingly to recent same-operator deltas (high self-citation, low external-anchor).

## Detection threshold

Trajectory dominated by self-citation chains beyond L1-tunable threshold emits `echo_chamber` immune sporocarp:

- Seed: ≥ 80% of recent-window node citations within L1-tunable causal-distance of recent self-citations.
- Operator-session-agnostic (DAG-structural, not operator-session keyed).

## Keying — substrate-keyed, not operator-keyed

Operator-keyed detection would:
1. Conflict with I1 prohibition (multiple operators ≠ multiple substrates).
2. Be bypassable via logout-reconnect-replay.

DAG-structural keying closes both.

## L4-tunable surfaces

- Down-weighting algorithm.
- Self-citation threshold (seed 80%).
- Causal-distance window.

L1 commits the structure: novelty score + echo-chamber detection; not the parameters.
