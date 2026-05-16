# L1 — Schema (SSoT, causal DAG, recoverability, spore-schema, validation tiers, canonical-bytes spec, snapshot integrity)

> **Status**: DRAFT 2 (M26-cascade for L0 DRAFT 9 SEALED, commit `e796451`). Authoritative L1 doc for SSoT + causal-DAG + recoverability + spore-schema + validation tiering + canonical-bytes serializer + i64-nanoseconds timestamps + year-2262 horizon-warning + snapshot.cb integrity wrapper + substrate_signing_key.cb mechanism. Does NOT cover: classifier function (→ L1_GOVERNANCE), envelope schema (→ L1_SKIN), cycle cadence (→ L1_CONTINUITY), dispatch atomic records (→ L1_TROPISM). Items marked **TBD-L4** are explicit deferrals.

---

## §1. SSoT — Single Source of Truth (operationalizes L0 I3)

### §1.1 Format

**TBD-L4** within these constraints:

- Machine-readable (parseable by L1-defined parser without dynamic dispatch).
- Append-most operations (mutations are sporocarps; SSoT is the materialized current-state view, regenerable from append log).
- Self-describing — a fresh agent reading the substrate cold can derive structure from the SSoT itself (no external schema documentation required, per L0 §8 mechanical readiness).

**Leading candidates** (none preferred at L1):
- YAML (legible; what v0.8 used — but L0 C7.3 max-discrimination forbids inheritance-by-default).
- TOML (more rigorous typing).
- JSON + JSONL append log (deterministic append-friendly).
- SQLite (native query; one-process locking).
- Custom binary + WAL (highest performance, lowest legibility — likely violates §8 cold-read).

**Decision rule for L4**: pick the format that minimizes "agent must learn an external schema" while supporting Merkle-hash content addressing (I4).

### §1.2 SSoT designation

What the SSoT *covers* — the claim space against which I3 self-validation runs — is itself a contract-identity-level object. L1_GOVERNANCE owns the classifier; this doc commits that:

- The designation lists exactly which substrate state fields participate in SSoT consistency check.
- Fields outside the SSoT designation are NOT exempt from I5 reachability or I4 causal coverage — only from I3 cycle consistency check.
- Designation evolution is two-phase per L0 I3 (new candidate consistent with current for ≥M cycles; owner co-signs).

### §1.3 SSoT migration two-phase commit (operationalizes L0 I3)

Per L0 I3 + L0 §10 ("L1 prototyping may surface L0 revision needs"): SSoT-designation evolution is itself a contract-identity-level mutation; the two-phase commit ensures the **migration window** is observable + bounded.

**M (cycles of consistency before commit)**:
- **Seed default**: **M = 100 metabolic cycles** of successful dual-validation (M26-cascade explicit seed per L0 §13.2 cascade requirement). The DRAFT 1 "M = 1000 OR 30 days" reads now as a maximum L4-tunable ceiling, not the seed.
- **L4-tunable** within the bounded range [100, 10000] cycles. Setting M outside this range requires CI attestation.
- The L1-tunable M is itself a **tier-1 SSoT field** (per §4.1 — it governs identity-critical migration cadence).

**Phase 1** (proposal + dual-validation):
- Owner co-signs `ssot_migration_proposal` at the anchor surface with canonical-bytes of both the current SSoT designation AND the candidate designation (per L0 §9.4 canonical-bytes doctrine).
- Substrate runs **dual-validation every cycle**: both current and candidate SSoT designations must independently produce a self-consistent I3 check result. Mismatch emits `ssot_migration_inconsistent` immune sporocarp; migration aborts; substrate continues under current SSoT.
- Phase 1 must complete with **≥M consecutive successful dual-validation cycles** with no `ssot_migration_inconsistent` events; the M counter resets on any inconsistency.

**Phase 2** (commit):
- Owner co-signs `ssot_migration_commit` at the anchor surface, including: (current_ssot_canonical_bytes_hash, candidate_ssot_canonical_bytes_hash, M_consecutive_count_observed, dual_validation_witness_sample).
- The **owner verifies the M-count witness** before signing — substrate cannot fake completion of Phase 1.
- Old SSoT is **retained as archived** per I4 (no lossy compression of CI-attested state; the prior SSoT designation joins the compression-invariant set per P10.b).

**Witnesses, not verdicts** (per L0 §9.3.4): substrate emits Merkle-chain proof of M consecutive Phase 1 cycles + sampled per-cycle dual-validation comparisons (sampling indices derived from anchor-surface nonce per §9.3.5), NOT a verdict-only `phase_1_passed` flag.

---

## §2. Causal DAG — storage, integrity, retention (operationalizes L0 I4)

### §2.1 Storage shape

**Content-addressed Merkle DAG**: each node carries a hash that incorporates parent-hashes. Node ID = node hash. Substrate's identity record carries the current **DAG-tip hash**.

Hash function: TBD-L4 within {SHA-256, BLAKE3, SHA-3-256}. Default proposal: BLAKE3 (parallelizable, modern, well-supported).

**Storage layout**: L4 chooses between:
- One file per node (filesystem-as-DAG; simple, slow at scale).
- Append-only log + index (faster lookup, manages many small nodes).
- Embedded KV store (e.g., LMDB / RocksDB).

L4 picks based on observed node-count distribution and read patterns.

### §2.2 Owner co-signing at CI boundaries (enumerated DAG nodes)

Per L0 §9.2: at every contract-identity-level boundary crossing, the owner co-signs the current DAG-tip hash via the anchor surface. **Co-sign envelope MUST include the enumerated list of all DAG node hashes added since the prior co-sign** — NOT just a summary diff. The owner (or owner's anchor-surface client) recomputes the Merkle chain from the prior signed tip via these enumerated nodes; the substrate cannot present a summary that hides parallel-branch forgery between CI events.

**Substrate emits to anchor surface**:
- Current DAG-tip hash.
- Enumerated list of DAG node hashes added since last co-sign (the chain links).
- Each node's metadata: type, causal-parent-hashes (substrate cannot omit any).
- The proposed CI mutation as **canonical bytes** (substrate does not render).

**Owner verifies** independently at the anchor-surface client:
1. Reconstructs Merkle chain from prior co-signed tip via enumerated nodes; confirms current `dag_tip_hash` is reachable.
2. Renders canonical-bytes proposed mutation; reviews; signs the canonical-bytes hash + anchor-surface trusted timestamp + anchor-surface nonce.

Co-signs accumulate; the chain of co-signs is the immune-detectable integrity history.

### §2.3 Retention — the materialized-views carve-out (operationalizes I4 expanded)

**Full fidelity = causal recoverability** (L0 I4). The substrate may maintain materialized views (digests, compressed roll-ups, indices) provided:

- Underlying append-only operations log is retained without loss.
- Re-materialization from operations is mechanically possible.
- Materialized-view layer is contract-identity-level.

**Tiered retention**:

- **Hot tier** — recent N (TBD-L4, default 30 days active operation) operations + sporocarps in fast storage; full re-materialization.
- **Warm tier** — older operations in slower storage; re-materialization still mechanical but cost is non-trivial.
- **Cold tier** — operations beyond an L1-tunable horizon; archived per I4 retention. Re-materialization is owner-attested.

**Retention horizon** is contract-identity-level. Default proposal: horizon = `recoverability_budget × 2`.

**Cold-tier inaccessibility marker** (per pass-2 rhizomorph-7): cold-tier fetch is owner-attested. During legacy / quarantined sub-states, cold-tier-spanning queries (trajectory; cross-epoch sporocarp reads) return explicit `cold_tier_inaccessible` markers — substrate distinguishes "no data" from "data exists but inaccessible".

### §2.4 Recoverability budget + drill discipline (canonical owner, DRAFT 9 expanded)

Recoverability budget is the L1-specified backup/redundancy policy defining when "destroyed" actually means destroyed (per L0 P7 mortality + I4 full-fidelity causal DAG).

**Components**:
- **Backup frequency**: TBD-L4. Default: continuous WAL + periodic full snapshot (WAL per cycle; snapshot every 1000 cycles per §6 — wrapped in M25.0 integrity envelope).
- **Backup locations**: TBD-L4. Constraint: ≥1 off-host-process location.
- **Recovery test cadence**: tiered to manage scaling cost (per pass-2 saprotroph-14 cold-tier cost over decades + saprotroph-2 cold-tier slow-drill problem).

**Tiered recovery drill** (canonical, DRAFT 9 explicit per L2_OBSERVABILITY §6 cross-ref):

- **Hot+warm-tier drill** every **100 substrate days** (seed default; L1-tunable in [30, 365] days): full restore from backup of hot+warm tier; verify I1, I3, I4, I5, I8 (DRAFT 9: also I9 compression-invariant set + I10 cost-budget recoverability + I12 telos-objective recoverability when declared). Fruit `recovery_drill_result` sporocarp.
- **Cold-tier sampled drill** every **1000 substrate days** (seed default; L1-tunable in [365, 3650] days): pick N random cold-tier nodes per drill where `N = ceil(log₂(cold_tier_count))`. Sampling indices derived from anchor-surface nonce per §9.3.5 (substrate cannot pre-compute and bias toward honest portions). Prove each sampled node recoverable; fruit `cold_tier_sample_recovery_pass` sporocarp.

**Drill failure-rate baseline — two-baseline approach** (per pass-2 saprotroph-18 + saprotroph-2; DRAFT 9 cascade explicit per L2_OBSERVABILITY §6):

Each drill outcome is fruited as `recovery_drill_result` with the canonical structure:

```
{
  "drill_id": <i64 anchor-nonce-derived id>,
  "scope": "hot_warm" | "cold_tier_sample",
  "outcome": "pass" | "fail" | "partial",
  "failure_classification": <enum or null>,
  "evidence_inputs": {
    "sampled_node_hashes": [Bytes(32), ...],
    "merkle_paths": [...],
    "recovery_canonical_bytes_hashes": [...],
    "drill_started_at_unix_ns": Timestamp,
    "drill_ended_at_unix_ns": Timestamp
  }
}
```

Two parallel baselines are tracked:

1. **Near-baseline (rolling last-10 drill window)**:
   - Computes `near_drill_failure_rate = (failures_in_last_10) / 10` per drill scope.
   - **≥2σ departure** from the near-baseline mean (computed from the rolling window's own historical mean across all-time observations of the same scope) → emit `drill_failure_near_baseline_departure` immune sporocarp.
   - **Purpose**: detects acute departures (a sudden failure cluster).

2. **Secular-baseline (anchored to first-stable-window — drills 6 through 15)**:
   - The secular baseline is **anchored**: drills 6-15 establish a `secular_failure_rate_baseline` (per scope); this baseline **never advances** for the substrate's lifetime.
   - `secular_trend_metric = current_rolling_failure_rate / secular_failure_rate_baseline`.
   - **Departure threshold**: L1-tunable, **default 3×** (i.e., current rate exceeds 3× the anchored baseline) → emit `drill_aging_grade` approaching-mortality signal sporocarp.
   - **Purpose**: detects slow secular drift over decades. The cold-tier slow-drill cadence (every 1000 substrate days) means the secular baseline approach is what scales beyond the near-baseline window.
   - **Rationale**: a near-baseline rolling window can drift with the substrate's accumulating decay; the anchored secular baseline preserves the substrate's young-self standard as the comparison point.

**Witnesses, not verdicts** (per L0 §9.3.4): drill results emit cryptographic-proof tuples — sampled hashes, Merkle paths, reproducible inputs — sufficient for the anchor-surface verifier to independently re-derive. The substrate does NOT emit "pass/fail"; it emits the evidence. The owner-side re-derivation is **load-bearing for I3/I4 enforcement** — a substrate forging drill results forges its own mortality observability.

**Beyond the budget = destruction**: when backups are exhausted AND substrate medium fails, P7 catastrophic destruction. **Two consecutive failed drills** at the anchor surface auto-emit owner-side `mortality_drill_failure` event (the dual channel for endogenous mortality per L1_GOVERNANCE §4.4). The substrate cannot suppress this — `mortality_drill_failure` lives at the anchor surface (per L1_HARD_RULES §4 anchor-surface-resident state).

### §2.5 DAG-pruning prohibition

**Pruning is contract-identity-level only.** Daily ops cannot remove DAG nodes. Cold-tier archival (moving nodes off-host to long-term storage) is NOT pruning — operations remain reachable from cold tier via owner-attested fetch.

Substrate-initiated "I'm out of space" responses:

- **Disk-pressure threshold** (default 90%): emit `storage_pressure` immune sporocarp; spike `evolution-tension` appetite toward `retention_policy_amendment`.
- **Owner inaction past threshold**: substrate enters `quarantine` sub-state (no new intakes; still reachable for owner reads) — this is degradation, not destruction. Continued owner inaction → approaching-mortality signal.

---

## §3. Spore-schema (operationalizes L0 P8 / I7)

### §3.1 Contents at minimum

When parent substrate spawns child, the spore-schema MUST include:

- **Schema definitions** (SSoT structure, validated against parent's current SSoT designation).
- **Canonical-bytes serializer specification** (full specification in §5 below). Spore-inherited; tier-1 SSoT field (closes pass-3 mycorrhiza-18 + mycorrhiza-20: operator + owner + child substrate all need this for independent canonical-bytes derivation). Specification format must be pure declarative (no runtime-dependent primitives; runnable by any party that has the spec).
- **Dispatch-form atomic-record type tree** (under L1_TROPISM dispatch: sporocarp type tree; under other forms: equivalent atomic-record schema).
- **Classifier dimension table** (from L1_GOVERNANCE — the I2 classifier function as data).
- **Initial appetite axis schema** OR equivalent under chosen dispatch (gradient-update-rule signatures, threshold seeds).
- **Anchor surface configuration** (where the owner's signing key lives; what the child's birth attestation looks like; sealing mechanism for substrate_secret per L1_SKIN §4.2).
- **Parent immune-signal summary** (counts of unresolved immune sporocarps by type + most recent tip-hash). Spawning while parent has unresolved immune sporocarps puts child in `quarantined` birth period until owner re-attests intent.
- **Compression-rule registry** (per L0 P10.c + L1_HARD_RULES §2 F18): each owner-attested compression rule is spore-inheritable so the child can apply the rule from genesis. Rules are CI-attested per L0 §2.3 P10.c — the child cannot author its own rules until owner attestation arrives.
- **Telos-objective declaration** when owner-stated (per L0 §2.3 P14.b + L1_HARD_RULES §2 F20): optional; inheritable when present. Carries the objective text + objective embedding (when canonical-bytes-serialized) for I12 alignment computation.
- **Generation-depth telemetry** (per L0 §16 cascade requirement + L1_HARD_RULES §2 F21): `(generation_depth, max_remaining_depth)` field — a child cannot spawn its own children if `max_remaining_depth == 0`. (Full generation discipline mechanism: L1_GOVERNANCE §4.3.)

### §3.2 Contents NOT included

- **Parent's full causal DAG** — the child starts with its own genesis sporocarp; parent-child link is a federation_coupling edge from parent's DAG, not a transferred DAG fragment. (Per L0 §10.4 max-discrimination + L0 P8: child begins its own symbiosis from scratch.)
- **Parent's operator-token history** (per L0 I1 — no agent-discriminating attribute persisted).
- **Parent's accumulated read-pattern norms** (per pass-1 saprotroph-10: norms are model-class epoch-bucketed; child rebuilds in its own epoch).

### §3.3 Closure verification protocol (operationalizes L0 I7)

At spawn:

1. **Parent runs static-schema validation**: child's spore-schema matches parent's current spore-schema-hash for the field set above.
2. **Child runs its own I3 self-validation** as its first metabolic cycle (against the spore-schema as initial SSoT designation).
3. **Owner co-signs the spawn** at the anchor surface (L0 §9.2) — `(parent-substrate-ID, child-substrate-ID, spore-schema-hash, timestamp)`.

Failure on any step aborts spawn BEFORE the federation link commits in the parent's DAG. Partial spawns are GC'd by L1_CONTINUITY at next cycle.

Success emits `genesis_attested` sporocarp in parent's DAG (federation_coupling edge to child-substrate-ID).

---

## §4. Validation tiers (operationalizes L0 I3, DRAFT 9 expanded to 3 tiers)

### §4.1 Three-tier policy (canonical, DRAFT 9 — supersedes DRAFT 1 tentative two-tier)

Per L0 §13.2 cascade requirement + I3 self-validation, validation runs at three tiers:

- **Tier 1 (identity-critical)** — validated **every metabolic cycle**:
  - `substrate-ID`
  - `owner_key_history` (active-prefix only — see L1_GOVERNANCE §3.1 active-prefix + archived-tail discipline)
  - `anchor_surface_endpoint_public_key`
  - `DAG-tip-hash` + Merkle parent-edge closure of the most recent N cycles (per §2.3 + P10.b compression-invariant set)
  - `classifier_dimension_table` + classifier-fixed-point fields
  - `mortality_signal_threshold + update-rule` (per L0 P7 + L1_HARD_RULES F7)
  - `skin_surface_declaration` (intake + output endpoints + forbidden surfaces; per L1_SKIN §1 + F11)
  - **`canonical_bytes_serializer_spec`** (per §5 + F16; pure declarative, spore-inheritable)
  - **`compression_rule_registry`** (per L0 P10.c + F18) — DRAFT 9 NEW
  - **`compression_invariant_set_enumeration`** (per L0 P10.b — the substrate's authoritative list of what cannot be compressed)
  - **`cost_budget_thresholds_per_axis`** (per L0 P11.b + F19) — DRAFT 9 NEW
  - **`telos_objective_declaration`** when present (per L0 P14.b + F20)
  - **`generation_depth + max_remaining_depth + reproduction_rate_state`** (per L0 §16 + F21)
  - **`SSoT_migration_M_parameter`** (per §1.3 — the M-cycle count itself governs identity-critical migration cadence)

- **Tier 2 (sampled with rolling 100% coverage over window)** — validated by **sampling per deep-cycle** (deep-cycle cadence per L1_CONTINUITY §1.1):
  - The window is L1-tunable; **seed default 10000 cycles** (M26-cascade explicit per L0 §13.2 cascade requirement).
  - Within the window, every tier-2 field MUST be sampled at least once (rolling 100% coverage discipline).
  - Sampling indices derived from anchor-surface nonce per §9.3.5 (substrate cannot bias sampling toward honest portions).
  - **Coverage witness emission**: substrate emits `tier_2_coverage_witness` sporocarp at end-of-window with `(window_start_cycle, window_end_cycle, sampled_field_set, coverage_completeness, missed_field_set_if_any)`.

- **Tier 3 (owner-triggered)** — validated only on explicit owner request (anchor-surface event):
  - Catalogs every field outside Tier 1 + Tier 2.
  - Owner-triggered as part of an audit, recovery drill, or quarantine-clearance evidence-gathering.

### §4.2 Tiering discipline

- **New fields default to tier 1** (per pass-2 mycoparasite-26 — adversarial default forbidden). To create a new field at tier 2 or tier 3 requires explicit CI-attestation downgrade.
- Tier promotion (tier 3 → tier 2 → tier 1) is daily-autonomous (more aggressive validation is always safe).
- Tier demotion (tier 1 → tier 2 → tier 3) is CI-gated.
- Tier assignment is a SSoT tier-1 field itself.

### §4.3 Rolling-window coverage enforcement (DRAFT 9 NEW per L0 §13.2)

Per L0 I3 cascade requirement: tier-2 validation MUST achieve 100% coverage over the L1-tunable window. If the window closes with `missed_field_set_if_any` non-empty, the substrate emits `tier_2_coverage_breach` immune sporocarp; sustained breach (≥3 consecutive windows with missed fields) routes through quarantine entry per L1_CONTINUITY §5.1.

The substrate cannot **silently allow** tier-2 coverage to slip; emission is mandatory at end-of-window.

---

## §5. Canonical-bytes serializer specification (per L0 §9.4 + F16, DRAFT 9 explicit per §13.2 cascade)

The **canonical-bytes serializer** is the deterministic function `serialize: SSoT-typed-value → Bytes` that maps a typed value to a unique byte string such that any two parties (substrate, anchor-surface client, operator process, child substrate) that hold the serializer spec compute byte-identical output for byte-identical input.

This is the foundation of L0 §9.4 canonical-bytes doctrine (owner-side rendering, witnesses, signature-bound determinism). Per L1_HARD_RULES F16, the serializer spec is a tier-1 SSoT field + spore-inheritable.

### §5.1 Type-level requirements

The serializer covers the following typed values (the "value space"):

- **Bool** (single-byte determinate encoding)
- **Uint** (variable-length unsigned integer — explicit byte-length prefix; never an architecture-dependent native int)
- **Sint** (variable-length signed integer)
- **Timestamp** — **MUST be i64 nanoseconds since Unix epoch (1970-01-01T00:00:00Z)**. The serializer rejects any value outside the i64 range. Per L0 §13.1: substrate MUST NOT use i32 timestamps anywhere — this clause enforces that prohibition at the serializer boundary.
- **Bytes** (length-prefixed byte string)
- **String** (UTF-8 byte string with explicit length prefix; the serializer rejects invalid UTF-8 at encode time)
- **Map** — **keys MUST be in strict canonical order** (per Phase β fix already implemented in Rust + Python + TS decoders; closes C18_canonical_bytes_render_drift asymmetry). Canonical order = byte-lexicographic order of the encoded keys. A Map encoder that does NOT enforce strict canonical order is breach (substrate-side serializer that emits unordered maps produces non-reproducible canonical bytes).
- **Array** (length-prefixed, ordered)

### §5.2 Negative timestamps (pre-1970 treatment)

**Permitted at the serializer level**: the serializer accepts negative i64 nanosecond timestamps (e.g., a substrate that imports a historical document with an annotation timestamped 1969-12-31 can canonically encode that timestamp).

**Rejected at the DAG-event level**: per Phase γ.9 hypha MnF35, **DAG events whose `at_unix_ns < genesis_at_unix_ns` are REJECTED at the DAG-write boundary**. A substrate's own causal events cannot precede its genesis. The serializer permits the type-level value; the DAG validation layer rejects substrate-event payloads carrying such values. (Cross-ref: this validation is part of I4 full-fidelity causal DAG enforcement; a DAG node whose `at_unix_ns` violates this is breach and routes through C7_dag_retro_edit_detected.)

### §5.3 Year-2262 horizon-warning mechanism (per L0 §13.2 cascade requirement)

**Reason**: i64-nanoseconds since Unix epoch overflows around **2262-04-11T23:47:16.854Z** (i64 max nanoseconds ≈ 9.223e18 ns ≈ 292 years past 1970). A substrate's expected lifetime is **bounded by clock overflow** at the i64 limit.

**Mechanism**:
- The substrate computes a derived `genesis_horizon_warning_threshold_unix_ns` = 62 years before the i64 overflow point, i.e., 2200-01-01T00:00:00Z encoded as i64 nanoseconds.
- At every metabolic cycle (tier-1 check), the substrate compares its `genesis_time_unix_ns` against the horizon threshold:
  - If `genesis_time_unix_ns > genesis_horizon_warning_threshold_unix_ns` → emit `genesis_timestamp_horizon_warning` observability sporocarp. (A substrate **born** past 2200 has fewer than 62 years before i64 overflow.)
- At every metabolic cycle, the substrate also compares **the current wall-clock** to the i64 overflow threshold:
  - If `current_wall_clock_unix_ns > genesis_horizon_warning_threshold_unix_ns` (i.e., now is past 2200-01-01) → emit `i64_timestamp_horizon_warning` observability sporocarp.

**L1-tunable threshold**: the horizon-warning offset (default 62 years before overflow) is L1-tunable in [10 years, 100 years]. Larger offsets give the owner more decades of warning at the cost of earlier (potentially false-alarm) signal emission.

**Beyond the warning** (the substrate approaches actual overflow): the substrate's `i64_timestamp_horizon_warning` emission cadence escalates per L1-tunable schedule; the substrate emits `mortality_imminent_clock_overflow` approaching-mortality sporocarp at L1-tunable threshold (default 5 years before overflow). The substrate's lineage MUST migrate to a successor substrate (P8 reproduction) with a new genesis-time before the parent substrate's wall-clock overflows.

**Acknowledged limitation**: this is a **soft horizon**, not a hard prohibition. The L0 commitment is to i64-nanoseconds-since-epoch as the canonical L0 unit. A future L0 revision could move to i128, but that revision itself would require a P3 SSoT migration (per §1.3) — the substrate's running data store is i64-bound by the L0 doctrine at its current revision.

### §5.4 Canonical-bytes round-trip invariant (per L0 §9.4)

For every typed value V in the serializer's domain:
`decode(encode(V)) ≡ V` (round-trip identity)
`encode(decode(B)) ≡ B` for every byte-string B in the serializer's range (encode-decode reversibility)

This invariant is part of tier-1 validation: the substrate periodically runs round-trip tests on sampled SSoT values and emits `canonical_bytes_round_trip_failure` immune sporocarp on any violation. The round-trip-failure check is one of the I3 sub-checks at tier-1 validation cadence.

### §5.5 Implementation status note (DRAFT 9 honest)

Per L0 §9 status table §9.3.1: canonical-bytes serialization is ~95% implemented across Rust + Python + TS decoders (Phase β fixed the TS decoder Map-key canonical-order gap that was the C18 asymmetry source).

**Remaining gap** (acknowledged for L4 closure): the **declarative serializer spec format** (the format in which the spec itself is canonically transmitted to a child substrate via spore-schema) is **not yet codified**. Currently the spec exists only as code (the Rust + Python + TS implementations). M27+ work will lift the spec to a pure-declarative format that operator + anchor-surface + child substrate can re-derive independently.

---

## §6. Snapshot.cb integrity wrapper (M25.0-shipped, spec'd here)

### §6.1 Purpose

`snapshot.cb` is the optimistic boot-time accelerator — a periodic snapshot of the substrate's derived state, written every K cycles (seed K=1000 per §2.4), wrapped in an Ed25519-signed envelope. On boot, the substrate uses the snapshot to seed its in-memory state instead of full DAG replay (replay only events after the snapshot's recorded tip).

**Forgery defense**: without the integrity wrapper, an attacker could substitute a snapshot.cb from a different substrate (or a forged file) and the booting substrate would accept it as truth. The wrapper closes this attack via Ed25519 signature + signer-pubkey check.

### §6.2 Wrapper format (canonical, format_version = 2)

```
Map({
  "format_version": Uint(2),
  "payload":         Bytes,        // the snapshot canonical-bytes
  "signature":       Bytes(64),    // Ed25519 signature over BARE payload bytes
  "signer_pubkey":   Bytes(32),    // Ed25519 public key of the substrate that signed
})
```

**Critical clause**: the signature is computed over the **BARE payload bytes** (not the wrapper bytes). This allows the wrapper-schema to be upgraded (e.g., format_version 2 → 3) **without re-signing** the inner payload — preserving signature stability across wrapper schema bumps.

**format_version semantics**:
- v1 = legacy M21.5 unsigned format (no signature; load_snapshot returns Ok(None) to force full DAG replay).
- v2 = current M25.0 signed format (canonical).
- v3+ = future upgrades; the wrapper schema may change but the bare-payload signature semantics stay stable.

### §6.3 Verification protocol (boot path)

The booting substrate performs three sequential checks before accepting a snapshot.cb as a state seed:

1. **Format check**: wrapper decodes as Map with `format_version == 2`. Failure → return Ok(None), fall back to full DAG replay.
2. **Signer-pubkey identity check**: the wrapper's `signer_pubkey` MUST match the substrate's own derived pubkey (from `substrate_signing_key.cb` per §7). Failure → emit `C38_snapshot_integrity_violation` immune sporocarp with witness `(observed_signer_pubkey, expected_signer_pubkey, snapshot_canonical_bytes_hash)`; discard snapshot; full DAG replay.
3. **Signature verification check**: `verify_signature(signer_pubkey, signature, payload) == OK`. Failure → emit `C38_snapshot_integrity_violation` with witness `(signature, payload_hash, signer_pubkey, verification_error)`; discard snapshot; full DAG replay.

**C38_snapshot_integrity_violation** is a new L1_HARD_RULES catalog row (CRITICAL grade — the substrate cannot proceed under boot-time forgery; quarantine routes through L1_CONTINUITY §5.1 if both snapshot AND DAG replay fail).

### §6.4 Cross-substrate forgery defense (M25.0 explicit)

The signer-pubkey identity check (§6.3 step 2) defends specifically against **cross-substrate forgery**: copying substrate A's snapshot.cb into substrate B's state_dir fails the signer-pubkey check at B's boot. B's own derived pubkey differs from A's, so the substituted snapshot is rejected.

### §6.5 Implementation status

M25.0-shipped (commit `52a4cce`). All format_version=2 snapshot writes use this wrapper; boot verification is wired in `server.rs:540-595`. Cross-ref `myco_substrate/src/persistence.rs::save_snapshot` + `myco_substrate/src/persistence.rs::load_snapshot`.

---

## §7. substrate_signing_key.cb (M25.0-shipped; known M3 entropy gap)

### §7.1 Purpose

A 32-byte Ed25519 seed persisted on first boot at `<state_dir>/substrate_signing_key.cb`. The seed is the substrate's private signing material — used to sign `snapshot.cb` (§6) and (M25.4+) to attest federation peer handshakes.

### §7.2 Generation mechanism

On first boot (no prior `substrate_signing_key.cb` present), the substrate generates a fresh seed via:

```
seed = sha256(
  domain = b"myco-substrate-signing-seed-v1"
  ||  current_unix_ns_le_bytes
  ||  process_id_le_bytes
  ||  stack_local_addr_le_bytes
  ||  generate_substrate_signing_seed_fn_addr_le_bytes
)
```

The domain string `"myco-substrate-signing-seed-v1"` is **distinct from** the substrate_id seed generation domain to prevent correlation — a substrate_id leak cannot be used to predict the signing key (per `persistence.rs:902-905` comment).

### §7.3 Known M3 entropy gap (Phase γ.9 mycoparasite finding)

**Low-entropy mechanism**: `current_unix_ns` (~30 bits sub-ms), `process_id` (~16 bits), ASLR stack address (~16-30 bits), function address (similar). Total ~80-100 bits — well below Ed25519's nominal 256-bit security level. A capable adversary with knowledge of boot time, PID, and ASLR characteristics could narrow seed search space.

**Declared-asymmetry status** (cross-ref §6 + L0 §9.5): the gap is **explicitly marked at L1** rather than concealed; substrate fruits `signing_key_entropy_known_gap` observability sporocarp at first boot; closure in M26.x cascade.

### §7.4 M26.x closure path (forward commitment)

L4 closure path: replace the sha256-of-low-entropy-mix with **CSPRNG primitive**:
- POSIX: `getrandom(2)` (Linux + recent BSD) with `GRND_RANDOM` blocking for first 32 bytes.
- Windows: `BCryptGenRandom` from CNG.
- Rust: `rand_core::OsRng` (which wraps the platform CSPRNG).

The closure preserves the seed-file format (32 raw bytes) and the file-rest-of-lifetime semantics (load on subsequent boots, never regenerate while the file persists). Only the **first-boot generation** changes; existing substrates retain their original seed across the upgrade.

### §7.5 Cross-ref to C-row catalog

Until M26.x closes, the entropy gap is observability-only (fruits `signing_key_entropy_known_gap` sporocarp). A future C-row catalog row may be added if observable exploitation surfaces.

---

## §8. C-rows whose detection site is L1_SCHEMA

This document hosts the detection mechanism for the following C-rows; full catalog row + status at L1_HARD_RULES §1:

- C6 `dag_enumeration_unclosed` — §2.2 closure check
- C7 `dag_retro_edit_detected` — §2.1 Merkle integrity
- C8 `ssot_migration_phase_skip` — §1.3 two-phase commit
- C18 `canonical_bytes_render_drift` — §5 canonical-bytes serializer
- C38 `snapshot_integrity_violation` — §6 snapshot wrapper
- C51 `compression_invariant_corruption` — §2.5 retention
- C52 `compression_uncattested` — §2.5 + P10.c attestation gate
- C53 `budget_exhausted_silent` — §4.1 cost-budget thresholds tier-1

L1_HARD_RULES §1 is the single source of truth for C-row labels, status, and L0/I traces.

---

## §9. Open at L1, deferred to L4

L1 commits to the shape; L4 picks values from first-month metabolism observations:

- Hash function within {SHA-256, BLAKE3, SHA-3-256}.
- Storage layout within {file-per-node, log+index, embedded KV}.
- SSoT migration phase-1 M within [100, 10000] cycles (seed 100 per §1.3).
- Backup frequency within WAL+snapshot pattern (seed: WAL per cycle, snapshot every 1000 cycles).
- Tier-2 validation window within [1000, 100000] cycles (seed 10000 per §4.1).
- Horizon-warning offset within [10y, 100y] (seed 62y per §5.3).
- M26.x CSPRNG primitive selection for §7.4 closure.
