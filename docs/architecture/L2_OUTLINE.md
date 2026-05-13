# L2 — Outline / Charter

> **Status**: OUTLINE DRAFT 2 (2026-05-13). Owner-decided shape (c): cross-cut doctrine themes. 5 L2 docs drafted.
> **Layer**: L2.
> **Authority**: navigation only. The 5 L2 docs below are authoritative.

---

## §0. L2 shape — owner-chosen: cross-cut themes

Owner chose **shape (c): 5 cross-cut doctrine themes**. Drafted in dependency order:

| # | File | Theme |
|---|---|---|
| 1 | `L2_TRUST_MODEL.md` | Trust derivation: triad + genesis + per-interaction + maintenance + recovery + limits |
| 2 | `L2_LIFECYCLE.md` | Operating regimes: genesis → birth → steady → dormancy → quarantine → legacy → mortality |
| 3 | `L2_EVOLUTION.md` | Self-evolution discipline: doctrine + schema + lexicon + threshold + versioning |
| 4 | `L2_FEDERATION.md` | Inter-substrate: P8 modes + spore-schema + peer-trust + network shape |
| 5 | `L2_OBSERVABILITY.md` | Self-model: Living Bets + immune catalog + drills + falsifiability |

Shapes (a) per-subsystem-family + (b) per-L1-deep-dive were rejected — see §1 below for rationale (retained for archaeology).

---

## §0.1 What this set covers vs L1 mechanism docs

| Question | L1 doc | L2 cross-cut |
|---|---|---|
| HOW does the substrate accept deltas? | L1_SKIN §2 | (trust model citation in L2_TRUST_MODEL §3.2) |
| WHEN does the substrate enter dormancy? | L1_CONTINUITY §2.2 | L2_LIFECYCLE §5.1 (unified picture of all transitions) |
| WHAT is the classifier function signature? | L1_GOVERNANCE §1.1 | L2_TRUST_MODEL §3.4 (CI mutation flow + L2_EVOLUTION §3.2 schema-evolution path) |
| HOW does federation egress check freshness? | L1_SKIN §3.1 | L2_FEDERATION §7 (full egress flow with rate-limiting + low-entropy + DAG edge recording) |
| WHEN does the bet-falsifiability trigger fire? | L0 §7 | L2_OBSERVABILITY §3 (falsifiability summary across all signals) |

L2 = high-altitude perspective on cross-doc behavior. L1 = mechanism specifications. L2 cites L1; L1 stands without L2.

---

## §1. Three candidate L2 shapes

### Shape (a): Per-subsystem-family doctrine (v0.8 inheritance)

L2 = one doc per mycology subsystem family. Requires first picking a subsystem partition (e.g., {mycelium, hyphae, spore, stipe, rhizomorph, pileus, chlamydospore}) — this becomes the v0.9 subsystem family.

**Pros**:
- Mirrors v0.8 L2 structure (owner familiar with the shape)
- Aligns with L0 §10.1's literal reading

**Cons**:
- v0.9's L1 is topic-organized, not subsystem-organized. Retrofitting a subsystem partition over L1 would mean each subsystem cross-cuts multiple L1 docs — the partition adds complexity rather than reducing it
- C7.3 max v0.8-origin discrimination: subsystem-partition was a v0.8 organizational choice. v0.9 hasn't independently re-derived the need for one
- Each subsystem doc would need to enumerate which L1 mechanisms it touches, AND which other subsystem docs it cross-cuts — high coupling cost

### Shape (b): Per-L1-mechanism deep-dive

L2 = one doc per L1 doc (L2_TROPISM, L2_GOVERNANCE, L2_SKIN, L2_SCHEMA, L2_CONTINUITY, L2_TRAJECTORY, L2_HARD_RULES). Each L2 doc is the deep-doctrine companion to its L1 doc.

**Pros**:
- 1:1 mapping with L1; trivially navigable
- No new partition decision needed

**Cons**:
- L1 docs are ALREADY mechanism-deep (~150-260 lines each with §1 form + §2 alternatives + §3 details + §A continuity + §B 10 hooks + §C deferred). Adding L2 docs that deep-dive would either duplicate L1 or speculate beyond L1
- L2 becomes architectural-astronaut territory: theory layer between L1 (already specific) and L3 (code map). Astronaut pass-2 would CRITICAL this

### Shape (c): Cross-cut doctrine themes ⭐ RECOMMENDED

L2 = a small set of doctrine docs each cross-cutting multiple L1 mechanisms. Each L2 doc carries ONE theme that doesn't fit cleanly in any single L1 doc.

**Pros**:
- Genuinely "higher layer" — L2 abstracts patterns that emerge from L1 mechanism interaction (not from individual L1 docs)
- No subsystem partition needed
- Aligns with how v0.9's L1 ended up structurally organized (cross-doc protocol: anchor surface ⇆ canonical bytes ⇆ governance ⇆ skin ⇆ schema)
- Independently traceable to L0: each L2 theme projects to multiple Ps + Is

**Cons**:
- Risk of theory-without-implementation-grounding (astronaut concern); mitigated by requiring each L2 doc to cite specific L1 sections it cross-cuts
- The theme set itself is a design decision; pass-N critics might find missing themes

**Candidate L2 theme set (5 docs)**:

1. **`L2_TRUST_MODEL.md`** — End-to-end trust derivation from L0 §9 anchor surface through L1_GOVERNANCE attestation protocol + L1_SKIN handshake + L1_SCHEMA canonical bytes. Answers: "how does a v0.9 substrate establish, maintain, and recover trust at every interaction point?" Cross-cuts L0 §9 + L1_GOVERNANCE §2-3 + L1_SKIN §4 + L1_SCHEMA §2.
2. **`L2_LIFECYCLE.md`** — Substrate lifecycle as cross-cut: genesis (L1_GOVERNANCE §4.1) → birth period (L1_TROPISM §4 + L1_GOVERNANCE §1.3) → steady state → reproduction (L1_GOVERNANCE §4.3) → dormancy (L1_CONTINUITY §2) → quarantine sub-states (L1_CONTINUITY §5) → mortality (L1_GOVERNANCE §4.4) → anchor-surface final seal. Answers: "what are the operating regimes and how do they transition?"
3. **`L2_EVOLUTION.md`** — Substrate evolution discipline: P3 schema evolution (L1_GOVERNANCE §6) + P3.b joint-context (L1_TRAJECTORY §5 epochs) + lexicon evolution (L0 P3) + template versioning (L1_TROPISM §B1) + L0/L1 revision back-pressure (L0 §9.4). Answers: "how does v0.9 evolve its own shape over decades without violating invariants?"
4. **`L2_FEDERATION.md`** — Inter-substrate doctrine: P8 reproduction modes (federation/cloning/cross-pollination) + I7 closure verification + L1_GOVERNANCE §5 federation discovery + L1_SKIN §3.1 egress + cross-substrate trust freshness. Answers: "what is the population-level shape of Myco and how do substrates federate without compromising P1.c?"
5. **`L2_OBSERVABILITY.md`** — How the substrate observes itself: L0 §7 Living Bets observatory + immune-grade sporocarps (per L1_HARD_RULES §1) + I3 self-validation + I5 reachability + drill failure-rate baseline + cycle backlog detection. Answers: "what is the substrate's self-model and falsifiability surface?"

This set is 5 docs (vs 7 L1 docs vs hypothetical 7 subsystem docs). Each is targeted; each cross-cuts multiple L1 mechanisms.

---

## §2. Status — 5 L2 docs drafted

All 5 cross-cut theme docs are DRAFT 1 (2026-05-13). After this L2 set lands, next steps:

1. Pass-1 critic cycle on L2 layer (same 6-lens 100%-confidence loop methodology used for L0/L1; expected to find polish, not CRITICAL, given L2 cites L1 and adds doctrine layer only)
2. L3 implementation map (code organization that operationalizes L1 mechanisms with L2 doctrine guidance)
3. L4 substrate (actual v0.9 code)

## §3. What L2 is NOT (per scope discipline)

- **NOT a duplication of L1**: each L2 doc explicitly cross-cuts ≥2 L1 docs and carries content that does not fit in any single L1 doc.
- **NOT a code-organization map**: that's L3.
- **NOT a re-litigation of L0 commitments**: L2 takes L0 as given.
- **NOT a per-subsystem-family doctrine** (under shape (c) — could be under (a)).

---

## §4. Open at L2 — pending owner decision

**The L2 shape choice itself**: (a) / (b) / (c) / D = owner-invented alternative. After owner decides, L2 substantive drafting begins.

If owner chooses (c), the 5-doc set in §1.c is the proposed starting point — owner may add/cut/merge themes before substantive drafting.

If owner chooses (a), the substrate subsystem partition must be decided first (which fungal-biology subsystem family?). L1_OUTLINE §1 candidate subsystems list applies.

If owner chooses (b), each L2_X.md is a deep-dive of L1_X.md; risk of overlap acknowledged.

---

## §5. Pending L0 / L1 revisions that L2 shape impacts

- L0 §10.1 reading sequence text may need refinement after L2 shape is chosen (currently says "per-subsystem-family"; if (c), it becomes "cross-cut themes").
- L1_OUTLINE §1 may add a forward-reference to L2_OUTLINE once shape is chosen.

These are deferred until L2 shape is confirmed.
