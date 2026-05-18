> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# Telos Drift (Cosine Centroid Algorithm)

> Extracted from L1/TROPISM §F. Normative spec lives at L1/TROPISM §F (P14.c).

## Form

```
telos_alignment(cycle) = cos_sim(
    sporocarp_centroid(rolling_window, cycle),
    objective_embedding
)
```

- `sporocarp_centroid`: L2-normalized vector mean of canonical-bytes-rendered text of every daily-class sporocarp in rolling window. CI-class EXCLUDED (governance events ≠ behavior).
- `objective_embedding`:
  - Owner objective declared (P14.b): `embed(owner_stated_objective_text)`. Tier-1 SSoT.
  - No objective: `embed(agent_feedback_trajectory_recent)` (L1/TRAJECTORY-derived).

Per-substrate at genesis, CI; switching branches requires owner CI attestation.

## Window + cadence

- Window: seed 90 substrate-days (= L0/cards/LB_living_bets §3 (falsifiability quorum) Living Bets window).
- Cadence: digest-emission per L1/CONTINUITY §1.1 step 2.
- Branch-2 fallback: empty feedback-marked deltas → centroid over agent's last-K deltas (K = window cycle count).

## Drift threshold grading

| Cosine | Status | Sporocarp |
|---|---|---|
| ≥ 0.6 | aligned | none |
| 0.4 < ≤ 0.6 | drifting | `telos_alignment_low` (observability) |
| 0.2 < ≤ 0.4 | drift | `telos_drift` daily |
| 0.0 < ≤ 0.2 | drift | `telos_drift` elevated |
| ≤ 0.0 | drift | `telos_drift` CRITICAL (C24) |

## Causal proof

`causal_in_edges`: `(sporocarp_centroid_hash, objective_embedding_hash, cosine_value, rolling_window_start_cycle, rolling_window_end_cycle, embedding_model_identity_hash, template_version)`. I3 recomputes centroid from window sporocarp set.

## Embedding-model identity

- `embedding_model_identity = (model_name, model_version, model_canonical_bytes_hash)`.
- External API: hash of service-identity + service-attested version.
- Mutation: owner attestation per L1/GOVERNANCE §2.2.
- Spore-inheritable; CI-mutable post-genesis.
- Storage: parameters NOT in spore-schema; hash + reference (URI / OCI digest / local-path+checksum).
- Verification: substrate verifies bytes match hash each cycle (mismatch → I3 fail → quarantine).
- F-row: `F_embedding_model_identity`.
