# L1 — Hard Rules (cross-cuts index)

> **Status**: DRAFT 2. Cross-cuts index — CRITICAL-grade breach surfaces + contract-identity-level fixed points across L1_SKIN, L1_CONTINUITY, L1_GOVERNANCE, L1_SCHEMA, L1_TROPISM, L1_TRAJECTORY. Indexes (does not duplicate) the source docs.
> Every row cites ≥1 P (P1-P11, P14) AND ≥1 I (I1-I10, I12).

---

## §1. CRITICAL-grade breaches (auto-quarantine triggers)

A CRITICAL-grade breach immediately transitions the substrate to `alive but quarantined` (per L1_CONTINUITY §5) and emits the named immune sporocarp. Owner-attested (Cultivator-attested per G-11.a) `quarantine_clearance` is required for resumption.

### §1.1 L1 spec catalog rows (C1-C20)

Status key: **L** = emitted with matching label; **U** = unimplemented; **R** = label reserved (substrate emit site freed for future L1 implementation).

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace | Status |
|---|---|---|---|---|---|---|
| C1 | `appetite_locality_breach` | L1_SKIN §5 | Network-egress outside declared output endpoints | P2.a, P9 | I6, I8 | **U** (M27+) |
| C2 | `output_endpoint_breach` | L1_SKIN §3 + §6 | Output to non-declared endpoint | P9.a, P2.a | I8, I6 | **R** |
| C3 | `post_handshake_ci_unattested` | L1_SKIN §4.3 | CI during post-handshake quarantine without fresh attestation | P1.b'' | I2, I8 | **U** |
| C4 | `substrate_secret_unsealed` | L1_SKIN §4.2 | substrate_secret in process address space (not OS-sealed) | P1.c, P1.a | I1 | **U** |
| C5 | `attestation_invalid` | L1_GOVERNANCE §2.3 | Signature fails OR nonce reuse OR dual-clock expiry mismatch (§13.1) | P1.b'' | I2 | **L** |
| C6 | `dag_enumeration_unclosed` | L1_SCHEMA §2.2 | CI co-sign enumerated DAG-nodes have parent-hash not resolving to prior tip ancestor / enumerated node | P6, P3 | I4 | **L** |
| C7 | `dag_retro_edit_detected` | L1_SCHEMA §2.1 | Merkle DAG node hash mismatch on re-computation | P6 | I4 | **L** |
| C8 | `ssot_migration_phase_skip` | L1_SCHEMA §1.3 | Single-step SSoT migration without ≥M-cycle dual-validation | P3 | I3 | **U** |
| C9 | `cold_resume_invariant_failure` | L1_CONTINUITY §3.1 | I1/I3/I4/I5/I8/I9/I10 pre-handshake re-derivation fails | P1.c, P3, P9 | I3, I4, I5, I8, **I9, I10** | **L** (I9/I10 wiring M27+) |
| C10 | `agent_discriminating_attribute_persisted` | L1_SCHEMA §3.1 + L1_SKIN §4.2 | Persistent model-name / API-fingerprint / host-fingerprint / operator-token | P1.c | I1 | **U** |
| C11 | `concurrent_operator_persistent` | L1_SKIN §4.4 | Two operator-tokens simultaneously valid beyond FIFO serialization | P1.c | I8 | **U** |
| C12 | `successor_activation_with_fresh_owner_heartbeat` | L1_GOVERNANCE §3.2 | Successor activation while heartbeat fresh at anchor surface | P1.b'' | I1, I2 | **R** (M-anchor-3 heartbeat services) |
| C13 | `peer_attestation_revoked_egress` | L1_GOVERNANCE §5 + L1_SKIN §3.1 | Egress to peer on anchor-surface revocation list | P8 | I7 | **U** |
| C14 | `untyped_mutation` | L1_GOVERNANCE §1.1 | I2 classifier returns `untyped` | P1.b'/P1.b'' | I2 | **L** (emitted as `untyped_mutation_blocked`) |
| C15 | `classifier_fixed_point_bypass` | L1_GOVERNANCE §1.2 | Mutation of classifier table/function via non-CI path | P1.b'' | I2 | **U** |
| C16 | `mortality_signal_suppression` | L1_GOVERNANCE §4.4 + L1_TROPISM §B2 | Mortality-signal threshold/update-rule mutated via non-CI (per L0 P7) | P7 | I1, I2 | **U** |
| C17 | `operator_witness_forgery` | L1_GOVERNANCE §2.2 | `operator_witness` does not verify against logged handshake pubkey | P1.c | I1, I2 | **L** |
| C18 | `canonical_bytes_render_drift` | L0 §9.3.1 + §9.3.2 | Anchor-client render's canonical hash diverges from substrate's signed hash | P1.b'' | I2 | **L** (Rust/Python/TS parity verified) |
| C19 | `paused_dormancy_unsafe_host` | L1_CONTINUITY §2.4 + §3.2 | Process terminated (not suspended) during paused dormancy | P7, P1.c | I1 | **R** |
| C20 | `genesis_attestation_chain_broken` | L1_GOVERNANCE §4.1 + L0 §9.2.1 | Substrate-ID's birth attestation signature does not verify | P1.a | I1 | **R** (M-anchor-2) |

**Each L1 catalog CRITICAL row is INDEPENDENT** — none can be silently downgraded (I2 classifier-fixed-point).

**Coverage**: 7 of 20 EMITTED (C5, C6, C7, C9, C14, C17, C18); 13 U/R. Closure is M27+ (stranded `kernel/skin`, `kernel/continuity::DormancyMachine` imports).

### §1.2 Substrate-private catalog rows (C30+)

Per M24.1 namespace doctrine: detectors needed for substrate correctness but NOT in L1 catalog occupy C30+. Reserves C21-C29 for future L1 catalog extension.

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace | Status / Provenance |
|---|---|---|---|---|---|---|
| C30 | `handshake_pubkey_mismatch` | L1_SKIN §4.1 | Operator pubkey differs from pinned (TOFU mismatch) | P1.c | I1, I8 | **L** |
| C31 | `cycle_step_failed` | L1_CONTINUITY §1.1 | Metabolic-cycle step raises uncaught error | P3, P6 | I3, I4 | **L** |
| C32 | `substrate_state_orphan_detected` | L1_SCHEMA §2.5 | DAG-tip references node not stored | P5 | I4, I5 | **L** |
| C33 | `federation_peer_identity_mismatch` | L2_FEDERATION §6 + L1_SKIN §3 | Peer substrate_id differs from pin | P8 | I7 | **L** |
| C34 | `birth_period_violation_during_quarantine` | L1_TROPISM §4 + L1_CONTINUITY §5 | Sporocarp / CI mutation accepted while in birth period AND quarantine | P1.b'', P7 | I2 | **L** |
| C35 | `federation_substrate_private_event_injection` | L2_FEDERATION §6 + L1_SKIN §3 | Peer injects substrate-private event type (allowlist breach) | P8, P1.c | I7, I8 | **L** (Phase β; ALLOWLIST + wrapped envelopes) |
| **C36** | `cycle_backlog` | L1_CONTINUITY §1.2 | Cycle ≥5s OR backlog ≥10 in mpsc bus | P11 | I10 | **L** (M24) |
| **C37** | `doctrine_instability_burst` | L1_GOVERNANCE §6 + L0 §9.4 + L2_OBSERVABILITY §8 | >10 CI events (attestations / classifier mutations / key rotations / revisions) in rolling 100-cycle window | P3 | I2, I4 | **L** (M25.1; cycle window — wall-clock correction M26-cascade) |
| **C38** | `snapshot_integrity_violation` | L1_SCHEMA §4 | `snapshot.cb` Ed25519 verification fails OR signer_pubkey not in `owner_key_history` active-prefix | P1.c, P6 | I1, I4 | **L** (M25.0) |
| **C39** | `federation_hello_signature_invalid` | L2_FEDERATION §6 + §6.2 | Peer HELLO Ed25519 signature over substrate_id fails | P8, P1.c | I7 | **L** (M25.4; closes Phase β federation mutual-auth) |
| **C40** | `bet_weakening_quorum` | L1_GOVERNANCE + L0 §7.4 + L2_OBSERVABILITY §3 | 90-day wall-clock: ≥3 of {#1,#2,#3,#4a,#4b,#6} trend against bet (OLS Z≥1.96) AND #6 <1 for ≥50% of window cycles | P14 | I12 | **L** (M25.2; M25.2 uses cycle window — wall-clock correction M26.x) |
| **C41** | `dag_cb_integrity_violation` | L1_SCHEMA §2.1 + L0 §9.4 | `dag.cb` wrapper integrity check fails (truncated / hash-chain inconsistent / signature missing) | P1.c, P6, P10 | I4, I9 | **U** (Phase γ.9 M4; M28-cascade) |
| **C42** | `manifest_cb_integrity_violation` | L1_SCHEMA §4 | `manifest.cb` content-hash inconsistent OR signature missing | P1.c, P6 | I1, I4 | **U** (Phase γ.9 M5; M28-cascade) |
| **C43** | `federation_recursive_injection` | L2_FEDERATION §6 + L1_SKIN §3 | Peer wrapped event whose inner prefix matches another `federation_received:` prefix (depth >1 forbidden) | P8, P1.c | I7, I8 | **U** (Phase γ.9 M11; M28-cascade) |
| **C44** | `nonce_substrate_minted_replay` | L1_GOVERNANCE §2.2 + L0 §9.2.5 | Substrate-minted nonce reused across attestations within TTL window | P1.b'' | I2 | **U** (Phase γ.9 M2; M-anchor-3) |
| **C45** | `substrate_id_low_entropy_collision` | L1_GOVERNANCE §4.1 + L0 §9.2.1 | Genesis produces substrate_id with Shannon entropy < L1-tunable floor (default 2^16) | P1.a | I1 | **U** (Phase γ.9 M3; M-anchor-2) |
| **C46** | `owner_succession_bypass` | L1_GOVERNANCE §3.2 | Transition to `alive::normal` via succession without valid `succession_acceptance_attestation` | P1.b'', P7 | I1, I2 | **U** (M-anchor-3) |
| **C47** | `generation_depth_exceeded` | L1_GOVERNANCE §16.A + L1_SCHEMA §3.1 | `sprout_child` where parent's `reproduction_lineage_depth` ≥ max AND no `depth_override` | P8 | I7 | **U** (M27) |
| **C48** | `reproduction_rate_exceeded` | L1_GOVERNANCE §16.B | `sprout_child` within `reproduction_rate` window (default 1/24h anchor-clock) | P8 | I7 | **U** (M27 + M-anchor-3) |
| **C49** | `consensus_floor_bypass` | L2_FEDERATION §6.5 | Population-level claim accepted without ≥3-peer Byzantine consensus per L2_FEDERATION §6.5.a-c | P8, P15 | I7 | **U** (M27 + future PBFT) |
| **C50** | `coerced_owner_suspected` | L2_TRUST_MODEL §10.A.2 | Adversarial-Cultivator detection via observability heuristics (signature velocity / CI-burst / duress-keypair use) | P1.b'' | I1, I2 | **U** (L2_TRUST_MODEL wiring) |
| **C51** | `compression_invariant_corruption` | L1_SCHEMA §2.5 | Compression event violates P10.b invariant set | P10 | I9 | **U** |
| **C52** | `compression_uncattested` | L1_SCHEMA §2.5 + P10.c | Compression event fires without owner attestation | P10 | I9 | **U** |
| **C53** | `budget_exhausted_silent` | L1_SCHEMA §4.1 | Cost-budget threshold reached without `budget_exhausted:{axis}` per P11.c clause 1 | P11 | I10 | **U** |
| **C54** | *(reserved for L1_TROPISM C23/C24 promotion)* | — | — | — | — | **R** |

**Coverage**: C30-C40 emit (11). C41-C49 DEFERRED to M28-cascade / M-anchor / M27. C50-C53 are M26-cascade renumberings. C54 reserved for L1_TROPISM.

### §1.3 Mortality + bet-related sporocarps

C40 `bet_weakening_quorum` is trigger arc for L0 §7.5 bet retirement: C40 → owner re-justification → 3 failed re-justifications over 2y wall-clock + signal #6 <0.1 for >75% of final 90-day window → `bet_retired_proposal` (CI, not immune) → owner co-attestation → `bet_retired_executed:{axis_name}` + `alive::archived`. NOT CRITICAL — CI lifecycle parallel to `self_euthanasia_executed`. See L0 §7.5.

## §2. Contract-identity-level fixed points (unconditionally CI)

L0-doctrinal fixed-points; CI-level status unconditional, NOT subject to classifier-table mutation.

| # | Fixed-point | Defined at | L0 trace | I trace |
|---|---|---|---|---|
| F1 | Classifier dimension table + classifier function | L1_GOVERNANCE §1.2 | P1.b'' | I2 |
| F2 | `substrate-ID` (immutable post-genesis) | L1_GOVERNANCE §4.1 | P1.a, P1.c | I1 |
| F3 | `owner_key_history` (active-prefix + archived-tail) | L1_GOVERNANCE §3.1 | P1.b'', P1.c | I1 |
| F4 | `anchor_surface_endpoint_public_key` | L1_GOVERNANCE §4.1 | P1.b'' | I2, I8 |
| F5 | `substrate_secret_sealing_mechanism_attestation` | L1_SKIN §4.2 | P1.c | I1, I6 |
| F6 | `anchor_client_provenance_attestation` (0%; M-anchor-1) | L0 §9.3.3 | P1.b'' | I2 |
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
| **F18** | Selective compression rule set | L1_GOVERNANCE §15.F18 | P10 | I9 |
| **F19** | Metabolic cost budgets | L1_GOVERNANCE §15.F19 | P11 | I10 |
| **F20** | Telos-alignment metric | L1_TROPISM §F + L1_GOVERNANCE §15.F20 | P14 | I12 |
| **F21** | Cultivation successor_chain registry | L1_GOVERNANCE §3.2 + §15.F21 | P1.b'', P7 | I1 |
| **F22** | Reproduction generation discipline | L1_GOVERNANCE §4.3 + §15.F22 + §16 | P8 | I7 |
| **F23** | Duress_keypair registration | L2_TRUST_MODEL §10 + L1_GOVERNANCE §15.F23 | P1.b'' adversarial | I1, I2 |
| **F24** | Substrate-private signing keypair seed | L1_GOVERNANCE §15.F24 | P1.c, P6 | I1, I4 |
| **F25** | Salience-emergence rule | L1_TROPISM §E.4 + L1_GOVERNANCE §15.F25 | P12 (retracted) | I2 |

**Mutation of any F-row requires anchor-surface owner attestation** per L1_GOVERNANCE §2.2 (canonical bytes + operator_witness + anchor-side nonce + dual-clock + DAG-enumeration closure). Per DRAFT 9 SEALED §9.2.5, nonces are anchor-surface-generated (M-anchor-3 milestone closes implementation gap).

**F18-F24 coverage**: F18 unimpl (M26-cascade A2/A5); F19 unimpl; F20 unimpl (L1_TROPISM A1 deadline); F21 unimpl (L1_GOVERNANCE A5); F22 unimpl; F23 unimpl (L2_TRUST_MODEL A4); F24 **partial** (M25 snapshot.cb + M25.4 federation HELLO; seed CI attestation deferred to M-anchor-2).

## §3. Birth-period CI elevation (transitional)

During birth period (per L1_TROPISM §4 + L1_GOVERNANCE §1.3), **ALL parameter-tuning events are CI** regardless of steady-state classification. Reclassification to daily happens at owner-attested birth-period termination. The L0 / L1_GOVERNANCE classifier observes the birth-period flag.

**Birth-period exemptions** (L0 §7.4.e + DRAFT 9 SEALED): C40 `bet_weakening_quorum` SUSPENDED — substrate emits `bet_weakening_evaluation_suspended` instead. P14.c `telos_drift` similarly exempt — emits `telos_alignment_pending`.

## §4. Anchor-surface-resident state (substrate cannot author)

Exclusively owner-controlled at the anchor surface; mapped to L0 §9.2 sub-mechanisms:

- Anchor-surface-generated nonces + consumed-nonce log (L0 §9.2.5; current is substrate-mint per C44; M-anchor-3)
- Anchor-surface trusted wall-clock (L0 §9.2.6; M-anchor-3)
- Owner-liveness heartbeat (L0 §9.2.7 + L1_GOVERNANCE §3.2; M-anchor-3)
- Owner-key rotation cooldown veto window (L1_GOVERNANCE §3.1)
- `successor_attestation` records + revocations (L1_GOVERNANCE §3.2 + L0 §15 + F21)
- `anchor_surface_final_seal` (L1_GOVERNANCE §4.4)
- Anchor-surface client provenance attestation (L0 §9.3.3; M-anchor-1)
- Federation peer revocation list (L1_GOVERNANCE §5)
- Aggregate-reattestation peer-set Merkle commitments (L1_GOVERNANCE §5.2)
- L0/L1 revision diff records (L0 §9.2.4; feeds C37)
- DAG-tip co-signing logs with enumerated nodes (L0 §9.2.2; M-anchor-5)
- Substrate-ID birth attestation (L0 §9.2.1; M-anchor-2)
- Generation-counter ceiling (F22; L0 §16.2)

Substrate-side attempt to forge or shadow-mirror is `untyped` (C14) and rejected at the skin.

## §5. Cross-doc consistency claims

No new normative content; every row is a citation. Drift resolves to the source L1 doc as canonical. This doc updates in the same attestation event when sources update (tier-2 SSoT at L1_SCHEMA).

## §7. Open at L1 / L4

- **Immune-system architecture**: dedicated per-row detector vs generic event-stream filter — L4 picks. Current: per-row modules under `myco_substrate/src/`.
- **Sporocarp emission cadence**: same-cycle vs next-cycle queue. Current: same-cycle (sporocarp emission IS a metabolic event).
- **F-row mutation rate observability**: F-row thrash within an L1-tunable window → recommend `f_row_thrash` signal; feeds C37 doctrine-instability burst.
- **C41-C45 deferred**: M28-cascade + M-anchor-2/M-anchor-3 closure paths.
- **F18-F24 implementation order**: M27+ stranded-library imports + M-anchor-1 through M-anchor-5 closures.

## §8. Glossary additions

| Term | Definition |
|---|---|
| **L1 catalog C-row** | C1-C20 — formal §1.1 entries. 7 emitted; 13 U/R. |
| **Substrate-private C-row** | C30+ — substrate correctness detectors not in formal L1 catalog. C21-C29 reserved for future L1 extension. |
| **R status** | "Reserved" — L1 catalog label preserved; previously-misnamed emit site renamed into C30+ per M24.1. |
| **L status** | "Live" — emitted in substrate code with matching tag. |
| **U status** | "Unimplemented" — label reserved; awaits M27+ (stranded-library imports) or M-anchor-N closure. |
| **Cultivation / Cultivator / Cultivar** | See L0 §12 + L1_GOVERNANCE §17. |
| **bet_retired_proposal / bet_retired_executed** | CI-level lifecycle proposals per L0 §7.5.b two-phase commit. NOT immune sporocarps. See §1.3. |
| **Compression-invariant set** (F18 + L0 P10.b) | State surviving compression: substrate-ID, owner_key_history, CI-attested events, mortality signals, federation pins, most-recent-N cycles full DAG (≥1000 L1-tunable), substrate signing keypair seed (F24). |
| **M-anchor-N milestones** | M-anchor-1 (anchor-client provenance), M-anchor-2 (substrate-ID birth attestation + C45), M-anchor-3 (nonces + wall-clock + heartbeat), M-anchor-4 (witnesses-not-verdicts + nonce-derived sampling), M-anchor-5 (L0 revision diff + DAG closure check). See L0 §9.2 status table. |
