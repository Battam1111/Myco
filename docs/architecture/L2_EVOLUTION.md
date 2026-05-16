# L2 — Evolution Doctrine

> **Status**: DRAFT 2 (2026-05-17, M27 CA5 cleanup). Cross-cut doctrine theme.
> **Scope**: substrate-self-evolution discipline. Cross-cuts L0 P3 + L1_GOVERNANCE §1.3 / §6 + L1_SCHEMA §1.3 / §4.2 + L1_TROPISM §B1 + L1_TRAJECTORY §5 + L0 §10.2 doctrine-revision protocol.

---

## §1. What evolves in v0.9

Five classes of mutable substrate state, each with its own evolution discipline:

| Class | Examples | Governance | Discipline |
|---|---|---|---|
| **Schema (SSoT designation)** | What fields exist; what claims I3 validates against | Contract-identity-level (L1_HARD_RULES F8) | Two-phase migration (L1_SCHEMA §1.3) |
| **Lexicon (vocabulary)** | Subsystem names; appetite names; sporocarp types | Contract-identity-level (per L0 P3 lexicon evolution clause) | Add via mycology-literature attestation; deprecate marks `terminal` (per L0 §5.1) |
| **Dispatch parameters** | Appetite-axis schema; sporocarp-type tree; clusterer choice | Contract-identity-level | P3 evolution with rollback on I3 failure |
| **Threshold values (in steady state)** | Emergent fruiting triggers; living-bets weights; observatory signals | Daily-autonomous IF non-mortality; CI for mortality axis | Emergent from substrate history (per C6.4) |
| **L0/L1 doctrine itself** | This document set | Owner-attested via L0 §10.2 protocol | Burst-detection per L0 §9.4 |

Each class has its own rules; the unifying principle is **P3: substrate's own shape evolves**.

---

## §2. The evolution invariants

Three invariants must hold across ALL evolution operations:

### §2.1 Causal traceability (I4)

Every evolution event is recorded in the causal DAG. Pre-evolution state is retained (per L1_SCHEMA §2.3 cold-tier eligibility); post-evolution state is a new DAG node referencing the prior. The Merkle chain proves the evolution happened legitimately.

### §2.2 Failure rollback (P3 failed-evolution clause)

Per L0 P3 + L1_GOVERNANCE §6: when an evolution produces an I3-inconsistent state, the substrate rolls back to pre-evolution snapshot. Rolled-back state is recorded as `evolution_failed` sporocarp (CI-elevated, ungated — failure is automatic). Pending CI sporocarps fruited within rolled-back window are dropped as `evolution_failed_pending_dropped`.

### §2.3 No silent corruption (I3)

Every state-claim against SSoT must be verifiable. Evolution that changes SSoT must pass two-phase migration: candidate SSoT lives alongside current SSoT; substrate runs dual-validation every cycle; mismatch emits `ssot_migration_inconsistent` and aborts.

---

## §3. The three evolution layers (descending granularity)

### §3.1 Doctrine evolution (L0 / L1 revision)

Cross-ref L0 §10.2 (revision protocol) + L1_OUTLINE §4 item 3 (L1-vs-L0 burst-tolerance asymmetry). Doctrine evolution is the slowest tier; Cultivator-attested; L0 revision diffs verbatim against prior L0 commit hash; burst-detection per L0 §9.4 emits `doctrine_instability` immune event.

### §3.2 Schema evolution (SSoT, dispatch params)

**Medium-paced**. CI-attested per L1_GOVERNANCE §2.2.

- **SSoT migration two-phase commit**: L1_SCHEMA §1.3 (candidate ≥M cycles co-exist; dual-validation each cycle; mismatch → abort; Cultivator co-signs; old SSoT cold-tier-retained per I4).
- **Dispatch-parameter evolution** (appetite-axis schema, sporocarp-type tree, classifier table, lexicon): standard L1_GOVERNANCE §2.2 CI protocol; rollback on I3 failure per §2.2.

### §3.3 Daily evolution (steady-state thresholds)

**Fast**. Daily-autonomous for non-mortality axes; emergent thresholds update continuously from substrate-history correlations per C6.4.

Constraints:
- Mortality-signal axis threshold + update-rule + emergence-rule are CI-level (cannot be silently tuned to suppress mortality)
- Tier-1 fields cannot be daily-mutated even by emergent threshold updates
- Threshold updates that produce I3-inconsistent state trigger §2.2 rollback (same as schema)

---

## §4. Versioning everything that evolves

**Why versioning**: without versions, evolved state cannot reference historical state. v0.9's discipline: every evolvable state has explicit versions; historical state validates against its own version.

**What carries versions** (full mechanism specs in cited L1 docs):
- **SSoT designation** — L1_SCHEMA §1.3 (migration; I4 archival).
- **causal_proof_template** — L1_TROPISM §B1 (`template_version_registry`).
- **Cluster_C** — L1_TRAJECTORY §4 (CI event creating new trajectory epoch).
- **Owner-key history** — L1_GOVERNANCE §3.1 (active-prefix + archived-tail).
- **Signature suite** — L1_GOVERNANCE §3.1 same pattern.

**Active-prefix + archived-tail discipline**: full spec L1_GOVERNANCE §3.1; applied to all monotone tier-1 fields; keeps per-cycle tier-1 cost O(K) regardless of substrate age (closes pass-3 saprotroph-1 unbounded growth).

---

## §5. Schema-evolution trajectory epochs

Per L1_TRAJECTORY §5: each contract-identity-level mutation creates a new trajectory epoch marker (`epoch_boundary` sporocarp). Trajectory queries default to within current epoch.

**Cross-epoch queries are deferred to L4** (per pass-2 astronaut-2): writing predicate-translation machinery before the substrate has survived its first schema change is premature. L4 codifies after observed need.

Implication: trajectory becomes "natively scoped" to the current schema epoch. Long-horizon agent goals (rhizomorph attack from C8.2 craft) that span multiple epochs may need explicit thread_id grouping (L1_TRAJECTORY §6 orthogonal grouping primitive) rather than trajectory clustering.

---

## §6. Lexicon evolution

**Mechanism**: L0 P3 lexicon-evolution clause + L0 §5.1 (mycology-literature attestation requirement; deprecation marks `terminal`; historical sporocarps retain old term per I4; cross-epoch translation deferred to L4).

**Why CI**: vocabulary shifts cascade through all sporocarps emitted under it. Silent vocabulary drift would break I3.

---

## §7. Birth-period evolution discipline

**Mechanism**: L1_GOVERNANCE §1.3 (during birth, ALL parameter-tuning elevates to CI; max-duration 180 days prevents attention-exhaustion attack). Cross-cut: L2_LIFECYCLE §3.

---

## §8. Evolution observability

Cross-ref L2_OBSERVABILITY §2.1 (signal #2 evolution-rate; zero rate = stagnation, P3 weak; excessive rate = `doctrine_instability` per L0 §9.4) + §8 (doctrine-instability burst detector).

---

## §9. Evolution failure modes

**Rollback procedure**: L1_GOVERNANCE §6.2 (failed schema migration / failed template evolution / failed lexicon mutation all share the same rollback shape — pre-evolution snapshot restored; pending sporocarps in rolled-back window dropped; sporocarps emitted under failed template marked `failed_template_emission`).

**Persistent failure pattern**: ≥3 consecutive failed evolutions within L1-tunable window → substrate enters standard quarantine per L1_CONTINUITY §5.1. No separate `evolution_quarantine` sub-state.

---

## §10. Evolution discipline summary

The substrate evolves freely in steady state, with discipline at three levels:

1. **Doctrine** (L0/L1): rare, owner-attested, burst-detected.
2. **Schema/dispatch** (CI-level state): two-phase migration; canonical bytes; rollback on I3 failure.
3. **Threshold/parameter** (daily steady-state): emergent from history; mortality protection enforced.

Active-prefix + archived-tail discipline ensures monotone tier-1 fields don't impose unbounded per-cycle cost. Versioning everything that evolves ensures historical state remains validatable.

**The substrate that does not evolve is dead** (per L0 P3). The substrate that evolves silently or arbitrarily violates I3/I4. v0.9 makes the discipline explicit at every layer.

---

## §11. Open at L2

- **L0 / L1 archive discipline**: how is the full history of L0/L1 revisions persisted for cold-read by future agents at year-30? Current commits-as-archaeology pattern is adequate; possibly worth substrate-side mirroring of doctrine git-blobs for offline access.
- **Cross-epoch trajectory translation format**: deferred to L4 per L1_TRAJECTORY §5.
- **Suite-break vs suite-deprecation**: cryptographic-suite rotation when current suite is broken (not just deprecated) needs historical re-anchoring. L1_GOVERNANCE §3.1 says "same pattern as key rotation" but operationalization is L4.
- **Decade-scale archived-tail validation cost**: active-prefix + archived-tail discipline keeps per-cycle tier-1 cost O(K), but deep-cycle Merkle-anchor validation over the FULL archived chain grows with substrate age. **Open**: does archived-tail need PERIODIC RE-ANCHORING (e.g., every 5 years, Cultivator co-signs full archived-tail Merkle root)? L4 confirms.
- **Federation historical re-anchoring**: 20+-year-old `federation_coupling` sporocarps reference aggregate-reattestation roots from epochs where signature suites may be deprecated. Possible mechanism: at suite rotation, Cultivator co-signs a `federation_historical_reanchor` event. L4 codifies.
