# L2 — Federation Doctrine

> **Status**: DRAFT 2 (2026-05-17). M26-cascade for L0 DRAFT 9 SEALED.
> **Scope**: inter-substrate cross-cut. Cross-cuts L0 P5/P8/P1.c/P9 + P15 (retracted from L0 per G-9.b) + L1_GOVERNANCE §4.3/§5 + L1_SCHEMA §3 + L1_SKIN §3.1 + I7 + I8.

---

## §1. What federation IS

Federation is **inter-substrate semantic transfer** (not byte-level sync, not API integration). Federated peer receives originating substrate's distilled material (sporocarps, refined decisions, schema-evolution markers) as deltas; peer's metabolism absorbs and reshapes. Extends P5 beyond a single substrate's interior. The **mycelial network** is the population linked via parent-child reproduction edges + peer coupling edges. Below the consensus floor (§6.5; ≤2 peers), federation = pairwise-trust + owner-attestation. At ≥3 peers, population-level claims require Byzantine-fault-tolerant consensus.

---

## §2. Reproduction modes (per L0 P8)

Three modes; each bounded by L0 §16 generation limits (depth + rate + per-parent quota at L1_GOVERNANCE §4.3 + §16). Each instantiates Cultivation at the child (L0 §1.2/§1.4/§15): new substrate is a Cultivar with its own Cultivator (typically inherited from parent at spawn-time co-attestation; transferable per L0 §1.4):

- **§2.1 Federation** (semantic transfer to existing child): identify peer; emit federation sporocarps containing canonical-bytes; peer absorbs as deltas. Continuous; bidirectional possible.
- **§2.2 Cloning** (full substrate copy): child spawned with parent's full state as spore-schema. Child has parent's content but OWN identity (substrate-ID, attestation chain, DAG from genesis). Use case: backup, geographical redundancy, archival forks.
- **§2.3 Cross-pollination** (≥2 parents): child's spore-schema combines content from ≥2 parents; each contribution recorded in genesis sporocarp. Use case: collaborative cognition.

L4 picks default; substrate canon specifies which modes substrate participates in.

---

## §3. Identity carrier across federation (P1.c)

Per L0 P1.c: each substrate has its own `substrate-ID`, owner key history (Cultivator-side transferable; substrate-ID fixed at genesis), DAG, operator-connections, P9 boundary (state_dir + process + skin endpoints — federation does NOT merge integuments). Spawned child has DIFFERENT agent-identity continuum than parent. **Federation transfers content, not identity.** This is the structural reason cross-substrate trust is NOT transitive (§6.4) and the grounding for §9 wrapped-events.

---

## §4. Spore-schema (parent → child)

Included/not-included field set per **L1_SCHEMA §3.1 + §3.2** (canonical). Child starts with own genesis sporocarp. Parent-child link in parent's DAG is `federation_coupling` edge to child-substrate-ID.

---

## §5. Closure verification (I7)

Spawn per **L1_SCHEMA §3.3 + L1_GOVERNANCE §4.3**: parent's static-schema validation against current spore-schema-hash for I7 field set → child runs own I3 as first cycle → owner co-signs at anchor surface. Failure aborts spawn before `federation_coupling` commits; partial spawns GC'd. Success emits `genesis_attested` sporocarp in parent's DAG.

### §5.1 Immune-summary inheritance

Spore-schema carries parent's outstanding immune-signal summary. Unresolved CI-grade signals at spawn → child enters birth-period `quarantined` until owner re-attests (prevents spawning to launder pathology).

---

## §6. Federation discovery + peer-trust

- **§6.1 Discovery modes** (L1_GOVERNANCE §5.1): peer-to-peer broadcast / owner-attested peer list (default; strongest isolation) / hub-and-spoke registry / hybrid.
- **§6.2 Peer-trust freshness** (L1_GOVERNANCE §5.2): L1-bounded window (default 90 active-operation days); within → events flow; past → `peer_attestation_stale` + queue re-attestation; past grace (default 30 days) → reject + `untrusted_federation`. Revocation list at anchor rejects immediately.
- **§6.3 Aggregate re-attestation**: owner issues `federation_peer_set_reattestation` signing peer-set Merkle root + diff. Owner workload O(1) per period; verification O(N).
- **§6.4 Cross-substrate trust NOT transitive**: A↔B and B↔C → A does NOT auto-trust C. Each pairwise requires owner attestation (L1_GOVERNANCE §5.4); transitivity would let compromised B route untrusted-C content under B's authority. P15 (§6.5) does NOT make trust transitive — consensus operates over shared claims (§6.5.b), not chained trust.

### §6.5 Population-level consensus floor (P15 landing per G-9.b/G-7.c)

- **§6.5.a Activation**: BOTH (1) peer count ≥3 (L0 floor; L1 may tighten) AND (2) population-level claim (§6.5.b). Below: pairwise + owner-attestation; consensus dormant. Above: Byzantine protocol (§6.5.c) ONLY valid mechanism; bypass = `C49_consensus_floor_bypass`. 2→3 crossing emits `consensus_floor_activated(peer_count, activation_cycle, peer_set_merkle_root)`; 3→2 emits `consensus_floor_deactivated` (in-flight votes → `population_consensus_pending` indefinitely; no retroactive pairwise).
- **§6.5.b Taxonomy** (single-peer cannot legitimately decide; truth involves federation-as-aggregate): (1) **Peer revocation by another peer** — accused cannot self-revoke; ≥2/3 quorum required (single accuser would let compromised peer revoke all); (2) **Universal-junk raw_material classification** — population-wide spam fingerprint at all intakes (vs independent P12); (3) **Cross-substrate aggregate observability metrics** — L2_OBSERVABILITY §9 federation-network signals emitted only at quorum. Pairwise (below floor): peer freshness §6.2; per-peer P12; trust establishment §6.4 non-transitive; per-peer owner revocation (O(1) anchor list). L4 may extend; CI-attested.
- **§6.5.c Protocol**: PBFT Tendermint-style (O(N²)/round; finalization-deterministic; substrate-attested vote semantics). L4 may pick HotStuff/synchronous-network variant; L2-attestable. Excluded: proof-of-work (incompatible P11); proof-of-stake (no economic-stake); gossip-only without finalization (incompatible P6).
- **§6.5.d FT bound**: `f ≤ ⌊(N-1)/3⌋` (honest 2/3+1). N=3→f=0; N=4→f=1; N=7→f=2; N=10→f=3. Substrate emits `byzantine_threshold_check(N, f_tolerated, votes_received, votes_consistent)`.
- **§6.5.e Voting**: each peer signs with FED_HELLO-pinned `signer_pubkey`. Vote carries `claim_type, claim_payload (canonical-bytes), claim_hash (BLAKE3), peer_substrate_id, peer_signature` over `canonical_bytes(Map({"context": "myco-population-vote-v1", "claim_type", "claim_hash", "peer_substrate_id", "round_id"}))`, `round_id` (monotonic per-claim; replay prevention), `peer_dag_tip_at_vote` (freshness). Context distinct from `myco-fed-hello-v1` + `myco-self-euthanasia-v1` — prevents cross-protocol replay.
- **§6.5.f Quorum certificate**: ≥2/3 distinct-peer votes within L1-tunable timeout (seed 30 wall-clock min) → emit `population_consensus_reached:{claim_type}` DAG event `(claim_type, claim_hash, claim_payload, round_id, quorum_size, peer_votes (list (peer_substrate_id, peer_signature) self-verifying), reached_at_cycle)`. Content-addressed BLAKE3; downstream cites as proof without re-running. Wrapped per §9 (authority from embedded `peer_votes`, not wrapping).
- **§6.5.g No consensus / pending**: timeout without quorum → `population_consensus_pending(claim_type, claim_hash, round_id, votes_received, timeout_elapsed_at)`; indefinite; substrate never acts until future quorum. >7 consecutive timeouts → `population_consensus_stuck:{claim_type}` immune. Pairwise normal for non-population claims; P14/P11 unaffected.
- **§6.5.h Composition**: P1.c consensus-on-claims-not-identity; P5 consensus-passive CI-attested; P6 DAG with `causal_in_edges`; P7 self-euthanasia regardless of pending; P11 voting feeds signal #8 (high-rate → `consensus_cost_elevated`); P14 optional `consensus_participation` sub-criterion; I7 spawned child does NOT inherit consensus state.

---

## §7. Federation event flow (egress)

Per L1_SKIN §3.1 + L1_GOVERNANCE §5.3:

- **§7.1 Per-emission freshness**: every outbound verifies target peer freshness + non-revocation; stale/revoked → suppress + `federation_egress_blocked` immune.
- **§7.2 Egress rate-limiting**: per-peer-per-day volume at anchor; spike → `federation_egress_saturation` (covert-channel defense).
- **§7.3 Canonical low-entropy serialization**: sorted-key, normalized-whitespace, fixed-precision-numeric. Limits covert-channel bandwidth.
- **§7.4 `federation_coupling` DAG edges** (L1_TROPISM §B8): record `(peer_substrate_id, aggregate_reattestation_root_at_emission, peer_inclusion_merkle_path)` — self-contained "trusted at this emission" proof; verifiable without chain-walking subsequent re-attestations.

---

## §8. Federation event flow (intake)

Peer egress arrives as delta at intake endpoint (L1_SKIN §2). Handling: envelope integrity check (sender = peer; sender_token = peer signing identity); freshness check; absorb as gradient delta; metabolism may fruit sporocarp with `federation_coupling` edge to source. Intake is **substrate-mediated** (not direct content insertion); subject to P2 + I6. **Peer events wrapped per §9 before insertion** — SECURITY-CRITICAL: prevents peer events from contaminating this substrate's Merkle chain.

---

## §9. Wrapped-events architecture (M25.4 sealed)

Cascades from L0 P1.c + P9 + I4: peer substrate-IDs DISTINCT carrier identities; peer DAGs DISTINCT Merkle chains; peer integuments DISTINCT boundaries. Peer events MUST be wrapped as "I heard X say Y" attestations, never grafted. Pre-fix attack: malicious peer pushes `operator_pinned`/`cycle_advanced`/`genesis_event` → direct insert creates cross-substrate parent edges → hijacks receiver identity or wipes state.

**§9.1 Envelope schema** — wrapper `node_type = "federation_received:{peer_id_prefix}"` (first 8 hex bytes / 16 chars of peer substrate-ID). Content (canonical-bytes Map):

| Field | Type | Semantics |
|---|---|---|
| `from_peer_substrate_id` | Bytes(32) | Peer's full substrate-ID |
| `peer_event_node_type` | String | Inner `node_type`; §9.4 allowlist + §11 recursive validation |
| `peer_event_parent_hashes` | Array(Bytes(32)) | Peer-side parents; provenance only, NOT wrapper parents |
| `peer_event_content_canonical_bytes` | Bytes | Inner canonical-bytes content |
| `peer_event_original_hash` | Bytes(32) | BLAKE3 `merkle_hash(parent_hashes, content_canonical_bytes)`; proves exact event seen |
| `peer_event_created_at_cycle` | Uint | Inner `created_at_cycle` (peer-side) |

**§9.2 Parent rule (security-critical invariant)** — wrapper's parent = THIS substrate's local DAG tip at ingest. NEVER peer's parent_hashes. Preserves Merkle validity: tip depends only on events whose `causal_in_edges` are reconstructible from THIS substrate. Peer chains never merge. Cross-chain merge (banned) makes Merkle root peer-dependent + trust transitive; "I heard X say Y" keeps single-chain integrity + pairwise trust.

**§9.3 "I heard X say Y" semantics** — `federation_received:{prefix}` asserts ONLY: "at receiver-cycle K, this substrate ingested wrapped attestation that peer P emitted event type T content hash H at peer-cycle J, peer-parents [...]." Testimony, not adoption. Receiver does NOT trust inner semantics (P2 envelope-gated + P12), adopt inner parent_hashes as causal history (informational only), verify peer's `causal_in_edges` (peer's I4). Receiver MAY treat inner as `raw_material:` (P2 + I8); fruit citing wrapper hash as `causal_in_edges` (wrapper first-class causal evidence); aggregate same-content multi-peer wrappers as "many-peer-corroboration" (P15 input per §6.5.b).

**§9.4 Allowed inner node_type prefixes** — enforced at ingest by `is_federation_safe_node_type` (`myco_substrate/src/federation/protocol.rs`):

| Allowed prefix | Semantics |
|---|---|
| `raw_material:` | Peer's environmental ingestion (P2) |
| `sporocarp:` | Peer's fruiting (causal-only; no receiver state mutation) |
| `mutation:` | Peer's mutation audit trail (observability only) |
| `immune:` | Peer's immune sporocarps (cross-substrate pathology observability) |
| `federation_received:` | Recursive wrapper; §11 recursion bound applies |

Banned (reject + `C35_federation_substrate_private_event_injection`): `operator_pinned:*` (hijacks TOFU); `cycle_advanced:*` (corrupts metabolic time); `genesis_event:*` (re-genesis attempt); non-allowlisted defaults reject. L4 may extend (CI-attested).

**§9.5 Idempotency** — re-pull produces identical wrapper (deterministic fields + canonical-bytes); DAG `insert_node` content-hash idempotent; re-pull no-op on duplicate. Composes with §8 freshness: stale peer events still wrappable.

**§9.6 Composition with §6.5 consensus** — when floor active, P15 quorum certificate crosses federation as `federation_received:{cert_origin_peer_prefix}` wrapping. Receiver verifies embedded `peer_votes` signatures using each peer's §10 pinned `signer_pubkey`. Quorum self-evidenced; wrapping is provenance, not authority.

---

## §10. Ed25519 FED_HELLO mutual authentication (M25.4 sealed)

Cascades from L0 P9 (FED_HELLO is skin endpoint) + P1.c (distinct carriers; symmetric pinning) + §6.5.e (pinned `signer_pubkey` used for population votes).

- **§10.1 Context**: `myco-fed-hello-v1` (fixed; rotated only via CI). Distinct from `myco-self-euthanasia-v1` (M23.2) + `myco-population-vote-v1` (§6.5.e) → prevents cross-protocol replay.
- **§10.2 Signing input** (canonical-bytes sorted-key Map):

  ```
  canonical_bytes(Map({
    "context":           String("myco-fed-hello-v1"),
    "peer_substrate_id": Bytes(32),
    "dag_tip":           Bytes(32),
    "protocol_version":  Uint
  }))
  ```

  Signed with substrate's federation signing key (identity-signing or derived sub-key; L1-tunable).
- **§10.3 TOFU + signer_pubkey pinning**: first FED_HELLO from `peer_substrate_id` → verify Ed25519 with `signer_pubkey`; pin `(peer_substrate_id, pinned_signer_pubkey, pinned_at_cycle)`; tampered → reject + `C39_federation_hello_signature_invalid`. Subsequent HELLOs MUST match pinned key. Peer-side rotation is CI-attested at peer's anchor; rotated event wrapped per §9; requires owner-attested re-pinning.
- **§10.4 Legacy peer fallback**: both fields absent = pre-M25.4 peer; accepted under substrate-ID-TOFU only; emits `federation_legacy_peer_pinned` (NOT immune); `pinned_signer_pubkey = None`. **Cannot sign population votes** — consensus-passive (counted in §6.5.d N, contributes no votes). L1 deprecation horizon (seed 12 wall-clock months); post-horizon → reject + `federation_legacy_peer_horizon_expired`.
- **§10.5 Tampered signature**: both fields present, Ed25519 fails → reject (no pin, no transition) + C39 recording (substrate-ID, attempted pubkey hex prefix, context prefix). Persistent same-IP → `federation_hello_signature_burst` (L1-tunable; immune >10/hour). Detector: `verify_fed_hello_signature`.
- **§10.6 Mutual asymmetry**: initiator HELLO → receiver verifies → HELLO_ACK signed → initiator verifies. Either-side fail → terminate + BOTH emit C39. Pinning per-direction (A pins B; B pins A). Closes pre-M25.4 origin-asymmetry where receiver-only TOFU let attacker first-connecting under victim's substrate-ID occupy slot; now both sides require fresh Ed25519, unforgeable without victim's private key.

---

## §11. Recursive injection defense (SECURITY-CRITICAL; M27 impl)

Without this defense, §9 is bypassable via recursive nesting: §9.4 allowlist applies only to OUTERMOST inner `node_type`; attacker smuggles banned inner via nested `federation_received:` wrappers (matches own prefix → layered laundry).

- **§11.1 Attack**: malicious peer X builds inner `federation_received:peer_X/operator_pinned`; wraps in OUTER `federation_received:peer_Y`; receiver §9.4 sees outer inner prefix-matches → accept; DAG now contains wrapper attesting banned `operator_pinned` as observed-via-federation; downstream P12 may mistake smuggled claim as legitimate cross-substrate evidence.
- **§11.2 Defense (recursive inner validation)**:

  ```
  function validate_federation_inner(content_canonical_bytes, depth, max_depth):
      if depth > max_depth:
          reject ("federation_recursive_depth_exceeded")
          emit C43_federation_recursive_injection (cascade_flag=true)
          return Rejected
      decoded = cb_decode(content_canonical_bytes)
      inner_node_type = decoded["peer_event_node_type"]
      if not is_federation_safe_node_type(inner_node_type):
          reject (inner_node_type)
          emit C35_federation_substrate_private_event_injection (cascade_flag=true, depth=depth)
          return Rejected
      if inner_node_type.starts_with("federation_received:"):
          return validate_federation_inner(decoded["peer_event_content_canonical_bytes"], depth + 1, max_depth)
      return Accepted

  validate_federation_inner(outer_wrapper.content, depth=0, max_depth=L1_max_recursion_depth)
  ```

- **§11.3 Max depth**: seed `max_recursion_depth = 5`. Depth=0 = outermost; depth-exceeded → reject OUTERMOST (partial acceptance forbidden). L1 may tighten (3) or relax (7); CI-attested.
- **§11.4 Rejection cascade**: reject ENTIRE outermost envelope (layers 0..N-1's testimony was *about* layer N). Emit C35 (banned inner at depth N: `cascade_flag=true, depth=N, inner_node_type=T, peer_substrate_id`) OR C43 (depth-exceeded: `attempted_depth=N+1, peer_substrate_id`). Per-peer rate-limit (seed 3 rejections / 24 wall-clock hours) → `federation_peer_recursive_attack_burst` + propose peer revocation (below floor: owner-attested; above: P15 §6.5.b.1).
- **§11.5 C43 row** (A6 cascade):

  | ID | Name | P-cov | I-cov | Detector | Semantics |
  |---|---|---|---|---|---|
  | C43 | `federation_recursive_injection` | P9 + P15.guard | I8 | `myco_substrate/src/server.rs` (M27) | Depth exceeded; outermost rejected; `attempted_depth + peer_substrate_id` |

  C43 vs C35: C35 = banned-type-at-some-depth; C43 = depth-exhaustion.
- **§11.6 Composition**: §11 extends §9.4 to every depth. §10 transport-auth irrelevant (content validation; valid-FED_HELLO peer still subject to §11). §6.5 quorum cert at depth-1 has allowlist-validated content + embedded `peer_votes` §10 Ed25519-verified — depth-bypass still fails signature verification.

---

## §12. Network shape (the mycelial population)

Federated substrates form a mycelial network: genealogy edges (parent→child P8); coupling edges (peer-to-peer §9-wrapped); aggregation (hub substrates from many spokes); consensus edges (§6.5-active quorum certificates).

Doctrine commits: each substrate carries its own identity (P1.c); trust pairwise below floor (non-transitive §6.4), population-level above (§6.5); reproduction structural + generation-bounded (I7), content transfer semantic; peer events wrapped per §9 not grafted; recursive wrapping depth-bounded §11; FED_HELLO mutually Ed25519-authenticated §10; each substrate independently mortal (P7), others persist; each is Cultivar with own Cultivator (L0 §1.2/§1.4/§15).

---

## §13. Federation health observability

Signals #4a/#4b at **L2_OBSERVABILITY §10** + §2.1. Divergence = mycelial fragmentation. Federation-specific signals (not in 10-signal Living Bets):

- `consensus_participation_rate` (§6.5 active): per-claim quorum-cert completion; declining → voting-fragmentation.
- `byzantine_witness_lag`: per-claim wall-clock first-vote→quorum; up → throughput stress.
- `fork_resolution_latency`: per-claim cycles first-dissenting-vote → quorum-cert/pending finalization.
- `federation_legacy_peer_count` (M25.4): peers without pinned `signer_pubkey`; → 0 post-horizon.
- `federation_hello_signature_burst`: persistent C39 from one IP/peer (immune if >10/hour).
- `federation_peer_recursive_attack_burst`: persistent C35/C43 from one peer (§11.4).
- `federation_received_event_count`: cumulative ingested wrappers.

Consensus signals NULL until §6.5 active; legacy signal nonzero only during M25.4 transition.

---

## §14. Federation limits

- Substrate cannot detect peer compromise; freshness catches staleness; subtler drift needs owner-monitoring OR §6.5 ≥2/3 quorum revocation.
- Content canonical-bytes verifiable (§10 + §9); semantics NOT validatable beyond §9.4 allowlist + §11 recursive validation.
- Aggregate re-attestation: O(1) owner workload + O(N) verification cost.
- Cross-substrate trust non-transitivity is a feature (P15 operates over shared claims, not chained trust).
- Wrapped-events one-way receiver-protective: Merkle stays valid; cannot validate peer's `causal_in_edges` (§11.6).
- FED_HELLO mutual auth protects identity asymmetry NOT key compromise; peer key exfiltration enables impersonation.
- Recursive defense bounded-depth (L1-tuned).
- Consensus floor adds safety not liveness; partition → `population_consensus_pending` indefinitely; pairwise continues.

---

## §15. Glossary

Cultivator / Cultivar / Cultivation see **L0 §12**. Each peer is separate Cultivar with own Cultivator; reproduction produces Cultivars with distinct substrate-IDs.

- **federation_received** (§9; M25.4): wrapper prefix `federation_received:{peer_id_prefix}` (first 8 hex bytes); schema §9.1.
- **wrapped-events architecture** (§9; M25.4): SECURITY-CRITICAL; peer events ingested as wrappers parented to receiver's local DAG tip; "I heard X say Y" not Merkle-merge.
- **recursive injection defense** (§11): bounded-depth recursive inner validation (seed depth 5).
- **population-level claim** (§6.5): claim crossing consensus floor (≥3 peers + §6.5.b taxonomy) requiring BFT agreement.
- **consensus floor** (§6.5): ≥3 peers + population claim; below = pairwise.
- **quorum certificate** (§6.5.f): self-verifying DAG event with embedded signed votes.
- **legacy peer** (§10.4): FED_HELLO without `signer_pubkey`/`hello_signature`; substrate-ID-TOFU only; consensus-passive; deprecated at L1-tunable horizon.
- **TOFU**: M25.4 pins `(substrate_id, signer_pubkey)` jointly; subsequent connections must match BOTH.
