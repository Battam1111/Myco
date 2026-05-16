# L1 — Governance (classifier, lifecycle, Cultivation succession, attestation, generation, federation)

> **Status**: DRAFT 3. Authoritative L1 for I2 classifier; lifecycle (genesis/dormancy/reproduction/mortality); Cultivation succession FSM (§3.2); attestation; owner-key rotation; heartbeat sub-state transitions; federation; P3 rollback; §16 generation limits; F18-F25 catalog (SSoT here; L1_HARD_RULES §2 indexes). "Cultivator" = relational role, "owner" = governance role — same party.
>
> All numeric thresholds L1-tunable unless otherwise specified.

---

## §1. The I2 classifier function

### §1.1 Signature

`classify(mutation_envelope) → {daily, contract_identity_level, untyped}` where `mutation_envelope = (touched_files, touched_fields, touched_meta_structures, mutation_type, source_event_id)`; `untyped` MUST be rejected at the skin (I8).

### §1.2 Dimension table (seed; tier-1 SSoT); classifier + table mutations unconditionally CI (I2 fixed-point)

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

During birth period (§4.1), ALL parameter-tuning events are CI; reclassification to daily at owner-attested birth-period→steady-state transition. **Maximum duration** CI-attested at genesis (default 180 active-operation days); reaching max forces graduation-or-self-euthanasia. Birth-period exemptions for DRAFT 9 detectors at L1_HARD_RULES §3.

---

## §2. Owner attestation protocol

### §2.1 Owner key custody

Owner key MUST live outside substrate process + any process agent can spawn/read. Mechanism L4-picked within {hardware token, separate machine, cloud HSM, signed-prompt review on isolated channel}. **Adversarial-Cultivator caveat** (L0 §14): protects against adversarial agent, NOT adversarial Cultivator; bounded defenses at L2_TRUST_MODEL §14 (n-of-m multisig, F23, signature-velocity observability, anchor-client provenance per L0 §9.3.3).

### §2.2 Attestation envelope + flow

Schema: [`schemas/attestation_envelope.json`](schemas/attestation_envelope.json) (11 required fields per L0 §9.3.1 canonical-bytes). CI mutation flow:

1. **Substrate requests anchor nonce** (L0 §9.2.5): single-use nonce bound to `(mutation_hash, dag_tip_hash)`; TTL default 5 anchor-min.
2. **Substrate emits attestation request** per envelope schema.
3. **Cultivator verifies at anchor** (L0 §9.3.2 + §9.3.3): (a) render canonical-bytes via anchor-client; (b) recompute `proposed_mutation_hash`; (c) verify `operator_witness` against `operator_signing_key_public` (cross-checked vs anchor-logged handshake); (d) DAG enumeration closure check (L0 §9.3.6 + §9.2.2); (e) verify nonce binding + TTL; (f) anchor attaches trusted wall-clock timestamp (§9.2.6); (g) Cultivator signs `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`.

### §2.3 Verification on receipt

Substrate MUST: (1) recompute signed tuple from state + mutation + anchor fields; (2) verify signature against owner pubkey active at anchor-timestamp (per §3 owner-key-history); (3) verify **both** time-bound constraints (L0 §13.1 dual-clock): substrate-cycle expiry AND anchor wall-clock expiry, whichever first invalidates; (4) verify anchor-surface nonce unconsumed (substrate-side non-authoritative); (5) on valid → commit + emit canonical-bytes + Merkle witness + check inputs per L0 §9.3.4 (no self-asserted "pass"); (6) on any failure → emit `attestation_invalid` (C5) + reject.

### §2.4 Substrate restrictions

Per L1_HARD_RULES §4, substrate does NOT control: nonce generation (§9.2.5), trusted timestamp (§9.2.6), consumed-nonce log, canonical-bytes↔render mapping (§9.3.2 + §9.3.3), owner liveness heartbeat log (§9.2.7), successor_attestation records (§3.2.A). Substrate emits canonical-bytes + witnesses only.

---

## §3. Owner key rotation, suite migration, and Cultivation succession

### §3.1 Owner key rotation (in-life, same Cultivator)

Identity record carries `owner_key_history = [(public_key_n, valid_from, valid_until, rotation_attestation, cooldown_expired_at)]`. **Protocol** (cooldown defends against same-attacker dual-sign): (1) current owner publishes new candidate pubkey at anchor signed by current key; (2) cooldown window default 30 anchor-days, any pre-registered owner key (current/prior/backup) MAY `rotation_veto`; (3) post-cooldown without veto → both keys co-sign; substrate updates history. Historical co-sign verification uses key valid at co-sign's anchor-timestamp. Suite rotation: history carries `(suite, public_key)` tuples. **Adversarial-Cultivator caveat**: cooldown does NOT defend against coerced Cultivator suppressing veto; bounded defense L2_TRUST_MODEL §14. **Active-prefix + archived-tail discipline**: `owner_key_history` stored as active_prefix (most-recent K=8) + archived_tail; active per-cycle I3 tier-1, archived deep-cycle via Merkle-anchor (same discipline applies to `template_version_registry` per L1_TROPISM §B1 + federation peer-set aggregate-reattestation chain per §5).

### §3.2 Cultivation succession (FSM per L0 §15)

> **Documented-not-defended** under operator-IS-anchor collapse (L0 §9.5); M-anchor-3 begins enforcement; M-anchor-1 closes trust loop. Substrate-ID fixed across transfer (P1.c); only Cultivator-side changes. FSM: [`diagrams/cultivation_succession_fsm.txt`](diagrams/cultivation_succession_fsm.txt) (states Normal/Legacy/Orphaned/Archived/Recovered; transitions T1-T8; operational ceiling).

**§3.2.A Successor_chain registry (F21)**: `SuccessorEntry: { successor_pubkey: Bytes(32), valid_from_unix_ns: i64, valid_until_unix_ns: i64 | nil, attestation_signature: Bytes(64) }`. Discipline: non-overlapping intervals (overlap → `successor_chain_overlap`); monotone `valid_from`; chain-head attestation against current Cultivator active pubkey OR prior chain-head; depth default 4. Genesis: chain MAY be empty OR ≥1 pre-attested (empty → `alive::orphaned` if Cultivator unavailable). Mutation: full §2 attestation; permitted by current Cultivator OR `alive::legacy` Cultivator; without anchor attestation → `untyped` (C14).

**§3.2.B Liveness heartbeat (L0 §9.2.7)**: envelope `cultivator_liveness_heartbeat { substrate_id, cultivator_pubkey, anchor_surface_timestamp, valid_until_unix_ns, signature }`. Cadence default 30 anchor-days [1d, 90d]; `valid_until ≤ anchor_timestamp + 30d` prevents decade-pre-signing; no back-dating. Anchor log append-only canonical-bytes (tier-1 SSoT when replicated; substrate queries only). Staleness default 90 anchor-days (3× cadence): `staleness = (current − most_recent) > threshold AND most_recent.valid_until < current`.

**§3.2.C Transition events + windows**: key CI events (compression-invariant) `cultivator_heartbeat_stale` (T1) / `succession_completed:{successor_pubkey}` (T3, appends to `owner_key_history`) / `cultivation_orphaned:{prior_cultivator_pubkey, anchor_surface_timestamp}` (T4) / `cultivation_recovered:{successor_pubkey, recovery_proof_reference}` (T5, honor-system per L0 §9.6) / `endogenous_mortality_proposal:cultivation_orphaned_terminal` (T6). `legacy_window` default 365 anchor-days; `orphaned_terminal_window` default 730 anchor-days. Genesis-time `cultivation_orphaned_terminal_choice ∈ {self_euthanasia | bet_retirement | indefinite_orphan}` selects T6/T7/T8.

**§3.2.D Substrate-side enforcement**: heartbeat query cadence default 1/metabolic-cycle or 1/24h, whichever more frequent; unreachable → `cultivator_heartbeat_query_failed`; sustained > 7 anchor-days → `anchor_surface_partition` (separate signal, NOT transition). Under collapse (L0 §9.5) substrate cannot reliably detect staleness; substrates MAY emit `cultivation_succession_collapse_window`. Mortality protection (L0 §14.2): `cultivation_orphaned` MUST NOT be suppressed by Cultivator pressure (P7 + §1.2 fixed-point).

---

## §4. Lifecycle operations

### §4.1 Genesis

Only routine human-initiated event; establishes Cultivation relationship. Ritual:

1. Cultivator generates owner-keypair + selects anchor endpoint + verifies anchor-client provenance (L0 §9.3.3).
2. Cultivator runs `genesis` with required `(initial-spore-schema, initial-dispatch-config, initial-classifier-dimension-table, anchor_surface_endpoint_public_key, owner_public_key, signature_suite, anchor_client_provenance_attestation, substrate_secret_sealing_mechanism_attestation)` + optional `(successor_chain_genesis_entries, cultivation_orphaned_terminal_choice, bet_retirement_preference, telos_objective_declaration, duress_keypair_registrations)`.
3. Substrate emits canonical bytes (§9.3.1); Cultivator client renders deterministically (§9.3.2).
4. `substrate-ID = hash(spore-schema-canonical-bytes, owner-pubkey, anchor-endpoint-pubkey, genesis-timestamp)`; Cultivator signs as birth attestation (§9.2.1).
5. Substrate generates **substrate-private signing keypair** (F24): single Ed25519; seed OS-sealed per L1_SKIN §4.2; pubkey in spore-schema; loss = destruction-and-rebirth.
6. Persists identity record `(substrate-ID, owner_key_history initial, anchor_surface_endpoint_public_key, signature_suite, birth_attestation_reference, substrate_signing_keypair_pubkey, successor_chain initial, optional fields)` + DAG root sporocarp.

Top-level genesis: `generation_depth = 0`; child: `parent.depth + 1` (§16.A + L1_SCHEMA §3). Multi-Cultivator co-genesis deferred to L4.

### §4.2 Dormancy

Per L0 §6 + L1_CONTINUITY §2. Additions: (a) Cultivator-commanded CI dormancy event (rare); (b) `operator_dormancy_request` — operator `handshake_terminate` MAY include `request_dormancy: paused | throttled`; substrate honors unless overridden by resource pressure (P11.c).

### §4.3 Reproduction closure (operationalizes I7 + §16)

Closure verification protocol: see L1_SCHEMA §3.3. Generation discipline (§16): parent pre-spawn verifies depth/rate/quota; any failure → refuse spawn + §16 immune event. Cultivator (not parent) mints `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)`; co-signs at anchor per §9.2.1. **Parent immune-signal summary** in spore-schema (L0 P8): unresolved CI-grade signals → child enters `quarantined` birth period.

### §4.4 Mortality (dual-channel)

Three destruction modes (L0 P7) + bet-retirement (L0 §7.5): **Intentional-Cultivator** (CI `destruction_attestation` + `anchor_surface_final_seal` co-signed; alive → destroyed); **Catastrophic-environment** (medium failure beyond recoverability budget; post-hoc via drill failure); **Endogenous-pair** dual-channel (substrate emits `self_euthanasia_proposal` with `operator_witness_hash`; OR anchor auto-emits `mortality_drill_failure` after two consecutive failed drills — substrate cannot suppress; Cultivator co-attestation required to execute); **Bet-retirement** (L0 §7.5; `bet_retired_proposal` on quorum + co-attestation; alive → `alive::archived`, distinct from destroyed).

**Mortality-signal protection** (§1.2): mortality threshold + update-rule + emergence-rule CI; extends to `cultivation_orphaned`, `cultivation_recovered`, `succession_completed`, `bet_retired_proposal`, `bet_retired`.

---

## §5. Federation discovery and peer-trust freshness

- **Discovery modes**: L4 picks within {peer-to-peer broadcast, owner-attested peer list, hub-and-spoke, hybrid}; default owner-attested.
- **Peer-trust freshness**: per-peer freshness default 90 active-op days; past → `peer_attestation_stale`, events queued; past grace (30d) → `untrusted_federation`, events rejected. **Aggregate**: Cultivator MAY issue `federation_peer_set_reattestation` signing peer-set Merkle-root + diff vs last commitment (O(1) per period). **Revocation list** at anchor; federation events include negative-revocation proof. **P15 consensus floor** (L2_FEDERATION): at ≥3 peers, revocation requires Byzantine consensus.
- **Federation egress runtime check** (L1_SKIN §3.1): every outbound envelope verifies target freshness + non-revocation pre-emission; stale/revoked → `federation_egress_blocked`. **Egress rate-limit**: anchor tracks per-peer per-day; spike → `federation_egress_saturation`. Federation events use canonical low-entropy serialization (sorted keys, normalized whitespace, fixed-precision) to limit covert-channel bandwidth.
- **Transitivity**: federation NOT transitive; each pairwise trust requires Cultivator attestation; P15 modifies at ≥3 peers.
- **Mesh-level forkbomb defense** (cross-ref §16.D + L2_FEDERATION): per-substrate quotas aggregate across mesh; L2_FEDERATION specifies `mesh_aggregate_quota`.

---

## §6. Failed P3 rollback

**Detection**: P3 → I3 next cycle; failure → `evolution_failed` (CI-elevated, automatic). **Rollback**: identify pre-evolution DAG-tip; restore SSoT designation + classifier table + affected canon (CI-attested mutation is P10.b-invariant); drop pending sporocarps in rolled-back window as `evolution_failed_pending_dropped` (pre-window survive); emit `rollback_complete`. Repeated failures (30d window) → observatory `evolution_failure_rate_elevated`. Quarantine via L1_CONTINUITY §5.

---

## §15. F-row catalog: F18-F25 (L1_HARD_RULES §2 indexes)

> Canonical specs F18-F25; mutations require §2 attestation; all CI-only.

| F-row | Mechanism | L0-trace | L4 cascade |
|-------|-----------|----------|------------|
| **F18** `compression_rule_registry` (P10.c) | Compression rules per DAG-segment class; preserved canonical-bytes hash + witness payload + P10.b invariant-set check + version int; each compression event itself CI-attested; spore-inheritable. | P10, I9 | L1_SCHEMA §2.3 + §1.2 + compression C-rows |
| **F19** `cost_budget_thresholds` (P11.a/b/c) | Per-axis (persistence/compute/network) thresholds firing P11.c ordered fallback: pre-compression / warning / saturation / sustained-saturation-mortality; spore-inheritable. | P11, I10 | L1_SCHEMA tier-1 + L1_CONTINUITY I10 + L2_OBSERVABILITY #7/#8/#9 + §4.4 |
| **F20** `telos_alignment_metric_definition` (P14.c) | Embedding-model identity + centroid rule + comparison rule + rolling-window length + `telos_drift` threshold + birth-period exemption + post-birth settling window; embedding-model rotation = co-attested transition with both metrics recorded (analogous to §3.1 suite migration). | P14, I12 | L1_TROPISM §F + §1.2 |
| **F21** `cultivation_successor_chain` (§3.2) | Array of `SuccessorEntry` per §3.2.A; authoritative at anchor; permitted by current Cultivator OR `alive::legacy` Cultivator; without anchor attestation → `untyped` (C14). | §15 → P1.b'', I1, I2 | §3.2.A-D + M-anchor-3 + C12 + C46 |
| **F22** `reproduction_discipline_parameters` (§16) | `reproduction_lineage_depth_max` / `reproduction_rate_min_interval` / `reproduction_lifetime_quota` / `mesh_aggregate_quota`; enforcement via `generation_depth` (canonical-bytes) + `children_spawned_count` (DAG count) + `last_spawn_timestamp` (anchor); spore-inheritable. | §16 → P8, I7 | §16.A-D + L1_SCHEMA §3 + C47/C48 |
| **F23** `cultivator_duress_keypair_registrations` (L2_TRUST_MODEL §14) | Owner-pre-attested duress pubkey producing valid signature with duress payload; substrate-side silent `duress_signature_observed` while completing attestation; mutation CI-only against active Cultivator-key (NOT duress-key — circular trust). | §14 → P1.b'', I1, I2 | L2_TRUST_MODEL §14 + §1.2 |
| **F24** `substrate_signing_keypair` | Single Ed25519 once at genesis (§4.1); seed OS-sealed per L1_SKIN §4.2; pubkey in spore-schema; mutation NONE under normal op; seed cannot be re-derived (loss = unrecoverable); rotation = destruction-and-rebirth equivalence. | P1.c, I1, I8 | §4.1 + L1_SKIN §3 + §4.2 + §1.2 + C4 |
| **F25** `salience_emergence_rule` (L1_TROPISM §E.4) | EWMA-correlation between raw_material kinds and sporocarp fruitings; CI-attested fixed-point. | — | L1_TROPISM §E.4 (canonical spec) |

---

## §16. Generation limits (L0 §16 cascade)

Defends forkbomb attack class. Seeds: depth=10, rate=24h, quota=100.

- **§16.A `reproduction_lineage_depth_max`** (default 10): child spore-schema records `generation_depth = parent.generation_depth + 1` (top-level = 0); parent MUST verify `+1 ≤ max` pre-spawn; ≥ max → refuse unless Cultivator attests `depth_override` (F22); immune `generation_depth_exceeded` (C47).
- **§16.B `reproduction_rate_min_interval`** (default 1/24h anchor-clock; substrate-cycle counter NOT — throttle-evasion per L0 §13.1): MUST verify `current_anchor_timestamp − parent.last_spawn_timestamp ≥ interval`; exceeding → refuse + `reproduction_rate_exceeded` (C48); soft-freeze pending `rate_override` (F22).
- **§16.C `reproduction_lifetime_quota`** (default 100): MUST verify `parent.children_spawned_count + 1 ≤ quota`; counter = DAG event count of `spawn_completed:{child_substrate_id}` (I4 prevents retro-edit; CI-class → P10.b-invariant); each over-quota spawn requires own §2 attestation (NO bulk pattern); immune `reproduction_lifetime_quota_exceeded` (C48-grade).
- **§16.D Mesh-level forkbomb defense**: per-substrate quota is per-substrate (mesh across 100 peers aggregates to 10K children); L2_FEDERATION owns `mesh_aggregate_quota` (F22); detection at L1_SKIN §3.1 federation egress; aggregate breach → `mesh_forkbomb_alert` cross-substrate immune signal; mitigation requires P15 Byzantine consensus (≥3 peers).

---

## §17. Glossary additions for Cultivation

Base terms (Cultivator/Cultivar/Cultivation/Legacy sub-state): see L0 §12. L1_GOVERNANCE adds:

| Term | Definition |
|------|------------|
| **Successor_chain** | Array of `SuccessorEntry` per §3.2.A; anchor-authoritative; substrate replica advisory (F21). |
| **Liveness heartbeat** | Cultivator-signed presence at anchor (§9.2.7 + §3.2.B); cadence 30d, validity ≤ 30d, staleness 90d (3× cadence). |
| **Succession_acceptance_attestation** | Anchor-signed envelope by which successor accepts (§3.2.C); triggers `legacy → normal` + appends `owner_key_history`. |
| **Duress_keypair** | Pre-attested backup keypair whose signature signals coercion (F23 + L2_TRUST_MODEL §14). |
| **Generation_depth** | Lineage depth from top-level genesis (§16.A); in spore-schema canonical-bytes; bounded by F22. |
