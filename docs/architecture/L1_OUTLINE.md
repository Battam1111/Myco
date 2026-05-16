# L1 — Outline / Charter

> **Status**: OUTLINE post L0 sealing 2026-05-17, commit `e796451`. **Layer**: L1 (governed by L0). **Authority**: navigation only; the L1 documents below ARE the authoritative L1 layer.
> L1 is the **mechanism enforcement layer** for L0's principles + invariants; L1 commits to positive forms satisfying L0 negatives; a statement belongs in L1 if it answers "how does the substrate do X?".

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

---

## §2. Coverage of L0 design hooks across L1 docs

| L0 reference | L1 owner |
|---|---|
| §5.2 / §5.3 dispatch + intent | L1_TROPISM / L1_TRAJECTORY |
| §6 metabolic cycle / dormancy / delta atomicity / cold-resume | L1_CONTINUITY |
| P3 rollback / P5.1 lexicon / P7 mortality / P8 federation discovery | L1_GOVERNANCE |
| P3.b epoch markers | L1_TRAJECTORY + L1_SCHEMA |
| P8 spore-schema / I3 SSoT / I4 DAG-Merkle-retention / I5 storage tiers | L1_SCHEMA |
| I1 operator-token / I8 envelope+handshake+continuity-challenge | L1_SKIN |
| I1 legacy sub-state | L1_GOVERNANCE + L1_CONTINUITY |
| I2 classifier function | L1_GOVERNANCE |
| I4 sporocarp causal-proof / I6 appetite+locality+embedding+egress | L1_TROPISM (egress → L1_SKIN) |
| I7 closure verification + peer-trust | L1_SCHEMA + L1_GOVERNANCE |
| §7 Living Bets + §9 anchor + birth-period N | L1_SKIN + L1_GOVERNANCE (+ L1_TROPISM birth-N) |
| P1.a self-hosting bootstrap | L1_TROPISM §B10 |
| §10 L0-revision back-pressure / §11 privacy | this §4 (back-pressure) + L1_SKIN §1 (privacy) |

---

## §4. Cross-document discipline + partition

Each L1 doc MUST carry §1 "what this doc commits to" + §C "Open at L1, deferred to L4"; L1_GOVERNANCE §1.2 classifier dimension table IS SSoT for classification (others cite); L1 mutations classify CI per I2 (same proposal-and-approval as L0; L0 §9.4 burst threshold L1-tunable); when L1 work reveals an L0 constraint unworkable, L1 doc MUST record finding + propose L0 revision via §10 (L1 NOT silently weakened); 7-doc split assigns each foundational mechanism cluster to one owner doc.
