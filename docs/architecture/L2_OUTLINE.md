# L2 — Outline / Charter

> **Status**: OUTLINE (post L0 DRAFT 9 SEALED, 2026-05-17, commit `e796451`).
> **Layer**: L2.
> **Authority**: navigation only. The 6 L2 docs below are authoritative.

---

## §0. L2 shape — owner-chosen: cross-cut themes (6 docs)

Owner chose **shape (c): cross-cut doctrine themes**. DRAFT 2 added `L2_TRAJECTORY.md` as the 6th theme. Set, in dependency order:

| # | File | Theme |
|---|---|---|
| 1 | `L2_TRUST_MODEL.md` | Trust derivation: triad + genesis + per-interaction + maintenance + recovery + limits |
| 2 | `L2_LIFECYCLE.md` | Operating regimes: genesis → birth → steady → dormancy → quarantine → legacy → mortality |
| 3 | `L2_EVOLUTION.md` | Self-evolution discipline: doctrine + schema + lexicon + threshold + versioning |
| 4 | `L2_FEDERATION.md` | Inter-substrate: P8 modes + spore-schema + peer-trust + network shape |
| 5 | `L2_OBSERVABILITY.md` | Self-model: Living Bets + immune catalog + drills + falsifiability |
| 6 | `L2_TRAJECTORY.md` | Intent doctrine: fossil-record vs teleology + cold-start + cluster_C + thread_id + injection defense |

Shapes (a) per-subsystem-family + (b) per-L1-deep-dive were rejected at the shape-decision stage; the original rationale lives in the L2_OUTLINE bc88445 commit.

---

## §0.1 What this set covers vs L1 mechanism docs

| Question | L1 doc | L2 cross-cut |
|---|---|---|
| HOW does the substrate accept deltas? | L1_SKIN §2 | L2_TRUST_MODEL §3.2 (trust-model citation) |
| WHEN does the substrate enter dormancy? | L1_CONTINUITY §2.2 | L2_LIFECYCLE §5.1 (unified picture of all transitions) |
| WHAT is the classifier function signature? | L1_GOVERNANCE §1.1 | L2_TRUST_MODEL §3.4 (CI mutation flow) + L2_EVOLUTION §3.2 (schema-evolution path) |
| HOW does federation egress check freshness? | L1_SKIN §3.1 | L2_FEDERATION §7 (full egress flow with rate-limiting + low-entropy + DAG edge recording) |
| WHEN does the bet-falsifiability trigger fire? | L0 §7 | L2_OBSERVABILITY §3 (falsifiability summary across all signals) |
| HOW is intent derived without storing it? | L0 §5.3 + L1_TRAJECTORY | L2_TRAJECTORY §2 (full cross-cut: fossil-record vs teleology + cluster_C coupling + injection defense) |

L2 = high-altitude perspective on cross-doc behavior. L1 = mechanism specifications. L2 cites L1; L1 stands without L2.

---

## §3. What L2 is NOT

L2 is cross-cut doctrine, not navigation; per-mechanism specs live in L1.
