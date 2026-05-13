# L1 — Schema (SSoT, causal DAG, recoverability, spore-schema, validation tiers)

> **Status**: DRAFT 1 (2026-05-13). Authoritative L1 doc for substrate-internal data shape.
> **Layer**: L1 (mechanism). Governed by L0.
> **Scope**: SSoT designation + format; causal-DAG storage; recoverability budget; spore-schema (P8); validation tiering (I3 cycles). Does NOT cover: classifier function (→ L1_GOVERNANCE), envelope schema (→ L1_SKIN), cycle cadence (→ L1_CONTINUITY), dispatch atomic records (→ L1_TROPISM).
> **Honesty**: items marked **TBD-L4** are explicit deferrals — L1 commits that the decision exists and bounds the space; L4 implementation makes the call. Per pass-1 architectural-astronaut, L1 over-commitment is anti-pattern.

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

**M (cycles of consistency before commit)**: TBD-L4. Default proposal: M = 1000 metabolic cycles OR 30 days continuous operation, whichever longer. Tunable per substrate canon.

**Phase 1**: candidate SSoT lives alongside current SSoT; substrate runs **dual-validation** every cycle (both must remain self-consistent). Mismatch emits `ssot_migration_inconsistent` immune event; migration aborts.

**Phase 2**: owner co-signs migration via anchor surface (L0 §9). Old SSoT is retained as archived per I4 (no lossy compression).

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

### §2.2 Owner co-signing at CI boundaries

Per L0 §9.2: at every contract-identity-level boundary crossing, the owner co-signs the current DAG-tip hash via the anchor surface. Co-signs accumulate; the chain of co-signs is the immune-detectable integrity history.

**What the substrate emits to owner at CI events**:
- Current DAG-tip hash.
- Diff hash since last co-sign.
- The proposed CI mutation (sporocarp content).

**What the owner signs**: a tuple `(DAG-tip-hash, diff-hash, proposed-mutation-hash, timestamp)`. The signature lands on the anchor surface; the substrate stores a reference (not the signing key itself).

### §2.3 Retention — the materialized-views carve-out (operationalizes I4 expanded)

**Full fidelity = causal recoverability** (L0 I4). The substrate may maintain materialized views (digests, compressed roll-ups, indices) provided:

- Underlying append-only operations log is retained without loss.
- Re-materialization from operations is mechanically possible.
- Materialized-view layer is contract-identity-level.

**Tiered retention**:

- **Hot tier** — recent N (TBD-L4, default 30 days active operation) operations + sporocarps in fast storage; full re-materialization.
- **Warm tier** — older operations in slower storage; re-materialization still mechanical but cost is non-trivial.
- **Cold tier** — operations beyond an L1-tunable horizon; archived per I4 retention. Re-materialization is owner-attested.

**Retention horizon** is contract-identity-level. Default proposal: horizon = `recoverability_budget × 2` (the substrate keeps twice the destruction-recoverability budget worth of cold-tier operations).

### §2.4 Recoverability budget

Per L0 §10.4 / §11 (proto archaeology), recoverability budget is the L1-specified backup/redundancy policy that defines when "destroyed" actually means destroyed.

**Components**:
- **Backup frequency**: TBD-L4. Default proposal: continuous WAL + periodic full snapshot (frequency: every metabolic cycle for WAL; full snapshot every 1000 cycles).
- **Backup locations**: TBD-L4. Constraints: ≥1 backup location is off-host-process (cannot be destroyed by a single host failure).
- **Recovery test cadence**: TBD-L4. Default: every 100 substrate days, a recovery drill is performed (restore from backup into a sandbox substrate; verify I1-I8); failure to pass drill is an immune-grade signal.

**Beyond the budget = destruction**: when backups are exhausted AND the substrate medium fails, P7 catastrophic destruction. Otherwise: recovery is possible.

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
- **Dispatch-form atomic-record type tree** (under L1_TROPISM dispatch: sporocarp type tree; under other forms: equivalent atomic-record schema).
- **Classifier dimension table** (from L1_GOVERNANCE — the I2 classifier function as data).
- **Initial appetite axis schema** OR equivalent under chosen dispatch (gradient-update-rule signatures, threshold seeds).
- **Anchor surface configuration** (where the owner's signing key lives; what the child's birth attestation looks like).
- **Parent immune-signal summary** (per pass-1 mycoparasite-13): counts of unresolved immune sporocarps by type + most recent tip-hash. Spawning while parent has unresolved immune sporocarps puts child in `quarantined` birth period until owner re-attests intent.

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

## §4. Validation tiers (operationalizes L0 I3)

Per pass-1 saprotroph-12, full I3 validation grows linearly with SSoT size. Validation tiering keeps cycle cadence (§6 continuity) sustainable.

### §4.1 Three-tier policy

- **Tier 1 (identity-critical)** — substrate-ID integrity, owner-signature integrity, DAG-tip-hash, classifier-fixed-point fields. Validated **every metabolic cycle**.
- **Tier 2 (governance-relevant)** — SSoT designation, contract-identity-level field set, federation peer attestations. **Sampled per cycle with rolling 100% coverage over an L1-tunable window**. Default window: 100 cycles.
- **Tier 3 (deep state)** — full SSoT consistency, full DAG reachability checks. **Owner-triggered or on-demand** (e.g., as part of governance event resolution; as part of recovery drill).

### §4.2 Tiering as contract-identity-level

The tier assignment of any field is contract-identity-level. Field cannot be silently demoted from tier 1 → tier 2 to skip cycle validation. Tier promotion (tier 2 → tier 1) is daily-autonomous (more aggressive validation is always safe); tier demotion is CI-gated.

### §4.3 Sampled validation strategy

Tier 2 rolling sampling: each cycle picks `ceil(tier2_field_count / window_size)` fields to validate this cycle. Over `window_size` cycles, every tier-2 field is validated at least once. Failures emit `tier2_sample_failure` immune events.

---

## §5. Open at L1, deferred to L4

Per pass-1 architectural-astronaut: don't over-commit. These are L4 calls informed by first-month metabolism observations:

- Exact hash function within {SHA-256, BLAKE3, SHA-3-256}.
- Exact storage layout within {file-per-node, log+index, embedded KV}.
- Exact M for SSoT migration phase-1 within {1000 cycles, 30 days, custom}.
- Exact backup frequency within the WAL+snapshot pattern.
- Exact validation window size within {50, 100, 200, custom}.

L1_SCHEMA commits to the **shape** of these decisions; L4 picks values based on observed behavior.
