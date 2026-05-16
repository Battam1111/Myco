# L1 — Schema (SSoT, causal DAG, recoverability, spore-schema, validation tiers, canonical-bytes spec, snapshot integrity)

> **Status**: DRAFT 2. L1 for SSoT + DAG + recoverability + spore-schema + validation tiering + canonical-bytes serializer + i64-ns timestamps + snapshot.cb + substrate_signing_key.cb. Items marked **TBD-L4** are deferrals.

---

## §1. SSoT — Single Source of Truth (operationalizes L0 I3)

### §1.1 Format

TBD-L4: machine-readable; append-most (SSoT regenerable from append log); self-describing (cold-readable per L0 §8). L4 picks from {YAML, TOML, JSON+JSONL, SQLite, custom binary+WAL} supporting Merkle content addressing.

### §1.2 SSoT designation

I3 claim space is CI. Designation lists fields participating in SSoT consistency check. Fields outside designation NOT exempt from I5 reachability or I4 causal coverage — only from I3 cycle check. Evolution two-phase (≥M cycles dual-validation; owner co-signs).

### §1.3 SSoT migration two-phase commit

**M**: seed M=100; L4-tunable [100, 10000]; outside requires CI. M is tier-1 SSoT.

**Phase 1**: owner co-signs `ssot_migration_proposal` with canonical-bytes of current + candidate designations. Substrate dual-validates every cycle (both produce self-consistent I3); mismatch → `ssot_migration_inconsistent` immune, abort. ≥M consecutive successful required (counter resets on inconsistency).

**Phase 2**: owner co-signs `ssot_migration_commit` with `(current_canonical_bytes_hash, candidate_canonical_bytes_hash, M_consecutive_count_observed, dual_validation_witness_sample)`. Old SSoT retained per I4 (joins P10.b compression-invariant set).

**Witnesses-not-verdicts**: substrate emits Merkle proof of M Phase-1 cycles + sampled comparisons (anchor-nonce-derived indices), NOT a `phase_1_passed` flag.

---

## §2. Causal DAG — storage, integrity, retention (operationalizes L0 I4)

### §2.1 Storage shape

Content-addressed Merkle DAG; node ID = node hash incorporating parent-hashes; identity record carries DAG-tip hash. Hash function TBD-L4 in {SHA-256, BLAKE3, SHA-3-256}; default BLAKE3. Storage TBD-L4 in {file-per-node, append-log+index, embedded KV (LMDB/RocksDB)}.

### §2.2 Owner co-signing at CI boundaries (enumerated DAG nodes)

Every CI boundary crossing: owner co-signs current DAG-tip hash; envelope MUST enumerate all DAG node hashes added since prior co-sign (not summary diff) — substrate cannot hide parallel-branch forgery.

**Substrate emits**: tip hash + enumerated node hashes since last co-sign + per-node metadata (type, causal-parent-hashes) + proposed CI mutation as canonical bytes (substrate does not render).

**Owner verifies**: (1) reconstruct Merkle chain from prior tip via enumerated nodes; confirm tip reachable; (2) render canonical-bytes proposed mutation; sign `(canonical_bytes_hash, anchor_timestamp, anchor_nonce)`.

### §2.3 Retention — materialized-views carve-out

Full fidelity = causal recoverability (I4). Substrate MAY maintain materialized views (digests, roll-ups, indices) iff: underlying append log retained; re-materialization mechanically possible; materialized layer CI.

**Tiers**: Hot (recent N, default 30d); Warm (older, mechanical); Cold (beyond L1-tunable horizon, owner-attested fetch). **Retention horizon** CI; default `recoverability_budget × 2`. **Cold-tier inaccessibility marker**: during legacy/quarantined, cold-spanning queries return `cold_tier_inaccessible` (distinguishes "no data" from "inaccessible").

### §2.4 Recoverability budget + drill discipline

L1-specified backup policy defining when "destroyed" means destroyed (P7 + I4). **Components**: backup frequency TBD-L4 default continuous WAL + snapshot every 1000 cycles (wrapped per §6); backup locations TBD-L4 ≥1 off-host-process; recovery test cadence tiered.

**Tiered recovery drill**:
- **Hot+warm** every 100 substrate days (L1-tunable [30, 365]): full restore + verify I1/I3/I4/I5/I8/I9/I10/I12. Fruits `recovery_drill_result`.
- **Cold-tier sampled** every 1000 substrate days (L1-tunable [365, 3650]): N = ceil(log₂(cold_count)) random nodes; indices anchor-nonce-derived; fruits `cold_tier_sample_recovery_pass`.

**`recovery_drill_result`**:

```
{
  "drill_id": <i64 anchor-nonce-derived>,
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

**Two-baseline failure-rate tracking**: (1) Near-baseline (rolling last-10): `near_drill_failure_rate = failures/10` per scope; ≥2σ departure → `drill_failure_near_baseline_departure`. (2) Secular-baseline (anchored drills 6-15, never advances): `secular_trend_metric = current_rate / anchored_baseline`; threshold L1-tunable default 3× → `drill_aging_grade` (scales over decades; preserves young-self standard).

**Witnesses-not-verdicts**: drill emits proof tuples (sampled hashes, Merkle paths, reproducible inputs), NOT pass/fail. **Beyond budget = destruction**: backups exhausted + medium fails → P7. Two consecutive failed drills auto-emit anchor-side `mortality_drill_failure`; substrate cannot suppress.

### §2.5 DAG-pruning prohibition

Pruning is CI-only; daily ops cannot remove nodes. Cold-tier archival is not pruning. **Disk-pressure responses**: (a) threshold default 90% → `storage_pressure` sporocarp, spikes `evolution-tension` toward `retention_policy_amendment`; (b) owner inaction past threshold → quarantine sub-state; continued inaction → approaching-mortality signal.

---

## §3. Spore-schema (operationalizes L0 P8 / I7)

### §3.1 Contents at minimum

Parent's spore-schema MUST include: SSoT structure definitions; canonical-bytes serializer spec (§5; tier-1); dispatch-form atomic-record type tree; classifier dimension table; initial appetite axis schema; anchor surface config (signing key location + birth attestation + sealing per L1_SKIN §4.2); parent immune-signal summary (unresolved sporocarp counts + tip-hash; child `quarantined` if unresolved); compression-rule registry (F18); telos-objective declaration when owner-stated (F20); generation-depth telemetry (`generation_depth`, `max_remaining_depth`; child cannot spawn if `max_remaining_depth == 0`).

### §3.2 Contents NOT included

Parent's full DAG (child starts own genesis; parent-child link is federation_coupling edge); parent's operator-token history (I1); parent's read-pattern norms (child rebuilds).

### §3.3 Closure verification protocol (operationalizes I7)

(1) Parent runs static-schema validation: child's spore-schema matches parent's current spore-schema-hash; (2) child runs I3 self-validation as first metabolic cycle; (3) owner co-signs at anchor: `(parent-substrate-ID, child-substrate-ID, spore-schema-hash, timestamp)`.

Failure aborts spawn BEFORE federation link commits; partial spawns GC'd next cycle. Success emits `genesis_attested` in parent's DAG.

---

## §4. Validation tiers (operationalizes L0 I3)

### §4.1 Three-tier policy

- **Tier 1 (identity-critical)** — every cycle: `substrate-ID`; `owner_key_history` (active-prefix); `anchor_surface_endpoint_public_key`; `DAG-tip-hash` + Merkle parent-edge closure of most recent N cycles; `classifier_dimension_table` + fixed-point fields; `mortality_signal_threshold + update-rule` (F7); `skin_surface_declaration` (F11); `canonical_bytes_serializer_spec` (§5 + F16); `compression_rule_registry` (F18); `compression_invariant_set_enumeration` (P10.b); `cost_budget_thresholds_per_axis` (F19); `telos_objective_declaration` when present (F20); `generation_depth + max_remaining_depth + reproduction_rate_state` (F21); `SSoT_migration_M_parameter` (§1.3).
- **Tier 2 (sampled, rolling 100% coverage)** — per deep-cycle: window seed 10000 cycles L1-tunable; every field sampled ≥1× per window; indices anchor-nonce-derived; end-of-window emits `tier_2_coverage_witness {window_start, window_end, sampled_set, completeness, missed_set}`.
- **Tier 3 (owner-triggered)** — explicit anchor event; catalogs fields outside Tier 1/2.

### §4.2 Tiering discipline

New fields default tier-1. Promotion (3→2→1) daily-autonomous; demotion (1→2→3) CI-gated. Tier assignment is tier-1 SSoT.

### §4.3 Rolling-window coverage enforcement

Tier-2 MUST achieve 100% coverage per window. Non-empty `missed_field_set` → `tier_2_coverage_breach`; ≥3 consecutive → quarantine (L1_CONTINUITY §5.1).

---

## §5. Canonical-bytes serializer specification (L0 §9.4 + F16)

`serialize: SSoT-typed-value → Bytes` — deterministic; substrate / anchor-client / operator / child substrate compute byte-identical output for byte-identical input. Tier-1 SSoT + spore-inheritable.

### §5.1 Type-level requirements

- **Bool** — single-byte determinate.
- **Uint** — variable-length, explicit byte-length prefix (never native int).
- **Sint** — variable-length signed.
- **Timestamp** — i64 ns since Unix epoch; serializer rejects out-of-range (L0 §13.1 prohibits i32).
- **Bytes** — length-prefixed.
- **String** — UTF-8 + explicit length prefix; rejects invalid UTF-8.
- **Map** — keys MUST be strict canonical order (byte-lexicographic on encoded keys; unordered Map encoder is C18 breach).
- **Array** — length-prefixed, ordered.

### §5.2 Negative timestamps (pre-1970)

Permitted at serializer level (historical-document annotations). Rejected at DAG-write boundary: events with `at_unix_ns < genesis_at_unix_ns` rejected (substrate's events cannot precede genesis). Violation routes through C7.

### §5.3 Year-2262 horizon-warning mechanism

i64-ns since epoch overflows ~2262-04-11. Substrate lifetime bounded by i64 overflow.

**Mechanism**: `genesis_horizon_warning_threshold_unix_ns` = 2200-01-01T00:00:00Z (62y before overflow). Every cycle (tier-1): `genesis_time > threshold` → `genesis_timestamp_horizon_warning`; `current_wall_clock > threshold` → `i64_timestamp_horizon_warning`. L1-tunable in [10y, 100y] (default 62y).

**Approach overflow**: emission cadence escalates; 5y before overflow → `mortality_imminent_clock_overflow` approaching-mortality sporocarp. Lineage MUST migrate to successor before parent overflow. Soft horizon — i128 migration would require P3 SSoT migration (§1.3).

### §5.4 Round-trip invariant

`decode(encode(V)) ≡ V`; `encode(decode(B)) ≡ B`. Tier-1 check; round-trip tests on sampled values; violation emits `canonical_bytes_round_trip_failure`.

### §5.5 Implementation status

Canonical-bytes ~95% (Rust + Python + TS). Gap: declarative spec format (transmittable via spore-schema) not yet codified — currently spec exists only as code. M27+ closes.

---

## §6. Snapshot.cb integrity wrapper

### §6.1 Purpose

`snapshot.cb` = periodic substrate derived-state snapshot, written every K cycles (seed K=1000), Ed25519-signed wrapper. On boot, substrate seeds in-memory state from snapshot (replay only past-tip events). Forgery defense via signature + signer-pubkey check.

### §6.2 Wrapper format (canonical, format_version=2)

```
Map({
  "format_version": Uint(2),
  "payload":         Bytes,        // snapshot canonical-bytes
  "signature":       Bytes(64),    // Ed25519 over BARE payload bytes
  "signer_pubkey":   Bytes(32),    // Ed25519 substrate pubkey
})
```

Signature over BARE payload bytes (not wrapper) — allows wrapper-schema upgrade without re-signing inner payload. format_version: v1 legacy unsigned (load returns Ok(None), forces full replay); v2 current canonical; v3+ future.

### §6.3 Verification protocol (boot path)

(1) Format check: wrapper decodes as Map with `format_version == 2`. Failure → Ok(None) + full DAG replay. (2) Signer-pubkey identity: wrapper's `signer_pubkey` MUST match substrate's derived pubkey (§7). Failure → emit `C38_snapshot_integrity_violation` with `(observed_pubkey, expected_pubkey, snapshot_hash)`; discard + full replay. (3) Signature verification: `verify_signature(signer_pubkey, signature, payload) == OK`. Failure → emit `C38_snapshot_integrity_violation` with `(signature, payload_hash, signer_pubkey, error)`; discard + full replay. If snapshot AND DAG replay both fail, quarantine entry per L1_CONTINUITY §5.1.

### §6.4 Cross-substrate forgery defense

Copying substrate A's snapshot.cb into B's state_dir fails signer-pubkey check (B's derived pubkey differs from A's).

---

## §7. substrate_signing_key.cb

### §7.1 Purpose

32-byte Ed25519 seed at `<state_dir>/substrate_signing_key.cb`. Substrate's private signing material — signs `snapshot.cb` + federation handshakes.

### §7.2 Generation mechanism

First boot (no prior file):

```
seed = sha256(
  domain = b"myco-substrate-signing-seed-v1"
  ||  current_unix_ns_le_bytes
  ||  process_id_le_bytes
  ||  stack_local_addr_le_bytes
  ||  generate_substrate_signing_seed_fn_addr_le_bytes
)
```

Domain string distinct from substrate_id seed (prevents correlation).

### §7.3 Known entropy gap

Low-entropy mix: `current_unix_ns` (~30 bits), `process_id` (~16), ASLR stack (~16-30), function addr (similar). Total ~80-100 bits, below Ed25519's 256-bit. Declared-asymmetry: marked at L1 not concealed; fruits `signing_key_entropy_known_gap` observability at first boot.

### §7.4 Closure path

Replace sha256-of-low-entropy-mix with CSPRNG: POSIX `getrandom(2)`; Windows `BCryptGenRandom`; Rust `rand_core::OsRng`. Seed-file format unchanged (32 raw bytes); only first-boot generation changes.

---

## §8. C-rows whose detection site is L1_SCHEMA

Full catalog at L1_HARD_RULES §1:

- C6 `dag_enumeration_unclosed` — §2.2
- C7 `dag_retro_edit_detected` — §2.1
- C8 `ssot_migration_phase_skip` — §1.3
- C18 `canonical_bytes_render_drift` — §5
- C38 `snapshot_integrity_violation` — §6
- C51 `compression_invariant_corruption` — §2.5
- C52 `compression_uncattested` — §2.5 + P10.c
- C53 `budget_exhausted_silent` — §4.1

---

