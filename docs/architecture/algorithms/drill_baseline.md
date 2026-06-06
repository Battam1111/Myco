> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4). See `docs/architecture/OUTLINE.md` §3 for details.

---

# `drill_baseline`: Two-baseline recovery-drill failure-rate tracking

> **Status**: REFERENCE ALGORITHM. Extracted from L1/SCHEMA §2.4 to keep active doctrine lean. Authoritative spec at **L1/SCHEMA §2.4** (commitment) + this file (consolidated algorithm).

---

## §1. Drill scopes + cadence

- **Hot+warm drill**: every 100 substrate-days (L1-tunable [30, 365]). Full restore + verify I1/I3/I4/I5/I8/I9/I10/I12. Fruits `recovery_drill_result`.
- **Cold-tier sampled drill**: every 1000 substrate-days (L1-tunable [365, 3650]). N = ceil(log₂(cold_count)) random nodes; sample indices substrate/DAG-tip-derived (keyless v3.1.5: seeded from the DAG-tip hash, not an anchor-minted nonce; the prior `AS_anchor_surface §3.5` anchor-nonce rule is retired); fruits `cold_tier_sample_recovery_pass`.

## §2. `recovery_drill_result` envelope

```
{
  "drill_id": <i64 substrate/DAG-tip-derived>,
  "scope": "hot_warm" | "cold_tier_sample",
  "outcome": "pass" | "fail" | "partial",
  "failure_classification": <enum or null>,
  "evidence_inputs": {
    "sampled_node_hashes": [Bytes(32), ...],
    "merkle_paths": [...],
    "recovery_canonical_bytes_hashes": [...],
    "drill_started_at_unix_ns": Timestamp,
    "drill_ended_at_unix_ns": Timestamp
  }
}
```

## §3. Near-baseline (rolling)

- `near_drill_failure_rate = failures_in_last_10_drills / 10` (per scope).
- ≥ 2σ departure from prior near-window → fire `drill_failure_near_baseline_departure` sporocarp.

## §4. Secular-baseline (anchored, never advances)

- Anchor: drills 6-15 form the anchored baseline rate (computed once; never re-anchored after birth period).
- `secular_trend_metric = current_rate / anchored_baseline`.
- Threshold L1-tunable, default 3× → fire `drill_aging_grade` sporocarp.
- Rationale: secular-baseline scales drift detection over decade time-horizons by preserving the young-self standard against current-self drift.

## §5. Witnesses-not-verdicts

Drill emits proof tuples `(sampled_node_hashes, merkle_paths, reproducible_inputs)`. Substrate does NOT emit pass/fail self-attestation; the verdict is re-derived by the cultivator at the live human-in-the-loop CI gate (keyless v3.1.5; was "anchor-side evaluation"; the witness layer is unchanged, only the evaluator moves from the anchor surface to the live human).

## §6. Mortality coupling

- Beyond recoverability budget AND medium fails → P7 (L0/cards/P04_eternal_iteration.md §3-§4 + L1/CONTINUITY mortality).
- Two consecutive failed drills → the substrate's own internal mortality signal `recovery_drill_failure` (keyless v3.1.5; acknowledged-debt: there is no external auto-emitter; the prior anchor-side `mortality_drill_failure` that "the substrate cannot suppress" is retired with the anchor surface, so the substrate self-reports). The un-suppressibility intent is preserved keyless by the MUST-NOT against silent self-destruction (L0/cards/P07_mortality.md §5.8 + L1/GOVERNANCE §4.4 single live whole-death channel).

## §7. Cascade

- L1 commitment: L1/SCHEMA §2.4.
- L1/GOVERNANCE §4.4: single live whole-death mortality channel (keyless v3.1.5; was "dual-channel"; the anchor auto-emit channel is retired, acknowledged-debt).
- L2/OBSERVABILITY: drill-result observability signal.
- L1/HARD_RULES C-row: relevant drift signals C30+ substrate-private namespace.
