> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# Echo-Chamber Detection (Trajectory-Injection Defense)

> Extracted from L1/TRAJECTORY §9. Normative spec lives at L1/TRAJECTORY §9.

## Attack

Agent floods deltas crafted to make `cluster_C` produce desired trajectory T; downstream trusts; immune-grade drift suppressed.

## Defense — delta-novelty weighting

Trajectory derivation down-weights deltas whose `causal_in_edges` (L1/TROPISM §B6) trace overwhelmingly to recent same-operator deltas (high self-citation, low external-anchor).

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
