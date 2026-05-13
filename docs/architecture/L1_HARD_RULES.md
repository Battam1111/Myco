# L1 — Hard Rules (cross-cuts index)

> **Status**: DRAFT 1 (2026-05-13). Cross-cuts index for the 6 mechanism L1 docs. NOT a v0.8 R1-R7 grammatical inheritance — it is a normative enumeration of CRITICAL-grade breach surfaces + contract-identity-level fixed points, drawn from the 6 mechanism docs as a single source of truth for L4 immune-system construction.
> **Layer**: L1. Governed by L0.
> **Scope**: indexes (does not duplicate) the enforcement targets across L1_SKIN, L1_CONTINUITY, L1_GOVERNANCE, L1_SCHEMA, L1_TROPISM, L1_TRAJECTORY. When L4 implements the immune system, this doc is the enumeration of "what to detect" — CRITICAL breaches that auto-quarantine + CI fixed-points that owner-attestation is unconditionally required for.
> **L0 traceability** (per C7.3 v0.8-origin discrimination — this doc traces independently to L0): every row in §1 and §2 below cites at least one P (P1-P9) AND one I (I1-I8) it enforces. The G-rules grammar of v0.8 is NOT inherited; the index pattern is independently derived from L0's invariants.

---

## §1. CRITICAL-grade breaches (auto-quarantine triggers)

A CRITICAL-grade breach immediately transitions the substrate to `alive but quarantined` (per L1_CONTINUITY §5) and emits the named immune sporocarp. Owner-attested `quarantine_clearance` is required for resumption.

| # | Breach name | Detection site | Detection mechanism | L0 trace | I trace |
|---|---|---|---|---|---|
| C1 | `appetite_locality_breach` | L1_SKIN §5 | Network-egress detection — any traffic exits substrate process outside declared output endpoints | P2.a (strong inclusion), P9 (skin) | I6 (universal inclusion), I8 (skin) |
| C2 | `output_endpoint_breach` | L1_SKIN §3 + §6 | Output to non-declared endpoint | P9, P2.a | I8, I6 |
| C3 | `post_handshake_ci_unattested` | L1_SKIN §4.3 | CI-level operation during post-handshake quarantine window without fresh attestation | P1.b'' | I2, I8 |
| C4 | `substrate_secret_unsealed` | L1_SKIN §4.2 | substrate_secret detected in substrate-process address space (not OS-sealed) | P1.c, P1.a | I1 |
| C5 | `attestation_invalid` | L1_GOVERNANCE §2.3 | Owner signature fails verification OR nonce reuse OR expiry-clock-mismatch (substrate-cycle / wall-clock dual check) | P1.b'' | I2 |
| C6 | `dag_enumeration_unclosed` | L1_SCHEMA §2.2 | At CI co-sign, enumerated DAG-nodes include a parent-hash that does not resolve to ancestor of prior tip OR another enumerated node | P6, P3 | I4 |
| C7 | `dag_retro_edit_detected` | L1_SCHEMA §2.1 | Merkle DAG node hash mismatch from re-computation | P6 | I4 |
| C8 | `ssot_migration_phase_skip` | L1_SCHEMA §1.3 | Single-step SSoT migration without ≥M cycles of dual-validation phase | P3 | I3 |
| C9 | `cold_resume_invariant_failure` | L1_CONTINUITY §3.1 | Any of I1/I3/I4/I5/I8 pre-handshake check fails (witnesses fail re-derivation at anchor-surface verifier) | P1.c, P3, P9 | I3, I4, I5, I8 |
| C10 | `agent_discriminating_attribute_persisted` | L1_SCHEMA §3.1 + L1_SKIN §4.2 | Persistent storage of model-name / API-fingerprint / host-fingerprint / deterministic-operator-token | P1.c | I1 |
| C11 | `concurrent_operator_persistent` | L1_SKIN §4.4 | Two operator-tokens simultaneously valid for the same substrate beyond the strict-FIFO handshake serialization window | P1.c | I8 |
| C12 | `successor_activation_with_fresh_owner_heartbeat` | L1_GOVERNANCE §3.2 | Successor `successor_activation` event fires while owner liveness heartbeat is fresh at anchor surface | P1.b'' | I1, I2 |
| C13 | `peer_attestation_revoked_egress` | L1_GOVERNANCE §5 + L1_SKIN §3.1 | Federation envelope emitted to a peer whose attestation appears on anchor-surface revocation list | P8 | I7 |
| C14 | `untyped_mutation` | L1_GOVERNANCE §1.1 | Mutation envelope cannot be classified by the I2 classifier function (returns `untyped`) | P1.b'/P1.b'' | I2 |
| C15 | `classifier_fixed_point_bypass` | L1_GOVERNANCE §1.2 | Attempt to mutate classifier dimension table or classifier function via non-CI path | P1.b'' | I2 |
| C16 | `mortality_signal_suppression` | L1_GOVERNANCE §4.4 + L1_TROPISM §B2 | Mortality-signal threshold or update-rule mutated via non-CI path (per L0 P7 mortality-signal protection clause) | P7 | I1, I2 |
| C17 | `operator_witness_forgery` | L1_GOVERNANCE §2.2 | `operator_witness` signature on attestation envelope does not verify against the operator_signing_key_public from the substrate's logged handshake | P1.c | I1, I2 |
| C18 | `canonical_bytes_render_drift` | L0 §9.3 | Anchor-surface client's render of canonical bytes does not produce the same canonical hash the substrate signed | P1.b'' | I2 |
| C19 | `paused_dormancy_unsafe_host` | L1_CONTINUITY §2.4 + §3.2 | Substrate process terminated (not suspended) during paused dormancy; routes through cold-resume quarantine | P7, P1.c | I1 |
| C20 | `genesis_attestation_chain_broken` | L1_GOVERNANCE §4.1 + L0 §9.2 | Substrate-ID's birth attestation signature does not verify against anchor-surface birth attestation record | P1.a | I1 |

**Each CRITICAL row above is INDEPENDENT** — none can be silently downgraded to elevated/daily by any L1 mutation (per §1's L0 trace and classifier-fixed-point in I2).

## §2. Contract-identity-level fixed points (unconditionally CI; cannot be re-classified)

These are L0-doctrinal fixed-points whose CI-level status is unconditional, NOT subject to classifier dimension table mutation:

| # | Fixed-point | Defined at | L0 trace | I trace |
|---|---|---|---|---|
| F1 | The classifier dimension table itself + the classifier function | L0 I2, L1_GOVERNANCE §1.2 | P1.b'' | I2 |
| F2 | `substrate-ID` field (immutable post-genesis) | L0 I1, L1_GOVERNANCE §4.1 | P1.a, P1.c | I1 |
| F3 | `owner_key_history` (active-prefix + archived-tail per L1_GOVERNANCE §3.1) | L0 I1, L1_GOVERNANCE §3.1 | P1.b'', P1.c | I1 |
| F4 | `anchor_surface_endpoint_public_key` (owner-controlled at genesis) | L0 §9, L1_GOVERNANCE §4.1 | P1.b'' | I2, I8 |
| F5 | `substrate_secret_sealing_mechanism_attestation` (owner-attested at genesis) | L1_SKIN §4.2, L1_GOVERNANCE §4.1 | P1.c | I1, I6 |
| F6 | `anchor_client_provenance_attestation` (owner-attested at genesis) | L0 §9.3, L1_GOVERNANCE §4.1 | P1.b'' | I2 |
| F7 | Mortality-signal threshold + update-rule + threshold_emergence_rule for mortality axis | L0 P7, L1_GOVERNANCE §1.2 | P7 | I1 |
| F8 | SSoT designation (what counts as SSoT, what fields, claim coverage) | L0 I3, L1_SCHEMA §1.2 | P3 | I3 |
| F9 | DAG retention policy (no lossy compression; cold-tier archival is contract-identity-level) | L0 I4, L1_SCHEMA §2.5 | P6 | I4 |
| F10 | Storage tier exemption from I5 reachability | L0 I5, L1_SCHEMA §2.3 | P5 | I5 |
| F11 | Skin surface declaration (intake + output endpoints + forbidden surfaces) | L0 I8, L1_SKIN §1 | P9 | I8 |
| F12 | Appetite-axis schema + sporocarp-type tree (under L1_TROPISM dispatch) | L1_GOVERNANCE §1.2 | P3 | I2 |
| F13 | Threshold_emergence_rule for ANY axis (under L1_TROPISM dispatch) | L1_GOVERNANCE §1.2 | P3 | I2 |
| F14 | Federation peer attestation list (incl. revocations) | L0 P8, L1_GOVERNANCE §5 | P8 | I7 |
| F15 | `template_version_registry` (active-prefix + archived-tail; L1_TROPISM §B1) | L1_TROPISM §B1, L1_GOVERNANCE §1.2 | P3, P6 | I2, I4 |
| F16 | `canonical_bytes_serializer_spec` (spore-inheritable, tier-1 SSoT, pure declarative) | L1_SCHEMA §3.1, §4.1 | P1.c, P6 | I1, I3, I4 |
| F17 | `cluster_C` (L1_TRAJECTORY clustering algorithm) | L1_TRAJECTORY §4 | P6 | I4 |

**Mutation of any F-row requires anchor-surface owner attestation** with all the protocol elements from L1_GOVERNANCE §2.2 (canonical bytes + operator_witness + anchor-side nonce + dual-clock + DAG-enumeration closure check).

## §3. Birth-period CI elevation (transitional)

During the substrate's birth period (per L1_TROPISM §4 + L1_GOVERNANCE §1.3), **ALL parameter-tuning events are contract-identity-level** regardless of steady-state classification — even those that would be daily in steady state. The reclassification to daily-autonomous happens at owner-attested birth-period termination.

This index row exists to mark the transition pattern, not to enumerate every birth-period CI event (the set is open-ended). The L0 / L1_GOVERNANCE classifier observes the birth-period flag and elevates accordingly.

## §4. Anchor-surface-resident state (substrate cannot author)

The substrate cannot author the following — they live exclusively at the anchor surface and are owner-controlled:

- Anchor-surface-generated nonces + consumed-nonce log (L1_GOVERNANCE §2.2 + L0 §9.2)
- Anchor-surface trusted wall-clock timestamps (L0 §9.2)
- Owner-liveness heartbeat (L0 §9.2 + L1_GOVERNANCE §3.2 succession trigger)
- Owner-key rotation cooldown veto window (L1_GOVERNANCE §3.1)
- `successor_attestation` records + revocations (L1_GOVERNANCE §3.2)
- `anchor_surface_final_seal` (L1_GOVERNANCE §4.4 — terminal destruction record)
- Anchor-surface client distribution / provenance attestation (L0 §9.3, L1_GOVERNANCE §4.1)
- Federation peer revocation list (L1_GOVERNANCE §5)
- Aggregate-reattestation peer-set Merkle commitments (L1_GOVERNANCE §5.2)
- L0/L1 revision diff records (L0 §9.4)

Any substrate-side attempt to forge or shadow-mirror these is breach (specifically: such mutation classifies as `untyped` per C14 above and is rejected at the skin).

## §5. Cross-doc consistency claims

This doc carries NO new normative content. Every row is a citation. Drift between this doc and its source L1 doc resolves to the source L1 doc as canonical.

When source L1 docs are updated (CI events), this doc updates as part of the same attestation event (it's a tier-2 SSoT field at L1_SCHEMA; not tier-1 because it's derivative).

## §6. What this doc is NOT

- NOT a duplication of v0.8 R1-R7. R1-R7 was an imperative-rules grammar; this is an enumeration of breach + fixed-point surfaces.
- NOT load-bearing normative content. Every row cites a load-bearing source doc.
- NOT a replacement for the source docs. Reading this doc alone is insufficient to operate v0.9; it indexes the docs that ARE sufficient.
- NOT a v0.8 contamination per C7.3 — each row independently traces to ≥1 P + ≥1 I; the v0.8 R-rule grammar is structurally absent.

## §7. Open at L1 / L4 design questions surfaced by this index

- **Immune-system architecture**: how does L4 implement detection for the 20 C-rows? Per-row dedicated detector? Generic event-stream filter? L4 picks.
- **Sporocarp emission cadence**: when C-grade breach detected, does substrate fruit immune sporocarp the same metabolic cycle, or queue for next cycle? L4 picks (per L1_CONTINUITY §1).
- **F-row mutation rate observability**: F-rows should mutate rarely. If multiple F-rows mutate within an L1-tunable window, is this `f_row_thrash` immune signal? Recommend yes; L4 spec'd.
