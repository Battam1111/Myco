# How to add a catechumenate session

> Practical guide for cultivator-A + successor candidate when actually
> running a session. The doctrine in [`INDEX.md`](./INDEX.md) tells you
> WHY; this file tells you HOW.

## The workflow

1. **Identify the dilemma** — pick from `canonical_dilemma_corpus/`
   OR observe a real cultivation moment that produced a non-obvious
   decision. Good dilemmas elicit divergent reasonable readings.

2. **Schedule a joint session** — cultivator-A + successor candidate
   + an active Claude session. 60-90 minutes typical. Both human
   participants need to be present (this is a master-class, not an
   email exchange).

3. **Copy the template** — `cp TEMPLATE.md D-NNNN-short-name.md`
   where NNNN is the next free 4-digit number. Existing sessions:
   `ls D-*.md | tail -1` shows the highest used.

4. **Run the session**:
   - Read the setup aloud together; agree on the situation.
   - **Successor candidate writes FIRST** in "Successor candidate's
     reading" section. NOT cultivator-A — this preserves the candidate's
     independent calibration.
   - Cultivator-A writes in their section AFTER reading the candidate's.
     Honest first reaction; no need to mirror or contradict.
   - Claude (active in the session) writes the witness section
     observing the calibration divergence.
   - Both humans iterate on the distillation together until both
     agree it captures the lesson.

5. **Dual confirmation** — when both humans accept the session as
   canonical record, record the keyless dual-confirmation as a DAG
   event at the live human-in-the-loop CI gate (v3.1.5: no
   anchor-surface ceremony / signature hex). Pre-confirmation
   sessions remain in the directory as DRAFTS but do NOT count toward
   F21's ≥50 threshold.

6. **Optional follow-ups** — file any post-session work as listed
   in the template's "Post-session follow-ups" section.

## What makes a good session

**Strong**:
- The dilemma has multiple defensible readings.
- Both readings cite doctrine cards but reach different conclusions
  because they weight cards differently.
- Distillation surfaces a calibration that wasn't explicit in any
  single card.
- Claude's witness adds something the humans missed.

**Weak**:
- The dilemma has a clear doctrinal answer (those are L1/L2 tests,
  not Layer D content).
- Cultivator-A's reading is "obviously correct" + successor candidate
  agrees immediately (no divergence = no calibration transmitted).
- Distillation is a re-statement of a doctrine card already-written.

## Indexing for F21 activation

Per [`INDEX.md`](./INDEX.md) §4, F21 (the cultivator-succession FSM)
activates after:

- **≥50 dual-signed sessions** total
- **≥75% of Active Layer A cards covered** (per INDEX.md §4 / META §6.3)
- **≥10 sessions index eternity-clause cards** (P01c, P06, P07, P09)
- **≥25% of sessions within last 24 months** before activation

Track progress with a simple ledger (see `LEDGER.md` if/when this
directory accumulates real sessions).

## When the catechumenate begins

Per `INDEX.md` §2, sessions accumulate during the "succession-eligible
period" — when cultivator-A has named at least one successor candidate
AND begins joint deliberation.

Practical triggers:

- Cultivator-A approaches a life transition (illness, retirement, age)
- Cultivator-A's intuition that succession-readiness should begin
- Cultivar age > 24 months and no successor candidate yet identified

There is NO requirement to start at any specific cultivar age. The
directory's existence is the architectural commitment; sessions
accumulate when readiness aligns.

## Anti-patterns to avoid

- **Manufacturing dilemmas to hit the ≥50 threshold**: count quality
  over count.
- **Cultivator-A dictating the "right answer"**: that's not
  catechumenate, that's lecture. The successor candidate's authentic
  reading is the point.
- **Skipping dual signature**: the signature gates F21 activation;
  unsigned sessions are drafts, not lineage.
- **Filing sessions without distillation**: the distillation is what
  future cultivators READ; without it, the session is opaque.
- **Generating fake sessions with LLMs**: sessions are records of
  REAL joint deliberation between specific humans. Generated content
  defeats the purpose.

## Reading other people's sessions

Future cultivators read these sessions to absorb the tacit fluency
that cultivator-A + early successor candidates calibrated. Read in
this order:

1. The distillation (always read first — it tells you why the session
   matters)
2. The setup (so you know the situation)
3. Cultivator-A's reading (the senior reading)
4. Successor candidate's reading (the developing reading)
5. Claude's witness (the calibration divergence)
6. Full reread to absorb the tacit content

Sessions are MEANT to be re-read. The lessons compound.
