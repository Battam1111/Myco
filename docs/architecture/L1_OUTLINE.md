# L1 — Outline / Charter

> **Status**: OUTLINE (post L0 DRAFT 9 SEALED, 2026-05-17, commit `e796451`).
> **Layer**: L1. Governed by L0.
> **Authority**: navigation only — no binding authority. The L1 documents listed below ARE the authoritative L1 layer.

---

## §0. What L1 is

L1 is the **mechanism enforcement layer** for L0's principles + invariants. L0 commits to identity, negative space, and constraints; L1 commits to the positive forms satisfying those constraints. A statement belongs in L1 if it answers "*how does the substrate actually do X?*".

---

## §1. L1 document set — current state

| File | Topic | Status |
|---|---|---|
| **`L1_OUTLINE.md`** (this file) | L1 charter + index | OUTLINE |
| **`L1_TROPISM.md`** | Positive dispatch form | **DRAFT 2 (2026-05-13)** ✓ |
| **`L1_TRAJECTORY.md`** | Positive intent-derivation | **DRAFT 2 (2026-05-13)** ✓ |
| **`L1_SCHEMA.md`** | SSoT, Merkle DAG, recoverability, spore-schema, validation tiers | **DRAFT 1 (2026-05-13)** ✓ NEW |
| **`L1_GOVERNANCE.md`** | I2 classifier, lifecycle, owner attestation, succession, federation discovery | **DRAFT 1 (2026-05-13)** ✓ NEW |
| **`L1_SKIN.md`** | I8 envelope, handshake, single-operator, network-egress, breach detection | **DRAFT 1 (2026-05-13)** ✓ NEW |
| **`L1_CONTINUITY.md`** | Metabolic cycle, dormancy, recovery, delta atomicity | **DRAFT 1 (2026-05-13)** ✓ NEW |
| `L1_HARD_RULES.md` | Cross-cuts index of CRITICAL breaches + CI fixed-points + anchor-surface-resident state | **DRAFT 1 (2026-05-13)** ✓ NEW |

**All 7 L1 docs exist as DRAFTs.** L1 layer is structurally complete. L1_HARD_RULES is the cross-cuts index — NOT a v0.8 R1-R7 grammatical inheritance per C7.3 max-discrimination; it independently traces every row to ≥1 P + ≥1 I (see L1_HARD_RULES §6 "What this doc is NOT").

---

## §2. Coverage of L0 design hooks across L1 docs

| L0 reference | L1 doc owning it |
|---|---|
| §5.2 positive dispatch form | `L1_TROPISM.md` ✓ |
| §5.3 positive intent-derivation | `L1_TRAJECTORY.md` ✓ |
| §6 metabolic cycle cadence | `L1_CONTINUITY.md` ✓ |
| §6 dormancy compute budget | `L1_CONTINUITY.md` ✓ |
| §6 delta atomicity | `L1_CONTINUITY.md` ✓ |
| P3 failed-evolution rollback | `L1_GOVERNANCE.md` ✓ |
| P3.b joint-context evolution epoch markers | `L1_TRAJECTORY.md` (epoch boundaries) + `L1_SCHEMA.md` (DAG nodes) ✓ |
| P5.1 lexicon evolution discipline | `L1_GOVERNANCE.md` ✓ |
| P7 endogenous mortality | `L1_GOVERNANCE.md` (lifecycle) ✓ |
| P8 federation discovery | `L1_GOVERNANCE.md` ✓ |
| P8 spore-schema contents | `L1_SCHEMA.md` ✓ |
| I1 operator-token construction | `L1_SKIN.md` ✓ |
| I1 legacy sub-state | `L1_GOVERNANCE.md` (owner succession) + `L1_CONTINUITY.md` (sub-state) ✓ |
| I2 classifier function | `L1_GOVERNANCE.md` ✓ |
| I3 SSoT format + claim coverage | `L1_SCHEMA.md` ✓ |
| I3 migration two-phase commit | `L1_SCHEMA.md` ✓ |
| I3 validation tiering | `L1_SCHEMA.md` ✓ |
| I4 DAG storage + Merkle integrity | `L1_SCHEMA.md` ✓ |
| I4 retention + materialized-views | `L1_SCHEMA.md` ✓ |
| I4 sporocarp causal-proof | `L1_TROPISM.md` ✓ |
| I5 storage tiers + enumerability | `L1_SCHEMA.md` ✓ |
| I6 internal implementation | `L1_TROPISM.md` (appetite-locality) ✓ |
| I6 network-egress detection | `L1_SKIN.md` ✓ |
| I6 embedding-service carve-out | `L1_TROPISM.md` + `L1_SKIN.md` ✓ |
| I7 closure verification | `L1_SCHEMA.md` (spore-schema validation) + `L1_GOVERNANCE.md` (reproduction) ✓ |
| I7 peer-trust freshness | `L1_GOVERNANCE.md` ✓ |
| I8 envelope schema | `L1_SKIN.md` ✓ |
| I8 single-operator handshake | `L1_SKIN.md` ✓ |
| I8 handshake continuity-challenge | `L1_SKIN.md` ✓ |
| I8 cold-resume invariant checks | `L1_CONTINUITY.md` ✓ |
| §7 Living Bets signal #6 attestation cross-check | `L1_SKIN.md` ✓ |
| §7 Living Bets signal #6 model-class epoch buckets | `L1_GOVERNANCE.md` (epoch boundaries) ✓ |
| §7 falsifiability trigger predicate | `L1_GOVERNANCE.md` (observatory) + L0 (predicate) ✓ |
| §9 anchor surface specific form | `L1_GOVERNANCE.md` ✓ |
| §9.4 L0-revision burst detection | `L1_GOVERNANCE.md` ✓ |
| §11 birth-period N | `L1_TROPISM.md` (steady-state activation) + `L1_GOVERNANCE.md` (owner vigilance + maximum-duration) ✓ |
| P1.a self-hosting bootstrap | `L1_TROPISM.md` §B10 ✓ |
| §10.2 L0-revision back-pressure protocol | this `L1_OUTLINE.md` §4 + L0 §10.2 ✓ |
| §11 privacy/access (no internal boundaries) | implicit L1_SKIN §1 single-skin ✓ |

**Every L0 design hook has an L1 owner.**

---

## §4. Cross-document discipline

1. **Each L1 doc carries a small §1 "what this doc commits to"** — already established in all current L1 docs.
2. **Cross-doc consistency** — when one L1 doc says "X is governance-classified", L1_GOVERNANCE classifier dimension table (§1.2) is the source of truth. Other L1 docs cite, not duplicate.
3. **L1 mutation discipline** — a change to an L1 doc is contract-identity-level (per L0 I2). Same proposal-and-approval process as L0 modifications, with one specific difference: L1 revisions may be more frequent than L0 revisions (L1 evolves as L2/L3 implementation surfaces refinement needs); L0 §9.4 burst-detection threshold for L1 is L1-tunable but recommended higher tolerance than L0 (since L1 is closer to implementation).
4. **L0 revision back-pressure** — per L0 §10.2: when L1 work reveals an L0 constraint is unworkable, the L1 doc records the finding and L0 revision is proposed through L0 §10.2 protocol. The L1 doc is NOT silently weakened to "fit" a wrong L0.

---

## §5. Confidence + partition discipline

Per L0 §10.2: L1 mechanism specifications use "best current sketch + clearly-marked deferred zones"; each L1 doc maintains a §C "Open at L1, deferred to L4" section. The 7-doc topic split (tropism / trajectory / schema / governance / skin / continuity / hard-rules) assigns each foundational mechanism cluster to one owner doc.
