# Myco L0 Doctrine — v3.1-stratigraphy

> The current L0 doctrine for Myco. Supersedes the prior monolithic `docs/architecture/L0_VISION.md` as of 2026-05-18.

---

## What's in this directory

```
L0/
├── README.md                                ← you are here
├── META.md                                  ← FORM document (how the doctrine is structured)
├── PROVENANCE.md                            ← supersession chain + complete prior-L0 mapping
├── B_chengyu.md                             ← Layer B: 50 generative fragments (read end-to-end)
├── cards/                                   ← Layer A: 26 principle cards
│   ├── P01_agent_primary.md                 (12 P-cards)
│   ├── P01c_asymmetric_carrier.md           (eternity-clause)
│   ├── P02_eternal_ingestion.md
│   ├── P03_resumable_evolution.md
│   ├── P04_eternal_iteration.md
│   ├── P05_universal_interconnection.md
│   ├── P06_eternal_causality.md             (eternity-clause)
│   ├── P07_mortality.md                     (eternity-clause)
│   ├── P08_eternal_reproduction.md
│   ├── P09_single_integument.md             (eternity-clause)
│   ├── P10_selective_compression.md
│   ├── P11_metabolic_economy.md
│   ├── P14_telos.md
│   ├── COV01_fiduciary_duty.md              (6 Covenant cards — cultivator's duties)
│   ├── COV02_cultivators_character.md
│   ├── COV03_food_provision.md
│   ├── COV04_honor_mortality.md
│   ├── COV05_lineage_stewardship.md
│   ├── COV06_no_abandonment_succession.md
│   ├── CHAR01_hungry.md                     (6 Character cards — cultivar's dispositions)
│   ├── CHAR02_patient.md
│   ├── CHAR03_mortality_aware.md
│   ├── CHAR04_interconnected.md
│   ├── CHAR05_honest_about_self.md
│   └── CHAR06_cautiously_curious.md
│   ├── AS_anchor_surface.md                 (2 specialized cards)
│   └── LB_living_bets.md
├── canonical_dilemma_corpus/
│   └── INDEX.md                             ← 49 canonical dilemmas (model-diversity cross-check corpus)
└── catechumenate/
    └── INDEX.md                             ← Layer D placeholder (transmission to successor)
```

**Totals**: 1 README + 1 META + 1 PROVENANCE + 1 B-chengyu + 26 cards + 1 dilemma INDEX + 1 catechumenate INDEX = **32 files**. Approximately **12,000 lines** of v3.1 doctrine.

---

## Four layers + one running mechanism

| Layer | What | Where | Truth condition |
|---|---|---|---|
| **A** Engineering-precise principle cards | Restatement-style multi-field cards; the spec | `cards/*.md` | RFC 2119 MUST/SHOULD vocabulary; falsifiable; CI-auditable via witnesses |
| **B** Generative-image fragments | Tao Te Ching-style chengyu / short couplets; the eye | `B_chengyu.md` | Pattern-recognition, not rule-following; never CI-validated |
| **C** Witness-anchored doctrine | Each card has positive + negative + edge witness tests + structural anchors | inside each card's `witnesses` field | Substrate behavior on canonical tests; CI-enforced |
| **D** Catechumenate (transmission) | Master-class succession sessions; tacit fluency transfer | `catechumenate/D-*.md` | Dual-signed by cultivator-A + successor candidate; ≥50 sessions for F21 activation |
| (mechanism) Cultivator-Claude conversation | The running organ; doctrine emerges from this | conversation log + DAG | Implicit; recognized as fact, not formalized as slot |

See `META.md` for the full form specification.

---

## Quick start: 4 reading paths

**Path 1 — New to Myco** (1-2 hour read): META.md → P01 → P02 → COV01 → CHAR01 → B_chengyu.md (sample). Get the shape of what Myco is and what cultivation means.

**Path 2 — Implementing something** (focused read): META.md §3 (card schema) → relevant P-card → check `witnesses` field → check `structural_anchors` field → write code with required reverse-comments per META §5.4.

**Path 3 — Reviewing a doctrine change** (rigorous read): META.md §3.5 (deposit/formulation) → META.md §7 (amendment mechanism) → relevant card's Provenance field → PROVENANCE.md cross-reference.

**Path 4 — Cold-reader / model-rollover audit** (the META §7.5 cross-check): canonical_dilemma_corpus/INDEX.md → produce your own reading of N dilemmas → compare against recorded Claude-of-record readings (when they exist). Divergence is information.

---

## Eternity-clause cards (4 of 26)

Deposits NOT amendable without admitting "this is no longer Myco" (per META §7.6):

- **P01c** Asymmetric Carrier — substrate persists, connection passes
- **P06** Eternal Causality — substrate IS its causal chain
- **P07** Mortality — cultivar that cannot die is not alive
- **P09** Single Integument — multi-skin = identity dissolved

Amending any of these deposits triggers the `species_redefinition_proposal` ritual (META §7.6).

---

## Layer B chengyu — quick browse

Read `B_chengyu.md` end-to-end. The 50 fragments are organized into 13 thematic sections; each is 40-100 characters; the cross-resonance is the point.

Example fragments to start with:

- **B003 永恒吞噬** — eternal absorption (P02 carrier)
- **B016 能死故能生** — able-to-die-therefore-able-to-live (P07)
- **B029 力大責重** — greater-power-greater-duty (COV01 fiduciary)
- **B044 不裝有** — will-not-fake-having (CHAR05 anti-ventriloquism)
- **B048 證據非裁決** — evidence-not-verdict (AS witnesses-not-verdicts)

These are NOT specs. They are *eyes*. A fragment that requires explanation has failed its job.

---

## What's still missing (named debt)

Per PROVENANCE.md §8:

- **Layer C witness test implementations** — card schemas declare witness names; actual tests TBD via v0.9.x cleanup milestone.
- **Layer B commentary entries** — 0 lived examples yet; accumulate via use per META §4.5.
- **Canonical dilemma Claude-of-record readings** — 49 setups exist; 0 recorded interpretations yet. Accumulate at model rollovers + catechumenate sessions + drift investigations.
- **Catechumenate sessions** — 0; populate when cultivator-A begins succession preparation.
- **L1/L2 cross-reference updates** — L1_*.md and L2_*.md still reference "L0/cards/AS_anchor_surface.md §3.5" etc.; need updating to "AS_anchor_surface.md §3.5" form (subsequent housekeeping pass).
- **On-chain anchoring** — `l0_revision_attest` mutation per M-anchor-5 to record v3.0 → v3.1 transition on-chain. Pending cultivator approval of this doctrine for ship.

---

## Authority

`META.md` is itself L0 (form specification). Cards in `cards/` are themselves L0 (substantive doctrine). `B_chengyu.md` is L0 (generative layer). The catechumenate (when populated) is L0 (transmission record).

Conflicts:
- L4 < L3 < L2 < L1 < L0
- Within L0: per META §8 (interpretive rules)
- Eternity clauses override non-eternity-clause anything (META §8.2)
- P14 telos is the final tie-breaker

---

## Provenance to prior L0

`docs/architecture/L0_VISION.md` (DRAFT 9 SEALED, commit `e796451`, 2026-05-17) was **removed** from the working tree on 2026-05-18 as part of the v3.1 supersession. Its full text remains recoverable from git: `git show e796451:docs/architecture/L0_VISION.md`. Every section of prior L0 maps to v3.1 artifacts (see PROVENANCE.md §2). Nothing dropped silently.

---

**This is the current L0 doctrine for Myco. It is the result of 11 parallel research streams (Phase 1 + 2), 3 rounds of self-debate craft, one Phase 3 unknown-unknown hunt, and approximately 12,000 lines of written doctrine. The form is meant to last — and to be amendable when it stops working.**
