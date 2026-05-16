# L1 — Outline / Charter

> **Status**: OUTLINE (post L0 sealing 2026-05-17, commit `e796451`). **Layer**: L1, governed by L0. **Authority**: navigation only — the L1 documents listed below ARE the authoritative L1 layer.

---

## §0. What L1 is

L1 is the **mechanism enforcement layer** for L0's principles + invariants: L0 commits to identity/negative-space/constraints; L1 commits to positive forms satisfying them. A statement belongs in L1 if it answers "how does the substrate do X?".

---

## §1. L1 document set

| File | Topic |
|---|---|
| `L1_OUTLINE.md` (this) | Charter + index |
| `L1_TROPISM.md` | Positive dispatch form |
| `L1_TRAJECTORY.md` | Positive intent-derivation |
| `L1_SCHEMA.md` | SSoT, Merkle DAG, recoverability, spore-schema, validation tiers |
| `L1_GOVERNANCE.md` | I2 classifier, lifecycle, attestation, succession, federation discovery |
| `L1_SKIN.md` | I8 envelope, handshake, single-operator, network-egress, breach detection |
| `L1_CONTINUITY.md` | Metabolic cycle, dormancy, recovery, delta atomicity |
| `L1_HARD_RULES.md` | Cross-cuts index of CRITICAL breaches + CI fixed-points + anchor-resident state |

L1 layer structurally complete. L1_HARD_RULES is cross-cuts index (not v0.8 R1-R7 inheritance per C7.3); independently traces every row to ≥1 P + ≥1 I.

---

## §2. Coverage of L0 design hooks across L1 docs

| L0 reference | L1 owner |
|---|---|
| §5.2/§5.3 dispatch + intent | `L1_TROPISM` / `L1_TRAJECTORY` |
| §6 metabolic cycle / dormancy / delta atomicity / cold-resume | `L1_CONTINUITY` |
| P3 rollback / P5.1 lexicon / P7 mortality / P8 federation discovery | `L1_GOVERNANCE` |
| P3.b epoch markers | `L1_TRAJECTORY` + `L1_SCHEMA` |
| P8 spore-schema / I3 SSoT / I4 DAG-Merkle-retention / I5 storage tiers | `L1_SCHEMA` |
| I1 operator-token / I8 envelope+handshake+continuity-challenge | `L1_SKIN` |
| I1 legacy sub-state | `L1_GOVERNANCE` + `L1_CONTINUITY` |
| I2 classifier function | `L1_GOVERNANCE` |
| I4 sporocarp causal-proof / I6 (appetite + locality + embedding + egress) | `L1_TROPISM` (egress → `L1_SKIN`) |
| I7 closure verification + peer-trust | `L1_SCHEMA` + `L1_GOVERNANCE` |
| §7 Living Bets + §9 anchor + §11 birth-period N | `L1_SKIN` + `L1_GOVERNANCE` (+ `L1_TROPISM` for birth-N) |
| P1.a self-hosting bootstrap | `L1_TROPISM` §B10 |
| §10.2 L0-revision back-pressure / §11 privacy/access | this §4 (back-pressure); implicit `L1_SKIN` §1 (privacy) |

Every L0 design hook has an L1 owner.

---

## §4. Cross-document discipline

1. Each L1 doc carries §1 "what this doc commits to".
2. **Cross-doc consistency**: L1_GOVERNANCE classifier dimension table (§1.2) is SSoT for classification; other docs cite, not duplicate.
3. **L1 mutation discipline**: L1 changes CI per L0 I2; same proposal-and-approval as L0; revisions may be more frequent (closer to implementation); L0 §9.4 burst threshold tunable, higher tolerance recommended.
4. **L0 back-pressure**: when L1 work reveals an L0 constraint unworkable, L1 doc records finding + proposes L0 revision via §10.2; L1 NOT silently weakened.

---

## §5. Confidence + partition discipline

L1 specs use "best current sketch + marked deferred zones"; each doc maintains §C "Open at L1, deferred to L4"; 7-doc split assigns each foundational mechanism cluster to one owner doc.
