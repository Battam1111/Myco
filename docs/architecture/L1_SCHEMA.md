# L1 — Schema (SSoT, causal DAG, recoverability, spore-schema, validation tiers, canonical-bytes spec, snapshot integrity)

> **Status**: DRAFT 2. L1 for SSoT + DAG + recoverability + spore-schema + validation tiering + canonical-bytes serializer + i64-ns timestamps + snapshot.cb + substrate_signing_key.cb. Items marked **TBD-L4** are deferrals.

---

## §1. SSoT — Single Source of Truth (operationalizes L0 I3)

### §1.1 Format

TBD-L4: MUST be machine-readable; append-most (SSoT regenerable from append log); self-describing (cold-readable per L0 §8). L4 picks from {YAML, TOML, JSON+JSONL, SQLite, custom binary+WAL} supporting Merkle content addressing.

### §1.2 SSoT designation

I3 claim space is CI. Designation lists fields participating in SSoT consistency check. Fields outside designation NOT exempt from I5 reachability or I4 causal coverage — only from I3 cycle check. Evolution is two-phase (§1.3).

### §1.3 SSoT migration two-phase commit

Algorithm: [`algorithms/ssot_migration_2pc.md`](algorithms/ssot_migration_2pc.md) (Phase 1 dual-validation ≥ M consecutive cycles; Phase 2 commit; M_default=100, L4-tunable [100, 10000]; M is tier-1 SSoT). Substrate emits Merkle proof + sampled comparisons; substrate does NOT self-attest `phase_1_passed` flag. Old SSoT retained per I4 (joins P10.b compression-invariant set).

---

## §2. Causal DAG — storage, integrity, retention (operationalizes L0 I4)

### §2.1 Storage shape

Content-addressed Merkle DAG; node ID = node hash incorporating parent-hashes; identity record carries DAG-tip hash. Hash function TBD-L4 in {SHA-256, BLAKE3, SHA-3-256}; default BLAKE3. Storage TBD-L4 in {file-per-node, append-log+index, embedded KV (LMDB/RocksDB)}.

### §2.2 Owner co-signing at CI boundaries (enumerated DAG nodes)

Every CI boundary crossing: owner MUST co-sign current DAG-tip hash; envelope MUST enumerate all DAG node hashes added since prior co-sign (not summary diff) — substrate cannot hide parallel-branch forgery. Substrate emits tip hash + enumerated node hashes + per-node metadata (type, causal-parent-hashes) + proposed CI mutation as canonical bytes (substrate does not render). Owner verifies via Merkle-chain reconstruction; signs `(canonical_bytes_hash, anchor_timestamp, anchor_nonce)`.

### §2.3 Retention — materialized-views carve-out

Full fidelity = causal recoverability (I4). Substrate MAY maintain materialized views (digests, roll-ups, indices) iff underlying append log retained AND re-materialization mechanically possible AND materialized layer CI. **Tiers**: Hot (recent N, default 30d) / Warm (older, mechanical) / Cold (beyond L1-tunable horizon, owner-attested fetch). **Retention horizon** CI; default `recoverability_budget × 2`. **Cold-tier inaccessibility marker**: during legacy/quarantined, cold-spanning queries return `cold_tier_inaccessible` (distinguishes "no data" from "inaccessible").

### §2.4 Recoverability budget + drill discipline

Algorithm: [`algorithms/drill_baseline.md`](algorithms/drill_baseline.md) (tiered drill cadence + `recovery_drill_result` envelope + near-baseline ≥2σ trigger + secular-baseline 3× trigger + witnesses-not-verdicts + dual-channel mortality coupling).

**Backup policy**: backup frequency TBD-L4, default continuous WAL + snapshot every 1000 cycles (wrapped per §6); backup locations TBD-L4, ≥1 off-host-process; recovery test cadence tiered per algorithm.

### §2.5 DAG-pruning prohibition

Pruning is CI-only; daily ops cannot remove nodes. Cold-tier archival is not pruning. **Disk-pressure responses**: threshold default 90% → `storage_pressure` sporocarp + spikes `evolution-tension` toward `retention_policy_amendment`; owner inaction past threshold → quarantine sub-state; continued inaction → approaching-mortality signal.

---

## §3. Spore-schema (operationalizes L0 P8 / I7)

### §3.1 Contents at minimum

Parent's spore-schema MUST include: SSoT structure definitions; canonical-bytes serializer spec (§5; tier-1); dispatch-form atomic-record type tree; classifier dimension table; initial appetite axis schema; anchor surface config (signing key location + birth attestation + sealing per L1_SKIN §4.2); parent immune-signal summary (unresolved sporocarp counts + tip-hash; child `quarantined` if unresolved); compression-rule registry (F18); telos-objective declaration when owner-stated (F20); generation-depth telemetry (`generation_depth`, `max_remaining_depth`; child cannot spawn if `max_remaining_depth == 0`).

### §3.2 Contents NOT included

Parent's full DAG (child starts own genesis; parent-child link is federation_coupling edge); parent's operator-token history (I1); parent's read-pattern norms (child rebuilds).

### §3.3 Closure verification protocol (operationalizes I7)

(1) Parent runs static-schema validation: child's spore-schema matches parent's current spore-schema-hash. (2) Child runs I3 self-validation as first metabolic cycle. (3) Owner co-signs at anchor: `(parent-substrate-ID, child-substrate-ID, spore-schema-hash, timestamp)`. Failure aborts spawn BEFORE federation link commits; partial spawns GC'd next cycle; success emits `genesis_attested` in parent's DAG.

---

## §4. Validation tiers (operationalizes L0 I3)

### §4.1 Three-tier policy

- **Tier 1 (identity-critical)** — every cycle: `substrate-ID`; `owner_key_history` (active-prefix); `anchor_surface_endpoint_public_key`; `DAG-tip-hash` + Merkle parent-edge closure of most recent N cycles; `classifier_dimension_table` + fixed-point fields; `mortality_signal_threshold + update-rule` (F7); `skin_surface_declaration` (F11); `canonical_bytes_serializer_spec` (§5 + F16); `compression_rule_registry` (F18); `compression_invariant_set_enumeration` (P10.b); `cost_budget_thresholds_per_axis` (F19); `telos_objective_declaration` when present (F20); `generation_depth + max_remaining_depth + reproduction_rate_state` (F21); `SSoT_migration_M_parameter` (§1.3).
- **Tier 2 (sampled, rolling 100% coverage)** — per deep-cycle: window seed 10000 cycles L1-tunable; every field sampled ≥1× per window; indices anchor-nonce-derived; end-of-window emits `tier_2_coverage_witness {window_start, window_end, sampled_set, completeness, missed_set}`.
- **Tier 3 (owner-triggered)** — explicit anchor event; catalogs fields outside Tier 1/2.

### §4.2 Tiering discipline

New fields default tier-1. Promotion (3→2→1) is daily-autonomous; demotion (1→2→3) is CI-gated. Tier assignment is tier-1 SSoT.

### §4.3 Rolling-window coverage enforcement

Tier-2 MUST achieve 100% coverage per window. Non-empty `missed_field_set` → `tier_2_coverage_breach`; ≥3 consecutive → quarantine (L1_CONTINUITY §5.1).

---

## §5. Canonical-bytes serializer specification (L0 §9.4 + F16)

`serialize: SSoT-typed-value → Bytes` MUST be deterministic; substrate / anchor-client / operator / child substrate produce byte-identical output for byte-identical input. Tier-1 SSoT + spore-inheritable.

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

i64-ns overflows ~2262-04-11; substrate lifetime bounded. `genesis_horizon_warning_threshold_unix_ns = 2200-01-01T00:00:00Z` (62y pre-overflow; L1-tunable [10y, 100y]); every cycle (tier-1): `genesis_time > threshold` → `genesis_timestamp_horizon_warning`; `current_wall_clock > threshold` → `i64_timestamp_horizon_warning`. 5y before overflow → `mortality_imminent_clock_overflow` approaching-mortality sporocarp; lineage MUST migrate to successor before parent overflow. i128 migration would require P3 SSoT migration (§1.3).

### §5.4 Round-trip invariant

`decode(encode(V)) ≡ V`; `encode(decode(B)) ≡ B`. Tier-1 check; round-trip tests on sampled values; violation emits `canonical_bytes_round_trip_failure`.

### §5.5 Implementation status

Canonical-bytes ~95% (Rust + Python + TS). Gap: declarative spec format (transmittable via spore-schema) not yet codified — currently spec exists only as code; M27+ closes.

---

## §6. Snapshot.cb integrity wrapper

**§6.1 Purpose**: `snapshot.cb` = periodic substrate derived-state snapshot, written every K cycles (seed K=1000), Ed25519-signed wrapper; on boot substrate seeds in-memory state from snapshot then replays only past-tip events; forgery defense via signature + signer-pubkey check.

**§6.2 Wrapper format**: schema [`schemas/snapshot_wrapper.json`](schemas/snapshot_wrapper.json) (`format_version=2`; signature over BARE payload bytes). v1 legacy unsigned → load returns Ok(None) + full replay; v2 current canonical; v3+ future.

**§6.3 Verification protocol (boot path)**: (1) Format check (`format_version == 2`); failure → Ok(None) + full DAG replay. (2) Signer-pubkey identity MUST match substrate's derived pubkey (§7); failure → emit `C38_snapshot_integrity_violation { observed_pubkey, expected_pubkey, snapshot_hash }`; discard + full replay. (3) Signature verification `verify_signature(signer_pubkey, signature, payload) == OK`; failure → emit `C38_snapshot_integrity_violation { signature, payload_hash, signer_pubkey, error }`; discard + full replay. If snapshot AND DAG replay both fail → quarantine entry per L1_CONTINUITY §5.1.

**§6.4 Cross-substrate forgery defense**: copying substrate A's snapshot.cb into B's state_dir MUST fail signer-pubkey check (B's derived pubkey differs from A's).

---

## §7. substrate_signing_key.cb

32-byte Ed25519 seed at `<state_dir>/substrate_signing_key.cb`; substrate's private signing material — signs `snapshot.cb` + federation handshakes. First-boot generation: `seed = sha256(domain="myco-substrate-signing-seed-v1" || current_unix_ns_le || process_id_le || stack_local_addr_le || generate_substrate_signing_seed_fn_addr_le)`; domain string distinct from substrate_id seed (prevents correlation).

**Known entropy gap** (declared-asymmetry, marked at L1 not concealed): mix ≈ 80-100 bits, below Ed25519 256-bit; fruits `signing_key_entropy_known_gap` observability at first boot. **Closure path** (M26+): replace low-entropy mix with CSPRNG (POSIX `getrandom(2)` / Windows `BCryptGenRandom` / Rust `rand_core::OsRng`); seed-file format unchanged.

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
