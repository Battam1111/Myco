> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L1 — Governance (classifier, lifecycle, Cultivation succession, attestation, generation, federation)

> Authoritative L1 for I2 classifier; lifecycle; Cultivation succession FSM (§3.2); attestation; key rotation; heartbeat sub-state transitions; federation; P3 rollback; §16 generation limits; F18-F25 catalog (SSoT here; L1/HARD_RULES §2 indexes). "Cultivator" = relational role, "owner" = governance role — same party. All numeric thresholds L1-tunable unless specified.

---

## §1. The I2 classifier function

**§1.1 Signature**: `classify(mutation_envelope) → {daily, contract_identity_level, untyped}` where `mutation_envelope = (touched_files, touched_fields, touched_meta_structures, mutation_type, source_event_id)`; `untyped` MUST be rejected at skin (I8).

**§1.2 Dimension table** (tier-1 SSoT; classifier + table mutations unconditionally CI per I2 fixed-point):

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
| Compression-rule registry (F18 / P10.c) | CI |
| Compression-invariant set definition (P10.b; L0-fixed) | CI |
| Cost-budget thresholds per axis (F19 / P11.a) | CI |
| Telos-alignment metric + embedding-model identity (F20 / P14.c) | CI |
| Telos-objective declaration when owner-stated (P14.b) | CI |
| successor_chain registry (F21 / §3.2) | CI |
| Reproduction discipline parameters (F22 / §16) | CI |
| Duress_keypair registration (F23) | CI |
| Substrate-private signing keypair seed (F24; one-time at genesis) | CI |
| Consensus-floor threshold + Byzantine algorithm (P15, L2/FEDERATION-owned) | CI |
| Salience-emergence rule (L1/TROPISM §E); runtime salience values | CI rule; daily values |
| Daily content (deltas, gradient updates, ordinary fruiting, federation coupling, per-cycle telos/salience/cost values) | daily |
| All else | **untyped** (rejected) |

**§1.3 Birth-period CI elevation**: During birth period (§4.1), ALL parameter-tuning CI; reclassification at owner-attested termination. Maximum duration CI-attested at genesis (default 180 active-operation days); reaching max forces graduation-or-self-euthanasia. Detector exemptions at L1/HARD_RULES §3.

---

## §2. Owner attestation protocol

**§2.1 Key custody**: Owner key MUST live outside substrate process + any process agent can spawn/read. Mechanism L4 ∈ {hardware token, separate machine, cloud HSM, signed-prompt review}.

**§2.2 Envelope + flow**: Schema [`schemas/attestation_envelope.json`](schemas/attestation_envelope.json) (11 required fields per L0/cards/AS_anchor_surface §3.8). CI flow: (1) Substrate requests anchor nonce bound to `(mutation_hash, dag_tip_hash)`; TTL 5 anchor-min. (2) Substrate emits attestation request per schema. (3) Cultivator at anchor: (a) render canonical-bytes via anchor-client; (b) recompute `proposed_mutation_hash`; (c) verify `operator_witness` against logged handshake pubkey; (d) DAG enumeration closure (L0/cards/AS_anchor_surface §3.13); (e) verify nonce binding + TTL; (f) attach trusted wall-clock; (g) sign `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`.

**§2.3 Verification on receipt**: Substrate MUST: (1) recompute signed tuple from state + mutation + anchor fields; (2) verify signature against owner pubkey active at anchor-timestamp; (3) verify dual-clock (L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics)): substrate-cycle AND anchor wall-clock expiry; (4) verify anchor nonce unconsumed (substrate-side non-authoritative); (5) on valid → commit + emit canonical-bytes + Merkle witness + check inputs (no self-asserted "pass"); (6) on failure → emit `attestation_invalid` (C5) + reject.

**§2.4 Substrate restrictions** (cross-ref L1/HARD_RULES §4): substrate does NOT control nonce generation, trusted timestamp, consumed-nonce log, canonical-bytes↔render mapping, heartbeat log, successor_attestation records. Emits canonical-bytes + witnesses only.

---

## §3. Owner key rotation, suite migration, Cultivation succession

**§3.1 Key rotation (in-life)**: Identity record carries `owner_key_history = [(public_key_n, valid_from, valid_until, rotation_attestation, cooldown_expired_at)]`. Protocol: (1) current owner publishes new candidate at anchor signed by current key; (2) cooldown 30 anchor-days, any pre-registered key MAY `rotation_veto`; (3) post-cooldown both keys co-sign; substrate updates history. Historical co-sign verification uses key valid at co-sign timestamp. Suite rotation: history carries `(suite, public_key)` tuples. **Active-prefix + archived-tail discipline**: active_prefix (most-recent K=8) per-cycle I3 tier-1; archived_tail deep-cycle via Merkle-anchor (applies to `template_version_registry` per L1/TROPISM §B1 + federation peer-set aggregate chain per §5).

**§3.2 Cultivation succession (FSM per L0/cards/COV06_no_abandonment_succession (cultivator mortality))**: Substrate-ID fixed across transfer. FSM: [`diagrams/cultivation_succession_fsm.txt`](diagrams/cultivation_succession_fsm.txt) (Normal/Legacy/Orphaned/Archived/Recovered; transitions T1-T8).

**§3.2.A Successor_chain registry (F21)**: `SuccessorEntry: { successor_pubkey: Bytes(32), valid_from_unix_ns: i64, valid_until_unix_ns: i64 | nil, attestation_signature: Bytes(64) }`. Non-overlapping intervals; monotone `valid_from`; chain-head attests against current Cultivator OR prior chain-head; depth default 4. Empty genesis → `alive::orphaned` if Cultivator unavailable. Mutation requires §2 attestation; without → `untyped` (C14).

**§3.2.B Liveness heartbeat (L0/cards/AS_anchor_surface §3.7)**: envelope `cultivator_liveness_heartbeat { substrate_id, cultivator_pubkey, anchor_surface_timestamp, valid_until_unix_ns, signature }`. Cadence 30 anchor-days [1d, 90d]; staleness 90 anchor-days (3× cadence).

**§3.2.C Transitions + enforcement**: events `cultivator_heartbeat_stale` (T1) / `succession_completed` (T3) / `cultivation_orphaned` (T4) / `cultivation_recovered` (T5) / `endogenous_mortality_proposal:cultivation_orphaned_terminal` (T6); `legacy_window` 365d / `orphaned_terminal_window` 730d; genesis `cultivation_orphaned_terminal_choice ∈ {self_euthanasia | bet_retirement | indefinite_orphan}`. Substrate heartbeat-query cadence 1/cycle or 1/24h; unreachable → `cultivator_heartbeat_query_failed`; sustained >7 anchor-days → `anchor_surface_partition`. Under collapse substrate MAY emit `cultivation_succession_collapse_window`. Mortality protection (L0/cards/P07_mortality §4 (substrate irreducible commitments)): `cultivation_orphaned` MUST NOT be suppressed.

---

## §4. Lifecycle operations

**§4.1 Genesis** — Only routine human-initiated event. Ritual: (1) Cultivator generates owner-keypair + anchor endpoint + verifies anchor-client provenance. (2) Run `genesis` with required `(initial-spore-schema, initial-dispatch-config, initial-classifier-dimension-table, anchor_surface_endpoint_public_key, owner_public_key, signature_suite, anchor_client_provenance_attestation, substrate_secret_sealing_mechanism_attestation)` + optional `(successor_chain_genesis_entries, cultivation_orphaned_terminal_choice, bet_retirement_preference, telos_objective_declaration, duress_keypair_registrations)`. (3) Substrate emits canonical bytes; Cultivator client renders deterministically. (4) `substrate-ID = hash(spore-schema-canonical-bytes, owner-pubkey, anchor-endpoint-pubkey, genesis-timestamp)`; Cultivator signs as birth attestation. (5) Substrate generates **substrate-private signing keypair** (F24): single Ed25519; seed OS-sealed per L1/SKIN §4.2; pubkey in spore-schema; loss = destruction-and-rebirth. (6) Persists identity record + DAG root sporocarp. Top-level `generation_depth = 0`; child `parent.depth + 1`.

**§4.2 Dormancy** — Per L0/cards/P04_eternal_iteration §3-§4 + L1/CONTINUITY + L1/CONTINUITY §2. Additions: Cultivator-commanded CI dormancy event (rare); `operator_dormancy_request` via `handshake_terminate` MAY include `request_dormancy: paused | throttled`; substrate honors unless overridden by resource pressure (P11.c).

**§4.3 Reproduction closure** (operationalizes I7 + §16) — Closure verification: L1/SCHEMA §3.3. Generation discipline (§16): parent pre-spawn verifies depth/rate/quota; failure → refuse + §16 immune. Cultivator mints `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)`; co-signs at anchor. Parent immune-signal summary in spore-schema: unresolved CI-grade signals → child enters `quarantined` birth period.

**§4.4 Mortality (dual-channel)** — Three modes (L0 P7) + bet-retirement (L0/cards/LB_living_bets §4 (retirement)): **Intentional-Cultivator** (CI `destruction_attestation` + `anchor_surface_final_seal` co-signed; alive → destroyed); **Catastrophic-environment** (medium failure beyond recoverability budget; post-hoc via drill failure); **Endogenous-pair** dual-channel (substrate emits `self_euthanasia_proposal` with `operator_witness_hash`; OR anchor auto-emits `mortality_drill_failure` after two consecutive failed drills — substrate cannot suppress; Cultivator co-attestation to execute); **Bet-retirement** (L0/cards/LB_living_bets §4 (retirement); `bet_retired_proposal` on quorum + co-attestation; alive → `alive::archived`). Mortality-signal protection (§1.2): mortality threshold + update-rule + emergence-rule CI; extends to `cultivation_orphaned`, `cultivation_recovered`, `succession_completed`, `bet_retired_proposal`, `bet_retired`.

---

## §5. Federation discovery + peer-trust freshness

- **Discovery**: L4 ∈ {peer-to-peer broadcast, owner-attested peer list, hub-and-spoke, hybrid}; default owner-attested.
- **Freshness**: per-peer 90 active-op days; past → `peer_attestation_stale` (queued); past grace 30d → `untrusted_federation` (rejected). Aggregate: Cultivator MAY issue `federation_peer_set_reattestation` signing Merkle-root + diff (O(1) per period). Revocation list at anchor; federation events include negative-revocation proof. P15 consensus floor (L2/FEDERATION): at ≥3 peers, revocation requires Byzantine consensus.
- **Egress runtime check** (L1/SKIN §3.1): every outbound envelope verifies target freshness + non-revocation pre-emission; stale/revoked → `federation_egress_blocked`. Rate-limit: anchor tracks per-peer per-day; spike → `federation_egress_saturation`. Events use canonical low-entropy serialization (sorted keys, normalized whitespace, fixed-precision) to limit covert-channel bandwidth.
- **Transitivity**: federation NOT transitive; each pairwise trust requires Cultivator attestation; P15 modifies at ≥3 peers.
- **Mesh-level forkbomb defense** (cross-ref §16.D): per-substrate quotas aggregate across mesh; L2/FEDERATION specifies `mesh_aggregate_quota`.

---

## §6. P3 self-evolution discipline (rollback + classes + layers)

### §6.1 Five classes of mutable substrate state (P3)

| Class | Examples | Governance | Discipline |
|---|---|---|---|
| Schema (SSoT) | Fields exist; what I3 validates | Contract-identity (F8) | Two-phase migration (L1/SCHEMA §1.3) |
| Lexicon | Subsystem / appetite / sporocarp names | Contract-identity (L0 P3) | Mycology-literature attestation; deprecation `terminal` (L0/META §9 (lexicon).1) |
| Dispatch parameters | Appetite-axis schema; sporocarp-type tree; clusterer choice | Contract-identity | P3 evolution; I3-failure rollback |
| Threshold values (steady) | Emergent fruiting; bets weights; signals | Daily-autonomous non-mortality; CI for mortality | Emergent from history (C6.4) |
| L0/L1 doctrine | This document set | Owner-attested via L0/META §7.5 (model-diversity) | Burst-detection per L0/cards/AS_anchor_surface §4 (failure modes) → `doctrine_instability` |

### §6.2 Three layers — doctrine + schema/dispatch + threshold

- **Doctrine (L0/L1)**: slowest; Cultivator-attested per L0/META §7.5 (model-diversity) + L1/* doctrine docs §4 item 3; L0 revision diffs verbatim against prior commit hash; burst-detection per L0/cards/AS_anchor_surface §4 (failure modes) (signal #2 evolution-rate; zero = stagnation/P3-weak; excessive = `doctrine_instability` → C37; detector L2/OBSERVABILITY §8).
- **Schema/dispatch (CI)**: L1/SCHEMA §1.3 two-phase migration; §2.2 dispatch-parameter evolution; I3-failure rollback per §6.4.
- **Daily threshold**: fast; daily-autonomous non-mortality; emergent per C6.4. Constraints: mortality-signal triple (threshold + update-rule + emergence-rule) CI-level; tier-1 fields cannot be daily-mutated; I3-inconsistent → §6.4 rollback.

### §6.3 Evolution invariants

- **Causal traceability (I4)**: every event DAG-recorded; pre-evolution state retained (L1/SCHEMA §2.3 cold-tier); post-evolution references prior; Merkle proves legitimacy.
- **No silent corruption (I3)**: SSoT-changing mutation passes two-phase migration: candidate alongside current; per-cycle dual-validation; mismatch → `ssot_migration_inconsistent` immune sporocarp + abort (algorithm at L1/SCHEMA §1.3).
- **Versioning carriers**: SSoT designation (L1/SCHEMA §1.3); `causal_proof_template` (L1/TROPISM §B1 `template_version_registry`); `Cluster_C` (L1/TRAJECTORY §4 — each CI mutation creates trajectory `epoch_boundary` sporocarp, queries default within-epoch); owner-key history (§3.1); signature suite. Active-prefix + archived-tail (§3.1) keeps per-cycle tier-1 cost O(K) regardless of age.

### §6.4 Failed P3 rollback

Detection: P3 → I3 next cycle; failure → `evolution_failed` (CI-elevated, automatic, ungated). Rollback: identify pre-evolution DAG-tip; restore SSoT designation + classifier table + affected canon (CI-attested mutation is P10.b-invariant); drop pending sporocarps in rolled-back window as `evolution_failed_pending_dropped`; emit `rollback_complete`. Failed schema migration / template evolution / lexicon mutation share this rollback shape; emissions under failed template marked `failed_template_emission`. Repeated failures (30d) → observatory `evolution_failure_rate_elevated`. Persistent failure ≥3 consecutive within window → quarantine per L1/CONTINUITY §5.

> **Doctrinal frame**: substrate evolves freely in steady state, disciplined at three layers — (1) doctrine: rare, owner-attested, burst-detected; (2) schema/dispatch: two-phase migration + canonical-bytes + I3-rollback; (3) threshold/parameter: emergent + mortality-protected. **Substrate that does not evolve is dead** (L0 P3); silent or arbitrary evolution violates I3/I4.

---

## §15. F-row catalog: F18-F25 (L1/HARD_RULES §2 indexes)

> Canonical specs F18-F25; mutations require §2 attestation; all CI-only.

| F-row | Mechanism | L0-trace |
|-------|-----------|----------|
| **F18** `compression_rule_registry` (P10.c) | Per DAG-segment class; preserved canonical-bytes hash + witness payload + P10.b invariant check + version int; each event CI-attested; spore-inheritable. | P10, I9 |
| **F19** `cost_budget_thresholds` (P11.a/b/c) | Per-axis (persistence/compute/network) thresholds firing P11.c ordered fallback: pre-compression / warning / saturation / sustained-saturation-mortality; spore-inheritable. | P11, I10 |
| **F20** `telos_alignment_metric_definition` (P14.c) | Embedding-model identity + centroid rule + comparison rule + rolling-window length + `telos_drift` threshold + birth-period exemption + post-birth settling; embedding-model rotation = co-attested transition with both metrics recorded. | P14, I12 |
| **F21** `cultivation_successor_chain` (§3.2) | Array of `SuccessorEntry` per §3.2.A; authoritative at anchor; permitted by current Cultivator OR `alive::legacy` Cultivator; without anchor attestation → `untyped` (C14). | §15 → P1.b'', I1, I2 |
| **F22** `reproduction_discipline_parameters` (§16) | `reproduction_lineage_depth_max` / `reproduction_rate_min_interval` / `reproduction_lifetime_quota` / `mesh_aggregate_quota`; enforcement via `generation_depth` + `children_spawned_count` (DAG count) + `last_spawn_timestamp` (anchor); spore-inheritable. | §16 → P8, I7 |
| **F23** `cultivator_duress_keypair_registrations` (L2/TRUST_MODEL §10) | Owner-pre-attested duress pubkey producing valid signature with duress payload; substrate silent `duress_signature_observed` while completing attestation; mutation CI-only against active Cultivator-key (NOT duress-key — circular trust). | §14 → P1.b'', I1, I2 |
| **F24** `substrate_signing_keypair` | Single Ed25519 once at genesis (§4.1); seed OS-sealed per L1/SKIN §4.2; pubkey in spore-schema; mutation NONE under normal op; seed cannot be re-derived; rotation = destruction-and-rebirth. | P1.c, I1, I8 |
| **F25** `salience_emergence_rule` (L1/TROPISM §E.4) | EWMA-correlation between raw_material kinds and sporocarp fruitings; CI-attested fixed-point. | — |

---

## §16. Generation limits (L0/cards/P08_eternal_reproduction (generation limits) cascade)

Defends forkbomb attack class. Seeds: depth=10, rate=24h, quota=100.

- **§16.A `reproduction_lineage_depth_max`** (default 10): child spore-schema records `generation_depth = parent.generation_depth + 1`; parent verifies `+1 ≤ max` pre-spawn; ≥ max → refuse unless Cultivator attests `depth_override` (F22); immune `generation_depth_exceeded` (C47).
- **§16.B `reproduction_rate_min_interval`** (default 1/24h anchor-clock; substrate-cycle counter NOT — throttle-evasion per L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics)): verify `current_anchor_timestamp − parent.last_spawn_timestamp ≥ interval`; exceeding → refuse + `reproduction_rate_exceeded` (C48); soft-freeze awaiting `rate_override` (F22).
- **§16.C `reproduction_lifetime_quota`** (default 100): verify `parent.children_spawned_count + 1 ≤ quota`; counter = DAG event count of `spawn_completed:{child_substrate_id}` (I4 prevents retro-edit; CI-class → P10.b-invariant); each over-quota spawn requires own §2 attestation (NO bulk); immune `reproduction_lifetime_quota_exceeded` (C48-grade).
- **§16.D Mesh forkbomb**: per-substrate quota local (mesh across 100 peers aggregates to 10K children); L2/FEDERATION owns `mesh_aggregate_quota`; detection at L1/SKIN §3.1 federation egress; aggregate breach → `mesh_forkbomb_alert`; mitigation requires P15 Byzantine consensus (≥3 peers).

---

