> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4); see `docs/architecture/OUTLINE.md` §3 for details.

---

# L1: Schema (SSoT, causal DAG, recoverability, spore-schema, validation tiers, canonical-bytes, snapshot integrity)

> L1 for SSoT + DAG + recoverability + spore + validation tiering + canonical-bytes serializer + i64-ns timestamps + snapshot.cb + substrate_signing_key.cb. **TBD-L4** items are deferrals. All numeric thresholds L1-tunable unless specified.

---

## §1. SSoT: Single Source of Truth (operationalizes L0 I3)

**§1.1 Format**: TBD-L4; MUST be machine-readable; append-most; self-describing (cold-readable per L0/cards/LB_living_bets.md §1 (intelligence band)). L4 ∈ {YAML, TOML, JSON+JSONL, SQLite, custom binary+WAL} supporting Merkle content addressing.

**§1.2 Designation**: I3 claim space is CI. Designation lists fields participating in SSoT consistency. Fields outside designation NOT exempt from I5 reachability or I4 causal coverage, only from I3 cycle check.

**§1.3 Migration two-phase commit**: Algorithm [`algorithms/ssot_migration_2pc.md`](../algorithms/ssot_migration_2pc.md) (Phase 1 dual-validation ≥ M consecutive cycles; Phase 2 commit; M_default=100, L4-tunable [100, 10000]; M is tier-1 SSoT). Substrate emits Merkle proof + sampled comparisons; substrate does NOT self-attest `phase_1_passed`. Old SSoT retained per I4 (joins P10.b invariant set).

---

## §2. Causal DAG: storage, integrity, retention (operationalizes L0 I4)

**§2.1 Storage**: Content-addressed Merkle DAG; node ID = node hash incorporating parent-hashes; identity record carries DAG-tip hash. Hash function TBD-L4 ∈ {SHA-256, BLAKE3, SHA-3-256}; default BLAKE3. Storage TBD-L4 ∈ {file-per-node, append-log+index, embedded KV}.

**§2.2 CI-boundary co-review (keyless v3.1.5)**: Every CI crossing: the cultivator at the live human-in-the-loop CI gate MUST re-review the current DAG-tip; the enumeration MUST list all DAG node hashes added since the prior gate crossing (not summary diff), so the substrate cannot hide parallel-branch forgery. Substrate emits tip hash + enumerated node hashes + per-node metadata (type, causal-parent-hashes) + proposed CI mutation as canonical bytes. The cultivator re-derives via Merkle-chain reconstruction at the gate and approves or rejects in the loop. *(Keyless v3.1.5: the prior owner co-signature over `(canonical_bytes_hash, anchor_timestamp, anchor_nonce)` is removed; there is no owner key, no anchor timestamp, and no anchor nonce. Tip ordering uses the substrate's own monotonic clock (keyless; acknowledged-debt: no external trusted clock); the gate approval is the live human, not an owner signature.)*

**§2.3 Retention: materialized-views carve-out**: Full fidelity = causal recoverability (I4). Substrate MAY maintain materialized views iff underlying append log retained AND re-materialization mechanically possible AND materialized layer CI. **Tiers**: Hot (recent N, default 30d) / Warm (older, mechanical) / Cold (beyond L1-tunable horizon, fetch approved at the live CI gate). Retention horizon CI; default `recoverability_budget × 2`. Cold-tier inaccessibility marker: during legacy/quarantined, cold-spanning queries return `cold_tier_inaccessible`.

**§2.4 Recoverability budget + drill**: Algorithm [`algorithms/drill_baseline.md`](../algorithms/drill_baseline.md) (tiered drill cadence + `recovery_drill_result` envelope + near-baseline ≥2σ trigger + secular-baseline 3× trigger + witnesses-not-verdicts + dual-channel mortality coupling). Backup policy TBD-L4: default continuous WAL + snapshot every 1000 cycles (wrapped per §6); locations ≥1 off-host-process.

**§2.5 DAG-pruning prohibition**: Pruning CI-only; daily ops cannot remove nodes. Cold-tier archival is not pruning. Disk-pressure: threshold default 90% → `storage_pressure` sporocarp + spikes `evolution-tension` toward `retention_policy_amendment`; cultivator inaction past threshold → quarantine; continued inaction → approaching-mortality signal.

---

## §3. Spore-schema (operationalizes L0 P8 / I7)

**§3.1 Contents**: Parent's spore-schema MUST include: SSoT structure definitions; canonical-bytes serializer spec (§5; tier-1); dispatch-form atomic-record type tree; classifier dimension table; initial appetite axis schema; substrate-key config (the substrate's own F24 signing-key location + at-rest sealing per L1/SKIN §4.2; keyless v3.1.5: no owner-key/anchor-endpoint/birth-attestation inputs; substrate-ID is self-derived per L1/GOVERNANCE §4.1); parent immune-signal summary (unresolved sporocarp counts + tip-hash; child `quarantined` if unresolved); compression-rule registry (F18); telos-objective declaration when cultivator-stated (F20); generation-depth telemetry (`generation_depth`, `max_remaining_depth`; child cannot spawn if `max_remaining_depth == 0`).

**§3.2 NOT included**: parent's full DAG (child starts own genesis; parent-child link is federation_coupling edge); parent's operator-token history (I1); parent's read-pattern norms.

**§3.3 Closure verification (I7)**: (1) Parent runs static-schema validation: child's spore-schema matches parent's current hash. (2) Child runs I3 self-validation as first metabolic cycle. (3) The cultivator co-approves the spawn at the live CI gate via the `myco-spawn-cosign-v1` envelope binding `(parent-substrate-ID, child-substrate-ID, spore-schema-hash, timestamp)` (C68 gate; keyless v3.1.5: the prior owner Ed25519 co-signature is removed; the kept gate is the envelope structure + parent replay-guard + spore-schema-hash binding, approved by the live human). Failure aborts spawn BEFORE federation link commits; partial spawns GC'd next cycle; success emits `genesis_attested` in parent's DAG.

---

## §4. Validation tiers (operationalizes L0 I3)

**§4.1 Three-tier policy**:
- **Tier 1 (identity-critical)** every cycle: `substrate-ID`; `DAG-tip-hash` + Merkle parent-edge closure of recent N cycles; `classifier_dimension_table` + fixed-point fields; `mortality_signal_threshold + update-rule` (F7); `skin_surface_declaration` (F11); `canonical_bytes_serializer_spec` (F16); `compression_rule_registry` (F18); `compression_invariant_set_enumeration` (P10.b); `cost_budget_thresholds_per_axis` (F19); `telos_objective_declaration` when present (F20); `generation_depth + max_remaining_depth + reproduction_rate_state` (F21); `SSoT_migration_M_parameter` (§1.3). *(Keyless v3.1.5: `owner_key_history` + `anchor_surface_endpoint_public_key` are removed from the tier-1 set; both were owner-key/anchor-surface fields, retired with the anchor surface (F3/F4 DELETED). The substrate's own F24 signing-key pubkey is carried in the spore-schema, not as a per-cycle tier-1 owner-key check.)*
- **Tier 2 (sampled, rolling 100% coverage)** per deep-cycle: window seed 10000 cycles; every field sampled ≥1× per window; sampling indices are substrate/DAG-tip-derived (keyless v3.1.5: was anchor-nonce-derived); end-of-window emits `tier_2_coverage_witness {window_start, window_end, sampled_set, completeness, missed_set}`.
- **Tier 3 (cultivator-triggered)** explicit event approved at the live CI gate (keyless v3.1.5: was an owner-triggered anchor event); catalogs fields outside Tier 1/2.

**§4.2 Tiering discipline**: New fields default tier-1. Promotion (3→2→1) daily-autonomous; demotion (1→2→3) CI-gated. Tier assignment is tier-1 SSoT.

**§4.3 Rolling-window coverage enforcement**: Tier-2 MUST achieve 100% coverage per window. Non-empty `missed_field_set` → `tier_2_coverage_breach`; ≥3 consecutive → quarantine (L1/CONTINUITY §5.1).

---

## §5. Canonical-bytes serializer (L0/cards/AS_anchor_surface.md §4 (failure modes) + F16)

`serialize: SSoT-typed-value → Bytes` MUST be deterministic; substrate / verifier-at-the-live-CI-gate / operator / child substrate produce byte-identical output (keyless v3.1.5: the prior out-of-band anchor-client renderer is retired; the deterministic re-derivation is now done by the live human-in-the-loop at the CI gate). Tier-1 SSoT + spore-inheritable.

**§5.1 Type requirements**:
- **Bool**: single-byte determinate.
- **Uint**: variable-length, explicit byte-length prefix (never native int).
- **Sint**: variable-length signed.
- **Timestamp**: i64 ns since Unix epoch; serializer rejects out-of-range (L0/cards/P06_eternal_causality.md + L1/CONTINUITY (time semantics) prohibits i32).
- **Bytes**: length-prefixed.
- **String**: UTF-8 + explicit length prefix; rejects invalid UTF-8.
- **Map**: keys MUST be strict canonical order (byte-lexicographic on encoded keys; unordered Map encoder is C18 breach).
- **Array**: length-prefixed, ordered.

**§5.2 Negative timestamps (pre-1970)**: Permitted at serializer level (historical annotations). Rejected at DAG-write boundary: events with `at_unix_ns < genesis_at_unix_ns` rejected. Violation routes through C7.

**§5.3 Year-2262 horizon-warning**: i64-ns overflows ~2262-04-11. `genesis_horizon_warning_threshold_unix_ns = 2200-01-01T00:00:00Z` (62y pre-overflow; tunable [10y, 100y]); every cycle (tier-1): `genesis_time > threshold` → `genesis_timestamp_horizon_warning`; `current_wall_clock > threshold` → `i64_timestamp_horizon_warning`. 5y before overflow → `mortality_imminent_clock_overflow` approaching-mortality. i128 migration would require P3 SSoT migration (§1.3).

**§5.4 Round-trip invariant**: `decode(encode(V)) ≡ V`; `encode(decode(B)) ≡ B`. Tier-1 check; round-trip on sampled values; violation emits `canonical_bytes_round_trip_failure`.

**§5.5 Declarative spec**: declarative serializer specification (transmittable via spore-schema, language-agnostic) is doctrine commitment; format TBD-L4.

---

## §6. Snapshot.cb integrity wrapper

**§6.1 Purpose**: `snapshot.cb` = periodic substrate derived-state snapshot, written every K cycles (seed K=1000), Ed25519-signed wrapper; on boot substrate seeds in-memory state from snapshot then replays only past-tip events; forgery defense via signature + signer-pubkey check.

**§6.2 Format**: Schema [`schemas/snapshot_wrapper.json`](../schemas/snapshot_wrapper.json) (`format_version=2`; signature over BARE payload bytes). v1 legacy unsigned → load returns Ok(None) + full replay; v2 current canonical.

**§6.3 Verification (boot path)**: (1) Format check; failure → Ok(None) + full DAG replay. (2) Signer-pubkey identity MUST match substrate's derived pubkey (§7); failure → emit `C38_snapshot_integrity_violation`; discard + full replay. (3) Signature verification; failure → emit C38; discard + full replay. Snapshot AND DAG replay both fail → quarantine entry per L1/CONTINUITY §5.1.

**§6.4 Cross-substrate forgery defense**: Copying substrate A's snapshot.cb into B's state_dir MUST fail signer-pubkey check (B's derived pubkey differs from A's).

---

## §7. substrate_signing_key.cb

32-byte Ed25519 seed at `<state_dir>/substrate_signing_key.cb`; signs `snapshot.cb` + federation handshakes. First-boot generation MUST use OS CSPRNG (POSIX `getrandom(2)` / Windows `BCryptGenRandom` / equivalent); domain distinct from substrate_id seed. Entropy-deficient seeds (non-CSPRNG composition) MUST emit `signing_key_entropy_known_gap` at first boot: declared, not concealed.

---

## §8. C-rows whose detection site is L1/SCHEMA

Full catalog at L1/HARD_RULES §1: C6 (§2.2), C7 (§2.1), C8 (§1.3), C18 (§5), C38 (§6), C51 / C52 (§2.5), C53 (§4.1).
