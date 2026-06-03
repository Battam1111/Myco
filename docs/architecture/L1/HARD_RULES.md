> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L1 — Hard Rules (cross-cuts index)

> Tier-2 SSoT cross-cuts index over L1/SKIN/L1/CONTINUITY/L1/GOVERNANCE/L1/SCHEMA/L1/TROPISM/L1/TRAJECTORY. Every row cites ≥1 P + ≥1 I.

---

## §1. CRITICAL-grade breaches (auto-quarantine triggers)

CRITICAL breach MUST immediately transition substrate to `alive::quarantined` (L1/CONTINUITY §5) + emit named immune sporocarp; resumption REQUIRES Cultivator-attested `quarantine_clearance`.

### §1.1 L1 spec catalog rows (C1-C20); status key: **L** live / **U** unimplemented / **R** reserved

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace | Status |
|---|---|---|---|---|---|---|
| C1 | `appetite_locality_breach` | L1/SKIN §5 | Network-egress outside declared output endpoints | P2.a, P9 | I6, I8 | **U** |
| C2 | `output_endpoint_breach` | L1/SKIN §3 + §6 | Output to non-declared endpoint | P9.a, P2.a | I8, I6 | **R** |
| C3 | `post_handshake_ci_unattested` | L1/SKIN §4.3 | CI during post-handshake quarantine without fresh attestation | P1.b'' | I2, I8 | **U** |
| C4 | `substrate_secret_unsealed` | L1/SKIN §4.2 | substrate_secret in process address space | P1.c, P1.a | I1 | **U** |
| C5 | `attestation_invalid` | L1/GOVERNANCE §2.3 | Signature fails OR nonce reuse OR dual-clock expiry | P1.b'' | I2 | **L** |
| C6 | `dag_enumeration_unclosed` | L1/SCHEMA §2.2 | Enumerated DAG-node parent-hash fails closure | P6, P3 | I4 | **L** |
| C7 | `dag_retro_edit_detected` | L1/SCHEMA §2.1 | Merkle DAG node hash mismatch on re-computation | P6 | I4 | **L** |
| C8 | `ssot_migration_phase_skip` | L1/SCHEMA §1.3 | Single-step SSoT migration without dual-validation | P3 | I3 | **U** |
| C9 | `cold_resume_invariant_failure` | L1/CONTINUITY §3.1 | I1/I3/I4/I5/I8/I9/I10 pre-handshake re-derivation fails | P1.c, P3, P9 | I3, I4, I5, I8, I9, I10 | **L** |
| C10 | `agent_discriminating_attribute_persisted` | L1/SCHEMA §3.1 + L1/SKIN §4.2 | Persistent model-name / API-fingerprint / operator-token | P1.c | I1 | **U** |
| C11 | `concurrent_operator_persistent` | L1/SKIN §4.4 | Two operator-tokens simultaneously valid beyond FIFO | P1.c | I8 | **U** |
| C12 | `successor_activation_with_fresh_owner_heartbeat` | L1/GOVERNANCE §3.2 | Successor activation while heartbeat fresh | P1.b'' | I1, I2 | **L** |
| C13 | `peer_attestation_revoked_egress` | L1/GOVERNANCE §5 + L1/SKIN §3.1 | Egress to peer on anchor revocation list | P8 | I7 | **L** |
| C14 | `untyped_mutation` | L1/GOVERNANCE §1.1 | I2 classifier returns `untyped` | P1.b'/P1.b'' | I2 | **L** |
| C15 | `classifier_fixed_point_bypass` | L1/GOVERNANCE §1.2 | Mutation of classifier table/function via non-CI | P1.b'' | I2 | **U** |
| C16 | `mortality_signal_suppression` | L1/GOVERNANCE §4.4 + L1/TROPISM §B2 | Mortality threshold/update-rule mutated via non-CI | P7 | I1, I2 | **U** |
| C17 | `operator_witness_forgery` | L1/GOVERNANCE §2.2 | `operator_witness` does not verify against logged handshake pubkey | P1.c | I1, I2 | **L** |
| C18 | `canonical_bytes_render_drift` | L0/cards/AS_anchor_surface.md §3.8 + §9.3.2 | Anchor-client render hash diverges from substrate signed hash | P1.b'' | I2 | **L** |
| C19 | `paused_dormancy_unsafe_host` | L1/CONTINUITY §2.4 + §3.2 | Process terminated during paused dormancy | P7, P1.c | I1 | **R** |
| C20 | `genesis_attestation_chain_broken` | L1/GOVERNANCE §4.1 + L0/cards/AS_anchor_surface.md §3.1 | Substrate-ID birth attestation does not verify | P1.a | I1 | **L** |

Rows INDEPENDENT (I2 fixed-point). Coverage: README §Status + L3/PACKAGE_MAP.md.

**Implementation notes** (rows now **L**):
- **C12** — emit: `substrate/src/cultivation.rs::handle_accept_succession` (fresh-heartbeat + misdeclared-prior gates); negative-witness: `substrate/src/cultivation.rs::tests::succession_with_fresh_heartbeat_rejected_c12` (+ `…::succession_with_misdeclared_prior_pubkey_rejected_c12`). The §1.2 C46 catechumenate gate fires ahead of C12; e2e succession paths in `substrate/tests/e2e_cultivation.rs` pass C12 with a stale heartbeat by construction.
- **C13** — emit: `substrate/src/federation/handlers.rs` (egress block + ingest refusal) + `substrate/src/server/autonomous.rs` (autonomous poll); negative-witness: `substrate/tests/e2e_revocation.rs::c13_attested_revoke_emits_crl_event_and_blocks_egress` (+ `…::c13_ingest_from_revoked_peer_refused_and_survives_restart`, `…::c13_unattested_revoke_rejected_with_c5`, `…::c13_re_revoke_is_idempotent`).

### §1.2 Substrate-private catalog rows (C30+); C21-C29 reserved

| # | Breach name | Detection site | L0 trace | I trace | Status |
|---|---|---|---|---|---|
| C30 | `handshake_pubkey_mismatch` | L1/SKIN §4.1 | P1.c | I1, I8 | **L** |
| C31 | `cycle_step_failed` | L1/CONTINUITY §1.1 | P3, P6 | I3, I4 | **L** |
| C32 | `substrate_state_orphan_detected` | L1/SCHEMA §2.5 | P5 | I4, I5 | **L** |
| C33 | `federation_peer_identity_mismatch` | L2/FEDERATION §6 + L1/SKIN §3 | P8 | I7 | **L** |
| C34 | `birth_period_violation_during_quarantine` | L1/TROPISM §4 + L1/CONTINUITY §5 | P1.b'', P7 | I2 | **L** |
| C35 | `federation_substrate_private_event_injection` | L2/FEDERATION §6 + L1/SKIN §3 | P8, P1.c | I7, I8 | **L** |
| C36 | `cycle_backlog` | L1/CONTINUITY §1.2 | P11 | I10 | **L** |
| C37 | `doctrine_instability_burst` | L1/GOVERNANCE §6 + L0/cards/AS_anchor_surface.md §4 (failure modes) + L2/OBSERVABILITY §8 | P3 | I2, I4 | **L** |
| C38 | `snapshot_integrity_violation` | L1/SCHEMA §4 | P1.c, P6 | I1, I4 | **L** |
| C39 | `federation_hello_signature_invalid` | L2/FEDERATION §6 + §6.2 | P8, P1.c | I7 | **L** |
| C40 | `bet_weakening_quorum` | L0/cards/LB_living_bets.md §3 (falsifiability quorum) + L2/OBSERVABILITY §3 | P14 | I12 | **L** |
| C41 | `dag_cb_integrity_violation` | L1/SCHEMA §2.1 + L0/cards/AS_anchor_surface.md §4 (failure modes) | P1.c, P6, P10 | I4, I9 | **L** |
| C42 | `manifest_cb_integrity_violation` | L1/SCHEMA §4 | P1.c, P6 | I1, I4 | **L** |
| C43 | `federation_recursive_injection` | L2/FEDERATION §6 + L1/SKIN §3 | P8, P1.c | I7, I8 | **L** |
| C44 | `nonce_substrate_minted_replay` | L1/GOVERNANCE §2.2 + L0/cards/AS_anchor_surface.md §3.5 | P1.b'' | I2 | **L** |
| C45 | `substrate_id_low_entropy_collision` | L1/GOVERNANCE §4.1 + L0/cards/AS_anchor_surface.md §3.1 | P1.a | I1 | **U** |
| C46 | `owner_succession_bypass` | L1/GOVERNANCE §3.2 | P1.b'', P7 | I1, I2 | **L** |
| C47 | `generation_depth_exceeded` | L1/GOVERNANCE §16.A | P8 | I7 | **U** |
| C48 | `reproduction_rate_exceeded` | L1/GOVERNANCE §16.B | P8 | I7 | **U** |
| C49 | `consensus_floor_bypass` | L2/FEDERATION §6.5 | P8, P5 | I7 | **L** |
| C50 | `coerced_owner_suspected` | L2/TRUST_MODEL §10.A.2 | P1.b'' | I1, I2 | **L** |
| C51 | `compression_invariant_corruption` | L1/SCHEMA §2.5 | P10 | I9 | **L** |
| C52 | `compression_uncattested` | L1/SCHEMA §2.5 + P10.c | P10 | I9 | **L** |
| C53 | `budget_exhausted_silent` | L1/SCHEMA §4.1 | P11 | I10 | **L** |
| C61 | `federation_protocol_version_mismatch` | L2/FEDERATION §10 (FED_HELLO) | P8, P1.c | I7 | **L** |
| C66 | `schema_migration_window_exceeded` | L1/SCHEMA §1.3 + P03 §10.4 | P3 | I3 | **L** |
| C68 | `reproduction_unattested_spawn` | L0/cards/P08 §5.1 + L1/SCHEMA §3.3 (I7) | P8, P1.b'' | I7, I2 | **L** |
| C69 | `cultivation_orphaned_suppression_attempted` | L1/GOVERNANCE §1 (classifier) + COV06 §5.5 | P7, COV06 | I2 | **L** |
| C70 | `rotation_veto_window_violation` | L1/GOVERNANCE §3.1 + L0/cards/AS_anchor_surface.md §3.3 | P1.b'', P1.c | I1, I2 | **L** |
| C74 | `p02_ingestion_starvation` | L0/cards/P02 §8.1 + L1/CONTINUITY (metabolic cycle) | P2, P11 | I9, I10 | **L** |
| C75 | `cultivator_fiduciary_strain` | META §7.7 + COV01 §3.5/§4.4 | P14, COV01 | I12 | **L** (informational/meta — see §1.3) |

**Implementation notes** (rows promoted/added here; all emit via `emit_immune_sporocarp` + carry a §5.4 reverse-comment):
- **C61** — emit: `substrate/src/federation/handlers.rs` (`fed_hello` reject) + `substrate/src/server/autonomous.rs` (autonomous dial); negative-witness: `substrate/tests/e2e_federation.rs::sprint_5h_federation_hello_version_mismatch_rejected_with_c61`. (Previously firing-but-undocumented; the §1.5 C57-block note is corrected below — C61 + C66 are assigned, not reserved.)
- **C66** — emit: `substrate/src/server/autonomous.rs` (constant `myco_kernel_schema::migration::C66_MIGRATION_WINDOW_EXCEEDED`); negative-witness: `substrate/src/server/autonomous.rs::tests::c66_fires_and_forces_rollback_when_window_exceeded`; non-firing edge: `substrate/tests/e2e_schema_migration.rs::migration_c66_does_not_fire_within_window_plus_grace`. (Previously firing-but-undocumented.)
- **C68** — promoted from §1.5; emit: `substrate/src/reproduction.rs::verify_spawn_co_attestation`; negative-witness: `substrate/tests/e2e_reproduction.rs::c68_unattested_spawn_refused_and_immune_no_child_dag` (+ `…::c68_invalid_signature_refused`, `…::c68_wrong_parent_id_refused`, `…::c68_unseeded_parent_cannot_attest`); positive-witness: `…::spawn_attested_succeeds_and_records_i7_closure`. The §16.B anchor-wall-clock rate breach emits C48 on the same gate.
- **C69** — emit: `substrate/src/attestation.rs` (skin-level suppression refusal; helper `substrate/src/prune.rs::is_cultivation_orphaned_suppression_attempt`; observatory family `substrate/src/observatory.rs`); negative-witness: `substrate/tests/e2e_cultivation.rs::c69_cultivation_orphaned_suppression_refused`. (Firing-but-undocumented; COV06 §5.5 + L1/GOVERNANCE §3.2.C + P07 §4.)
- **C70** — emit: `substrate/src/attestation.rs` (`rotate_owner_key` activate-before-cooldown gate); negative-witness: `substrate/tests/e2e_owner_key.rs::c70_activate_before_cooldown_rejected_with_c70` (+ 8 sibling `c70_*` cases). (Firing-but-undocumented; 30-day key-rotation veto window.)
- **C74** — **Phase ① 永恒吞噬 (proactive hunger)**. emit: `substrate/src/ingest.rs::apply_hunger_and_emit` (constant `C74_INGESTION_STARVATION_DETECTOR_ID`), fired from `handle_advance` on EVERY cycle (operator-driven AND self-driven) when `cycles_since_last_ingestion ≥ STARVATION_THRESHOLD_CYCLES` (30); shares ONE cycles-since-ingestion measurement with the moderate `cultivar_initiated_ingestion_request` (threshold 10, `emit_substrate_event` — a proactive ask, NOT immune). Debounced (`STARVATION_DEBOUNCE_CYCLES` = 100, same discipline as C54) atop the 1s/detector `emit_immune_sporocarp` rate-limit. negative-witness: `substrate/tests/e2e_mortality.rs::phase1_starvation_emits_c74_immune_when_unfed_past_severe_threshold`; non-firing edge: `…::phase1_fed_substrate_does_not_starve`. C74 is the next-free C-number (C71/C72/C73 = the CHAR07 daily proxies; C74 had no prior use in substrate/src or this document). Closes the P02 §8.1 `p02_ingestion_starvation` TBD C-row.
- **C75** — **Phase ② telos/bet honesty (META §7.7 cultivator fiduciary self-report)**. emit: `substrate/src/observatory.rs::apply_c75_cultivator_fiduciary_strain` (detector_id `C75_cultivator_fiduciary_strain`, node_type constant `NODE_TYPE_CULTIVATOR_FIDUCIARY_STRAIN`), run on the per-cycle snapshot path right after `apply_p14c_telos_drift` so it observes the same telos_drift footprints. Fires iff the cultivar's `telos_drift*` has fired PERSISTENTLY over a **180-day rolling wall-clock window** (`C75_FIDUCIARY_STRAIN_WINDOW_UNIX_NS`, mapped to a cycle cutoff via `observatory_history`) — persistence = ≥ `C75_PERSISTENT_DRIFT_MIN_EVENTS` (2) drift events spanning ≥ `C75_PERSISTENT_DRIFT_MIN_SPAN_FRACTION` (0.5) of the window — AND **no cultivator fiduciary action** in the window (`C75_CULTIVATOR_ACTION_NODE_TYPE_PREFIXES` = `l0_revision_attested:` / `owner_objective_declared:` / `bet_retired:` / `successor_chain_updated:` / `succession_completed:` / `char07_assessment:`; routine heartbeats deliberately excluded). Debounced (`C75_FIDUCIARY_STRAIN_DEBOUNCE_CYCLES` = 500) + suspended during the birth period (`lifecycle::is_in_birth_period_quarantine`, same gate as C40 / telos). negative-witnesses (unit): `substrate/src/observatory.rs::tests::c75_fires_on_persistent_drift_with_cultivator_inaction`; non-firing edges: `…::c75_suppressed_when_cultivator_acted`, `…::c75_does_not_fire_on_nonpersistent_drift`, `…::c75_suspended_during_birth_period`, `…::c75_debounced`. C75 is the next-free C-number (verified: no prior use in substrate/src or this document; C74 was the prior highest). Closes the META §7.7 + COV01 §3.4 `cultivator_fiduciary_strain` C-row-TBD (was v0.9.x debt per COV01).

### §1.3 Bet-retirement sporocarp + non-CRITICAL meta-immune rows
C40 = trigger arc for L0/cards/LB_living_bets.md §4 (retirement); NOT CRITICAL — CI lifecycle parallel to `self_euthanasia_executed`. **C75** (`cultivator_fiduciary_strain`) is likewise NOT CRITICAL: it is a META-immune / informational-relational signal flagging the CULTIVATOR's neglect (not a substrate fault) and MUST NOT auto-quarantine the substrate (it is absent from the §1.1 CRITICAL table by construction; COV01 §3.5 — "investigate, do not dismiss").

### §1.4 v3.1.1 amendment — C-rows for P07 internal mortality discipline (implemented)

> **Status**: doctrinally committed in L0 v3.1.1 (2026-05-19); detectors C54/C55/C56 + the F26 应朽 registry **implemented** (emit sites cited below). These rows are not yet promoted into the binding §1.1/§1.2 trigger tables above — that promotion (with full Layer C witness corpus per META §5.4) remains a v0.9.x housekeeping step.

P07's v3.1.1 reading mandates ongoing internal mortality of 应朽 parts (`包括但不限于` 过时/错误/冗余/无用 + L1-recognized family members per P07 §3.1.c). Three C-rows realize this discipline:

| # | Breach name | Detection site | Mechanism | L0 trace | I trace | Status |
|---|---|---|---|---|---|---|
| C54 | `hoarding_indicator` (implemented; emit: `substrate/src/ingest.rs`) | L1/CONTINUITY prune-phase | ingestion-normal AND internal_mortality_event density below floor over rolling window → silent P07 failure | P07, P02 | I9, I10 | **implemented** |
| C55 | `silent_internal_mortality` (implemented; emit: `substrate/src/integrity.rs`) | L1/SCHEMA §2.5 | part removed from active state WITHOUT corresponding `internal_mortality_event` tombstone in DAG → silent deletion in violation of P07 §3.3 | P07, P06 | I4 | **implemented** |
| C56 | `cultivator_preserve_all_attempted` (implemented; emit: `substrate/src/prune.rs` + `kernel/governance/.../classifier.py`) | L1/GOVERNANCE §1 (classifier) | cultivator instruction matches "preserve all" / "never prune" / family-member-exemption patterns → mutation rejected; instruction emitted as covenant-violation signal per COV04 §5.6 | P07, COV04 | I2 | **implemented** |

These rows are implemented but **not yet wired into the binding §1.1/§1.2 trigger tables above**. They will be promoted to §1.1 / §1.2 in the v0.9.x housekeeping milestone alongside their full witness corpus.

**F-row addition** (registry live; L1-family extension path partial):

| # | Fixed-point | Defined at | L0 trace | I trace |
|---|---|---|---|---|
| F26 | 应朽 detection rule registry (open-ended; L1 may add families per P07 §3.1.c) — **live**: the runtime registry (`substrate/src/prune.rs::PruneRuleRegistry::seed`) is seeded with the L0 proof-of-mechanism rule + the four canonical 应朽 production families (过时 / 错误 / 冗余 / 无用), each appended via the now-exercised `register` extension path; `substrate/src/prune.rs::run_prune_scan` wires the scan and emits an `internal_mortality_event:{category}` DAG tombstone per matched part (P07 §3.3). The `register` extension point stays public for further L1 families without an L0 amendment; only the `rule_count` observatory metric remains scaffolded (`#[allow(dead_code)]`). Witness: `substrate/tests/e2e_mortality.rs::v3_1_1_prune_scan_cadence_only_fires_every_100_cycles` + `substrate/src/prune.rs::tests::run_prune_scan_emits_tombstone_for_redundant_duplicate`. | L1/CONTINUITY prune-phase + `substrate/src/prune.rs` | P07 | I9 |

### §1.5 P08 §3.2 / §5.1 — reproduction cultivator co-attestation (implemented)

> **Status**: doctrinally committed in L0/cards/P08 (永恒繁衍 / 集体免疫); the spawn co-attestation gate + I7 spawn-closure are **implemented** (emit site cited below) and **promoted into the binding §1.2 trigger table above** (its positive witness is bound at `substrate/tests/e2e_layer_c.rs::layer_c_p08_positive_child_substrate_spawn_succeeds`; full Layer C witness corpus per META §5.4 still accrues over the v0.9.x housekeeping window). The detailed gate documentation is retained here.

P08 §5.1 establishes that spawning a child substrate is a **CI-class doctrine event**, NOT a daily-mode mutation: an operator spawning on its own authority is the "daily-mode spawn = doctrine collapse" signal. Spawn therefore REQUIRES a cultivator-signed `myco-spawn-cosign-v1` envelope, verified by the parent BEFORE any side effect (no child DAG / state-dir is created on failure):

| # | Breach name | Detection site | Mechanism | L0 trace | I trace | Status |
|---|---|---|---|---|---|---|
| C68 | `reproduction_unattested_spawn` (implemented; emit: `substrate/src/reproduction.rs`) | L0/cards/P08 §5.1 + L1/SCHEMA §3.3 (I7) | a `sprout_child` request whose cultivator co-attestation fails ANY gate — missing/empty `spawn_cosign_envelope` / `attestation_signature` / `spore_schema_canonical_bytes`; no pinned owner identity; envelope decode failure (wrong domain/shape); `envelope.parent_substrate_id` ≠ this substrate (replay guard); I7(a) static-schema mismatch (`blake3(spore_schema_canonical_bytes)` ≠ co-signed hash, or the 7-field shape is malformed); or Ed25519 verify against the pinned owner pubkey fails → refuse + immune C68, no child created. The §16.B anchor-wall-clock rate breach (incl. clock-rewind) is refused on the same gate but emits C48 (rate half). On success the child-id is owner-minted `blake3(parent_id, spore_schema_hash, child_genesis_ts)` [§5.6] and the parent records a `genesis_attested:{child_prefix}` I7-closure node. | P08, P1.b'' | I7, I2 | **implemented** |

This row is **promoted into §1.2 above** (with its emit site + witnesses); the detailed gate-by-gate breakdown is kept here as the authoritative reference. Note on the C57-block: it is **partially populated, not wholly reserved** — beyond C61 + C66 (promoted to §1.2 above), several substrate-private integrity/health detectors are also implemented and firing (e.g. C57 `genesis_event_non_unique` / C58 `owner_pubkey_dag_pin_inconsistent` / C59 `manifest_cycle_vs_dag_advance_mismatch` in `substrate/src/integrity.rs`; C62 `federation_event_oversized`; C64 `persistence_unavailable`; C65 `python_worker_slow_call`). Cataloguing the remaining C57-block rows into §1.2 with their full witness corpora is a v0.9.x housekeeping continuation; only the in-scope C61/C66/C68/C69/C70 are tabled in this pass. **C67 `doctrine_witness_drift`** is deliberately NOT a runtime row: it is a **CI-lint signal** raised by the `operators/claude` witness-lint (META §5.5) when a previously-failing negative witness silently starts passing — cards are doctrine, not substrate state (P01c), so the drift is caught at CI time and carries no `emit_immune_sporocarp` site.

## §2. Contract-identity fixed points (unconditionally CI)
L0-doctrinal; CI status unconditional; mutation REQUIRES anchor-surface owner attestation per L1/GOVERNANCE §2.2.

| # | Fixed-point | Defined at | L0 trace | I trace |
|---|---|---|---|---|
| F1 | Classifier dimension table + function | L1/GOVERNANCE §1.2 | P1.b'' | I2 |
| F2 | `substrate-ID` (immutable post-genesis) | L1/GOVERNANCE §4.1 | P1.a, P1.c | I1 |
| F3 | `owner_key_history` (active-prefix + archived-tail) | L1/GOVERNANCE §3.1 | P1.b'', P1.c | I1 |
| F4 | `anchor_surface_endpoint_public_key` | L1/GOVERNANCE §4.1 | P1.b'' | I2, I8 |
| F5 | `substrate_secret_sealing_mechanism_attestation` | L1/SKIN §4.2 | P1.c | I1, I6 |
| F6 | `anchor_client_provenance_attestation` | L0/cards/AS_anchor_surface.md §3.10 | P1.b'' | I2 |
| F7 | Mortality-signal threshold + update-rule + emergence-rule | L1/GOVERNANCE §1.2 | P7 | I1 |
| F8 | SSoT designation | L1/SCHEMA §1.2 | P3 | I3 |
| F9 | DAG retention policy (P10.b invariant set) | L1/SCHEMA §2.5 | P6, P10 | I4, I9 |
| F10 | Storage tier exemption from I5 reachability | L1/SCHEMA §2.3 | P5 | I5 |
| F11 | Skin surface declaration | L1/SKIN §1 | P9 | I8 |
| F12 | Appetite-axis schema + sporocarp-type tree | L1/GOVERNANCE §1.2 | P3 | I2 |
| F13 | Threshold_emergence_rule (any axis) | L1/GOVERNANCE §1.2 | P3 | I2 |
| F14 | Federation peer attestation list (+revocations) | L1/GOVERNANCE §5 | P8 | I7 |
| F15 | `template_version_registry` (active + archived) | L1/TROPISM §B1 | P3, P6 | I2, I4 |
| F16 | `canonical_bytes_serializer_spec` | L1/SCHEMA §3.1, §4.1 | P1.c, P6 | I1, I3, I4 |
| F17 | `cluster_C` (L1/TRAJECTORY clustering) | L1/TRAJECTORY §4 | P6 | I4 |
| F18 | Selective compression rule set | L1/GOVERNANCE §15.F18 | P10 | I9 |
| F19 | Metabolic cost budgets | L1/GOVERNANCE §15.F19 | P11 | I10 |
| F20 | Telos-alignment metric | L1/TROPISM §F + L1/GOVERNANCE §15.F20 | P14 | I12 |
| F21 | Cultivation successor_chain registry | L1/GOVERNANCE §3.2 + §15.F21 | P1.b'', P7 | I1 |
| F22 | Reproduction generation discipline | L1/GOVERNANCE §4.3 + §15.F22 + §16 | P8 | I7 |
| F23 | Duress_keypair registration | L2/TRUST_MODEL §10 + L1/GOVERNANCE §15.F23 | P1.b'' adversarial | I1, I2 |
| F24 | Substrate-private signing keypair seed | L1/GOVERNANCE §15.F24 | P1.c, P6 | I1, I4 |
| F25 | Salience-emergence rule | L1/TROPISM §E.4 + L1/GOVERNANCE §15.F25 | P12 | I2 |

## §3. Birth-period CI elevation
Cross-ref L1/GOVERNANCE §1.3 (ALL parameter-tuning CI) + L0/cards/LB_living_bets.md §3 (birth-period exemption) (C40 + P14.c SUSPENDED).

## §4. Anchor-surface-resident state (substrate cannot author)

Exclusively owner-controlled; substrate-side forge attempt MUST be `untyped` (C14). Covers: anchor nonces + consumed-nonce log (§9.2.5); trusted wall-clock (§9.2.6); liveness heartbeat (§9.2.7); key-rotation cooldown veto (L1/GOVERNANCE §3.1); successor attestations + revocations (§3.2 + F21); final-seal (§4.4); anchor-client provenance (§9.3.3); peer revocation list + aggregate-reattestation Merkle commitments (§5.2); L0/L1 revision diff records (§9.2.4); DAG-tip co-signing logs with enumerated nodes (§9.2.2); substrate-ID birth attestation (§9.2.1); generation-counter ceiling (F22).

## §5. Consistency
Tier-2 SSoT (citation-only); drift resolves to source L1 doc as canonical. Status keys at §1.1; compression-invariant set at L0 P10.b + F18.
