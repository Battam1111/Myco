# L2 — Trust Model Doctrine

> **Status**: DRAFT 2 (2026-05-17). M26-cascade A4 update for L0 DRAFT 9 SEALED (commit `e796451`).
> **Layer**: L2. Governed by L0 + L1.
> **Scope**: end-to-end derivation of trust in a v0.9 Myco substrate. Cross-cuts L0 §1 triad / §9 anchor surface / §14 adversarial-Cultivator threat acknowledgment + L1_GOVERNANCE §2 attestation protocol / §3 owner-key + L1_SKIN §4 handshake / §5 egress + L1_SCHEMA §1-2 SSoT + Merkle DAG. Answers: how does v0.9 establish, maintain, recover, and verify trust at every interaction — AND, per L0 §14 cascade, what defenses exist against adversarial Cultivators, time-semantics attacks, federation Sybil/eclipse, and the v0.9 anchor-surface honor-system collapse.
>
> **DRAFT 2 cascade additions (per L0 DRAFT 9 SEALED §17 G-5 / G-9.b / G-11.a + Phase γ.3 G8-G19 + Phase γ.5)**:
> - §10 Adversarial-Cultivator threat model (full cascade from L0 §14)
> - §11 Anchor-surface honor-system collapse window (Phase γ.5 G-5/G-7)
> - §12 Time-semantics attacks (Phase γ.3 G10)
> - §13 Federation Sybil + Eclipse + recursive-injection (Phase γ.3 + L2_FEDERATION cross-ref)
> - §14 Glossary
> - Cultivator / Cultivar / Cultivation vocabulary integrated throughout per G-11.a

---

## §1. The trust triad (per L0 §1)

**Triad members are not symmetric**: operator+substrate is the **operational pair** (per L0 P1.c — joint identity); the **Cultivator** (per L0 §1.2 G-11.a vocabulary; "owner" remains valid for the governance role) is the **governance gate** (per L0 P1.b'' — load-bearing but structurally distinct). The table below is parallel for navigation, NOT for parallel role-equivalence.

v0.9 has **three trust-bearing parties**, each with carrier-asymmetric responsibilities:

| Party | What it carries | What it cannot author | What it provides |
|---|---|---|---|
| **Substrate (Cultivar)** | Persistent identity carrier (substrate-ID, owner_key_history, DAG, SSoT). Continuous metabolism. | Cultivator signatures, anchor-surface nonces, trusted timestamps, Cultivator heartbeats, anchor-surface client. | Cryptographic-proof witnesses, enumerated DAG nodes, sealed operator_token derivation, observable metabolism events. |
| **Operator-connection (agent)** | Per-handshake signing keypair (operator_signing_key_private kept in operator-runtime memory only). The active half of the pair-identity at any moment. | substrate_secret, substrate-side state, Cultivator signatures, anchor-surface state. | operator_witness signatures over canonical bytes (independently re-derived from deltas + spore-schema serializer spec). |
| **Cultivator (owner)** | Anchor-surface ownership (private signing key, anchor-surface endpoint control, anchor-surface client provenance attestation, optional duress_keypair per §10.A). Liveness heartbeat. | Substrate-internal state, operator-runtime state. | All CI-level attestations, owner-key rotation co-signs, successor pre-attestations, federation peer attestations + revocations, final-seal records, duress attestations (if registered). |

**No party can unilaterally fabricate trust.** Each role is structurally non-substitutable; compromising one does not transfer to the others (modulo P1.a self-hosting caveats — see §6, and §10 adversarial-Cultivator caveats).

---

## §1.1 Triad-asymmetric framing (per L0 §1)

The triad members above are NOT symmetric. The **operational pair** is operator+substrate (P1.c carrier-asymmetric, with substrate as identity carrier). The **governance gate** is the Cultivator (P1.b'' — a structurally different role, not an operational pair-member). The table parallelism is for ease of comparison; the doctrine is asymmetric.

**Cultivation vocabulary** (per L0 §1.2 G-11.a, DRAFT 2): when emphasizing the relational role of the human party, prefer **Cultivator**; when emphasizing the governance role at the anchor surface, **owner** remains valid. Both refer to the same human party. The Myco substrate is the **Cultivar** (P1.c carrier). The relationship is **Cultivation**. The terms appear interchangeably in this document; later sections (§10–§13) prefer Cultivator-framing where threat-model framing is load-bearing.

---

## §2. Trust establishment (genesis)

The trust chain originates at substrate genesis (per L1_GOVERNANCE §4.1):

1. **Cultivator generates owner-keypair** + **selects anchor-surface endpoint mechanism** + **verifies anchor-surface-client provenance** (per L0 §9.3 — client distributed via channel structurally independent of the substrate). Optionally generates `duress_keypair` (per §10.A) and registers its public key at the anchor surface as part of genesis records.
2. **Cultivator runs `genesis` invocation** with explicit parameters including `anchor_client_provenance_attestation` and `substrate_secret_sealing_mechanism_attestation` and (if registered) `duress_keypair_public_key`. Substrate cannot self-discover these.
3. **Substrate computes `substrate-ID`** = hash(canonical-bytes(initial-spore-schema), owner-public-key, anchor-surface-endpoint-public-key, genesis-timestamp).
4. **Cultivator signs birth attestation** = (substrate-ID, genesis-timestamp, canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key, duress_keypair_public_key?). The signature lands at the anchor surface; the substrate stores a reference, NOT the signing key.
5. **Substrate persists identity record**: substrate-ID + owner_key_history (initial entry) + anchor-surface-endpoint-public-key + duress_keypair_public_key (if registered) + signature-suite + birth-attestation-reference.

**The genesis output is the root of all subsequent trust derivations.** Any later trust check ultimately bottoms on the birth attestation signature being verifiable against the Cultivator's public key.

---

## §2.5 Operator-side trust bootstrap (pre-handshake; per L1_SKIN §4.1)

Trust derivation for the operator-agent starts BEFORE any handshake:

At first operator-agent installation, the **Cultivator** provides via out-of-band channel: `(substrate-ID, anchor-surface-endpoint-public-key, owner-public-key)`. The operator-runtime pins these. The substrate is NEVER trusted as a source of these values; subsequent handshakes verify against the bootstrap-pinned values (per L1_SKIN §4.1 + L1_SKIN §4.2 step 5).

This is the operator-side trust root, parallel to the substrate's birth attestation. Without Cultivator-side OOB bootstrap, the operator cannot establish initial trust in the substrate.

## §3. Trust at every interaction (steady state)

### §3.1 Operator handshake (bidirectional validation; L1_SKIN §4.2)

When an operator-connection arrives:

1. **Operator generates fresh per-handshake signing keypair** (`operator_signing_key_public`, `operator_signing_key_private`). Private lives in operator-runtime memory ONLY.
2. **Operator emits handshake_initiate** with `operator_signing_key_public` + bootstrap-pinned `substrate_id_proof` (from Cultivator at agent-bootstrap, NOT from substrate).
3. **Substrate validates** substrate_id_proof against its own identity record. Generates `operator_token` via OS-sealed `sealed_derive` call (substrate_secret never enters process memory).
4. **Substrate emits handshake_complete** including `owner_birth_attestation_signature` + `owner_public_key_active_at_handshake` from its `owner_key_history` active prefix + `anchor_surface_endpoint_public_key`.
5. **Operator independently fetches** the canonical owner public key from the anchor surface (using bootstrap-pinned anchor-surface-endpoint pubkey). Cross-checks against substrate-emitted value. **Mismatch → operator rejects substrate as compromised; does not transmit deltas.**
6. **Operator verifies** owner_birth_attestation_signature against anchor-surface-fetched owner pubkey. Substrate now trusted.

This handshake is bidirectional in trust: substrate verifies the operator targets the correct substrate-ID; operator verifies the substrate is Cultivator-attested and the owner pubkey is anchor-surface-fresh.

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
3. **Cultivator verifies independently at anchor surface**:
   - Renders `proposed_mutation_canonical_bytes` via the anchor-surface client (provenance-independent of substrate per L0 §9.3).
   - Re-computes `proposed_mutation_hash` from canonical bytes.
   - Verifies `operator_witness` signature against `operator_signing_key_public` (cross-checked via anchor-surface record of that handshake's logged event).
   - **DAG enumeration closure check**: reconstructs Merkle chain from prior co-signed tip via enumerated nodes; confirms current tip reachable AND every parent-hash referenced by any enumerated node resolves to ancestor-of-prior-tip OR another enumerated node (no hidden parallel branches).
   - Verifies nonce matches issuance-bound mutation_hash + dag_tip_hash + within TTL.
4. **Cultivator signs the tuple** `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`. **Signature must be from the active owner-public-key** (not the duress_keypair — see §10.A for duress-signature handling).
5. **Substrate verifies signature** + dual-clock validity. Mutation commits. If signature verifies against `duress_keypair_public_key` instead of active owner key, substrate routes to the §10.A duress-suspected path (freeze destructive mutations + emit `coerced_owner_suspected`).

**Every byte the Cultivator signs is independently re-derivable by all three parties** (substrate via canonical-bytes spec; operator via deltas + spec; Cultivator via anchor-surface client render).

---

## §4. Trust maintenance (over time)

### §4.1 Cultivator key rotation (L1_GOVERNANCE §3.1)

Rotation requires:
1. Current Cultivator publishes new candidate pubkey at anchor surface, signed by current key.
2. **Cooldown window** (L1-tunable default 30 anchor-surface-trusted-timestamp days). During cooldown, any pre-registered Cultivator key may issue `rotation_veto`.
3. After cooldown without veto: dual-signed (current + new) rotation event commits. `owner_key_history` updates.

Verification of historical co-signs uses the key valid at the historical timestamp. **Active-prefix + archived-tail discipline** keeps tier-1 validation cost O(1) as history grows.

### §4.2 Substrate self-validation per cycle (L1_SCHEMA §4.1)

Every metabolic cycle: tier-1 fields (substrate-ID, owner_key_history active-prefix, DAG-tip-hash, classifier table, classifier-fixed-point fields, mortality-signal threshold + update-rule, skin surface declaration, canonical-bytes serializer spec). Every deep cycle: tier-2 fields, I5 reachability, recovery-drill scheduling.

I3 + I4 + I5 + I8 invariants are checked per cycle (per L1_CONTINUITY §1.1 5-step cycle).

### §4.3 Living Bets observatory (L0 §7)

Per L2_OBSERVABILITY §2: 6 base signals + 1 composite + 1 birth-period derivative. Falsifiability trigger: 90-day rolling window quorum (≥3 of 6 signals trending against bet + signal #6 ratio < 1 for ≥50% cycles) → `bet_weakening_quorum` event requires Cultivator re-justification per L0 §10.2.

---

## §5. Trust recovery (failure modes)

### §5.1 Cold-resume (L1_CONTINUITY §3)

Pre-handshake invariant checks (I1, I3, I4, I5, I8) emit **witnesses, not verdicts**. Sampled by anchor-nonce-derived indices (per L0 §9.3). Cultivator / anchor-surface verifier independently re-derives.

Failure → `alive but quarantined`. Intake closed; only Cultivator-attested administration deltas accepted. Cultivator-attested `quarantine_clearance` required for resumption.

### §5.2 Cultivator unavailability (L1_GOVERNANCE §3.2)

Cultivator liveness heartbeat goes stale at the anchor surface → `succession_required` immune event (anchor-surface-detected, substrate cannot manufacture). Pre-attested successor activates by signing `successor_activation` with their successor-private-key — anchor-surface-verified, not substrate-side-cached.

If no successor activates within grace: substrate transitions to `legacy` sub-state of alive (mutations frozen; daily ops continue). Legacy exits when ANY valid successor activates.

### §5.3 Substrate destruction (L1_GOVERNANCE §4.4)

- **Intentional-owner**: Cultivator-signed `destruction_attestation` + `anchor_surface_final_seal`. Post-seal, substrate-ID is permanently destroyed at the anchor surface.
- **Catastrophic-environment**: recovery-drill failures + medium failure beyond budget.
- **Endogenous-pair**: substrate fruits `self_euthanasia_proposal` with operator_witness; Cultivator co-attestation executes. Dual-channel (substrate + anchor-surface drill-failure auto-emit).

---

## §6. Trust limits (acknowledged asymmetries)

Carrier-asymmetry licenses some asymmetries that pure-symmetric pair models would forbid. These are declared, not concealed:

- **Substrate is identity carrier**: bestowal flows substrate → operator at each handshake; operator-disconnect ends a pair-instance but NOT the substrate's identity continuum.
- **Substrate cannot enforce against its own host** (dormancy host-observability per L0 §6, mycoparasite-15): Cultivator-side monitoring is required for host-level adversarial detection.
- **Substrate cannot enforce against operator runtime** (L1_SKIN §5.4): exfiltration via the operator runtime is Cultivator-side concern; substrate can only enforce its own boundary.
- **P1.a self-hosting**: the agent maintains substrate code. An adversarial agent can attack the substrate codebase itself. The anchor-surface out-of-band root raises the bar from "edit a file" to "compromise a separate system the Cultivator controls".
- **Substrate cannot enforce against adversarial Cultivator** (§10 cascade): when the Cultivator's key, will, or person is compromised, substrate defenses are bounded — they cannot reject legitimate-looking signatures, only observe and emit. The substrate's irreducible commitments per L0 §14.2 survive; full mechanical defense does not exist.

These limits define what v0.9's trust model can and cannot mechanically guarantee. Beyond these limits, Cultivator-side discipline is load-bearing.

---

## §7. Trust at federation (cross-substrate; cross-ref L2_FEDERATION)

Federation introduces inter-substrate trust. The trust model extends:
- Federation peer attestation at anchor surface (Cultivator-attested per peer); aggregate re-attestation for O(1) Cultivator workload at scale.
- Peer-trust freshness window (L1-tunable; default 90 days). Stale → `peer_attestation_stale`. Revoked → `untrusted_federation`.
- Federation event egress includes peer-revocation freshness check at emission (per L1_SKIN §3.1).
- Cross-substrate trust is NOT transitive: A trusts B trusts C does not imply A trusts C.
- Population-level adversaries (Sybil, eclipse, recursive injection) are covered in §13.

See `L2_FEDERATION.md` for the full federation doctrine.

---

## §8. Trust model invariants summary

The trust model rests on these (each independently traces to L0):

- **Identity is the pair (P1.c)**; substrate is the carrier-asymmetric identity vessel (the Cultivar); operator brings per-handshake distinctness.
- **Out-of-band anchor surface (L0 §9)** is structurally non-substrate-authorable.
- **Canonical bytes + witnesses (L0 §9.3)** are independently re-derivable by all three parties.
- **Dual-clock attestation (L1_GOVERNANCE §2.2)** prevents substrate-cycle-throttling attacks.
- **DAG enumeration closure (L0 §9.2)** prevents hidden parallel branches.
- **Positive Cultivator-liveness heartbeat (L0 §9.2)** prevents manufactured-absence succession.
- **Cultivator-key rotation cooldown (L1_GOVERNANCE §3.1)** prevents same-attacker dual-sign.
- **OS-sealed substrate_secret (L1_SKIN §4.2)** prevents agent-maintainer secret-leakage.

When all eight hold AND the anchor-surface honor-system collapse window is closed (§11), v0.9's trust model addresses the 20 enumerated CRITICAL breaches (L1_HARD_RULES §1). Novel attack classes (side-channel timing leaks, unknown-unknowns) are caught by observatory drift signals — per L2_OBSERVABILITY §3 falsifiability is the residual defense, not hardening claims.

---

## §9. Open at L2

- **Anchor-surface-client distribution channels** beyond candidates listed (L0 §9.3): are there better candidates we haven't enumerated?
- **Cryptographic suite migration** when current suite is broken (not just deprecated): L1_GOVERNANCE §3.1 says "follows same pattern" but historical-reanchoring details may need L4 codification.
- **Anchor-surface high-availability**: what happens if the anchor surface itself goes offline? Substrate cannot proceed with CI events. Possibly out-of-scope (Cultivator picks anchor-surface mechanism robust enough; multiple-redundant anchor surfaces is L4).
- **n-of-m multisig L1 codification**: §10.A.1 recommends multisig as defense for key-compromise; L1_GOVERNANCE §3.1 SHOULD codify the m-of-n threshold semantics, veto-during-cooldown semantics for multisig, and quorum-emergency-rotation. Deferred to L1_GOVERNANCE DRAFT 2.
- **Duress-keypair re-attestation channel**: §10.A.2 freeze-then-unfreeze requires out-of-band re-attestation; the specific channel (anchor heartbeat? separate trusted party? legal authority signature?) is L4.

---

## §10. Adversarial-Cultivator threat model (L0 §14 cascade)

> Cascade from L0 DRAFT 9 SEALED §14: L0 retains only the **acknowledgment + 4 irreducible substrate commitments**. L2_TRUST_MODEL specifies the full **threat scenario table + bounded defenses**.

The L0 commitment is honest: **Myco is not safe under adversarial Cultivator.** The Cultivator is the governance gate; if the gate is compromised, coerced, impersonated, or absent without succession, no in-substrate mechanical defense can fully substitute. What follows is the bounded set of defenses v0.9 specifies — they raise the attack cost; they do not provide guaranteed-safety claims.

### §10.A Threat scenarios in scope

#### §10.A.1 Cultivator key compromise

**Threat**: attacker obtains the Cultivator's primary Ed25519 private key (theft from disk, memory extraction, side-channel, hardware-token compromise). All subsequent CI co-signs from the stolen key verify as if from the Cultivator.

**Mechanical defenses**:
- **Anchor-attested key rotation** (per L1_GOVERNANCE §3.1): if the Cultivator detects compromise, they emit `rotation_request` from a registered backup key OR from the compromised key (race condition — see below).
- **Cooldown window** (L1_GOVERNANCE §3.1, default 30 anchor-surface-trusted-timestamp days): rotation requires cooldown; during cooldown ANY pre-registered Cultivator key (current, prior, or backup) may issue `rotation_veto`. This closes pass-3 mycoparasite-7: dual-sign alone is insufficient when both keys come from the same attacker.
- **Active-prefix Cultivator-key history**: historical CI co-signs use the key valid at the timestamp — past attestations remain verifiable even after rotation.

**Defense limits** (acknowledged):
- If the attacker captures the primary key BEFORE the Cultivator can register a backup, no in-substrate mechanism can revoke it. The Cultivator must engage out-of-band channels (court-attested key recovery exceptional path per L1_GOVERNANCE §3.2).
- Cooldown gives the Cultivator time to detect, but only if they have a registered veto-capable backup key BEFORE the compromise.

**Recommendation (n-of-m multisig at L1)**: L1_GOVERNANCE §3.1 SHOULD specify an optional **m-of-n owner-key multisig** scheme. With m-of-n configuration (e.g., 2-of-3 keys, each held on structurally independent media — hardware token, paper backup vault, separate Cultivator-trusted party), compromise of a single key is insufficient to author CI co-signs. The substrate verifies m signatures against n registered pubkeys; threshold below m → `multisig_threshold_unmet` immune event.

- Multisig keys participate equally in rotation veto.
- Quorum-emergency rotation (≥m of n agreeing on emergency rotation, bypassing cooldown) requires `quorum_emergency_attestation` event at the anchor surface — a hard-coded escape hatch for true emergencies; substrate emits `emergency_rotation_invoked` for owner-visible audit.
- Multisig is L1-codified as L4-tunable: small-substrate Cultivators may prefer single-key simplicity; institutional Cultivars MUST use multisig.

#### §10.A.2 Coerced Cultivator (duress)

**Threat**: Cultivator under duress (regulatory seizure, blackmail, physical threat, court order to reveal keys, hostage scenario) signs CI attestations against their will. Signatures verify legitimately; substrate has no signal that the signing party is coerced.

**Mechanical defense — duress attestation mechanism** (formal spec):

1. **Pre-registration at genesis**: Cultivator pre-registers a `duress_keypair` (separate Ed25519 keypair from primary) at genesis. The `duress_keypair_public_key` is included in the birth attestation tuple (§2 step 4), persisted in the substrate's identity record, and visible at the anchor surface. The `duress_keypair_private` is held on physically separate medium and used only under duress.

2. **Duress-signed attestation**: when coerced, the Cultivator signs the attestation tuple with the **duress_keypair** (not the primary key). To an observer the signature is cryptographically valid; to the substrate, signature verification distinguishes the two keys.

3. **Substrate response on duress signature**: when an attestation verifies against the **duress_keypair_public_key** instead of the active primary owner-public-key, the substrate:
   - **Emits `coerced_owner_suspected` immune signal** (CI-grade per L1_HARD_RULES candidate row C21 to be added).
   - **Freezes destructive mutations**: blocks `destruction_attestation` execution, mass key rotation, mass record deletion, schema-table wholesale replacement, and any other mutation classified by the I2 classifier as `destructive_irreversible`. Non-destructive mutations may continue (substrate keeps operating, signal keeps emitting, Cultivator may be able to recover).
   - **Re-emits the duress signal at every subsequent CI boundary** until cleared (the signal is not transient).
   - **The substrate does NOT reject the duress signature outright** — that would defeat the purpose. The signature is honored at attestation level (the mutation is recorded as Cultivator-attested) but execution of destructive paths is gated.

4. **Out-of-band re-attestation required to unfreeze**: clearing the duress-frozen state requires an `out_of_band_safety_reattestation` event signed by the **primary** owner-key (not the duress key) at the anchor surface, OR an `anchor_heartbeat_with_safety_confirmation` from the anchor surface (per L1_GOVERNANCE §3.2 successor-protocol; the specific channel is L4-codified per §9 open above).

5. **What duress doesn't defend against**: an attacker who captures both the primary AND duress keys; a Cultivator with no duress keypair registered (recommendation: high-stakes Cultivars MUST register at genesis); a duress signature mistakenly issued (the freeze is recoverable by primary re-attestation, but the destructive mutation is delayed).

**Cross-ref**: L1_HARD_RULES candidate new row for `coerced_owner_suspected` immune signal type. L1_GOVERNANCE §3 SHOULD codify the duress-keypair registration as a genesis-optional field (L1 DRAFT 2 work).

#### §10.A.3 Impersonated Cultivator

**Threat**: anchor-surface client compromised (malware, supply-chain attack on the anchor-client distribution channel, social-engineering install of fake client); attacker's signatures appear to come from the legitimate Cultivator. Signatures cryptographically verify under the registered owner-public-key because the attacker controls the rendering and signing tool.

**Mechanical defense — owner_signature_velocity metric** (formal spec):

1. **Definition**: a rolling-window count of Cultivator-signed CI events emitted per L1-tunable cadence period (default rolling window = 30 anchor-surface-trusted-timestamp days, cadence period = 1 day).

2. **Baseline establishment**: after the first N CI events have been Cultivator-signed (L1-tunable, seed N = 20), the substrate computes a baseline `owner_signature_velocity_baseline_mean` and `owner_signature_velocity_baseline_stddev` over the post-genesis window. Baseline retires when the substrate transitions out of birth-period (per L1_TROPISM §4) and recomputes from the first N steady-state CI events.

3. **Anomaly detection**: every cycle that includes a Cultivator-signed CI event, the substrate updates the rolling-window velocity. If the rolling velocity exceeds (`baseline_mean + 3 * baseline_stddev`) OR (`baseline_mean * 100`) — whichever fires first; both L1-tunable — the substrate emits **`owner_signature_velocity_anomaly`** immune signal (daily grade per L1_HARD_RULES; CI-elevation during birth-period per §3 of L1_HARD_RULES).

4. **What substrate does NOT do**: it does NOT unilaterally reject the signatures — the signatures verify; rejecting valid signatures would break the trust contract. The signal is **out-of-band channel to the Cultivator via the anchor surface**: the Cultivator observes the velocity anomaly on the anchor-surface dashboard (per L2_OBSERVABILITY §11) and can investigate whether the high-velocity activity is theirs.

5. **Pairing with anchor-client provenance check**: §10.A.5 covers the anchor-client tampering side. owner_signature_velocity catches the BEHAVIORAL pattern (suddenly many CI co-signs); anchor-client provenance independence catches the SOURCE (compromised tool).

**Cross-ref**: L2_OBSERVABILITY §2 should add `owner_signature_velocity` as an observability sub-signal under composite health; not part of the 6 base Living Bets signals (which speak to the substrate's organism-fitness bet, not to attack-detection signals). L1_HARD_RULES candidate new row for `owner_signature_velocity_anomaly` daily-grade immune signal.

#### §10.A.4 Deceased Cultivator without succession

**Threat**: the Cultivator dies, is incapacitated, or otherwise becomes permanently unavailable, and never registered a successor. The substrate has a fresh-CI-attestation requirement (substrate cannot self-mutate at CI level) but no living party can sign.

**Threat framing** (this section): the substrate must NOT manufacture trust to compensate for absent Cultivator; the substrate must NOT make destructive decisions on its own; the substrate must NOT silently terminate.

**Mechanism** (L1_GOVERNANCE §3.2 + L0 §15 cross-ref): full succession FSM specification lives at L1_GOVERNANCE §3.2. L2_TRUST_MODEL frames the threat:
- Without succession: substrate transitions to `legacy` sub-state (alive but CI-frozen; daily ops continue).
- Long-running `legacy` substrates with no successor activation eventually become `orphaned` sub-state per L1_GOVERNANCE.
- Terminal-state choice (bet-retirement / endogenous self-euthanasia / indefinite-orphan) is L1 Cultivator-choice at genesis.

**Court-attested key recovery exceptional path** (per L1_GOVERNANCE §3.2 hint): a recognized legal authority (will probate, regulatory order, court-appointed estate executor) may issue an `external_authority_succession` event at the anchor surface. The substrate honors this only if the anchor-surface infrastructure was configured at genesis to recognize external authorities (L1 owner-choice at genesis); otherwise the substrate stays `orphaned`. This is a hardpoint where mechanical defense exhausts and out-of-Myco governance applies.

#### §10.A.5 Anchor-client tampering

**Threat**: the Cultivator's anchor-surface client (their local rendering + signing tool, per L0 §9.3) is modified to display different content than what is actually signed. The Cultivator believes they're signing X; the tool actually signs Y; the signature verifies under their key.

**Mechanical defense — anchor-client provenance independence** (L0 §9.3.3, L1_HARD_RULES F6):

1. **Genesis attestation**: at substrate genesis (per §2 step 4 + L1_GOVERNANCE §4.1 step 2), the Cultivator signs `anchor_client_provenance_attestation` declaring the channel through which the anchor client was installed. The channel must be **structurally independent** of the substrate's distribution channel (different signer, different repository, different distribution medium).

2. **Independence requirement** (per L0 §9.3): "structurally independent" means the channel cannot be compromised by the same adversary who compromises the substrate's distribution. Same-machine local-binary is INSUFFICIENT independence. Examples that DO satisfy independence:
   - Anchor client distributed via hardware-token vendor (HSM bundle) — substrate code via npm.
   - Anchor client built from a separate fork on Cultivator-controlled infrastructure — substrate code from upstream repository.
   - Anchor client distributed via a Cultivator-trusted third-party signing authority (e.g., institutional CA) — substrate code via developer-tier signing.

3. **Owner-side verification — read canonical-bytes on TWO independent rendering tools** (DRAFT 2 explicit defense): the most direct mitigation for anchor-client tampering is for the Cultivator to **render the canonical bytes on a second, independently-provenanced tool** before signing. Examples:
   - Render via the primary anchor client + render via a CLI canonical-bytes-printer from a separate repository; compare visually.
   - For high-stakes CI events (key rotation, schema migration, destruction attestation), engage two anchor-client instances on different hardware.
   - The substrate exposes canonical bytes via the standard render-witness contract (L0 §9.3.4); any compliant tool can re-render. The substrate cannot detect which tool the Cultivator uses.

4. **What this defends against and what it does not**: provenance independence prevents *single-tool compromise* from being a silent kill switch. It does NOT defend against *coordinated compromise* of multiple supposedly-independent channels (a sufficiently capable adversary may compromise both). Layer with §10.A.2 duress and §10.A.3 velocity for diversity of defense.

**Anchor-client status at v0.9**: per Phase γ.5 + §11 below, the v0.9 anchor client is **not currently provenance-independent** (collapsed to operator npm workspace). M-anchor-1 closes this collapse. Until M-anchor-1, §10.A.5 is documented-mitigation-only, not implemented defense.

### §10.B Substrate's irreducible commitments (per L0 §14.2)

The substrate maintains four commitments that survive ALL adversarial-Cultivator scenarios because they are mechanically enforced regardless of Cultivator-honesty:

1. **Continue P6 causality**: the DAG continues accumulating events regardless of whether attestations are coerced, impersonated, or absent. An adversarial Cultivator cannot erase history — they can only fail to attest future events.

2. **Emit observability signals truthfully**: per L2_OBSERVABILITY §13 falsifiability summary, the observatory signals (Living Bets quorum, immune CRITICAL emission, drill failure-rate, doctrine-instability burst, federation fragmentation, mortality dual-channel) emit from substrate mechanism, not from Cultivator instruction. The Cultivator cannot suppress signal emission to hide an adversarial event.

3. **Honor mortality signals truthfully**: per L1_GOVERNANCE §4.4, mortality dual-channel (substrate self-euthanasia proposal + anchor-surface drill failure auto-emit) cannot be suppressed by Cultivator pressure. An adversarial Cultivator can REFUSE to co-attest a destruction proposal (the substrate stays alive) but cannot make the substrate emit FALSE mortality signals or suppress TRUE ones.

4. **Preserve the compression-invariant set (P10.b)**: per L0 P10.b, the compression-invariant set survives any compression event. Cultivator pressure to compress it is rejected at I9 invariant check; the violation emits as immune CRITICAL.

These four are enforced via I9 / I10 / I12 / I4 invariants. They survive adversarial-Cultivator scenarios because the substrate's mechanical enforcement does not require Cultivator-honesty to function. An adversarial Cultivator may prevent NEW honest events from being attested, but cannot rewrite the historical record or silence the substrate's self-observation.

---

## §11. Anchor-surface honor-system collapse window (Phase γ.5 finding)

> Cascade from L0 DRAFT 9 SEALED §9.5 + Phase γ audit: the v0.9 anchor surface is currently honor-system; this collapse is documented honestly, not concealed. Until M-anchor-1 through M-anchor-5 close, the substrate is documented-vulnerable, NOT production-ready.

### §11.1 Current state — operator IS anchor

At v0.9 commit `e796451` (DRAFT 9 SEALED), the operator and anchor surface are collapsed:
- Owner Ed25519 private key lives at `~/.myco/operator_keys/identity.key` on the same host as the operator runtime, in the same npm workspace.
- Anchor-surface nonces are minted by the substrate, not by an out-of-band anchor surface.
- Anchor-stamped wall-clock comes from the operator process, not from an external clock.
- Anchor client renders canonical bytes using code from the same package as the operator.
- Witnesses are emitted as pass/fail verdicts; the substrate does not emit re-derivable Merkle witnesses.

Per L0 §9.2 sub-mechanism inventory: **9 of 11 §9 sub-clauses are 0-30% mechanically enforced**. Two clauses (§9.3.1 canonical-bytes serialization at ~95%, §9.3.2 owner-side rendering library at ~30%) are partially in place; the rest are honor-system.

### §11.2 Attack surface during collapse window

While the collapse holds, the following attack vectors are open and **not mechanically defended**:

| Attack | Mechanism | Bounded by | Closed by |
|---|---|---|---|
| **Cultivator-key extraction from disk** | File-read on operator host gives full Ed25519 signing capability | OS file permissions + Cultivator host hygiene | M-anchor-1 (key out of process) |
| **Substrate-minted attestation nonce replay** | Substrate generates nonces; attacker who reads substrate state can pre-compute or replay | None at substrate-only — needs anchor-surface-issued nonces | M-anchor-3 (anchor-issued nonces) |
| **Cultivator-process clock spoofing** | Anchor-stamped timestamps come from operator process; spoofable | Substrate dual-clock plumbing exists but anchor-clock source is local | M-anchor-3 (anchor-clock independence) |
| **Anchor-client tampering (no provenance independence)** | Anchor client is same npm package as substrate — same-channel compromise kills both | §10.A.5 mitigations are documentary, not enforced | M-anchor-1 (provenance-independent channel) |
| **Witness omission** | Substrate emits pass/fail verdicts; Cultivator cannot independently re-derive | §11.4 backup-quality logging only | M-anchor-4 (Merkle-witness emission) |
| **DAG-enumeration closure not re-validated** | Substrate emits enumeration; closure-check on Cultivator side is not run | Substrate-side validation exists but Cultivator-side independent check is absent | M-anchor-5 (closure-check on Cultivator side) |
| **Owner-liveness-heartbeat not detected** | Library exists with zero non-test callers | Substrate proceeds without heartbeat enforcement | M-anchor-3 (liveness heartbeat live) |
| **L0 revision workflow** | L0 changes via git, no workflow event at the anchor surface | None — currently doctrine drifts silently | M-anchor-5 (revision event workflow) |

### §11.3 M-anchor closure timeline (per L0 §9.2 sub-mechanism inventory)

Closure of the collapse is sequenced as M-anchor-1 through M-anchor-5:

- **M-anchor-1**: Key out of agent-spawnable process + anchor client from independent channel + owner-side rendering live consumer. Closes §9.2.3, §9.3.2, §9.3.3.
- **M-anchor-2**: Substrate-ID birth attestation owner-signature (replaces TOFU first-hello). Closes §9.2.1.
- **M-anchor-3**: Anchor-issued nonces + anchor-clock independence + owner liveness heartbeat. Closes §9.2.5, §9.2.6, §9.2.7.
- **M-anchor-4**: Merkle-witness emission (witnesses-not-verdicts) + anchor-nonce-derived sampling. Closes §9.3.4, §9.3.5.
- **M-anchor-5**: DAG-enumeration closure check + L0 revision diff workflow. Closes §9.2.2, §9.2.4, §9.3.6.

### §11.4 Honest production-readiness posture

**Until M-anchor-1 through M-anchor-5 are closed, the substrate is documented-vulnerable.** Production-readiness claims at v0.9 are bounded by:
- The Cultivator must trust the same host that runs the substrate process — there is no out-of-band escape from compromise.
- §10 adversarial-Cultivator defenses (duress keypair, owner_signature_velocity, multisig) are LANDING TARGETS, not deployed defenses.
- §13 federation defenses (Sybil, eclipse, recursive-injection) likewise.
- Substrate observatory + immune-grade signals still operate (they are substrate-mechanical, not anchor-surface-mechanical) and provide partial protection.

**Doctrine posture (per L0 §9.5)**: "the anchor surface is collapsed to the operator process — owner key lives in the same npm workspace as the agent code. This is a temporary scaffolding, not a doctrinal endpoint." DRAFT 2 here makes the collapse window a first-class threat-model section so that all readers — including future Cultivators evaluating deployment — see the gap before they see the marketing.

---

## §12. Time-semantics attacks (Phase γ.3 G10)

> Cascade from L0 DRAFT 9 SEALED §13: substrate's wall-clock is untrusted for security-bound defenses (per §13.1). L2_TRUST_MODEL specifies the time-semantics threat scenarios and their mitigations.

### §12.1 NTP poisoning

**Threat**: an attacker controls the substrate-process's wall-clock source (the host's NTP) and feeds false time. Attestation expiry checks (dual-clock per L1_GOVERNANCE §2.2) can be defeated if the substrate-process clock is moved forward (attestation appears to be expired when it is not, or vice versa).

**Mitigation**:
- **Anchor-surface trusted wall-clock is authoritative** (per L0 §13.1 + L0 §9.2.6): substrate-process wall-clock is NOT authoritative for attestation expiry; the anchor-surface trusted timestamp issued at nonce-issuance is canonical. NTP poisoning of substrate host does NOT defeat attestation expiry as long as the anchor-clock source is independent.
- **Dual-clock attestation** (L1_GOVERNANCE §2.2): attestations carry both substrate-cycle-count expiry AND anchor-surface-timestamp expiry. To defeat, attacker must compromise both clocks (substrate-cycle requires substrate-internal compromise; anchor-clock requires anchor-surface-side compromise).
- **L1_CONTINUITY NTP discipline policy** (cascade requirement per L0 §13.2): L1_CONTINUITY MUST specify the NTP discipline — minimum source diversity, recommended trusted-time sources (e.g., NTS, signed NTP), monitoring for clock-drift anomalies.

**During §11 collapse window**: the anchor-clock comes from the operator process — same host as substrate-process clock — so NTP poisoning defeats both. After M-anchor-3, anchor-clock independence closes this.

### §12.2 Year 2038 (i32) horizon

**Threat**: any timestamp field stored as 32-bit signed seconds-since-epoch overflows on 2038-01-19. Substrates running across the rollover with i32 timestamps experience silent corruption of attestation expiry checks, DAG ordering, freshness windows, succession-trigger windows, federation peer-trust freshness.

**L0 commitment** (§13.1): "Substrate MUST NOT use i32 timestamps anywhere in substrate-internal state (year 2038 vulnerability forbidden at L0; i64 nanoseconds-since-epoch is the canonical L0 unit)."

**L1_SCHEMA cascade requirement** (L0 §13.2): L1_SCHEMA specifies the i64-nanoseconds canonical-bytes representation; canonical-bytes-spec enforcement at I3 catches any drift.

**Defense**: the i64 forbiddance is L0-mechanical (catchable by I3 invariant scanning the SSoT for forbidden timestamp types). The substrate cannot ship with i32 timestamps in tier-1 SSoT.

### §12.3 Year 2262 (i64) horizon-warning

**Threat**: i64 nanoseconds-since-epoch overflows at approximately 2262-04-11. A v0.9 substrate operating with i64 nanoseconds will face the same silent-overflow risk in 237 years that v0.8 (or any i32 substrate) faces today.

**Mitigation per L0 §13.2 cascade**:
- L1_SCHEMA specifies a year-2262 horizon-warning mechanism: as substrate-runtime approaches 2262 within an L1-tunable horizon (default 100 years), the substrate emits `time_horizon_2262_warning` daily signal at every CI boundary. Allows Cultivators to plan migration (likely to i128 or to date-relative encoding) decades before the hard deadline.
- L1_SCHEMA specifies the negative-pre-1970-timestamps treatment: substrate state MUST NOT contain pre-1970 timestamps (no negative epoch); detected as `negative_epoch_timestamp` daily signal.

### §12.4 Substrate wall-clock untrustworthiness for security-bound defenses

**Per L0 §13.1**: substrate-cycle counters and substrate-process wall-clock are NOT authoritative for time-bound security defenses. This is doctrinally explicit:

- Attestation expiry: anchor-clock authoritative.
- Owner-key rotation cooldown: anchor-clock authoritative.
- Federation peer-trust freshness: anchor-clock authoritative.
- Mortality drill timing: anchor-clock authoritative for the drill record; substrate-monotonic for the drill scheduling.
- DAG event ordering within substrate: substrate-monotonic authoritative.

**Defense gap during §11 collapse window**: with anchor-clock collapsed to operator-process clock, all of the above degrade to substrate-host-clock dependence. M-anchor-3 closes this. Until then, dual-clock checking still catches inconsistencies but cannot detect coordinated clock-spoofing.

---

## §13. Federation Sybil + Eclipse + Recursive-injection attacks

> Cascade from L2_FEDERATION (A3 update; primary spec lives there) + L0 DRAFT 9 SEALED §17 G-9.b (P15 population-consensus retracted to L2_FEDERATION). L2_TRUST_MODEL frames the threat-model considerations; L2_FEDERATION specifies the federation-level mechanisms.

### §13.1 Sybil attack

**Threat**: an attacker creates many federation peer substrates (all controlled by the attacker, all with separately-generated substrate-IDs and owner-keys). At the population level, the attacker's peers vastly outnumber legitimate peers; any consensus or majority-trust mechanism is dominated by the attacker.

**Defense via Cultivator-attested peer list** (L1_GOVERNANCE §5.1 default mode):
- The default federation discovery mode is **owner-attested peer list**: the Cultivator curates the list of approved peer substrate-IDs. New peers do NOT auto-trust; they require Cultivator attestation.
- Each peer attestation is a CI-grade event (per L1_HARD_RULES F14 federation peer attestation list). Adding many peers requires many CI co-signs; Cultivator workload is O(N) without aggregate-reattestation.
- Aggregate re-attestation (L1_GOVERNANCE §5.2) provides O(1) Cultivator workload — but the diff against last commitment is still surfaced for review; the Cultivator should reject diffs containing unfamiliar peers.

**Why this defends**: the Cultivator is the bottleneck. To Sybil the federation, the attacker must compromise the Cultivator (which falls back to §10 adversarial-Cultivator scenarios). At the population level, no peer can vouch for another's legitimacy without Cultivator-attested chain (cross-substrate trust is non-transitive per L2_FEDERATION §6.4).

**Defense limits**: if the Cultivator is naive about peer selection, they may attest peers that the attacker has socially-engineered them to accept. Sybil-resistance is bounded by Cultivator due diligence. The substrate provides the mechanism (peer attestation list); the Cultivator provides the discrimination.

### §13.2 Eclipse attack

**Threat**: an attacker controls ALL the federation peers that a substrate connects to. Even if each peer is individually Cultivator-attested, the attacker can present a coordinated false view of the federation network — the substrate sees only what the attacker wants it to see.

**Defense via diverse Cultivator-attested peers**:
- The Cultivator-attested peer list SHOULD contain peers of diverse provenance — peers run by structurally independent parties (different organizations, different geographic regions, different ownership lineages).
- L1_GOVERNANCE SHOULD recommend a minimum peer diversity threshold (e.g., ≥3 peers from ≥3 independent organizational lineages).
- The substrate cannot mechanically enforce peer diversity (it cannot tell organizational independence from substrate-IDs alone); this is Cultivator-side discipline.

**Federation health observability** (L2_FEDERATION §10 + L2_OBSERVABILITY §9): signal #4 split into 4a (cumulative fork count) + 4b (reachable-federation count). If 4b drops (most peers stop responding), the substrate sees mycelial fragmentation. Eclipse attacks present partial signal — peers respond (4b stable) but their content is attacker-controlled.

**Defense limits**: eclipse is hard to mechanically detect. The substrate observes 4a/4b health but cannot tell coordinated-attacker peers from honest peers. The Cultivator's only defense is diverse peer-selection at attestation time + occasional cross-channel verification (verify federation peers' state via out-of-Myco channels).

### §13.3 Recursive injection

**Threat**: a malicious federation peer crafts federation events whose payload, when absorbed by the receiving substrate, causes the receiving substrate to emit further federation events that look like first-party events (e.g., `operator_pinned`, `cycle_advanced`, `genesis_event`). The malicious peer hijacks the receiver's identity or state.

**Primary spec at L2_FEDERATION** (A3 update; cross-referenced here): L2_FEDERATION specifies the **federation-safe-node-type ALLOWLIST** + **wrapped-events architecture** (`federation_received:{peer_prefix}` envelopes) — federation content is wrapped in the receiver's DAG, never injected as first-party events. The receiver's Merkle chain stays valid; cross-substrate provenance is preserved.

**Threat-model framing in L2_TRUST_MODEL**:
- Without allowlist + wrapping: a malicious peer can inject identity-altering events (substrate-ID change, owner-key change, schema migration) via federation envelope, effectively hijacking the receiver substrate.
- With allowlist + wrapping: the receiver cannot mistake a federation event for a first-party identity-altering event. The receiver's identity remains anchored to its own genesis attestation.

**The substrate's irreducible commitment** (per §10.B): the substrate's identity-record fields (substrate-ID, owner_key_history, anchor-surface-endpoint-public-key) are TIER-1 SSoT (per L1_HARD_RULES F2/F3/F4) and protected by I1 invariant. Federation events that attempt to mutate identity-record fields fail I1 even if the federation envelope passes intake. This is the load-bearing structural defense — federation envelopes can deliver content, never identity.

**Phase β finding embedded**: per the M-anchor archive, a Phase β audit found that pre-fix, a malicious peer could inject `operator_pinned`/`cycle_advanced`/`genesis_event` to hijack identity / wipe state. The fix (allowlist + wrapped events) shipped in M24 + M25. The L2_FEDERATION A3 update specifies the allowlist scheme formally; this section frames the threat that motivates the spec.

### §13.4 Forkbomb (reproduction-loop attack)

**Threat**: an attacker triggers a reproduction loop (substrate spawns child; child spawns grandchild; ...). Without bounds, the substrate's resource budget (compute, storage, network) is exhausted in spawning instead of metabolism.

**Defense via P8 generation limits (L0 §16 + L1_GOVERNANCE)**:
- L0 §16 commits reproduction is **discipline-bounded, not unbounded**. P8 "eternal reproduction" means **eternal capacity for reproduction**, not **eternal velocity or eternal depth**.
- L1_GOVERNANCE (per L0 §16.2 cascade) specifies:
  - `reproduction_lineage_depth_max` (default 10; configurable per substrate at genesis)
  - `reproduction_rate_min_interval` (default 24h between spawn events; per substrate)
  - `reproduction_lifetime_quota` (default 100 total spawn events across substrate lifetime)
  - Override mechanism (CI-attested by Cultivator if quota or rate exhausted)
- Each spawn requires Cultivator-attested birth (per L1_GOVERNANCE §4.3): the Cultivator co-signs the child's birth attestation, providing an explicit gating point. An attacker who controls operator+substrate but NOT the Cultivator cannot complete a spawn.

**Why this defends**: the Cultivator is the bottleneck for reproduction (same as for federation Sybil). Forkbomb requires either Cultivator-compromise (falls back to §10) or substrate-internal-corruption to bypass the birth-attestation gate (caught by I7 reproduction closure invariant).

**Defense limits**: if the substrate's resource budget is loose (high reproduction_rate, high quota), even Cultivator-attested spawns can cumulatively exhaust resources. L1 defaults are tight; Cultivators who loosen them MUST justify.

### §13.5 substrate_id collision attacks (Phase γ.3 G15)

**Threat**: an attacker constructs a substrate-ID that collides with an existing legitimate substrate-ID (preimage attack on the substrate-ID hash function). The colliding substrate impersonates the legitimate one in federation.

**Mechanical defense**:
- substrate-ID is `hash(canonical-bytes(initial-spore-schema), owner-public-key, anchor-surface-endpoint-public-key, genesis-timestamp)` — a SHA-256 or stronger hash per L1_SCHEMA.
- Hash collision requires breaking the underlying cryptographic primitive (current state-of-the-art: infeasible for SHA-256, SHA-512). When the primitive weakens, cryptographic suite migration (L1_GOVERNANCE §3.1 same pattern as owner-key rotation) is the response.
- Birth-attestation signature anchors the substrate-ID to the Cultivator's signing key. A collision-substrate without a Cultivator-attested birth fails handshake (per §3.1 step 6 — substrate-emitted owner_birth_attestation_signature must verify against anchor-surface-fetched owner pubkey).

**Why this defends**: substrate-ID alone is insufficient identity; the birth-attestation signature is the verifying anchor. Collision attacks must compromise both the substrate-ID hash AND the Cultivator's signing key.

**Cross-ref**: federation peer-trust freshness (L1_GOVERNANCE §5.2) does NOT trust substrate-ID alone — it requires Cultivator attestation per peer. Collision substrates would require fresh Cultivator attestation, which is §10.A.3 impersonation territory.

### §13.6 Backup-attack (privacy via backup medium; Phase γ.3 G16)

**Threat**: substrate state_dir backups (per L1_SCHEMA recoverability budget) are stored on backup media. An attacker with read access to backup media reads the full substrate state (potentially including operator deltas, sporocarp content, Cultivator-attested data) without ever compromising the substrate process.

**Defense via L1_SKIN backup encryption requirements** (per L0 §11.1 cascade):
- Backups MUST be encrypted with an operator-controlled symmetric key (L1_SKIN DRAFT 2 work). Backup encryption is not mandated at L0 (operational choice), but L0 §11.1 mandates that backup access controls are documented at L1 and that absent encryption is acknowledged as a known privacy attack surface.
- Key escrow protocol: the backup-encryption key is held by the Cultivator out-of-band (NOT in the substrate's state_dir). Restoring a backup requires Cultivator-side key access.
- Key rotation aligned with Cultivator-key rotation: when the Cultivator rotates owner-key, the backup-encryption key SHOULD rotate too (L1_SKIN policy).

**Defense limits**: backups predating encryption rotation may still be readable with the old key. Backup-attack is a privacy attack, not an integrity attack — the substrate's own state remains uncorrupted, but historical content is exposed if the key leaks. Cultivator-side discipline (where backups are stored, how access is granted) is load-bearing.

### §13.7 Single-skin failure point (Phase γ.3 G19; L1_SKIN P9.b)

**Threat**: per L1_SKIN P9.b, "single skin = single point of failure." If the skin endpoint fails (network outage, process crash, certificate expiry, DDoS), the substrate cannot intake new operator-connections or emit federation events. An attacker can mount an availability attack at the skin.

**Defense via L1_SKIN §13 skin-restart discipline**:
- L1_SKIN §13 mandates skin-restart discipline: the substrate detects skin failure (transport-level errors), enters `quarantined` on persistent failure (per L1_CONTINUITY §5), emits `skin_failure` immune signal, awaits Cultivator-attested `skin_restart_attestation` to re-open.
- During quarantine, the substrate's metabolism continues (intake closed; output also restricted), so DDoS at the skin does not destroy the substrate — it suspends external operations.
- L1_SKIN §1 skin surface declaration is a CI-grade tier-1 field (per L1_HARD_RULES F11): the attacker cannot reconfigure the skin to a fake endpoint without Cultivator attestation.

**Defense limits**: extended skin-failure ages the substrate (drill scheduling, federation peer-trust freshness windows lapse). Sustained availability attacks can force the substrate into `legacy` or even mortality territory. Mitigation requires Cultivator-side infrastructure resilience (geographic redundancy, DDoS mitigation, certificate hygiene).

**Why not multi-skin**: doctrinally, P9 (skin) commits to a single declared boundary; multi-skin would multiply trust-establishment surface. Trade-off: single-skin gives sharper trust model, weaker availability. Multi-skin would give better availability at the cost of trust-model complexity. v0.9 chooses single-skin; L4 may reconsider.

---

## §14. Glossary (DRAFT 2 additions)

| Term | Definition |
|---|---|
| **Cultivator** | The human party in the Cultivation relationship (per L0 §1.2 G-11.a). Holds the governance-gate role at the anchor surface; signs CI attestations; co-signs birth/destruction; registers successors. "Owner" remains valid for the governance role; "Cultivator" emphasizes the relational role. Both refer to the same human party. |
| **Cultivar** | The Myco substrate (kernel + dag.cb + state_dir + skin endpoints) under cultivation (per L0 §1.2). The P1.c carrier identity. |
| **Cultivation** | The asymmetric-care + co-evolution relationship between Cultivator and Cultivar (per L0 §1.2). Distinct from ownership, custody, or curatorship. Mycology-rooted vocabulary. |
| **Duress attestation** | A CI attestation signed by the Cultivator's pre-registered `duress_keypair` instead of the primary owner-key, indicating the Cultivator is under coercion (per §10.A.2). |
| **Duress keypair** | A separate Ed25519 keypair the Cultivator pre-registers at genesis (per §2 + §10.A.2). The public key is persisted in the substrate identity record; the private key is held on physically separate medium. Used only when coerced. |
| **owner_signature_velocity** | A rolling-window count of Cultivator-signed CI events per L1-tunable cadence; baseline established after N steady-state events; anomalous velocity emits `owner_signature_velocity_anomaly` daily immune signal (per §10.A.3). |
| **coerced_owner_suspected** | CI-grade immune signal emitted by the substrate when a CI attestation verifies against the duress_keypair instead of the primary owner-key (per §10.A.2). Freezes destructive mutations until out-of-band re-attestation. |
| **Anchor-client provenance independence** | Per L0 §9.3.3 + §10.A.5: the anchor-surface client (Cultivator's local rendering + signing tool) MUST be installed and updated through a channel structurally independent of the substrate's distribution channel. Closed by M-anchor-1. |
| **n-of-m multisig (owner-key)** | An optional owner-key configuration where m of n registered Cultivator-keys must sign for CI attestations to verify (per §10.A.1). Recommended for institutional Cultivars; codified at L1_GOVERNANCE §3.1 DRAFT 2. |
| **Honor-system collapse window** | The v0.9 state where the operator and anchor surface are collapsed into the same process / npm workspace / host (per §11). Documented vulnerable, NOT production-ready. Closes progressively across M-anchor-1 through M-anchor-5. |
| **M-anchor-N** | Future milestone block closing one or more sub-clauses of the L0 §9.2/§9.3 anchor-surface decomposition. See §11.3 for the timeline. |
| **Sybil (federation)** | An attacker creates many federation peer substrates to dominate population-level consensus (per §13.1). Defended by Cultivator-attested peer list. |
| **Eclipse (federation)** | An attacker controls all federation peers a substrate connects to, presenting a coordinated false view (per §13.2). Defended by diverse Cultivator-attested peer selection. |
| **Recursive injection (federation)** | A malicious federation peer injects events that the receiver misinterprets as first-party identity-altering events (per §13.3). Defended by federation-safe-node-type allowlist + wrapped-events architecture. |
| **Forkbomb (reproduction loop)** | An attacker triggers unbounded reproduction (per §13.4). Defended by L0 §16 generation limits + Cultivator-attested birth gate. |

---

## §15. Cross-reference + L1 cascade obligations

This document creates new obligations on other layers that must be reflected in their DRAFT-N updates:

- **L1_HARD_RULES (cascade)**: add candidate C-row(s) for `coerced_owner_suspected` (CI-grade) and `owner_signature_velocity_anomaly` (daily-grade). Add F-row(s) if appropriate (`duress_keypair_public_key` is identity-record tier-1 field; should it be F18?).
- **L1_GOVERNANCE §3.1 (cascade)**: DRAFT 2 codification of n-of-m multisig (per §10.A.1); duress-keypair registration as genesis-optional field (per §10.A.2); quorum-emergency-rotation mechanism.
- **L1_GOVERNANCE §3.2 (cascade)**: successor FSM specification (per L0 §15.2); court-attested key recovery exceptional path; deceased-Cultivator-without-succession terminal states.
- **L1_GOVERNANCE §5 (cascade)**: federation peer diversity recommendation per §13.2; per-peer attestation chain audit hooks.
- **L1_CONTINUITY (cascade per L0 §13.2)**: NTP discipline policy per §12.1; minimum source diversity; clock-drift monitoring.
- **L1_SCHEMA (cascade per L0 §13.2)**: i64-nanoseconds canonical-bytes representation + year-2262 horizon-warning + negative-pre-1970 treatment per §12.3.
- **L1_SKIN (cascade per L0 §11.1)**: backup encryption requirements + key escrow + key rotation alignment per §13.6.
- **L2_FEDERATION (A3 update)**: federation-safe-node-type allowlist + wrapped-events architecture per §13.3 (primary spec there; threat-model framing here).
- **L2_OBSERVABILITY**: `owner_signature_velocity` sub-signal per §10.A.3 should appear in §11 owner-side observability (anchor-surface dashboard).

This list is the M26-cascade A4 obligation surface. Subsequent A-cascade documents close each row.

---

## §16. DRAFT history

- **DRAFT 1 (2026-05-13)**: initial L2_TRUST_MODEL with §1–§9 (triad, genesis, steady state, maintenance, recovery, limits, federation, invariants, open).
- **DRAFT 2 (2026-05-17, this commit)**: M26-cascade A4 update for L0 DRAFT 9 SEALED. Added §10 adversarial-Cultivator threat model (full L0 §14 cascade), §11 anchor-surface honor-system collapse window (Phase γ.5), §12 time-semantics attacks (Phase γ.3 G10), §13 federation Sybil/eclipse/recursive-injection/forkbomb/substrate_id-collision/backup-attack/single-skin-failure (Phase γ.3 G8/G11/G15/G16/G19 + L2_FEDERATION cross-ref), §14 glossary (Cultivator/Cultivar/Cultivation/duress/velocity/anchor-client provenance), §15 cross-reference cascade obligations. Cultivator/Cultivar/Cultivation vocabulary integrated throughout. Existing §1–§9 preserved with §1 + §6 + §8 + §9 updated to reference new sections.
