# L1 — Governance (classifier, lifecycle, attestation protocol, federation)

> **Status**: DRAFT 2 (2026-05-13). Authoritative L1 doc for governance mechanism.
> **Layer**: L1. Governed by L0.
> **Scope**: I2 classifier function + dimension table; lifecycle (genesis, dormancy, reproduction, mortality); attestation protocol with canonical-bytes + operator-witnesses + dual-clock + anchor-side nonces; owner-key rotation; owner-liveness-heartbeat-based succession; federation discovery + peer-trust-freshness with aggregate re-attestation; rollback for failed P3 evolution.

---

## §1. The I2 classifier function

### §1.1 Signature

```
classify(mutation_envelope) → {daily, contract_identity_level, untyped}
```

Where `mutation_envelope` carries `(touched_files, touched_fields, touched_meta_structures, mutation_type, source_event_id)`.

**`untyped`** = no classifier rule matches. Untyped mutations are rejected at the skin (I8) as breach attempts.

### §1.2 Dimension table (seed)

Classifier behavior is data-driven from a single dimension table — a tier-1 SSoT field. **The classifier function itself, and any mutation to this table, is unconditionally contract-identity-level** (L0 I2 classifier-fixed-point).

| Touched scope | Classification |
|---|---|
| L0 file | contract_identity_level |
| L1 file (any) | contract_identity_level |
| `substrate-ID` field | contract_identity_level (immutable post-genesis except via destruction) |
| Owner public-key history field | contract_identity_level |
| Anchor-surface endpoint declaration | contract_identity_level |
| Classifier dimension table itself | contract_identity_level (fixed-point) |
| Mortality-signal threshold + update-rule | contract_identity_level |
| Threshold_emergence_rule (any axis) | contract_identity_level |
| Threshold emergence in steady-state via update_rule: NON-mortality axes | daily |
| Threshold emergence in steady-state via update_rule: mortality-signal axis | contract_identity_level |
| Appetite-axis schema | contract_identity_level |
| Sporocarp-type tree | contract_identity_level |
| Skin surface declaration | contract_identity_level |
| SSoT designation | contract_identity_level |
| DAG retention policy | contract_identity_level |
| Federation peer attestation list | contract_identity_level |
| Daily content (deltas absorbed; gradient state updates non-mortality; ordinary sporocarp fruiting; federation coupling) | daily |
| All else | **untyped** (rejected) |

### §1.3 Birth-period CI elevation

During birth period (defined in §4.1), ALL parameter-tuning events are contract-identity-level regardless of steady-state classification. Reclassification to daily-autonomous happens at the birth-period → steady-state transition, which is itself owner-attested.

**Birth period has a CI-attested MAXIMUM duration** committed at genesis (L4-tunable, default 180 active-operation days). Reaching maximum forces forced-graduation-or-self-euthanasia decision (substrate fruits `birth_period_max_reached` and either auto-graduates if convergence achieved, or `self_euthanasia_proposal` if not).

---

## §2. Owner attestation protocol

### §2.1 Owner key custody

Owner's signing key MUST live outside the substrate's process boundary AND outside any process the agent can spawn or read memory of. **Specific mechanism is L4-picked** within {hardware security token, separate machine, cloud HSM, signed-prompt review on isolated channel}. The L1 constraint: the owner's private key never enters the substrate process's address space; substrate sees only signatures.

### §2.2 Attestation envelope schema

CI-level mutation flow:

1. **Substrate requests anchor-surface nonce**: substrate sends `nonce_request {substrate_id, proposed_mutation_hash, dag_tip_hash, request_timestamp_substrate_cycles}` to anchor surface. Anchor surface issues a **single-use nonce bound at issuance to the declared mutation_hash + dag_tip_hash** (closes pass-3 mycoparasite-5: nonces cannot be hoarded for later mutations; each is tied to its declared content). Nonce TTL is L1-tunable (default 5 anchor-surface-trusted-timestamp minutes). Anchor surface rate-limits nonce issuance per substrate; spike triggers `attestation_request_saturation` owner-side observable.

2. **Substrate emits attestation request envelope** with the issued nonce:

```
{
  "type": "contract_identity_attestation_request",
  "substrate_id": <owner-signed at genesis>,
  "dag_tip_hash": <current Merkle DAG tip>,
  "enumerated_dag_nodes_since_last_co_sign": [<hash>, <hash>, ...],
  "proposed_mutation_canonical_bytes": <canonical serialization of mutation>,
  "proposed_mutation_hash": <hash over canonical_bytes>,
  "operator_witness": <signature over proposed_mutation_canonical_bytes using operator_signing_key_private from L1_SKIN §4.1>,
  "operator_signing_key_public": <from current handshake>,
  "request_timestamp_substrate_cycles": <substrate metabolic-cycle counter>,
  "anchor_surface_nonce": <bound by anchor surface at step 1>,
  "expiry_constraints": {"cycles_max": <L1-tunable>, "wall_clock_seconds_max": <L1-tunable>}
}
```

Note: DRAFT 7's `operator_witness_hash` + `operator_acknowledgment` fields are **collapsed to a single `operator_witness` signature** (per pass-3 astronaut-1 — the seen-vs-signed distinction is speculative); the new field uses the operator-side per-handshake signing key (per pass-3 mycorrhiza-17 + rhizomorph-1 — operator_token was substrate-known and could not provide carrier-distinctness).

3. **Owner verifies independently at the anchor surface**:
   1. Render `proposed_mutation_canonical_bytes` via the anchor-surface client (provenance-independent per L0 §9.3).
   2. Re-compute `proposed_mutation_hash` from canonical bytes.
   3. Verify `operator_witness` signature against `operator_signing_key_public` (from substrate's handshake_complete envelope, but cross-checked via anchor-surface record of that handshake's logged event).
   4. **DAG enumeration closure check**: reconstruct Merkle chain from prior co-signed tip via `enumerated_dag_nodes_since_last_co_sign`; confirm `dag_tip_hash` is reachable AND every parent-hash referenced by any enumerated node resolves to either an ancestor of the prior co-signed tip OR another enumerated node (closes pass-3 mycoparasite-2 hidden-parallel-branch attack).
   5. Verify the anchor-surface nonce matches the issuance-bound mutation_hash + dag_tip_hash + within TTL.
   6. Anchor surface attaches trusted wall-clock timestamp; appends to signed tuple.
   7. Owner signs the tuple `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`.

### §2.3 Verification on receipt

The substrate, on receipt of an owner signature:

1. Recomputes the signed tuple from current substrate state + the proposed mutation + the anchor-surface fields.
2. Verifies signature against the owner's public key (active at the anchor-surface timestamp per §3 owner-key-history).
3. Verifies **both** time-bound constraints: substrate-cycle expiry AND anchor-surface wall-clock expiry — whichever expires first invalidates the attestation. The substrate cannot extend wall-clock budget by throttling cycles.
4. Verifies the anchor-surface nonce has not been previously consumed (anchor-surface maintains the consumed-nonce log; substrate-side replay protection is non-authoritative).
5. If all valid: mutation commits.
6. If any fail: emit `attestation_invalid` immune event (elevated grade); reject mutation.

### §2.4 What the substrate does NOT control

- Nonce generation (anchor-surface owns).
- Trusted timestamp (anchor-surface owns).
- Consumed-nonce log (anchor-surface owns).
- Canonical-bytes ↔ rendered-form mapping (anchor-surface client owns rendering).

Substrate emits canonical bytes; substrate does not narrate.

---

## §3. Owner key rotation, suite migration, and succession

### §3.1 Owner key rotation (in-life rotation, same owner)

The substrate's identity record carries `owner_key_history` — a chronological list `[(public_key_n, valid_from_anchor_timestamp, valid_until_anchor_timestamp, rotation_attestation_signed_by_prior_and_new_keys, cooldown_expired_at)]`.

**Rotation requires a cooldown window** (closes pass-3 mycoparasite-7: dual-sign alone is insufficient when both keys come from the same attacker). Rotation protocol:

1. Current owner publishes new candidate pubkey at the anchor surface, signed by current key.
2. **Cooldown window** (L1-tunable, default 30 anchor-surface-trusted-timestamp days) begins. During the cooldown, ANY pre-registered owner key (current, prior, or registered backup-key) may issue a `rotation_veto` at the anchor surface. Veto cancels the rotation.
3. After cooldown without veto, the new key is co-signed by both current and new keys; substrate accepts and updates owner_key_history.

Verification of any historical co-sign uses the key valid at the co-sign's anchor-surface timestamp. Cryptographic suite rotation follows the same pattern (history carries `(suite, public_key)` tuples).

**Active-prefix + archived-tail discipline** (closes pass-3 saprotroph-1: monotone tier-1 fields grow unbounded → per-cycle cost grows): `owner_key_history` is stored as `active_prefix` (most-recent K entries, K L4-tunable default 8) + `archived_tail` (older entries). Active prefix participates in per-cycle I3 tier-1 validation; archived tail validated at deep-cycle scope via Merkle-anchor over the full chain. Same discipline applies to `template_version_registry` (L1_TROPISM §B1) and to the federation peer-set aggregate-reattestation chain (§5.2).

### §3.2 Owner succession (different owner, same substrate)

Owner-succession protocol is **deferred to L4** as a concrete operational protocol, after first real-world need. The L1 minimum:

- The owner MAY record `(successor_public_key, succession_trigger_condition)` tuples at the anchor surface during their lifetime.
- Succession activation requires the successor signing a `successor_activation` envelope; the substrate validates against the anchor-surface successor record (NOT against a substrate-side cache).
- Succession trigger uses **positive owner-liveness-heartbeat staleness** at the anchor surface — not substrate-side absence-of-CI-emission. Owner periodically signs `liveness_heartbeat` events at the anchor surface; succession trigger fires only when the heartbeat has been stale at the anchor surface for ≥ L1-tunable window. Substrate cannot manufacture trigger.

The full FSM (grace periods, legacy sub-state details, trust-chain re-anchoring) is L4-codified after the FIRST real-world owner-succession surfaces concrete requirements. Pre-empting it here would be speculation.

---

## §4. Lifecycle operations

### §4.1 Genesis

The only routine human-initiated event in the substrate's lifecycle.

**Protocol**:

1. Owner generates owner-keypair + selects an anchor-surface endpoint mechanism.
2. Owner runs `genesis` invocation with explicit parameters: `(initial-spore-schema, initial-dispatch-config, initial-classifier-dimension-table, anchor_surface_endpoint_public_key, owner_public_key, signature_suite)`. The `anchor_surface_endpoint_public_key` is owner-controlled; the substrate cannot self-discover it.
3. The substrate emits **canonical bytes** of the spore-schema; owner client renders deterministically; owner reviews the render.
4. The substrate computes `substrate-ID = hash(initial-spore-schema-canonical-bytes, owner-public-key, anchor-surface-endpoint-public-key, genesis-timestamp)`.
5. Owner signs **the canonical bytes hash + the substrate-ID tuple** at the anchor surface — the birth attestation.
6. Substrate persists identity record (substrate-ID, owner-key-history with first entry, anchor-surface-endpoint-public-key, signature-suite, birth-attestation-reference) + DAG root sporocarp.

Multi-owner co-genesis is deferred to L4.

### §4.2 Dormancy

Per L0 §6 + L1_CONTINUITY §2. This doc adds:

- Owner-commanded dormancy via CI event (rare; for substrate hibernation).
- `operator_dormancy_request` — operator's `handshake_terminate` envelope may include `request_dormancy: paused | throttled` field; substrate honors the operator's preference unless overridden by resource pressure.

### §4.3 Reproduction closure (operationalizes I7)

**Child substrate-ID minting**: parent proposes spore-schema canonical bytes; the **owner** (or owner's anchor-surface tooling) computes `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)`. Parent cannot mint. Owner signs the child's birth attestation at the anchor surface.

**Closure verification protocol** (operationalizes I7): see L1_SCHEMA §3.3 for spore-schema validation steps. Owner co-signs the spawn at the anchor surface — `(parent-substrate-ID, child-substrate-ID, spore-schema-canonical-bytes-hash, anchor-surface-timestamp)`.

**Parent's outstanding immune-signal summary** is included in the spore-schema (per L0 P8). Child whose parent had unresolved CI-grade immune signals enters birth in `quarantined` until owner re-attests intent.

### §4.4 Mortality (dual-channel)

Three destruction modes per L0 P7:

**Intentional-owner**: owner emits CI-level `destruction_attestation` sporocarp signed by owner. Substrate transitions alive → destroyed. **Final action before terminating**: substrate emits `anchor_surface_final_seal` co-signed by owner at the anchor surface — an explicit terminal record stating "this substrate-ID is destroyed at anchor-surface-timestamp T" (closes pass-3 rhizomorph-2). Post-seal owner activity at the anchor surface remains valid for OTHER substrates / federated peers but cannot wake or revive this substrate-ID; any handshake attempt against a sealed substrate-ID returns `substrate_destroyed` at the anchor surface (substrate process is gone; anchor surface holds the terminal record).

**Catastrophic-environment**: substrate medium failure beyond L1_SCHEMA recoverability budget. Detected post-hoc via recovery drill failure.

**Endogenous-pair** (with operator witness, dual channel):
- **Substrate channel**: substrate fruits `self_euthanasia_proposal` when its own metabolism crosses unrecoverable-pathology threshold. **The active operator-connection at proposal time must produce an `operator_witness_hash`** before the proposal transmits to anchor surface. If no operator is connected, substrate enters `pre-mortal-pending` and waits for operator handshake before transmitting.
- **Anchor-surface channel**: two consecutive failed recovery drills at the anchor surface auto-emit an owner-side `mortality_drill_failure` event. The substrate cannot suppress this — it lives at anchor surface.

Either channel can trigger the destruction proposal; owner co-attestation is required to execute (substrate cannot self-destroy without owner sign-off; anchor-surface-side trigger cannot bypass owner co-sign).

**Mortality-signal protection**: per §1.2, mortality-signal threshold + update-rule + emergence-rule for mortality axis are all CI-level.

---

## §5. Federation discovery and peer-trust freshness

### §5.1 Discovery modes

L4 picks from: peer-to-peer broadcast / owner-attested peer list / hub-and-spoke registry / hybrid. Default: owner-attested peer list (strongest isolation).

### §5.2 Peer-trust freshness with aggregate re-attestation

Each peer's attestation has an L1-bounded freshness window (default 90 active-operation days). Past freshness → `peer_attestation_stale` immune event; events queued pending re-attestation. Past additional grace (default 30 days) → `untrusted_federation`; events rejected.

**Aggregate re-attestation**: to avoid O(N) owner workload per period, owner MAY issue a single `federation_peer_set_reattestation` event signing the current peer-set Merkle-root hash + diff against last commitment. The anchor surface displays the diff (peers added/removed since last aggregate-reattestation); owner reviews the diff, not the full set. Aggregate re-attestation is structurally equivalent to N pairwise re-attestations; owner cost is O(1) per period.

**Revocation list**: anchor surface maintains a peer-revocation list. Successor activations and federation events must include an anchor-surface negative-revocation proof (fresh attestation that target has not been revoked).

### §5.3 Federation egress runtime check

Per L1_SKIN §3.1: every outbound federation envelope verifies the target peer's freshness + non-revocation BEFORE emission. Stale/revoked → suppression + `federation_egress_blocked` immune event.

**Egress rate-limiting**: anchor surface tracks federation egress volume per peer per day. Spike beyond L1-tunable triggers `federation_egress_saturation` immune event. Federation event content uses canonical low-entropy serialization (sorted keys, normalized whitespace, fixed-precision numerics) to limit covert-channel bandwidth.

### §5.4 Cross-substrate trust transitivity

Federation is NOT transitive. Each pairwise trust requires owner attestation.

---

## §6. Failed P3 evolution rollback

### §6.1 Failure detection

P3 evolution fires; substrate runs I3 self-validation in next cycle. If I3 fails → emit `evolution_failed` sporocarp (CI-elevated, ungated — failure is automatic). Substrate enters rollback procedure.

### §6.2 Rollback procedure

1. Identify pre-evolution DAG-tip from predecessor of evolution event.
2. Restore SSoT designation + classifier table + affected canon to pre-evolution snapshot (retained per I4).
3. Pending sporocarps fruited within rolled-back window are dropped, recorded as `evolution_failed_pending_dropped`. Pre-window pending sporocarps survive.
4. Emit `rollback_complete`.

Repeated failures across a 30-day window appear in observatory as `evolution_failure_rate_elevated`; owner reviews. No separate `evolution_quarantine` sub-state (handled via standard quarantine entry under L1_CONTINUITY §5).

---

## §7. Open at L1, deferred to L4

- Owner key custody specific mechanism.
- Idle timeout for alive → dormant (default 100 cycles).
- Federation discovery mode (default owner-attested peer list).
- Federation peer-trust freshness window (default 90 days active op).
- Federation egress rate-limit ceilings.
- Anchor-surface endpoint specific protocol (hardware token / separate machine / cloud HSM / signed prompt review).
- Canonical-bytes serialization format (sorted-keys YAML / canonical-JSON / custom).
- Liveness heartbeat cadence (default monthly).
- Birth period maximum duration (default 180 days).
- Full owner-succession FSM (deferred until first real-world need).
- Cryptographic suite candidates within {SHA-256, BLAKE3, SHA-3-256, Ed25519, post-quantum candidates}.

Shape is committed; values are L4.
