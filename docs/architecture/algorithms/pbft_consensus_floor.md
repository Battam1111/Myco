> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# PBFT — Population Consensus Floor (seed protocol)

Canonical algorithm reference for **L2/FEDERATION §6.5.c**.

## Protocol family

PBFT Tendermint-style: O(N²) communication per round; finalization-deterministic; substrate-attested vote semantics. L4 may substitute HotStuff or a synchronous-network variant; L2-attestable.

Excluded:

- Proof-of-work (incompatible with L0 P11 metabolic economy).
- Proof-of-stake (Myco has no economic-stake substrate).
- Gossip-only without explicit finalization (incompatible with L0 P6 causal DAG).

## Byzantine-fault bound

`f ≤ ⌊(N-1)/3⌋`; honest 2/3+1.

| N (peers) | f tolerated |
|---|---|
| 3 | 0 |
| 4 | 1 |
| 7 | 2 |
| 10 | 3 |

Substrate emits `byzantine_threshold_check(N, f_tolerated, votes_received, votes_consistent)` per round.

## Voting

Each peer signs with the FED_HELLO-pinned `signer_pubkey` (see L2/FEDERATION §10).

Vote fields:

- `claim_type`, `claim_payload` (canonical-bytes), `claim_hash` (BLAKE3).
- `peer_substrate_id`, `peer_signature` over `canonical_bytes(Map({"context": "myco-population-vote-v1", "claim_type", "claim_hash", "peer_substrate_id", "round_id"}))`.
- `round_id` (monotonic per-claim; replay prevention).
- `peer_dag_tip_at_vote` (freshness).

Context `myco-population-vote-v1` is distinct from `myco-fed-hello-v1` and `myco-self-euthanasia-v1` — prevents cross-protocol replay.

## Quorum certificate

≥2/3 distinct-peer votes within L1-tunable timeout (seed 30 wall-clock minutes) → emit `population_consensus_reached:{claim_type}` DAG event:

`(claim_type, claim_hash, claim_payload, round_id, quorum_size, peer_votes (list (peer_substrate_id, peer_signature) self-verifying), reached_at_cycle)`.

Content-addressed BLAKE3. Downstream cites as proof without re-running. Wrapped per L2/FEDERATION §9 (authority from embedded `peer_votes`, not wrapping).

## No-consensus / pending

Timeout without quorum → `population_consensus_pending(claim_type, claim_hash, round_id, votes_received, timeout_elapsed_at)`; indefinite; substrate never acts until future quorum.

>7 consecutive timeouts → `population_consensus_stuck:{claim_type}` immune. Pairwise normal for non-population claims; P14/P11 unaffected.

## Composition with L0 principles

- P1.c: consensus on claims, not identity.
- P5: consensus-passive; CI-attested.
- P6: DAG with `causal_in_edges`.
- P7: self-euthanasia regardless of pending.
- P11: voting feeds signal #8 (high-rate → `consensus_cost_elevated`).
- P14: optional `consensus_participation` sub-criterion.
- I7: spawned child does NOT inherit consensus state.
