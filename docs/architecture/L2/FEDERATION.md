> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L2 — Federation Doctrine

> **Scope**: inter-substrate cross-cut. Cross-cuts L0 P5/P8/P1.c/P9 + P15 + L1/GOVERNANCE §4.3/§5 + L1/SCHEMA §3 + L1/SKIN §3.1 + I7 + I8. All numeric thresholds L1-tunable unless specified.

---

## §1. What federation IS

**Inter-substrate semantic transfer**: peer receives originating substrate's distilled material (sporocarps, refined decisions, schema-evolution markers) as deltas; peer metabolism absorbs and reshapes. Extends P5 beyond single substrate. **Mycelial network** = population linked via parent-child reproduction + peer coupling. Below consensus floor (§6.5; ≤2 peers): pairwise-trust + owner-attestation. At ≥3 peers: population claims require BFT consensus.

---

## §2. Reproduction modes (P8)

Three modes bounded by L0/cards/P08_eternal_reproduction.md (generation limits) generation limits (L1/GOVERNANCE §4.3 + §16). Each child is Cultivar with own Cultivator (typically inherited; transferable per L0/META §1 + L0/cards/P01_agent_primary.md §4):

- **§2.1 Federation** — semantic transfer; bidirectional possible.
- **§2.2 Cloning** — full copy; child has OWN substrate-ID + DAG (backup, geo-redundancy, archival).
- **§2.3 Cross-pollination** — ≥2 parents; spore-schema combines contributions.

---

## §3. Identity carrier (P1.c)

Each substrate has own `substrate-ID`, owner key history, DAG, P9 boundary. Spawned child has DIFFERENT agent-identity continuum than parent. **Federation transfers content, not identity** — structural reason cross-substrate trust is non-transitive (§6.4) + grounding for §9 wrapped-events.

---

## §4-§5. Spore + closure

§4 spore-schema: L1/SCHEMA §3.1 + §3.2 canonical field set; child starts with own genesis sporocarp; parent DAG records `federation_coupling` edge.

§5 closure verification (I7): L1/SCHEMA §3.3 + L1/GOVERNANCE §4.3 — parent static-schema validation → child I3 as first cycle → owner anchor co-sign. Failure aborts pre-`federation_coupling`; partials GC'd. Success emits `genesis_attested`. §5.1 immune-summary inheritance: unresolved CI-grade signals → child enters birth-period `quarantined`.

---

## §6. Discovery + peer-trust

- **§6.1 Discovery** — L1/GOVERNANCE §5.1: p2p / owner-attested list (default) / hub-and-spoke / hybrid.
- **§6.2 Freshness** — L1/GOVERNANCE §5.2: L1-bounded window (default 90 active-operation days); past → `peer_attestation_stale`; past grace → `untrusted_federation`.
- **§6.3 Aggregate re-attestation** — owner signs peer-set Merkle root + diff; O(1) owner, O(N) verification.
- **§6.4 Non-transitivity** — A↔B + B↔C does NOT give A↔C; each pairwise requires owner attestation; P15 (§6.5) operates over shared claims, not chained trust.

### §6.5 Population-level consensus floor

- **§6.5.a Activation** — BOTH peer-count ≥3 AND population-level claim (§6.5.b). 2→3 emits `consensus_floor_activated(peer_count, activation_cycle, peer_set_merkle_root)`; 3→2 emits `consensus_floor_deactivated`. Bypass = `C49_consensus_floor_bypass`.
- **§6.5.b Taxonomy** — three population-only claim classes: (1) peer revocation by another peer (≥2/3 quorum; accused cannot self-revoke); (2) universal-junk raw_material classification; (3) cross-substrate aggregate observability metrics (L2/OBSERVABILITY §9). Pairwise: freshness §6.2; per-peer P12; trust §6.4 non-transitive; per-peer owner revocation.
- **§6.5.c-h Protocol** — PBFT Tendermint-style; see `algorithms/pbft_consensus_floor.md` for FT bound `f ≤ ⌊(N-1)/3⌋`, voting context `myco-population-vote-v1`, quorum-certificate schema, timeout/pending behavior, composition with P1.c/P5/P6/P7/P11/P14/I7.

---

## §7-§8. Event flow

§7 egress (L1/SKIN §3.1 + L1/GOVERNANCE §5.3): per-emission freshness + non-revocation; per-peer-per-day rate-limit (spike → `federation_egress_saturation`); canonical low-entropy serialization; `federation_coupling` DAG edges record `(peer_substrate_id, aggregate_reattestation_root_at_emission, peer_inclusion_merkle_path)` self-contained proof.

§8 intake (L1/SKIN §2): envelope integrity + freshness + absorb as gradient delta; metabolism may fruit sporocarp with `federation_coupling` to source. Subject to P2 + I6. **Peer events MUST be wrapped per §9 before insertion** — SECURITY-CRITICAL.

---

## §9. Wrapped-events architecture

Cascades L0 P1.c + P9 + I4: peer substrate-IDs DISTINCT carriers; peer DAGs DISTINCT Merkle chains; peer integuments DISTINCT boundaries. Peer events MUST be wrapped as "I heard X say Y" attestations, never grafted. Attack class: peer pushes `operator_pinned`/`cycle_advanced`/`genesis_event` direct-insert → cross-substrate parent edges → identity hijack or state wipe.

- **§9.1 Envelope** — wrapper `node_type = "federation_received:{peer_id_prefix}"` (first 8 hex bytes / 16 chars). Full field set + types + allowed/banned inner prefixes: `schemas/federation_received.json`.
- **§9.2 Parent rule (security-critical)** — wrapper parent = THIS substrate's local DAG tip at ingest. NEVER peer parent_hashes. Preserves Merkle validity; peer chains never merge.
- **§9.3 Semantics** — "I heard X say Y" testimony, not adoption. Receiver MAY treat inner as `raw_material:` (P2 + I8); aggregate multi-peer same-content as P15 input.
- **§9.4 Allowed inner prefixes** — allowlist + banned set in `schemas/federation_received.json`. Banned → reject + `C35_federation_substrate_private_event_injection`.
- **§9.5 Idempotency** — re-pull → identical wrapper (deterministic + canonical-bytes); content-hash idempotent.
- **§9.6 Composition with §6.5** — P15 quorum cert crosses federation as `federation_received:{cert_origin_peer_prefix}`; receiver verifies embedded `peer_votes` using each peer's §10 pinned `signer_pubkey`. Quorum self-evidenced; wrapping = provenance, not authority.

---

## §10. Ed25519 FED_HELLO mutual auth

Cascades L0 P9 + P1.c + §6.5.e (pinned `signer_pubkey` for population votes). Context `myco-fed-hello-v1`; signing input + legacy fallback + TOFU + tamper response in `schemas/fed_hello_signing.json`.

- **§10.2 Pinning** — first FED_HELLO pins `(peer_substrate_id, pinned_signer_pubkey, pinned_at_cycle)`; subsequent must match BOTH. Mismatch → reject + `C39_federation_hello_signature_invalid`.
- **§10.3 Legacy peer** — substrate-ID-TOFU only; consensus-passive (counted in §6.5.d N; no votes); deprecation horizon (seed 12 months) → `federation_legacy_peer_horizon_expired`.
- **§10.4 Mutual asymmetry** — initiator → receiver verify → ACK signed → initiator verify. Either fail → BOTH emit C39.

---

## §11. Recursive injection defense

§9.4 allowlist applies only to OUTERMOST inner type; attacker smuggles banned inner via nested `federation_received:` wrappers (matches own prefix → layered laundry). Full attack + recursive-validation algorithm + max-depth (seed 5) + rejection cascade + per-peer rate-limit + composition: `algorithms/federation_recursive_validation.md`. Emits **C43 `federation_recursive_injection`** (depth-exhaustion) or C35 (banned-type-at-depth).

---

## §12-§14. Network shape + observability + limits

§12 network shape: mycelial network = genealogy (P8) + coupling (§9) + aggregation + consensus (§6.5). Doctrine: identity per-substrate (P1.c); trust pairwise below floor + population above; reproduction generation-bounded (I7); peer events wrapped (§9); recursive bounded (§11); FED_HELLO mutually authenticated (§10); independently mortal (P7).

§13 observability — see **L2/OBSERVABILITY §10** for #4a/#4b. Federation-specific: `consensus_participation_rate`; `byzantine_witness_lag`; `fork_resolution_latency`; `federation_legacy_peer_count`; `federation_hello_signature_burst`; `federation_peer_recursive_attack_burst`; `federation_received_event_count`. Consensus signals NULL until §6.5 active.

§14 limits — peer-compromise detection: freshness catches staleness; subtler drift needs owner-monitoring OR §6.5 ≥2/3 revocation. Cross-substrate trust non-transitive. Wrapped-events one-way receiver-protective. FED_HELLO protects identity asymmetry, NOT key compromise. Consensus floor adds safety not liveness; partition → `population_consensus_pending` indefinitely.
