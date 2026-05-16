# L2 — Evolution Doctrine

> **Status**: DRAFT 2 (2026-05-17, M27 CA5 cleanup). Cross-cuts L0 P3 + L1_GOVERNANCE §1.3 / §6 + L1_SCHEMA §1.3 / §4.2 + L1_TROPISM §B1 + L1_TRAJECTORY §5 + L0 §10.2.

---

## §1. What evolves in v0.9

Five classes of mutable substrate state:

| Class | Examples | Governance | Discipline |
|---|---|---|---|
| **Schema (SSoT designation)** | What fields exist; what claims I3 validates | Contract-identity (L1_HARD_RULES F8) | Two-phase migration (L1_SCHEMA §1.3) |
| **Lexicon** | Subsystem names; appetite names; sporocarp types | Contract-identity (L0 P3 lexicon clause) | Mycology-literature attestation; deprecation marks `terminal` (L0 §5.1) |
| **Dispatch parameters** | Appetite-axis schema; sporocarp-type tree; clusterer choice | Contract-identity | P3 evolution; rollback on I3 failure |
| **Threshold values (steady state)** | Emergent fruiting; living-bets weights; observatory signals | Daily-autonomous if non-mortality; CI for mortality | Emergent from substrate history (C6.4) |
| **L0/L1 doctrine** | This document set | Owner-attested via L0 §10.2 | Burst-detection per L0 §9.4 |

Unifying principle: **P3 — substrate's own shape evolves**.

---

## §2. Evolution invariants (must hold across ALL evolution)

- **§2.1 Causal traceability (I4)** — Every evolution event recorded in DAG; pre-evolution state retained (L1_SCHEMA §2.3 cold-tier); post-evolution is new DAG node referencing prior. Merkle chain proves legitimacy.
- **§2.2 Failure rollback (P3)** — Per L0 P3 + L1_GOVERNANCE §6: I3-inconsistent state triggers rollback to pre-evolution snapshot; recorded as `evolution_failed` (CI-elevated, ungated); pending CI sporocarps in rolled-back window dropped as `evolution_failed_pending_dropped`.
- **§2.3 No silent corruption (I3)** — SSoT-changing evolution must pass two-phase migration: candidate SSoT alongside current; per-cycle dual-validation; mismatch emits `ssot_migration_inconsistent` and aborts.

---

## §3. Three evolution layers (descending granularity)

- **§3.1 Doctrine (L0/L1)** — Slowest. Cultivator-attested per L0 §10.2 + L1_OUTLINE §4 item 3. L0 revision diffs verbatim against prior commit hash; burst-detection per L0 §9.4 emits `doctrine_instability`.
- **§3.2 Schema/dispatch (CI)** — Medium-paced. L1_SCHEMA §1.3 two-phase SSoT migration (candidate ≥M cycles co-exist; dual-validation; mismatch aborts; Cultivator co-signs; old SSoT cold-tier-retained per I4). Dispatch-parameter evolution per L1_GOVERNANCE §2.2; rollback on I3 failure per §2.2.
- **§3.3 Daily (threshold)** — Fast. Daily-autonomous for non-mortality; emergent thresholds update continuously per C6.4. Constraints: mortality-signal threshold + update-rule + emergence-rule CI-level; tier-1 fields cannot be daily-mutated; I3-inconsistent updates trigger §2.2 rollback.

---

## §4. Versioning everything that evolves

Every evolvable state has explicit versions; historical state validates against its own version.

What carries versions (full specs in cited L1 docs):
- **SSoT designation** — L1_SCHEMA §1.3.
- **causal_proof_template** — L1_TROPISM §B1 (`template_version_registry`).
- **Cluster_C** — L1_TRAJECTORY §4 (CI event creating new trajectory epoch).
- **Owner-key history** — L1_GOVERNANCE §3.1.
- **Signature suite** — L1_GOVERNANCE §3.1 same pattern.

**Active-prefix + archived-tail** (L1_GOVERNANCE §3.1) applied to all monotone tier-1 fields; keeps per-cycle tier-1 cost O(K) regardless of substrate age.

---

## §5. Schema-evolution trajectory epochs

L1_TRAJECTORY §5: each contract-identity-level mutation creates `epoch_boundary` sporocarp. Trajectory queries default to within current epoch. Cross-epoch queries L4-deferred. Long-horizon agent goals spanning epochs may need explicit `thread_id` grouping (L1_TRAJECTORY §6) rather than trajectory clustering.

---

## §6. Lexicon evolution

L0 P3 lexicon-evolution clause + §5.1 (mycology-literature attestation; deprecation marks `terminal`; historical sporocarps retain old term per I4; cross-epoch translation L4-deferred). CI because vocabulary shifts cascade through all sporocarps emitted under it — silent drift would break I3.

---

## §7. Birth-period

L1_GOVERNANCE §1.3 + L2_LIFECYCLE §3.

---

## §8. Evolution observability

L2_OBSERVABILITY §2.1 (signal #2 evolution-rate; zero=stagnation/P3-weak; excessive=`doctrine_instability` per L0 §9.4) + §8 (doctrine-instability burst detector).

---

## §9. Failure modes

L1_GOVERNANCE §6.2: failed schema migration / template evolution / lexicon mutation share rollback shape — pre-evolution snapshot restored; pending sporocarps dropped; sporocarps emitted under failed template marked `failed_template_emission`. Persistent failure: ≥3 consecutive within L1-tunable window → standard quarantine per L1_CONTINUITY §5.1 (no separate `evolution_quarantine` sub-state).

---

## §10. Summary

Substrate evolves freely in steady state, disciplined at three layers: (1) doctrine — rare, owner-attested, burst-detected; (2) schema/dispatch — two-phase migration, canonical bytes, rollback on I3 failure; (3) threshold/parameter — emergent from history, mortality protected. Active-prefix + archived-tail keeps per-cycle tier-1 cost O(K). Versioning ensures historical state remains validatable.

**The substrate that does not evolve is dead** (L0 P3). Silent or arbitrary evolution violates I3/I4.
