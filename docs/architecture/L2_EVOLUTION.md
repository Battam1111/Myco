# L2 — Evolution Doctrine

> **Status**: DRAFT 1 (2026-05-13). Cross-cut doctrine theme.
> **Layer**: L2.
> **Scope**: substrate-self-evolution discipline. Cross-cuts L0 P3 / P3.b joint-context evolution + lexicon evolution + L1_GOVERNANCE §1.3 birth-period CI elevation / §6 failed-evolution rollback + L1_SCHEMA §1.3 SSoT migration two-phase + §4.2 tier promotion/demotion + L1_TROPISM §B1 template versioning + L1_TRAJECTORY §5 schema-evolution epochs + L0 §9.4 L0-revision burst-detection. Answers: how does v0.9 evolve its own shape over decades without violating invariants?

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

**Slowest**. Owner-attested per L0 §10.2 protocol. L0 revision diffs are verbatim against prior L0 commit hash; owner reviews canonical bytes at anchor surface (not substrate-supplied summary).

Burst-detection per L0 §9.4: ≥L1-tunable rate of L0/L1 revisions over rolling window emits `doctrine_instability` immune event. Owner reviews whether revisions are doctrine-driven (continue) or implementation-driven (rollback). Rolling rate over 12 months above threshold marks `doctrine_drift_grade`.

**L0 revisions should be rare post-seal.** L1 revisions may be more frequent (L1 is closer to mechanism); L1_OUTLINE §4.3 acknowledges higher tolerance.

### §3.2 Schema evolution (SSoT, dispatch params)

**Medium-paced**. CI-attested per L1_GOVERNANCE §2.2.

For SSoT migration (L1_SCHEMA §1.3):
1. New candidate SSoT designation co-exists with current for ≥M cycles (default 1000 cycles or 30 days, whichever longer).
2. Substrate runs dual-validation every cycle. Mismatch → abort.
3. Owner co-signs migration via anchor surface.
4. Old SSoT retained per I4 (cold-tier-eligible).

For dispatch-parameter evolution (appetite-axis schema, sporocarp-type tree, classifier table, lexicon):
1. CI proposal lands at anchor surface per L1_GOVERNANCE §2.2.
2. Owner reviews canonical bytes; signs.
3. Substrate applies in next cycle.
4. If next cycle's I3 fails → rollback per §2.2.

### §3.3 Daily evolution (steady-state thresholds)

**Fast**. Daily-autonomous for non-mortality axes; emergent thresholds update continuously from substrate-history correlations per C6.4.

Constraints:
- Mortality-signal axis threshold + update-rule + emergence-rule are CI-level (cannot be silently tuned to suppress mortality)
- Tier-1 fields cannot be daily-mutated even by emergent threshold updates
- Threshold updates that produce I3-inconsistent state trigger §2.2 rollback (same as schema)

---

## §4. Versioning everything that evolves

### §4.1 Why versioning

Without versions, evolved state cannot reference historical state. Validating a year-old sporocarp under the current schema fails if the schema evolved meanwhile. v0.9's discipline: every evolvable state has explicit versions; historical state validates against its own version.

### §4.2 What carries versions

- **SSoT designation**: each designation is a contract-identity-level object; migration transitions update the active designation; prior designations are archived per I4.
- **causal_proof_template** (L1_TROPISM §B1): each template carries `template_version`. Sporocarps record version under which proof was computed; I3 validates against that version, not the current. `template_version_registry` (CI-level field, active-prefix + archived-tail discipline) lists historical templates.
- **Cluster_C** (L1_TRAJECTORY §4): substrate-resident clustering algorithm. Each change is a CI event creating a new trajectory epoch.
- **Owner key history** (L0 I1 + L1_GOVERNANCE §3.1): chronological list of `(public_key_n, valid_from, valid_until, rotation_attestation)` with active-prefix + archived-tail.
- **Signature suite**: same pattern as owner keys; historical signatures verify under the suite valid at the time.

### §4.3 Active-prefix + archived-tail discipline

Per L1_GOVERNANCE §3.1, applied to all monotone tier-1 fields (closes pass-3 saprotroph-1 unbounded growth):

- **Active prefix**: most-recent K entries + currently-valid entries. Participates in per-cycle tier-1 I3 validation. O(K) cost.
- **Archived tail**: older entries. Stored cold-tier-eligible (per L1_SCHEMA §2.3). Validated at deep-cycle scope via Merkle anchor over the full chain.

This keeps tier-1 per-cycle cost O(K) regardless of substrate age.

---

## §5. Schema-evolution trajectory epochs

Per L1_TRAJECTORY §5: each contract-identity-level mutation creates a new trajectory epoch marker (`epoch_boundary` sporocarp). Trajectory queries default to within current epoch.

**Cross-epoch queries are deferred to L4** (per pass-2 astronaut-2): writing predicate-translation machinery before the substrate has survived its first schema change is premature. L4 codifies after observed need.

Implication: trajectory becomes "natively scoped" to the current schema epoch. Long-horizon agent goals (rhizomorph attack from C8.2 craft) that span multiple epochs may need explicit thread_id grouping (L1_TRAJECTORY §6 orthogonal grouping primitive) rather than trajectory clustering.

---

## §6. Lexicon evolution

Per L0 P3 lexicon-evolution clause + L0 §5.1:

**Adding a term**:
- Requires mycology-literature attestation (the new term describes a real fungal phenomenon)
- CI event; owner co-signs at anchor surface
- New term lands in lexicon registry

**Deprecating a term**:
- Marks term `terminal` — no new sporocarps use it
- Historical sporocarps with the deprecated term retain it per I4 (no retroactive edits)
- Cross-epoch translation tables (deferred to L4) MAY map deprecated → current within strict-mycology constraint

**Why lexicon is CI**: vocabulary shifts cascade through all sporocarps emitted under it. Silent vocabulary drift would break I3 (claims under new vocabulary not validatable against historical sporocarps under old vocabulary).

---

## §7. Birth-period evolution discipline

Per L2_LIFECYCLE §3 + L1_GOVERNANCE §1.3: during birth period, ALL parameter-tuning events are CI-level regardless of steady-state classification.

This means during birth:
- Threshold seed adjustments → CI
- Lexicon additions → CI (same as steady state)
- Schema tweaks → CI
- Appetite-axis additions → CI

The CI elevation is intentional: owner attention is concentrated when the substrate is most vulnerable to silent bad-tuning. Birth-period maximum duration (default 180 active-operation days) prevents indefinite CI-elevation as an attention-exhaustion attack vector.

After birth-period termination, most parameter-tuning relaxes to daily-autonomous per the classifier dimension table.

---

## §8. Evolution observability

The Living Bets observatory (L0 §7) tracks evolution-rate as signal #2. Healthy v0.9 substrates evolve continuously (P3); zero evolution rate is a stagnation signal (Living Bets weak). Excessive evolution rate triggers `doctrine_instability` (per L0 §9.4).

The substrate's evolution-rate baseline is itself emergent from historical metrics per C6.4. Pathological patterns (e.g., L0 revisions spiking during owner-unavailability) are immune-detectable.

---

## §9. Evolution failure modes

### §9.1 Failed schema migration

Per L1_GOVERNANCE §6.2 rollback procedure. Pre-evolution snapshot is restored; pending sporocarps fruited within rolled-back window are dropped.

### §9.2 Failed template evolution

Same pattern: rollback to prior template_version. Sporocarps emitted under the failed version are marked `failed_template_emission`; they retain their causal_in_edges but I3 validation under the rollback template will likely fail them, routing through standard quarantine entry per L1_CONTINUITY §5.1.

### §9.3 Failed lexicon mutation

Lexicon additions that pass owner attestation but produce I3 failures in subsequent cycles trigger standard rollback. Deprecations should not produce I3 failures (deprecated terms in historical sporocarps remain valid via I4 retention).

### §9.4 Persistent evolution failure pattern

If repeated evolutions fail (≥3 consecutive within L1-tunable window), substrate enters standard quarantine per L1_CONTINUITY §5.1. No separate `evolution_quarantine` sub-state (cut per pass-2 astronaut-7).

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
- **Cross-epoch trajectory translation format**: deferred to L4 per L1_TRAJECTORY §5; expected to emerge from first multi-epoch concrete need.
- **Suite-break vs suite-deprecation** (per pass-2 saprotroph-5): cryptographic-suite rotation when current suite is broken (not just deprecated) needs historical re-anchoring. L1_GOVERNANCE §3.1 says "same pattern as key rotation" but operationalization is L4.
