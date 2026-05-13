# L1 — Outline / Charter

> **Status**: OUTLINE (revised post DRAFT 6 of L0 + 4 new L1 doc spawns, 2026-05-13).
> **Layer**: L1. Governed by L0.
> **Authority**: this outline is navigation only — no binding authority. The L1 documents listed below ARE the authoritative L1 layer.
> **Naming**: *"v0.9"* = Myco substrate version. *"DRAFT N"* (no `v` prefix) = document revision counter.

---

## §0. What L1 is

L1 is the **mechanism enforcement layer** for L0's principles + invariants. L0 commits to identity, negative space, and constraints; L1 commits to the positive forms satisfying those constraints. A statement belongs in L1 if it answers "*how does the substrate actually do X?*".

The 100%-confidence-loop applied between DRAFT 5 and DRAFT 6 of L0 surfaced that 5 of 8 invariants pointed to unwritten L1 docs — making the doctrine layer claim completeness it could not demonstrate. DRAFT 6 spawning includes **4 new L1 documents** (SCHEMA / GOVERNANCE / SKIN / CONTINUITY) addressing the foundational mechanisms.

### What L1 does NOT inherit from v0.8

v0.8 L1 was 7 hard rules (R1-R7) + canon schema + exit codes. Per L0 C7.3, v0.9 L1 is rebuilt from L0's eight invariants and nine principles:

- **No boot/session-end ritual** (§6 — continuous online substrate dissolves R1/R2).
- **Sense-before-assert** subsumed into gradient-read primitive.
- **Capture-now** survives as the `hunger` appetite axis.
- **Cross-reference** survives as I5 + orphans as immune signals.
- **Write-surface** survives as I8 + appetite-locality from I6.
- **Top-down** survives as the L0-L1-L2-L3-L4 layering itself.

L1 v0.9 is **not** "R1-R7 rephrased". L1 is whatever specifications emerge from operationalizing the 8 invariants + the chosen positive forms (tropism + trajectory) + remaining mechanism choices.

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
| `L1_HARD_RULES.md` | G-rules catalog (v0.9 replacement for v0.8 R1-R7) | NOT YET WRITTEN |

**6 of 7 L1 docs exist as DRAFTs.** Only L1_HARD_RULES remains unwritten; it operationalizes the others (cites specific schema sections, classifier rules, skin specs) so it sensibly drafts last.

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
| §11 birth-period N | `L1_TROPISM.md` (steady-state activation) + `L1_GOVERNANCE.md` (owner vigilance) ✓ |

**Every L0 design hook has an L1 owner. None pending.**

---

## §3. Outstanding L1 work

**L1_HARD_RULES.md** is the remaining unwritten L1 doc. Drafting it requires the other 6 L1 docs (G-rules cite specific schema sections, classifier rules, skin specs). Drafting order: write last.

Per pass-1 architectural-astronaut: L1 docs should explicitly demote over-commitment to L4 deferred zones rather than over-specifying. L1_TROPISM and L1_TRAJECTORY have been revised in DRAFT 2 to demote ~40% of their prior specific mechanism commitments.

---

## §4. Cross-document discipline

1. **Each L1 doc carries a small §1 "what this doc commits to"** — already established in all current L1 docs.
2. **Cross-doc consistency** — when one L1 doc says "X is governance-classified", L1_GOVERNANCE classifier dimension table (§1.2) is the source of truth. Other L1 docs cite, not duplicate.
3. **L1 mutation discipline** — a change to an L1 doc is contract-identity-level (per L0 I2). Same proposal-and-approval process as L0 modifications, with one specific difference: L1 revisions may be more frequent than L0 revisions (L1 evolves as L2/L3 implementation surfaces refinement needs); L0 §9.4 burst-detection threshold for L1 is L1-tunable but recommended higher tolerance than L0 (since L1 is closer to implementation).
4. **L0 revision back-pressure** — per L0 §10.2: when L1 work reveals an L0 constraint is unworkable, the L1 doc records the finding and L0 revision is proposed through L0 §10.2 protocol. The L1 doc is NOT silently weakened to "fit" a wrong L0.

---

## §5. Confidence discipline (per pass-1 architectural-astronaut)

The 100%-confidence-loop applies to **L0 identity claims**. For L1 mechanism specifications, the appropriate bar is **"best current sketch + clearly-marked deferred zones"** — over-commitment at L1 in absence of implementation creates speculative complexity that L4 will reject.

Each L1 doc maintains a §C "Open at L1, deferred to L4" (or equivalent) section explicitly listing decisions punted to implementation observation. L1_TROPISM DRAFT 2 expanded this deferred-section from DRAFT 1's 5 items to 11.

L1 is "load-bearing where load is unavoidable, deferred everywhere else". Substantial deferral is a feature.

---

## §6. Document-set partition rationale

The 7-doc topic split (tropism / trajectory / schema / governance / skin / continuity / hard-rules) was chosen over a monolithic L1.md or per-invariant / per-principle partitions because L1 is large enough to warrant partitioning but invariants couple too tightly to align with a 1-doc-per-invariant cut. The chosen partition assigns each foundational mechanism cluster to one owner doc, with cross-references where coupling exists (catalogued in §2 above).
