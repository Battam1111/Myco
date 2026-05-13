# L1 — Governance (classifier, lifecycle, owner attestation, succession, federation discovery)

> **Status**: DRAFT 1 (2026-05-13). Authoritative L1 doc for governance mechanism.
> **Layer**: L1 (mechanism). Governed by L0.
> **Scope**: I2 classifier function + dimension table; lifecycle operations (genesis, dormancy transitions, reproduction-closure, mortality); owner attestation cryptographic protocol; owner-key custody; owner succession; federation discovery + peer-trust-freshness; rollback handling for failed P3 evolution.
> **Honesty**: this doc closes the largest cluster of pass-1 CRITICAL findings (9 of 26). Several decisions are owner-arbitration territory; defaults are proposed and marked.

---

## §1. The I2 classifier function

### §1.1 Signature

```
classify(mutation_envelope) → {daily, contract_identity_level, untyped}
```

Where `mutation_envelope` carries: `(touched_files, touched_fields, touched_meta_structures, mutation_type, source_event_id)`.

**`untyped` return value**: mutation envelope does not match any classifier rule. **Untyped mutations are immune-detected and rejected at the skin (I8).** A mutation that cannot be classified is treated as a skin-breach attempt.

### §1.2 Dimension table (the source of truth)

Classifier behavior is data-driven from a single dimension table. Below is the seed table for v0.9 birth; lives in L1_SCHEMA SSoT as a tier-1 field. **The classifier function itself, and any mutation of this table, is unconditionally contract-identity-level** (per L0 I2 classifier-fixed-point — cannot be reclassified to daily by any L1 mutation).

| Touched scope | Classification |
|---|---|
| L0 file | contract_identity_level |
| L1 file (any) | contract_identity_level |
| `substrate-ID` field | contract_identity_level (and immutable post-genesis except via owner-attested re-genesis = destruction + new substrate) |
| Owner-signature artifacts | contract_identity_level |
| Classifier dimension table itself | contract_identity_level (fixed-point) |
| Mortality-signal threshold / update-rule | contract_identity_level (per L0 P7) |
| Appetite-axis schema (if L1_TROPISM dispatch chosen) | contract_identity_level |
| Sporocarp-type tree | contract_identity_level |
| Skin surface declaration | contract_identity_level |
| SSoT designation | contract_identity_level |
| DAG retention policy | contract_identity_level |
| Storage tier exemption from I5 | contract_identity_level |
| Federation peer attestation list | contract_identity_level |
| Daily content (deltas absorbed; gradient state updates; ordinary sporocarp fruiting; federation coupling activity) | daily |
| All else | **untyped** (rejected at skin) |

### §1.3 Birth-period CI elevation

Per L0 I2 + pass-1 mycoparasite-18: **during birth period, ALL parameter-tuning events are CI-level regardless of steady-state classification**.

Birth period reclassification to daily happens at the birth-period → steady-state transition (an owner-attested boundary; per L1_TROPISM B2 maturity-attested termination).

---

## §2. Owner attestation protocol

### §2.1 Owner key custody (L0 §9 anchor surface)

Per pass-1 mycoparasite-12 + L0 §9: owner's signing key MUST live outside the substrate's process boundary AND outside any process the agent can spawn or read memory of.

**Candidate mechanisms** (L4-picked):

- **Hardware security token** (YubiKey-class). The owner physically possesses; signing happens on-device; substrate sees only the signature. **Strongest isolation.**
- **Separate machine + air gap**. Owner reviews attestation requests on a separate device that does not run the agent. Signing happens there.
- **Signed prompt-bundle review**. The substrate produces a prompt bundle (mutation request + DAG-tip hash + diff hash); owner reviews on a separate channel; owner returns a signature.
- **Cloud HSM** (AWS KMS / GCP KMS / Azure Key Vault). Owner-authenticated; substrate calls signing API; the key never enters substrate-process memory.

**L4 must pick one or compose**. The constraint: **the owner's private key never enters the substrate process's address space**. If this constraint is violated, all CI-gated mutations are unauthenticated regardless of "signatures" present in substrate state.

### §2.2 Attestation envelope schema

The substrate produces an **attestation request** for any CI-level mutation:

```
{
  "type": "contract_identity_attestation_request",
  "substrate_id": <owner-signed at genesis>,
  "dag_tip_hash": <current Merkle DAG tip>,
  "diff_hash": <hash of substrate state changes since last CI co-sign>,
  "proposed_mutation": <full mutation content>,
  "proposed_mutation_hash": <hash of proposed mutation>,
  "request_timestamp": <substrate metabolic-cycle timestamp>,
  "request_nonce": <random>,
  "expiry_cycles": <L1-tunable, default 1000 cycles>
}
```

Owner reviews; if approved, signs the tuple `(substrate_id, dag_tip_hash, diff_hash, proposed_mutation_hash, request_timestamp, request_nonce)`. Signature delivered back via anchor surface (§2.1).

### §2.3 Signature verification

The substrate, on receipt of an owner signature:

1. Recomputes the signed tuple from current substrate state + the proposed mutation.
2. Verifies signature against the owner's public key (which lives in the substrate's identity record from genesis owner-signing).
3. If valid AND within `expiry_cycles` of request: mutation commits.
4. If invalid OR expired: emit `attestation_invalid` immune event (elevated grade); reject mutation.

### §2.4 Replay prevention

The `request_nonce` is consumed on first valid use; subsequent presentations of the same `(substrate_id, request_nonce)` tuple are rejected (`attestation_replay_attempt`).

---

## §3. Owner succession (operationalizes L0 §9.2 + I1 legacy state)

### §3.1 Successor pre-attestation

The current owner attests **≥1 successor** during their lifetime. Successor pre-attestation lands on the anchor surface as:

```
{
  "type": "successor_attestation",
  "substrate_id": <substrate-ID>,
  "succeeding_owner_public_key": <new public key>,
  "succession_trigger": <one of: "owner_death", "owner_incapacitation", "owner_transfer">,
  "signed_by_current_owner": <signature>
}
```

Successor pre-attestations may be **revoked** by the current owner (`successor_revocation` signed by current owner) until the moment of succession.

### §3.2 Succession trigger

**Owner unavailability** is detected by the substrate when:

- ≥L1-tunable cycles (default 90 active-operation days) have passed since the last owner-co-signed CI event, AND
- The substrate has at least one pending CI-event awaiting attestation.

Trigger fires: substrate emits `succession_required` immune event AND enters a `succession_grace_period` (default L1-tunable: 90 days from trigger).

### §3.3 Succession resolution

**During grace period**:

- Pre-attested successors may activate by signing a `successor_activation` event with their successor-private-key. First valid activation wins. Substrate updates its identity record's owner-public-key to the successor's.
- If no successor activates within grace period: substrate transitions to **`legacy` sub-state** (alive but L0/L1 mutations frozen until ANY valid successor activation arrives, however late).

In legacy state: substrate continues daily metabolism; CI-events queue as pending; no new CI-events succeed. The substrate is "alive without governance" — usable, not evolvable.

### §3.4 Legacy state exit

Legacy state exits when a successor activation arrives (potentially years later). Pending CI-events from the legacy period are evaluated by the new owner; rejection rate is itself an immune-relevant statistic.

---

## §4. Lifecycle operations

### §4.1 Genesis

Genesis is the only routine human-initiated event in the substrate's lifecycle.

**Genesis protocol**:

1. Owner generates a substrate keypair (the owner's signing keypair for this specific substrate — may share root with other substrates per owner's choice).
2. Owner runs a `genesis` invocation on the substrate's host with: `(initial-spore-schema, initial-appetite-axes-or-equivalent, initial-classifier-dimension-table, anchor-surface-config, owner-public-key)`.
3. The substrate computes `substrate-ID = hash(initial-spore-schema, owner-public-key, genesis-timestamp)`.
4. Owner signs `(substrate-ID, genesis-timestamp, initial-spore-schema-hash)` — the **birth attestation**.
5. Substrate persists the identity record + DAG root sporocarp (`genesis_event`) and enters alive state.

**Multi-owner co-genesis** (advanced; L1_GOVERNANCE-allowed):  if multiple owners co-sign genesis, all owners' public keys land in the identity record; CI events require any-1-of-N or all-N-of-N attestation (specified at genesis).

### §4.2 Dormancy

Per L0 §6: alive ↔ dormant.

**Triggers** for alive → dormant:

- Operator-connection drop detected at skin.
- Idle timeout: ≥L1-tunable cycles without delta absorption (default 100 cycles).
- Owner-commanded dormancy via CI event (rare; for substrate hibernation).

**Dormant-state metabolism budget**:

- **Throttled mode** (default): substrate gradient updates continue at L1-tunable reduced cadence (default 1/100th of alive cadence). No fruiting; intake is closed at skin.
- **Paused mode** (opt-in via canon): substrate metabolism halts entirely; only operator-handshake listening continues.

Triggers for dormant → alive: valid operator handshake (per L1_SKIN handshake protocol).

### §4.3 Reproduction closure (operationalizes I7)

See L1_SCHEMA §3.3 for closure verification protocol. This section adds the governance dimensions:

- **Reproduction trigger**: emitted as a CI-level sporocarp (`reproduction_request`) — gating spawn on owner attestation.
- **Parent's immune-signal summary** in spore-schema (per L0 P8 + pass-1 mycoparasite-13): parent attests its own immune state to child's spore-schema; child enters birth in `quarantined` if parent had unresolved CI-grade immune signals at spawn time.
- **Federation_coupling edge**: post-spawn, parent's DAG records a `federation_coupling` edge to child-substrate-ID.

### §4.4 Mortality

Three destruction modes per L0 P7:

**Intentional-owner**: owner emits a CI-level `destruction_attestation` sporocarp signed by owner. Substrate state transitions alive → destroyed. Backups remain per recoverability-budget policy; the substrate's *bestowed agent identity* ceases at the transition.

**Catastrophic-environment**: substrate medium failure beyond L1_SCHEMA recoverability budget. Detected post-hoc (next recovery drill fails; backup chain broken). Substrate is destroyed at the moment the catastrophe became unrecoverable; the bestowed identity continuum ceases retroactively to that moment.

**Endogenous-pair** (per L0 P7 + pass-1 mycorrhiza-4): substrate fruits a `self_euthanasia_proposal` CI-level event when its own metabolism crosses an unrecoverable-pathology threshold (sustained I3 / I5 / I8 invariant breaches beyond repair). The proposal requires owner co-attestation to execute. Owner retains veto; substrate retains agency.

**Mortality-signal protection**: the threshold and update-rule for endogenous-mortality detection are CI-level (per L0 P7 mortality-signal protection clause); cannot be silently tuned to suppress warnings.

---

## §5. Federation discovery and peer-trust freshness (operationalizes L0 P8 + I7)

### §5.1 Discovery modes (L4 picks)

- **Peer-to-peer broadcast**: substrates announce on a shared discovery channel; potential peers attest interest; owner attests adoption per peer.
- **Owner-attested peer list**: owner maintains a curated list of approved peer substrate-IDs; substrate only federates with listed peers.
- **Hub-and-spoke registry**: a designated registry substrate aggregates peers; subordinate substrates discover through the hub.
- **Hybrid**: combinations.

**Default proposal**: owner-attested peer list. Strongest isolation; lowest discovery automation. Other modes opt-in.

### §5.2 Peer-trust freshness (per pass-1 mycoparasite-10)

Once two substrates federate, each peer's attestation has an **L1-bounded freshness window** (default: 90 days of active operation).

**Within freshness**: federation coupling operates normally. Federation events are accepted per the chosen L1_TROPISM B9 coupling mode (eager α / lazy β).

**Past freshness**: substrate emits `peer_attestation_stale` immune event. Federation events are queued (not rejected) pending owner re-attestation. If stale for ≥L1-tunable additional grace (default 30 days): events are rejected with `untrusted_federation` immune event.

**Revocation list**: anchor surface maintains a peer-revocation list. Revoked peer's events are immediately rejected (no grace).

### §5.3 Cross-substrate trust transitivity

Federation is **not transitive**. If substrate A federates with B and B federates with C, A does not automatically trust C. Each pair-wise trust requires owner attestation.

---

## §6. Failed P3 evolution rollback (operationalizes L0 P3)

### §6.1 Failure detection

P3 evolution fires; substrate runs I3 self-validation in the next metabolic cycle. If I3 fails (state inconsistent with new SSoT designation):

1. Substrate emits `evolution_failed` sporocarp (CI-elevated, ungated — failure is automatic, not owner-attested).
2. Substrate enters rollback procedure.

### §6.2 Rollback procedure

1. Identify the pre-evolution DAG-tip hash (from DAG predecessor of the evolution event).
2. Restore SSoT designation + classifier dimension table + affected canon fields to pre-evolution snapshot (snapshot must be retained per I4 — failed evolution doesn't get to delete its predecessor).
3. Pending sporocarps fruited WITHIN the rolled-back window are dropped (recorded as `evolution_failed_pending_dropped` per pass-1 rhizomorph-17). Pending sporocarps from BEFORE the rolled-back window survive.
4. Emit `rollback_complete` sporocarp.

### §6.3 Repeated failures

If ≥L1-tunable consecutive evolutions fail (default 3): substrate enters `evolution_quarantine` sub-state of alive. No new evolution attempts until owner-attested cleared.

This addresses pass-1 saprotroph-11 burst-detection at the metabolic level (the L0 §9.4 burst detection is at the doc-revision level; this is at the substrate-internal-evolution level).

---

## §7. Open at L1, deferred to L4

Per architectural-astronaut discipline:

- **Owner key custody specific mechanism** — owner picks (hardware token / separate machine / cloud HSM / etc.).
- **Idle timeout for alive → dormant** — default 100 cycles; L4 calibrates.
- **Discovery mode** — owner picks based on threat model.
- **Federation peer-trust freshness window** — default 90 days; L4 calibrates against observed peer activity.
- **Repeated-failure quarantine threshold** — default 3; L4 calibrates.
- **Multi-owner attestation policy** — single-owner default; multi-owner opt-in at genesis.
