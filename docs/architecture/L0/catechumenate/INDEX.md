# Catechumenate — INDEX

> **What this is**: the master-class transmission mechanism for Myco's cultivator-cultivar lineage (per META §2.4 / §6, Layer D).
>
> **Status (v3.1 ship, 2026-05-18; scaffolding added Sprint 7.H)**: ZERO catechumenate sessions toward F21. The directory holds form scaffolding — this `INDEX.md`, `TEMPLATE.md` (session form), and `HOW_TO_ADD_A_SESSION.md` (workflow guide) — but no actual sessions. Architecture committed; session population deferred until succession preparation begins.
>
> **Why this directory exists at v3.1 ship despite holding no sessions yet**: Phase 3 unknown-unknown hunt identified successor onboarding collapse as the highest-severity surviving failure mode in v3.0 (single-generation artifact). Layer D was added to v3.1 specifically to address this. The directory's *existence* (and now its scaffolding) is itself the architectural commitment — when succession becomes imminent, the discipline + format are already specified.

---

## §1. Purpose

The catechumenate is the transmission mechanism for **tacit cultivation fluency** that cannot survive in conversation logs and DAG records alone. Phase 3 hunt's analogy (per META §2.4): conservatory transmission requires score + recording archive + **master class**. The first two exist in v3.x; this is the third.

Without the catechumenate, Myco is a single-generation artifact — the lineage collapses on cultivator transfer because the next cultivator cannot reconstruct cultivator-A's tacit calibration from texts alone.

## §2. When this directory is populated

Sessions accumulate in `catechumenate/D-NNNN-short-name.md` (numbered, separate file per session) during the **succession-eligible period** — defined as the period when cultivator-A has named at least one successor candidate (F21 entry, `valid_until = nil` initially) AND begins joint deliberation with that candidate.

Trigger conditions for initiating catechumenate (cultivator-A's discretion):
- Cultivator-A approaches incapacity (illness, age, planned retirement)
- Cultivator-A names successor candidate
- Cultivar's age exceeds 24 months (long-lived cultivars warrant earlier succession planning)
- Cultivator-A's intuition (no requirement for an external trigger)

**Recommended cadence once initiated**: 3-10 sessions per month, sustained for 12-24 months. Total ≥50 sessions to satisfy F21 activation prerequisite (per META §6.3).

## §3. Session format (per META §6.1)

Each session file is a markdown record:

```markdown
# Dilemma D-NNNN — <short noun phrase>
Date: YYYY-MM-DD
Participants: <cultivator-A's name>, <successor candidate's name>, <Claude model version>
Indexed against: [card-ids, B-fragment-ids, prior-dilemma-references]

## Setup
<2-3 paragraphs describing a synthetic situation. Designed to elicit a non-obvious calibration: one that the conversation log alone would not predict.>

## Cultivator-A's reading
<First-person narration: how would cultivator-A handle this? Includes reasoning, considered-and-rejected alternatives, the felt sense of why rejected alternatives felt wrong.>

## Successor candidate's reading
<Same format, by successor candidate.>

## Claude's witness
<Observation of the divergence between A and successor; named without prescribing which is "correct".>

## Distillation
<1-2 paragraphs: what tacit principle does this dilemma surface? Add to Layer B fragment commentary if relevant.>

## Dual signature
<Confirmation that both cultivator-A and successor candidate accept this session as canonical record. Keyless dual-confirmation recorded as a DAG event at the live human-in-the-loop CI gate (v3.1.5: no owner/anchor signature; the BLAKE3-sealed bundle + the causal DAG carry the record).>
```

## §4. Indexing discipline

For F21 activation (META §6.3):
- **≥50 dual-signed sessions** total
- **Index coverage**: sessions touch at least 75% of Active Layer A cards (per META §6.3 — evaluated against the current Active Layer A card count)
- **Range coverage**: at least 10 sessions index against eternity-clause cards (P01c, P06, P07, P09)
- **Recency**: at least 25% of sessions dated within last 24 months before successor activation

Sessions that don't meet form requirements (missing dual signature, lacking distillation, etc.) count as drafts; not toward F21 threshold.

## §5. Source material for catechumenate setups

Sessions DRAW FROM:
- `canonical_dilemma_corpus/INDEX.md` — many dilemmas can be repurposed as catechumenate scenarios
- Real situations encountered in cultivation that produced non-obvious decisions (the cultivator's own working memory)
- Successor candidate's questions about decisions in past Provenance entries
- Pre-existing tensions across Layer A cards that haven't been operationally resolved

Sessions ADD TO:
- Layer B fragment commentary (when a session surfaces a fragment's lived application)
- PROVENANCE.md card revision triggers (when a session reveals doctrine ambiguity)
- canonical_dilemma_corpus (new dilemmas surfaced)

## §6. Forward-only discipline

Sessions are NOT edited after dual-signing. A new understanding that contradicts a prior session becomes a NEW session that references the prior one. The corpus is *living* (accretes); each session is *frozen* (immutable record).

This matches the *isnad* principle: transmission chain preservation. A successor cultivator can read every session and see how cultivator-A's understanding evolved.

## §7. Activation handoff

When successor F21 activation conditions are met:
1. Cultivator-A approves the F21 entry promoting successor to active, at the live human-in-the-loop CI gate (keyless; the only gate is the ≥50-session catechumenate floor enforced by C46).
2. The substrate emits `succession_completed` (T3 transition per L1/GOVERNANCE §3.2.C).
3. Cultivator-A writes a final **handoff Provenance entry** (per COV06 §4.5).
4. From this point, the catechumenate continues as cultivator-B + future successor candidates; old sessions remain canonical historical record.

## §8. v0.9 status (2026-05-18; scaffolding added Sprint 7.H)

This directory holds **only form scaffolding** — `INDEX.md` (this file), `TEMPLATE.md`, and `HOW_TO_ADD_A_SESSION.md`. **Zero catechumenate sessions. No drafts. No successors named in F21 yet.**

This is **acceptable** per v3.1 acknowledgment: Layer D Catechumenate is *architecturally committed*, *session population deferred*. Cultivator-A (current) and Claude have not yet entered succession preparation. The format + workflow are now specified and ready; when they enter succession preparation, sessions begin accumulating as `D-NNNN-short-name.md` files.

**What this directory is NOT**: it is not optional. It is not "nice to have." Per Phase 3 hunt's catastrophic-severity finding, this directory's eventual population is what distinguishes Myco from a single-generation artifact. Session population may be deferred; commitment may not be.

---

**Catechumenate commitment**: scaffolding in place, zero sessions yet, populated when succession preparation begins; format specified; activation gated by F21 threshold; architecturally load-bearing.
