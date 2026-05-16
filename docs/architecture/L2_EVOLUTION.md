# L2 — Evolution Doctrine

> Cross-cuts L0 P3 + L1_GOVERNANCE §1.3/§6 + L1_SCHEMA §1.3/§4.2 + L1_TROPISM §B1 + L1_TRAJECTORY §5 + L0 §10.2. All numeric thresholds L1-tunable unless specified.

---

## §1. What evolves

Five classes of mutable substrate state; unifying principle **P3 — substrate's own shape evolves**:

| Class | Examples | Governance | Discipline |
|---|---|---|---|
| Schema (SSoT) | Fields exist; what I3 validates | Contract-identity (F8) | Two-phase migration (L1_SCHEMA §1.3) |
| Lexicon | Subsystem/appetite/sporocarp names | Contract-identity (L0 P3) | Mycology-literature attestation; deprecation `terminal` (L0 §5.1) |
| Dispatch parameters | Appetite-axis schema; sporocarp-type tree; clusterer choice | Contract-identity | P3 evolution; I3-failure rollback |
| Threshold values (steady) | Emergent fruiting; bets weights; signals | Daily-autonomous (non-mortality); CI for mortality | Emergent from history (C6.4) |
| L0/L1 doctrine | This document set | Owner-attested via L0 §10.2 | Burst-detection per L0 §9.4 |

---

## §2. Evolution invariants

- **§2.1 Causal traceability (I4)**: every event DAG-recorded; pre-evolution state retained (L1_SCHEMA §2.3 cold-tier); post-evolution references prior; Merkle proves legitimacy.
- **§2.2 Failure rollback (P3)**: I3-inconsistent → pre-evolution snapshot; recorded `evolution_failed` (CI-elevated, ungated); in-flight CI sporocarps in window dropped as `evolution_failed_pending_dropped`.
- **§2.3 No silent corruption (I3)**: SSoT-changing passes two-phase migration: candidate alongside current; per-cycle dual-validation; mismatch → `ssot_migration_inconsistent` + abort.

---

## §3. Three layers

- **§3.1 Doctrine (L0/L1)** — slowest; Cultivator-attested per **L0 §10.2 + L1_OUTLINE §4 item 3**. L0 revision diffs verbatim against prior commit hash; burst-detection per L0 §9.4 emits `doctrine_instability`.
- **§3.2 Schema/dispatch (CI)** — **L1_SCHEMA §1.3** two-phase migration; **L1_GOVERNANCE §2.2** dispatch-parameter evolution; I3-failure rollback per §2.2.
- **§3.3 Daily (threshold)** — fast; daily-autonomous (non-mortality); emergent per C6.4. Constraints: mortality-signal triple (threshold + update-rule + emergence-rule) CI-level; tier-1 fields cannot be daily-mutated; I3-inconsistent → §2.2 rollback.

---

## §4. Versioning

Every evolvable state has explicit versions; historical state validates against own version. Carriers: SSoT designation (L1_SCHEMA §1.3); `causal_proof_template` (L1_TROPISM §B1 `template_version_registry`); `Cluster_C` (L1_TRAJECTORY §4 CI creates trajectory epoch); owner-key history (L1_GOVERNANCE §3.1); signature suite. **Active-prefix + archived-tail** applied to all monotone tier-1 fields; per-cycle tier-1 cost O(K) regardless of age.

---

## §5-§10. Cross-references + summary

§5 schema-evolution epochs: L1_TRAJECTORY §5 — each contract-identity mutation creates `epoch_boundary` sporocarp; queries default within-epoch; long-horizon thread_id grouping at L1_TRAJECTORY §6.

§6 lexicon evolution: L0 P3 + §5.1 (mycology-literature attestation; deprecation marks `terminal`; historical sporocarps retain old term per I4; cross-epoch translation L4-deferred). CI because vocabulary shifts cascade through all sporocarps emitted under it.

§7 birth-period: L1_GOVERNANCE §1.3 + L2_LIFECYCLE §3.

§8 observability: L2_OBSERVABILITY §2.1 (signal #2 evolution-rate; zero = stagnation/P3-weak; excessive = `doctrine_instability` per L0 §9.4) + §8 (burst detector).

§9 failure modes: L1_GOVERNANCE §6.2 — failed schema migration / template evolution / lexicon mutation share rollback shape; pre-evolution snapshot restored; in-flight sporocarps dropped; emissions under failed template marked `failed_template_emission`. Persistent failure: ≥3 consecutive within window → quarantine per L1_CONTINUITY §5.1.

§10 summary: substrate evolves freely in steady state, disciplined at three layers — (1) doctrine: rare, owner-attested, burst-detected; (2) schema/dispatch: two-phase migration + canonical-bytes + I3-rollback; (3) threshold/parameter: emergent + mortality-protected. Active-prefix + archived-tail keeps tier-1 cost O(K). **Substrate that does not evolve is dead** (L0 P3); silent/arbitrary evolution violates I3/I4.
