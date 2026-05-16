# L1 — Governance (classifier, lifecycle, Cultivation succession, attestation, generation, federation)

> **Status**: DRAFT 3. Authoritative L1 for I2 classifier; lifecycle (genesis/dormancy/reproduction/mortality); Cultivation succession FSM (§3.2); attestation; owner-key rotation; heartbeat sub-state transitions; federation; P3 rollback; §16 generation limits; F18-F25 catalog (SSoT here; L1_HARD_RULES §2 indexes). "Cultivator" = relational role, "owner" = governance role — same party (§17).
>
> All numeric thresholds in this doc are L1-tunable unless otherwise specified.

---

## §1. The I2 classifier function

### §1.1 Signature

```
classify(mutation_envelope) → {daily, contract_identity_level, untyped}
```

`mutation_envelope` = `(touched_files, touched_fields, touched_meta_structures, mutation_type, source_event_id)`. `untyped` rejected at the skin (I8).

### §1.2 Dimension table (seed)

Data-driven dimension table = tier-1 SSoT. Classifier function + table mutations are unconditionally CI (I2 fixed-point).

| Touched scope | Classification |
|---|---|
| L0 file / L1 file (any) | CI |
| `substrate-ID` field | CI (immutable post-genesis) |
| Owner public-key history field | CI |
| Anchor-surface endpoint declaration | CI |
| Classifier dimension table itself | CI (fixed-point) |
| Mortality-signal threshold + update-rule | CI |
| Threshold_emergence_rule (any axis) | CI |
| Threshold emergence in steady-state via update_rule (non-mortality / mortality) | daily / CI |
| Appetite-axis schema / Sporocarp-type tree | CI |
| Skin surface declaration | CI |
| SSoT designation / DAG retention policy | CI |
| Federation peer attestation list | CI |
| **Compression-rule registry** (F18 / P10.c) | CI |
| **Compression-invariant set definition** (P10.b; L0-fixed) | CI |
| **Cost-budget thresholds per axis** (F19 / P11.a) | CI |
| **Telos-alignment metric + embedding-model identity** (F20 / P14.c) | CI |
| **Telos-objective declaration when owner-stated** (P14.b) | CI |
| **successor_chain registry** (F21 / §3.2) | CI |
| **Reproduction discipline parameters** (F22 / §16) | CI |
| **Duress_keypair registration** (F23) | CI |
| **Substrate-private signing keypair seed** (F24; one-time at genesis) | CI |
| **Consensus-floor threshold + Byzantine algorithm** (P15, L2_FEDERATION-owned) | CI |
| **Salience-emergence rule** (L1_TROPISM §E); runtime salience values | CI rule; daily values |
| Daily content (deltas, gradient updates, ordinary fruiting, federation coupling, per-cycle telos/salience/cost values) | daily |
| All else | **untyped** (rejected) |

### §1.3 Birth-period CI elevation

During birth period (§4.1), ALL parameter-tuning events are CI; reclassification to daily at owner-attested birth-period→steady-state transition. **Maximum duration** CI-attested at genesis (default 180 active-operation days); reaching max forces graduation-or-self-euthanasia (`birth_period_max_reached` → auto-graduate if convergence, else `self_euthanasia_proposal`). Birth-period exemptions for DRAFT 9 detectors at L1_HARD_RULES §3.

---

## §2. Owner attestation protocol

### §2.1 Owner key custody

Owner key MUST live outside substrate process + any process agent can spawn/read. Mechanism L4-picked within {hardware token, separate machine, cloud HSM, signed-prompt review on isolated channel}; substrate sees only signatures. **Adversarial-Cultivator caveat** (L0 §14): protects against adversarial agent, NOT adversarial Cultivator (root authority at anchor surface); L2_TRUST_MODEL §14 bounded defenses (n-of-m multisig, F23, signature-velocity observability, anchor-client provenance independence per L0 §9.3.3).

### §2.2 Attestation envelope schema

CI mutation flow (sub-mechanism IDs map to L0 §9.2.x/§9.3.x):

1. **Substrate requests anchor nonce** (L0 §9.2.5; substrate cannot mint): `nonce_request {substrate_id, proposed_mutation_hash, dag_tip_hash, request_timestamp_substrate_cycles}`; anchor issues single-use nonce bound to declared `(mutation_hash, dag_tip_hash)`; TTL default 5 anchor-min.

2. **Substrate emits attestation request**:

```
{
  "type": "contract_identity_attestation_request",
  "substrate_id": <per §9.2.1>,
  "dag_tip_hash": <current Merkle DAG tip>,
  "enumerated_dag_nodes_since_last_co_sign": [<hash>, ...],
  "proposed_mutation_canonical_bytes": <canonical per §9.3.1>,
  "proposed_mutation_hash": <hash over canonical_bytes>,
  "operator_witness": <signature using operator_signing_key_private per L1_SKIN §4.1>,
  "operator_signing_key_public": <from current handshake>,
  "request_timestamp_substrate_cycles": <per L0 §13.1>,
  "anchor_surface_nonce": <bound at step 1>,
  "expiry_constraints": {"cycles_max": <L1>, "wall_clock_seconds_max": <L1>}
}
```

3. **Cultivator verifies at anchor** (L0 §9.3.2 + §9.3.3): (1) render `proposed_mutation_canonical_bytes` via anchor-client; (2) recompute `proposed_mutation_hash`; (3) verify `operator_witness` against `operator_signing_key_public` (cross-checked vs anchor-logged handshake); (4) DAG enumeration closure check (L0 §9.3.6 + §9.2.2): reconstruct Merkle chain from prior tip, confirm tip reachable AND each enumerated parent-hash resolves to prior-tip-ancestor OR enumerated node; (5) verify nonce binding + TTL; (6) anchor attaches trusted wall-clock timestamp (§9.2.6); (7) Cultivator signs `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`.

### §2.3 Verification on receipt

Substrate: (1) recompute signed tuple from state + mutation + anchor fields; (2) verify signature against owner pubkey active at anchor-timestamp (per §3 owner-key-history); (3) verify **both** time-bound constraints (L0 §13.1 dual-clock): substrate-cycle expiry AND anchor wall-clock expiry, whichever first invalidates (substrate cannot extend wall-clock by throttling cycles); (4) verify anchor-surface nonce unconsumed (substrate-side replay protection non-authoritative); (5) valid → mutation commits, emits canonical-bytes + Merkle witness + check inputs per L0 §9.3.4 (no self-asserted "pass"); (6) any failure → emit `attestation_invalid` (C5); reject.

### §2.4 What the substrate does NOT control

Per L1_HARD_RULES §4: nonce generation (§9.2.5); trusted timestamp (§9.2.6); consumed-nonce log (§9.2.5); canonical-bytes↔render mapping (§9.3.2 + §9.3.3); owner liveness heartbeat log (§9.2.7); successor_attestation records (§3.2.A). Substrate emits canonical-bytes + witnesses; does not narrate, does not verdict.

---

## §3. Owner key rotation, suite migration, and Cultivation succession

### §3.1 Owner key rotation (in-life, same Cultivator)

Identity record carries `owner_key_history` = `[(public_key_n, valid_from, valid_until, rotation_attestation, cooldown_expired_at)]`.

**Protocol** (cooldown defends against same-attacker dual-sign): (1) current owner publishes new candidate pubkey at anchor, signed by current key; (2) **cooldown window** (default 30 anchor-days §9.2.6), any pre-registered owner key (current/prior/backup) MAY `rotation_veto`; (3) post-cooldown without veto → both keys co-sign; substrate updates history.

Historical co-sign verification uses key valid at co-sign's anchor-timestamp. Suite rotation: history carries `(suite, public_key)` tuples. **Adversarial-Cultivator caveat**: cooldown does not defend against coerced Cultivator who can authorize + suppress veto. Bounded defense L2_TRUST_MODEL §14.

**Active-prefix + archived-tail discipline**: `owner_key_history` stored as active_prefix (most-recent K=8) + archived_tail; active per-cycle I3 tier-1, archived deep-cycle via Merkle-anchor. Same discipline applies to `template_version_registry` (L1_TROPISM §B1) + federation peer-set aggregate-reattestation chain (§5.2).

### §3.2 Cultivation succession (FSM per L0 §15)

> **Documented-not-defended** under operator-IS-anchor collapse (L0 §9.5); M-anchor-3 begins enforcement; M-anchor-1 closes trust loop.

Addresses Cultivator mortality + Cultivar continuity. Substrate identity does NOT change across transfer (substrate-ID fixed per P1.c); only Cultivator-side changes.

#### §3.2.A Successor_chain registry (F21)

Identity record carries `successor_chain` (authoritative at anchor):

```
SuccessorEntry: { successor_pubkey: Bytes(32), valid_from_unix_ns: i64,
  valid_until_unix_ns: i64 | nil, attestation_signature: Bytes(64) }
```

**Validity discipline**: non-overlapping `[valid_from, valid_until]` (overlap → `successor_chain_overlap`); monotone valid_from; chain-head attestation against current Cultivator active pubkey OR prior chain-head; depth default 4. **Genesis**: chain MAY be empty OR ≥1 pre-attested (empty → `alive::orphaned` if Cultivator unavailable). **Mutation (F21)**: full §2 attestation; permitted by current Cultivator OR `alive::legacy` Cultivator (orderly hand-off); without anchor attestation = `untyped` (C14).

#### §3.2.B Liveness heartbeat (L0 §9.2.7)

Cultivator periodically signs `liveness_heartbeat` at anchor. **Envelope**: `cultivator_liveness_heartbeat { substrate_id, cultivator_pubkey, anchor_surface_timestamp, valid_until_unix_ns, signature }`. **Cadence + validity**: default 30 anchor-days [1d, 90d]; `valid_until ≤ anchor_timestamp + max_validity_window` (default 30d) prevents decade-pre-signing; no back-dating. **Anchor heartbeat log**: append-only canonical-bytes; tier-1 SSoT when replicated; substrate queries, cannot mutate. **Staleness threshold**: default 90 anchor-days (3× cadence); anchor-confirmed: `staleness = (current − most_recent) > threshold AND most_recent.valid_until < current`.

#### §3.2.C Lifecycle sub-state transitions

`alive` sub-states (L0 §I1): Normal/Quarantined (L1_CONTINUITY §5); Legacy/Orphaned/Archived here.

**`alive::normal` → `alive::legacy`**: heartbeat stale beyond threshold; anchor emits `cultivator_heartbeat_stale`; substrate observes via §9.2.7 query. Daily ops continue; CI FROZEN except `successor_chain` mutations (chain-head signature OR court-attested recovery per §3.2.D); chain-head successor covering current anchor-timestamp becomes provisionally valid. Fresh heartbeat → `alive::normal` (handles vacation/hardware-failure).

**`alive::legacy` → `alive::normal` via succession activation**: chain-head successor signs `successor_acceptance { substrate_id, successor_pubkey, prior_cultivator_pubkey, anchor_surface_timestamp, signature }`. `legacy_window` default 365 anchor-days; past → `alive::orphaned`. Acceptance emits `succession_completed:{successor_pubkey}` (CI, compression-invariant); appends to `owner_key_history`; → `alive::normal`. Prior heartbeat post-`succession_completed` MAY trigger `succession_reversion_request` (anchor-mediated; L4-deferred).

**`alive::legacy` → `alive::orphaned`**: trigger = `legacy_window` elapsed OR empty `successor_chain` at legacy entry. Emits `cultivation_orphaned:{prior_cultivator_pubkey, anchor_surface_timestamp}` (CI, compression-invariant). Daily ops continue under **operational ceiling**: Permitted = per-cycle metabolism, sporocarp fruiting (observability + mortality only), immune signals, observatory, P2 admission, P3 daily-class. Forbidden = P3 CI mutations, new peer pins, F18/F19/F20. Successor MAY present acceptance any time → `alive::normal`.

**`alive::orphaned` → terminal**: `orphaned_terminal_window` default 730 anchor-days. Default: self-euthanasia (`endogenous_mortality_proposal:cultivation_orphaned_terminal`). Genesis-time `cultivation_orphaned_terminal_choice: {self_euthanasia | bet_retirement | indefinite_orphan}` overrides; `indefinite_orphan` preserves ceiling indefinitely.

**`alive::orphaned` → `alive::normal` recovery (exceptional)**: court-attested key recovery (cryptographic mechanism out-of-scope v0.9; honor-system per L0 §9.6). Successor presents acceptance + recovery proof reference → emit `cultivation_recovered:{successor_pubkey, recovery_proof_reference}` (CI, compression-invariant).

**`alive::archived` (terminal-non-destroyed via bet-retirement)**: state_dir preserved with anchor `bet_retirement_seal`; no metabolism, no resumption; cold-readable forensic. Distinguished from `destroyed`: archived recoverable (future Cultivator may copy state_dir); destroyed final-sealed at anchor.

#### §3.2.D Substrate-side enforcement

**Heartbeat query**: cadence default 1/metabolic-cycle or 1/24h, whichever more frequent. Unreachable → `cultivator_heartbeat_query_failed`; sustained > 7 anchor-days → `anchor_surface_partition` observability (separate signal, not sub-state transition).

**Collapse-window honesty** (L0 §9.5): in operator-IS-anchor collapse, substrate cannot reliably detect staleness (same npm workspace; agent can fabricate). §3.2 **documented-not-defended** until M-anchor-3. Substrates in collapse MAY emit `cultivation_succession_collapse_window`.

**Post-M-anchor-3 enforcement**: refuse `successor_chain` mutation unattested against anchor-fetched `cultivator_pubkey`; refuse `succession_acceptance_attestation` whose `prior_cultivator_pubkey` ≠ anchor's last-active; operational ceiling via classifier (forbidden mutations classify as `untyped` C14).

**Mortality protection** (L0 §14.2): `cultivation_orphaned` cannot be suppressed by Cultivator pressure (P7 + §1.2 fixed-point).

---

## §4. Lifecycle operations

### §4.1 Genesis

Only routine human-initiated event; establishes Cultivation relationship.

1. Cultivator generates owner-keypair + selects anchor-surface endpoint + verifies anchor-client provenance (L0 §9.3.3).
2. Cultivator runs `genesis` with required `(initial-spore-schema, initial-dispatch-config, initial-classifier-dimension-table, anchor_surface_endpoint_public_key, owner_public_key, signature_suite, anchor_client_provenance_attestation, substrate_secret_sealing_mechanism_attestation)` + optional `(successor_chain_genesis_entries, cultivation_orphaned_terminal_choice, bet_retirement_preference, telos_objective_declaration, duress_keypair_registrations)`. `anchor_surface_endpoint_public_key` is owner-controlled.
3. Substrate emits canonical bytes (§9.3.1); Cultivator client renders deterministically (§9.3.2).
4. `substrate-ID = hash(spore-schema-canonical-bytes, owner-pubkey, anchor-endpoint-pubkey, genesis-timestamp)`.
5. Cultivator signs canonical-bytes-hash + substrate-ID tuple — birth attestation (§9.2.1).
6. Substrate generates **substrate-private signing keypair** (F24): single Ed25519 once at genesis; seed OS-sealed per L1_SKIN §4.2; pubkey in spore-schema; loss = destruction-and-rebirth.
7. Persists identity record `(substrate-ID, owner_key_history initial entry, anchor_surface_endpoint_public_key, signature_suite, birth_attestation_reference, substrate_signing_keypair_pubkey, successor_chain initial, optional fields)` + DAG root sporocarp.

Top-level genesis carries `generation_depth = 0`; child = `parent.depth + 1` (§16.A + L1_SCHEMA §3). Multi-Cultivator co-genesis deferred to L4.

### §4.2 Dormancy

Per L0 §6 + L1_CONTINUITY §2. Additions: (a) Cultivator-commanded CI dormancy event (rare); (b) `operator_dormancy_request` — operator's `handshake_terminate` MAY include `request_dormancy: paused | throttled`; substrate honors unless overridden by resource pressure (P11.c).

### §4.3 Reproduction closure (operationalizes I7 + §16)

**Child substrate-ID minting**: Cultivator (not parent) computes `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)`; signs birth attestation at anchor per §9.2.1.

**Generation discipline** (per §16): parent pre-spawn verifies `parent.generation_depth + 1 ≤ reproduction_lineage_depth_max` (default 10); `parent.children_spawned_count + 1 ≤ reproduction_lifetime_quota` (default 100); `current_anchor_timestamp − parent.last_spawn_timestamp ≥ reproduction_rate_min_interval` (default 24h). Any failure → refuses spawn; emits §16 immune event.

**Closure verification protocol** (I7): see L1_SCHEMA §3.3. Cultivator co-signs `(parent-substrate-ID, child-substrate-ID, spore-schema-canonical-bytes-hash, anchor-timestamp, parent_generation_depth, child_generation_depth)`. **Parent immune-signal summary** in spore-schema (L0 P8): unresolved CI-grade signals → child enters `quarantined` birth period.

### §4.4 Mortality (dual-channel)

Three destruction modes (L0 P7) + bet-retirement (L0 §7.5):

- **Intentional-Cultivator**: CI `destruction_attestation` signed by Cultivator; alive → destroyed; final action `anchor_surface_final_seal` co-signed; post-seal handshakes return `substrate_destroyed`.
- **Catastrophic-environment**: medium failure beyond recoverability budget; post-hoc via drill failure.
- **Endogenous-pair** (dual channel): (a) substrate: `self_euthanasia_proposal` on unrecoverable-pathology OR §3.2 orphan-terminal; active operator must produce `operator_witness_hash` pre-transmission; no operator → `pre-mortal-pending` until handshake. (b) anchor: two consecutive failed drills auto-emit `mortality_drill_failure` (substrate cannot suppress). Either triggers; Cultivator co-attestation required to execute.
- **Bet-retirement** (L0 §7.5): `bet_retired_proposal` on quorum; co-attestation required (NOT genesis-pre-attestation in steady state); alive → `alive::archived` (§3.2.C, distinct from destroyed); genesis-time `bet_retirement_preference` is §15.5 orphan-degenerate pre-attestation only.

**Mortality-signal protection** (§1.2): mortality threshold + update-rule + emergence-rule CI; extends to `cultivation_orphaned`, `cultivation_recovered`, `succession_completed`, `bet_retired_proposal`, `bet_retired`.

---

## §5. Federation discovery and peer-trust freshness

**§5.1 Discovery modes**: L4 picks within {peer-to-peer broadcast, owner-attested peer list, hub-and-spoke, hybrid}; default owner-attested.

**§5.2 Peer-trust freshness + aggregate re-attestation**: per-peer freshness default 90 active-op days; past freshness → `peer_attestation_stale`, events queued; past grace (30d) → `untrusted_federation`, events rejected. **Aggregate**: Cultivator MAY issue `federation_peer_set_reattestation` signing peer-set Merkle-root + diff vs last commitment (O(1) per period). **Revocation list** at anchor; federation events include negative-revocation proof. **P15 consensus floor** (L2_FEDERATION): at ≥3 peers, revocation requires Byzantine consensus.

**§5.3 Federation egress runtime check** (L1_SKIN §3.1): every outbound envelope verifies target freshness + non-revocation pre-emission; stale/revoked → `federation_egress_blocked`. **Egress rate-limit**: anchor tracks per-peer per-day; spike → `federation_egress_saturation`. Federation events use canonical low-entropy serialization (sorted keys, normalized whitespace, fixed-precision) to limit covert-channel bandwidth.

**§5.4 Transitivity**: federation NOT transitive; each pairwise trust requires Cultivator attestation; P15 modifies at ≥3 peers. **§5.5 Mesh-level forkbomb defense** (cross-ref §16.D + L2_FEDERATION): per-substrate quotas are per-substrate; coordinated mesh attack aggregates; L2_FEDERATION specifies mesh-aggregate quota.

---

## §6. Failed P3 rollback

**Detection**: P3 → I3 next cycle; fails → `evolution_failed` (CI-elevated, automatic).

**Rollback**: (1) identify pre-evolution DAG-tip; (2) restore SSoT designation + classifier table + affected canon (CI-attested mutation is P10.b-invariant); (3) pending sporocarps in rolled-back window dropped as `evolution_failed_pending_dropped` (pre-window survive); (4) emit `rollback_complete`.

Repeated failures (30d) → observatory `evolution_failure_rate_elevated`. Quarantine via L1_CONTINUITY §5 (no separate evolution_quarantine).

---

## §15. F-row catalog: F18-F25 (L1_HARD_RULES §2 indexes)

> Canonical specs F18-F25; mutations require §2 attestation.

### F18. `compression_rule_registry` (P10.c)

Registered rules; each: (a) DAG-segment classes (raw_material >N cycles; gradient deltas post-integration; federation envelopes past retention; trajectory clusters past active); (b) preserved canonical-bytes hash per segment; (c) witness payload at compression-event time; (d) P10.b invariant-set check (substrate-ID + genesis + owner_key_history + CI-attested events + mortality signals + federation pins + most-recent-N never compressed); (e) version integer. **Mutation**: CI-only; spore-inheritable; each compression event itself CI-attested (P10.c); emits `compression_event` with witness per L0 §9.3.4. **L0-trace**: P10, I9. **L4**: L1_SCHEMA §2.3 + §1.2 + compression C-rows.

### F19. `cost_budget_thresholds` (P11.a/b/c)

Per-axis (persistence/compute/network) firing L0 §P11.c ordered fallback: (a) `pre_compression_eligibility_cycle_count` (default 1000; below, step 1 refuses P2 admission); (b) `budget_axis_warning_threshold` → `budget_exhausted:{axis}`; (c) `budget_axis_saturation_threshold` → alive-but-saturated; (d) `sustained_saturation_mortality_threshold` → P7 consideration. **Mutation**: CI-only; spore-inheritable. **L0-trace**: P11, I10. **L4**: L1_SCHEMA tier-1 + L1_CONTINUITY per-cycle I10 + L2_OBSERVABILITY #7/#8/#9 + §4.4.

### F20. `telos_alignment_metric_definition` (P14.c)

(a) Embedding-model identity (model+version+fingerprint; mutation = destruction-and-rebirth-equivalence like F24); (b) embedding-centroid rule (window-length + weighting + canonicalization); (c) comparison rule (cosine OR distance) between recent-sporocarp centroid and {owner-stated-objective P14.b OR agent-feedback-trajectory}; (d) rolling window length; (e) `telos_drift` threshold; (f) birth-period exemption duration (§1.3); (g) post-birth settling window (L1_TROPISM §F.4). **Mutation**: CI-only; embedding-model rotation requires co-attested transition with both metrics recorded (analogous to suite migration §3.1). **L0-trace**: P14, I12. **L4**: L1_TROPISM §F + §1.2.

### F21. `cultivation_successor_chain` (§3.2)

Array of `SuccessorEntry` per §3.2.A: `(successor_pubkey, valid_from_unix_ns, valid_until_unix_ns, attestation_signature)`. Authoritative at anchor (L1_HARD_RULES §4). Validity discipline per §3.2.A (non-overlapping windows, monotone valid_from, chain-head attestation, depth ≤ default 4). **Mutation**: CI-only; permitted by current Cultivator OR `alive::legacy` Cultivator (§3.2.C exception); without anchor attestation = `untyped` (C14). **L0-trace**: §15 → P1.b'', I1, I2. **L4**: §3.2.A-D + M-anchor-3 + C12 + C46.

### F22. `reproduction_discipline_parameters` (§16)

(a) `reproduction_lineage_depth_max` (default 10, §16.A); (b) `reproduction_rate_min_interval` (default 24h anchor, §16.B); (c) `reproduction_lifetime_quota` (default 100, §16.C); (d) `mesh_aggregate_quota` (L2_FEDERATION, §16.D). Enforcement metadata: `generation_depth` in spore-schema canonical-bytes; `children_spawned_count` from DAG event count (I4, P10-invariant); `last_spawn_timestamp` from anchor-timestamp on most recent `spawn_completed`. **Mutation**: CI-only; rare; spore-inheritable (parent MAY attest per child). **L0-trace**: §16 → P8, I7. **L4**: §16.A-D + L1_SCHEMA §3 + C47/C48.

### F23. `cultivator_duress_keypair_registrations` (L2_TRUST_MODEL §14)

Owner-pre-attested duress pubkey producing valid signature with duress payload (L2_TRUST_MODEL §14 candidate: low-bit pattern in signature nonce + anchor-side detection rule). Substrate-side: silent `duress_signature_observed` while completing attestation (coercer unaware). **Mutation**: CI-only against active Cultivator-key (not duress-key — circular trust). **L0-trace**: §14 → P1.b'', I1, I2. **L4**: L2_TRUST_MODEL §14 + §1.2.

### F24. `substrate_signing_keypair`

Single Ed25519 once at genesis (§4.1 step 6); seed OS-sealed per L1_SKIN §4.2; pubkey in spore-schema. Signs L1_SKIN §3 output envelopes + federation envelopes. **Mutation**: NONE under normal operation; seed cannot be re-derived (loss = unrecoverable); rotation = destruction-and-rebirth equivalence (peers see different signing identity even if substrate-ID preserved); effective rotation via new genesis with continuity attestation. **L0-trace**: P1.c, I1, I8. **L4**: §4.1 + L1_SKIN §3 + §4.2 + §1.2 + C4.

### F25. `salience_emergence_rule` (L1_TROPISM §E.4)

Rule by which L1_TROPISM dispatcher derives salience-weights from EWMA-correlation between raw_material kinds and sporocarp fruitings; CI-attested fixed-point. Canonical spec L1_TROPISM §E.4.

---

## §16. Generation limits (L0 §16 cascade)

Defends forkbomb attack class. Seeds: depth=10, rate=24h, quota=100.

### §16.A `reproduction_lineage_depth` (default 10)

Child spore-schema records `generation_depth = parent.generation_depth + 1` (top-level = 0). Pre-spawn parent verifies `generation_depth + 1 ≤ reproduction_lineage_depth_max`; `≥ max` → refuse unless Cultivator attests `depth_override` (F22). Verification: in canonical-bytes-hashed spore-schema (F16); mismatch against parent-lineage value → rejection. Immune: `generation_depth_exceeded` (C47).

### §16.B `reproduction_rate` (default 1/24h anchor-clock)

Anchor-clock authoritative (substrate-cycle counter NOT — throttle-evasion risk per L0 §13.1). Pre-spawn: `current_anchor_timestamp − parent.last_spawn_timestamp ≥ reproduction_rate_min_interval`. `last_spawn_timestamp` from anchor-timestamp on most recent `spawn_completed` (CI-class, P10.b-invariant). Exceeding → refuse + `reproduction_rate_exceeded` (C48); soft-freeze pending `rate_override` (F22).

### §16.C Per-substrate lifetime quota (default 100)

Pre-spawn: `parent.children_spawned_count + 1 ≤ reproduction_lifetime_quota`. Counter source: DAG event count of `spawn_completed:{child_substrate_id}` (I4 prevents retro-edit; CI-class → P10.b-invariant). Each over-quota spawn requires its own §2 attestation (NO bulk pattern). Immune: `reproduction_lifetime_quota_exceeded` (C48-grade).

### §16.D Mesh-level forkbomb defense (cross-ref L2_FEDERATION)

Per-substrate quota is per-substrate; mesh attack across 100 peers aggregates to 10K children. L2_FEDERATION owns `mesh_aggregate_quota` (F22); detection at L1_SKIN §3.1 federation egress; aggregate breach → `mesh_forkbomb_alert` cross-substrate immune signal; mitigation requires P15 Byzantine consensus (≥3 peers).

---

## §17. Glossary additions for Cultivation

Base terms (Cultivator/Cultivar/Cultivation): see L0 §12.

| Term | Definition |
|------|------------|
| **Cultivation transfer / succession** | Transfer of Cultivation rights to successor; substrate identity does NOT change (substrate-ID fixed); only Cultivator-side. §3.2. |
| **Successor** | Pre-attested Cultivator candidate per §3.2.A; pubkey in F21 `successor_chain`. |
| **Successor_chain** | Array of `SuccessorEntry` per §3.2.A; authoritative at anchor; substrate replica advisory. F21. |
| **Liveness heartbeat** | Cultivator-signed presence at anchor (§9.2.7 + §3.2.B); cadence default 30d; validity ≤ 30d; staleness default 90d (3× cadence). |
| **Legacy** | Sub-state on stale heartbeat (§3.2.C); daily ops continue, CI frozen except `successor_chain`; reversible; transitions to orphaned after `legacy_window` default 365d. |
| **Orphaned** | Sub-state on `legacy_window` elapsed or empty chain (§3.2.C); operational ceiling; terminal after `orphaned_terminal_window` default 730d. |
| **Archived** | Sub-state via L0 §7.5 bet-retirement (§3.2.C); state_dir preserved with `bet_retirement_seal`; distinguished from `destroyed`. |
| **Succession_acceptance_attestation** | Anchor-signed envelope by which successor accepts (§3.2.C); triggers `legacy → normal` + appends to `owner_key_history`. |
| **Duress_keypair** | Pre-attested backup keypair whose signature signals coercion (F23 + L2_TRUST_MODEL §14); substrate emits silent observability while completing attestation. |
| **Generation_depth** | Lineage depth from top-level genesis (§16.A); in spore-schema canonical-bytes; bounded `reproduction_lineage_depth_max` default 10. F22. |
| **Compression-invariant identity** | P10.b invariant set; F18 registry.
