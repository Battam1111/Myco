# L1 — Hard Rules (cross-cuts index)

> **Status**: DRAFT 2 (2026-05-17, M26-cascade A6). Cross-cuts index for the 6 mechanism L1 docs + DRAFT 9 SEALED L0 additions. NOT a v0.8 R1-R7 grammatical inheritance — it is a normative enumeration of CRITICAL-grade breach surfaces + contract-identity-level fixed points, drawn from the 6 mechanism docs + L0 DRAFT 9 SEALED as a single source of truth for L4 immune-system construction.
> **Layer**: L1. Governed by L0 DRAFT 9 SEALED.
> **Scope**: indexes (does not duplicate) the enforcement targets across L1_SKIN, L1_CONTINUITY, L1_GOVERNANCE, L1_SCHEMA, L1_TROPISM, L1_TRAJECTORY. When L4 implements the immune system, this doc is the enumeration of "what to detect" — CRITICAL breaches that auto-quarantine + CI fixed-points that owner-attestation is unconditionally required for.
> **L0 traceability** (per C7.3 v0.8-origin discrimination — this doc traces independently to L0): every row in §1 and §2 below cites at least one P (P1-P11, P14 — twelve-principle DRAFT 9 SEALED set; P12/P13 retracted to L1_TROPISM/L1_SKIN per G-9.b; P15 retracted to L2_FEDERATION) AND one I (I1-I10, I12 — eleven-invariant DRAFT 9 SEALED set; I11 retracted to L1_TROPISM) it enforces. The G-rules grammar of v0.8 is NOT inherited; the index pattern is independently derived from L0's invariants.
> **DRAFT 2 additions** (M26-cascade A6, 2026-05-17): C36-C45 substrate-private + DRAFT 9 SEALED catalog additions; F18-F24 new F-rows; Status column added for C1-C20; Cultivation vocabulary integrated.

---

## §1. CRITICAL-grade breaches (auto-quarantine triggers)

A CRITICAL-grade breach immediately transitions the substrate to `alive but quarantined` (per L1_CONTINUITY §5) and emits the named immune sporocarp. Owner-attested (Cultivator-attested per G-11.a) `quarantine_clearance` is required for resumption.

### §1.1 L1 spec catalog rows (C1-C20)

Status column key:
- **L** = L1 spec label, **emitted** in substrate code with matching label (true coverage).
- **U** = L1 spec label, **unimplemented** — no substrate emit site uses this label.
- **R** = label reserved post-M24.1 namespace cleanup (previously misused; substrate emit site freed for future L1 implementation).

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace | Status |
|---|---|---|---|---|---|---|
| C1 | `appetite_locality_breach` | L1_SKIN §5 | Network-egress detection — any traffic exits substrate process outside declared output endpoints | P2.a (envelope-gated inclusion), P9 (single integument) | I6 (universal inclusion w/ observed metabolism), I8 (single-skin integrity) | **U** (M27+: kernel/skin import wiring) |
| C2 | `output_endpoint_breach` | L1_SKIN §3 + §6 | Output to non-declared endpoint | P9.a, P2.a | I8, I6 | **R** (C30 occupied this slot pre-M24.1) |
| C3 | `post_handshake_ci_unattested` | L1_SKIN §4.3 | CI-level operation during post-handshake quarantine window without fresh attestation | P1.b'' | I2, I8 | **U** |
| C4 | `substrate_secret_unsealed` | L1_SKIN §4.2 | substrate_secret detected in substrate-process address space (not OS-sealed) | P1.c, P1.a | I1 | **U** |
| C5 | `attestation_invalid` | L1_GOVERNANCE §2.3 | Owner signature fails verification OR nonce reuse OR expiry-clock-mismatch (substrate-cycle / wall-clock dual check per §13.1) | P1.b'' | I2 | **L** (emitted) |
| C6 | `dag_enumeration_unclosed` | L1_SCHEMA §2.2 | At CI co-sign, enumerated DAG-nodes include a parent-hash that does not resolve to ancestor of prior tip OR another enumerated node | P6, P3 | I4 | **L** (emitted) |
| C7 | `dag_retro_edit_detected` | L1_SCHEMA §2.1 | Merkle DAG node hash mismatch from re-computation | P6 | I4 | **L** (emitted) |
| C8 | `ssot_migration_phase_skip` | L1_SCHEMA §1.3 | Single-step SSoT migration without ≥M cycles of dual-validation phase | P3 | I3 | **U** |
| C9 | `cold_resume_invariant_failure` | L1_CONTINUITY §3.1 | Any of I1/I3/I4/I5/I8 pre-handshake check fails (witnesses fail re-derivation at anchor-surface verifier); per DRAFT 9 SEALED also include I9 compression-invariant + I10 cost-budget state check | P1.c, P3, P9 | I3, I4, I5, I8, **I9, I10** | **L** (emitted; I9/I10 wiring deferred to M27+) |
| C10 | `agent_discriminating_attribute_persisted` | L1_SCHEMA §3.1 + L1_SKIN §4.2 | Persistent storage of model-name / API-fingerprint / host-fingerprint / deterministic-operator-token | P1.c | I1 | **U** |
| C11 | `concurrent_operator_persistent` | L1_SKIN §4.4 | Two operator-tokens simultaneously valid for the same substrate beyond the strict-FIFO handshake serialization window | P1.c | I8 | **U** |
| C12 | `successor_activation_with_fresh_owner_heartbeat` | L1_GOVERNANCE §3.2 | Successor `successor_activation` event fires while owner liveness heartbeat is fresh at anchor surface (per L0 §15 succession protocol + §9.2.7 heartbeat) | P1.b'' | I1, I2 | **R** (C31 occupied this slot pre-M24.1; reserved for M27+ owner-succession FSM) |
| C13 | `peer_attestation_revoked_egress` | L1_GOVERNANCE §5 + L1_SKIN §3.1 | Federation envelope emitted to a peer whose attestation appears on anchor-surface revocation list | P8 | I7 | **U** |
| C14 | `untyped_mutation` | L1_GOVERNANCE §1.1 | Mutation envelope cannot be classified by the I2 classifier function (returns `untyped`) | P1.b'/P1.b'' | I2 | **L** (emitted as `untyped_mutation_blocked`) |
| C15 | `classifier_fixed_point_bypass` | L1_GOVERNANCE §1.2 | Attempt to mutate classifier dimension table or classifier function via non-CI path | P1.b'' | I2 | **U** |
| C16 | `mortality_signal_suppression` | L1_GOVERNANCE §4.4 + L1_TROPISM §B2 | Mortality-signal threshold or update-rule mutated via non-CI path (per L0 P7 mortality-signal protection clause) | P7 | I1, I2 | **U** |
| C17 | `operator_witness_forgery` | L1_GOVERNANCE §2.2 | `operator_witness` signature on attestation envelope does not verify against the operator_signing_key_public from the substrate's logged handshake | P1.c | I1, I2 | **L** (emitted) |
| C18 | `canonical_bytes_render_drift` | L0 §9.3.1 + §9.3.2 | Anchor-surface client's render of canonical bytes does not produce the same canonical hash the substrate signed | P1.b'' | I2 | **L** (emitted; cross-language byte parity verified Rust/Python/TS) |
| C19 | `paused_dormancy_unsafe_host` | L1_CONTINUITY §2.4 + §3.2 | Substrate process terminated (not suspended) during paused dormancy; routes through cold-resume quarantine | P7, P1.c | I1 | **R** (C32 occupied this slot pre-M24.1) |
| C20 | `genesis_attestation_chain_broken` | L1_GOVERNANCE §4.1 + L0 §9.2.1 | Substrate-ID's birth attestation signature does not verify against anchor-surface birth attestation record | P1.a | I1 | **R** (C33 occupied this slot pre-M24.1; reserved for M-anchor-2 substrate-ID birth attestation) |

**Each L1 catalog CRITICAL row above is INDEPENDENT** — none can be silently downgraded to elevated/daily by any L1 mutation (per §1's L0 trace and classifier-fixed-point in I2).

**Coverage as of 2026-05-17 (M26-cascade A6)**: 7 of 20 L1-catalog C-rows are EMITTED with matching labels (C5, C6, C7, C9, C14, C17, C18). 13 are unimplemented (U) or label-reserved post-M24.1 namespace cleanup (R). Closing the unimplemented set is **M27+ work** (depends on importing stranded `kernel/skin`, `kernel/continuity::DormancyMachine`, and `kernel/governance::classifier` libraries — see M24 snapshot).

### §1.2 Substrate-private catalog rows (C30+)

Per `myco_substrate/src/events.rs` M24.1 namespace doctrine: detectors needed for live-substrate correctness but NOT in the L1 catalog occupy the C30+ namespace. Reserved range so future L1 revisions can extend the formal catalog (C21-C29) without renumber thrash.

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace | Status / Provenance |
|---|---|---|---|---|---|---|
| C30 | `handshake_pubkey_mismatch` | L1_SKIN §4.1 | Operator presented `operator_signing_key_public` differs from prior pinned value (TOFU mismatch) | P1.c | I1, I8 | **L** (emitted; was misnamed C2 pre-M24.1) |
| C31 | `cycle_step_failed` | L1_CONTINUITY §1.1 | Metabolic-cycle step raises uncaught error; substrate state may be inconsistent | P3, P6 | I3, I4 | **L** (emitted; was misnamed C12 pre-M24.1) |
| C32 | `substrate_state_orphan_detected` | L1_SCHEMA §2.5 | DAG-tip references node not stored on disk; orphan in active tier | P5 | I4, I5 | **L** (emitted; was misnamed C19 pre-M24.1) |
| C33 | `federation_peer_identity_mismatch` | L2_FEDERATION §6 + L1_SKIN §3 | Federation peer's offered substrate_id differs from prior pin (federation-side TOFU mismatch) | P8 | I7 | **L** (emitted; was misnamed C20 pre-M24.1) |
| C34 | `birth_period_violation_during_quarantine` | L1_TROPISM §4 + L1_CONTINUITY §5 | Substrate emits sporocarp / accepts CI mutation while simultaneously in birth period AND quarantine | P1.b'', P7 | I2 | **L** (emitted; was misnamed C21 pre-M24.1) |
| C35 | `federation_substrate_private_event_injection` | L2_FEDERATION §6 + L1_SKIN §3 | Peer attempts to inject substrate-private event type (`operator_pinned`, `cycle_advanced`, `genesis_event`) via federation pull; allowlist breach | P8, P1.c | I7, I8 | **L** (Phase β fix; enforces ALLOWLIST-based federation safety + wrapped-envelope architecture) |
| **C36** | `cycle_backlog` | L1_CONTINUITY §1.2 | Cycle duration ≥5s OR backlog ≥10 cycles pending in mpsc bus (per L0 §6 metabolic cycle existence + L2_OBSERVABILITY §7) | P11 (metabolic economy: compute saturation) | I10 (metabolic-economy observation) | **L** (M24-shipped; emitted by main loop on cycle pacing failure) |
| **C37** | `doctrine_instability_burst` | L1_GOVERNANCE §6 (rollback) + L0 §9.4 + L2_OBSERVABILITY §8 | >10 CI events (any combination of attestations, classifier mutations, owner-key rotations, L0/L1 revision events) within rolling 100-substrate-cycle window | P3 (resumable evolution; bursts indicate doctrine thrash) | I2 (classifier fixed-point), I4 (DAG records bursts) | **L** (M25.1-shipped; window currently substrate-cycle-based — DRAFT 9 SEALED §13.1 demands wall-clock window; **M26-cascade post-fix required**) |
| **C38** | `snapshot_integrity_violation` | L1_SCHEMA §4 (tier-1 validation) | `snapshot.cb` Ed25519 signature fails verification against logged signer_pubkey OR signer_pubkey not in `owner_key_history` active-prefix | P1.c (substrate-secret integrity), P6 (causality integrity) | I1, I4 | **L** (M25.0-shipped; per L0 §9.4 anchor-surface receives canonical bytes + witnesses) |
| **C39** | `federation_hello_signature_invalid` | L2_FEDERATION §6 + §6.2 | Peer HELLO envelope's Ed25519 signature over the peer's claimed substrate_id fails verification | P8 (federation), P1.c (identity carrier) | I7 | **L** (M25.4-shipped; closes Phase β federation mutual-auth gap; per L0 §9.4 witnesses-not-verdicts) |
| **C40** | `bet_weakening_quorum` | L1_GOVERNANCE §observatory + L0 §7.4 + L2_OBSERVABILITY §3 | Within a 90-day **wall-clock** window (per L0 §7.4.a; M25.2 implementation uses substrate-cycle window — **post-M25.2 wall-clock correction is M26.x work**), ≥3 of countable signals {#1, #2, #3, #4a, #4b, #6} trend against the bet (OLS-slope significance gate Z≥1.96) AND signal #6 stays <1 for ≥50% of cycles in the window | P14 (telos — bet weakening = pair value falsifiability) | I12 (telos alignment) | **L** (M25.2-shipped; window-unit correction pending) |
| **C41** | `dag_cb_integrity_violation` | L1_SCHEMA §2.1 + L0 §9.4 wrapper integrity | `dag.cb` wrapper file integrity check fails — file truncated, hash chain inconsistent, or signature-attestation missing where one is required (per L0 §9.4 wrapped events architecture) | P1.c (carrier integrity), P6 (causality), P10 (compression-invariant set survival) | I4 (Merkle DAG integrity), I9 (compression discipline) | **U** (Phase γ.9 mycoparasite M4 finding; DEFERRED to M28-cascade — `dag.cb` currently has NO signature attestation, integrity is implicit-trust-on-disk) |
| **C42** | `manifest_cb_integrity_violation` | L1_SCHEMA §4 (tier-1 validation) | `manifest.cb` integrity check fails — content hash inconsistent OR signature missing (per L0 §9.4 wrapped attestation) | P1.c, P6 | I1, I4 | **U** (Phase γ.9 mycoparasite M5 finding; DEFERRED to M28-cascade — `manifest.cb` currently lacks signature attestation; mirrors C41) |
| **C43** | `federation_recursive_injection` | L2_FEDERATION §6 + L1_SKIN §3 | Peer wrapped event whose inner content prefix matches another `federation_received:` prefix — substrate-private federation envelope recursion (depth >1 forbidden absent owner attestation) | P8, P1.c | I7, I8 | **U** (Phase γ.9 mycoparasite M11 finding; DEFERRED to M28-cascade — current C35 allowlist blocks inner substrate-private types but does not specifically block nested `federation_received:` recursion) |
| **C44** | `nonce_substrate_minted_replay` | L1_GOVERNANCE §2.2 + L0 §9.2.5 | Substrate-minted nonce reused across two distinct attestation envelopes within nonce-TTL window (per L0 §9.2.5 anchor-surface SHOULD be sole minter; current implementation has substrate mint nonces — pre-mintable + replayable by insider attacker) | P1.b'' | I2 | **U** (Phase γ.9 mycoparasite M2 finding; DEFERRED to M-anchor-3 — full mitigation requires anchor-surface-generated nonces; substrate-mint is honor-system) |
| **C45** | `substrate_id_low_entropy_collision` | L1_GOVERNANCE §4.1 + L0 §9.2.1 | Genesis attempted with `substrate_id = sha256(time \|\| pid \|\| stack_addr)` producing < L1-tunable Shannon-entropy floor (default 2^16); insider attacker can guess substrate_id | P1.a (substrate-ID genesis) | I1 | **U** (Phase γ.9 mycoparasite M3 finding; DEFERRED to M-anchor-2 — full mitigation requires owner-attested random seed at substrate-ID genesis; current substrate-ID composition is honor-system) |
| **C46** | `owner_succession_bypass` | L1_GOVERNANCE §3.2 | Substrate transitions to `alive::normal` via succession path WITHOUT a valid `succession_acceptance_attestation` (per L1_GOVERNANCE §3.2.C); attacker attempts to skip the legacy/orphaned states | P1.b'', P7 | I1, I2 | **U** (DRAFT 9 cascade addition per L1_GOVERNANCE §3.2; depends on M-anchor-3 heartbeat services + succession FSM implementation) |
| **C47** | `generation_depth_exceeded` | L1_GOVERNANCE §16.A + L1_SCHEMA §3.1 | A `sprout_child` attempt where parent's `reproduction_lineage_depth` ≥ L1-tunable maximum (default 10) AND no Cultivator-attested `depth_override` at the anchor surface | P8 | I7 | **U** (DRAFT 9 cascade addition per L0 §16 → L1_GOVERNANCE §16 cascade; depends on M27 implementation) |
| **C48** | `reproduction_rate_exceeded` | L1_GOVERNANCE §16.B | A `sprout_child` attempt within `reproduction_rate` window (default: 1 sprout per 24h anchor-clock); attacker-driven forkbomb pattern | P8 | I7 | **U** (DRAFT 9 cascade addition per L0 §16 → L1_GOVERNANCE §16 cascade; depends on M27 implementation + M-anchor-3 anchor-clock services) |
| **C49** | `consensus_floor_bypass` | L2_FEDERATION §6.5 | Population-level claim (peer revocation, universal-junk classification, aggregate observability) accepted by substrate WITHOUT going through ≥3-peer Byzantine consensus protocol (per L2_FEDERATION §6.5.a-c) | P8, P15 | I7 | **U** (DRAFT 9 cascade addition per G-7.c P15 retraction to L2_FEDERATION; depends on M27 + future L2_FEDERATION Tendermint-style PBFT implementation) |

**Coverage as of 2026-05-17 (M26-cascade A6 + reconciliation)**: C30-C40 emit (11 substrate-private detectors shipped). C41-C49 are Phase γ.9 mycoparasite findings + DRAFT 9 cascade additions, all DEFERRED to M28-cascade / M-anchor / M27 milestones — they are doctrinally enumerated here so that future implementation has a stable label namespace.

### §1.3 Mortality- and bet-related additional sporocarps (cross-ref §1 of catalog)

C40 `bet_weakening_quorum` interacts with L0 §7.5 bet retirement:
- C40 fires → owner re-justification → counter reset (success) OR counter increment (failure)
- After 3 consecutive failed re-justifications over 2-year wall-clock window AND signal #6 <0.1 for >75% of samples in final 90-day window → substrate emits `bet_retired_proposal` (NOT immune sporocarp; CI-level proposal requiring owner co-attestation per §7.5.b two-phase commit)
- On owner co-attestation accept → substrate emits `bet_retired_executed:{axis_name}` + transitions to `alive::archived` sub-state (per L0 §7.5.c terminal state semantics; distinct from Destroyed because state_dir is preserved with anchor seal)

This is **not a CRITICAL breach** (substrate is not pathological; it is gracefully retiring) — it is a **CI-level lifecycle transition** parallel to `self_euthanasia_executed`. Cross-referenced here for catalog completeness.

## §2. Contract-identity-level fixed points (unconditionally CI; cannot be re-classified)

These are L0-doctrinal fixed-points whose CI-level status is unconditional, NOT subject to classifier dimension table mutation:

| # | Fixed-point | Defined at | L0 trace | I trace |
|---|---|---|---|---|
| F1 | The classifier dimension table itself + the classifier function | L0 I2, L1_GOVERNANCE §1.2 | P1.b'' | I2 |
| F2 | `substrate-ID` field (immutable post-genesis) | L0 I1, L1_GOVERNANCE §4.1 | P1.a, P1.c | I1 |
| F3 | `owner_key_history` (active-prefix + archived-tail per L1_GOVERNANCE §3.1) | L0 I1, L1_GOVERNANCE §3.1 | P1.b'', P1.c | I1 |
| F4 | `anchor_surface_endpoint_public_key` (owner-controlled at genesis) | L0 §9, L1_GOVERNANCE §4.1 | P1.b'' | I2, I8 |
| F5 | `substrate_secret_sealing_mechanism_attestation` (owner-attested at genesis) | L1_SKIN §4.2, L1_GOVERNANCE §4.1 | P1.c | I1, I6 |
| F6 | `anchor_client_provenance_attestation` (owner-attested at genesis; per L0 §9.3.3 provenance independence; currently 0% — M-anchor-1) | L0 §9.3.3, L1_GOVERNANCE §4.1 | P1.b'' | I2 |
| F7 | Mortality-signal threshold + update-rule + threshold_emergence_rule for mortality axis | L0 P7, L1_GOVERNANCE §1.2 | P7 | I1 |
| F8 | SSoT designation (what counts as SSoT, what fields, claim coverage) | L0 I3, L1_SCHEMA §1.2 | P3 | I3 |
| F9 | DAG retention policy (per DRAFT 9 SEALED: I4-compression-aware + P10.b compression-invariant set; F9 mutation = adding/removing items from invariant set; cold-tier archival is contract-identity-level) | L0 I4 + I9 (DRAFT 9 SEALED), L1_SCHEMA §2.5 | P6, P10 | I4, I9 |
| F10 | Storage tier exemption from I5 reachability | L0 I5, L1_SCHEMA §2.3 | P5 | I5 |
| F11 | Skin surface declaration (intake + output endpoints + forbidden surfaces) | L0 I8, L1_SKIN §1 | P9 | I8 |
| F12 | Appetite-axis schema + sporocarp-type tree (under L1_TROPISM dispatch) | L1_GOVERNANCE §1.2 | P3 | I2 |
| F13 | Threshold_emergence_rule for ANY axis (under L1_TROPISM dispatch) | L1_GOVERNANCE §1.2 | P3 | I2 |
| F14 | Federation peer attestation list (incl. revocations) | L0 P8, L1_GOVERNANCE §5 | P8 | I7 |
| F15 | `template_version_registry` (active-prefix + archived-tail; L1_TROPISM §B1) | L1_TROPISM §B1, L1_GOVERNANCE §1.2 | P3, P6 | I2, I4 |
| F16 | `canonical_bytes_serializer_spec` (spore-inheritable, tier-1 SSoT, pure declarative) | L1_SCHEMA §3.1, §4.1 | P1.c, P6 | I1, I3, I4 |
| F17 | `cluster_C` (L1_TRAJECTORY clustering algorithm) | L1_TRAJECTORY §4 | P6 | I4 |
| **F18** | **Selective compression rule set** (per L0 P10.c; compression-rule registry is spore-inheritable; each rule is CI-attested per L0 P10.c with witness emission; rules generate compression events that produce `compression_event` sporocarp witnesses per I9) | L0 P10 + I9 (DRAFT 9 SEALED), L1_SCHEMA §2.5 + §3.1, **L1_GOVERNANCE §1.2 (A5 primary spec)** | P10 | I9 |
| **F19** | **Metabolic cost budgets** (per L0 P11.a abstract cost units + P11.b cost-budget signals + P11.c ordered fallback; L1-budgeted thresholds for persistence cost, compute cost, network cost; mutation of budget threshold = CI; tier-1 SSoT field per L1_SCHEMA §4) | L0 P11 + I10 (DRAFT 9 SEALED), L1_SCHEMA §4, L1_CONTINUITY §1.2, **L1_GOVERNANCE §1.2 (A5 primary spec)** | P11 | I10 |
| **F20** | **Telos-alignment metric** (per L0 P14.a substrate-internal purpose + P14.c drift detection; M26-cascade forcing function — L1_TROPISM operationalizes the metric; the **metric specification itself** is CI; substrate cannot tune the metric to suppress drift signals; owner-stated objectives per P14.b are also CI-attested when present) | L0 P14 + I12 (DRAFT 9 SEALED), **L1_TROPISM §B-telos (A1 primary spec)**, L1_GOVERNANCE §1.2 | P14 | I12 |
| **F21** | **Cultivation successor_chain registry** (per L0 §15.1 succession states + §1.4 Cultivation transferability; successor_chain is anchor-resident at §9.2.7 owner-liveness-heartbeat layer; successor attestations + revocations + activation events live there; per G-11.a the Cultivator-side of the Cultivation relationship is what changes across succession, not the Cultivar's substrate-ID) | L0 §15 (DRAFT 9 SEALED), **L1_GOVERNANCE §3.2 (A5 primary spec)** | P1.b'', P7 | I1 |
| **F22** | **Reproduction generation discipline** (per L0 §16.1 generation-depth bound + §16.2 reproduction rate + §16.3 per-parent quota; spore-schema MUST carry `(generation_depth, max_remaining_depth)` field; bounds are CI-attested; override is anchor-attested CI mutation; seed values from DRAFT 9 PROPOSAL: depth=10, rate=24h, quota=100) | L0 P8 (Generation-Bounded) + §16 (DRAFT 9 SEALED), **L1_GOVERNANCE §4.3 (A5 primary spec)**, L1_SCHEMA §3.1 | P8 | I7 |
| **F23** | **Duress_keypair registration** (per L0 §14.1 adversarial-owner threat model + §14.2 substrate's irreducible commitments; owner registers a duress keypair at genesis whose use triggers structural responses without alerting the coercer — substrate emits silent observability events recording duress signature; the duress keypair list + its trigger rules are CI-attested; cannot be silently revoked) | L0 §14 (DRAFT 9 SEALED), **L2_TRUST_MODEL §X (A5 primary spec)**, L1_GOVERNANCE §3.1 | P1.b'' | I1, I2 |
| **F24** | **Substrate-private signing keypair seed** (per Phase γ.9 mycoparasite M3 finding + L0 §9.2.1 substrate-ID birth attestation; the seed material for substrate's own signing keypair — used for snapshot.cb signatures, federation HELLO signatures, etc. — must be CI-attested at genesis with owner co-attestation over the keypair fingerprint; substrate cannot silently rotate this keypair without re-attestation; per L0 P10.b also part of compression-invariant set) | L0 §9.2.1 + P1.c + Phase γ.9 finding (DRAFT 9 SEALED), **L1_GOVERNANCE §4.1 (A5 primary spec)**, L1_SCHEMA §4 tier-1 | P1.a, P1.c | I1 |

**Mutation of any F-row requires anchor-surface owner attestation** with all the protocol elements from L1_GOVERNANCE §2.2 (canonical bytes + operator_witness + anchor-side nonce + dual-clock + DAG-enumeration closure check). Per DRAFT 9 SEALED §9.2.5, nonces are anchor-surface-generated (NOT substrate-mintable) — the M-anchor-3 milestone closes the implementation gap.

**F18-F24 coverage status (2026-05-17, M26-cascade A6)**:
- F18 compression rules: **unimplemented**; L0 P10 doctrine sealed; L1_SCHEMA + L1_GOVERNANCE M26-cascade A2/A5 deferred work.
- F19 cost budgets: **unimplemented**; L0 P11 doctrine sealed; L2_OBSERVABILITY §2 signals #7/#8/#9 specified (this cascade); L1 budget tables M27+.
- F20 telos metric: **unimplemented**; L0 P14 M26-cascade forcing function active — L1_TROPISM A1 cascade has bounded deadline.
- F21 succession registry: **unimplemented**; L0 §15 doctrine sealed; L1_GOVERNANCE A5 cascade adds.
- F22 generation discipline: **unimplemented**; L0 §16 doctrine sealed; L1_GOVERNANCE A5 cascade adds seed values.
- F23 duress keypair: **unimplemented**; L0 §14 doctrine sealed; L2_TRUST_MODEL A4 cascade adds full mechanism.
- F24 substrate signing keypair: **partially implemented** via M25 snapshot.cb signing + M25.4 federation HELLO; CI attestation of the seed itself is unimplemented (M-anchor-2 milestone).

## §3. Birth-period CI elevation (transitional)

During the substrate's birth period (per L1_TROPISM §4 + L1_GOVERNANCE §1.3), **ALL parameter-tuning events are contract-identity-level** regardless of steady-state classification — even those that would be daily in steady state. The reclassification to daily-autonomous happens at owner-attested birth-period termination.

This index row exists to mark the transition pattern, not to enumerate every birth-period CI event (the set is open-ended). The L0 / L1_GOVERNANCE classifier observes the birth-period flag and elevates accordingly.

**Per L0 §7.4.e + DRAFT 9 SEALED Phase γ.9 primordium CF6**: bet_weakening_quorum (C40) is **SUSPENDED during birth period** — substrate emits `bet_weakening_evaluation_suspended` observability event instead. Reason: at t=0 signal #6 is structurally <1 (no content yet), signal #1 is monotone-growing-from-zero, signal #3 is structurally zero. Per L0 P14.c, `telos_drift` similarly has birth-period exemption — substrate emits `telos_alignment_pending` instead.

## §4. Anchor-surface-resident state (substrate cannot author)

The substrate cannot author the following — they live exclusively at the anchor surface and are owner-controlled. Per L0 §9.2 DRAFT 9 SEALED decomposition, each is mapped to a specific sub-mechanism:

- Anchor-surface-generated nonces + consumed-nonce log (L0 §9.2.5 + L1_GOVERNANCE §2.2; current implementation is substrate-mint per Phase γ honor-system gap C44; M-anchor-3 milestone)
- Anchor-surface trusted wall-clock timestamps (L0 §9.2.6; current implementation is operator-process-as-clock-source; M-anchor-3 milestone)
- Owner-liveness heartbeat (L0 §9.2.7 + L1_GOVERNANCE §3.2 succession trigger + DRAFT 9 SEALED §15.2; library exists, zero non-test callers; M-anchor-3 milestone)
- Owner-key rotation cooldown veto window (L1_GOVERNANCE §3.1)
- `successor_attestation` records + revocations (L1_GOVERNANCE §3.2 + L0 §15 + F21)
- `anchor_surface_final_seal` (L1_GOVERNANCE §4.4 — terminal destruction record)
- Anchor-surface client distribution / provenance attestation (L0 §9.3.3, L1_GOVERNANCE §4.1; M-anchor-1 milestone)
- Federation peer revocation list (L1_GOVERNANCE §5)
- Aggregate-reattestation peer-set Merkle commitments (L1_GOVERNANCE §5.2)
- L0/L1 revision diff records (L0 §9.2.4 + §9.4 doctrine-instability; this maps to C37 detector)
- DAG-tip co-signing logs with enumerated nodes (L0 §9.2.2; M-anchor-5 milestone closure check)
- Substrate-ID birth attestation (L0 §9.2.1; M-anchor-2 milestone)
- Generation-counter ceiling (per F22; anchor-attested per L0 §16.2; L1 may delegate substrate-resident counter with anchor-attested ceiling — L1_GOVERNANCE chooses)

Any substrate-side attempt to forge or shadow-mirror these is breach (specifically: such mutation classifies as `untyped` per C14 above and is rejected at the skin).

## §5. Cross-doc consistency claims

This doc carries NO new normative content. Every row is a citation. Drift between this doc and its source L1 doc resolves to the source L1 doc as canonical.

When source L1 docs are updated (CI events), this doc updates as part of the same attestation event (it's a tier-2 SSoT field at L1_SCHEMA; not tier-1 because it's derivative).

**M26-cascade A6 alignment** (this DRAFT 2): C36-C40 substrate-private rows are sourced from `myco_substrate/src/events.rs` M24+ doctrine block (live emit sites). C41-C45 are sourced from Phase γ.9 mycoparasite findings + DRAFT 9 SEALED Phase γ §17 G-10.c hybrid sealing decision (deferred to cascade work). F18-F24 are sourced from DRAFT 9 SEALED §2.3 (P10/P11/P14), §14, §15, §16.

## §6. What this doc is NOT

- NOT a duplication of v0.8 R1-R7. R1-R7 was an imperative-rules grammar; this is an enumeration of breach + fixed-point surfaces.
- NOT load-bearing normative content. Every row cites a load-bearing source doc.
- NOT a replacement for the source docs. Reading this doc alone is insufficient to operate v0.9; it indexes the docs that ARE sufficient.
- NOT a v0.8 contamination per C7.3 — each row independently traces to ≥1 P + ≥1 I; the v0.8 R-rule grammar is structurally absent.
- NOT the immune system itself. The immune system is L4 substrate code that **uses** this catalog to detect breach.

## §7. Open at L1 / L4 design questions surfaced by this index

- **Immune-system architecture**: how does L4 implement detection for the 20 L1-catalog C-rows + 16 substrate-private (C30-C45) detectors? Per-row dedicated detector? Generic event-stream filter? L4 picks. Current implementation: dedicated per-row detector modules under `myco_substrate/src/` with shared sporocarp-emission discipline.
- **Sporocarp emission cadence**: when C-grade breach detected, does substrate fruit immune sporocarp the same metabolic cycle, or queue for next cycle? Current implementation emits same-cycle; rationale = under L0 §6 metabolic-cycle existence, sporocarp emission IS a metabolic event.
- **F-row mutation rate observability**: F-rows should mutate rarely. If multiple F-rows mutate within an L1-tunable window, is this `f_row_thrash` immune signal? Recommend yes; L4 spec'd. Per L0 §9.4 doctrine-instability burst, F-row mutations count as L0/L1 revisions and feed C37 detector window.
- **C41-C45 deferred work**: M28-cascade (mycoparasite findings) + M-anchor-2/M-anchor-3 (low-entropy substrate_id, substrate-minted nonces) are the implementation paths. Each requires owner co-attestation at the anchor-surface client + substrate-side detector wiring.
- **F18-F24 implementation order**: A5 cascade adds the L1_GOVERNANCE primary specs; this catalog row enumerates the labels. Implementation depends on M27+ (stranded-library imports) + M-anchor-1 through M-anchor-5 (anchor surface closures).

## §8. Glossary additions (DRAFT 2)

| Term | Definition |
|---|---|
| **L1 catalog C-row** | C1-C20 — formal L1_HARD_RULES §1.1 entries. 7 currently emitted with matching labels; 13 unimplemented or label-reserved post-M24.1. |
| **Substrate-private C-row** | C30+ — detectors live in `myco_substrate/src/events.rs` that exist for substrate correctness but not in the formal L1 catalog. Reserved range so future L1 revisions can extend C21-C29 without renumber thrash. |
| **R status** | "Reserved" — the L1 catalog label is preserved; the previously-misnamed emit site has been renamed into C30+ namespace per M24.1 doctrine cleanup; awaiting future L1-catalog implementation. |
| **L status** | "Live" — the L1 catalog label is emitted in substrate code at runtime with matching tag. |
| **U status** | "Unimplemented" — the L1 catalog label is reserved but no substrate emit site exists yet; depends on stranded-library import (M27+) or anchor-surface milestone closure (M-anchor-1 through M-anchor-5). |
| **Cultivation / Cultivator / Cultivar** (G-11.a) | Owner-substrate relationship per L0 §1.2 DRAFT 9 SEALED. Cultivator = owner (relational role); owner = same party (governance role). Cultivar = substrate-as-cultivated-species. "Quarantine clearance is Cultivator-attested" = "owner attests; the doctrinal vocabulary is Cultivation". Both vocabularies remain valid; new doc additions prefer Cultivation terminology per G-11.a. |
| **bet_retired_proposal / bet_retired_executed** | CI-level lifecycle proposals per L0 §7.5.b two-phase commit. NOT immune sporocarps. Trigger: 3 consecutive failed re-justifications over 2-year wall-clock + signal #6 <0.1 for >75% of samples in final 90-day window. Execution: owner co-attestation per genesis-time `bet_retirement_consent_at_genesis` flag (DRAFT 9 SEALED §7.5.b two-phase commit). |
| **Compression-invariant set** (per F18 + L0 P10.b) | The set of substrate state surviving any compression event: substrate-ID, owner_key_history, ALL CI-attested events, mortality signal events, federation peer pin events, most recent N cycles (≥1000, L1-tunable, monotone-non-decreasing per Phase γ.9 hypha C5 fix) of full DAG, **substrate-private signing keypair seed (F24)**. |
| **M-anchor-N milestones** (per L0 §9.2 status table) | M-anchor-1 (anchor-client provenance independence + owner-side rendering live consumer), M-anchor-2 (substrate-ID birth attestation + low-entropy fix C45), M-anchor-3 (anchor-surface-generated nonces + anchor-stamped wall-clock + owner-liveness-heartbeat), M-anchor-4 (witnesses-not-verdicts + anchor-nonce-derived sampling), M-anchor-5 (L0 revision diff workflow + DAG-tip co-signing closure check). DRAFT 9 SEALED commits to all 5 as future milestone blocks; this catalog references them as closure paths for U-status rows. |
