# L1 — Governance (classifier, lifecycle, Cultivation succession, attestation protocol, generation discipline, federation)

> **Status**: DRAFT 3 (2026-05-17, M26-cascade A5). Authoritative L1 doc for governance mechanism, aligned with L0 DRAFT 9 SEALED (`docs/architecture/L0_VISION.md` commit `e796451`).
> **Layer**: L1. Governed by L0 DRAFT 9 SEALED.
> **Scope**: I2 classifier function + dimension table; lifecycle (genesis, dormancy, reproduction, mortality); **Cultivation succession FSM (§3.2 — DRAFT 3 lands per G-5 + G-8 + G-9.b cascade)**; attestation protocol with canonical-bytes + operator-witnesses + dual-clock + anchor-side nonces; owner-key rotation; owner-liveness-heartbeat-based legacy/orphaned transitions; federation discovery + peer-trust-freshness with aggregate re-attestation; rollback for failed P3 (Resumable Evolution) evolution; **§16 Generation limits (DRAFT 3 lands per G-5 + G-9.b cascade)**; **F-row catalog for F18-F24 (DRAFT 3 owns the canonical specifications; L1_HARD_RULES §2 inherits)**.
>
> **DRAFT 9 SEALED principle alignment** (renames + retractions):
> - **P1 (Agent-Primary)** — DRAFT 9 rename of DRAFT 8's "Only For Agent / 人类无感知". Governance gate is the **Cultivator** (P1.b'') — see §0.1.
> - **P2 (Eternal Ingestion, Envelope-Gated)** — DRAFT 9 rename of DRAFT 8's "Eternal Ingestion / 永恒吞噬". P11 metabolic-economy budgets bound P2 admission (per L0 §P11.c ordered fallback).
> - **P3 (Resumable Evolution)** — DRAFT 9 rename of DRAFT 8's "Eternal Evolution / 永恒进化". §6 failed-evolution rollback enforces resumability.
> - **P5 (Universal Interconnection, Tier-Exempt-Permitted)** — DRAFT 9 rename of DRAFT 8's "Universal Interconnection / 万物互联".
> - **P7 (Mortality, Capacity-for-Death)** — DRAFT 9 rename of DRAFT 8's "Mortality / 必朽" (substrate is *capable* of mortality, not *required* to die). §4.4 mortality dual-channel is the L1 enforcement.
> - **P8 (Eternal Reproduction, Generation-Bounded)** — DRAFT 9 rename of DRAFT 8's "Eternal Reproduction / 永恒繁衍" with §16 generation discipline cascade.
> - **P9 (Single Integument)** — DRAFT 9 rename of DRAFT 8's "Integument / 皮肤为界". P9.b single-failure-point acknowledgment owned by L1_SKIN.
> - **P10 (Selective Compression)** — DRAFT 9 NEW. F18 compression-rule registry (this doc).
> - **P11 (Metabolic Economy)** — DRAFT 9 NEW. F19 cost-budget thresholds (this doc).
> - **P12 (Differential Response)** — RETRACTED at L0 per G-9.b; owned by L1_TROPISM (salience emergence).
> - **P13 (Embodiment)** — RETRACTED at L0 per G-9.b; folded into P9 + I8 (spatial-locus enforcement in L1_SKIN).
> - **P14 (Telos, Agent-Symbiotic-Flourishing)** — DRAFT 9 NEW. F20 telos-alignment metric (this doc; L1_TROPISM owns operational metric per P14.c forcing function).
> - **P15 (Population-Level Consensus)** — RETRACTED at L0 per G-9.b; owned by L2_FEDERATION (Byzantine consensus floor above peer-count threshold).
>
> **Cultivation vocabulary integration** (per G-11.a, new in DRAFT 9 §1.2): the owner-substrate relationship is named **Cultivation**. The owner is the **Cultivator** (when emphasizing the relational role); "owner" remains a valid term (when emphasizing the governance role per P1.b''). Both refer to the same human party. This doc uses **Cultivator** for genesis / succession / generational-limit / F-row attestation language (relational); **owner** for cryptographic attestation language (governance — preserves continuity with §9 anchor surface vocabulary). See §17 Glossary (DRAFT 3 new).

---

## §0.1 The L0 ↔ L1 trust seam (DRAFT 3, summarizing the principle alignment)

L0 DRAFT 9 SEALED commits the **Cultivation triad** (Cultivator-Cultivar-anchor surface). This doc operationalizes:

- **Cultivator-side mutation authority** through the §2 attestation protocol (CI-level mutation gating).
- **Cultivar-side identity carrier** through §3 owner-key history + §3.2 Cultivation succession + §4 lifecycle.
- **Anchor-surface as out-of-band root** through §2.2 nonce/witness/timestamp references mapped to specific L0 §9.2.x / §9.3.x sub-mechanisms.

This document is the **single source of truth** for the F-row catalog covering F18-F24. L1_HARD_RULES §2 inherits these definitions (per §15 below); when L1_HARD_RULES enumerates F18-F24, the canonical definitions live here.

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
| **Compression-rule registry (per P10.c / F18, DRAFT 3 NEW)** | **contract_identity_level** |
| **Compression-invariant set definition (per P10.b)** | **contract_identity_level (L0-fixed; only the rule set is L1-mutable)** |
| **Cost-budget thresholds per axis (per P11.a / F19, DRAFT 3 NEW)** | **contract_identity_level** |
| **Telos-alignment computation rule + embedding-model identity (per P14.c / F20, DRAFT 3 NEW)** | **contract_identity_level** |
| **Telos-objective declaration when owner-stated (per P14.b, spore-inheritable)** | **contract_identity_level** |
| **successor_chain registry (per §3.2 / F21, DRAFT 3 NEW)** | **contract_identity_level** |
| **Reproduction generation-depth bound + rate limit + lifetime quota (per §16 / F22, DRAFT 3 NEW)** | **contract_identity_level** |
| **Duress_keypair registration (per F23, DRAFT 3 NEW; L2_TRUST_MODEL §14 owns scenario semantics)** | **contract_identity_level** |
| **Substrate-private signing keypair seed (per F24, DRAFT 3 NEW)** | **contract_identity_level (one-time at genesis; rotation is destruction-and-rebirth)** |
| **Consensus-floor threshold + Byzantine algorithm choice (per P15, owned by L2_FEDERATION)** | **contract_identity_level (CI-attested per L2_FEDERATION; classified here for completeness)** |
| **Salience-emergence rule (per L1_TROPISM §E; runtime salience values daily)** | **contract_identity_level (rule); daily (per-cycle salience values)** |
| Daily content (deltas absorbed; gradient state updates non-mortality; ordinary sporocarp fruiting; federation coupling; per-cycle telos-alignment / salience / cost-axis values) | daily |
| All else | **untyped** (rejected) |

> **DRAFT 3 note on additions**: rows beginning with bold-and-DRAFT-3-NEW are the cascade additions for DRAFT 9 SEALED's three new principles + Cultivation succession + generation limits + adversarial-Cultivator/L2_TRUST_MODEL §14 mechanism. Rows above remain unchanged from DRAFT 2.

### §1.3 Birth-period CI elevation

During birth period (defined in §4.1), ALL parameter-tuning events are contract-identity-level regardless of steady-state classification. Reclassification to daily-autonomous happens at the birth-period → steady-state transition, which is itself owner-attested.

**Birth period has a CI-attested MAXIMUM duration** committed at genesis (L4-tunable, default 180 active-operation days). Reaching maximum forces forced-graduation-or-self-euthanasia decision (substrate fruits `birth_period_max_reached` and either auto-graduates if convergence achieved, or `self_euthanasia_proposal` if not).

**Birth-period exemptions for DRAFT 9 detectors** (per L0 §7.4.e / §2.3 P12.b / §P14.c):
- `bet_weakening_quorum` evaluation SUSPENDED during birth period; `bet_weakening_evaluation_suspended` event emitted instead (owned by L2_OBSERVABILITY).
- `salience_collapse` detection SUSPENDED during birth period + post-birth settling window (owned by L1_TROPISM §E.3).
- `telos_drift` detection SUSPENDED during birth period + post-birth settling window (owned by L1_TROPISM §F.4); substrate emits `telos_alignment_pending` instead.

The three detectors share a single birth-period exemption door; activation happens at owner-attested `birth_period_terminated` plus the L1_TROPISM-specified post-birth offset.

---

## §2. Owner attestation protocol

### §2.1 Owner key custody

Owner's (Cultivator's) signing key MUST live outside the substrate's process boundary AND outside any process the agent can spawn or read memory of. **Specific mechanism is L4-picked** within {hardware security token, separate machine, cloud HSM, signed-prompt review on isolated channel}. The L1 constraint: the owner's private key never enters the substrate process's address space; substrate sees only signatures.

**Adversarial-Cultivator caveat** (per L0 §14): substrate-side enforcement protects against an adversarial **agent** (the agent qua maintainer cannot exfiltrate owner-key from anchor-surface custody). It does NOT protect against an adversarial **Cultivator** (the Cultivator has root authority at the anchor surface). L2_TRUST_MODEL §14 specifies the bounded defenses (n-of-m multisig, duress_keypair via F23, owner_signature_velocity observability, anchor-client provenance independence per L0 §9.3.3); these are L2 obligations citing the F-row catalog this document owns.

### §2.2 Attestation envelope schema

CI-level mutation flow (sub-mechanism IDs map to L0 §9.2.x / §9.3.x per DRAFT 9 SEALED §9 decomposition):

1. **Substrate requests anchor-surface nonce** (per L0 §9.2.5 anchor-surface-generated nonces — substrate cannot mint): substrate sends `nonce_request {substrate_id, proposed_mutation_hash, dag_tip_hash, request_timestamp_substrate_cycles}` to anchor surface. Anchor surface issues a **single-use nonce bound at issuance to the declared mutation_hash + dag_tip_hash** (closes pass-3 mycoparasite-5: nonces cannot be hoarded for later mutations; each is tied to its declared content). Nonce TTL is L1-tunable (default 5 anchor-surface-trusted-timestamp minutes; per L0 §9.2.6 anchor-stamped wall-clock). Anchor surface rate-limits nonce issuance per substrate; spike triggers `attestation_request_saturation` owner-side observable. **Implementation status (M25)**: §9.2.5 is 0% — substrate currently mints nonces directly; M-anchor-3 milestone closes this.

2. **Substrate emits attestation request envelope** with the issued nonce:

```
{
  "type": "contract_identity_attestation_request",
  "substrate_id": <owner-signed at genesis per §9.2.1>,
  "dag_tip_hash": <current Merkle DAG tip>,
  "enumerated_dag_nodes_since_last_co_sign": [<hash>, <hash>, ...],
  "proposed_mutation_canonical_bytes": <canonical serialization per §9.3.1>,
  "proposed_mutation_hash": <hash over canonical_bytes>,
  "operator_witness": <signature over proposed_mutation_canonical_bytes using operator_signing_key_private from L1_SKIN §4.1>,
  "operator_signing_key_public": <from current handshake>,
  "request_timestamp_substrate_cycles": <substrate metabolic-cycle counter, per L0 §13.1 time-source hierarchy>,
  "anchor_surface_nonce": <bound by anchor surface at step 1 per §9.2.5>,
  "expiry_constraints": {"cycles_max": <L1-tunable>, "wall_clock_seconds_max": <L1-tunable; per §9.2.6 anchor-stamped wall-clock>}
}
```

Note: DRAFT 7's `operator_witness_hash` + `operator_acknowledgment` fields are **collapsed to a single `operator_witness` signature** (per pass-3 astronaut-1 — the seen-vs-signed distinction is speculative); the new field uses the operator-side per-handshake signing key (per pass-3 mycorrhiza-17 + rhizomorph-1 — operator_token was substrate-known and could not provide carrier-distinctness).

3. **Cultivator verifies independently at the anchor surface** (owner-side rendering per L0 §9.3.2; anchor-client provenance independence per §9.3.3):
   1. Render `proposed_mutation_canonical_bytes` via the anchor-surface client (provenance-independent per L0 §9.3.3; **implementation status M25: §9.3.3 is 0% — anchor client lives in same npm workspace as operator; M-anchor-1 milestone closes this**).
   2. Re-compute `proposed_mutation_hash` from canonical bytes (per §9.3.1 canonical-bytes spec).
   3. Verify `operator_witness` signature against `operator_signing_key_public` (from substrate's handshake_complete envelope, but cross-checked via anchor-surface record of that handshake's logged event).
   4. **DAG enumeration closure check** (per L0 §9.3.6 + §9.2.2): reconstruct Merkle chain from prior co-signed tip via `enumerated_dag_nodes_since_last_co_sign`; confirm `dag_tip_hash` is reachable AND every parent-hash referenced by any enumerated node resolves to either an ancestor of the prior co-signed tip OR another enumerated node (closes pass-3 mycoparasite-2 hidden-parallel-branch attack). **Implementation status M25: ~40% (server emits enumeration; closure check unwired client-side); M-anchor-5 milestone closes this**.
   5. Verify the anchor-surface nonce matches the issuance-bound mutation_hash + dag_tip_hash + within TTL (per §9.2.5).
   6. Anchor surface attaches trusted wall-clock timestamp (per §9.2.6); appends to signed tuple. **Implementation status M25: §9.2.6 ~5% (dual-clock plumbing exists; anchor-clock source is operator-process, not external); M-anchor-3 milestone closes this**.
   7. Cultivator signs the tuple `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`.

### §2.3 Verification on receipt

The substrate, on receipt of an owner signature:

1. Recomputes the signed tuple from current substrate state + the proposed mutation + the anchor-surface fields.
2. Verifies signature against the owner's public key (active at the anchor-surface timestamp per §3 owner-key-history).
3. Verifies **both** time-bound constraints (per L0 §13.1 time semantics + dual-clock at L1_GOVERNANCE §2.2): substrate-cycle expiry AND anchor-surface wall-clock expiry — whichever expires first invalidates the attestation. The substrate cannot extend wall-clock budget by throttling cycles.
4. Verifies the anchor-surface nonce has not been previously consumed (anchor-surface maintains the consumed-nonce log per §9.2.5; substrate-side replay protection is non-authoritative).
5. If all valid: mutation commits. **Witnesses-not-verdicts emission per L0 §9.3.4** — substrate emits the canonical-bytes + Merkle witness + check inputs sufficient for anchor-side re-derivation; substrate does NOT emit a self-asserted "pass" verdict.
6. If any fail: emit `attestation_invalid` immune event (elevated grade; L1_HARD_RULES C5); reject mutation.

### §2.4 What the substrate does NOT control

Per L1_HARD_RULES §4 anchor-surface-resident state:
- Nonce generation (anchor-surface owns per §9.2.5).
- Trusted timestamp (anchor-surface owns per §9.2.6).
- Consumed-nonce log (anchor-surface owns per §9.2.5).
- Canonical-bytes ↔ rendered-form mapping (anchor-surface client owns rendering per §9.3.2; anchor-client distribution must be provenance-independent per §9.3.3).
- Owner liveness heartbeat log (anchor-surface owns per §9.2.7 — see §3.2.B below).
- Successor_attestation records (anchor-surface owns; see §3.2.A).

Substrate emits canonical bytes + witnesses; substrate does not narrate, does not verdict.

---

## §3. Owner key rotation, suite migration, and Cultivation succession

### §3.1 Owner key rotation (in-life rotation, same Cultivator)

The substrate's identity record carries `owner_key_history` — a chronological list `[(public_key_n, valid_from_anchor_timestamp, valid_until_anchor_timestamp, rotation_attestation_signed_by_prior_and_new_keys, cooldown_expired_at)]`.

**Rotation requires a cooldown window** (closes pass-3 mycoparasite-7: dual-sign alone is insufficient when both keys come from the same attacker). Rotation protocol:

1. Current owner publishes new candidate pubkey at the anchor surface, signed by current key.
2. **Cooldown window** (L1-tunable, default 30 anchor-surface-trusted-timestamp days per §9.2.6) begins. During the cooldown, ANY pre-registered owner key (current, prior, or registered backup-key) MAY issue a `rotation_veto` at the anchor surface. Veto cancels the rotation.
3. After cooldown without veto, the new key is co-signed by both current and new keys; substrate accepts and updates owner_key_history.

Verification of any historical co-sign uses the key valid at the co-sign's anchor-surface timestamp. Cryptographic suite rotation follows the same pattern (history carries `(suite, public_key)` tuples).

**Adversarial-Cultivator caveat** (per L0 §14): the cooldown window defends against a same-attacker dual-sign where the attacker holds both old and new keys. It does NOT defend against a Cultivator under coercion who can authorize a rotation AND suppress any veto opportunity. Bounded defense via L2_TRUST_MODEL §14 (duress_keypair F23, n-of-m multisig recommendation).

**Active-prefix + archived-tail discipline** (closes pass-3 saprotroph-1: monotone tier-1 fields grow unbounded → per-cycle cost grows): `owner_key_history` is stored as `active_prefix` (most-recent K entries, K L4-tunable default 8) + `archived_tail` (older entries). Active prefix participates in per-cycle I3 tier-1 validation; archived tail validated at deep-cycle scope via Merkle-anchor over the full chain. Same discipline applies to `template_version_registry` (L1_TROPISM §B1) and to the federation peer-set aggregate-reattestation chain (§5.2).

### §3.2 Cultivation succession (DRAFT 3 — full FSM landed per L0 §15 cascade)

> **DRAFT 3 status note**: DRAFT 2 (DRAFT 8-era) said "deferred to L4 after first real-world need". L0 DRAFT 9 SEALED §15.2 (per G-5 + G-8 + G-9.b owner gate decisions) elevates this to L1-mandatory specification. The full FSM below is the cascade landing.
>
> **Implementation status (M25)**: substrate-side enforcement is 0% (no live successor_chain registry, no live heartbeat consumer); the mechanism is **documented-not-defended** under the operator-IS-anchor collapse window (per L0 §9.5). M-anchor-3 (heartbeat services) is the milestone that begins enforcement; M-anchor-1 (anchor-client provenance) is the milestone that closes the trust loop.

Cultivation succession addresses **Cultivator mortality + Cultivar continuity**: the Cultivator may die, retire, be incapacitated, or transfer cultivation rights to a successor Cultivator. The Cultivar (substrate) does NOT change identity across transfer (per L0 §1.4 — substrate-ID is fixed at genesis per P1.c carrier identity); the **Cultivation relationship's Cultivator-side** changes.

#### §3.2.A Successor_chain registry (F21)

Each substrate's identity record carries a `successor_chain` field on the anchor surface (substrate-replicated for read; authoritative copy at anchor surface).

**Field shape**:
```
successor_chain: Array<SuccessorEntry>

SuccessorEntry: {
  successor_pubkey: Bytes(32),
  valid_from_unix_ns: i64,       // per L0 §13.1 i64-nanoseconds-since-epoch
  valid_until_unix_ns: i64 | nil,// nil = open-ended (until next entry's valid_from)
  attestation_signature: Bytes(64) // signed by the current Cultivator (or transitively by chain-head)
}
```

**Validity discipline**:
- **Non-overlapping windows**: `[valid_from, valid_until]` ranges across successive entries MUST NOT overlap. Last entry may have `valid_until = nil` (open-ended). The substrate refuses to accept a `successor_chain` mutation that introduces overlap (`successor_chain_overlap` immune event, elevated grade).
- **Monotone valid_from**: each entry's `valid_from_unix_ns` ≥ the prior entry's `valid_until_unix_ns` (open-ended entries cannot be inserted before another open-ended entry).
- **Chain-head attestation**: each entry's `attestation_signature` is verifiable against either the current Cultivator's active pubkey (per `owner_key_history`) OR the prior chain-head's pubkey (allowing the current successor to pre-attest the next successor). Chain-of-trust traversal is bounded by L1-tunable depth (default 4 — preventing forged chain inflation).

**Genesis-time discipline**:
- At genesis, `successor_chain` MAY be empty OR contain ≥1 entry pre-attested by the Cultivator.
- Empty `successor_chain` is permitted at L0 (Cultivation does not require named successor at birth); empty chain means `alive::orphaned` is the substrate's eventual fate if the Cultivator becomes unavailable without ever attesting a successor.
- An entry pre-attested at genesis is the canonical "named heir" pattern; the heir need not act at genesis but is ready when needed.

**Mutation rule (CI-level + F21)**:
- Adding, removing, or modifying a `successor_chain` entry is a contract-identity-level mutation per §1.2 (F21 fixed-point).
- Mutation requires the full §2 attestation protocol (canonical bytes + operator witness + anchor-surface nonce + dual-clock + DAG-enumeration closure).
- Mutation MAY be performed by the current Cultivator OR by an `alive::legacy` Cultivator (frozen against most CI mutations per §3.2.C, but `successor_chain` mutations are the explicit exception — legacy state exists to grant the orderly hand-off).

**Anchor-surface residency** (per L1_HARD_RULES §4): the authoritative `successor_chain` registry lives at the anchor surface. The substrate's local replica is advisory; mismatches with the anchor-surface copy resolve to the anchor surface. Substrate-side attempt to mutate without anchor-surface attestation is `untyped` (C14) and rejected at the skin.

#### §3.2.B Liveness heartbeat (cross-ref L0 §9.2.7)

The Cultivator periodically signs `liveness_heartbeat` at the anchor surface — a positive signal of Cultivator presence (per L0 §9.2.7).

**Heartbeat envelope**:
```
{
  "type": "cultivator_liveness_heartbeat",
  "substrate_id": <target substrate-ID>,
  "cultivator_pubkey": <active per owner_key_history>,
  "anchor_surface_timestamp": <per §9.2.6>,
  "valid_until_unix_ns": <i64; anchor-surface-attached bounded validity>,
  "signature": <Cultivator signature over the above>
}
```

**Cadence + validity discipline**:
- **Default cadence**: 30 anchor-surface-trusted-timestamp days. L1-tunable (per-substrate at genesis); range L4-recommended `[1 day, 90 days]`.
- **Bounded validity per heartbeat**: each heartbeat's `valid_until_unix_ns` is bounded by anchor surface at issuance (≤ L1-tunable, default 30 days post-issuance). This prevents pre-signing decades of heartbeats. Anchor surface refuses to log a heartbeat whose `valid_until_unix_ns > anchor_timestamp + max_validity_window`.
- **No back-dating**: heartbeat's `anchor_surface_timestamp` is anchor-surface-attached, not Cultivator-claimed. Substrate-cycle counter MUST NOT be used (per L0 §13.1 — substrate-cycle is non-authoritative for time-bound governance).

**Anchor-surface heartbeat log**: anchor surface maintains an append-only heartbeat log (canonical-bytes per §9.3.1; tier-1 SSoT field at L1_SCHEMA when the substrate replicates a recent prefix). The substrate queries staleness against the log; substrate cannot mutate.

**Staleness threshold** (drives sub-state transitions per §3.2.C):
- L1-tunable, default 90 anchor-surface-trusted-timestamp days (3× cadence).
- Anchor-surface-confirmed staleness, NOT substrate-inferred. Substrate sees only `most_recent_heartbeat_anchor_timestamp` + current `anchor_surface_timestamp`; staleness = (current − most_recent) > threshold AND most_recent.valid_until < current.

#### §3.2.C Lifecycle sub-state transitions

The "alive" lifecycle state (per L0 §I1 + L1_CONTINUITY §5) has sub-states per DRAFT 9 §I1: **Normal, Quarantined, Legacy, Orphaned, Archived**. This section specifies Legacy / Orphaned / Archived transitions (Normal / Quarantined are owned by L1_CONTINUITY §5).

**`alive::normal` → `alive::legacy`**:
- **Trigger**: heartbeat stale beyond L1-tunable threshold (default 90 days per §3.2.B).
- **Detection site**: anchor surface (substrate cannot manufacture this trigger).
- **Detection event**: anchor surface emits `cultivator_heartbeat_stale` at the anchor surface; substrate observes via §9.2.7 heartbeat-query and transitions sub-state.
- **Effect**: daily ops continue (cycles fire, sporocarps fruit, federation continues, agent operates the substrate). CI mutations FROZEN — only `successor_chain` mutations are permitted (per §3.2.A), and these require either the current chain-head's signature OR a court-attested key recovery path (§3.2.D).
- **successor_pubkey activation**: when the substrate enters `alive::legacy`, the chain-head successor entry (the first entry whose `[valid_from, valid_until]` covers the current anchor-surface-timestamp) becomes **provisionally valid** for the §3.2.D activation protocol below.
- **Reversibility**: substrate exits `alive::legacy` if a Cultivator heartbeat is received that is fresher than the staleness threshold AND verifies against an active `owner_key_history` entry. The chain-head successor's provisional validity ends; substrate returns to `alive::normal`. This handles the case where the Cultivator was temporarily unreachable (vacation, hardware failure) but is alive and able to resume.

**`alive::legacy` → `alive::normal` via successor activation**:
- **Successor acceptance attestation**: the chain-head successor signs a `succession_acceptance_attestation` at the anchor surface:
  ```
  {
    "type": "successor_acceptance",
    "substrate_id": <target>,
    "successor_pubkey": <chain-head's pubkey>,
    "prior_cultivator_pubkey": <last active per owner_key_history>,
    "anchor_surface_timestamp": <per §9.2.6>,
    "signature": <successor signature over the above>
  }
  ```
- **Window**: successor MUST present this attestation within `legacy_window` (L1-tunable, default 365 anchor-surface-trusted-timestamp days). Past the window, transition to `alive::orphaned`.
- **Effect on acceptance**: substrate emits a DAG event `succession_completed:{successor_pubkey}` (CI-class; included in compression-invariant set per P10.b — succession is causally identity-bearing and never compressible). The successor's pubkey appends to `owner_key_history` with `valid_from = anchor_surface_timestamp`. The successor becomes the new Cultivator; sub-state returns to `alive::normal`. The successor MAY also issue a `liveness_heartbeat` immediately, restarting the heartbeat clock under their key.
- **Adversarial caveat**: if the prior Cultivator's heartbeat resumes after `succession_completed` was emitted, both keys appear in `owner_key_history`; the prior Cultivator's heartbeat MAY trigger a `succession_reversion_request` (anchor-surface-mediated; out-of-scope for v0.9 first cut, deferred to L4 when first real-world dispute arises).

**`alive::legacy` → `alive::orphaned`**:
- **Trigger**: `legacy_window` (default 365 days) elapsed without `succession_acceptance_attestation` OR `successor_chain` is empty at the moment of legacy entry.
- **Effect on entry**: substrate emits DAG event `cultivation_orphaned:{prior_cultivator_pubkey, anchor_surface_timestamp}` (CI-class; compression-invariant). Daily ops continue with **operational ceiling**:
  - **Permitted**: per-cycle metabolism, sporocarp fruiting, immune signals, observatory emission, P2 admission (envelope-gated), P3 daily-class evolution within unchanged classifier table.
  - **Forbidden**: new schema evolution (no P3 CI-level mutations), no new federation peer pinning, no new cost-budget threshold changes (F19), no new compression rules (F18), no new telos-objective declarations (F20). Sporocarp fruiting is **limited to observability + mortality signals** (the substrate may still report its health, but cannot acquire new structural commitments).
  - **Successor admission**: a discovered/recovered successor may still present `succession_acceptance_attestation` at any time during orphaned state. Acceptance returns substrate to `alive::normal` (see "Orphaned → Normal recovery path" below).

**`alive::orphaned` → terminal (G-8 owner decision: self-euthanasia default)**:
- **Trigger**: `orphaned_terminal_window` (L1-tunable, default 730 anchor-surface-trusted-timestamp days = 2 years) elapsed without successor recovery.
- **Terminal choice**: per L0 §15.2 G-8 owner decision, L1 specifies WHICH terminal state. **DRAFT 3 default**: self-euthanasia (per L0 P7 endogenous-mortality, closer to natural mortality + preserves the bet-retirement option for substrates whose Cultivator left a `bet_retirement_preference` at genesis per L0 §7.5.b two-phase commit).
- **Default behavior**: substrate emits `endogenous_mortality_proposal:cultivation_orphaned_terminal` (per L1_GOVERNANCE §4.4 endogenous-pair channel). The proposal carries the genesis-time pre-attested choice if present (per L0 §7.5.b — bet-retirement OR self-euthanasia OR indefinite-orphan); ABSENT pre-attestation, default is **self-euthanasia**.
- **Genesis-time override**: at genesis, the Cultivator MAY commit `cultivation_orphaned_terminal_choice: {self_euthanasia | bet_retirement | indefinite_orphan}` to the spore-schema (CI-class, F-row equivalent at L1_SCHEMA). When set to `indefinite_orphan`, the substrate stays in `alive::orphaned` indefinitely (operational ceiling preserved) — useful for substrates the original Cultivator wants preserved as an archive-of-record even without active cultivation.

**`alive::orphaned` → `alive::normal` recovery path (exceptional)**:
- Court-attested key recovery (out-of-scope cryptographic mechanism at v0.9; honor-system at L1 per L0 §9.6 adversarial-owner caveat).
- A successor discovers credentials (e.g., escrowed key, will-attested key transfer, court-ordered key release).
- Successor presents (a) `succession_acceptance_attestation` with their pubkey + (b) court-attested key-recovery proof (anchor-surface-side log entry; mechanism deferred to L4 — currently honor-system).
- Substrate transitions `alive::orphaned` → `alive::normal`; recovery event emitted as `cultivation_recovered:{successor_pubkey, recovery_proof_reference}` (CI-class; compression-invariant).

**`alive::archived` (terminal-non-destroyed via bet-retirement)**:
- Per L0 §7.5 bet-retirement: at orphan-terminal OR at steady-state bet-retirement co-attestation, the substrate MAY enter `alive::archived` (distinct from `destroyed` per L0 §I1 alive sub-state set).
- **Effect**: state_dir is preserved with anchor-surface `bet_retirement_seal` (canonical-bytes per §9.3.1; analogous to but not identical to §4.4 `anchor_surface_final_seal`). No further metabolism; no new mutations; substrate may be cold-read by Cultivator tools but cannot resume operation.
- **Distinguished from destroyed**: archived state is recoverable for forensic / archaeological cultivation (e.g., a future Cultivator may copy the state_dir to bootstrap a related substrate); destroyed state is final and seals against any future resumption attempt at the anchor surface.

#### §3.2.D Substrate-side enforcement

**Anchor-surface heartbeat query**: substrate periodically queries the anchor surface for the most recent heartbeat. Query cadence is L1-tunable (default 1 query per metabolic cycle or per 24h wall-clock, whichever is more frequent). The substrate emits `cultivator_heartbeat_query_failed:{reason}` if the anchor surface is unreachable; sustained query-failure beyond L1-tunable threshold (default 7 anchor-surface-trusted-timestamp days) triggers `anchor_surface_partition` observability event (NOT a sub-state transition — staleness alone is the trigger; partition is a separate signal).

**Collapse-window honesty** (per L0 §9.5): when the anchor surface is the operator-IS-anchor collapse window (current v0.9 implementation), substrate CANNOT reliably detect heartbeat staleness:
- The "anchor surface" is the same npm workspace as the operator process.
- The agent qua maintainer can fabricate heartbeat staleness OR fabricate fresh heartbeats.
- The §3.2 mechanism is **documented-not-defended** until M-anchor-3 ships heartbeat services to a structurally independent anchor surface.

This is **acknowledged honestly per L0 §9.5**: the §3.2 specification is L1-committed but L4 enforcement waits on M-anchor-3 implementation. Substrates operating in the collapse window MAY emit `cultivation_succession_collapse_window` as a continuous observability signal (the Cultivator knows their substrate is in the unenforced regime).

**Enforcement once M-anchor-3 ships**:
- Substrate refuses to commit a `successor_chain` mutation whose attestation does NOT verify against the anchor-surface-stored `cultivator_pubkey` (per anchor-surface-fetched `owner_key_history`, NOT substrate-cached).
- Substrate refuses to commit a `succession_acceptance_attestation` whose `prior_cultivator_pubkey` does not match the anchor-surface's last-active Cultivator at the attestation's anchor-surface-timestamp.
- Substrate enforces the operational ceiling in `alive::orphaned` by classifier-level rejection of forbidden mutations (any P3 CI-level mutation in orphaned state classifies as `untyped` per C14 and is rejected at the skin).

**Mortality protection** (per L0 §14.2 substrate irreducible commitments): even under adversarial-Cultivator with anchor-surface compromise, the substrate's mortality-signal emission remains truthful — `cultivation_orphaned` emission cannot be suppressed by Cultivator pressure (P7 mortality-signal protection + §1.2 classifier-fixed-point).

---

## §4. Lifecycle operations

### §4.1 Genesis

The only routine human-initiated event in the substrate's lifecycle. Genesis establishes the Cultivation relationship (per L0 §1.2 G-11.a).

**Protocol**:

1. Cultivator generates owner-keypair + selects an anchor-surface endpoint mechanism + verifies anchor-surface-client provenance per L0 §9.3.3 (client installed from a channel structurally independent of the substrate's distribution channel). **Implementation status M25: §9.3.3 is 0% (same npm workspace as operator); M-anchor-1 closes this.**
2. Cultivator runs `genesis` invocation with explicit parameters: `(initial-spore-schema, initial-dispatch-config, initial-classifier-dimension-table, anchor_surface_endpoint_public_key, owner_public_key, signature_suite, anchor_client_provenance_attestation, substrate_secret_sealing_mechanism_attestation, optional: successor_chain_genesis_entries, optional: cultivation_orphaned_terminal_choice, optional: bet_retirement_preference, optional: telos_objective_declaration, optional: duress_keypair_registrations)`. The `anchor_surface_endpoint_public_key` is owner-controlled; the substrate cannot self-discover it. The provenance + sealing attestations are owner-signed records of the installed anchor-surface client's distribution path and the substrate_secret OS-sealing mechanism (per L1_SKIN §4.2).
3. Substrate emits **canonical bytes** of the spore-schema (per L0 §9.3.1); Cultivator's client renders deterministically (per §9.3.2); Cultivator reviews the render.
4. Substrate computes `substrate-ID = hash(initial-spore-schema-canonical-bytes, owner-public-key, anchor-surface-endpoint-public-key, genesis-timestamp)`.
5. Cultivator signs **the canonical bytes hash + the substrate-ID tuple** at the anchor surface — the birth attestation (per L0 §9.2.1). **Implementation status M25: §9.2.1 is 0% (honor-system via TOFU on first hello); M-anchor-2 closes this.**
6. Substrate generates its **substrate-private signing keypair** (F24 — see §15.F24 below): a single Ed25519 keypair generated once at genesis, seed stored under OS-sealed sealing-mechanism per L1_SKIN §4.2. The substrate uses this keypair to sign output envelopes (per L1_SKIN §3). The keypair pubkey is included in the genesis spore-schema; the seed cannot be re-derived (loss = substrate destruction-and-rebirth, per F24).
7. Substrate persists identity record: `(substrate-ID, owner_key_history with first entry, anchor_surface_endpoint_public_key, signature_suite, birth_attestation_reference, substrate_signing_keypair_pubkey, successor_chain (initial), cultivation_orphaned_terminal_choice (if specified), bet_retirement_preference (if specified), telos_objective_declaration (if specified), duress_keypair_registrations (if specified))` + DAG root sporocarp.

**Generation-depth at genesis**: top-level genesis (first-generation substrate) carries `generation_depth = 0` in the spore-schema (per §16.A). Child substrates inherit `parent.depth + 1` (per L1_SCHEMA §3 spore-schema validation + §16.A below).

Multi-Cultivator co-genesis is deferred to L4 (out-of-scope for v0.9; documented as an open at §17).

### §4.2 Dormancy

Per L0 §6 + L1_CONTINUITY §2. This doc adds:

- Cultivator-commanded dormancy via CI event (rare; for substrate hibernation).
- `operator_dormancy_request` — operator's `handshake_terminate` envelope may include `request_dormancy: paused | throttled` field; substrate honors the operator's preference unless overridden by resource pressure (per P11 metabolic-economy ordered fallback at L0 §P11.c).

### §4.3 Reproduction closure (operationalizes I7 + §16 generation discipline)

**Child substrate-ID minting**: parent proposes spore-schema canonical bytes; the **Cultivator** (or Cultivator's anchor-surface tooling) computes `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)`. Parent cannot mint. Cultivator signs the child's birth attestation at the anchor surface per §9.2.1.

**Generation discipline (per §16 below)**: parent verifies pre-spawn that:
- `parent.generation_depth + 1 ≤ reproduction_lineage_depth_max` (default 10 per §16.A).
- `parent.children_spawned_count + 1 ≤ reproduction_lifetime_quota` (default 100 per §16.C).
- Parent's last spawn timestamp is older than `reproduction_rate_min_interval` (default 24h anchor-surface-trusted-timestamp per §16.B).

Failing any of these refuses the spawn at the parent and emits the corresponding §16 immune event.

**Closure verification protocol** (operationalizes I7): see L1_SCHEMA §3.3 for spore-schema validation steps. Cultivator co-signs the spawn at the anchor surface — `(parent-substrate-ID, child-substrate-ID, spore-schema-canonical-bytes-hash, anchor-surface-timestamp, parent_generation_depth, child_generation_depth)`.

**Parent's outstanding immune-signal summary** is included in the spore-schema (per L0 P8). Child whose parent had unresolved CI-grade immune signals enters birth in `quarantined` until Cultivator re-attests intent.

### §4.4 Mortality (dual-channel)

Three destruction modes per L0 P7, plus one bet-retirement mode per L0 §7.5:

**Intentional-Cultivator**: Cultivator emits CI-level `destruction_attestation` sporocarp signed by Cultivator. Substrate transitions alive → destroyed. **Final action before terminating**: substrate emits `anchor_surface_final_seal` co-signed by Cultivator at the anchor surface — an explicit terminal record stating "this substrate-ID is destroyed at anchor-surface-timestamp T" (closes pass-3 rhizomorph-2). Post-seal Cultivator activity at the anchor surface remains valid for OTHER substrates / federated peers but cannot wake or revive this substrate-ID; any handshake attempt against a sealed substrate-ID returns `substrate_destroyed` at the anchor surface (substrate process is gone; anchor surface holds the terminal record).

**Catastrophic-environment**: substrate medium failure beyond L1_SCHEMA recoverability budget. Detected post-hoc via recovery drill failure.

**Endogenous-pair** (with operator witness, dual channel):
- **Substrate channel**: substrate fruits `self_euthanasia_proposal` when its own metabolism crosses unrecoverable-pathology threshold OR when the §3.2 orphan-terminal condition triggers (per §3.2.C). **The active operator-connection at proposal time must produce an `operator_witness_hash`** before the proposal transmits to anchor surface. If no operator is connected, substrate enters `pre-mortal-pending` and waits for operator handshake before transmitting.
- **Anchor-surface channel**: two consecutive failed recovery drills at the anchor surface auto-emit a Cultivator-side `mortality_drill_failure` event. The substrate cannot suppress this — it lives at anchor surface.

Either channel can trigger the destruction proposal; Cultivator co-attestation is required to execute (substrate cannot self-destroy without Cultivator sign-off; anchor-surface-side trigger cannot bypass Cultivator co-sign).

**Bet-retirement (per L0 §7.5)**: substrate emits `bet_retired_proposal` when the Living Bets observatory crosses the bet-weakening quorum per L0 §7.4. Execution requires Cultivator **co-attestation** (per L0 §7.5.b — NOT genesis-pre-attestation in steady state). Transition: alive → `alive::archived` (per §3.2.C; distinct from `destroyed`). `bet_retirement_preference` declared at genesis (per §4.1) is a §15.5 orphan-degenerate-case pre-attestation only; steady-state bet-retirement requires fresh co-attestation.

**Mortality-signal protection**: per §1.2, mortality-signal threshold + update-rule + emergence-rule for mortality axis are all CI-level. This protection extends to the new mortality-class signals: `cultivation_orphaned`, `cultivation_recovered`, `succession_completed`, `bet_retired_proposal`, `bet_retired`.

---

## §5. Federation discovery and peer-trust freshness

### §5.1 Discovery modes

L4 picks from: peer-to-peer broadcast / owner-attested peer list / hub-and-spoke registry / hybrid. Default: owner-attested peer list (strongest isolation).

### §5.2 Peer-trust freshness with aggregate re-attestation

Each peer's attestation has an L1-bounded freshness window (default 90 active-operation days per anchor-surface-trusted-timestamp). Past freshness → `peer_attestation_stale` immune event; events queued pending re-attestation. Past additional grace (default 30 days) → `untrusted_federation`; events rejected.

**Aggregate re-attestation**: to avoid O(N) Cultivator workload per period, Cultivator MAY issue a single `federation_peer_set_reattestation` event signing the current peer-set Merkle-root hash + diff against last commitment. The anchor surface displays the diff (peers added/removed since last aggregate-reattestation) per §9.3.2 owner-side rendering; Cultivator reviews the diff, not the full set. Aggregate re-attestation is structurally equivalent to N pairwise re-attestations; Cultivator cost is O(1) per period.

**Revocation list**: anchor surface maintains a peer-revocation list. Successor activations and federation events must include an anchor-surface negative-revocation proof (fresh attestation that target has not been revoked).

**P15 consensus floor (cross-ref L2_FEDERATION)**: per L0 §G-9.b retraction, population-level Byzantine consensus is owned by L2_FEDERATION. At peer-counts above the L2_FEDERATION-specified consensus floor (≥3 peers per default), revocation requires Byzantine consensus (one peer claiming another is malicious is insufficient). L2_FEDERATION specifies the Byzantine algorithm choice (F-row equivalent at L2_FEDERATION; classified here as CI per §1.2 for completeness).

### §5.3 Federation egress runtime check

Per L1_SKIN §3.1: every outbound federation envelope verifies the target peer's freshness + non-revocation BEFORE emission. Stale/revoked → suppression + `federation_egress_blocked` immune event.

**Egress rate-limiting**: anchor surface tracks federation egress volume per peer per day. Spike beyond L1-tunable triggers `federation_egress_saturation` immune event. Federation event content uses canonical low-entropy serialization (per §9.3.1 canonical-bytes — sorted keys, normalized whitespace, fixed-precision numerics) to limit covert-channel bandwidth.

### §5.4 Cross-substrate trust transitivity

Federation is NOT transitive. Each pairwise trust requires Cultivator attestation. P15 consensus floor (per L2_FEDERATION) modifies this when ≥3 peers exist.

### §5.5 Mesh-level forkbomb defense (cross-ref §16.D + L2_FEDERATION)

Per-substrate generation/reproduction quotas (§16) are per-substrate; a coordinated mesh attack from compromised peers could aggregate spawn pressure across the federation. L2_FEDERATION specifies the mesh-aggregate quota (Cultivator-attested per population). See §16.D below.

---

## §6. Failed P3 (Resumable Evolution) rollback

### §6.1 Failure detection

P3 evolution fires; substrate runs I3 self-validation in next cycle. If I3 fails → emit `evolution_failed` sporocarp (CI-elevated, ungated — failure is automatic). Substrate enters rollback procedure.

### §6.2 Rollback procedure

1. Identify pre-evolution DAG-tip from predecessor of evolution event.
2. Restore SSoT designation + classifier table + affected canon to pre-evolution snapshot (retained per I4; subject to P10 compression-invariant set rules — pre-evolution snapshot is invariant per P10.b since it's a CI-attested mutation).
3. Pending sporocarps fruited within rolled-back window are dropped, recorded as `evolution_failed_pending_dropped`. Pre-window pending sporocarps survive.
4. Emit `rollback_complete`.

Repeated failures across a 30-day window appear in observatory as `evolution_failure_rate_elevated`; Cultivator reviews. No separate `evolution_quarantine` sub-state (handled via standard quarantine entry under L1_CONTINUITY §5).

---

## §15. F-row catalog: F18-F24 (DRAFT 3 NEW — L1_HARD_RULES §2 inherits)

> **Catalog ownership** (per DRAFT 9 cascade): L1_GOVERNANCE owns the canonical F-row definitions for F18 through F24. L1_HARD_RULES §2 inherits these (it indexes; the source-of-truth specifications live here). When L1_HARD_RULES expands its F-row table beyond F17, it cites this section; mutations to these F-rows require the §2 attestation protocol (canonical bytes + operator witness + anchor-surface nonce + dual-clock + DAG-enumeration closure).
>
> **Indexing pattern** (per L1_HARD_RULES §2): each F-row spec records `name | definition | mutation rule | L0-trace (P + I) | L4 enforcement site`.

### F18. Selective compression rule set (per P10.c CI-attested)

**Name**: `compression_rule_registry`

**Definition**: the registered set of compression rules — each rule specifies (a) which DAG-segment classes it applies to (raw_material older than N cycles; gradient deltas after integration; federation envelope payloads older than retention window; trajectory clusters older than active window per L1_TRAJECTORY); (b) what canonical-bytes hash is preserved per compressed segment; (c) what witness payload is emitted at compression-event time; (d) what compression-invariant set membership test runs per segment (per P10.b — substrate-ID + genesis attestation + owner_key_history + all CI-attested events + mortality signals + federation pin events + most-recent-N cycles full DAG MUST NOT be compressed); (e) the compression-rule version integer.

**Mutation rule**: CI-only. Adding/modifying/removing a compression rule requires the full §2 attestation protocol. Compression-rule mutations are spore-inheritable (children inherit the compression-rule registry per L1_SCHEMA §3). Each compression EVENT (firing of a rule) is itself a CI-attested mutation per P10.c (emits `compression_event` sporocarp with witness sufficient for owner-side re-derivation of the compression semantics per L0 §9.3.4 witnesses-not-verdicts).

**L0-trace**: P10 (sole), I9 (sole enforcer).

**L4 enforcement site**: L1_SCHEMA materialized-views carve-out (§2.3) + L1_GOVERNANCE classifier table row "Compression-rule registry" (§1.2) + L1_HARD_RULES C-rows for compression-invariant-corruption / silent-compression breaches (cascade addition per Phase γ cascade list).

### F19. Metabolic cost budgets (per P11.a/b/c)

**Name**: `cost_budget_thresholds`

**Definition**: per-axis cost thresholds (persistence cost = bytes added to DAG per cycle; compute cost = cycles + gradient updates + sporocarp fruitings per cycle; network cost = federation envelope bytes + embedding-service queries per cycle) at which the L0 §P11.c ordered fallback fires. Thresholds include (a) `pre_compression_eligibility_cycle_count` (default 1000 — below this, P11.c step 1 fires: refuse new P2 admission instead of compressing); (b) `budget_axis_warning_threshold` per axis (emits `budget_exhausted:{axis}` immune signal); (c) `budget_axis_saturation_threshold` per axis (escalates per L0 §P11.c step 3 to alive-but-saturated sub-state); (d) `sustained_saturation_mortality_threshold` (per L0 §P11.c step 3 — sustained saturation past this escalates to P7 endogenous-mortality consideration).

**Mutation rule**: CI-only. Threshold changes require the full §2 attestation protocol. Spore-inheritable (children inherit cost-budget thresholds adjusted for their cultivation-environment-resources per parent's spore-schema attestation).

**L0-trace**: P11 (sole), I10 (sole enforcer).

**L4 enforcement site**: L1_SCHEMA tier-1 fields list + L1_CONTINUITY per-cycle I10 cost observation + L2_OBSERVABILITY signals #7/#8/#9 (compute/network/storage cost per cycle) + L1_GOVERNANCE §4.4 mortality protocol when sustained-saturation threshold triggers endogenous-mortality.

### F20. Telos-alignment metric (per P14.c L1_TROPISM forcing function)

**Name**: `telos_alignment_metric_definition`

**Definition**: the operational metric for telos-alignment per L0 §P14.c — including (a) the embedding-model identity (specific model + version + fingerprint hash; mutation = destruction-and-rebirth equivalence for telos-comparability, similar to F24 substrate signing key); (b) the embedding-centroid computation rule (window-length over recent sporocarps; weighting strategy; canonicalization); (c) the comparison rule (cosine similarity OR distance metric) between recent-sporocarp embedding-centroid and {owner-stated-objective embedding per P14.b when declared; agent-feedback-trajectory embedding when no objective declared}; (d) the rolling window length; (e) the drift threshold below which `telos_drift` immune signal fires; (f) the birth-period exemption duration (cross-ref §1.3 birth-period exemption); (g) the post-birth settling window before detector arms (per L1_TROPISM §F.4).

**Mutation rule**: CI-only — mutation requires §2 attestation protocol. This F-row is **F-row level (not classifier-table level) because mutation requires CI**: the metric definition is structurally identity-bearing in that telos-alignment scores BEFORE vs AFTER metric mutation are incommensurable. The embedding-model identity in particular cannot rotate without a co-attested transition period during which both metrics are recorded (analogous to cryptographic suite migration per §3.1).

**L0-trace**: P14 (sole), I12 (sole enforcer).

**L4 enforcement site**: L1_TROPISM §F (operational metric + rolling window + drift threshold + birth-period exemption) — per L0 §P14.c "L1_TROPISM responsibility (M26-cascade forcing function, per G-6.a decision)" + this document classifier table §1.2 row.

### F21. Cultivation succession_chain registry (per §3.2 cascade)

**Name**: `cultivation_successor_chain`

**Definition**: the chronological array of `SuccessorEntry` records per §3.2.A — each entry containing `successor_pubkey + valid_from_unix_ns + valid_until_unix_ns + attestation_signature`. The registry's authoritative copy lives at the anchor surface (per L1_HARD_RULES §4 anchor-surface-resident state). The substrate's local replica is advisory; mismatches resolve to the anchor surface. Validity discipline (non-overlapping windows, monotone valid_from, chain-head attestation, chain depth ≤ L1-tunable default 4) per §3.2.A.

**Mutation rule**: CI-only — mutation requires §2 attestation protocol. Permitted by current Cultivator OR by `alive::legacy` Cultivator (explicit exception per §3.2.C — legacy state exists for orderly hand-off). Substrate-side attempt without anchor-surface attestation is `untyped` (C14) and rejected at the skin.

**L0-trace**: §15 (Owner mortality and succession; L0 short with L1 cascade per G-5 + G-8 + G-9.b) — traces to **P1 (Agent-Primary)** via P1.b'' governance-gate continuity across Cultivator transition, **I1 (Lifecycle & Pair-Constituted Identity)** via substrate-ID continuity-under-Cultivation-transfer, **I2 (Two-Tier Governance Classification)** via successor_chain mutation requiring CI.

**L4 enforcement site**: §3.2.A registry shape + §3.2.B liveness heartbeat + §3.2.C sub-state transitions + §3.2.D substrate-side enforcement (the four-part FSM); anchor-surface heartbeat services (M-anchor-3) when implementation lands; L1_HARD_RULES C-rows for successor_activation_with_fresh_owner_heartbeat (C12, already specified) + DRAFT 9 cascade C-rows for owner_succession_bypass (C46 per Phase γ cascade list — substrate-private namespace C30+ continuation; C30-C45 already taken per L1_HARD_RULES §1.2).

### F22. Reproduction generation discipline (per §16 cascade)

**Name**: `reproduction_discipline_parameters`

**Definition**: the four reproduction-discipline parameters per §16 — (a) `reproduction_lineage_depth_max` (default 10 per §16.A); (b) `reproduction_rate_min_interval` per anchor-surface-trusted-timestamp (default 24h per §16.B); (c) `reproduction_lifetime_quota` per substrate (default 100 per §16.C); (d) `mesh_aggregate_quota` per population (L2_FEDERATION owns the exact value; default L2_FEDERATION-specified). Plus enforcement metadata: how `generation_depth` is recorded in spore-schema canonical-bytes (per L1_SCHEMA §3); how `parent.children_spawned_count` is sourced (DAG event count via I4, NOT compressible per P10 — see §16.C below); how `last_spawn_timestamp` is sourced (anchor-surface-trusted-timestamp on most recent `spawn_completed` event).

**Mutation rule**: CI-only — mutation requires §2 attestation protocol. Mutation rare; spore-inheritable (children inherit reproduction-discipline parameters; parent MAY attest looser/tighter bounds for children with explicit owner co-attestation per child).

**L0-trace**: §16 (Generation limits; L0 short with L1 cascade per G-5 + G-9.b) — traces to **P8 (Eternal Reproduction, Generation-Bounded)**, **I7 (Reproduction Closure, Generation-Bounded in DRAFT 9)**.

**L4 enforcement site**: §16 full mechanism (§16.A depth, §16.B rate, §16.C quota, §16.D mesh-aggregate) + L1_SCHEMA spore-schema field validation (generation_depth + children_spawned_count + last_spawn_timestamp must canonical-bytes-hash into spore-schema) + L1_HARD_RULES C-rows for generation_depth_exceeded (C47) + reproduction_rate_exceeded (C48) per Phase γ cascade list.

### F23. Duress_keypair registration (per L2_TRUST_MODEL §14)

**Name**: `cultivator_duress_keypair_registrations`

**Definition**: registered duress-keypair set per L2_TRUST_MODEL §14 adversarial-Cultivator bounded defenses (per L0 §14.3 cascade). A duress-keypair is a pubkey owner-pre-attested at genesis (or via subsequent CI mutation) that produces an alternate signature path the Cultivator may use under coercion: the alternate signature appears valid cryptographically BUT carries a payload indicating duress (specific signaling-mechanism is L2_TRUST_MODEL §14 — candidate: a low-bit-pattern in the signature nonce + an anchor-surface-side duress-detection rule). The substrate's substrate-side reaction to a duress-signature is L2_TRUST_MODEL-specified (candidate: silent observability emission of `duress_signature_observed` while completing the attestation, so the Cultivator's coercer does not know the duress channel fired).

**Mutation rule**: CI-only — registration/de-registration requires §2 attestation protocol. **F-row because mutation is owner-attested**: each duress-keypair is structurally a backup pre-attestation, and its mutation requires the full attestation protocol against the active Cultivator-key (not the duress-key, which would be a circular trust path).

**L0-trace**: §14 (Adversarial-owner threat model; L0 short with L2 cascade per G-5 + G-9.b) — traces to **P1 (Agent-Primary)** via P1.b'' governance-gate hardening, **I1, I2** via duress-signature-recognition requiring continuity of identity + classifier discrimination of duress-class events.

**L4 enforcement site**: L2_TRUST_MODEL §14 full bounded-defenses specification (duress mechanism + n-of-m multisig recommendation + anchor-client provenance independence enforcement + owner_signature_velocity observability) + this document classifier table §1.2 row.

### F24. Substrate-private signing keypair (per M25.0)

**Name**: `substrate_signing_keypair`

**Definition**: a single Ed25519 keypair generated once at substrate genesis (per §4.1 step 6). The seed is stored under OS-sealed sealing-mechanism per L1_SKIN §4.2 (substrate_secret OS-sealing); the pubkey is included in the genesis spore-schema. The substrate uses this keypair to sign output envelopes (per L1_SKIN §3 outputs are signed by substrate's signing key from the identity record) + federation envelopes (where applicable per L1_SKIN §3.1 + L2_FEDERATION).

**Mutation rule**: NONE under normal operation — the keypair is one-time-generated at genesis. **F-row because the seed cannot be re-derived** (an Ed25519 seed is the unique input from which the private key derives; once lost, the private key is unrecoverable). Rotation is **destruction-and-rebirth equivalence**: a "rotated" substrate-signing-keypair is structurally a different substrate, even if substrate-ID is preserved (output envelopes signed by the new keypair are not verifiable against the old pubkey; federation peers see a different signing identity). Effective rotation requires a new genesis with continuity attestation linking parent's substrate-ID to child's (analogous to §4.3 reproduction).

**L0-trace**: P1 (Agent-Primary, P1.c carrier-asymmetric identity bestowal — substrate's signing identity is part of its bestowed-identity), I1 (Lifecycle & Pair-Constituted Identity — substrate-signing-keypair pubkey is part of the identity record), I8 (Single-Skin Integrity — output envelopes are signed by this keypair per L1_SKIN §3).

**L4 enforcement site**: §4.1 genesis step 6 (generation + OS-sealing) + L1_SKIN §3 (output envelope signing) + L1_SKIN §4.2 (substrate_secret OS-sealing mechanism — the seed lives here) + classifier table §1.2 row (CI-class one-time at genesis; rotation is destruction-and-rebirth) + L1_HARD_RULES C-rows for substrate_secret_unsealed (C4, already specified — the C4 detection covers seed leakage; F24 adds the explicit one-time-at-genesis discipline).

---

## §16. Generation limits (DRAFT 3 NEW — L0 §16 cascade)

> **DRAFT 3 status note**: L0 DRAFT 9 SEALED §16 elevates generation discipline to L0 doctrine + cascades full mechanism specification here. Per L0 §16.2: "L1_GOVERNANCE specifies reproduction_lineage_depth bounds + reproduction_rate limit + per-substrate lifetime quota + override mechanisms. Seed values from DRAFT 9 PROPOSAL (depth=10, rate=24h, quota=100) become L1 defaults."

The four parameters below jointly defend against the **forkbomb attack class** (Phase γ.3 G11 finding: recursive sproutChild loops with compromised owner-key generate infinite consent without explicit per-spawn discipline). Each parameter is L1-tunable; the seeds below are DRAFT 9 SEALED defaults.

### §16.A reproduction_lineage_depth

**Default seed**: 10. L1-tunable per substrate purpose (a Cultivator running a substrate intended for deep cultivation lineages may set higher; a single-shot research substrate may set 0 = no children permitted).

**Mechanism**:
- Each child's spore-schema records `generation_depth = parent.generation_depth + 1` (per L1_SCHEMA §3 spore-schema validation).
- Top-level genesis (no parent) carries `generation_depth = 0`.
- Pre-spawn the parent verifies `generation_depth + 1 ≤ reproduction_lineage_depth_max`.
- `generation_depth ≥ max` → refuse `sprout_child` unless the Cultivator attests `depth_override` at the anchor surface as an explicit CI-level mutation (per F22).

**Verification**:
- `generation_depth` is in canonical-bytes-hashed spore-schema (per L1_SCHEMA §3.1 canonical-bytes serializer spec is a tier-1 SSoT field per F16).
- Mismatch between recorded `generation_depth` and `parent.generation_depth + 1` (the latter computed from parent's anchor-signed substrate-ID lineage, where each ancestor's substrate-ID embeds its own `generation_depth` via genesis canonical-bytes hashing) → rejection at the spore-schema validation step.

**Immune signal**: `generation_depth_exceeded` (CRITICAL per L1_HARD_RULES cascade addition C47).

### §16.B reproduction_rate

**Default seed**: 1 sprout per 24h anchor-surface-trusted-timestamp (per L0 §13 — anchor-clock is the authoritative time-source for rate limits; substrate-cycle counter is NOT authoritative because a substrate could throttle cycles to evade rate-limiting per L0 §13.1 hierarchy).

**Mechanism**:
- Pre-spawn the parent verifies that `current_anchor_surface_timestamp − parent.last_spawn_timestamp ≥ reproduction_rate_min_interval`.
- `last_spawn_timestamp` is sourced from the anchor-surface-trusted-timestamp on the most recent `spawn_completed` event in the parent's DAG (per I4 + P10.b compression-invariant — spawn events are CI-class so they remain in the compression-invariant set).
- Exceeding the rate → refuse `sprout_child`. Emit `reproduction_rate_exceeded` immune signal (CRITICAL per L1_HARD_RULES cascade addition C48). Substrate enters a soft-freeze on further sprout attempts pending Cultivator attestation (the Cultivator may issue a `rate_override` CI-level mutation per F22).

**Immune signal**: `reproduction_rate_exceeded` (CRITICAL per L1_HARD_RULES cascade addition C48).

### §16.C Per-substrate lifetime quota

**Default seed**: 100 children. L1-tunable per substrate purpose.

**Mechanism**:
- Pre-spawn the parent verifies `parent.children_spawned_count + 1 ≤ reproduction_lifetime_quota`.
- Quota counter source: DAG event count of `spawn_completed:{child_substrate_id}` events in parent's DAG (per I4 federation-tamper-resistant — DAG events cannot be silently retro-edited per I4 Merkle integrity).
- **Compression-invariance discipline**: the `spawn_completed` events that feed the quota counter MUST be in the compression-invariant set (P10.b) so a future compression event cannot reset the quota counter. Per DRAFT 3, the compression-invariant set includes `sprout_child_count_for_quota_verification` (canonical name: `spawn_completed` DAG events are CI-class per §1.2; CI-class events are compression-invariant per P10.b).
- Exceeding requires CI attestation per spawn (NOT bulk attestation; each over-quota spawn requires its own owner attestation). The substrate refuses bulk-attestation patterns ("Cultivator pre-authorizes next 50 spawns") — each spawn is its own §2 attestation envelope.

**Immune signal**: `reproduction_lifetime_quota_exceeded` (additional cascade addition; same grade as C48).

### §16.D Mesh-level forkbomb defense (cross-ref L2_FEDERATION)

**Threat model**: per-substrate quota is per-substrate; coordinated mesh attack from 100 compromised peers could spawn 100×100=10K children at the mesh-aggregate level even if each peer respects its own §16.C quota.

**Mechanism (cross-ref L2_FEDERATION)**:
- L2_FEDERATION specifies the mesh-aggregate quota (Cultivator-attested per population — F22's `mesh_aggregate_quota` parameter).
- Detection at the federation egress layer (per L1_SKIN §3.1 federation egress check + L2_FEDERATION egress aggregation): when aggregate spawn-rate across mesh exceeds the L2-tunable threshold, all federation peers receive `mesh_forkbomb_alert` (cross-substrate immune signal).
- Mesh-level mitigation requires Byzantine consensus per P15 (≥3 peers required; per L2_FEDERATION's consensus floor) — one peer claiming another is forkbombing is insufficient (could itself be a malicious actor).

This is the **only L1_GOVERNANCE-cascaded mechanism that crosses into L2_FEDERATION territory**; the L2_FEDERATION cascade (separate M26-cascade agent) is responsible for the Byzantine algorithm specification + the mesh-aggregate-quota numeric default.

---

## §17. Glossary additions for Cultivation (DRAFT 3 NEW)

This section defines the Cultivation-specific vocabulary integrated throughout DRAFT 3 per L0 §1.2 G-11.a + §1.4. Cross-ref L0 §12 Glossary (which contains additional DRAFT 9 vocabulary).

| Term | Definition |
|------|------------|
| **Cultivator** | The human party responsible for substrate cultivation: provides resources (compute, storage, network), signs CI mutations at the anchor surface, may transfer cultivation rights to a successor. Synonymous with "owner" in the governance role (P1.b''); "Cultivator" emphasizes the **relational role** per L0 §1.2 G-11.a, "owner" emphasizes the **governance role** per L0 §1.2. Both refer to the same human party. |
| **Cultivar** | The Myco substrate as the species under cultivation: kernel + `dag.cb` + `state_dir` (per L0 §1.2). The Cultivar is what the Cultivator cultivates; the substrate-ID identifies a specific Cultivar instance (P1.c carrier asymmetry); the Cultivar's "body" is its `state_dir + process + skin endpoints` (P13 retraction folded into P9 + I8 per L0 §I8 + L1_SKIN §12). |
| **Cultivation** | The asymmetric-care relationship between Cultivator and Cultivar (per L0 §1.2 + §1.4). Cultivation captures asymmetric care (Cultivator-provided resources bounded by P11), co-evolution (Cultivator's intent shapes Cultivar varieties; Cultivar outputs shape Cultivator understanding), and mycology-rooted vocabulary (cultivation is a real biological practice with precise technical meaning). Distinct from ownership (legal/property), custody (legalistic), curatorship (information-science). |
| **Cultivation transfer / Cultivation succession** | The transfer of Cultivation rights from one Cultivator to another (per L0 §1.4). The substrate (Cultivar) does NOT change identity across transfer; only the Cultivation relationship's Cultivator-side changes. Mechanism: §3.2 succession FSM. |
| **Successor** | A pre-attested Cultivator candidate who may accept Cultivation rights upon the prior Cultivator's heartbeat staleness (per §3.2.A). The successor's pubkey is registered in the `successor_chain` (F21). |
| **Successor_chain** | The chronologically-ordered array of `SuccessorEntry` records in the substrate's identity record (per §3.2.A). Authoritative copy at the anchor surface; substrate's local replica is advisory. F-row F21. |
| **Liveness heartbeat** | A Cultivator-signed positive presence signal at the anchor surface (per L0 §9.2.7 + §3.2.B). Cadence L1-tunable (default 30 days); validity-bounded per heartbeat (≤ L1-tunable, default 30 days); staleness drives sub-state transitions (default 90 days = 3× cadence). Anchor-surface-resident state (L1_HARD_RULES §4). |
| **Legacy (sub-state of alive)** | Sub-state entered when Cultivator's heartbeat is stale beyond threshold (per §3.2.C). Daily ops continue; CI mutations frozen except `successor_chain` mutations. Reversible if Cultivator's heartbeat returns; otherwise transitions to orphaned after `legacy_window` (default 365 days). |
| **Orphaned (sub-state of alive)** | Sub-state entered when `legacy_window` elapsed without successor acceptance OR `successor_chain` was empty at legacy entry (per §3.2.C). Daily ops continue with operational ceiling (no new schema evolution, no new federation peer pinning, no new cost-budget threshold changes, sporocarp fruiting limited to observability + mortality signals). Recovery via court-attested key recovery (exceptional, L4-deferred). Terminal transition after `orphaned_terminal_window` (default 730 days). |
| **Archived (sub-state of alive, terminal-non-destroyed)** | Sub-state entered via L0 §7.5 bet-retirement (per §3.2.C). state_dir preserved with anchor-surface `bet_retirement_seal`. No further metabolism; no resumption possible. Distinguished from `destroyed`: archived is cold-readable forensic, destroyed is final-sealed (per §4.4). |
| **Succession_acceptance_attestation** | The anchor-surface-signed envelope by which a successor accepts Cultivation rights (per §3.2.C). Triggers `alive::legacy` → `alive::normal` transition + appends successor's pubkey to `owner_key_history`. |
| **Duress_keypair** | A pre-attested Cultivator backup keypair whose signature signals coercion (per F23 + L2_TRUST_MODEL §14). The substrate's response to duress-signatures is silent observability emission while completing the attestation, so the coercer does not know the duress channel fired. |
| **Generation_depth** | The substrate's lineage depth from top-level genesis (per §16.A). Recorded in spore-schema canonical-bytes; bounded by `reproduction_lineage_depth_max` (default 10). F-row F22. |
| **Compression-invariant identity** (cross-ref L0 §12) | The compression-invariant set per L0 §P10.b — substrate-ID + genesis attestation + owner_key_history + CI-attested events + mortality signals + federation pins + most-recent-N cycles full DAG. F-row F18 specifies the compression-rule registry. |

---

## §18. Open at L1, deferred to L4 (renumbered from prior §7)

> DRAFT 2's §7 "Open at L1, deferred to L4" is renumbered §18 in DRAFT 3 to accommodate §15-§17 additions. Content updated for DRAFT 9 SEALED cascade.

- Owner key custody specific mechanism (M-anchor-1 candidate forms: hardware token, separate machine, cloud HSM, signed prompt review).
- Anchor-surface endpoint specific protocol (M-anchor-1 candidate forms).
- Idle timeout for alive → dormant (default 100 cycles; per L0 §6 + L1_CONTINUITY §2).
- Federation discovery mode (default owner-attested peer list; M-anchor-N candidates).
- Federation peer-trust freshness window (default 90 days active op).
- Federation egress rate-limit ceilings.
- Canonical-bytes serialization format (sorted-keys YAML / canonical-JSON / custom — F16 already L1-CI; choice within candidates is L4).
- Liveness heartbeat cadence default 30 days (L4 picks per substrate purpose).
- Birth period maximum duration (default 180 active-operation days).
- Cryptographic suite candidates within {SHA-256, BLAKE3, SHA-3-256, Ed25519, post-quantum candidates}.
- **§3.2 Cultivation succession parameters** (DRAFT 3 NEW):
  - Heartbeat cadence default (default 30 days; L1-tunable range L4-recommended `[1 day, 90 days]`).
  - Heartbeat validity window per issuance (default 30 days post-issuance).
  - Heartbeat staleness threshold (default 90 days = 3× cadence).
  - Legacy_window (default 365 days = 1 year).
  - Orphaned_terminal_window (default 730 days = 2 years).
  - Successor chain depth bound (default 4).
  - Anchor-surface query cadence (default 1 query per metabolic cycle or per 24h, whichever more frequent).
  - Sustained query-failure threshold for `anchor_surface_partition` (default 7 days).
  - Multi-Cultivator co-genesis (out-of-scope for v0.9; defer until first real-world need).
  - Court-attested key recovery cryptographic mechanism (currently honor-system; L4 when first real dispute arises).
  - Succession-reversion-request semantics (when prior Cultivator's heartbeat resumes post-succession; deferred to L4).
- **§16 Generation discipline parameters** (DRAFT 3 NEW):
  - Reproduction_lineage_depth (default 10).
  - Reproduction_rate_min_interval (default 24h).
  - Reproduction_lifetime_quota (default 100).
  - Mesh_aggregate_quota (L2_FEDERATION-specified; default L2_FEDERATION cascade picks).
- **F-row parameters** (DRAFT 3 NEW; per §15):
  - F18 compression-rule registry seed (each Cultivar's first compression rule set is genesis-attested; default empty per L0 §P10.c).
  - F19 cost-budget thresholds per axis (default L1-CONTINUITY + L1_SCHEMA picks per substrate cultivation-environment-resources).
  - F20 telos-alignment metric default (L1_TROPISM §F operationalizes; embedding-model identity default at genesis per Cultivar's purpose).
  - F23 duress_keypair default (default empty at genesis; Cultivator may register at genesis or via subsequent CI per L2_TRUST_MODEL §14).
- **L0 §14 adversarial-Cultivator bounded defenses** (L2 cascade ownership):
  - n-of-m multisig recommendation parameters (L2_TRUST_MODEL §14 + this document §17 glossary cross-ref).
  - Owner_signature_velocity observability thresholds (L2_TRUST_MODEL §14).
  - Anchor-client provenance independence enforcement (L0 §9.3.3; M-anchor-1).
