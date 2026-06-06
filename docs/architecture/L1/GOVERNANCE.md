> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L1 — Governance (classifier, lifecycle, Cultivation succession, attestation, generation, federation)

> Authoritative L1 for I2 classifier; lifecycle; Cultivation succession FSM (§3.2); CI approval at the live human-in-the-loop gate; federation; P3 rollback; §16 generation limits; F18-F25 catalog (SSoT here; L1/HARD_RULES §2 indexes). *(Keyless v3.1.5: owner key rotation + the anchor liveness-heartbeat sub-state machinery are retired — see §3.)* "Cultivator" = relational role; the prior separate "owner" governance role collapses into it (no owner key). All numeric thresholds L1-tunable unless specified.

---

## §1. The I2 classifier function

**§1.1 Signature**: `classify(mutation_envelope) → {daily, contract_identity_level, untyped}` where `mutation_envelope = (touched_files, touched_fields, touched_meta_structures, mutation_type, source_event_id)`; `untyped` MUST be rejected at skin (I8).

**§1.2 Dimension table** (tier-1 SSoT; classifier + table mutations unconditionally CI per I2 fixed-point):

| Touched scope | Classification |
|---|---|
| L0 file / L1 file (any) | CI |
| `substrate-ID` field | CI (immutable post-genesis) |
| ~~Owner public-key history field~~ | **removed v3.1.5 (owner key retired)** |
| ~~Anchor-surface endpoint declaration~~ | **removed v3.1.5 (anchor surface retired)** |
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
| ~~Duress_keypair registration (F23)~~ | **removed v3.1.5 (duress keypair retired)** |
| Substrate-private signing keypair seed (F24; one-time at genesis; KEPT — substrate's own keypair) | CI |
| Consensus-floor threshold + Byzantine algorithm (P15, L2/FEDERATION-owned) | CI |
| Salience-emergence rule (L1/TROPISM §E); runtime salience values | CI rule; daily values |
| Daily content (deltas, gradient updates, ordinary fruiting, federation coupling, per-cycle telos/salience/cost values) | daily |
| All else | **untyped** (rejected) |

**§1.3 Birth-period CI elevation**: During birth period (§4.1), ALL parameter-tuning CI; reclassification at termination approved at the live CI gate. Maximum duration set at genesis (default 180 active-operation days); reaching max forces graduation-or-self-euthanasia. Detector exemptions at L1/HARD_RULES §3.

---

## §2. CI approval protocol (keyless v3.1.5 — was "Owner attestation protocol")

> *(Keyless v3.1.5: the owner Ed25519 key + the out-of-band anchor surface — nonces, trusted wall-clock, owner-signature verification, the duress keypair — are retired. CI approval is now exercised by a **live human-in-the-loop at the CI gate**, and CI integrity rests on the keyless triad: the live human + the causal DAG (P06) + the BLAKE3-sealed bundle. The substrate still emits **witnesses, not verdicts** — the human re-derives the verdict at the gate.)*

**§2.1 No key custody (retired)**: there is no owner key to custody. The prior requirement (owner key outside the substrate process; L4 ∈ {hardware token, separate machine, cloud HSM, signed-prompt review}) is removed. The substrate's own signing keypair (F24) is OS-sealed and signs only the substrate's own snapshot.cb + federation hello — it is NOT an owner key and does not gate CI.

**§2.2 CI flow (keyless)**: (1) The substrate's I2 classifier elevates a CI-scope mutation; (2) the substrate emits the proposed mutation as canonical-bytes (F16) + a Merkle witness + DAG-enumeration closure (the verifier re-derives, the substrate does not self-assert "pass"); (3) the **cultivator reviews at the live human-in-the-loop CI gate** — renders the canonical-bytes deterministically, re-derives `proposed_mutation_hash`, confirms DAG-tip + enumeration closure — and **approves or rejects in the loop**. There is no nonce, no owner signature, no trusted-wall-clock stamp.

**§2.3 Verification on receipt (keyless)**: Substrate MUST: (1) re-derive the mutation hash from state + mutation; (2) verify the change matches what was approved at the live CI gate; (3) verify the DAG-tip is current (substrate-cycle ordering; no anchor wall-clock); (4) on valid → commit + emit canonical-bytes + Merkle witness + check inputs (no self-asserted "pass"); (5) on a malformed/unapproved CI envelope → emit `attestation_invalid` (C5, now keyless local content-validation) + reject.

**§2.4 Substrate restrictions** (cross-ref L1/HARD_RULES §4, retired): the prior list (substrate does NOT control nonce generation / trusted timestamp / consumed-nonce log / canonical-bytes↔render mapping / heartbeat log / successor_attestation records) is mostly moot — those anchor-resident artifacts no longer exist. What remains: the substrate emits canonical-bytes + witnesses only, and does NOT self-author CI-class fixed-points; the gate is a present human (META §7.8), not the substrate.

---

## §3. Cultivation succession (keyless v3.1.5 — owner key rotation + suite migration retired)

**§3.1 Owner key rotation — RETIRED v3.1.5**: there is no owner key, so there is no key rotation, no `owner_key_history`, no 30-day cooldown veto window (C70, retired), no suite migration. This entire sub-protocol is removed with the anchor surface. (The active-prefix + archived-tail discipline it described still applies to the *other* registries that use it — `template_version_registry` per L1/TROPISM §B1 + the federation peer-set aggregate chain per §5 — independent of any owner key.)

**§3.2 Cultivation succession (FSM per L0/cards/COV06_no_abandonment_succession.md (cultivator mortality))**: Substrate-ID fixed across transfer. FSM: [`diagrams/cultivation_succession_fsm.txt`](../diagrams/cultivation_succession_fsm.txt) (Normal/Legacy/Orphaned/Archived/Recovered; transitions T1-T8).

**§3.2.A Successor_chain registry (F21, keyless)**: `SuccessorEntry: { successor_pubkey: Bytes(32), valid_from_unix_ns: i64, valid_until_unix_ns: i64 | nil }`. Non-overlapping intervals; monotone `valid_from`; depth default 4. Empty genesis → `alive::orphaned` if Cultivator unavailable. Mutation requires CI approval at the live human-in-the-loop gate; without → `untyped` (C14). *(Keyless v3.1.5: the prior `attestation_signature: Bytes(64)` owner-signature field is removed; succession's only gate is the C46 catechumenate-session floor — ≥50 dual-confirmed sessions — verified by `substrate/src/cultivation.rs::handle_accept_succession`. `successor_pubkey` is retained as the successor's identity handle, not an owner-signature verifier.)*

**§3.2.B Liveness heartbeat — RETIRED v3.1.5 (acknowledged-debt)**: the prior `cultivator_liveness_heartbeat` envelope (owner-signed, anchor-stamped) is removed with the anchor surface. Keyless mode has **no trusted wall-clock**, so a heartbeat-staleness *auto-detection* cannot be done securely (the substrate must not trust its own clock for a security-bearing timeout). The cultivator's **duty** of presence at sustainable cadence stands (COV06 §3.1); the *auto-detection* is acknowledged-debt (COV06 §8.5) until a trusted-time source returns.

**§3.2.C Transitions + enforcement (keyless)**: events `succession_completed` (T3) / `cultivation_orphaned` (T4) / `cultivation_recovered` (T5) / `endogenous_mortality_proposal:cultivation_orphaned_terminal` (T6); `legacy_window` 365d / `orphaned_terminal_window` 730d; genesis `cultivation_orphaned_terminal_choice ∈ {self_euthanasia | bet_retirement | indefinite_orphan}`. *(Keyless v3.1.5: the `cultivator_heartbeat_stale` (T1) auto-transition + the substrate heartbeat-query / `anchor_surface_partition` machinery are retired with the anchor heartbeat — see §3.2.B acknowledged-debt; `alive::orphaned` is now established by a human-in-the-loop, e.g. a pre-named contact, rather than auto-timed.)* Mortality protection (L0/cards/P07_mortality.md §4): `cultivation_orphaned` MUST NOT be suppressed — the un-suppressibility is enforced keyless by **C69** (`c69_cultivation_orphaned_suppression_refused`).

---

## §4. Lifecycle operations

**§4.1 Genesis (keyless v3.1.5)** — Only routine human-initiated event. Ritual: (1) Cultivator prepares the genesis inputs (no owner-keypair / anchor endpoint / anchor-client provenance to generate). (2) Run `genesis` with required `(initial-spore-schema, initial-dispatch-config, initial-classifier-dimension-table, substrate_secret_sealing_mechanism_attestation)` + optional `(successor_chain_genesis_entries, cultivation_orphaned_terminal_choice, bet_retirement_preference, telos_objective_declaration)`. *(Keyless: the prior required `anchor_surface_endpoint_public_key` / `owner_public_key` / `signature_suite` / `anchor_client_provenance_attestation` and the optional `duress_keypair_registrations` are removed.)* (3) Substrate emits canonical bytes; the cultivator reviews deterministically at the live CI gate. (4) `substrate-ID = hash(spore-schema-canonical-bytes, genesis-timestamp)` *(keyless: owner-pubkey + anchor-endpoint inputs dropped)*; there is no owner-signed birth attestation (C20 retired). (5) Substrate generates **substrate-private signing keypair** (F24, KEPT): single Ed25519; seed OS-sealed per L1/SKIN §4.2; pubkey in spore-schema; loss = destruction-and-rebirth. (6) Persists identity record + DAG root sporocarp. Top-level `generation_depth = 0`; child `parent.depth + 1`.

**§4.2 Dormancy** — Per L0/cards/P04_eternal_iteration.md §3-§4 + L1/CONTINUITY + L1/CONTINUITY §2. Additions: Cultivator-commanded CI dormancy event (rare); `operator_dormancy_request` via `handshake_terminate` MAY include `request_dormancy: paused | throttled`; substrate honors unless overridden by resource pressure (P11.c).

**§4.3 Reproduction closure** (operationalizes I7 + §16) — Closure verification: L1/SCHEMA §3.3. Generation discipline (§16): parent pre-spawn verifies depth/rate/quota; failure → refuse + §16 immune. `child-substrate-ID = hash(parent-substrate-ID, spore-schema-canonical-bytes-hash, child-genesis-timestamp)` is derived deterministically; the cultivator co-approves the spawn at the live CI gate via the `myco-spawn-cosign-v1` envelope (C68 gate; keyless — no owner signature). Parent immune-signal summary in spore-schema: unresolved CI-grade signals → child enters `quarantined` birth period.

**§4.4 Mortality (keyless v3.1.5 — single live whole-death channel)** — Three modes (L0 P7) + bet-retirement (L0/cards/LB_living_bets.md §4 (retirement)): **Intentional-Cultivator** (cultivator co-approves at the live CI gate — accepts a `self_euthanasia_proposal` node; final tip sealed by the BLAKE3 at-rest seal F5; alive → destroyed); **Catastrophic-environment** (medium failure beyond recoverability budget; post-hoc); **Endogenous-pair** (substrate emits `self_euthanasia_proposal`; Cultivator co-approves at the live CI gate to execute — `handle_accept_self_euthanasia_proposal`). *(Keyless v3.1.5: the prior second sub-channel — an anchor auto-emitted `mortality_drill_failure` the substrate "cannot suppress" — is removed with the anchor surface; there is no keyless trusted auto-emitter. The MUST-NOT against silent self-destruction is preserved keyless at P07 §5.8.)* **Bet-retirement** (L0/cards/LB_living_bets.md §4; `bet_retired_proposal` on quorum + co-approval at the live CI gate; alive → `alive::archived`). Mortality-signal protection (§1.2): mortality threshold + update-rule + emergence-rule CI; extends to `cultivation_orphaned`, `cultivation_recovered`, `succession_completed`, `bet_retired_proposal`, `bet_retired`.

---

## §5. Federation discovery + peer-trust freshness

- **Discovery**: L4 ∈ {peer-to-peer broadcast, cultivator-attested peer list, hub-and-spoke, hybrid}; default cultivator-attested (at the live CI gate; keyless).
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
| L0/L1 doctrine | This document set | Approved at the live CI gate via L0/META §7.5 (model-diversity) + the BLAKE3-sealed bundle (keyless v3.1.5) | Burst-detection (L2/OBSERVABILITY §8) → `doctrine_instability` (C37) |

### §6.2 Three layers — doctrine + schema/dispatch + threshold

- **Doctrine (L0/L1)**: slowest; approved at the live CI gate per L0/META §7.5 (model-diversity) + L1/* doctrine docs §4 item 3; L0 revisions sealed as the BLAKE3 bundle hash chained in PROVENANCE §6 (keyless v3.1.5; verbatim against prior bundle hash); burst-detection (signal #2 evolution-rate; zero = stagnation/P3-weak; excessive = `doctrine_instability` → C37; detector L2/OBSERVABILITY §8).
- **Schema/dispatch (CI)**: L1/SCHEMA §1.3 two-phase migration; §2.2 dispatch-parameter evolution; I3-failure rollback per §6.4.
- **Daily threshold**: fast; daily-autonomous non-mortality; emergent per C6.4. Constraints: mortality-signal triple (threshold + update-rule + emergence-rule) CI-level; tier-1 fields cannot be daily-mutated; I3-inconsistent → §6.4 rollback.

### §6.3 Evolution invariants

- **Causal traceability (I4)**: every event DAG-recorded; pre-evolution state retained (L1/SCHEMA §2.3 cold-tier); post-evolution references prior; Merkle proves legitimacy.
- **No silent corruption (I3)**: SSoT-changing mutation passes two-phase migration: candidate alongside current; per-cycle dual-validation; mismatch → `ssot_migration_inconsistent` immune sporocarp + abort (algorithm at L1/SCHEMA §1.3).
- **Versioning carriers**: SSoT designation (L1/SCHEMA §1.3); `causal_proof_template` (L1/TROPISM §B1 `template_version_registry`); `Cluster_C` (L1/TRAJECTORY §4 — each CI mutation creates trajectory `epoch_boundary` sporocarp, queries default within-epoch). *(Keyless v3.1.5: owner-key history + signature suite are retired as versioning carriers.)* The active-prefix + archived-tail discipline (formerly §3.1) keeps per-cycle tier-1 cost O(K) regardless of age for `template_version_registry` + the federation peer-set aggregate chain.

### §6.4 Failed P3 rollback

Detection: P3 → I3 next cycle; failure → `evolution_failed` (CI-elevated, automatic, ungated). Rollback: identify pre-evolution DAG-tip; restore SSoT designation + classifier table + affected canon (CI-attested mutation is P10.b-invariant); drop pending sporocarps in rolled-back window as `evolution_failed_pending_dropped`; emit `rollback_complete`. Failed schema migration / template evolution / lexicon mutation share this rollback shape; emissions under failed template marked `failed_template_emission`. Repeated failures (30d) → observatory `evolution_failure_rate_elevated`. Persistent failure ≥3 consecutive within window → quarantine per L1/CONTINUITY §5.

> **Doctrinal frame**: substrate evolves freely in steady state, disciplined at three layers — (1) doctrine: rare, approved at the live CI gate + BLAKE3-bundle-sealed, burst-detected; (2) schema/dispatch: two-phase migration + canonical-bytes + I3-rollback; (3) threshold/parameter: emergent + mortality-protected. **Substrate that does not evolve is dead** (L0 P3); silent or arbitrary evolution violates I3/I4.

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
| ~~**F23** `cultivator_duress_keypair_registrations`~~ | **DELETED v3.1.5** — the duress keypair is retired with the anchor surface. The residual coercion risk (a coerced human at the live CI gate) is named as acknowledged-debt at D-0047 / L2/TRUST_MODEL §10.A.4; there is no cryptographic duress detector. | — |
| **F24** `substrate_signing_keypair` (KEPT keyless — the substrate's OWN keypair, NOT the owner key) | Single Ed25519 once at genesis (§4.1); seed OS-sealed per L1/SKIN §4.2; pubkey in spore-schema; signs the substrate's own snapshot.cb + federation hello; mutation NONE under normal op; seed cannot be re-derived; rotation = destruction-and-rebirth. | P1.c, I1, I8 |
| **F25** `salience_emergence_rule` (L1/TROPISM §E.4) | EWMA-correlation between raw_material kinds and sporocarp fruitings; CI-attested fixed-point. | — |

---

## §16. Generation limits (L0/cards/P08_eternal_reproduction.md (generation limits) cascade)

Defends forkbomb attack class. Seeds: depth=10, rate=24h, quota=100.

- **§16.A `reproduction_lineage_depth_max`** (default 10): child spore-schema records `generation_depth = parent.generation_depth + 1`; parent verifies `+1 ≤ max` pre-spawn; ≥ max → refuse unless Cultivator attests `depth_override` (F22); immune `generation_depth_exceeded` (C47).
- **§16.B `reproduction_rate_min_interval`** (default 1/24h anchor-clock; substrate-cycle counter NOT — throttle-evasion per L0/cards/P06_eternal_causality.md + L1/CONTINUITY (time semantics)): verify `current_anchor_timestamp − parent.last_spawn_timestamp ≥ interval`; exceeding → refuse + `reproduction_rate_exceeded` (C48); soft-freeze awaiting `rate_override` (F22).
- **§16.C `reproduction_lifetime_quota`** (default 100): verify `parent.children_spawned_count + 1 ≤ quota`; counter = DAG event count of `spawn_completed:{child_substrate_id}` (I4 prevents retro-edit; CI-class → P10.b-invariant); each over-quota spawn requires own §2 attestation (NO bulk); immune `reproduction_lifetime_quota_exceeded` (C48-grade).
- **§16.D Mesh forkbomb**: per-substrate quota local (mesh across 100 peers aggregates to 10K children); L2/FEDERATION owns `mesh_aggregate_quota`; detection at L1/SKIN §3.1 federation egress; aggregate breach → `mesh_forkbomb_alert`; mitigation requires P15 Byzantine consensus (≥3 peers).

---

