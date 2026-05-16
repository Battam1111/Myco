# L1 — Hard Rules (cross-cuts index)

> **Status**: DRAFT 2. Cross-cuts index — CRITICAL breach surfaces + contract-identity fixed points across L1_SKIN, L1_CONTINUITY, L1_GOVERNANCE, L1_SCHEMA, L1_TROPISM, L1_TRAJECTORY. Indexes source docs (no duplication). Every row cites ≥1 P (P1-P11, P14) AND ≥1 I (I1-I10, I12).

---

## §1. CRITICAL-grade breaches (auto-quarantine triggers)

CRITICAL breach immediately transitions substrate to `alive but quarantined` (L1_CONTINUITY §5) and emits the named immune sporocarp. Cultivator-attested `quarantine_clearance` required for resumption.

### §1.1 L1 spec catalog rows (C1-C20)

Status key: **L** emitted with matching label; **U** unimplemented; **R** label reserved.

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace | Status |
|---|---|---|---|---|---|---|
| C1 | `appetite_locality_breach` | L1_SKIN §5 | Network-egress outside declared output endpoints | P2.a, P9 | I6, I8 | **U** |
| C2 | `output_endpoint_breach` | L1_SKIN §3 + §6 | Output to non-declared endpoint | P9.a, P2.a | I8, I6 | **R** |
| C3 | `post_handshake_ci_unattested` | L1_SKIN §4.3 | CI during post-handshake quarantine without fresh attestation | P1.b'' | I2, I8 | **U** |
| C4 | `substrate_secret_unsealed` | L1_SKIN §4.2 | substrate_secret in process address space (not OS-sealed) | P1.c, P1.a | I1 | **U** |
| C5 | `attestation_invalid` | L1_GOVERNANCE §2.3 | Signature fails OR nonce reuse OR dual-clock expiry mismatch | P1.b'' | I2 | **L** |
| C6 | `dag_enumeration_unclosed` | L1_SCHEMA §2.2 | CI co-sign enumerated DAG-nodes have parent-hash not resolving to prior tip ancestor / enumerated node | P6, P3 | I4 | **L** |
| C7 | `dag_retro_edit_detected` | L1_SCHEMA §2.1 | Merkle DAG node hash mismatch on re-computation | P6 | I4 | **L** |
| C8 | `ssot_migration_phase_skip` | L1_SCHEMA §1.3 | Single-step SSoT migration without ≥M-cycle dual-validation | P3 | I3 | **U** |
| C9 | `cold_resume_invariant_failure` | L1_CONTINUITY §3.1 | I1/I3/I4/I5/I8/I9/I10 pre-handshake re-derivation fails | P1.c, P3, P9 | I3, I4, I5, I8, I9, I10 | **L** |
| C10 | `agent_discriminating_attribute_persisted` | L1_SCHEMA §3.1 + L1_SKIN §4.2 | Persistent model-name / API-fingerprint / host-fingerprint / operator-token | P1.c | I1 | **U** |
| C11 | `concurrent_operator_persistent` | L1_SKIN §4.4 | Two operator-tokens simultaneously valid beyond FIFO serialization | P1.c | I8 | **U** |
| C12 | `successor_activation_with_fresh_owner_heartbeat` | L1_GOVERNANCE §3.2 | Successor activation while heartbeat fresh at anchor | P1.b'' | I1, I2 | **R** |
| C13 | `peer_attestation_revoked_egress` | L1_GOVERNANCE §5 + L1_SKIN §3.1 | Egress to peer on anchor revocation list | P8 | I7 | **U** |
| C14 | `untyped_mutation` | L1_GOVERNANCE §1.1 | I2 classifier returns `untyped` | P1.b'/P1.b'' | I2 | **L** |
| C15 | `classifier_fixed_point_bypass` | L1_GOVERNANCE §1.2 | Mutation of classifier table/function via non-CI path | P1.b'' | I2 | **U** |
| C16 | `mortality_signal_suppression` | L1_GOVERNANCE §4.4 + L1_TROPISM §B2 | Mortality-signal threshold/update-rule mutated via non-CI | P7 | I1, I2 | **U** |
| C17 | `operator_witness_forgery` | L1_GOVERNANCE §2.2 | `operator_witness` does not verify against logged handshake pubkey | P1.c | I1, I2 | **L** |
| C18 | `canonical_bytes_render_drift` | L0 §9.3.1 + §9.3.2 | Anchor-client render's canonical hash diverges from substrate's signed hash | P1.b'' | I2 | **L** |
| C19 | `paused_dormancy_unsafe_host` | L1_CONTINUITY §2.4 + §3.2 | Process terminated (not suspended) during paused dormancy | P7, P1.c | I1 | **R** |
| C20 | `genesis_attestation_chain_broken` | L1_GOVERNANCE §4.1 + L0 §9.2.1 | Substrate-ID's birth attestation signature does not verify | P1.a | I1 | **R** |

Each row is INDEPENDENT — none silently downgradeable (I2 classifier-fixed-point). **Coverage**: 7 of 20 EMITTED (C5/C6/C7/C9/C14/C17/C18); 13 U/R.

### §1.2 Substrate-private catalog rows (C30+)

Detectors needed for substrate correctness but NOT in L1 catalog occupy C30+. C21-C29 reserved for future L1 catalog extension.

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace | Status / Provenance |
|---|---|---|---|---|---|---|
| C30 | `handshake_pubkey_mismatch` | L1_SKIN §4.1 | Operator pubkey differs from pinned | P1.c | I1, I8 | **L** |
| C31 | `cycle_step_failed` | L1_CONTINUITY §1.1 | Metabolic-cycle step raises uncaught error | P3, P6 | I3, I4 | **L** |
| C32 | `substrate_state_orphan_detected` | L1_SCHEMA §2.5 | DAG-tip references node not stored | P5 | I4, I5 | **L** |
| C33 | `federation_peer_identity_mismatch` | L2_FEDERATION §6 + L1_SKIN §3 | Peer substrate_id differs from pin | P8 | I7 | **L** |
| C34 | `birth_period_violation_during_quarantine` | L1_TROPISM §4 + L1_CONTINUITY §5 | Sporocarp / CI mutation accepted while in birth period AND quarantine | P1.b'', P7 | I2 | **L** |
| C35 | `federation_substrate_private_event_injection` | L2_FEDERATION §6 + L1_SKIN §3 | Peer injects substrate-private event type (allowlist breach) | P8, P1.c | I7, I8 | **L** |
| C36 | `cycle_backlog` | L1_CONTINUITY §1.2 | Cycle ≥5s OR backlog ≥10 in mpsc bus | P11 | I10 | **L** |
| C37 | `doctrine_instability_burst` | L1_GOVERNANCE §6 + L0 §9.4 + L2_OBSERVABILITY §8 | >10 CI events in rolling 100-cycle window | P3 | I2, I4 | **L** |
| C38 | `snapshot_integrity_violation` | L1_SCHEMA §4 | `snapshot.cb` Ed25519 verification fails OR signer_pubkey not in `owner_key_history` active-prefix | P1.c, P6 | I1, I4 | **L** |
| C39 | `federation_hello_signature_invalid` | L2_FEDERATION §6 + §6.2 | Peer HELLO Ed25519 signature over substrate_id fails | P8, P1.c | I7 | **L** |
| C40 | `bet_weakening_quorum` | L1_GOVERNANCE + L0 §7.4 + L2_OBSERVABILITY §3 | 90-day wall-clock: ≥3 of {#1,#2,#3,#4a,#4b,#6} trend against bet (OLS Z≥1.96) AND #6 <1 for ≥50% of window cycles | P14 | I12 | **L** |
| C41 | `dag_cb_integrity_violation` | L1_SCHEMA §2.1 + L0 §9.4 | `dag.cb` wrapper integrity check fails (truncated / hash-chain inconsistent / signature missing) | P1.c, P6, P10 | I4, I9 | **U** |
| C42 | `manifest_cb_integrity_violation` | L1_SCHEMA §4 | `manifest.cb` content-hash inconsistent OR signature missing | P1.c, P6 | I1, I4 | **U** |
| C43 | `federation_recursive_injection` | L2_FEDERATION §6 + L1_SKIN §3 | Peer wrapped event whose inner prefix matches another `federation_received:` prefix | P8, P1.c | I7, I8 | **U** |
| C44 | `nonce_substrate_minted_replay` | L1_GOVERNANCE §2.2 + L0 §9.2.5 | Substrate-minted nonce reused across attestations within TTL | P1.b'' | I2 | **U** |
| C45 | `substrate_id_low_entropy_collision` | L1_GOVERNANCE §4.1 + L0 §9.2.1 | Genesis produces substrate_id with Shannon entropy < L1-tunable floor | P1.a | I1 | **U** |
| C46 | `owner_succession_bypass` | L1_GOVERNANCE §3.2 | Transition to `alive::normal` via succession without valid `succession_acceptance_attestation` | P1.b'', P7 | I1, I2 | **U** |
| C47 | `generation_depth_exceeded` | L1_GOVERNANCE §16.A + L1_SCHEMA §3.1 | `sprout_child` where parent's `reproduction_lineage_depth` ≥ max AND no `depth_override` | P8 | I7 | **U** |
| C48 | `reproduction_rate_exceeded` | L1_GOVERNANCE §16.B | `sprout_child` within `reproduction_rate` window | P8 | I7 | **U** |
| C49 | `consensus_floor_bypass` | L2_FEDERATION §6.5 | Population-level claim accepted without ≥3-peer Byzantine consensus | P8, P15 | I7 | **U** |
| C50 | `coerced_owner_suspected` | L2_TRUST_MODEL §10.A.2 | Adversarial-Cultivator detection via observability heuristics | P1.b'' | I1, I2 | **U** |
| C51 | `compression_invariant_corruption` | L1_SCHEMA §2.5 | Compression event violates P10.b invariant set | P10 | I9 | **U** |
| C52 | `compression_uncattested` | L1_SCHEMA §2.5 + P10.c | Compression event fires without owner attestation | P10 | I9 | **U** |
| C53 | `budget_exhausted_silent` | L1_SCHEMA §4.1 | Cost-budget threshold reached without `budget_exhausted:{axis}` | P11 | I10 | **U** |
| C54 | *(reserved for L1_TROPISM C23/C24 promotion)* | — | — | — | — | **R** |

**Coverage**: C30-C40 emit (11); C41-C53 deferred.

### §1.3 Mortality + bet-related sporocarps

C40 `bet_weakening_quorum` is trigger arc for L0 §7.5 bet retirement. NOT CRITICAL — CI lifecycle parallel to `self_euthanasia_executed`. See L0 §7.5.

## §2. Contract-identity fixed points (unconditionally CI)

L0-doctrinal; CI-level status unconditional, NOT subject to classifier-table mutation.

| # | Fixed-point | Defined at | L0 trace | I trace |
|---|---|---|---|---|
| F1 | Classifier dimension table + classifier function | L1_GOVERNANCE §1.2 | P1.b'' | I2 |
| F2 | `substrate-ID` (immutable post-genesis) | L1_GOVERNANCE §4.1 | P1.a, P1.c | I1 |
| F3 | `owner_key_history` (active-prefix + archived-tail) | L1_GOVERNANCE §3.1 | P1.b'', P1.c | I1 |
| F4 | `anchor_surface_endpoint_public_key` | L1_GOVERNANCE §4.1 | P1.b'' | I2, I8 |
| F5 | `substrate_secret_sealing_mechanism_attestation` | L1_SKIN §4.2 | P1.c | I1, I6 |
| F6 | `anchor_client_provenance_attestation` | L0 §9.3.3 | P1.b'' | I2 |
| F7 | Mortality-signal threshold + update-rule + emergence-rule | L1_GOVERNANCE §1.2 | P7 | I1 |
| F8 | SSoT designation | L1_SCHEMA §1.2 | P3 | I3 |
| F9 | DAG retention policy (P10.b invariant set; cold-tier CI) | L1_SCHEMA §2.5 | P6, P10 | I4, I9 |
| F10 | Storage tier exemption from I5 reachability | L1_SCHEMA §2.3 | P5 | I5 |
| F11 | Skin surface declaration | L1_SKIN §1 | P9 | I8 |
| F12 | Appetite-axis schema + sporocarp-type tree | L1_GOVERNANCE §1.2 | P3 | I2 |
| F13 | Threshold_emergence_rule (any axis) | L1_GOVERNANCE §1.2 | P3 | I2 |
| F14 | Federation peer attestation list (+revocations) | L1_GOVERNANCE §5 | P8 | I7 |
| F15 | `template_version_registry` (active-prefix + archived-tail) | L1_TROPISM §B1 | P3, P6 | I2, I4 |
| F16 | `canonical_bytes_serializer_spec` | L1_SCHEMA §3.1, §4.1 | P1.c, P6 | I1, I3, I4 |
| F17 | `cluster_C` (L1_TRAJECTORY clustering) | L1_TRAJECTORY §4 | P6 | I4 |
| F18 | Selective compression rule set | L1_GOVERNANCE §15.F18 | P10 | I9 |
| F19 | Metabolic cost budgets | L1_GOVERNANCE §15.F19 | P11 | I10 |
| F20 | Telos-alignment metric | L1_TROPISM §F + L1_GOVERNANCE §15.F20 | P14 | I12 |
| F21 | Cultivation successor_chain registry | L1_GOVERNANCE §3.2 + §15.F21 | P1.b'', P7 | I1 |
| F22 | Reproduction generation discipline | L1_GOVERNANCE §4.3 + §15.F22 + §16 | P8 | I7 |
| F23 | Duress_keypair registration | L2_TRUST_MODEL §10 + L1_GOVERNANCE §15.F23 | P1.b'' adversarial | I1, I2 |
| F24 | Substrate-private signing keypair seed | L1_GOVERNANCE §15.F24 | P1.c, P6 | I1, I4 |
| F25 | Salience-emergence rule | L1_TROPISM §E.4 + L1_GOVERNANCE §15.F25 | P12 | I2 |

Mutation of any F-row requires anchor-surface owner attestation per L1_GOVERNANCE §2.2 (canonical bytes + operator_witness + anchor nonce + dual-clock + DAG-enumeration closure).

## §3. Birth-period CI elevation (transitional)

During birth period (L1_TROPISM §4 + L1_GOVERNANCE §1.3), ALL parameter-tuning events are CI regardless of steady-state classification. Reclassification to daily at owner-attested birth-period termination.

**Birth-period exemptions** (L0 §7.4.e): C40 `bet_weakening_quorum` SUSPENDED — emits `bet_weakening_evaluation_suspended`. P14.c `telos_drift` exempt — emits `telos_alignment_pending`.

## §4. Anchor-surface-resident state (substrate cannot author)

Exclusively owner-controlled at anchor; mapped to L0 §9.2:

- Anchor-generated nonces + consumed-nonce log (§9.2.5)
- Anchor trusted wall-clock (§9.2.6)
- Owner-liveness heartbeat (§9.2.7 + L1_GOVERNANCE §3.2)
- Owner-key rotation cooldown veto window (L1_GOVERNANCE §3.1)
- `successor_attestation` records + revocations (L1_GOVERNANCE §3.2 + L0 §15 + F21)
- `anchor_surface_final_seal` (L1_GOVERNANCE §4.4)
- Anchor client provenance attestation (§9.3.3)
- Federation peer revocation list (L1_GOVERNANCE §5)
- Aggregate-reattestation peer-set Merkle commitments (L1_GOVERNANCE §5.2)
- L0/L1 revision diff records (§9.2.4; feeds C37)
- DAG-tip co-signing logs with enumerated nodes (§9.2.2)
- Substrate-ID birth attestation (§9.2.1)
- Generation-counter ceiling (F22; L0 §16.2)

Substrate-side forge/shadow-mirror attempt is `untyped` (C14), rejected at skin.

## §5. Cross-doc consistency claims

No new normative content; every row is a citation. Drift resolves to source L1 doc as canonical. This doc updates in the same attestation event when sources update (tier-2 SSoT).

## §7. Open at L1 / L4

- Immune-system architecture: per-row detector vs generic event-stream filter — L4. Current: per-row modules.
- Sporocarp emission cadence: same-cycle (sporocarp emission IS a metabolic event).
- F-row mutation-rate observability: F-row thrash → `f_row_thrash` signal recommended; feeds C37.

## §8. Glossary additions

| Term | Definition |
|---|---|
| **L1 catalog C-row** | C1-C20 formal §1.1 entries. 7 emitted; 13 U/R. |
| **Substrate-private C-row** | C30+ — substrate correctness detectors not in formal catalog. C21-C29 reserved. |
| **R status** | Reserved — label preserved; emit site freed for future. |
| **L status** | Live — emitted in substrate code with matching tag. |
| **U status** | Unimplemented — label reserved. |
| **Cultivation / Cultivator / Cultivar** | See L0 §12 + L1_GOVERNANCE §17. |
| **bet_retired_proposal / bet_retired_executed** | CI lifecycle per L0 §7.5.b two-phase commit. NOT immune. |
| **Compression-invariant set** (F18 + L0 P10.b) | State surviving compression: substrate-ID, owner_key_history, CI-attested events, mortality signals, federation pins, most-recent-N cycles full DAG, substrate signing keypair seed (F24). |
