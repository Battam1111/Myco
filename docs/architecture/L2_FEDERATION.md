# L2 — Federation Doctrine

> **Status**: DRAFT 2 (2026-05-17). Cross-cut doctrine theme. Cascaded for L0 DRAFT 9 SEALED (commit `e796451`).
> **Layer**: L2.
> **Scope**: inter-substrate doctrine — the population-level shape of Myco. Cross-cuts L0 **P5 (Universal Interconnection, Tier-Exempt-Permitted)** / **P8 (Eternal Reproduction, Generation-Bounded)** / **P1.c carrier-asymmetry** / **P9 (Single Integument)** + **P15 (Population-Level Consensus)** retracted from L0 to here per G-9.b/G-7.c + L1_GOVERNANCE §4.3 reproduction / §5 federation discovery & peer-trust freshness + L1_SCHEMA §3 spore-schema + L1_SKIN §3.1 federation egress / §3 output gating + I7 (Reproduction Closure, Generation-Bounded) reproduction closure / I8 inter-substrate edge in P5. Answers: how does v0.9 extend beyond a single substrate; what is the mycelial network shape; how do substrates trust each other without compromising P1.c; how does the substrate behave at population level (≥3 peers) where pairwise trust no longer suffices; how is the wrapped-events architecture security-hardened against recursive injection.

> **DRAFT 9 cascade additions** (this revision):
> - **§6.5 Population-level consensus floor** (P15 landing per G-9.b/G-7.c): activates at ≥3 federation peers + population-level claim taxonomy; PBFT-style Byzantine consensus; ≤(N-1)/3 fault tolerance.
> - **§9 Wrapped-events architecture** (M25.4 formal doctrine): `federation_received:{peer_prefix}` envelope schema; "I heard X say Y" attestation graph (NOT multi-substrate event-graph merge).
> - **§10 Ed25519 FED_HELLO mutual auth** (M25.4 formal doctrine): signing context `myco-fed-hello-v1`; TOFU + signer_pubkey pin; legacy peer fallback; C39 detector.
> - **§11 Recursive injection defense** (Phase γ.9 mycoparasite M11 SECURITY-CRITICAL): inner content of `federation_received:` envelopes MUST be recursively validated against allowed-prefix list to a bounded depth; C36 detector.
> - **§15 Glossary** expanded with Cultivation vocabulary (G-11.a) + new federation security terms.

---

## §1. What federation IS

Federation is **inter-substrate semantic transfer** (not byte-level file sync, not API integration). A federated peer substrate receives the originating substrate's distilled material (sporocarps, refined decisions, schema-evolution markers) as deltas into its own field. The peer's own metabolism absorbs and reshapes.

Federation extends **P5 (Universal Interconnection, Tier-Exempt-Permitted)** beyond a single substrate's interior. The **mycelial network** in v0.9's biology is the population of federated substrates linked via parent-child reproduction edges + peer coupling edges. **Below the population-level consensus floor (§6.5; ≤2 peers), federation operates under pairwise-trust + owner-attestation per DRAFT 8 inheritance. At and above the floor (≥3 peers), population-level claims (§6.5.b taxonomy) require Byzantine-fault-tolerant consensus.**

---

## §2. Reproduction modes (per L0 P8 Eternal Reproduction, Generation-Bounded)

Three modes produce federated substrates. **Each mode is bounded by L0 §16 generation limits** (depth bound + rate limit + per-parent quota; full mechanism at L1_GOVERNANCE §4.3 + §16). Each mode also instantiates the **Cultivation relationship** at the child (L0 §1.2 / §1.4 / §15): the new substrate is a Cultivar with its own Cultivator (typically inherited from parent at spawn-time owner co-attestation; transferable per L0 §1.4):

### §2.1 Federation (semantic transfer to existing child)

The originating substrate identifies a peer; emits federation sporocarps containing canonical-bytes of distilled state; peer absorbs as deltas. Continuous; bidirectional possible.

### §2.2 Cloning (full substrate copy)

A new child substrate is spawned with the parent's full state as the initial spore-schema. The child immediately has the parent's content but its OWN identity (own substrate-ID, own owner-attestation chain, own DAG starting from genesis).

Use case: backup substrates, geographical redundancy, archival forks.

### §2.3 Cross-pollination (multiple parents)

A new child substrate is spawned with spore-schema combining content from ≥2 parent substrates. Each parent's contribution is recorded in the child's genesis-event sporocarp.

Use case: merging insights from independent substrates; collaborative cognition.

L4 picks default mode; substrate canon at genesis specifies which modes the substrate participates in.

---

## §3. Identity carrier across federation (P1.c)

Per L0 P1.c carrier-asymmetry: the substrate is the identity carrier. Federation does NOT transfer identity:

- Each substrate has its own `substrate-ID` (owner-signed at its own genesis; P1.c carrier-asymmetry).
- Each substrate has its own owner key history (its own Cultivator key chain; the Cultivation relationship's Cultivator-side may transfer per L0 §1.4 / §15 succession, but substrate-ID is fixed at genesis).
- Each substrate has its own DAG.
- Each substrate has its own operator-connections.
- Each substrate has its own **P9 Single Integument** boundary (its own state_dir + process + skin endpoints — federation does NOT merge integuments).
- A child substrate spawned from a parent has a DIFFERENT agent-identity continuum than its parent.

**Federation transfers content, not identity.** This is the structural reason cross-substrate trust is NOT transitive (§6.4 below). It is also the doctrinal grounding for the wrapped-events architecture (§9): peer events do NOT graft into the receiver's Merkle chain; they are wrapped as "I heard peer say X" attestations whose parent is the receiver's own local tip.

---

## §4. Spore-schema (parent → child, per L1_SCHEMA §3)

When parent substrate spawns child:

**Spore-schema includes** (per L1_SCHEMA §3.1):
- Schema definitions (validated against parent's current SSoT)
- Canonical-bytes serializer specification (spore-inheritable; tier-1)
- Dispatch-form atomic-record type tree
- Classifier dimension table
- Initial appetite-axis schema (or equivalent under chosen dispatch)
- Anchor-surface configuration (incl. sealing mechanism)
- Parent's outstanding immune-signal summary

**Spore-schema does NOT include** (per L1_SCHEMA §3.2):
- Parent's full causal DAG (child starts own DAG from genesis)
- Parent's operator-token history (forbidden by I1)
- Parent's accumulated read-pattern norms (model-class epoch buckets per L0 §7 signal #6)

**Child starts with own genesis sporocarp.** Parent-child link in parent's DAG is a `federation_coupling` edge to the child-substrate-ID.

---

## §5. Closure verification (I7)

Spawn protocol verification (per L1_SCHEMA §3.3 + L1_GOVERNANCE §4.3):

1. Parent runs static-schema validation: child's spore-schema matches parent's current spore-schema-hash for the I7 field set.
2. Child runs own I3 self-validation as first metabolic cycle.
3. Owner co-signs spawn at anchor surface: `(parent-substrate-ID, child-substrate-ID, spore-schema-canonical-bytes-hash, anchor-surface-timestamp)`.

**Failure on any step aborts spawn BEFORE federation_coupling edge commits.** Partial spawns are GC'd by L1_CONTINUITY at next cycle.

**Success emits `genesis_attested` sporocarp** in parent's DAG.

### §5.1 Immune-summary inheritance (per pass-1 mycoparasite-13)

Spore-schema includes parent's outstanding immune-signal summary (counts of unresolved CI-grade immune sporocarps + most recent tip-hash). If parent had unresolved CI-grade immune signals at spawn, child enters birth-period in `quarantined` until owner re-attests intent. This prevents "spawning to launder unresolved pathology".

---

## §6. Federation discovery and peer-trust

### §6.1 Discovery modes (per L1_GOVERNANCE §5.1)

L4 picks from:
- **Peer-to-peer broadcast**: substrates announce on a shared discovery channel; potential peers attest interest; owner attests adoption per peer.
- **Owner-attested peer list** (default): owner curates list of approved peer substrate-IDs.
- **Hub-and-spoke registry**: a registry substrate aggregates peers; subordinate substrates discover through hub.
- **Hybrid**.

Default is owner-attested peer list: strongest isolation; lowest discovery automation.

### §6.2 Peer-trust freshness (per L1_GOVERNANCE §5.2)

Each peer's attestation has an L1-bounded freshness window (default 90 active-operation days):

- **Within freshness**: federation events flow normally.
- **Past freshness**: substrate emits `peer_attestation_stale`; federation events queue pending owner re-attestation.
- **Past additional grace** (default 30 days): events rejected; `untrusted_federation` immune event.

**Revocation list at anchor surface**: revoked peers' events are immediately rejected (no grace).

### §6.3 Aggregate re-attestation (per pass-2 saprotroph-17)

To avoid O(N) owner workload per period: owner MAY issue `federation_peer_set_reattestation` event signing the current peer-set Merkle root + diff against last commitment. Anchor surface displays diff (peers added/removed since last aggregate-reattestation); owner reviews diff (not full set); signs.

**Owner workload is O(1) per period; verification cost is O(N) at the anchor surface** (anchor surface re-computes Merkle root from enumerated peer list, not from substrate-supplied summary).

### §6.4 Cross-substrate trust is NOT transitive

If A federates with B and B federates with C, A does NOT automatically trust C. Each pairwise trust requires owner attestation.

**Rationale**: trust transitivity would let a compromised B route untrusted-C content into A under the guise of B's authority. Per L1_GOVERNANCE §5.4 explicit clause.

**Note on P15 (§6.5)**: population-level consensus does NOT make trust transitive. Consensus operates over **shared claims** (taxonomy in §6.5.b), not over chained trust. Even at ≥3-peer scale, A still attests each peer of A's pairwise; the consensus layer adds a quorum check on whether population-level claims are valid, not on whether A inherits B's trust list.

### §6.5 Population-level consensus floor (P15 landing)

> **DRAFT 9 cascade addition** (per L0 §2.3 G-9.b retraction + §17 G-7.c choice).
> **Doctrinal status**: P15 Population-Level Consensus retracted from L0 to L2_FEDERATION. Substrate-internal does not require consensus; federation-level Byzantine fault tolerance is L2 territory.

#### §6.5.a Activation threshold

The consensus floor activates when **both** conditions hold simultaneously:

1. **Peer count ≥ 3** federation peers in the substrate's active peer-set (owner-attested per §6.1/§6.2; revocation list at anchor surface). The threshold ≥3 is the **L0 floor**; L1 may tighten (e.g. ≥5) but never relax.
2. **Population-level claim** is being made or evaluated (taxonomy §6.5.b below).

Below the activation threshold (≤2 peers, OR claim is not population-level): **pairwise-trust + owner-attestation** per DRAFT 8 inheritance (§6.1–§6.4 above). The consensus mechanism is dormant — no Byzantine layer is invoked, no `population_consensus_*` events emit.

**Above the threshold**: the Byzantine consensus protocol (§6.5.c) is the **only** valid mechanism for the population-level claim to take effect. Bypass = breach (`C29_consensus_floor_bypass` per L1_HARD_RULES extension; A6 cascade).

**Floor crossing — activation event**: when the active peer-set count first crosses from 2 to 3 (or when a substrate is born into a federation that already has ≥3 peers), substrate emits `consensus_floor_activated` sporocarp recording (peer_count, activation_cycle, peer_set_merkle_root). Anchor surface co-attests at next CI boundary.

**Floor crossing — deactivation**: when active peer-set count drops from 3 to 2 (peer revocation or attestation expiry), the floor deactivates and substrate reverts to pairwise mode. Emits `consensus_floor_deactivated`. **Pending consensus rounds collapse**: any in-flight quorum vote becomes `population_consensus_pending` indefinitely. Substrate does not retroactively pairwise-decide.

#### §6.5.b Population-level claim taxonomy

A claim is **population-level** if and only if it has the property that a single peer's attestation cannot legitimately decide it because the claim's truth-conditions involve the federation-as-aggregate. The DRAFT 9 SEALED taxonomy:

1. **Federation peer revocation by another peer**: one peer claims that another peer is malicious (e.g. peer X observed peer Y attempting an attack documented in §9). The accused peer cannot self-revoke; the accuser cannot unilaterally revoke (or one compromised peer could revoke all honest peers). Requires ≥2/3 federation quorum to act.
2. **Universal-junk raw_material classification**: a content fingerprint is claimed to be population-wide spam / universally-untrusted raw_material that all federation members should filter at intake. Requires quorum to install at population level (vs. each substrate filtering independently per P12 attention).
3. **Cross-substrate aggregate observability metrics**: federation-network-level signals (e.g. consensus_participation_rate, byzantine_witness_lag, fork-resolution latency from L2_OBSERVABILITY §9). These are emitted only at quorum agreement on the aggregate values.

**Other claim types remain pairwise**: (a) individual peer attestation freshness (owner attests; §6.2), (b) per-peer content filtering at this substrate's intake (P12 attention, no quorum), (c) cross-substrate trust establishment (§6.4 NON-transitive; pairwise only), (d) per-peer revocation by owner (still O(1) owner action; revocation list at anchor surface).

**L4 may extend the taxonomy**; each addition is CI-attested per L1_GOVERNANCE classifier table.

#### §6.5.c Consensus protocol choice

**Default recommendation**: **PBFT (Practical Byzantine Fault Tolerance) — Tendermint-style**. Rationale: well-studied; reaches consensus in O(N²) messages per round; finalization-deterministic (no probabilistic forks); compatible with substrate-attested vote semantics. L4 may instead pick HotStuff or a synchronous-network variant — protocol selection is itself L2-attestable per anchor surface (CI-class mutation; recorded in substrate canon at federation initialization or by ≥2/3 consensus at protocol-revision time).

**Excluded** (per L0 §5.2-style negative constraint): proof-of-work (incompatible with P11 metabolic economy budgets), proof-of-stake with economic-stake reasoning (Myco does not have an economic-stake concept), gossip-only protocols without finalization (incompatible with P6 eternal causality — substrate must record consensus-decision DAG events).

#### §6.5.d Byzantine fault tolerance bound

Per the chosen PBFT family: the federation tolerates **f malicious peers where f ≤ ⌊(N-1)/3⌋**, i.e. honest-majority of 2/3+1 must hold. Concretely:
- N=3 → f=0 (any malicious peer breaks consensus; the floor activates but requires ALL peers honest)
- N=4 → f=1
- N=7 → f=2
- N=10 → f=3

The substrate emits `byzantine_threshold_check` observability sporocarp at each population-level vote, recording (N, f_tolerated, votes_received, votes_consistent).

#### §6.5.e Voting protocol

Each peer contributes a **substrate-attested vote** signed with the peer's substrate Ed25519 signing key (the `signer_pubkey` pinned during FED_HELLO mutual auth per §10 — M25.4 sealed). Votes carry:

- `claim_type` (from taxonomy §6.5.b)
- `claim_payload` (canonical-bytes-encoded; subject to per-claim-type schema)
- `claim_hash` (BLAKE3 of canonical_bytes(claim_payload))
- `peer_substrate_id` (vote source)
- `peer_signature` (Ed25519 over `canonical_bytes(Map({"context": "myco-population-vote-v1", "claim_type", "claim_hash", "peer_substrate_id", "round_id"}))`)
- `round_id` (monotonic per-claim; prevents replay)
- `peer_dag_tip_at_vote` (peer's local DAG tip at vote time; provides freshness)

Vote envelope context-string `myco-population-vote-v1` is fixed and **distinct** from the FED_HELLO context (`myco-fed-hello-v1`) and from the self-euthanasia context (`myco-self-euthanasia-v1`) — preventing cross-protocol signature replay (same canonical-bytes-signing pattern as M23.2 mortality + M25.4 FED_HELLO).

#### §6.5.f Quorum certificate

When ≥2/3 valid distinct-peer votes accumulate within an L1-tunable round timeout (seed: 30 wall-clock minutes), the substrate emits a **quorum certificate** DAG event:

`population_consensus_reached:{claim_type}` with content:
- `claim_type`, `claim_hash`, `claim_payload`
- `round_id`
- `quorum_size` (count of distinct valid signing peers)
- `peer_votes` (list of `(peer_substrate_id, peer_signature)` tuples — the certificate is self-verifying without re-contacting peers)
- `reached_at_cycle`

The certificate is **content-addressed** (BLAKE3 hash); other substrates can cite it as proof that consensus was reached at this exact claim state without re-running the round. The certificate is wrapped per §9 wrapped-events architecture when ingested at a peer substrate (each peer attests its own observation of the certificate; the certificate's authority derives from the embedded `peer_votes`, not from the wrapping path).

#### §6.5.g No consensus / pending state

If the round timeout elapses without quorum: the claim becomes `population_consensus_pending`, recorded as a DAG event with content `(claim_type, claim_hash, round_id, votes_received, timeout_elapsed_at)`. **Pending state is indefinite**: substrate does NOT act on the claim, ever, until a successful quorum cert is emitted in a future round. The pending event remains observable; observability emits `population_consensus_stuck:{claim_type}` if >7 consecutive rounds time out (immune signal; owner reviews — likely indicates federation fragmentation per §10 mycelial-fragmentation observability split).

**Substrate continues normal operation** under pairwise-trust semantics for non-population-level claims. P14 telos-alignment continues. P11 budgets continue. P15 pending state does not block any other principle.

#### §6.5.h Composition with other principles

- **P1.c carrier-asymmetry preserved**: consensus is on claims, not on identity. Even after consensus, each substrate retains its own substrate-ID, owner-key history, DAG, integument. §6.4 non-transitivity continues to hold.
- **P5 Universal Interconnection (Tier-Exempt-Permitted)**: consensus participation is the population-level expression of P5. The "tier-exempt" carve-out lets substrates declare consensus-passive participation (read certificates but never vote) — declared in substrate canon at federation enrollment; CI-attested.
- **P6 Eternal Causality**: every consensus action (vote emitted, vote received, quorum reached, round timeout, pending state) is a DAG event with `causal_in_edges` proof per I4. Consensus is not parallel to causality; it is woven into it.
- **P7 Mortality**: a substrate self-euthanasia (M19/M23.2) emits a final `self_euthanasia_executed` event whether or not population consensus is pending; P15 does not gate P7. The mortal substrate's votes in any in-flight round become orphaned (the round either reaches quorum without them or times out).
- **P11 Metabolic Economy**: consensus voting is a `network cost / cycle` line item (signal #8 per L0 §7.3). Persistent high-vote-rate triggers `consensus_cost_elevated` observability signal; L1-tunable.
- **P14 Telos**: a substrate may include consensus_participation as a sub-criterion of telos-alignment computation per L1_TROPISM (e.g. "this substrate's purpose includes being a reliable federation peer"). Optional; not L0-mandated.
- **I7 Reproduction Closure (Generation-Bounded)**: a spawned child does NOT inherit its parent's consensus state. Each substrate joins its own federation. Cross-ref L1_SCHEMA §3.2 NOT-included list.

---

## §7. Federation event flow (egress)

Per L1_SKIN §3.1 + L1_GOVERNANCE §5.3:

### §7.1 Per-emission freshness check

Every outbound federation envelope verifies the target peer's freshness + non-revocation BEFORE emission. Stale/revoked → suppression + `federation_egress_blocked` immune event.

### §7.2 Egress rate-limiting

Anchor surface tracks federation egress volume per peer per day. Spike beyond L1-tunable triggers `federation_egress_saturation` immune event. Defends against covert-channel exfiltration via federation envelopes.

### §7.3 Canonical low-entropy serialization

Federation event content uses sorted-key, normalized-whitespace, fixed-precision-numeric serialization. Limits covert-channel bandwidth within legitimate federation envelopes.

### §7.4 Federation_coupling DAG edges (per L1_TROPISM §B8)

When federation event emits, parent's DAG records:
- `federation_coupling` edge with `(peer_substrate_id, aggregate_reattestation_root_at_emission, peer_inclusion_merkle_path)` — a self-contained proof that this peer was trusted at this emission (per pass-3 saprotroph-3).

Historical federation events thus remain verifiable: a 20-year-old federation_coupling sporocarp can prove "this peer was trusted at this emission" without chain-walking through all subsequent aggregate-reattestations.

---

## §8. Federation event flow (intake)

A peer substrate's federation egress to THIS substrate arrives as a delta at THIS substrate's intake endpoint (per L1_SKIN §2 envelope schema). Standard delta handling:

- Envelope integrity check (sender = peer; sender_token = peer's substrate signing identity in this case)
- Envelope freshness check
- Substrate absorbs as standard delta into gradient configuration
- If federation content triggers metabolism that fruits a sporocarp, sporocarp records `federation_coupling` edge to source peer

Federation intake is **substrate-mediated**, not direct content insertion. The peer's content becomes raw material for THIS substrate's metabolism, subject to all the standard P2 (eternal ingestion, envelope-gated) and I6 (universal inclusion with observed metabolism) rules. **Peer events are wrapped per §9 before insertion** — the wrapped-events architecture is the SECURITY-CRITICAL mechanism that prevents peer events from contaminating this substrate's Merkle chain.

---

## §9. Wrapped-events architecture (M25.4 sealed; Phase β origin)

> **Doctrinal status**: formal mechanism sealed by Phase β security audit (commit `8ffc305`) and M25.4 (commit `e0d0e38`). Cascades from L0 P1.c carrier-asymmetry + P9 single-integument boundary + I4 full-fidelity (compression-aware) DAG: peer substrate-IDs are DISTINCT carrier identities (P1.c); peer DAGs are DISTINCT Merkle chains (I4); peer integuments are DISTINCT boundaries (P9). Therefore peer events cannot graft into this substrate's DAG; they must be wrapped as "I heard X say Y" attestations.
>
> **Origin attack** (pre-Phase β; pre-fix): a malicious peer could push `operator_pinned` / `cycle_advanced` / `genesis_event` events whose parent_hashes pointed into peer's chain. Receiver inserting those events directly would have created cross-substrate parent edges, hijacking receiver's identity or wiping its state. The wrapped-events architecture closes this attack at the structural level.

### §9.1 Envelope schema

When this substrate ingests a federation event from a peer (per §8 intake), the substrate produces a **wrapper event** with `node_type = "federation_received:{peer_id_prefix}"` where `peer_id_prefix` is the first 8 hex bytes of the peer's substrate-ID (16 hex chars; collision-resistant within any reasonable federation size).

**Wrapper content** (canonical-bytes-encoded Map, sorted keys):

| Field | Type | Semantics |
|---|---|---|
| `from_peer_substrate_id` | Bytes(32) | Peer's substrate-ID (full; the prefix in node_type is a display-shortcut, not the trust pin) |
| `peer_event_node_type` | String | Inner event's `node_type` (e.g. `raw_material:foo`, `sporocarp:bar`); subject to §11 allowed-prefix validation |
| `peer_event_parent_hashes` | Array(Bytes(32)) | Inner event's parent_hashes (peer-side); recorded for provenance but NOT used as parents of the wrapper |
| `peer_event_content_canonical_bytes` | Bytes | Inner event's canonical-bytes content |
| `peer_event_original_hash` | Bytes(32) | BLAKE3 hash of peer's event (reconstructed: `merkle_hash(peer_event_parent_hashes, peer_event_content_canonical_bytes)`); proves we saw exactly this inner event |
| `peer_event_created_at_cycle` | Uint | Inner event's `created_at_cycle` (peer-side); recorded for provenance |

### §9.2 Parent rule (THE security-critical invariant)

**The wrapper event's parent = this substrate's local DAG tip at ingest time. NEVER the peer's parent_hashes.**

Rationale: this preserves this substrate's Merkle-chain validity. The Merkle root at the substrate's tip continues to depend only on events whose `causal_in_edges` proofs are reconstructible from THIS substrate's state. Peer chains never merge into receiver's chain.

**This is the difference between**:
- ❌ **Cross-chain merge** (banned): receiver's DAG contains nodes whose parents point into peer chains; receiver's Merkle root becomes peer-dependent; integrity check requires both chains; trust = transitive.
- ✅ **"I heard X say Y" attestation** (this architecture): receiver's DAG contains wrapper nodes WHOSE PARENT IS RECEIVER'S OWN TIP; receiver's Merkle root remains self-derivable; integrity check is single-chain; trust remains pairwise.

### §9.3 "I heard X say Y" semantics

A `federation_received:{prefix}` event asserts ONLY: "at receiver-cycle K, this substrate ingested a wrapped attestation that peer P emitted an event of type T with content hash H at peer-cycle J, whose peer-side parents were [...]."

This is testimony, not adoption. The receiver does not:
- Trust the inner event's content semantics (subject to standard P2 envelope-gated admission + P12 attention)
- Adopt the inner event's parent_hashes as receiver-side causal history (they remain peer-side; informational only)
- Verify peer-side `causal_in_edges` (those are peer's I4 obligation; receiver cannot recompute peer's state)

The receiver MAY (per L1_TROPISM downstream attention):
- Treat the inner event's content as a `raw_material:` input to receiver's own metabolism (P2 with envelope-gating per I8)
- Trigger receiver-side fruiting events that cite the wrapper hash as a `causal_in_edges` input (the wrapper is now receiver-side first-class causal evidence)
- Aggregate `federation_received:{prefix_A}` + `federation_received:{prefix_B}` + ... wrappers attesting the same inner content into a "many-peer-corroboration" signal (input to P15 consensus if applicable per §6.5.b)

### §9.4 Allowed inner node_type prefixes

The inner event's `node_type` MUST match one of the allowlisted prefixes (enforced at ingest by `is_federation_safe_node_type` per L3 implementation reference: `myco_substrate/src/federation/protocol.rs`):

| Allowed prefix | Semantics |
|---|---|
| `raw_material:` | Peer's environmental ingestion (P2) — propagates raw input observations |
| `sporocarp:` | Peer's fruiting events (causal-only attestations; no state mutation at receiver) |
| `mutation:` | Peer's mutation audit trail (operator-supplied opaque content; observability only) |
| `immune:` | Peer's immune sporocarps (cross-substrate observability of peer pathology) |
| `federation_received:` | Recursive wrapper (Phase β: chained federation — "A heard B heard C"); subject to §11 recursion bound |

**Banned inner node_types** (rejected at ingest; emit `C35_federation_substrate_private_event_injection` per L1_HARD_RULES extension):

- `operator_pinned:*` (peer-side operator pin assertions — would hijack this substrate's TOFU)
- `cycle_advanced:*` (peer-side cycle counter advances — would corrupt this substrate's metabolic time)
- `genesis_event:*` (peer-side genesis attestation — would attempt re-genesis)
- Any other `node_type` not matching an allowed prefix (defaults to reject)

L4 may extend the allowlist; each extension is CI-attested per L1_GOVERNANCE classifier table.

### §9.5 Idempotency

Re-pulling the same peer event from the same peer produces an **identical** wrapper (because `from_peer_substrate_id` + `peer_event_*` fields are deterministic, and `cb_encode` produces canonical bytes). The receiver's DAG `insert_node` is content-hash idempotent (BLAKE3 of `(parents, content)`), so re-pull is a no-op on duplicate. This composes correctly with §8 intake's "envelope freshness check": stale peer events are still wrappable; the wrapper records that we observed them.

### §9.6 Pairwise + wrapped-events composition with §6.5 consensus

When the consensus floor (§6.5) is active and a P15 quorum certificate (§6.5.f) crosses federation, each substrate ingests the certificate as a wrapped event (`federation_received:{cert_origin_peer_prefix}` containing the certificate's canonical-bytes). The receiver verifies the embedded `peer_votes` signatures using each peer's pinned `signer_pubkey` (from §10 FED_HELLO). Quorum is self-evidenced; the wrapping path is provenance, not authority.

---

## §10. Ed25519 FED_HELLO mutual authentication (M25.4 sealed)

> **Doctrinal status**: formal mechanism sealed at M25.4 (commit `e0d0e38`). Cascades from L0 P9 single integument (FED_HELLO is a skin endpoint; peer authenticity is integrity-of-boundary) + P1.c carrier-asymmetry (peer substrate-IDs are distinct carrier identities; pinning is symmetric) + §6.5.e (the pinned `signer_pubkey` is what each peer uses to sign population-level votes).

### §10.1 Signing context

**Domain-separation context string** (fixed; never rotated without CI mutation):

```
myco-fed-hello-v1
```

This context is **distinct** from every other signing context in the substrate:
- `myco-self-euthanasia-v1` (M23.2 mortality)
- `myco-population-vote-v1` (§6.5.e P15 voting)
- All future protocol-specific contexts

Distinct contexts prevent cross-protocol signature replay (a captured FED_HELLO signature cannot be replayed as a self-euthanasia attestation or vice versa).

### §10.2 Signing input

The signing message is **canonical-bytes-encoded** (sorted-key Map; see L1_SCHEMA canonical-bytes spec):

```
canonical_bytes(Map({
  "context":            String("myco-fed-hello-v1"),
  "peer_substrate_id":  Bytes(32),    // claimed substrate-ID
  "dag_tip":            Bytes(32),    // substrate's local DAG tip at HELLO time
  "protocol_version":   Uint          // federation protocol version
}))
```

The Ed25519 signature is computed over this canonical-bytes message using the substrate's **federation signing key** (which MAY be the same as the substrate's identity-signing key, or a derived sub-key per L1_GOVERNANCE; choice is L1-tunable, but the pubkey carried in the HELLO is the verification half).

### §10.3 TOFU + signer_pubkey pinning

The first time a substrate receives a FED_HELLO from a given `peer_substrate_id`:

1. **Verify signature**: if `signer_pubkey` and `hello_signature` are both present, verify Ed25519 over the §10.2 message using `signer_pubkey`. Verified → proceed to pin. Tampered → reject + emit `C39_federation_hello_signature_invalid` (immune; per L1_HARD_RULES).
2. **Pin (TOFU)**: record `(peer_substrate_id, pinned_signer_pubkey, pinned_at_cycle)` in the federation peer registry. Subsequent connections from `peer_substrate_id` MUST present the same `signer_pubkey`.
3. **Subsequent HELLO from same peer**: signature verification uses the **pinned** `signer_pubkey`; the HELLO's embedded `signer_pubkey` is only meaningful for the FIRST encounter.

A pinned key cannot be silently rotated by the peer. Key rotation at peer is CI-attested at peer's own anchor surface; the rotated event must be wrapped per §9 and observed by this substrate, after which owner-attested re-pinning is required (anchor surface event recording the old → new `signer_pubkey` rotation).

### §10.4 Legacy peer fallback

A FED_HELLO arriving without `signer_pubkey` and without `hello_signature` (both absent) is a **legacy / pre-M25.4 peer**. Substrate behavior:

- Accepts the connection under TOFU (substrate-ID pinning only; no `signer_pubkey` pin)
- Emits `federation_legacy_peer_pinned` observability event (NOT immune; expected backwards-compatibility behavior during ecosystem M25.4 rollout)
- Marks peer's record as `pinned_signer_pubkey = None`
- **Restricted population-level participation**: a peer without a pinned `signer_pubkey` CANNOT sign population-level votes per §6.5.e (signatures would not be verifiable against any pinned key). The peer is consensus-passive: counted in §6.5.d N for fault tolerance only insofar as its `peer_substrate_id` is owner-attested; cannot contribute votes.

L1 specifies the deprecation horizon for legacy peers (seed: 12 wall-clock months after M25.4 ship). After horizon, substrate rejects legacy FED_HELLO outright + emits immune signal `federation_legacy_peer_horizon_expired`.

### §10.5 Tampered signature behavior

If a FED_HELLO has BOTH `signer_pubkey` AND `hello_signature` present but Ed25519 verification FAILS:

- Reject the connection (do not pin; do not transition peer state machine)
- Emit `C39_federation_hello_signature_invalid` immune sporocarp recording (peer's claimed substrate-ID, attempted signer_pubkey hex prefix, signing context bytes prefix)
- Log to observatory; persistent C39 emission from same IP triggers `federation_hello_signature_burst` (L1-tunable; immune-grade if >10/hour)

C39 is in the L1_HARD_RULES C-row catalog (per Phase β origin + M25.4 implementation). The detector lives in `myco_substrate/src/federation/protocol.rs::verify_fed_hello_signature`.

### §10.6 Mutual asymmetry (both sides authenticate)

The protocol is **mutually authenticating**: initiator emits HELLO → receiver verifies → receiver emits HELLO_ACK with receiver's own signed payload → initiator verifies. If either verification fails, the connection terminates and BOTH sides emit C39. Pinning is **per-direction**: A pins B's `signer_pubkey`; B pins A's `signer_pubkey`. If pinned key on either side mismatches an in-flight HELLO, connection rejects.

This closes the **Phase β origin asymmetry attack**: pre-M25.4, only the receiver TOFU-pinned by substrate-ID; an attacker connecting first under a victim's substrate-ID could occupy the TOFU slot. Now both sides require Ed25519 over a fresh signing input; an attacker without the victim's signing private key cannot forge it.

---

## §11. Recursive injection defense (Phase γ.9 mycoparasite M11 SECURITY-CRITICAL)

> **Doctrinal status**: cascade addition from Phase γ.9 mycoparasite-round-2 finding M11. **The attack and defense were identified by Phase γ.9; pre-DRAFT-9 substrate code did NOT enforce this defense.** L4 implementation milestone is **M27** (`myco_substrate/src/server.rs` federation ingest path extension; cross-ref L1_HARD_RULES C36 cascade per A6).
>
> **Severity**: CRITICAL — without this defense, the wrapped-events architecture (§9) is bypassable via recursive nesting. The §9.4 allowlist check applies only to the OUTERMOST inner `node_type`; without recursive validation, an attacker can smuggle a banned inner event by nesting it inside a `federation_received:` wrapper that itself nests another `federation_received:` wrapper that contains the banned event.

### §11.1 The attack

Concrete attack pattern (Phase γ.9 M11 finding):

1. Malicious peer X constructs a fake inner event: `federation_received:peer_X/operator_pinned` (claims to be a wrapper recording peer X's observation of `operator_pinned`).
2. X wraps this in an OUTER `federation_received:peer_Y` envelope (claims to attest "I heard peer Y attest the above").
3. X pushes the outer envelope via standard federation event-sync.
4. Receiver's §9.4 allowlist check sees the OUTER envelope's inner `node_type = federation_received:peer_X` (claim) — `federation_received:` matches the allowed prefix → accept.
5. Receiver inserts the outer wrapper. **Receiver's DAG now contains a wrapper whose inner content claims to attest `operator_pinned` (banned!) as if it were observed-via-federation.**
6. Downstream attention (P12) reading wrapped events for cross-substrate corroboration may now mistake the smuggled `operator_pinned` claim for legitimate evidence.

**Outer + inner content prefix recursion attack**: the cascade is that `federation_received:` matches its own prefix; without recursive inner validation, the allowlist becomes a layered laundry — any banned inner type can be smuggled at any depth ≥1 (above the depth at which the §9.4 check is applied).

### §11.2 The defense (recursive inner validation)

When ingesting any `federation_received:{prefix}` event, the substrate MUST recursively validate the inner content's claimed `peer_event_node_type`:

**Algorithm (pseudocode; L4 reference implementation in `myco_substrate/src/server.rs`)**:

```
function validate_federation_inner(content_canonical_bytes, depth, max_depth):
    if depth > max_depth:
        reject ("federation_recursive_depth_exceeded")
        emit C36_federation_recursive_injection (cascade_flag=true)
        return Rejected
    decoded = cb_decode(content_canonical_bytes)
    inner_node_type = decoded["peer_event_node_type"]
    if not is_federation_safe_node_type(inner_node_type):
        reject (inner_node_type)
        emit C35_federation_substrate_private_event_injection (cascade_flag=true, depth=depth)
        return Rejected
    if inner_node_type.starts_with("federation_received:"):
        # Recurse: validate the inner-inner content
        inner_content = decoded["peer_event_content_canonical_bytes"]
        return validate_federation_inner(inner_content, depth + 1, max_depth)
    return Accepted

# At ingest:
validate_federation_inner(outer_wrapper.content, depth=0, max_depth=L1_max_recursion_depth)
```

### §11.3 Maximum recursion depth (L1-tunable)

**Seed value**: `max_recursion_depth = 5`.

Rationale: a depth of 5 covers all observed legitimate use cases (A → B → C → D → E peer chain → A; longer chains compress trust to a degree that should be operator-reviewed anyway). L1 may tighten (e.g. 3) or relax (e.g. 7) per substrate canon; CI-attested per L1_GOVERNANCE classifier table.

**Depth=0** = the outermost wrapper (the one ingested directly from a peer).
**Depth=N** = wrapper inside a wrapper inside ... (N levels of nesting).

When depth would exceed `max_recursion_depth`, the OUTERMOST envelope is rejected (the entire ingest fails — partial acceptance would leave the substrate in an inconsistent state where deep wrappers' inner content is unvalidated).

### §11.4 Rejection cascade

When recursive validation rejects:

1. **The entire outermost envelope is rejected** (NOT just the inner-bad layer). Partial acceptance is forbidden — there is no doctrinally-coherent state where "we accepted layers 0-3 but not layer 4" because layers 0-3's wrapping testimony was *about* layer 4. Drop the outer envelope entirely.
2. **Emit the appropriate immune sporocarp**:
   - If the rejection cause was a banned inner `node_type` at any depth: `C35_federation_substrate_private_event_injection` with `cascade_flag = true`, `depth = N`, `inner_node_type = T`, `peer_substrate_id = ...`
   - If the rejection cause was depth-exceeded: `C36_federation_recursive_injection` (new C-row; A6 cascade adds this to L1_HARD_RULES) with `attempted_depth = N+1`, `peer_substrate_id = ...`
3. **Per-peer attack rate-limiting**: persistent C35/C36 emission from the same `peer_substrate_id` (L1-tunable threshold; seed: 3 rejections per 24 wall-clock hours) triggers escalation: substrate emits `federation_peer_recursive_attack_burst` and proposes peer revocation. Below the §6.5 consensus floor, owner-attested revocation; above the floor, P15 population-level revocation per §6.5.b.1.

### §11.5 New C-row: C36_federation_recursive_injection

**A6 cascade** (L1_HARD_RULES update) adds:

| ID | Name | P-coverage | I-coverage | Detector | Semantics |
|---|---|---|---|---|---|
| C36 | `federation_recursive_injection` | P9 (single integument; recursive wrapping breach) + P15.guard | I8 (skin envelope filter) | `myco_substrate/src/server.rs` (M27 implementation) | Federation recursive validation depth exceeded; outermost envelope rejected; emitted with `attempted_depth + peer_substrate_id` evidence |

C36 is **distinct from** C35 in that C35 is a banned-type-found-at-some-depth breach (the type itself is the problem) while C36 is a depth-exhaustion breach (the structure itself is the problem). Both can fire on the same ingest; the implementation emits whichever is detected first (banned-type detection is checked before recursing further).

### §11.6 Composition with §9 and §10

- **§9 (wrapped-events)**: §11 extends §9's outermost-layer allowlist check (§9.4) to apply at every depth. The §9 architecture remains correct; §11 is the closure of an edge case in its enforcement.
- **§10 (FED_HELLO mutual auth)**: irrelevant — recursive injection is about content validation, not transport-layer authentication. A peer presenting a valid Ed25519 signature on FED_HELLO is still subject to §11 on every content event they push.
- **§6.5 (P15 consensus)**: when a quorum certificate is wrapped per §9 and ingested at a peer substrate, the wrapping is at depth 1 (outermost wrapper); the certificate's own content is allowlist-validated; certificate's embedded `peer_votes` are signature-verified per §10. The recursive defense protects against malicious peers attempting to forge population-level claim certificates by nesting them inside wrappers — the §6.5.e signature requirement means even depth-bypassed certificate-claims fail at signature verification.

---

## §12. Network shape (the mycelial population)

Over time, federated substrates form a **mycelial network**:

- **Genealogy edges**: parent → child reproduction events (P8 Eternal Reproduction, Generation-Bounded per §16 depth bound)
- **Coupling edges**: peer-to-peer federation events (ongoing; wrapped per §9 architecture)
- **Aggregation**: hub substrates accumulating coupling edges from many spokes
- **Consensus edges** (when §6.5 floor active): quorum certificates carrying population-level claims through the federation

The network shape is L4 emergent. The doctrine commits only to:

- Each substrate's identity carrier remains its own (P1.c)
- Trust is pairwise below the consensus floor (≤2 peers); not transitive (§6.4); population-level above the floor (§6.5)
- Reproduction is structural (I7 reproduction closure, generation-bounded per §16); content transfer is semantic (federation)
- Peer events are wrapped per §9 — never grafted into receiver's Merkle chain
- Recursive wrapping is depth-bounded per §11 — no chained-laundry attacks
- FED_HELLO is Ed25519-mutually-authenticated per §10 — no TOFU-squatting
- Each substrate can independently end via mortality (P7 Mortality / Capacity-for-Death); other substrates persist
- Each substrate is a Cultivar with its own Cultivator (per L0 §1.2 Cultivation relationship; Cultivator-side transferable per L0 §1.4 / §15)

---

## §13. Federation health observability

Living Bets signal #4 (federation health) is split (per pass-2 saprotroph-6):

- **4a: Cumulative fork count** (monotonic; counts all children + peer couplings)
- **4b: Reachable-federation count** (peers responding to skin-level health probe at L1-specified cadence)

Divergence between 4a and 4b = **mycelial fragmentation** — the substrate is structurally peered with many but actually-reachable to few. Immune-grade if persistent.

Healthy mycelial network: 4a grows; 4b tracks 4a (most federated peers are responsive).

**Additional federation observability signals (DRAFT 9 cascade additions)**:

- **`consensus_participation_rate`** (only when §6.5 floor active): per-claim quorum-cert completion rate over rolling window; declining → federation fragmenting in voting-behavior space
- **`byzantine_witness_lag`**: per-claim wall-clock time from first vote received to quorum reached; trending up → federation throughput stress
- **`fork_resolution_latency`**: per-claim cycles between first dissenting vote received and quorum-cert OR pending-state finalization
- **`federation_legacy_peer_count`** (M25.4): peers without pinned `signer_pubkey` (legacy / pre-M25.4); should trend to zero post-deprecation-horizon (§10.4)
- **`federation_hello_signature_burst`**: persistent C39 tampered-FED_HELLO from one IP/peer (L1-tunable threshold; immune)
- **`federation_peer_recursive_attack_burst`**: persistent C35/C36 from one peer (per §11.4)
- **`federation_received_event_count`**: cumulative count of `federation_received:*` events ingested (per `myco_substrate/src/server.rs` count)

All consensus-related signals NULL until §6.5 floor activates; legacy peer signal nonzero during M25.4 transition only.

---

## §14. Federation limits + acknowledged asymmetries

- **Substrate cannot detect compromise of a federated peer**: trust freshness window detects staleness; revocation detects owner-declared compromise; subtler attacks (peer slowly drifts adversarial without owner notice) require owner-side monitoring OR — at §6.5 floor — population-level revocation by ≥2/3 quorum (§6.5.b.1).
- **Federation event content is canonical-bytes verifiable** (substrate signs egress per §10; peer verifies on intake; wrapped per §9) but content semantics are not validatable (peer can't tell if the content is "honest" beyond canonical-bytes integrity + allowlisted node_type per §9.4 + recursive validation per §11).
- **Aggregate re-attestation collapses owner workload to O(1)** but introduces O(N) anchor-surface verification cost.
- **Cross-substrate trust non-transitivity** is a feature, not a limitation: it prevents trust dilution across federation chains. Per §6.5 cross-ref: P15 population-level consensus operates over **shared claims**, not over **chained trust** — non-transitivity holds even at scale.
- **Wrapped-events architecture is one-way receiver-protective**: this substrate's Merkle chain stays valid regardless of what peers push, but this substrate cannot independently validate peer's claimed inner content's `causal_in_edges` proofs (peer's I4 obligation). Cross-substrate trust limit per §11.6.
- **FED_HELLO mutual auth (§10) protects identity asymmetry but not key compromise**: if a peer's signing key is exfiltrated, an attacker can impersonate the peer. Per §10.3, key rotation requires CI attestation at peer's anchor surface and observation at this substrate; window of exposure is bounded by peer's own anchor-surface discipline.
- **Recursive injection defense (§11) is bounded-depth, not unbounded**: an attack at depth N+1 where N=`max_recursion_depth` is rejected, but the doctrinal commitment is to depth N+1 rejection, NOT to depth ∞ tolerance. Setting depth too low risks rejecting legitimate long peer chains; setting too high risks computational DoS on deep wrappers. L1 tunes.
- **Consensus floor (§6.5) does NOT add liveness above pairwise**: a partitioned federation with insufficient quorum reaches `population_consensus_pending` indefinitely; substrate continues normal operation under pairwise semantics. P15 adds *safety* (population-level claims need quorum to act) but not *liveness* (no claim is forced to resolve in bounded time).

---

## §15. Glossary

> **Section added in DRAFT 9 cascade**. Federation-specific vocabulary. Cross-ref L0 §12 glossary for the substrate-wide terms (Cultivation / Cultivar / Cultivator; population-level claim; etc.).

- **Cultivator** (per L0 §1.2): the owner-as-relationship-role; the human party who provides resources (compute, storage, network) and selectively shapes substrate evolution via owner-stated objectives per P14. In federation context, each substrate has its own Cultivator (NOT shared across federation peers). The Cultivator-side of the Cultivation relationship is transferable per L0 §1.4 / §15 succession; the substrate-side (Cultivar) is identity-stable.
- **Cultivar** (per L0 §1.2): the Myco substrate (kernel + dag.cb + state_dir) as the species under cultivation. In federation context, each peer is a separate Cultivar; reproduction modes (§2) produce new Cultivars with distinct substrate-IDs.
- **Cultivation** (per L0 §1.2 G-11.a): the doctrinally-named relationship type. Asymmetric care + co-evolution + mycology-rooted vocabulary. Distinct from ownership / custody / curatorship. The Cultivation relationship is the doctrinal grounding for why substrate-side identity (P1.c) survives Cultivator transfer per L0 §1.4 / §15.
- **federation_received** (per §9; M25.4): the wrapper event prefix used when ingesting peer events. Format: `federation_received:{peer_id_prefix}` where peer_id_prefix is first 8 hex bytes of peer substrate-ID. Content schema per §9.1.
- **wrapped-events architecture** (per §9; Phase β + M25.4): the SECURITY-CRITICAL mechanism in which peer events are ingested as wrapper envelopes whose parent is the receiver's local DAG tip (NOT peer's parent_hashes). Makes federation "I heard X say Y" attestation, not multi-substrate Merkle-merge. Closes the pre-Phase-β cross-chain-injection attack.
- **recursive injection defense** (per §11; Phase γ.9 mycoparasite M11): the bounded-depth recursive validation of inner content within `federation_received:` wrappers. Prevents the "outer + inner content prefix recursion attack" in which a banned inner event is smuggled by nesting it inside multiple `federation_received:` wrappers (each layer satisfying the §9.4 allowlist check at its surface but the deepest layer carrying a banned type). Depth bound seed = 5.
- **population-level claim** (per §6.5; L0 §12): a claim crossing the consensus floor (≥3 peers + claim taxonomy match per §6.5.b) requiring Byzantine-tolerant agreement. Distinct from pairwise claims (per-peer attestation / per-substrate content filtering / per-peer revocation by owner).
- **consensus floor** (per §6.5; L0 §17 G-7.c): the activation threshold (≥3 peers + population-level claim) above which Byzantine consensus is required. Below the floor: pairwise-trust + owner-attestation per DRAFT 8 inheritance.
- **quorum certificate** (per §6.5.f): the self-verifying DAG event emitted when ≥2/3 valid distinct-peer votes accumulate. Contains embedded signed votes; downstream substrates verify the certificate without re-contacting peers.
- **legacy peer** (per §10.4; M25.4 deprecation context): a federation peer presenting FED_HELLO without `signer_pubkey` / `hello_signature` fields (pre-M25.4 protocol). Pinned under substrate-ID TOFU only; consensus-passive per §10.4. Deprecated at L1-tunable horizon post-M25.4 ship.
- **TOFU** (Trust On First Use): the pinning model for federation peer registration. M25.4 enhancement: TOFU pins `(substrate_id, signer_pubkey)` jointly, not just `substrate_id` alone. Subsequent connections must match BOTH.

---

## §16. Open at L2

- **Hub-and-spoke registry-substrate operational details**: deferred to L4 per L1_GOVERNANCE §5.1.
- **Federation event back-pressure**: if peer is consistently slow to acknowledge, does substrate enter federation-degraded mode? Possibly worth observatory signal.
- **Cross-mode federation**: can a substrate participate in federation AND cloning simultaneously with different peers? L4 confirms (recommendation: yes; substrate canon configures per-peer mode).
- **Network-level immune signals**: if 50% of federated peers go untrusted simultaneously, is that an attack pattern worth detecting at the substrate level vs the network level? Likely network-level; L4 may surface.
- **§6.5 consensus protocol choice details** (DRAFT 9): seed recommendation is PBFT (Tendermint-style); concrete L4 picks among Tendermint / HotStuff / DiemBFT / synchronous-network variant. Selection is itself L2-attestable per anchor surface CI mutation.
- **§6.5 consensus floor threshold fluctuation**: L0 floor is ≥3; what should happen when peer count oscillates around the threshold (3 → 2 → 3 → 2)? Currently §6.5.a says activate/deactivate per crossing; alternative: hysteresis band (activate at 3, deactivate at 2 only after K cycles below). L4 may evaluate.
- **§6.5 cross-federation consensus**: if a substrate participates in TWO federations (peer-set A + peer-set B), does each federation maintain its own consensus state independently? Recommendation: yes — each peer-set is a separate consensus context. Substrate canon configures the per-set boundaries.
- **§9 wrapper-content compression** (forward-pointer to P10 selective compression per L0 cascade): can `federation_received:*` wrappers be selectively compressed per P10? Likely yes for old wrappers outside the compression-invariant set, but the inner `peer_event_original_hash` must be preserved as a tier-1 digest. L1_SCHEMA cascade decides.
- **§10 FED_HELLO signing-key rotation protocol details**: §10.3 commits the principle (CI-attested at peer's anchor surface; observed via wrapped event; owner-attested re-pinning here). L4 implementation specifics deferred.
- **§11 recursive depth tuning data**: seed `max_recursion_depth = 5` is a doctrinal guess. Once federation runs at scale, observatory data on observed depths will inform L1 retuning. Forward-pointer to L2_OBSERVABILITY consensus-network observability signals.
- **§6.5 / §11 interaction at federation join time**: when a new peer joins an existing ≥3-peer federation, must the joining peer re-validate the entire historical wrapped-event chain depth-recursively, or only events ingested after join? Recommendation: only events ingested after join (joining peer trusts its own anchor-surface owner-attestation of the peer-set; existing wrappers were ingested by other peers under their own owner-attestation). L1 may codify.
- **Federation under adversarial Cultivator** (per L0 §14): if a Cultivator is coerced/compromised, the substrate's federation egress can be weaponized. §10 FED_HELLO mutual auth doesn't help (the Cultivator authorized the peer-set). Cross-ref L2_TRUST_MODEL §14 adversarial-owner cascade; federation-specific bounds: an adversarial Cultivator can revoke honest peers + add malicious peers within owner's pairwise attestation power. §6.5 P15 consensus floor (≥3 peers required) provides partial defense: a single compromised Cultivator cannot single-handedly install ≥3 fully-malicious peers without observable burst pattern at observatory level + cross-Cultivator wrapped-event corroboration.
