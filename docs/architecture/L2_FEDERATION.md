# L2 — Federation Doctrine

> **Status**: DRAFT 1 (2026-05-13). Cross-cut doctrine theme.
> **Layer**: L2.
> **Scope**: inter-substrate doctrine — the population-level shape of Myco. Cross-cuts L0 P5 (universal interconnection) / P8 (eternal reproduction) + L1_GOVERNANCE §4.3 reproduction / §5 federation discovery & peer-trust freshness + L1_SCHEMA §3 spore-schema + L1_SKIN §3.1 federation egress / §3 output gating + I7 reproduction closure / I8 inter-substrate edge in P5. Answers: how does v0.9 extend beyond a single substrate; what is the mycelial network shape; how do substrates trust each other without compromising P1.c?

---

## §1. What federation IS

Federation is **inter-substrate semantic transfer** (not byte-level file sync, not API integration). A federated peer substrate receives the originating substrate's distilled material (sporocarps, refined decisions, schema-evolution markers) as deltas into its own field. The peer's own metabolism absorbs and reshapes.

Federation extends P5 (universal interconnection) beyond a single substrate's interior. The **mycelial network** in v0.9's biology is the population of federated substrates linked via parent-child reproduction edges + peer coupling edges.

---

## §2. Reproduction modes (per L0 P8)

Three modes produce federated substrates:

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

- Each substrate has its own `substrate-ID` (owner-signed at its own genesis).
- Each substrate has its own owner key history.
- Each substrate has its own DAG.
- Each substrate has its own operator-connections.
- A child substrate spawned from a parent has a DIFFERENT agent-identity continuum than its parent.

**Federation transfers content, not identity.** This is the structural reason cross-substrate trust is NOT transitive (§6.3 below).

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

Federation intake is **substrate-mediated**, not direct content insertion. The peer's content becomes raw material for THIS substrate's metabolism, subject to all the standard P2 (eternal ingestion) and I6 (universal inclusion with observed metabolism) rules.

---

## §9. Network shape (the mycelial population)

Over time, federated substrates form a **mycelial network**:

- **Genealogy edges**: parent → child reproduction events
- **Coupling edges**: peer-to-peer federation events (ongoing)
- **Aggregation**: hub substrates accumulating coupling edges from many spokes

The network shape is L4 emergent. The doctrine commits only to:

- Each substrate's identity carrier remains its own (P1.c)
- Trust is pairwise; not transitive (§6.4)
- Reproduction is structural (I7 closure); content transfer is semantic (federation)
- Each substrate can independently end via mortality (P7); other substrates persist

---

## §10. Federation health observability

Living Bets signal #4 (federation health) is split (per pass-2 saprotroph-6):

- **4a: Cumulative fork count** (monotonic; counts all children + peer couplings)
- **4b: Reachable-federation count** (peers responding to skin-level health probe at L1-specified cadence)

Divergence between 4a and 4b = **mycelial fragmentation** — the substrate is structurally peered with many but actually-reachable to few. Immune-grade if persistent.

Healthy mycelial network: 4a grows; 4b tracks 4a (most federated peers are responsive).

---

## §11. Federation limits + acknowledged asymmetries

- **Substrate cannot detect compromise of a federated peer**: trust freshness window detects staleness; revocation detects owner-declared compromise; subtler attacks (peer slowly drifts adversarial without owner notice) require owner-side monitoring.
- **Federation event content is canonical-bytes verifiable** (substrate signs egress; peer verifies on intake) but content semantics are not validatable (peer can't tell if the content is "honest" beyond canonical-bytes integrity).
- **Aggregate re-attestation collapses owner workload to O(1)** but introduces O(N) anchor-surface verification cost.
- **Cross-substrate trust non-transitivity** is a feature, not a limitation: it prevents trust dilution across federation chains.

---

## §12. Open at L2

- **Hub-and-spoke registry-substrate operational details**: deferred to L4 per L1_GOVERNANCE §5.1.
- **Federation event back-pressure**: if peer is consistently slow to acknowledge, does substrate enter federation-degraded mode? Possibly worth observatory signal.
- **Cross-mode federation**: can a substrate participate in federation AND cloning simultaneously with different peers? L4 confirms (recommendation: yes; substrate canon configures per-peer mode).
- **Network-level immune signals**: if 50% of federated peers go untrusted simultaneously, is that an attack pattern worth detecting at the substrate level vs the network level? Likely network-level; L4 may surface.
