---
title: Primordia compression workflow — archive directory + wave-close checkpoint
decision_class: kernel_contract
wave: 22
contract_bump: v0.20.0 → v0.21.0
rounds: 3
confidence: 0.88
closes:
  - "NH-4 (MEDIUM): primordia/ grew past soft limit (45 > 40) with no standing workflow to compress SUPERSEDED/COMPILED crafts; hunger signal fires every run but has no procedural response"
author: Claude (Myco kernel agent, Wave 22, panorama-#2 followup)
date: 2026-04-12
---

# Primordia Compression Craft (Wave 22)

## Round 1 — Claim & First Attack

### A1. Claim

The `detect_structural_bloat` signal has been firing for at least
3 waves with no standing response. The agent reads it on each
`myco hunger`, thinks "yes, primordia is full", and moves on.
This is exactly the same pathology as "a sensor that fires but
nothing catches the signal" — the primordia bloat detector is a
working sensor with no effector. The remedy is twofold:

1. **Physical compression**: move the N most obviously finished
   crafts (already-COMPILED ones whose destinations are known and
   live) into a sibling `archive/` directory. `structural_bloat`'s
   existing non-recursive glob means archived files stop counting.
2. **Standing workflow**: a wave-close checkpoint that triggers
   compression whenever primordia count exceeds soft limit. The
   checkpoint is not a separate reflex arc — it's a one-line rule
   added to `docs/WORKFLOW.md` that any wave reading the
   `structural_bloat` signal in its closing hunger MUST either
   compress or explicitly justify deferral in the log.

### A2. Proposal

- Create `docs/primordia/archive/` directory. Subdirectory
  structure keeps the archive path predictable and the non-
  recursive glob in `detect_structural_bloat` naturally excludes
  it.
- Move these 11 [COMPILED] / [ORIGIN/COMPILED] crafts into
  `archive/`:
  - `generalization_debate_2026-04-07.md` → compiled into
    `docs/evolution_engine.md` + `docs/reusable_system_design.md`
  - `llm_wiki_debate_2026-04-07.md` → compiled into
    `docs/architecture.md`
  - `tacit_knowledge_debate_2026-04-07.md` → compiled into
    `docs/theory.md` + WORKFLOW §W6
  - `nuwa_caveman_integration_2026-04-07.md` → compiled into
    W8-W12 of WORKFLOW.md
  - `retrospective_p4_midterm_2026-04-07.md` → compiled into
    `wiki/results.md` (ASCC side) + evolution protocol
  - `system_state_assessment_2026-04-07.md` → compiled into
    evolution protocol + closed weaknesses W-001..W-005
  - `vision_debate_2026-04-08.md` → superseded by
    `myco_vision_2026-04-08.md` and the final `docs/vision.md`
  - `myco_vision_2026-04-08.md` → compiled into `docs/vision.md`
  - `gear4_trigger_debate_2026-04-09.md` → compiled into
    evolution_engine Gear 4 trigger matrix
  - `decoupling_positioning_debate_2026-04-09.md` → superseded
    by `positioning_craft_2026-04-09.md` (positioning section)
    and `decoupling_craft_2026-04-09.md` (decoupling section)
  - `gear3_v090_milestone_2026-04-09.md` → compiled into v0.9.0
    release notes + Gear 3 retrospective (COMPILED marker already
    in README)
- Update `docs/primordia/README.md` to list archived files in a
  new "Archive (compiled, compressed)" section with the same
  content pointers. No information is lost — the README preserves
  the mental map.
- Add `docs/WORKFLOW.md` Rule W13 — "Primordia Compression
  Checkpoint". One rule: when closing a wave, if hunger shows
  `structural_bloat: primordia`, the wave must either compress OR
  append `deferred: primordia-compression (reason)` to its log
  entry. The rule uses existing sensor, adds no new state.
- Canon bump v0.20.0 → v0.21.0.

### A3. First attacks

- **R1.1** "Moving files changes git blame lineage for future
  readers. Information loss."
- **R1.2** "Archive is just `/dev/null` with extra steps — if the
  content is compiled, why keep it at all?"
- **R1.3** "W13 is a workflow rule, not a kernel constraint —
  this should not bump the contract."
- **R1.4** "45 → 34 brings us under the limit now, but the next
  10 crafts will put us back over. One-shot compression is
  not a standing solution."

### A4. Defenses

- **R1.1 defense**. `git log --follow` preserves full history
  across moves; git blame chains forward. Additionally, the
  README entry for each archived file is updated to keep its
  pointer (source of truth for "where did this compile to"),
  so even readers who don't walk git history see the lineage.
- **R1.2 defense**. The raw debate transcripts contain *how*
  decisions were reached, not just *what* was decided. Compiled
  docs have the answers; the crafts have the rejected
  alternatives and the attacks/defenses that shaped the final
  answer. Future Gear 4 introspection or post-mortem needs the
  transcript. Archive preserves this while removing it from the
  active sensor.
- **R1.3 defense**. W13 is being added *alongside* a canon bump
  for a different reason (the compression itself is a one-time
  event, W13 encodes the standing response). But the rule IS
  binding — failing to respond to `structural_bloat` after W13
  is a W5 (continuous evolution) violation. Code artifacts
  backing W13 are: the sensor already exists, the
  archive convention is codified in WORKFLOW.md text, and
  violations are caught by `myco hunger` itself on the next
  wave. No new lint dimension needed; the accountability is
  procedural.
- **R1.4 defense (valid, design response)**. The standing
  workflow IS the solution to one-shot decay. Every subsequent
  wave of 10 crafts triggers another checkpoint. As long as the
  compression velocity matches or exceeds the creation velocity,
  primordia stays below soft limit indefinitely. If creation
  velocity ever exceeds compression (e.g., wave 30+ where
  everything is still active), that's a real signal — probably
  time to raise the soft limit or split primordia by phase.

## Round 2 — Implementation Plan & Second Attack

### B1. Archive directory mechanics

```bash
mkdir -p docs/primordia/archive
git mv docs/primordia/generalization_debate_2026-04-07.md docs/primordia/archive/
# ... 10 more git mv lines
```

`git mv` preserves history. The `detect_structural_bloat`
function uses `primordia_dir.glob("*.md")` (non-recursive), so
`archive/*.md` is naturally excluded. No code change.

### B2. README restructure

Add a new "## Archive (compiled/compressed)" section at the
bottom of `docs/primordia/README.md` with a table of the 11
archived crafts + their compilation destinations (rehomed from
their existing rows). Add a 2-sentence preamble explaining what
the archive is and when to consult it (post-mortem, Gear 4,
history-of-idea queries).

### B3. WORKFLOW.md Rule W13

Add to `docs/WORKFLOW.md` after W12:

> **W13 — Primordia Compression Checkpoint.** Every wave closes
> with a `myco hunger` read (see session-end protocol). If the
> report includes a `structural_bloat: primordia` signal, the
> wave MUST either:
>
> (a) move ≥N [COMPILED]/[SUPERSEDED] crafts to
> `docs/primordia/archive/` (where N is large enough to bring
> the count back under the soft limit), updating
> `docs/primordia/README.md` to rehome the archived entries; OR
>
> (b) append a `deferred: primordia-compression (<reason>)`
> line to the log.md entry, explaining why no craft is yet ripe
> for archiving.
>
> Compression without a justification, or deferral without a
> reason, is a W5 (continuous evolution) violation detectable by
> reading the next wave's `myco hunger`.

### B4. Canon bump

`_canon.yaml::system.contract_version` and
`synced_contract_version` → v0.21.0. Template same. Comment:
`# Wave 22: primordia compression workflow (closes NH-4)`.

### B5. Changelog v0.21.0 entry

Standard structure — motivation, changes, self-tests, limits.

### B6. Second attacks

- **R2.1** "W13 bakes the archive path into WORKFLOW.md. If we
  ever move or rename the archive, we have to find and update
  all references. Hard-coding paths is brittle."
- **R2.2** "The README rehome is error-prone — if I forget to
  update a row, a reader following the old path hits a 404."
- **R2.3** "`git mv` requires running git commands in the
  sandbox shell, not the desktop-commander host. Does the
  sandbox have git?"
- **R2.4** "Compression velocity matching creation velocity is
  aspirational, not enforced. Nothing stops a wave from creating
  5 new crafts and archiving 0."

### B7. Second defenses

- **R2.1 defense**. The archive path is `docs/primordia/archive/`
  by convention — referenced in W13 as literal text. If moved,
  one search-replace in WORKFLOW.md + the README. Acceptable
  coupling — making it canon-configurable would add more
  surface area than it saves.
- **R2.2 defense**. The README edit is a single commit, audited
  via `git diff` before committing. Missing rows get caught by
  readers in ~next-wave review. Not a permanent data loss — the
  files themselves still exist in archive/, discoverable by
  `ls`.
- **R2.3 defense**. Yes, sandbox has git — confirmed by Wave
  20/21 commits. `git mv` works fine from sandbox shell.
- **R2.4 defense**. W13 is not an enforcement rule, it's a
  response rule: IF `structural_bloat` fires THEN act or defer.
  A wave creating 5 crafts with 0 archives will push primordia
  further over limit → bigger signal next wave → bigger pressure
  to respond. The feedback loop is the enforcement. Explicit
  hard-cap would break creative flow; soft pressure is the
  correct mechanism.

## Round 3 — Edge Cases & Decision

### C1. `archive/` subdirectory might be picked up by other tools

Check: L15 craft-reflex trigger surfaces include
`docs/primordia/`? The L15 trigger list is enumerated in canon;
currently it lists specific files, not globs. So archived
crafts are no longer L15 triggers after the move — correct
behavior (they're frozen, edits to archived files shouldn't
fire L15).

### C2. Link rot in other docs

Some compiled docs reference the debate crafts by path. Search
for `docs/primordia/(generalization|llm_wiki|tacit_knowledge|...)`
across the repo. If found, update to `docs/primordia/archive/...`.
This is a step in the landing checklist.

### C3. README row counting

After moving 11 files, the 11 README rows must move too.
Alternative: keep the rows in their current sections but add
`(archived)` marker, plus path update. Lower risk than moving
rows. Go with that.

### C4. README becomes section-heavy

With an "(archived)" marker the existing sections stay intact.
Total README length barely changes. Acceptable.

### C5. New files created in this wave don't count

`observability_integrity_craft_2026-04-12.md` (Wave 21),
`silent_fail_elimination_craft_2026-04-11.md` (Wave 20),
`primordia_compression_craft_2026-04-12.md` (this file, Wave
22) — all active, stay in primordia. Count goes from 45 → 45-11+1
= 35 after this wave. Soft limit 40, over by -5 (slack of 5).

### C6. Instance projects don't inherit primordia

ASCC does not have `docs/primordia/` — it's a Myco kernel
construct. W13 applies to the kernel and to any instance that
adopts primordia as a working-doc convention. The rule is
idempotent on instances that don't use primordia.

### C7. What about `docs/primordia/README.md` itself?

It's in primordia/ but is not a craft — it's navigation. The
`glob("*.md")` in `detect_structural_bloat` counts it. Going
from 45 → 35 includes README.md, so 34 crafts + 1 README = 35.
Acceptable.

### C8. Decision

**D1** Create `docs/primordia/archive/` and move 11 listed
[COMPILED] crafts via `git mv`.
**D2** Update `docs/primordia/README.md` — mark each archived
row with `(archived)` and update its path to
`archive/<filename>`.
**D3** Add W13 to `docs/WORKFLOW.md` after W12.
**D4** Grep the repo for references to the 11 moved files and
update paths.
**D5** Canon bump v0.20.0 → v0.21.0 in kernel + template.
**D6** Contract changelog v0.21.0 entry.
**D7** Dogfood: final `myco hunger` should NOT show
`structural_bloat: primordia` any more.
**D8** Hole closure: NH-4 (MEDIUM) closed by the combination of
physical compression + standing workflow rule.

**Confidence**: 0.88. All four R1 attacks addressed, all four
R2 attacks addressed, seven edge cases enumerated. Ready to
land.

## 5. Landing Checklist

- [x] Craft written (3 rounds, kernel_contract, confidence ≥0.85)
- [ ] `mkdir -p docs/primordia/archive`
- [ ] `git mv` the 11 listed crafts to `archive/`
- [ ] Update `docs/primordia/README.md` (11 rows get `(archived)` + new path)
- [ ] Add W13 to `docs/WORKFLOW.md` after W12
- [ ] Repo-wide grep + path updates for references to the 11 files
- [ ] Canon bump v0.20.0 → v0.21.0 (kernel + template)
- [ ] `docs/contract_changelog.md` v0.21.0 entry
- [ ] `myco lint` → ≥16/17 green (only pre-existing L13 MEDIUM allowed)
- [ ] `myco hunger` → no `structural_bloat: primordia` signal
- [ ] `myco correct/eat` Wave 22 conclusion → digest to integrated
- [ ] Append `log.md` Wave 22 milestone
- [ ] Commit `[contract:minor] Wave 22 — primordia compression workflow (v0.21.0)`
- [ ] Push via PID 9756
- [ ] Mark Wave 22 complete, move to Wave 23

## 6. Known Limitations

- **L-1** W13 is not lint-enforced. Agent discipline is the only
  mechanism. A future Wave could add an L17 that fires on
  `structural_bloat: primordia` present across 2+ consecutive
  waves without a `deferred: primordia-compression` marker in
  the intervening log entries. Deferred as out-of-scope.
- **L-2** The archive is append-only by convention but not by
  enforcement. A future wave could accidentally delete
  archive/* files. Not a critical risk because git history is
  the ultimate archive.
- **L-3** Archive doesn't preserve chronological grouping — all
  11 files land in a flat directory. For 11 files this is fine;
  if archive grows past ~50 files, consider sub-directory by
  year or by theme.
- **L-4** The "11 files" selection is judgment, not algorithm.
  Future compression checkpoints will also require judgment.
  Automating "which crafts are ripe" would need NLP on the
  `status` frontmatter field + destination-link liveness check —
  deferred.
