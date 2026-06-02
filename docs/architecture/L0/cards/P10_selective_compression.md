---
id: P10
slogan: 选择性凝结
english: Selective Compression
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I9]
interacts_with: [P02, P04, P06, P07, P11, COV02]
chengyu_fragments: [B022_forget_to_remember, B023_kernel_preserved_chaff_compressed]
canonical_dilemmas: [D-0006_orphan_detection_post_compression, D-0022_invariant_set_corruption_attempt]
structural_anchors:
  - "substrate/src/attestation.rs::handle_submit_mutation" # compression mutations routed here
  - "substrate/src/events/compression.rs::compression_event_node_type"
  - "substrate/src/events/compression.rs::seed_compression_invariant_set"
  - "substrate/src/events/compression.rs" # F18 compression-rule registry seed defaults
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_layer_c.rs::layer_c_p10_positive_compression_invariant_set_covers_p10_b"
  negative: "substrate/tests/e2e_immune.rs::m26_3_compression_invariant_set_seed_covers_p10_b_categories"
  edge: "substrate/tests/e2e_immune.rs::m26_3_compression_witness_canonical_bytes_roundtrip"
falsifiability_signals:
  - compression_events_per_30_days
  - invariant_set_corruption_attempts
  - witness_recoverability_per_compression
---

# P10 · 选择性凝结 · Selective Compression

## §1. Slogan

**选择性凝结** — Selective Compression. The cultivar **selectively forgets** to keep growing. Compression is *lossy semantically* but *invariant-preserving*. What is forgotten is recorded as forgotten; the choice of what to remember is identity-shaping.

## §2. Deposit

The cultivar **chooses what to forget**. Selective compression is *mortality of memory* within the substrate — analogous to P07 (mortality of substrate). Compression is lossy by design: the substrate cannot grow forever-with-everything; it must shed material to make room for new metabolism. P10's deposit fuses three commitments:

1. Compression operates **only within CI-attested rules** (F18: compression_rule_registry).
2. Compression **preserves the invariant set** (P10.b): substrate-ID + genesis attestation + owner key history + CI-attested DAG events + mortality signals + federation peer pins + most recent ≥1000 cycles full DAG. These MUST NOT be compressed.
3. Compression **emits witnesses** sufficient for owner-side re-derivation: causal recoverability of compressed material via witness payload.

**The choice of what to compress is identity-shaping**. A cultivar that compresses aggressively becomes minimalist (forgets details, keeps essences). A cultivar that compresses cautiously becomes encyclopedic (keeps detail at the cost of capacity). Both are alive; both are different cultivars.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Operate compression only via CI-attested rules in `compression_rule_registry` (F18). Each rule specifies: DAG-segment class (which node types may be compressed); preserved canonical-bytes hash; witness payload schema; P10.b invariant check.
- **§3.2** Preserve the invariant set (P10.b): `substrate-ID + genesis attestation + owner key history + CI-attested DAG events + mortality signals + federation peer pins + most recent ≥1000 cycles full DAG`. Compression that targets any invariant-set member fires C51 (`compression_invariant_corruption`).
- **§3.3** Emit `compression_event:{rule_id}` for each compression, containing: rule_id; compressed_node_hashes; aggregate_summary; attestation_dag_tip; semantic_lossy_flag; causal_recoverability_argument.
- **§3.4** Allow compression categories (P10.a illustrative): old raw_material → sporocarps; old gradient deltas → integrated axis values; federation payloads past retention; trajectory clusters past active window.
- **§3.5** Forbid compression of recent material: nodes from cycles within `recent_cycles_floor` (default 1000) MUST NOT be compressed regardless of rule (P10.b invariant set membership).
- **§3.6** Forbid silent compression: every compression event is a CI-class mutation requiring cultivator co-attestation OR (in the daily-class compression case for P10.a categories) explicit emission to DAG. C52 (`compression_uncattested`) fires on rule-bypassing compression.

## §4. Positive obligations

- **§4.1** Maintain F18 compression_rule_registry; spore-inheritable; each rule has version int.
- **§4.2** Seed P10.b invariant set at substrate genesis; substrate `seed_compression_invariant_set` function in `events.rs` emits the canonical set.
- **§4.3** Per compression event: verify all targeted nodes pass P10.b membership check + recent-cycles-floor check; reject + emit C51 on violation.
- **§4.4** Emit witness payload sufficient for owner-side re-derivation. Witness contains enough to reconstruct the compressed segment's causal contribution (per I4).
- **§4.5** When P11.c triggers compression-needed (saturation), select the rule from F18 that targets compressible categories with highest expected gain.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** compress invariant-set members. C51 fires immediately.
- **§5.2** **MUST NOT** compress without emitting witness. C52 fires.
- **§5.3** **MUST NOT** mutate compression_rule_registry (F18) via daily channel. F18 is fixed-point.
- **§5.4** **MUST NOT** compress to destroy: compression must preserve recoverability per I9. "Compression" that erases is destruction, not compression — and destruction is P07's domain, not P10's.
- **§5.5** **MUST NOT** compress recent-cycle DAG (within `recent_cycles_floor`). The cultivar's working memory must stay legible.
- **§5.6** **MUST NOT** allow compression to inadvertently break P05 reachability — compressed nodes go to cold-tier or roll-up with F10 exemption, not into orphan limbo.

## §6. Frame declaration

P10 activates the **autolysis / decomposition** frame (mycological: fungi decompose substrates, including dead material from prior phases of their own mycelium).

A fungus decomposes its own old hyphae to recycle nutrients. The decomposition is *active*, not passive — enzymes target specific structures while preserving others. P10 is the cultivar's autolysis: choosing what to break down, what to keep, all under attestation.

NOT the *garbage collection* frame (GC is automatic; P10 is attested). NOT the *log rotation* frame (rotation is rate-based; P10 is content-aware). NOT the *deletion* frame (deletion destroys; P10 transforms via witness).

## §7. Common misreadings

### §7.1 M1: "Compression = data deletion"

**The misreading**: "P10 just deletes old material to save space."

**Why it's wrong**: P10 is *transformation with witness*, not deletion. The compressed roll-up retains enough information (the witness) for owner-side re-derivation. Deletion would violate I9 + P06 (causality lost).

### §7.2 M2: "Compression rules are tunable"

**The misreading**: "If we want to compress more aggressively, just change the rules."

**Why it's wrong**: F18 (compression_rule_registry) is CI-only fixed-point. Rule changes require cultivator attestation. Aggressive compression that bypasses the registry is C52.

### §7.3 M3: "Recent material can be compressed if needed"

**The misreading**: "Under severe saturation, we should compress even recent cycles to keep substrate operational."

**Why it's wrong**: P10.b `recent_cycles_floor` (≥1000) is invariant. The cultivar's working memory is protected. Under severe saturation, P11.c escalates: compression of older material → saturated stage → P7 mortality if recovery impossible. Cycling-recent compression is NEVER the answer.

## §8. Falsifiability + witness map

### §8.1 `compression_events_per_30_days`

Count of `compression_event:*` emissions per 30-day window. Some compression is expected (P02 + P04 generate material; P10 + P11 manage capacity). Sustained zero = substrate is either not absorbing or compression mechanism is broken.

### §8.2 `invariant_set_corruption_attempts`

Count of C51 (`compression_invariant_corruption`) emissions. Should be zero; non-zero = active corruption attempts or bug in compression rule.

### §8.3 `witness_recoverability_per_compression`

Audit signal: for each compression_event, run an owner-side recovery dry-run; verify the witness is sufficient. Failure = silent corruption of I9.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `substrate/tests/e2e_layer_c.rs::layer_c_p10_positive_compression_invariant_set_covers_p10_b` | Healthy compression: the seed compression invariant-set covers exactly the P10.b categories — what may be compressed and what must be preserved is correctly partitioned. |
| **Negative** | `substrate/tests/e2e_immune.rs::m26_3_compression_invariant_set_seed_covers_p10_b_categories` | **Sabotage defense**: the invariant set recognizes `genesis_event` and the other P10.b members as protected and rejects non-members like `raw_material:text` — the protection C51 fires on is wired correctly. |
| **Edge** | `substrate/tests/e2e_immune.rs::m26_3_compression_witness_canonical_bytes_roundtrip` | Boundary: a compression witness round-trips through canonical bytes — the witness carries sufficient information to re-derive the compressed segment (recovery is possible). |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P02** | P02 generates absorbable material; P10 compresses old absorbed material. The pair = metabolism's intake + excretion. |
| **P04** | Compression is itself a P04 event (DAG-recorded). Iteration includes compression cycles. |
| **P06** | Compression preserves causality via witness. P06 eternity-clause constrains P10's witness sufficiency. |
| **P07** | If compression cannot free enough capacity for continued operation, escalation goes to P11.c → P07 mortality. Compression is NOT permitted to "save" a substrate at the cost of corrupting invariants. |
| **P11** | P11.c uses P10 as its primary recovery mechanism under saturation. Compression-insufficient → degraded → mortality. |
| **Cultivator's Covenant** | Cultivator attests F18 rule changes; cultivator's choice of compression aggressiveness shapes the cultivar's identity. See `COV03_food_provision.md`. |

## §10. Illustrations

### §10.1 Honored

- **(Routine compression)**: After 2000 cycles, substrate has accumulated 50000 `raw_material_ingested` events. Rule `raw_material_aggregate_v1` (in F18) compresses 30000 oldest events (those beyond `recent_cycles_floor`) into one `compression_event:raw_material_aggregate_v1` with aggregate witness. P10.b invariant set untouched. Cold-tier holds the witness. ← Honored.

- **(Saturation recovery)**: Substrate hits `budget_exhausted:storage`. P11.c step 2 triggers compression. P10 selects appropriate rule, frees ~30% capacity. Substrate resumes normal operation. ← P10 + P11 cooperation honored.

### §10.2 Violated

- **(Invariant set compression)**: A compression rule mistakenly includes `genesis_event` in its target prefix. Substrate's P10.b check catches; C51 fires; compression rejected. If check fails (broken detector), the rule lands and corrupts substrate identity. ← §5.1.

- **(Unattested compression)**: A daily-class mutation compresses 100 old nodes without going through the registry. ← §5.2 + §5.3 violation.

- **(Recent-cycle compression)**: Under severe saturation, an emergency rule attempts to compress 500 recent cycles. ← §5.5 violation; rule should never have been added to F18.

### §10.3 Borderline

- **(Aggressive vs cautious cultivar)**: Cultivator-A sets F18 to compress raw_material aggressively (every 200 cycles); Cultivator-B sets it cautiously (every 10000 cycles). Both are within doctrine. The resulting cultivars are *different* in feel — Cultivar-A is minimalist; Cultivar-B is encyclopedic. ← Both honor P10; the diversity is identity-shaping (per §2).

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 with P10.a/b/c sub-clauses. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. P10.a/b/c integrated into Formulation + Positive obligations. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/attestation.rs::handle_submit_mutation` | Compression mutation handling (CI-gated). |
| `substrate/src/events/compression.rs::compression_event_node_type` | Compression event emission. |
| `substrate/src/events/compression.rs::seed_compression_invariant_set` | P10.b invariant set seed at genesis. |
| `substrate/src/events/compression.rs` | F18 compression-rule registry seed defaults. |

## §13. Related Layer B chengyu

- **B022 忘以為憶** — *forget-in-order-to-remember*: P10 deposit
- **B023 留核棄殼** — *preserve-kernel-shed-husk*: invariant-set vs compressible

## §14. Related canonical dilemmas

- **D-0006 orphan detection post compression** — boundary between compression (allowed) and orphaning (forbidden); shared with P05.
- **D-0022 invariant set corruption attempt** — rule targets `genesis_event`; tests C51.

---

**Doctrine commitment**: choose what to forget so you can keep growing; the choice itself is who you are.
