# L2 — Outline / Charter

> **Status**: OUTLINE DRAFT 3 (2026-05-13). Post L2 pass-2 verification: 5/6 lenses CONVERGED, 0 CRITICAL, 7 findings (3 SHOULD, 4 NICE). All 3 SHOULDs were L2_OUTLINE stale-text drift — this DRAFT 3 resyncs.
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

Shapes (a) per-subsystem-family + (b) per-L1-deep-dive were rejected at the shape-decision stage; the original rationale lives in the L2_OUTLINE bc88445 commit (charter version pre-decision). Brief recap retained in §1 below as one-line entries.

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

## §1. Shape decision archaeology (one-line per rejected shape)

Decision is owner-finalized as shape (c). Brief archaeology of the rejected alternatives:

- **Shape (a) Per-subsystem-family doctrine** (v0.8-style): REJECTED. v0.9's L1 is topic-organized, not subsystem-organized; retrofitting a subsystem partition over L1 would add complexity rather than reduce it. Plus C7.3 v0.8-origin-contamination risk.
- **Shape (b) Per-L1-mechanism deep-dive** (1:1 L1↔L2): REJECTED. L1 docs are already mechanism-deep (~150-260 lines each with §B 10 hooks + §C deferred); per-L1 deep-dive would duplicate or speculate beyond.
- **Shape (c) Cross-cut doctrine themes**: CHOSEN. Genuinely higher-layer; no subsystem partition needed; each theme cross-cuts multiple L1 mechanisms; aligns with v0.9's L1 cross-doc protocol shape (anchor surface ⇆ canonical bytes ⇆ governance ⇆ skin ⇆ schema). DRAFT 2 expanded to 6 themes (added L2_TRAJECTORY per L2 pass-1 rhizomorph-1).

Full rationale + pros/cons for each shape is in the L2_OUTLINE DRAFT 1 charter (commit bc88445); not duplicated here.

---

## §2. Status — sealing-ready

All 6 cross-cut theme docs exist as DRAFT 1+ (TRUST_MODEL, LIFECYCLE, EVOLUTION, FEDERATION, OBSERVABILITY at DRAFT 1; TRAJECTORY at DRAFT 1 from DRAFT 2 round). Pass-1 cycle found 22 findings (5 SHOULD + 17 NICE, 0 CRITICAL); all 5 SHOULDs + key NICEs applied. Pass-2 cycle verified 7 findings (3 SHOULD + 4 NICE, 0 CRITICAL) — all SHOULDs in L2_OUTLINE itself (stale text drift), which this DRAFT 3 resyncs.

L2 layer is **sealing-ready**. Next steps:

1. (DONE) Resync L2_OUTLINE to 6-doc state (this DRAFT 3).
2. L3 implementation map drafting (code organization that operationalizes L1 mechanisms with L2 doctrine guidance).
3. L4 substrate (actual v0.9 code).

L3 layer expected to be smaller than L2 (2-3 docs likely): file-layout/module-boundaries map; build-order; first-implementation-target priorities.

---

## §3. What L2 is NOT (scope discipline)

- **NOT a duplication of L1**: each L2 doc explicitly cross-cuts ≥2 L1 docs and carries content that does not fit in any single L1 doc.
- **NOT a code-organization map**: that's L3.
- **NOT a re-litigation of L0 commitments**: L2 takes L0 as given.
- **NOT a per-subsystem-family doctrine** (under shape (c); was the alternative under shape (a)).

---

## §4. Pending L0 / L1 revisions made

These were deferred until L2 shape was confirmed; now applied:

- L0 §10.1 reading sequence updated to 6 L2 docs (commits bf688d8, e5a7d83).
- L1_OUTLINE forward-reference to L2_OUTLINE — not required since L0 §10.1 carries the reading sequence; L1_OUTLINE coverage matrix is self-contained for the L0-L1 hooks.

No further L0/L1 revisions pending from L2 shape decision.
