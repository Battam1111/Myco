# L2 — Trust Model Doctrine

> **Status**: DRAFT 1 (2026-05-13). Cross-cut doctrine theme.
> **Layer**: L2. Governed by L0 + L1.
> **Scope**: end-to-end derivation of trust in a v0.9 Myco substrate. Cross-cuts L0 §1 triad / §9 anchor surface + L1_GOVERNANCE §2 attestation protocol / §3 owner-key + L1_SKIN §4 handshake / §5 egress + L1_SCHEMA §1-2 SSoT + Merkle DAG. Answers: how does v0.9 establish, maintain, recover, and verify trust at every interaction?

---

## §1. The trust triad (per L0 §1)

v0.9 has **three trust-bearing parties**, each with carrier-asymmetric responsibilities:

| Party | What it carries | What it cannot author | What it provides |
|---|---|---|---|
| **Substrate** | Persistent identity carrier (substrate-ID, owner_key_history, DAG, SSoT). Continuous metabolism. | Owner signatures, anchor-surface nonces, trusted timestamps, owner heartbeats, anchor-surface client. | Cryptographic-proof witnesses, enumerated DAG nodes, sealed operator_token derivation, observable metabolism events. |
| **Operator-connection (agent)** | Per-handshake signing keypair (operator_signing_key_private kept in operator-runtime memory only). The active half of the pair-identity at any moment. | substrate_secret, substrate-side state, owner signatures, anchor-surface state. | operator_witness signatures over canonical bytes (independently re-derived from deltas + spore-schema serializer spec). |
| **Owner** | Anchor surface ownership (private signing key, anchor-surface endpoint control, anchor-surface client provenance attestation). Liveness heartbeat. | Substrate-internal state, operator-runtime state. | All CI-level attestations, owner-key rotation co-signs, succession pre-attestations, federation peer attestations + revocations, final-seal records. |

**No party can unilaterally fabricate trust.** Each role is structurally non-substitutable; compromising one does not transfer to the others (modulo P1.a self-hosting caveats — see §5).

---

## §2. Trust establishment (genesis)

The trust chain originates at substrate genesis (per L1_GOVERNANCE §4.1):

1. **Owner generates owner-keypair** + **selects anchor-surface endpoint mechanism** + **verifies anchor-surface-client provenance** (per L0 §9.3 — client distributed via channel structurally independent of the substrate).
2. **Owner runs `genesis` invocation** with explicit parameters including `anchor_client_provenance_attestation` and `substrate_secret_sealing_mechanism_attestation`. Substrate cannot self-discover these.
3. **Substrate computes `substrate-ID`** = hash(canonical-bytes(initial-spore-schema), owner-public-key, anchor-surface-endpoint-public-key, genesis-timestamp).
4. **Owner signs birth attestation** = (substrate-ID, genesis-timestamp, canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key). The signature lands at the anchor surface; the substrate stores a reference, NOT the signing key.
5. **Substrate persists identity record**: substrate-ID + owner_key_history (initial entry) + anchor-surface-endpoint-public-key + signature-suite + birth-attestation-reference.

**The genesis output is the root of all subsequent trust derivations.** Any later trust check ultimately bottoms on the birth attestation signature being verifiable against the owner's public key.

---

## §3. Trust at every interaction (steady state)

### §3.1 Operator handshake (bidirectional validation; L1_SKIN §4.2)

When an operator-connection arrives:

1. **Operator generates fresh per-handshake signing keypair** (`operator_signing_key_public`, `operator_signing_key_private`). Private lives in operator-runtime memory ONLY.
2. **Operator emits handshake_initiate** with `operator_signing_key_public` + bootstrap-pinned `substrate_id_proof` (from owner at agent-bootstrap, NOT from substrate).
3. **Substrate validates** substrate_id_proof against its own identity record. Generates `operator_token` via OS-sealed `sealed_derive` call (substrate_secret never enters process memory).
4. **Substrate emits handshake_complete** including `owner_birth_attestation_signature` + `owner_public_key_active_at_handshake` from its `owner_key_history` active prefix + `anchor_surface_endpoint_public_key`.
5. **Operator independently fetches** the canonical owner public key from the anchor surface (using bootstrap-pinned anchor-surface-endpoint pubkey). Cross-checks against substrate-emitted value. **Mismatch → operator rejects substrate as compromised; does not transmit deltas.**
6. **Operator verifies** owner_birth_attestation_signature against anchor-surface-fetched owner pubkey. Substrate now trusted.

This handshake is bidirectional in trust: substrate verifies the operator targets the correct substrate-ID; operator verifies the substrate is owner-attested and the owner pubkey is anchor-surface-fresh.

### §3.2 Delta absorption (L1_SKIN §2)

Every delta enters via the skin envelope:

- `envelope_digest = HMAC(operator_token, canonical_envelope_fields || payload)` — provides in-flight tamper detection + operator authentication via the substrate-generated operator_token shared at handshake.
- `causal_parent_ref` — links the delta into the causal DAG. If non-null, must refer to a sporocarp visible in the recent digest the agent could have read.
- Envelope freshness check + size check + payload_shape recognition.

Trust here: the substrate trusts the envelope is from the currently-handshaken operator (HMAC keyed by `operator_token`); the delta content itself is unfiltered (P2 universality).

### §3.3 Sporocarp emission (L1_TROPISM §B6)

Substrate-initiated; carries `causal_in_edges` proof — `(input_set, state-snapshot-hash, threshold-value, template_version)` — sufficient for I3 self-validation to re-derive the fruiting condition.

Trust here: the substrate proves its own sporocarps mechanically (not by self-claim). I3 self-validation runs every cycle; sporocarps without verifiable causal-proofs are rejected before DAG insertion.

### §3.4 CI-level mutation attestation (L1_GOVERNANCE §2.2)

The critical path. When the substrate proposes a contract-identity-level mutation:

1. **Substrate requests anchor-surface nonce**: anchor surface issues nonce bound at issuance to declared `mutation_hash + dag_tip_hash + timestamp`. Single-use, L1-tunable TTL (default 5 min anchor-trusted-time), rate-limited per substrate.
2. **Substrate emits attestation request envelope** with `proposed_mutation_canonical_bytes`, `proposed_mutation_hash`, `enumerated_dag_nodes_since_last_co_sign`, `operator_witness` signature (using operator's per-handshake private key over canonical bytes), `operator_signing_key_public`, anchor-surface nonce, dual-clock expiry constraints.
3. **Owner verifies independently at anchor surface**:
   - Renders `proposed_mutation_canonical_bytes` via the anchor-surface client (provenance-independent of substrate per L0 §9.3).
   - Re-computes `proposed_mutation_hash` from canonical bytes.
   - Verifies `operator_witness` signature against `operator_signing_key_public` (cross-checked via anchor-surface record of that handshake's logged event).
   - **DAG enumeration closure check**: reconstructs Merkle chain from prior co-signed tip via enumerated nodes; confirms current tip reachable AND every parent-hash referenced by any enumerated node resolves to ancestor-of-prior-tip OR another enumerated node (no hidden parallel branches).
   - Verifies nonce matches issuance-bound mutation_hash + dag_tip_hash + within TTL.
4. **Owner signs the tuple** `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`.
5. **Substrate verifies signature** + dual-clock validity. Mutation commits.

**Every byte the owner signs is independently re-derivable by all three parties** (substrate via canonical-bytes spec; operator via deltas + spec; owner via anchor-surface client render).

---

## §4. Trust maintenance (over time)

### §4.1 Owner key rotation (L1_GOVERNANCE §3.1)

Rotation requires:
1. Current owner publishes new candidate pubkey at anchor surface, signed by current key.
2. **Cooldown window** (L1-tunable default 30 anchor-surface-trusted-timestamp days). During cooldown, any pre-registered owner key may issue `rotation_veto`.
3. After cooldown without veto: dual-signed (current + new) rotation event commits. `owner_key_history` updates.

Verification of historical co-signs uses the key valid at the historical timestamp. **Active-prefix + archived-tail discipline** keeps tier-1 validation cost O(1) as history grows.

### §4.2 Substrate self-validation per cycle (L1_SCHEMA §4.1)

Every metabolic cycle: tier-1 fields (substrate-ID, owner_key_history active-prefix, DAG-tip-hash, classifier table, classifier-fixed-point fields, mortality-signal threshold + update-rule, skin surface declaration, canonical-bytes serializer spec). Every deep cycle: tier-2 fields, I5 reachability, recovery-drill scheduling.

I3 + I4 + I5 + I8 invariants are checked per cycle (per L1_CONTINUITY §1.1 5-step cycle).

### §4.3 Living Bets observatory (L0 §7)

7 signals (6 base + 1 composite). Falsifiability trigger: 90-day rolling window quorum (≥3 of 6 signals trending against bet + signal #6 ratio < 1 for ≥50% cycles) → `bet_weakening_quorum` event requires owner re-justification per L0 §10.2.

---

## §5. Trust recovery (failure modes)

### §5.1 Cold-resume (L1_CONTINUITY §3)

Pre-handshake invariant checks (I1, I3, I4, I5, I8) emit **witnesses, not verdicts**. Sampled by anchor-nonce-derived indices (per L0 §9.3). Owner / anchor-surface verifier independently re-derives.

Failure → `alive but quarantined`. Intake closed; only owner-attested administration deltas accepted. Owner-attested `quarantine_clearance` required for resumption.

### §5.2 Owner unavailability (L1_GOVERNANCE §3.2)

Owner liveness heartbeat goes stale at the anchor surface → `succession_required` immune event (anchor-surface-detected, substrate cannot manufacture). Pre-attested successor activates by signing `successor_activation` with their successor-private-key — anchor-surface-verified, not substrate-side-cached.

If no successor activates within grace: substrate transitions to `legacy` sub-state of alive (mutations frozen; daily ops continue). Legacy exits when ANY valid successor activates.

### §5.3 Substrate destruction (L1_GOVERNANCE §4.4)

- **Intentional-owner**: owner-signed `destruction_attestation` + `anchor_surface_final_seal`. Post-seal, substrate-ID is permanently destroyed at the anchor surface.
- **Catastrophic-environment**: recovery-drill failures + medium failure beyond budget.
- **Endogenous-pair**: substrate fruits `self_euthanasia_proposal` with operator_witness; owner co-attestation executes. Dual-channel (substrate + anchor-surface drill-failure auto-emit).

---

## §6. Trust limits (acknowledged asymmetries)

Carrier-asymmetry licenses some asymmetries that pure-symmetric pair models would forbid. These are declared, not concealed:

- **Substrate is identity carrier**: bestowal flows substrate → operator at each handshake; operator-disconnect ends a pair-instance but NOT the substrate's identity continuum.
- **Substrate cannot enforce against its own host** (dormancy host-observability per L0 §6, mycoparasite-15): owner-side monitoring is required for host-level adversarial detection.
- **Substrate cannot enforce against operator runtime** (L1_SKIN §5.4): exfiltration via the operator runtime is owner-side concern; substrate can only enforce its own boundary.
- **P1.a self-hosting**: the agent maintains substrate code. An adversarial agent can attack the substrate codebase itself. The anchor-surface out-of-band root raises the bar from "edit a file" to "compromise a separate system the owner controls".

These limits define what v0.9's trust model can and cannot mechanically guarantee. Beyond these limits, owner-side discipline is load-bearing.

---

## §7. Trust at federation (cross-substrate; cross-ref L2_FEDERATION)

Federation introduces inter-substrate trust. The trust model extends:
- Federation peer attestation at anchor surface (owner-attested per peer); aggregate re-attestation for O(1) owner workload at scale.
- Peer-trust freshness window (L1-tunable; default 90 days). Stale → `peer_attestation_stale`. Revoked → `untrusted_federation`.
- Federation event egress includes peer-revocation freshness check at emission (per L1_SKIN §3.1).
- Cross-substrate trust is NOT transitive: A trusts B trusts C does not imply A trusts C.

See `L2_FEDERATION.md` for the full federation doctrine.

---

## §8. Trust model invariants summary

The trust model rests on these (each independently traces to L0):

- **Identity is the pair (P1.c)**; substrate is the carrier-asymmetric identity vessel; operator brings per-handshake distinctness.
- **Out-of-band anchor surface (L0 §9)** is structurally non-substrate-authorable.
- **Canonical bytes + witnesses (L0 §9.3)** are independently re-derivable by all three parties.
- **Dual-clock attestation (L1_GOVERNANCE §2.2)** prevents substrate-cycle-throttling attacks.
- **DAG enumeration closure (L0 §9.2)** prevents hidden parallel branches.
- **Positive owner liveness heartbeat (L0 §9.2)** prevents manufactured-absence succession.
- **Owner-key rotation cooldown (L1_GOVERNANCE §3.1)** prevents same-attacker dual-sign.
- **OS-sealed substrate_secret (L1_SKIN §4.2)** prevents agent-maintainer secret-leakage.

When all eight hold, v0.9's trust model is adversarially-hardened against the 20 CRITICAL breaches enumerated in L1_HARD_RULES §1.

---

## §9. Open at L2

- **Anchor-surface-client distribution channels** beyond candidates listed (L0 §9.3): are there better candidates we haven't enumerated?
- **Cryptographic suite migration** when current suite is broken (not just deprecated): L1_GOVERNANCE §3.1 says "follows same pattern" but historical-reanchoring details may need L4 codification.
- **Anchor surface high-availability**: what happens if the anchor surface itself goes offline? Substrate cannot proceed with CI events. Possibly out-of-scope (owner picks anchor-surface mechanism robust enough; multiple-redundant anchor surfaces is L4).

These are L4-territory unless deferred surfaces become load-bearing for L3 design.
